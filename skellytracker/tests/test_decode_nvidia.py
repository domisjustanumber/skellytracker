"""The GPU JPEG decoder (`core/decode/nvidia.py`), on JPEG bytes that the test makes.

The tests with no marker use a fake nvImageCodec module. The tests with the marker `gpu` run on
each installed NVIDIA EP pack with the GPU JPEG decoder component, and skip the others.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from skellytracker.core.decode import cpu, nvidia
from skellytracker.core.decode.nvidia import NvJpegDecoder
from skellytracker.core.errors import EpUnavailableError
from skellytracker.core.eps import build_session, registration, store
from skellytracker.core.eps._probe_model import model_bytes
from skellytracker.tests.test_decode_cpu import with_exif_orientation

FLAGS = cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION
SAMPLING = {"420": cv2.IMWRITE_JPEG_SAMPLING_FACTOR_420, "422": cv2.IMWRITE_JPEG_SAMPLING_FACTOR_422}


def picture(width: int, height: int, seed: int = 0) -> np.ndarray:
    """A smooth picture with noise, so that the JPEG is not trivial and each pixel position differs."""
    y, x = np.mgrid[0:height, 0:width]
    image = np.dstack([x * 255 // max(width - 1, 1), y * 255 // max(height - 1, 1), (x + 3 * y) % 256]).astype(np.uint8)
    noise = np.random.default_rng(seed).integers(0, 30, image.shape, dtype=np.uint8)
    return cv2.GaussianBlur(image + noise, (5, 5), 0)


def jpeg(image: np.ndarray, sampling: str = "420") -> bytes:
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 90, cv2.IMWRITE_JPEG_SAMPLING_FACTOR, SAMPLING[sampling]])
    assert ok
    return encoded.tobytes()


def reference(buffer: bytes) -> np.ndarray:
    return cv2.imdecode(np.frombuffer(buffer, np.uint8), FLAGS)


def steps(found: np.ndarray, expected: np.ndarray) -> int:
    assert found.shape == expected.shape
    return int(np.abs(found.astype(np.int16) - expected.astype(np.int16)).max())


# --- tests with a fake nvImageCodec: no GPU ---


class FakeDecoder:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs, self.calls = kwargs, []

    def decode(self, sources: list, **kwargs: object) -> list:
        self.calls.append(list(sources))
        return [None] * len(sources)


FAKE_MODULE = SimpleNamespace(Decoder=FakeDecoder, Backend=lambda kind: kind, BackendKind=SimpleNamespace(GPU_ONLY="gpu", HYBRID_CPU_GPU="hybrid"),
                              DecodeParams=lambda **kwargs: kwargs, I_BGR="bgr")


def fake_cudart(calls: list, current: int = 0) -> SimpleNamespace:
    """A CUDA runtime that records each call. `cudaGetDevice` gives `current`; a stream gets the handle 7."""

    def record(name: str, value: object = None) -> int:
        calls.append(name if value is None else (name, value))
        return 0

    def get_device(device: object) -> int:
        device._obj.value = current  # `device` is a `ctypes.byref` argument
        return record("cudaGetDevice")

    def create(stream: object, flags: int) -> int:
        stream._obj.value = 7
        return record("cudaStreamCreateWithFlags", flags)

    return SimpleNamespace(cudaGetDevice=get_device, cudaSetDevice=lambda device: record("cudaSetDevice", device), cudaStreamCreateWithFlags=create,
                           cudaStreamSynchronize=lambda stream: 0, cudaStreamDestroy=lambda stream: record("cudaStreamDestroy"))


def fake_decoder(calls: list | None = None, device_id: int = 0) -> NvJpegDecoder:
    return NvJpegDecoder(FAKE_MODULE, fake_cudart([] if calls is None else calls), "cuda", None, device_id)


def test_open_gives_none_when_the_pack_has_no_usable_decoder(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(registration, "prepare_jpeg_decoder", lambda key: None)
    assert NvJpegDecoder.open("cuda") is None


def test_open_gives_none_and_one_warning_when_the_cuda_runtime_does_not_load(monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                                                                             caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr(store, "_warned", set())
    monkeypatch.setattr(registration, "prepare_jpeg_decoder", lambda key: (FAKE_MODULE, tmp_path / "no-cudart.dll"))
    with caplog.at_level(logging.WARNING):
        assert NvJpegDecoder.open("cuda") is None
        assert NvJpegDecoder.open("cuda") is None
    assert [record.getMessage() for record in caplog.records if "CUDA runtime does not load" in record.getMessage()] != []
    assert len([record for record in caplog.records if "GPU JPEG decoder" in record.getMessage()]) == 1


def test_open_gives_none_and_a_warning_when_the_cuda_runtime_lacks_a_function(monkeypatch: pytest.MonkeyPatch,
                                                                              caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr(store, "_warned", set())
    monkeypatch.setattr(registration, "prepare_jpeg_decoder", lambda key: (FAKE_MODULE, Path("cudart.dll")))
    monkeypatch.setattr(nvidia.ctypes, "CDLL", lambda path: SimpleNamespace(cudaGetDevice=None))
    with caplog.at_level(logging.WARNING):
        assert NvJpegDecoder.open("trt-rtx") is None
    assert any("'trt-rtx'" in record.getMessage() and "cudaSetDevice" in record.getMessage() for record in caplog.records)


def test_the_decoder_allows_only_the_nvjpeg_backends_and_sets_the_stream_count_to_the_thread_count() -> None:
    kwargs = fake_decoder()._decoder.kwargs
    assert kwargs["backends"] == ["gpu", "hybrid"]
    assert kwargs["options"].split(" ")[0] == f":num_cuda_streams={kwargs['max_num_cpu_threads']}"
    assert 1 <= kwargs["max_num_cpu_threads"] == nvidia.cuda_threads() <= 8


def test_the_decoder_does_the_huffman_step_on_the_gpu_above_500000_pixels() -> None:
    assert fake_decoder()._decoder.kwargs["options"].split(" ")[1:] == ["nvjpeg_cuda_decoder:hybrid_huffman_threshold=500000"]


def test_the_stream_is_made_and_destroyed_on_the_device_of_the_decoder_and_the_current_device_comes_back() -> None:
    calls: list = []
    decoder = fake_decoder(calls, device_id=1)
    decoder.close()
    switch = ["cudaGetDevice", ("cudaSetDevice", 1)]
    assert calls == [*switch, ("cudaStreamCreateWithFlags", 1), ("cudaSetDevice", 0), *switch, "cudaStreamDestroy", ("cudaSetDevice", 0)]


def test_a_buffer_with_no_soi_marker_never_goes_to_the_library() -> None:
    decoder = fake_decoder()
    assert decoder.decode([b"", bytearray(), b"\x89PNG\r\n", b"\xff"], [0, 90, 180, 270]) == [None] * 4
    assert decoder._decoder.calls == []
    assert decoder.decode([b"", b"\xff\xd8\xff", b"x"], [0, 0, 0]) == [None] * 3
    assert decoder._decoder.calls == [[b"\xff\xd8\xff"]]


def test_the_decode_refuses_a_rotation_that_is_not_a_quarter_turn_and_a_missing_rotation() -> None:
    decoder = fake_decoder()
    for rotations in ([45], [0, 0]):
        with pytest.raises(ValueError, match="rotation_deg"):
            decoder.decode([b"\xff\xd8"], rotations)


def test_close_twice_is_allowed_and_a_decode_after_close_raises() -> None:
    with fake_decoder() as decoder:
        pass
    decoder.close()
    with pytest.raises(RuntimeError, match="closed"):
        decoder.decode([b"\xff\xd8"], [0])


# --- tests on the GPU ---


@pytest.fixture(scope="module", params=["cuda", "trt-rtx"])
def gpu_decoder(request: pytest.FixtureRequest):
    try:
        _, report = build_session(model_bytes(), execution_provider=request.param)
    except EpUnavailableError as error:
        pytest.skip(f"{request.param} is not installed: {error}")
    decoder = NvJpegDecoder.open(request.param, report.device_key, report.ep_device_id)
    if decoder is None:
        pytest.skip(f"{request.param} has no GPU JPEG decoder component")
    with decoder:
        yield decoder


@pytest.mark.gpu
@pytest.mark.parametrize("batch", [1, 3, 6])
def test_a_batch_of_mixed_sizes_and_chroma_formats_is_within_3_steps_of_cv2_and_on_the_device(gpu_decoder: NvJpegDecoder, batch: int) -> None:
    sizes = [(640, 480), (641, 359), (64, 48), (1280, 720), (33, 17), (320, 240)]
    buffers = []
    for i, (width, height) in enumerate(sizes[:batch]):
        image = picture(width, height, i)
        buffers.append(jpeg(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)) if i == 2 else jpeg(image, ("420", "422")[i % 2]))
    frames = gpu_decoder.decode(buffers, [0] * batch)
    for buffer, frame in zip(buffers, frames, strict=True):
        assert frame is not None and frame.pixels is None and frame.device.device_name() == "cuda"
        assert frame.device.data_type() == "tensor(uint8)"
        assert steps(frame.host, reference(buffer)) <= 3


@pytest.mark.gpu
@pytest.mark.parametrize("rotation_deg", [90, 180, 270])
def test_the_turn_on_the_gpu_equals_cpu_turn_of_the_same_decoded_pixels(gpu_decoder: NvJpegDecoder, rotation_deg: int) -> None:
    buffers = [jpeg(picture(641, 359, 1), "422"), jpeg(picture(40, 24, 2)), jpeg(picture(641, 359, 3))]
    plain = [frame.host for frame in gpu_decoder.decode(buffers, [0] * 3)]
    for _ in range(2):  # the second pass runs the cached turn session again, with the sizes in turn
        turned = gpu_decoder.decode(buffers, [rotation_deg] * 3)
        for source, frame in zip(plain, turned, strict=True):
            expected = cpu.turn(source, rotation_deg)
            assert (frame.height, frame.width) == expected.shape[:2]
            assert frame.device.device_name() == "cuda"
            np.testing.assert_array_equal(frame.host, expected)


@pytest.mark.gpu
def test_the_decode_does_not_apply_the_exif_orientation(gpu_decoder: NvJpegDecoder) -> None:
    data = jpeg(picture(64, 32))
    (frame,) = gpu_decoder.decode([with_exif_orientation(data, 6)], [0])
    assert (frame.width, frame.height) == (64, 32)
    assert steps(frame.host, reference(data)) <= 3


@pytest.mark.gpu
def test_a_bad_buffer_in_a_batch_gives_none_and_the_good_frames_around_it(gpu_decoder: NvJpegDecoder) -> None:
    good = [jpeg(picture(320, 240, 4)), jpeg(picture(200, 100, 5), "422")]
    png = cv2.imencode(".png", picture(32, 32))[1].tobytes()
    noise = b"\xff\xd8" + np.random.default_rng(6).integers(0, 256, 4000, dtype=np.uint8).tobytes()
    frames = gpu_decoder.decode([good[0], png, b"", noise, b"\xff\xd8", good[1]], [0, 0, 0, 0, 0, 90])
    assert frames[1:5] == [None] * 4
    assert steps(frames[0].host, reference(good[0])) <= 3
    assert steps(frames[5].host, cv2.rotate(reference(good[1]), cv2.ROTATE_90_CLOCKWISE)) <= 3


@pytest.mark.gpu
def test_300_decodes_of_pictures_that_change_each_time_give_no_wrong_frame(gpu_decoder: NvJpegDecoder) -> None:
    """The race check of the wait: without `cudaStreamSynchronize`, earlier measurements gave 62 to 81 wrong runs of 300."""
    image = picture(1280, 720, 7)
    buffers = [jpeg(image, "422"), jpeg(cv2.flip(image, 0), "422")]
    expected = {(c, r): cpu.turn(gpu_decoder.decode([buffers[c]], [0])[0].host, r) for c in (0, 1) for r in (0, 180)}
    wrong = 0
    for i in range(300):
        keys = [((i + k) % 2, 180 * (k == 2)) for k in range(3)]
        frames = gpu_decoder.decode([buffers[c] for c, _ in keys], [r for _, r in keys])
        wrong += any(not np.array_equal(frame.device.numpy(), expected[key]) for key, frame in zip(keys, frames, strict=True))
    assert wrong == 0


@pytest.mark.gpu
@pytest.mark.parametrize("kept", [1, 3])
@pytest.mark.parametrize("rotation_deg", [0, 180, 90])
def test_a_kept_frame_keeps_its_pixels_through_later_decodes_of_the_same_size(gpu_decoder: NvJpegDecoder, rotation_deg: int, kept: int) -> None:
    """A later decode must not write into the GPU memory of a frame that a reader still holds."""
    images = [picture(1280, 720, 10 + k) for k in range(kept)]
    a = [jpeg(image, "422") for image in images]
    b = [jpeg(cv2.flip(image, -1), "422") for image in images]  # the same size, an other content
    expected = [cpu.turn(frame.host, rotation_deg) for frame in gpu_decoder.decode(a, [0] * kept)]
    frames = gpu_decoder.decode(a, [rotation_deg] * kept)
    for later in range(3):
        gpu_decoder.decode(b, [rotation_deg] * kept)
        for k, frame in enumerate(frames):
            assert np.array_equal(frame.device.numpy(), expected[k]), f"kept frame {k} changed after {later + 1} later decodes"


@pytest.mark.gpu
def test_a_frame_kept_after_close_reads_back_its_pixels(gpu_decoder: NvJpegDecoder) -> None:
    data = jpeg(picture(1280, 720, 20), "422")
    expected = cpu.turn(gpu_decoder.decode([data], [0])[0].host, 90)
    decoder = NvJpegDecoder.open(gpu_decoder.execution_provider, gpu_decoder.device_key, gpu_decoder.device_id)
    plain, turned = decoder.decode([data, data], [0, 90])
    decoder.close()
    np.testing.assert_array_equal(turned.host, expected)
    np.testing.assert_array_equal(cpu.turn(plain.host, 90), expected)
    del plain, turned


@pytest.mark.gpu
def test_a_device_frame_goes_to_a_reader_with_no_upload_and_no_host_copy(gpu_decoder: NvJpegDecoder) -> None:
    (frame,) = gpu_decoder.decode([jpeg(picture(64, 48))], [0])

    def no_upload(image: np.ndarray, device_id: object) -> None:
        raise AssertionError("a device frame must not upload")

    assert frame.on_device(gpu_decoder.device_id, no_upload) is frame.device
    assert frame.device.device_name() == "cuda" and frame.device.shape() == [48, 64, 3]
    assert "host" not in vars(frame)  # no host copy was made


ONE_IMAGE = """
import sys
import cv2, numpy as np
from skellytracker.core.decode import nvidia
from skellytracker.core.decode.nvidia import NvJpegDecoder
if sys.argv[2] != "default":
    nvidia.cuda_threads = lambda: int(sys.argv[2])
decoder = NvJpegDecoder.open(sys.argv[1])
(frame,) = decoder.decode([cv2.imencode('.jpg', np.full((48, 64, 3), 100, np.uint8))[1].tobytes()], [0])
print('decoded', frame.width, frame.height, flush=True)
del frame
decoder.close()
"""


@pytest.mark.gpu
@pytest.mark.parametrize("threads", ["default", "4"])
def test_a_decode_of_one_image_returns_when_the_environment_sets_one_cuda_stream(gpu_decoder: NvJpegDecoder, threads: str) -> None:
    env = dict(os.environ, NVIMGCODEC_DEFAULT_NUM_CUDA_STREAMS="1")
    try:
        done = subprocess.run([sys.executable, "-c", ONE_IMAGE, gpu_decoder.execution_provider, threads], capture_output=True, text=True,  # noqa: S603
                              env=env, timeout=120, check=False)
    except subprocess.TimeoutExpired:
        pytest.fail("the decode of one image did not return in 120 s")
    assert done.returncode == 0 and "decoded 64 48" in done.stdout, done.stderr[-2000:]


@pytest.mark.gpu
def test_close_of_a_gpu_decoder_twice_is_allowed_and_a_decode_after_close_raises(gpu_decoder: NvJpegDecoder) -> None:
    decoder = NvJpegDecoder.open(gpu_decoder.execution_provider, gpu_decoder.device_key, gpu_decoder.device_id)
    data = jpeg(picture(64, 48))
    (frame,) = decoder.decode([data], [180])
    assert steps(frame.host, cv2.rotate(reference(data), cv2.ROTATE_180)) <= 3
    del frame
    decoder.close()
    decoder.close()
    with pytest.raises(RuntimeError, match="closed"):
        decoder.decode([data], [0])

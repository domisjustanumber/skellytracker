"""`BatchPreprocessor`: the batch must be byte-identical to `np.stack` over `preprocess_image`.

Each case compares the bytes of the batch, the dtype, the shape and each geometry with the
reference, also across calls that change the frame sizes, the ROIs and the batch size.
"""
from __future__ import annotations

import itertools
from collections.abc import Sequence
from typing import Any

import numpy as np
import pytest

from skellytracker.core.detectors.processing.pre.preprocess import BatchPreprocessor, ResizeGeometry, preprocess_image
from skellytracker.core.model_spec.model import SidecarModel
from skellytracker.tests.model_spec import sidecars

CUSTOM = {"mode": "custom", "scale": 0.5, "mean": [10.0, 20.0, 30.0], "std": [40.0, 50.0, 60.0]}
NORMALIZATIONS = ("none", "unit_float", "imagenet", CUSTOM)
INPUT_DTYPES = ("float32", "float16", "uint8")
SIZE = {"letterbox": "n", "stretch": "n", "fit": "n", "affine_crop": "m", "none": "n"}
# (c_x, c_y, w, h, rotation) in the pixels of a 160 x 90 frame: inside, partly outside, turned
ROIS = [(80.0, 50.0, 40.0, 70.0, 0.0), (150.0, 80.0, 50.0, 45.0, 0.0), (55.0, 45.0, 30.0, 50.0, 0.3)]


def frames(*shapes: tuple[int, int], seed: int = 0) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    return [rng.integers(0, 256, (height, width, 3), dtype=np.uint8) for height, width in shapes]


def sidecar_of(
    method: str, interpolation: str = "linear", compute: str = "uint8", normalization: Any = "none",
    color: str = "bgr", dtype: str = "float32", alt: bool = False,
) -> SidecarModel:
    """A test sidecar with a small target: 40 x 56 for letterbox, stretch and fit, 32 x 24 for affine_crop.

    `alt` takes the other value of each field of the method: an array pad, the centre pad,
    `half_even`, expand 1.0 and no aspect fix.
    """
    base = {"affine_crop": sidecars.simcc_keypoint_detector, "none": sidecars.packed_pose_detector}.get(method, sidecars.nms_detector)()
    size = SIZE[method]
    changes: dict[str, Any] = {"input.normalization": normalization, "input.color_format": color, "input.dtype": {"fp32": dtype}}
    height, width = (32, 24) if method == "affine_crop" else (40, 56)
    if method != "none":
        changes[f"sizes.{size}.input.shape"] = [-1, 3, height, width]
        changes[f"sizes.{size}.input.resize.target_size"] = [height, width]
        resize: dict[str, Any] = {"method": method, "interpolation": interpolation, "compute_dtype": compute}
        pad: Any = [10, 128, 240] if alt else 114
        if method == "letterbox":
            resize |= {"pad_position": "center" if alt else "top_left", "rounding": "half_even" if alt else "half_up", "pad_value": pad}
        elif method == "fit":
            resize["pad_value"] = pad
        elif method == "affine_crop":
            resize["crop_policy"] = {"expand_ratio": 1.0, "maintain_aspect_ratio": False, "pad_value": pad} if alt else {"pad_value": 7}
        changes["input.resize"] = resize
    return SidecarModel.model_validate(sidecars.changed(base, changes))


def reference(sidecar: SidecarModel, size: str, images: Sequence[np.ndarray], rois: Sequence[Any] | None = None) -> tuple[np.ndarray, list[ResizeGeometry]]:
    prepared = [preprocess_image(image, sidecar, size, "fp32", None if rois is None else rois[index]) for index, image in enumerate(images)]
    return np.stack([tensor for tensor, _ in prepared]), [geometry for _, geometry in prepared]


def assert_same(got: tuple[np.ndarray, list[ResizeGeometry]], expected: tuple[np.ndarray, list[ResizeGeometry]], where: str = "") -> None:
    (batch, geometries), (want, want_geometries) = got, expected
    assert (batch.dtype, batch.shape) == (want.dtype, want.shape), where
    assert batch.flags.c_contiguous, where
    assert batch.tobytes() == want.tobytes(), f"{where}: max abs diff {np.abs(batch.astype(np.float64) - want.astype(np.float64)).max()}"
    assert len(geometries) == len(want_geometries), where
    for geometry, want_geometry in zip(geometries, want_geometries, strict=True):
        assert (geometry.method, geometry.src_w, geometry.src_h, geometry.input_size) == (
            want_geometry.method, want_geometry.src_w, want_geometry.src_h, want_geometry.input_size), where
        assert geometry.values.keys() == want_geometry.values.keys(), where
        for key, value in geometry.values.items():
            assert np.array_equal(value, want_geometry.values[key]), f"{where}: {key}"


def inputs_of(method: str) -> tuple[list[np.ndarray], list[Any] | None]:
    if method == "none":
        return frames((48, 64), (48, 64), (48, 64)), None
    if method == "affine_crop":
        return frames((90, 160), (90, 160), (120, 100)), ROIS
    return frames((90, 160), (48, 64), (120, 100)), None


# ---------------------------------------------------------------------------
# Equality with the reference
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method, interpolation, compute",
    [("none", None, None)]
    + list(itertools.product(("letterbox", "stretch", "fit", "affine_crop"), ("linear", "nearest", "cubic", "area"), ("uint8", "float32"))),
)
def test_the_batch_equals_the_stacked_tensors_of_preprocess_image(method: str, interpolation: str | None, compute: str | None) -> None:
    """Each normalization, colour order, input dtype and alternative pad, with mixed frame sizes in one call."""
    images, rois = inputs_of(method)
    for normalization, color, dtype, alt in itertools.product(NORMALIZATIONS, ("bgr", "rgb"), INPUT_DTYPES, (False, True)):
        if method == "none" and alt:
            continue
        sidecar = sidecar_of(method, interpolation or "linear", compute or "uint8", normalization, color, dtype, alt)
        preprocessor = BatchPreprocessor(sidecar, SIZE[method], "fp32")
        where = f"{normalization} {color} {dtype} alt={alt}"
        for count in (1, 3):  # one camera, then three: the first slot keeps its pad
            assert_same(preprocessor.preprocess(images[:count], None if rois is None else rois[:count]),
                        reference(sidecar, SIZE[method], images[:count], None if rois is None else rois[:count]), where)


def test_the_package_sidecars_give_the_batch_of_the_reference() -> None:
    from skellytracker.core.detectors.catalog import load_detector_sidecar

    yolox, rtmw = load_detector_sidecar("yolox-person@openmmlab-exporter"), load_detector_sidecar("rtmw-wholebody133@openmmlab-exporter")
    images = frames((180, 320), (180, 320), (240, 200))
    assert_same(BatchPreprocessor(yolox, "m", "fp32").preprocess(images), reference(yolox, "m", images))
    rois = [(160.0, 100.0, 80.0, 140.0, 0.0), (300.0, 160.0, 100.0, 90.0, 0.0), (110.0, 90.0, 60.0, 100.0, 0.3)]
    assert_same(BatchPreprocessor(rtmw, "m", "fp32").preprocess(images, rois), reference(rtmw, "m", images, rois))


# ---------------------------------------------------------------------------
# Changes between calls
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("alt", [False, True], ids=["top-left", "centre"])
def test_a_new_frame_size_in_a_slot_writes_the_pad_of_its_new_geometry(alt: bool) -> None:
    sidecar = sidecar_of("letterbox", normalization="imagenet", color="rgb", alt=alt)
    preprocessor = BatchPreprocessor(sidecar, "n", "fp32")
    wide, tall, square = frames((90, 160), (120, 100), (64, 64), seed=1)
    for images in ([wide, tall, square], [tall, square, wide], [tall, square, wide], [square, wide, tall]):
        assert_same(preprocessor.preprocess(images), reference(sidecar, "n", images))


def test_a_smaller_batch_uses_the_first_slots_and_a_larger_batch_after_it_is_correct() -> None:
    """A camera with no frame gives a smaller batch. The slots after it keep old values, but no call returns them."""
    sidecar = sidecar_of("letterbox", normalization="unit_float", dtype="float16")
    preprocessor = BatchPreprocessor(sidecar, "n", "fp32")
    wide, tall, square, small = frames((90, 160), (120, 100), (64, 64), (30, 20), seed=2)
    for images in ([wide, tall, square], [square], [tall, wide], [small, small, wide, tall], [wide, tall, square]):
        assert_same(preprocessor.preprocess(images), reference(sidecar, "n", images))


def test_a_new_roi_and_a_new_rotation_between_calls_give_the_crop_of_the_reference() -> None:
    sidecar = sidecar_of("affine_crop", normalization="imagenet", color="rgb")
    preprocessor = BatchPreprocessor(sidecar, "m", "fp32")
    images = frames((90, 160), (120, 100), seed=3)
    for rois in ([ROIS[0], ROIS[1]], [ROIS[2], ROIS[0]], [(70.0, 40.0, 30.0, 30.0, -1.2)], [ROIS[1]] * 2 + [ROIS[2]] * 3):
        items = [images[index % 2] for index in range(len(rois))]
        assert_same(preprocessor.preprocess(items, rois), reference(sidecar, "m", items, rois))


def test_a_new_frame_size_of_method_none_gives_a_new_batch() -> None:
    sidecar = sidecar_of("none", normalization="imagenet", color="rgb")
    preprocessor = BatchPreprocessor(sidecar, "n", "fp32")
    for shapes in ([(48, 64)] * 3, [(30, 40)] * 2, [(48, 64)]):
        images = frames(*shapes, seed=len(shapes))
        assert_same(preprocessor.preprocess(images), reference(sidecar, "n", images))


@pytest.mark.parametrize("method", ["letterbox", "affine_crop", "none"])
def test_a_frame_that_is_a_view_of_a_larger_array_gives_the_batch_of_the_reference(method: str) -> None:
    (large,) = frames((130, 200), seed=6)
    views = [large[20:110, 10:170], large[::2, ::2][:48, :64] if method == "none" else large[5:125, 50:150]]
    if method == "none":
        views = [views[1], large[1::2, 1::2][:48, :64]]
    assert not views[0].flags.c_contiguous
    sidecar = sidecar_of(method, normalization="imagenet", color="rgb")
    rois = ROIS[:2] if method == "affine_crop" else None
    assert_same(BatchPreprocessor(sidecar, SIZE[method], "fp32").preprocess(views, rois), reference(sidecar, SIZE[method], views, rois))


def test_the_batch_is_the_array_of_the_next_call_so_a_caller_that_keeps_it_copies_it() -> None:
    sidecar = sidecar_of("stretch")
    preprocessor = BatchPreprocessor(sidecar, "n", "fp32")
    first, _ = preprocessor.preprocess(frames((90, 160), seed=4))
    kept = first.copy()
    second, _ = preprocessor.preprocess(frames((90, 160), seed=5))
    assert np.shares_memory(first, second) and not np.array_equal(first, kept)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


def raised(call: Any) -> tuple[type[BaseException], str]:
    with pytest.raises(Exception) as found:  # noqa: PT011 - the test compares the error with the error of the reference
        call()
    return found.type, str(found.value)


@pytest.mark.parametrize(
    "method, images, rois",
    [
        ("letterbox", [np.zeros((48, 64), np.uint8)], None),
        ("letterbox", [np.zeros((48, 64, 3), np.float32)], None),
        ("letterbox", [np.zeros((48, 64, 4), np.uint8)], None),
        ("letterbox", [np.zeros((0, 64, 3), np.uint8)], None),
        ("stretch", [np.zeros((48, 64, 3), np.uint8)], [ROIS[0]]),
        ("affine_crop", [np.zeros((48, 64, 3), np.uint8)], None),
        ("affine_crop", [np.zeros((48, 64, 3), np.uint8)], [(1.0, 1.0, 0.0, 0.0, 0.0)]),
        ("affine_crop", [np.zeros((48, 64, 3), np.uint8)], [(1.0, 1.0, float("nan"), 2.0, 0.0)]),
        ("none", [np.zeros((48, 64, 3), np.float32)], None),
        ("none", [np.zeros((48, 64, 3), np.uint8), np.zeros((48, 60, 3), np.uint8)], None),
        ("none", [np.zeros((48, 64, 3), np.uint8), np.zeros((48, 60, 3), np.uint16)], None),
        ("fit", [], None),
    ],
    ids=["2d", "float32", "4-channels", "empty-frame", "roi-for-stretch", "no-roi", "empty-crop", "nan-roi",
         "none-float32", "none-two-shapes", "none-shape-then-dtype", "no-image"],
)
def test_a_bad_input_raises_the_error_of_the_reference(method: str, images: list[np.ndarray], rois: list[Any] | None) -> None:
    sidecar = sidecar_of(method)
    size = SIZE[method]
    assert raised(lambda: BatchPreprocessor(sidecar, size, "fp32").preprocess(images, rois)) == raised(lambda: reference(sidecar, size, images, rois))


def test_a_bad_size_or_precision_raises_the_error_of_the_reference() -> None:
    sidecar, image = sidecar_of("letterbox"), frames((48, 64))[0]
    assert raised(lambda: BatchPreprocessor(sidecar, "x", "fp32")) == raised(lambda: preprocess_image(image, sidecar, "x", "fp32"))
    assert raised(lambda: BatchPreprocessor(sidecar, "n", "fp16")) == raised(lambda: preprocess_image(image, sidecar, "n", "fp16"))
    with pytest.raises(ValueError, match="one length"):
        BatchPreprocessor(sidecar, "n", "fp32").preprocess([image], [ROIS[0], ROIS[1]])

"""`NvJpegDecoder`: the GPU decode of JPEG buffers with nvJPEG (nvImageCodec), and the turn of each frame in GPU memory.

Implements: pipeline.running

This module imports no `onnxruntime`, no `onnx` and no `nvidia` module at import time.
"""
from __future__ import annotations

import ctypes
import os
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np

from skellytracker.core._hardware.sanitize import sanitize_text
from skellytracker.core.decode.cpu import ROTATIONS, starts_as_jpeg
from skellytracker.core.decode.frame import DecodedFrame
from skellytracker.core.eps import registration, store
from skellytracker.core.eps.session import build_session

NON_BLOCKING = 1  # cudaStreamNonBlocking: the stream does not wait for the legacy default stream
TURN_OPSET = 17
CUDART_SYMBOLS = ("cudaGetDevice", "cudaSetDevice", "cudaStreamCreateWithFlags", "cudaStreamSynchronize", "cudaStreamDestroy")


def cuda_threads() -> int:
    """The worker thread count of the decoder, and also its CUDA stream count.

    nvImageCodec 0.10.0 never returns from a decode of one image when it has fewer CUDA streams than
    threads. It limits the threads to the CPU count minus 1, ignores a stream count that it refuses
    (more streams than threads), and then takes NVIMGCODEC_DEFAULT_NUM_CUDA_STREAMS. A count below
    the CPU count and at most 8 is thus valid, and the variable cannot lower it.
    """
    return min(max(1, (os.process_cpu_count() or 2) - 1), 8)


def turn_graph(rotation_deg: int) -> bytes:
    """The ONNX model that turns a BGR `uint8` frame `(H, W, 3)` clockwise by 90, 180 or 270 degrees, as `cv2.rotate`.

    The graph casts to float32, moves the pixels and casts back: TensorRT takes `uint8` only into a
    `Cast`, and each value from 0 to 255 is exact in float32. The height and the width are dynamic.
    """
    from onnx import TensorProto, numpy_helper
    from onnx import helper as oh

    def ints(name: str, values: list[int]):
        return numpy_helper.from_array(np.array(values, np.int64), name)

    # 90: transpose, then reverse the columns. 270: transpose, then reverse the rows. 180: reverse both.
    axes = {90: [1], 180: [0, 1], 270: [0]}[rotation_deg]
    nodes = [oh.make_node("Cast", ["frame"], ["f"], to=TensorProto.FLOAT)]
    moved = "f"
    if rotation_deg != 180:
        nodes.append(oh.make_node("Transpose", ["f"], ["t"], perm=[1, 0, 2]))
        moved = "t"
    nodes += [oh.make_node("Slice", [moved, "starts", "ends", "axes", "steps"], ["r"]),
              oh.make_node("Cast", ["r"], ["turned"], to=TensorProto.UINT8)]
    inits = [ints("starts", [-1] * len(axes)), ints("ends", [-(2**63)] * len(axes)), ints("axes", axes), ints("steps", [-1] * len(axes))]
    graph = oh.make_graph(nodes, f"turn_{rotation_deg}", [oh.make_tensor_value_info("frame", TensorProto.UINT8, ["h", "w", 3])],
                          [oh.make_tensor_value_info("turned", TensorProto.UINT8, None)], inits)
    model = oh.make_model(graph, opset_imports=[oh.make_opsetid("", TURN_OPSET)])
    model.ir_version = 8
    return model.SerializeToString()


class NvJpegDecoder:
    """The nvJPEG decoder of one run on one GPU, with its private CUDA stream and its turn sessions.

    Make it with `open()`. One run uses it from one thread: it is not thread safe. `decode()` gives
    each frame as a device `DecodedFrame`, an `onnxruntime.OrtValue` in GPU memory of the device id.
    The decoder allows only the nvJPEG backends (`GPU_ONLY` and `HYBRID_CPU_GPU`; `GPU_ONLY` alone
    refuses each JPEG on an RTX 3070): nvImageCodec thus never decodes a buffer on the CPU with no
    signal, and a buffer that nvJPEG refuses gives None.
    """

    def __init__(self, nvimgcodec: Any, cudart: Any, execution_provider: str, device_key: str | None, device_id: int) -> None:
        self._nvimgcodec, self._cudart = nvimgcodec, cudart
        self.execution_provider, self.device_key, self.device_id = execution_provider, device_key, device_id
        self._turns: dict[int, Any] = {}  # rotation_deg: the turn session
        self._stream = ctypes.c_void_p()
        self._on_device(lambda: cudart.cudaStreamCreateWithFlags(ctypes.byref(self._stream), NON_BLOCKING), "cudaStreamCreateWithFlags")
        threads = cuda_threads()  # the same count for the threads and the streams
        try:
            self._decoder = nvimgcodec.Decoder(
                device_id=device_id, max_num_cpu_threads=threads, options=f":num_cuda_streams={threads}",
                backends=[nvimgcodec.Backend(nvimgcodec.BackendKind.GPU_ONLY), nvimgcodec.Backend(nvimgcodec.BackendKind.HYBRID_CPU_GPU)])
        except Exception:
            self._on_device(lambda: cudart.cudaStreamDestroy(self._stream), "cudaStreamDestroy")
            raise
        self._params = nvimgcodec.DecodeParams(apply_exif_orientation=False, sample_format=nvimgcodec.I_BGR)

    @classmethod
    def open(cls, execution_provider: str, device_key: str | None = None, ep_device_id: str | int | None = None) -> NvJpegDecoder | None:
        """The decoder for the EP `cuda` or `trt-rtx` on one GPU, or None when the run must decode on the CPU.

        `device_key` and `ep_device_id` are the `SessionReport` fields of a session of the run on that
        GPU. None is the default GPU of `build_session()` and CUDA device 0. The result is None when
        `prepare_jpeg_decoder()` gives None: the pack has no decoder, or the component is missing or
        unusable. It is also None, with one log warning, when the CUDA runtime of the component does
        not load or lacks a function. An other error of the CUDA runtime or of nvImageCodec passes through.
        """
        prepared = registration.prepare_jpeg_decoder(execution_provider)
        if prepared is None:
            return None
        nvimgcodec, cudart_path = prepared
        try:
            cudart = ctypes.CDLL(str(cudart_path))
            for name in CUDART_SYMBOLS:
                getattr(cudart, name)
        except (OSError, AttributeError) as error:
            store.warn_once(f"jpeg-decoder-cudart:{execution_provider}",
                            f"The GPU JPEG decoder of '{execution_provider}' is not used: the CUDA runtime does not load: {sanitize_text(str(error))[:300]}.")
            return None
        return cls(nvimgcodec, cudart, execution_provider, device_key, int(ep_device_id or 0))

    def decode(self, buffers: Sequence[bytes | bytearray], rotations: Sequence[int]) -> list[DecodedFrame | None]:
        """Decode the buffers in one batch, wait for the GPU, then turn each frame clockwise by its `rotation_deg`.

        Buffers can have different sizes. An item is None when nvJPEG cannot decode that buffer: the
        caller decodes it on the CPU. A buffer that does not start with the JPEG SOI marker, also an
        empty buffer, never goes to nvImageCodec and gives None. Each `rotation_deg` is a key of
        `ROTATIONS`. The width and the height of a frame are the values after the turn.
        """
        if self._decoder is None:
            raise RuntimeError("the GPU JPEG decoder is closed")
        if len(buffers) != len(rotations) or any(rotation not in ROTATIONS for rotation in rotations):
            raise ValueError(f"give one rotation_deg of {sorted(ROTATIONS)} for each buffer")
        import onnxruntime

        index = [i for i, buffer in enumerate(buffers) if starts_as_jpeg(buffer)]
        images = self._decoder.decode([buffers[i] for i in index], params=self._params, cuda_stream=self._stream.value) if index else []
        # decode() returns before nvJPEG writes the frames: wait for the private stream.
        _check(self._cudart.cudaStreamSynchronize(self._stream), "cudaStreamSynchronize")
        frames: list[DecodedFrame | None] = [None] * len(buffers)
        for i, image in zip(index, images, strict=True):
            if image is not None:
                # The OrtValue holds the DLPack capsule, and the capsule holds the nvImageCodec image.
                # If a kept frame changes, keep `image` with the frame here.
                value = self._turn(onnxruntime.OrtValue.from_dlpack(image.__dlpack__()), rotations[i])
                height, width = value.shape()[:2]
                frames[i] = DecodedFrame(int(width), int(height), device=value)
        return frames

    def _turn(self, value: Any, rotation_deg: int) -> Any:
        if rotation_deg == 0:
            return value
        if rotation_deg not in self._turns:
            session, report = build_session(turn_graph(rotation_deg), execution_provider=self.execution_provider, device_key=self.device_key)
            if int(report.ep_device_id or 0) != self.device_id:
                raise RuntimeError(f"the turn session is on CUDA device {report.ep_device_id}, not on the device {self.device_id} of the decoder")
            if report.cpu_nodes:  # the result is still exact, but the frame goes to the host and back
                store.warn_once(f"jpeg-turn-cpu:{self.execution_provider}:{rotation_deg}",
                                f"The GPU turn by {rotation_deg} degrees runs {report.cpu_nodes} nodes on the CPU EP: {', '.join(report.cpu_op_types)}.")
            self._turns[rotation_deg] = session
        session = self._turns[rotation_deg]
        binding = session.io_binding()
        binding.bind_ortvalue_input("frame", value)
        binding.bind_output("turned", "cuda", self.device_id)
        session.run_with_iobinding(binding)
        binding.synchronize_outputs()
        return binding.get_outputs()[0]

    def close(self) -> None:
        """Release the turn sessions, the decoder and the CUDA stream, in this order. A second call does nothing.

        The decoder holds no decoded frame. The caller drops each frame of this decoder before the call.
        """
        self._turns.clear()
        self._decoder = None
        if self._stream.value:
            self._on_device(lambda: self._cudart.cudaStreamDestroy(self._stream), "cudaStreamDestroy")
            self._stream = ctypes.c_void_p()

    def _on_device(self, call: Callable[[], int], what: str) -> None:
        """Run one CUDA runtime call on the device of the decoder, then restore the current device of the thread."""
        # shortcut: no host with 2 GPUs tested the device switch; test it on one before multi-GPU is supported.
        previous = ctypes.c_int()
        _check(self._cudart.cudaGetDevice(ctypes.byref(previous)), "cudaGetDevice")
        _check(self._cudart.cudaSetDevice(self.device_id), "cudaSetDevice")
        try:
            _check(call(), what)
        finally:
            _check(self._cudart.cudaSetDevice(previous.value), "cudaSetDevice")

    def __enter__(self) -> NvJpegDecoder:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def _check(code: int, what: str) -> None:
    if code != 0:
        raise RuntimeError(f"{what} returned the CUDA error {code}")

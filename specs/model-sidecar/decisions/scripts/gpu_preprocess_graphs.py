"""Shared code of the GPU preprocess scripts: the preprocess graphs and the nvJPEG hand-over.

Evidence of the proposal resize-pixel-tolerance (section `pre.resize.interpolation`). It is not a
script to run: `gpu_preprocess_parity.py` and `gpu_preprocess_race.py` import it.

A preprocess graph is an ONNX model of the resize and the normalization of one batch. Its inputs
are the RGB frames `frame_<i>`, uint8 (H, W, 3), that nvJPEG decodes into VRAM (nvImageCodec), with
no host copy. Its outputs are `tensor`, the model input, and `pixels`, the resize result before the
normalization (float32 values on the 0-255 scale, in the channel order of the model, with the pad
or the border). The graph of each method, with the OpenCV call of the reference in brackets:

- letterbox (`cv2.resize`, then the pad): Resize, then Pad;
- stretch (`cv2.resize`): Resize to `target_size`;
- fit (`cv2.warpAffine`, constant border): GridSample with the fixed map of `[[s, 0, left], [0, s, top]]`;
- affine_crop (`cv2.warpAffine`, constant border): GridSample with the map of `M` of each ROI (input `theta`).

GridSample pads only with zeros. For a border value `v`, the graph samples `x - v` and adds `v`
back: each filter has weights that sum to 1, so the taps outside the image get the value `v`, as
`BORDER_CONSTANT` gives. The letterbox pad uses the same shift, so a `pad_value` array works.

`compute_dtype: uint8` adds `Floor(x + 0.5)` and `Clip(0, 255)`: the OpenCV uint8 kernels use
fixed-point arithmetic that rounds half up. ONNX `Round` rounds half to even, and that gave a
1-step difference at each exact tie. `compute_dtype: float32` has no round and no clip.

The hand-over: nvJPEG decodes on a private CUDA stream, and the host waits for that stream with
`cudaStreamSynchronize` before the session runs. `Decoder.decode()` returns before nvJPEG writes
the frames, and the stream of the EP does not wait for the decode stream.
"""

from __future__ import annotations

import ctypes
import sys
from importlib import metadata
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from nvidia import nvimgcodec
from onnx import TensorProto
from onnx import helper as oh
from onnx import numpy_helper

import skellytracker
from skellytracker.core.detectors.processing.pre.normalize import IMAGENET_MEAN_RGB, IMAGENET_STD_RGB
from skellytracker.core.detectors.processing.pre.preprocess import resize_geometry
from skellytracker.core.detectors.processing.pre.resize_interpolation import border_values
from skellytracker.core.eps import store
from skellytracker.core.eps.catalog import load_catalog
from skellytracker.core.eps.session import build_session
from skellytracker.core.model_spec.model import SidecarModel

BATCH = 3  # the batch of the landed b3 artifacts
OPSET = 17
SIZE, PRECISION = "m", "fp32"
YOLOX, RTMW = "yolox-person@openmmlab-exporter", "rtmw-wholebody133@openmmlab-exporter"
PACKAGE_ZOO = Path(skellytracker.__file__).parent / "core" / "model_zoo" / "detectors"
RESIZE_MODES = {  # interpolation: the attributes of ONNX Resize that give the cv2.resize filter
    "linear": {"mode": "linear", "coordinate_transformation_mode": "half_pixel"},
    "cubic": {"mode": "cubic", "coordinate_transformation_mode": "half_pixel", "cubic_coeff_a": -0.75},
    "nearest": {"mode": "nearest", "coordinate_transformation_mode": "asymmetric", "nearest_mode": "floor"},
}
GRID_MODES = {"linear": "bilinear", "cubic": "bicubic", "nearest": "nearest"}  # GridSample of opset 16 to 19


def add_common_arguments(parser) -> None:
    parser.add_argument("--ep", nargs="+", default=["cuda", "trt-rtx"], help="EP keys of the catalog")
    parser.add_argument("--model-root", type=Path, default=PACKAGE_ZOO,
                        help="a folder that holds the ONNX files, for example skellytracker/core/model_zoo/detectors "
                             "of an other checkout (default: the model_zoo of the installed package)")
    parser.add_argument("--cudart", type=Path, help="the CUDA runtime library (default: the one in an installed EP pack)")


def with_resize(sidecar: SidecarModel, **changes) -> SidecarModel:
    """A copy of the sidecar with changed `input.resize` fields. The package code does not change."""
    resize = sidecar.input.resize.model_copy(update=changes)
    return sidecar.model_copy(update={"input": sidecar.input.model_copy(update={"resize": resize})})


def model_file(sidecar: SidecarModel, model_root: Path) -> Path:
    name = sidecar.artifact(SIZE, PRECISION).filename
    found = sorted(model_root.rglob(name))
    if not found:
        raise SystemExit(f"no {name} under {model_root}; give --model-root")
    return found[0]


def versions() -> str:
    names = ("onnxruntime", "onnx", "opencv-contrib-python", "numpy", "nvidia-nvimgcodec-cu13", "nvidia-nvjpeg")
    return ", ".join(f"{name} {_version(name)}" for name in names)


def _version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


def session(model, ep: str, label: str):
    """Build a session with the package code. Print the EP pack, the node count of each EP and the CPU nodes.

    Return the session and the CPU node count.
    """
    built, report = build_session(model, execution_provider=ep)
    print(f"  session {label} on {ep} (pack {report.pack_id} {report.pack_version}): nodes {dict(report.nodes_by_ep)}, "
          f"CPU nodes {report.cpu_nodes} {list(report.cpu_op_types)}", flush=True)
    return built, report.cpu_nodes


def load_cudart(path: Path | None):
    """The CUDA runtime from `path`, or from the first installed EP pack that has one."""
    if path is None:
        pattern = "cudart64_*.dll" if sys.platform == "win32" else "libcudart.so*"
        catalog = load_catalog()
        for key in ("trt-rtx", "cuda"):
            pack = catalog.pack(key)
            found = sorted(store.pack_dir(pack["id"], pack["version"]).rglob(pattern)) if pack else []
            if found:
                path = found[0]
                break
        else:
            raise SystemExit("no CUDA runtime library in the installed EP packs; give --cudart")
    return ctypes.CDLL(str(path))


class DeviceDecoder:
    """nvJPEG decode into VRAM on a private CUDA stream."""

    def __init__(self, cudart):
        self.cudart = cudart
        self.decoder = nvimgcodec.Decoder()
        self.stream = ctypes.c_void_p()
        check(cudart.cudaStreamCreateWithFlags(ctypes.byref(self.stream), 1), "cudaStreamCreateWithFlags")  # non-blocking

    def decode(self, jpegs: list[bytes], wait: bool = True) -> list:
        """Decode on the private stream. `wait=False` leaves out the required wait: only the race test uses it."""
        images = self.decoder.decode(jpegs, cuda_stream=self.stream.value)
        if wait:
            check(self.cudart.cudaStreamSynchronize(self.stream), "cudaStreamSynchronize")
        return images

    def host_bgr(self, jpeg: bytes) -> np.ndarray:
        """The nvJPEG pixels of one JPEG, copied to the host, in BGR order."""
        return np.ascontiguousarray(np.asarray(self.decode([jpeg])[0].cpu())[..., ::-1])


def check(code: int, what: str) -> None:
    if code != 0:
        raise RuntimeError(f"{what} returned {code}")


def frame_inputs(images: list) -> dict:
    """The decoded images as the graph inputs, through DLPack: no copy."""
    return {f"frame_{i}": ort.OrtValue.from_dlpack(image.__dlpack__()) for i, image in enumerate(images)}


def bind_run(built, inputs: dict) -> list:
    """Run with OrtValue inputs. The outputs stay in VRAM, in the order of the session outputs."""
    binding = built.io_binding()
    for name, value in inputs.items():
        binding.bind_ortvalue_input(name, value)
    for output in built.get_outputs():
        binding.bind_output(output.name, "cuda", 0)
    built.run_with_iobinding(binding)
    binding.synchronize_outputs()
    return binding.get_outputs()


def _const(name: str, value) -> object:
    return numpy_helper.from_array(np.asarray(value), name)


def _frames_nchw(nodes: list, inits: list, color_format: str) -> str:
    """BATCH inputs uint8 (H, W, 3) RGB -> float32 (BATCH, 3, H, W) in the channel order of the model."""
    inits.append(_const("axis0", np.array([0], np.int64)))
    for i in range(BATCH):
        nodes.append(oh.make_node("Cast", [f"frame_{i}"], [f"f_{i}"], to=TensorProto.FLOAT))  # TensorRT: uint8 only into a Cast
        nodes.append(oh.make_node("Unsqueeze", [f"f_{i}", "axis0"], [f"u_{i}"]))
    nodes.append(oh.make_node("Concat", [f"u_{i}" for i in range(BATCH)], ["nhwc"], axis=0))
    nodes.append(oh.make_node("Transpose", ["nhwc"], ["nchw"], perm=[0, 3, 1, 2]))
    if color_format == "rgb":
        return "nchw"
    inits.append(_const("bgr", np.array([2, 1, 0], np.int64)))
    nodes.append(oh.make_node("Gather", ["nchw", "bgr"], ["frames"], axis=1))
    return "frames"


def _compute_dtype(nodes: list, inits: list, name: str, compute_dtype: str) -> str:
    if compute_dtype == "float32":
        return name
    inits += [_const("half", np.float32(0.5)), _const("lo", np.float32(0)), _const("hi", np.float32(255))]
    nodes.append(oh.make_node("Add", [name, "half"], ["plus_half"]))
    nodes.append(oh.make_node("Floor", ["plus_half"], ["rounded"]))  # half up, as OpenCV; Round is half to even
    nodes.append(oh.make_node("Clip", ["rounded", "lo", "hi"], ["clipped"]))
    return "clipped"


def _warp(nodes: list, inits: list, x: str, grid: str, interpolation: str, border) -> str:
    """GridSample with a constant border: sample `x - v` with zero padding, then add `v`."""
    inits.append(_const("border", np.array(border, np.float32).reshape(1, 3, 1, 1)))
    nodes.append(oh.make_node("Sub", [x, "border"], ["shifted"]))
    nodes.append(oh.make_node("GridSample", ["shifted", grid], ["sampled"], mode=GRID_MODES[interpolation],
                              padding_mode="zeros", align_corners=0))
    nodes.append(oh.make_node("Add", ["sampled", "border"], ["warped"]))
    return "warped"


def _grid(nodes: list, inits: list, theta: str, t_h: int, t_w: int) -> str:
    """The GridSample grid of a target pixel index (x, y, 1) for `theta` (BATCH, 2, 3)."""
    ys, xs = np.mgrid[0:t_h, 0:t_w]
    base = np.stack([xs.ravel(), ys.ravel(), np.ones(t_h * t_w)], axis=1).astype(np.float32)  # (HW, 3)
    inits += [_const("base", base), _const("grid_shape", np.array([BATCH, t_h, t_w, 2], np.int64))]
    nodes.append(oh.make_node("Transpose", [theta], ["theta_t"], perm=[0, 2, 1]))  # (BATCH, 3, 2)
    nodes.append(oh.make_node("MatMul", ["base", "theta_t"], ["grid_flat"]))  # (BATCH, HW, 2)
    nodes.append(oh.make_node("Reshape", ["grid_flat", "grid_shape"], ["grid"]))
    return "grid"


def preprocess_graph(sidecar: SidecarModel, src_w: int, src_h: int) -> bytes:
    """The preprocess graph of the resize method of the sidecar, for frames of src_w x src_h."""
    spec, resize = sidecar.input, sidecar.input.resize
    normalization = spec.normalization_for(PRECISION)
    if normalization not in ("none", "imagenet") or resize.interpolation not in GRID_MODES:
        raise SystemExit(f"no graph for the normalization {normalization!r} or the interpolation {resize.interpolation!r}")
    t_h, t_w = (int(v) for v in sidecar.size(SIZE).target_size)
    border = border_values(resize.crop_policy.pad_value if resize.method == "affine_crop" else resize.pad_value or 0)
    nodes, inits, extra = [], [], []
    x = _frames_nchw(nodes, inits, spec.color_format)
    if resize.method in ("letterbox", "stretch"):
        g = resize_geometry(resize, [t_h, t_w], src_w, src_h).values
        n_h, n_w = (g["n_h"], g["n_w"]) if resize.method == "letterbox" else (t_h, t_w)
        inits.append(_const("sizes", np.array([BATCH, 3, n_h, n_w], np.int64)))
        nodes.append(oh.make_node("Resize", [x, "", "", "sizes"], ["resized"], **RESIZE_MODES[resize.interpolation]))
        x = _compute_dtype(nodes, inits, "resized", resize.compute_dtype)
        if resize.method == "letterbox":  # pad `x - v` with zeros, then add `v`: one value for each channel
            pads = [0, 0, g["top"], g["left"], 0, 0, t_h - n_h - g["top"], t_w - n_w - g["left"]]
            inits += [_const("pads", np.array(pads, np.int64)), _const("pad", np.array(border, np.float32).reshape(1, 3, 1, 1))]
            nodes.append(oh.make_node("Sub", [x, "pad"], ["unpadded"]))
            nodes.append(oh.make_node("Pad", ["unpadded", "pads"], ["padded"], mode="constant"))
            nodes.append(oh.make_node("Add", ["padded", "pad"], ["canvas"]))
            x = "canvas"
    elif resize.method in ("fit", "affine_crop"):
        if resize.method == "fit":
            g = resize_geometry(resize, [t_h, t_w], src_w, src_h).values
            matrix = [[g["scale"], 0.0, g["left"]], [0.0, g["scale"], g["top"]]]
            inits.append(_const("theta", np.stack([theta_of(matrix, src_w, src_h)] * BATCH)))
        else:
            extra.append(oh.make_tensor_value_info("theta", TensorProto.FLOAT, [BATCH, 2, 3]))
        grid = _grid(nodes, inits, "theta", t_h, t_w)
        x = _compute_dtype(nodes, inits, _warp(nodes, inits, x, grid, resize.interpolation, border), resize.compute_dtype)
    else:
        raise SystemExit(f"no graph for the method {resize.method!r}")
    nodes.append(oh.make_node("Identity", [x], ["pixels"]))
    if normalization == "none":
        nodes.append(oh.make_node("Identity", [x], ["tensor"]))
    else:
        mean, std = np.array(IMAGENET_MEAN_RGB, np.float32), np.array(IMAGENET_STD_RGB, np.float32)
        if spec.color_format == "bgr":
            mean, std = mean[::-1], std[::-1]
        inits += [_const("mean", mean.reshape(1, 3, 1, 1)), _const("std", std.reshape(1, 3, 1, 1))]
        nodes.append(oh.make_node("Sub", [x, "mean"], ["centered"]))
        nodes.append(oh.make_node("Div", ["centered", "std"], ["tensor"]))
    inputs = [oh.make_tensor_value_info(f"frame_{i}", TensorProto.UINT8, [src_h, src_w, 3]) for i in range(BATCH)]
    outputs = [oh.make_tensor_value_info(name, TensorProto.FLOAT, [BATCH, 3, t_h, t_w]) for name in ("tensor", "pixels")]
    model = oh.make_model(oh.make_graph(nodes, "preprocess", inputs + extra, outputs, inits),
                          opset_imports=[oh.make_opsetid("", OPSET)])
    model.ir_version = 9
    return model.SerializeToString()


def theta_of(matrix, src_w: int, src_h: int) -> np.ndarray:
    """`M` (source -> target, OpenCV pixel indices) -> the GridSample map of a target pixel index (x, y, 1)."""
    inv = cv2.invertAffineTransform(np.asarray(matrix, np.float64))
    theta = np.empty((2, 3))
    theta[0] = [2 * inv[0, 0] / src_w, 2 * inv[0, 1] / src_w, (2 * inv[0, 2] + 1) / src_w - 1]
    theta[1] = [2 * inv[1, 0] / src_h, 2 * inv[1, 1] / src_h, (2 * inv[1, 2] + 1) / src_h - 1]
    return theta.astype(np.float32)


def thetas(sidecar: SidecarModel, rois: list, src_w: int, src_h: int):
    """The `theta` input of BATCH ROIs, as an OrtValue."""
    target = sidecar.size(SIZE).target_size
    values = [theta_of(resize_geometry(sidecar.input.resize, target, src_w, src_h, roi).values["matrix"], src_w, src_h)
              for roi in rois]
    return ort.OrtValue.ortvalue_from_numpy(np.stack(values))

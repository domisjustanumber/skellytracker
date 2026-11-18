"""The preprocess graph: the resize step and the normalization of one sidecar as ONNX nodes.

`build_preprocess_graph` gives an ONNX model for one sidecar, one size, one precision, one list of
camera slots and one batch. Each slot `i` has a source size and one input `frame_<i>`: one host
frame, uint8, `(H_i, W_i, 3)`, BGR. The sizes of the slots can differ. The input `index`, int64,
`(batch,)`, gives the slot of each item of the batch: a slot can have many items, for example one
item for each box of a top-down model, or no item. An `affine_crop` graph has the input `theta`:
float32, `(batch, 2, 3)`, one map for each item, from `affine_crop_theta`. Its outputs are
`tensor`, the model input that `preprocess_image` gives for each item (`(batch, 3, T_h, T_w)` in
`input.dtype`), and `pixels`, the resize result before the normalization: float32 on the 0-255
scale, in the channel order of the model, with the pad or the border. The resize limit of
`pre.resize.interpolation` applies to `pixels` (`within_resize_limit`).

For `letterbox`, `stretch`, `fit` and `none`, the source size sets the geometry: each slot has its
own nodes and constants up to the model input size, then `Concat` joins the slots and `Gather`
takes the slot of each item. `none` refuses slots of different sizes. For `affine_crop`, each item
has its own map: each slot is padded at the bottom and the right to the canvas (the largest width
and the largest height) with the border value, then `Concat` and `Gather` give the canvas of each
item, and one `GridSample` samples it.

The graph has only ONNX nodes that run on `cuda` and `trt-rtx` with no CPU node (evidence of
ADR-J1HK): a `Cast` is the first node on each uint8 input; `Gather` changes the channel order;
`Resize` has the attributes of `RESIZE_MODES` for `linear` and `cubic`; for `nearest`, two `Gather`
nodes take the rows and the columns that `cv2.resize` with `cv2.INTER_NEAREST` takes for an index
ramp, so the pixels are equal to the CPU path; a `uint8` result is `Clip(Floor(x + 0.5), 0, 255)`,
because ONNX `Round` rounds half to even and OpenCV rounds half up; `Pad` makes the letterbox pad.
`fit` and `affine_crop` use `GridSample` (`align_corners=0`, zero padding) on `x - v` and then add
`v`, for the border value `v`; the grid is `MatMul` of the target pixel indices and `theta`, the
inverse of `M` in the normalized coordinates of `GridSample`. `nearest` with `fit` uses one `Gather`
with the source index of each target pixel that `cv2.warpAffine` with `cv2.INTER_NEAREST` gives for
an index image in the compute dtype; the border pixels take an added pixel of value `v`. `none` has
no resize step: the graph only casts, changes the channel order and normalizes.

The graph does `letterbox`, `stretch`, `fit` and `affine_crop` with `linear` and `cubic` in the
compute dtype `uint8`, `letterbox`, `stretch` and `fit` with `nearest` in both compute dtypes, and
`none`, with the normalizations `none` and `imagenet` and the input dtypes `float32` and `float16`.
It refuses `area`, `nearest` with `affine_crop`, `compute_dtype: float32` with `linear` or `cubic`
(the float32 results of `Resize` and `GridSample` go over the limit on a large frame), the other
normalizations and the other input dtypes with `PreprocessGraphRefusedError`: the caller then uses
`preprocess_image`.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import cv2
import numpy as np
import onnx
from onnx import TensorProto, numpy_helper
from onnx import helper as oh

from skellytracker.core.detectors.processing.pre.normalize import IMAGENET_MEAN_RGB, IMAGENET_STD_RGB
from skellytracker.core.detectors.processing.pre.preprocess import resize_geometry
from skellytracker.core.detectors.processing.pre.resize_interpolation import COMPUTE_DTYPES, border_values
from skellytracker.core.model_spec.model import SidecarModel

OPSET = 17
IR_VERSION = 9  # onnxruntime 1.31 reads IR version 13 or lower
RESIZE_MODES = {  # the attributes of ONNX Resize that give the cv2.resize filter
    "linear": {"mode": "linear", "coordinate_transformation_mode": "half_pixel"},
    "cubic": {"mode": "cubic", "coordinate_transformation_mode": "half_pixel", "cubic_coeff_a": -0.75},
}
GRID_MODES = {"linear": "bilinear", "cubic": "bicubic"}  # GridSample modes of opset 16 to 19, cubic a = -0.75
INTERPOLATIONS = ("linear", "cubic", "nearest")  # nearest: Gather nodes with index tables of the OpenCV call
NORMALIZATIONS = ("none", "imagenet")
TENSOR_TYPES = {"float32": TensorProto.FLOAT, "float16": TensorProto.FLOAT16}


class PreprocessGraphRefusedError(ValueError):
    """The preprocess graph does not implement this configuration. Use `preprocess_image`."""


def build_preprocess_graph(
    sidecar: SidecarModel, size: str, precision: str, sources: Sequence[tuple[int, int]], batch: int
) -> onnx.ModelProto:
    """Return the preprocess graph of `preprocess_image` for `batch` items on the frames of `sources`.

    Implements: pre.resize.interpolation
    Implements: pre.resize.letterbox
    Implements: pre.resize.stretch
    Implements: pre.resize.fit
    Implements: pre.resize.affine_crop
    Implements: pre.resize.none
    Implements: pre.normalize

    `sources` holds the `(src_w, src_h)` of each camera slot. The sizes can differ, except for
    `none`. The geometry comes from `resize_geometry`, as in `preprocess_image`. For `affine_crop`,
    the caller gives the input `theta` of the ROIs from `affine_crop_theta` with the same `sources`.
    The caller must bind each input `frame_<i>`, also when no item of `index` uses the slot `i`:
    then any frame of the size of the slot is correct, because its content does not change the
    outputs. A configuration that the graph does not implement raises `PreprocessGraphRefusedError`.
    """
    spec, resize = sidecar.input, sidecar.input.resize
    if precision not in spec.dtype:
        raise ValueError(f"no precision {precision!r}; input.dtype has {list(spec.dtype)}")
    if batch < 1:
        raise ValueError(f"the batch must be 1 or more, not {batch}")
    normalization, dtype = spec.normalization_for(precision), spec.dtype[precision]
    if resize.method != "none" and resize.interpolation not in INTERPOLATIONS:
        raise PreprocessGraphRefusedError(f"the preprocess graph has no interpolation {resize.interpolation!r}")
    if resize.method == "affine_crop" and resize.interpolation == "nearest":
        # the GridSample nearest of the evidence graphs took other source pixels; M changes with each ROI
        raise PreprocessGraphRefusedError("the preprocess graph has no interpolation 'nearest' with the method 'affine_crop'")
    if resize.compute_dtype == "float32" and resize.interpolation in ("linear", "cubic"):
        # the float32 results of Resize and GridSample go over the limit of 0.05 on a large frame (CPU EP)
        raise PreprocessGraphRefusedError(f"the preprocess graph has no compute dtype 'float32' with the interpolation {resize.interpolation!r}")
    if normalization not in NORMALIZATIONS:
        raise PreprocessGraphRefusedError(f"the preprocess graph has no normalization {normalization!r}")
    if dtype not in TENSOR_TYPES:
        raise PreprocessGraphRefusedError(f"the preprocess graph has no input dtype {dtype!r}")

    sources = [(int(src_w), int(src_h)) for src_w, src_h in sources]
    if not sources:
        raise ValueError("the graph needs one source or more")
    if resize.method == "none" and len(set(sources)) > 1:
        raise PreprocessGraphRefusedError(f"the preprocess graph has no method 'none' with different source sizes {sources}")
    target_size = sidecar.size(size).target_size
    if resize.method == "affine_crop":  # the geometry needs the ROI: the caller gives it in `theta`
        t_h, t_w = (int(value) for value in target_size)
        canvas_w, canvas_h = max(w for w, _ in sources), max(h for _, h in sources)
    else:  # the model input size of letterbox, stretch and fit is the target size; of none, the one source size
        t_h, t_w = resize_geometry(resize, target_size, *sources[0]).input_size
    inits: dict[str, onnx.TensorProto] = {}  # one name for each constant: the slots of one source size share theirs
    if resize.method in ("letterbox", "fit", "affine_crop"):
        pad_value = resize.crop_policy.pad_value if resize.method == "affine_crop" else resize.pad_value
        # in the order of color_format, cast through the compute dtype as the border and the canvas fill of the CPU path
        border = np.array(border_values(pad_value)).astype(COMPUTE_DTYPES[str(resize.compute_dtype)]).astype(np.float32)
        inits["border"] = _const("border", border.reshape(1, 3, 1, 1))
    if spec.color_format == "rgb":
        inits["rgb_order"] = _const("rgb_order", np.array([2, 1, 0], np.int64))
    inputs: list[onnx.ValueInfoProto] = []
    nodes: list[onnx.NodeProto] = []
    slots = []
    for i, (src_w, src_h) in enumerate(sources):
        key, s = f"{src_w}x{src_h}", f"_{i}"  # `key` names the constants of a source size, `s` the values of the slot
        inputs.append(oh.make_tensor_value_info(f"frame{s}", TensorProto.UINT8, [src_h, src_w, 3]))
        inits[f"shape_{key}"] = _const(f"shape_{key}", np.array([1, src_h, src_w, 3], np.int64))
        nodes += [
            oh.make_node("Cast", [f"frame{s}"], [f"cast{s}"], to=TensorProto.FLOAT),  # TensorRT: uint8 only into a Cast
            oh.make_node("Reshape", [f"cast{s}", f"shape_{key}"], [f"hwc{s}"]),
            oh.make_node("Transpose", [f"hwc{s}"], [f"bgr{s}"], perm=[0, 3, 1, 2]),
        ]
        x = f"bgr{s}"
        if spec.color_format == "rgb":
            nodes.append(oh.make_node("Gather", [x, "rgb_order"], [f"rgb{s}"], axis=1))
            x = f"rgb{s}"
        if resize.method in ("letterbox", "stretch"):
            geometry = resize_geometry(resize, target_size, src_w, src_h)
            n_h, n_w = (geometry.values["n_h"], geometry.values["n_w"]) if resize.method == "letterbox" else (t_h, t_w)
            if resize.interpolation == "nearest":
                # cv2.INTER_NEAREST does not give floor(x * src_n / dst_n) at each size, so the tables come from the same call.
                columns = cv2.resize(np.arange(src_w, dtype=np.float32)[None], (n_w, 1), interpolation=cv2.INTER_NEAREST)[0]
                rows = cv2.resize(np.arange(src_h, dtype=np.float32)[:, None], (1, n_h), interpolation=cv2.INTER_NEAREST)[:, 0]
                inits[f"rows_{key}"] = _const(f"rows_{key}", rows.astype(np.int64))
                inits[f"columns_{key}"] = _const(f"columns_{key}", columns.astype(np.int64))
                nodes += [
                    oh.make_node("Gather", [x, f"rows_{key}"], [f"picked_rows{s}"], axis=2),
                    oh.make_node("Gather", [f"picked_rows{s}", f"columns_{key}"], [f"resized{s}"], axis=3),
                ]
            else:
                inits[f"sizes_{key}"] = _const(f"sizes_{key}", np.array([1, 3, n_h, n_w], np.int64))
                nodes.append(oh.make_node("Resize", [x, "", "", f"sizes_{key}"], [f"resized{s}"], **RESIZE_MODES[str(resize.interpolation)]))
            x = _round_half_up(nodes, inits, f"resized{s}", s, str(resize.compute_dtype))
            if resize.method == "letterbox":  # pad `x - v` with zeros, then add `v`: one value for each channel
                top, left = geometry.values["top"], geometry.values["left"]
                pads = [0, 0, top, left, 0, 0, t_h - n_h - top, t_w - n_w - left]
                inits[f"pads_{key}"] = _const(f"pads_{key}", np.array(pads, np.int64))
                nodes += [
                    oh.make_node("Sub", [x, "border"], [f"unpadded{s}"]),
                    oh.make_node("Pad", [f"unpadded{s}", f"pads_{key}"], [f"padded{s}"], mode="constant"),
                    oh.make_node("Add", [f"padded{s}", "border"], [f"canvas{s}"]),
                ]
                x = f"canvas{s}"
        elif resize.method == "fit" and resize.interpolation == "nearest":  # the source index of each target pixel, src_h * src_w for the border
            matrix = _fit_matrix(resize_geometry(resize, target_size, src_w, src_h).values)
            inits[f"flat_shape_{key}"] = _const(f"flat_shape_{key}", np.array([1, 3, src_h * src_w], np.int64))
            inits["border_pixel"] = _const("border_pixel", border.reshape(1, 3, 1))
            inits[f"source_index_{key}"] = _const(f"source_index_{key}", _warp_nearest_index(matrix, src_w, src_h, t_w, t_h, str(resize.compute_dtype)))
            nodes += [
                oh.make_node("Reshape", [x, f"flat_shape_{key}"], [f"flat{s}"]),
                oh.make_node("Concat", [f"flat{s}", "border_pixel"], [f"flat_and_border{s}"], axis=2),
                oh.make_node("Gather", [f"flat_and_border{s}", f"source_index_{key}"], [f"resized{s}"], axis=2),
            ]
            x = _round_half_up(nodes, inits, f"resized{s}", s, str(resize.compute_dtype))
        elif resize.method == "fit":  # GridSample with a constant border
            matrix = _fit_matrix(resize_geometry(resize, target_size, src_w, src_h).values)
            inits[f"theta_{key}"] = _const(f"theta_{key}", _theta(matrix, src_w, src_h)[None])
            nodes.append(oh.make_node("Sub", [x, "border"], [f"shifted{s}"]))
            x = _grid_sample(nodes, inits, f"shifted{s}", f"theta_{key}", s, 1, t_h, t_w, str(resize.interpolation))
            x = _round_half_up(nodes, inits, x, s, str(resize.compute_dtype))
        elif resize.method == "affine_crop":  # pad `x - v` with zeros to the canvas: a pad pixel is the border value
            nodes.append(oh.make_node("Sub", [x, "border"], [f"shifted{s}"]))
            x = f"shifted{s}"
            if (src_h, src_w) != (canvas_h, canvas_w):
                inits[f"canvas_pads_{key}"] = _const(f"canvas_pads_{key}", np.array([0, 0, 0, 0, 0, 0, canvas_h - src_h, canvas_w - src_w], np.int64))
                nodes.append(oh.make_node("Pad", [x, f"canvas_pads_{key}"], [f"on_canvas{s}"], mode="constant"))
                x = f"on_canvas{s}"
        slots.append(x)
    if len(slots) > 1:  # (F, 3, H, W); one slot needs no Concat
        nodes.append(oh.make_node("Concat", slots, ["slots"], axis=0))
        slots = ["slots"]
    inputs.append(oh.make_tensor_value_info("index", TensorProto.INT64, [batch]))
    nodes.append(oh.make_node("Gather", [slots[0], "index"], ["items"], axis=0))  # (batch, 3, H, W): the slot of each item
    x = "items"
    if resize.method == "affine_crop":  # one GridSample of the canvas of each item with the map of its ROI
        inputs.append(oh.make_tensor_value_info("theta", TensorProto.FLOAT, [batch, 2, 3]))
        x = _grid_sample(nodes, inits, x, "theta", "", batch, t_h, t_w, str(resize.interpolation))
        x = _round_half_up(nodes, inits, x, "", str(resize.compute_dtype))
    nodes.append(oh.make_node("Identity", [x], ["pixels"]))
    if normalization == "imagenet":
        mean, std = np.array(IMAGENET_MEAN_RGB, np.float32), np.array(IMAGENET_STD_RGB, np.float32)
        if spec.color_format == "bgr":
            mean, std = mean[::-1], std[::-1]
        inits |= {"mean": _const("mean", mean.reshape(1, 3, 1, 1)), "std": _const("std", std.reshape(1, 3, 1, 1))}
        nodes += [oh.make_node("Sub", [x, "mean"], ["centered"]), oh.make_node("Div", ["centered", "std"], ["normalized"])]
        x = "normalized"
    nodes.append(oh.make_node("Cast", [x], ["tensor"], to=TENSOR_TYPES[dtype]))

    outputs = [
        oh.make_tensor_value_info("tensor", TENSOR_TYPES[dtype], [batch, 3, t_h, t_w]),
        oh.make_tensor_value_info("pixels", TensorProto.FLOAT, [batch, 3, t_h, t_w]),
    ]
    model = oh.make_model(
        oh.make_graph(nodes, "preprocess", inputs, outputs, list(inits.values())), opset_imports=[oh.make_opsetid("", OPSET)]
    )
    model.ir_version = IR_VERSION
    return model


def affine_crop_theta(
    sidecar: SidecarModel, size: str, sources: Sequence[tuple[int, int]], rois: Sequence[Sequence[Any]]
) -> np.ndarray:
    """Return the input `theta` of an `affine_crop` graph: float32, `(len(rois), 2, 3)`.

    Implements: pre.resize.affine_crop

    `sources` are the `(src_w, src_h)` of the graph, one for each slot. Each ROI is
    `(c_x, c_y, w, h, rotation)` in the pixels of the frame of its item, as `preprocess_image` takes
    it (for a box, `roi_from_box`). The matrix `M` comes from `resize_geometry`, as in the CPU path.
    The map is in the normalized coordinates of the canvas (the largest width and the largest
    height of `sources`), because the graph samples each frame on that canvas.
    """
    target_size = sidecar.size(size).target_size
    canvas_w, canvas_h = max(w for w, _ in sources), max(h for _, h in sources)
    matrices = [resize_geometry(sidecar.input.resize, target_size, canvas_w, canvas_h, roi).values["matrix"] for roi in rois]
    return np.stack([_theta(matrix, canvas_w, canvas_h) for matrix in matrices])


def _round_half_up(nodes: list[onnx.NodeProto], inits: dict[str, onnx.TensorProto], x: str, s: str, compute_dtype: str) -> str:
    """`Clip(Floor(x + 0.5), 0, 255)` for the compute dtype `uint8`: ONNX `Round` rounds half to even, OpenCV half up."""
    if compute_dtype != "uint8":
        return x
    inits |= {"half": _const("half", np.float32(0.5)), "low": _const("low", np.float32(0)), "high": _const("high", np.float32(255))}
    nodes += [
        oh.make_node("Add", [x, "half"], [f"plus_half{s}"]),
        oh.make_node("Floor", [f"plus_half{s}"], [f"rounded{s}"]),
        oh.make_node("Clip", [f"rounded{s}", "low", "high"], [f"clipped{s}"]),
    ]
    return f"clipped{s}"


def _grid_sample(nodes: list[onnx.NodeProto], inits: dict[str, onnx.TensorProto], x: str, theta: str, s: str,
                 batch: int, t_h: int, t_w: int, interpolation: str) -> str:
    """Sample `x - v` (`x`) at the grid of `theta` (`(batch, 2, 3)`) with zero padding, then add the border `v`."""
    ys, xs = np.mgrid[0:t_h, 0:t_w]
    base = np.stack([xs.ravel(), ys.ravel(), np.ones(t_h * t_w)], axis=1).astype(np.float32)  # (T_h * T_w, 3)
    inits |= {"base": _const("base", base), f"grid_shape_{batch}": _const(f"grid_shape_{batch}", np.array([batch, t_h, t_w, 2], np.int64))}
    nodes += [
        oh.make_node("Transpose", [theta], [f"theta_t{s}"], perm=[0, 2, 1]),  # (batch, 3, 2)
        oh.make_node("MatMul", ["base", f"theta_t{s}"], [f"grid_flat{s}"]),  # (batch, T_h * T_w, 2)
        oh.make_node("Reshape", [f"grid_flat{s}", f"grid_shape_{batch}"], [f"grid{s}"]),
        oh.make_node("GridSample", [x, f"grid{s}"], [f"sampled{s}"], mode=GRID_MODES[interpolation],
                     padding_mode="zeros", align_corners=0),
        oh.make_node("Add", [f"sampled{s}", "border"], [f"resized{s}"]),
    ]
    return f"resized{s}"


def _fit_matrix(values: dict[str, Any]) -> np.ndarray:
    return np.array([[values["scale"], 0.0, values["left"]], [0.0, values["scale"], values["top"]]], dtype=np.float64)


def _theta(matrix: np.ndarray, src_w: int, src_h: int) -> np.ndarray:
    """`M` (source -> target, OpenCV pixel indices) -> the GridSample map of a target pixel index `(x, y, 1)`."""
    inverse = cv2.invertAffineTransform(np.asarray(matrix, np.float64))
    theta = np.empty((2, 3))
    theta[0] = [2 * inverse[0, 0] / src_w, 2 * inverse[0, 1] / src_w, (2 * inverse[0, 2] + 1) / src_w - 1]
    theta[1] = [2 * inverse[1, 0] / src_h, 2 * inverse[1, 1] / src_h, (2 * inverse[1, 2] + 1) / src_h - 1]
    return theta.astype(np.float32)


def _warp_nearest_index(matrix: np.ndarray, src_w: int, src_h: int, t_w: int, t_h: int, compute_dtype: str) -> np.ndarray:
    """The flat source index of each target pixel of `cv2.warpAffine` with `cv2.INTER_NEAREST`.

    The index image has the shape, the channels and the dtype of the frame of the CPU path, so OpenCV
    takes the same code path. Each value is a byte: rows and columns are two bytes each, in two
    calls; channel 2 is 1 only in the border. A border pixel gets the index `src_h * src_w`.
    """
    ys, xs = np.mgrid[0:src_h, 0:src_w]
    rows, outside = _nearest_source(ys, matrix, t_w, t_h, compute_dtype)
    columns, _ = _nearest_source(xs, matrix, t_w, t_h, compute_dtype)
    return np.where(outside, src_h * src_w, rows * src_w + columns)


# At module level: beartype decorates a nested function again on each call of its outer function.
def _nearest_source(values: np.ndarray, matrix: np.ndarray, t_w: int, t_h: int, compute_dtype: str) -> tuple[np.ndarray, np.ndarray]:
    planes = np.stack([values >> 8, values & 255, np.zeros_like(values)], axis=-1).astype(COMPUTE_DTYPES[compute_dtype])
    warped = cv2.warpAffine(planes, matrix, (t_w, t_h), flags=cv2.INTER_NEAREST,
                            borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 1)).astype(np.int64)
    return warped[..., 0] * 256 + warped[..., 1], warped[..., 2] == 1


def _const(name: str, value: np.ndarray | np.floating) -> onnx.TensorProto:
    return numpy_helper.from_array(np.asarray(value), name)

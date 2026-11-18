"""The preprocess graph: the resize step and the normalization of one sidecar as ONNX nodes.

`build_preprocess_graph` gives an ONNX model for one sidecar, one size, one precision, one source
size and one batch. Its input `frames` is a batch of host frames: uint8, `(batch, H, W, 3)`, BGR.
An `affine_crop` graph has a second input `theta`: float32, `(batch, 2, 3)`, one map for each item
of the batch, from `affine_crop_theta`. Its outputs are `tensor`, the model input that
`preprocess_image` gives for each frame (`(batch, 3, T_h, T_w)` in `input.dtype`), and `pixels`,
the resize result before the normalization: float32 on the 0-255 scale, in the channel order of
the model, with the pad or the border. The resize limit of `pre.resize.interpolation` applies to
`pixels` (`within_resize_limit`).

The graph has only ONNX nodes that run on `cuda` and `trt-rtx` with no CPU node (evidence of
ADR-J1HK): a `Cast` is the first node on the uint8 input; `Gather` changes the channel order;
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
    sidecar: SidecarModel, size: str, precision: str, src_w: int, src_h: int, batch: int
) -> onnx.ModelProto:
    """Return the preprocess graph of `preprocess_image` for `batch` frames of `src_w` x `src_h`.

    Implements: pre.resize.interpolation
    Implements: pre.resize.letterbox
    Implements: pre.resize.stretch
    Implements: pre.resize.fit
    Implements: pre.resize.affine_crop
    Implements: pre.resize.none
    Implements: pre.normalize

    The geometry comes from `resize_geometry`, as in `preprocess_image`. For `affine_crop`, the
    caller gives the input `theta` of the ROIs from `affine_crop_theta`. A configuration that the
    graph does not implement raises `PreprocessGraphRefusedError`.
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

    target_size = sidecar.size(size).target_size
    if resize.method == "affine_crop":  # the geometry needs the ROI: the caller gives it in `theta`
        t_h, t_w = (int(value) for value in target_size)
    else:
        geometry = resize_geometry(resize, target_size, src_w, src_h)
        t_h, t_w = geometry.input_size
    inits: list[onnx.TensorProto] = []
    inputs = [oh.make_tensor_value_info("frames", TensorProto.UINT8, [batch, src_h, src_w, 3])]
    nodes = [
        oh.make_node("Cast", ["frames"], ["cast"], to=TensorProto.FLOAT),  # TensorRT: uint8 only into a Cast
        oh.make_node("Transpose", ["cast"], ["bgr"], perm=[0, 3, 1, 2]),
    ]
    x = "bgr"
    if spec.color_format == "rgb":
        inits.append(_const("rgb_order", np.array([2, 1, 0], np.int64)))
        nodes.append(oh.make_node("Gather", ["bgr", "rgb_order"], ["rgb"], axis=1))
        x = "rgb"
    if resize.method in ("fit", "affine_crop"):
        pad_value = resize.crop_policy.pad_value if resize.method == "affine_crop" else resize.pad_value
        # in the order of color_format, cast through the compute dtype as the border of the CPU path
        border = np.array(border_values(pad_value)).astype(COMPUTE_DTYPES[str(resize.compute_dtype)]).astype(np.float32)
    if resize.method == "none":
        pass
    elif resize.method in ("letterbox", "stretch"):
        n_h, n_w = (geometry.values["n_h"], geometry.values["n_w"]) if resize.method == "letterbox" else (t_h, t_w)
        if resize.interpolation == "nearest":
            # cv2.INTER_NEAREST does not give floor(x * src_n / dst_n) at each size, so the tables come from the same call.
            columns = cv2.resize(np.arange(src_w, dtype=np.float32)[None], (n_w, 1), interpolation=cv2.INTER_NEAREST)[0]
            rows = cv2.resize(np.arange(src_h, dtype=np.float32)[:, None], (1, n_h), interpolation=cv2.INTER_NEAREST)[:, 0]
            inits += [_const("rows", rows.astype(np.int64)), _const("columns", columns.astype(np.int64))]
            nodes += [
                oh.make_node("Gather", [x, "rows"], ["picked_rows"], axis=2),
                oh.make_node("Gather", ["picked_rows", "columns"], ["resized"], axis=3),
            ]
        else:
            inits.append(_const("sizes", np.array([batch, 3, n_h, n_w], np.int64)))
            nodes.append(oh.make_node("Resize", [x, "", "", "sizes"], ["resized"], **RESIZE_MODES[str(resize.interpolation)]))
        x = "resized"
    elif resize.interpolation == "nearest":  # fit: the source index of each target pixel, src_h * src_w for the border
        matrix = _fit_matrix(geometry.values)
        index = _warp_nearest_index(matrix, src_w, src_h, t_w, t_h, str(resize.compute_dtype))
        inits += [
            _const("flat_shape", np.array([batch, 3, src_h * src_w], np.int64)),
            _const("border_pixel", np.broadcast_to(border.reshape(1, 3, 1), (batch, 3, 1)).copy()),
            _const("source_index", index),
        ]
        nodes += [
            oh.make_node("Reshape", [x, "flat_shape"], ["flat"]),
            oh.make_node("Concat", ["flat", "border_pixel"], ["flat_and_border"], axis=2),
            oh.make_node("Gather", ["flat_and_border", "source_index"], ["resized"], axis=2),
        ]
        x = "resized"
    else:  # fit or affine_crop: GridSample with a constant border
        if resize.method == "fit":
            inits.append(_const("theta", np.stack([_theta(_fit_matrix(geometry.values), src_w, src_h)] * batch)))
        else:
            inputs.append(oh.make_tensor_value_info("theta", TensorProto.FLOAT, [batch, 2, 3]))
        ys, xs = np.mgrid[0:t_h, 0:t_w]
        base = np.stack([xs.ravel(), ys.ravel(), np.ones(t_h * t_w)], axis=1).astype(np.float32)  # (T_h * T_w, 3)
        inits += [
            _const("base", base),
            _const("grid_shape", np.array([batch, t_h, t_w, 2], np.int64)),
            _const("border", border.reshape(1, 3, 1, 1)),
        ]
        nodes += [
            oh.make_node("Transpose", ["theta"], ["theta_t"], perm=[0, 2, 1]),  # (batch, 3, 2)
            oh.make_node("MatMul", ["base", "theta_t"], ["grid_flat"]),  # (batch, T_h * T_w, 2)
            oh.make_node("Reshape", ["grid_flat", "grid_shape"], ["grid"]),
            oh.make_node("Sub", [x, "border"], ["shifted"]),
            oh.make_node("GridSample", ["shifted", "grid"], ["sampled"], mode=GRID_MODES[str(resize.interpolation)],
                         padding_mode="zeros", align_corners=0),
            oh.make_node("Add", ["sampled", "border"], ["resized"]),
        ]
        x = "resized"
    if resize.method != "none" and resize.compute_dtype == "uint8":  # half up, as OpenCV
        inits += [_const("half", np.float32(0.5)), _const("low", np.float32(0)), _const("high", np.float32(255))]
        nodes += [
            oh.make_node("Add", [x, "half"], ["plus_half"]),
            oh.make_node("Floor", ["plus_half"], ["rounded"]),
            oh.make_node("Clip", ["rounded", "low", "high"], ["clipped"]),
        ]
        x = "clipped"
    if resize.method == "letterbox":  # pad `x - v` with zeros, then add `v`: one value for each channel
        top, left = geometry.values["top"], geometry.values["left"]
        pads = [0, 0, top, left, 0, 0, t_h - n_h - top, t_w - n_w - left]
        # in the order of color_format, cast through the compute dtype as the canvas fill of the CPU path
        pad = np.array(border_values(resize.pad_value)).astype(COMPUTE_DTYPES[str(resize.compute_dtype)]).astype(np.float32).reshape(1, 3, 1, 1)
        inits += [_const("pads", np.array(pads, np.int64)), _const("pad", pad)]
        nodes += [
            oh.make_node("Sub", [x, "pad"], ["unpadded"]),
            oh.make_node("Pad", ["unpadded", "pads"], ["padded"], mode="constant"),
            oh.make_node("Add", ["padded", "pad"], ["canvas"]),
        ]
        x = "canvas"
    nodes.append(oh.make_node("Identity", [x], ["pixels"]))
    if normalization == "imagenet":
        mean, std = np.array(IMAGENET_MEAN_RGB, np.float32), np.array(IMAGENET_STD_RGB, np.float32)
        if spec.color_format == "bgr":
            mean, std = mean[::-1], std[::-1]
        inits += [_const("mean", mean.reshape(1, 3, 1, 1)), _const("std", std.reshape(1, 3, 1, 1))]
        nodes += [oh.make_node("Sub", [x, "mean"], ["centered"]), oh.make_node("Div", ["centered", "std"], ["normalized"])]
        x = "normalized"
    nodes.append(oh.make_node("Cast", [x], ["tensor"], to=TENSOR_TYPES[dtype]))

    outputs = [
        oh.make_tensor_value_info("tensor", TENSOR_TYPES[dtype], [batch, 3, t_h, t_w]),
        oh.make_tensor_value_info("pixels", TensorProto.FLOAT, [batch, 3, t_h, t_w]),
    ]
    model = oh.make_model(
        oh.make_graph(nodes, "preprocess", inputs, outputs, inits), opset_imports=[oh.make_opsetid("", OPSET)]
    )
    model.ir_version = IR_VERSION
    return model


def affine_crop_theta(sidecar: SidecarModel, size: str, src_w: int, src_h: int, rois: Sequence[Sequence[Any]]) -> np.ndarray:
    """Return the input `theta` of an `affine_crop` graph: float32, `(len(rois), 2, 3)`.

    Implements: pre.resize.affine_crop

    Each ROI is `(c_x, c_y, w, h, rotation)` in source pixels, as `preprocess_image` takes it (for a
    box, `roi_from_box`). The matrix `M` comes from `resize_geometry`, as in the CPU path. Item `k`
    of the batch warps the frame `k` with the ROI `k`: for some ROIs on one frame, repeat the frame.
    """
    target_size = sidecar.size(size).target_size
    matrices = [resize_geometry(sidecar.input.resize, target_size, src_w, src_h, roi).values["matrix"] for roi in rois]
    return np.stack([_theta(matrix, src_w, src_h) for matrix in matrices])


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

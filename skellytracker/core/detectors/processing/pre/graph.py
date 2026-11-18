"""The preprocess graph: the resize step and the normalization of one sidecar as ONNX nodes.

`build_preprocess_graph` gives an ONNX model for one sidecar, one size, one precision, one source
size and one batch. Its input `frames` is a batch of host frames: uint8, `(batch, H, W, 3)`, BGR.
Its outputs are `tensor`, the model input that `preprocess_image` gives for each frame
(`(batch, 3, T_h, T_w)` in `input.dtype`), and `pixels`, the resize result before the
normalization: float32 on the 0-255 scale, in the channel order of the model, with the pad. The
resize limit of `pre.resize.interpolation` applies to `pixels` (`within_resize_limit`).

The graph has only ONNX nodes that run on `cuda` and `trt-rtx` with no CPU node (evidence of
ADR-J1HK): a `Cast` is the first node on the uint8 input; `Gather` changes the channel order;
`Resize` has the attributes of `RESIZE_MODES` for `linear` and `cubic`; for `nearest`, two `Gather`
nodes take the rows and the columns that `cv2.resize` with `cv2.INTER_NEAREST` takes for an index
ramp, so the pixels are equal to the CPU path; a `uint8` result is `Clip(Floor(x + 0.5), 0, 255)`,
because ONNX `Round` rounds half to even and OpenCV rounds half up; `Pad` makes the letterbox pad.

The graph does `letterbox` and `stretch` with `linear`, `cubic` and `nearest`, both compute dtypes,
the normalizations `none` and `imagenet`, and the input dtypes `float32` and `float16`. Each other
configuration raises `PreprocessGraphRefusedError`: the caller then uses `preprocess_image`.
"""
from __future__ import annotations

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
INTERPOLATIONS = ("linear", "cubic", "nearest")  # nearest: two Gather nodes with index tables of cv2.resize
METHODS = ("letterbox", "stretch")
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
    Implements: pre.normalize

    The geometry comes from `resize_geometry`, as in `preprocess_image`. A configuration that the
    graph does not implement raises `PreprocessGraphRefusedError`.
    """
    spec, resize = sidecar.input, sidecar.input.resize
    if precision not in spec.dtype:
        raise ValueError(f"no precision {precision!r}; input.dtype has {list(spec.dtype)}")
    if batch < 1:
        raise ValueError(f"the batch must be 1 or more, not {batch}")
    normalization, dtype = spec.normalization_for(precision), spec.dtype[precision]
    if resize.method not in METHODS:
        raise PreprocessGraphRefusedError(f"the preprocess graph has no resize method {resize.method!r}")
    if resize.interpolation not in INTERPOLATIONS:
        raise PreprocessGraphRefusedError(f"the preprocess graph has no interpolation {resize.interpolation!r}")
    if normalization not in NORMALIZATIONS:
        raise PreprocessGraphRefusedError(f"the preprocess graph has no normalization {normalization!r}")
    if dtype not in TENSOR_TYPES:
        raise PreprocessGraphRefusedError(f"the preprocess graph has no input dtype {dtype!r}")

    geometry = resize_geometry(resize, sidecar.size(size).target_size, src_w, src_h)
    t_h, t_w = geometry.input_size
    n_h, n_w = (geometry.values["n_h"], geometry.values["n_w"]) if resize.method == "letterbox" else (t_h, t_w)
    inits: list[onnx.TensorProto] = []
    nodes = [
        oh.make_node("Cast", ["frames"], ["cast"], to=TensorProto.FLOAT),  # TensorRT: uint8 only into a Cast
        oh.make_node("Transpose", ["cast"], ["bgr"], perm=[0, 3, 1, 2]),
    ]
    x = "bgr"
    if spec.color_format == "rgb":
        inits.append(_const("rgb_order", np.array([2, 1, 0], np.int64)))
        nodes.append(oh.make_node("Gather", ["bgr", "rgb_order"], ["rgb"], axis=1))
        x = "rgb"
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
    if resize.compute_dtype == "uint8":  # half up, as OpenCV
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

    inputs = [oh.make_tensor_value_info("frames", TensorProto.UINT8, [batch, src_h, src_w, 3])]
    outputs = [
        oh.make_tensor_value_info("tensor", TENSOR_TYPES[dtype], [batch, 3, t_h, t_w]),
        oh.make_tensor_value_info("pixels", TensorProto.FLOAT, [batch, 3, t_h, t_w]),
    ]
    model = oh.make_model(
        oh.make_graph(nodes, "preprocess", inputs, outputs, inits), opset_imports=[oh.make_opsetid("", OPSET)]
    )
    model.ir_version = IR_VERSION
    return model


def _const(name: str, value: np.ndarray | np.floating) -> onnx.TensorProto:
    return numpy_helper.from_array(np.asarray(value), name)

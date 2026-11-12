"""Reference implementation of the sidecar section ``pre.resize.letterbox``.

Section ID: ``pre.resize.letterbox`` (``specs/model-sidecar/pre/resize-letterbox.md``).
This module has the forward letterbox and its Inverse (points and boxes).

Source commit: OpenMMLab-Exporter 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278. The host code is the
same at 18320f4e51660fe0cb9c546441eb9be09d53f339. The host functions are:

- OpenMMLab-Exporter onnx_runtime/preprocess.py::round_size at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278
- OpenMMLab-Exporter onnx_runtime/preprocess.py::letterbox at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278
- OpenMMLab-Exporter onnx_runtime/unprojection.py::letterbox_geometry at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278
- OpenMMLab-Exporter onnx_runtime/unprojection.py::inverse_points at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278
- OpenMMLab-Exporter onnx_runtime/unprojection.py::inverse_boxes at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278

Vector results: ``vectors/pre.resize.letterbox.yaml`` of skellytracker
8351b7f8c20c8db74eb3e547478970e4dceb0308. All 52 cases pass (26 ``run``, 26 ``inverse``).
``make_vectors.py fill`` printed no problems, and the filled file is byte-identical to the spec
file. The formula module of the section agrees within the tolerance 0.0001. The host functions
give the same results on all 52 cases.

Parity: unchanged. The yolox-person parity check ran with this module in place of the host code
(OpenMMLab-Exporter ADR-3NNK (decisions/scripts/yolox_person_reference_swap.py at 53a48480d0b715f9b726963bce002ddb503b050b)). That run used this file before this note line changed (SHA-256 babce8c2a9dc2f85869df94ad8e4288452489827130cf0f3905da319d9cbfd80).

Imported section modules: none. Fixtures: none. The forward function gets the OpenCV
interpolation flag from its caller. Section ``pre.resize.interpolation`` maps
``input.resize.interpolation`` to that flag.
"""

from __future__ import annotations

import math

import cv2
import numpy as np

PAD_POSITIONS = ("top_left", "center")
ROUNDINGS = ("half_even", "half_up")
DEFAULT_PAD_VALUE = 114


def round_size(value, rounding):
    """Round one scaled length with ``input.resize.rounding`` (section ``pre.resize.letterbox``).

    ``half_even`` is Python ``round``. ``half_up`` is ``floor(x + 0.5)``. The function does not cut
    the value with ``int()``.

    Source: OpenMMLab-Exporter onnx_runtime/preprocess.py::round_size at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    if rounding == "half_even":
        return int(round(value))
    if rounding == "half_up":
        return int(math.floor(value + 0.5))
    raise ValueError(f"V-pre.resize.letterbox-1: unsupported rounding {rounding!r}")


def run(params, input):
    """Return the letterbox geometry ``{n_w, n_h, left, top}`` (section ``pre.resize.letterbox``).

    ``params`` holds ``target_size`` ``[T_h, T_w]``, ``pad_position`` and ``rounding``. ``input``
    holds ``src_w`` and ``src_h``, the source size in pixels. The steps are:
    ``s = min(T_w / src_w, T_h / src_h)``, ``n = max(1, R(src * s))`` and the pad offsets of
    ``pad_position``. For ``center``, an odd remainder goes to the right and the bottom.

    Source: OpenMMLab-Exporter onnx_runtime/unprojection.py::letterbox_geometry at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278 (the arithmetic of
    onnx_runtime/preprocess.py::letterbox at the same commit).
    """
    target_h, target_w = (int(value) for value in params["target_size"])
    src_w, src_h = int(input["src_w"]), int(input["src_h"])
    if target_h <= 0 or target_w <= 0:
        raise ValueError(f"target_size must be positive, not {[target_h, target_w]!r}")
    if src_w <= 0 or src_h <= 0:
        raise ValueError(f"the source size must be positive, not {src_w} x {src_h}")
    rounding = params.get("rounding")
    position = params.get("pad_position")
    if rounding not in ROUNDINGS:
        raise ValueError(f"V-pre.resize.letterbox-1: unsupported rounding {rounding!r}")
    if position not in PAD_POSITIONS:
        raise ValueError(f"V-pre.resize.letterbox-1: unsupported pad_position {position!r}")
    scale = min(target_w / src_w, target_h / src_h)
    n_w = max(1, round_size(src_w * scale, rounding))
    n_h = max(1, round_size(src_h * scale, rounding))
    if position == "top_left":
        left, top = 0, 0
    else:
        left, top = (target_w - n_w) // 2, (target_h - n_h) // 2
    return {"n_w": n_w, "n_h": n_h, "left": left, "top": top}


def letterbox(image, params, interpolation):
    """Letterbox an ``(H, W, 3)`` image and return ``(canvas, geometry)`` (section ``pre.resize.letterbox``).

    ``params`` holds ``target_size``, ``pad_position``, ``rounding`` and the optional
    ``pad_value``. The default ``pad_value`` is 114. An array ``pad_value`` gives one value for each
    channel in the order of ``input.color_format``. Thus the image must have that channel order.
    ``interpolation`` is the OpenCV flag of section ``pre.resize.interpolation``, for example
    ``cv2.INTER_LINEAR`` for ``linear``. The canvas has the dtype of the image. Section
    ``pre.resize.interpolation`` (``compute_dtype``) sets that dtype before this call.
    ``geometry`` is the result of :func:`run`.

    Source: OpenMMLab-Exporter onnx_runtime/preprocess.py::letterbox at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    image = np.asarray(image)
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"the image must have shape (H, W, 3), not {image.shape}")
    src_h, src_w = image.shape[:2]
    geometry = run(params, {"src_w": src_w, "src_h": src_h})
    pad = np.asarray(params.get("pad_value", DEFAULT_PAD_VALUE), dtype=np.float64)
    if pad.shape not in ((), (3,)):
        raise ValueError(f"pad_value must be a number or 3 numbers, not {pad.tolist()!r}")
    target_h, target_w = (int(value) for value in params["target_size"])
    n_w, n_h, left, top = geometry["n_w"], geometry["n_h"], geometry["left"], geometry["top"]
    canvas = np.empty((target_h, target_w, 3), dtype=image.dtype)
    canvas[...] = pad
    canvas[top : top + n_h, left : left + n_w] = cv2.resize(
        image, (n_w, n_h), interpolation=interpolation
    )
    return canvas, geometry


def inverse_axes(x, y, geometry, src_w, src_h):
    """Map model-input x and y to source pixels, one axis at a time (section ``pre.resize.letterbox``, Inverse).

    ``x_src = (x - left) * (src_w / n_w)`` and ``y_src = (y - top) * (src_h / n_h)``, with the
    rounded ``n_w`` and ``n_h`` and the pad offsets of :func:`run`. The function adds no ``0.5``
    offset. The order of the operations is the order of the host decoder.

    Source: OpenMMLab-Exporter onnx_runtime/unprojection.py::_inverse_axes at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278 (the ``letterbox`` branch).
    """
    left, top, n_w, n_h = geometry["left"], geometry["top"], geometry["n_w"], geometry["n_h"]
    return (x - left) * (src_w / n_w), (y - top) * (src_h / n_h)


def inverse_points(model_xy, geometry, src_w, src_h):
    """Map ``(..., 2)`` model-input positions to source pixels (section ``pre.resize.letterbox``, Inverse).

    The result is float64. ``geometry`` is the result of :func:`run` for the source size
    ``src_w`` x ``src_h``.

    Source: OpenMMLab-Exporter onnx_runtime/unprojection.py::inverse_points at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    points = np.asarray(model_xy, dtype=np.float64)
    if points.shape[-1:] != (2,):
        raise ValueError(f"positions must have shape (..., 2), not {points.shape}")
    x, y = inverse_axes(points[..., 0], points[..., 1], geometry, src_w, src_h)
    return np.stack([x, y], axis=-1)


def inverse_boxes(model_xyxy, geometry, src_w, src_h):
    """Map ``(..., 4)`` xyxy model-input boxes to source pixels (section ``pre.resize.letterbox``, Inverse).

    A float32 or float64 input keeps its dtype. Another dtype gives float64. The function does not
    clamp the boxes. The clamp is a step of ``post.unprojection``.

    Source: OpenMMLab-Exporter onnx_runtime/unprojection.py::inverse_boxes at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    boxes = np.asarray(model_xyxy)
    dtype = boxes.dtype if boxes.dtype in (np.float32, np.float64) else np.float64
    boxes = np.array(boxes, dtype=dtype, copy=True)
    if boxes.shape[-1:] != (4,):
        raise ValueError(f"boxes must have shape (..., 4), not {boxes.shape}")
    x, y = inverse_axes(boxes[..., 0::2], boxes[..., 1::2], geometry, src_w, src_h)
    boxes[..., 0::2], boxes[..., 1::2] = x, y
    return boxes


def inverse(params, input):
    """Return ``{source_xy}`` for one model-input position (section ``pre.resize.letterbox``, Inverse).

    ``input`` holds ``src_w``, ``src_h`` and ``model_xy``. The geometry is the result of
    :func:`run` for the same ``params`` and source size.

    Source: OpenMMLab-Exporter onnx_runtime/unprojection.py::inverse_points at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    geometry = run(params, input)
    source = inverse_points(input["model_xy"], geometry, int(input["src_w"]), int(input["src_h"]))
    return {"source_xy": [float(value) for value in source]}

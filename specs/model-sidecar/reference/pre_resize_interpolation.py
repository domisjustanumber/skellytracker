"""Reference implementation of the sidecar section pre.resize.interpolation.

Section ID: pre.resize.interpolation (specs/model-sidecar/pre/interpolation.md).
Source commit: OpenMMLab-Exporter onnx_runtime/preprocess.py::letterbox and
onnx_runtime/preprocess.py::affine_person_crop at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
The code is unchanged at 18320f4e51660fe0cb9c546441eb9be09d53f339.
The host constants are _INTERPOLATION and COMPUTE_DTYPES of the same file.
Imported section modules: none. Fixtures: none.
Vector results: the vector file has 2 cases. Both are validator cases (function: none).
make_vectors.py fill kept both expect values. run gives the same failed list for both cases.
The file has no numeric case.
Parity: yolox-person: unchanged. Its parity check ran with this module in place of the host code
(OpenMMLab-Exporter ADR-3NNK (decisions/scripts/yolox_person_reference_swap.py at 53a48480d0b715f9b726963bce002ddb503b050b)). That run used this file before this note changed (SHA-256 5c3efe96de6aeaf1494a34f3780cb8f7cd924d0d899ca851080ba54c1fa70dc4). rtmw-wholebody133: to run. Its intake has blocking rows, so it has no parity run of the model.

The module has one function for each part of the section:

- interpolation_flag: the OpenCV filter of input.resize.interpolation.
- compute_dtype: the dtype of input.resize.compute_dtype.
- to_compute_dtype: the cast of the 8-bit image before the resize and the pad.
- pixel_centre: the pixel-centre convention of the OpenCV call of each resize method.
- failed_rules: the validation rule V-pre.resize.interpolation-1.

The resize methods (letterbox, stretch, fit, affine_person_crop) make the OpenCV call. Their
modules call these functions. This module does not resize an image.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import cv2
import numpy as np

SECTION = "pre.resize.interpolation"
RULE_COMPUTE_DTYPE = "V-pre.resize.interpolation-1"

DEFAULT_INTERPOLATION = "linear"
INTERPOLATION_FLAGS = {
    "linear": cv2.INTER_LINEAR,
    "area": cv2.INTER_AREA,
    "cubic": cv2.INTER_CUBIC,
    "nearest": cv2.INTER_NEAREST,
}

DEFAULT_COMPUTE_DTYPE = "uint8"
COMPUTE_DTYPES = {"uint8": np.uint8, "float32": np.float32}

# The OpenCV call of each method that resizes the image, and the centre of pixel i (i + offset).
RESIZE_CALLS = {
    "letterbox": "cv2.resize",
    "stretch": "cv2.resize",
    "fit": "cv2.warpAffine",
    "affine_person_crop": "cv2.warpAffine",
}
PIXEL_CENTRE_OFFSETS = {"cv2.resize": 0.5, "cv2.warpAffine": 0.0}


def interpolation_flag(resize: Mapping[str, Any]) -> int:
    """Return the OpenCV filter constant of ``input.resize.interpolation``.

    Section pre.resize.interpolation, table "Interpolation values". The default is ``linear``.
    The filter has no antialias. A value that is not in the table gives a ValueError.
    Source: OpenMMLab-Exporter onnx_runtime/preprocess.py::letterbox at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    name = resize.get("interpolation", DEFAULT_INTERPOLATION)
    if not isinstance(name, str) or name not in INTERPOLATION_FLAGS:
        raise ValueError(f"unsupported interpolation: {name!r}")
    return INTERPOLATION_FLAGS[name]


def compute_dtype(resize: Mapping[str, Any]) -> type:
    """Return the NumPy dtype of ``input.resize.compute_dtype``.

    Section pre.resize.interpolation, heading "Compute dtype". The default is ``uint8``. A value
    other than ``uint8`` or ``float32`` gives a ValueError with the rule ID
    V-pre.resize.interpolation-1.
    Source: OpenMMLab-Exporter onnx_runtime/preprocess.py::affine_person_crop at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    name = resize.get("compute_dtype", DEFAULT_COMPUTE_DTYPE)
    if not isinstance(name, str) or name not in COMPUTE_DTYPES:
        raise ValueError(f"{RULE_COMPUTE_DTYPE}: unsupported compute_dtype: {name!r}")
    return COMPUTE_DTYPES[name]


def to_compute_dtype(image: np.ndarray, resize: Mapping[str, Any]) -> np.ndarray:
    """Return the 8-bit image in the compute dtype, before the resize and the pad.

    Section pre.resize.interpolation, heading "Compute dtype". With ``uint8``, the image does not
    change. With ``float32``, the cast keeps the 0-255 scale. The resize and the pad then run in
    this dtype, with no round and no clamp. The pad value and the border of the warp have this
    dtype too.
    Source: OpenMMLab-Exporter onnx_runtime/preprocess.py::affine_person_crop at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    return np.ascontiguousarray(image, dtype=compute_dtype(resize))


def pixel_centre(method: str, index: float) -> float:
    """Return the coordinate of the centre of pixel ``index`` for a resize method.

    Section pre.resize.interpolation, heading "Pixel centres" (decision G79P). ``letterbox`` and
    ``stretch`` call ``cv2.resize``: pixel i covers [i, i + 1) and its centre is i + 0.5.
    ``fit`` and ``affine_person_crop`` call ``cv2.warpAffine``: the coordinate is the pixel index
    and the centre of pixel i is i. ``none`` makes no resize call, so it gives a ValueError.
    No step adds or removes a 0.5 offset between the forward step and the Inverse.
    Source: the OpenCV calls of OpenMMLab-Exporter onnx_runtime/preprocess.py::letterbox
    (cv2.resize) and onnx_runtime/preprocess.py::affine_person_crop (cv2.warpAffine) at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278. The host has no stretch or fit. Their rows come
    from the table of the section.
    """
    if method not in RESIZE_CALLS:
        raise ValueError(f"the resize method {method!r} has no resize call")
    return index + PIXEL_CENTRE_OFFSETS[RESIZE_CALLS[method]]


def failed_rules(resize: Mapping[str, Any]) -> list[str]:
    """Return the rules of this section that the ``input.resize`` block fails.

    Section pre.resize.interpolation, rule V-pre.resize.interpolation-1: if
    ``compute_dtype`` is present, it must be ``uint8`` or ``float32``.
    Source: the compute_dtype check of OpenMMLab-Exporter
    onnx_runtime/preprocess.py::affine_person_crop at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    if "compute_dtype" not in resize:
        return []
    try:
        compute_dtype(resize)
    except ValueError:
        return [RULE_COMPUTE_DTYPE]
    return []


def run(params: Mapping[str, Any], input: Mapping[str, Any]) -> dict[str, Any]:
    """Return ``{"failed": [...]}``: the rules of this section that ``input["sidecar"]`` fails.

    Section pre.resize.interpolation, heading "Validation rules". The rule reads only the
    shared block ``input.resize`` of the sidecar. A sidecar with no ``input.resize`` fails no
    rule of this section. ``params`` is not used.
    Source: the compute_dtype check of OpenMMLab-Exporter
    onnx_runtime/preprocess.py::affine_person_crop at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    sidecar = input.get("sidecar") or {}
    resize = (sidecar.get("input") or {}).get("resize") or {}
    return {"failed": failed_rules(resize)}

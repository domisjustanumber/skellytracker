"""The resize filter, the compute dtype and the border of a resize (section `pre.resize.interpolation`).

The resize methods make the OpenCV call. This module gives them the filter constant, the image in
the compute dtype and the value of each channel of the pad or the border.
"""
from __future__ import annotations

from collections.abc import Sequence

import cv2
import numpy as np

INTERPOLATION_FLAGS = {
    "linear": cv2.INTER_LINEAR,
    "area": cv2.INTER_AREA,
    "cubic": cv2.INTER_CUBIC,
    "nearest": cv2.INTER_NEAREST,
}
COMPUTE_DTYPES = {"uint8": np.uint8, "float32": np.float32}


def interpolation_flag(interpolation: str) -> int:
    """Return the OpenCV filter constant of `input.resize.interpolation`. The filter has no antialias.

    Implements: pre.resize.interpolation
    """
    if interpolation not in INTERPOLATION_FLAGS:
        raise ValueError(f"unsupported interpolation: {interpolation!r}")
    return INTERPOLATION_FLAGS[interpolation]


def to_compute_dtype(image: np.ndarray, compute_dtype: str) -> np.ndarray:
    """Return the 8-bit host frame in `input.resize.compute_dtype`, before the resize and the pad.

    Implements: pre.resize.interpolation

    The frame is an 8-bit, 3-channel image in HWC layout. With `uint8`, it does not change. With
    `float32`, the cast keeps the 0-255 scale. The resize and the pad then run in this dtype, with
    no round and no clamp.
    """
    if compute_dtype not in COMPUTE_DTYPES:
        raise ValueError(f"unsupported compute_dtype: {compute_dtype!r}")
    if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"the frame must be uint8 with the shape (H, W, 3), not {image.dtype} {image.shape}")
    return np.ascontiguousarray(image, dtype=COMPUTE_DTYPES[compute_dtype])


def border_values(pad_value: int | float | Sequence[int | float]) -> tuple[float, float, float]:
    """Return the pad or border value of each of the 3 channels.

    Implements: pre.resize.interpolation

    A scalar `s` gives `(s, s, s)`: OpenCV fills only channel 0 from a scalar border. An array
    gives one value for each channel, in the order of the array.
    """
    if isinstance(pad_value, bool):
        raise ValueError("pad_value must be a number or 3 numbers")
    if isinstance(pad_value, (int, float)):
        return (float(pad_value),) * 3
    values = tuple(float(value) for value in pad_value)
    if len(values) != 3:
        raise ValueError(f"a pad_value array must have 3 values, not {len(values)}")
    return values

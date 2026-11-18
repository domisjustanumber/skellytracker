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
# The resize limit of each compute dtype: the largest absolute difference of one value, 0-255 scale.
RESIZE_LIMITS = {"uint8": 1.0, "float32": 0.05}


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


def within_resize_limit(reference: np.ndarray, result: np.ndarray, compute_dtype: str) -> tuple[float, bool]:
    """Return `(max_difference, within_limit)` of a resize result against the reference result.

    Implements: pre.resize.interpolation

    `reference` is the output of the OpenCV call of the method, in `compute_dtype`. `result` is the
    result of an other implementation for the same host frame and geometry, of any dtype. The whole
    result counts, also the pad. Both convert to float64 (a `float32` result from its float32
    value). With `uint8`, each value must be an integer from 0 to 255 and differ by at most 1.
    With `float32`, each value must be finite and differ by at most 0.05. A NaN gives a NaN
    `max_difference`. A shape that is not the reference shape, and an empty result, raise a
    `ValueError`.
    """
    if compute_dtype not in COMPUTE_DTYPES:
        raise ValueError(f"unsupported compute_dtype: {compute_dtype!r}")
    expected = np.asarray(reference, dtype=COMPUTE_DTYPES[compute_dtype]).astype(np.float64)
    # A uint8 result can be a float tensor, so its values are checked before a cast.
    given = np.asarray(result, dtype=np.float64 if compute_dtype == "uint8" else np.float32).astype(np.float64)
    if given.shape != expected.shape:
        raise ValueError(f"the result has the shape {given.shape}, not {expected.shape}")
    if given.size == 0:
        raise ValueError("an empty image has no resize result")
    difference = float(np.max(np.abs(given - expected)))
    if compute_dtype == "uint8":
        in_range = bool(np.all((given == np.floor(given)) & (given >= 0) & (given <= 255)))
    else:
        in_range = bool(np.all(np.isfinite(given)))
    return difference, in_range and difference <= RESIZE_LIMITS[compute_dtype]


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

"""The stretch resize and its Inverse (section `pre.resize.stretch`)."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import cv2
import numpy as np


def stretch_geometry(src_w: int, src_h: int, target_size: Sequence[int]) -> dict[str, Any]:
    """Return `{dst_w, dst_h, scale_x, scale_y}`: the output size and the scale factor of each axis.

    Implements: pre.resize.stretch
    """
    target_h, target_w = (int(value) for value in target_size)
    if target_h <= 0 or target_w <= 0 or src_w <= 0 or src_h <= 0:
        raise ValueError(f"the sizes must be positive: target {[target_h, target_w]}, source {src_w} x {src_h}")
    return {"dst_w": target_w, "dst_h": target_h, "scale_x": target_w / src_w, "scale_y": target_h / src_h}


def stretch(image: np.ndarray, target_size: Sequence[int], interpolation: int) -> tuple[np.ndarray, dict[str, Any]]:
    """Resize an image to `target_size` with no pad and no crop. Return the image and the geometry.

    Implements: pre.resize.stretch
    """
    src_h, src_w = image.shape[:2]
    geometry = stretch_geometry(src_w, src_h, target_size)
    return cv2.resize(image, (geometry["dst_w"], geometry["dst_h"]), interpolation=interpolation), geometry


def inverse_points(model_xy: Any, target_size: Sequence[int], src_w: int, src_h: int) -> np.ndarray:
    """Map `(..., 2)` model-input positions to source pixels, in float64.

    Implements: pre.resize.stretch

    `x_src = x * src_w / T_w` and `y_src = y * src_h / T_h`. The function adds no `0.5` offset.
    """
    points = np.asarray(model_xy, dtype=np.float64)
    target_h, target_w = (int(value) for value in target_size)
    return np.stack([points[..., 0] * src_w / target_w, points[..., 1] * src_h / target_h], axis=-1)

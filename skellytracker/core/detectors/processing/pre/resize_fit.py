"""The fit resize and its Inverse (section `pre.resize.fit`)."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import cv2
import numpy as np


def fit_geometry(src_w: int, src_h: int, target_size: Sequence[int]) -> dict[str, float]:
    """Return `{scale, left, top}` of the warp matrix `[[s, 0, left], [0, s, top]]`, in float64.

    Implements: pre.resize.fit

    The function does not round the scale or the offsets.
    """
    target_h, target_w = (int(value) for value in target_size)
    if target_h <= 0 or target_w <= 0 or src_w <= 0 or src_h <= 0:
        raise ValueError(f"the sizes must be positive: target {[target_h, target_w]}, source {src_w} x {src_h}")
    scale = min(target_w / src_w, target_h / src_h)
    return {"scale": scale, "left": (target_w - src_w * scale) / 2, "top": (target_h - src_h * scale) / 2}


def fit(
    image: np.ndarray, target_size: Sequence[int], pad_value: Sequence[float], interpolation: int
) -> tuple[np.ndarray, dict[str, float]]:
    """Warp the whole `(H, W, 3)` image onto the `target_size` canvas. Return the canvas and the geometry.

    Implements: pre.resize.fit

    `pad_value` holds one border value for each channel, in the channel order of the image. It has
    no default. `interpolation` is the OpenCV filter constant. The canvas has the dtype of the image.
    """
    src_h, src_w = image.shape[:2]
    geometry = fit_geometry(src_w, src_h, target_size)
    scale, left, top = geometry["scale"], geometry["left"], geometry["top"]
    border = tuple(float(value) for value in pad_value)
    if len(border) != 3:
        raise ValueError("pad_value must have one value for each channel")
    canvas = cv2.warpAffine(
        image,
        np.array([[scale, 0.0, left], [0.0, scale, top]], dtype=np.float64),
        (int(target_size[1]), int(target_size[0])),
        flags=interpolation,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border,
    )
    return canvas, geometry


def inverse_points(model_xy: Any, geometry: dict[str, float]) -> np.ndarray:
    """Map `(..., 2)` model-input positions to source pixels, in float64.

    Implements: pre.resize.fit

    `x_src = (x - left) / s` and `y_src = (y - top) / s`. The function adds no `0.5` offset.
    """
    points = np.asarray(model_xy, dtype=np.float64)
    x = (points[..., 0] - geometry["left"]) / geometry["scale"]
    y = (points[..., 1] - geometry["top"]) / geometry["scale"]
    return np.stack([x, y], axis=-1)

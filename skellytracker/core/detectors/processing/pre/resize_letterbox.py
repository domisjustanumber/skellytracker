"""The letterbox resize and its Inverse (section `pre.resize.letterbox`)."""
from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import cv2
import numpy as np


def round_size(value: float, rounding: str) -> int:
    """Round one scaled length with `input.resize.rounding`. The function does not cut the value.

    Implements: pre.resize.letterbox
    """
    if rounding == "half_even":
        return int(round(value))
    if rounding == "half_up":
        return int(math.floor(value + 0.5))
    raise ValueError(f"unsupported rounding: {rounding!r}")


def letterbox_geometry(
    src_w: int, src_h: int, target_size: Sequence[int], pad_position: str, rounding: str
) -> dict[str, int]:
    """Return `{n_w, n_h, left, top}`: the resized size and its place on the `target_size` canvas.

    Implements: pre.resize.letterbox

    `s = min(T_w / src_w, T_h / src_h)` and `n = max(1, R(src * s))`, in float64. For `center`, an
    odd remainder goes to the right and the bottom.
    """
    target_h, target_w = (int(value) for value in target_size)
    if target_h <= 0 or target_w <= 0 or src_w <= 0 or src_h <= 0:
        raise ValueError(f"the sizes must be positive: target {[target_h, target_w]}, source {src_w} x {src_h}")
    if pad_position not in ("top_left", "center"):
        raise ValueError(f"unsupported pad_position: {pad_position!r}")
    scale = min(target_w / src_w, target_h / src_h)
    n_w = max(1, round_size(src_w * scale, rounding))
    n_h = max(1, round_size(src_h * scale, rounding))
    left, top = (0, 0) if pad_position == "top_left" else ((target_w - n_w) // 2, (target_h - n_h) // 2)
    return {"n_w": n_w, "n_h": n_h, "left": left, "top": top}


def letterbox(
    image: np.ndarray,
    target_size: Sequence[int],
    pad_position: str,
    rounding: str,
    pad_value: Sequence[float],
    interpolation: int,
) -> tuple[np.ndarray, dict[str, int]]:
    """Letterbox an `(H, W, 3)` image. Return the canvas and the geometry.

    Implements: pre.resize.letterbox

    `pad_value` holds one value for each channel, in the channel order of the image.
    `interpolation` is the OpenCV filter constant. The canvas has the dtype of the image.
    """
    src_h, src_w = image.shape[:2]
    geometry = letterbox_geometry(src_w, src_h, target_size, pad_position, rounding)
    n_w, n_h, left, top = geometry["n_w"], geometry["n_h"], geometry["left"], geometry["top"]
    canvas = np.empty((int(target_size[0]), int(target_size[1]), 3), dtype=image.dtype)
    canvas[...] = np.asarray(pad_value, dtype=np.float64)
    canvas[top : top + n_h, left : left + n_w] = cv2.resize(image, (n_w, n_h), interpolation=interpolation)
    return canvas, geometry


def inverse_points(model_xy: Any, geometry: dict[str, int], src_w: int, src_h: int) -> np.ndarray:
    """Map `(..., 2)` model-input positions to source pixels, in float64.

    Implements: pre.resize.letterbox

    `x_src = (x - left) * (src_w / n_w)` and `y_src = (y - top) * (src_h / n_h)`, with the rounded
    `n_w` and `n_h`. The function adds no `0.5` offset.
    """
    points = np.asarray(model_xy, dtype=np.float64)
    x = (points[..., 0] - geometry["left"]) * (src_w / geometry["n_w"])
    y = (points[..., 1] - geometry["top"]) * (src_h / geometry["n_h"])
    return np.stack([x, y], axis=-1)

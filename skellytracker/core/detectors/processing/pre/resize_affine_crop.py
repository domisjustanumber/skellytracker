"""The affine crop of an ROI and its Inverse (section `pre.resize.affine_crop`).

The ROI and the warp points use the float32 steps of the section. `cv2.getAffineTransform` solves
the warp matrix `M` in float64 from the float32 points.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import cv2
import numpy as np

Roi = tuple[np.float32, np.float32, np.float32, np.float32, float]


def roi_from_box(bbox_xyxy: Sequence[Any]) -> Roi:
    """Return the ROI `(c_x, c_y, w, h, rotation)` of a box `[x1, y1, x2, y2]`, with rotation 0.

    Implements: pre.resize.affine_crop

    Each value rounds to float32, and each operation rounds its result to float32.
    """
    x1, y1, x2, y2 = (np.float32(float(value)) for value in bbox_xyxy)
    half = np.float32(0.5)
    return (x1 + x2) * half, (y1 + y2) * half, x2 - x1, y2 - y1, 0.0


def roi_values(roi: Sequence[Any]) -> Roi:
    """Return the ROI as the steps use it: a float32 centre and size, and a float64 rotation in radians.

    Implements: pre.resize.affine_crop

    The host gives the ROI. A value that is not finite is refused.
    """
    values = [float(value) for value in roi]
    if len(values) != 5:
        raise ValueError("an ROI has five values: c_x, c_y, w, h and rotation")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("each ROI value must be finite")
    c_x, c_y, w, h, rotation = values
    return np.float32(c_x), np.float32(c_y), np.float32(w), np.float32(h), rotation


def crop_size(
    roi: Roi, target_size: Sequence[int], expand_ratio: float, maintain_aspect_ratio: bool
) -> tuple[np.float32, np.float32, np.float32, np.float32]:
    """Return `(c_x, c_y, w, h)`: the centre and the crop size along the ROI axes, in float32.

    Implements: pre.resize.affine_crop

    The order is: expand, then fix the aspect ratio. The comparison is a strict `>`. An ROI that
    gives an empty crop is refused.
    """
    c_x, c_y, w, h, _ = roi
    t_h, t_w = (int(value) for value in target_size)
    e = np.float32(float(expand_ratio))
    w = np.float32(w) * e
    h = np.float32(h) * e
    if maintain_aspect_ratio:
        a = np.float32(t_w / t_h)
        if w > h * a:
            h = w / a
        else:
            w = h * a
    if not (w > 0 and h > 0):
        raise ValueError("the ROI gives an empty crop")
    return np.float32(c_x), np.float32(c_y), w, h


def warp_points(
    center_and_size: tuple[np.float32, np.float32, np.float32, np.float32],
    rotation: float,
    target_size: Sequence[int],
    maintain_aspect_ratio: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """Return the three float32 point pairs `(src, dst)` that define `M`, each of shape (3, 2).

    Implements: pre.resize.affine_crop

    The second point is half the crop width from the centre, against the ROI x axis: left of the
    centre for rotation 0. With `maintain_aspect_ratio` true, the third point turns `P0 - P1` by
    +90 degrees around `P1`, in float32. With false, it is half the crop height from the centre,
    against the ROI y axis.
    """
    c_x, c_y, w, h = center_and_size
    t_h, t_w = (int(value) for value in target_size)
    half = np.float32(0.5)
    cs, sn = math.cos(float(rotation)), math.sin(float(rotation))
    half_w, half_h = float(w * half), float(h * half)
    src = np.zeros((3, 2), dtype=np.float32)
    dst = np.zeros((3, 2), dtype=np.float32)
    src[0] = (c_x, c_y)
    dst[0] = (t_w * 0.5, t_h * 0.5)
    src[1] = (float(c_x) - half_w * cs, float(c_y) - half_w * sn)
    dst[1] = (0.0, t_h * 0.5)
    if maintain_aspect_ratio:
        d_x = src[0, 0] - src[1, 0]
        d_y = src[0, 1] - src[1, 1]
        src[2] = (src[1, 0] - d_y, src[1, 1] + d_x)
        dst[2] = (0.0, t_h * 0.5 + t_w * 0.5)
    else:
        src[2] = (float(c_x) + half_h * sn, float(c_y) - half_h * cs)
        dst[2] = (t_w * 0.5, 0.0)
    return src, dst


def warp_matrix(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """Return `M`, the float64 (2, 3) affine map that takes `src` onto `dst`.

    Implements: pre.resize.affine_crop
    """
    return cv2.getAffineTransform(np.asarray(src, np.float32), np.asarray(dst, np.float32))


def crop_geometry(
    roi: Sequence[Any], target_size: Sequence[int], expand_ratio: float, maintain_aspect_ratio: bool
) -> dict[str, Any]:
    """Return `{center, crop_w, crop_h, matrix}` of one ROI `(c_x, c_y, w, h, rotation)`.

    Implements: pre.resize.affine_crop

    For a box, give `roi_from_box(bbox_xyxy)`. `matrix` is `M`, a float64 (2, 3) array.
    """
    values = roi_values(roi)
    size = crop_size(values, target_size, expand_ratio, maintain_aspect_ratio)
    src, dst = warp_points(size, values[4], target_size, maintain_aspect_ratio)
    c_x, c_y, w, h = size
    return {"center": [float(c_x), float(c_y)], "crop_w": float(w), "crop_h": float(h), "matrix": warp_matrix(src, dst)}


def affine_crop(
    image: np.ndarray,
    roi: Sequence[Any],
    target_size: Sequence[int],
    expand_ratio: float,
    maintain_aspect_ratio: bool,
    pad_value: Sequence[float],
    interpolation: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Warp one ROI of an `(H, W, 3)` image to `target_size`. Return the crop and the geometry.

    Implements: pre.resize.affine_crop

    `pad_value` holds one border value for each channel, in the channel order of the image.
    `interpolation` is the OpenCV filter constant. The crop has the dtype of the image.
    """
    geometry = crop_geometry(roi, target_size, expand_ratio, maintain_aspect_ratio)
    border = tuple(float(value) for value in pad_value)
    if len(border) != 3:
        raise ValueError("pad_value must have one value for each channel")
    crop = cv2.warpAffine(
        np.ascontiguousarray(image),
        geometry["matrix"],
        (int(target_size[1]), int(target_size[0])),
        flags=interpolation,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border,
    )
    return crop, geometry


def unproject(model_xy: Any, matrix: Any) -> np.ndarray:
    """Map `(..., 2)` model-input positions to source pixels with the inverse of `M`, in float64.

    Implements: pre.resize.affine_crop

    The function adds no `0.5` offset.
    """
    inverse = cv2.invertAffineTransform(np.asarray(matrix, dtype=np.float64))
    points = np.asarray(model_xy, dtype=np.float64)
    x, y = points[..., 0], points[..., 1]
    return np.stack(
        [x * inverse[0, 0] + y * inverse[0, 1] + inverse[0, 2], x * inverse[1, 0] + y * inverse[1, 1] + inverse[1, 2]],
        axis=-1,
    )

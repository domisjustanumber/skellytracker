"""The unprojection of decoded positions to the source image (section `post.unprojection`).

The unprojection has two steps. `to_model_pixels` converts a decoded position to model-input
pixels. `resize_inverse` then applies the Inverse of the resize method. The math is in float64. No
step adds or removes a `0.5` offset.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from skellytracker.core.detectors.processing.pre import (
    resize_affine_crop,
    resize_fit,
    resize_letterbox,
    resize_stretch,
)
from skellytracker.core.detectors.processing.pre.preprocess import ResizeGeometry


def to_model_pixels(decoded: Any, space: str, input_size: Sequence[int]) -> np.ndarray:
    """Convert `(..., 2)` decoded positions to model-input pixels, in float64.

    Implements: post.unprojection

    `space` is `object.decode.box_space` or `keypoint.decode.coordinate_space`. `input_size` is
    `(height, width)` of the model input. `normalized_01` multiplies x by the width and y by the
    height. `normalized_11` maps `[-1, 1]` to `[0, width]` and to `[0, height]`.
    """
    points = np.array(decoded, dtype=np.float64)
    if points.shape[-1:] != (2,):
        raise ValueError(f"positions must have the shape (..., 2), not {points.shape}")
    size = np.array([float(input_size[1]), float(input_size[0])])
    if space == "pixel":
        return points
    if space == "normalized_01":
        return points * size
    if space == "normalized_11":
        return (points + 1) / 2 * size
    raise ValueError(f"unsupported coordinate space: {space!r}")


def resize_inverse(model_xy: Any, geometry: ResizeGeometry) -> np.ndarray:
    """Map `(..., 2)` positions in model-input pixels to source pixels, in float64.

    Implements: post.unprojection
    Implements: pre.resize.none

    The function calls the Inverse of the resize method of the geometry. `none` returns the
    positions unchanged.
    """
    points = np.asarray(model_xy, dtype=np.float64)
    if points.shape[-1:] != (2,):
        raise ValueError(f"positions must have the shape (..., 2), not {points.shape}")
    method, values = geometry.method, geometry.values
    if method == "none":
        return points.copy()
    if method == "letterbox":
        return resize_letterbox.inverse_points(points, values, geometry.src_w, geometry.src_h)
    if method == "stretch":
        return resize_stretch.inverse_points(points, geometry.input_size, geometry.src_w, geometry.src_h)
    if method == "fit":
        return resize_fit.inverse_points(points, values)
    if method == "affine_crop":
        return resize_affine_crop.unproject(points, values["matrix"])
    raise ValueError(f"unsupported resize method: {method!r}")


def unproject_points(decoded_xy: Any, space: str, geometry: ResizeGeometry) -> np.ndarray:
    """Unproject `(..., 2)` decoded positions to source pixels, in float64.

    Implements: post.unprojection
    """
    return resize_inverse(to_model_pixels(decoded_xy, space, geometry.input_size), geometry)


def unproject_boxes(decoded_xyxy: Any, space: str, geometry: ResizeGeometry) -> np.ndarray:
    """Unproject `(..., 4)` decoded xyxy boxes to source pixels, in float64.

    Implements: post.unprojection

    The function maps the two corners of each box. It does not clamp the boxes: the clamp and the
    size filter are steps of the object decode.
    """
    boxes = np.asarray(decoded_xyxy, dtype=np.float64)
    if boxes.shape[-1:] != (4,):
        raise ValueError(f"boxes must have the shape (..., 4), not {boxes.shape}")
    corners = unproject_points(boxes.reshape(*boxes.shape[:-1], 2, 2), space, geometry)
    return corners.reshape(boxes.shape)

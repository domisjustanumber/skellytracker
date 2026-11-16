"""The shared steps of the object decode (section `post.object.decode`, "Selection behaviour").

The selection modules set the order of the steps and call these functions. Each score comparison
is in float32: the score and the threshold round to float32 first. The score order, the clamp and
the size filter are in float64.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from skellytracker.core.detectors.processing.post.unprojection import resize_inverse, to_model_pixels
from skellytracker.core.detectors.processing.pre.preprocess import ResizeGeometry
from skellytracker.core.model_spec.model import ObjectDecodeSpec


def score_order(scores: Any) -> np.ndarray:
    """Return the indexes of `scores` by descending score. A tie goes to the lower index.

    Implements: post.object.decode

    An input with more than one dimension flattens in row-major order.
    """
    flat = np.asarray(scores, dtype=np.float64).reshape(-1)
    return np.argsort(-flat, kind="stable").astype(np.int64)


def to_xyxy(boxes: Any, box_format: str) -> np.ndarray:
    """Shared step 2: convert `(..., 4)` boxes from `box_format` to xyxy, in float64.

    Implements: post.object.decode

    `xywh` is the top-left corner and the size. `cxcywh` is the centre and the size. The result is
    a new array. The function does not apply `box_space`.
    """
    out = np.array(boxes, dtype=np.float64)
    if out.shape[-1:] != (4,):
        raise ValueError(f"boxes must have the shape (..., 4), not {out.shape}")
    a, b, c, d = (out[..., i].copy() for i in range(4))
    if box_format == "xywh":
        out[..., 2], out[..., 3] = a + c, b + d
    elif box_format == "cxcywh":
        out[..., 0], out[..., 1] = a - c * 0.5, b - d * 0.5
        out[..., 2], out[..., 3] = a + c * 0.5, b + d * 0.5
    elif box_format != "xyxy":
        raise ValueError(f"unsupported box_format: {box_format!r}")
    return out


def to_model_boxes(boxes: Any, decode: ObjectDecodeSpec, input_size: Sequence[int]) -> np.ndarray:
    """Shared step 2: return `(..., 4)` xyxy boxes in model-input pixels, in float64.

    Implements: post.object.decode

    The function converts `box_format` to xyxy, then `box_space` to model-input pixels.
    `input_size` is `(height, width)` of the model input. No unprojection yet.
    """
    xyxy = to_xyxy(boxes, decode.box_format)
    corners = to_model_pixels(xyxy.reshape(*xyxy.shape[:-1], 2, 2), decode.box_space, input_size)
    return corners.reshape(xyxy.shape)


def filter_classes(indexes: Any, classes: Sequence[str | None], keep_classes: Sequence[str] | None) -> np.ndarray:
    """Shared step 1: return the int64 class index of each candidate, or -1 for a candidate to drop.

    Implements: post.object.decode

    A floating index rounds half to even. An index outside `[0, len(classes))`, an index of a gap
    (`None`) and, with `keep_classes`, an index whose name is not in it give -1.
    """
    given = np.asarray(indexes)
    if np.issubdtype(given.dtype, np.floating):
        given = np.rint(given)
    index = given.astype(np.int64)
    kept = np.asarray(
        [name is not None and (keep_classes is None or name in keep_classes) for name in classes], dtype=bool
    )
    inside = (index >= 0) & (index < len(classes))
    inside &= kept[np.clip(index, 0, len(classes) - 1)]
    return np.where(inside, index, -1).astype(np.int64)


def clamp(boxes_xyxy: Any, src_w: float | int, src_h: float | int) -> np.ndarray:
    """Shared step 4: clamp `(..., 4)` xyxy source boxes to `[0, src_w]` and `[0, src_h]`, in float64.

    Implements: post.object.decode

    The caller applies it only when `clamp_boxes` is true. The clamp keeps a box with zero area.
    """
    out = np.array(boxes_xyxy, dtype=np.float64)
    out[..., 0::2] = out[..., 0::2].clip(0, src_w)
    out[..., 1::2] = out[..., 1::2].clip(0, src_h)
    return out


def size_mask(boxes_xyxy: Any, min_box_size: float | int | None) -> np.ndarray:
    """Shared step 5: return the mask of the boxes that the size filter keeps.

    Implements: post.object.decode

    A box stays only when `x2 - x1 > min_box_size` and `y2 - y1 > min_box_size`, in float64, with
    no `+1`. With `None`, each box stays.
    """
    boxes = np.asarray(boxes_xyxy, dtype=np.float64)
    if min_box_size is None:
        return np.ones(boxes.shape[:-1], dtype=bool)
    return np.asarray(((boxes[..., 2] - boxes[..., 0]) > min_box_size) & ((boxes[..., 3] - boxes[..., 1]) > min_box_size))


def confidence_mask(scores: Any, threshold: float | int) -> np.ndarray:
    """Shared step 6: return the mask of the scores that stay: `score > threshold`, in float32.

    Implements: post.object.decode

    The score and the threshold round to float32 first. A score equal to the threshold goes.
    """
    return np.asarray(scores, dtype=np.float64).astype(np.float32) > np.float32(threshold)


def unproject_and_filter(
    model_xyxy: Any,
    scores: Any,
    decode: ObjectDecodeSpec,
    geometry: ResizeGeometry | None,
    min_score: float | int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Shared steps 3 to 6 for the selected boxes. Return the positions that stay and their boxes.

    Implements: post.object.decode

    `model_xyxy` are `(N, 4)` xyxy boxes in model-input pixels, and `scores` are their `(N,)`
    scores. The steps are: unproject the boxes to the source image, clamp them when `clamp_boxes`
    is true, drop each box that the size filter of `min_box_size` refuses, then drop each box
    unless `score > min_score`. `min_score` is the value of the caller. With `None`, it is
    `object.decode.min_score`. With no `geometry`, steps 3 to 5 do not run and the boxes stay in
    model-input pixels.
    """
    boxes = np.asarray(model_xyxy, dtype=np.float64).reshape(-1, 4)
    keep = np.ones(boxes.shape[0], dtype=bool)
    if geometry is not None:
        boxes = resize_inverse(boxes.reshape(-1, 2, 2), geometry).reshape(-1, 4)
        if decode.clamp_boxes:
            boxes = clamp(boxes, geometry.src_w, geometry.src_h)
        keep &= size_mask(boxes, decode.min_box_size)
    keep &= confidence_mask(np.asarray(scores).reshape(-1), decode.min_score if min_score is None else min_score)
    positions = np.flatnonzero(keep)
    return positions, boxes[positions]

"""The decode of `selection: nms` for one image (section `post.object.selection.nms`).

The score filter is in float32. The IoU and the score order are in float64. The box area has no
`+1`, as the ONNX `NonMaxSuppression` operator with `center_point_box` 0.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from skellytracker.core.detectors.processing.post.object_decode import (
    filter_classes,
    to_model_boxes,
    unproject_and_filter,
)
from skellytracker.core.detectors.processing.pre.preprocess import ResizeGeometry
from skellytracker.core.model_spec.model import NmsSpec, ObjectDecodeSpec


def box_iou(box: np.ndarray, boxes: np.ndarray) -> np.ndarray:
    """Return the IoU of one xyxy box with each of the `(N, 4)` xyxy boxes, in float64.

    Implements: post.object.selection.nms

    The area of a box is `(x2 - x1) * (y2 - y1)`. The two corners of a box are any diagonal pair.
    When a box has zero area, or the intersection is empty, the IoU is 0.
    """
    ax1, ax2 = min(box[0], box[2]), max(box[0], box[2])
    ay1, ay2 = min(box[1], box[3]), max(box[1], box[3])
    bx1, bx2 = np.minimum(boxes[:, 0], boxes[:, 2]), np.maximum(boxes[:, 0], boxes[:, 2])
    by1, by2 = np.minimum(boxes[:, 1], boxes[:, 3]), np.maximum(boxes[:, 1], boxes[:, 3])
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    inter_w = np.maximum(np.minimum(ax2, bx2) - np.maximum(ax1, bx1), 0.0)
    inter_h = np.maximum(np.minimum(ay2, by2) - np.maximum(ay1, by1), 0.0)
    inter = inter_w * inter_h
    union = area_a + area_b - inter
    valid = (area_a > 0.0) & (area_b > 0.0) & (inter > 0.0) & (union > 0.0)
    return np.where(valid, inter / np.where(union > 0.0, union, 1.0), 0.0)


def hard_nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float | int) -> np.ndarray:
    """Run greedy hard NMS over one group of candidates. Return the positions that stay, in visit order.

    Implements: post.object.selection.nms

    The function visits the candidates by descending score. A tie goes to the lower position. A
    candidate stays when its IoU with each box that stays before it is not more than
    `iou_threshold`.
    """
    order = np.lexsort((np.arange(scores.size), -scores))
    kept: list[int] = []
    for position in order:
        if not kept or not np.any(box_iou(boxes[position], boxes[kept]) > iou_threshold):
            kept.append(int(position))
    return np.asarray(kept, np.int64)


def select_nms(boxes: Any, scores: Any, class_indices: Any, nms: NmsSpec) -> np.ndarray:
    """Return the input rows that the NMS selection keeps, in output order (steps 1, 4 and 5).

    Implements: post.object.selection.nms

    `boxes` are `(Q, 4)` xyxy in model-input pixels. `class_indices` are the `(Q,)` class indexes
    after the class filter: -1 marks a candidate to drop. A candidate stays only when
    `score > nms.score_threshold`. The NMS runs for each class, or over all candidates when
    `class_agnostic` is true. The survivors are in descending score order. A tie goes to the lower
    row. `post_nms_top_k` keeps the first survivors.
    """
    box = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
    score = np.asarray(scores, dtype=np.float64).reshape(-1)
    classes = np.asarray(class_indices, np.int64).reshape(-1)
    if not box.shape[0] == score.size == classes.size:
        raise ValueError(f"boxes, scores and class_indices need one row count: {box.shape[0]}, {score.size}, {classes.size}")
    rows = np.flatnonzero((score.astype(np.float32) > np.float32(nms.score_threshold)) & (classes >= 0))
    groups = [rows] if nms.class_agnostic else [rows[classes[rows] == c] for c in np.unique(classes[rows])]
    survivors = [group[hard_nms(box[group], score[group], nms.iou_threshold)] for group in groups]
    found = np.concatenate([np.zeros(0, np.int64), *survivors])
    found = found[np.lexsort((found, -score[found]))]
    if nms.post_nms_top_k is not None:
        found = found[: nms.post_nms_top_k]
    return found.astype(np.int64)


def decode_nms(
    boxes: Any,
    scores: Any,
    class_indexes: Any,
    decode: ObjectDecodeSpec,
    classes: Sequence[str | None],
    input_size: Sequence[int],
    geometry: ResizeGeometry | None,
    min_score: float | int | None = None,
) -> dict[str, np.ndarray]:
    """Run the decode of `selection: nms` for one image. Return `rows`, `scores`, `class_indices` and `boxes`.

    Implements: post.object.selection.nms

    `boxes` are the `(Q, 4)` boxes of the primary output, in `box_format` and `box_space`. `scores`
    are the `(Q,)` scores. `class_indexes` are the `(Q,)` model class indexes, or `None` when the
    sidecar has no class source: each candidate then has the class index 0. `classes` is
    `object.classes`. `input_size` is `(height, width)` of the model input. `min_score` is the
    value of the caller for the last filter. With `None`, it is `object.decode.min_score`.

    `rows` are the input rows in output order. The boxes are xyxy in source pixels. With no
    `geometry`, the unprojection, the clamp and the size filter do not run, and the boxes stay in
    model-input pixels.
    """
    if decode.nms is None:
        raise ValueError("the decode of selection: nms needs object.decode.nms")
    score = np.asarray(scores, dtype=np.float64).reshape(-1)
    model = to_model_boxes(np.asarray(boxes).reshape(-1, 4), decode, input_size)
    if class_indexes is None:
        class_indices = np.zeros(score.size, np.int64)
    else:
        class_indices = filter_classes(np.asarray(class_indexes).reshape(-1), classes, decode.keep_classes)
    rows = select_nms(model, score, class_indices, decode.nms)
    positions, out_boxes = unproject_and_filter(model[rows], score[rows], decode, geometry, min_score)
    rows = rows[positions]
    return {"rows": rows, "scores": score[rows], "class_indices": class_indices[rows], "boxes": out_boxes}

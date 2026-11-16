"""The node ``redetect_trigger``: give the image when a detector must run again.

Implements: node.redetect_trigger

The state of one camera is ``last``: the ``frame_index`` of the last frame on which the node gave
the image, or ``None`` at the start.
"""
from __future__ import annotations

import math
from typing import Any

from skellytracker.core.pipelines._runtime.context import FrameContext
from skellytracker.core.pipelines.config import FitnessCheck, RedetectTriggerParams
from skellytracker.core.pipelines.values import PortInfo

# An empty `image` stops the node. The other inputs are optional (Behaviour step 1).
READS_EMPTY: frozenset[str] = frozenset()
# The default of each field of each check (Fields).
DEFAULTS = {"threshold": {"min_keypoint_score": 0.3, "keypoints_within_bbox_ratio": 0.5}, "n_frames": 30,
            "min_area_ratio": 0.25, "expand_ratio": 1.10, "min_score": 0.0}


def output_info(
    node_id: str, params: RedetectTriggerParams, inputs: dict[str, PortInfo]
) -> tuple[dict[str, PortInfo], list[dict[str, Any]]]:
    """Check V-node.redetect_trigger-2, and return the facts of the output ``image``.

    Implements: node.redetect_trigger

    The params model checks V-node.redetect_trigger-1.
    """
    if any(check.check == "roi_missing" for check in params.fitness_checks) and "previous_rois" not in inputs:
        raise ValueError(f"V-node.redetect_trigger-2: {node_id}: the check roi_missing needs the input previous_rois")
    return {"image": inputs["image"]}, []


def _field(check: FitnessCheck, name: str) -> Any:
    """Return a field of a check, or its default when the item does not write it."""
    value = getattr(check, name)
    if value is not None:
        return value
    default = DEFAULTS[name]
    return default[check.check] if isinstance(default, dict) else default


def _valid(point: list[float]) -> bool:
    """A point is valid when its x and its y are not NaN."""
    return not (math.isnan(point[0]) or math.isnan(point[1]))


def _inside(point: list[float], roi: list[float]) -> bool:
    """Return true when the point is in the ROI, edges included."""
    cx, cy, w, h, rotation = roi
    dx, dy = point[0] - cx, point[1] - cy
    u = math.cos(rotation) * dx + math.sin(rotation) * dy
    v = -math.sin(rotation) * dx + math.cos(rotation) * dy
    return abs(u) <= w / 2.0 and abs(v) <= h / 2.0


def _area_collapsed(row: list[list[float]], roi: list[float], check: FitnessCheck) -> bool:
    """The check ``bbox_area_collapse`` for one row with an ROI. A point is ``[x, y, score]``."""
    min_score = _field(check, "min_score")
    points = [p for p in row if _valid(p) and (min_score <= 0 or p[2] >= min_score)]
    if not points:
        return True
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    width, height = max(xs) - min(xs), max(ys) - min(ys)
    if width <= 0 or height <= 0:
        return True
    grow = _field(check, "expand_ratio")
    expected = roi[2] * roi[3]
    return expected > 0 and width * grow * height * grow < _field(check, "min_area_ratio") * expected


def _fails(check: FitnessCheck, frames_since: int, row: list[list[float]] | None, roi: list[float] | None, connected: bool) -> bool:
    """Return true when one fitness check fails for one instance row (Behaviour step 6).

    ``connected`` is true when ``previous_keypoints`` is connected. A row of ``None`` is missing.
    """
    kind = check.check
    if kind == "max_frames_without_redetect":
        return frames_since >= _field(check, "n_frames")
    if kind == "roi_missing":
        return roi is None
    if row is None:
        return kind == "bbox_area_collapse" and connected and roi is not None
    points = [p for p in row if _valid(p)]
    if kind == "min_keypoint_score":
        return bool(points) and sum(p[2] for p in points) / len(points) < _field(check, "threshold")
    if roi is None:
        return False
    if kind == "keypoints_within_bbox_ratio":
        return bool(points) and sum(_inside(p, roi) for p in points) / len(points) < _field(check, "threshold")
    return _area_collapsed(row, roi, check)


def run(
    params: RedetectTriggerParams, inputs: dict[str, Any], state: int | None, frame: FrameContext, infos: Any = None
) -> tuple[dict[str, Any], int | None]:
    """Give the image or an empty output for one frame. Return the output and the new ``last``.

    Implements: node.redetect_trigger
    """
    image = inputs["image"]
    if frame.running_mode == "image":
        return {"image": image}, None
    n, last = frame.frame_index, state
    hit = last is None or n - last >= params.redetect_interval
    if not hit:
        keypoints, rois = inputs.get("previous_keypoints"), inputs.get("previous_rois")
        count = max(0 if keypoints is None else len(keypoints.present), 0 if rois is None else len(rois.present))
        for i in range(max(count, 1)):
            row = roi = None
            if keypoints is not None and i < len(keypoints.present) and keypoints.present[i]:
                row = [[x, y, score] for (x, y), score in zip(keypoints.xyz[i, :, :2].tolist(), keypoints.score[i].tolist(), strict=True)]
            if rois is not None and i < len(rois.present) and rois.present[i]:
                roi = rois.rois[i].tolist()
            if any(_fails(check, n - last, row, roi, "previous_keypoints" in inputs) for check in params.fitness_checks):
                hit = True
                break
    return {"image": image if hit else None}, n if hit else last

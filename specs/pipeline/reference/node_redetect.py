"""Reference implementation of the pipeline section node.redetect (draft).

Note:

- Section ID: node.redetect.
- Source: skellytracker/core/temporal_processing/bbox_policy.py (BBoxPolicy.should_redetect, the four
  checks and predict_bbox_from_keypoints) and skellytracker/core/tracker/detection_stage.py
  (DetectionStage.run). Today the boxes have no rotation.
- Imported section modules: none.

A case is one sequence of frames. Each frame holds frame_number, previous_keypoints and previous_rois.
previous_keypoints is a list of instance rows, and each row is a list of points [x, y, visibility].
previous_rois is a list of instance rows, and each row is an ROI [cx, cy, w, h, rotation] or null (the
row is not present). An input that is null is empty. The result is True for each frame where the
node gives the image (the trigger).
"""

from __future__ import annotations

import math
from typing import Any

FIELDS = {
    "min_keypoint_visibility": {"threshold": 0.3},
    "keypoints_within_bbox_ratio": {"threshold": 0.5},
    "max_frames_without_redetect": {"n_frames": 30},
    "bbox_area_collapse": {"min_area_ratio": 0.25, "expansion_ratio": 0.05, "min_visibility": 0.0},
}
RUNNING_MODES = ("image", "video", "live")


def resolve_check(check: dict[str, Any]) -> dict[str, Any]:
    """Return one fitness check with its defaults, or refuse it (node.redetect, V-node.redetect-1)."""
    kind = check.get("kind")
    if kind not in FIELDS:
        raise ValueError(f"unknown fitness check kind {kind!r}")
    foreign = sorted(set(check) - {"kind"} - set(FIELDS[kind]))
    if foreign:
        raise ValueError(f"V-node.redetect-1: the check {kind} has no field {foreign}")
    return {**FIELDS[kind], **check}


def valid(point: list[float]) -> bool:
    """A point is valid when x and y are not NaN (node.redetect)."""
    return not (math.isnan(point[0]) or math.isnan(point[1]))


def inside(point: list[float], roi: list[float]) -> bool:
    """True when the point is in the ROI, edges included (node.redetect)."""
    cx, cy, w, h, rotation = roi
    dx, dy = point[0] - cx, point[1] - cy
    u = math.cos(rotation) * dx + math.sin(rotation) * dy
    v = -math.sin(rotation) * dx + math.cos(rotation) * dy
    return abs(u) <= w / 2.0 and abs(v) <= h / 2.0


def area_collapsed(row: list[list[float]], roi: list[float], check: dict[str, Any]) -> bool:
    """The check bbox_area_collapse for one row with an ROI (node.redetect)."""
    points = [p for p in row if valid(p) and (check["min_visibility"] <= 0 or p[2] >= check["min_visibility"])]
    if not points:
        return True
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    width, height = max(xs) - min(xs), max(ys) - min(ys)
    if width <= 0 or height <= 0:
        return True
    grow = 1.0 + 2.0 * check["expansion_ratio"]
    expected = roi[2] * roi[3]
    return expected > 0 and width * grow * height * grow < check["min_area_ratio"] * expected


def fails(check: dict[str, Any], frames_since: int, row: list[list[float]] | None, roi: list[float] | None) -> bool:
    """True when one fitness check fails for one instance row (node.redetect, Behaviour)."""
    kind = check["kind"]
    if kind == "max_frames_without_redetect":
        return frames_since >= check["n_frames"]
    if row is None:
        return False
    points = [p for p in row if valid(p)]
    if kind == "min_keypoint_visibility":
        return bool(points) and sum(p[2] for p in points) / len(points) < check["threshold"]
    if roi is None:
        return False
    if kind == "keypoints_within_bbox_ratio":
        return bool(points) and sum(inside(p, roi) for p in points) / len(points) < check["threshold"]
    return area_collapsed(row, roi, check)


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Decide for each frame of a sequence if a new detection is needed (node.redetect, Behaviour).

    input holds running_mode and frames. The result holds triggered, one boolean for each frame.
    """
    unknown = sorted(set(params) - {"redetect_interval", "fitness_checks"})
    if unknown:
        raise ValueError(f"unknown params {unknown}")
    interval = params.get("redetect_interval", 1)
    checks = [resolve_check(check) for check in params.get("fitness_checks", [])]
    if input["running_mode"] not in RUNNING_MODES:
        raise ValueError(f"unknown running_mode {input['running_mode']!r}")
    last = None
    triggered = []
    for frame in input["frames"]:
        n = frame["frame_number"]
        if input["running_mode"] == "image" or last is None or n - last >= interval:
            hit = True
        else:
            keypoints, rois = frame["previous_keypoints"], frame["previous_rois"]
            count = max(len(keypoints or []), len(rois or []))
            hit = any(
                fails(
                    check,
                    n - last,
                    keypoints[i] if keypoints is not None and i < len(keypoints) else None,
                    rois[i] if rois is not None and i < len(rois) else None,
                )
                for check in checks
                for i in range(max(count, 1))
            )
        if hit:
            last = n
        triggered.append(hit)
    return {"triggered": triggered}

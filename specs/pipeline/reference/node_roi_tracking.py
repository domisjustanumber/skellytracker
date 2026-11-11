"""Reference implementation of the pipeline section node.roi_tracking.

Note:

- Section ID: node.roi_tracking.
- Source: the section text specs/pipeline/nodes/roi_tracking.md. It follows the MediaPipe
  RoiTrackingCalculator rules of MediaPipe-Exporter docs/mediapipe-whole-body.md (sections 1.8 and
  4.2) at 8f708a1ddecd8e035de15a5a9a7b652af035a58a.
- Imported section modules: node.roi_from_points (node_roi_from_points, the function
  normalize_radians). Fixtures: none.
"""

from __future__ import annotations

import math
from typing import Any

import node_roi_from_points

# The defaults of RoiTrackingParams in specs/pipeline/reference/pipeline_config.py.
DEFAULTS = {"max_rotation_deg": 40.0, "max_offset": 0.2, "max_size_change": 0.4, "keypoint_margin": -0.1}


def keep_previous(
    params: dict[str, Any], previous: list[float], current: list[float], points: list[list[float]]
) -> bool:
    """True when the previous ROI passes the tests of steps 4 to 7 (node.roi_tracking)."""
    pcx, pcy, pw, ph, pr = previous
    cx, cy, w, h, r = current
    if abs(node_roi_from_points.normalize_radians(pr - r)) > math.radians(params["max_rotation_deg"]):
        return False
    c, s = math.cos(r), math.sin(r)

    def frame(x: float, y: float) -> tuple[float, float]:
        return (x - cx) * c + (y - cy) * s, -(x - cx) * s + (y - cy) * c

    u, v = frame(pcx, pcy)
    if abs(u) > params["max_offset"] * w or abs(v) > params["max_offset"] * h:
        return False
    if abs(pw - w) > params["max_size_change"] * w or abs(ph - h) > params["max_size_change"] * h:
        return False
    grow = 1 + params["keypoint_margin"]
    for x, y in points:
        if math.isnan(x) or math.isnan(y):
            continue
        u, v = frame(x, y)
        if abs(u) > grow * w / 2 or abs(v) > grow * h / 2:
            return False
    return True


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Choose the previous or the current ROI of each row (node.roi_tracking).

    params holds the params of the node; a missing param takes its default. input holds previous
    and current (None for an empty input, else one [cx, cy, w, h, rotation] or None for each row)
    and the optional previous_keypoints (None or absent, else xy and present). The result holds
    rois: None for an empty output, else one ROI or None for each row.
    """
    params = {**DEFAULTS, **params}
    if not params["keypoint_margin"] > -1:
        raise ValueError(f"V-node.roi_tracking-1: keypoint_margin must be greater than -1, not {params['keypoint_margin']}")
    current = input["current"]
    if current is None:
        return {"rois": None}
    previous = input["previous"] or [None] * len(current)
    keypoints = input.get("previous_keypoints")
    rows = []
    for i, roi in enumerate(current):
        if roi is None or previous[i] is None:
            rows.append(roi)
            continue
        points = keypoints["xy"][i] if keypoints is not None and keypoints["present"][i] else []
        rows.append(previous[i] if keep_previous(params, previous[i], roi, points) else roi)
    return {"rois": rows}

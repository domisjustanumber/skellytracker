"""Reference implementation of the pipeline section node.smooth_roi (draft).

Note:

- Section ID: node.smooth_roi.
- Source: skellytracker/core/temporal_processing/bbox_smoothing.py (apply_bbox_ema) and
  skellytracker/core/tracker/detection_stage.py (DetectionStage._smooth_bbox). Today the boxes have no
  rotation.
- Imported section modules: node.roi_from_points (node_roi_from_points, the function
  normalize_radians).

A case is one sequence of frames. Each frame is a list of instance rows, and each row is an ROI
[cx, cy, w, h, rotation] or null (the row is not present). A frame that is null is an empty input:
the node does not run.
"""

from __future__ import annotations

from typing import Any

import node_roi_from_points

RUNNING_MODES = ("image", "video", "live")


def blend(previous: list[float], given: list[float], alpha: float) -> list[float]:
    """alpha x previous + (1 - alpha) x given, with the rotation on the short arc (node.smooth_roi)."""
    cx, cy, w, h = (alpha * a + (1.0 - alpha) * b for a, b in zip(previous[:4], given[:4]))  # noqa: B905
    turn = node_roi_from_points.normalize_radians(previous[4] - given[4])
    rotation = node_roi_from_points.normalize_radians(given[4] + alpha * turn)
    return [cx, cy, w, h, rotation]


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Smooth a sequence of ROI frames (node.smooth_roi, Behaviour).

    input holds running_mode and frames. The result holds rois, one output frame for each input frame.
    """
    unknown = sorted(set(params) - {"alpha"})
    if unknown:
        raise ValueError(f"unknown params {unknown}")
    alpha = params.get("alpha", 0.5)
    if input["running_mode"] not in RUNNING_MODES:
        raise ValueError(f"unknown running_mode {input['running_mode']!r}")
    if input["running_mode"] == "image":
        return {"rois": input["frames"]}
    previous: dict[int, list[float]] = {}
    output = []
    for frame in input["frames"]:
        if frame is None:
            output.append(None)
            continue
        out_frame = []
        for i, roi in enumerate(frame):
            if roi is not None:
                previous[i] = list(roi) if i not in previous else blend(previous[i], roi, alpha)
            out_frame.append(None if roi is None else previous[i])
        output.append(out_frame)
    return {"rois": output}

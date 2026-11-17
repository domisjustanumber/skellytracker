"""Reference implementation of the pipeline section node.smooth_boxes (draft).

Note:

- Section ID: node.smooth_boxes.
- Source: skellytracker/core/temporal_processing/bbox_smoothing.py (apply_bbox_ema) and
  skellytracker/core/tracker/detection_stage.py (DetectionStage._smooth_bbox). Today the boxes have no
  rotation. The filter one_euro follows apply_bbox_one_euro of the skellytracker branch sfn26
  (decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md).
- Imported section modules: node.boxes_from_points (node_boxes_from_points, the function
  normalize_radians).

A case is one sequence of frames. Each frame is a list of instance rows, and each row is a box
[cx, cy, w, h, rotation] or null (the row is not present). A frame that is null is an empty input:
the node does not run. A case of the filter one_euro also has timestamps_ms, the timestamp_ms of
each frame.
"""

from __future__ import annotations

import math
from typing import Any

import node_boxes_from_points

RUNNING_MODES = ("image", "video", "live")
# The params of each filter and their defaults (SmoothBoxesParams in pipeline_config.py).
FILTER_PARAMS = {
    "ema": {"previous_weight": 0.5},
    "one_euro": {"min_cutoff": 3.0, "beta": 0.02, "d_cutoff": 1.0, "reset_after_ms": 500.0},
}


def blend(previous: list[float], given: list[float], weight: float) -> list[float]:
    """weight x previous + (1 - weight) x given, with the rotation on the short arc (node.smooth_boxes)."""
    cx, cy, w, h = (weight * a + (1.0 - weight) * b for a, b in zip(previous[:4], given[:4]))  # noqa: B905
    turn = node_boxes_from_points.normalize_radians(previous[4] - given[4])
    rotation = node_boxes_from_points.normalize_radians(given[4] + weight * turn)
    return [cx, cy, w, h, rotation]


def alpha(cutoff: float, dt: float) -> float:
    """1 / (1 + 1 / (2 pi x cutoff x dt)) (node.smooth_keypoints, Behaviour step 7)."""
    return 1.0 / (1.0 + 1.0 / (2.0 * math.pi * cutoff * dt))


def one_euro_row(state: dict[str, Any] | None, roi: list[float], t: float, params: dict[str, Any]) -> dict[str, Any]:
    """Return the new state of one row for a present box (node.smooth_boxes, Behaviour step 8).

    The state holds est and d of the corners [x1, y1, x2, y2] and t_prev.
    """
    cx, cy, w, h = roi[:4]
    corners = [cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0]
    if state is None or t - state["t_prev"] > params["reset_after_ms"]:
        return {"est": corners, "d": [0.0] * 4, "t_prev": t}
    dt = (t - state["t_prev"]) / 1000.0
    if dt <= 0:
        raise ValueError("V-node.smooth_keypoints-3: timestamp_ms must increase from frame to frame")
    est, d = [], []
    for z, before, slope in zip(corners, state["est"], state["d"]):  # noqa: B905 (four values)
        a_d = alpha(params["d_cutoff"], dt)
        slope = a_d * (z - before) / dt + (1.0 - a_d) * slope
        a = alpha(params["min_cutoff"] + params["beta"] * abs(slope), dt)
        est.append(a * z + (1.0 - a) * before)
        d.append(slope)
    # Step 8.3: exchange the estimates of two corners that crossed. The derivatives do not move.
    if est[0] > est[2]:
        est[0], est[2] = est[2], est[0]
    if est[1] > est[3]:
        est[1], est[3] = est[3], est[1]
    return {"est": est, "d": d, "t_prev": t}


def box_of(state: dict[str, Any], rotation: float) -> list[float]:
    """The box of the corner estimates, with the rotation of the input (node.smooth_boxes, step 8.4)."""
    x1, y1, x2, y2 = state["est"]
    return [(x1 + x2) / 2.0, (y1 + y2) / 2.0, x2 - x1, y2 - y1, rotation]


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Smooth a sequence of box frames (node.smooth_boxes, Behaviour).

    input holds running_mode and frames, and timestamps_ms for the filter one_euro. The result holds
    boxes, one output frame for each input frame.
    """
    kind = params.get("filter", "ema")
    if kind not in FILTER_PARAMS:
        raise ValueError(f"unknown filter {kind!r}")
    known = {name for names in FILTER_PARAMS.values() for name in names}
    unknown = sorted(set(params) - {"filter"} - known)
    if unknown:
        raise ValueError(f"unknown params {unknown}")
    foreign = sorted(set(params) - {"filter"} - set(FILTER_PARAMS[kind]))
    if foreign:
        raise ValueError(f"V-node.smooth_boxes-1: the filter {kind} does not take {', '.join(foreign)}")
    values = {**FILTER_PARAMS[kind], **params}
    if input["running_mode"] not in RUNNING_MODES:
        raise ValueError(f"unknown running_mode {input['running_mode']!r}")
    if input["running_mode"] == "image":
        return {"boxes": input["frames"]}
    if kind == "one_euro":
        return {"boxes": run_one_euro(values, input["frames"], input["timestamps_ms"])}
    previous: dict[int, list[float]] = {}
    output = []
    for frame in input["frames"]:
        if frame is None:
            output.append(None)
            continue
        out_frame = []
        for i, roi in enumerate(frame):
            if roi is not None:
                previous[i] = list(roi) if i not in previous else blend(previous[i], roi, values["previous_weight"])
            out_frame.append(None if roi is None else previous[i])
        output.append(out_frame)
    return {"boxes": output}


def run_one_euro(params: dict[str, Any], frames: list[Any], timestamps_ms: list[float]) -> list[Any]:
    """The filter one_euro on a sequence of frames (node.smooth_boxes, Behaviour steps 2, 4 and 8)."""
    states: dict[int, dict[str, Any]] = {}
    output = []
    for frame, t in zip(frames, timestamps_ms, strict=True):
        if frame is None:
            # Step 2: an empty input clears the state of each row.
            states.clear()
            output.append(None)
            continue
        out_frame = []
        for i, roi in enumerate(frame):
            if roi is None:
                # Step 4: a row that is not present clears its state.
                states.pop(i, None)
                out_frame.append(None)
                continue
            states[i] = one_euro_row(states.get(i), roi, t, params)
            out_frame.append(box_of(states[i], roi[4]))
        output.append(out_frame)
    return output

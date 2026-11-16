"""The node ``smooth_roi``: an EMA or a One Euro filter on the ROI of each instance row.

Implements: node.smooth_roi

The state of one camera is a tuple with one item for each row, or ``None`` at the start. An item is
``None`` (the row has no state), the last output ROI as a tuple (filter ``ema``), or
``(est, d, t_prev)`` with the corner estimates and their derivatives (filter ``one_euro``).
"""
from __future__ import annotations

import math
from typing import Any

from skellytracker.core.pipelines._runtime.context import FrameContext
from skellytracker.core.pipelines._runtime.node_roi_from_points import normalize_radians
from skellytracker.core.pipelines.config import SmoothRoiParams
from skellytracker.core.pipelines.values import InstanceRois, PortInfo

# The filter `one_euro` clears its state on an empty input, so the node gets it (Behaviour step 2).
READS_EMPTY: frozenset[str] = frozenset({"rois"})


def output_info(
    node_id: str, params: SmoothRoiParams, inputs: dict[str, PortInfo]
) -> tuple[dict[str, PortInfo], list[dict[str, Any]]]:
    """Return the facts of the output ``rois``: those of the input. The params model checks V-node.smooth_roi-1.

    Implements: node.smooth_roi
    """
    return {"rois": inputs["rois"]}, []


def _blend(previous: tuple[float, ...], given: list[float], weight: float) -> tuple[float, ...]:
    """Return weight x previous + (1 - weight) x given, with the rotation on the short arc (step 6)."""
    cx, cy, w, h = (weight * a + (1.0 - weight) * b for a, b in zip(previous[:4], given[:4], strict=True))
    turn = normalize_radians(previous[4] - given[4])
    return (cx, cy, w, h, normalize_radians(given[4] + weight * turn))


def _alpha(cutoff: float, dt: float) -> float:
    """Return 1 / (1 + 1 / (2 pi x cutoff x dt)) (node.smooth_keypoints, Behaviour step 7)."""
    return 1.0 / (1.0 + 1.0 / (2.0 * math.pi * cutoff * dt))


def _one_euro_row(state: Any, roi: list[float], t: float, params: SmoothRoiParams) -> tuple[Any, ...]:
    """Return the new state ``(est, d, t_prev)`` of one row for a present ROI (step 8)."""
    cx, cy, w, h = roi[:4]
    corners = (cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0)
    if state is None or t - state[2] > params.reset_after_ms:
        return (corners, (0.0,) * 4, t)
    dt = (t - state[2]) / 1000.0
    if dt <= 0:
        raise ValueError("V-node.smooth_keypoints-3: timestamp_ms must increase from frame to frame")
    est, d = [], []
    for z, before, slope in zip(corners, state[0], state[1], strict=True):
        a_d = _alpha(params.d_cutoff, dt)
        slope = a_d * (z - before) / dt + (1.0 - a_d) * slope
        a = _alpha(params.min_cutoff + params.beta * abs(slope), dt)
        est.append(a * z + (1.0 - a) * before)
        d.append(slope)
    # Step 8.3: exchange the estimates of two corners that crossed. The derivatives do not move.
    if est[0] > est[2]:
        est[0], est[2] = est[2], est[0]
    if est[1] > est[3]:
        est[1], est[3] = est[3], est[1]
    return (tuple(est), tuple(d), t)


def run(
    params: SmoothRoiParams, inputs: dict[str, Any], state: Any, frame: FrameContext, infos: Any = None
) -> tuple[dict[str, InstanceRois], Any]:
    """Smooth the ROI of each row of one frame. Return the output and the new state.

    Implements: node.smooth_roi
    """
    rois: InstanceRois = inputs["rois"]
    if frame.running_mode == "image":
        return {"rois": rois}, None
    count = len(rois.present)
    one_euro = params.filter == "one_euro"
    if not rois.present.any():
        # Step 2: the node does not run. The filter `one_euro` also clears the state of each row.
        return {"rois": InstanceRois.empty(count)}, None if one_euro else state
    rows = list(state) if state is not None else [None] * count
    out = InstanceRois.empty(count)
    for i in range(count):
        if not rois.present[i]:
            if one_euro:
                rows[i] = None  # step 4: a row that is not present clears its state
            continue
        roi = rois.rois[i].tolist()
        if one_euro:
            if frame.timestamp_ms is None:
                raise ValueError("the filter one_euro needs the timestamp_ms of the frame")
            rows[i] = _one_euro_row(rows[i], roi, frame.timestamp_ms, params)
            x1, y1, x2, y2 = rows[i][0]
            out.rois[i] = ((x1 + x2) / 2.0, (y1 + y2) / 2.0, x2 - x1, y2 - y1, roi[4])
        else:
            rows[i] = tuple(roi) if rows[i] is None else _blend(rows[i], roi, params.previous_weight)
            out.rois[i] = rows[i]
        out.instance_score[i] = rois.instance_score[i]
        out.present[i] = True
    return {"rois": out}, tuple(rows)

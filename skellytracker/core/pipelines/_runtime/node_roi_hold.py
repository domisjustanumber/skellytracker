"""The node ``roi_hold``: the previous ROI or the current ROI of each instance row.

Implements: node.roi_hold
"""
from __future__ import annotations

import math
from typing import Any

from skellytracker.core.pipelines._runtime.context import FrameContext
from skellytracker.core.pipelines._runtime.node_roi_from_points import normalize_radians
from skellytracker.core.pipelines.config import RoiHoldParams
from skellytracker.core.pipelines.values import InstanceRois, PortInfo

# The node reads an empty `previous`: it is empty on the first frame (Behaviour step 2).
READS_EMPTY: frozenset[str] = frozenset({"previous"})


def output_info(
    node_id: str, params: RoiHoldParams, inputs: dict[str, PortInfo]
) -> tuple[dict[str, PortInfo], list[dict[str, Any]]]:
    """Check the load rules that need the ports, and return the facts of the output ``rois``.

    Implements: node.roi_hold

    It checks V-node.roi_hold-2 and -3. The params model checks -1.
    """
    current = inputs["current"]
    others = {name: inputs[name] for name in ("previous", "previous_keypoints") if name in inputs}
    for name, info in others.items():
        if info.max_instances != current.max_instances:
            raise ValueError(f"V-node.roi_hold-2: {node_id}: {name} has {info.max_instances} rows and current has {current.max_instances}")
    for name, info in others.items():
        if info.instance_source != current.instance_source:
            raise ValueError(f"V-node.roi_hold-3: {node_id}: {name} does not have the instance source of current")
    return {"rois": current}, []


def _keep_previous(params: RoiHoldParams, previous: list[float], current: list[float], points: list[list[float]]) -> bool:
    """Return true when the previous ROI passes the tests of Behaviour steps 4 to 7."""
    pcx, pcy, pw, ph, pr = previous
    cx, cy, w, h, r = current
    if abs(normalize_radians(pr - r)) > math.radians(params.max_rotation_deg):
        return False
    c, s = math.cos(r), math.sin(r)

    def frame(x: float, y: float) -> tuple[float, float]:
        return (x - cx) * c + (y - cy) * s, -(x - cx) * s + (y - cy) * c

    u, v = frame(pcx, pcy)
    if abs(u) > params.max_offset * w or abs(v) > params.max_offset * h:
        return False
    if abs(pw - w) > params.max_size_change * w or abs(ph - h) > params.max_size_change * h:
        return False
    grow = 1 + params.keypoint_margin
    for x, y in points:
        if math.isnan(x) or math.isnan(y):
            continue
        u, v = frame(x, y)
        if abs(u) > grow * w / 2 or abs(v) > grow * h / 2:
            return False
    return True


def run(
    params: RoiHoldParams, inputs: dict[str, Any], state: Any, frame: FrameContext, infos: Any = None
) -> tuple[dict[str, InstanceRois], None]:
    """Choose the previous or the current ROI of each row. The node keeps no state.

    Implements: node.roi_hold
    """
    current: InstanceRois = inputs["current"]
    previous: InstanceRois = inputs["previous"]
    keypoints = inputs.get("previous_keypoints")
    count = len(current.present)
    out = InstanceRois.empty(count)
    for i in range(count):
        if not current.present[i]:
            continue
        out.present[i] = True
        kept = False
        if previous.present[i]:
            points = keypoints.xy[i].tolist() if keypoints is not None and keypoints.present[i] else []
            kept = _keep_previous(params, previous.rois[i].tolist(), current.rois[i].tolist(), points)
        chosen = previous if kept else current
        out.rois[i] = chosen.rois[i]
        out.instance_score[i] = chosen.instance_score[i]
    return {"rois": out}, None

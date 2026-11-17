"""The node ``boxes_from_points``: one box from the keypoints of each present instance row.

Implements: node.boxes_from_points
"""
from __future__ import annotations

import math
from typing import Any

from skellytracker.core.pipelines.config import BoxesFromPointsParams, derivation_sources
from skellytracker.core.pipelines.values import InstanceKeypoints, InstanceBoxes, PortInfo

from skellytracker.core.pipelines._runtime.context import FrameContext

# No required input is read when it is empty: an empty `keypoints` stops the node (Behaviour step 1).
READS_EMPTY: frozenset[str] = frozenset()
# The param of each size floor and the optional input that it needs (V-node.boxes_from_points-6).
FLOOR_INPUTS = {"min_previous_ratio": "previous_boxes", "min_reference_ratio": "reference_boxes"}


def normalize_radians(angle: float) -> float:
    """Return the angle in [-pi, pi): ``a - 2 pi floor((a + pi) / (2 pi))`` (Behaviour step 6).

    Implements: node.boxes_from_points
    """
    return angle - 2 * math.pi * math.floor((angle + math.pi) / (2 * math.pi))


def _weights(derivation: Any) -> dict[str, float]:
    """Return the weight of each source: 1 (passthrough), 1 / n (mean) or as given (weighted)."""
    if isinstance(derivation, dict):
        return dict(derivation)
    names = derivation_sources(derivation)
    return {name: 1.0 / len(names) for name in names}


def output_info(
    node_id: str, params: BoxesFromPointsParams, inputs: dict[str, PortInfo]
) -> tuple[dict[str, PortInfo], list[dict[str, Any]]]:
    """Check the load rules that need the ports, and return the facts of the output ``boxes``.

    Implements: node.boxes_from_points

    It checks V-node.boxes_from_points-2, -6 and -7. The params model checks -1, -3, -4 and -5.
    """
    keypoints = inputs["keypoints"]
    names, derived = set(keypoints.point_names), set(params.derived_points)
    used = [name for entry in params.points or [] for name in ([entry] if isinstance(entry, str) else entry)]
    used += [name for name in (params.alignment_start, params.alignment_end) if name is not None]
    unknown = [name for name in used if name not in names and name not in derived]
    unknown += [
        name for derivation in params.derived_points.values() for name in derivation_sources(derivation) if name not in names
    ]
    if unknown:
        raise ValueError(f"V-node.boxes_from_points-2: {node_id}: unknown point names {unknown!r}")
    for name, port in FLOOR_INPUTS.items():
        if getattr(params, name) is not None and port not in inputs:
            raise ValueError(f"V-node.boxes_from_points-6: {node_id}: {name} needs the input {port}")
    for port in FLOOR_INPUTS.values():
        info = inputs.get(port)
        if info is not None and (info.instance_source, info.max_instances) != (keypoints.instance_source, keypoints.max_instances):
            raise ValueError(
                f"V-node.boxes_from_points-7: {node_id}: {port} does not have the instance source and the rows of keypoints"
            )
    out = PortInfo("boxes", max_instances=keypoints.max_instances, instance_source=keypoints.instance_source, tracked=keypoints.tracked)
    return {"boxes": out}, []


def _row_box(
    params: BoxesFromPointsParams,
    names: tuple[str, ...],
    xy: list[list[float]],
    score: list[float],
    previous: list[float] | None,
    reference: list[float] | None,
) -> list[float] | None:
    """Return the box of one present row, or None for an empty row (Behaviour steps 3 to 10)."""
    found = {
        name: (x, y)
        for name, (x, y), value in zip(names, xy, score, strict=True)
        if value > params.score_threshold and not (math.isnan(x) or math.isnan(y))
    }
    for name, derivation in params.derived_points.items():
        weights = _weights(derivation)
        if all(source in found for source in weights):
            found[name] = (
                sum(w * found[source][0] for source, w in weights.items()),
                sum(w * found[source][1] for source, w in weights.items()),
            )
    points = []
    if params.points is None:
        # Each present point of the input; no point is required (step 5).
        points = [found[name] for name in names if name in found]
        if not points:
            return None
    for entry in params.points or []:
        present = [found[name] for name in ([entry] if isinstance(entry, str) else entry) if name in found]
        if not present:
            return None
        points.append(present[0])
    start, end = params.alignment_start, params.alignment_end
    uses_alignment = params.size_rule == "alignment" or params.target_rotation_deg is not None
    if uses_alignment and (start not in found or end not in found):
        return None
    rotation = 0.0
    if params.target_rotation_deg is not None:
        (x0, y0), (x1, y1) = found[start], found[end]
        rotation = normalize_radians(math.radians(params.target_rotation_deg) - math.atan2(-(y1 - y0), x1 - x0))
    c, s = math.cos(rotation), math.sin(rotation)
    if params.size_rule == "alignment":
        (x0, y0), (x1, y1) = found[start], found[end]
        cx, cy = x0, y0
        w = h = 2 * math.hypot(x1 - x0, y1 - y0)
    else:
        us = [x * c + y * s for x, y in points]
        vs = [-x * s + y * c for x, y in points]
        w, h = max(us) - min(us), max(vs) - min(vs)
        uc, vc = (max(us) + min(us)) / 2, (max(vs) + min(vs)) / 2
        cx, cy = uc * c - vc * s, uc * s + vc * c
    cx += w * params.shift_x * c - h * params.shift_y * s
    cy += w * params.shift_x * s + h * params.shift_y * c
    if params.square_long:
        w = h = max(w, h)
    w, h = w * params.expand_ratio, h * params.expand_ratio
    # Step 10: the floors keep the centre and the rotation.
    if params.min_previous_ratio is not None and previous is not None:
        w, h = max(w, params.min_previous_ratio * previous[2]), max(h, params.min_previous_ratio * previous[3])
    if params.min_reference_ratio is not None and reference is not None:
        w, h = max(w, params.min_reference_ratio * reference[2]), max(h, params.min_reference_ratio * reference[3])
    w, h = max(w, params.min_size_px), max(h, params.min_size_px)
    return [cx, cy, w, h, rotation]


def _row(boxes: InstanceBoxes | None, i: int) -> list[float] | None:
    """Return row ``i`` of an optional box input, or None when the row is not there."""
    if boxes is None or not boxes.present[i]:
        return None
    return boxes.boxes[i].tolist()


def run(
    params: BoxesFromPointsParams, inputs: dict[str, Any], state: Any, frame: FrameContext, infos: Any = None
) -> tuple[dict[str, InstanceBoxes], None]:
    """Make one box for each present row of ``keypoints``. The node keeps no state.

    Implements: node.boxes_from_points
    """
    keypoints: InstanceKeypoints = inputs["keypoints"]
    previous, reference = inputs.get("previous_boxes"), inputs.get("reference_boxes")
    count = len(keypoints.present)
    out = InstanceBoxes.empty(count)
    for i in range(count):
        if not keypoints.present[i]:
            continue
        roi = _row_box(
            params, keypoints.point_names, keypoints.xy[i].tolist(), keypoints.score[i].tolist(),
            _row(previous, i), _row(reference, i),
        )
        if roi is not None:
            out.boxes[i] = roi
            out.instance_score[i] = keypoints.instance_score[i]
            out.present[i] = True
    return {"boxes": out}, None



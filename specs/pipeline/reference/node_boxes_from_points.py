"""Reference implementation of the pipeline section node.boxes_from_points.

Note:

- Section ID: node.boxes_from_points.
- Source: the section text specs/pipeline/nodes/boxes_from_points.md. It follows the MediaPipe rect
  rules of MediaPipe-Exporter docs/mediapipe-whole-body.md (sections 1.2 and 1.3) at
  8f708a1ddecd8e035de15a5a9a7b652af035a58a. The size floors of step 10 follow
  skellytracker/core/temporal_processing/bbox_policy.py (BBoxPolicy.predict_bbox).
- Imported section modules: none. Fixtures: none.
"""

from __future__ import annotations

import math
import re
from typing import Any

# A derived point name (pipeline.file, Fields) and the weight-sum tolerance of the sidecar
# derived points (post.keypoint.schema, `keypoint.derived_points`).
NAME = r"^[a-z][a-z0-9_-]*$"
WEIGHT_SUM_TOLERANCE = 1e-6

# The defaults of BoxesFromPointsParams in specs/pipeline/reference/pipeline_config.py.
DEFAULTS = {
    "points": None,
    "derived_points": {},
    "size_rule": "bounds",
    "alignment_start": None,
    "alignment_end": None,
    "target_rotation_deg": None,
    "score_threshold": 0.0,
    "shift_x": 0.0,
    "shift_y": 0.0,
    "square_long": False,
    "expand_ratio": 1.0,
    "min_previous_ratio": None,
    "min_reference_ratio": None,
    "min_size_px": 0.0,
}
# The param of each size floor that needs an optional input (V-node.boxes_from_points-6).
FLOOR_INPUTS = {"min_previous_ratio": "previous_boxes", "min_reference_ratio": "reference_boxes"}


def sources(derivation: str | list[str] | dict[str, float]) -> list[str]:
    """The source names of a derived point: passthrough, mean or weighted (node.boxes_from_points, step 4)."""
    return [derivation] if isinstance(derivation, str) else list(derivation)


def weights_of(derivation: str | list[str] | dict[str, float]) -> dict[str, float]:
    """The weight of each source: 1 (passthrough), 1 / n (mean) or as given (weighted)."""
    if isinstance(derivation, dict):
        return dict(derivation)
    names = sources(derivation)
    return {name: 1.0 / len(names) for name in names}


def normalize_radians(angle: float) -> float:
    """Return the angle in [-π, π): a - 2π · floor((a + π) / (2π)) (node.boxes_from_points, step 6)."""
    return angle - 2 * math.pi * math.floor((angle + math.pi) / (2 * math.pi))


def uses_alignment(params: dict[str, Any]) -> bool:
    """True when the node uses alignment_start and alignment_end (node.boxes_from_points, Fields)."""
    return params["size_rule"] == "alignment" or params["target_rotation_deg"] is not None


def check_rules(params: dict[str, Any], names: list[str]) -> None:
    """Refuse params that break V-node.boxes_from_points-1 to -4, with ValueError (node.boxes_from_points)."""
    start, end = params["alignment_start"], params["alignment_end"]
    if params["size_rule"] == "alignment" and (start is None or end is None):
        raise ValueError("V-node.boxes_from_points-1: the size rule alignment needs alignment_start and alignment_end")
    if params["size_rule"] == "bounds" and params["target_rotation_deg"] is not None and (start is None or end is None):
        raise ValueError("V-node.boxes_from_points-4: bounds with a target rotation needs alignment_start and alignment_end")
    derived = list(params["derived_points"])
    if any(re.match(NAME, name) is None or name in names for name in derived):
        raise ValueError(f"V-node.boxes_from_points-3: a derived point name is not a name: {derived!r}")
    for name, derivation in params["derived_points"].items():
        weights = weights_of(derivation)
        if not weights or abs(math.fsum(weights.values()) - 1.0) > WEIGHT_SUM_TOLERANCE:
            raise ValueError(f"V-node.boxes_from_points-5: the weights of {name!r} do not sum to 1")
    used = [name for entry in params["points"] or [] for name in ([entry] if isinstance(entry, str) else entry)]
    used += [name for name in (start, end) if name is not None]
    weighted = [name for derivation in params["derived_points"].values() for name in sources(derivation)]
    unknown = [name for name in used if name not in names and name not in derived]
    unknown += [name for name in weighted if name not in names]
    if unknown:
        raise ValueError(f"V-node.boxes_from_points-2: unknown point names {unknown!r}")


def row_box(
    params: dict[str, Any],
    names: list[str],
    xy: list[list[float]],
    score: list[float],
    previous: list[float] | None = None,
    reference: list[float] | None = None,
) -> list[float] | None:
    """Return the box of one present row, or None for an empty row (node.boxes_from_points, steps 3 to 10).

    previous and reference are the rows of previous_boxes and reference_boxes, or None for a row that is
    not present.
    """
    found = {
        name: (x, y)
        for name, (x, y), value in zip(names, xy, score)  # noqa: B905 (one row of one input)
        if value > params["score_threshold"] and not (math.isnan(x) or math.isnan(y))
    }
    for name, derivation in params["derived_points"].items():
        weights = weights_of(derivation)
        # The score of a derived point is the minimum of the scores of its sources: present when each source is.
        if all(source in found for source in weights):
            found[name] = (
                sum(w * found[source][0] for source, w in weights.items()),
                sum(w * found[source][1] for source, w in weights.items()),
            )
    points = []
    if params["points"] is None:
        # Each present point of the input; no point is required (step 5).
        points = [found[name] for name in names if name in found]
        if not points:
            return None
    for entry in params["points"] or []:
        aliases = [entry] if isinstance(entry, str) else entry
        present = [found[name] for name in aliases if name in found]
        if not present:
            return None
        points.append(present[0])
    start, end = params["alignment_start"], params["alignment_end"]
    if uses_alignment(params) and (start not in found or end not in found):
        return None
    rotation = 0.0
    if params["target_rotation_deg"] is not None:
        (x0, y0), (x1, y1) = found[start], found[end]
        rotation = normalize_radians(math.radians(params["target_rotation_deg"]) - math.atan2(-(y1 - y0), x1 - x0))
    c, s = math.cos(rotation), math.sin(rotation)
    if params["size_rule"] == "alignment":
        (x0, y0), (x1, y1) = found[start], found[end]
        cx, cy = x0, y0
        w = h = 2 * math.hypot(x1 - x0, y1 - y0)
    else:
        us = [x * c + y * s for x, y in points]
        vs = [-x * s + y * c for x, y in points]
        w, h = max(us) - min(us), max(vs) - min(vs)
        uc, vc = (max(us) + min(us)) / 2, (max(vs) + min(vs)) / 2
        cx, cy = uc * c - vc * s, uc * s + vc * c
    cx += w * params["shift_x"] * c - h * params["shift_y"] * s
    cy += w * params["shift_x"] * s + h * params["shift_y"] * c
    if params["square_long"]:
        w = h = max(w, h)
    w, h = w * params["expand_ratio"], h * params["expand_ratio"]
    # Step 10: the floors keep the centre and the rotation.
    if params["min_previous_ratio"] is not None and previous is not None:
        w, h = max(w, params["min_previous_ratio"] * previous[2]), max(h, params["min_previous_ratio"] * previous[3])
    if params["min_reference_ratio"] is not None and reference is not None:
        w, h = max(w, params["min_reference_ratio"] * reference[2]), max(h, params["min_reference_ratio"] * reference[3])
    w, h = max(w, params["min_size_px"]), max(h, params["min_size_px"])
    return [cx, cy, w, h, rotation]


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Make one box for each present row of the keypoints (node.boxes_from_points).

    params holds the params of the node; a missing param takes its default. input holds point_names
    (the point names of the input port, known at load) and keypoints: None for an empty input, else
    xy (one list of [x, y] for each row), score and present, and optionally instance_score (one
    value for each row). The result holds boxes: None for an empty output, else one
    [cx, cy, w, h, rotation] or None for each row. When the keypoints have instance_score, the result
    also holds instance_score: the value of the keypoints row for each box row, 0 for an empty row
    (pipeline.graph, Behaviour item 8). input can hold previous_boxes and reference_boxes: None for an
    empty input, else one [cx, cy, w, h, rotation] or None for each row. An input with no such key has
    that port not connected.
    """
    params = {**DEFAULTS, **params}
    names, keypoints = input["point_names"], input["keypoints"]
    check_rules(params, names)
    for name, port in FLOOR_INPUTS.items():
        if params[name] is not None and port not in input:
            raise ValueError(f"V-node.boxes_from_points-6: {name} needs the input {port}")
    if keypoints is None:
        return {"boxes": None}
    count = len(keypoints["present"])
    previous = input.get("previous_boxes") or [None] * count
    reference = input.get("reference_boxes") or [None] * count
    rows = zip(keypoints["xy"], keypoints["score"], keypoints["present"], previous, reference)  # noqa: B905 (one length I)
    boxes = [
        row_box(params, names, xy, score, before, detected) if present else None
        for xy, score, present, before, detected in rows
    ]
    if "instance_score" not in keypoints:
        return {"boxes": boxes}
    scores = [0.0 if roi is None else value for roi, value in zip(boxes, keypoints["instance_score"])]  # noqa: B905
    return {"boxes": boxes, "instance_score": scores}

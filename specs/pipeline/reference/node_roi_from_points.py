"""Reference implementation of the pipeline section node.roi_from_points.

Note:

- Section ID: node.roi_from_points.
- Source: the section text specs/pipeline/nodes/roi_from_points.md. It follows the MediaPipe rect
  rules of MediaPipe-Exporter docs/mediapipe-whole-body.md (sections 1.2 and 1.3) at
  8f708a1ddecd8e035de15a5a9a7b652af035a58a.
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

# The defaults of RoiFromPointsParams in specs/pipeline/reference/pipeline_config.py.
DEFAULTS = {
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
}


def sources(derivation: str | list[str] | dict[str, float]) -> list[str]:
    """The source names of a derived point: passthrough, mean or weighted (node.roi_from_points, step 4)."""
    return [derivation] if isinstance(derivation, str) else list(derivation)


def weights_of(derivation: str | list[str] | dict[str, float]) -> dict[str, float]:
    """The weight of each source: 1 (passthrough), 1 / n (mean) or as given (weighted)."""
    if isinstance(derivation, dict):
        return dict(derivation)
    names = sources(derivation)
    return {name: 1.0 / len(names) for name in names}


def normalize_radians(angle: float) -> float:
    """Return the angle in [-π, π): a - 2π · floor((a + π) / (2π)) (node.roi_from_points, step 6)."""
    return angle - 2 * math.pi * math.floor((angle + math.pi) / (2 * math.pi))


def uses_alignment(params: dict[str, Any]) -> bool:
    """True when the node uses alignment_start and alignment_end (node.roi_from_points, Fields)."""
    return params["size_rule"] == "alignment" or params["target_rotation_deg"] is not None


def check_rules(params: dict[str, Any], names: list[str]) -> None:
    """Refuse params that break V-node.roi_from_points-1 to -4, with ValueError (node.roi_from_points)."""
    start, end = params["alignment_start"], params["alignment_end"]
    if params["size_rule"] == "alignment" and (start is None or end is None):
        raise ValueError("V-node.roi_from_points-1: the size rule alignment needs alignment_start and alignment_end")
    if params["size_rule"] == "bounds" and params["target_rotation_deg"] is not None and (start is None or end is None):
        raise ValueError("V-node.roi_from_points-4: bounds with a target rotation needs alignment_start and alignment_end")
    derived = list(params["derived_points"])
    if any(re.match(NAME, name) is None or name in names for name in derived):
        raise ValueError(f"V-node.roi_from_points-3: a derived point name is not a name: {derived!r}")
    for name, derivation in params["derived_points"].items():
        weights = weights_of(derivation)
        if not weights or abs(math.fsum(weights.values()) - 1.0) > WEIGHT_SUM_TOLERANCE:
            raise ValueError(f"V-node.roi_from_points-5: the weights of {name!r} do not sum to 1")
    used = [name for entry in params["points"] for name in ([entry] if isinstance(entry, str) else entry)]
    used += [name for name in (start, end) if name is not None]
    weighted = [name for derivation in params["derived_points"].values() for name in sources(derivation)]
    unknown = [name for name in used if name not in names and name not in derived]
    unknown += [name for name in weighted if name not in names]
    if unknown:
        raise ValueError(f"V-node.roi_from_points-2: unknown point names {unknown!r}")


def row_roi(
    params: dict[str, Any], names: list[str], xy: list[list[float]], score: list[float]
) -> list[float] | None:
    """Return the ROI of one present row, or None for an empty row (node.roi_from_points, steps 3 to 9)."""
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
    for entry in params["points"]:
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
    return [cx, cy, w * params["expand_ratio"], h * params["expand_ratio"], rotation]


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Make one ROI for each present row of the keypoints (node.roi_from_points).

    params holds the params of the node; a missing param takes its default. input holds point_names
    (the point names of the input port, known at load) and keypoints: None for an empty input, else
    xy (one list of [x, y] for each row), score and present, and optionally instance_score (one
    value for each row). The result holds rois: None for an empty output, else one
    [cx, cy, w, h, rotation] or None for each row. When the keypoints have instance_score, the result
    also holds instance_score: the value of the keypoints row for each ROI row, 0 for an empty row
    (pipeline.graph, Behaviour item 8).
    """
    params = {**DEFAULTS, **params}
    names, keypoints = input["point_names"], input["keypoints"]
    check_rules(params, names)
    if keypoints is None:
        return {"rois": None}
    rows = zip(keypoints["xy"], keypoints["score"], keypoints["present"])  # noqa: B905 (one length I)
    rois = [row_roi(params, names, xy, score) if present else None for xy, score, present in rows]
    if "instance_score" not in keypoints:
        return {"rois": rois}
    scores = [0.0 if roi is None else value for roi, value in zip(rois, keypoints["instance_score"])]  # noqa: B905
    return {"rois": rois, "instance_score": scores}

"""Reference implementation of the pipeline section node.merge (draft).

Note:

- Section ID: node.merge.
- Source: the section text specs/pipeline/nodes/merge.md.
- Imported section modules: node.first_of (node_first_of, the function is_empty), node.concat
  (the keypoints value form).
- Test: tools/tests/test_pipeline_glue_nodes.py (a named test, no vector file; ADR-3SF2 item 4).

A keypoints value has the form of node_concat: None (empty) or a mapping with `point_names`, `xyz`,
`score`, `instance_score`, `present`, `track_ids`, `instance_source` and `geometry`.
"""

from __future__ import annotations

import math
from typing import Any

import node_first_of

DEFAULTS = {"max_distance": None, "map": {}}


def present(point: list[float]) -> bool:
    """A point is present when its x and its y are not NaN (node.merge)."""
    return not (math.isnan(point[0]) or math.isnan(point[1]))


def bare(name: str) -> str:
    """The point name without its prefix: the text after the first dot (pipeline.graph)."""
    return name.partition(".")[2]


def slot_columns(params: dict[str, Any], source_names: list[str]) -> list[str]:
    """The added columns: `<slot>.<point>` for each slot, then for each source point (node.merge, Fields)."""
    return [f"{slot}.{bare(name)}" for slot in params["slots"] for name in source_names]


def check(params: dict[str, Any], target_names: list[str], source_names: list[str]) -> None:
    """Refuse params and inputs that break V-node.merge-1 and -2 (node.merge, Validation rules)."""
    columns = slot_columns(params, source_names)
    if set(columns) & set(target_names):
        raise ValueError("V-node.merge-1: a slot column is a point name of target")
    unknown = [name for name in params["slots"].values() if name not in target_names]
    unknown += [params["source_anchor"]] if params["source_anchor"] not in source_names else []
    unknown += [name for name in params["map"] if name not in target_names]
    unknown += [name for name in params["map"].values() if name not in columns]
    if unknown:
        raise ValueError(f"V-node.merge-2: unknown point names {unknown!r}")


def diagonal(row: list[list[float]]) -> float:
    """The diagonal of the axis-aligned box around the present points of one row (node.merge)."""
    points = [point for point in row if present(point)]
    if not points:
        return 0.0
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    return math.hypot(max(xs) - min(xs), max(ys) - min(ys))


def matches(params: dict[str, Any], target: dict[str, Any], source: dict[str, Any]) -> dict[tuple[int, int], int]:
    """Return (target row, slot index) -> source row: the greedy nearest match (node.merge, step 3)."""
    slots = list(params["slots"].values())
    anchor = source["point_names"].index(params["source_anchor"])
    pairs = []
    for i, row in enumerate(target["xyz"]):
        if not target["present"][i]:
            continue
        limit = math.inf if params["max_distance"] is None else params["max_distance"] * diagonal(row)
        for k, name in enumerate(slots):
            slot_point = row[target["point_names"].index(name)]
            for j, source_row in enumerate(source["xyz"]):
                source_point = source_row[anchor]
                if not (source["present"][j] and present(slot_point) and present(source_point)):
                    continue
                distance = math.hypot(source_point[0] - slot_point[0], source_point[1] - slot_point[1])
                if distance <= limit:
                    pairs.append((distance, j, i, k))
    found: dict[tuple[int, int], int] = {}
    used: set[int] = set()
    for _, j, i, k in sorted(pairs):
        if j not in used and (i, k) not in found:
            found[i, k] = j
            used.add(j)
    return found


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Add one column set for each slot to the target, and apply the map (node.merge, Behaviour).

    input holds `target`, `source` (keypoints values) and `source_names` (the point names of the
    source port, known at load). The result holds `keypoints`, None when `target` is empty.
    """
    unknown = sorted(set(params) - {"slots", "source_anchor", *DEFAULTS})
    if unknown:
        raise ValueError(f"unknown params {unknown}")
    params = {**DEFAULTS, **params}
    target, source, source_names = input["target"], input["source"], input["source_names"]
    check(params, [] if target is None else target["point_names"], source_names)
    if node_first_of.is_empty(target):
        return {"keypoints": None}
    if source is not None and source["geometry"] != target["geometry"]:
        raise ValueError("V-node.merge-3: target and source have different geometries")
    found = {} if node_first_of.is_empty(source) else matches(params, target, source)
    names = target["point_names"] + slot_columns(params, source_names)
    missing = [math.nan, math.nan, math.nan]
    xyz, score = [], []
    for i, row in enumerate(target["xyz"]):
        row_xyz, row_score = [list(point) for point in row], list(target["score"][i])
        for k in range(len(params["slots"])):
            j = found.get((i, k))
            row_xyz += [list(point) for point in source["xyz"][j]] if j is not None else [missing[:] for _ in source_names]
            row_score += list(source["score"][j]) if j is not None else [0.0] * len(source_names)
        for target_name, column in params["map"].items():
            t, c = names.index(target_name), names.index(column)
            if present(row_xyz[c]):
                row_xyz[t], row_score[t] = list(row_xyz[c]), row_score[c]
        xyz.append(row_xyz)
        score.append(row_score)
    return {
        "keypoints": {
            "point_names": names,
            "xyz": xyz,
            "score": score,
            "instance_score": list(target["instance_score"]),
            "present": list(target["present"]),
            "track_ids": list(target["track_ids"]),
            "instance_source": target["instance_source"],
            "geometry": target["geometry"],
        }
    }

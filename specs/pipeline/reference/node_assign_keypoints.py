"""Reference implementation of the pipeline section node.assign_keypoints (draft).

Note:

- Section ID: node.assign_keypoints.
- Source: the section text specs/pipeline/nodes/assign_keypoints.md.
- Imported section modules: node.first_of (node_first_of, the function is_empty).

A keypoints value is None (empty) or a mapping with `point_names`, `xy`,
`score`, `instance_score`, `present`, `track_ids`, `instance_source` and `geometry`, and `z` only
for a `3d` value.
"""

from __future__ import annotations

import math
from typing import Any

from scipy.optimize import linear_sum_assignment

import node_first_of

DEFAULTS = {"map": {}}


def present(point: list[float]) -> bool:
    """A point is present when its x and its y are not NaN (node.assign_keypoints)."""
    return not (math.isnan(point[0]) or math.isnan(point[1]))


def group(name: str) -> str:
    """The group of a point name: the text before the first `/` (pipeline.graph)."""
    return name.partition("/")[0]


def bare(name: str) -> str:
    """The point name without its group: the text after the first `/` (pipeline.graph)."""
    return name.partition("/")[2]


def check(params: dict[str, Any], target_names: list[str], source_names: list[str]) -> None:
    """Refuse params and inputs that break V-node.assign_keypoints-2, -4 and -5 (node.assign_keypoints, Validation rules)."""
    if len({group(name) for name in source_names}) != 1:
        raise ValueError("V-node.assign_keypoints-4: source does not have exactly one group")
    points = {bare(name) for name in source_names}
    unknown = [name for name in params["slots"].values() if name not in target_names]
    unknown += [params["source_anchor"]] if params["source_anchor"] not in source_names else []
    unknown += [name for name in params["map"] if name not in target_names]
    unknown += [v for v in params["map"].values() if group(v) not in params["slots"] or bare(v) not in points]
    if unknown:
        raise ValueError(f"V-node.assign_keypoints-2: unknown point names {unknown!r}")
    if "face" in params["slots"] and "face" in map(group, target_names):
        if not any(group(name) == "face" for name in params["map"]):
            raise ValueError("V-node.assign_keypoints-5: the slot face replaces the group face and map fills no point of it")


def fills(params: dict[str, Any], target_names: list[str], source_names: list[str], canonical: dict[str, str]) -> dict[str, str]:
    """Target point of a replaced group -> the slot point with the same canonical name (step 5)."""
    by_canonical = {canonical[name]: bare(name) for name in source_names if name in canonical}
    return {
        name: f"{group(name)}/{by_canonical[canonical[name]]}"
        for name in target_names
        if group(name) in params["slots"] and canonical.get(name) in by_canonical
    }


def diagonal(row: list[list[float]]) -> float:
    """The diagonal of the axis-aligned box around the present points of one row (node.assign_keypoints)."""
    points = [point for point in row if present(point)]
    if not points:
        return 0.0
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    return math.hypot(max(xs) - min(xs), max(ys) - min(ys))


def assignment(rows: list[int], columns: list[Any], cost: dict[tuple[int, Any], float]) -> list[tuple[int, Any]]:
    """The pairs of one assignment with the most pairs, then the smallest total (Hungarian method)."""
    if not rows or not columns:
        return []
    # A forbidden pair costs more than any assignment of allowed pairs, so the most pairs come first.
    big = (len(cost) + 1) * (max(cost.values(), default=0.0) + 1.0)
    r, c = linear_sum_assignment([[cost.get((j, col), big) for col in columns] for j in rows])
    return [(rows[a], columns[b]) for a, b in zip(r, c, strict=True) if (rows[a], columns[b]) in cost]


def matches(params: dict[str, Any], target: dict[str, Any], source: dict[str, Any]) -> dict[tuple[int, int], int]:
    """Return (target row, slot index) -> source row (node.assign_keypoints, step 3)."""
    anchor = source["point_names"].index(params["source_anchor"])
    rows = [j for j, row in enumerate(source["xy"]) if source["present"][j] and present(row[anchor])]
    columns, cost = [], {}
    for i, row in enumerate(target["xy"]):
        if not target["present"][i]:
            continue
        limit = params["max_distance"] * diagonal(row)
        for k, name in enumerate(params["slots"].values()):
            slot_point = row[target["point_names"].index(name)]
            if not present(slot_point):
                continue
            columns.append((i, k))  # in the tie order: target row, then slot
            for j in rows:
                point = source["xy"][j][anchor]
                distance = math.hypot(point[0] - slot_point[0], point[1] - slot_point[1])
                if distance <= limit:
                    cost[j, (i, k)] = distance
    best = assignment(rows, columns, cost)
    count, total = len(best), math.fsum(cost[pair] for pair in best)
    # The tie order: give each source row, from the lowest, its first slot that keeps the optimum.
    found: list[tuple[int, Any]] = []
    for n, j in enumerate(rows):
        used = {column for _, column in found}
        for column in columns:
            if (j, column) not in cost or column in used:
                continue
            free = [c for c in columns if c != column and c not in used]
            pairs = [*found, (j, column), *assignment(rows[n + 1 :], free, cost)]
            pair_total = math.fsum(cost[pair] for pair in pairs)
            # Equal totals: at most 1e-9 of the larger total apart (step 3); total stays the optimum.
            if len(pairs) == count and pair_total - total <= 1e-9 * max(pair_total, total):
                found.append((j, column))
                break
    return {column: j for j, column in found}


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Join the source rows to the slots of the target rows (node.assign_keypoints, Behaviour).

    input holds `target`, `source` (keypoints values), `target_names`, `source_names` and the
    optional `canonical` (known at load). The result holds `keypoints`, None when `target` is empty.
    """
    unknown = sorted(set(params) - {"slots", "source_anchor", "max_distance", *DEFAULTS})
    if unknown:
        raise ValueError(f"unknown params {unknown}")
    params = {**DEFAULTS, **params}
    target, source = input["target"], input["source"]
    target_names, source_names = input["target_names"], input["source_names"]
    check(params, target_names, source_names)
    if node_first_of.is_empty(target):
        return {"keypoints": None}
    if source is not None and source["geometry"] != target["geometry"]:
        raise ValueError("V-node.assign_keypoints-3: target and source have different geometries")
    found = {} if node_first_of.is_empty(source) else matches(params, target, source)
    target_groups = {group(name) for name in target_names}
    adding = [slot for slot in params["slots"] if slot not in target_groups]
    names = target_names + [f"{slot}/{bare(name)}" for slot in adding for name in source_names]
    filled = fills(params, target_names, source_names, input.get("canonical", {}))
    # A point is [x, y], or [x, y, z] for a `3d` value, so that x, y and z move together.
    depth = target["geometry"] == "3d"

    def joined(value: dict[str, Any]) -> list[list[list[float]]]:
        if not depth:
            return value["xy"]
        return [[[*point, z] for point, z in zip(xy, zs, strict=True)] for xy, zs in zip(value["xy"], value["z"], strict=True)]

    source_points = None if source is None else joined(source)
    missing = ([math.nan] * (3 if depth else 2), 0.0)
    xyz, score = [], []
    for i, row in enumerate(joined(target)):
        slot_points = {}
        for k, slot in enumerate(params["slots"]):
            j = found.get((i, k))
            for p, name in enumerate(source_names):
                slot_points[f"{slot}/{bare(name)}"] = missing if j is None else (source_points[j][p], source["score"][j][p])
        points = []
        for t, name in enumerate(target_names):
            if group(name) in params["slots"]:  # a replaced group
                point = slot_points[filled[name]] if name in filled else missing
                points.append(point if present(point[0]) else missing)
            else:
                points.append((row[t], target["score"][i][t]))
        points += [slot_points[name] for name in names[len(target_names) :]]
        for target_name, slot_point in params["map"].items():
            if present(slot_points[slot_point][0]):
                points[names.index(target_name)] = slot_points[slot_point]
        xyz.append([list(point) for point, _ in points])
        score.append([value for _, value in points])
    return {
        "keypoints": {
            "point_names": names,
            "xy": [[point[:2] for point in row] for row in xyz],
            **({"z": [[point[2] for point in row] for row in xyz]} if depth else {}),  # a `2d` value has no z
            "score": score,
            "instance_score": list(target["instance_score"]),
            "present": list(target["present"]),
            "track_ids": list(target["track_ids"]),
            "instance_source": target["instance_source"],
            "geometry": target["geometry"],
        }
    }

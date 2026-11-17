"""Reference implementation of the pipeline section node.merge (draft).

Note:

- Section ID: node.merge.
- Source: the section text specs/pipeline/nodes/merge.md.
- Imported section modules: node.first_of (node_first_of, the function is_empty).

A keypoints value is None (empty) or a mapping with `point_names`, `xy`, `score`,
`instance_score`, `present`, `track_ids`, `instance_source` and `geometry`, and `z` only for a
`3d` value.
"""

from __future__ import annotations

import math
from typing import Any

import node_first_of

DEFAULTS = {"map": {}}
PARTS = ("left_hand", "right_hand", "face")
REGION = {"left_hand": "hand", "right_hand": "hand", "face": "face"}


def group(name: str) -> str:
    """The group of a point name: the text before the first `/` (pipeline.graph)."""
    return name.partition("/")[0]


def bare(name: str) -> str:
    """The point name without its group: the text after the first `/` (pipeline.graph)."""
    return name.partition("/")[2]


def present(point: list[float]) -> bool:
    """A point is present when its x and its y are not NaN."""
    return not (math.isnan(point[0]) or math.isnan(point[1]))


def output_names(params: dict[str, Any], input: dict[str, Any], parts: dict[str, list[str]]) -> list[str]:
    """The point names of the output in the layout of `format` (node.merge, step 2), after the load checks."""
    for name, names in parts.items():
        if len({group(point) for point in names}) != 1:
            raise ValueError(f"V-node.merge-6: the part {name} does not have exactly one group")
    given = [value for value in (input.get("body"), *(input.get(name) for name in parts)) if value is not None]
    if len({value["instance_source"] for value in given}) > 1 or len({value["geometry"] for value in given}) > 1:
        raise ValueError("V-node.merge-7: the inputs must have one instance source and one geometry")
    schemas, regions = input.get("schemas", {}), input.get("regions", {})
    for name in parts:
        schema = schemas.get(name)
        if schema is not None and list(regions.get(schema, [])) != [REGION[name]]:
            raise ValueError(f"V-node.merge-8: the landmark schema {schema} of the part {name} is not a {REGION[name]} schema")
    body_groups: dict[str, list[str]] = {}
    for point in input["body_names"]:
        body_groups.setdefault(group(point), []).append(point)
    names: list[str] = []
    for item in input["layout"]:
        if item["name"] in body_groups:
            names += body_groups[item["name"]]
        elif item["name"] in parts:
            names += [f"{item['name']}/{bare(point)}" for point in parts[item["name"]]]
        else:
            names += [f"{item['name']}/{point}" for point in item["points"]]
    unknown = [point for point in params["map"] if point not in names]
    unknown += [
        point for point in params["map"].values()
        if group(point) not in parts or bare(point) not in {bare(name) for name in parts[group(point)]}
    ]
    if unknown:
        raise ValueError(f"V-node.merge-9: unknown point names {unknown!r}")
    return names


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Join the parts to `body`, row for row (node.merge, Behaviour).

    input holds `body` (a keypoints value) and `body_names`, and for each connected part
    `<part>` (a keypoints value) and `<part>_names`. It also holds `layout` (the groups of
    `format`: a list of `{name, points}`) and the optional `canonical`, `schemas` (part ->
    landmark schema or null) and `regions` (schema -> its group names), known at load. The result
    holds `keypoints`, None when `body` is empty.
    """
    unknown = sorted(set(params) - {"format", *DEFAULTS})
    if unknown or "format" not in params:
        raise ValueError(f"the params must have format and no unknown key: {unknown}")
    params = {**DEFAULTS, **params}
    parts = {name: input[f"{name}_names"] for name in PARTS if f"{name}_names" in input}
    names = output_names(params, input, parts)
    body = input["body"]
    if node_first_of.is_empty(body):
        return {"keypoints": None}
    depth = body["geometry"] == "3d"
    missing = ([math.nan] * (3 if depth else 2), 0.0)
    canonical = input.get("canonical", {})
    body_groups = {group(point) for point in input["body_names"]}

    def point_of(value: dict[str, Any], i: int, column: int) -> tuple[list[float], float]:
        xy = list(value["xy"][i][column])
        return ([*xy, value["z"][i][column]] if depth else xy), value["score"][i][column]

    xyz, score = [], []
    for i in range(len(body["present"])):
        if not body["present"][i]:  # a padding row stays a padding row
            xyz.append([missing[0]] * len(names))
            score.append([0.0] * len(names))
            continue
        points = dict.fromkeys(names, missing)
        for column, name in enumerate(input["body_names"]):
            if name in points:
                points[name] = point_of(body, i, column)
        for name in PARTS:
            value = input.get(name)
            if name not in parts or value is None or not value["present"][i]:
                continue  # no part row: the points of step 2 stay (step 5)
            part_names = parts[name]
            if name in body_groups:  # step 3: replace by canonical name
                by_canonical = {canonical[point]: column for column, point in enumerate(part_names) if point in canonical}
                for point in input["body_names"]:
                    if group(point) != name:
                        continue
                    column = by_canonical.get(canonical[point]) if point in canonical else None
                    found = missing if column is None else point_of(value, i, column)
                    points[point] = found if present(found[0]) else missing
            else:  # step 4: add the group
                for column, point in enumerate(part_names):
                    found = point_of(value, i, column)
                    points[f"{name}/{bare(point)}"] = found if present(found[0]) else missing
        for target, source in params["map"].items():  # step 6
            value = input.get(group(source))
            if value is not None and value["present"][i]:
                column = [bare(point) for point in parts[group(source)]].index(bare(source))
                found = point_of(value, i, column)
                if present(found[0]):
                    points[target] = found
        xyz.append([list(points[name][0]) for name in names])
        score.append([points[name][1] for name in names])
    return {
        "keypoints": {
            "point_names": names,
            "xy": [[point[:2] for point in row] for row in xyz],
            **({"z": [[point[2] for point in row] for row in xyz]} if depth else {}),  # a `2d` value has no z
            "score": score,
            "instance_score": list(body["instance_score"]),
            "present": list(body["present"]),
            "track_ids": list(body["track_ids"]),
            "instance_source": body["instance_source"],
            "geometry": body["geometry"],
        }
    }

"""Reference implementation of the pipeline section node.concat (draft).

Note:

- Section ID: node.concat.
- Source: the section text specs/pipeline/nodes/concat.md.
- Imported section modules: node.first_of (node_first_of, the function is_empty).

A keypoints value is None (empty) or a mapping with `point_names` (P names), `xy` (I rows of P
points [x, y]), `score` (I rows of P scores), `instance_score` (I values), `present` (I flags),
`track_ids` (I ids), and the facts of its output schema `instance_source` and `geometry`. Only a
`3d` value has `z` (I rows of P depths).
"""

from __future__ import annotations

import math
from typing import Any

import node_first_of

# The instance_score and the track_ids of a padding row (pipeline.outputs).
PADDING = {"instance_score": 0.0, "track_ids": -1}


def check(values: list[dict[str, Any] | None], point_names: list[list[str]]) -> None:
    """Refuse inputs that break V-node.concat-1 to -3 (node.concat, Validation rules)."""
    given = [value for value in values if value is not None]
    sources = {value["instance_source"] for value in given}
    if len(sources) > 1:
        raise ValueError(f"V-node.concat-1: the inputs have more than one instance source: {sorted(sources)}")
    names = [name for names in point_names for name in names]
    if len(names) != len(set(names)):
        raise ValueError("V-node.concat-2: the point names of the inputs collide")
    geometries = {value["geometry"] for value in given}
    if len(geometries) > 1:
        raise ValueError(f"V-node.concat-3: the inputs have more than one geometry: {sorted(geometries)}")


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Join row i of each input to row i of the output, in list order (node.concat, Behaviour).

    input holds `values`, one keypoints value for each item of the `inputs` list, and
    `point_names`, the point names of each input (from its output schema, known at load). The
    columns of an empty input are missing points. The result holds `keypoints`, None when each
    input is empty.
    """
    if params:
        raise ValueError(f"unknown params {sorted(params)}")
    values, point_names = input["values"], input["point_names"]
    check(values, point_names)
    given = [value for value in values if not node_first_of.is_empty(value)]
    if not given:
        return {"keypoints": None}
    rows = range(len(given[0]["present"]))

    def columns(value: dict[str, Any] | None, names: list[str], key: str, i: int) -> list[Any]:
        if node_first_of.is_empty(value):
            return {"xy": [[math.nan] * 2 for _ in names], "z": [math.nan] * len(names), "score": [0.0] * len(names)}[key]
        return list(value[key][i])

    def first_present(key: str, i: int) -> Any:
        return next((value[key][i] for value in given if value["present"][i]), PADDING[key])

    pairs = list(zip(values, point_names))  # noqa: B905 (one item for each input)

    def joined(key: str) -> list[list[Any]]:
        return [[item for value, names in pairs for item in columns(value, names, key, i)] for i in rows]

    return {
        "keypoints": {
            "point_names": [name for names in point_names for name in names],
            "xy": joined("xy"),
            **({"z": joined("z")} if given[0]["geometry"] == "3d" else {}),  # a `2d` value has no z
            "score": joined("score"),
            "instance_score": [first_present("instance_score", i) for i in rows],
            "present": [any(value["present"][i] for value in given) for i in rows],
            "track_ids": [first_present("track_ids", i) for i in rows],
            "instance_source": given[0]["instance_source"],
            "geometry": given[0]["geometry"],
        }
    }

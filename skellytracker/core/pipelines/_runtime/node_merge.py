"""The node ``merge``: join the parts ``left_hand``, ``right_hand`` and ``face`` to ``body``, row for row, in one layout of groups.

Implements: node.merge

The layout of ``format`` fixes the groups of the output and their order (``layout``). For each
group of the layout, the output takes the group of ``body``, or else the part of its name, or else
the points of the layout, all missing. A connected part replaces the group of its name in ``body``,
point for point by canonical name, or adds it. ``canonical`` of ``output_info`` and ``prepare``
maps a point name of ``body`` or of a part to its canonical point name. ``regions`` maps the name
of a landmark schema to the names of its groups. The caller finds both in the landmark schema
registry.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np

from skellytracker.core.pipelines._runtime import mediapipe_tasks
from skellytracker.core.pipelines._runtime.context import FrameContext
from skellytracker.core.pipelines.config import MERGE_PARTS, MediapipeTasksParams, MergeParams
from skellytracker.core.pipelines.values import Group, InstanceKeypoints, PortInfo

READS_EMPTY: frozenset[str] = frozenset()  # an empty `body` stops the node; an empty part does not
REGION = {"left_hand": "hand", "right_hand": "hand", "face": "face"}
"""The region of the landmark schema of each part (V-node.merge-8)."""
WHOLEBODY_SCHEMA = "COCO_WholeBody"
PART_WITHOUT_SCHEMA = "merge_part_without_landmark_schema"


def _bare(name: str) -> str:
    """Return the point name without its group: the text after the first ``/``."""
    return name.partition("/")[2]


def layout(format_name: str, registry: Mapping[str, Any]) -> PortInfo:
    """Return the groups and the point names of the layout of ``format`` (Behaviour step 5).

    ``wholebody`` is the group order and the points of ``COCO_WholeBody``. ``holistic`` is the
    group order and the points of the ``mediapipe_tasks`` variant ``holistic``.
    """
    if format_name == "holistic":
        return mediapipe_tasks.output_info("holistic", MediapipeTasksParams(variant="holistic"))[0]["keypoints"]
    schema = registry[WHOLEBODY_SCHEMA]
    names: list[str] = []
    groups: list[Group] = []
    for part in schema.groups:
        groups.append(Group(part.name, len(names), len(part.points), WHOLEBODY_SCHEMA))
        names += [f"{part.name}/{point}" for point in part.points]
    return PortInfo("keypoints", point_names=tuple(names), groups=tuple(groups))


def _fills(group: str, body: PortInfo, part: PortInfo, canonical: Mapping[str, str]) -> dict[str, str]:
    """Return body point of the replaced group -> the part point with the same canonical name (step 3)."""
    by_canonical = {canonical[name]: name for name in part.point_names if name in canonical}
    return {
        name: by_canonical[canonical[name]]
        for name in body.point_names
        if name.partition("/")[0] == group and canonical.get(name) in by_canonical
    }


def output_info(
    node_id: str, params: MergeParams, inputs: dict[str, PortInfo], canonical: Mapping[str, str] | None = None,
    layout_info: PortInfo | None = None, regions: Mapping[str, tuple[str, ...]] | None = None,
) -> tuple[dict[str, PortInfo], list[dict[str, Any]]]:
    """Check the load rules that need the ports, and return the facts of the output ``keypoints``.

    Implements: node.merge

    It checks V-node.merge-6, -7, -8 and the names of -9. It gives the load warnings
    ``merge_part_without_landmark_schema`` and ``merge_unfilled_points``.
    """
    body = inputs["body"]
    parts = {name: inputs[name] for name in MERGE_PARTS if name in inputs}
    for name, part in parts.items():
        if len(part.groups) != 1:
            raise ValueError(f"V-node.merge-6: {node_id}: the part {name} does not have exactly one group")
    if len({info.instance_source for info in inputs.values()}) > 1 or len({info.geometry for info in inputs.values()}) > 1:
        raise ValueError(f"V-node.merge-7: {node_id}: the inputs must have one instance source and one geometry")
    warnings: list[dict[str, Any]] = []
    for name, part in parts.items():
        schema = part.groups[0].landmark_schema
        if schema is None:
            warnings.append({
                "code": PART_WITHOUT_SCHEMA,
                "message": f"{node_id}: the part {name} has no landmark_schema, so the load cannot check its region",
                "node_ids": (node_id,), "details": {"part": name},
            })
        elif tuple((regions or {}).get(schema, ())) != (REGION[name],):
            raise ValueError(f"V-node.merge-8: {node_id}: the landmark schema {schema} of the part {name} is not a {REGION[name]} schema")
    assert layout_info is not None  # noqa: S101 (resolve gives the layout)
    body_groups = {group.name: group for group in body.groups}
    names: list[str] = []
    groups: list[Group] = []
    for wanted in layout_info.groups:
        if wanted.name in body_groups:
            given = body_groups[wanted.name]
            points, schema = body.point_names[given.start:given.start + given.count], given.landmark_schema
        elif wanted.name in parts:
            part = parts[wanted.name]
            points, schema = tuple(f"{wanted.name}/{_bare(point)}" for point in part.point_names), part.groups[0].landmark_schema
        else:
            points, schema = layout_info.point_names[wanted.start:wanted.start + wanted.count], wanted.landmark_schema
        groups.append(Group(wanted.name, len(names), len(points), schema))
        names += points
    kept = set(names)
    edges = [edge for edge in body.edges if edge[0] in kept and edge[1] in kept]
    for name, part in parts.items():
        if name not in body_groups:
            edges += [(f"{name}/{_bare(a)}", f"{name}/{_bare(b)}") for a, b in part.edges]
    unknown = [point for point in params.map if point not in kept]
    unknown += [
        point for point in params.map.values()
        if point.partition("/")[0] not in parts or _bare(point) not in {_bare(name) for name in parts[point.partition("/")[0]].point_names}
    ]
    if unknown:
        raise ValueError(f"V-node.merge-9: {node_id}: unknown point names {unknown!r}")
    unfilled: list[str] = []
    for name, part in parts.items():
        if name in body_groups:  # a replaced group
            filled = _fills(name, body, part, canonical or {})
            unfilled += [point for point in body.point_names if point.partition("/")[0] == name and point not in filled and point not in params.map]
    if unfilled:
        warnings.append({
            "code": "merge_unfilled_points",
            "message": f"{node_id}: {len(unfilled)} points of a replaced group are unfilled and no key of map names them",
            "node_ids": (node_id,), "details": {"points": unfilled},
        })
    out = PortInfo(
        "keypoints", max_instances=body.max_instances, instance_source=body.instance_source, point_names=tuple(names),
        groups=tuple(groups), geometry=body.geometry, depth_unit=body.depth_unit, edges=tuple(edges), tracked=body.tracked,
    )
    return {"keypoints": out}, warnings


@dataclass(frozen=True)
class MergePlan:
    """The column indexes of one ``merge`` node, fixed at load."""

    output: PortInfo
    body: tuple[np.ndarray, np.ndarray]
    """(output columns, body columns) of each point of ``body`` that the output keeps."""
    parts: tuple[tuple[str, np.ndarray, np.ndarray, np.ndarray], ...]
    """(part, cleared output columns, output columns, part columns) of each connected part, in the order of ``MERGE_PARTS``."""
    map: tuple[tuple[int, str, int], ...]
    """(output column, part, part column) of each entry of ``map``, in its order."""


def prepare(
    node_id: str, params: MergeParams, inputs_info: dict[str, PortInfo], outputs_info: dict[str, PortInfo],
    canonical: Mapping[str, str] | None = None,
) -> MergePlan:
    """Return the column indexes that ``run`` needs."""
    body, output = inputs_info["body"], outputs_info["keypoints"]
    column = {name: index for index, name in enumerate(output.point_names)}
    kept = [(column[name], index) for index, name in enumerate(body.point_names) if name in column]
    body_groups = {group.name for group in body.groups}
    parts = []
    for name in MERGE_PARTS:
        if name not in inputs_info:
            continue
        part = inputs_info[name]
        if name in body_groups:  # replace: clear the group, then fill it by canonical name
            group = next(group for group in output.groups if group.name == name)
            cleared = list(range(group.start, group.start + group.count))
            pairs = [(column[point], part.point_names.index(source)) for point, source in _fills(name, body, part, canonical or {}).items()]
        else:  # add: the columns of the part
            cleared = []
            pairs = [(column[f"{name}/{_bare(point)}"], index) for index, point in enumerate(part.point_names)]
        parts.append((name, np.array(cleared, dtype=np.int64), np.array([a for a, _ in pairs], dtype=np.int64), np.array([b for _, b in pairs], dtype=np.int64)))
    by_bare = {name: {_bare(point): index for index, point in enumerate(inputs_info[name].point_names)} for name in MERGE_PARTS if name in inputs_info}
    return MergePlan(
        output=output,
        body=(np.array([a for a, _ in kept], dtype=np.int64), np.array([b for _, b in kept], dtype=np.int64)),
        parts=tuple(parts),
        map=tuple((column[point], source.partition("/")[0], by_bare[source.partition("/")[0]][_bare(source)]) for point, source in params.map.items()),
    )


def _copy(out: InstanceKeypoints, rows: np.ndarray, out_columns: np.ndarray, part: InstanceKeypoints, part_columns: np.ndarray) -> None:
    """Copy each present part point of the rows ``rows`` to its output column: x, y, z, the score and the raw score."""
    present = rows[:, None] & ~np.isnan(part.xy[:, part_columns]).any(axis=2)
    row, k = np.nonzero(present)
    out.xy[row, out_columns[k]] = part.xy[row, part_columns[k]]
    out.score[row, out_columns[k]] = part.score[row, part_columns[k]]
    out.raw_score[row, out_columns[k]] = part.raw_score[row, part_columns[k]]
    if out.z is not None and part.z is not None:
        out.z[row, out_columns[k]] = part.z[row, part_columns[k]]


def run(
    params: MergeParams, inputs: dict[str, Any], state: Any, frame: FrameContext, infos: MergePlan
) -> tuple[dict[str, InstanceKeypoints], None]:
    """Join the rows of the parts to the rows of ``body``. The node keeps no state.

    Implements: node.merge
    """
    body: InstanceKeypoints = inputs["body"]
    out: InstanceKeypoints = infos.output.empty()
    out_columns, body_columns = infos.body
    out.xy[:, out_columns] = body.xy[:, body_columns]
    out.score[:, out_columns] = body.score[:, body_columns]
    out.raw_score[:, out_columns] = body.raw_score[:, body_columns]
    if out.z is not None:  # V-node.merge-7: each input then has z
        out.z[:, out_columns] = body.z[:, body_columns]
    for name, cleared, part_out, part_columns in infos.parts:
        part = inputs.get(name)
        if part is None or not part.present.any():
            continue  # a part with no present row leaves the points of body (step 4)
        rows = np.flatnonzero(part.present)
        out.xy[np.ix_(rows, cleared)] = np.nan
        out.score[np.ix_(rows, cleared)] = 0.0
        out.raw_score[np.ix_(rows, cleared)] = 0.0
        if out.z is not None:
            out.z[np.ix_(rows, cleared)] = np.nan
        _copy(out, part.present, part_out, part, part_columns)
    for column, name, point in infos.map:  # step 6
        part = inputs.get(name)
        if part is not None:
            _copy(out, part.present, np.array([column]), part, np.array([point]))
    out.instance_score[:] = body.instance_score
    out.present[:] = body.present
    out.track_ids[:] = body.track_ids
    # A body row that is not present stays a padding row.
    out.xy[~out.present] = np.nan
    if out.z is not None:
        out.z[~out.present] = np.nan
    out.score[~out.present] = 0.0
    out.raw_score[~out.present] = 0.0
    return {"keypoints": out}, None

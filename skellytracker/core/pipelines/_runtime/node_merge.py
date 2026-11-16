"""The node ``merge``: join the keypoints of a ``source`` to the slots of the rows of a ``target``.

Implements: node.merge

``canonical`` of ``output_info`` and ``prepare`` maps a point name of ``target`` or ``source`` to
its canonical point name (Behaviour step 5). The caller finds the names in the schema files of the
landmark schema registry. A point with no canonical name is not a key.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np

from skellytracker.core.pipelines._runtime.context import FrameContext
from skellytracker.core.pipelines.config import MergeParams
from skellytracker.core.pipelines.values import Group, InstanceKeypoints, PortInfo, is_empty

# An empty `source` does not stop the node: each slot point is then missing (Behaviour step 1).
READS_EMPTY: frozenset[str] = frozenset({"source"})


def _group(name: str) -> str:
    """Return the group of a point name: the text before the first ``/``."""
    return name.partition("/")[0]


def _bare(name: str) -> str:
    """Return the point name without its group: the text after the first ``/``."""
    return name.partition("/")[2]


def _fills(params: MergeParams, target: PortInfo, source: PortInfo, canonical: Mapping[str, str]) -> dict[str, str]:
    """Return target point of a replaced group -> the source point with the same canonical name (step 5)."""
    by_canonical = {canonical[name]: name for name in source.point_names if name in canonical}
    return {
        name: by_canonical[canonical[name]]
        for name in target.point_names
        if _group(name) in params.slots and canonical.get(name) in by_canonical
    }


def output_info(
    node_id: str, params: MergeParams, inputs: dict[str, PortInfo], canonical: Mapping[str, str] | None = None
) -> tuple[dict[str, PortInfo], list[dict[str, Any]]]:
    """Check the load rules that need the ports, and return the facts of the output ``keypoints``.

    Implements: node.merge

    It checks V-node.merge-2 (the names of the ports), -3, -4 and -5. The params model checks -1
    and the slot names of -2. It gives the load warning ``merge_unfilled_points``.
    """
    target, source = inputs["target"], inputs["source"]
    if len(source.groups) != 1:
        raise ValueError(f"V-node.merge-4: {node_id}: source does not have exactly one group")
    points = {_bare(name) for name in source.point_names}
    unknown = [name for name in params.slots.values() if name not in target.point_names]
    unknown += [params.source_anchor] if params.source_anchor not in source.point_names else []
    unknown += [name for name in params.map if name not in target.point_names]
    unknown += [value for value in params.map.values() if _group(value) not in params.slots or _bare(value) not in points]
    if unknown:
        raise ValueError(f"V-node.merge-2: {node_id}: unknown point names {unknown!r}")
    target_groups = {group.name for group in target.groups}
    if "face" in params.slots and "face" in target_groups and not any(_group(name) == "face" for name in params.map):
        raise ValueError(f"V-node.merge-5: {node_id}: the slot face replaces the group face and map fills no point of it")
    if target.geometry != source.geometry:
        raise ValueError(f"V-node.merge-3: {node_id}: target and source have different geometries")
    adding = [slot for slot in params.slots if slot not in target_groups]
    names, groups, edges = list(target.point_names), list(target.groups), list(target.edges)
    for slot in adding:
        groups.append(Group(slot, len(names), len(source.point_names), source.groups[0].landmark_schema))
        names += [f"{slot}/{_bare(name)}" for name in source.point_names]
        edges += [(f"{slot}/{_bare(a)}", f"{slot}/{_bare(b)}") for a, b in source.edges]
        edges.append((params.slots[slot], f"{slot}/{_bare(params.source_anchor)}"))
    out = PortInfo(
        "keypoints", max_instances=target.max_instances, instance_source=target.instance_source, point_names=tuple(names),
        groups=tuple(groups), geometry=target.geometry, depth_unit=target.depth_unit, edges=tuple(edges), tracked=target.tracked,
    )
    filled = _fills(params, target, source, canonical or {})
    unfilled = [
        name for name in target.point_names
        if _group(name) in params.slots and name not in filled and name not in params.map
    ]
    warnings = []
    if unfilled:
        warnings.append({
            "code": "merge_unfilled_points",
            "message": f"{node_id}: {len(unfilled)} points of a replaced group are unfilled and no key of map names them",
            "node_ids": (node_id,),
            "details": {"points": unfilled},
        })
    return {"keypoints": out}, warnings


@dataclass(frozen=True)
class MergePlan:
    """The column indexes of one ``merge`` node, fixed at load."""

    output: PortInfo
    source_anchor: int
    slot_anchors: tuple[int, ...]
    """The target column of the anchor of each slot, in the order of ``slots``."""
    replaced: tuple[int, ...]
    """The target columns of the replaced groups."""
    fills: tuple[tuple[int, int, int], ...]
    """``(target column, slot index, source column)`` of each filled point of a replaced group."""
    adding: tuple[tuple[int, int], ...]
    """``(slot index, first output column)`` of each adding slot."""
    map: tuple[tuple[int, int, int], ...]
    """``(output column, slot index, source column)`` of each entry of ``map``, in its order."""


def prepare(
    node_id: str, params: MergeParams, inputs_info: dict[str, PortInfo], outputs_info: dict[str, PortInfo],
    canonical: Mapping[str, str] | None = None,
) -> MergePlan:
    """Return the column indexes that ``run`` needs."""
    target, source, output = inputs_info["target"], inputs_info["source"], outputs_info["keypoints"]
    slots = list(params.slots)
    source_column = {_bare(name): column for column, name in enumerate(source.point_names)}
    filled = _fills(params, target, source, canonical or {})
    target_groups = {group.name for group in target.groups}
    return MergePlan(
        output=output,
        source_anchor=source.point_names.index(params.source_anchor),
        slot_anchors=tuple(target.point_names.index(name) for name in params.slots.values()),
        replaced=tuple(column for column, name in enumerate(target.point_names) if _group(name) in params.slots),
        fills=tuple(
            (target.point_names.index(name), slots.index(_group(name)), source.point_names.index(point))
            for name, point in filled.items()
        ),
        adding=tuple(
            (index, output.point_names.index(f"{slot}/{_bare(source.point_names[0])}"))
            for index, slot in enumerate(slots) if slot not in target_groups
        ),
        map=tuple(
            (output.point_names.index(name), slots.index(_group(point)), source_column[_bare(point)])
            for name, point in params.map.items()
        ),
    )


def _present(point: Any) -> bool:
    """A point is present when its x and its y are not NaN (Behaviour step 2)."""
    return not (math.isnan(point[0]) or math.isnan(point[1]))


def _diagonal(row: list[list[float]]) -> float:
    """Return the diagonal of the axis-aligned box around the present points of one row."""
    points = [point for point in row if _present(point)]
    if not points:
        return 0.0
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    return math.hypot(max(xs) - min(xs), max(ys) - min(ys))


def _assignment(rows: list[int], columns: list[Any], cost: dict[tuple[int, Any], float]) -> list[tuple[int, Any]]:
    """Return the pairs of one assignment with the most pairs, then the smallest total (Hungarian method)."""
    from scipy.optimize import linear_sum_assignment

    if not rows or not columns:
        return []
    # A forbidden pair costs more than any assignment of allowed pairs, so the most pairs come first.
    big = (len(cost) + 1) * (max(cost.values(), default=0.0) + 1.0)
    r, c = linear_sum_assignment([[cost.get((j, column), big) for column in columns] for j in rows])
    return [(rows[a], columns[b]) for a, b in zip(r, c, strict=True) if (rows[a], columns[b]) in cost]


def _matches(max_distance: float, plan: MergePlan, target: InstanceKeypoints, source: InstanceKeypoints) -> dict[tuple[int, int], int]:
    """Return (target row, slot index) -> source row (Behaviour step 3)."""
    anchors = source.xy[:, plan.source_anchor].tolist()
    rows = [j for j, point in enumerate(anchors) if source.present[j] and _present(point)]
    columns: list[Any] = []
    cost: dict[tuple[int, Any], float] = {}
    for i in np.flatnonzero(target.present).tolist():
        row = target.xy[i].tolist()
        limit = max_distance * _diagonal(row)
        for k, column in enumerate(plan.slot_anchors):
            slot_point = row[column]
            if not _present(slot_point):
                continue
            columns.append((i, k))  # in the tie order: target row, then slot
            for j in rows:
                distance = math.hypot(anchors[j][0] - slot_point[0], anchors[j][1] - slot_point[1])
                if distance <= limit:
                    cost[j, (i, k)] = distance
    best = _assignment(rows, columns, cost)
    count, total = len(best), math.fsum(cost[pair] for pair in best)
    # The tie order: give each source row, from the lowest, its first slot that keeps the optimum.
    found: list[tuple[int, Any]] = []
    for n, j in enumerate(rows):
        used = {column for _, column in found}
        for column in columns:
            if (j, column) not in cost or column in used:
                continue
            free = [c for c in columns if c != column and c not in used]
            pairs = [*found, (j, column), *_assignment(rows[n + 1:], free, cost)]
            pair_total = math.fsum(cost[pair] for pair in pairs)
            # Equal totals: at most 1e-9 of the larger total apart (step 3); total stays the optimum.
            if len(pairs) == count and pair_total - total <= 1e-9 * max(pair_total, total):
                found.append((j, column))
                break
    return {column: j for j, column in found}


def _copy(out: InstanceKeypoints, i: int, column: Any, source: InstanceKeypoints, j: int, point: Any) -> None:
    """Copy x, y, z and the score of the source points to the columns of row ``i``."""
    out.xy[i, column] = source.xy[j, point]
    out.score[i, column] = source.score[j, point]
    if out.z is not None and source.z is not None:
        out.z[i, column] = source.z[j, point]


def run(
    params: MergeParams, inputs: dict[str, Any], state: Any, frame: FrameContext, infos: MergePlan
) -> tuple[dict[str, InstanceKeypoints], None]:
    """Join the source rows to the slots of the target rows. The node keeps no state.

    Implements: node.merge
    """
    target: InstanceKeypoints = inputs["target"]
    source: InstanceKeypoints = inputs["source"]
    out: InstanceKeypoints = infos.output.empty()
    if is_empty(target):
        return {"keypoints": out}, None
    found = {} if is_empty(source) else _matches(params.max_distance, infos, target, source)
    width = len(target.point_names)
    out.xy[:, :width] = target.xy
    if out.z is not None:  # V-node.merge-3: target and source then have z
        out.z[:, :width] = target.z
    out.score[:, :width] = target.score
    # Step 5: a point of a replaced group is missing until a slot point fills it.
    replaced = list(infos.replaced)
    out.xy[:, replaced] = np.nan
    if out.z is not None:
        out.z[:, replaced] = np.nan
    out.score[:, replaced] = 0.0
    count = len(source.point_names)
    for (i, k), j in found.items():
        for column, slot, point in infos.fills:
            if slot == k and _present(source.xy[j, point]):
                _copy(out, i, column, source, j, point)
        for slot, start in infos.adding:
            if slot == k:
                _copy(out, i, slice(start, start + count), source, j, slice(None))
    # Step 6: a present slot point replaces the target point, in the order of `map`.
    for column, slot, point in infos.map:
        for (i, k), j in found.items():
            if slot == k and _present(source.xy[j, point]):
                _copy(out, i, column, source, j, point)
    out.instance_score[:] = target.instance_score
    out.present[:] = target.present
    out.track_ids[:] = target.track_ids
    # A target row that is not present stays a padding row.
    out.xy[~out.present] = np.nan
    if out.z is not None:
        out.z[~out.present] = np.nan
    out.score[~out.present] = 0.0
    return {"keypoints": out}, None

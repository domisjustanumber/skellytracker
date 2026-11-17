"""The canonical form of a `keypoints` output.

Implements: pipeline.outputs
Implements: post.keypoint.canonical_mapping

The canonical form maps the groups that one node or one `merge` slot made together, with the
canonical mapping of their landmark schema. A group with a null `landmark_schema` passes through.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from skellytracker.core.detectors.processing.post.keypoint_schema import derived_points
from skellytracker.core.model_spec.landmark_schemas import load_landmark_schema_registry, source_names
from skellytracker.core.pipelines.values import Group, InstanceKeypoints


@dataclass(frozen=True)
class CanonicalKeypoints:
    """The canonical form of one `keypoints` value: `I` rows, each with `C` canonical points."""

    point_names: tuple[str, ...]
    """``(C,)``: the `canonical_names` of the output schema. The field has the name of the field of a `keypoints` value."""
    xy: NDArray[np.float64]
    """``(I, C, 2)``: x and y of each point, in source-image pixels. A missing point is NaN."""
    score: NDArray[np.float64]
    """``(I, C)``. A missing point has 0."""
    groups: tuple[Group, ...]
    """The passthrough groups, with `start` and `count` in the canonical columns."""
    z: NDArray[np.float64] | None = None
    """``(I, C)``, only for a `3d` output: the depth of each point. A missing point is NaN. `None` for a `2d` output."""

    @property
    def geometry(self) -> str:
        """`"3d"` when the value has `z`, else `"2d"`."""
        return "2d" if self.z is None else "3d"


@dataclass(frozen=True)
class _Plan:
    names: tuple[str, ...]
    copies: tuple[tuple[int, int], ...]  # (canonical column, input column) of each point that keeps its values
    derived: tuple[tuple[int, Any], ...]  # (canonical column, derivation with input point names) of each mean or weighted point
    groups: tuple[Group, ...]


def _groups(groups: Sequence[Group | Mapping[str, Any]]) -> tuple[Group, ...]:
    return tuple(
        group if isinstance(group, Group) else Group(group["name"], group["start"], group["count"], group["landmark_schema"])
        for group in groups
    )


@lru_cache(maxsize=64)
def _plan(groups: tuple[Group, ...], point_names: tuple[str, ...], user_root: Path | None) -> _Plan:
    registry = load_landmark_schema_registry(user_root)
    by_name = {group.name: group for group in groups}
    names: list[str] = []
    copies: list[tuple[int, int]] = []
    derived: list[tuple[int, Any]] = []
    passthrough: list[Group] = []
    for group in groups:
        region, read, column = None, False, {}
        if group.landmark_schema is not None:
            if group.landmark_schema not in registry:
                raise ValueError(f"the group {group.name!r} names the landmark schema {group.landmark_schema!r}, which is not in the registry")
            schema = registry[group.landmark_schema]
            mapping = schema.canonical_mapping
            if len(schema.groups) == 1:
                # A group of a schema with one group stands alone. Its name is the id of its node or its slot.
                region = mapping.get(schema.groups[0].name)
                column = {point: group.start + position for position, point in enumerate(schema.groups[0].points)}
            else:
                # The groups of a schema with two or more groups come from one node, with the names of the schema.
                region = mapping.get(group.name)
                column = {
                    point: by_name[part.name].start + position
                    for part in schema.groups if part.name in by_name for position, point in enumerate(part.points)
                }
                sources = {point for entries in mapping.values() for source in entries.values() for point in source_names(source) or []}
                read = any(point in sources for part in schema.groups if part.name == group.name for point in part.points)
        if region is None and read:
            continue  # A group that a region reads and that is not a region gives no canonical point.
        if region is None:
            passthrough.append(Group(group.name, len(names), group.count, group.landmark_schema))
            copies += [(len(names) + position, group.start + position) for position in range(group.count)]
            names += point_names[group.start:group.start + group.count]
            continue
        for canonical, source in region.items():
            missing = [point for point in source_names(source) or [] if point not in column]
            if missing:
                raise ValueError(f"{group.name}/{canonical}: the output has no column for the source points {missing}")
            if isinstance(source, str):
                copies.append((len(names), column[source]))
            elif isinstance(source, Mapping):
                derived.append((len(names), {point_names[column[point]]: weight for point, weight in source.items()}))
            else:
                derived.append((len(names), [point_names[column[point]] for point in source]))
            names.append(f"{group.name}/{canonical}")
    return _Plan(tuple(names), tuple(copies), tuple(derived), tuple(passthrough))


def canonical_names(
    groups: Sequence[Group | Mapping[str, Any]], point_names: Sequence[str], user_root: Path | None = None
) -> tuple[str, ...]:
    """Return the `canonical_names` of an output with these `groups` and `point_names`.

    `groups` holds `Group` items or `{name, start, count, landmark_schema}` mappings, in column
    order. `point_names` gives the names of a passthrough group. `user_root` is the user sidecar
    root of the landmark schema registry.
    """
    return _plan(_groups(groups), tuple(point_names), user_root).names


def canonical_edges(
    groups: Sequence[Group | Mapping[str, Any]],
    point_names: Sequence[str],
    edges: Sequence[Sequence[str]],
    user_root: Path | None = None,
) -> tuple[tuple[str, str], ...]:
    """Return the `canonical_edges` of an output with these `groups`, `point_names` and `edges`.

    Each point that the canonical form copies or renames gets its canonical name. The result keeps
    the order of `edges`. It leaves out an edge with a point that has no canonical name, an edge
    whose two points get one canonical name, and a pair that an earlier edge gave, in either
    direction. A mean or a weighted canonical point is in no edge.
    """
    plan = _plan(_groups(groups), tuple(point_names), user_root)
    renamed: dict[str, str] = {}
    for target, source in plan.copies:
        renamed.setdefault(point_names[source], plan.names[target])
    kept: dict[frozenset[str], tuple[str, str]] = {}
    for start, end in edges:
        if start in renamed and end in renamed and renamed[start] != renamed[end]:
            kept.setdefault(frozenset((renamed[start], renamed[end])), (renamed[start], renamed[end]))
    return tuple(kept.values())


def to_canonical(keypoints_value: InstanceKeypoints, output_schema: Mapping[str, Any], *, user_root: Path | None = None) -> CanonicalKeypoints:
    """Return the canonical form of the value of one `keypoints` output.

    `output_schema` is the schema of that output: it gives `groups` and `canonical_names`. A
    passthrough point keeps its position and its score. A mean or a weighted point is missing when
    one or more of its sources are missing, and its score is the minimum of the scores of its sources.
    A source is missing when its `raw_score` is 0 or less: a mapped score of a present point can be
    0.0 in float32. The result has `z` only when the value has `z`, and it has no `raw_score`.
    """
    plan = _plan(_groups(output_schema["groups"]), tuple(keypoints_value.point_names), user_root)
    if plan.names != tuple(output_schema["canonical_names"]):
        raise ValueError("canonical_names of the output schema does not agree with its groups and the point names of the value")
    # One array of the coordinates, (I, P, 2) or (I, P, 3), so that x, y and z get the same mapping.
    z = keypoints_value.z
    points = keypoints_value.xy if z is None else np.concatenate([keypoints_value.xy, z[..., None]], axis=2)
    rows = points.shape[0]
    xyz = np.full((rows, len(plan.names), points.shape[2]), np.nan)
    score = np.zeros((rows, len(plan.names)))
    if plan.copies:
        target, source = (list(columns) for columns in zip(*plan.copies, strict=True))
        xyz[:, target] = points[:, source]
        score[:, target] = keypoints_value.score[:, source]
    if plan.derived:
        target = [column for column, _ in plan.derived]
        xyz[:, target], score[:, target] = derived_points(
            points, keypoints_value.score, keypoints_value.point_names,
            {str(column): derivation for column, derivation in plan.derived}, present=keypoints_value.raw_score > 0,
        )
    return CanonicalKeypoints(plan.names, xyz[..., :2], score, tuple(plan.groups), None if z is None else xyz[..., 2])

"""The node ``concat``: join the keypoint sets of one instance source into one keypoint set.

Implements: node.concat
"""
from __future__ import annotations

from typing import Any

import numpy as np

from skellytracker.core.pipelines._runtime.context import FrameContext
from skellytracker.core.pipelines.config import NoParams
from skellytracker.core.pipelines.values import Group, InstanceKeypoints, PortInfo, is_empty

# The node runs with an empty input and gives missing points in its columns (Behaviour).
READS_EMPTY: frozenset[str] = frozenset({"*"})


def output_info(node_id: str, params: NoParams, inputs: list[PortInfo]) -> tuple[dict[str, PortInfo], list[dict[str, Any]]]:
    """Check the load rules of the node, and return the facts of the output ``keypoints``.

    Implements: node.concat

    It checks V-node.concat-1, -2 and -3. The output has the points, the groups and the edges of
    each input, in the order of the list.
    """
    sources = {info.instance_source for info in inputs}
    if len(sources) > 1:
        raise ValueError(f"V-node.concat-1: {node_id}: the inputs have more than one instance source: {sorted(map(str, sources))}")
    names = tuple(name for info in inputs for name in info.point_names)
    if len(names) != len(set(names)):
        raise ValueError(f"V-node.concat-2: {node_id}: the point names of the inputs collide")
    geometries = {info.geometry for info in inputs}
    if len(geometries) > 1:
        raise ValueError(f"V-node.concat-3: {node_id}: the inputs have more than one geometry: {sorted(map(str, geometries))}")
    groups, start = [], 0
    for info in inputs:
        groups += [Group(group.name, start + group.start, group.count, group.landmark_schema) for group in info.groups]
        start += len(info.point_names)
    first = inputs[0]
    out = PortInfo(
        "keypoints", max_instances=first.max_instances, instance_source=first.instance_source, point_names=names,
        groups=tuple(groups), geometry=first.geometry, depth_unit=first.depth_unit,
        edges=tuple(edge for info in inputs for edge in info.edges), tracked=first.tracked,
    )
    return {"keypoints": out}, []


def prepare(node_id: str, params: NoParams, inputs_info: list[PortInfo], outputs_info: dict[str, PortInfo]) -> PortInfo:
    """Return the facts of the output: ``run`` needs its point names and its empty value."""
    return outputs_info["keypoints"]


def run(params: NoParams, inputs: list[Any], state: Any, frame: FrameContext, infos: PortInfo) -> tuple[dict[str, InstanceKeypoints], None]:
    """Join row ``i`` of each input to row ``i`` of the output. The node keeps no state.

    Implements: node.concat
    """
    out = infos.empty()
    column = 0
    for value in inputs:
        count = len(value.point_names)
        if not is_empty(value):  # the columns of an empty input stay missing points
            out.xyz[:, column:column + count] = value.xyz
            out.score[:, column:column + count] = value.score
        column += count
    # The last input first: the first input whose row is present then gives the row values.
    for value in reversed(inputs):
        rows = value.present
        out.instance_score[rows] = value.instance_score[rows]
        out.track_ids[rows] = value.track_ids[rows]
        out.present[rows] = True
    # A row with no present input row is a padding row.
    out.xyz[~out.present] = np.nan
    out.score[~out.present] = 0.0
    return {"keypoints": out}, None

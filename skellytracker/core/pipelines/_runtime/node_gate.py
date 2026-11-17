"""The node ``gate``: pass ``value`` or give an empty output, from a test on ``condition``.

Implements: node.gate
"""
from __future__ import annotations

import dataclasses
from typing import Any

import numpy as np

from skellytracker.core.pipelines._runtime.context import FrameContext
from skellytracker.core.pipelines.config import GateParams
from skellytracker.core.pipelines.values import InstanceBoxes, InstanceKeypoints, PortInfo, is_empty

# The mode `is_empty` tests for an empty `condition`, so the node gets it (Behaviour step 1).
READS_EMPTY: frozenset[str] = frozenset({"condition"})
INSTANCE_TYPES = ("boxes", "keypoints")
SCORED_TYPES = INSTANCE_TYPES
# The modes of a `flag` condition (V-node.gate-4).
FLAG_MODES = ("is_true", "is_false")


def output_info(
    node_id: str, params: GateParams, inputs: dict[str, PortInfo]
) -> tuple[dict[str, PortInfo], list[dict[str, Any]]]:
    """Check the load rules that need the ports, and return the facts of the output ``value``.

    Implements: node.gate

    It checks V-node.gate-2, -3 and -4. The params model checks -1. The output has the facts of the
    input ``value``.
    """
    value, condition = inputs["value"], inputs["condition"]
    if params.mode in FLAG_MODES and condition.port_type != "flag":
        raise ValueError(f"V-node.gate-4: {node_id}: {params.mode} needs a flag condition, not {condition.port_type}")
    if params.mode not in FLAG_MODES and condition.port_type == "flag":
        raise ValueError(f"V-node.gate-2: {node_id}: {params.mode} needs a condition that is not a flag")
    if params.mode == "score_above" and condition.port_type not in SCORED_TYPES:
        raise ValueError(f"V-node.gate-2: {node_id}: score_above needs a boxes or keypoints condition, not {condition.port_type}")
    by_row = value.port_type in INSTANCE_TYPES and condition.port_type in INSTANCE_TYPES
    if by_row and value.max_instances != condition.max_instances:
        raise ValueError(f"V-node.gate-3: {node_id}: value has {value.max_instances} rows and condition has {condition.max_instances}")
    return {"value": value}, []


def prepare(node_id: str, params: GateParams, inputs_info: dict[str, PortInfo], outputs_info: dict[str, PortInfo]) -> dict[str, PortInfo]:
    """Return the facts of the inputs: ``run`` needs their port types."""
    return dict(inputs_info)


def _row_score(condition: Any, i: int) -> float:
    """Return the score of one present row of ``condition`` (Fields, "Score of a row")."""
    if isinstance(condition, InstanceBoxes):
        return float(condition.instance_score[i])
    valid = ~np.isnan(condition.xy[i]).any(axis=1)
    seen = condition.score[i][valid].tolist()
    return sum(seen) / len(seen) if seen else 0.0


def _passes(params: GateParams, condition: Any, rows: list[int]) -> bool:
    """The test of a list of present rows of ``condition`` (Behaviour step 2). ``rows`` holds row indexes."""
    if params.mode == "is_empty":
        return not rows
    if params.mode == "is_present":
        return bool(rows)
    return any(_row_score(condition, i) > params.threshold for i in rows)


def keep_rows(value: Any, keep: np.ndarray) -> Any:
    """Return an instance value with the rows of ``value`` where ``keep`` is true, and padding rows elsewhere."""
    padding = type(value).empty(value.point_names, len(keep)) if isinstance(value, InstanceKeypoints) else type(value).empty(len(keep))
    fields = {}
    for field in dataclasses.fields(value):
        given = getattr(value, field.name)
        if not isinstance(given, np.ndarray):
            continue
        mask = keep.reshape((-1,) + (1,) * (given.ndim - 1))
        fields[field.name] = np.where(mask, given, getattr(padding, field.name))
    return dataclasses.replace(value, **fields)


def run(
    params: GateParams, inputs: dict[str, Any], state: Any, frame: FrameContext, infos: dict[str, PortInfo]
) -> tuple[dict[str, Any], None]:
    """Pass ``value`` or give an empty output. The node keeps no state.

    Implements: node.gate
    """
    value, condition = inputs["value"], inputs["condition"]
    value_info, condition_type = infos["value"], infos["condition"].port_type
    if is_empty(value):
        return {"value": value_info.empty()}, None
    if condition_type == "flag":  # one test for the frame (step 5)
        return {"value": value if bool(condition) == (params.mode == "is_true") else value_info.empty()}, None
    condition_rows = condition_type in INSTANCE_TYPES
    if value_info.port_type in INSTANCE_TYPES and condition_rows:
        # Row by row (step 3).
        present = np.zeros(len(value.present), dtype=bool) if condition is None else condition.present
        keep = np.array([
            bool(value.present[i]) and _passes(params, condition, [i] if present[i] else []) for i in range(len(value.present))
        ], dtype=bool)
        return {"value": keep_rows(value, keep)}, None
    # One test (step 4).
    if condition is None:
        rows: list[int] = []
    elif condition_rows:
        rows = [int(i) for i in np.flatnonzero(condition.present)]
    else:
        rows = [0]
    return {"value": value if _passes(params, condition, rows) else value_info.empty()}, None

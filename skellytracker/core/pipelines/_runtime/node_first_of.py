"""The node ``first_of``: the first of its inputs that is not empty.

Implements: node.first_of
"""
from __future__ import annotations

from typing import Any

from skellytracker.core.pipelines._runtime.context import FrameContext
from skellytracker.core.pipelines.config import NoParams
from skellytracker.core.pipelines.values import PortInfo, is_empty

# The node skips each empty input, so no empty input stops it (Behaviour).
READS_EMPTY: frozenset[str] = frozenset({"*"})
INSTANCE_TYPES = ("roi", "keypoints", "detections")


def output_info(node_id: str, params: NoParams, inputs: list[PortInfo]) -> tuple[dict[str, PortInfo], list[dict[str, Any]]]:
    """Check the load rule that needs the ports, and return the facts of the output ``value``.

    Implements: node.first_of

    It checks V-node.first_of-2. ``check_structure`` checks -1. The output has the facts of the
    first input.
    """
    first = inputs[0]
    if first.port_type in INSTANCE_TYPES:
        sources = {info.instance_source for info in inputs}
        if len(sources) > 1:
            raise ValueError(f"V-node.first_of-2: {node_id}: the inputs have more than one instance source: {sorted(map(str, sources))}")
        if any(info.groups != first.groups for info in inputs):
            raise ValueError(f"V-node.first_of-2: {node_id}: the inputs do not have the same groups")
    return {"value": first}, []


def prepare(node_id: str, params: NoParams, inputs_info: list[PortInfo], outputs_info: dict[str, PortInfo]) -> PortInfo:
    """Return the facts of the output: ``run`` gives its empty value when each input is empty."""
    return outputs_info["value"]


def run(params: NoParams, inputs: list[Any], state: Any, frame: FrameContext, infos: PortInfo) -> tuple[dict[str, Any], None]:
    """Give the first input that is not empty, in list order. The node keeps no state.

    Implements: node.first_of
    """
    return {"value": next((value for value in inputs if not is_empty(value)), infos.empty())}, None

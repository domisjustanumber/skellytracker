"""The node ``flag_when``: make a ``flag`` from one test on all present rows of a ``boxes`` or ``keypoints`` value.

Implements: node.flag_when
"""
from __future__ import annotations

from typing import Any

import numpy as np

from skellytracker.core.pipelines._runtime import node_gate
from skellytracker.core.pipelines._runtime.context import FrameContext
from skellytracker.core.pipelines.config import FlagWhenParams
from skellytracker.core.pipelines.values import PortInfo

# The node runs with an empty `value`: the mode `is_empty` tests for it (Behaviour step 1).
READS_EMPTY: frozenset[str] = frozenset({"value"})


def output_info(node_id: str, params: FlagWhenParams, inputs: dict[str, PortInfo]) -> tuple[dict[str, PortInfo], list[dict[str, Any]]]:
    """Return the facts of the output ``flag``. The params model checks V-node.flag_when-1."""
    return {"flag": PortInfo("flag")}, []


def run(params: FlagWhenParams, inputs: dict[str, Any], state: Any, frame: FrameContext, infos: Any) -> tuple[dict[str, bool], None]:
    """Give true when the test passes, else false. The node keeps no state.

    Implements: node.flag_when
    """
    value = inputs["value"]
    rows = [] if value is None else np.flatnonzero(value.present).tolist()
    if params.mode == "is_empty":
        flag = not rows
    elif params.mode == "is_present":
        flag = bool(rows)
    else:  # the score of a row is that of `gate` (Fields)
        flag = any(node_gate._row_score(value, i) > params.threshold for i in rows)
    return {"flag": flag}, None

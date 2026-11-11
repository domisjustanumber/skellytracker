"""Reference implementation of the pipeline section node.gate.

Note:

- Section ID: node.gate.
- Source: the section text specs/pipeline/nodes/gate.md.
- Imported section modules: none. Fixtures: none.
"""

from __future__ import annotations

import math
from typing import Any

INSTANCE_TYPES = ("roi", "keypoints", "detections")
SCORED_TYPES = ("detections", "keypoints")


def score(condition_type: str, row: dict[str, Any]) -> float:
    """Return the score of one present row of condition (node.gate, Fields).

    A detections row holds confidence. A keypoints row holds xy and visibility: the score is the
    mean visibility of the points whose x and y are not NaN, or 0 when each point is NaN.
    """
    if condition_type == "detections":
        return row["confidence"]
    seen = [v for (x, y), v in zip(row["xy"], row["visibility"]) if not (math.isnan(x) or math.isnan(y))]  # noqa: B905 (one row)
    return sum(seen) / len(seen) if seen else 0.0


def passes(params: dict[str, Any], condition_type: str, rows: list[Any]) -> bool:
    """The test of a list of present rows of condition (node.gate, step 2)."""
    if params["mode"] == "is_empty":
        return not rows
    if params["mode"] == "is_present":
        return bool(rows)
    return any(score(condition_type, row) > params["threshold"] for row in rows)


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Pass value or give an empty output, from a test on condition (node.gate).

    params holds mode and, for score_above, threshold. input holds value_type and condition_type
    (the port types, known at load), and value and condition. A value of an instance port is None
    (empty) or one row or None (an empty row) for each instance. A value of another port type is
    None (empty) or any other value. The result holds value in the same form.
    """
    mode, threshold = params["mode"], params.get("threshold")
    if (mode == "score_above") != (threshold is not None):
        raise ValueError("V-node.gate-1: the mode score_above needs a threshold, and the other modes have none")
    value_type, condition_type = input["value_type"], input["condition_type"]
    if mode == "score_above" and condition_type not in SCORED_TYPES:
        raise ValueError(f"V-node.gate-2: score_above needs a detections or keypoints condition, not {condition_type}")
    value, condition = input["value"], input["condition"]
    by_row = value_type in INSTANCE_TYPES and condition_type in INSTANCE_TYPES
    if by_row and condition is not None and value is not None and len(condition) != len(value):
        raise ValueError(f"V-node.gate-3: value has {len(value)} rows and condition has {len(condition)}")
    if value is None:
        return {"value": None}
    if by_row:
        conditions = condition or [None] * len(value)
        return {
            "value": [
                row if row is not None and passes(params, condition_type, [] if test is None else [test]) else None
                for row, test in zip(value, conditions)  # noqa: B905 (V-node.gate-3)
            ]
        }
    if condition is None:
        rows = []
    elif condition_type in INSTANCE_TYPES:
        rows = [row for row in condition if row is not None]
    else:
        rows = [condition]
    return {"value": value if passes(params, condition_type, rows) else None}

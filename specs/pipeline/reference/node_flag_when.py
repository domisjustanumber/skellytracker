"""Reference implementation of the pipeline section node.flag_when (draft).

Note:

- Section ID: node.flag_when.
- Source: the section text specs/pipeline/nodes/flag_when.md.
- Imported section modules: node.gate (node_gate, the functions score and passes).
"""

from __future__ import annotations

from typing import Any

import node_gate


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Give the flag of one test on all present rows of value (node.flag_when, Behaviour).

    params holds mode and, for score_above, threshold. input holds value_type (boxes or keypoints,
    known at load) and value: None (empty) or one row or None (an empty row) for each instance, in
    the form of node.gate. The result holds flag: true or false.
    """
    mode, threshold = params["mode"], params.get("threshold")
    if (mode == "score_above") != (threshold is not None):
        raise ValueError("V-node.flag_when-1: the mode score_above needs a threshold, and the other modes have none")
    rows = [row for row in input["value"] or [] if row is not None]
    return {"flag": node_gate.passes(params, input["value_type"], rows)}

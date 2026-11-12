"""Reference implementation of the pipeline section node.first_of (draft).

Note:

- Section ID: node.first_of.
- Source: the section text specs/pipeline/nodes/first_of.md.
- Imported section modules: none. Fixtures: none.
- Test: tools/tests/test_pipeline_glue_nodes.py (a named test, no vector file; ADR-3SF2 item 4).

A value is None (no value), a value of an instance port (a mapping with `present`, one flag for each
instance row) or any other value.
"""

from __future__ import annotations

from typing import Any


def is_empty(value: Any) -> bool:
    """True for no value, and for a value of an instance port with no present row (pipeline.graph)."""
    if value is None:
        return True
    return isinstance(value, dict) and "present" in value and not any(value["present"])


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Give the first input that is not empty, in list order (node.first_of, Behaviour).

    input holds `values`, one value for each item of the `inputs` list. The result holds `value`.
    """
    if params:
        raise ValueError(f"unknown params {sorted(params)}")
    return {"value": next((value for value in input["values"] if not is_empty(value)), None)}

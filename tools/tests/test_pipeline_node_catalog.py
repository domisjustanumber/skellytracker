"""`list_node_types()` of the package gives the node tables of the pipeline spec (ADR-V7GZ item 9).

For each node type, the rows that this test makes from `list_node_types()` are the committed
params table and ports table between the `node-table` markers of `specs/pipeline/nodes/<type>.md`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skellytracker.core.pipelines.nodes import NodeTypeInfo, list_node_types

NODES_DIR = Path(__file__).resolve().parents[2] / "specs" / "pipeline" / "nodes"


def table(path: Path, name: str) -> str:
    text = path.read_text(encoding="utf-8")
    return text.split(f"<!-- node-table:{name} -->\n")[1].split(f"\n<!-- /node-table:{name} -->")[0]


def params_table(node: NodeTypeInfo) -> str:
    if not node.params:
        return "This node has no parameters."
    lines = ["| Param | Type | Range | Default | Set during run | Description | Source |", "|---|---|---|---|---|---|---|"]
    for param in node.params:
        cells = [
            f"`{param.name}`",
            f"`{param.type}`",
            param.range,
            "required" if param.required else f"`{json.dumps(param.default)}`",
            "yes" if param.set_during_run else "no",
            param.description,
            param.source,
        ]
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", " ") for cell in cells) + " |")
    return "\n".join(lines)


def ports_table(node: NodeTypeInfo) -> str:
    lines = ["| Port | Direction | Type |", "|---|---|---|"]
    lines += [f"| `{port.name}` | {port.direction} | `{port.port_type}` |" for port in (*node.inputs, *node.outputs)]
    return "\n".join(lines)


@pytest.mark.parametrize("node", list_node_types(), ids=lambda node: node.type)
def test_the_node_catalog_gives_the_committed_tables(node: NodeTypeInfo) -> None:
    path = NODES_DIR / f"{node.type}.md"
    assert params_table(node) == table(path, "params")
    assert ports_table(node) == table(path, "ports")


def test_the_node_catalog_gives_the_sections_the_required_inputs_and_the_timing_spans() -> None:
    by_type = {node.type: node for node in list_node_types()}
    assert len(by_type) == 11 and all(node.section == f"node.{name}" for name, node in by_type.items())
    onnx = by_type["onnx_model"]
    assert [(port.name, port.required) for port in onnx.inputs] == [("image", True), ("boxes", False)]
    assert onnx.timing_spans == ("preprocess", "inference", "postprocess")
    assert [(port.name, port.required) for port in by_type["first_of"].inputs] == [("*", True)]
    assert by_type["gate"].timing_spans == ("run",)

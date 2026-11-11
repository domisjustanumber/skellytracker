"""The pipeline schema and the node tables agree with the reference model (ADR-3SF2 item 3).

`tools/make_pipeline_schema.py` writes `specs/pipeline/pipeline.schema.json` and the tables of
`specs/pipeline/nodes/<type>.md` from `specs/pipeline/reference/pipeline_config.py`. These tests
check two things:

- the tool on small fixtures in `tmp_path`: it writes the files, `--check` then passes, a stale
  table fails, and a node file without markers fails;
- this repository: the committed schema and tables are current. Each param has a `description`,
  `live` (a bool) and `source` (a string). The `section` of each node class is `node.<type>`, and
  the front matter `id` of `nodes/<type>.md` is that section. Each port type is a known port
  type. Each `specs/pipeline/examples/*.pipeline.yaml` passes `PipelineConfig.model_validate`.

The repository tests skip when the reference model does not exist. The example test also skips
when there are no examples.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

import make_pipeline_schema as mps
import sidecar_trace as st

PORT_TYPES = {"image", "roi", "keypoints", "detections", "tensor", "trigger", "any"}

FIXTURE_MODEL = '''
from typing import Literal

from pydantic import BaseModel, Field


class GateParams(BaseModel):
    threshold: float = Field(
        0.5, ge=0, le=1, description="The limit | bound.",
        json_schema_extra={"live": True, "source": "a test"},
    )
    mode: Literal["a", "b"] = Field(
        description="The mode.", json_schema_extra={"live": False, "source": "a test"}
    )


class Gate:
    type = "gate"
    section = "node.gate"
    Params = GateParams
    inputs = {"value": "any"}
    outputs = {"value": "any"}


class PipelineConfig(BaseModel):
    schema_version: str


NODE_TYPES = (Gate,)
'''

NODE_FILE = (
    "---\nid: node.gate\n---\n# Gate\n\n<!-- node-table:params -->\n<!-- /node-table:params -->\n\n"
    "Prose stays.\n\n<!-- node-table:ports -->\nold\n<!-- /node-table:ports -->\n"
)


@pytest.fixture
def spec(tmp_path: Path) -> tuple[Path, Path]:
    """A fixture reference model and a pipeline folder with one node file."""
    model = tmp_path / "reference" / "pipeline_config.py"
    model.parent.mkdir()
    model.write_text(FIXTURE_MODEL, encoding="utf-8")
    base = tmp_path / "pipeline"
    (base / "nodes").mkdir(parents=True)
    (base / "nodes" / "gate.md").write_text(NODE_FILE, encoding="utf-8")
    return model, base


def test_the_tool_writes_the_files_and_then_the_check_passes(spec: tuple[Path, Path]) -> None:
    model, base = spec
    assert mps.run(model, base) == 0
    schema = json.loads((base / "pipeline.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["schema_version"]["type"] == "string"
    assert b"\r\n" not in (base / "pipeline.schema.json").read_bytes()
    node = (base / "nodes" / "gate.md").read_text(encoding="utf-8")
    assert node.startswith("---\nid: node.gate\n---\n# Gate\n") and "Prose stays." in node
    assert (
        "| `threshold` | `float` | >= 0, <= 1 | `0.5` | yes | The limit \\| bound. | a test |" in node
    )
    assert "| `mode` | `Literal['a', 'b']` |  | required | no | The mode. | a test |" in node
    assert "| `value` | input | `any` |\n| `value` | output | `any` |\n" in node
    assert "\nold\n" not in node
    assert mps.run(model, base, check=True) == 0


def test_a_stale_table_fails_the_check_and_the_check_writes_nothing(
    spec: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    model, base = spec
    mps.run(model, base)
    node = base / "nodes" / "gate.md"
    stale = node.read_text(encoding="utf-8").replace("`0.5`", "`0.4`")
    node.write_text(stale, encoding="utf-8")
    capsys.readouterr()
    assert mps.run(model, base, check=True) == 1
    assert capsys.readouterr().out == "differs: nodes/gate.md\n"
    assert node.read_text(encoding="utf-8") == stale


@pytest.mark.parametrize(
    "broken",
    [NODE_FILE.replace("<!-- /node-table:ports -->", ""), NODE_FILE + NODE_FILE, None],
    ids=["missing-marker", "two-pairs", "no-node-file"],
)
def test_a_node_file_without_one_marker_pair_fails_and_nothing_is_written(
    spec: tuple[Path, Path], capsys: pytest.CaptureFixture[str], broken: str | None
) -> None:
    model, base = spec
    node = base / "nodes" / "gate.md"
    if broken is None:
        node.unlink()
    else:
        node.write_text(broken, encoding="utf-8")
    assert mps.run(model, base) == 1
    assert capsys.readouterr().out.startswith("nodes/gate.md: ")
    assert not (base / "pipeline.schema.json").exists()


def test_no_reference_model_is_not_an_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert mps.run(tmp_path / "pipeline_config.py", tmp_path, check=True) == 0
    assert len(capsys.readouterr().out.splitlines()) == 1


# ---------------------------------------------------------------------------
# This repository
# ---------------------------------------------------------------------------

needs_model = pytest.mark.skipif(
    not mps.MODEL.is_file(), reason="specs/pipeline/reference/pipeline_config.py does not exist yet"
)


@needs_model
def test_the_committed_schema_and_tables_are_current() -> None:
    assert mps.run(check=True) == 0, "run: uv run python tools/make_pipeline_schema.py"


@needs_model
def test_each_param_has_a_description_live_and_source() -> None:
    for node in mps.load_model().NODE_TYPES:
        for name, field in node.Params.model_fields.items():
            extra = field.json_schema_extra
            where = f"{node.type}.{name}"
            assert field.description, f"{where}: no description"
            assert isinstance(extra, dict), f"{where}: no json_schema_extra"
            assert isinstance(extra.get("live"), bool), f"{where}: live must be a bool"
            assert isinstance(extra.get("source"), str) and extra["source"], f"{where}: no source"


@needs_model
def test_each_node_class_names_its_section_file_and_known_port_types() -> None:
    for node in mps.load_model().NODE_TYPES:
        assert node.section == f"node.{node.type}"
        path = mps.PIPELINE_DIR / "nodes" / f"{node.type}.md"
        assert path.is_file(), f"no node file {path.name}"
        front, _ = st.parse_front_matter(path.read_text(encoding="utf-8"), path.name)
        assert front.get("id") == node.section, f"{path.name}: the id must be {node.section}"
        assert set(node.inputs.values()) | set(node.outputs.values()) <= PORT_TYPES, node.type


EXAMPLES = sorted((mps.PIPELINE_DIR / "examples").glob("*.pipeline.yaml"))


@needs_model
@pytest.mark.skipif(not EXAMPLES, reason="no pipeline examples yet")
@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_each_example_passes_the_model(path: Path) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    mps.load_model().PipelineConfig.model_validate(data)

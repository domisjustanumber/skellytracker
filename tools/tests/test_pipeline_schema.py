"""The pipeline schema and the node tables agree with the reference model (ADR-3SF2 item 3).

`tools/make_pipeline_schema.py` writes `specs/pipeline/pipeline.schema.json` and the tables of
`specs/pipeline/nodes/<type>.md` from `specs/pipeline/reference/pipeline_config.py`. These tests
check two things:

- the tool on small fixtures in `tmp_path`: it writes the files, `--check` then passes, a stale
  table fails, and a node file without markers fails;
- this repository: the committed schema and tables are current. Each param has a `description`,
  `set_during_run` (a bool) and `source` (a string). The `section` of each node class is `node.<type>`, and
  the front matter `id` of `nodes/<type>.md` is that section. Each port type is a known port
  type. Each `specs/pipeline/examples/*.pipeline.yaml` passes `PipelineConfig.model_validate`.
  The structural checks refuse a small config for each newer rule (point-name prefixes, list
  inputs, `any` types, outputs and taps with no `@prev` or frame port, an output key that is not
  `wholebody`, `holistic` or `boxes`, an output port of the wrong type, and an output `boxes` that
  can hold a rotated box).

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

PORT_TYPES = {"image", "boxes", "keypoints", "flag"}

FIXTURE_MODEL = '''
from typing import Literal

from pydantic import BaseModel, Field


class GateParams(BaseModel):
    threshold: float = Field(
        0.5, ge=0, le=1, description="The limit | bound.",
        json_schema_extra={"set_during_run": True, "source": "a test"},
    )
    mode: Literal["a", "b"] = Field(
        description="The mode.", json_schema_extra={"set_during_run": False, "source": "a test"}
    )


class Gate:
    type = "gate"
    section = "node.gate"
    Params = GateParams
    inputs = {"value": ("boxes", "keypoints")}
    outputs = {"value": ("boxes", "keypoints")}


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
    assert "| `value` | input | `boxes`, `keypoints` |\n| `value` | output | `boxes`, `keypoints` |\n" in node
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
            assert isinstance(extra.get("set_during_run"), bool), f"{where}: set_during_run must be a bool"
            assert isinstance(extra.get("source"), str) and extra["source"], f"{where}: no source"


@needs_model
def test_each_node_class_names_its_section_file_and_known_port_types() -> None:
    for node in mps.load_model().NODE_TYPES:
        assert node.section == f"node.{node.type}"
        path = mps.PIPELINE_DIR / "nodes" / f"{node.type}.md"
        assert path.is_file(), f"no node file {path.name}"
        front, _ = st.parse_front_matter(path.read_text(encoding="utf-8"), path.name)
        assert front.get("id") == node.section, f"{path.name}: the id must be {node.section}"
        assert {kind for kinds in (*node.inputs.values(), *node.outputs.values()) for kind in kinds} <= PORT_TYPES, node.type


EXAMPLES = sorted((mps.PIPELINE_DIR / "examples").glob("*.pipeline.yaml"))


@needs_model
@pytest.mark.skipif(not EXAMPLES, reason="no pipeline examples yet")
@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_each_example_passes_the_model(path: Path) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    mps.load_model().PipelineConfig.model_validate(data)


def _config(nodes: list[dict], outputs: dict | None = None, taps: list[dict] | None = None) -> dict:
    """A small pipeline config with a person detector `person` and a body model `body`."""
    base = [
        {"id": "person", "type": "onnx_model", "inputs": {"image": "frame.image"}, "params": {"key": "p@x", "size": "m"}},
        {"id": "body", "type": "onnx_model", "inputs": {"image": "frame.image", "boxes": "person.boxes"},
         "params": {"key": "b@x", "size": "m"}},
    ]
    return {
        "schema_version": "2.0.0", "pipeline_id": "t", "source": {"name": "skellytracker", "version": "2.0.0"},
        "nodes": base + nodes, "outputs": outputs or {"wholebody": "body.keypoints"},
        "instrumentation": {"taps": taps or []},
    }


BOX = {"id": "box", "type": "boxes_from_points", "inputs": {"keypoints": "body.keypoints"}}
TURNED = {**BOX, "params": {"size_rule": "alignment", "alignment_start": "body/a", "alignment_end": "body/b", "target_rotation_deg": 90}}


@needs_model
@pytest.mark.parametrize(
    ("config", "rule"),
    [
        (_config([{**BOX, "params": {"points": ["left_wrist"]}}]), "V-pipeline.graph-8"),
        (_config([{**BOX, "params": {"points": ["hand.wrist"]}}]), "V-pipeline.graph-8"),
        (_config([{**BOX, "params": {"points": ["body/a"], "derived_points": {"m": {"body/a": 0.5, "body/b": 0.4}}}}]),
         "V-node.boxes_from_points-5"),
        (_config([{"id": "pick", "type": "first_of", "inputs": ["person.boxes", "body.keypoints"]}]), "V-node.first_of-1"),
        (_config([{"id": "pick", "type": "first_of", "inputs": ["body.keypoints"]},
                  {"id": "crop", "type": "smooth_boxes", "inputs": {"boxes": "pick.value"}}]), "V-pipeline.graph-3"),
        (_config([{"id": "pass", "type": "gate", "inputs": {"value": "body.keypoints@prev", "condition": "person.boxes"},
                   "params": {"mode": "is_present"}}]), "V-pipeline.graph-9"),
        (_config([{"id": "pick", "type": "first_of", "inputs": ["body.keypoints@prev"]}]), "V-pipeline.graph-9"),
        (_config([{"id": "pick", "type": "first_of", "inputs": ["person.boxes", "body.keypoints@prev"]}]), "V-node.first_of-1"),
        (_config([{"id": "pass", "type": "gate", "inputs": {"value": "frame.image", "condition": "person.boxes"}, "params": {"mode": "is_present"}}]),
         "V-pipeline.graph-3: pass.value takes boxes or keypoints, but 'frame.image' gives image"),
        (_config([{"id": "pick", "type": "first_of", "inputs": ["person.boxes", "frame.image"]}]), "V-pipeline.graph-3: pick.\\*"),
        (_config([{"id": "need", "type": "redetect_trigger"},
                  {"id": "pass", "type": "gate", "inputs": {"value": "person.boxes", "condition": "need.redetect@prev"},
                   "params": {"mode": "is_true"}}]), "V-pipeline.graph-12: pass.condition"),
        (_config([{"id": "other", "type": "onnx_model", "inputs": {"image": "frame.image", "run_if": "person.boxes"},
                   "params": {"key": "p@x", "size": "m"}}]), "V-node.onnx_model-6"),
        (_config([{"id": "need", "type": "redetect_trigger"},
                  {"id": "whole", "type": "mediapipe_tasks", "inputs": {"image": "frame.image", "run_if": "need.redetect"},
                   "params": {"variant": "holistic"}}]), "V-node.mediapipe_tasks-3"),
        (_config([{"id": "hands", "type": "mediapipe_tasks", "inputs": {"image": "frame.image", "run_if": "body.keypoints"},
                   "params": {"variant": "hand"}}]), "V-node.mediapipe_tasks-3"),
        (_config([{"id": "need", "type": "redetect_trigger", "inputs": {"image": "frame.image"}}]), "V-pipeline.graph-5"),
        (_config([{"id": "other", "type": "onnx_model", "inputs": {"image": "person.boxes"}, "params": {"key": "p@x", "size": "m"}}]),
         "V-pipeline.graph-3: other.image takes image, but 'person.boxes' gives boxes"),
        (_config([], outputs={"wholebody": "body.keypoints@prev"}), "V-pipeline.outputs-1"),
        (_config([], outputs={"wholebody": "frame.image"}), "V-pipeline.outputs-1"),
        (_config([], outputs={"node_ran": "body.keypoints"}), "V-pipeline.outputs-1: the output key 'node_ran'"),
        (_config([], outputs={"boxes": "body.keypoints"}), "V-pipeline.outputs-4: the output boxes must name a boxes port"),
        (_config([{"id": "need", "type": "redetect_trigger"}], outputs={"holistic": "need.redetect"}), "V-pipeline.outputs-4"),
        (_config([TURNED], outputs={"boxes": "box.boxes"}), "V-pipeline.outputs-5: .* box"),
        (_config([TURNED, {"id": "pass", "type": "gate", "inputs": {"value": "box.boxes", "condition": "person.boxes"},
                           "params": {"mode": "is_present"}}], outputs={"boxes": "pass.value"}), "V-pipeline.outputs-5: .* box"),
        (_config([], taps=[{"action": "record", "port": "frame.image", "name": "img"}]), "V-pipeline.taps-1"),
        (_config([{"id": "m", "type": "assign_keypoints", "inputs": {"target": "body.keypoints", "source": "body.keypoints"},
                   "params": {"slots": {"hand": "body/wrist"}, "source_anchor": "body/wrist", "max_distance": 0.15,
                              "map": {"body/wrist": "face/tip"}}}]), "V-node.assign_keypoints-2"),
        (_config([{"id": "m", "type": "assign_keypoints", "inputs": {"target": "body.keypoints", "source": "body.keypoints"},
                   "params": {"slots": {"hand": "body/wrist"}, "source_anchor": "body/wrist"}}]), "max_distance"),
        (_config([{"id": "m", "type": "merge", "inputs": {"body": "body.keypoints"},
                   "params": {"format": "wholebody", "map": {"body/wrist": "hand/root"}}}]), "V-node.merge-9"),
        (_config([{"id": "m", "type": "merge", "inputs": {"left_hand": "body.keypoints"}, "params": {"format": "wholebody"}}]),
         "V-pipeline.graph-6: m: missing input 'body'"),
        (_config([{"id": "m", "type": "merge", "inputs": {"body": "body.keypoints"}}]), "format"),
        (_config([{"id": "m", "type": "concat", "inputs": ["body.keypoints"]}]), "concat"),
        (_config([{"id": "hands", "type": "mediapipe_tasks", "inputs": {"image": "frame.image"},
                   "params": {"variant": "hand", "size": "heavy"}}]), "V-node.mediapipe_tasks-2"),
        (_config([{**BOX, "params": {"min_previous_ratio": 0.995}}]), "V-node.boxes_from_points-6"),
        (_config([{**BOX, "inputs": {"keypoints": "body.keypoints", "previous_boxes": "person.boxes"},
                   "params": {"min_reference_ratio": 0.5}}]), "V-node.boxes_from_points-6"),
        (_config([{"id": "need", "type": "redetect_trigger",
                   "params": {"fitness_checks": [{"check": "box_missing", "threshold": 0.5}]}}]), "V-node.redetect_trigger-1"),
        (_config([{"id": "need", "type": "redetect_trigger",
                   "params": {"fitness_checks": [{"check": "box_missing"}]}}]), "V-node.redetect_trigger-2"),
        (_config([{"id": "crop", "type": "smooth_boxes", "inputs": {"boxes": "person.boxes"},
                   "params": {"filter": "one_euro", "previous_weight": 0.4}}]), "V-node.smooth_boxes-1"),
        (_config([{"id": "crop", "type": "smooth_boxes", "inputs": {"boxes": "person.boxes"},
                   "params": {"min_cutoff": 3.0}}]), "V-node.smooth_boxes-1"),
    ],
    ids=["no-prefix", "dot-form", "weight-sum", "first-of-types", "any-type-inferred",
         "gate-value-prev", "first-of-only-prev", "first-of-types-prev", "gate-takes-no-image", "first-of-takes-no-image", "prev-of-a-flag",
         "run-if-not-a-flag", "run-if-on-holistic", "run-if-of-a-hand-not-a-flag", "trigger-has-no-image", "image-input-gets-boxes",
         "output-prev", "output-frame", "output-unknown-key", "output-wrong-type", "output-flag", "output-rotated",
         "output-rotated-through-gate", "tap-frame", "assign-map-column", "assign-no-max-distance",
         "merge-map-part", "merge-no-body", "merge-no-format", "no-concat",
         "mediapipe-size-not-body", "floor-no-previous-boxes", "floor-no-reference-boxes",
         "box-missing-field", "box-missing-no-previous-boxes", "one-euro-with-ema-param", "ema-with-one-euro-param"],
)
def test_the_reference_model_refuses_the_new_structural_cases(config: dict, rule: str) -> None:
    with pytest.raises(ValueError, match=rule):
        mps.load_model().PipelineConfig.model_validate(config)


@needs_model
def test_the_schema_of_outputs_has_the_three_keys_and_no_other_key() -> None:
    outputs = mps.load_model().PipelineConfig.model_json_schema()["properties"]["outputs"]
    assert set(outputs["properties"]) == {"wholebody", "holistic", "boxes"}
    assert outputs["additionalProperties"] is False and outputs["minProperties"] == 1


@needs_model
def test_the_reference_model_accepts_the_new_optional_forms() -> None:
    """`points` can be empty, a floor has its input, `box_missing` has `previous_boxes`, and one_euro has its params."""
    nodes = [
        {"id": "need", "type": "redetect_trigger",
         "inputs": {"previous_boxes": "crop.boxes@prev"},
         "params": {"fitness_checks": [{"check": "box_missing"}]}},
        {"id": "again", "type": "onnx_model", "inputs": {"image": "frame.image", "run_if": "need.redetect"}, "params": {"key": "p@x", "size": "m"}},
        {"id": "box", "type": "boxes_from_points",
         "inputs": {"keypoints": "body.keypoints@prev", "previous_boxes": "crop.boxes@prev", "reference_boxes": "person.boxes"},
         "params": {"min_previous_ratio": 0.995, "min_reference_ratio": 0.5, "min_size_px": 80}},
        {"id": "plain", "type": "boxes_from_points", "inputs": {"keypoints": "body.keypoints"}},
        {"id": "crop", "type": "smooth_boxes", "inputs": {"boxes": "box.boxes"},
         "params": {"filter": "one_euro", "min_cutoff": 3.0, "reset_after_ms": 500}},
    ]
    config = mps.load_model().PipelineConfig.model_validate(_config(nodes))
    by_id = {node.id: node for node in config.nodes}
    assert by_id["plain"].params.points is None
    assert by_id["crop"].params.previous_weight == 0.5

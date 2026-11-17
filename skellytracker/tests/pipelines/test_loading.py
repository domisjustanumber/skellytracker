"""`load_pipeline` and `export_pipeline`: the input forms, the rules of pipeline.file and the two export forms."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from skellytracker.core.pipelines.config import PipelineConfig, SmoothBoxesParams
from skellytracker.core.pipelines.loading import IMPLEMENTED_VERSIONS, export_pipeline, load_pipeline

BASE: dict[str, Any] = {
    "schema_version": "2.0.0",
    "pipeline_id": "demo",
    "source": {"name": "demo-source", "version": "1.0.0"},
    "nodes": [
        {"id": "holistic", "type": "mediapipe_tasks", "inputs": {"image": "frame.image"}, "params": {"variant": "holistic"}},
        {"id": "smooth", "type": "smooth_keypoints", "inputs": {"keypoints": "holistic.keypoints"}},
    ],
    "outputs": {"holistic": "smooth.keypoints"},
}


def changed(**changes: Any) -> dict[str, Any]:
    """Return a copy of `BASE` with top-level keys replaced. The value `...` removes a key."""
    data = {**copy.deepcopy(BASE), **changes}
    return {key: value for key, value in data.items() if value is not ...}


def write(folder: Path, data: dict[str, Any], name: str = "demo.pipeline.yaml") -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(json.dumps(data) if name.endswith(".json") else yaml.safe_dump(data), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------------------------
# The input forms
# ---------------------------------------------------------------------------------------------


def test_a_mapping_a_yaml_file_and_a_json_file_give_the_same_config(tmp_path: Path) -> None:
    config = load_pipeline(BASE)
    assert isinstance(config, PipelineConfig) and config.pipeline_id == "demo"
    yaml_path = write(tmp_path, BASE)
    assert load_pipeline(yaml_path) == config
    assert load_pipeline(str(yaml_path)) == config
    assert load_pipeline(write(tmp_path, BASE, "any-name.json")) == config


def test_a_string_with_no_file_suffix_is_a_key_of_the_catalog(tmp_path: Path) -> None:
    write(tmp_path / "pipelines", BASE)
    assert load_pipeline("demo@demo-source", user_root=tmp_path) == load_pipeline(BASE)
    assert load_pipeline("demo@demo-source==1.0.0", user_root=tmp_path) == load_pipeline(BASE)


def test_a_yaml_file_makes_only_plain_data(tmp_path: Path) -> None:
    path = tmp_path / "demo.pipeline.yaml"
    path.write_text(yaml.safe_dump(BASE) + "description: !!python/object/apply:os.getcwd []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="cannot parse demo.pipeline.yaml"):
        load_pipeline(path)


# ---------------------------------------------------------------------------------------------
# The rules of pipeline.file
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("version", ["2.0", "v2.0.0", 2])
def test_v_pipeline_file_1_schema_version_must_be_a_semver_string(version: Any) -> None:
    with pytest.raises(ValidationError, match="schema_version"):
        load_pipeline(changed(schema_version=version))


def test_v_pipeline_file_1_schema_version_must_be_a_version_of_the_changelog() -> None:
    assert IMPLEMENTED_VERSIONS == ("2.0.0",)
    with pytest.raises(ValueError, match="V-pipeline.file-1: .*'2.0.1'"):
        load_pipeline(changed(schema_version="2.0.1"))


@pytest.mark.parametrize(
    "changes",
    [
        {"pipeline_id": "Demo"},
        {"source": {"name": "demo-source", "version": "1.0.0", "url": "x"}},
        {"source": {"name": "demo-source"}},
        {"source": {"name": "Demo_Source", "version": "1.0.0"}},
        {"source": {"name": "demo-source", "version": ""}},
    ],
    ids=["pipeline-id", "source-extra-key", "source-no-version", "source-name", "empty-version"],
)
def test_v_pipeline_file_2_pipeline_id_and_source(changes: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="pipeline_id|source"):
        load_pipeline(changed(**changes))


@pytest.mark.parametrize("name", ["other.pipeline.yaml", "demo.yaml", "demo.pipeline.yml"])
def test_v_pipeline_file_2_the_file_name_must_be_the_pipeline_id(tmp_path: Path, name: str) -> None:
    with pytest.raises(ValueError, match=f"V-pipeline.file-2: .*{name} must be demo.pipeline.yaml"):
        load_pipeline(write(tmp_path, BASE, name))


def test_v_pipeline_file_3_no_unknown_key_at_any_level() -> None:
    node = BASE["nodes"][0]
    cases = [
        changed(extra=1),
        changed(nodes=[{**node, "extra": 1}]),
        changed(nodes=[{**node, "params": {"variant": "holistic", "extra": 1}}]),
        changed(instrumentation={"extra": []}),
    ]
    for data in cases:
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            load_pipeline(data)


@pytest.mark.parametrize("key", ["schema_version", "pipeline_id", "source", "nodes", "outputs"])
def test_v_pipeline_file_4_each_required_key(key: str) -> None:
    with pytest.raises(ValidationError, match=f"{key}\n  Field required"):
        load_pipeline(changed(**{key: ...}))


def test_v_pipeline_file_4_one_node_and_one_output_or_more() -> None:
    for changes in ({"nodes": []}, {"outputs": {}}):
        with pytest.raises(ValidationError, match="at least 1 item"):
            load_pipeline(changed(**changes))


def test_v_pipeline_file_4_the_top_level_of_a_file_must_be_a_mapping(tmp_path: Path) -> None:
    path = tmp_path / "demo.pipeline.yaml"
    path.write_text("- 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="V-pipeline.file-4"):
        load_pipeline(path)


def test_v_pipeline_file_5_a_yaml_file_must_have_no_duplicate_key(tmp_path: Path) -> None:
    path = tmp_path / "demo.pipeline.yaml"
    path.write_text(yaml.safe_dump(BASE) + "description: one\ndescription: two\n", encoding="utf-8")
    with pytest.raises(ValueError, match="^V-pipeline.file-5: demo.pipeline.yaml: .*duplicate key 'description'"):
        load_pipeline(path)
    nested = yaml.safe_dump(BASE).replace("  version: 1.0.0\n", "  version: 1.0.0\n  version: 1.0.1\n")
    path.write_text(nested, encoding="utf-8")
    with pytest.raises(ValueError, match="^V-pipeline.file-5: .*'version'"):
        load_pipeline(path)


def test_v_pipeline_file_5_a_json_file_must_have_no_duplicate_key(tmp_path: Path) -> None:
    path = tmp_path / "demo.json"
    path.write_text(json.dumps(BASE)[:-1] + ', "pipeline_id": "other"}', encoding="utf-8")
    with pytest.raises(ValueError, match="^V-pipeline.file-5: duplicate key 'pipeline_id'"):
        load_pipeline(path)


def test_the_error_of_a_structural_rule_keeps_its_rule_id() -> None:
    with pytest.raises(ValidationError, match="V-pipeline.outputs-1"):
        load_pipeline(changed(outputs={"holistic": "nothing.keypoints"}))


# ---------------------------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------------------------


def test_the_export_as_written_holds_only_what_the_config_gives_and_loads_again() -> None:
    config = load_pipeline(BASE)
    written = export_pipeline(config)
    assert written == BASE
    assert load_pipeline(written) == config
    assert json.loads(json.dumps(written)) == written  # only JSON types


def test_the_export_as_written_keeps_a_description_of_the_pipeline_and_of_a_node() -> None:
    data = {**BASE, "description": "Two lines\nfor people.", "nodes": [{**BASE["nodes"][0], "description": "The landmarker."}, *BASE["nodes"][1:]]}
    written = export_pipeline(load_pipeline(data))
    assert written == data and written["nodes"][0]["description"] == "The landmarker."
    assert "description" not in written["nodes"][1]  # an empty default is not written
    assert export_pipeline(load_pipeline(BASE), resolved=True)["nodes"][1]["description"] == ""


def test_the_resolved_export_holds_each_param_with_its_default() -> None:
    resolved = export_pipeline(load_pipeline(BASE), resolved=True)
    assert resolved["description"] == "" and resolved["instrumentation"] == {"timing_spans": [], "taps": []}
    holistic, smooth = resolved["nodes"]
    assert holistic["params"]["size"] == "heavy" and holistic["params"]["max_instances"] == 1
    assert smooth["params"]["filter"] == "one_euro" and smooth["params"]["max_gap_ms"] is None
    for node, model in zip(resolved["nodes"], load_pipeline(BASE).nodes, strict=True):
        assert set(node["params"]) == set(type(model.params).model_fields)


def test_the_export_as_written_of_a_default_size_validates_again() -> None:
    """ADR-97X9 item 10: `size` has a default, and V-node.mediapipe_tasks-2 refuses a written `size` for holistic."""
    config = load_pipeline(BASE)
    assert "size" not in export_pipeline(config)["nodes"][0]["params"]
    with pytest.raises(ValidationError, match="V-node.mediapipe_tasks-2"):
        load_pipeline(export_pipeline(config, resolved=True))


def test_the_export_as_written_holds_a_param_that_the_caller_changes() -> None:
    config = load_pipeline(BASE)
    config.nodes[1].params.min_cutoff = 2.0
    config.instrumentation.timing_spans.append("pipeline.run")  # a change in place of a default value
    written = export_pipeline(config)
    assert written["nodes"][1] == {**BASE["nodes"][1], "params": {"min_cutoff": 2.0}}
    assert written == {**BASE, "nodes": written["nodes"], "instrumentation": {"timing_spans": ["pipeline.run"]}}
    assert export_pipeline(load_pipeline(written)) == written
    built = SmoothBoxesParams(filter="one_euro", beta=0.1)
    assert built.model_dump(exclude_unset=True) == {"filter": "one_euro", "beta": 0.1}

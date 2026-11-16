"""The built-in pipelines of `core/model_zoo/pipelines/` and the schema file of the package."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from skellytracker.core.detectors.catalog import USER_ROOT_VARIABLE, scan_sidecar_roots
from skellytracker.core.pipelines import config as config_module
from skellytracker.core.pipelines.catalog import PACKAGE_PIPELINE_ROOT, list_pipelines
from skellytracker.core.pipelines.config import PipelineConfig
from skellytracker.core.pipelines.loading import export_pipeline, load_pipeline

BUILT_INS = ("mediapipe-holistic-tasks", "yolox-rtmw-wholebody")
EXAMPLES = Path(__file__).resolve().parents[3] / "specs" / "pipeline" / "examples"
HASH_LINE = "sidecar_sha256:"


@pytest.fixture(autouse=True)
def no_user_root_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(USER_ROOT_VARIABLE, raising=False)


def test_the_package_root_holds_the_built_ins() -> None:
    assert sorted(path.name for path in PACKAGE_PIPELINE_ROOT.iterdir()) == [f"{name}.pipeline.yaml" for name in BUILT_INS]


@pytest.mark.parametrize("name", BUILT_INS)
def test_a_built_in_loads_by_its_key_and_its_export_is_the_file(name: str, tmp_path: Path) -> None:
    (entry,) = [entry for entry in list_pipelines(tmp_path) if entry.key == f"{name}@skellytracker"]
    # The ONNX files of the package root are not in git: a built-in is then unavailable, and it loads.
    assert entry.available or {warning.code for warning in entry.warnings} == {"missing_dependency"}, entry
    assert not entry.superseded and entry.version == "2.0.0", entry
    config = load_pipeline(entry.key, user_root=tmp_path)
    assert config == load_pipeline(entry.path)
    written = export_pipeline(config)
    assert written == yaml.safe_load(entry.path.read_text(encoding="utf-8"))
    assert load_pipeline(written) == config


def test_each_sidecar_sha256_of_a_built_in_is_the_hash_of_its_package_sidecar(tmp_path: Path) -> None:
    sidecars = {found.key: found.sha256 for found in scan_sidecar_roots(tmp_path)}
    nodes = [
        node
        for name in BUILT_INS
        for node in load_pipeline(PACKAGE_PIPELINE_ROOT / f"{name}.pipeline.yaml").nodes
        if node.type == "onnx_model"
    ]
    assert len(nodes) == 2
    for node in nodes:  # a shipped file must give the hash (ADR-7NY2 item 10)
        assert node.params.sidecar_sha256 == sidecars[node.params.key], node.id


@pytest.mark.skipif(not EXAMPLES.is_dir(), reason="the spec examples are not in an installed package")
@pytest.mark.parametrize("name", BUILT_INS)
def test_a_built_in_is_its_spec_example_with_the_sidecar_hashes(name: str) -> None:
    built_in = (PACKAGE_PIPELINE_ROOT / f"{name}.pipeline.yaml").read_text(encoding="utf-8").splitlines()
    example = (EXAMPLES / f"{name}.pipeline.yaml").read_text(encoding="utf-8").splitlines()
    assert not any(line.strip().startswith(HASH_LINE) for line in example)
    assert [line for line in built_in if not line.strip().startswith(HASH_LINE)] == example


def test_the_schema_file_of_the_package_is_the_schema_of_the_model() -> None:
    schema = json.loads(Path(config_module.__file__).with_name("pipeline.schema.json").read_text(encoding="utf-8"))
    assert schema == PipelineConfig.model_json_schema()

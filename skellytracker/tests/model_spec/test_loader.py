"""`load_sidecar`, the typed model, the landmark schema registry and the SPDX check."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from skellytracker.core.model_spec import (
    IMPLEMENTED_SCHEMA_VERSIONS,
    PACKAGE_SIDECAR_ROOT,
    SidecarSchemaVersionError,
    SidecarValidationError,
    load_landmark_schema_registry,
    load_sidecar,
)
from skellytracker.core.model_spec.landmark_schemas import check_landmark_schema
from skellytracker.core.model_spec.loader import FIELD_TYPE
from skellytracker.core.model_spec.rules import PLACEHOLDER_SHA256
from skellytracker.core.model_spec.spdx import has_license_ref, is_spdx_expression, spdx_license_list_version
from skellytracker.tests.model_spec.sidecars import BASES, MISSING, changed, write_yaml

EXAMPLES_ROOT = Path(__file__).resolve().parents[3] / "specs" / "model-sidecar" / "examples"
DETECTOR_PATH = "detectors/object_detectors/demo/demo.yaml"


def load(root: Path, sidecar: dict[str, Any], relative_path: str = DETECTOR_PATH, **options: Any) -> Any:
    write_yaml(root / relative_path, sidecar)
    return load_sidecar(root / relative_path, root, **options)


# ---------------------------------------------------------------------------------------------
# load_sidecar and the model
# ---------------------------------------------------------------------------------------------


def test_load_sidecar_gives_the_model_with_the_defaults_of_the_spec(tmp_path: Path) -> None:
    sidecar = load(tmp_path, changed(BASES["nms"](), {"input.resize.pad_value": MISSING}))
    assert sidecar.model_id == "demo" and sidecar.source.name == "demo-exporter"
    assert sidecar.default_size == "n" and sidecar.size("n").target_size == [416, 416]
    assert sidecar.artifact("n", "fp32").filename == "demo-n_b3_fp32.onnx"
    resize = sidecar.input.resize
    assert (resize.pad_value, resize.interpolation, resize.compute_dtype, resize.crop_policy) == (114, "linear", "uint8", None)
    decode = sidecar.object.decode
    assert (decode.min_score, decode.clamp_boxes, decode.box_format, decode.box_space) == (0.7, True, "xyxy", "pixel")
    assert decode.nms.class_agnostic is False and decode.min_box_size is None
    assert sidecar.batching.batch == 3 and not sidecar.batching.supports_dynamic_batch
    assert sidecar.input.normalization_for("fp32") == "none"
    assert sidecar.output("scores").semantic == "scores"


def test_an_unknown_size_or_precision_is_an_error(tmp_path: Path) -> None:
    sidecar = load(tmp_path, BASES["nms"]())
    with pytest.raises(ValueError, match="no size 'xl'"):
        sidecar.size("xl")
    with pytest.raises(ValueError, match="no precision 'fp16'"):
        sidecar.artifact("n", "fp16")


def test_an_absent_resize_is_method_none_with_no_resize_field(tmp_path: Path) -> None:
    packed = changed(BASES["packed"](), {"keypoint.landmark_schema": "Demo17"})
    write_yaml(tmp_path / "user" / "landmark_schemas" / "Demo17.yaml", {"name": "Demo17", "source": "test", "groups": [{"name": "body", "points": packed["keypoint"]["point_names"]}]})
    sidecar = load(tmp_path / "root", packed, "detectors/keypoint_detectors/demo/body/demo-body.yaml", user_root=tmp_path / "user")
    assert sidecar.input.resize.method == "none"
    assert sidecar.input.resize.interpolation is None and sidecar.input.resize.compute_dtype is None
    assert sidecar.size("n").target_size is None
    assert sidecar.keypoint.decode.coordinate_space is None
    assert sidecar.outputs[0].packed_keypoints.components == ["x", "y", "score"]


def test_the_sizes_keep_the_order_of_the_file(tmp_path: Path) -> None:
    base = BASES["nms"]()
    sizes = dict.fromkeys(("s", "n", "m"), base["sizes"]["n"])
    assert list(load(tmp_path, changed(base, {"sizes": sizes})).sizes) == ["s", "n", "m"]


@pytest.mark.parametrize(
    ("version", "rule"),
    [("3.0.0", "V-format.versioning-2"), ("2.0.0-rc.1", "V-format.versioning-2"), ("v2024.09.1019", "V-format.versioning-1"), (2.0, "V-format.versioning-1")],
)
def test_a_version_that_the_release_does_not_implement_is_refused_by_name(tmp_path: Path, version: Any, rule: str) -> None:
    with pytest.raises(SidecarSchemaVersionError, match=str(version).replace(".", r"\.")) as info:
        load(tmp_path, changed(BASES["nms"](), {"schema_version": version}))
    assert info.value.rules == (rule,)
    assert IMPLEMENTED_SCHEMA_VERSIONS == ("2.0.0",)


def test_a_sidecar_that_fails_rules_names_each_rule(tmp_path: Path) -> None:
    with pytest.raises(SidecarValidationError) as info:
        load(tmp_path, changed(BASES["nms"](), {"input.layout": "NCHW", "batching.batch": 2}))
    assert set(info.value.rules) == {"V-format.composition-5", "V-common.sizes_and_artifacts-12", "V-common.batch_conversion-3"}
    assert "demo.yaml" in str(info.value)


def test_the_file_name_must_be_the_model_id(tmp_path: Path) -> None:
    with pytest.raises(SidecarValidationError) as info:
        load(tmp_path, BASES["nms"](), "detectors/object_detectors/demo/other.yaml")
    assert info.value.rules == ("V-common.identity-1",)


def test_the_placeholder_hash_is_refused_outside_the_examples(tmp_path: Path) -> None:
    sidecar = changed(BASES["nms"](), {"sizes.n.onnx.precision_artifacts.fp32.sha256": PLACEHOLDER_SHA256})
    with pytest.raises(SidecarValidationError) as info:
        load(tmp_path, sidecar)
    assert info.value.rules == ("V-common.sizes_and_artifacts-11",)
    assert load(tmp_path / "specs" / "model-sidecar" / "examples", sidecar).model_id == "demo"


def test_a_wrong_field_type_that_no_rule_names_is_refused(tmp_path: Path) -> None:
    with pytest.raises(SidecarValidationError) as info:
        load(tmp_path, changed(BASES["nms"](), {"outputs.0.shape": "many"}))
    assert FIELD_TYPE in info.value.rules


@pytest.mark.skipif(not EXAMPLES_ROOT.is_dir(), reason="the reference examples are not in an installed package")
def test_each_reference_example_loads() -> None:
    paths = sorted(EXAMPLES_ROOT.glob("detectors/*/**/*.yaml"))
    loaded = [load_sidecar(path, EXAMPLES_ROOT) for path in paths if "shared" not in path.parts]
    assert {sidecar.model_id for sidecar in loaded} >= {"yolox-person", "rtmw-wholebody133"}


# ---------------------------------------------------------------------------------------------
# The landmark schema registry
# ---------------------------------------------------------------------------------------------

SCHEMA = {
    "name": "Demo",
    "source": "https://example.org/demo, read 2026-11-16",
    "groups": [{"name": "body", "points": ["hip", "knee"]}, {"name": "left_hand", "points": ["wrist", "tip"]}],
    "canonical_mapping": {"body": {"hip": "hip", "leg": ["hip", "knee"], "mid": {"hip": 0.5, "knee": 0.5}, "hand": "wrist"}},
}


def test_the_package_registry_holds_coco_wholebody() -> None:
    registry = load_landmark_schema_registry()
    assert len(registry["COCO_WholeBody"].point_names) == 133
    assert registry["COCO_WholeBody"].path.parent == PACKAGE_SIDECAR_ROOT / "landmark_schemas"


def test_a_valid_schema_passes() -> None:
    assert check_landmark_schema(SCHEMA, "Demo") == []


@pytest.mark.parametrize(
    ("rule", "changes"),
    [
        ("V-post.keypoint.landmark_schema-1", {"notes": "x"}),
        ("V-post.keypoint.landmark_schema-1", {"source": MISSING}),
        ("V-post.keypoint.landmark_schema-1", {"name": "Other"}),
        ("V-post.keypoint.landmark_schema-1", {"source": ""}),
        ("V-post.keypoint.landmark_schema-2", {"groups": []}),
        ("V-post.keypoint.landmark_schema-2", {"groups.0.label": "x"}),
        ("V-post.keypoint.landmark_schema-2", {"groups.0.name": "Body"}),
        ("V-post.keypoint.landmark_schema-2", {"groups.1.name": "body"}),
        ("V-post.keypoint.landmark_schema-2", {"groups.0.points": []}),
        ("V-post.keypoint.landmark_schema-3", {"groups.1.points": ["hip", "tip"]}),
        ("V-post.keypoint.landmark_schema-3", {"groups.1.points": ["wrist", "the tip"]}),
        ("V-post.keypoint.landmark_schema-3", {"groups.1.points": ["wrist", "hand/tip"]}),
        ("V-post.keypoint.canonical_mapping-1", {"canonical_mapping": {"feet": {"toe": "hip"}}}),
        ("V-post.keypoint.canonical_mapping-1", {"groups.1.name": "face", "canonical_mapping": {"face": {"nose": "wrist"}}}),
        ("V-post.keypoint.canonical_mapping-1", {"canonical_mapping.body.the hip": "hip"}),
        ("V-post.keypoint.canonical_mapping-1", {"canonical_mapping.body.mid": {"hip": 0.5, "knee": 0.4}}),
        ("V-post.keypoint.canonical_mapping-1", {"canonical_mapping.body.leg": []}),
        ("V-post.keypoint.canonical_mapping-1", {"canonical_mapping.body.leg": ["hip", "ankle"]}),
    ],
)
def test_a_changed_schema_fails_its_rule(rule: str, changes: dict[str, Any]) -> None:
    assert rule in {failure.rule for failure in check_landmark_schema(changed(SCHEMA, changes), "Demo")}


def test_the_registry_reads_the_user_root_and_refuses_a_name_in_two_files(tmp_path: Path) -> None:
    package, user = tmp_path / "package", tmp_path / "user"
    write_yaml(package / "landmark_schemas" / "Demo.yaml", SCHEMA)
    write_yaml(user / "landmark_schemas" / "Mine.yaml", {**SCHEMA, "name": "Mine"})
    write_yaml(user / "landmark_schemas" / "deeper" / "Skipped.yaml", {"not": "a schema"})
    assert sorted(load_landmark_schema_registry(user, package)) == ["Demo", "Mine"]
    write_yaml(user / "landmark_schemas" / "Demo.yaml", SCHEMA)
    with pytest.raises(SidecarValidationError) as info:
        load_landmark_schema_registry(user, package)
    assert info.value.rules == ("V-post.keypoint.landmark_schema-4",)
    assert str(package / "landmark_schemas" / "Demo.yaml") in str(info.value)


def test_a_schema_file_with_a_duplicate_key_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "landmark_schemas" / "Demo.yaml"
    path.parent.mkdir()
    path.write_bytes(b"name: Demo\nname: Demo\nsource: x\ngroups: []\n")
    with pytest.raises(Exception, match="duplicate key"):
        load_landmark_schema_registry(None, tmp_path)


def test_a_keypoint_sidecar_names_a_schema_of_the_registry(tmp_path: Path) -> None:
    path = "detectors/keypoint_detectors/demo/body/demo-body.yaml"
    with pytest.raises(SidecarValidationError) as info:
        load(tmp_path, BASES["simcc"](), path)
    assert info.value.rules == ("V-post.keypoint.schema-10",) and "Demo3" in str(info.value)
    write_yaml(tmp_path / "user" / "landmark_schemas" / "Demo3.yaml", {"name": "Demo3", "source": "test", "groups": [{"name": "body", "points": ["a", "b", "c"]}]})
    sidecar = load(tmp_path, BASES["simcc"](), path, user_root=tmp_path / "user")
    assert sidecar.keypoint.landmark_schema == "Demo3" and sidecar.outputs[0].keypoint_axis == 1
    assert sidecar.input.resize.crop_policy.expand_ratio == 1.25


# ---------------------------------------------------------------------------------------------
# SPDX
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "expression",
    ["MIT", "mit", "GPL-2.0+", "Apache-2.0 AND (MIT OR BSD-3-Clause)", "GPL-2.0-only WITH Classpath-exception-2.0",
     "CC-BY-4.0 AND LicenseRef-COCO-Images", "DocumentRef-a:LicenseRef-b", "MIT or Apache-2.0"],
)
def test_a_valid_spdx_expression(expression: str) -> None:
    assert is_spdx_expression(expression)


@pytest.mark.parametrize(
    "expression",
    ["", "Not-A-License", "MIT AND", "MIT OR OR MIT", "(MIT", "MIT)", "MIT WITH", "MIT WITH MIT", "MIT And MIT", "MIT Apache-2.0", "unknown"],
)
def test_a_text_that_is_not_an_spdx_expression(expression: str) -> None:
    assert not is_spdx_expression(expression)


def test_the_spdx_list_is_pinned_and_a_license_ref_is_found() -> None:
    assert spdx_license_list_version() == "3.29.0"
    assert has_license_ref("CC-BY-4.0 AND LicenseRef-COCO-Images") and not has_license_ref("MIT")

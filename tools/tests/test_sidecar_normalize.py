"""The normalization table and the selector matching of `tools/sidecar_normalize.py`."""

from __future__ import annotations

import ast
import copy
import sys
from pathlib import Path
from typing import Any

import pytest

import sidecar_normalize as sn

MODULE_PATH = Path(sn.__file__)


def detector(**decode: Any) -> dict[str, Any]:
    """A small object detector sidecar, as the resolver returns it."""
    return {
        "role": ["object_detector"],
        "input": {
            "normalization": "unit_float",
            "resize": {"method": "letterbox", "pad_value": 114},
        },
        "decode": decode,
    }


# --------------------------------------------------------------------------------------------
# normalize
# --------------------------------------------------------------------------------------------


def test_requires_nms_true_derives_selection_nms() -> None:
    assert sn.normalize(detector(requires_nms=True))["decode"]["selection"] == "nms"


def test_requires_nms_false_derives_selection_none() -> None:
    assert sn.normalize(detector(requires_nms=False))["decode"]["selection"] == "none"


def test_missing_requires_nms_derives_selection_none() -> None:
    assert sn.normalize(detector())["decode"]["selection"] == "none"


def test_an_authored_selection_is_kept() -> None:
    data = detector(selection="top_k", requires_nms=True)
    assert sn.normalize(data)["decode"]["selection"] == "top_k"


def test_a_null_selection_counts_as_absent() -> None:
    data = detector(selection=None, requires_nms=True)
    assert sn.normalize(data)["decode"]["selection"] == "nms"


def test_a_detector_without_decode_gets_selection_none() -> None:
    data = detector()
    del data["decode"]
    assert sn.normalize(data)["decode"] == {"selection": "none"}


def test_a_pose_estimator_gets_no_selection() -> None:
    data = {"role": ["pose_estimator"], "input": {"normalization": "none"}}
    assert "decode" not in sn.normalize(data)


def test_a_two_role_sidecar_gets_a_selection() -> None:
    data = detector(requires_nms=True)
    data["role"] = ["object_detector", "pose_estimator"]
    assert sn.normalize(data)["decode"]["selection"] == "nms"


def test_a_role_given_as_a_string_is_read() -> None:
    data = detector(requires_nms=True)
    data["role"] = "object_detector"
    assert sn.normalize(data)["decode"]["selection"] == "nms"


def test_absent_resize_gets_method_none() -> None:
    data = {"role": ["pose_estimator"], "input": {"normalization": "none"}}
    assert sn.normalize(data)["input"]["resize"] == {"method": "none"}


def test_a_null_resize_counts_as_absent() -> None:
    data = {
        "role": ["pose_estimator"],
        "input": {"normalization": "none", "resize": None},
    }
    assert sn.normalize(data)["input"]["resize"] == {"method": "none"}


def test_a_given_resize_is_kept() -> None:
    resize = {"method": "fit", "pad_value": 114}
    data = {"role": ["pose_estimator"], "input": {"resize": resize}}
    assert sn.normalize(data)["input"]["resize"] == resize


def test_letterbox_without_preserve_aspect_ratio_stays_letterbox() -> None:
    assert sn.normalize(detector())["input"]["resize"]["method"] == "letterbox"


def test_letterbox_with_preserve_aspect_ratio_true_stays_letterbox() -> None:
    data = detector()
    data["input"]["resize"]["preserve_aspect_ratio"] = True
    assert sn.normalize(data)["input"]["resize"]["method"] == "letterbox"


def test_letterbox_with_preserve_aspect_ratio_false_becomes_stretch() -> None:
    data = detector()
    data["input"]["resize"]["preserve_aspect_ratio"] = False
    assert sn.normalize(data)["input"]["resize"]["method"] == "stretch"


def test_the_alias_changes_only_the_method() -> None:
    data = detector()
    data["input"]["resize"]["preserve_aspect_ratio"] = False
    expected = copy.deepcopy(data["input"]["resize"])
    expected["method"] = "stretch"
    assert sn.normalize(data)["input"]["resize"] == expected


def test_only_letterbox_has_the_alias() -> None:
    data = detector()
    data["input"]["resize"] = {"method": "fit", "preserve_aspect_ratio": False}
    assert sn.normalize(data)["input"]["resize"]["method"] == "fit"


def test_absent_normalization_gets_imagenet_bgr() -> None:
    data = {"role": ["pose_estimator"], "input": {"resize": {"method": "fit"}}}
    assert sn.normalize(data)["input"]["normalization"] == "imagenet_bgr"


def test_a_given_normalization_is_kept() -> None:
    assert sn.normalize(detector())["input"]["normalization"] == "unit_float"


def test_a_custom_normalization_stays_an_object() -> None:
    custom = {"mode": "custom", "mean": [1.0, 2.0, 3.0], "std": [4.0, 5.0, 6.0]}
    data = detector()
    data["input"]["normalization"] = custom
    assert sn.normalize(data)["input"]["normalization"] == custom


def test_input_defaults_do_not_invent_an_input() -> None:
    data = {"role": ["pose_estimator"]}
    assert sn.normalize(data) == data


def test_normalize_changes_nothing_else() -> None:
    data = detector(selection="none")
    data["outputs"] = [{"name": "o", "semantic": "detections"}]
    assert sn.normalize(data) == data


def test_normalize_returns_a_copy_and_keeps_the_input() -> None:
    data = detector(requires_nms=True)
    before = copy.deepcopy(data)
    result = sn.normalize(data)
    assert data == before
    result["input"]["resize"]["method"] = "changed"
    assert data == before


def test_normalize_is_idempotent() -> None:
    data = detector(requires_nms=True)
    data["input"]["resize"]["preserve_aspect_ratio"] = False
    once = sn.normalize(data)
    assert sn.normalize(once) == once


def test_normalize_needs_a_mapping() -> None:
    with pytest.raises(TypeError):
        sn.normalize(["not", "a", "mapping"])  # type: ignore[arg-type]


def test_derived_by_names_the_rules_that_changed_something() -> None:
    data = {"role": ["object_detector"], "input": {}, "decode": {"requires_nms": True}}
    assert sn.derived_by(data) == ("selection", "resize", "normalization")


def test_derived_by_is_empty_for_a_complete_sidecar() -> None:
    assert sn.derived_by(detector(selection="none")) == ()


def test_the_legacy_alias_is_reported() -> None:
    data = detector(selection="none")
    data["input"]["resize"]["preserve_aspect_ratio"] = False
    assert sn.derived_by(data) == ("letterbox_alias",)


# --------------------------------------------------------------------------------------------
# The table
# --------------------------------------------------------------------------------------------


def test_the_table_has_the_five_derivations_in_order() -> None:
    assert [rule.name for rule in sn.NORMALIZATION_TABLE] == [
        "selection",
        "resize",
        "letterbox_alias",
        "normalization",
        "custom_normalization",
    ]


def test_each_rule_names_its_source_section_and_heading() -> None:
    for rule in sn.NORMALIZATION_TABLE:
        assert rule.section and rule.heading and rule.summary, rule.name


def test_only_the_custom_rule_has_no_action() -> None:
    assert [r.name for r in sn.NORMALIZATION_TABLE if r.apply is None] == [
        "custom_normalization"
    ]


# --------------------------------------------------------------------------------------------
# matches
# --------------------------------------------------------------------------------------------

NORMALIZED = {
    "role": ["object_detector", "pose_estimator"],
    "input": {
        "normalization": "unit_float",
        "resize": {
            "method": "letterbox",
            "pad_value": 114,
            "supports_dynamic_size": False,
        },
    },
    "outputs": [
        {"name": "a", "semantic": "detections", "packed_keypoints": {"offset": 6}},
        {"name": "b", "semantic": "poses", "keypoint_axis": 2},
    ],
    "decode": {"selection": "none", "is_person_only": True, "nothing": None},
    "pose": {"canonical_mapping": {"nose": "head"}, "decode": {"method": "simcc"}},
}


@pytest.mark.parametrize(
    "selector",
    [
        "input.resize.method=letterbox",
        "input.normalization=unit_float",
        "decode.selection=none",
        "role=object_detector",
        "role=pose_estimator",
        "outputs[].semantic=detections",
        "outputs[].semantic=poses",
        "outputs[].keypoint_axis=2",
        "pose.decode.method=simcc",
        "input.resize.pad_value=114",
        "decode.is_person_only=true",
        "input.resize.supports_dynamic_size=false",
    ],
)
def test_matching_selectors(selector: str) -> None:
    assert sn.matches(selector, NORMALIZED)


@pytest.mark.parametrize(
    "selector",
    [
        "input.resize.method=stretch",
        "input.normalization=none",
        "decode.selection=nms",
        "role=other",
        "outputs[].semantic=heatmap",
        "outputs.semantic=detections",
        "outputs[].name=c",
        "input.resize.method.deeper=letterbox",
        "input.normalization.mode=custom",
        "decode.is_person_only=True",
        "decode.is_person_only=false",
        "input.resize.pad_value=114.0",
        "input.resize=letterbox",
        "pose.canonical_mapping=head",
        "missing.path=x",
    ],
)
def test_selectors_that_do_not_match(selector: str) -> None:
    assert not sn.matches(selector, NORMALIZED)


@pytest.mark.parametrize(
    ("selector", "expected"),
    [
        ("pose.canonical_mapping", True),
        ("outputs[].packed_keypoints", True),
        ("outputs[].keypoint_axis", True),
        ("outputs[].name", True),
        ("role", True),
        ("overlay", False),
        ("decode.nothing", False),
        ("outputs[].shape", False),
        ("input.resize.supports_dynamic_size", True),
    ],
)
def test_a_selector_without_value_tests_that_the_path_exists_and_is_not_null(
    selector: str, expected: bool
) -> None:
    assert sn.matches(selector, NORMALIZED) is expected


def test_a_custom_normalization_object_matches_on_its_mode() -> None:
    data = {"input": {"normalization": {"mode": "custom", "scale": 1.0}}}
    assert sn.matches("input.normalization.mode=custom", data)
    assert not sn.matches("input.normalization=custom", data)
    assert not sn.matches("input.normalization=none", data)


def test_a_named_normalization_has_no_mode() -> None:
    data = {"input": {"normalization": "none"}}
    assert not sn.matches("input.normalization.mode=custom", data)
    assert sn.matches("input.normalization=none", data)


def test_a_list_of_scalars_matches_on_any_element() -> None:
    assert sn.matches("tags=b", {"tags": ["a", "b"]})
    assert not sn.matches("tags=c", {"tags": ["a", "b"]})
    assert sn.matches("sizes=2", {"sizes": [1, 2]})
    assert sn.matches("flags=true", {"flags": [False, True]})


def test_a_list_of_mappings_does_not_match_a_value() -> None:
    assert not sn.matches("outputs=detections", NORMALIZED)


def test_a_bracket_segment_needs_a_list() -> None:
    assert not sn.matches("decode[].selection=none", NORMALIZED)
    assert not sn.matches("input[]", NORMALIZED)


def test_a_bracket_segment_can_end_a_path() -> None:
    assert sn.matches("role[]=object_detector", NORMALIZED)
    assert not sn.matches("role[]=other", NORMALIZED)


def test_a_nested_bracket_path_reaches_every_element() -> None:
    data = {"groups": [{"items": [{"id": "a"}]}, {"items": [{"id": "b"}]}]}
    assert sn.matches("groups[].items[].id=b", data)
    assert not sn.matches("groups[].items[].id=c", data)


def test_a_key_that_is_a_number_matches_by_its_text() -> None:
    data = {"batch_artifacts": {1: {"precision": "fp32"}}}
    assert sn.matches("batch_artifacts.1.precision=fp32", data)


def test_a_value_may_contain_an_equals_sign() -> None:
    assert sn.matches("formula=a=b", {"formula": "a=b"})


@pytest.mark.parametrize(
    "selector",
    ["", "=x", "a..b", ".a", "a.", "a=", "a b=c", "a[=c", "a[0]=c", "a.[]=c"],
)
def test_a_selector_that_is_not_well_formed_raises(selector: str) -> None:
    with pytest.raises(ValueError):
        sn.matches(selector, NORMALIZED)


def test_a_selector_must_be_a_string() -> None:
    with pytest.raises(ValueError):
        sn.parse_selector(5)  # type: ignore[arg-type]


def test_parse_selector_splits_path_and_value() -> None:
    assert sn.parse_selector("outputs[].semantic=heatmap") == (
        ("outputs[]", "semantic"),
        "heatmap",
    )
    assert sn.parse_selector("overlay") == (("overlay",), None)


# --------------------------------------------------------------------------------------------
# applies
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("kind", ["format", "common"])
def test_format_and_common_sections_apply_to_every_sidecar(kind: str) -> None:
    assert sn.applies({"kind": kind, "selectors": []}, {})
    assert sn.applies({"kind": kind, "selectors": []}, NORMALIZED)


def test_any_matching_selector_is_enough() -> None:
    front = {
        "kind": "postprocessor",
        "selectors": ["role=other", "decode.selection=none"],
    }
    assert sn.applies(front, NORMALIZED)


def test_no_matching_selector_means_the_section_does_not_apply() -> None:
    front = {
        "kind": "postprocessor",
        "selectors": ["role=other", "decode.selection=nms"],
    }
    assert not sn.applies(front, NORMALIZED)


def test_a_section_without_selectors_applies_to_nothing() -> None:
    assert not sn.applies({"kind": "preprocessor", "selectors": []}, NORMALIZED)
    assert not sn.applies({"kind": "preprocessor"}, NORMALIZED)


def test_selectors_must_be_a_list() -> None:
    with pytest.raises(ValueError):
        sn.applies({"kind": "schema", "selectors": "overlay"}, NORMALIZED)


# --------------------------------------------------------------------------------------------
# The legacy cases end to end
# --------------------------------------------------------------------------------------------


def test_a_legacy_yolox_style_sidecar_gets_the_current_selectors() -> None:
    legacy = {
        "role": ["object_detector"],
        "input": {
            "normalization": "none",
            "resize": {"method": "letterbox", "preserve_aspect_ratio": True},
        },
        "decode": {"requires_nms": False},
    }
    normalized = sn.normalize(legacy)
    assert sn.matches("decode.selection=none", normalized)
    assert sn.matches("input.resize.method=letterbox", normalized)
    assert not sn.matches("decode.selection", legacy)


def test_a_legacy_stretch_alias_matches_stretch_and_not_letterbox() -> None:
    legacy = detector(requires_nms=False)
    legacy["input"]["resize"]["preserve_aspect_ratio"] = False
    normalized = sn.normalize(legacy)
    assert sn.matches("input.resize.method=stretch", normalized)
    assert not sn.matches("input.resize.method=letterbox", normalized)


def test_an_old_pose_sidecar_without_normalization_matches_imagenet_bgr() -> None:
    legacy = {
        "role": ["pose_estimator"],
        "input": {"resize": {"method": "affine_person_crop"}},
    }
    assert sn.matches("input.normalization=imagenet_bgr", sn.normalize(legacy))
    assert not sn.matches("input.normalization=imagenet_bgr", legacy)


# --------------------------------------------------------------------------------------------
# The module moves into the package unchanged
# --------------------------------------------------------------------------------------------


def _imported_modules() -> set[str]:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "a relative import cannot move"
            modules.add(node.module or "")
    return modules


def test_the_module_imports_only_the_standard_library() -> None:
    for module in _imported_modules():
        assert module.split(".")[0] in sys.stdlib_module_names, module


def test_the_module_imports_nothing_from_tools() -> None:
    tools = {p.stem for p in MODULE_PATH.parent.glob("*.py")} - {MODULE_PATH.stem}
    assert not {m.split(".")[0] for m in _imported_modules()} & tools

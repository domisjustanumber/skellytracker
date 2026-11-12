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
        "object": {"classes": ["person"], "decode": decode},
    }


# --------------------------------------------------------------------------------------------
# normalize
# --------------------------------------------------------------------------------------------


def test_an_authored_selection_is_kept() -> None:
    data = detector(selection="top_k")
    assert sn.normalize(data)["object"]["decode"]["selection"] == "top_k"


def test_no_rule_derives_a_selection() -> None:
    assert sn.normalize(detector())["object"]["decode"] == {}
    data = detector()
    del data["object"]
    assert "object" not in sn.normalize(data)


def test_absent_resize_gets_method_none() -> None:
    data = {"role": ["keypoint_detector"], "input": {"normalization": "none"}}
    assert sn.normalize(data)["input"]["resize"] == {"method": "none"}


def test_a_null_resize_counts_as_absent() -> None:
    data = {
        "role": ["keypoint_detector"],
        "input": {"normalization": "none", "resize": None},
    }
    assert sn.normalize(data)["input"]["resize"] == {"method": "none"}


def test_a_given_resize_is_kept() -> None:
    resize = {"method": "fit", "pad_value": 114}
    data = {"role": ["keypoint_detector"], "input": {"resize": resize}}
    assert sn.normalize(data)["input"]["resize"] == resize


def test_a_letterbox_stays_letterbox() -> None:
    assert sn.normalize(detector())["input"]["resize"]["method"] == "letterbox"


def test_absent_normalization_stays_absent() -> None:
    # `input.normalization` is required and has no default (ADR-0QKK).
    data = {"role": ["keypoint_detector"], "input": {"resize": {"method": "fit"}}}
    normalized = sn.normalize(data)
    assert "normalization" not in normalized["input"]
    assert not sn.matches("input.normalization=imagenet", normalized)


def test_a_given_normalization_is_kept() -> None:
    assert sn.normalize(detector())["input"]["normalization"] == "unit_float"


def test_a_custom_normalization_stays_an_object() -> None:
    custom = {"mode": "custom", "mean": [1.0, 2.0, 3.0], "std": [4.0, 5.0, 6.0]}
    data = detector()
    data["input"]["normalization"] = custom
    assert sn.normalize(data)["input"]["normalization"] == custom


def test_input_defaults_do_not_invent_an_input() -> None:
    data = {"role": ["keypoint_detector"]}
    assert sn.normalize(data) == data


def test_normalize_changes_nothing_else() -> None:
    data = detector(selection="none")
    data["outputs"] = [{"name": "o", "semantic": "detections"}]
    assert sn.normalize(data) == data


def test_normalize_returns_a_copy_and_keeps_the_input() -> None:
    data = detector(selection="none")
    before = copy.deepcopy(data)
    result = sn.normalize(data)
    assert data == before
    result["input"]["resize"]["method"] = "changed"
    assert data == before


def test_normalize_is_idempotent() -> None:
    data = {"role": ["object_detector"], "input": {}, "object": {"decode": {}}}
    once = sn.normalize(data)
    assert once != data
    assert sn.normalize(once) == once


def test_normalize_needs_a_mapping() -> None:
    with pytest.raises(TypeError):
        sn.normalize(["not", "a", "mapping"])  # type: ignore[arg-type]


def test_derived_by_names_the_rules_that_changed_something() -> None:
    data = {"role": ["object_detector"], "input": {}, "object": {"decode": {}}}
    assert sn.derived_by(data) == ("resize",)


def test_derived_by_is_empty_for_a_complete_sidecar() -> None:
    assert sn.derived_by(detector(selection="none")) == ()


# --------------------------------------------------------------------------------------------
# The table
# --------------------------------------------------------------------------------------------


def test_the_table_has_its_rules_in_order() -> None:
    assert [rule.name for rule in sn.NORMALIZATION_TABLE] == [
        "resize",
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
    "role": ["object_detector", "keypoint_detector"],
    "input": {
        "normalization": "unit_float",
        "resize": {
            "method": "letterbox",
            "pad_value": 114,
            "crop_policy": {"maintain_aspect_ratio": False},
        },
    },
    "outputs": [
        {"name": "a", "semantic": "packed_detections", "packed_keypoints": {"offset": 6}},
        {"name": "b", "semantic": "instance_keypoints", "keypoint_axis": 2},
    ],
    "object": {"decode": {"selection": "none", "clamp_boxes": True, "nothing": None}},
    "keypoint": {
        "canonical_mapping": {"nose": "head"},
        "decode": {"method": "simcc"},
    },
}


@pytest.mark.parametrize(
    "selector",
    [
        "input.resize.method=letterbox",
        "input.normalization=unit_float",
        "object.decode.selection=none",
        "role=object_detector",
        "role=keypoint_detector",
        "outputs[].semantic=packed_detections",
        "outputs[].semantic=instance_keypoints",
        "outputs[].keypoint_axis=2",
        "keypoint.decode.method=simcc",
        "input.resize.pad_value=114",
        "object.decode.clamp_boxes=true",
        "input.resize.crop_policy.maintain_aspect_ratio=false",
    ],
)
def test_matching_selectors(selector: str) -> None:
    assert sn.matches(selector, NORMALIZED)


@pytest.mark.parametrize(
    "selector",
    [
        "input.resize.method=stretch",
        "input.normalization=none",
        "object.decode.selection=nms",
        "role=other",
        "outputs[].semantic=simcc_x",
        "outputs.semantic=packed_detections",
        "outputs[].name=c",
        "input.resize.method.deeper=letterbox",
        "input.normalization.mode=custom",
        "object.decode.clamp_boxes=True",
        "object.decode.clamp_boxes=false",
        "input.resize.pad_value=114.0",
        "input.resize=letterbox",
        "keypoint.canonical_mapping=head",
        "missing.path=x",
    ],
)
def test_selectors_that_do_not_match(selector: str) -> None:
    assert not sn.matches(selector, NORMALIZED)


@pytest.mark.parametrize(
    ("selector", "expected"),
    [
        ("keypoint.canonical_mapping", True),
        ("outputs[].packed_keypoints", True),
        ("outputs[].keypoint_axis", True),
        ("outputs[].name", True),
        ("role", True),
        ("keypoint.overlay", False),
        ("object.decode.nothing", False),
        ("outputs[].shape", False),
        ("input.resize.crop_policy.maintain_aspect_ratio", True),
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
    assert sn.parse_selector("outputs[].semantic=simcc_x") == (
        ("outputs[]", "semantic"),
        "simcc_x",
    )
    assert sn.parse_selector("overlay") == (("overlay",), None)


# --------------------------------------------------------------------------------------------
# applies
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("kind", ["format", "common"])
def test_format_and_common_sections_apply_to_every_sidecar(kind: str) -> None:
    assert sn.applies(kind, [], {})
    assert sn.applies(kind, [], NORMALIZED)


def test_a_common_section_of_one_key_applies_only_when_the_key_is_present() -> None:
    selectors = ["batching.batch_conversion"]
    assert not sn.applies("common", selectors, {"batching": {"mode": "static"}})
    assert sn.applies("common", selectors, {"batching": {"batch_conversion": {"profile_id": "p"}}})


def test_any_matching_selector_is_enough() -> None:
    assert sn.applies("postprocessor", ["role=other", "object.decode.selection=none"], NORMALIZED)


def test_no_matching_selector_means_the_section_does_not_apply() -> None:
    assert not sn.applies("postprocessor", ["role=other", "object.decode.selection=nms"], NORMALIZED)


def test_a_section_without_selectors_applies_to_nothing() -> None:
    assert not sn.applies("preprocessor", [], NORMALIZED)


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

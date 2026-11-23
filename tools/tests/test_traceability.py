"""Doc tests for the traceability of the sidecar spec.

They check the front matter of the section files, the section map, the rule IDs, the form of the
references to code, the tests and the vectors, the selectors, the section applicability of
synthetic sidecars, the note of the generated `TRACEABILITY.md`, and the normalization table.

This file moves to the specs repository with `tools/sidecar_trace.py`. It imports no
skellytracker, onnx or onnxruntime, and it reads no file of the package
(`tools/tests/test_intake_gate.py` checks the imports). The selector code is the lead copy of the
spec that `sidecar_trace` loads. The skellytracker test `tools/tests/test_package_traceability.py`
checks the parts that need the package: the referenced functions, the `Literal` values of the
package model, the sidecar scan with the package resolver, the generated file and the spec
citations in the code.
"""

from __future__ import annotations

import ast
import functools
import re
from pathlib import Path
from typing import Any

import pytest

import sidecar_trace as st

sn = st.sidecar_normalize  # the lead copy: specs/model-sidecar/reference/sidecar_normalize.py

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "tools"
SPEC_DIR = REPO_ROOT / "specs" / "model-sidecar"
INDEX_PATH = REPO_ROOT / "specs" / "model-sidecar" / "sidecar-spec.md"


# --------------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------------


def relative(path: Path) -> str:
    return path.relative_to(SPEC_DIR).as_posix()


@functools.cache
def section_paths() -> tuple[Path, ...]:
    return tuple(st.section_files(REPO_ROOT))


@functools.cache
def front_of(path: Path) -> dict[str, Any]:
    return st.parse_front_matter(path.read_text(encoding="utf-8"), relative(path))[0]


@functools.cache
def all_sections() -> tuple[st.Section, ...]:
    return tuple(st.load_sections(REPO_ROOT))


def section_ids() -> list[str]:
    return [section.id for section in all_sections()]


def headings_of(text: str) -> set[str]:
    """Return the headings of a Markdown text, lowercase and without backticks."""
    found = set()
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
        elif not in_fence and (match := re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)):
            found.add(match.group(1).replace("`", "").strip().lower())
    return found


def step_pairs() -> list[tuple[str, str, str]]:
    return [
        (section.id, step, reference)
        for section in all_sections()
        for step, reference in section.implemented_by.items()
    ]


path_ids = relative

# --------------------------------------------------------------------------------------------
# Front matter
# --------------------------------------------------------------------------------------------


def test_there_are_section_files() -> None:
    assert len(section_paths()) >= 28


def test_every_section_file_has_valid_front_matter() -> None:
    # load_sections raises a TraceError on a file whose front matter breaks a FrontMatter rule.
    assert len(st.load_sections(REPO_ROOT)) == len(section_paths())


@pytest.mark.parametrize("path", section_paths(), ids=path_ids)
def test_a_section_has_the_draft_banner_exactly_when_it_is_draft(path: Path) -> None:
    body = st.parse_front_matter(path.read_text(encoding="utf-8"), relative(path))[1]
    lines = [line for line in body.splitlines() if line.strip()]
    assert lines[0].startswith("# "), relative(path)
    banner = lines[1].startswith(st.DRAFT_BANNER)
    assert banner == (front_of(path)["status"]["spec"] == "draft"), relative(path)


def test_each_no_model_reason_names_a_section() -> None:
    no_model = st.load_inventory(REPO_ROOT)["no_model"]
    assert set(no_model) <= set(section_ids())
    assert all(isinstance(reason, str) and reason.strip() for reason in no_model.values())


@pytest.mark.parametrize("path", section_paths(), ids=path_ids)
def test_a_section_names_the_inverse_step_exactly_when_it_has_an_inverse(
    path: Path,
) -> None:
    body = st.parse_front_matter(path.read_text(encoding="utf-8"), relative(path))[1]
    has_inverse = "inverse" in headings_of(body)
    assert ("inverse" in front_of(path)["implemented_by"]) == has_inverse


@pytest.mark.parametrize("path", section_paths(), ids=path_ids)
def test_the_other_lists(path: Path) -> None:
    front = front_of(path)
    assert len(set(front["tests"])) == len(front["tests"])
    for test_path in front["tests"]:
        assert test_path.startswith("skellytracker/tests/") and test_path.endswith(
            ".py"
        )


# --------------------------------------------------------------------------------------------
# Section IDs and the section map
# --------------------------------------------------------------------------------------------


def test_section_ids_are_unique() -> None:
    ids = [front_of(path)["id"] for path in section_paths()]
    assert len(ids) == len(set(ids)), sorted({i for i in ids if ids.count(i) > 1})


def test_the_section_map_matches_the_section_files() -> None:
    rows = st.readme_section_map(REPO_ROOT)
    assert len({row.id for row in rows}) == len(rows)
    assert {row.id for row in rows} == {front_of(p)["id"] for p in section_paths()}
    assert [row.id for row in rows] == section_ids()
    by_id = {section.id: section for section in all_sections()}
    for row in rows:
        section = by_id[row.id]
        assert row.file == section.path, row.id
        assert row.title == section.title, row.id


def test_the_section_map_lists_every_file_once() -> None:
    files = [row.file for row in st.readme_section_map(REPO_ROOT)]
    assert sorted(files) == sorted(relative(path) for path in section_paths())


# --------------------------------------------------------------------------------------------
# Rule IDs
# --------------------------------------------------------------------------------------------

RULE_LINE = re.compile(
    r"^- \[[ xX]\] `(?P<rule>V-(?P<owner>[a-z][a-z0-9_.]*[a-z0-9])-(?P<number>\d+))`",
    re.MULTILINE,
)
RULE_NAME = re.compile(r"V-(?P<owner>[a-z][a-z0-9_.]*[a-z0-9])-(?P<number>\d+)\b")


def defined_rules() -> dict[Path, list[re.Match[str]]]:
    return {
        path: list(RULE_LINE.finditer(path.read_text(encoding="utf-8")))
        for path in section_paths()
    }


def test_there_are_rules() -> None:
    assert sum(len(matches) for matches in defined_rules().values()) >= 60


def test_rule_ids_are_unique_across_files() -> None:
    seen: dict[str, Path] = {}
    for path, matches in defined_rules().items():
        for match in matches:
            rule = match["rule"]
            assert (
                rule not in seen
            ), f"{rule} is defined in {relative(seen[rule])} and {relative(path)}"
            seen[rule] = path


def test_each_rule_belongs_to_the_section_of_its_file() -> None:
    for path, matches in defined_rules().items():
        for match in matches:
            assert match["owner"] == front_of(path)["id"], (
                relative(path),
                match["rule"],
            )


def test_the_rules_of_a_section_are_unique_and_numbered_from_one() -> None:
    """A deleted rule leaves its number unused, so a section can have gaps (ADR-6GE2)."""
    for path, matches in defined_rules().items():
        numbers = [int(match["number"]) for match in matches]
        assert numbers == sorted(set(numbers)) and all(n >= 1 for n in numbers), relative(path)


def test_every_rule_that_a_section_file_names_is_defined() -> None:
    defined = {m["rule"] for matches in defined_rules().values() for m in matches}
    for path in section_paths():
        for match in RULE_NAME.finditer(path.read_text(encoding="utf-8")):
            assert match.group(0) in defined, f"{relative(path)} names {match.group(0)}"


# --------------------------------------------------------------------------------------------
# References to code, tests and vectors
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("section_id", "step", "reference"),
    step_pairs(),
    ids=[f"{section}:{step}" for section, step, _ in step_pairs()],
)
def test_implemented_by_has_the_form_of_a_package_reference(
    section_id: str, step: str, reference: str
) -> None:
    """The form only. `tools/tests/test_package_traceability.py` finds the file and the symbol."""
    parts = st.split_reference(reference)
    if parts is None:
        return
    path, _symbol = parts
    assert path.startswith("skellytracker/")


# The code that the implementation stage writes. Each implementing function there has the line
# `Implements: <section-id>` in its docstring (the skill `implement-sidecar-section`).
NEW_CODE = (
    "skellytracker/core/model_spec/",
    "skellytracker/core/detectors/processing/pre/",
    "skellytracker/core/detectors/processing/post/",
)


def new_code_pairs() -> list[tuple[str, str, str]]:
    return [pair for pair in step_pairs() if pair[2].startswith(NEW_CODE)]


def test_there_are_implementing_functions_in_the_new_code() -> None:
    assert new_code_pairs()


@pytest.mark.parametrize("section", all_sections(), ids=lambda s: s.id)
def test_the_vector_file_exists_and_has_the_name_of_the_section(
    section: st.Section,
) -> None:
    if section.vectors is None:
        return
    assert section.vectors == f"vectors/{section.id}.yaml"
    assert (SPEC_DIR / section.vectors).is_file()


def test_every_vector_file_belongs_to_the_section_that_names_it() -> None:
    named = {s.vectors for s in all_sections() if s.vectors}
    files = {f"vectors/{p.name}" for p in (SPEC_DIR / "vectors").glob("*.yaml")}
    assert files == named


# --------------------------------------------------------------------------------------------
# The selectors
# --------------------------------------------------------------------------------------------


def selector_values(path: str) -> set[str]:
    """Return the values of every selector that tests the given path."""
    values = set()
    for section in all_sections():
        for selector in section.front.selectors:
            segments, value = sn.parse_selector(selector)
            if ".".join(segments) == path and value is not None:
                values.add(value)
    return values


def test_the_custom_normalization_has_the_mode_selector() -> None:
    assert "custom" in selector_values("input.normalization.mode")


# --------------------------------------------------------------------------------------------
# The generated file
# --------------------------------------------------------------------------------------------


def test_traceability_says_that_it_is_generated() -> None:
    text = (SPEC_DIR / "TRACEABILITY.md").read_text(encoding="utf-8")
    assert "Generated by `tools/sidecar_trace.py matrix`; do not edit." in text


# --------------------------------------------------------------------------------------------
# The applicability of the sections, as the sidecars imply it
# --------------------------------------------------------------------------------------------

# Synthetic sidecars pin the semantics, so a new example model does not change these tests.
NONE_DETECTOR = {
    "schema_version": "2.0.0",
    "model_id": "none-detector",
    "role": ["object_detector"],
    "input": {"resize": {"method": "letterbox"}, "normalization": "imagenet"},
    "object": {"classes": ["person"], "decode": {"selection": "none"}},
    "outputs": [{"semantic": "packed_detections"}],
}
# No rule derives a selection: a detector that omits it matches no selection section.
NO_SELECTION_DETECTOR = {
    **{key: value for key, value in NONE_DETECTOR.items() if key != "object"},
    "model_id": "no-selection-detector",
}
NMS_DETECTOR = {
    "schema_version": "2.0.0",
    "model_id": "nms-detector",
    "role": ["object_detector"],
    "input": {"resize": {"method": "letterbox"}, "normalization": "unit_float"},
    "object": {"classes": ["person"], "decode": {"selection": "nms"}},
    "outputs": [{"semantic": "boxes"}],
}
BOTTOM_UP_POSE = {
    "schema_version": "2.0.0",
    "model_id": "bottom-up-pose",
    "role": ["object_detector", "keypoint_detector"],
    "input": {"resize": {"method": "fit"}, "normalization": "unit_float"},
    "object": {"classes": ["person"], "decode": {"selection": "none"}},
    "keypoint": {"estimator_type": "bottom_up", "decode": {"method": "coordinate"}},
    "outputs": [{"semantic": "packed_detections", "packed_keypoints": {"offset": 6}}],
}
DETECTOR_SECTIONS = {
    "pre.resize.interpolation",
    "pre.normalize",
    "post.object.decode",
    "post.object.outputs",
    "post.unprojection",
}


def synthetic(data: dict[str, Any]) -> st.Sidecar:
    return st.Sidecar(
        key=f"{data['model_id']}@test",
        model_id=data["model_id"],
        source="test",
        origin="example",
        path=f"{data['model_id']}.yaml",
        schema_version=data["schema_version"],
        resolved=data,
        normalized=sn.normalize(data),
        derived=sn.derived_by(data),
    )


@functools.cache
def sections_by_id() -> dict[str, st.Section]:
    return {section.id: section for section in all_sections()}


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (NONE_DETECTOR, {*DETECTOR_SECTIONS, "pre.resize.letterbox", "post.object.selection.none"}),
        (NO_SELECTION_DETECTOR, {*DETECTOR_SECTIONS, "pre.resize.letterbox"}),
        (NMS_DETECTOR, {*DETECTOR_SECTIONS, "pre.resize.letterbox", "post.object.selection.nms"}),
        (
            BOTTOM_UP_POSE,
            {
                *DETECTOR_SECTIONS,
                "pre.resize.fit",
                "post.object.selection.none",
                "post.keypoint.bottom_up",
                "post.keypoint.decode.coordinate",
                "post.keypoint.schema",
                "post.keypoint.landmark_schema",
                "post.keypoint.canonical_mapping",
            },
        ),
    ],
    ids=lambda value: value["model_id"] if isinstance(value, dict) else "",
)
def test_a_sidecar_matches_exactly_the_sections_of_its_selectors(
    data: dict[str, Any], expected: set[str]
) -> None:
    universal = {
        s.id
        for s in all_sections()
        if s.kind in sn.UNIVERSAL_KINDS and not s.front.selectors
    }
    sidecar = synthetic(data)
    applicable = st.applicable_models(all_sections(), [sidecar])
    assert {sid for sid, models in applicable.items() if models} == universal | expected


def test_an_explicit_normalization_is_kept_and_an_omitted_one_gets_no_default() -> None:
    # `input.normalization` has no default (ADR-0QKK).
    explicit = synthetic(BOTTOM_UP_POSE)
    omitted = sn.normalize({"input": {}})
    assert explicit.normalized["input"]["normalization"] == "unit_float"
    assert "normalization" not in explicit.derived
    assert "normalization" not in omitted["input"]


def test_a_detector_without_a_selection_gets_no_derived_selection() -> None:
    omitted = synthetic(NO_SELECTION_DETECTOR)
    assert omitted.derived == ()
    assert "object" not in omitted.normalized


def test_the_cells_that_carry_text() -> None:
    def cell(section_id: str, data: dict[str, Any]) -> str:
        return st._cell(sections_by_id()[section_id], synthetic(data))

    poses = {**BOTTOM_UP_POSE, "outputs": [{"semantic": "instance_keypoints"}]}
    no_resize = {**BOTTOM_UP_POSE, "input": {"normalization": "unit_float"}}
    assert cell("pre.normalize", NONE_DETECTOR) == "imagenet"
    assert cell("pre.normalize", NMS_DETECTOR) == "unit_float"
    assert cell("pre.normalize", BOTTOM_UP_POSE) == "unit_float"
    assert cell("pre.resize.none", no_resize) == "x (derived)"
    assert cell("post.object.selection.none", NONE_DETECTOR) == "none"
    assert cell("post.object.selection.nms", NMS_DETECTOR) == "nms"
    assert cell("post.object.selection.none", BOTTOM_UP_POSE) == "none"
    assert cell("post.keypoint.bottom_up", BOTTOM_UP_POSE) == "x (packed)"
    assert cell("post.keypoint.bottom_up", poses) == "x (instance_keypoints)"
    assert cell("post.object.decode", NMS_DETECTOR) == "x"


# --------------------------------------------------------------------------------------------
# The normalization table cites real sections and headings
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("rule", sn.NORMALIZATION_TABLE, ids=lambda r: r.name)
def test_each_normalization_rule_cites_an_existing_section_and_heading(
    rule: sn.NormalizationRule,
) -> None:
    sections = {s.id: s for s in all_sections()}
    assert rule.section in sections
    assert rule.heading.lower() in headings_of(sections[rule.section].body)


# --------------------------------------------------------------------------------------------
# The heading compare of the spec citations (tools/tests/test_package_traceability.py)
# --------------------------------------------------------------------------------------------


def normalized_heading(text: str) -> str:
    return text.replace("`", "").strip().lower()


def test_a_citation_compares_without_case_and_backticks() -> None:
    assert normalized_heading("Sizes") == normalized_heading("`sizes`")


# --------------------------------------------------------------------------------------------
# The tools
# --------------------------------------------------------------------------------------------


def test_no_tool_imports_the_tests() -> None:
    test_modules = {p.stem for p in (TOOLS_DIR / "tests").glob("*.py")} | {"tests"}
    for path in sorted(TOOLS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                names = {(node.module or "").split(".")[0]}
            else:
                continue
            assert (
                not names & test_modules
            ), f"{path.name} imports {names & test_modules}"

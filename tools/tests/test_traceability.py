"""Doc tests for the traceability of the sidecar spec.

They check the front matter of the section files, the section map, the rule IDs, the references
to code, tests and vectors, the coverage of the model's `Literal` values, the sidecar scan,
the generated `TRACEABILITY.md`, and the spec citations in the code.
"""

from __future__ import annotations

import ast
import functools
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

import sidecar_normalize as sn
import sidecar_trace as st

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "tools"
SPEC_DIR = REPO_ROOT / "specs" / "model-sidecar"
INDEX_PATH = REPO_ROOT / "specs" / "model-sidecar" / "sidecar-spec.md"
MODEL_PATH = REPO_ROOT / "skellytracker" / "core" / "sidecar" / "model.py"
PACKAGE_DIR = REPO_ROOT / "skellytracker"


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


@functools.cache
def scan() -> st.Scan:
    return st.scan_sidecars(REPO_ROOT)


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


def test_the_rules_of_a_section_are_numbered_from_one_without_gaps() -> None:
    for path, matches in defined_rules().items():
        numbers = sorted(int(match["number"]) for match in matches)
        assert numbers == list(range(1, len(numbers) + 1)), relative(path)


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
def test_implemented_by_names_a_function_that_exists(
    section_id: str, step: str, reference: str
) -> None:
    parts = st.split_reference(reference)
    if parts is None:
        return
    path, symbol = parts
    assert path.startswith("skellytracker/")
    file = REPO_ROOT / path
    assert file.is_file(), f"{section_id} {step}: {path} does not exist"
    assert st.find_symbol(
        file.read_text(encoding="utf-8"), symbol
    ), f"{section_id} {step}: {path} has no {symbol}"


@pytest.mark.parametrize("section", all_sections(), ids=lambda s: s.id)
def test_the_test_files_exist(section: st.Section) -> None:
    for test_path in section.tests:
        assert (REPO_ROOT / test_path).is_file(), test_path


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
# The Literal values of model.py are covered by selectors
# --------------------------------------------------------------------------------------------


def literal_values(annotation: ast.AST) -> list[str]:
    """Return the string values of the first `Literal[...]` in an annotation."""
    for node in ast.walk(annotation):
        if (
            isinstance(node, ast.Subscript)
            and getattr(node.value, "id", None) == "Literal"
        ):
            arguments = (
                node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            )
            return [a.value for a in arguments if isinstance(a, ast.Constant)]
    raise AssertionError("no Literal in the annotation")


def alias_values(tree: ast.Module, name: str) -> list[str]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            return literal_values(node.value)
    raise AssertionError(f"model.py has no module-level {name}")


def field_values(tree: ast.Module, class_name: str, field: str) -> list[str]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for member in node.body:
                if (
                    isinstance(member, ast.AnnAssign)
                    and isinstance(member.target, ast.Name)
                    and member.target.id == field
                ):
                    return literal_values(member.annotation)
    raise AssertionError(f"model.py has no {class_name}.{field}")


@functools.cache
def model_tree() -> ast.Module:
    return ast.parse(MODEL_PATH.read_text(encoding="utf-8"))


def selector_values(path: str) -> set[str]:
    """Return the values of every selector that tests the given path."""
    values = set()
    for section in all_sections():
        for selector in section.front.selectors:
            segments, value = sn.parse_selector(selector)
            if ".".join(segments) == path and value is not None:
                values.add(value)
    return values


# shortcut: the frozen model.py keeps imagenet_bgr and imagenet_rgb (ADR-90CE), so the check
# skips them and asks for the merged mode imagenet; delete this at stage M8 of the
# implementation plan, when model.py has the mode imagenet.
MERGED_IMAGENET_MODES = {"imagenet_bgr", "imagenet_rgb"}

# shortcut: the frozen model.py still accepts heatmap and simcc_z, which the spec removed (ADR-9MJ6,
# ADR-9HBB), so the check skips them; delete this at stage M8 of the implementation plan, when
# model.py drops them.
REMOVED_VALUES = {"heatmap", "simcc_z"}


def literal_cases() -> list[tuple[str, list[str], set[str]]]:
    tree = model_tree()
    return [
        (
            "ResizeSpec.method",
            field_values(tree, "ResizeSpec", "method"),
            selector_values("input.resize.method"),
        ),
        (
            "NamedNormalizationMode and custom",
            [
                *(
                    set(alias_values(tree, "NamedNormalizationMode"))
                    - MERGED_IMAGENET_MODES
                ),
                "imagenet",
                "custom",
            ],
            selector_values("input.normalization")
            | selector_values("input.normalization.mode"),
        ),
        (
            "OutputSemantic",
            sorted(set(alias_values(tree, "OutputSemantic")) - REMOVED_VALUES),
            selector_values("outputs[].semantic"),
        ),
        (
            "PoseDecodeSpec.method",
            sorted(set(field_values(tree, "PoseDecodeSpec", "method")) - REMOVED_VALUES),
            selector_values("pose.decode.method"),
        ),
        ("Role", alias_values(tree, "Role"), selector_values("role")),
    ]


@pytest.mark.parametrize(
    ("name", "values", "covered"),
    literal_cases(),
    ids=[case[0] for case in literal_cases()],
)
def test_every_literal_value_is_covered_by_a_selector(
    name: str, values: list[str], covered: set[str]
) -> None:
    assert values, f"no values found for {name}"
    assert (
        set(values) <= covered
    ), f"{name}: no selector covers {sorted(set(values) - covered)}"


def test_the_literal_reader_finds_the_known_values() -> None:
    tree = model_tree()
    assert "letterbox" in field_values(tree, "ResizeSpec", "method")
    assert "imagenet_rgb" in alias_values(tree, "NamedNormalizationMode")
    assert "simcc_x" in alias_values(tree, "OutputSemantic")
    assert "coordinate" in field_values(tree, "PoseDecodeSpec", "method")


def test_the_custom_normalization_has_the_mode_selector() -> None:
    assert "custom" in selector_values("input.normalization.mode")


# --------------------------------------------------------------------------------------------
# The generated file
# --------------------------------------------------------------------------------------------


def test_traceability_equals_a_fresh_generation() -> None:
    path = SPEC_DIR / "TRACEABILITY.md"
    actual = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    assert actual == st.render_traceability(
        REPO_ROOT
    ), "TRACEABILITY.md is out of date; run: python tools/sidecar_trace.py matrix"


def test_traceability_says_that_it_is_generated() -> None:
    text = (SPEC_DIR / "TRACEABILITY.md").read_text(encoding="utf-8")
    assert "Generated by `tools/sidecar_trace.py matrix`; do not edit." in text


def test_the_matrix_has_a_row_for_each_section_and_a_column_for_each_sidecar() -> None:
    lines = st.render_traceability(REPO_ROOT).splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| Section | "))
    table = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        table.append(line)
    header, _rule, *rows = table
    assert header.count("<br>") == len(scan().sidecars)
    assert [row.split("`")[1] for row in rows] == section_ids()


# --------------------------------------------------------------------------------------------
# The scan
# --------------------------------------------------------------------------------------------


def test_the_scan_keys_are_unique() -> None:
    keys = [sidecar.key for sidecar in scan().sidecars]
    assert keys
    assert len(keys) == len(set(keys))


def test_the_scan_finds_no_sidecar_outside_the_examples() -> None:
    # The old package sidecars are deleted and replaced, not migrated (ADR-AMJ8).
    sidecars = scan().sidecars
    assert sidecars
    for sidecar in sidecars:
        assert sidecar.origin == "example", sidecar.key
        assert sidecar.path.startswith("specs/model-sidecar/examples/"), sidecar.key
    assert not any(name.startswith("skellytracker/") for name in scan().skipped)


def test_the_example_sidecars_have_schema_version_2_0_0() -> None:
    for sidecar in scan().sidecars:
        assert sidecar.schema_version == "2.0.0", sidecar.key


def test_the_scan_skips_every_other_yaml_file() -> None:
    every_yaml = {
        p.relative_to(REPO_ROOT).as_posix()
        for p in (SPEC_DIR / "examples").rglob("*.yaml")
    }
    found = {sidecar.path for sidecar in scan().sidecars}
    skipped = set(scan().skipped)
    assert not found & skipped
    assert found | skipped == every_yaml
    assert len(found) == len(scan().sidecars)
    assert not skipped  # no example uses a fragment since ADR-NBG2


def test_a_skipped_file_is_not_a_sidecar() -> None:
    for name in scan().skipped:
        data = yaml.safe_load((REPO_ROOT / name).read_text(encoding="utf-8"))
        is_sidecar = (
            isinstance(data, dict)
            and "schema_version" in data
            and data.get("model_id") == Path(name).stem
        )
        assert not is_sidecar, name


# --------------------------------------------------------------------------------------------
# The applicability of the sections, as the sidecars imply it
# --------------------------------------------------------------------------------------------

# Synthetic sidecars pin the semantics, so a new example model does not change these tests.
NONE_DETECTOR = {
    "schema_version": "2.0.0",
    "model_id": "none-detector",
    "role": ["object_detector"],
    "input": {"resize": {"method": "letterbox"}, "normalization": "imagenet"},
    "decode": {"selection": "none"},
    "outputs": [{"semantic": "detections"}],
}
# No rule derives a selection: a detector that omits it matches no selection section.
NO_SELECTION_DETECTOR = {
    **{key: value for key, value in NONE_DETECTOR.items() if key != "decode"},
    "model_id": "no-selection-detector",
}
NMS_DETECTOR = {
    "schema_version": "2.0.0",
    "model_id": "nms-detector",
    "role": ["object_detector"],
    "input": {"resize": {"method": "letterbox"}, "normalization": "unit_float"},
    "decode": {"selection": "nms"},
    "outputs": [{"semantic": "boxes"}],
}
BOTTOM_UP_POSE = {
    "schema_version": "2.0.0",
    "model_id": "bottom-up-pose",
    "role": ["object_detector", "pose_estimator"],
    "input": {"resize": {"method": "fit"}, "normalization": "unit_float"},
    "decode": {"selection": "none"},
    "pose": {"estimator_type": "bottom_up", "decode": {"method": "coordinate"}},
    "outputs": [{"semantic": "detections", "packed_keypoints": {"offset": 6}}],
}
DETECTOR_SECTIONS = {
    "pre.resize.interpolation",
    "pre.normalize",
    "post.det.decode",
    "post.det.outputs",
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


@functools.cache
def applicability() -> dict[str, set[str]]:
    applicable = st.applicable_models(all_sections(), scan().sidecars)
    return {
        section_id: {s.key for s in models} for section_id, models in applicable.items()
    }


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (NONE_DETECTOR, {*DETECTOR_SECTIONS, "pre.resize.letterbox", "post.det.selection.none"}),
        (NO_SELECTION_DETECTOR, {*DETECTOR_SECTIONS, "pre.resize.letterbox"}),
        (NMS_DETECTOR, {*DETECTOR_SECTIONS, "pre.resize.letterbox", "post.det.selection.nms"}),
        (
            BOTTOM_UP_POSE,
            {
                *DETECTOR_SECTIONS,
                "pre.resize.fit",
                "post.det.selection.none",
                "post.pose.bottom_up",
                "post.pose.decode.coordinate",
                "post.pose.schema",
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
    assert "decode" not in omitted.normalized


def test_every_example_detector_gives_its_selection() -> None:
    # The selection rows show only what the sidecar gives, because no rule derives a selection.
    for sidecar in scan().sidecars:
        if "object_detector" in sidecar.resolved.get("role", []):
            assert sidecar.resolved["decode"]["selection"], sidecar.key


def test_the_cells_that_carry_text() -> None:
    def cell(section_id: str, data: dict[str, Any]) -> str:
        return st._cell(sections_by_id()[section_id], synthetic(data))

    poses = {**BOTTOM_UP_POSE, "outputs": [{"semantic": "poses"}]}
    no_resize = {**BOTTOM_UP_POSE, "input": {"normalization": "unit_float"}}
    assert cell("pre.normalize", NONE_DETECTOR) == "imagenet"
    assert cell("pre.normalize", NMS_DETECTOR) == "unit_float"
    assert cell("pre.normalize", BOTTOM_UP_POSE) == "unit_float"
    assert cell("pre.resize.none", no_resize) == "x (derived)"
    assert cell("post.det.selection.none", NONE_DETECTOR) == "none"
    assert cell("post.det.selection.nms", NMS_DETECTOR) == "nms"
    assert cell("post.det.selection.none", BOTTOM_UP_POSE) == "none"
    assert cell("post.pose.bottom_up", BOTTOM_UP_POSE) == "x (packed)"
    assert cell("post.pose.bottom_up", poses) == "x (poses)"
    assert cell("post.det.decode", NMS_DETECTOR) == "x"


def test_format_and_common_sections_without_selectors_apply_to_every_sidecar() -> None:
    for section in all_sections():
        if section.kind in sn.UNIVERSAL_KINDS and not section.front.selectors:
            assert applicability()[section.id] == {s.key for s in scan().sidecars}


def test_every_sidecar_matches_the_normalization_section() -> None:
    for sidecar in scan().sidecars:
        assert sidecar.key in applicability()["pre.normalize"], sidecar.key


def test_every_sidecar_matches_a_resize_section() -> None:
    resize = {
        "pre.resize.letterbox",
        "pre.resize.stretch",
        "pre.resize.fit",
        "pre.resize.none",
        "pre.resize.affine_person_crop",
    }
    for sidecar in scan().sidecars:
        hits = {sid for sid in resize if sidecar.key in applicability()[sid]}
        assert len(hits) == 1, (sidecar.key, hits)


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
# Spec citations in the code
# --------------------------------------------------------------------------------------------

CITATION = re.compile(r'specs/model-sidecar/sidecar-spec\.md,?\s+"(?P<heading>[^"\n]+)"')


def normalized_heading(text: str) -> str:
    return text.replace("`", "").strip().lower()


def citations() -> list[tuple[str, str]]:
    found = []
    for path in sorted(PACKAGE_DIR.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        found.extend(
            (path.relative_to(REPO_ROOT).as_posix(), match["heading"])
            for match in CITATION.finditer(text)
        )
    return found


def test_the_code_cites_the_spec() -> None:
    assert len(citations()) >= 8


def test_every_spec_citation_in_the_code_names_a_heading_of_the_index() -> None:
    index = {
        normalized_heading(h)
        for h in headings_of(INDEX_PATH.read_text(encoding="utf-8"))
    }
    missing = [
        f"{path}: {heading!r}"
        for path, heading in citations()
        if normalized_heading(heading) not in index
    ]
    assert not missing, "the permanent index has no such heading:\n" + "\n".join(
        missing
    )


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

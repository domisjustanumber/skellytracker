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

KINDS = {"format", "common", "preprocessor", "postprocessor", "schema"}
REQUIRED_STEPS_BY_KIND = {
    "format": {"validate", "load"},
    "common": {"validate", "load"},
    "preprocessor": {"validate", "forward"},
    "postprocessor": {"validate", "decode"},
    "schema": {"validate", "load"},
}
# A preprocessor names an `inverse` step only when its algorithm has an inverse. Normalization and
# interpolation have none: the section has an "Inverse" heading exactly when it has the step.
OPTIONAL_STEPS_BY_KIND = {"preprocessor": {"inverse"}}
KINDS_BY_FOLDER = {
    "format": {"format"},
    "common": {"common"},
    "pre": {"preprocessor"},
    "post": {"postprocessor", "schema"},
}
STEP_STATES = {"implemented", "partial", "missing"}
SPEC_STATES = {"stable", "draft"}
VERSION = re.compile(r"vNEXT|v\d{4}\.\d{2}\.\d+")

EXPECTED_KEYS = {
    "yolox@skellytracker",
    "rtmpose-body@skellytracker",
    "rtmpose-hand@skellytracker",
    "rtmpose-face@skellytracker",
    "rtmw-wholebody@skellytracker",
    "yolo26@ultralytics-exporter",
    "yolo26-body@ultralytics-exporter",
    "rtmdet-person@openmmlab-exporter",
    "rtmw-wholebody@openmmlab-exporter",
    "rtmo-body7@openmmlab-exporter",
}


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


@pytest.mark.parametrize("path", section_paths(), ids=path_ids)
def test_front_matter_has_exactly_the_documented_keys(path: Path) -> None:
    assert set(front_of(path)) == set(st.FRONT_MATTER_KEYS)


@pytest.mark.parametrize("path", section_paths(), ids=path_ids)
def test_identity_fields(path: Path) -> None:
    front = front_of(path)
    assert isinstance(front["id"], str) and front["id"]
    assert isinstance(front["title"], str) and front["title"]
    assert front["kind"] in KINDS
    folder = path.parent.name
    assert front["id"].split(".")[0] == folder
    assert front["kind"] in KINDS_BY_FOLDER[folder]


@pytest.mark.parametrize("path", section_paths(), ids=path_ids)
def test_version_fields(path: Path) -> None:
    front = front_of(path)
    assert isinstance(front["since"], str) and VERSION.fullmatch(front["since"])
    assert isinstance(front["changed_in"], list)
    assert len(set(front["changed_in"])) == len(front["changed_in"])
    for version in front["changed_in"]:
        assert isinstance(version, str) and VERSION.fullmatch(version), version


@pytest.mark.parametrize("path", section_paths(), ids=path_ids)
def test_selectors(path: Path) -> None:
    front = front_of(path)
    selectors = front["selectors"]
    assert isinstance(selectors, list)
    assert len(set(selectors)) == len(selectors)
    for selector in selectors:
        sn.parse_selector(selector)
    if front["kind"] in sn.UNIVERSAL_KINDS:
        # a common section of one optional key has one key-presence selector
        assert all("=" not in selector for selector in selectors), selectors
        assert len(selectors) <= 1, selectors
    else:
        assert selectors, "a section of this kind needs at least one selector"


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
def test_implemented_by_has_the_steps_of_the_kind(path: Path) -> None:
    front = front_of(path)
    implemented_by = front["implemented_by"]
    assert isinstance(implemented_by, dict)
    required = REQUIRED_STEPS_BY_KIND[front["kind"]]
    optional = OPTIONAL_STEPS_BY_KIND.get(front["kind"], set())
    assert required <= set(implemented_by) <= required | optional
    for reference in implemented_by.values():
        assert isinstance(reference, str)


@pytest.mark.parametrize("path", section_paths(), ids=path_ids)
def test_a_section_names_the_inverse_step_exactly_when_it_has_an_inverse(
    path: Path,
) -> None:
    body = st.parse_front_matter(path.read_text(encoding="utf-8"), relative(path))[1]
    has_inverse = "inverse" in headings_of(body)
    assert ("inverse" in front_of(path)["implemented_by"]) == has_inverse


@pytest.mark.parametrize("path", section_paths(), ids=path_ids)
def test_status_has_a_spec_state_and_a_state_for_each_step(path: Path) -> None:
    front = front_of(path)
    status = front["status"]
    assert isinstance(status, dict)
    assert set(status) == {"spec", *front["implemented_by"]}
    assert status["spec"] in SPEC_STATES
    for step in front["implemented_by"]:
        assert status[step] in STEP_STATES, step


@pytest.mark.parametrize("path", section_paths(), ids=path_ids)
def test_a_step_is_missing_in_the_status_exactly_when_it_is_missing_in_implemented_by(
    path: Path,
) -> None:
    front = front_of(path)
    for step, reference in front["implemented_by"].items():
        assert (reference == st.MISSING) == (front["status"][step] == "missing"), step


@pytest.mark.parametrize("path", section_paths(), ids=path_ids)
def test_the_other_lists(path: Path) -> None:
    front = front_of(path)
    assert isinstance(front["external_impl"], list)
    assert isinstance(front["tests"], list)
    assert len(set(front["tests"])) == len(front["tests"])
    for test_path in front["tests"]:
        assert isinstance(test_path, str)
        assert test_path.startswith("skellytracker/tests/") and test_path.endswith(
            ".py"
        )
    assert front["vectors"] is None or isinstance(front["vectors"], str)


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
        for selector in section.front["selectors"]:
            segments, value = sn.parse_selector(selector)
            if ".".join(segments) == path and value is not None:
                values.add(value)
    return values


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
            [*alias_values(tree, "NamedNormalizationMode"), "custom"],
            selector_values("input.normalization")
            | selector_values("input.normalization.mode"),
        ),
        (
            "OutputSemantic",
            alias_values(tree, "OutputSemantic"),
            selector_values("outputs[].semantic"),
        ),
        (
            "PoseDecodeSpec.method",
            field_values(tree, "PoseDecodeSpec", "method"),
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


def test_the_scan_finds_exactly_the_expected_sidecars() -> None:
    keys = [sidecar.key for sidecar in scan().sidecars]
    assert len(keys) == len(set(keys))
    assert set(keys) == EXPECTED_KEYS


def test_the_package_sidecars_have_the_legacy_version_and_the_package_source() -> None:
    package = [s for s in scan().sidecars if s.source == "skellytracker"]
    assert {s.model_id for s in package} == {
        "yolox",
        "rtmpose-body",
        "rtmpose-hand",
        "rtmpose-face",
        "rtmw-wholebody",
    }
    for sidecar in package:
        assert sidecar.origin == "package"
        assert sidecar.schema_version == "v2024.09.1019"
        assert sidecar.legacy


def test_the_example_sidecars_are_at_vnext() -> None:
    for sidecar in scan().sidecars:
        if sidecar.origin == "example":
            assert sidecar.schema_version == "vNEXT"
            assert not sidecar.legacy


def test_the_scan_skips_every_other_yaml_file() -> None:
    roots = [PACKAGE_DIR / "core" / "detectors", SPEC_DIR / "examples"]
    every_yaml = {
        p.relative_to(REPO_ROOT).as_posix() for r in roots for p in r.rglob("*.yaml")
    }
    found = {sidecar.path for sidecar in scan().sidecars}
    skipped = set(scan().skipped)
    assert not found & skipped
    assert found | skipped == every_yaml
    assert len(found) == len(EXPECTED_KEYS)
    for name in (
        "skellytracker/core/detectors/shared/skeletons/coco17_tracked_points.yaml",
        "skellytracker/core/detectors/keypoint_detectors/mediapipe/body/mediapipe_body.yaml",
        "skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_to_canonical_mapping.yaml",
        "specs/model-sidecar/examples/detectors/shared/skeletons/coco133_skeletons.yaml",
    ):
        assert name in skipped


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

BODY_HAND_FACE = [
    "rtmpose-body@skellytracker",
    "rtmpose-hand@skellytracker",
    "rtmpose-face@skellytracker",
]
RTMW_BOTH = ["rtmw-wholebody@skellytracker", "rtmw-wholebody@openmmlab-exporter"]

EXPECTED_APPLICABILITY = {
    "common.batch_conversion": set(),
    "pre.resize.letterbox": {
        "yolox@skellytracker",
        "yolo26@ultralytics-exporter",
        "yolo26-body@ultralytics-exporter",
        "rtmdet-person@openmmlab-exporter",
    },
    "pre.resize.stretch": set(),
    "pre.resize.fit": {"rtmo-body7@openmmlab-exporter"},
    "pre.resize.none": set(),
    "pre.resize.affine_person_crop": {*BODY_HAND_FACE, *RTMW_BOTH},
    "post.det.selection.none": {
        "yolox@skellytracker",
        "yolo26@ultralytics-exporter",
        "yolo26-body@ultralytics-exporter",
        "rtmo-body7@openmmlab-exporter",
    },
    "post.det.selection.top_k": set(),
    "post.det.selection.nms": {"rtmdet-person@openmmlab-exporter"},
    "post.pose.decode.simcc": {*BODY_HAND_FACE, *RTMW_BOTH},
    "post.pose.decode.heatmap": set(),
    "post.pose.decode.coordinate": {
        "yolo26-body@ultralytics-exporter",
        "rtmo-body7@openmmlab-exporter",
    },
    "post.pose.bottom_up": {
        "yolo26-body@ultralytics-exporter",
        "rtmo-body7@openmmlab-exporter",
    },
}

EXPECTED_NORMALIZATION = {
    "yolox@skellytracker": "none",
    "rtmpose-body@skellytracker": "imagenet_bgr",
    "rtmpose-hand@skellytracker": "imagenet_bgr",
    "rtmpose-face@skellytracker": "imagenet_bgr",
    "rtmw-wholebody@skellytracker": "imagenet_bgr",
    "yolo26@ultralytics-exporter": "unit_float",
    "yolo26-body@ultralytics-exporter": "unit_float",
    "rtmdet-person@openmmlab-exporter": "imagenet_bgr",
    "rtmw-wholebody@openmmlab-exporter": "imagenet_rgb",
    "rtmo-body7@openmmlab-exporter": "none",
}


@functools.cache
def applicability() -> dict[str, set[str]]:
    applicable = st.applicable_models(all_sections(), scan().sidecars)
    return {
        section_id: {s.key for s in models} for section_id, models in applicable.items()
    }


@pytest.mark.parametrize(
    ("section_id", "expected"), sorted(EXPECTED_APPLICABILITY.items())
)
def test_section_applicability(section_id: str, expected: set[str]) -> None:
    assert applicability()[section_id] == expected


def matrix_cells() -> dict[str, dict[str, str]]:
    """Return the cell text of the generated matrix: section ID -> sidecar key -> text."""
    lines = st.render_traceability(REPO_ROOT).splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| Section | "))
    keys = [
        c.strip().replace("<br>@", "@") for c in lines[start].strip("|").split("|")[1:]
    ]
    cells: dict[str, dict[str, str]] = {}
    for line in lines[start + 2 :]:
        if not line.startswith("|"):
            break
        columns = [c.strip() for c in line.strip("|").split("|")]
        cells[columns[0].split("`")[1]] = dict(zip(keys, columns[1:], strict=True))
    return cells


EXPECTED_CELLS = {
    "pre.normalize": {
        "yolox@skellytracker": "none",
        "rtmpose-body@skellytracker": "imagenet_bgr (legacy)",
        "rtmpose-hand@skellytracker": "imagenet_bgr (legacy)",
        "rtmpose-face@skellytracker": "imagenet_bgr (legacy)",
        "rtmw-wholebody@skellytracker": "imagenet_bgr (legacy)",
        "yolo26@ultralytics-exporter": "unit_float",
        "yolo26-body@ultralytics-exporter": "unit_float",
        "rtmdet-person@openmmlab-exporter": "imagenet_bgr",
        "rtmw-wholebody@openmmlab-exporter": "imagenet_rgb",
        "rtmo-body7@openmmlab-exporter": "none",
    },
    "post.det.selection.none": {
        "yolox@skellytracker": "none (legacy, derived)",
        "yolo26@ultralytics-exporter": "none",
        "yolo26-body@ultralytics-exporter": "none",
        "rtmo-body7@openmmlab-exporter": "none",
    },
    "post.det.selection.nms": {"rtmdet-person@openmmlab-exporter": "nms"},
    "post.pose.bottom_up": {
        "yolo26-body@ultralytics-exporter": "x (packed)",
        "rtmo-body7@openmmlab-exporter": "x (poses)",
    },
}


@pytest.mark.parametrize(("section_id", "expected"), sorted(EXPECTED_CELLS.items()))
def test_the_cells_that_carry_text(section_id: str, expected: dict[str, str]) -> None:
    row = matrix_cells()[section_id]
    assert {key: text for key, text in row.items() if text} == expected


def test_every_sidecar_matches_the_normalization_section_with_its_mode() -> None:
    for sidecar in scan().sidecars:
        assert sidecar.key in applicability()["pre.normalize"]
        mode = sidecar.normalized["input"]["normalization"]
        assert mode == EXPECTED_NORMALIZATION[sidecar.key]


def test_the_legacy_yolox_selection_is_derived() -> None:
    by_key = {s.key: s for s in scan().sidecars}
    assert by_key["yolox@skellytracker"].derived == ("selection",)
    assert by_key["yolox@skellytracker"].normalized["decode"]["selection"] == "none"
    for key, sidecar in by_key.items():
        if key != "yolox@skellytracker":
            assert "selection" not in sidecar.derived, key


def test_format_and_common_sections_without_selectors_apply_to_every_sidecar() -> None:
    for section in all_sections():
        if section.kind in sn.UNIVERSAL_KINDS and not section.front["selectors"]:
            assert applicability()[section.id] == EXPECTED_KEYS


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

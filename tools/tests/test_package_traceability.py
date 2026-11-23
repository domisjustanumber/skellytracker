"""Doc tests for the traceability of the sidecar spec that need the package.

They check that each `implemented_by` reference names a function of the package, the `Implements:`
lines of the package code, the test files of the sections, the coverage of the `Literal` values of
the package model, the sidecar scan with the package resolver and the package sidecars, the
generated `TRACEABILITY.md`, the spec citations in the code and the section table of the package.

This test stays in skellytracker. The checks of the spec alone are in
`tools/tests/test_traceability.py`, which moves to the specs repository with
`tools/sidecar_trace.py`. This file uses the helpers of that file. That file must never import
this file.
"""

from __future__ import annotations

import ast
import functools
import re
from pathlib import Path

import pytest
import yaml
from test_traceability import (
    INDEX_PATH,
    REPO_ROOT,
    SPEC_DIR,
    all_sections,
    headings_of,
    new_code_pairs,
    normalized_heading,
    section_ids,
    selector_values,
    step_pairs,
)

import sidecar_trace as st
from sidecar_trace_package import HOST
from skellytracker.core.model_spec import sidecar_normalize as sn


@pytest.mark.parametrize(
    ("section_id", "step", "reference"),
    step_pairs(),
    ids=[f"{section}:{step}" for section, step, _ in step_pairs()],
)
def test_implemented_by_names_a_function_that_exists(
    section_id: str, step: str, reference: str
) -> None:
    """The file and the symbol. `test_traceability.py` checks the form of the reference."""
    parts = st.split_reference(reference)
    if parts is None:
        return
    path, symbol = parts
    file = REPO_ROOT / path
    assert file.is_file(), f"{section_id} {step}: {path} does not exist"
    assert st.find_symbol(
        file.read_text(encoding="utf-8"), symbol
    ), f"{section_id} {step}: {path} has no {symbol}"


MODEL_PATH = REPO_ROOT / "skellytracker" / "core" / "sidecar" / "model.py"


PACKAGE_DIR = REPO_ROOT / "skellytracker"


@functools.cache
def scan() -> st.Scan:
    return st.scan_sidecars(REPO_ROOT, **HOST)


IMPLEMENTS = re.compile(r"^\s*Implements: (\S+)\s*$", re.M)


def docstring_of(path: Path, symbol: str) -> str:
    """Return the docstring of `name` or `Class.name` in a Python file."""
    nodes: list[ast.AST] = [ast.parse(path.read_text(encoding="utf-8"))]
    for name in symbol.split("."):
        nodes = [
            child
            for node in nodes
            for child in ast.iter_child_nodes(node)
            if isinstance(child, ast.ClassDef | ast.FunctionDef) and child.name == name
        ]
    assert len(nodes) == 1, f"{path}: {symbol}"
    return ast.get_docstring(nodes[0]) or ""  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("section_id", "step", "reference"),
    new_code_pairs(),
    ids=[f"{section}:{step}" for section, step, _ in new_code_pairs()],
)
def test_an_implementing_function_of_the_new_code_names_its_section(
    section_id: str, step: str, reference: str
) -> None:
    path, symbol = st.split_reference(reference)
    assert section_id in IMPLEMENTS.findall(docstring_of(REPO_ROOT / path, symbol)), reference


def test_each_implements_line_names_a_section() -> None:
    # The pipeline sections have no traceability matrix: their IDs come from the front matter.
    pipeline = REPO_ROOT / "specs" / "pipeline"
    front = re.compile(r"^id: (\S+)$", re.M)
    known = set(section_ids()) | {
        found.group(1)
        for file in [*pipeline.glob("*.md"), *(pipeline / "nodes").glob("*.md")]
        if (found := front.search(file.read_text(encoding="utf-8")))
    }
    for path in sorted((REPO_ROOT / "skellytracker").rglob("*.py")):
        named = set(IMPLEMENTS.findall(path.read_text(encoding="utf-8")))
        assert named <= known, f"{path.relative_to(REPO_ROOT).as_posix()}: {sorted(named - known)}"


@pytest.mark.parametrize("section", all_sections(), ids=lambda s: s.id)
def test_the_test_files_exist(section: st.Section) -> None:
    for test_path in section.tests:
        assert (REPO_ROOT / test_path).is_file(), test_path


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


# shortcut: the frozen model.py keeps imagenet_bgr and imagenet_rgb (ADR-90CE), so the check
# skips them and asks for the merged mode imagenet; delete this at stage M8 of the
# implementation plan, when model.py has the mode imagenet.
MERGED_IMAGENET_MODES = {"imagenet_bgr", "imagenet_rgb"}


# shortcut: the frozen model.py still accepts heatmap and simcc_z, which the spec removed (ADR-9MJ6,
# ADR-9HBB), so the check skips them; delete this at stage M8 of the implementation plan, when
# model.py drops them.
REMOVED_VALUES = {"heatmap", "simcc_z"}


# shortcut: the frozen model.py keeps the names from before ADR-88WQ and ADR-G3FA, so the check maps them to the
# new names; delete this at stage M8 of the implementation plan, when model.py has the new names.
RENAMED_VALUES = {
    "pose_estimator": "keypoint_detector",
    "detections": "packed_detections",
    "keypoints": "keypoint_coordinates",
    "poses": "instance_keypoints",
    "affine_person_crop": "affine_crop",
}


def renamed(values: list[str]) -> list[str]:
    return [RENAMED_VALUES.get(value, value) for value in values]


def literal_cases() -> list[tuple[str, list[str], set[str]]]:
    tree = model_tree()
    return [
        (
            "ResizeSpec.method",
            renamed(field_values(tree, "ResizeSpec", "method")),
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
            renamed(sorted(set(alias_values(tree, "OutputSemantic")) - REMOVED_VALUES)),
            selector_values("outputs[].semantic"),
        ),
        (
            "PoseDecodeSpec.method",
            sorted(set(field_values(tree, "PoseDecodeSpec", "method")) - REMOVED_VALUES),
            selector_values("keypoint.decode.method"),
        ),
        ("Role", renamed(alias_values(tree, "Role")), selector_values("role")),
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


def test_traceability_equals_a_fresh_generation() -> None:
    path = SPEC_DIR / "TRACEABILITY.md"
    actual = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    assert actual == st.render_traceability(
        REPO_ROOT, **HOST
    ), "TRACEABILITY.md is out of date; run: python tools/sidecar_trace_package.py matrix"


def test_the_matrix_has_a_row_for_each_section_and_a_column_for_each_sidecar() -> None:
    lines = st.render_traceability(REPO_ROOT, **HOST).splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| Section | "))
    table = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        table.append(line)
    header, _rule, *rows = table
    assert header.count("<br>") == len(scan().sidecars)
    assert [row.split("`")[1] for row in rows] == section_ids()


def test_the_scan_keys_are_unique() -> None:
    keys = [sidecar.key for sidecar in scan().sidecars]
    assert keys
    assert len(keys) == len(set(keys))


PACKAGE_DETECTORS = REPO_ROOT / "skellytracker" / "core" / "model_zoo" / "detectors"


def test_each_package_sidecar_is_a_byte_copy_of_an_example() -> None:
    # The old package sidecars are deleted and replaced, not migrated (ADR-AMJ8). A sidecar of
    # `core/model_zoo/detectors/` is the copy of a reference example, at the same layout path.
    sidecars = scan().sidecars
    assert sidecars
    for sidecar in sidecars:
        assert sidecar.origin in ("example", "example, package"), sidecar.key
        assert sidecar.path.startswith("specs/model-sidecar/examples/"), sidecar.key
    assert not any(name.startswith("skellytracker/") for name in scan().skipped)
    copies = {
        f"specs/model-sidecar/examples/detectors/{p.relative_to(PACKAGE_DETECTORS).as_posix()}": p
        for p in PACKAGE_DETECTORS.rglob("*.yaml")
    }
    assert copies
    assert set(copies) == {s.path for s in sidecars if s.origin == "example, package"}
    for example, copy in copies.items():
        assert (REPO_ROOT / example).read_bytes() == copy.read_bytes(), example


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
    assert not skipped  # no example uses a fragment since ADR-NBG2, and no package sidecar has one


def test_a_skipped_file_is_not_a_sidecar() -> None:
    for name in scan().skipped:
        data = yaml.safe_load((REPO_ROOT / name).read_text(encoding="utf-8"))
        is_sidecar = (
            isinstance(data, dict)
            and "schema_version" in data
            and data.get("model_id") == Path(name).stem
        )
        assert not is_sidecar, name


@functools.cache
def applicability() -> dict[str, set[str]]:
    applicable = st.applicable_models(all_sections(), scan().sidecars)
    return {
        section_id: {s.key for s in models} for section_id, models in applicable.items()
    }


def test_every_example_detector_gives_its_selection() -> None:
    # The selection rows show only what the sidecar gives, because no rule derives a selection.
    for sidecar in scan().sidecars:
        if "object_detector" in sidecar.resolved.get("role", []):
            assert sidecar.resolved["object"]["decode"]["selection"], sidecar.key


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
        "pre.resize.affine_crop",
    }
    for sidecar in scan().sidecars:
        hits = {sid for sid in resize if sidecar.key in applicability()[sid]}
        assert len(hits) == 1, (sidecar.key, hits)


CITATION = re.compile(r'specs/model-sidecar/sidecar-spec\.md,?\s+"(?P<heading>[^"\n]+)"')


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


def test_the_package_section_table_equals_the_front_matter_of_the_spec() -> None:
    from skellytracker.core.model_spec.sections import IMPLEMENTED_SECTIONS, SECTIONS

    spec = [(section.id, section.kind, tuple(section.front.selectors)) for section in st.load_sections(REPO_ROOT)]
    assert [tuple(section) for section in SECTIONS] == spec
    assert IMPLEMENTED_SECTIONS <= {section.id for section in SECTIONS}

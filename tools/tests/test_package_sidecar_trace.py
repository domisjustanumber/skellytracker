"""The functions of `tools/sidecar_trace.py` that resolve sidecars, with the package resolver.

The scan, the matrix, `impact` and `examples` resolve each sidecar with the resolver of a host. In
skellytracker, the resolver is `resolve_sidecar_composition` of the package, and
`tools/sidecar_trace_package.py` gives it. These tests use the small repositories of
`tools/tests/test_sidecar_trace.py` (`make_repo`, `make_git_repo`).

This test stays in skellytracker: it imports the package. `tools/tests/test_sidecar_trace.py`
moves to the specs repository with the trace tool. This file uses the helpers of that file. That
file must never import this file.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest
import yaml
from test_sidecar_trace import (
    BAR,
    BAZ,
    FOO,
    MODEL_V1,
    POST_V1,
    PRE_V1,
    git,
    make_git_repo,
    make_repo,
    needs_git,
    needs_git_program,
    write,
)

import sidecar_trace as st
import sidecar_trace_package as stp
from skellytracker.core.model_spec.resolution import resolve_sidecar_composition

# The host of the trace in the small repositories: the package resolver and the package sidecar root.
HOST = {"resolve": resolve_sidecar_composition, "package_root": "skellytracker/core/model_zoo"}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return make_repo(tmp_path)


@pytest.fixture
def git_repo(repo: Path) -> Path:
    return make_git_repo(repo)


def test_the_scan_finds_the_sidecars_and_skips_the_other_yaml(repo: Path) -> None:
    scan = st.scan_sidecars(repo, **HOST)
    assert [s.key for s in scan.sidecars] == [
        "foo@a-lib",
        "baz@declared-lib",
        "bar@other-exporter",
    ]
    assert scan.skipped == (
        "specs/model-sidecar/examples/detectors/object_detectors/foo/other.yaml",
        "specs/model-sidecar/examples/detectors/shared/empty.yaml",
        "specs/model-sidecar/examples/detectors/shared/skeletons/frag.yaml",
    )


PACKAGE_BAZ = "skellytracker/core/model_zoo/detectors/keypoint_detectors/baz/body/baz.yaml"


EXAMPLE_BAZ = "specs/model-sidecar/examples/detectors/keypoint_detectors/baz/body/baz.yaml"


def test_the_scan_reads_only_the_detectors_folder_of_the_package_root(repo: Path) -> None:
    write(repo, "skellytracker/core/detectors/shared/bad.yaml", "a: [1\n")
    write(repo, "skellytracker/core/model_zoo/landmark_schemas/bad.yaml", "a: [1\n")
    scan = st.scan_sidecars(repo, **HOST)
    shown = [s.path for s in scan.sidecars] + list(scan.skipped)
    assert all(p.startswith("specs/model-sidecar/examples/") for p in shown)
    assert {s.origin for s in scan.sidecars} == {"example"}


def test_a_package_copy_of_an_example_is_one_model_with_both_roots(repo: Path) -> None:
    before = st.scan_sidecars(repo, **HOST)
    write(repo, PACKAGE_BAZ, BAZ)
    scan = st.scan_sidecars(repo, **HOST)
    assert [s.key for s in scan.sidecars] == [s.key for s in before.sidecars]
    origins = {s.key: s.origin for s in scan.sidecars}
    assert origins.pop("baz@declared-lib") == "example, package"
    assert set(origins.values()) == {"example"}
    baz = next(s for s in scan.sidecars if s.key == "baz@declared-lib")
    assert baz.path == EXAMPLE_BAZ
    assert scan.skipped == before.skipped
    assert "| `baz@declared-lib` | example, package |" in st.render_traceability(repo, **HOST)


def test_a_package_sidecar_with_one_different_byte_raises_with_both_files(repo: Path) -> None:
    write(repo, PACKAGE_BAZ, BAZ + "\n")
    with pytest.raises(st.TraceError) as error:
        st.scan_sidecars(repo, **HOST)
    assert PACKAGE_BAZ in str(error.value)
    assert EXAMPLE_BAZ in str(error.value)


def test_a_package_sidecar_with_no_example_has_the_root_package(repo: Path) -> None:
    only = "skellytracker/core/model_zoo/detectors/keypoint_detectors/qux/body/qux.yaml"
    write(repo, only, BAZ.replace("model_id: baz", "model_id: qux"))
    scan = st.scan_sidecars(repo, **HOST)
    qux = next(s for s in scan.sidecars if s.key == "qux@declared-lib")
    assert (qux.origin, qux.path) == ("package", only)


def test_a_declared_source_wins_over_the_inventory(repo: Path) -> None:
    keys = {s.key: s for s in st.scan_sidecars(repo, **HOST).sidecars}
    assert keys["baz@declared-lib"].source == "declared-lib"
    assert keys["bar@other-exporter"].source == "other-exporter"
    assert keys["bar@other-exporter"].origin == "example"


def test_an_example_without_any_source_raises(repo: Path) -> None:
    write(repo, "specs/model-sidecar/inventory.yaml", "examples: {}\n")
    with pytest.raises(st.TraceError, match="source"):
        st.scan_sidecars(repo, **HOST)


def test_a_repeated_key_raises(repo: Path) -> None:
    write(
        repo,
        "specs/model-sidecar/examples/detectors/object_detectors/copy/foo.yaml",
        FOO,
    )
    with pytest.raises(st.TraceError, match="foo@a-lib"):
        st.scan_sidecars(repo, **HOST)


def test_a_yaml_error_raises(repo: Path) -> None:
    write(repo, "specs/model-sidecar/examples/detectors/shared/bad.yaml", "a: [1\n")
    with pytest.raises(st.TraceError, match="bad.yaml"):
        st.scan_sidecars(repo, **HOST)


def test_a_sidecar_that_cannot_resolve_raises(repo: Path) -> None:
    broken = (
        FOO.replace("model_id: foo", "model_id: broken")
        + "extra: {$ref: missing.yaml}\n"
    )
    write(
        repo,
        "specs/model-sidecar/examples/detectors/object_detectors/broken/broken.yaml",
        broken,
    )
    with pytest.raises(st.TraceError, match="broken.yaml"):
        st.scan_sidecars(repo, **HOST)


def test_the_scan_derives_no_normalization(repo: Path) -> None:
    # `input.normalization` has no default (ADR-0QKK).
    foo = next(s for s in st.scan_sidecars(repo, **HOST).sidecars if s.model_id == "foo")
    assert "normalization" not in foo.normalized["input"]
    assert foo.normalized["object"] == foo.resolved["object"]
    assert foo.derived == ()


def test_the_sections_apply_to_the_right_sidecars(repo: Path) -> None:
    sections = st.load_sections(repo)
    sidecars = st.scan_sidecars(repo, **HOST).sidecars
    applicable = st.applicable_models(sections, sidecars)
    assert [s.key for s in applicable["common.a"]] == [s.key for s in sidecars]
    assert [s.key for s in applicable["pre.resize.letterbox"]] == ["bar@other-exporter"]
    assert [s.key for s in applicable["post.object.selection.nms"]] == [
        "foo@a-lib",
        "bar@other-exporter",
    ]


def test_the_text_has_the_note_and_the_four_parts(repo: Path) -> None:
    text = st.render_traceability(repo, **HOST)
    assert st.NOTE in text
    assert "tools/sidecar_trace.py matrix" in text
    for heading in (
        "## Models and sections",
        "## Implementation status",
        "## External implementations",
        "## Backlog",
    ):
        assert heading in text


def test_the_text_is_deterministic_and_has_lf_endings(repo: Path) -> None:
    text = st.render_traceability(repo, **HOST)
    assert text == st.render_traceability(repo, **HOST)
    assert "\r" not in text
    assert text.endswith("\n") and not text.endswith("\n\n")


def test_the_matrix_rows_and_cells(repo: Path) -> None:
    lines = st.render_traceability(repo, **HOST).splitlines()
    header = next(line for line in lines if line.startswith("| Section | foo<br>"))
    assert header == (
        "| Section | foo<br>@a-lib | baz<br>@declared-lib | bar<br>@other-exporter |"
    )
    row = next(line for line in lines if line.startswith("| [`common.a`]"))
    assert row == "| [`common.a`](common/a.md) | x | x | x |"
    row = next(line for line in lines if line.startswith("| [`pre.resize.letterbox`]"))
    assert row == "| [`pre.resize.letterbox`](pre/letterbox.md) |  |  | x |"
    row = next(
        line for line in lines if line.startswith("| [`post.object.selection.nms`]")
    )
    assert row == (
        "| [`post.object.selection.nms`](post/nms.md) | nms |  | nms |"
    )


def test_the_statuses_functions_tests_and_vectors_are_listed(repo: Path) -> None:
    text = st.render_traceability(repo, **HOST)
    assert (
        "| [`pre.resize.letterbox`](pre/letterbox.md) | stable | "
        "`validate` implemented: `pkg/model.py::Resize`<br>"
        "`forward` implemented: `pkg/pre.py::letterbox`<br>"
        "`inverse` missing | `pkg/test_pre.py` | "
        "[`vectors/pre.resize.letterbox.yaml`](vectors/pre.resize.letterbox.yaml)<br>"
        "0 cases, 0 verified | 1 unknown | 0 of 0 | none |  | open: example, vectors |"
    ) in text


def test_the_coverage_columns_and_the_gate(repo: Path) -> None:
    spec = repo / "specs/model-sidecar"
    path = spec / "pre/letterbox.md"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\n- [ ] `V-pre.resize.letterbox-1`: one.\n- [ ] `V-pre.resize.letterbox-2`: two.\n",
        encoding="utf-8",
        newline="\n",
    )
    cases = [
        {"id": "a", "verified_against": ["x"], "expect": {"n_w": 1}},
        {"id": "b", "expect": {"failed": ["V-pre.resize.letterbox-1"]}},
    ]
    write(repo, "specs/model-sidecar/vectors/pre.resize.letterbox.yaml", yaml.safe_dump({"cases": cases}))
    row = next(
        line
        for line in st.render_traceability(repo, **HOST).splitlines()
        if line.startswith("| [`pre.resize.letterbox`]") and "cases" in line
    )
    # The unverified `failed` case does not open `vectors`: only the numeric cases count.
    assert row.endswith(
        "2 cases, 1 verified | 1 unknown | 1 of 2 | none |  | open: example, rules |"
    )

    cases[1]["verified_against"] = ["x"]
    cases.append({"id": "c", "verified_against": ["x"], "expect": {"error": "V-pre.resize.letterbox-2"}})
    write(repo, "specs/model-sidecar/vectors/pre.resize.letterbox.yaml", yaml.safe_dump({"cases": cases}))
    write(repo, "specs/model-sidecar/reference/pre_resize_letterbox.py", "")
    inventory = yaml.safe_load((spec / "inventory.yaml").read_text(encoding="utf-8"))
    inventory["no_model"] = {"pre.resize.letterbox": "No | model yet."}
    write(repo, "specs/model-sidecar/inventory.yaml", yaml.safe_dump(inventory))
    row = next(
        line
        for line in st.render_traceability(repo, **HOST).splitlines()
        if line.startswith("| [`pre.resize.letterbox`]") and "cases" in line
    )
    assert row.endswith(
        "3 cases, 3 verified | 1 unknown | 2 of 2 | "
        "[`reference/pre_resize_letterbox.py`](reference/pre_resize_letterbox.py) | "
        "No \\| model yet. | pass |"
    )


def test_the_backlog_counts_the_models_of_each_missing_step(repo: Path) -> None:
    text = st.render_traceability(repo, **HOST)
    assert "4 entries are `missing`." in text
    assert "| [`pre.resize.letterbox`](pre/letterbox.md) | `inverse` | 1 of 3 |" in text
    assert "| [`common.a`](common/a.md) | `validate` | 3 of 3 |" in text


def test_external_implementations_are_listed_when_a_section_has_them(
    repo: Path,
) -> None:
    assert "No section lists an external implementation" in st.render_traceability(repo, **HOST)
    path = repo / "specs/model-sidecar/pre/letterbox.md"
    text = path.read_text(encoding="utf-8").replace(
        "external_impl: []", "external_impl:\n- Some-Exporter: host/pre.py::letterbox"
    )
    path.write_text(text, encoding="utf-8", newline="\n")
    rendered = st.render_traceability(repo, **HOST)
    assert "No section lists an external implementation" not in rendered
    assert (
        "| [`pre.resize.letterbox`](pre/letterbox.md) | Some-Exporter | `host/pre.py::letterbox` |"
        in rendered
    )


def test_write_traceability_writes_lf_and_the_check_sees_it(repo: Path) -> None:
    assert not st.traceability_is_current(repo, **HOST)
    path = st.write_traceability(repo, **HOST)
    assert path == repo / "specs/model-sidecar/TRACEABILITY.md"
    assert b"\r" not in path.read_bytes()
    assert st.traceability_is_current(repo, **HOST)


def test_the_check_ignores_line_endings_and_sees_a_change(repo: Path) -> None:
    path = st.write_traceability(repo, **HOST)
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    assert st.traceability_is_current(repo, **HOST)
    path.write_text(path.read_text(encoding="utf-8") + "extra\n", encoding="utf-8")
    assert not st.traceability_is_current(repo, **HOST)


def test_a_changed_section_file_reaches_the_models_and_exporters(repo: Path) -> None:
    affected = st.affected_sections({"specs/model-sidecar/pre/letterbox.md"}, repo, **HOST)
    assert [a.section.id for a in affected] == ["pre.resize.letterbox"]
    item = affected[0]
    assert item.reasons == ("section file changed: specs/model-sidecar/pre/letterbox.md",)
    assert item.models == ("bar@other-exporter",)
    assert item.exporters == ("Other-Exporter: exports/bar.yaml",)
    assert item.functions == ("pkg/model.py::Resize", "pkg/pre.py::letterbox")
    assert item.tests == ("pkg/test_pre.py",)
    assert item.vectors == ("specs/model-sidecar/vectors/pre.resize.letterbox.yaml",)


def test_a_changed_implementing_file_reaches_the_sections_that_name_it(
    repo: Path,
) -> None:
    affected = st.affected_sections({"pkg/post.py"}, repo, **HOST)
    assert [a.section.id for a in affected] == ["post.object.selection.nms"]
    assert affected[0].reasons == ("implementing file changed: pkg/post.py",)
    assert affected[0].models == ("foo@a-lib", "bar@other-exporter")
    assert affected[0].exporters == ("Other-Exporter: exports/bar.yaml",)


def test_a_changed_vector_file_reaches_its_section(repo: Path) -> None:
    changed = {"specs/model-sidecar/vectors/pre.resize.letterbox.yaml"}
    affected = st.affected_sections(changed, repo, **HOST)
    assert [a.reasons for a in affected] == [
        ("vector file changed: specs/model-sidecar/vectors/pre.resize.letterbox.yaml",)
    ]


def test_reasons_add_up_for_one_section(repo: Path) -> None:
    changed = {"specs/model-sidecar/pre/letterbox.md", "pkg/pre.py", "pkg/model.py"}
    (item,) = st.affected_sections(changed, repo, **HOST)
    assert item.reasons == (
        "section file changed: specs/model-sidecar/pre/letterbox.md",
        "implementing file changed: pkg/model.py",
        "implementing file changed: pkg/pre.py",
    )


def test_an_unrelated_change_reaches_no_section(repo: Path) -> None:
    assert st.affected_sections({"README.md", "pkg/test_pre.py"}, repo, **HOST) == []


def test_the_impact_text_lists_each_section_and_a_summary(repo: Path) -> None:
    changed = ["pkg/post.py", "specs/model-sidecar/pre/letterbox.md"]
    text = st.format_impact("main..HEAD", changed, st.affected_sections(changed, repo, **HOST))
    assert text.startswith(
        "Range: main..HEAD\nChanged files: 2\nAffected sections: 2\n"
    )
    assert "\npre.resize.letterbox\n  reason: section file changed" in text
    assert "  exporters: Other-Exporter: exports/bar.yaml\n" in text
    assert (
        "\nSummary\n  sections (2):\n    post.object.selection.nms\n    pre.resize.letterbox\n"
        in text
    )


def reached(git_repo: Path, git_range: str = "HEAD") -> dict[str, st.AffectedSection]:
    _changed, affected = st.impact(git_range, git_repo, **HOST)
    return {item.section.id: item for item in affected}


@needs_git_program
def test_an_unchanged_repository_reaches_no_section(git_repo: Path) -> None:
    assert st.impact("HEAD", git_repo, **HOST) == ([], [])


@needs_git_program
def test_a_change_of_another_function_of_the_file_reaches_no_section(
    git_repo: Path,
) -> None:
    write(
        git_repo,
        "pkg/pre.py",
        PRE_V1.replace(
            "def other(image):\n    return image", "def other(image):\n    return None"
        ),
    )
    write(
        git_repo,
        "pkg/model.py",
        MODEL_V1.replace("class Other:\n    value = 1", "class Other:\n    value = 2"),
    )
    changed, affected = st.impact("HEAD", git_repo, **HOST)
    assert changed == ["pkg/model.py", "pkg/pre.py"]
    assert affected == []


@needs_git_program
def test_a_changed_function_reaches_only_the_sections_that_name_it(
    git_repo: Path,
) -> None:
    write(
        git_repo,
        "pkg/pre.py",
        PRE_V1.replace(
            "def letterbox(image):\n    return image",
            "def letterbox(image):\n    return image.copy()",
        ),
    )
    reach = reached(git_repo)
    assert list(reach) == ["pre.resize.letterbox"]
    item = reach["pre.resize.letterbox"]
    assert item.reasons == ("implementing function changed: pkg/pre.py::letterbox",)
    assert item.functions == ("pkg/pre.py::letterbox",)
    assert item.models == ("bar@other-exporter",)
    assert item.tests == ("pkg/test_pre.py",)


@needs_git_program
def test_a_class_changes_when_one_of_its_lines_changes(git_repo: Path) -> None:
    write(
        git_repo,
        "pkg/model.py",
        MODEL_V1.replace(
            "class Resize:\n    value = 1", "class Resize:\n    value = 2"
        ),
    )
    reach = reached(git_repo)
    assert list(reach) == ["pre.resize.letterbox"]
    assert reach["pre.resize.letterbox"].functions == ("pkg/model.py::Resize",)


@needs_git_program
def test_two_changed_functions_of_one_section_are_both_named(git_repo: Path) -> None:
    write(
        git_repo,
        "pkg/pre.py",
        PRE_V1.replace(
            "return image\n\n\ndef other", "return image.copy()\n\n\ndef other"
        ),
    )
    write(
        git_repo,
        "pkg/model.py",
        MODEL_V1.replace(
            "class Resize:\n    value = 1", "class Resize:\n    value = 2"
        ),
    )
    item = reached(git_repo)["pre.resize.letterbox"]
    assert item.reasons == (
        "implementing function changed: pkg/model.py::Resize",
        "implementing function changed: pkg/pre.py::letterbox",
    )
    assert item.functions == ("pkg/model.py::Resize", "pkg/pre.py::letterbox")


@needs_git_program
def test_a_function_that_only_moves_has_not_changed(git_repo: Path) -> None:
    write(
        git_repo,
        "pkg/pre.py",
        "import os\n\n\ndef added():\n    return os\n\n\n" + PRE_V1,
    )
    changed, affected = st.impact("HEAD", git_repo, **HOST)
    assert changed == ["pkg/pre.py"]
    assert affected == []


@needs_git_program
def test_a_change_of_line_endings_alone_reaches_no_section(git_repo: Path) -> None:
    (git_repo / "pkg" / "pre.py").write_bytes(PRE_V1.replace("\n", "\r\n").encode())
    assert st.impact("HEAD", git_repo, **HOST)[1] == []


@needs_git_program
def test_a_symbol_that_one_side_lacks_has_changed(git_repo: Path) -> None:
    write(
        git_repo, "pkg/post.py", POST_V1.replace("def decode(", "def decode_renamed(")
    )
    item = reached(git_repo)["post.object.selection.nms"]
    assert item.reasons == ("implementing function changed: pkg/post.py::decode",)


@needs_git_program
@pytest.mark.parametrize("how", ["deleted", "broken"])
def test_a_deleted_or_unreadable_file_changes_in_whole(
    git_repo: Path, how: str
) -> None:
    if how == "deleted":
        (git_repo / "pkg" / "post.py").unlink()
    else:
        write(git_repo, "pkg/post.py", "def decode(:\n")
    item = reached(git_repo)["post.object.selection.nms"]
    assert item.reasons == ("implementing file changed: pkg/post.py",)
    assert item.functions == ("pkg/post.py::decode",)


@needs_git_program
def test_a_section_file_change_lists_every_function_of_the_section(
    git_repo: Path,
) -> None:
    text = (git_repo / "specs/model-sidecar/pre/letterbox.md").read_text(encoding="utf-8")
    write(git_repo, "specs/model-sidecar/pre/letterbox.md", text + "\nMore.\n")
    write(
        git_repo,
        "pkg/pre.py",
        PRE_V1.replace(
            "def letterbox(image):\n    return image",
            "def letterbox(image):\n    return image.copy()",
        ),
    )
    item = reached(git_repo)["pre.resize.letterbox"]
    assert item.reasons == (
        "section file changed: specs/model-sidecar/pre/letterbox.md",
        "implementing function changed: pkg/pre.py::letterbox",
    )
    assert item.functions == ("pkg/model.py::Resize", "pkg/pre.py::letterbox")


@needs_git_program
def test_a_committed_range_reads_both_sides_from_the_commits(git_repo: Path) -> None:
    changed = PRE_V1.replace(
        "def letterbox(image):\n    return image",
        "def letterbox(image):\n    return image.copy()",
    )
    write(git_repo, "pkg/pre.py", changed)
    git(git_repo, "commit", "--quiet", "--all", "--message", "second")
    write(
        git_repo, "pkg/pre.py", changed + "\n\ndef newest():\n    return 1\n"
    )  # not in the range
    assert list(reached(git_repo, "HEAD~1..HEAD")) == ["pre.resize.letterbox"]
    assert reached(git_repo, "HEAD..HEAD") == {}
    write(git_repo, "pkg/pre.py", PRE_V1)  # the working tree equals the first commit
    assert list(reached(git_repo, "HEAD~1..HEAD")) == ["pre.resize.letterbox"]


def test_compare_examples_reports_same_different_and_unavailable(
    repo: Path, tmp_path_factory: Any
) -> None:
    exporters = tmp_path_factory.mktemp("exporters")
    copy = "# a comment\n" + BAR.replace(
        "decode: {selection: nms}", "decode: {selection: nms}  # more\n"
    )
    write(exporters, "Other-Exporter/exports/bar.yaml", copy)
    reports = st.compare_examples(repo, exporters, resolve=resolve_sidecar_composition)
    assert [(r.example, r.status) for r in reports] == [
        ("detectors/keypoint_detectors/baz/body/baz.yaml", "unavailable"),
        ("detectors/object_detectors/bar/bar.yaml", "same"),
    ]
    changed = copy.replace("pad_position: center", "pad_position: top_left")
    write(exporters, "Other-Exporter/exports/bar.yaml", changed)
    _, bar = st.compare_examples(repo, exporters, resolve=resolve_sidecar_composition)
    assert bar.status == "different"
    assert bar.lines == (
        "input.resize.pad_position: 'center' in the example, 'top_left' in the exporter copy",
    )
    assert bar.exporter_file == "Other-Exporter/exports/bar.yaml"


def test_compare_examples_reports_an_exporter_copy_that_is_not_yaml(
    repo: Path, tmp_path_factory: Any
) -> None:
    exporters = tmp_path_factory.mktemp("exporters")
    write(exporters, "Other-Exporter/exports/bar.yaml", "a: [1\n")
    _, bar = st.compare_examples(repo, exporters, resolve=resolve_sidecar_composition)
    assert bar.status == "unavailable"


EXAMPLE_BAR = "specs/model-sidecar/examples/detectors/object_detectors/bar/bar.yaml"


EXAMPLE_POINTS = "specs/model-sidecar/examples/detectors/shared/points.yaml"


POINTS = "- a\n- b\n"


POINTS_SHA256 = hashlib.sha256(POINTS.encode()).hexdigest()


POINTS_REF = f'keypoint:\n  point_names: {{$ref: ../../shared/points.yaml, sha256: "{POINTS_SHA256}"}}\n'


POINTS_INLINE = "keypoint:\n  point_names: [a, b]\n"


def test_compare_examples_resolves_a_fragment_of_the_example(
    repo: Path, tmp_path_factory: Any
) -> None:
    """The example refers to a fragment; the exporter copy lists the same values inline."""
    write(repo, EXAMPLE_POINTS, POINTS)
    write(repo, EXAMPLE_BAR, BAR + POINTS_REF)
    exporters = tmp_path_factory.mktemp("exporters")
    write(exporters, "Other-Exporter/exports/bar.yaml", BAR + POINTS_INLINE)
    _, bar = st.compare_examples(repo, exporters, resolve=resolve_sidecar_composition)
    assert (bar.status, bar.lines, bar.notes) == ("same", (), ())
    write(
        exporters,
        "Other-Exporter/exports/bar.yaml",
        BAR + POINTS_INLINE.replace("b]", "c]"),
    )
    _, bar = st.compare_examples(repo, exporters, resolve=resolve_sidecar_composition)
    assert bar.lines == (
        "keypoint.point_names: ['a', 'b'] in the example, ['a', 'c'] in the exporter copy",
    )


def test_compare_examples_resolves_a_fragment_of_the_exporter_copy(
    repo: Path, tmp_path_factory: Any
) -> None:
    write(repo, EXAMPLE_BAR, BAR + POINTS_INLINE)
    exporters = tmp_path_factory.mktemp("exporters")
    write(exporters, "Other-Exporter/exports/points.yaml", POINTS)
    write(
        exporters,
        "Other-Exporter/exports/bar.yaml",
        BAR + f'keypoint:\n  point_names: {{$ref: points.yaml, sha256: "{POINTS_SHA256}"}}\n',
    )
    _, bar = st.compare_examples(repo, exporters, resolve=resolve_sidecar_composition)
    assert (bar.status, bar.lines, bar.notes) == ("same", (), ())


def test_compare_examples_says_when_the_exporter_copy_does_not_resolve(
    repo: Path, tmp_path_factory: Any
) -> None:
    write(repo, EXAMPLE_BAR, BAR + POINTS_INLINE)
    exporters = tmp_path_factory.mktemp("exporters")
    write(
        exporters,
        "Other-Exporter/exports/bar.yaml",
        BAR + "keypoint:\n  point_names: {$ref: missing.yaml}\n",
    )
    _, bar = st.compare_examples(repo, exporters, resolve=resolve_sidecar_composition)
    assert bar.status == "different"
    assert len(bar.notes) == 1
    assert bar.notes[0].startswith(
        "the exporter copy was compared as written, not resolved: "
    )
    assert "missing.yaml" in bar.notes[0]
    text = st.format_examples([bar])
    assert f"  note: {bar.notes[0]}\n" in text


def test_compare_examples_reports_an_example_that_does_not_resolve(
    repo: Path, tmp_path_factory: Any
) -> None:
    wrong = "0" * 64
    write(repo, EXAMPLE_POINTS, "- a\n- b\n")
    write(
        repo,
        EXAMPLE_BAR,
        BAR
        + f'keypoint:\n  point_names: {{$ref: ../../shared/points.yaml, sha256: "{wrong}"}}\n',
    )
    exporters = tmp_path_factory.mktemp("exporters")
    write(exporters, "Other-Exporter/exports/bar.yaml", BAR + POINTS_INLINE)
    _, bar = st.compare_examples(repo, exporters, resolve=resolve_sidecar_composition)
    assert bar.status == "unavailable"
    assert bar.lines[0].startswith("the example does not resolve: ")
    assert "does not match" in bar.lines[0]


def test_compare_examples_changes_no_file(repo: Path, tmp_path_factory: Any) -> None:
    exporters = tmp_path_factory.mktemp("exporters")
    write(exporters, "Other-Exporter/exports/bar.yaml", BAR)

    def snapshot() -> dict[str, bytes]:
        return {
            p.relative_to(root).as_posix(): p.read_bytes()
            for root in (repo, exporters)
            for p in sorted(root.rglob("*"))
            if p.is_file()
        }

    before = snapshot()
    st.compare_examples(repo, exporters, resolve=resolve_sidecar_composition)
    assert snapshot() == before


def test_the_examples_text_has_a_summary_line(
    repo: Path, tmp_path_factory: Any
) -> None:
    exporters = tmp_path_factory.mktemp("exporters")
    write(exporters, "Other-Exporter/exports/bar.yaml", BAR)
    text = st.format_examples(st.compare_examples(repo, exporters, resolve=resolve_sidecar_composition))
    assert (
        "detectors/object_detectors/bar/bar.yaml: same\n  exporter copy: Other-Exporter/exports/bar.yaml\n"
        in text
    )
    assert text.endswith("2 examples: 1 same, 0 different, 1 unavailable\n")


@needs_git
def test_main_impact_for_an_empty_range(capsys: pytest.CaptureFixture[str]) -> None:
    assert stp.main(["impact", "HEAD..HEAD"]) == 0
    assert "No section is affected." in capsys.readouterr().out


@needs_git
def test_main_impact_for_a_bad_range(capsys: pytest.CaptureFixture[str]) -> None:
    assert stp.main(["impact", "no-such-revision-0123456789"]) == 1
    assert capsys.readouterr().err.startswith("error: ")


def test_main_examples_needs_a_folder(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert stp.main(["examples", "--exporters-root", str(tmp_path / "absent")]) == 2
    assert "not a folder" in capsys.readouterr().err


def test_main_examples_prints_one_entry_for_each_example(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert stp.main(["examples", "--exporters-root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert out.count(": unavailable\n") == len(st.load_inventory()["examples"])
    assert not list(tmp_path.iterdir())


def test_main_needs_a_command(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        stp.main([])
    assert exc.value.code == 2


def test_the_package_entry_point_gives_the_package_resolver_and_root() -> None:
    assert stp.HOST["resolve"] is resolve_sidecar_composition
    assert stp.HOST["package_root"] == st.REPO_ROOT / "skellytracker" / "core" / "model_zoo"
    assert (stp.HOST["package_root"] / "detectors").is_dir()


def test_the_scan_without_a_package_root_reads_only_the_examples(repo: Path) -> None:
    write(repo, PACKAGE_BAZ, BAZ + "\n")  # other bytes than the example: an error of a package scan
    with pytest.raises(st.TraceError):
        st.scan_sidecars(repo, **HOST)
    scan = st.scan_sidecars(repo, resolve=resolve_sidecar_composition)
    assert {s.origin for s in scan.sidecars} == {"example"}
    assert not any(p.startswith("skellytracker/") for p in [s.path for s in scan.sidecars] + list(scan.skipped))


def test_the_scan_takes_an_absolute_package_root_outside_the_repository(repo: Path, tmp_path_factory: Any) -> None:
    package = tmp_path_factory.mktemp("package")
    only = "detectors/keypoint_detectors/qux/body/qux.yaml"
    write(package, only, BAZ.replace("model_id: baz", "model_id: qux"))
    scan = st.scan_sidecars(repo, resolve=resolve_sidecar_composition, package_root=package)
    qux = next(s for s in scan.sidecars if s.key == "qux@declared-lib")
    assert (qux.origin, qux.path) == ("package", (package / only).as_posix())

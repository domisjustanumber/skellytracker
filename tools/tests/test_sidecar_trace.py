"""The functions of `tools/sidecar_trace.py`, on small repositories made for each test."""

from __future__ import annotations

import ast
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

import sidecar_trace as st

TRACE_PATH = Path(st.__file__)

# --------------------------------------------------------------------------------------------
# A small repository
# --------------------------------------------------------------------------------------------

README = """\
# Spec

| Section ID | File | Title |
|------------|------|-------|
| `common.a` | [common/a.md](common/a.md) | Common A |
| `pre.resize.letterbox` | [pre/letterbox.md](pre/letterbox.md) | Letterbox |
| `post.det.selection.nms` | [post/nms.md](post/nms.md) | Selection: NMS |
"""

FOO = """\
schema_version: v2024.09.1019
model_id: foo
role: [object_detector]
input:
  normalization: none
  resize: {method: letterbox, preserve_aspect_ratio: false}
decode: {requires_nms: true}
"""

BAR = """\
schema_version: vNEXT
model_id: bar
role: [object_detector]
input:
  normalization: unit_float
  resize: {method: letterbox, pad_position: center, rounding: half_even}
decode: {selection: nms}
"""

BAZ = """\
schema_version: vNEXT
model_id: baz
source: {name: declared-lib, version: "1.0"}
role: [pose_estimator]
input: {resize: {method: fit}}
"""


def front_matter(
    section_id: str,
    kind: str,
    selectors: list[str],
    implemented_by: dict[str, str] | None = None,
    tests: list[str] | None = None,
    vectors: str | None = None,
) -> str:
    steps = implemented_by or {"validate": "missing", "load": "missing"}
    front: dict[str, Any] = {
        "id": section_id,
        "title": section_id,
        "kind": kind,
        "since": "vNEXT",
        "changed_in": [],
        "selectors": selectors,
        "implemented_by": steps,
        "external_impl": [],
        "tests": tests or [],
        "vectors": vectors,
        "status": {"spec": "stable", **dict.fromkeys(steps, "missing")},
    }
    return "---\n" + yaml.safe_dump(front, sort_keys=False) + "---\n\n# Title\n"


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    spec = "specs/model-sidecar/"
    write(tmp_path, spec + "README.md", README)
    write(tmp_path, spec + "common/a.md", front_matter("common.a", "common", []))
    write(
        tmp_path,
        spec + "pre/letterbox.md",
        front_matter(
            "pre.resize.letterbox",
            "preprocessor",
            ["input.resize.method=letterbox"],
            {
                "validate": "pkg/model.py::Resize",
                "forward": "pkg/pre.py::letterbox",
                "inverse": "missing",
            },
            tests=["pkg/test_pre.py"],
            vectors="vectors/pre.resize.letterbox.yaml",
        ),
    )
    write(
        tmp_path,
        spec + "post/nms.md",
        front_matter(
            "post.det.selection.nms",
            "postprocessor",
            ["decode.selection=nms"],
            {"validate": "missing", "decode": "pkg/post.py::decode"},
        ),
    )
    write(
        tmp_path,
        spec + "inventory.yaml",
        yaml.safe_dump(
            {
                "examples": {
                    "detectors/object_detectors/bar/bar.yaml": {
                        "source": "other-exporter",
                        "exporter": "Other-Exporter",
                        "exporter_path": "exports/bar.yaml",
                    },
                    "detectors/keypoint_detectors/baz/body/baz.yaml": {
                        "source": "ignored-exporter",
                        "exporter": "Ignored-Exporter",
                        "exporter_path": "exports/baz.yaml",
                    },
                },
                "proposed": [
                    {
                        "key": "zed@x-exporter",
                        "exporter": "X",
                        "plan": "X/p.md",
                        "status": "proposed",
                        "notes": "n",
                    },
                    {
                        "key": "alpha@x-exporter",
                        "exporter": "X",
                        "plan": "X/p.md",
                        "status": "proposed",
                        "notes": "m",
                    },
                ],
            },
            sort_keys=False,
        ),
    )
    write(tmp_path, "skellytracker/core/detectors/object_detectors/foo/foo.yaml", FOO)
    write(tmp_path, "skellytracker/core/detectors/object_detectors/foo/other.yaml", FOO)
    write(
        tmp_path,
        "skellytracker/core/detectors/shared/skeletons/frag.yaml",
        "- a\n- b\n",
    )
    write(tmp_path, "skellytracker/core/detectors/shared/empty.yaml", "")
    write(tmp_path, spec + "examples/detectors/object_detectors/bar/bar.yaml", BAR)
    write(
        tmp_path, spec + "examples/detectors/keypoint_detectors/baz/body/baz.yaml", BAZ
    )
    return tmp_path


# --------------------------------------------------------------------------------------------
# Front matter and references
# --------------------------------------------------------------------------------------------


def test_front_matter_is_the_text_between_the_first_two_rules() -> None:
    front, body = st.parse_front_matter(
        "---\nid: a\nlist: [1, 2]\n---\n\n# Title\n\n---\nx: 1\n"
    )
    assert front == {"id": "a", "list": [1, 2]}
    assert body == "\n# Title\n\n---\nx: 1\n"


def test_front_matter_reads_a_file_with_crlf_line_endings() -> None:
    front, body = st.parse_front_matter("---\r\nid: a\r\n---\r\n# Title\r\n")
    assert front == {"id": "a"}
    assert body == "# Title\r\n"


@pytest.mark.parametrize(
    "text",
    [
        "# Title\n",
        "---\nid: a\n",
        "---\n- a\n- b\n---\n",
        "---\nid: [a\n---\n",
        "---\n---\n",
    ],
)
def test_bad_front_matter_raises(text: str) -> None:
    with pytest.raises(st.TraceError):
        st.parse_front_matter(text, "file.md")


def test_split_reference() -> None:
    assert st.split_reference("missing") is None
    assert st.split_reference("a/b.py::Class.method") == ("a/b.py", "Class.method")


@pytest.mark.parametrize(
    "value", ["a/b.py", "a/b.py::", "::name", "a.py::b::c", "Missing", ""]
)
def test_a_bad_reference_raises(value: str) -> None:
    with pytest.raises(st.TraceError):
        st.split_reference(value)


SOURCE = """
import os

CONSTANT = 1

def function(): ...

async def coroutine(): ...

class Thing:
    def method(self): ...

    @property
    def prop(self): ...

    class Inner:
        def deep(self): ...

    attribute = 1

if os.name:
    def conditional(): ...
"""


@pytest.mark.parametrize(
    "symbol",
    ["function", "coroutine", "Thing", "Thing.method", "Thing.prop"],
)
def test_find_symbol_finds_functions_classes_and_methods(symbol: str) -> None:
    assert st.find_symbol(SOURCE, symbol)


@pytest.mark.parametrize(
    "symbol",
    [
        "CONSTANT",
        "os",
        "Thing.attribute",
        "Thing.Inner",
        "Thing.Inner.deep",
        "Thing.missing",
        "method",
        "function.inner",
        "missing",
        "conditional",
        "",
    ],
)
def test_find_symbol_rejects_anything_else(symbol: str) -> None:
    assert not st.find_symbol(SOURCE, symbol)


def test_symbol_text_gives_the_lines_of_a_symbol_and_its_decorators() -> None:
    assert st.symbol_text(SOURCE, "function") == "def function(): ..."
    assert (
        st.symbol_text(SOURCE, "Thing.prop") == "    @property\n    def prop(self): ..."
    )
    thing = st.symbol_text(SOURCE, "Thing")
    assert thing is not None
    assert thing.startswith("class Thing:\n    def method(self): ...")
    assert thing.endswith("    attribute = 1")


@pytest.mark.parametrize("symbol", ["CONSTANT", "Thing.missing", "missing", ""])
def test_symbol_text_is_none_for_a_symbol_that_the_module_lacks(symbol: str) -> None:
    assert st.symbol_text(SOURCE, symbol) is None


def test_symbol_text_ignores_line_endings_trailing_blanks_and_the_place() -> None:
    moved = "import sys\n\n\n" + SOURCE.replace(
        "def function(): ...", "def function(): ...  "
    )
    for variant in (moved, moved.replace("\n", "\r\n"), moved.replace("\n", "\r")):
        for symbol in ("function", "Thing", "Thing.prop"):
            assert st.symbol_text(variant, symbol) == st.symbol_text(SOURCE, symbol)


def test_symbol_text_sees_a_change_of_a_body_or_a_decorator() -> None:
    changed = SOURCE.replace("def method(self): ...", "def method(self): return 1")
    assert st.symbol_text(changed, "Thing.method") != st.symbol_text(
        SOURCE, "Thing.method"
    )
    assert st.symbol_text(changed, "Thing") != st.symbol_text(SOURCE, "Thing")
    assert st.symbol_text(changed, "function") == st.symbol_text(SOURCE, "function")
    undecorated = SOURCE.replace("    @property\n", "")
    assert st.symbol_text(undecorated, "Thing.prop") != st.symbol_text(
        SOURCE, "Thing.prop"
    )


# --------------------------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------------------------


def test_the_section_map_lists_the_rows_in_order(repo: Path) -> None:
    rows = st.readme_section_map(repo)
    assert [(r.id, r.file, r.title) for r in rows] == [
        ("common.a", "common/a.md", "Common A"),
        ("pre.resize.letterbox", "pre/letterbox.md", "Letterbox"),
        ("post.det.selection.nms", "post/nms.md", "Selection: NMS"),
    ]


def test_sections_come_in_the_order_of_the_map(repo: Path) -> None:
    assert [s.id for s in st.load_sections(repo)] == [
        "common.a",
        "pre.resize.letterbox",
        "post.det.selection.nms",
    ]


def test_a_section_that_the_map_omits_comes_last(repo: Path) -> None:
    write(
        repo,
        "specs/model-sidecar/pre/another.md",
        front_matter("pre.another", "preprocessor", ["x"]),
    )
    assert [s.id for s in st.load_sections(repo)][-1] == "pre.another"


def test_a_repeated_section_id_raises(repo: Path) -> None:
    write(repo, "specs/model-sidecar/pre/copy.md", front_matter("common.a", "common", []))
    with pytest.raises(st.TraceError, match="common.a"):
        st.load_sections(repo)


def test_section_properties(repo: Path) -> None:
    section = {s.id: s for s in st.load_sections(repo)}["pre.resize.letterbox"]
    assert section.path == "pre/letterbox.md"
    assert section.kind == "preprocessor"
    assert section.tests == ["pkg/test_pre.py"]
    assert section.vectors == "vectors/pre.resize.letterbox.yaml"
    assert section.implemented_by["inverse"] == "missing"
    assert section.status["spec"] == "stable"
    assert section.body.strip() == "# Title"


def test_missing_entries_list_the_missing_steps(repo: Path) -> None:
    entries = st.missing_entries(st.load_sections(repo))
    assert [(s.id, step) for s, step in entries] == [
        ("common.a", "validate"),
        ("common.a", "load"),
        ("pre.resize.letterbox", "inverse"),
        ("post.det.selection.nms", "validate"),
    ]


# --------------------------------------------------------------------------------------------
# The scan
# --------------------------------------------------------------------------------------------


def test_the_scan_finds_the_sidecars_and_skips_the_other_yaml(repo: Path) -> None:
    scan = st.scan_sidecars(repo)
    assert [s.key for s in scan.sidecars] == [
        "foo@skellytracker",
        "baz@declared-lib",
        "bar@other-exporter",
    ]
    assert scan.skipped == (
        "skellytracker/core/detectors/object_detectors/foo/other.yaml",
        "skellytracker/core/detectors/shared/empty.yaml",
        "skellytracker/core/detectors/shared/skeletons/frag.yaml",
    )


def test_a_declared_source_wins_over_the_inventory(repo: Path) -> None:
    keys = {s.key: s for s in st.scan_sidecars(repo).sidecars}
    assert keys["baz@declared-lib"].source == "declared-lib"
    assert keys["bar@other-exporter"].source == "other-exporter"
    assert keys["foo@skellytracker"].origin == "package"
    assert keys["bar@other-exporter"].origin == "example"


def test_an_example_without_any_source_raises(repo: Path) -> None:
    write(repo, "specs/model-sidecar/inventory.yaml", "examples: {}\nproposed: []\n")
    with pytest.raises(st.TraceError, match="source"):
        st.scan_sidecars(repo)


def test_a_repeated_key_raises(repo: Path) -> None:
    write(
        repo,
        "skellytracker/core/detectors/object_detectors/copy/foo.yaml",
        FOO,
    )
    with pytest.raises(st.TraceError, match="foo@skellytracker"):
        st.scan_sidecars(repo)


def test_a_yaml_error_raises(repo: Path) -> None:
    write(repo, "skellytracker/core/detectors/shared/bad.yaml", "a: [1\n")
    with pytest.raises(st.TraceError, match="bad.yaml"):
        st.scan_sidecars(repo)


def test_a_sidecar_that_cannot_resolve_raises(repo: Path) -> None:
    broken = (
        FOO.replace("model_id: foo", "model_id: broken")
        + "extra: {$ref: missing.yaml}\n"
    )
    write(
        repo, "skellytracker/core/detectors/object_detectors/broken/broken.yaml", broken
    )
    with pytest.raises(st.TraceError, match="broken.yaml"):
        st.scan_sidecars(repo)


def test_the_scan_normalizes_each_sidecar(repo: Path) -> None:
    foo = next(s for s in st.scan_sidecars(repo).sidecars if s.model_id == "foo")
    assert foo.legacy
    assert foo.normalized["decode"]["selection"] == "nms"
    assert foo.normalized["input"]["resize"]["method"] == "stretch"
    assert foo.resolved["decode"] == {"requires_nms": True}
    assert foo.derived == ("selection", "letterbox_alias")


def test_proposed_models_are_sorted_by_key(repo: Path) -> None:
    assert [e["key"] for e in st.proposed_models(repo)] == [
        "alpha@x-exporter",
        "zed@x-exporter",
    ]


def test_the_sections_apply_to_the_right_sidecars(repo: Path) -> None:
    sections = st.load_sections(repo)
    sidecars = st.scan_sidecars(repo).sidecars
    applicable = st.applicable_models(sections, sidecars)
    assert [s.key for s in applicable["common.a"]] == [s.key for s in sidecars]
    assert [s.key for s in applicable["pre.resize.letterbox"]] == ["bar@other-exporter"]
    assert [s.key for s in applicable["post.det.selection.nms"]] == [
        "foo@skellytracker",
        "bar@other-exporter",
    ]


# --------------------------------------------------------------------------------------------
# TRACEABILITY.md
# --------------------------------------------------------------------------------------------


def test_the_text_has_the_note_and_the_five_parts(repo: Path) -> None:
    text = st.render_traceability(repo)
    assert st.NOTE in text
    assert "tools/sidecar_trace.py matrix" in text
    for heading in (
        "## Models and sections",
        "## Implementation status",
        "## External implementations",
        "## Proposed models",
        "## Backlog",
    ):
        assert heading in text


def test_the_text_is_deterministic_and_has_lf_endings(repo: Path) -> None:
    text = st.render_traceability(repo)
    assert text == st.render_traceability(repo)
    assert "\r" not in text
    assert text.endswith("\n") and not text.endswith("\n\n")


def test_the_matrix_rows_and_cells(repo: Path) -> None:
    lines = st.render_traceability(repo).splitlines()
    header = next(line for line in lines if line.startswith("| Section | foo<br>"))
    assert header == (
        "| Section | foo<br>@skellytracker | baz<br>@declared-lib | bar<br>@other-exporter |"
    )
    row = next(line for line in lines if line.startswith("| [`common.a`]"))
    assert row == "| [`common.a`](common/a.md) | x | x | x |"
    row = next(line for line in lines if line.startswith("| [`pre.resize.letterbox`]"))
    assert row == "| [`pre.resize.letterbox`](pre/letterbox.md) |  |  | x |"
    row = next(
        line for line in lines if line.startswith("| [`post.det.selection.nms`]")
    )
    assert row == (
        "| [`post.det.selection.nms`](post/nms.md) | nms (legacy, derived) |  | nms |"
    )


def test_the_normalization_row_shows_the_mode_and_the_legacy_flag() -> None:
    legacy = _fake_sidecar("imagenet_bgr", "v2024.09.1019", derived=())
    current = _fake_sidecar("imagenet_bgr", "vNEXT", derived=())
    derived = _fake_sidecar("imagenet_bgr", "vNEXT", derived=("normalization",))
    custom = _fake_sidecar({"mode": "custom"}, "vNEXT", derived=())
    assert st._normalization_label(legacy) == "imagenet_bgr (legacy)"
    assert st._normalization_label(current) == "imagenet_bgr"
    assert st._normalization_label(derived) == "imagenet_bgr (derived)"
    assert st._normalization_label(custom) == "custom"
    assert st._normalization_label(_fake_sidecar("none", "v2024.09.1019", ())) == "none"


def _fake_sidecar(
    normalization: Any, version: str, derived: tuple[str, ...]
) -> st.Sidecar:
    return st.Sidecar(
        key="m@s",
        model_id="m",
        source="s",
        origin="package",
        path="p.yaml",
        schema_version=version,
        resolved={},
        normalized={
            "input": {"normalization": normalization},
            "decode": {"selection": "none"},
        },
        derived=derived,
    )


def test_the_bottom_up_row_shows_packed_keypoints_and_poses_outputs() -> None:
    def sidecar(outputs: list[dict[str, Any]]) -> st.Sidecar:
        fake = _fake_sidecar("none", "vNEXT", ())
        return st.Sidecar(**{**fake.__dict__, "normalized": {"outputs": outputs}})

    packed = sidecar([{"semantic": "detections", "packed_keypoints": {"offset": 6}}])
    poses = sidecar([{"semantic": "detections"}, {"semantic": "poses"}])
    both = sidecar([{"semantic": "poses", "packed_keypoints": {"offset": 6}}])
    neither = sidecar([{"semantic": "detections", "packed_keypoints": None}])
    assert st._bottom_up_label(packed) == "x (packed)"
    assert st._bottom_up_label(poses) == "x (poses)"
    assert st._bottom_up_label(both) == "x (packed, poses)"
    assert st._bottom_up_label(neither) == "x"


def test_the_selection_row_shows_the_selection_and_marks_a_derived_one() -> None:
    assert st._selection_label(_fake_sidecar("none", "vNEXT", ())) == "none"
    derived = _fake_sidecar("none", "v2024.09.1019", ("selection",))
    assert st._selection_label(derived) == "none (legacy, derived)"


def test_the_statuses_functions_tests_and_vectors_are_listed(repo: Path) -> None:
    text = st.render_traceability(repo)
    assert (
        "| [`pre.resize.letterbox`](pre/letterbox.md) | stable | "
        "`validate` missing: `pkg/model.py::Resize`<br>"
        "`forward` missing: `pkg/pre.py::letterbox`<br>"
        "`inverse` missing | `pkg/test_pre.py` | "
        "[`vectors/pre.resize.letterbox.yaml`](vectors/pre.resize.letterbox.yaml) |"
    ) in text


def test_the_proposed_models_are_listed_and_not_matched(repo: Path) -> None:
    text = st.render_traceability(repo)
    assert text.index("`alpha@x-exporter`") < text.index("`zed@x-exporter`")
    assert "alpha@x-exporter<br>" not in text


def test_the_backlog_counts_the_models_of_each_missing_step(repo: Path) -> None:
    text = st.render_traceability(repo)
    assert "4 entries are `missing`." in text
    assert "| [`pre.resize.letterbox`](pre/letterbox.md) | `inverse` | 1 of 3 |" in text
    assert "| [`common.a`](common/a.md) | `validate` | 3 of 3 |" in text


def test_external_implementations_are_listed_when_a_section_has_them(
    repo: Path,
) -> None:
    assert "No section lists an external implementation" in st.render_traceability(repo)
    path = repo / "specs/model-sidecar/pre/letterbox.md"
    text = path.read_text(encoding="utf-8").replace(
        "external_impl: []", "external_impl:\n- Some-Exporter: host/pre.py::letterbox"
    )
    path.write_text(text, encoding="utf-8", newline="\n")
    rendered = st.render_traceability(repo)
    assert "No section lists an external implementation" not in rendered
    assert (
        "| [`pre.resize.letterbox`](pre/letterbox.md) | Some-Exporter | `host/pre.py::letterbox` |"
        in rendered
    )


def test_write_traceability_writes_lf_and_the_check_sees_it(repo: Path) -> None:
    assert not st.traceability_is_current(repo)
    path = st.write_traceability(repo)
    assert path == repo / "specs/model-sidecar/TRACEABILITY.md"
    assert b"\r" not in path.read_bytes()
    assert st.traceability_is_current(repo)


def test_the_check_ignores_line_endings_and_sees_a_change(repo: Path) -> None:
    path = st.write_traceability(repo)
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    assert st.traceability_is_current(repo)
    path.write_text(path.read_text(encoding="utf-8") + "extra\n", encoding="utf-8")
    assert not st.traceability_is_current(repo)


# --------------------------------------------------------------------------------------------
# impact
# --------------------------------------------------------------------------------------------


def test_a_changed_section_file_reaches_the_models_and_exporters(repo: Path) -> None:
    affected = st.affected_sections({"specs/model-sidecar/pre/letterbox.md"}, repo)
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
    affected = st.affected_sections({"pkg/post.py"}, repo)
    assert [a.section.id for a in affected] == ["post.det.selection.nms"]
    assert affected[0].reasons == ("implementing file changed: pkg/post.py",)
    assert affected[0].models == ("foo@skellytracker", "bar@other-exporter")
    assert affected[0].exporters == ("Other-Exporter: exports/bar.yaml",)


def test_a_changed_vector_file_reaches_its_section(repo: Path) -> None:
    changed = {"specs/model-sidecar/vectors/pre.resize.letterbox.yaml"}
    affected = st.affected_sections(changed, repo)
    assert [a.reasons for a in affected] == [
        ("vector file changed: specs/model-sidecar/vectors/pre.resize.letterbox.yaml",)
    ]


def test_reasons_add_up_for_one_section(repo: Path) -> None:
    changed = {"specs/model-sidecar/pre/letterbox.md", "pkg/pre.py", "pkg/model.py"}
    (item,) = st.affected_sections(changed, repo)
    assert item.reasons == (
        "section file changed: specs/model-sidecar/pre/letterbox.md",
        "implementing file changed: pkg/model.py",
        "implementing file changed: pkg/pre.py",
    )


def test_an_unrelated_change_reaches_no_section(repo: Path) -> None:
    assert st.affected_sections({"README.md", "pkg/test_pre.py"}, repo) == []


def test_the_impact_text_lists_each_section_and_a_summary(repo: Path) -> None:
    changed = ["pkg/post.py", "specs/model-sidecar/pre/letterbox.md"]
    text = st.format_impact("main..HEAD", changed, st.affected_sections(changed, repo))
    assert text.startswith(
        "Range: main..HEAD\nChanged files: 2\nAffected sections: 2\n"
    )
    assert "\npre.resize.letterbox\n  reason: section file changed" in text
    assert "  exporters: Other-Exporter: exports/bar.yaml\n" in text
    assert (
        "\nSummary\n  sections (2):\n    post.det.selection.nms\n    pre.resize.letterbox\n"
        in text
    )


def test_the_impact_text_says_so_when_nothing_is_affected() -> None:
    text = st.format_impact("a..b", ["x.py"], [])
    assert text == "Range: a..b\nChanged files: 1\nNo section is affected.\n"


needs_git = pytest.mark.skipif(
    shutil.which("git") is None or not (st.REPO_ROOT / ".git").exists(),
    reason="git is not installed, or the repository has no .git",
)


@needs_git
def test_an_empty_git_range_lists_no_file() -> None:
    assert st.changed_files("HEAD..HEAD") == []


@needs_git
@pytest.mark.parametrize("git_range", ["", "--stat", "no-such-revision-0123456789"])
def test_a_bad_git_range_raises(git_range: str) -> None:
    with pytest.raises(st.TraceError):
        st.changed_files(git_range)


# The functions of a git repository that the test makes. The repository uses the files of
# the `repo` fixture, and the sections of that fixture name the functions of three modules.

needs_git_program = pytest.mark.skipif(
    shutil.which("git") is None, reason="git is not installed"
)

MODEL_V1 = "class Resize:\n    value = 1\n\n\nclass Other:\n    value = 1\n"
PRE_V1 = (
    "def letterbox(image):\n    return image\n\n\ndef other(image):\n    return image\n"
)
POST_V1 = "def decode(rows):\n    return rows\n\n\ndef helper(rows):\n    return rows\n"


def git(root: Path, *arguments: str) -> None:
    program = shutil.which("git")
    assert program is not None
    subprocess.run(  # noqa: S603
        [
            program,
            "-C",
            str(root),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.autocrlf=false",
            *arguments,
        ],
        check=True,
        capture_output=True,
    )


@pytest.fixture
def git_repo(repo: Path) -> Path:
    write(repo, "pkg/model.py", MODEL_V1)
    write(repo, "pkg/pre.py", PRE_V1)
    write(repo, "pkg/post.py", POST_V1)
    git(repo, "init", "--quiet")
    git(repo, "add", "--all")
    git(repo, "commit", "--quiet", "--message", "first")
    return repo


def reached(git_repo: Path, git_range: str = "HEAD") -> dict[str, st.AffectedSection]:
    _changed, affected = st.impact(git_range, git_repo)
    return {item.section.id: item for item in affected}


@needs_git_program
def test_diff_entries_give_the_status_and_the_blobs(git_repo: Path) -> None:
    write(git_repo, "pkg/pre.py", PRE_V1 + "\n# more\n")
    write(git_repo, "pkg/new.py", "x = 1\n")
    git(git_repo, "add", "pkg/new.py")
    (git_repo / "pkg" / "post.py").unlink()
    entries = {entry.path: entry for entry in st.diff_entries("HEAD", git_repo)}
    assert sorted(entries) == ["pkg/new.py", "pkg/post.py", "pkg/pre.py"]
    assert [entries[name].status for name in sorted(entries)] == ["A", "D", "M"]
    assert entries["pkg/pre.py"].old_blob
    assert entries["pkg/new.py"].old_blob is None
    assert entries["pkg/post.py"].old_blob and entries["pkg/post.py"].new_blob is None
    assert st.changed_files("HEAD", git_repo) == sorted(entries)


@needs_git_program
def test_an_unchanged_repository_reaches_no_section(git_repo: Path) -> None:
    assert st.impact("HEAD", git_repo) == ([], [])


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
    changed, affected = st.impact("HEAD", git_repo)
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
    changed, affected = st.impact("HEAD", git_repo)
    assert changed == ["pkg/pre.py"]
    assert affected == []


@needs_git_program
def test_a_change_of_line_endings_alone_reaches_no_section(git_repo: Path) -> None:
    (git_repo / "pkg" / "pre.py").write_bytes(PRE_V1.replace("\n", "\r\n").encode())
    assert st.impact("HEAD", git_repo)[1] == []


@needs_git_program
def test_a_symbol_that_one_side_lacks_has_changed(git_repo: Path) -> None:
    write(
        git_repo, "pkg/post.py", POST_V1.replace("def decode(", "def decode_renamed(")
    )
    item = reached(git_repo)["post.det.selection.nms"]
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
    item = reached(git_repo)["post.det.selection.nms"]
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


# --------------------------------------------------------------------------------------------
# examples
# --------------------------------------------------------------------------------------------


def test_diff_yaml_of_equal_values_is_empty() -> None:
    value = {"a": [1, 2, {"b": None}], "c": {"d": "x"}, "e": 1.5}
    assert (
        st.diff_yaml(value, {"c": {"d": "x"}, "e": 1.5, "a": [1, 2, {"b": None}]}) == []
    )


def test_diff_yaml_names_the_keys_that_differ() -> None:
    ours = {"a": 1, "b": {"c": [1, 2, 3], "d": "x"}, "only_ours": True}
    theirs = {"a": 2, "b": {"c": [1, 2, 4], "d": "x"}, "only_theirs": True}
    assert st.diff_yaml(ours, theirs) == [
        "a: 1 in the example, 2 in the exporter copy",
        "b.c: [1, 2, 3] in the example, [1, 2, 4] in the exporter copy",
        "only_ours: only in the example",
        "only_theirs: only in the exporter copy",
    ]


def test_diff_yaml_walks_lists_of_mappings() -> None:
    ours = {"outputs": [{"name": "a", "rank": 3}, {"name": "b"}]}
    theirs = {"outputs": [{"name": "a", "rank": 4}, {"name": "b"}]}
    assert st.diff_yaml(ours, theirs) == [
        "outputs[0].rank: 3 in the example, 4 in the exporter copy"
    ]


def test_diff_yaml_walks_lists_of_mappings_that_have_no_names_by_index() -> None:
    ours = {"x": [{"id": 1}, {"id": 2}]}
    assert st.diff_yaml(ours, {"x": [{"id": 1}, {"id": 3}]}) == [
        "x[1].id: 2 in the example, 3 in the exporter copy"
    ]
    assert st.diff_yaml({"x": [{"id": 1}]}, {"x": [{"id": 1}, {"id": 2}]}) == [
        "x[1:]: extra items in the exporter copy: 1"
    ]
    twins = {"x": [{"name": "a", "v": 1}, {"name": "a", "v": 2}]}
    assert st.diff_yaml(
        twins, {"x": [{"name": "a", "v": 1}, {"name": "a", "v": 3}]}
    ) == ["x[1].v: 2 in the example, 3 in the exporter copy"]


def test_diff_yaml_matches_mappings_by_name_when_the_names_differ() -> None:
    ours = {"c": [{"name": "a", "x": 1}, {"name": "b"}]}
    theirs = {"c": [{"name": "b"}, {"name": "z"}, {"name": "a", "x": 2}]}
    assert st.diff_yaml(ours, theirs) == [
        "c[a].x: 1 in the example, 2 in the exporter copy",
        "c[z]: only in the exporter copy",
    ]
    only_ours = {"c": [{"name": "k"}, {"name": "a", "x": 1}]}
    assert st.diff_yaml(only_ours, {"c": [{"name": "a", "x": 1}]}) == [
        "c[k]: only in the example"
    ]


def test_diff_yaml_reports_names_in_a_different_order() -> None:
    ours = {"c": [{"name": "a"}, {"name": "b"}]}
    theirs = {"c": [{"name": "b"}, {"name": "a"}]}
    assert st.diff_yaml(ours, theirs) == ["c: the same names in a different order"]


def test_diff_yaml_counts_the_items_that_a_long_list_has_on_one_side() -> None:
    ours = {"p": [f"n{i}" for i in range(10)]}
    theirs = {"p": [f"n{i}" for i in range(2, 12)]}
    assert st.diff_yaml(ours, theirs) == [
        "p: 2 only in the example: 'n0', 'n1'; 2 only in the exporter copy: 'n10', 'n11'"
    ]
    many = {"p": [f"m{i}" for i in range(10)]}
    (line,) = st.diff_yaml(ours, many)
    assert line.startswith("p: 10 only in the example: 'n0', 'n1', 'n2', ...; 10 only")


def test_diff_yaml_reports_a_long_list_in_a_different_order() -> None:
    names = [f"n{i}" for i in range(10)]
    assert st.diff_yaml({"p": names}, {"p": names[::-1]}) == [
        "p: the same 10 items in a different order"
    ]
    assert st.diff_yaml({"p": names}, {"p": list(names)}) == []


def test_diff_yaml_compares_long_lists_of_pairs() -> None:
    ours = {"edges": [[f"p{i}", f"p{i + 1}"] for i in range(10)]}
    theirs = {"edges": [*ours["edges"][:-1], ["p9", "q"]]}
    assert st.diff_yaml(ours, theirs) == [
        "edges: 1 only in the example: ['p9', 'p10']; 1 only in the exporter copy: ['p9', 'q']"
    ]


def test_diff_yaml_tells_apart_a_bool_an_int_and_a_float() -> None:
    assert st.diff_yaml({"a": True}, {"a": 1})
    assert st.diff_yaml({"a": 1}, {"a": 1.0})
    assert st.diff_yaml({"a": [1, True]}, {"a": [1, 1]})
    assert not st.diff_yaml({"a": [1, True]}, {"a": [1, True]})


def test_diff_yaml_shortens_long_values() -> None:
    (line,) = st.diff_yaml({"a": "x" * 200}, {"a": "y"})
    assert len(line) < 100 and "..." in line


def test_the_top_level_can_differ() -> None:
    assert st.diff_yaml([1], {"a": 1}) == [
        "<top level>: [1] in the example, {'a': 1} in the exporter copy"
    ]


def test_compare_examples_reports_same_different_and_unavailable(
    repo: Path, tmp_path_factory: Any
) -> None:
    exporters = tmp_path_factory.mktemp("exporters")
    copy = "# a comment\n" + BAR.replace(
        "decode: {selection: nms}", "decode: {selection: nms}  # more\n"
    )
    write(exporters, "Other-Exporter/exports/bar.yaml", copy)
    reports = st.compare_examples(repo, exporters)
    assert [(r.example, r.status) for r in reports] == [
        ("detectors/keypoint_detectors/baz/body/baz.yaml", "unavailable"),
        ("detectors/object_detectors/bar/bar.yaml", "same"),
    ]
    changed = copy.replace("pad_position: center", "pad_position: top_left")
    write(exporters, "Other-Exporter/exports/bar.yaml", changed)
    _, bar = st.compare_examples(repo, exporters)
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
    _, bar = st.compare_examples(repo, exporters)
    assert bar.status == "unavailable"


EXAMPLE_BAR = "specs/model-sidecar/examples/detectors/object_detectors/bar/bar.yaml"
EXAMPLE_POINTS = "specs/model-sidecar/examples/detectors/shared/points.yaml"
POINTS_REF = "pose:\n  tracked_points: {$ref: ../../shared/points.yaml}\n"
POINTS_INLINE = "pose:\n  tracked_points: [a, b]\n"


def test_compare_examples_resolves_a_fragment_of_the_example(
    repo: Path, tmp_path_factory: Any
) -> None:
    """The example refers to a fragment; the exporter copy lists the same values inline."""
    write(repo, EXAMPLE_POINTS, "- a\n- b\n")
    write(repo, EXAMPLE_BAR, BAR + POINTS_REF)
    exporters = tmp_path_factory.mktemp("exporters")
    write(exporters, "Other-Exporter/exports/bar.yaml", BAR + POINTS_INLINE)
    _, bar = st.compare_examples(repo, exporters)
    assert (bar.status, bar.lines, bar.notes) == ("same", (), ())
    write(
        exporters,
        "Other-Exporter/exports/bar.yaml",
        BAR + POINTS_INLINE.replace("b]", "c]"),
    )
    _, bar = st.compare_examples(repo, exporters)
    assert bar.lines == (
        "pose.tracked_points: ['a', 'b'] in the example, ['a', 'c'] in the exporter copy",
    )


def test_compare_examples_resolves_a_fragment_of_the_exporter_copy(
    repo: Path, tmp_path_factory: Any
) -> None:
    write(repo, EXAMPLE_BAR, BAR + POINTS_INLINE)
    exporters = tmp_path_factory.mktemp("exporters")
    write(exporters, "Other-Exporter/exports/points.yaml", "- a\n- b\n")
    write(
        exporters,
        "Other-Exporter/exports/bar.yaml",
        BAR + "pose:\n  tracked_points: {$ref: points.yaml}\n",
    )
    _, bar = st.compare_examples(repo, exporters)
    assert (bar.status, bar.lines, bar.notes) == ("same", (), ())


def test_compare_examples_says_when_the_exporter_copy_does_not_resolve(
    repo: Path, tmp_path_factory: Any
) -> None:
    write(repo, EXAMPLE_BAR, BAR + POINTS_INLINE)
    exporters = tmp_path_factory.mktemp("exporters")
    write(
        exporters,
        "Other-Exporter/exports/bar.yaml",
        BAR + "pose:\n  tracked_points: {$ref: missing.yaml}\n",
    )
    _, bar = st.compare_examples(repo, exporters)
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
        + f'pose:\n  tracked_points: {{$ref: ../../shared/points.yaml, sha256: "{wrong}"}}\n',
    )
    exporters = tmp_path_factory.mktemp("exporters")
    write(exporters, "Other-Exporter/exports/bar.yaml", BAR + POINTS_INLINE)
    _, bar = st.compare_examples(repo, exporters)
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
    st.compare_examples(repo, exporters)
    assert snapshot() == before


def test_the_examples_text_has_a_summary_line(
    repo: Path, tmp_path_factory: Any
) -> None:
    exporters = tmp_path_factory.mktemp("exporters")
    write(exporters, "Other-Exporter/exports/bar.yaml", BAR)
    text = st.format_examples(st.compare_examples(repo, exporters))
    assert (
        "detectors/object_detectors/bar/bar.yaml: same\n  exporter copy: Other-Exporter/exports/bar.yaml\n"
        in text
    )
    assert text.endswith("2 examples: 1 same, 0 different, 1 unavailable\n")


# --------------------------------------------------------------------------------------------
# Command line (on the real repository, read only)
# --------------------------------------------------------------------------------------------


@needs_git
def test_main_impact_for_an_empty_range(capsys: pytest.CaptureFixture[str]) -> None:
    assert st.main(["impact", "HEAD..HEAD"]) == 0
    assert "No section is affected." in capsys.readouterr().out


@needs_git
def test_main_impact_for_a_bad_range(capsys: pytest.CaptureFixture[str]) -> None:
    assert st.main(["impact", "no-such-revision-0123456789"]) == 1
    assert capsys.readouterr().err.startswith("error: ")


def test_main_examples_needs_a_folder(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert st.main(["examples", "--exporters-root", str(tmp_path / "absent")]) == 2
    assert "not a folder" in capsys.readouterr().err


def test_main_examples_prints_one_entry_for_each_example(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert st.main(["examples", "--exporters-root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert out.count(": unavailable\n") == len(st.load_inventory()["examples"])
    assert not list(tmp_path.iterdir())


def test_main_needs_a_command(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        st.main([])
    assert exc.value.code == 2


# --------------------------------------------------------------------------------------------
# The tool does not import the package
# --------------------------------------------------------------------------------------------


def test_the_tool_imports_only_the_standard_library_yaml_and_its_siblings() -> None:
    tree = ast.parse(TRACE_PATH.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add((node.module or "").split(".")[0])
    allowed = set(sys.stdlib_module_names) | {
        "yaml",
        "sidecar_normalize",
        "sidecar_refs",
    }
    assert modules <= allowed, modules - allowed

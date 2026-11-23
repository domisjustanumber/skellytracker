"""The functions of `tools/sidecar_trace.py`, on small repositories made for each test.

This file moves to the specs repository with `tools/sidecar_trace.py`. It imports no
skellytracker, onnx or onnxruntime (`tools/tests/test_intake_gate.py` checks it). Each function
of the trace tool that resolves a sidecar needs the resolver of a host. The skellytracker test
`tools/tests/test_package_sidecar_trace.py` checks these functions with the package resolver, on
the same small repositories (`make_repo`, `make_git_repo`).
"""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
from collections import Counter
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
| `post.object.selection.nms` | [post/nms.md](post/nms.md) | Selection: NMS |
"""

# A legacy package sidecar. The scan must not find it (ADR-C0YD item 1).
PACKAGE_FOO = """\
schema_version: v2024.09.1019
model_id: foo
role: [object_detector]
input:
  normalization: none
  resize: {method: letterbox, preserve_aspect_ratio: false}
decode: {requires_nms: true}
"""

FOO = """\
schema_version: "1"
model_id: foo
source: {name: a-lib, version: "1.0"}
role: [object_detector]
input:
  resize: {method: stretch}
object: {classes: [person], decode: {selection: nms}}
"""

BAR = """\
schema_version: "1"
model_id: bar
role: [object_detector]
input:
  normalization: unit_float
  resize: {method: letterbox, pad_position: center, rounding: half_even}
object: {classes: [person], decode: {selection: nms}}
"""

BAZ = """\
schema_version: "1"
model_id: baz
source: {name: declared-lib, version: "1.0"}
role: [keypoint_detector]
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
        "selectors": selectors,
        "implemented_by": steps,
        "external_impl": [],
        "tests": tests or [],
        "vectors": vectors,
        "status": {
            "spec": "stable",
            **{step: "missing" if ref == "missing" else "implemented" for step, ref in steps.items()},
        },
    }
    return "---\n" + yaml.safe_dump(front, sort_keys=False) + "---\n\n# Title\n"


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return make_repo(tmp_path)


def make_repo(tmp_path: Path) -> Path:
    """Write the small repository in `tmp_path` and return it. `test_package_sidecar_trace.py` uses it too."""
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
            "post.object.selection.nms",
            "postprocessor",
            ["object.decode.selection=nms"],
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
            },
            sort_keys=False,
        ),
    )
    write(
        tmp_path, "skellytracker/core/detectors/object_detectors/foo/foo.yaml", PACKAGE_FOO
    )
    examples = spec + "examples/detectors/"
    write(tmp_path, examples + "object_detectors/foo/foo.yaml", FOO)
    write(tmp_path, examples + "object_detectors/foo/other.yaml", FOO)
    write(tmp_path, examples + "shared/skeletons/frag.yaml", "- a\n- b\n")
    write(tmp_path, examples + "shared/empty.yaml", "")
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


VALID = {
    "id": "pre.a",
    "title": "A",
    "kind": "preprocessor",
    "selectors": ["input.resize.method=a"],
    "implemented_by": {"validate": "missing", "forward": "pkg/a.py::f", "inverse": "missing"},
    "external_impl": [],
    "tests": [],
    "vectors": None,
    "status": {"spec": "draft", "validate": "missing", "forward": "partial", "inverse": "missing"},
}

DROP = object()  # a key that the test removes


def synthetic_section(section_id: str, kind: str, implemented_by: dict[str, str]) -> st.Section:
    front = st.FrontMatter(section_id, section_id, kind, (), implemented_by, (), (), None, {})
    return st.Section(section_id, section_id, kind, f"{section_id}.md", front, "")


def test_front_matter_parse_gives_an_immutable_front_matter() -> None:
    front = st.FrontMatter.parse(VALID, "pre", "a.md")
    assert front.selectors == ("input.resize.method=a",)
    assert front.implemented_by["forward"] == "pkg/a.py::f"
    assert st.FRONT_MATTER_KEYS == tuple(VALID)
    with pytest.raises(TypeError):
        front.status["spec"] = "stable"  # type: ignore[index]


@pytest.mark.parametrize(
    ("change", "folder", "problem"),
    [
        ({"since": "1.0"}, "pre", "unknown keys: since"),
        ({"vectors": DROP}, "pre", "missing keys: vectors"),
        ({"tests": None}, "pre", "`tests` must be"),
        ({"id": "post.a"}, "pre", "must start with the folder"),
        ({"title": ""}, "pre", "`title` must be"),
        ({}, "post", "not allowed in 'post'"),
        ({"selectors": []}, "pre", "needs at least one selector"),
        ({"selectors": ["a", "a"]}, "pre", "must not repeat"),
        ({"selectors": ["a b"]}, "pre", "bad path segment"),
        ({"id": "", "kind": "common"}, "common", "`id` must be"),
        ({"selectors": "a"}, "pre", "list of strings"),
        ({"selectors": ["a", 3]}, "pre", "list of strings"),
        ({"id": "common.a", "kind": "common", "selectors": ["a=b"]}, "common", "at most one"),
        ({"id": "common.a", "kind": "common", "selectors": ["a", "b"]}, "common", "at most one"),
        (
            {"implemented_by": {"validate": "missing"}, "status": {"spec": "draft", "validate": "missing"}},
            "pre",
            "must have the steps",
        ),
        (
            {
                "implemented_by": {**VALID["implemented_by"], "decode": "missing"},
                "status": {**VALID["status"], "decode": "missing"},
            },
            "pre",
            "must have the steps",
        ),
        ({"implemented_by": []}, "pre", "map each step to a string"),
        ({"implemented_by": {**VALID["implemented_by"], "forward": 3}}, "pre", "map each step"),
        ({"external_impl": {}}, "pre", "`external_impl` must be"),
        ({"vectors": 3}, "pre", "`vectors` must be"),
        ({"status": None}, "pre", "`status` must have the keys"),
        ({"status": {"spec": "draft"}}, "pre", "`status` must have the keys"),
        ({"status": {**VALID["status"], "spec": "final"}}, "pre", "`status.spec` must be"),
        ({"status": {**VALID["status"], "forward": "done"}}, "pre", "`status.forward` must be one"),
        ({"status": {**VALID["status"], "forward": "missing"}}, "pre", "exactly when"),
    ],
)
def test_front_matter_parse_refuses_a_broken_rule(
    change: dict[str, Any], folder: str, problem: str
) -> None:
    data = {key: value for key, value in {**VALID, **change}.items() if value is not DROP}
    with pytest.raises(st.TraceError, match=f"^a.md: .*{re.escape(problem)}"):
        st.FrontMatter.parse(data, folder, "a.md")


def test_front_matter_parse_skips_the_status_check_when_implemented_by_is_bad() -> None:
    data = {**VALID, "implemented_by": {**VALID["implemented_by"], "forward": 3}}
    with pytest.raises(st.TraceError) as info:
        st.FrontMatter.parse(data, "pre", "a.md")
    assert "`status" not in str(info.value)


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
        ("post.object.selection.nms", "post/nms.md", "Selection: NMS"),
    ]


def test_sections_come_in_the_order_of_the_map(repo: Path) -> None:
    assert [s.id for s in st.load_sections(repo)] == [
        "common.a",
        "pre.resize.letterbox",
        "post.object.selection.nms",
    ]


def test_a_section_that_the_map_omits_comes_last(repo: Path) -> None:
    write(
        repo,
        "specs/model-sidecar/pre/another.md",
        front_matter("pre.another", "preprocessor", ["x"], {"validate": "missing", "forward": "missing"}),
    )
    assert [s.id for s in st.load_sections(repo)][-1] == "pre.another"


def test_a_repeated_section_id_raises(repo: Path) -> None:
    write(repo, "specs/model-sidecar/common/copy.md", front_matter("common.a", "common", []))
    with pytest.raises(st.TraceError, match="common.a"):
        st.load_sections(repo)


def test_section_properties(repo: Path) -> None:
    section = {s.id: s for s in st.load_sections(repo)}["pre.resize.letterbox"]
    assert section.path == "pre/letterbox.md"
    assert section.kind == "preprocessor"
    assert section.tests == ("pkg/test_pre.py",)
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
        ("post.object.selection.nms", "validate"),
    ]


# --------------------------------------------------------------------------------------------
# TRACEABILITY.md
# --------------------------------------------------------------------------------------------


def test_the_normalization_row_shows_the_mode() -> None:
    current = _fake_sidecar("imagenet_bgr", "1", derived=())
    custom = _fake_sidecar({"mode": "custom"}, "1", derived=())
    # A dated version adds no label: the package sidecars are not in the matrix (ADR-C0YD item 1).
    dated = _fake_sidecar("imagenet_bgr", "v2024.09.1019", derived=())
    assert st._normalization_label(current) == "imagenet_bgr"
    assert st._normalization_label(custom) == "custom"
    assert st._normalization_label(dated) == "imagenet_bgr"
    assert st._normalization_label(_fake_sidecar("none", "1", ())) == "none"


def _fake_sidecar(
    normalization: Any, version: str, derived: tuple[str, ...]
) -> st.Sidecar:
    return st.Sidecar(
        key="m@s",
        model_id="m",
        source="s",
        origin="example",
        path="p.yaml",
        schema_version=version,
        resolved={},
        normalized={
            "input": {"normalization": normalization},
            "object": {"decode": {"selection": "none"}},
        },
        derived=derived,
    )


def test_the_bottom_up_row_shows_packed_keypoints_and_instance_keypoints_outputs() -> None:
    def sidecar(outputs: list[dict[str, Any]]) -> st.Sidecar:
        fake = _fake_sidecar("none", "1", ())
        return st.Sidecar(**{**fake.__dict__, "normalized": {"outputs": outputs}})

    packed = sidecar([{"semantic": "packed_detections", "packed_keypoints": {"offset": 6}}])
    poses = sidecar([{"semantic": "packed_detections"}, {"semantic": "instance_keypoints"}])
    both = sidecar([{"semantic": "instance_keypoints", "packed_keypoints": {"offset": 6}}])
    neither = sidecar([{"semantic": "packed_detections", "packed_keypoints": None}])
    assert st._bottom_up_label(packed) == "x (packed)"
    assert st._bottom_up_label(poses) == "x (instance_keypoints)"
    assert st._bottom_up_label(both) == "x (packed, instance_keypoints)"
    assert st._bottom_up_label(neither) == "x"


def test_the_selection_row_shows_the_selection_only() -> None:
    assert st._selection_label(_fake_sidecar("none", "1", ())) == "none"
    dated = _fake_sidecar("none", "v2024.09.1019", ("normalization",))
    assert st._selection_label(dated) == "none"


def test_a_kind_export_example_meets_the_example_item_of_the_gate() -> None:
    section = synthetic_section("s", "common", {})
    counts = st.VectorCounts(cases=1, verified=1, rules=frozenset())
    assert st.gate_items(section, counts, Counter(forecast=2), None) == ["example"]
    assert st.gate_items(section, counts, Counter(export=1), None) == []
    assert st.gate_items(section, counts, Counter(), "reason") == []


def test_the_vectors_item_counts_only_numeric_cases_of_an_algorithm() -> None:
    plain = synthetic_section("s", "common", {})
    algorithm = synthetic_section("p", "preprocessor", {"forward": "x"})
    none = st.VectorCounts(cases=0, verified=0, rules=frozenset())
    refusal_only = st.VectorCounts(cases=1, verified=0, rules=frozenset(), numeric=0, numeric_verified=0)
    open_case = st.VectorCounts(cases=2, verified=1, rules=frozenset(), numeric=2, numeric_verified=1)
    assert st.gate_items(plain, none, Counter(export=1), None) == []
    assert st.gate_items(algorithm, none, Counter(export=1), None) == ["vectors"]
    assert st.gate_items(algorithm, refusal_only, Counter(export=1), None) == ["vectors"]
    assert st.gate_items(plain, open_case, Counter(export=1), None) == ["vectors"]


# --------------------------------------------------------------------------------------------
# impact
# --------------------------------------------------------------------------------------------


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
    return make_git_repo(repo)


def make_git_repo(repo: Path) -> Path:
    """Add the three modules to `repo`, make it a git repository with one commit and return it."""
    write(repo, "pkg/model.py", MODEL_V1)
    write(repo, "pkg/pre.py", PRE_V1)
    write(repo, "pkg/post.py", POST_V1)
    git(repo, "init", "--quiet")
    git(repo, "add", "--all")
    git(repo, "commit", "--quiet", "--message", "first")
    return repo


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


# --------------------------------------------------------------------------------------------
# Command line (on the real repository, read only)
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("argv", [["matrix", "--check"], ["impact", "HEAD"], ["examples", "--exporters-root", "."]])
def test_main_without_a_resolver_stops_with_status_2(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert st.main(argv) == 2
    assert "needs the sidecar resolver of a host" in capsys.readouterr().err


# --------------------------------------------------------------------------------------------
# The imports of the tool
# --------------------------------------------------------------------------------------------


def test_the_tool_imports_only_the_standard_library_yaml_and_its_siblings() -> None:
    tree = ast.parse(TRACE_PATH.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add((node.module or "").split(".")[0])
    # No host package: the host gives the resolver (`main`, `resolve`), and the selector matching
    # loads from specs/model-sidecar/reference/sidecar_normalize.py.
    allowed = set(sys.stdlib_module_names) | {"yaml", "sidecar_refs"}
    assert modules <= allowed, modules - allowed


def test_the_tool_loads_the_lead_copy_of_the_selector_matching() -> None:
    path = st.REPO_ROOT / "specs" / "model-sidecar" / "reference" / "sidecar_normalize.py"
    assert Path(st.sidecar_normalize.__file__).resolve() == path.resolve()

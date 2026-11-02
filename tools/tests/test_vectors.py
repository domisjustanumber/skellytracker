"""The sidecar test vectors match their generator, their sections and the package.

The vector files are in `specs/model-sidecar/vectors/`. `tools/make_vectors.py` writes
them. These tests check four things:

- the files have the documented shape and name existing sections. The same
  shape checks apply to the vectors of a proposal (part 4 of the change
  proposal template);
- the files equal the generator's output, so they never drift from it. The
  generator computes each `expect` again from the other keys of the file;
- hand-computed anchors from the section text agree with the files;
- the skellytracker functions named in `verified_against` still give the same
  results as the cases that list them (and differ where a case does not).
"""

from __future__ import annotations

import functools
import importlib
import math
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytest
import yaml

import make_vectors as mv
from vector_form import (
    CASE_KEYS,
    FILE_KEYS,
    CaseDefect,
    agrees,
    entry_problems,
    file_problems,
    has_fraction,
    problems,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = REPO_ROOT / "specs" / "model-sidecar"
VECTORS_DIR = SPEC_ROOT / "vectors"

MAX_FILE_BYTES = 256 * 1024
# The rule lines of the "Validation rules" headings (the same form as test_traceability.py).
RULE_LINE = re.compile(r"^- \[[ xX]\] `(V-[a-z][a-z0-9_.]*[a-z0-9]-\d+)`", re.MULTILINE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def vector_paths() -> list[Path]:
    return sorted(VECTORS_DIR.glob("*.yaml"))


@functools.cache
def load(name: str) -> dict[str, Any]:
    return yaml.safe_load((VECTORS_DIR / name).read_text(encoding="utf-8"))


def cases_of(section: str) -> list[dict[str, Any]]:
    return load(f"{section}.yaml")["cases"]


def case_params(section: str) -> list[Any]:
    return [pytest.param(case, id=case["id"]) for case in cases_of(section)]


def case_named(section: str, case_id: str) -> dict[str, Any]:
    return next(case for case in cases_of(section) if case["id"] == case_id)


def forward_params(section: str) -> list[Any]:
    """The cases that call `run`, without the `-inverse` cases."""
    return [
        pytest.param(case, id=case["id"])
        for case in cases_of(section)
        if "function" not in case
    ]


def inverse_of(section: str, case: dict[str, Any]) -> dict[str, Any]:
    inverse = case_named(section, f"{case['id']}-inverse")
    assert inverse["function"] == "inverse"
    assert inverse["params"] == case["params"]
    return inverse


def exact_unless_fractional(section: str, *results: Any) -> float:
    """The file tolerance when a result holds a fraction, else 0: integers match exactly."""
    return load(f"{section}.yaml")["tolerance"] if has_fraction(list(results)) else 0


@functools.cache
def section_texts() -> dict[str, str]:
    """The text of each section file, keyed by the section ID of its front matter."""
    found: dict[str, str] = {}
    for path in SPEC_ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if text.startswith("---\n"):
            front_matter = yaml.safe_load(text.split("---\n", 2)[1])
            if isinstance(front_matter, dict) and "id" in front_matter:
                found[front_matter["id"]] = text
    return found


def section_ids() -> set[str]:
    """Every section ID in the front matter of the section files."""
    return set(section_texts())


@functools.cache
def defined_rule_ids() -> frozenset[str]:
    """Every rule ID that a section file defines."""
    return frozenset(
        match for text in section_texts().values() for match in RULE_LINE.findall(text)
    )


def case_problems(
    case: dict[str, Any], section: str, reference_dir: Path = mv.REFERENCE_DIR
) -> list[str]:
    """The form problems of one case (`vector_form.problems`) in this repo."""
    return problems(
        case,
        defined_rule_ids(),
        reference=lambda: mv.producer(section, reference_dir),
        package_function=resolve_function,
    )


def vector_file_problems(
    data: dict[str, Any], reference_dir: Path = mv.REFERENCE_DIR
) -> list[str]:
    """The form problems of one vector file (`vector_form.file_problems`) in this repo."""
    return file_problems(
        data,
        defined_rule_ids(),
        reference=lambda: mv.producer(data["section"], reference_dir),
        package_function=resolve_function,
    )


def resolve_function(reference: str) -> Any:
    """Return the function named by `path/to/module.py::function`."""
    path, _, name = reference.partition("::")
    assert (REPO_ROOT / path).is_file(), f"no file {path}"
    module = importlib.import_module(
        Path(path).with_suffix("").as_posix().replace("/", ".")
    )
    return getattr(module, name)


@functools.cache
def generated_texts() -> dict[str, str]:
    return mv.generate()


@functools.cache
def built_vectors() -> dict[str, dict[str, Any]]:
    """The data that the generator computes from each file, keyed by section ID."""
    return {path.stem: mv.run_file(load(path.name)) for path in vector_paths()}


# ---------------------------------------------------------------------------
# Shape of the files
# ---------------------------------------------------------------------------


def test_the_folder_holds_a_file_for_each_formula_module_with_run() -> None:
    sections = {p.stem.replace(".", "_") for p in vector_paths()}
    with_run = {
        p.stem for p in mv.FORMULAS_DIR.glob("*.py") if hasattr(getattr(mv, p.stem), "run")
    }
    references = {p.stem for p in mv.REFERENCE_DIR.glob("*.py")}
    assert with_run <= sections
    # A file whose section has no formula `run` has a reference (ADR-8DSW item 3).
    assert sections - with_run <= references


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_file_equals_the_generator_output(path: Path) -> None:
    assert path.read_text(encoding="utf-8") == generated_texts()[path.name]


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_file_parses_to_the_generator_data(path: Path) -> None:
    section = path.name.removesuffix(".yaml")
    assert agrees(
        yaml.safe_load(path.read_text(encoding="utf-8")),
        built_vectors()[section],
    )


# The tolerance of the files of each group of sections.
FILE_TOLERANCE = {"resize": 1e-4, "unprojection": 1e-4, "normalize": 1e-5, "selection": 1e-5}


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_file_has_the_documented_top_level_keys(path: Path) -> None:
    data = load(path.name)
    verification = "verified_against" if "verified_against" in data else "unverified"
    assert ("verified_against" in data) != ("unverified" in data)
    checks = ["checks"] if "checks" in data else []
    assert list(data) == ["section", "notes", "tolerance", *checks, verification, "cases"]
    assert data["notes"][0].startswith("Normative text: specs/model-sidecar/")
    group = next(name for name in FILE_TOLERANCE if name in data["section"])
    assert data["tolerance"] == FILE_TOLERANCE[group]


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_file_has_the_two_header_lines_and_no_other_comment(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert tuple(lines[:2]) == mv.HEADER
    assert not [line for line in lines[2:] if line.lstrip().startswith("#")]
    assert not {"spec_revision", "generated_by"} & set(load(path.name))


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_section_matches_the_file_name_and_an_existing_section(path: Path) -> None:
    section = load(path.name)["section"]
    assert path.name == f"{section}.yaml"
    assert section in section_ids()


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_unverified_gives_a_reason(path: Path) -> None:
    data = load(path.name)
    if "unverified" in data:
        assert isinstance(data["unverified"], str)
        assert len(data["unverified"]) > 20


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_verified_against_names_a_function_that_exists(path: Path) -> None:
    for entry in load(path.name).get("verified_against", []):
        assert not entry_problems(entry, resolve_function)


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_cases_have_the_documented_shape(path: Path) -> None:
    data = load(path.name)
    cases = data["cases"]
    assert cases
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids))
    for case in cases:
        assert not case_problems(case, data["section"])
    assert not vector_file_problems(data)


def _pair(forward: dict[str, Any] | None = None, inverse: dict[str, Any] | None = None) -> list:
    """The first forward case of pre.resize.stretch and its `-inverse` case, with changes."""
    first, second = cases_of("pre.resize.stretch")[:2]
    changed = [{**first, **(forward or {})}, {**second, **(inverse or {})}]
    return [in_order({k: v for k, v in c.items() if v is not None}, CASE_KEYS) for c in changed]


# Each row: the cases of a file with one broken rule between cases, and a part of the problem.
BROKEN_CASE_LISTS = [
    (lambda: _pair(inverse={"id": "zzz"}), "an Inverse case has function inverse"),
    (lambda: _pair()[::-1], "follows the case"),
    (lambda: _pair(inverse={"function": None}), "an Inverse case has function inverse"),
    (lambda: [_pair()[0], {**_pair()[0], "id": "x-inverse"}], "an Inverse case has function"),
    (lambda: _pair(inverse={"params": {"target_size": [1, 1]}}), "the params of its forward"),
    (
        lambda: _pair(inverse={"input": {"src_w": 1920, "src_h": 1080}}),
        "forward input plus model_xy",
    ),
    (
        lambda: _pair(forward={"note": "refused", "expect": {"error": "no-rule"}}),
        "needs the check refused",
    ),
    (lambda: _pair(forward={"checks": ["refused"]}), "needs the check refused"),
]


@pytest.mark.parametrize(
    ("cases", "problem"), BROKEN_CASE_LISTS, ids=[f"{r[1]}-{i}" for i, r in enumerate(BROKEN_CASE_LISTS)]
)
def test_a_file_that_breaks_a_rule_between_cases_has_a_problem(cases: Any, problem: str) -> None:
    data = load("pre.resize.stretch.yaml")
    assert not vector_file_problems({**data, "cases": _pair()})
    found = vector_file_problems({**data, "cases": cases()})
    assert any(problem in item for item in found), found


def test_each_inverse_case_gives_source_xy() -> None:
    inverse = [c for p in vector_paths() for c in load(p.name)["cases"] if c.get("function") == "inverse"]
    assert inverse and all(list(case["expect"]) == ["source_xy"] for case in inverse)


# Each row: a change to a valid case (None removes a key) and a part of the problem that it must give.
BROKEN_FORMS = [
    ({"note": None, "expect": {"error": "no-rule"}}, "a no-rule result needs a note"),
    ({"function": "none"}, "function none is only for a failed result"),
    ({"input": {"src_w": 1920, "src_h": 1080, "target_size": [640, 640]}}, "share the keys"),
    ({"function": "no_such_function"}, "no function no_such_function"),
    ({"tolerance": 0.0001}, "not a case form"),
    ({"unproject": {"model_xy": [0, 0], "source_xy": [0, 0]}}, "not a case form"),
    ({"note": ""}, "note must be a string"),
    ({"checks": ["refused", "refused"]}, "checks must be a list"),
]


def in_order(mapping: dict[str, Any], order: tuple[str | None, ...]) -> dict[str, Any]:
    """Return `mapping` with its keys in the form order; a key out of the form goes last."""
    names = [k for key in order for k in ((key,) if key else ("verified_against", "unverified"))]
    return {
        **{key: mapping[key] for key in names if key in mapping},
        **{key: value for key, value in mapping.items() if key not in names},
    }


@pytest.mark.parametrize(
    ("change", "problem"), BROKEN_FORMS, ids=[row[1] for row in BROKEN_FORMS]
)
def test_a_case_that_breaks_a_form_rule_has_a_problem(
    change: dict[str, Any], problem: str
) -> None:
    section = "pre.resize.letterbox"
    valid = case_named(section, "center-upscale")
    assert not case_problems(valid, section)
    changed = {key: value for key, value in {**valid, **change}.items() if value is not None}
    found = case_problems(in_order(changed, CASE_KEYS), section)
    assert any(problem in item for item in found), found


def test_a_case_keeps_the_key_order() -> None:
    case = case_named("pre.resize.letterbox", "center-upscale")
    moved = {"params": case["params"], **case}
    assert any("not a case form" in found for found in case_problems(moved, "pre.resize.letterbox"))


def test_a_data_only_validator_case_names_no_function() -> None:
    """`function: none` with a failed result needs no producer function."""
    case = {
        "id": "valid",
        "function": "none",
        "params": {},
        "input": {"sidecar": {}},
        "expect": {"failed": []},
    }

    def no_producer() -> Any:
        raise AssertionError("a data-only case does not load the producer")

    assert not problems(case, [], reference=no_producer, package_function=resolve_function)


@pytest.mark.parametrize(
    ("change", "problem"),
    [
        ({"spec_revision": "vNEXT"}, "not a file form"),
        ({"tolerance": -1}, "tolerance must be a number"),
        ({"notes": "one note"}, "notes must be a list"),
        ({"checks": ["input-size-follows-resize"]}, "also a check of the case"),
    ],
    ids=["spec-revision", "negative-tolerance", "notes-not-a-list", "check-twice"],
)
def test_a_file_that_breaks_a_form_rule_has_a_problem(change: dict[str, Any], problem: str) -> None:
    data = load("pre.resize.letterbox.yaml")
    case = in_order({**data["cases"][0], "checks": ["input-size-follows-resize"]}, CASE_KEYS)
    valid = {**data, "cases": [case]}
    assert not vector_file_problems(valid)
    found = vector_file_problems(in_order({**valid, **change}, FILE_KEYS))
    assert any(problem in item for item in found), found


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_file_is_small(path: Path) -> None:
    assert path.stat().st_size <= MAX_FILE_BYTES


def test_the_generator_writes_the_case_form_of_a_proposal(tmp_path: Path) -> None:
    """`function`, `compare`, an error by rule ID, NaN, notes, data-only cases and an exporter entry."""
    (tmp_path / "pre_resize_letterbox.py").write_text(
        "def geometry(**kwargs):\n    return {}\n", encoding="utf-8"
    )
    exporter = {"OpenMMLab-Exporter": "onnx_runtime/preprocess.py::letterbox"}
    long_note = ('a note with a colon: "quotes", a # sign and enough words ' * 3).strip()
    geometry = {"function": "geometry", "params": {}, "input": {}}
    vectors = {
        "section": "pre.resize.letterbox",
        "notes": ["Normative text: specs/model-sidecar/pre/resize-letterbox.md.", long_note],
        "tolerance": 1e-4,
        "verified_against": [exporter],
        "cases": [
            {
                "id": "two-tolerances",
                **geometry,
                "expect": {"z": 0.1, "k": 1 / 3},
                "compare": {"z": {"atol": 1e-4}, "k": {"atol": 1e-6}},
            },
            {
                "id": "angle",
                **geometry,
                "expect": {"rotation": -3.14159},
                "compare": {"rotation": {"atol": 1e-6, "period": 2 * math.pi}},
            },
            {
                "id": "refused",
                **geometry,
                "expect": {"error": "V-pre.resize.letterbox-1"},
                "checks": ["refused"],
            },
            {
                "id": "refused-caller-argument",
                **geometry,
                "expect": {"error": "no-rule"},
                "note": long_note,
                "checks": ["refused"],
            },
            {"id": "valid", "function": "none", "params": {}, "input": {}, "expect": {"failed": []}},
            {
                "id": "one-failed-rule",
                "function": "none",
                "params": {},
                "input": {},
                "expect": {"failed": ["V-pre.resize.letterbox-1"]},
            },
            {
                "id": "not-a-number",
                **geometry,
                "input": {"x": math.nan},
                "expect": {"y": math.nan, "w": math.inf},
            },
        ],
    }
    text = mv.render(vectors)
    data = yaml.safe_load(text)
    assert agrees(data, mv.form(vectors))
    assert all(len(line) <= mv.LINE_WIDTH for line in text.splitlines())
    assert data["notes"][1] == data["cases"][3]["note"] == long_note
    spaced = f" {long_note}  {long_note} "  # a fold would lose these spaces
    assert yaml.safe_load("\n".join(mv._string_entry("note: ", spaced)))["note"] == spaced
    assert data["verified_against"] == [exporter]
    assert data["cases"][0]["expect"]["k"] == 0.333333  # expect has 6 decimals
    assert not vector_file_problems(data, tmp_path)
    for case in data["cases"]:
        assert not case_problems(case, data["section"], tmp_path)
    refused = data["cases"][2]
    for expect in (
        {"error": "V-pre.resize.letterbox-99"},
        {"failed": ["V-pre.resize.letterbox-99"]},
        {"failed": ["V-pre.resize.letterbox-2", "V-pre.resize.letterbox-1"]},
        {"failed": ["V-pre.resize.letterbox-1", "V-pre.resize.letterbox-1"]},
        {"failed": [], "n_w": 1},
    ):
        assert case_problems({**refused, "expect": expect}, data["section"], tmp_path)
    with pytest.raises(FileNotFoundError):
        mv.load_reference("pre.resize.stretch", tmp_path)


def test_outcome_writes_a_refusal_as_its_rule_id_or_no_rule() -> None:
    def refuse(message: str) -> dict[str, Any]:
        raise ValueError(message)

    def lookup() -> dict[str, Any]:
        return {}["missing"]

    assert mv.outcome(lambda x: {"y": x + 1}, 1) == {"y": 2}
    assert mv.outcome(refuse, "V-pre.resize.letterbox-1: bad pad") == {
        "error": "V-pre.resize.letterbox-1"
    }
    assert mv.outcome(refuse, "bad shape (V-pre.resize.letterbox-1: no)") == {
        "error": mv.NO_RULE
    }
    assert mv.outcome(refuse, message="bad shape") == {"error": "no-rule"}
    with pytest.raises(KeyError):
        mv.outcome(lookup)


def test_a_reference_module_imports_the_module_of_another_section(
    tmp_path: Path,
) -> None:
    (tmp_path / "g3owner_section.py").write_text("VALUE = 2\n", encoding="utf-8")
    (tmp_path / "g3user_section.py").write_text(
        "import g3owner_section\n\n"
        "def value():\n    return {'value': g3owner_section.VALUE + 1}\n",
        encoding="utf-8",
    )
    module = mv.load_reference("g3user.section", tmp_path)
    assert module.value() == {"value": 3}
    assert str(tmp_path) not in sys.path
    assert sys.modules["g3user_section"] is module
    # A case cannot name a function of another section through its module.
    (tmp_path / "g3rebind_section.py").write_text(
        "from g3owner_section import VALUE\n"
        "import g3user_section\n\n"
        "value = g3user_section.value\n",
        encoding="utf-8",
    )
    case = {"id": "rebound", "function": "value", "params": {}, "input": {}, "expect": {}}
    assert case_problems(case, "g3rebind.section", tmp_path)


def test_a_module_of_another_folder_does_not_shadow_an_import(tmp_path: Path) -> None:
    for name, value in (("one", 1), ("two", 2)):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "g3shadow_owner.py").write_text(f"VALUE = {value}\n", encoding="utf-8")
        (folder / "g3shadow_user.py").write_text(
            "import g3shadow_owner\n\ndef value():\n    return g3shadow_owner.VALUE\n", encoding="utf-8"
        )
        assert mv.load_reference("g3shadow.user", folder).value() == value


def test_a_formula_module_does_not_take_the_place_of_a_missing_sibling(
    tmp_path: Path,
) -> None:
    (tmp_path / "post_unprojection.py").write_text(
        "import pre_resize_letterbox\n", encoding="utf-8"
    )
    with pytest.raises(ModuleNotFoundError):
        mv.load_reference("post.unprojection", tmp_path)
    assert mv.post_unprojection.pre_resize_letterbox is mv.pre_resize_letterbox


def test_the_renderer_writes_a_long_item_in_block_form_and_a_large_float() -> None:
    long_item = {"points": [[float(i) + 0.125 for i in range(12)] for _ in range(3)]}
    vectors = {
        "section": "post.unprojection",
        "notes": [],
        "tolerance": 1e-4,
        "checks": [],
        "unverified": "a test of the renderer, with no implementation",
        "cases": [
            {
                "id": "long-nested-item",
                "checks": [],
                "params": {},
                "input": {"items": [long_item, [list(range(40)), "x"]]},
                "expect": {"huge": 1e308, "neg": -2.0**60, "whole": 3.0},
                "verified_against": [],
            }
        ],
    }
    text = mv.render(vectors)
    assert all(len(line) <= mv.LINE_WIDTH for line in text.splitlines())
    assert "huge: 1.0e+308" in text
    assert agrees(yaml.safe_load(text), mv.form(vectors))
    # An empty notes, checks or case verified_against goes, so the text reads back the same.
    data = yaml.safe_load(text)
    assert list(data) == ["section", "tolerance", "unverified", "cases"]
    assert list(data["cases"][0]) == ["id", "params", "input", "expect"]
    assert mv.render(data) == text


# ---------------------------------------------------------------------------
# The generator computes `expect` from the other keys of a file
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_the_generator_writes_the_same_bytes_from_the_file_without_expect(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    data["cases"] = [
        {k: v for k, v in case.items() if k != "expect" or case.get("function") == "none"}
        for case in data["cases"]
    ]
    assert mv.render(mv.run_file(data)) == text


def test_a_run_keeps_a_hand_edited_note_and_restores_a_hand_edited_expect() -> None:
    text = (VECTORS_DIR / "pre.resize.stretch.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    data["cases"][1]["expect"] = {"source_xy": [0, 0]}
    assert mv.render(mv.run_file(data)) == text
    data["cases"][0]["note"] = "a note that a person wrote"
    expected = yaml.safe_load(text)
    expected["cases"][0]["note"] = "a note that a person wrote"
    assert yaml.safe_load(mv.render(mv.run_file(data))) == expected


def test_a_data_only_case_keeps_the_expect_of_its_author_and_needs_one() -> None:
    data = yaml.safe_load((VECTORS_DIR / "pre.resize.stretch.yaml").read_text(encoding="utf-8"))
    valid = {"id": "valid", "function": "none", "params": {}, "input": {}, "expect": {"failed": []}}
    data["cases"].append(valid)
    assert mv.run_file(data)["cases"][-1] == valid
    data["cases"][-1] = {key: value for key, value in valid.items() if key != "expect"}
    with pytest.raises(CaseDefect, match="valid: a case with function none needs"):
        mv.run_file(data)


def test_a_reference_producer_writes_expect_and_must_agree_with_the_formulas(
    tmp_path: Path,
) -> None:
    name = "pre.resize.stretch.yaml"
    vectors = tmp_path / "vectors"
    vectors.mkdir()
    shutil.copy(VECTORS_DIR / name, vectors / name)
    formulas = (mv.FORMULAS_DIR / "pre_resize_stretch.py").read_text(encoding="utf-8")

    def reference(shift: float) -> Path:
        """A reference that moves the x of each Inverse result by `shift`."""
        folder = tmp_path / f"reference-{len(list(tmp_path.iterdir()))}"
        folder.mkdir()
        (folder / "pre_resize_stretch.py").write_text(
            f"{formulas}\n_inverse = inverse\n\n\n"
            "def inverse(params, input):\n"
            "    x, y = _inverse(params, input)['source_xy']\n"
            f"    return {{'source_xy': [x + {shift!r}, y]}}\n",
            encoding="utf-8",
        )
        return folder

    assert mv.generate(vectors, reference(0.0)) == {
        name: (VECTORS_DIR / name).read_text(encoding="utf-8")
    }
    # Within the tolerance of the file, the value of the reference is written.
    written = yaml.safe_load(mv.generate(vectors, reference(0.00004))[name])
    assert written["cases"][1]["expect"]["source_xy"] == [960.00004, 540]
    with pytest.raises(CaseDefect, match="-inverse: the reference and the formulas disagree"):
        mv.generate(vectors, reference(0.001))


def test_a_section_with_only_a_reference_runs_without_a_formula_module(tmp_path: Path) -> None:
    (tmp_path / "post_only_reference.py").write_text(
        "def run(params, input):\n    return {'y': params['a'] + input['b']}\n", encoding="utf-8"
    )
    case = {"id": "sum", "params": {"a": 1}, "input": {"b": 0.5}}
    data = {"section": "post.only_reference", "tolerance": 1e-4, "unverified": "a test"}
    assert not hasattr(mv, "post_only_reference")
    assert mv.run_file({**data, "cases": [case]}, tmp_path)["cases"] == [{**case, "expect": {"y": 1.5}}]
    with pytest.raises(CaseDefect, match="sum: post_only_reference has no check box-order"):
        mv.run_file({**data, "cases": [{**case, "checks": ["box-order"]}]}, tmp_path)


def test_the_generator_stops_on_a_file_that_breaks_the_form() -> None:
    data = load("pre.resize.stretch.yaml")
    forward, inverse = data["cases"][:2]
    assert inverse["id"] == f"{forward['id']}-inverse"
    with pytest.raises(CaseDefect, match="-inverse: an Inverse case follows the case"):
        mv.run_file({**data, "cases": [inverse, forward, *data["cases"][2:]]})
    with pytest.raises(CaseDefect, match="the keys .* are not a file form"):
        mv.run_file({**data, "spec_revision": "vNEXT"})


# ---------------------------------------------------------------------------
# Named checks (the `CHECKS` of the formula modules) and unknown enums
# ---------------------------------------------------------------------------

LETTERBOX = {"target_size": [640, 640], "pad_position": "center", "rounding": "half_even"}
CENTER = {"method": "letterbox", **LETTERBOX}
AFFINE = {
    "method": "affine_person_crop",
    "target_size": [256, 192],
    "expand_ratio": 1.0,
    "maintain_aspect_ratio": True,
}
FULL_HD = {"src_w": 1920, "src_h": 1080}
SCORED = {"score_field": "score", "class_field": "class_id"}
DETECTION_FIELDS = ["x1", "y1", "x2", "y2", "score", "class_id"]

# Each row: the section, the check and a case that breaks its claim.
BROKEN_CLAIMS = [
    ("pre.resize.letterbox", "rounding-changes-result", LETTERBOX, FULL_HD),
    ("pre.resize.letterbox", "rounding-keeps-result", LETTERBOX, {"src_w": 1280, "src_h": 101}),
    ("pre.resize.letterbox", "scaled-width-rounds-to-zero", LETTERBOX, FULL_HD),
    ("pre.resize.letterbox", "cut-differs-from-round", LETTERBOX, FULL_HD),
    (
        "post.det.selection.none",
        "float32-stable",
        {**SCORED, "confidence_threshold_default": 0.7},
        # 0.70000001 > 0.7 in float64; in float32 both are 0.699999988.
        {"fields": DETECTION_FIELDS, "rows": [[0, 0, 8, 8, 0.70000001, 0]]},
    ),
    (
        "post.unprojection",
        "input-size-follows-resize",
        {"scale": "pixel", "input_size": [480, 640], "resize": CENTER},
        {**FULL_HD, "decoded_xy": [0, 0]},
    ),
    (
        "post.unprojection",
        "input-size-follows-resize",
        {"scale": "pixel", "input_size": [256, 192], "resize": AFFINE},
        {**FULL_HD, "bbox_xyxy": [100, 200, 196, 328], "decoded_xy": [0, 0]},
    ),
    (
        "post.unprojection",
        "input-size-follows-resize",
        {"scale": "pixel", "input_size": [640, 640], "resize": {"method": "none"}},
        {"src_w": 640, "src_h": 480, "decoded_xy": [0, 0]},
    ),
    (
        "post.unprojection",
        "input-size-follows-resize",
        {"scale": "pixel", "input_size": [640, 640], "resize": CENTER},
        {**FULL_HD, "bbox_xyxy": [100, 200, 196, 328], "decoded_xy": [0, 0]},
    ),
    (
        "post.unprojection",
        "clear-of-upper-clamp-bound",
        {"scale": "pixel", "input_size": [640, 640], "resize": CENTER},
        {**FULL_HD, "decoded_xyxy": [0, 140, 640, 500]},
    ),
    (
        "post.unprojection",
        "keeps-area-after-clamp",
        {"scale": "pixel", "input_size": [640, 640], "resize": CENTER},
        {**FULL_HD, "decoded_xyxy": [0, 0, 320, 100]},
    ),
]


def formula_module(section: str) -> Any:
    return getattr(mv, section.replace(".", "_"))


def checked_case(section: str, checks: list[str], params: Any, inp: Any) -> dict[str, Any]:
    expect = formula_module(section).run(params, inp)
    return {"id": "probe", "checks": checks, "params": params, "input": inp, "expect": expect}


@pytest.mark.parametrize(
    ("section", "name", "params", "inp"),
    [pytest.param(*row, id=f"{row[1]}-{i}") for i, row in enumerate(BROKEN_CLAIMS)],
)
def test_a_check_stops_the_generator_on_a_case_that_breaks_its_claim(
    section: str, name: str, params: Any, inp: Any
) -> None:
    case = checked_case(section, [name], params, inp)
    with pytest.raises(CaseDefect, match=f"^probe: {name}: "):
        mv.run_checks(formula_module(section), case)


def test_each_registered_check_holds_on_the_published_cases_that_declare_it() -> None:
    declared, registered = set(), set()
    for section, data in built_vectors().items():
        module = formula_module(section)
        file_checks = data.get("checks", [])
        registered |= {(section, name) for name in getattr(module, "CHECKS", {})}
        for case in data["cases"]:
            mv.run_checks(module, case, file_checks)
            declared |= {(section, name) for name in [*file_checks, *case.get("checks", [])]}
    assert declared == registered
    assert {name for _, name in registered} == {row[1] for row in BROKEN_CLAIMS}


def test_the_box_checks_pass_on_a_point_case() -> None:
    params = {"scale": "pixel", "input_size": [640, 640], "resize": CENTER}
    checks = ["clear-of-upper-clamp-bound", "keeps-area-after-clamp"]
    case = checked_case("post.unprojection", checks, params, {**FULL_HD, "decoded_xy": [0, 0]})
    mv.run_checks(mv.post_unprojection, case)


@pytest.mark.parametrize(
    ("checks", "expect"),
    [
        (["no-such-check"], {"n_w": 1}),
        ([], {"error": "no-rule"}),
        (["refused"], {"n_w": 1}),
    ],
    ids=["unknown-name", "error-without-refused", "refused-without-error"],
)
def test_run_checks_stops_on_an_unknown_name_or_a_wrong_refused(
    checks: list[str], expect: dict[str, Any]
) -> None:
    case = {"id": "probe", "checks": checks, "params": {}, "input": {}, "expect": expect}
    with pytest.raises(CaseDefect):
        mv.run_checks(mv.pre_resize_letterbox, case)


def test_run_checks_accepts_an_error_result_with_refused() -> None:
    case = {"id": "probe", "checks": ["refused"], "params": {}, "input": {}, "expect": {"error": "no-rule"}}
    mv.run_checks(mv.pre_resize_letterbox, case)


NONE_PIXELS = {"normalization": "none", "color_format": "rgb"}


@pytest.mark.parametrize(
    ("section", "params", "inp"),
    [
        ("pre.resize.letterbox", {**LETTERBOX, "rounding": "half_down"}, FULL_HD),
        ("pre.normalize", {"normalization": "imagenet"}, {"pixels_bgr": [[0, 0, 0]]}),
        ("pre.normalize", {"normalization": {"mode": "scaled"}}, {"pixels_bgr": [[0, 0, 0]]}),
        ("pre.normalize", {**NONE_PIXELS, "color_format": "rgba"}, {"pixels_bgr": [[0, 0, 0]]}),
        (
            "post.det.selection.top_k",
            {"top_k": 1, "score_activation": "softmax"},
            {"boxes": [[0, 0, 8, 8]], "class_logits": [[0.5]]},
        ),
    ],
    ids=["rounding", "normalization", "custom-mode", "color-format", "score-activation"],
)
def test_an_unknown_enum_value_is_a_defect(section: str, params: Any, inp: Any) -> None:
    with pytest.raises(CaseDefect, match="unknown"):
        formula_module(section).run(params, inp)


# ---------------------------------------------------------------------------
# Hand-computed anchors (from the section text, not from the generator)
# ---------------------------------------------------------------------------


# Each row: the case id, the path into the case and the expected value, by section.
ANCHORS: dict[str, list[tuple[str, tuple[str | int, ...], Any]]] = {
    "pre.resize.letterbox": [
        (
            "center-half-even-landscape",
            ("expect",),
            {"n_w": 640, "n_h": 360, "left": 0, "top": 140},
        ),
        ("center-half-even-landscape-inverse", ("input", "model_xy"), [320, 320]),
        ("center-half-even-landscape-inverse", ("expect",), {"source_xy": [960, 540]}),
        ("center-rounding-tie-half-even", ("expect", "n_h"), 50),
        ("center-rounding-tie-half-even", ("expect", "top"), 295),
        ("center-rounding-tie-half-up", ("expect", "n_h"), 51),
        ("center-rounding-tie-half-up", ("expect", "top"), 294),
        ("center-odd-remainder-bottom", ("expect", "top"), 80),
        ("center-odd-remainder-right", ("expect", "left"), 80),
        (
            "center-scale-exactly-one",
            ("expect",),
            {"n_w": 640, "n_h": 640, "left": 0, "top": 0},
        ),
        ("center-width-guard", ("expect", "n_w"), 1),
        ("center-width-guard", ("expect", "left"), 319),
        ("center-width-guard", ("expect", "n_h"), 640),
        ("center-float-noise-below-integer", ("expect", "n_w"), 416),
        ("center-float-noise-below-integer", ("expect", "n_h"), 312),
        ("top-left-fraction-above-half", ("expect", "n_h"), 360),
    ],
    "pre.resize.stretch": [
        ("portrait-target", ("expect", "dst_w"), 384),
        ("portrait-target", ("expect", "dst_h"), 640),
        ("portrait-target-inverse", ("expect", "source_xy"), [1920, 1080]),
        ("unproject-fractional-inverse", ("expect", "source_xy"), [300, 168.75]),
    ],
    "pre.resize.fit": [
        ("fractional-offset", ("expect",), {"scale": 0.64, "left": 0, "top": 213.44}),
        ("fractional-offset-inverse", ("expect", "source_xy"), [500, 166.5]),
        ("half-pixel-offset-scale-one", ("expect", "top"), 80.5),
        ("unproject-in-the-padding-inverse", ("expect", "source_xy"), [0, -420]),
        ("one-pixel-wide-source", ("expect", "left"), 316.8),
    ],
    "pre.resize.affine_person_crop": [
        ("tall-box-grows-width", ("expect", "center"), [200, 250]),
        ("tall-box-grows-width", ("expect", "crop_w"), 375),
        ("tall-box-grows-width", ("expect", "crop_h"), 500),
        (
            "tall-box-grows-width",
            ("expect", "matrix"),
            [[0.512, 0, -6.4], [0, 0.512, 0]],
        ),
        ("wide-box-grows-height", ("expect", "crop_w"), 500),
        ("wide-box-grows-height", ("expect", "crop_h"), pytest.approx(666.666667)),
        ("aspect-ratio-not-kept", ("expect", "matrix", 0, 0), 0.768),
        ("aspect-ratio-not-kept", ("expect", "matrix", 1, 1), 0.512),
    ],
    "post.unprojection": [
        # Letterbox with `center` on 1920x1080 -> 640x640:
        # s = 1/3, n_h = 360, top = 140.
        (
            "normalized-01-top-left-corner",
            ("expect",),
            {"model_xy": [0, 0], "source_xy": [0, -420]},
        ),
        (
            "normalized-01-bottom-right-corner",
            ("expect",),
            {"model_xy": [640, 640], "source_xy": [1920, 1500]},
        ),
        # normalized_11 maps -1 and 1 to the edges 0 and the width,
        # not to pixel centres.
        ("normalized-11-left-edge", ("expect", "model_xy"), [0, 320]),
        ("normalized-11-right-edge", ("expect", "model_xy"), [640, 320]),
        ("normalized-11-left-edge", ("expect", "source_xy"), [0, 540]),
        ("normalized-11-right-edge", ("expect", "source_xy"), [1920, 540]),
        (
            "normalized-11-off-centre",
            ("expect",),
            {"model_xy": [160, 480], "source_xy": [480, 1020]},
        ),
        # target_size [384, 640]: x uses the width 640 and y uses the height 384;
        # top = 12.
        (
            "normalized-01-non-square-input",
            ("expect",),
            {"model_xy": [320, 192], "source_xy": [960, 540]},
        ),
        (
            "normalized-11-non-square-input",
            ("expect",),
            {"model_xy": [640, 0], "source_xy": [1920, -36]},
        ),
        (
            "normalized-01-stretch",
            ("expect",),
            {"model_xy": [160, 480], "source_xy": [480, 810]},
        ),
        (
            "pixel-affine-person-crop",
            ("expect",),
            {"model_xy": [96, 128], "source_xy": [148, 264]},
        ),
        # Box clamping.
        ("box-clamp-default-is-true", ("expect", "source_xyxy"), [-60, -120, 600, 780]),
        ("box-clamp-default-is-true", ("expect", "output_xyxy"), [0, 0, 600, 780]),
        ("box-clamp-boxes-true", ("expect", "output_xyxy"), [0, 0, 600, 780]),
        (
            "box-clamp-boxes-false-keeps-negative-values",
            ("expect", "output_xyxy"),
            [-60, -120, 600, 780],
        ),
        (
            "box-clamp-after-the-scale-conversion",
            ("expect", "source_xyxy"),
            [0, -420, 960, 540],
        ),
        (
            "box-clamp-after-the-scale-conversion",
            ("expect", "output_xyxy"),
            [0, 0, 960, 540],
        ),
        (
            "box-normalized-01-inside-the-image",
            ("expect", "source_xyxy"),
            [480, 420, 1440, 660],
        ),
        (
            "box-normalized-01-inside-the-image",
            ("expect", "output_xyxy"),
            [480, 420, 1440, 660],
        ),
    ],
    "pre.normalize": [
        ("imagenet-rgb", ("expect", "channel_order"), "rgb"),
        ("imagenet-bgr", ("expect", "channel_order"), "bgr"),
        ("imagenet-bgr-legacy", ("expect", "channel_order"), "bgr"),
        ("imagenet-bgr-legacy", ("params", "schema_version"), "< vNEXT"),
        ("imagenet-bgr", ("params", "schema_version"), "vNEXT"),
        # An all-black pixel: the well-known first row of ImageNet-normalized black.
        (
            "imagenet-rgb",
            ("expect", "values", 0),
            pytest.approx([-2.117904, -2.035714, -1.804444]),
        ),
    ],
    "post.det.selection.none": [
        ("threshold-is-strict", ("expect", "kept_rows"), [1, 4]),
        ("class-id-map-drops-minus-one", ("expect", "kept_rows"), [0, 2, 3, 5]),
        ("class-id-map-drops-minus-one", ("expect", "class_ids"), [2, 0, 5, 5]),
        ("default-confidence-threshold", ("expect", "kept_rows"), [0, 2]),
        ("no-nms-for-overlapping-boxes", ("expect", "kept_rows"), [0, 1]),
        ("max-detections-does-not-pad", ("expect", "kept_rows"), [0, 1]),
        ("box-format-cxcywh", ("expect", "boxes_xyxy"), [[40, 35, 60, 45]]),
    ],
    "post.det.selection.top_k": [
        ("several-classes-on-one-row", ("expect", "kept_rows"), [2, 0, 0]),
        ("several-classes-on-one-row", ("expect", "class_ids"), [1, 0, 1]),
        ("several-classes-on-one-row", ("expect", "scores"), [0.95, 0.9, 0.8]),
        ("ties-keep-the-lower-flat-index", ("expect", "kept_rows"), [0, 0, 1]),
        ("ties-keep-the-lower-flat-index", ("expect", "class_ids"), [0, 1, 0]),
        ("class-id-map-lowers-the-count", ("expect", "kept_rows"), [0]),
        ("class-id-map-lowers-the-count", ("expect", "class_ids"), [7]),
        ("sigmoid-and-strict-threshold", ("expect", "kept_rows"), [1, 0]),
        (
            "sigmoid-and-strict-threshold",
            ("expect", "scores"),
            pytest.approx([0.982014, 0.880797], abs=1e-6),
        ),
    ],
    "post.det.selection.nms": [
        ("suppress-overlap-and-threshold", ("expect", "kept_rows"), [0, 2]),
        ("suppress-overlap-and-threshold", ("expect", "scores"), [0.9, 0.7]),
        ("iou-equal-to-threshold-is-kept", ("expect", "kept_rows"), [0, 1]),
        ("iou-above-threshold-is-suppressed", ("expect", "kept_rows"), [0]),
        ("box-area-adds-nothing", ("expect", "kept_rows"), [0, 1]),
        ("equal-scores-lower-row-wins", ("expect", "kept_rows"), [0, 2]),
        ("output-is-sorted-by-score", ("expect", "kept_rows"), [1, 2, 0]),
        ("per-class-nms-keeps-both", ("expect", "kept_rows"), [0, 1]),
        ("class-agnostic-suppresses-across-classes", ("expect", "kept_rows"), [0]),
        ("post-nms-top-k-keeps-the-highest", ("expect", "kept_rows"), [1, 2]),
        ("post-nms-top-k-counts-survivors", ("expect", "kept_rows"), [0, 2]),
        ("class-id-map-drop-comes-before-nms", ("expect", "kept_rows"), [1]),
        ("is-person-only-drop-comes-before-nms", ("expect", "kept_rows"), [1]),
        ("no-class-source-uses-person-class-id", ("expect", "class_ids"), [2, 2]),
    ],
}


@pytest.mark.parametrize(
    ("section", "case_id", "path", "expected"),
    [
        pytest.param(
            section,
            case_id,
            path,
            expected,
            id=f"{section}/{case_id}/{'.'.join(map(str, path))}",
        )
        for section, rows in ANCHORS.items()
        for case_id, path, expected in rows
    ],
)
def test_anchor(
    section: str, case_id: str, path: tuple[str | int, ...], expected: Any
) -> None:
    value: Any = case_named(section, case_id)
    for key in path:
        value = value[key]
    assert value == expected


def test_letterbox_cases_cover_both_pad_positions_and_roundings() -> None:
    cases = cases_of("pre.resize.letterbox")
    assert {c["params"]["pad_position"] for c in cases} == {"center", "top_left"}
    assert {c["params"]["rounding"] for c in cases} == {"half_even", "half_up"}


def test_unprojection_scale_conversion_comes_first() -> None:
    """Scale conversion comes before unprojection: 0.5 and 320 give one result."""
    section = "post.unprojection"
    pixel = case_named(section, "pixel-is-the-model-input-position")["expect"]
    assert case_named(section, "normalized-01-centre")["expect"] == pixel
    assert case_named(section, "normalized-11-centre")["expect"] == pixel
    affine = case_named(section, "pixel-affine-person-crop")["expect"]
    assert case_named(section, "normalized-11-affine-person-crop")["expect"] == affine


def test_unprojection_clamp_boxes_defaults_to_true() -> None:
    section = "post.unprojection"
    clamped = case_named(section, "box-clamp-default-is-true")
    assert "clamp_boxes" not in clamped["params"]
    kept = case_named(section, "box-clamp-boxes-false-keeps-negative-values")
    assert kept["params"]["clamp_boxes"] is False


def test_normalize_anchors_come_from_the_published_imagenet_statistics() -> None:
    """The torchvision mean and std (0..1 range) give the 0..255 statistics."""
    mean = np.array([0.485, 0.456, 0.406])  # R, G, B
    std = np.array([0.229, 0.224, 0.225])
    section = "pre.normalize"
    rgb = case_named(section, "imagenet-rgb")
    bgr = case_named(section, "imagenet-bgr")
    legacy = case_named(section, "imagenet-bgr-legacy")
    for index, (b, g, r) in enumerate(rgb["input"]["pixels_bgr"]):
        expected_rgb = (np.array([r, g, b]) / 255 - mean) / std
        expected_bgr = (np.array([b, g, r]) / 255 - mean[::-1]) / std[::-1]
        expected_legacy = (np.array([b, g, r]) / 255 - mean) / std
        assert rgb["expect"]["values"][index] == pytest.approx(expected_rgb, abs=1e-5)
        assert bgr["expect"]["values"][index] == pytest.approx(expected_bgr, abs=1e-5)
        assert legacy["expect"]["values"][index] == pytest.approx(
            expected_legacy, abs=1e-5
        )
    assert bgr["expect"]["values"] != legacy["expect"]["values"]


def test_normalize_channel_order_follows_color_format() -> None:
    section = "pre.normalize"
    pixel = case_named(section, "none-rgb")["input"]["pixels_bgr"][2]  # B, G, R
    assert pixel == [10, 128, 250]
    assert case_named(section, "none-rgb")["expect"]["values"][2] == [250, 128, 10]
    assert case_named(section, "none-bgr")["expect"]["values"][2] == [10, 128, 250]
    assert case_named(section, "unit-float-rgb")["expect"]["values"][1] == [1, 1, 1]
    assert case_named(section, "default-is-imagenet-bgr")["expect"][
        "resolved_mode"
    ] == ("imagenet_bgr")
    assert (
        case_named(section, "precision-override")["expect"]["resolved_mode"] == "none"
    )
    assert case_named(section, "precision-without-override")["expect"][
        "resolved_mode"
    ] == ("unit_float")
    custom_rgb = case_named(section, "custom-rgb")["expect"]["values"]
    custom_bgr = case_named(section, "custom-bgr")["expect"]["values"]
    assert np.allclose(np.array(custom_bgr)[:, ::-1], np.array(custom_rgb), atol=1e-5)


def test_top_k_larger_than_the_candidates_keeps_every_candidate() -> None:
    case = case_named("post.det.selection.top_k", "top-k-larger-than-the-candidates")
    assert len(case["expect"]["scores"]) == 4


# ---------------------------------------------------------------------------
# Properties of the selection results (independent of the greedy algorithm)
# ---------------------------------------------------------------------------


def _iou(a: list[float], b: list[float]) -> float:
    width = min(a[2], b[2]) - max(a[0], b[0])
    height = min(a[3], b[3]) - max(a[1], b[1])
    inter = max(width, 0) * max(height, 0)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union


@pytest.mark.parametrize("case", case_params("post.det.selection.nms"))
def test_nms_result_obeys_the_rules(case: dict[str, Any]) -> None:
    params, expect = case["params"], case["expect"]
    boxes = [
        mv.post_det_decode.to_xyxy(row, params.get("box_format", "xyxy"))
        for row in (
            case["input"].get("boxes") or [r[:4] for r in case["input"]["rows"]]
        )
    ]
    rows, scores, classes = expect["kept_rows"], expect["scores"], expect["class_ids"]
    assert len(rows) == len(set(rows)) == len(scores) == len(classes)
    assert scores == sorted(scores, reverse=True)
    assert all(s > params["score_threshold"] for s in scores)
    assert all(s > params.get("confidence_threshold_default", 0.7) for s in scores)
    if "post_nms_top_k" in params:
        assert len(rows) <= params["post_nms_top_k"]
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if params.get("class_agnostic", False) or classes[i] == classes[j]:
                assert _iou(boxes[rows[i]], boxes[rows[j]]) <= params["iou_threshold"]


@pytest.mark.parametrize("case", case_params("post.det.selection.top_k"))
def test_top_k_result_obeys_the_rules(case: dict[str, Any]) -> None:
    params, expect = case["params"], case["expect"]
    scores = expect["scores"]
    assert len(scores) <= params["top_k"]
    assert scores == sorted(scores, reverse=True)
    assert all(s > params.get("confidence_threshold_default", 0.7) for s in scores)
    pairs = [
        (r, c) for r, c in zip(expect["kept_rows"], expect["class_ids"], strict=True)
    ]
    assert len(pairs) == len(set(pairs))


@pytest.mark.parametrize("case", case_params("post.det.selection.none"))
def test_none_result_obeys_the_rules(case: dict[str, Any]) -> None:
    params, expect = case["params"], case["expect"]
    rows = expect["kept_rows"]
    assert rows == sorted(set(rows))
    assert all(
        s > params.get("confidence_threshold_default", 0.7) for s in expect["scores"]
    )
    if "max_detections" in params:
        # The graph gives a fixed number of rows; the host neither pads nor truncates.
        assert len(case["input"]["rows"]) == params["max_detections"]
        assert len(rows) <= params["max_detections"]


# ---------------------------------------------------------------------------
# The resize unprojection inverts the forward map (checked with OpenCV)
# ---------------------------------------------------------------------------


def _forward_matrix(section: str, case: dict[str, Any]) -> np.ndarray:
    src_w, src_h = case["input"].get("src_w"), case["input"].get("src_h")
    expect = case["expect"]
    if section == "pre.resize.letterbox":
        scale_x, scale_y = expect["n_w"] / src_w, expect["n_h"] / src_h
        return np.array(
            [[scale_x, 0, expect["left"]], [0, scale_y, expect["top"]]], dtype=float
        )
    if section == "pre.resize.stretch":
        return np.array(
            [[expect["scale_x"], 0, 0], [0, expect["scale_y"], 0]], dtype=float
        )
    if section == "pre.resize.fit":
        s = expect["scale"]
        return np.array([[s, 0, expect["left"]], [0, s, expect["top"]]], dtype=float)
    return np.array(expect["matrix"], dtype=float)


UNPROJECTION_SECTIONS = [
    "pre.resize.letterbox",
    "pre.resize.stretch",
    "pre.resize.fit",
    "pre.resize.affine_person_crop",
]


@pytest.mark.parametrize(
    ("section", "case"),
    [
        pytest.param(section, param.values[0], id=f"{section}:{param.id}")
        for section in UNPROJECTION_SECTIONS
        for param in forward_params(section)
    ],
)
def test_unprojection_inverts_the_forward_map(
    section: str, case: dict[str, Any]
) -> None:
    forward = _forward_matrix(section, case)
    inverse = cv2.invertAffineTransform(forward)
    inverse_case = inverse_of(section, case)
    model_x, model_y = inverse_case["input"]["model_xy"]
    source = inverse @ np.array([model_x, model_y, 1.0])
    # `scale`, `left` and `top` are rounded to 6 decimals in the file, so the
    # inverse of the file's matrix differs from `source_xy` by about 1e-5 relative.
    expected = inverse_case["expect"]["source_xy"]
    tolerance = exact_unless_fractional(
        section, case["expect"], inverse_case["input"]["model_xy"], expected
    )
    assert source == pytest.approx(expected, rel=1e-5, abs=tolerance)


# ---------------------------------------------------------------------------
# post.unprojection: the scale, the inverse of the resize and the clamp
# ---------------------------------------------------------------------------

UNPROJECTION = "post.unprojection"
SCALE_RANGES = {"normalized_01": (0.0, 1.0), "normalized_11": (-1.0, 1.0)}


def points_of(values: Any) -> np.ndarray:
    """Return a flat list [x, y] or [x1, y1, x2, y2] as an (N, 2) array."""
    return np.array(values, dtype=float).reshape(-1, 2)


def decoded_points(case: dict[str, Any]) -> np.ndarray:
    data = case["input"]
    return points_of(
        data["decoded_xy"] if "decoded_xy" in data else data["decoded_xyxy"]
    )


def expect_points(case: dict[str, Any], name: str) -> np.ndarray:
    """Return `model_xy` or `model_xyxy` (name `model`), or the `source` pair."""
    expect = case["expect"]
    return points_of(
        expect[f"{name}_xy"] if f"{name}_xy" in expect else expect[f"{name}_xyxy"]
    )


def forward_matrix(case: dict[str, Any]) -> np.ndarray:
    """Return the map from source pixels to model-input pixels, from the resize fields of a case."""
    resize = case["params"]["resize"]
    method = resize["method"]
    if method == "none":
        return np.array([[1, 0, 0], [0, 1, 0]], dtype=float)
    t_h, t_w = resize["target_size"]
    if method == "affine_person_crop":
        x1, y1, x2, y2 = case["input"]["bbox_xyxy"]
        width = (x2 - x1) * resize["expand_ratio"]
        height = (y2 - y1) * resize["expand_ratio"]
        if resize["maintain_aspect_ratio"]:
            if width / height > t_w / t_h:
                height = width * t_h / t_w
            else:
                width = height * t_w / t_h
        scale_x, scale_y = t_w / width, t_h / height
        return np.array(
            [
                [scale_x, 0, t_w / 2 - scale_x * (x1 + x2) / 2],
                [0, scale_y, t_h / 2 - scale_y * (y1 + y2) / 2],
            ]
        )
    src_w, src_h = case["input"]["src_w"], case["input"]["src_h"]
    if method == "stretch":
        return np.array([[t_w / src_w, 0, 0], [0, t_h / src_h, 0]])
    s = min(t_w / src_w, t_h / src_h)
    if method == "fit":
        return np.array([[s, 0, (t_w - src_w * s) / 2], [0, s, (t_h - src_h * s) / 2]])
    assert method == "letterbox"
    if resize["rounding"] == "half_even":
        n_w, n_h = round(src_w * s), round(src_h * s)
    else:
        n_w, n_h = math.floor(src_w * s + 0.5), math.floor(src_h * s + 0.5)
    n_w, n_h = max(1, n_w), max(1, n_h)
    left, top = (
        (0, 0)
        if resize["pad_position"] == "top_left"
        else ((t_w - n_w) // 2, (t_h - n_h) // 2)
    )
    return np.array([[n_w / src_w, 0, left], [0, n_h / src_h, top]])


@pytest.mark.parametrize("case", case_params(UNPROJECTION))
def test_the_decoded_value_is_converted_to_model_input_pixels(
    case: dict[str, Any],
) -> None:
    """`normalized_01` maps [0, 1] and `normalized_11` maps [-1, 1] linearly to [0, size]."""
    in_h, in_w = case["params"]["input_size"]
    decoded = decoded_points(case)
    scale = case["params"]["scale"]
    if scale == "pixel":
        expected = decoded
    else:
        low, high = SCALE_RANGES[scale]
        expected = np.stack(
            [
                np.interp(decoded[:, 0], [low, high], [0, in_w]),
                np.interp(decoded[:, 1], [low, high], [0, in_h]),
            ],
            axis=1,
        )
    assert expect_points(case, "model") == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize("case", case_params(UNPROJECTION))
def test_the_unprojection_inverts_the_resize_of_the_case(case: dict[str, Any]) -> None:
    inverse = cv2.invertAffineTransform(forward_matrix(case))
    model = expect_points(case, "model")
    source = np.hstack([model, np.ones((len(model), 1))]) @ inverse.T
    assert source == pytest.approx(expect_points(case, "source"), abs=1e-6)


BOX_CASES = [
    pytest.param(case, id=case["id"])
    for case in cases_of(UNPROJECTION)
    if "decoded_xyxy" in case["input"]
]


@pytest.mark.parametrize("case", BOX_CASES)
def test_the_output_box_is_the_clamped_source_box_unless_clamp_boxes_is_false(
    case: dict[str, Any],
) -> None:
    expect = case["expect"]
    source = np.array(expect["source_xyxy"], dtype=float)
    if case["params"].get("clamp_boxes", True):
        assert expect["output_xyxy"] == np.maximum(source, 0).tolist()
    else:
        assert expect["output_xyxy"] == expect["source_xyxy"]


@pytest.mark.parametrize("case", BOX_CASES)
def test_no_box_case_depends_on_the_open_questions_of_the_clamp(
    case: dict[str, Any],
) -> None:
    """The spec leaves the upper bound (W or W - 1) and a box without area undefined."""
    source = np.array(case["expect"]["source_xyxy"], dtype=float)
    assert source[0::2].max() <= case["input"]["src_w"] - 1
    assert source[1::2].max() <= case["input"]["src_h"] - 1
    x1, y1, x2, y2 = np.maximum(source, 0)
    assert x2 > x1 and y2 > y1


def test_the_unprojection_cases_cover_every_scale_method_and_clamp_setting() -> None:
    cases = cases_of(UNPROJECTION)
    assert {c["params"]["scale"] for c in cases} == {
        "pixel",
        "normalized_01",
        "normalized_11",
    }
    assert {c["params"]["resize"]["method"] for c in cases} == {
        "letterbox",
        "stretch",
        "fit",
        "none",
        "affine_person_crop",
    }
    boxes = [c for c in cases if "decoded_xyxy" in c["input"]]
    assert {c["params"].get("clamp_boxes") for c in boxes} == {None, True, False}


def test_the_unprojection_file_is_unverified_because_no_function_runs_it() -> None:
    assert "unverified" in load(f"{UNPROJECTION}.yaml")


# ---------------------------------------------------------------------------
# skellytracker functions named in `verified_against`
# ---------------------------------------------------------------------------

SOURCE_VALUE = 200
LETTERBOX_PAD = 114


def package_letterbox_geometry(case: dict[str, Any]) -> dict[str, int] | None:
    """Run `letterbox_preprocess` on a flat image; None when it cannot run the case.

    The function reports only a scale factor, so the geometry is read from the
    padded image: the source value (200) differs from the padding (114).
    """
    function = resolve_function(mv.LETTERBOX_FUNCTION)
    params = case["params"]
    if params["pad_position"] != "top_left":
        return None  # the function has no `center`
    image = np.full(
        (case["input"]["src_h"], case["input"]["src_w"], 3),
        SOURCE_VALUE,
        dtype=np.uint8,
    )
    try:
        padded, _ratio = function(
            image, tuple(params["target_size"]), pad_value=LETTERBOX_PAD
        )
    except cv2.error:
        return None
    covered = (padded != LETTERBOX_PAD).any(axis=2)
    columns, rows = np.flatnonzero(covered.any(axis=0)), np.flatnonzero(
        covered.any(axis=1)
    )
    return {
        "n_w": len(columns),
        "n_h": len(rows),
        "left": int(columns[0]) if len(columns) else 0,
        "top": int(rows[0]) if len(rows) else 0,
    }


@pytest.mark.parametrize("case", forward_params("pre.resize.letterbox"))
def test_letterbox_preprocess_agrees_exactly_where_the_case_says(
    case: dict[str, Any],
) -> None:
    geometry = package_letterbox_geometry(case)
    listed = mv.LETTERBOX_FUNCTION in case.get("verified_against", [])
    if geometry is None:
        assert not listed, "a case the function cannot run is not verified"
    else:
        assert (geometry == case["expect"]) == listed, geometry


def test_letterbox_file_claims_no_more_than_the_function_gives() -> None:
    data = load("pre.resize.letterbox.yaml")
    forward = [param.values[0] for param in forward_params("pre.resize.letterbox")]
    assert not any("verified_against" in c for c in data["cases"] if "function" in c)
    if "verified_against" in data:
        assert all(package_letterbox_geometry(c) == c["expect"] for c in forward)
    else:
        listed = [mv.LETTERBOX_FUNCTION in c.get("verified_against", []) for c in forward]
        assert any(listed), "the function reproduces some cases"
        assert not all(listed), "the function does not reproduce every case"


def _axis_extent(mask_axis: np.ndarray) -> tuple[int, int]:
    indexes = np.flatnonzero(mask_axis)
    return int(indexes[0]), int(indexes[-1])


def test_fit_file_names_its_function() -> None:
    assert load("pre.resize.fit.yaml")["verified_against"] == [mv.FIT_FUNCTION]


@pytest.mark.parametrize("case", forward_params("pre.resize.fit"))
def test_fit_preprocess_agrees_with_the_case(case: dict[str, Any]) -> None:
    function = resolve_function(mv.FIT_FUNCTION)
    t_h, t_w = case["params"]["target_size"]
    src_w, src_h = case["input"]["src_w"], case["input"]["src_h"]
    image = np.full((src_h, src_w, 3), SOURCE_VALUE, dtype=np.uint8)
    padded, (scale, left, top) = function(image, (t_h, t_w), pad_value=0)

    expect = case["expect"]
    inverse_case = inverse_of("pre.resize.fit", case)
    tolerance = exact_unless_fractional(
        "pre.resize.fit", expect, inverse_case["input"]["model_xy"], inverse_case["expect"]
    )
    assert agrees({"scale": scale, "left": left, "top": top}, expect, case, tolerance)

    # The warped image agrees with the reported geometry. The edges blend with
    # the border, so allow the blend zone of one source pixel (`scale` pixels).
    assert padded.shape == (t_h, t_w, 3)
    margin = math.ceil(scale) + 1
    covered = (padded > 0).any(axis=2)
    for axis, size, start, length in ((0, t_w, left, src_w), (1, t_h, top, src_h)):
        first, last = _axis_extent(covered.any(axis=axis))
        low, high = max(start, 0.0), min(start + length * scale, size)
        assert math.floor(low) - margin <= first <= math.ceil(low) + 1
        assert math.floor(high) - 2 <= last <= math.ceil(high) + margin

    # The unprojection is the exact inverse of the warp matrix of the function.
    matrix = np.array([[scale, 0, left], [0, scale, top]], dtype=float)
    model_x, model_y = inverse_case["input"]["model_xy"]
    source = cv2.invertAffineTransform(matrix) @ np.array([model_x, model_y, 1.0])
    assert source == pytest.approx(inverse_case["expect"]["source_xy"], abs=tolerance)

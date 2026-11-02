"""Tests of `make_vectors.py fill` and `make_vectors.py land` (ADR-8DSW, items 5 and 6).

Each test works on copies in `tmp_path`. No test writes `specs/model-sidecar/vectors/`.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

import make_vectors as mv

NAME = "pre.resize.stretch.yaml"
SECTION_FILE = mv.VECTORS_DIR / NAME
FORMULAS = (mv.FORMULAS_DIR / "pre_resize_stretch.py").read_text(encoding="utf-8")


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def strip_expect(data: dict[str, Any]) -> dict[str, Any]:
    return {**data, "cases": [{k: v for k, v in c.items() if k != "expect"} for c in data["cases"]]}


def case(case_id: str, src_w: int, *, shift: float = 0.0, **extra: Any) -> dict[str, Any]:
    """A stretch case of 640 x 640 with the `expect` of the formulas, plus `shift` on scale_x."""
    params, given = {"target_size": [640, 640]}, {"src_w": src_w, "src_h": 1080}
    expect = mv.clean(mv.pre_resize_stretch.run(params, given), digits=6)
    expect["scale_x"] = round(expect["scale_x"] + shift, 6)
    return {"id": case_id, **extra, "params": params, "input": given, "expect": expect}


PART4_KEYS = {"section": "pre.resize.stretch", "tolerance": 0.0001, "unverified": "a test"}


@pytest.fixture
def spec(tmp_path: Path) -> tuple[Path, Path]:
    """A copy of the vectors folder with the stretch file, and an empty landed reference folder."""
    vectors = tmp_path / "spec-vectors"
    vectors.mkdir()
    shutil.copy(SECTION_FILE, vectors / NAME)
    return vectors, tmp_path / "spec-reference"


# ---------------------------------------------------------------------------
# fill
# ---------------------------------------------------------------------------


def test_fill_writes_only_expect_with_the_emitter_of_the_generator(tmp_path: Path) -> None:
    """Without a bundle module, the producer of this checkout gives the bytes of the published file."""
    target = dump(tmp_path / "payload" / "vectors" / NAME, strip_expect(load(SECTION_FILE)))
    assert mv.fill(target, tmp_path / "payload" / "reference") == []
    assert target.read_text(encoding="utf-8") == SECTION_FILE.read_text(encoding="utf-8")


def test_fill_runs_the_bundle_reference_without_the_formula_cross_check(tmp_path: Path) -> None:
    """A proposed reference can differ from the current text: fill writes its values."""
    reference = tmp_path / "payload" / "reference"
    reference.mkdir(parents=True)
    (reference / "pre_resize_stretch.py").write_text(
        f"{FORMULAS}\n_inverse = inverse\n\n\n"
        "def inverse(params, input):\n"
        "    x, y = _inverse(params, input)['source_xy']\n"
        "    return {'source_xy': [x + 0.5, y]}\n",
        encoding="utf-8",
    )
    target = dump(tmp_path / "payload" / "vectors" / NAME, strip_expect(load(SECTION_FILE)))
    assert mv.fill(target, reference) == []
    assert load(target)["cases"][1]["expect"] == {"source_xy": [960.5, 540]}


def test_fill_refuses_a_file_of_this_checkout(tmp_path: Path) -> None:
    before = SECTION_FILE.read_bytes()
    (found,) = mv.fill(SECTION_FILE, tmp_path)
    assert "outside this checkout" in found
    assert SECTION_FILE.read_bytes() == before


def test_fill_reports_a_form_problem_and_writes_nothing(tmp_path: Path) -> None:
    target = dump(tmp_path / "vectors" / NAME, {**strip_expect(load(SECTION_FILE)), "tolerance": -1})
    before = target.read_bytes()
    (found,) = mv.fill(target, tmp_path / "reference")
    assert "tolerance must be a number of 0 or more" in found
    assert target.read_bytes() == before


# ---------------------------------------------------------------------------
# land
# ---------------------------------------------------------------------------


def test_land_replaces_in_place_and_appends_the_new_cases(spec: tuple[Path, Path], tmp_path: Path) -> None:
    vectors, reference = spec
    current = load(vectors / NAME)["cases"]
    current_ids = [c["id"] for c in current]
    replaced = {**current[current_ids.index("portrait-target")], "note": "replaced by part 4"}
    part4 = dump(tmp_path / "part4.yaml", {**PART4_KEYS, "cases": [replaced, case("new-a", 1000)]})
    contribution = dump(tmp_path / "c.yaml", {**PART4_KEYS, "cases": [case("new-b", 800)]})
    assert mv.land(part4, [contribution], ["portrait-target"], vectors, reference) == []
    landed = load(vectors / NAME)
    assert [c["id"] for c in landed["cases"]] == [*current_ids, "new-a", "new-b"]
    assert landed["cases"][current_ids.index("portrait-target")]["note"] == "replaced by part 4"
    # The landed file is the output of the generator.
    assert mv.generate(vectors, reference) == {NAME: (vectors / NAME).read_text(encoding="utf-8")}


@pytest.mark.parametrize("replaces", [[], ["portrait-target", "landscape-to-square"]])
def test_land_needs_replaces_to_equal_the_overlap(
    spec: tuple[Path, Path], tmp_path: Path, replaces: list[str]
) -> None:
    vectors, reference = spec
    before = (vectors / NAME).read_bytes()
    part4 = dump(tmp_path / "part4.yaml", {**PART4_KEYS, "cases": [case("portrait-target", 1920)]})
    (found,) = mv.land(part4, [], replaces, vectors, reference)
    assert "part 4 replaces ['portrait-target']" in found
    assert (vectors / NAME).read_bytes() == before


@pytest.mark.parametrize(
    ("change", "lands"),
    [
        ({}, True),
        ({"verified_against": [{"Some-Exporter": "host.py::stretch"}]}, True),
        ({"shift": 0.00005}, True),  # within the tolerance of the file
        ({"shift": 0.01}, False),
        ({"note": "another note"}, False),
    ],
)
def test_land_needs_a_contribution_case_to_agree_with_the_case_of_its_id(
    spec: tuple[Path, Path], tmp_path: Path, change: dict[str, Any], lands: bool
) -> None:
    vectors, reference = spec
    known = next(c for c in load(vectors / NAME)["cases"] if c["id"] == "landscape-to-square")
    shift = change.pop("shift", 0.0)
    theirs = {**known, **change}
    theirs["expect"] = {**known["expect"], "scale_x": known["expect"]["scale_x"] + shift}
    part4 = dump(tmp_path / "part4.yaml", {**PART4_KEYS, "cases": [case("new-a", 1000)]})
    contribution = dump(tmp_path / "c.yaml", {**PART4_KEYS, "cases": [theirs]})
    found = mv.land(part4, [contribution], [], vectors, reference)
    if lands:
        assert found == []
        assert [c["id"] for c in load(vectors / NAME)["cases"]].count("landscape-to-square") == 1
    else:
        assert found == ["c.yaml: the case landscape-to-square differs from the case with its id"]


def test_land_needs_each_given_expect_to_agree_with_the_landed_producer(
    spec: tuple[Path, Path], tmp_path: Path
) -> None:
    vectors, reference = spec
    before = (vectors / NAME).read_bytes()
    part4 = dump(tmp_path / "part4.yaml", {**PART4_KEYS, "cases": [case("new-a", 1000, shift=0.01)]})
    (found,) = mv.land(part4, [], [], vectors, reference)
    assert found.startswith("new-a: the given expect")
    assert (vectors / NAME).read_bytes() == before


def test_land_refuses_a_file_over_256_kib(spec: tuple[Path, Path], tmp_path: Path) -> None:
    vectors, reference = spec
    before = (vectors / NAME).read_bytes()
    long = case("new-a", 1000, note=" ".join(["word"] * 60_000))
    part4 = dump(tmp_path / "part4.yaml", {**PART4_KEYS, "cases": [long]})
    (found,) = mv.land(part4, [], [], vectors, reference)
    assert "more than 256 KiB" in found
    assert (vectors / NAME).read_bytes() == before


def test_land_reports_a_form_problem_of_each_input(spec: tuple[Path, Path], tmp_path: Path) -> None:
    vectors, reference = spec
    part4 = dump(tmp_path / "part4.yaml", {**PART4_KEYS, "tolerance": -1, "cases": [case("new-a", 1000)]})
    contribution = dump(tmp_path / "c.yaml", {**PART4_KEYS, "section": "pre.resize.fit", "cases": []})
    assert mv.land(part4, [contribution], [], vectors, reference) == [
        "part4.yaml: pre.resize.stretch: tolerance must be a number of 0 or more",
        "c.yaml: not a vector file of the section pre.resize.stretch",
    ]


def test_land_takes_the_file_keys_of_part_4_for_a_new_section(tmp_path: Path) -> None:
    vectors = tmp_path / "spec-vectors"
    vectors.mkdir()
    part4 = dump(tmp_path / "part4.yaml", {**PART4_KEYS, "cases": [case("new-a", 1000)]})
    assert mv.land(part4, [], [], vectors, tmp_path / "spec-reference") == []
    assert load(vectors / NAME) == {**PART4_KEYS, "cases": [case("new-a", 1000)]}

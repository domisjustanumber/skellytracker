"""Write `expect` in each sidecar vector file with the producer of its section.

Each vector file is `specs/model-sidecar/vectors/<section-id>.yaml`. A case is a small
worked example: the inputs of one section's algorithm and the exact expected
output. The vector file is the only source of its cases (ADR-8DSW). A person
writes the other keys. This tool reads each file, computes `expect` of each case
again and writes the file.

The producer of a section is `specs/model-sidecar/reference/<section_module>.py`
when it exists, else the formula module `tools/vector_formulas/<section_module>.py`.
Each formula module is a reading of its section file. A vector that disagrees
with the normative text is a defect of the spec or of the producer: fix one of
them, never the vector alone. When a reference is the producer, the formula
function of the same name must agree with it within the tolerance of the file.

A case is one call: `run` when the case has no `function`. The case
`<id>-inverse` calls the section's Inverse (`function: inverse`) with the input
of the case `<id>` and `model_xy`. A validator case with `function: none` is
data only: no function runs it, and its author writes its `expect`. `expect`
has at most 6 decimals.

The tool calls each case through `outcome`. A function refuses an input with
`ValueError`, and `outcome` writes the refusal as `{error: <rule ID>}` when the
message starts with a rule ID, or as `{error: no-rule}`. A broken case or
formula calls `vector_form.defect`, which stops the tool. A case or a file
declares its claims by name in `checks`; `run_checks` runs each one from the
`CHECKS` of the formula module. Hosts ignore `checks`.

A file has one `tolerance`: compare each fractional number with an absolute
difference of at most this value. Integers must match exactly. A case can give
a tolerance for each field (`compare: {<field>: {atol: ..., period: ...}}`).
A file has either `verified_against` (the list of independent implementations
that produced the same results) or `unverified` (the reason that none did). An
entry is a skellytracker function (`path::function`) or an exporter function
(`{<Exporter repo>: <file>::<function>}`). `tools/tests/test_vectors.py` runs
each skellytracker function through its adapter in `PACKAGE_RUNNERS`.

Usage:
    python tools/make_vectors.py            # write the files
    python tools/make_vectors.py --check    # exit 1 when a file differs
    python tools/make_vectors.py fill <bundle vectors file> --reference <bundle reference folder>
    python tools/make_vectors.py land <part 4 file> [--contribution <file>...] --replaces [<id>...]

`fill` and `land` are items 6 and 5 of ADR-8DSW. Each prints its problems and
exits 1 when it finds one. It writes its file only when it finds none.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import re
import sys
import textwrap
from collections.abc import Callable
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import yaml

import intake_bundle
import sidecar_trace
from vector_form import (
    CASE_KEYS,
    DATA_ONLY,
    NO_RULE,
    CaseDefect,
    agrees,
    defect,
    file_problems,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
VECTORS_DIR = REPO_ROOT / "specs" / "model-sidecar" / "vectors"
REFERENCE_DIR = REPO_ROOT / "specs" / "model-sidecar" / "reference"
FORMULAS_DIR = REPO_ROOT / "tools" / "vector_formulas"
HEADER = (
    "# tools/make_vectors.py writes `expect`. Edit the other keys, then run it.",
    "# Hosts ignore `checks`. The names are the self-checks of the generator.",
)
# The keys of a file, in their order.
FILE_ORDER = ("section", "notes", "tolerance", "checks", "verified_against", "unverified", "cases")

LINE_WIDTH = 100
VECTOR_LIMIT = 256 * 1024
ROUND_DIGITS = 6
# A refusal message that starts with a rule ID names the rule that refuses the input.
LEADING_RULE = re.compile(r"(V-[a-z][a-z0-9_.]*[a-z0-9]-\d+):")
# From this size, a float is always whole; an int of it would write all of its digits.
EXACT_INT_LIMIT = 2.0**53
# The folders that `load_reference` has run, as given (`str(folder)`).
_LOADED_FOLDERS: set[str] = set()


def load_reference(section: str, folder: Path = REFERENCE_DIR) -> ModuleType:
    """Return the reference implementation of `section`.

    The folder is not a Python package and its path has a hyphen, so the file
    is loaded by its path. While the file runs, its folder is on `sys.path`, so
    it can import the module of another section by its name. The module is
    registered under its file name, so an import of it gives the same object.
    """
    path = folder / f"{section.replace('.', '_')}.py"
    spec = spec_from_file_location(path.stem, path)
    # A section name from a vector file can be an absolute path: load only a file of `folder` (ADR-AD33).
    inside = path.parent.resolve() == folder.resolve()
    if spec is None or spec.loader is None or not inside or not path.is_file():
        raise FileNotFoundError(f"{section}: no reference implementation at {path}")
    module = module_from_spec(spec)
    # A module of the same name from another folder (for example a proposal folder) is stale here.
    resolved = folder.resolve()
    for stem in {p.stem for p in folder.glob("*.py")}:
        cached = sys.modules.get(stem)
        cached_file = getattr(cached, "__file__", None) if cached is not None else None
        if cached is not None and (not cached_file or Path(cached_file).resolve().parent != resolved):
            del sys.modules[stem]
    # A module of a folder that this function ran earlier must not stand in for a missing sibling.
    for stem, cached in list(sys.modules.items()):
        where = os.path.dirname(getattr(cached, "__file__", None) or "")
        if where in _LOADED_FOLDERS and where != str(folder):
            del sys.modules[stem]
    _LOADED_FOLDERS.add(str(folder))
    sys.modules[path.stem] = module
    sys.path.insert(0, str(folder))
    try:
        spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[path.stem]
        raise
    finally:
        sys.path.remove(str(folder))
    return module


def outcome(
    function: Callable[..., dict[str, Any]], *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Return the `expect` mapping of one case of a producer function.

    A `ValueError` is a refusal: the result is `{"error": <rule ID>}` when the
    message starts with a rule ID and a colon, else `{"error": "no-rule"}`. Any
    other exception is a defect of the case or of the function, so it stops
    the generator.
    """
    try:
        return function(*args, **kwargs)
    except ValueError as error:
        match = LEADING_RULE.match(str(error))
        return {"error": match.group(1) if match else NO_RULE}


def producer(section: str, folder: Path = REFERENCE_DIR) -> ModuleType:
    """Return the reference of `section` in `folder`, else its formula module."""
    module = globals().get(section.replace(".", "_"))
    if isinstance(module, ModuleType) and not (folder / f"{module.__name__}.py").is_file():
        return module
    return load_reference(section, folder)


# The formula modules load like reference modules, so they import each other by name.
# A module loads before the modules that import it, so each name has one module object.
post_det_decode = load_reference("post.det.decode", FORMULAS_DIR)
pre_resize_letterbox = load_reference("pre.resize.letterbox", FORMULAS_DIR)
pre_resize_stretch = load_reference("pre.resize.stretch", FORMULAS_DIR)
pre_resize_fit = load_reference("pre.resize.fit", FORMULAS_DIR)
pre_resize_affine_person_crop = load_reference("pre.resize.affine_person_crop", FORMULAS_DIR)
pre_normalize = load_reference("pre.normalize", FORMULAS_DIR)
post_det_selection_none = load_reference("post.det.selection.none", FORMULAS_DIR)
post_det_selection_top_k = load_reference("post.det.selection.top_k", FORMULAS_DIR)
post_det_selection_nms = load_reference("post.det.selection.nms", FORMULAS_DIR)
post_unprojection = load_reference("post.unprojection", FORMULAS_DIR)


def clean(value: Any, *, digits: int | None = None) -> Any:
    """Return `value` as plain data; a whole float becomes an int.

    With `digits`, a fraction is rounded to that many decimals. Without it,
    a float keeps its exact value (inputs and parameters are never rounded).
    NaN and infinity stay as they are.
    """
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not math.isfinite(number):
            return number
        if digits is not None:
            number = round(number, digits)
        if abs(number) >= EXACT_INT_LIMIT:
            return number
        return int(number) if number == int(number) else number
    if isinstance(value, dict):
        return {str(k): clean(item, digits=digits) for k, item in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [clean(item, digits=digits) for item in value]
    raise TypeError(f"cannot write {type(value).__name__}")




# ---------------------------------------------------------------------------
# YAML writer (the vector files use a small, fixed layout)
# ---------------------------------------------------------------------------

_PLAIN = re.compile(r"[A-Za-z_][A-Za-z0-9_.\-/]*(::[A-Za-z_][A-Za-z0-9_]*)?")
_RESERVED = {"y", "n", "yes", "no", "on", "off", "true", "false", "null"}


def _float_text(number: float) -> str:
    """Write a float with its shortest exact digits.

    A float of 2**53 or more is written with an exponent, for example
    `1.0e+308`; YAML 1.1 needs the dot. Other floats have no exponent.
    """
    if math.isnan(number):
        return ".nan"
    if math.isinf(number):
        return ".inf" if number > 0 else "-.inf"
    text = repr(number)
    if abs(number) >= EXACT_INT_LIMIT and "e" in text:
        mantissa, _, exponent = text.partition("e")
        return f"{mantissa if '.' in mantissa else mantissa + '.0'}e{exponent}"
    if "e" in text or "E" in text:
        text = format(Decimal(text), "f")
    return text if "." in text else text + ".0"


def _scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _float_text(value)
    if isinstance(value, str):
        if _PLAIN.fullmatch(value) and value.lower() not in _RESERVED:
            return value
        return json.dumps(value)
    raise TypeError(f"cannot write {type(value).__name__}")


def _flow(value: Any) -> str:
    if isinstance(value, dict):
        items = ", ".join(f"{_scalar(k)}: {_flow(v)}" for k, v in value.items())
        return "{" + items + "}"
    if isinstance(value, list):
        return "[" + ", ".join(_flow(item) for item in value) + "]"
    return _scalar(value)


def _entry(key: str, value: Any, indent: int) -> list[str]:
    """Return the lines of `key: value`; use a block when the flow form is too long."""
    pad = " " * indent
    line = f"{pad}{key}: {_flow(value)}"
    block_list = isinstance(value, list) and key == "verified_against"
    if not block_list and (
        len(line) <= LINE_WIDTH or not isinstance(value, (dict, list)) or not value
    ):
        return [line]
    lines = [f"{pad}{key}:"]
    if isinstance(value, dict):
        for sub_key, sub_value in value.items():
            lines.extend(_entry(_scalar(sub_key), sub_value, indent + 2))
        return lines
    for item in value:
        lines.extend(_item(item, indent + 2))
    return lines


def _item(value: Any, indent: int) -> list[str]:
    """Return the lines of one list item; use a block when the flow form is too long."""
    pad = " " * indent
    line = f"{pad}- {_flow(value)}"
    if len(line) <= LINE_WIDTH or not isinstance(value, (dict, list)) or not value:
        return [line]
    lines: list[str] = []
    if isinstance(value, dict):
        for sub_key, sub_value in value.items():
            lines.extend(_entry(_scalar(sub_key), sub_value, indent + 2))
    else:
        for sub_item in value:
            lines.extend(_item(sub_item, indent + 2))
    lines[0] = f"{pad}- {lines[0][indent + 2 :]}"
    return lines


def _string_entry(head: str, text: str, indent: int = 0) -> list[str]:
    """Write `head` and a double-quoted string, folded over several lines when it is long."""
    pad = " " * indent
    quoted = json.dumps(text)
    if len(f"{pad}{head}{quoted}") <= LINE_WIDTH:
        return [f"{pad}{head}{quoted}"]
    body = textwrap.wrap(
        quoted[1:-1],
        width=LINE_WIDTH - 16,
        break_long_words=False,
        break_on_hyphens=False,
    )
    if " ".join(body) != quoted[1:-1]:  # a fold would lose a double, first or last space
        return [f"{pad}{head}{quoted}"]
    lines = [f'{pad}{head}"{body[0]}'] + [f"{pad}  {part}" for part in body[1:]]
    lines[-1] += '"'
    return lines



def _ordered(data: dict[str, Any], order: tuple[str, ...], optional: tuple[str, ...]) -> dict[str, Any]:
    """Return `data` with its keys in `order`, then the keys out of `order`.

    An `optional` key with an empty value or None goes, so that a run can read its own file again.
    """
    keys = [key for key in order if key in data] + [key for key in data if key not in order]
    return {key: data[key] for key in keys if not (key in optional and not data[key])}


def form(data: dict[str, Any]) -> dict[str, Any]:
    """Return the data of a vector file as the renderer writes it.

    The keys get the form order, and an empty `notes`, `checks` or case
    `verified_against` goes. `params`, `input` and `compare` become plain data,
    and `expect` gets 6 decimals. `vector_form.file_problems` checks the form.
    """
    out = _ordered(data, FILE_ORDER, ("notes", "checks"))
    out["cases"] = []
    for case in data["cases"]:
        written = _ordered(case, CASE_KEYS, ("checks", "verified_against"))
        for key in ("params", "input", "compare"):
            if key in written:
                written[key] = clean(written[key])
        if "expect" in written:
            written["expect"] = clean(written["expect"], digits=ROUND_DIGITS)
        out["cases"].append(written)
    return out


def render(data: dict[str, Any]) -> str:
    """Return the text of the YAML file for the data of a vector file (see `form`)."""
    data = form(data)
    lines = [*HEADER, f"section: {_scalar(data['section'])}"]
    if "notes" in data:
        lines.append("notes:")
        for note in data["notes"]:
            lines.extend(_string_entry("- ", note, 2))
    lines.append(f"tolerance: {_scalar(data['tolerance'])}")
    if "checks" in data:
        lines.extend(_entry("checks", data["checks"], 0))
    if "verified_against" in data:
        lines.extend(_entry("verified_against", data["verified_against"], 0))
    else:
        lines.extend(_string_entry("unverified: ", data["unverified"]))
    lines.append("cases:")
    for case_data in data["cases"]:
        lines.append(f"  - id: {_scalar(case_data['id'])}")
        for key, value in case_data.items():
            if key == "note":
                lines.extend(_string_entry("note: ", value, 4))
            elif key != "id":
                lines.extend(_entry(key, value, 4))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_checks(
    module: ModuleType,
    case: dict[str, Any],
    file_checks: list[str] | None = None,
    source: ModuleType | None = None,
) -> None:
    """Run each check that `case` or its file names, from the `CHECKS` of its formula module.

    A check is `check(function, params, input, expect)`, where `function` is
    the function of the case in `source` (the producer; `module` when not
    given), and calls `defect` when its claim fails. The built-in check
    `refused` claims an error result: an error result without it, or
    `refused` without an error result, is a defect.
    """
    case_id = case["id"]
    checks = [*(file_checks or []), *case.get("checks", [])]
    if ("error" in case["expect"]) != ("refused" in checks):
        defect(f"{case_id}: an error result needs the check refused, and only it")
    registry = getattr(module, "CHECKS", {})
    function = getattr(source or module, case.get("function", "run"), None)
    for name in checks:
        if name == "refused":
            continue
        if name not in registry:
            defect(f"{case_id}: {module.__name__} has no check {name}")
        try:
            registry[name](function, case["params"], case["input"], case["expect"])
        except CaseDefect as error:
            defect(f"{case_id}: {name}: {error}")


def rule_ids() -> frozenset[str]:
    """Return every rule ID that a section file defines."""
    sections = sidecar_trace.load_sections()
    return frozenset(rule for section in sections for rule in sidecar_trace.section_rules(section))


def package_function(reference: str) -> Any:
    """Return the skellytracker function named by `skellytracker/<path>.py::function`, else None.

    The entry can come from a bundle or a record, and this checkout is on `sys.path`. So the
    function imports only package code, never a file of `intakes/` or of a record (ADR-AD33).
    """
    path, _, name = reference.partition("::")
    if not path.startswith("skellytracker/") or ".." in path or not (REPO_ROOT / path).is_file():
        return None
    module = importlib.import_module(Path(path).with_suffix("").as_posix().replace("/", "."))
    return getattr(module, name, None)


def run_file(
    data: dict[str, Any],
    folder: Path = REFERENCE_DIR,
    *,
    rules: frozenset[str] | set[str] | None = None,
    cross_check: bool = True,
) -> dict[str, Any]:
    """Return the data of a vector file with the `expect` of each case computed again.

    The producer of the section (`producer(section, folder)`) runs each case,
    except a `function: none` case, which keeps its `expect`. When a reference
    is the producer, the formula function of the same name, if any, must agree
    with it within the file tolerance and the `compare` of the case. Then
    `vector_form.file_problems` checks the form, and the checks of the file and
    of the case run. The result is in the form of `form`. `rules` replaces
    `rule_ids()`, and `cross_check=False` skips the formula comparison (`fill`).
    """
    section = data["section"]
    source = producer(section, folder)
    formulas = globals().get(section.replace(".", "_"))  # None: the section has only a reference
    cases = []
    for given in data["cases"]:
        case = dict(given)
        name = case.get("function", "run")
        if name != DATA_ONLY:
            function = getattr(source, name, None)
            if not callable(function):
                defect(f"{case['id']}: no function {name} in {source.__name__}")
            case["expect"] = outcome(function, case["params"], case["input"])
            formula = getattr(formulas, name, None)
            if cross_check and source is not formulas and callable(formula):
                computed = outcome(formula, case["params"], case["input"])
                if not agrees(clean(case["expect"]), clean(computed), case, data["tolerance"]):
                    defect(f"{case['id']}: the reference and the formulas disagree")
        elif "expect" not in case:
            defect(f"{case['id']}: a case with function none needs the expect of its author")
        cases.append(case)
    out = form({**data, "cases": cases})
    found = file_problems(
        out,
        rule_ids() if rules is None else rules,
        reference=lambda: source,
        package_function=package_function,
    )
    if found:
        defect("; ".join(found))
    for case in out["cases"]:
        run_checks(formulas or source, case, out.get("checks"), source)
    return out


def generate(
    vectors_dir: Path = VECTORS_DIR, folder: Path = REFERENCE_DIR
) -> dict[str, str]:
    """Return the text of every vector file in `vectors_dir`, keyed by file name."""
    texts = {}
    for path in sorted(vectors_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if f"{data.get('section')}.yaml" != path.name:
            defect(f"{path.name}: the file holds section {data.get('section')}")
        texts[path.name] = render(run_file(data, folder))
    return texts


def _load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def fill(path: Path, reference: Path) -> list[str]:
    """Write `expect` in one bundle vector file with the bundle reference (ADR-8DSW, item 6).

    The producer is `<reference>/<section_module>.py`, else the producer of this
    checkout. The rule IDs are those of the section files and of part 2.4 of the
    `proposal.md` next to the reference folder. A proposed reference can differ
    from the current text, so no formula module cross-checks it. The tool writes
    only `path`, never a file of this checkout. It runs the code of `reference`,
    so it refuses a folder of this checkout, for example a bundle in `intakes/`
    or a record, and a folder that is not the `reference/` folder of the payload
    of `path` (ADR-AD33, item 5). Return the problems.
    """
    path, reference = path.resolve(), reference.resolve()
    if path.is_relative_to(REPO_ROOT):
        return [f"{path}: fill writes only a vector file of a payload folder outside this checkout"]
    if reference.is_relative_to(REPO_ROOT):
        return [f"{reference}: fill runs only the reference folder of a payload outside this checkout"]
    if reference != path.parent.parent / "reference":
        return [f"{reference}: fill runs only <payload>/reference of the payload of {path.name}"]
    data = _load(path)
    if not (isinstance(data, dict) and isinstance(data.get("section"), str)):
        return [f"{path.name}: a vector file names its section"]
    section = data["section"]
    module = reference / f"{section.replace('.', '_')}.py"
    folder = reference if module.is_file() else REFERENCE_DIR
    rules = set(rule_ids())
    # shortcut: a contribution has no proposal.md, so it cannot use a new rule ID of its owner yet.
    proposal = reference.parent / "proposal.md"
    if proposal.is_file():
        text = proposal.read_text(encoding="utf-8", errors="replace")
        rules.update(intake_bundle.RULE_ID.findall("".join(intake_bundle.PART_2_4.findall(text))))
    sys.path.append(str(REFERENCE_DIR))  # a bundle module can import a landed module
    try:
        out = run_file(data, folder, rules=rules, cross_check=False)
    except CaseDefect as error:
        return [f"{path.name}: {error}"]
    finally:
        sys.path.remove(str(REFERENCE_DIR))
    path.write_text(render(out), encoding="utf-8", newline="\n")
    return []


UNVERIFIED_SOME = (
    "The independent implementations ran only some cases. Each of these cases lists them in "
    "verified_against."
)


def place_verified(
    current: dict[str, Any],
    part4: dict[str, Any],
    contributions: list[dict[str, Any]],
    cases: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return the file keys and the `cases` with each `verified_against` entry on the cases it covers.

    A file-level entry covers each case of its file, and a case-level entry covers its case. The
    entries of `current` cover only the current cases that part 4 keeps. An entry that covers each
    case of `cases` is file-level, in the order that the entries come. Each other entry is
    case-level. Without a file-level entry, the file needs `unverified`. When no case lists an
    entry, it is that of `current`, else of part 4. Otherwise it is that of `current` or of part 4
    only when that file has a case-level entry, because only then does its text tell of a partial
    verification. Else it is `UNVERIFIED_SOME`.
    """
    covers: dict[str, list[Any]] = {}
    order: list[Any] = []
    replaced = {case["id"] for case in part4["cases"]}
    kept = {**current, "cases": [case for case in current["cases"] if case["id"] not in replaced]}
    for data in (kept, part4, *contributions):
        for case in data["cases"]:
            for entry in [*data.get("verified_against", []), *case.get("verified_against", [])]:
                for found in (covers.setdefault(case["id"], []), order):
                    if entry not in found:  # entries compare by value
                        found.append(entry)
    shared = [entry for entry in order if all(entry in covers.get(case["id"], []) for case in cases)]
    keys = {key: value for key, value in current.items() if key not in ("verified_against", "unverified")}
    placed = [
        {**case, "verified_against": [e for e in covers.get(case["id"], []) if e not in shared]}
        for case in cases
    ]  # `form` drops an empty case `verified_against`

    def partial(data: dict[str, Any]) -> str | None:
        return data.get("unverified") if any(c.get("verified_against") for c in data["cases"]) else None

    if shared:
        keys["verified_against"] = shared
    elif any(case["verified_against"] for case in placed):
        keys["unverified"] = partial(current) or partial(part4) or UNVERIFIED_SOME
    else:
        keys["unverified"] = current.get("unverified") or part4.get("unverified")
    return keys, placed


def land(
    part4: Path,
    contributions: list[Path],
    replaces: list[str],
    vectors_dir: Path = VECTORS_DIR,
    folder: Path = REFERENCE_DIR,
) -> list[str]:
    """Land the vectors of an accepted proposal: Procedure B step 9 (ADR-8DSW, item 5).

    The current cases come first. A part 4 case takes the place of the case with
    its id, and these ids must be `replaces`. A contribution case with a known id
    must agree with that case, `verified_against` aside. Each other case goes at
    the end, part 4 first. The file-level keys are those of the current file
    (of part 4 for a new section), except that `place_verified` puts each
    `verified_against` entry on the cases it covers. The landed producer computes each `expect`
    again, and each given `expect` must agree with it. The tool writes
    `<vectors_dir>/<section>.yaml` only when it finds no problem and the file is
    256 KiB or smaller. Return the problems.
    """
    files = [part4, *contributions]
    inputs = [_load(path) for path in files]
    if not (isinstance(inputs[0], dict) and isinstance(inputs[0].get("section"), str)):
        return [f"{part4.name}: a vector file names its section"]
    section = inputs[0]["section"]
    rules = rule_ids()
    found = []
    for path, data in zip(files, inputs):  # noqa: B905 (one data for each file)
        if not (isinstance(data, dict) and data.get("section") == section):
            found.append(f"{path.name}: not a vector file of the section {section}")
            continue
        found += [
            f"{path.name}: {problem}"
            for problem in file_problems(
                data,
                rules,
                reference=lambda: producer(section, folder),
                package_function=package_function,
            )
        ]
    if found:
        return found

    target = vectors_dir / f"{section}.yaml"
    current = _load(target) if target.is_file() else {**inputs[0], "cases": []}
    cases = list(current["cases"])
    index = {case["id"]: n for n, case in enumerate(cases)}
    overlap = sorted(set(index) & {case["id"] for case in inputs[0]["cases"]})
    if overlap != sorted(set(replaces)):
        found.append(f"{part4.name}: part 4 replaces {overlap}, --replaces gives {sorted(set(replaces))}")
    incoming = set()
    for n, data in enumerate(inputs):
        for case in data["cases"]:
            if n == 0 or case["id"] not in index:
                if case["id"] not in index:
                    index[case["id"]] = len(cases)
                    cases.append(case)
                cases[index[case["id"]]] = case
                incoming.add(case["id"])
            elif not intake_bundle._same_case(case, cases[index[case["id"]]], current["tolerance"]):
                found.append(f"{files[n].name}: the case {case['id']} differs from the case with its id")
    if found:
        return found
    keys, cases = place_verified(current, inputs[0], inputs[1:], cases)

    # The producer writes each incoming `expect` again. Only the author writes a `function: none` one.
    stripped = [
        {key: value for key, value in case.items() if key != "expect"}
        if case["id"] in incoming and case.get("function") != DATA_ONLY
        else case
        for case in cases
    ]
    try:
        out = run_file({**keys, "cases": stripped}, folder)
    except CaseDefect as error:
        return [str(error)]
    found = [
        f"{given['id']}: the given expect {given['expect']} differs from the landed producer: "
        f"{computed['expect']}"
        for given, computed in zip(cases, out["cases"])  # noqa: B905 (run_file keeps each case)
        if not agrees(given["expect"], computed["expect"], computed, out["tolerance"])
    ]
    text = render(out)
    size = len(text.encode("utf-8"))
    if size > VECTOR_LIMIT:
        found.append(f"{target.name}: the landed file has {size} bytes, more than 256 KiB")
    if not found:
        target.write_text(text, encoding="utf-8", newline="\n")
    return found


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="exit 1 when a file differs"
    )
    parser.add_argument("--out", type=Path, default=VECTORS_DIR, help="output folder")
    commands = parser.add_subparsers(dest="command")
    fill_command = commands.add_parser("fill", help="write expect in a bundle vector file")
    fill_command.add_argument("file", type=Path, help="vectors/<section ID>.yaml of a payload folder")
    fill_command.add_argument(
        "--reference", type=Path, required=True, help="the reference folder of the payload"
    )
    land_command = commands.add_parser("land", help="land the vectors of an accepted proposal")
    land_command.add_argument("part4", type=Path, help="the part 4 vector file of the record")
    land_command.add_argument("--contribution", type=Path, nargs="+", action="extend", default=[])
    land_command.add_argument(
        "--replaces", nargs="*", required=True, help="each current id that part 4 replaces"
    )
    args = parser.parse_args(argv[1:])

    if args.command:
        if args.command == "fill":
            found = fill(args.file, args.reference)
        else:
            found = land(args.part4, args.contribution, args.replaces)
        print("\n".join(found) or f"{args.command}: no problems")
        return 1 if found else 0

    texts = generate()
    if args.check:
        stale = [
            name
            for name, text in texts.items()
            if not (args.out / name).is_file()
            or (args.out / name).read_text(encoding="utf-8") != text
        ]
        print("\n".join(f"differs: {name}" for name in stale) or "vectors are current")
        return 1 if stale else 0

    args.out.mkdir(parents=True, exist_ok=True)
    for name, text in texts.items():
        (args.out / name).write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {len(texts)} files to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

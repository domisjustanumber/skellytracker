"""Write the sidecar test vectors from the normative formulas of the section files.

Each vector file is `specs/model-sidecar/vectors/<section-id>.yaml`. A case is a small
worked example: the inputs of one section's algorithm and the exact expected
output. The formulas in this file are copies of the formulas in the section
files. A vector that disagrees with the normative text is a defect of the spec
or of this file: fix one of them, never the vector alone.

A file has either `verified_against` (the list of independent implementations
that produced the same results) or `unverified` (the reason that none did). An
entry is a skellytracker function (`path::function`) or an exporter function
(`{<Exporter repo>: <file>::<function>}`). A case may list its own
`verified_against`. Only a test may add such a list: see
`tools/tests/test_vectors.py`, which runs the skellytracker functions.

When a section has a reference implementation
(`specs/model-sidecar/reference/<section_module>.py`), its builder calls it
through `load_reference` instead of a copy of the formulas. A case then names
the function that it runs (`function`). A builder calls a reference function
through `outcome`. A reference function refuses an input with `ValueError`, and
`outcome` writes the refusal as `{error: <rule ID>}` when the message starts
with a rule ID, or as `{error: no-rule}`. A validator case expects
`{failed: [<rule IDs>]}`. A case can give a tolerance for each field
(`compare: {<field>: {atol: ..., period: ...}}`).

Usage:
    python tools/make_vectors.py            # write the files
    python tools/make_vectors.py --check    # exit 1 when a file differs
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import textwrap
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
VECTORS_DIR = REPO_ROOT / "specs" / "model-sidecar" / "vectors"
REFERENCE_DIR = REPO_ROOT / "specs" / "model-sidecar" / "reference"
SPEC_REVISION = "vNEXT"
GENERATED_BY = "tools/make_vectors.py"

LETTERBOX_FUNCTION = "skellytracker/core/detectors/processing/image_preprocessing.py::letterbox_preprocess"
FIT_FUNCTION = (
    "skellytracker/core/detectors/processing/image_preprocessing.py::fit_preprocess"
)

# `letterbox_preprocess` supports only `pad_position: top_left`, and it cuts the
# scaled size with `int()`. These top-left cases give the same geometry with it.
# `test_vectors.py` runs the function and fails when this list is not exact.
LETTERBOX_PACKAGE_MATCHES: frozenset[str] = frozenset(
    {
        "top-left-half-up-landscape",
        "top-left-half-even-landscape",
        "top-left-half-even-portrait",
        "top-left-rounding-tie-half-even",
        "top-left-fraction-below-half",
        "top-left-scale-exactly-one",
        "top-left-upscale",
        "top-left-one-pixel-wide-source",
    }
)

LINE_WIDTH = 100
ROUND_DIGITS = 6
COMPARE_KEYS = {"atol", "period"}
NO_RULE = "no-rule"
# A refusal message that starts with a rule ID names the rule that refuses the input.
LEADING_RULE = re.compile(r"(V-[a-z][a-z0-9_.]*[a-z0-9]-\d+):")
# From this size, a float is always whole; an int of it would write all of its digits.
EXACT_INT_LIMIT = 2.0**53


def load_reference(section: str, folder: Path = REFERENCE_DIR) -> ModuleType:
    """Return the reference implementation of `section`.

    The folder is not a Python package and its path has a hyphen, so the file
    is loaded by its path. While the file runs, its folder is on `sys.path`, so
    it can import the module of another section by its name. The module is
    registered under its file name, so an import of it gives the same object.
    """
    path = folder / f"{section.replace('.', '_')}.py"
    spec = spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None or not path.is_file():
        raise FileNotFoundError(f"{section}: no reference implementation at {path}")
    module = module_from_spec(spec)
    # A module of the same name from another folder (for example a proposal folder) is stale here.
    resolved = folder.resolve()
    for stem in {p.stem for p in folder.glob("*.py")}:
        cached = sys.modules.get(stem)
        cached_file = getattr(cached, "__file__", None) if cached is not None else None
        if cached is not None and (not cached_file or Path(cached_file).resolve().parent != resolved):
            del sys.modules[stem]
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
    """Return the `expect` mapping of one case of a reference function.

    A `ValueError` is a refusal: the result is `{"error": <rule ID>}` when the
    message starts with a rule ID and a colon, else `{"error": "no-rule"}`. Any
    other exception is a defect of the builder or of the function, so it stops
    the generator.
    """
    try:
        return function(*args, **kwargs)
    except ValueError as error:
        match = LEADING_RULE.match(str(error))
        return {"error": match.group(1) if match else NO_RULE}


# Absolute tolerance of the cases that hold fractional numbers.
TOLERANCE = {"resize": 1e-4, "unprojection": 1e-4, "normalize": 1e-5, "selection": 1e-5}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


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


def has_fraction(value: Any) -> bool:
    """Return True when `value` holds a number with a fractional part."""
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(has_fraction(item) for item in value.values())
    if isinstance(value, list):
        return any(has_fraction(item) for item in value)
    return False


def require(condition: bool, message: str) -> None:
    """Raise when a case does not show the edge that its id claims."""
    if not condition:
        raise ValueError(message)


@dataclass
class Case:
    id: str
    params: dict[str, Any]
    input: dict[str, Any]
    expect: dict[str, Any]
    unproject: dict[str, Any] | None = None
    verified_against: list[str | dict[str, str]] | None = None
    note: str | None = None  # written as a YAML comment, not as data
    function: str | None = None  # the function of the reference implementation
    compare: dict[str, dict[str, float]] | None = None  # per-field atol and period

    def data(
        self, tolerance: float, digits: int | None = ROUND_DIGITS
    ) -> dict[str, Any]:
        out: dict[str, Any] = {"id": self.id}
        if self.function is not None:
            out["function"] = self.function
        out["params"] = clean(self.params)
        out["input"] = clean(self.input)
        out["expect"] = clean(self.expect, digits=digits)
        if self.unproject is not None:
            out["unproject"] = clean(self.unproject, digits=digits)
        if has_fraction(out["expect"]) or has_fraction(out.get("unproject")):
            out["tolerance"] = tolerance
        if self.compare is not None:
            out["compare"] = clean(self.compare)
        if self.verified_against:
            out["verified_against"] = list(self.verified_against)
        return out


@dataclass
class Vectors:
    section: str
    reading_notes: list[str]
    cases: list[Case]
    tolerance: float
    verified_against: list[str | dict[str, str]] | None = None
    unverified: str | None = None
    digits: int | None = ROUND_DIGITS  # None writes each expected value exactly

    def data(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "section": self.section,
            "spec_revision": SPEC_REVISION,
            "generated_by": GENERATED_BY,
        }
        if (self.verified_against is None) == (self.unverified is None):
            raise ValueError(f"{self.section}: give verified_against or unverified")
        if self.verified_against is not None:
            out["verified_against"] = list(self.verified_against)
        else:
            out["unverified"] = self.unverified
        ids = [case.id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{self.section}: duplicate case id")
        out["cases"] = [case.data(self.tolerance, self.digits) for case in self.cases]
        return out


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


def _string_entry(key: str, text: str) -> list[str]:
    """Write a long string as a double-quoted scalar folded over several lines."""
    quoted = json.dumps(text)
    if len(f"{key}: {quoted}") <= LINE_WIDTH:
        return [f"{key}: {quoted}"]
    body = textwrap.wrap(
        quoted[1:-1],
        width=LINE_WIDTH - 16,
        break_long_words=False,
        break_on_hyphens=False,
    )
    lines = [f'{key}: "{body[0]}'] + [f"  {part}" for part in body[1:]]
    lines[-1] += '"'
    return lines


def _comment_lines(text: str, indent: int) -> list[str]:
    pad = " " * indent
    width = LINE_WIDTH - indent - 2
    parts = textwrap.wrap(
        text, width=width, break_long_words=False, break_on_hyphens=False
    )
    return [f"{pad}# {part}" for part in parts]


def render(vectors: Vectors) -> str:
    """Return the text of the YAML file for `vectors`."""
    data = vectors.data()
    lines = [
        f"# Test vectors for the section `{vectors.section}`.",
        f"# Generated by {GENERATED_BY}. Do not edit this file by hand.",
        "# A case with fractional numbers gives a `tolerance`. Compare each fractional number",
        "# with an absolute difference of at most this value. Integers must match exactly.",
    ]
    for note in vectors.reading_notes:
        lines.extend(_comment_lines(note, 0))
    lines.extend(
        f"{key}: {_scalar(data[key])}"
        for key in ("section", "spec_revision", "generated_by")
    )
    if "verified_against" in data:
        lines.extend(_entry("verified_against", data["verified_against"], 0))
    else:
        lines.extend(_string_entry("unverified", data["unverified"]))
    lines.append("cases:")
    for case, case_data in zip(vectors.cases, data["cases"], strict=True):
        head = f"  - id: {_scalar(case_data['id'])}"
        trailing = f"{head}  # {case.note}" if case.note else head
        if case.note and len(trailing) > LINE_WIDTH:
            lines.append(head)
            lines.extend(_comment_lines(case.note, 4))
        else:
            lines.append(trailing)
        for key, value in case_data.items():
            if key != "id":
                lines.extend(_entry(key, value, 4))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# pre.resize.letterbox
# ---------------------------------------------------------------------------


def _round_half_even(x: float) -> int:
    return round(x)  # Python `round`: ties go to the even integer


def _round_half_up(x: float) -> int:
    return math.floor(x + 0.5)


ROUNDING: dict[str, Callable[[float], int]] = {
    "half_even": _round_half_even,
    "half_up": _round_half_up,
}


def letterbox_geometry(
    src_w: int,
    src_h: int,
    target_size: list[int],
    pad_position: str,
    rounding: str,
) -> dict[str, int]:
    """Section `pre.resize.letterbox`, Behaviour."""
    t_h, t_w = target_size
    s = min(t_w / src_w, t_h / src_h)
    round_ = ROUNDING[rounding]
    n_w = max(1, round_(src_w * s))
    n_h = max(1, round_(src_h * s))
    if pad_position == "top_left":
        left, top = 0, 0
    elif pad_position == "center":
        left, top = math.floor((t_w - n_w) / 2), math.floor((t_h - n_h) / 2)
    else:
        raise ValueError(f"unknown pad_position {pad_position!r}")
    require(n_w <= t_w and n_h <= t_h, "resized image is larger than the target")
    return {"n_w": n_w, "n_h": n_h, "left": left, "top": top}


def letterbox_unproject(
    geometry: dict[str, int], src_w: int, src_h: int, model_xy: list[float]
) -> list[float]:
    """Section `pre.resize.letterbox`, Inverse."""
    x, y = model_xy
    return [
        (x - geometry["left"]) * src_w / geometry["n_w"],
        (y - geometry["top"]) * src_h / geometry["n_h"],
    ]


def _letterbox_case(
    case_id: str,
    target: list[int],
    src: tuple[int, int],
    pad: str,
    rounding: str,
    model_xy: list[float],
    note: str | None = None,
) -> Case:
    src_w, src_h = src
    geometry = letterbox_geometry(src_w, src_h, target, pad, rounding)
    return Case(
        id=case_id,
        params={"target_size": target, "pad_position": pad, "rounding": rounding},
        input={"src_w": src_w, "src_h": src_h},
        expect=geometry,
        unproject={
            "model_xy": model_xy,
            "source_xy": letterbox_unproject(geometry, src_w, src_h, model_xy),
        },
        verified_against=(
            [LETTERBOX_FUNCTION] if case_id in LETTERBOX_PACKAGE_MATCHES else None
        ),
        note=note,
    )


def _other_rounding(rounding: str) -> str:
    return "half_up" if rounding == "half_even" else "half_even"


def build_letterbox() -> Vectors:
    sq = [640, 640]
    cases: list[Case] = []

    def add(*args: Any, differs_by_rounding: bool | None = None, **kwargs: Any) -> None:
        case = _letterbox_case(*args, **kwargs)
        if differs_by_rounding is not None:
            other = letterbox_geometry(
                case.input["src_w"],
                case.input["src_h"],
                case.params["target_size"],
                case.params["pad_position"],
                _other_rounding(case.params["rounding"]),
            )
            require(
                (other != case.expect) == differs_by_rounding,
                f"{case.id}: the rounding modes do not behave as the case says",
            )
        cases.append(case)

    # Center padding.
    add(
        "center-half-even-landscape",
        sq,
        (1920, 1080),
        "center",
        "half_even",
        [320, 320],
        "s = 1/3; the image fills the width and sits in the middle of the height",
    )
    add(
        "center-half-even-portrait",
        sq,
        (1080, 1920),
        "center",
        "half_even",
        [320, 100],
        "the padding is on the left and right",
    )
    add(
        "center-odd-remainder-bottom",
        sq,
        (640, 479),
        "center",
        "half_even",
        [10.5, 80],
        "161 rows of padding: 80 above, 81 below (the odd row goes to the bottom)",
    )
    add(
        "center-odd-remainder-right",
        sq,
        (479, 640),
        "center",
        "half_even",
        [80, 10.5],
        "161 columns of padding: 80 on the left, 81 on the right",
    )
    add(
        "center-rounding-tie-half-even",
        sq,
        (1280, 101),
        "center",
        "half_even",
        [320, 320],
        "src_h * s = 50.5: half_even gives 50 (half_up gives 51, top 294)",
        differs_by_rounding=True,
    )
    add(
        "center-rounding-tie-half-up",
        sq,
        (1280, 101),
        "center",
        "half_up",
        [320, 320],
        "src_h * s = 50.5: half_up gives 51 (half_even gives 50, top 295)",
        differs_by_rounding=True,
    )
    add(
        "center-rounding-tie-odd-half-even",
        sq,
        (1280, 103),
        "center",
        "half_even",
        [320, 320],
        "src_h * s = 51.5: the even neighbour is 52, so both modes give 52",
        differs_by_rounding=False,
    )
    add(
        "center-rounding-tie-odd-half-up",
        sq,
        (1280, 103),
        "center",
        "half_up",
        [320, 320],
        "src_h * s = 51.5: both modes give 52",
        differs_by_rounding=False,
    )
    add(
        "center-float-noise-below-integer",
        [416, 416],
        (1440, 1080),
        "center",
        "half_even",
        [208, 208],
        "src_w * s = 415.99999999999994 in float64: rounding gives 416, cutting gives 415",
    )
    add(
        "center-non-square-target",
        [384, 640],
        (1920, 1080),
        "center",
        "half_even",
        [320, 192],
        "target_size is [height, width]: [384, 640] is 640 wide and 384 high",
    )
    add(
        "center-upscale",
        sq,
        (320, 240),
        "center",
        "half_even",
        [320, 320],
        "s = 2",
    )
    add(
        "center-scale-exactly-one",
        sq,
        (640, 640),
        "center",
        "half_even",
        [123.5, 456.25],
        "no resize and no padding: the unprojection is the identity",
    )
    add(
        "center-one-pixel-wide-source",
        sq,
        (1, 100),
        "center",
        "half_even",
        [320, 320],
        "s = 6.4; n_w = round(6.4) = 6",
    )
    add(
        "center-width-guard",
        sq,
        (1, 10000),
        "center",
        "half_even",
        [319.5, 320],
        "src_w * s = 0.064 rounds to 0; max(1, x) keeps n_w at 1",
    )

    # Top-left padding.
    add(
        "top-left-half-up-landscape",
        sq,
        (1920, 1080),
        "top_left",
        "half_up",
        [320, 180],
        "the image sits in the top-left corner; the padding is below",
    )
    add(
        "top-left-half-even-landscape",
        sq,
        (1280, 720),
        "top_left",
        "half_even",
        [640, 360],
        "the bottom-right corner of the image maps to the bottom-right corner of the source",
    )
    add(
        "top-left-half-even-portrait",
        sq,
        (1080, 1920),
        "top_left",
        "half_even",
        [360, 640],
        "the padding is on the right",
    )
    add(
        "top-left-rounding-tie-half-even",
        sq,
        (1280, 101),
        "top_left",
        "half_even",
        [640, 50],
        "src_h * s = 50.5: half_even gives 50",
        differs_by_rounding=True,
    )
    add(
        "top-left-rounding-tie-half-up",
        sq,
        (1280, 101),
        "top_left",
        "half_up",
        [640, 51],
        "src_h * s = 50.5: half_up gives 51",
        differs_by_rounding=True,
    )
    add(
        "top-left-fraction-below-half",
        sq,
        (1000, 333),
        "top_left",
        "half_even",
        [640, 213],
        "src_h * s = 213.12: both modes give 213",
        differs_by_rounding=False,
    )
    add(
        "top-left-fraction-above-half",
        sq,
        (1366, 768),
        "top_left",
        "half_up",
        [640, 360],
        "src_h * s = 359.82: both modes give 360; cutting gives 359",
        differs_by_rounding=False,
    )
    add(
        "top-left-float-noise-below-integer",
        [416, 416],
        (1440, 1080),
        "top_left",
        "half_even",
        [416, 312],
        "src_w * s = 415.99999999999994 and src_h * s = 311.99999999999994 in float64",
    )
    add(
        "top-left-scale-exactly-one",
        sq,
        (640, 480),
        "top_left",
        "half_even",
        [100, 100],
        "no resize: the unprojection is the identity",
    )
    add(
        "top-left-upscale",
        sq,
        (320, 240),
        "top_left",
        "half_up",
        [640, 480],
        "s = 2",
    )
    add(
        "top-left-one-pixel-wide-source",
        sq,
        (1, 100),
        "top_left",
        "half_even",
        [6, 640],
        "s = 6.4; n_w = round(6.4) = 6",
    )
    add(
        "top-left-width-guard",
        sq,
        (1, 10000),
        "top_left",
        "half_even",
        [1, 640],
        "src_w * s = 0.064 rounds to 0; max(1, x) keeps n_w at 1",
    )

    for case in cases:
        src_w, src_h = case.input["src_w"], case.input["src_h"]
        t_h, t_w = case.params["target_size"]
        s = min(t_w / src_w, t_h / src_h)
        if "width-guard" in case.id:
            require(round(src_w * s) == 0, f"{case.id}: n_w would not be 0")
        if "float-noise" in case.id:
            require(
                int(src_w * s) != round(src_w * s)
                and int(src_h * s) != round(src_h * s),
                f"{case.id}: cutting and rounding give the same size",
            )

    return Vectors(
        section="pre.resize.letterbox",
        reading_notes=[
            "Normative text: specs/model-sidecar/pre/resize-letterbox.md.",
            "`target_size` is [height, width]. `src_w` and `src_h` are the source size in pixels.",
            "`expect` gives the size of the resized image (`n_w`, `n_h`) and its position on the "
            "padded canvas (`left`, `top`).",
            "`unproject` applies the section's Inverse to one model-input position.",
            "A case that lists `verified_against` gave the same `expect` values with that function. "
            "The function does not compute `unproject`.",
        ],
        cases=cases,
        tolerance=TOLERANCE["resize"],
        unverified=(
            "letterbox_preprocess implements only part of the section: it has no pad_position "
            "center, it cuts the scaled size instead of rounding it, and it fails when n_w "
            "would be 0. A case that lists verified_against gave the same n_w, n_h, left and "
            "top with that function. No independent implementation has run the other cases."
        ),
    )


# ---------------------------------------------------------------------------
# pre.resize.stretch
# ---------------------------------------------------------------------------


def build_stretch() -> Vectors:
    cases: list[Case] = []

    def add(
        case_id: str,
        target: list[int],
        src: tuple[int, int],
        model_xy: list[float],
        note: str | None = None,
    ) -> None:
        src_w, src_h = src
        t_h, t_w = target
        x, y = model_xy
        cases.append(
            Case(
                id=case_id,
                params={"target_size": target},
                input={"src_w": src_w, "src_h": src_h},
                expect={
                    "dst_w": t_w,
                    "dst_h": t_h,
                    "scale_x": t_w / src_w,
                    "scale_y": t_h / src_h,
                },
                unproject={
                    "model_xy": model_xy,
                    "source_xy": [x * src_w / t_w, y * src_h / t_h],
                },
                note=note,
            )
        )

    add(
        "landscape-to-square",
        [640, 640],
        (1920, 1080),
        [320, 320],
        "the x and y scale factors differ: 1/3 and 16/27",
    )
    add(
        "unproject-fractional",
        [640, 640],
        (1920, 1080),
        [100, 100],
        "y_src = 100 * 1080 / 640 = 168.75",
    )
    add(
        "portrait-target",
        [640, 384],
        (1920, 1080),
        [384, 640],
        "target_size [640, 384] is 384 wide and 640 high: the output size is (T_w, T_h)",
    )
    add("same-size", [480, 640], (640, 480), [123.5, 77.25], "scale 1 on both axes")
    add("upscale", [480, 640], (320, 240), [640, 480], "scale 2 on both axes")
    add(
        "one-pixel-wide-source",
        [640, 640],
        (1, 100),
        [640, 320],
        "scale_x = 640; the right edge of the model input maps to x_src = 1",
    )

    return Vectors(
        section="pre.resize.stretch",
        reading_notes=[
            "Normative text: specs/model-sidecar/pre/resize-stretch.md.",
            "`target_size` is [height, width]. `expect` gives the size of the output image "
            "(`dst_w`, `dst_h`) and the scale factor of each axis.",
            "`unproject` applies the section's Inverse to one model-input position.",
        ],
        cases=cases,
        tolerance=TOLERANCE["resize"],
        unverified=(
            "No independent implementation has run these vectors yet. They come from the "
            "section text only."
        ),
    )


# ---------------------------------------------------------------------------
# pre.resize.fit
# ---------------------------------------------------------------------------


def fit_geometry(src_w: int, src_h: int, target_size: list[int]) -> dict[str, float]:
    """Section `pre.resize.fit`, Behaviour. Nothing is rounded."""
    t_h, t_w = target_size
    s = min(t_w / src_w, t_h / src_h)
    return {
        "scale": s,
        "left": (t_w - src_w * s) / 2,
        "top": (t_h - src_h * s) / 2,
    }


def fit_unproject(geometry: dict[str, float], model_xy: list[float]) -> list[float]:
    """Section `pre.resize.fit`, Inverse. Uses the unrounded values."""
    x, y = model_xy
    return [
        (x - geometry["left"]) / geometry["scale"],
        (y - geometry["top"]) / geometry["scale"],
    ]


def build_fit() -> Vectors:
    sq = [640, 640]
    cases: list[Case] = []

    def add(
        case_id: str,
        target: list[int],
        src: tuple[int, int],
        model_xy: list[float],
        note: str | None = None,
    ) -> None:
        src_w, src_h = src
        geometry = fit_geometry(src_w, src_h, target)
        cases.append(
            Case(
                id=case_id,
                params={"target_size": target},
                input={"src_w": src_w, "src_h": src_h},
                expect=geometry,
                unproject={
                    "model_xy": model_xy,
                    "source_xy": fit_unproject(geometry, model_xy),
                },
                note=note,
            )
        )

    add(
        "landscape-into-square",
        sq,
        (1920, 1080),
        [320, 320],
        "s = 1/3; top = (640 - 360) / 2 = 140",
    )
    add(
        "unproject-in-the-padding",
        sq,
        (1920, 1080),
        [0, 0],
        "a position in the padding maps outside the source: y_src = -420",
    )
    add(
        "portrait-into-square",
        sq,
        (1080, 1920),
        [320, 320],
        "the padding is on the left and right: left = 140",
    )
    add(
        "fractional-offset",
        sq,
        (1000, 333),
        [320, 320],
        "s = 0.64; top = 213.44. A letterbox gives n_h = 213 and top = 213 here",
    )
    add(
        "half-pixel-offset-scale-one",
        sq,
        (640, 479),
        [100, 80.5],
        "s = 1; top = 80.5 (a letterbox with center gives top = 80)",
    )
    add(
        "scale-exactly-one",
        sq,
        (640, 640),
        [123.5, 456.25],
        "no padding: the unprojection is the identity",
    )
    add(
        "upscale",
        sq,
        (320, 240),
        [320, 80],
        "s = 2; top = 80",
    )
    add(
        "one-pixel-wide-source",
        sq,
        (1, 100),
        [320, 0],
        "s = 6.4; left = 316.8 (a letterbox with center gives n_w = 6 and left = 317)",
    )
    add(
        "non-square-target",
        [384, 640],
        (1920, 1080),
        [320, 192],
        "target_size [384, 640] is 640 wide and 384 high: s = 1/3 and top = 12",
    )
    add(
        "limited-by-height",
        [100, 640],
        (1920, 1080),
        [320, 50],
        "the height limits s: s = 100 / 1080 and left = 231.111111",
    )
    add(
        "float-noise-below-integer",
        [416, 416],
        (1440, 1080),
        [208, 208],
        "src_w * s = 415.99999999999994 in float64: left is 0 within the tolerance",
    )

    return Vectors(
        section="pre.resize.fit",
        reading_notes=[
            "Normative text: specs/model-sidecar/pre/resize-fit.md. Decision: "
            "notes/decisions/0012-fit-resize-for-rtmo.md.",
            "`target_size` is [height, width]. `expect` gives the scale and the fractional "
            "offsets of the warp matrix M = [[scale, 0, left], [0, scale, top]]. The geometry "
            "does not depend on `pad_value`.",
            "`unproject` applies the section's Inverse to one model-input position.",
        ],
        cases=cases,
        tolerance=TOLERANCE["resize"],
        verified_against=[FIT_FUNCTION],
    )


# ---------------------------------------------------------------------------
# pre.resize.affine_person_crop
# ---------------------------------------------------------------------------


def affine_crop(
    bbox_xyxy: list[float],
    target_size: list[int],
    expand_ratio: float,
    maintain_aspect_ratio: bool,
) -> dict[str, Any]:
    """Section `pre.resize.affine_person_crop`, Behaviour. The rotation is 0."""
    x1, y1, x2, y2 = bbox_xyxy
    t_h, t_w = target_size
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    w, h = (x2 - x1) * expand_ratio, (y2 - y1) * expand_ratio
    if maintain_aspect_ratio:
        if w > h * (t_w / t_h):
            h = w * (t_h / t_w)
        else:
            w = h * (t_w / t_h)
    sx, sy = t_w / w, t_h / h
    return {
        "center": [cx, cy],
        "crop_w": w,
        "crop_h": h,
        "matrix": [[sx, 0, t_w / 2 - sx * cx], [0, sy, t_h / 2 - sy * cy]],
    }


def affine_unproject(matrix: list[list[float]], model_xy: list[float]) -> list[float]:
    """Section `pre.resize.affine_person_crop`, Inverse: invert the scale and shift of M."""
    (sx, _, tx), (_, sy, ty) = matrix
    x, y = model_xy
    return [(x - tx) / sx, (y - ty) / sy]


def build_affine_person_crop() -> Vectors:
    cases: list[Case] = []

    def add(
        case_id: str,
        target: list[int],
        bbox: list[float],
        model_xy: list[float],
        note: str | None = None,
        *,
        expand_ratio: float = 1.25,
        maintain_aspect_ratio: bool = True,
    ) -> None:
        expect = affine_crop(bbox, target, expand_ratio, maintain_aspect_ratio)
        cases.append(
            Case(
                id=case_id,
                params={
                    "target_size": target,
                    "expand_ratio": expand_ratio,
                    "maintain_aspect_ratio": maintain_aspect_ratio,
                },
                input={"bbox_xyxy": bbox},
                expect=expect,
                unproject={
                    "model_xy": model_xy,
                    "source_xy": affine_unproject(expect["matrix"], model_xy),
                },
                note=note,
            )
        )

    add(
        "tall-box-grows-width",
        [256, 192],
        [100, 50, 300, 450],
        [96, 128],
        "box 200x400, expanded to 250x500; 250 < 500 * 0.75, so w = 375. The centre maps to "
        "the centre of the target",
    )
    add(
        "wide-box-grows-height",
        [256, 192],
        [0, 0, 400, 200],
        [0, 0],
        "box 400x200, expanded to 500x250; 500 > 250 * 0.75, so h = 500 * 256 / 192. "
        "The top-left corner of the target maps to the top-left corner of the crop",
    )
    add(
        "no-expansion",
        [256, 192],
        [10, 20, 110, 220],
        [192, 256],
        "expand_ratio 1.0: w = 100 grows to 150 to match the aspect ratio 192 / 256",
        expand_ratio=1.0,
    )
    add(
        "aspect-ratio-not-kept",
        [256, 192],
        [100, 50, 300, 450],
        [192, 256],
        "maintain_aspect_ratio false: the box is warped as it is, so the x and y scales differ",
        maintain_aspect_ratio=False,
    )
    add(
        "box-outside-the-image",
        [256, 192],
        [-50, -20, 150, 380],
        [96, 128],
        "the crop can reach outside the source image",
    )
    add(
        "square-target",
        [288, 288],
        [0, 0, 100, 100],
        [288, 288],
        "a square box in a square target: w = h = 125",
    )
    add(
        "target-384x288",
        [384, 288],
        [320, 100, 520, 600],
        [144, 192],
        "target_size [384, 288] is 288 wide and 384 high: w = 625 * 288 / 384 = 468.75. The target "
        "centre maps to the centre of the box",
    )

    return Vectors(
        section="pre.resize.affine_person_crop",
        reading_notes=[
            "Normative text: specs/model-sidecar/pre/resize-affine-person-crop.md.",
            "`target_size` is [height, width]. `bbox_xyxy` is the person box [x1, y1, x2, y2] "
            "in source pixels. The rotation is 0.",
            "`expect` gives the centre of the crop, its size (`crop_w`, `crop_h`) after the "
            "expansion and the aspect-ratio step, and the warp matrix M that maps source "
            "pixels to model-input pixels.",
            "`unproject` applies the section's Inverse to one model-input position.",
        ],
        cases=cases,
        tolerance=TOLERANCE["resize"],
        unverified=(
            "No independent implementation has run these vectors yet. They come from the "
            "section text only."
        ),
    )


# ---------------------------------------------------------------------------
# pre.normalize
# ---------------------------------------------------------------------------

IMAGENET_MEAN_RGB = (123.675, 116.28, 103.53)
IMAGENET_STD_RGB = (58.395, 57.12, 57.375)
PIXELS_BGR = [[0, 0, 0], [255, 255, 255], [10, 128, 250], [200, 100, 50]]


def resolve_mode(
    normalization: Any, by_precision: dict[str, str] | None, precision: str
) -> Any:
    """Resolution order of the section: by precision, then top level, then the default."""
    if by_precision and precision in by_precision:
        return by_precision[precision]
    if normalization is not None:
        return normalization
    return "imagenet_bgr"


def normalize_pixels(
    pixels_bgr: list[list[int]],
    mode: Any,
    color_format: str | None,
    *,
    legacy: bool,
    dtype: str = "float32",
) -> tuple[str, list[list[float]]]:
    """Return the channel order of the tensor and the normalized pixels."""
    if isinstance(mode, dict):
        order = mode.get("color_format") or color_format or "rgb"
    elif mode in ("none", "unit_float"):
        require(color_format is not None, f"{mode} needs color_format")
        order = color_format
    else:
        order = "bgr" if mode == "imagenet_bgr" else "rgb"

    out: list[list[float]] = []
    for b, g, r in pixels_bgr:
        values = [b, g, r] if order == "bgr" else [r, g, b]
        if isinstance(mode, dict):
            scale = mode.get("scale", 1.0)
            result = [
                (v * scale - m) / sd
                for v, m, sd in zip(values, mode["mean"], mode["std"], strict=True)
            ]
        elif mode == "none":
            result = [int(v) if dtype == "uint8" else float(v) for v in values]
        elif mode == "unit_float":
            result = [v / 255.0 for v in values]
        else:
            mean, std = list(IMAGENET_MEAN_RGB), list(IMAGENET_STD_RGB)
            if order == "bgr" and not legacy:
                mean, std = mean[::-1], std[::-1]
            result = [(v - m) / sd for v, m, sd in zip(values, mean, std, strict=True)]
        out.append(result)
    return order, out


def build_normalize() -> Vectors:
    cases: list[Case] = []

    def add(
        case_id: str,
        *,
        normalization: Any = None,
        by_precision: dict[str, str] | None = None,
        precision: str | None = None,
        color_format: str | None = None,
        dtype: str | None = None,
        schema_version: str | None = None,
        note: str | None = None,
    ) -> None:
        params: dict[str, Any] = {}
        if schema_version is not None:
            params["schema_version"] = schema_version
        if normalization is not None:
            params["normalization"] = normalization
        if by_precision is not None:
            params["normalization_by_precision"] = by_precision
        if precision is not None:
            params["precision"] = precision
        if color_format is not None:
            params["color_format"] = color_format
        if dtype is not None:
            params["dtype"] = dtype
        mode = resolve_mode(normalization, by_precision, precision or "fp32")
        order, values = normalize_pixels(
            PIXELS_BGR,
            mode,
            color_format,
            legacy=bool(schema_version and schema_version.startswith("<")),
            dtype=dtype or "float32",
        )
        cases.append(
            Case(
                id=case_id,
                params=params,
                input={"pixels_bgr": PIXELS_BGR},
                expect={
                    "resolved_mode": mode if isinstance(mode, str) else mode["mode"],
                    "channel_order": order,
                    "values": values,
                },
                note=note,
            )
        )

    add(
        "none-rgb",
        normalization="none",
        color_format="rgb",
        dtype="float32",
        note="the values stay 0..255; color_format rgb swaps the BGR source channels",
    )
    add("none-bgr", normalization="none", color_format="bgr", dtype="float32")
    add(
        "none-uint8",
        normalization="none",
        color_format="rgb",
        dtype="uint8",
        note="the cast to the input dtype keeps the 0..255 values",
    )
    add("unit-float-rgb", normalization="unit_float", color_format="rgb")
    add("unit-float-bgr", normalization="unit_float", color_format="bgr")
    add(
        "imagenet-bgr",
        normalization="imagenet_bgr",
        schema_version="vNEXT",
        note="B uses mean 103.53 and std 57.375; the tensor order is B, G, R",
    )
    add(
        "imagenet-bgr-legacy",
        normalization="imagenet_bgr",
        schema_version="< vNEXT",
        note="schema_version < vNEXT: B uses mean 123.675 and std 58.395 (notes/decisions/0009-imagenet-bgr-meaning.md)",
    )
    add(
        "imagenet-rgb",
        normalization="imagenet_rgb",
        note="R uses mean 123.675 and std 58.395; the tensor order is R, G, B",
    )
    add(
        "imagenet-rgb-with-color-format",
        normalization="imagenet_rgb",
        color_format="rgb",
        note="color_format agrees with the mode; the result is the same",
    )
    add(
        "custom-rgb",
        normalization={
            "mode": "custom",
            "color_format": "rgb",
            "scale": 1 / 255,
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225],
        },
        note="(pixel * scale - mean) / std; mean and std are in rgb order",
    )
    add(
        "custom-bgr",
        normalization={
            "mode": "custom",
            "color_format": "bgr",
            "scale": 1 / 255,
            "mean": [0.406, 0.456, 0.485],
            "std": [0.225, 0.224, 0.229],
        },
        note="the same statistics in bgr order give the custom-rgb values in reverse order",
    )
    add(
        "custom-inherits-color-format",
        normalization={"mode": "custom", "mean": [1, 2, 3], "std": [2, 2, 2]},
        color_format="bgr",
        note="custom.color_format is absent: it inherits input.color_format. scale defaults to 1",
    )
    add(
        "custom-defaults-to-rgb",
        normalization={"mode": "custom", "mean": [1, 2, 3], "std": [2, 2, 2]},
        note="no color_format anywhere: the order is rgb",
    )
    add(
        "default-is-imagenet-bgr",
        schema_version="vNEXT",
        note="normalization is absent: the default is imagenet_bgr",
    )
    add(
        "precision-override",
        normalization="unit_float",
        by_precision={"fp16": "none"},
        precision="fp16",
        color_format="rgb",
        dtype="uint8",
        note="normalization_by_precision wins over the top-level normalization",
    )
    add(
        "precision-without-override",
        normalization="unit_float",
        by_precision={"fp16": "none"},
        precision="fp32",
        color_format="rgb",
        note="no entry for fp32: the top-level normalization applies",
    )

    return Vectors(
        section="pre.normalize",
        reading_notes=[
            "Normative text: specs/model-sidecar/pre/normalization.md. Decision: "
            "notes/decisions/0009-imagenet-bgr-meaning.md.",
            "`pixels_bgr` are pixels of the resized frame in BGR source order, as OpenCV "
            "delivers them. `values` are the same pixels in the channel order of the tensor "
            "(`channel_order`), one list of three numbers per pixel.",
            "`params` use the sidecar field names: `normalization`, `normalization_by_precision`, "
            "`color_format` and `dtype` are fields of `input`; `precision` selects the entry "
            "of `normalization_by_precision` (default fp32).",
            "The meaning of `imagenet_bgr` depends on `schema_version`: a case with "
            '`schema_version: "< vNEXT"` uses the legacy meaning.',
        ],
        cases=cases,
        tolerance=TOLERANCE["normalize"],
        unverified=(
            "No independent implementation has run these vectors yet. They come from the "
            "section text only."
        ),
    )


# ---------------------------------------------------------------------------
# post.det.selection.* (shared decode steps)
# ---------------------------------------------------------------------------

FIELDS = ["x1", "y1", "x2", "y2", "score", "class_id"]
FIELD_PARAMS = {"score_field": "score", "class_field": "class_id"}


def _box(i: int) -> list[int]:
    """Return a box that overlaps no other `_box(j)`."""
    return [10 * i, 0, 10 * i + 8, 8]


def _row(i: int, score: float, cls: int) -> list[float]:
    return [*_box(i), score, cls]


@dataclass
class Kept:
    row: int
    box: list[float]
    score: float
    class_id: int


def to_xyxy(box: list[float], box_format: str) -> list[float]:
    a, b, c, d = box
    if box_format == "xyxy":
        return [a, b, c, d]
    if box_format == "xywh":
        return [a, b, a + c, b + d]
    if box_format == "cxcywh":
        return [a - c / 2, b - d / 2, a + c / 2, b + d / 2]
    raise ValueError(f"unknown box_format {box_format!r}")


def candidates(
    params: dict[str, Any], inp: dict[str, Any]
) -> list[tuple[list[float], float, int | None]]:
    """Return (box in xyxy, score, model class index or None) for each input row."""
    box_format = params.get("box_format", "xyxy")
    if "rows" in inp:
        fields = inp["fields"]
        i_score = fields.index(params["score_field"])
        i_class = (
            fields.index(params["class_field"]) if "class_field" in params else None
        )
        return [
            (
                to_xyxy(row[0:4], box_format),
                row[i_score],
                None if i_class is None else int(row[i_class]),
            )
            for row in inp["rows"]
        ]
    return [
        (to_xyxy(box, box_format), score, None)
        for box, score in zip(inp["boxes"], inp["scores"], strict=True)
    ]


def resolve_class(
    model_class: int | None,
    params: dict[str, Any],
    *,
    assign_person_without_source: bool,
) -> int | None:
    """Map a model class index to the emitted class id; None drops the candidate."""
    person = params.get("person_class_id", 0)
    if model_class is None:
        require(
            assign_person_without_source or params.get("is_person_only", False),
            "a candidate without a class source needs is_person_only here",
        )
        return person
    class_map = params.get("class_id_map")
    emitted = (
        class_map[model_class]
        if class_map is not None
        else params.get("class_id_base", 0) + model_class
    )
    if emitted == -1:
        return None
    if params.get("is_person_only", False) and emitted != person:
        return None
    return emitted


def iou(a: list[float], b: list[float]) -> float:
    """Intersection over union. The area is (x2 - x1) * (y2 - y1): nothing is added."""
    inter_w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    inter_h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = inter_w * inter_h
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def select_none(params: dict[str, Any], inp: dict[str, Any]) -> list[Kept]:
    """Section `post.det.selection.none`, Behaviour (before unprojection)."""
    threshold = params.get("confidence_threshold_default", 0.7)
    kept = []
    for row, (box, score, model_class) in enumerate(candidates(params, inp)):
        class_id = resolve_class(
            model_class, params, assign_person_without_source=False
        )
        if class_id is not None and score > threshold:
            kept.append(Kept(row, box, score, class_id))
    return kept


def select_top_k(params: dict[str, Any], inp: dict[str, Any]) -> list[Kept]:
    """Section `post.det.selection.top_k`, Behaviour (before unprojection)."""
    logits = inp["class_logits"]
    if params.get("score_activation", "none") == "sigmoid":
        p = [[1 / (1 + math.exp(-x)) for x in row] for row in logits]
    else:
        p = logits
    n_classes = len(p[0])
    flat = sorted(
        range(len(p) * n_classes), key=lambda i: (-p[i // n_classes][i % n_classes], i)
    )
    threshold = params.get("confidence_threshold_default", 0.7)
    kept = []
    for index in flat[: min(params["top_k"], len(flat))]:
        row, model_class = divmod(index, n_classes)
        score = p[row][model_class]
        class_id = resolve_class(
            model_class, params, assign_person_without_source=False
        )
        if class_id is not None and score > threshold:
            box = to_xyxy(inp["boxes"][row], params.get("box_format", "xyxy"))
            kept.append(Kept(row, box, score, class_id))
    return kept


def select_nms(params: dict[str, Any], inp: dict[str, Any]) -> list[Kept]:
    """Section `post.det.selection.nms`, Behaviour (before unprojection)."""
    pool = []
    for row, (box, score, model_class) in enumerate(candidates(params, inp)):
        if score <= params["score_threshold"]:
            continue
        class_id = resolve_class(model_class, params, assign_person_without_source=True)
        if class_id is not None:
            pool.append(Kept(row, box, score, class_id))
    pool.sort(key=lambda c: (-c.score, c.row))
    agnostic = params.get("class_agnostic", False)
    survivors: list[Kept] = []
    for cand in pool:
        suppressed = any(
            (agnostic or kept.class_id == cand.class_id)
            and iou(kept.box, cand.box) > params["iou_threshold"]
            for kept in survivors
        )
        if not suppressed:
            survivors.append(cand)
    if "post_nms_top_k" in params:
        survivors = survivors[: params["post_nms_top_k"]]
    threshold = params.get("confidence_threshold_default", 0.7)
    return [c for c in survivors if c.score > threshold]


def to_float32(value: Any) -> Any:
    """Round every float in `value` to float32 (a host may compare in float32)."""
    if isinstance(value, float):
        return float(np.float32(value))
    if isinstance(value, dict):
        return {key: to_float32(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_float32(item) for item in value]
    return value


def _selection_case(
    select: Callable[[dict[str, Any], dict[str, Any]], list[Kept]],
    case_id: str,
    params: dict[str, Any],
    inp: dict[str, Any],
    note: str | None,
    *,
    show_boxes: bool = False,
) -> Case:
    kept = select(params, inp)
    narrow = select(to_float32(params), to_float32(inp))
    require(
        [c.row for c in kept] == [c.row for c in narrow]
        and [c.class_id for c in kept] == [c.class_id for c in narrow],
        f"{case_id}: the result depends on the float width",
    )
    expect: dict[str, Any] = {
        "kept_rows": [c.row for c in kept],
        "scores": [c.score for c in kept],
        "class_ids": [c.class_id for c in kept],
    }
    if show_boxes:
        expect["boxes_xyxy"] = [c.box for c in kept]
    return Case(id=case_id, params=params, input=inp, expect=expect, note=note)


SELECTION_UNVERIFIED = (
    "No independent implementation has run these vectors yet. They come from the section "
    "text only."
)


def _selection_notes(section_file: str) -> list[str]:
    return [
        f"Normative text: specs/model-sidecar/post/{section_file} and "
        "specs/model-sidecar/post/detection-decode.md.",
        "`params` use the names of the `decode` fields. `kept_rows` are 0-based row indexes "
        "of the input, `scores` and `class_ids` are the scores and the emitted class ids of "
        "the kept detections, in output order.",
        "The cases stop before the unprojection and the clamp. `boxes_xyxy`, when it is given, "
        "holds the kept boxes in model-input pixels. Every score and threshold gives the "
        "same result in float32 and in float64.",
    ]


# ---------------------------------------------------------------------------
# post.det.selection.none
# ---------------------------------------------------------------------------


def build_selection_none() -> Vectors:
    cases: list[Case] = []

    def add(
        case_id: str,
        params: dict[str, Any],
        inp: dict[str, Any],
        note: str | None = None,
        **kwargs: Any,
    ) -> None:
        cases.append(_selection_case(select_none, case_id, params, inp, note, **kwargs))

    detections = {"fields": FIELDS}
    add(
        "threshold-is-strict",
        {**FIELD_PARAMS, "confidence_threshold_default": 0.5},
        {
            **detections,
            "rows": [
                _row(0, 0.5, 0),
                _row(1, 0.875, 0),
                _row(2, 0.25, 0),
                _row(3, 0.5, 1),
                _row(4, 0.75, 1),
            ],
        },
        "rows 0 and 3 have score == threshold: both are dropped",
    )
    add(
        "default-confidence-threshold",
        dict(FIELD_PARAMS),
        {
            **detections,
            "rows": [
                _row(0, 0.9, 0),
                _row(1, 0.65, 0),
                _row(2, 0.75, 0),
                _row(3, 0.5, 0),
            ],
        },
        "confidence_threshold_default is absent: the default is 0.7",
    )
    add(
        "class-id-map-drops-minus-one",
        {
            **FIELD_PARAMS,
            "class_id_map": [2, -1, 0, 5],
            "confidence_threshold_default": 0.25,
        },
        {
            **detections,
            "rows": [
                _row(0, 0.9, 0),
                _row(1, 0.875, 1),
                _row(2, 0.75, 2),
                _row(3, 0.625, 3),
                _row(4, 0.5, 1),
                _row(5, 0.375, 3),
            ],
        },
        "model class 1 maps to -1: rows 1 and 4 are dropped; the others get the mapped ids",
    )
    add(
        "class-id-base",
        {
            **FIELD_PARAMS,
            "class_id_base": 1,
            "person_class_id": 1,
            "confidence_threshold_default": 0.25,
        },
        {**detections, "rows": [_row(0, 0.75, 0), _row(1, 0.5, 2)]},
        "emitted class id = class_id_base + model class index",
    )
    add(
        "class-id-map-wins-over-base",
        {
            **FIELD_PARAMS,
            "class_id_base": 10,
            "class_id_map": [3, 4],
            "person_class_id": 3,
            "confidence_threshold_default": 0.25,
        },
        {**detections, "rows": [_row(0, 0.75, 0), _row(1, 0.5, 1)]},
        "class_id_map is present: class_id_base is ignored",
    )
    add(
        "is-person-only-with-class-field",
        {
            **FIELD_PARAMS,
            "class_id_base": 1,
            "is_person_only": True,
            "person_class_id": 1,
            "confidence_threshold_default": 0.25,
        },
        {
            **detections,
            "rows": [
                _row(0, 0.875, 0),
                _row(1, 0.75, 1),
                _row(2, 0.625, 0),
                _row(3, 0.5, 2),
            ],
        },
        "emitted ids are 1, 2, 1, 3; only person_class_id 1 stays (rows 0 and 2)",
    )
    add(
        "is-person-only-without-class-source",
        {
            "scores_output": "scores",
            "is_person_only": True,
            "person_class_id": 3,
            "confidence_threshold_default": 0.5,
        },
        {
            "boxes": [_box(0), _box(1), _box(2)],
            "scores": [0.875, 0.5, 0.75],
        },
        "no class source: every candidate gets person_class_id (3); row 1 has score == threshold",
    )
    add(
        "max-detections-does-not-pad",
        {**FIELD_PARAMS, "max_detections": 4, "confidence_threshold_default": 0.5},
        {
            **detections,
            "rows": [
                _row(0, 0.875, 0),
                _row(1, 0.75, 0),
                _row(2, 0.25, 0),
                _row(3, 0.125, 0),
            ],
        },
        "the graph gives max_detections = 4 rows; 2 pass the threshold, so the output has 2 rows",
    )
    add(
        "no-nms-for-overlapping-boxes",
        {**FIELD_PARAMS, "confidence_threshold_default": 0.5},
        {
            **detections,
            "rows": [
                [0, 0, 10, 10, 0.875, 0],
                [0, 0, 10, 10, 0.75, 0],
            ],
        },
        "two identical boxes: selection none does not suppress either of them",
    )
    add(
        "box-format-cxcywh",
        {**FIELD_PARAMS, "box_format": "cxcywh", "confidence_threshold_default": 0.5},
        {**detections, "rows": [[50, 40, 20, 10, 0.75, 0], [30, 30, 8, 8, 0.25, 0]]},
        "centre and size become corners: [40, 35, 60, 45]",
        show_boxes=True,
    )
    add(
        "box-format-xywh",
        {**FIELD_PARAMS, "box_format": "xywh", "confidence_threshold_default": 0.5},
        {**detections, "rows": [[40, 35, 20, 10, 0.75, 0], [30, 30, 8, 8, 0.25, 0]]},
        "top-left corner and size become corners: [40, 35, 60, 45]",
        show_boxes=True,
    )
    add(
        "no-row-passes",
        {**FIELD_PARAMS, "confidence_threshold_default": 0.9},
        {**detections, "rows": [_row(0, 0.875, 0), _row(1, 0.75, 0)]},
        "the output is empty",
    )

    return Vectors(
        section="post.det.selection.none",
        reading_notes=_selection_notes("selection-none.md"),
        cases=cases,
        tolerance=TOLERANCE["selection"],
        unverified=SELECTION_UNVERIFIED,
    )


# ---------------------------------------------------------------------------
# post.det.selection.top_k
# ---------------------------------------------------------------------------


def build_selection_top_k() -> Vectors:
    cases: list[Case] = []
    boxes3 = [_box(0), _box(1), _box(2)]
    boxes2 = [_box(0), _box(1)]
    grid = [[0.9, 0.8], [0.7, 0.6]]

    def add(
        case_id: str,
        params: dict[str, Any],
        inp: dict[str, Any],
        note: str | None = None,
    ) -> None:
        cases.append(_selection_case(select_top_k, case_id, params, inp, note))

    add(
        "several-classes-on-one-row",
        {"top_k": 3, "confidence_threshold_default": 0.25},
        {
            "boxes": boxes3,
            "class_logits": [[0.9, 0.8, 0.1], [0.2, 0.3, 0.1], [0.4, 0.95, 0.05]],
        },
        "the top 3 pairs are (2, 1), (0, 0) and (0, 1): row 0 is selected twice, with two classes",
    )
    add(
        "ties-keep-the-lower-flat-index",
        {"top_k": 3, "confidence_threshold_default": 0.25},
        {"boxes": boxes2, "class_logits": [[0.5, 0.5], [0.5, 0.5]]},
        "all scores are equal: flat indexes 0, 1, 2 are selected (rows 0, 0, 1)",
    )
    add(
        "top-k-larger-than-the-candidates",
        {"top_k": 10, "confidence_threshold_default": 0.25},
        {"boxes": boxes2, "class_logits": [[0.75, 0.5], [0.625, 0.875]]},
        "min(top_k, Q * C) = 4 pairs are selected",
    )
    add(
        "class-id-map-lowers-the-count",
        {
            "top_k": 3,
            "class_id_map": [-1, 7],
            "person_class_id": 7,
            "confidence_threshold_default": 0.25,
        },
        {"boxes": boxes2, "class_logits": grid},
        "the top 3 pairs are (0, 0), (0, 1), (1, 0); class 0 maps to -1; pair (1, 1) does not "
        "take their place",
    )
    add(
        "top-k-limit-comes-before-the-confidence-filter",
        {"top_k": 2, "confidence_threshold_default": 0.85},
        {"boxes": boxes2, "class_logits": grid},
        "the top 2 pairs have scores 0.9 and 0.8; 0.8 is dropped; 0.7 does not take its place",
    )
    add(
        "sigmoid-and-strict-threshold",
        {
            "top_k": 4,
            "score_activation": "sigmoid",
            "confidence_threshold_default": 0.5,
        },
        {"boxes": boxes2, "class_logits": [[0.0, 2.0], [-2.0, 4.0]]},
        "sigmoid(0) = 0.5 is not above the threshold 0.5; the kept scores are sigmoid values",
    )
    add(
        "is-person-only",
        {
            "top_k": 4,
            "is_person_only": True,
            "person_class_id": 0,
            "confidence_threshold_default": 0.25,
        },
        {"boxes": boxes2, "class_logits": grid},
        "only class 0 stays: pairs (0, 0) and (1, 0)",
    )
    add(
        "class-id-base",
        {
            "top_k": 2,
            "class_id_base": 5,
            "person_class_id": 5,
            "confidence_threshold_default": 0.25,
        },
        {"boxes": boxes2, "class_logits": grid},
        "emitted class id = class_id_base + model class index",
    )

    return Vectors(
        section="post.det.selection.top_k",
        reading_notes=[
            *_selection_notes("selection-top-k.md"),
            "`class_logits` is [Q, C] (rows, classes). `boxes` is [Q, 4]. A selected pair is a "
            "(row, class); one row can be selected for several classes.",
        ],
        cases=cases,
        tolerance=TOLERANCE["selection"],
        unverified=(
            "No independent implementation has run these vectors yet. They come from the "
            "section text only. skellytracker has no code for this section."
        ),
    )


# ---------------------------------------------------------------------------
# post.det.selection.nms
# ---------------------------------------------------------------------------


def build_selection_nms() -> Vectors:
    cases: list[Case] = []
    detections = {"fields": FIELDS}
    pair = [[0, 0, 12, 10], [4, 0, 16, 10]]  # IoU 80 / 160 = 0.5 exactly
    overlap = [[0, 0, 10, 10], [1, 1, 11, 11]]  # IoU 81 / 119 = 0.68

    def add(
        case_id: str,
        params: dict[str, Any],
        inp: dict[str, Any],
        note: str | None = None,
        **kwargs: Any,
    ) -> None:
        cases.append(_selection_case(select_nms, case_id, params, inp, note, **kwargs))

    base = {
        "iou_threshold": 0.5,
        "score_threshold": 0.05,
        "confidence_threshold_default": 0,
    }
    add(
        "suppress-overlap-and-threshold",
        {**base, "class_agnostic": False},
        {
            "boxes": [[0, 0, 10, 10], [1, 1, 11, 11], [20, 20, 30, 30], [0, 0, 10, 10]],
            "scores": [0.9, 0.8, 0.7, 0.04],
        },
        "row 1: IoU 0.68 > 0.5; row 3: 0.04 <= 0.05. No class source: class_ids get person_class_id",
    )
    add(
        "iou-equal-to-threshold-is-kept",
        base,
        {"boxes": pair, "scores": [0.75, 0.5]},
        "IoU is exactly 0.5 and the threshold is 0.5: suppression needs IoU > threshold",
    )
    add(
        "iou-above-threshold-is-suppressed",
        {**base, "iou_threshold": 0.25},
        {"boxes": pair, "scores": [0.75, 0.5]},
        "IoU 0.5 > 0.25: row 1 is suppressed",
    )
    add(
        "box-area-adds-nothing",
        {**base, "iou_threshold": 0.52},
        {"boxes": pair, "scores": [0.75, 0.5]},
        "IoU is 0.5 <= 0.52. An area with + 1 on the sides gives 0.529 and would suppress row 1",
    )
    add(
        "score-equal-to-score-threshold-is-dropped",
        {**base, "score_threshold": 0.5},
        {"boxes": [_box(0), _box(1), _box(2)], "scores": [0.5, 0.75, 0.25]},
        "candidates need score > score_threshold: 0.5 is dropped",
    )
    add(
        "confidence-threshold-is-strict",
        {**base, "confidence_threshold_default": 0.75},
        {"boxes": [_box(0), _box(1)], "scores": [0.75, 0.875]},
        "the last step keeps score > 0.75 only",
    )
    add(
        "default-confidence-threshold",
        {"iou_threshold": 0.5, "score_threshold": 0.05},
        {"boxes": [_box(0), _box(1), _box(2)], "scores": [0.9, 0.75, 0.65]},
        "confidence_threshold_default is absent: the default is 0.7",
    )
    add(
        "equal-scores-lower-row-wins",
        base,
        {
            "boxes": [overlap[0], overlap[1], [20, 20, 30, 30]],
            "scores": [0.75, 0.75, 0.75],
        },
        "rows 0 and 1 overlap and have equal scores: row 0 stays; the output order is rows 0, 2",
    )
    add(
        "output-is-sorted-by-score",
        base,
        {"boxes": [_box(0), _box(1), _box(2)], "scores": [0.5, 0.875, 0.75]},
        "survivors are sorted by descending score, not by row",
    )
    detection_pair = {
        **detections,
        "rows": [[0, 0, 10, 10, 0.875, 0], [0, 0, 10, 10, 0.75, 1]],
    }
    add(
        "per-class-nms-keeps-both",
        {**base, **FIELD_PARAMS, "class_agnostic": False},
        detection_pair,
        "two identical boxes of different classes: per-class NMS keeps both",
    )
    add(
        "class-agnostic-suppresses-across-classes",
        {**base, **FIELD_PARAMS, "class_agnostic": True},
        detection_pair,
        "the same input with class_agnostic true: row 1 is suppressed",
    )
    add(
        "post-nms-top-k-keeps-the-highest",
        {**base, "post_nms_top_k": 2},
        {
            "boxes": [_box(0), _box(1), _box(2), _box(3)],
            "scores": [0.5, 0.875, 0.875, 0.75],
        },
        "rows 1 and 2 have equal scores: the lower row comes first; the first 2 survivors stay",
    )
    add(
        "post-nms-top-k-counts-survivors",
        {**base, "post_nms_top_k": 2},
        {
            "boxes": [overlap[0], overlap[1], _box(5), _box(6)],
            "scores": [0.9, 0.85, 0.8, 0.7],
        },
        "row 1 is suppressed and takes no slot: the 2 slots go to rows 0 and 2",
    )
    add(
        "post-nms-top-k-larger-than-the-survivors",
        {**base, "post_nms_top_k": 10},
        {"boxes": [_box(0), _box(1)], "scores": [0.75, 0.5]},
        "all survivors stay",
    )
    add(
        "class-id-map-drop-comes-before-nms",
        {
            **base,
            **FIELD_PARAMS,
            "class_id_map": [0, -1],
            "class_agnostic": True,
        },
        {
            **detections,
            "rows": [[0, 0, 10, 10, 0.9, 1], [0, 0, 10, 10, 0.8, 0]],
        },
        "row 0 (class 1 maps to -1) is dropped before NMS, so it cannot suppress row 1",
    )
    add(
        "is-person-only-drop-comes-before-nms",
        {
            **base,
            **FIELD_PARAMS,
            "is_person_only": True,
            "person_class_id": 0,
            "class_agnostic": True,
        },
        {
            **detections,
            "rows": [[0, 0, 10, 10, 0.9, 1], [0, 0, 10, 10, 0.8, 0]],
        },
        "row 0 is not a person: it is dropped before NMS, so it cannot suppress row 1",
    )
    add(
        "no-class-source-uses-person-class-id",
        {**base, "person_class_id": 2},
        {"boxes": [_box(0), _box(1)], "scores": [0.75, 0.5]},
        "no class source: every candidate gets person_class_id (2)",
    )
    add(
        "class-id-base",
        {**base, **FIELD_PARAMS, "class_id_base": 1, "person_class_id": 1},
        {
            **detections,
            "rows": [_row(0, 0.75, 0), _row(1, 0.5, 2)],
        },
        "emitted class id = class_id_base + model class index",
    )
    add(
        "box-format-cxcywh",
        {**base, "box_format": "cxcywh"},
        {"boxes": [[6, 5, 12, 10], [10, 5, 12, 10]], "scores": [0.75, 0.5]},
        "centre and size become corners [0, 0, 12, 10] and [4, 0, 16, 10]: IoU 0.5, both stay",
        show_boxes=True,
    )
    add(
        "no-candidate-passes",
        {**base, "score_threshold": 0.9},
        {"boxes": [_box(0), _box(1)], "scores": [0.75, 0.5]},
        "the output is empty",
    )

    return Vectors(
        section="post.det.selection.nms",
        reading_notes=[
            *_selection_notes("selection-nms.md"),
            "`iou_threshold`, `score_threshold`, `class_agnostic` and `post_nms_top_k` are "
            "fields of the `nms` object; they are written without the `nms` key here. A case "
            "with `boxes` and `scores` has no class source.",
            "`confidence_threshold_default` is given as 0 in most cases, so that the last step "
            "keeps every survivor.",
        ],
        cases=cases,
        tolerance=TOLERANCE["selection"],
        unverified=SELECTION_UNVERIFIED,
    )


# ---------------------------------------------------------------------------
# post.unprojection
# ---------------------------------------------------------------------------


def to_model_pixels(
    scale: str, decoded_xy: list[float], input_size: list[int]
) -> list[float]:
    """Section `post.unprojection`, Behaviour: a decoded position in model-input pixels.

    `input_size` is [height, width] of the model input.
    """
    in_h, in_w = input_size
    x, y = decoded_xy
    if scale == "pixel":
        return [x, y]
    if scale == "normalized_01":
        return [x * in_w, y * in_h]
    if scale == "normalized_11":
        return [(x + 1) / 2 * in_w, (y + 1) / 2 * in_h]
    raise ValueError(f"unknown scale {scale!r}")


def resize_unproject(
    resize: dict[str, Any],
    src_w: int | None,
    src_h: int | None,
    bbox_xyxy: list[float] | None,
    model_xy: list[float],
) -> list[float]:
    """Sections `pre.resize.<method>`, Inverse: model-input pixels to source pixels."""
    method = resize["method"]
    x, y = model_xy
    if method == "letterbox":
        geometry = letterbox_geometry(
            src_w,
            src_h,
            resize["target_size"],
            resize["pad_position"],
            resize["rounding"],
        )
        return letterbox_unproject(geometry, src_w, src_h, model_xy)
    if method == "stretch":
        t_h, t_w = resize["target_size"]
        return [x * src_w / t_w, y * src_h / t_h]
    if method == "fit":
        geometry = fit_geometry(src_w, src_h, resize["target_size"])
        return fit_unproject(geometry, model_xy)
    if method == "none":
        return [x, y]
    if method == "affine_person_crop":
        crop = affine_crop(
            bbox_xyxy,
            resize["target_size"],
            resize["expand_ratio"],
            resize["maintain_aspect_ratio"],
        )
        return affine_unproject(crop["matrix"], model_xy)
    raise ValueError(f"unknown resize method {method!r}")


def clamp_to_lower_bound(box_xyxy: list[float]) -> list[float]:
    """Section `post.det.decode`, field `clamp_boxes`: the lower bound 0 of the source image.

    The spec does not define the upper bound. The cases never reach it: see `_box_case`.
    """
    return [max(0, value) for value in box_xyxy]


def _unprojection_inputs(
    resize: dict[str, Any],
    src: tuple[int, int] | None,
    bbox_xyxy: list[float] | None,
    input_size: list[int] | None,
) -> tuple[list[int], dict[str, Any]]:
    """Return the model input size [height, width] and the `input` of a case."""
    if resize["method"] == "affine_person_crop":
        require(
            bbox_xyxy is not None and src is None, "an affine case gives a box only"
        )
        return resize["target_size"], {"bbox_xyxy": bbox_xyxy}
    src_w, src_h = src
    if resize["method"] == "none":
        # The host passes the source image unchanged: the model input is the source size.
        require(
            input_size == [src_h, src_w], "method none: input_size is the source size"
        )
        return input_size, {"src_w": src_w, "src_h": src_h}
    require(
        input_size in (None, resize["target_size"]),
        "input_size must equal target_size",
    )
    return resize["target_size"], {"src_w": src_w, "src_h": src_h}


def _unprojection_case(
    case_id: str,
    scale: str,
    resize: dict[str, Any],
    src: tuple[int, int] | None,
    decoded_xy: list[float],
    note: str | None = None,
    *,
    bbox_xyxy: list[float] | None = None,
    input_size: list[int] | None = None,
) -> Case:
    size, case_input = _unprojection_inputs(resize, src, bbox_xyxy, input_size)
    src_w, src_h = src or (None, None)
    model_xy = to_model_pixels(scale, decoded_xy, size)
    return Case(
        id=case_id,
        params={"scale": scale, "input_size": size, "resize": resize},
        input={**case_input, "decoded_xy": decoded_xy},
        expect={
            "model_xy": model_xy,
            "source_xy": resize_unproject(resize, src_w, src_h, bbox_xyxy, model_xy),
        },
        note=note,
    )


def _box_case(
    case_id: str,
    scale: str,
    resize: dict[str, Any],
    src: tuple[int, int],
    decoded_xyxy: list[float],
    note: str | None = None,
    *,
    clamp_boxes: bool | None = None,
) -> Case:
    src_w, src_h = src
    size, case_input = _unprojection_inputs(resize, src, None, None)
    model_box = [
        *to_model_pixels(scale, decoded_xyxy[:2], size),
        *to_model_pixels(scale, decoded_xyxy[2:], size),
    ]
    source_box = [
        *resize_unproject(resize, src_w, src_h, None, model_box[:2]),
        *resize_unproject(resize, src_w, src_h, None, model_box[2:]),
    ]
    # The spec does not define the upper clamp bound ([0, W] or [0, W - 1]) or the result for
    # a box without area. A case keeps clear of both, so the open questions change no result.
    require(
        all(x <= src_w - 1 for x in source_box[0::2])
        and all(y <= src_h - 1 for y in source_box[1::2]),
        f"{case_id}: a coordinate reaches the upper clamp bound",
    )
    clamped = clamp_to_lower_bound(source_box)
    require(
        clamped[2] > clamped[0] and clamped[3] > clamped[1],
        f"{case_id}: the clamped box has no area",
    )
    clamp = True if clamp_boxes is None else clamp_boxes
    params: dict[str, Any] = {"scale": scale, "input_size": size, "resize": resize}
    if clamp_boxes is not None:
        params["clamp_boxes"] = clamp_boxes
    return Case(
        id=case_id,
        params=params,
        input={**case_input, "decoded_xyxy": decoded_xyxy},
        expect={
            "model_xyxy": model_box,
            "source_xyxy": source_box,
            "output_xyxy": clamped if clamp else source_box,
        },
        note=note,
    )


def build_unprojection() -> Vectors:
    sq = [640, 640]
    full_hd = (1920, 1080)
    center = {
        "method": "letterbox",
        "target_size": sq,
        "pad_position": "center",
        "rounding": "half_even",
    }
    top_left = {**center, "pad_position": "top_left", "rounding": "half_up"}
    stretch = {"method": "stretch", "target_size": sq}
    fit = {"method": "fit", "target_size": sq}
    affine = {
        "method": "affine_person_crop",
        "target_size": [256, 192],
        "expand_ratio": 1.0,
        "maintain_aspect_ratio": True,
    }
    wide_input = {**center, "target_size": [384, 640]}
    person_box = [100, 200, 196, 328]
    cases: list[Case] = []

    def point(*args: Any, **kwargs: Any) -> None:
        cases.append(_unprojection_case(*args, **kwargs))

    def box(*args: Any, **kwargs: Any) -> None:
        cases.append(_box_case(*args, **kwargs))

    # Decoded positions in each scale, with the letterbox resize that has padding above and below.
    point(
        "pixel-is-the-model-input-position",
        "pixel",
        center,
        full_hd,
        [320, 320],
        "no conversion: s = 1/3 and top = 140, so y_src = (320 - 140) * 3 = 540",
    )
    point(
        "normalized-01-centre",
        "normalized_01",
        center,
        full_hd,
        [0.5, 0.5],
        "0.5 * 640 = 320: the same result as the pixel case, because the conversion comes first",
    )
    point(
        "normalized-01-top-left-corner",
        "normalized_01",
        center,
        full_hd,
        [0, 0],
        "the top of the model input is padding: y_src = (0 - 140) * 3 = -420",
    )
    point(
        "normalized-01-bottom-right-corner",
        "normalized_01",
        center,
        full_hd,
        [1, 1],
        "1 maps to x = 640, the right edge of the model input, and not to 639",
    )
    point(
        "normalized-11-left-edge",
        "normalized_11",
        center,
        full_hd,
        [-1, 0],
        "-1 maps to x = 0, the left edge of the model input, and not to the centre of pixel 0",
    )
    point(
        "normalized-11-right-edge",
        "normalized_11",
        center,
        full_hd,
        [1, 0],
        "1 maps to x = 640, the right edge, and not to the centre of the last pixel",
    )
    point(
        "normalized-11-centre",
        "normalized_11",
        center,
        full_hd,
        [0, 0],
        "0 maps to the middle of the model input: (320, 320)",
    )
    point(
        "normalized-11-off-centre",
        "normalized_11",
        center,
        full_hd,
        [-0.5, 0.5],
        "(-0.5 + 1) / 2 * 640 = 160 and (0.5 + 1) / 2 * 640 = 480",
    )
    point(
        "normalized-01-non-square-input",
        "normalized_01",
        wide_input,
        full_hd,
        [0.5, 0.5],
        "target_size [384, 640] is 640 wide and 384 high: x scales with 640 and y with 384. "
        "top = 12",
    )
    point(
        "normalized-11-non-square-input",
        "normalized_11",
        wide_input,
        full_hd,
        [1, -1],
        "x = 640 and y = 0; y_src = (0 - 12) * 3 = -36",
    )

    # The same conversions with each of the other resize methods.
    point(
        "normalized-01-letterbox-top-left",
        "normalized_01",
        top_left,
        full_hd,
        [1, 0.5625],
        "(640, 360) is the bottom-right corner of the resized image: the source corner",
    )
    point(
        "normalized-01-stretch",
        "normalized_01",
        stretch,
        full_hd,
        [0.25, 0.75],
        "(160, 480) in model-input pixels; x_src = 160 * 1920 / 640, y_src = 480 * 1080 / 640",
    )
    point(
        "normalized-11-stretch",
        "normalized_11",
        stretch,
        full_hd,
        [1, 1],
        "the far corner of the model input maps to the far corner of the source",
    )
    point(
        "normalized-01-fit",
        "normalized_01",
        fit,
        (1280, 720),
        [0.25, 0.5],
        "fit does not round: s = 0.5, left = 0, top = 140",
    )
    point(
        "normalized-01-no-resize",
        "normalized_01",
        {"method": "none"},
        (640, 480),
        [0.5, 0.25],
        "method none: the model input is the source image; input_size is [480, 640]",
        input_size=[480, 640],
    )
    point(
        "pixel-affine-person-crop",
        "pixel",
        affine,
        None,
        [96, 128],
        "the centre of the target, (96, 128), maps to the centre of the person box, (148, 264); "
        "the box is 96x128 and the scale is 2",
        bbox_xyxy=person_box,
    )
    point(
        "normalized-11-affine-person-crop",
        "normalized_11",
        affine,
        None,
        [0, 0],
        "0 maps to (96, 128) in model-input pixels: the same position as the pixel case",
        bbox_xyxy=person_box,
    )

    # Boxes: the scale, the unprojection and then the clamp.
    box(
        "box-normalized-01-inside-the-image",
        "normalized_01",
        center,
        full_hd,
        [0.25, 0.4375, 0.75, 0.5625],
        "clamp_boxes is absent, so the default true applies; the box is inside the image and "
        "the clamp changes nothing",
    )
    box(
        "box-normalized-11-edge-and-inside",
        "normalized_11",
        center,
        full_hd,
        [-1, -0.5, 0, 0.5],
        "x1 = -1 maps to 0: on the edge, so the clamp changes nothing",
    )
    box(
        "box-clamp-default-is-true",
        "pixel",
        center,
        full_hd,
        [-20, 100, 200, 400],
        "clamp_boxes is absent: x1 = -60 and y1 = -120 become 0",
    )
    box(
        "box-clamp-boxes-true",
        "pixel",
        center,
        full_hd,
        [-20, 100, 200, 400],
        "the same box with clamp_boxes true",
        clamp_boxes=True,
    )
    box(
        "box-clamp-boxes-false-keeps-negative-values",
        "pixel",
        center,
        full_hd,
        [-20, 100, 200, 400],
        "the same box with clamp_boxes false: the output is the unprojected box",
        clamp_boxes=False,
    )
    box(
        "box-clamp-after-the-scale-conversion",
        "normalized_01",
        center,
        full_hd,
        [0, 0, 0.5, 0.5],
        "the box starts in the top padding: y1 = -420 becomes 0",
    )

    return Vectors(
        section="post.unprojection",
        reading_notes=[
            "Normative text: specs/model-sidecar/post/unprojection.md. It uses the Inverse of each "
            "resize section (specs/model-sidecar/pre/resize-*.md) and, for a box, `clamp_boxes` "
            "(specs/model-sidecar/post/detection-decode.md).",
            "`scale` is `decode.box_scale` for a box and `pose.decode.coordinate_scale` for a "
            "keypoint. `input_size` is [height, width] of the model input. `resize` holds the "
            "`input.resize` fields that the Inverse uses.",
            "`decoded_xy` and `decoded_xyxy` are values from the model output, in the given "
            "`scale`, with a top-left origin. `model_xy` and `model_xyxy` are the same values "
            "in model-input pixels. `source_xy` and `source_xyxy` are the unprojected values.",
            "`output_xyxy` is the final box. It is the clamped `source_xyxy` unless "
            "`clamp_boxes` is false. The clamp here sets a negative value to 0.",
            "Every result is exact in float64 arithmetic with the formulas of the sections, so no "
            "case gives a `tolerance`.",
            "The spec does not define the upper bound of the clamp ([0, W] or [0, W - 1]) or "
            "the result for a box without area after the clamp (notes/decisions/README.md, "
            "Open work). No case reaches the upper bound or loses its area, so these open "
            "questions change no result.",
        ],
        cases=cases,
        tolerance=TOLERANCE["unprojection"],
        unverified=(
            "No independent implementation has run these vectors yet. They come from the "
            "section text only. skellytracker has no shared unprojection function: each decoder "
            "unprojects on its own and none reads normalized_01 or normalized_11."
        ),
    )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

BUILDERS: dict[str, Callable[[], Vectors]] = {
    "pre.resize.letterbox": build_letterbox,
    "pre.resize.stretch": build_stretch,
    "pre.resize.fit": build_fit,
    "pre.resize.affine_person_crop": build_affine_person_crop,
    "post.unprojection": build_unprojection,
    "pre.normalize": build_normalize,
    "post.det.selection.none": build_selection_none,
    "post.det.selection.top_k": build_selection_top_k,
    "post.det.selection.nms": build_selection_nms,
}


def build_all() -> dict[str, Vectors]:
    """Return the vectors of every section, keyed by section ID."""
    built = {section: builder() for section, builder in BUILDERS.items()}
    for section, vectors in built.items():
        if vectors.section != section:
            raise ValueError(f"{section}: builder wrote section {vectors.section}")
    return built


def generate() -> dict[str, str]:
    """Return the text of every vector file, keyed by file name."""
    return {f"{section}.yaml": render(v) for section, v in build_all().items()}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="exit 1 when a file differs"
    )
    parser.add_argument("--out", type=Path, default=VECTORS_DIR, help="output folder")
    args = parser.parse_args(argv[1:])

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

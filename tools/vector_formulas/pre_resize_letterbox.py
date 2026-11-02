"""Section `pre.resize.letterbox`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`. A broken invariant calls `defect`.
`CHECKS` holds the named claims that a case can declare: `check(run, params, input, expect)`.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from vector_form import defect


def _round_half_even(x: float) -> int:
    return round(x)  # Python `round`: ties go to the even integer


def _round_half_up(x: float) -> int:
    return math.floor(x + 0.5)


ROUNDING: dict[str, Callable[[float], int]] = {
    "half_even": _round_half_even,
    "half_up": _round_half_up,
}


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, int]:
    """Behaviour: the size of the resized image and its position on the canvas."""
    src_w, src_h = input["src_w"], input["src_h"]
    t_h, t_w = params["target_size"]
    s = min(t_w / src_w, t_h / src_h)
    round_ = ROUNDING.get(params["rounding"])
    if round_ is None:
        defect(f"unknown rounding {params['rounding']!r}")
    n_w = max(1, round_(src_w * s))
    n_h = max(1, round_(src_h * s))
    pad_position = params["pad_position"]
    if pad_position == "top_left":
        left, top = 0, 0
    elif pad_position == "center":
        left, top = math.floor((t_w - n_w) / 2), math.floor((t_h - n_h) / 2)
    else:
        defect(f"unknown pad_position {pad_position!r}")
    if not (n_w <= t_w and n_h <= t_h):
        defect("resized image is larger than the target")
    return {"n_w": n_w, "n_h": n_h, "left": left, "top": top}


def inverse(
    params: dict[str, Any], input: dict[str, Any], model_xy: list[float]
) -> list[float]:
    """Inverse: a model-input position in source pixels."""
    geometry = run(params, input)
    x, y = model_xy
    return [
        (x - geometry["left"]) * input["src_w"] / geometry["n_w"],
        (y - geometry["top"]) * input["src_h"] / geometry["n_h"],
    ]


def _other_rounding(params: dict[str, Any]) -> dict[str, Any]:
    other = "half_up" if params["rounding"] == "half_even" else "half_even"
    return {**params, "rounding": other}


def _scaled(params: dict[str, Any], input: dict[str, Any]) -> tuple[float, float]:
    """`src_w * s` and `src_h * s`, before the rounding."""
    t_h, t_w = params["target_size"]
    s = min(t_w / input["src_w"], t_h / input["src_h"])
    return input["src_w"] * s, input["src_h"] * s


def _rounding_changes_result(run: Callable[..., Any], params: Any, input: Any, expect: Any) -> None:
    if run(_other_rounding(params), input) == expect:
        defect("the other rounding mode gives the same result")


def _rounding_keeps_result(run: Callable[..., Any], params: Any, input: Any, expect: Any) -> None:
    if run(_other_rounding(params), input) != expect:
        defect("the other rounding mode gives another result")


def _scaled_width_rounds_to_zero(
    run: Callable[..., Any], params: Any, input: Any, expect: Any
) -> None:
    if round(_scaled(params, input)[0]) != 0:
        defect("n_w would not be 0")


def _cut_differs_from_round(run: Callable[..., Any], params: Any, input: Any, expect: Any) -> None:
    if any(int(size) == round(size) for size in _scaled(params, input)):
        defect("cutting and rounding give the same size")


CHECKS: dict[str, Callable[..., None]] = {
    "rounding-changes-result": _rounding_changes_result,
    "rounding-keeps-result": _rounding_keeps_result,
    "scaled-width-rounds-to-zero": _scaled_width_rounds_to_zero,
    "cut-differs-from-round": _cut_differs_from_round,
}

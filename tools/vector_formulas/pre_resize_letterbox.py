"""Section `pre.resize.letterbox`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`. A broken invariant calls `defect`.
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
    round_ = ROUNDING[params["rounding"]]
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

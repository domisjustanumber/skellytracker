"""Section `pre.resize.fit`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`. A broken invariant calls `defect`.
`CHECKS` holds the named claims that a case can declare: `check(run, params, input, expect)`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from vector_form import defect


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, float]:
    """Behaviour: the scale and the offsets of the warp matrix. Nothing is rounded."""
    src_w, src_h = input["src_w"], input["src_h"]
    t_h, t_w = params["target_size"]
    s = min(t_w / src_w, t_h / src_h)
    return {
        "scale": s,
        "left": (t_w - src_w * s) / 2,
        "top": (t_h - src_h * s) / 2,
    }


def inverse(params: dict[str, Any], input: dict[str, Any]) -> dict[str, list[float]]:
    """Inverse: `input["model_xy"]` in source pixels. Uses the unrounded values."""
    geometry = run(params, input)
    x, y = input["model_xy"]
    return {
        "source_xy": [
            (x - geometry["left"]) / geometry["scale"],
            (y - geometry["top"]) / geometry["scale"],
        ]
    }


def border(params: dict[str, Any], input: dict[str, Any]) -> dict[str, list[float]]:
    """Behaviour: the `border` of the warp. A scalar `pad_value` s gives [s, s, s]."""
    pad = params["pad_value"]
    return {"border": list(pad) if isinstance(pad, list) else [pad, pad, pad]}


def _pixel_0_0_outside_source(
    function: Callable[..., Any], params: Any, input: Any, expect: Any
) -> None:
    """Pixel (0, 0) maps to x < -2 or y < -2, so no tap of a linear or cubic filter is a source pixel."""
    x, y = inverse(params, {**input, "model_xy": [0, 0]})["source_xy"]
    if not (x < -2 or y < -2):
        defect(f"pixel (0, 0) maps to ({x}, {y}), not outside the source")


CHECKS: dict[str, Callable[..., None]] = {
    "pixel-0-0-outside-source": _pixel_0_0_outside_source,
}

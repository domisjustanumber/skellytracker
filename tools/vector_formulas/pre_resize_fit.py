"""Section `pre.resize.fit`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`.
"""

from __future__ import annotations

from typing import Any


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

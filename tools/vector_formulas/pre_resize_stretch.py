"""Section `pre.resize.stretch`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`.
"""

from __future__ import annotations

from typing import Any


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, float]:
    """Behaviour: the size of the output image and the scale factor of each axis."""
    t_h, t_w = params["target_size"]
    return {
        "dst_w": t_w,
        "dst_h": t_h,
        "scale_x": t_w / input["src_w"],
        "scale_y": t_h / input["src_h"],
    }


def inverse(params: dict[str, Any], input: dict[str, Any]) -> dict[str, list[float]]:
    """Inverse: a model-input position in source pixels. `input` holds `model_xy`."""
    t_h, t_w = params["target_size"]
    x, y = input["model_xy"]
    return {"source_xy": [x * input["src_w"] / t_w, y * input["src_h"] / t_h]}

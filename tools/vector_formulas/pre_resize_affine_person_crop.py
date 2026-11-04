"""Section `pre.resize.affine_person_crop`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`. The rotation is 0. A broken invariant calls
`defect`. `CHECKS` holds the named claims that a case can declare:
`check(run, params, input, expect)`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from vector_form import defect


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Behaviour: the centre and the size of the crop, and the warp matrix M."""
    x1, y1, x2, y2 = input["bbox_xyxy"]
    t_h, t_w = params["target_size"]
    expand_ratio = params["expand_ratio"]
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    w, h = (x2 - x1) * expand_ratio, (y2 - y1) * expand_ratio
    if params["maintain_aspect_ratio"]:
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


def inverse(params: dict[str, Any], input: dict[str, Any]) -> dict[str, list[float]]:
    """Inverse: invert the scale and the shift of M. `input` holds `model_xy`."""
    (sx, _, tx), (_, sy, ty) = run(params, input)["matrix"]
    x, y = input["model_xy"]
    return {"source_xy": [(x - tx) / sx, (y - ty) / sy]}


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

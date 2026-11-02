"""Section `pre.resize.affine_person_crop`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`. The rotation is 0.
"""

from __future__ import annotations

from typing import Any


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


def inverse(
    params: dict[str, Any], input: dict[str, Any], model_xy: list[float]
) -> list[float]:
    """Inverse: invert the scale and the shift of M."""
    (sx, _, tx), (_, sy, ty) = run(params, input)["matrix"]
    x, y = model_xy
    return [(x - tx) / sx, (y - ty) / sy]

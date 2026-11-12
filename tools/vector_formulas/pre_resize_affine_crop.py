"""Section `pre.resize.affine_crop`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`. A case gives an ROI or a box. A broken invariant
calls `defect`. `CHECKS` holds the named claims that a case can declare:
`check(run, params, input, expect)`.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import numpy as np

from vector_form import defect

f32 = np.float32


def roi(input: dict[str, Any]) -> tuple[Any, ...]:
    """Behaviour: the ROI (c_x, c_y, w, h, rotation) of the case. A box gives rotation 0 in float32."""
    if ("roi" in input) == ("bbox_xyxy" in input):
        defect("a case gives roi or bbox_xyxy")
    if "bbox_xyxy" in input:
        x1, y1, x2, y2 = (f32(value) for value in input["bbox_xyxy"])
        half = f32(0.5)
        given = ((x1 + x2) * half, (y1 + y2) * half, x2 - x1, y2 - y1, 0.0)
    else:
        given = tuple(input["roi"])
    if not all(math.isfinite(float(value)) for value in given):
        raise ValueError("an ROI value is not finite")
    c_x, c_y, w, h, rotation = given
    return f32(c_x), f32(c_y), f32(w), f32(h), float(rotation)


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Behaviour: the float32 centre and size of the crop, and M from three float32 point pairs."""
    c_x, c_y, w, h, rotation = roi(input)
    t_h, t_w = params["target_size"]
    e, half = f32(params["expand_ratio"]), f32(0.5)
    keep = params["maintain_aspect_ratio"]
    w, h = w * e, h * e
    if keep:
        a = f32(t_w / t_h)
        if w > h * a:
            h = w / a
        else:
            w = h * a
    if not (w > 0 and h > 0):
        raise ValueError("the ROI gives an empty crop")
    # The turned points: float64 expressions, each rounded once to float32.
    cs, sn = math.cos(rotation), math.sin(rotation)
    hw, hh = float(w * half), float(h * half)
    p0 = (c_x, c_y)
    p1 = (f32(float(c_x) - hw * cs), f32(float(c_y) - hw * sn))
    if keep:
        p2 = (p1[0] - (p0[1] - p1[1]), p1[1] + (p0[0] - p1[0]))
    else:
        p2 = (f32(float(c_x) + hh * sn), f32(float(c_y) - hh * cs))
    q2 = (0, t_h / 2 + t_w / 2) if keep else (t_w / 2, 0)
    # M solves [x, y, 1] @ M.T = Q for the three pairs, in float64.
    src = np.array([[float(x), float(y), 1.0] for x, y in (p0, p1, p2)])
    dst = np.array([(t_w / 2, t_h / 2), (0, t_h / 2), q2], dtype=np.float32).astype(np.float64)
    matrix = np.linalg.solve(src, dst).T
    return {
        "center": [float(c_x), float(c_y)],
        "crop_w": float(w),
        "crop_h": float(h),
        "matrix": matrix.tolist(),
    }


def inverse(params: dict[str, Any], input: dict[str, Any]) -> dict[str, list[float]]:
    """Inverse: apply the inverse of M. `input` holds `model_xy`."""
    matrix = np.vstack([run(params, input)["matrix"], [0.0, 0.0, 1.0]])
    x, y = input["model_xy"]
    source = np.linalg.solve(matrix, [float(x), float(y), 1.0])
    return {"source_xy": [float(source[0]), float(source[1])]}


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

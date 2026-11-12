"""Section `post.unprojection`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`. A broken invariant calls `defect`.

It uses the Inverse of each resize section through its formula module and, for a
box, the clamp of `clamp_boxes` and the size filter of `min_box_size` (section
`post.object.decode`, ADR-17KN). `CHECKS` holds the named claims that a case can
declare: `check(run, params, input, expect)`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pre_resize_affine_crop
import pre_resize_fit
import pre_resize_letterbox
import pre_resize_stretch

from vector_form import defect

INVERSE = {
    "letterbox": pre_resize_letterbox.inverse,
    "stretch": pre_resize_stretch.inverse,
    "fit": pre_resize_fit.inverse,
    "affine_crop": pre_resize_affine_crop.inverse,
}


def to_model_pixels(
    scale: str, decoded_xy: list[float], input_size: list[int]
) -> list[float]:
    """Behaviour: a decoded position in model-input pixels.

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
    defect(f"unknown scale {scale!r}")


def resize_unproject(
    resize: dict[str, Any], input: dict[str, Any], model_xy: list[float]
) -> list[float]:
    """Sections `pre.resize.<method>`, Inverse: model-input pixels to source pixels."""
    method = resize["method"]
    if method == "none":
        x, y = model_xy
        return [x, y]
    if method not in INVERSE:
        defect(f"unknown resize method {method!r}")
    return INVERSE[method](resize, {**input, "model_xy": model_xy})["source_xy"]


def clamp_to_source(box_xyxy: list[float], src_w: float, src_h: float) -> list[float]:
    """Section `post.object.decode`, field `clamp_boxes`: x to [0, W] and y to [0, H].

    W and H are the source-image size.
    """
    x1, y1, x2, y2 = box_xyxy
    return [
        min(max(x1, 0), src_w),
        min(max(y1, 0), src_h),
        min(max(x2, 0), src_w),
        min(max(y2, 0), src_h),
    ]


def keeps_size(box_xyxy: list[float], min_box_size: float | None) -> bool:
    """Section `post.object.decode`, field `min_box_size`: width and height both more than it.

    The width is x2 - x1 and the height is y2 - y1, with no + 1. Absent: no box is dropped.
    """
    if min_box_size is None:
        return True
    x1, y1, x2, y2 = box_xyxy
    return x2 - x1 > min_box_size and y2 - y1 > min_box_size


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Behaviour: the scale conversion, the Inverse of the resize and, for a box, the clamp
    and the size filter. A box that the size filter drops has `output_xyxy` None."""
    scale, size, resize = params["scale"], params["input_size"], params["resize"]
    if "decoded_xy" in input:
        model_xy = to_model_pixels(scale, input["decoded_xy"], size)
        return {
            "model_xy": model_xy,
            "source_xy": resize_unproject(resize, input, model_xy),
        }
    decoded = input["decoded_xyxy"]
    model_box = [
        *to_model_pixels(scale, decoded[:2], size),
        *to_model_pixels(scale, decoded[2:], size),
    ]
    source_box = [
        *resize_unproject(resize, input, model_box[:2]),
        *resize_unproject(resize, input, model_box[2:]),
    ]
    output = (
        clamp_to_source(source_box, input["src_w"], input["src_h"])
        if params.get("clamp_boxes", True)
        else source_box
    )
    return {
        "model_xyxy": model_box,
        "source_xyxy": source_box,
        "output_xyxy": output if keeps_size(output, params.get("min_box_size")) else None,
    }


def _input_size_follows_resize(run: Callable[..., Any], params: Any, input: Any, expect: Any) -> None:
    """`input_size` is the target size of the resize, or the source size for method none."""
    resize = params["resize"]
    if resize["method"] == "affine_crop":
        if "bbox_xyxy" not in input or "src_w" in input or "src_h" in input:
            defect("an affine case gives a box only")
        if params["input_size"] != resize["target_size"]:
            defect("input_size must equal target_size")
        return
    if "bbox_xyxy" in input or "src_w" not in input or "src_h" not in input:
        defect("a non-affine case gives the source size only")
    if resize["method"] == "none":
        # The host passes the source image unchanged: the model input is the source size.
        if params["input_size"] != [input["src_h"], input["src_w"]]:
            defect("method none: input_size is the source size")
    elif params["input_size"] != resize["target_size"]:
        defect("input_size must equal target_size")


CHECKS: dict[str, Callable[..., None]] = {
    "input-size-follows-resize": _input_size_follows_resize,
}

"""Section `post.unprojection`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`. A broken invariant calls `defect`.

It uses the Inverse of each resize section through its formula module, and the
lower bound of `clamp_boxes` (section `post.det.decode`) for a box. `CHECKS`
holds the named claims that a case can declare: `check(run, params, input, expect)`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pre_resize_affine_person_crop
import pre_resize_fit
import pre_resize_letterbox
import pre_resize_stretch

from vector_form import defect

INVERSE = {
    "letterbox": pre_resize_letterbox.inverse,
    "stretch": pre_resize_stretch.inverse,
    "fit": pre_resize_fit.inverse,
    "affine_person_crop": pre_resize_affine_person_crop.inverse,
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


def clamp_to_lower_bound(box_xyxy: list[float]) -> list[float]:
    """Section `post.det.decode`, field `clamp_boxes`: the lower bound 0 of the source image.

    The spec does not define the upper bound. No vector case reaches it.
    """
    return [max(0, value) for value in box_xyxy]


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Behaviour: the scale conversion, the Inverse of the resize and, for a box, the clamp."""
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
    clamp = params.get("clamp_boxes", True)
    return {
        "model_xyxy": model_box,
        "source_xyxy": source_box,
        "output_xyxy": clamp_to_lower_bound(source_box) if clamp else source_box,
    }


def _input_size_follows_resize(run: Callable[..., Any], params: Any, input: Any, expect: Any) -> None:
    """`input_size` is the target size of the resize, or the source size for method none."""
    resize = params["resize"]
    if resize["method"] == "affine_person_crop":
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


# The spec does not define the upper clamp bound ([0, W] or [0, W - 1]) or the result for a box
# without area. A box case keeps clear of both, so the open questions change no result.
def _clear_of_upper_clamp_bound(
    run: Callable[..., Any], params: Any, input: Any, expect: Any
) -> None:
    if "source_xyxy" not in expect:
        return  # A point case has no box to clamp.
    box = expect["source_xyxy"]
    if not (
        all(x <= input["src_w"] - 1 for x in box[0::2])
        and all(y <= input["src_h"] - 1 for y in box[1::2])
    ):
        defect("a coordinate reaches the upper clamp bound")


def _keeps_area_after_clamp(run: Callable[..., Any], params: Any, input: Any, expect: Any) -> None:
    if "source_xyxy" not in expect:
        return  # A point case has no box to clamp.
    x1, y1, x2, y2 = clamp_to_lower_bound(expect["source_xyxy"])
    if not (x2 > x1 and y2 > y1):
        defect("the clamped box has no area")


CHECKS: dict[str, Callable[..., None]] = {
    "input-size-follows-resize": _input_size_follows_resize,
    "clear-of-upper-clamp-bound": _clear_of_upper_clamp_bound,
    "keeps-area-after-clamp": _keeps_area_after_clamp,
}

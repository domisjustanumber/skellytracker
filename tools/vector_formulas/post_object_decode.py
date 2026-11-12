"""Section `post.object.decode`: a reading of the section text, not an implementation.

The shared decode steps of the `post.object.selection.*` sections. Their formula
modules import this module by name. A broken invariant calls `defect`.
`SELECTION_CHECKS` holds the named claims that a selection case can declare; each
selection module publishes it as its `CHECKS`. The cases of this section are data
only, so this module has no `CHECKS`.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from collections.abc import Callable
from typing import Any

import numpy as np
import post_unprojection

from vector_form import defect

# The default of `min_score`.
DEFAULT_CONFIDENCE = 0.7


@dataclass
class Kept:
    row: int
    box: list[float]
    score: float
    class_id: int


def to_xyxy(box: list[float], box_format: str) -> list[float]:
    a, b, c, d = box
    if box_format == "xyxy":
        return [a, b, c, d]
    if box_format == "xywh":
        return [a, b, a + c, b + d]
    if box_format == "cxcywh":
        return [a - c / 2, b - d / 2, a + c / 2, b + d / 2]
    defect(f"unknown box_format {box_format!r}")


def candidates(
    params: dict[str, Any], inp: dict[str, Any]
) -> list[tuple[list[float], float, int | None]]:
    """Return (box in xyxy, score, model class index or None) for each input row."""
    box_format = params.get("box_format", "xyxy")
    if "rows" in inp:
        fields = inp["fields"]
        i_score = fields.index(params["score_field"])
        i_class = (
            fields.index(params["class_field"]) if "class_field" in params else None
        )
        return [
            (
                to_xyxy(row[0:4], box_format),
                row[i_score],
                None if i_class is None else int(row[i_class]),
            )
            for row in inp["rows"]
        ]
    return [
        (to_xyxy(box, box_format), score, None)
        for box, score in zip(inp["boxes"], inp["scores"], strict=True)
    ]


def resolve_class(model_class: int | None, params: dict[str, Any]) -> int | None:
    """Return the class index of a candidate; None drops it (shared step 1, ADR-88WQ).

    A candidate with no class source has the class index 0, and its sidecar has one class.
    An index outside `classes`, or a gap (None), drops the candidate. With `keep_classes`, a class whose name
    is not in the list drops the candidate.
    """
    classes = params["classes"]
    if model_class is None:
        if len(classes) != 1:
            defect("a sidecar with no class source has exactly one class")
        model_class = 0
    if not 0 <= model_class < len(classes) or classes[model_class] is None:
        return None
    keep = params.get("keep_classes")
    if keep is not None and classes[model_class] not in keep:
        return None
    return model_class


def iou(a: list[float], b: list[float]) -> float:
    """Intersection over union. The area is (x2 - x1) * (y2 - y1): nothing is added."""
    inter_w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    inter_h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = inter_w * inter_h
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def confidence_threshold(params: dict[str, Any]) -> float:
    return params.get("min_score", DEFAULT_CONFIDENCE)


def unproject_clamp_and_filter(
    kept: list[Kept], params: dict[str, Any], inp: dict[str, Any]
) -> list[Kept]:
    """Shared steps 3 to 5: the unprojection, the clamp and the size filter (ADR-17KN).

    Only a case that gives `resize` does these steps. The other cases stop before them.
    `params` has `input_size` and `resize`, and `inp` has `src_w` and `src_h`, as in
    section `post.unprojection`. The kept boxes become the final boxes in source pixels.
    The `input-size-follows-resize` check of `post.unprojection` stops a bad case.
    A case without `resize` must not give the parameters of steps 3 to 5, and its `box_space` is
    only `pixel`. It still does step 6, the confidence threshold. A case with
    `resize.method: affine_person_crop` stops, because a selection case gives no `bbox_xyxy`
    (ADR-0PK7).
    """
    if "resize" not in params:
        unused = [key for key in ("input_size", "min_box_size", "clamp_boxes") if key in params]
        unused += [key for key in ("src_w", "src_h") if key in inp]
        if params.get("box_space", "pixel") != "pixel":
            unused.append("box_space")
        if unused:
            defect(f"{', '.join(unused)} need resize: a case without resize stops before step 3")
        return kept
    if params["resize"]["method"] == "affine_person_crop":
        # shortcut: no end-to-end selection case uses affine; add bbox_xyxy here when one does.
        defect("an end-to-end selection case cannot use affine_person_crop: it needs bbox_xyxy")
    box_params = {
        "scale": params.get("box_space", "pixel"),
        "input_size": params["input_size"],
        "resize": params["resize"],
        **{key: params[key] for key in ("clamp_boxes", "min_box_size") if key in params},
    }
    source = {"src_w": inp["src_w"], "src_h": inp["src_h"]}
    post_unprojection.CHECKS["input-size-follows-resize"](post_unprojection.run, box_params, source, None)
    out = []
    for cand in kept:
        box = post_unprojection.run(box_params, {**source, "decoded_xyxy": cand.box})["output_xyxy"]
        if box is not None:
            out.append(replace(cand, box=box))
    return out


def published(kept: list[Kept], params: dict[str, Any]) -> dict[str, Any]:
    """The `expect` of a selection case: the kept detections in output order.

    Each case gives the boxes as `boxes_xyxy`. `boxes_space` tells the pixel space of the boxes.
    A case with `resize` gives `source`: the final boxes in source-image pixels.
    A case without `resize` gives `model_input`: the boxes in model-input pixels.
    """
    return {
        "kept_rows": [c.row for c in kept],
        "scores": [c.score for c in kept],
        "class_indices": [c.class_id for c in kept],
        "boxes_xyxy": [c.box for c in kept],
        "boxes_space": "source" if "resize" in params else "model_input",
    }


def to_float32(value: Any) -> Any:
    """Round every float in `value` to float32 (a host may compare in float32)."""
    if isinstance(value, float):
        return float(np.float32(value))
    if isinstance(value, dict):
        return {key: to_float32(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_float32(item) for item in value]
    return value


def float32_stable(
    run: Callable[..., dict[str, Any]], params: Any, input: Any, expect: dict[str, Any]
) -> None:
    """The kept rows and class ids do not change when every float is a float32."""
    narrow = run(to_float32(params), to_float32(input))
    if any(expect[key] != narrow[key] for key in ("kept_rows", "class_indices")):
        defect("the result depends on the float width")


SELECTION_CHECKS: dict[str, Callable[..., None]] = {"float32-stable": float32_stable}

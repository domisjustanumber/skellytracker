"""Section `post.det.decode`: a reading of the section text, not an implementation.

The shared decode steps of the `post.det.selection.*` sections. Their formula
modules import this module by name. A broken invariant calls `defect`.
`CHECKS` holds the named claims that a selection case can declare; each selection
module publishes it as its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from typing import Any

import numpy as np

from vector_form import defect

# The default of `confidence_threshold_default`.
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


def resolve_class(
    model_class: int | None,
    params: dict[str, Any],
    *,
    assign_person_without_source: bool,
) -> int | None:
    """Map a model class index to the emitted class id; None drops the candidate."""
    person = params.get("person_class_id", 0)
    if model_class is None:
        if not (assign_person_without_source or params.get("is_person_only", False)):
            defect("a candidate without a class source needs is_person_only here")
        return person
    class_map = params.get("class_id_map")
    emitted = (
        class_map[model_class]
        if class_map is not None
        else params.get("class_id_base", 0) + model_class
    )
    if emitted == -1:
        return None
    if params.get("is_person_only", False) and emitted != person:
        return None
    return emitted


def iou(a: list[float], b: list[float]) -> float:
    """Intersection over union. The area is (x2 - x1) * (y2 - y1): nothing is added."""
    inter_w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    inter_h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = inter_w * inter_h
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def confidence_threshold(params: dict[str, Any]) -> float:
    return params.get("confidence_threshold_default", DEFAULT_CONFIDENCE)


def published(kept: list[Kept]) -> dict[str, Any]:
    """The `expect` of a selection case: the kept detections in output order."""
    return {
        "kept_rows": [c.row for c in kept],
        "scores": [c.score for c in kept],
        "class_ids": [c.class_id for c in kept],
        "boxes_xyxy": [c.box for c in kept],
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
    if any(expect[key] != narrow[key] for key in ("kept_rows", "class_ids")):
        defect("the result depends on the float width")


CHECKS: dict[str, Callable[..., None]] = {"float32-stable": float32_stable}

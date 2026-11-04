"""Section `post.det.selection.nms`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`. The steps stop before the unprojection,
unless the case gives `resize`.
"""

from __future__ import annotations

from typing import Any

import post_det_decode as decode

CHECKS = decode.SELECTION_CHECKS


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Behaviour. A case with `resize` also does shared steps 3 to 5."""
    pool = []
    for row, (box, score, model_class) in enumerate(decode.candidates(params, input)):
        if score <= params["score_threshold"]:
            continue
        class_id = decode.resolve_class(model_class, params)
        if class_id is not None:
            pool.append(decode.Kept(row, box, score, class_id))
    pool.sort(key=lambda c: (-c.score, c.row))
    agnostic = params.get("class_agnostic", False)
    survivors: list[decode.Kept] = []
    for cand in pool:
        suppressed = any(
            (agnostic or kept.class_id == cand.class_id)
            and decode.iou(kept.box, cand.box) > params["iou_threshold"]
            for kept in survivors
        )
        if not suppressed:
            survivors.append(cand)
    if "post_nms_top_k" in params:
        survivors = survivors[: params["post_nms_top_k"]]
    survivors = decode.unproject_clamp_and_filter(survivors, params, input)
    threshold = decode.confidence_threshold(params)
    return decode.published([c for c in survivors if c.score > threshold], params)

"""Section `post.det.selection.top_k`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`. The steps stop before the unprojection.
"""

from __future__ import annotations

import math
from typing import Any

import post_det_decode as decode

from vector_form import defect

CHECKS = decode.CHECKS


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Behaviour (before unprojection)."""
    logits = input["class_logits"]
    activation = params.get("score_activation", "none")
    if activation == "sigmoid":
        p = [[1 / (1 + math.exp(-x)) for x in row] for row in logits]
    elif activation == "none":
        p = logits
    else:
        defect(f"unknown score_activation {activation!r}")
    n_classes = len(p[0])
    flat = sorted(
        range(len(p) * n_classes), key=lambda i: (-p[i // n_classes][i % n_classes], i)
    )
    threshold = decode.confidence_threshold(params)
    kept = []
    for index in flat[: min(params["top_k"], len(flat))]:
        row, model_class = divmod(index, n_classes)
        score = p[row][model_class]
        class_id = decode.resolve_class(
            model_class, params, assign_person_without_source=False
        )
        if class_id is not None and score > threshold:
            box = decode.to_xyxy(input["boxes"][row], params.get("box_format", "xyxy"))
            kept.append(decode.Kept(row, box, score, class_id))
    return decode.published(kept)

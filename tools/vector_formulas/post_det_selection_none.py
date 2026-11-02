"""Section `post.det.selection.none`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`. The steps stop before the unprojection.
"""

from __future__ import annotations

from typing import Any

import post_det_decode as decode


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Behaviour (before unprojection)."""
    threshold = decode.confidence_threshold(params)
    kept = []
    for row, (box, score, model_class) in enumerate(decode.candidates(params, input)):
        class_id = decode.resolve_class(
            model_class, params, assign_person_without_source=False
        )
        if class_id is not None and score > threshold:
            kept.append(decode.Kept(row, box, score, class_id))
    return decode.published(kept)

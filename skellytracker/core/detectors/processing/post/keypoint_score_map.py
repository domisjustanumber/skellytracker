"""The keypoint score map (section `post.keypoint.score_map`): the raw SimCC score to `[0, 1]`."""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from skellytracker.core.model_spec.model import ScoreMapSpec


def map_scores(raw: np.ndarray, score_map: ScoreMapSpec, point_groups: Sequence[str] | None) -> np.ndarray:
    """Return the mapped scores of (..., P) raw decode scores, as float32.

    Implements: post.keypoint.score_map

    `point_groups` is the landmark-schema group of each of the P keypoints. A keypoint of a group in
    `score_map.groups` uses the pair of that group, and each other keypoint uses `a` and `b`. A
    missing keypoint (raw NaN or raw `<= 0`) gets the score 0. Each other keypoint gets
    `1 / (1 + exp(-(a * raw + b)))`, computed in float64 as `0.5 * (1 + tanh(z / 2))`: no overflow,
    and an extreme `z` gives 0 or 1, never NaN. Raise `ValueError` when the map has `groups` and
    `point_groups` does not give the group of each keypoint.
    """
    raw64 = np.asarray(raw, dtype=np.float32).astype(np.float64)
    count = raw64.shape[-1]
    a, b = np.full(count, score_map.a), np.full(count, score_map.b)
    if score_map.groups:
        if point_groups is None or len(point_groups) != count:
            raise ValueError("no-rule: point_groups must give the group of each keypoint")
        names = np.asarray(point_groups)
        for name, pair in score_map.groups.items():
            a[names == name], b[names == name] = pair.a, pair.b
    present = raw64 > 0  # a comparison with NaN is false, so a NaN raw score is missing
    with np.errstate(over="ignore"):  # a > 0 and raw > 0, so an overflow is +inf, and tanh gives 1
        z = a * np.where(present, raw64, 0.0) + b
    return np.where(present, 0.5 * (1.0 + np.tanh(0.5 * z)), 0.0).astype(np.float32)

"""The 2D SimCC decode (section `post.keypoint.decode.simcc`).

The keypoints are in the model-input pixels of the crop. The unprojection to the source image is
the work of `post/unprojection.py`.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def decode_simcc(simcc_x: np.ndarray, simcc_y: np.ndarray, target_size: Sequence[int]) -> dict[str, np.ndarray]:
    """Decode one batch of crops. Return `bins` (B, P, 2), `keypoints` (B, P, 2) and `scores` (B, P).

    Implements: post.keypoint.decode.simcc

    `simcc_x` and `simcc_y` are the raw values, with the shapes (B, P, X_bins) and (B, P, Y_bins).
    `target_size` is `(height, width)` of the model input. The bin of an axis is the argmax of the
    raw values, with no softmax. The score is `peak_y` where `peak_x > peak_y`, else `peak_x`. A
    keypoint with a score `<= 0` gets the bin -1 on each axis. A NaN raw value gives the lowest bin
    of a NaN and a NaN peak. The pixel is `bin * extent / bin_count`, in float64.
    """
    if simcc_x.ndim != 3 or simcc_y.ndim != 3 or simcc_x.shape[:2] != simcc_y.shape[:2]:
        raise ValueError("simcc_x and simcc_y must have the shapes (B, P, bins) with the same B and P")
    height, width = int(target_size[0]), int(target_size[1])
    peak_x, peak_y = np.max(simcc_x, axis=-1), np.max(simcc_y, axis=-1)
    scores = np.where(peak_x > peak_y, peak_y, peak_x)
    bins = np.stack([np.argmax(simcc_x, axis=-1), np.argmax(simcc_y, axis=-1)], axis=-1).astype(np.int64)
    bins[scores <= 0] = -1
    keypoints = np.stack(
        [
            bins[..., 0].astype(np.float64) * width / simcc_x.shape[-1],
            bins[..., 1].astype(np.float64) * height / simcc_y.shape[-1],
        ],
        axis=-1,
    )
    return {"bins": bins, "keypoints": keypoints, "scores": scores}

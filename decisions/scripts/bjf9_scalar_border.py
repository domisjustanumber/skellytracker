#!/usr/bin/env python3
"""Show what a scalar ``borderValue`` fills in ``cv2.warpAffine`` (decision BJF9).

Usage::

    uv run python decisions/scripts/bjf9_scalar_border.py

The script warps a flat ``uint8`` image of 1920x1080x3 with the ``fit`` matrix of a 640x640 target.
Pixel (0, 0) of the result maps to ``y_src = -420``, in the padding. The script prints that pixel
for each ``borderValue`` form, and for ``fit_preprocess`` of skellytracker with ``pad_value=114``.
It writes no file.
"""

from __future__ import annotations

import cv2
import numpy as np

from skellytracker.core.detectors.processing.image_preprocessing import fit_preprocess


def main() -> None:
    print("cv2", cv2.__version__, "numpy", np.__version__)
    src = np.full((1080, 1920, 3), 200, np.uint8)
    s = 640 / 1920
    matrix = np.array([[s, 0, 0], [0, s, 140]], np.float64)
    for value in (114, 114.0, (114,), (114, 114, 114)):
        out = cv2.warpAffine(
            src, matrix, (640, 640), flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT, borderValue=value,
        )
        print(f"warpAffine borderValue={value!r}: pixel (0, 0) = {out[0, 0].tolist()}")
    out = cv2.warpAffine(src, matrix, (640, 640), flags=cv2.INTER_LINEAR)
    print(f"warpAffine with no borderValue: pixel (0, 0) = {out[0, 0].tolist()}")
    padded, _ = fit_preprocess(src, (640, 640), pad_value=114)
    print(f"fit_preprocess pad_value=114: pixel (0, 0) = {padded[0, 0].tolist()}")
    try:
        fit_preprocess(src, (640, 640), pad_value=[114, 114, 114])
        print("fit_preprocess pad_value=[114, 114, 114]: accepted")
    except Exception as error:  # the package type hint wants floats
        print(f"fit_preprocess pad_value=[114, 114, 114]: raises {type(error).__name__}")


if __name__ == "__main__":
    main()

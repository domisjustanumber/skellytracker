"""The normalization of the resized pixels (section `pre.normalize`).

The arithmetic is in float32, with the float32 value of each constant, in the order of the formula.
The cast to `input.dtype` is the last step.
"""
from __future__ import annotations

import numpy as np

from skellytracker.core.model_spec.model import CustomNormalization

INPUT_DTYPES = {"float32": np.float32, "float16": np.float16, "uint8": np.uint8}
# The ImageNet statistics x 255, in R, G, B order.
IMAGENET_MEAN_RGB = (123.675, 116.28, 103.53)
IMAGENET_STD_RGB = (58.395, 57.12, 57.375)


def normalize(
    pixels_bgr: np.ndarray,
    normalization: str | CustomNormalization,
    color_format: str,
    dtype: str | None,
) -> np.ndarray:
    """Return the pixels in the channel order of `color_format`, normalized and cast to `dtype`.

    Implements: pre.normalize

    `pixels_bgr` holds the pixels that the resize gives, in BGR order on the last axis, as uint8 or
    float32 (`input.resize.compute_dtype`). `normalization` is the resolved mode of the precision
    (`InputSpec.normalization_for`). `dtype` is the `input.dtype` entry of the precision. With
    `None`, the result stays in float32. The result keeps the shape of the pixels.
    """
    if pixels_bgr.dtype not in (np.uint8, np.float32) or pixels_bgr.shape[-1:] != (3,):
        raise ValueError(
            f"the pixels must be uint8 or float32 with 3 channels on the last axis, not {pixels_bgr.dtype} {pixels_bgr.shape}"
        )
    if color_format not in ("rgb", "bgr"):
        raise ValueError(f"unsupported color_format: {color_format!r}")
    if dtype is not None and dtype not in INPUT_DTYPES:
        raise ValueError(f"unsupported input dtype: {dtype!r}")
    pixels = (pixels_bgr[..., ::-1] if color_format == "rgb" else pixels_bgr).astype(np.float32)
    if isinstance(normalization, CustomNormalization):
        values = pixels * np.float32(normalization.scale) - np.array(normalization.mean, np.float32)
        values = values / np.array(normalization.std, np.float32)
    elif normalization == "none":
        values = pixels
    elif normalization == "unit_float":
        values = pixels / np.float32(255.0)
    elif normalization == "imagenet":
        mean, std = np.array(IMAGENET_MEAN_RGB, np.float32), np.array(IMAGENET_STD_RGB, np.float32)
        if color_format == "bgr":
            mean, std = mean[::-1], std[::-1]
        values = (pixels - mean) / std
    else:
        raise ValueError(f"unsupported normalization: {normalization!r}")
    return values if dtype is None else values.astype(INPUT_DTYPES[dtype])

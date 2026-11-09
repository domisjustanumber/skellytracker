"""Section `pre.normalize`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`. A broken invariant calls `defect`.

`params` use the sidecar field names.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from vector_form import defect

IMAGENET_MEAN_RGB = (123.675, 116.28, 103.53)
IMAGENET_STD_RGB = (58.395, 57.12, 57.375)
MODES = ("none", "unit_float", "imagenet")
# The values of input.dtype (V-common.input-2) and of input.resize.compute_dtype.
INPUT_DTYPES = {"float32": np.float32, "float16": np.float16, "uint8": np.uint8}
COMPUTE_DTYPES = ("uint8", "float32")


def resolve_mode(
    normalization: Any, by_precision: dict[str, str] | None, precision: str
) -> Any:
    """Resolution order of the section: by precision, then top level. There is no default."""
    if normalization is None:
        raise ValueError("V-pre.normalize-1: input.normalization must be present")
    if by_precision and precision in by_precision:
        return by_precision[precision]
    return normalization


def normalize_pixels(
    pixels_bgr: list[list[int]],
    mode: Any,
    color_format: str | None,
    *,
    dtype: str | None = None,
    compute_dtype: str = "uint8",
) -> tuple[str, list[list[float]]]:
    """Return the channel order of the tensor and the normalized pixels in `dtype`.

    `dtype` None gives the values before the cast (the notes of the vector file).
    """
    if isinstance(mode, dict):
        if mode.get("mode") != "custom":
            defect(f"unknown normalization mode {mode.get('mode')!r}")
        extra = set(mode) - {"mode", "scale", "mean", "std"}
        if extra:
            raise ValueError(f"V-pre.normalize-1: a custom object has the keys {sorted(extra)}")
    elif mode not in MODES:
        defect(f"unknown normalization mode {mode!r}")
    if color_format is None:
        raise ValueError("V-pre.normalize-1: input.color_format must be present")
    order = color_format
    if order not in ("rgb", "bgr"):
        defect(f"unknown color_format {order!r}")
    if compute_dtype not in COMPUTE_DTYPES:
        defect(f"unknown compute_dtype {compute_dtype!r}")
    if dtype is not None and dtype not in INPUT_DTYPES:
        raise ValueError(f"V-common.input-2: {dtype!r} is not a value of input.dtype")
    name = mode.get("mode") if isinstance(mode, dict) else mode
    if dtype == "uint8" and (name != "none" or compute_dtype != "uint8"):
        raise ValueError("V-pre.normalize-3: a uint8 input needs none and an 8-bit resize")
    # An 8-bit resize gives integer pixels from 0 to 255. The pixels are not a sidecar value.
    if compute_dtype == "uint8" and any(
        v != int(v) or not 0 <= v <= 255 for pixel in pixels_bgr for v in pixel
    ):
        raise ValueError("the pixels of an 8-bit resize are integers from 0 to 255")

    out: list[list[float]] = []
    for b, g, r in pixels_bgr:
        values = [b, g, r] if order == "bgr" else [r, g, b]
        if isinstance(mode, dict):
            scale = mode.get("scale", 1.0)
            result = [
                (v * scale - m) / sd
                for v, m, sd in zip(values, mode["mean"], mode["std"], strict=True)
            ]
        elif mode == "none":
            result = [float(v) for v in values]
        elif mode == "unit_float":
            result = [v / 255.0 for v in values]
        else:
            mean, std = list(IMAGENET_MEAN_RGB), list(IMAGENET_STD_RGB)
            if order == "bgr":
                mean, std = mean[::-1], std[::-1]
            result = [(v - m) / sd for v, m, sd in zip(values, mean, std, strict=True)]
        # The cast to input.dtype is the last step of each mode.
        out.append(result if dtype is None else np.asarray(result).astype(INPUT_DTYPES[dtype]).tolist())
    return order, out


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Behaviour: the resolved mode, the channel order of the tensor and the values."""
    mode = resolve_mode(
        params.get("normalization"),
        params.get("normalization_by_precision"),
        params.get("precision") or "fp32",
    )
    order, values = normalize_pixels(
        input["pixels_bgr"],
        mode,
        params.get("color_format"),
        dtype=params.get("dtype"),
        compute_dtype=(params.get("resize") or {}).get("compute_dtype", "uint8"),
    )
    return {
        "resolved_mode": mode if isinstance(mode, str) else mode["mode"],
        "channel_order": order,
        "values": values,
    }

"""Section `pre.normalize`: a reading of the section text, not an implementation.

`tools/make_vectors.py` computes the vectors of the section with it. It has the
calling convention of a reference module: `run(params, input) -> expect`, and a
refusal of the spec raises `ValueError`. A broken invariant calls `defect`.

`params` use the sidecar field names. A `schema_version` that starts with `<`
selects the legacy meaning of `imagenet_bgr`.
"""

from __future__ import annotations

from typing import Any

from vector_form import defect

IMAGENET_MEAN_RGB = (123.675, 116.28, 103.53)
IMAGENET_STD_RGB = (58.395, 57.12, 57.375)


def resolve_mode(
    normalization: Any, by_precision: dict[str, str] | None, precision: str
) -> Any:
    """Resolution order of the section: by precision, then top level, then the default."""
    if by_precision and precision in by_precision:
        return by_precision[precision]
    if normalization is not None:
        return normalization
    return "imagenet_bgr"


def normalize_pixels(
    pixels_bgr: list[list[int]],
    mode: Any,
    color_format: str | None,
    *,
    legacy: bool,
    dtype: str = "float32",
) -> tuple[str, list[list[float]]]:
    """Return the channel order of the tensor and the normalized pixels."""
    if isinstance(mode, dict):
        order = mode.get("color_format") or color_format or "rgb"
    elif mode in ("none", "unit_float"):
        if color_format is None:
            defect(f"{mode} needs color_format")
        order = color_format
    else:
        order = "bgr" if mode == "imagenet_bgr" else "rgb"

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
            result = [int(v) if dtype == "uint8" else float(v) for v in values]
        elif mode == "unit_float":
            result = [v / 255.0 for v in values]
        else:
            mean, std = list(IMAGENET_MEAN_RGB), list(IMAGENET_STD_RGB)
            if order == "bgr" and not legacy:
                mean, std = mean[::-1], std[::-1]
            result = [(v - m) / sd for v, m, sd in zip(values, mean, std, strict=True)]
        out.append(result)
    return order, out


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Behaviour: the resolved mode, the channel order of the tensor and the values."""
    mode = resolve_mode(
        params.get("normalization"),
        params.get("normalization_by_precision"),
        params.get("precision") or "fp32",
    )
    schema_version = params.get("schema_version")
    order, values = normalize_pixels(
        input["pixels_bgr"],
        mode,
        params.get("color_format"),
        legacy=bool(schema_version and schema_version.startswith("<")),
        dtype=params.get("dtype") or "float32",
    )
    return {
        "resolved_mode": mode if isinstance(mode, str) else mode["mode"],
        "channel_order": order,
        "values": values,
    }

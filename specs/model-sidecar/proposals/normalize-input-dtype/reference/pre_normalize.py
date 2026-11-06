"""Reference implementation of the section pre.normalize, as the proposal changes it.

This file uses ASD-STE100 Simplified Technical English.

Section ID: pre.normalize (section file specs/model-sidecar/pre/normalization.md).
Proposal: proposal-normalize-input-dtype@openmmlab-exporter (slug normalize-input-dtype). No
skellytracker decision entry covers it yet.
Target file in skellytracker: specs/model-sidecar/reference/pre_normalize.py.

Source commit: OpenMMLab-Exporter onnx_runtime/preprocess.py::make_normalizer, with its helpers
resolve_normalization, the top-level check and the custom check, at
7bc72b45137faa4b211d05a38f58812ffae5a109 ("Check the top-level normalization when an override
applies"). That host code casts the result of each mode to the input dtype, refuses uint8 with a
mode other than none, has no int8, checks the top-level normalization also when an override
applies, and gives the custom defaults scale 1, mean [0, 0, 0] and std [1, 1, 1]. The host
function has no input.resize.compute_dtype. Thus the compute_dtype part of V-pre.normalize-3 comes
from the text of part 2 of the proposal only.

Full section. skellytracker has no reference implementation of this section. Thus this file
implements the full section as changed: the resolution of the mode for a precision, the channel
order, the four modes, the cast to input.dtype, and the validation rules V-pre.normalize-1, -2
and -3. The section has no inverse.

Imported sections: pre.resize.interpolation (module pre_resize_interpolation, in
specs/model-sidecar/reference/). Its function compute_dtype gives the dtype of
input.resize.compute_dtype. Fixtures: none.

A rule of another section that this module refuses: V-common.input-2 (the values of input.dtype).
The section common.input has no algorithm and no reference module. The cast needs the set of
values, so the function input_dtype refuses a value outside it, with that rule ID.

Vector results: vectors/pre.normalize.yaml of the proposal bundle. make_vectors.py fill (at
skellytracker b065f6e6850686b65bcd08ca944116d739aa62de) wrote expect with this file. It found no
problem. It kept the expect of each of the 15 current cases. The host function make_normalizer
gives the same results for each numeric case that it can express (part 4 of the proposal).
Parity: yolox-person: to run (part 5 of the proposal). rtmw-wholebody133: to run.

The input is pixels of the resized frame in BGR source order, as OpenCV delivers them. The last
axis holds the 3 channels. The pixels have the compute dtype of the resize (uint8 or float32).
For method none, they are the 8-bit source pixels. The output has the same shape, in the channel
order of input.color_format, in input.dtype. The NCHW transpose is not part of this section.

The arithmetic is in float64. Then cast_to_input_dtype casts the result to input.dtype. The host
does the arithmetic in float32, with float32 statistics and scale. On random uint8 pixels, the
float32 results differ by at most 7.2e-07, which is less than the vector tolerance. The host names
imagenet_bgr and imagenet_rgb are not spec modes, so this module does not accept them.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

import pre_resize_interpolation

SECTION = "pre.normalize"
RULE_NORMALIZATION = "V-pre.normalize-1"
RULE_OVERRIDE = "V-pre.normalize-2"
RULE_UINT8 = "V-pre.normalize-3"
RULE_INPUT_DTYPE = "V-common.input-2"
RULE_COLOR_FORMAT = "V-common.input-5"

# The named modes of pre.normalize. A custom object is the fourth mode.
MODES = ("none", "unit_float", "imagenet")
CUSTOM_KEYS = ("mode", "scale", "mean", "std")
# The values of a custom key that is absent.
CUSTOM_DEFAULTS = {"scale": 1.0, "mean": (0.0, 0.0, 0.0), "std": (1.0, 1.0, 1.0)}
PRECISION_KEYS = ("fp32", "fp16")
COLOR_FORMATS = ("bgr", "rgb")
# The values of input.dtype (V-common.input-2). int8 is not a value.
INPUT_DTYPES = {"float32": np.float32, "float16": np.float16, "uint8": np.uint8}
# The ImageNet statistics x 255, in R, G, B order.
IMAGENET_MEAN_RGB = (123.675, 116.28, 103.53)
IMAGENET_STD_RGB = (58.395, 57.12, 57.375)


def is_number(value: Any) -> bool:
    """Return True for an int or a float that is not a bool."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def custom_parameters(normalization: Mapping[str, Any]) -> tuple[float, tuple[float, ...], tuple[float, ...]]:
    """Check a custom normalization object and return scale, mean and std.

    pre.normalize, rule V-pre.normalize-1: the object holds only mode, scale, mean and std. The
    mode must be custom. If scale is present, it must be a positive number. If mean or std is
    present, it must have 3 numbers. Behaviour, the custom row: each key other than mode is
    optional. The defaults are scale 1, mean [0, 0, 0] and std [1, 1, 1].

    Source: the custom check of OpenMMLab-Exporter onnx_runtime/preprocess.py at
    7bc72b45137faa4b211d05a38f58812ffae5a109.
    """
    if normalization.get("mode") != "custom":
        raise ValueError(f"{RULE_NORMALIZATION}: a normalization object must have mode custom: {normalization!r}")
    unknown = sorted(set(normalization) - set(CUSTOM_KEYS))
    if unknown:
        raise ValueError(f"{RULE_NORMALIZATION}: unknown keys of a custom normalization: {unknown}")
    scale = normalization.get("scale", CUSTOM_DEFAULTS["scale"])
    if not is_number(scale) or not scale > 0:
        raise ValueError(f"{RULE_NORMALIZATION}: the custom scale must be a positive number: {scale!r}")
    stats = []
    for key in ("mean", "std"):
        values = normalization.get(key, CUSTOM_DEFAULTS[key])
        if isinstance(values, (str, bytes)) or not isinstance(values, Sequence) or len(values) != 3:
            raise ValueError(f"{RULE_NORMALIZATION}: the custom {key} must have 3 numbers: {values!r}")
        if not all(is_number(value) for value in values):
            raise ValueError(f"{RULE_NORMALIZATION}: the custom {key} must have 3 numbers: {values!r}")
        stats.append(tuple(float(value) for value in values))
    return float(scale), stats[0], stats[1]


def check_top_level(normalization: Any) -> None:
    """Check the top-level input.normalization (V-pre.normalize-1).

    The value must be present. It must be a named mode or a valid custom object. The check applies
    also when normalization_by_precision replaces the value for the selected precision, because the
    rule names input.normalization with no condition.

    Source: the top-level check of OpenMMLab-Exporter onnx_runtime/preprocess.py at
    7bc72b45137faa4b211d05a38f58812ffae5a109.
    """
    if normalization is None:
        raise ValueError(f"{RULE_NORMALIZATION}: input.normalization must be present")
    if isinstance(normalization, Mapping):
        custom_parameters(normalization)
    elif not isinstance(normalization, str) or normalization not in MODES:
        raise ValueError(f"{RULE_NORMALIZATION}: unsupported normalization: {normalization!r}")


def check_overrides(normalization_by_precision: Any) -> dict[str, str]:
    """Check input.normalization_by_precision and return it as a dict (V-pre.normalize-2).

    The keys must be precision keys. The values must be named mode strings. A custom object is not
    a valid value. An absent override gives an empty dict.

    Source: OpenMMLab-Exporter onnx_runtime/preprocess.py::resolve_normalization at
    7bc72b45137faa4b211d05a38f58812ffae5a109.
    """
    if normalization_by_precision is None:
        return {}
    if not isinstance(normalization_by_precision, Mapping):
        raise ValueError(f"{RULE_OVERRIDE}: normalization_by_precision must be a map: {normalization_by_precision!r}")
    unknown = sorted(set(normalization_by_precision) - set(PRECISION_KEYS))
    if unknown:
        raise ValueError(f"{RULE_OVERRIDE}: the keys {unknown} are not precision keys")
    for key, value in normalization_by_precision.items():
        if not isinstance(value, str) or value not in MODES:
            raise ValueError(f"{RULE_OVERRIDE}: the override of {key!r} is not a mode string: {value!r}")
    return dict(normalization_by_precision)


def resolve_normalization(normalization: Any, normalization_by_precision: Any, precision: str) -> Any:
    """Return the normalization of one precision (pre.normalize, Behaviour).

    The order is normalization_by_precision[precision], then the top-level normalization. There
    is no default. The top-level normalization is checked first, also when the override applies
    (V-pre.normalize-1). Then the override is checked (V-pre.normalize-2).

    Source: OpenMMLab-Exporter onnx_runtime/preprocess.py::resolve_normalization at
    7bc72b45137faa4b211d05a38f58812ffae5a109.
    """
    check_top_level(normalization)
    if precision not in PRECISION_KEYS:
        raise ValueError(f"unsupported precision of the caller: {precision!r}")
    return check_overrides(normalization_by_precision).get(precision, normalization)


def mode_name(mode: Any) -> str:
    """Return the name of a resolved mode: the mode string, or custom for a custom object."""
    return "custom" if isinstance(mode, Mapping) else mode


def input_dtype(dtype: Any) -> type:
    """Return the NumPy type of one input.dtype value (V-common.input-2).

    The values are float32, float16 and uint8. int8 is not a value: with none, the pixels 128 to
    255 do not fit in int8, and the other modes give fractional values.

    Source: INPUT_DTYPES of OpenMMLab-Exporter onnx_runtime/preprocess.py at
    7bc72b45137faa4b211d05a38f58812ffae5a109.
    """
    if not isinstance(dtype, str) or dtype not in INPUT_DTYPES:
        raise ValueError(f"{RULE_INPUT_DTYPE}: unsupported input dtype: {dtype!r}")
    return INPUT_DTYPES[dtype]


def check_uint8(name: str, dtype: str, resize: Mapping[str, Any]) -> None:
    """Refuse a uint8 input that the cast cannot give exactly (V-pre.normalize-3).

    If input.dtype of the precision is uint8, the resolved normalization must be none, and
    input.resize.compute_dtype must be absent or uint8. The other modes and a float32 resize give
    fractional values, and their cast to uint8 is not defined.

    Source: the uint8 check of OpenMMLab-Exporter onnx_runtime/preprocess.py::make_normalizer at
    7bc72b45137faa4b211d05a38f58812ffae5a109 (the mode part). The compute_dtype part comes from the
    proposed text.
    """
    if dtype != "uint8":
        return
    if name != "none":
        raise ValueError(f"{RULE_UINT8}: a uint8 input needs the normalization none, not {name!r}")
    if pre_resize_interpolation.compute_dtype(resize) is not np.uint8:
        raise ValueError(f"{RULE_UINT8}: a uint8 input needs input.resize.compute_dtype uint8 or absent")


def source_pixels(pixels_bgr: Any, resize: Mapping[str, Any]) -> np.ndarray:
    """Return the pixels in the compute dtype of the resize (pre.resize.interpolation).

    With uint8 (the default, and method none), the pixels must be integers from 0 to 255. With
    float32, they can be fractional and outside 0 to 255. The pixels are a tensor of the resize,
    not a sidecar value, so a refusal has no rule ID.
    """
    compute = pre_resize_interpolation.compute_dtype(resize)
    pixels = np.asarray(pixels_bgr, np.float64)
    if pixels.ndim < 1 or pixels.shape[-1] != 3:
        raise ValueError(f"the pixels must have 3 channels on the last axis, not shape {pixels.shape}")
    if compute is np.uint8 and not (np.all(pixels == np.round(pixels)) and np.all((pixels >= 0) & (pixels <= 255))):
        raise ValueError("the pixels of an 8-bit resize must be integers from 0 to 255")
    return pixels.astype(compute)


def tensor_order(pixels: np.ndarray, color_format: Any) -> np.ndarray:
    """Put BGR source pixels in the channel order of input.color_format.

    input.color_format must be present (V-pre.normalize-1). It must be rgb or bgr
    (V-common.input-5). rgb reverses the last axis. bgr keeps it.

    Source: OpenMMLab-Exporter onnx_runtime/preprocess.py::make_normalizer (the flip) at
    7bc72b45137faa4b211d05a38f58812ffae5a109.
    """
    if color_format is None:
        raise ValueError(f"{RULE_NORMALIZATION}: input.color_format must be present")
    if color_format not in COLOR_FORMATS:
        raise ValueError(f"{RULE_COLOR_FORMAT}: unsupported color_format: {color_format!r}")
    return pixels[..., ::-1] if color_format == "rgb" else pixels


def normalize_none(pixels: np.ndarray) -> np.ndarray:
    """Mode none: the pixel values unchanged. cast_to_input_dtype then casts them."""
    return pixels.astype(np.float64)


def normalize_unit_float(pixels: np.ndarray) -> np.ndarray:
    """Mode unit_float: pixel / 255 for each channel. An 8-bit pixel gives [0, 1]."""
    return pixels.astype(np.float64) / 255.0


def normalize_imagenet(pixels: np.ndarray, color_format: str) -> np.ndarray:
    """Mode imagenet: (pixel - mean) / std on 0-255 pixels in the order of color_format.

    Each channel uses the statistics of its colour: R mean 123.675 / std 58.395, G 116.28 /
    57.12, B 103.53 / 57.375. For bgr, the statistics are in B, G, R order.
    """
    mean = np.array(IMAGENET_MEAN_RGB, np.float64)
    std = np.array(IMAGENET_STD_RGB, np.float64)
    if color_format == "bgr":
        mean, std = mean[::-1], std[::-1]
    return (pixels.astype(np.float64) - mean) / std


def normalize_custom(pixels: np.ndarray, scale: float, mean: Sequence[float], std: Sequence[float]) -> np.ndarray:
    """Mode custom: (pixel * scale - mean) / std on 0-255 channel values.

    mean and std are in the channel order of input.color_format, the order of pixels.
    """
    values = pixels.astype(np.float64) * float(scale) - np.array(mean, np.float64)
    return values / np.array(std, np.float64)


def cast_to_input_dtype(values: np.ndarray, dtype: str) -> np.ndarray:
    """Cast the result of a mode to input.dtype of the selected precision (Behaviour, the cast).

    Each mode casts its result. A float16 input rounds each value to float16. V-pre.normalize-3
    allows a uint8 input only when the values are integers from 0 to 255, so that cast keeps each
    value.

    Source: OpenMMLab-Exporter onnx_runtime/preprocess.py::make_normalizer (the finish step) at
    7bc72b45137faa4b211d05a38f58812ffae5a109.
    """
    return values.astype(input_dtype(dtype))


def normalize(
    pixels_bgr: Any,
    normalization: Any,
    color_format: Any,
    *,
    normalization_by_precision: Any = None,
    precision: str = "fp32",
    dtype: str | None = None,
    resize: Mapping[str, Any] | None = None,
) -> tuple[str, np.ndarray]:
    """Return the resolved mode and the normalized pixels in the channel order of color_format.

    The steps are: resolve the mode for precision, check the mode and the input dtype, take the
    pixels in the compute dtype of resize, put the channels in the order of color_format, apply
    the mode, and cast to dtype. dtype is the input.dtype entry of precision. resize is the
    input.resize block. Only its compute_dtype is used. dtype None gives the values before the
    cast, in float64.

    Source: OpenMMLab-Exporter onnx_runtime/preprocess.py::make_normalizer at
    7bc72b45137faa4b211d05a38f58812ffae5a109.
    """
    mode = resolve_normalization(normalization, normalization_by_precision, precision)
    name = mode_name(mode)
    if name == "custom":
        scale, mean, std = custom_parameters(mode)
    resize = resize or {}
    if dtype is not None:
        input_dtype(dtype)
        check_uint8(name, dtype, resize)
    pixels = tensor_order(source_pixels(pixels_bgr, resize), color_format)
    if name == "none":
        values = normalize_none(pixels)
    elif name == "unit_float":
        values = normalize_unit_float(pixels)
    elif name == "imagenet":
        values = normalize_imagenet(pixels, color_format)
    else:
        values = normalize_custom(pixels, scale, mean, std)
    return name, values if dtype is None else cast_to_input_dtype(values, dtype)


def check_rules(input_block: Mapping[str, Any]) -> list[str]:
    """Return the rules of this section that one sidecar input block fails, sorted.

    V-pre.normalize-1: input.normalization is present and valid, and input.color_format is
    present. V-pre.normalize-2: the override has precision keys and mode strings. V-pre.normalize-3:
    for each precision whose input.dtype is uint8, the resolved normalization is none, and
    input.resize.compute_dtype is absent or uint8. The rules of other sections are not checked.
    """
    failed = set()
    normalization = input_block.get("normalization")
    try:
        check_top_level(normalization)
    except ValueError:
        failed.add(RULE_NORMALIZATION)
    if input_block.get("color_format") is None:
        failed.add(RULE_NORMALIZATION)
    overrides = input_block.get("normalization_by_precision")
    try:
        check_overrides(overrides)
    except ValueError:
        failed.add(RULE_OVERRIDE)
    resize = input_block.get("resize") or {}
    dtypes = input_block.get("dtype") or {}
    for precision, dtype in dtypes.items():
        if dtype != "uint8":
            continue
        resolved = normalization
        if isinstance(overrides, Mapping) and precision in overrides:
            resolved = overrides[precision]
        if resolved != "none" or resize.get("compute_dtype", "uint8") != "uint8":
            failed.add(RULE_UINT8)
    return sorted(failed)


def run(params: Mapping[str, Any], input: Mapping[str, Any]) -> dict[str, Any]:
    """Return the resolved mode, the channel order of the tensor and the values (vector cases).

    params use the sidecar field names of input: normalization, normalization_by_precision,
    color_format, dtype (the input.dtype entry of the precision) and resize (input.resize; only
    compute_dtype is used). precision defaults to fp32. A case without dtype gives the values
    before the cast.
    """
    mode, values = normalize(
        input["pixels_bgr"],
        params.get("normalization"),
        params.get("color_format"),
        normalization_by_precision=params.get("normalization_by_precision"),
        precision=params.get("precision") or "fp32",
        dtype=params.get("dtype"),
        resize=params.get("resize"),
    )
    return {"resolved_mode": mode, "channel_order": params["color_format"], "values": values.tolist()}

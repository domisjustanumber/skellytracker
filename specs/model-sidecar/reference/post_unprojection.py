"""Reference implementation of the sidecar section post.unprojection (variant of the yolox-person bundle).

Note:

- Section ID: post.unprojection.
- Bundle: model-yolox-person@openmmlab-exporter. The target file is reference/post_unprojection.py.
  The rtmw-wholebody133 model bundle has a different variant of this file, because it holds a
  different set of section modules.
- Source commit: OpenMMLab-Exporter onnx_runtime/unprojection.py::unproject_points,
  onnx_runtime/unprojection.py::unproject_boxes and onnx_runtime/preprocess.py::to_model_pixels at
  5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278. The host code is unchanged at
  18320f4e51660fe0cb9c546441eb9be09d53f339.
- Imported section modules: pre.resize.letterbox (pre_resize_letterbox, the function inverse),
  post.object.decode (post_object_decode, the functions clamp_enabled, clamp and size_mask) and
  pre.resize.affine_person_crop (pre_resize_affine_person_crop, the functions inverse, check_rules
  and case_policy). In skellytracker, the import of pre_resize_affine_person_crop replaced the
  fixture affine_person_crop_inverse of the bundle file (ADR-3S5G).
- Fixtures: pre.resize.stretch (stretch_inverse) and pre.resize.fit (fit_inverse). No place of
  "Imports of other sections" has a module of these sections.
- The method none has no algorithm (its Inverse is the identity), so no section module exists for
  it. This module returns the position unchanged.
- Vector results: specs/model-sidecar/vectors/post.unprojection.yaml of skellytracker
  8351b7f8c20c8db74eb3e547478970e4dceb0308 (SHA-256
  cacfd8c9125777d533d3549e9fcd70cc47b38a4698b324f2cf596c731e09ad82). make_vectors.py fill ran in a
  <payload>/reference folder with only the reference files of this bundle (the staged
  pre_resize_letterbox, pre_resize_interpolation, pre_normalize, post_object_decode,
  post_object_selection_nms and this file). It printed no problems, and the filled file has the same
  expect values as the spec file. All 30 cases pass through run at the tolerance 0.0001.
- Parity: unchanged. The yolox-person parity check ran with this module in place of the host code
  (OpenMMLab-Exporter ADR-3NNK (decisions/scripts/yolox_person_reference_swap.py at 53a48480d0b715f9b726963bce002ddb503b050b)). That run used this file before this note line changed (SHA-256 85d8a64f66f3cd771d0a381d40e9c721b9859a9674ceaebcd6cc73beac2bfac7).

The unprojection has two steps. to_model_pixels converts a decoded position to model-input pixels.
resize_inverse then applies the Inverse of the resize method. A box then gets the clamp of
clamp_boxes and the size filter of min_box_size (section post.object.decode). No step adds or removes a
0.5 offset.
"""

from __future__ import annotations

from typing import Any

import post_object_decode
import pre_resize_affine_person_crop
import pre_resize_letterbox

SCALES = ("pixel", "normalized_01", "normalized_11")
RESIZE_METHODS = ("letterbox", "stretch", "fit", "none", "affine_person_crop")


def required(mapping: dict[str, Any], keys: tuple[str, ...], where: str) -> None:
    """Refuse a mapping that does not have each key of keys (post.unprojection).

    The refusal is a ValueError, as the rules of a reference module state.
    """
    if not isinstance(mapping, dict):
        raise ValueError(f"{where} must be a mapping, not {type(mapping).__name__}")
    missing = [key for key in keys if key not in mapping]
    if missing:
        raise ValueError(f"{where} needs the keys {missing!r}")


def positive_pair(values: Any, name: str) -> tuple[float, float]:
    """Return two positive numbers, or refuse them with ValueError (post.unprojection).

    Source: OpenMMLab-Exporter onnx_runtime/unprojection.py::_target and
    onnx_runtime/unprojection.py::_source at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    try:
        first, second = (float(value) for value in values)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be two numbers, not {values!r}") from error
    if not (first > 0 and second > 0):
        raise ValueError(f"{name} must be positive, not {[first, second]!r}")
    return first, second


def to_model_pixels(scale: str, decoded_xy: list[float], input_size: list[int]) -> list[float]:
    """Convert one decoded position to model-input pixels (post.unprojection, Behaviour).

    scale is object.decode.box_space or keypoint.decode.coordinate_space. input_size is [height, width] of the
    model input. normalized_01 multiplies x by the width and y by the height. normalized_11 maps
    [-1, 1] to [0, width] and to [0, height]. Source: OpenMMLab-Exporter
    onnx_runtime/preprocess.py::to_model_pixels at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    height, width = input_size
    x, y = (float(value) for value in decoded_xy)
    if scale == "pixel":
        return [x, y]
    if scale == "normalized_01":
        return [x * width, y * height]
    if scale == "normalized_11":
        return [(x + 1) / 2 * width, (y + 1) / 2 * height]
    raise ValueError(f"unsupported coordinate scale: {scale!r}")


def stretch_inverse(params: dict[str, Any], input: dict[str, Any]) -> dict[str, list[float]]:
    """Fixture of pre.resize.stretch. The Inverse: x_src = x * src_w / T_w, y_src = y * src_h / T_h.

    params is the input.resize block. input holds src_w, src_h and model_xy. A size that is not
    positive gives ValueError. Source: OpenMMLab-Exporter onnx_runtime/unprojection.py::stretch_geometry
    and onnx_runtime/unprojection.py::_inverse_axes (the stretch branch) at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    required(params, ("target_size",), "the stretch resize")
    required(input, ("src_w", "src_h", "model_xy"), "the stretch input")
    target_h, target_w = positive_pair(params["target_size"], "target_size")
    src_w, src_h = positive_pair([input["src_w"], input["src_h"]], "the source size")
    x, y = input["model_xy"]
    return {"source_xy": [x * (src_w / target_w), y * (src_h / target_h)]}


def fit_inverse(params: dict[str, Any], input: dict[str, Any]) -> dict[str, list[float]]:
    """Fixture of pre.resize.fit. The Inverse: x_src = (x - left) / s, y_src = (y - top) / s.

    s = min(T_w / src_w, T_h / src_h), left = (T_w - src_w * s) / 2 and top = (T_h - src_h * s) / 2.
    The values are not rounded. params is the input.resize block. input holds src_w, src_h and
    model_xy. A size that is not positive gives ValueError. Source: OpenMMLab-Exporter
    onnx_runtime/unprojection.py::fit_geometry and onnx_runtime/unprojection.py::_inverse_axes (the
    fit branch) at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    required(params, ("target_size",), "the fit resize")
    required(input, ("src_w", "src_h", "model_xy"), "the fit input")
    target_h, target_w = positive_pair(params["target_size"], "target_size")
    src_w, src_h = positive_pair([input["src_w"], input["src_h"]], "the source size")
    scale = min(target_w / src_w, target_h / src_h)
    left = (target_w - src_w * scale) / 2
    top = (target_h - src_h * scale) / 2
    x, y = input["model_xy"]
    return {"source_xy": [(x - left) / scale, (y - top) / scale]}


def resize_inverse(
    resize: dict[str, Any], input: dict[str, Any], model_xy: list[float]
) -> list[float]:
    """Map one position in model-input pixels to source pixels (post.unprojection, Behaviour).

    resize is the input.resize block. input holds src_w and src_h, or bbox_xyxy for
    affine_person_crop. letterbox calls pre_resize_letterbox.inverse. affine_person_crop calls
    pre_resize_affine_person_crop.inverse. resize holds target_size and the optional expand_ratio
    and maintain_aspect_ratio. A target_size that is not two positive numbers, and an expand_ratio or
    a maintain_aspect_ratio that breaks V-pre.resize.affine_person_crop-1, give ValueError. stretch
    and fit use the fixtures of this module. none returns the position unchanged.
    Source: OpenMMLab-Exporter onnx_runtime/unprojection.py::inverse_points at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    required(resize, ("method",), "input.resize")
    method = resize["method"]
    if method not in RESIZE_METHODS:
        raise ValueError(f"unsupported resize method: {method!r}")
    if method == "none":
        x, y = model_xy
        return [x, y]
    if method == "affine_person_crop":
        required(input, ("bbox_xyxy",), "the input of an affine_person_crop unprojection")
    else:
        required(input, ("src_w", "src_h"), f"the input of a {method} unprojection")
    given = {**input, "model_xy": model_xy}
    if method == "letterbox":
        required(resize, ("target_size",), "the letterbox resize")
        return pre_resize_letterbox.inverse(resize, given)["source_xy"]
    if method == "stretch":
        return stretch_inverse(resize, given)["source_xy"]
    if method == "fit":
        return fit_inverse(resize, given)["source_xy"]
    required(resize, ("target_size",), "the affine_person_crop resize")
    positive_pair(resize["target_size"], "target_size")
    policy = pre_resize_affine_person_crop.case_policy(resize)
    resolved = {"method": method, "target_size": resize["target_size"], "crop_policy": policy}
    failed = pre_resize_affine_person_crop.check_rules({"sizes": {"case": {"input": {"resize": resolved}}}})
    if failed:
        raise ValueError(f"{failed[0]}: the crop_policy values {policy!r} are not valid")
    return pre_resize_affine_person_crop.inverse(resize, given)["source_xy"]


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Unproject one decoded point or one decoded xyxy box (post.unprojection).

    params holds scale, input_size and resize, and for a box clamp_boxes (default true) and
    min_box_size (optional). The keys clamp_boxes and min_box_size have the names of the decode
    block, so params goes to post_object_decode as the decode block. input holds decoded_xy or
    decoded_xyxy, and src_w and src_h, or bbox_xyxy for affine_person_crop. A point gives model_xy
    and source_xy. A box gives model_xyxy, source_xyxy and output_xyxy. output_xyxy is None for a
    box that the size filter drops. Source: OpenMMLab-Exporter
    onnx_runtime/unprojection.py::unproject_points and onnx_runtime/unprojection.py::unproject_boxes
    at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    required(params, ("scale", "input_size", "resize"), "the params of post.unprojection")
    required(input, (), "the input of post.unprojection")
    scale, input_size, resize = params["scale"], params["input_size"], params["resize"]
    if scale not in SCALES:
        raise ValueError(f"unsupported coordinate scale: {scale!r}")
    if "decoded_xy" in input:
        model_xy = to_model_pixels(scale, input["decoded_xy"], input_size)
        return {"model_xy": model_xy, "source_xy": resize_inverse(resize, input, model_xy)}
    if "decoded_xyxy" not in input:
        raise ValueError("the input needs decoded_xy or decoded_xyxy")
    decoded = input["decoded_xyxy"]
    model_box = [
        *to_model_pixels(scale, decoded[:2], input_size),
        *to_model_pixels(scale, decoded[2:], input_size),
    ]
    source_box = [
        *resize_inverse(resize, input, model_box[:2]),
        *resize_inverse(resize, input, model_box[2:]),
    ]
    output = source_box
    if post_object_decode.clamp_enabled(params):
        required(input, ("src_w", "src_h"), "the clamp of a box")
        clamped = post_object_decode.clamp([source_box], params, input["src_w"], input["src_h"])[0]
        output = [float(value) for value in clamped]
    keep = bool(post_object_decode.size_mask([output], params)[0])
    return {
        "model_xyxy": model_box,
        "source_xyxy": source_box,
        "output_xyxy": output if keep else None,
    }

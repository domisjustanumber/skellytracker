"""Reference implementation of section `post.det.decode` (the shared decode steps).

Section ID: post.det.decode (specs/model-sidecar/post/object/decode.md, heading
"Selection behaviour": the score order with its tie rule and shared steps 1, 2, 4, 5 and 6;
ADR-17KN).

Source commit: OpenMMLab-Exporter 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278 (ADR-H1EF), unchanged
at 18320f4e51660fe0cb9c546441eb9be09d53f339. Host functions: OpenMMLab-Exporter
onnx_runtime/decode_nms.py::convert_boxes, ::_class_mapper, ::NmsDecoder.map_classes,
::NmsDecoder._candidates (the np.rint of class_field), ::NmsDecoder._no_source_class,
::NmsDecoder.__init__ (the field defaults and the thresholds), ::NmsDecoder.decode (the sort and
the size filter) and onnx_runtime/unprojection.py::clamp_boxes.

Vector results: vectors/post.det.decode.yaml has 2 cases. Both are data-only validator cases
(`function: none`). No function of this module runs them. `make_vectors.py fill` in a payload
layout gives no problem and no change of `expect`. The numeric cases of other sections also ran
through the functions of this module for the steps that they show (score order, class ids, box
format, clamp, size filter, confidence threshold), with the tolerance of each file. All pass:
post.det.selection.none 12 of 12 (in float64 and in float32), post.det.selection.top_k 10 of 10
(`score_order` on the flattened scores; the unprojection of one case comes from
post.unprojection), post.det.selection.nms 24 of 24 (through the post.det.selection.nms module,
which calls this module; `score_order` also gives the output order of the 23 cases with a kept
row) and the 13 box cases of post.unprojection (`output_xyxy` from `source_xyxy`).

Parity: unchanged. The yolox-person parity check ran with this module in place of the host code
(OpenMMLab-Exporter ADR-3NNK (decisions/scripts/yolox_person_reference_swap.py at 53a48480d0b715f9b726963bce002ddb503b050b)). That run used this file before this note line changed (SHA-256 f1110a43571abb1f2f0e6105b4af2b3b2f23be63a0b498adbfc77f76e1e8cf56).

Imports of other sections: none. Fixtures: none.

Scope. The module has one function for each algorithm of this section. The selection sections
(post.det.selection.none, post.det.selection.top_k and post.det.selection.nms) set the order of
the steps and call these functions. Shared step 3 (the unprojection) and the conversion of
`box_scale` to model-input pixels are algorithms of post.unprojection. They are not in this
module. Shared step 2 is `to_xyxy` of this module. The `box_scale` conversion of
post.unprojection follows it.

Validation. A function refuses a value of a field that it reads with ValueError, when the value
breaks V-post.det.decode-5, -6, -7, -8 or -9 in the decode block alone. The length rule of
V-post.det.decode-6 and the cross rule of V-post.det.decode-7 need the model or the full
sidecar. The validator checks them. These functions do not.

Comparisons. Each score comparison and each size comparison is in float64. A float16 or float32
value converts to float64 exactly. Thus, the result depends only on the values, not on the dtype.

The module has no `run`: the cases of this section are data only.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

BOX_FORMATS = ("xyxy", "xywh", "cxcywh")
DEFAULT_CONFIDENCE = 0.7


def integer_value(value: Any, rule: str, name: str) -> int:
    """Return `value` as an int. Refuse a value that is not a non-negative integer.

    A bool, a float, a string or None is not an integer. The message starts with `rule`.
    """
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 0:
        raise ValueError(f"{rule}: {name} must be a non-negative integer, got {value!r}")
    return int(value)


def number_value(value: Any, rule: str, name: str) -> float:
    """Return `value` as a float. Refuse a value that is not a real number.

    A bool, a string or None is not a number. The message starts with `rule`.
    """
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValueError(f"{rule}: {name} must be a number, got {value!r}")
    return float(value)


def score_order(scores: Any) -> np.ndarray:
    """Selection behaviour of post.det.decode: return the indexes of `scores` by descending score.

    A tie goes to the lower index. An input with more than one dimension flattens in row-major
    order. For `top_k`, the caller gives the `[Q, C]` scores, so the index is the flattened index
    `row * C + class`. For each other score ordering, the caller gives one score for each row,
    so the index is the row index. The result is int64. The comparison is in float64.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder.decode (the sort
    `np.lexsort((axis_index, rows, -det_scores))`) at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    The host also breaks a tie of one row by the class index. The section text does not state
    this case.
    """
    flat = np.asarray(scores, dtype=np.float64).reshape(-1)
    return np.argsort(-flat, kind="stable").astype(np.int64)


def to_xyxy(boxes: Any, decode: Mapping[str, Any]) -> np.ndarray:
    """Shared step 2 of post.det.decode: convert `(..., 4)` boxes from `box_format` to xyxy.

    `box_format` is `xyxy` (the default), `xywh` (the top-left corner and the size) or `cxcywh`
    (the centre and the size). A float32 or float64 input keeps its dtype. Another input dtype
    gives float64. The result is a new array. The function does not apply `box_scale`: that
    conversion is in post.unprojection.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::convert_boxes at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    box_format = decode.get("box_format", "xyxy")
    if box_format not in BOX_FORMATS:
        raise ValueError(f"V-post.det.decode-5: unsupported box_format {box_format!r}")
    given = np.asarray(boxes)
    dtype = given.dtype if given.dtype in (np.float32, np.float64) else np.float64
    out = np.array(given, dtype=dtype, copy=True)
    if out.shape[-1:] != (4,):
        raise ValueError(f"boxes must have shape (..., 4), not {out.shape}")
    a, b, c, d = (out[..., i].copy() for i in range(4))
    if box_format == "xywh":
        out[..., 2] = a + c
        out[..., 3] = b + d
    elif box_format == "cxcywh":
        half_w = c * out.dtype.type(0.5)
        half_h = d * out.dtype.type(0.5)
        out[..., 0] = a - half_w
        out[..., 1] = b - half_h
        out[..., 2] = a + half_w
        out[..., 3] = b + half_h
    return out


def class_id_map(decode: Mapping[str, Any]) -> np.ndarray | None:
    """Shared step 1 of post.det.decode: return `decode.class_id_map` as int64, or None.

    The map is a list of integers. Each value must be -1 or a non-negative integer. A bool or a
    float is not an integer. The non-negative values must be unique. A `$ref` must be resolved
    before the call.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::_class_mapper at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    raw = decode.get("class_id_map")
    if raw is None:
        return None
    if isinstance(raw, (str, Mapping)):
        raise ValueError("class_id_map must be a resolved list of integers, not a $ref")
    items = np.asarray(raw, dtype=object)
    if items.ndim != 1:
        raise ValueError(f"V-post.det.decode-6: class_id_map must be a list, got shape {items.shape}")
    for item in items:
        if not (isinstance(item, (int, np.integer)) and not isinstance(item, bool) and item >= -1):
            raise ValueError(f"V-post.det.decode-6: a class_id_map value must be -1 or a non-negative integer, got {item!r}")
    values = np.array([int(item) for item in items], dtype=np.int64)
    kept = values[values >= 0]
    if np.unique(kept).size != kept.size:
        raise ValueError("V-post.det.decode-6: the non-negative values of class_id_map must be unique")
    return values


def person_class_id(decode: Mapping[str, Any]) -> int:
    """Shared step 1 of post.det.decode: return `decode.person_class_id` (the default is 0).

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder.__init__ at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    return integer_value(decode.get("person_class_id", 0), "V-post.det.decode-7", "person_class_id")


def map_classes(indexes: Any, decode: Mapping[str, Any]) -> np.ndarray:
    """Shared step 1 of post.det.decode: map model class indexes to emitted class ids.

    The result is int64. The value -1 marks a candidate that the caller must drop.

    - `class_id_map` takes precedence over `class_id_base`. The emitted class id is
      `class_id_map[index]`, else `class_id_base + index` (the default base is 0).
    - A map value of -1 gives -1.
    - When `is_person_only` is true, each class id that is not `person_class_id` (default 0)
      gives -1.
    - A floating index rounds to the nearest integer, half to even (a `class_field` column of a
      float tensor).
    - A negative index, or an index outside `class_id_map`, gives -1. The section text does not
      state this case.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder.map_classes and the
    `np.rint` of NmsDecoder._candidates at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    given = np.asarray(indexes)
    if np.issubdtype(given.dtype, np.floating):
        given = np.rint(given)
    index = given.astype(np.int64)
    values = class_id_map(decode)
    if values is not None:
        inside = (index >= 0) & (index < values.size)
        safe = np.clip(index, 0, max(values.size - 1, 0))
        mapped = np.where(inside, values[safe] if values.size else -1, -1)
    else:
        base = integer_value(decode.get("class_id_base", 0), "V-post.det.decode-7", "class_id_base")
        mapped = np.where(index >= 0, base + index, -1)
    if is_person_only(decode):
        mapped = np.where(mapped == person_class_id(decode), mapped, -1)
    return np.asarray(mapped, np.int64)


def is_person_only(decode: Mapping[str, Any]) -> bool:
    """Shared step 1 of post.det.decode: return `decode.is_person_only` (the default is false).

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder.__init__ at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    value = decode.get("is_person_only", False)
    if not isinstance(value, bool):
        raise ValueError(f"V-post.det.decode-5: is_person_only must be a boolean, got {value!r}")
    return value


def no_source_class(decode: Mapping[str, Any]) -> int:
    """Shared step 1 of post.det.decode: the class id of a candidate with no class source.

    A candidate with no class source gets its class only from `is_person_only`: the class id is
    `person_class_id` (default 0). A decode block without `is_person_only: true` fails
    V-post.det.decode-9, so the function refuses it.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder._no_source_class at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278. The host does not refuse: without
    `is_person_only` it maps the model class index 0.
    """
    if not is_person_only(decode):
        raise ValueError("V-post.det.decode-9: a decode block with no class source must set is_person_only: true")
    return person_class_id(decode)


def clamp_enabled(decode: Mapping[str, Any]) -> bool:
    """Shared step 4 of post.det.decode: return `decode.clamp_boxes` (the default is true).

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder.__init__ at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    value = decode.get("clamp_boxes", True)
    if not isinstance(value, bool):
        raise ValueError(f"V-post.det.decode-5: clamp_boxes must be a boolean, got {value!r}")
    return value


def clamp(boxes_xyxy: Any, decode: Mapping[str, Any], src_w: float, src_h: float) -> np.ndarray:
    """Shared step 4 of post.det.decode: clamp `(..., 4)` xyxy source-image boxes.

    When `clamp_boxes` is true, each x goes to `[0, src_w]` and each y goes to `[0, src_h]`.
    `src_w` and `src_h` are the width and the height of the source image. When `clamp_boxes` is
    false, the boxes do not change. The clamp keeps a box with zero area. The result is a new
    array. A float32 or float64 input keeps its dtype. Another input dtype gives float64.

    Source: OpenMMLab-Exporter onnx_runtime/unprojection.py::clamp_boxes at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    given = np.asarray(boxes_xyxy)
    dtype = given.dtype if given.dtype in (np.float32, np.float64) else np.float64
    out = np.array(given, dtype=dtype, copy=True)
    if out.shape[-1:] != (4,):
        raise ValueError(f"boxes must have shape (..., 4), not {out.shape}")
    if clamp_enabled(decode):
        out[..., 0::2] = out[..., 0::2].clip(0, src_w)
        out[..., 1::2] = out[..., 1::2].clip(0, src_h)
    return out


def size_mask(boxes_xyxy: Any, decode: Mapping[str, Any]) -> np.ndarray:
    """Shared step 5 of post.det.decode: return the mask of the boxes that the size filter keeps.

    The boxes are `(..., 4)` xyxy in source-image pixels, after step 4. When `min_box_size` is
    present, a box stays only when `x2 - x1 > min_box_size` and `y2 - y1 > min_box_size`. The
    width and the height have no `+1`. When `min_box_size` is absent, each box stays. The
    subtraction and the comparison are in float64.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder.decode (the `keep` mask) and
    ::NmsDecoder.__init__ (the check of `min_box_size`) at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278. The host compares a float32 box with the size in
    float32.
    """
    boxes = np.asarray(boxes_xyxy, dtype=np.float64)
    if boxes.shape[-1:] != (4,):
        raise ValueError(f"boxes must have shape (..., 4), not {boxes.shape}")
    raw = decode.get("min_box_size")
    if raw is None:
        return np.ones(boxes.shape[:-1], dtype=bool)
    size = number_value(raw, "V-post.det.decode-8", "min_box_size")
    if not size >= 0:
        raise ValueError(f"V-post.det.decode-8: min_box_size must be a non-negative number, got {raw!r}")
    return ((boxes[..., 2] - boxes[..., 0]) > size) & ((boxes[..., 3] - boxes[..., 1]) > size)


def confidence_threshold(decode: Mapping[str, Any], override: float | None = None) -> float:
    """Shared step 6 of post.det.decode: return the final confidence threshold.

    The threshold is `override` when the caller gives it (host policy), else
    `confidence_threshold_default`, else 0.7. The sidecar value must be a number in `[0, 1]`.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder.__init__ (the argument
    `confidence_threshold`) at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    rule = "V-post.det.decode-8"
    default = number_value(
        decode.get("confidence_threshold_default", DEFAULT_CONFIDENCE), rule, "confidence_threshold_default"
    )
    if not 0.0 <= default <= 1.0:
        raise ValueError(f"{rule}: confidence_threshold_default must be in [0, 1], got {default!r}")
    if override is None:
        return default
    return number_value(override, "confidence threshold override", "the override")


def confidence_mask(scores: Any, threshold: float) -> np.ndarray:
    """Shared step 6 of post.det.decode: return the mask of the scores that stay.

    The comparison is strict: `score > threshold`. A score equal to the threshold goes. The
    comparison is in float64.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder.__init__ (the
    `score_threshold` of the NMS graph, which the host sets to `max(nms.score_threshold,
    confidence threshold)`) at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278. The host compares in
    float32.
    """
    limit = number_value(threshold, "confidence threshold", "threshold")
    return np.asarray(scores, dtype=np.float64) > limit

"""Reference implementation of section `post.object.decode` (the shared decode steps).

Section ID: post.object.decode (specs/model-sidecar/post/object/decode.md, heading
"Selection behaviour": the score order with its tie rule and shared steps 1, 2, 4, 5 and 6;
ADR-17KN).

Source commit: OpenMMLab-Exporter 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278 (ADR-H1EF), unchanged
at 18320f4e51660fe0cb9c546441eb9be09d53f339. Host functions: OpenMMLab-Exporter
onnx_runtime/decode_nms.py::convert_boxes, ::NmsDecoder._candidates (the np.rint of
class_field), ::NmsDecoder.__init__ (the field defaults and the thresholds), ::NmsDecoder.decode
(the sort and the size filter) and onnx_runtime/unprojection.py::clamp_boxes. The class filter of
shared step 1 (`class_names`, `filter_classes` and `no_source_class`) comes from the section text
(skellytracker ADR-88WQ). It replaces the class map of the host (::_class_mapper,
::NmsDecoder.map_classes and ::NmsDecoder._no_source_class).

Vector results: vectors/post.object.decode.yaml has 4 cases. Each is a data-only validator case
(`function: none`). No function of this module runs them. `make_vectors.py fill` in a payload
layout gives no problem and no change of `expect`. The numeric cases of other sections also ran
through the functions of this module for the steps that they show (score order, class ids, box
format, clamp, size filter, confidence threshold), with the tolerance of each file. All pass:
post.object.selection.none 12 of 12 (in float64 and in float32), post.object.selection.top_k 10 of 10
(`score_order` on the flattened scores; the unprojection of one case comes from
post.unprojection), post.object.selection.nms 24 of 24 (through the post.object.selection.nms module,
which calls this module; `score_order` also gives the output order of the 23 cases with a kept
row) and the 13 box cases of post.unprojection (`output_xyxy` from `source_xyxy`).

Parity: unchanged. The yolox-person parity check ran with this module in place of the host code
(OpenMMLab-Exporter ADR-3NNK (decisions/scripts/yolox_person_reference_swap.py at 53a48480d0b715f9b726963bce002ddb503b050b)). That run used this file before this note line changed (SHA-256 f1110a43571abb1f2f0e6105b4af2b3b2f23be63a0b498adbfc77f76e1e8cf56).

Imports of other sections: none. Fixtures: none.

Scope. The module has one function for each algorithm of this section. The selection sections
(post.object.selection.none, post.object.selection.top_k and post.object.selection.nms) set the order of
the steps and call these functions. Shared step 3 (the unprojection) and the conversion of
`box_space` to model-input pixels are algorithms of post.unprojection. They are not in this
module. Shared step 2 is `to_xyxy` of this module. The `box_space` conversion of
post.unprojection follows it.

Validation. A function refuses a value of a field that it reads with ValueError, when the value
breaks V-post.object.decode-5, -8, -9, -10 or -11 in the object block alone. The length rule of
V-post.object.decode-10 (the class count `C`) needs the model or the full sidecar. The validator
checks it. These functions do not.

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


def number_value(value: Any, rule: str, name: str) -> float:
    """Return `value` as a float. Refuse a value that is not a real number.

    A bool, a string or None is not a number. The message starts with `rule`.
    """
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValueError(f"{rule}: {name} must be a number, got {value!r}")
    return float(value)


def score_order(scores: Any) -> np.ndarray:
    """Selection behaviour of post.object.decode: return the indexes of `scores` by descending score.

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
    """Shared step 2 of post.object.decode: convert `(..., 4)` boxes from `box_format` to xyxy.

    `box_format` is `xyxy` (the default), `xywh` (the top-left corner and the size) or `cxcywh`
    (the centre and the size). A float32 or float64 input keeps its dtype. Another input dtype
    gives float64. The result is a new array. The function does not apply `box_space`: that
    conversion is in post.unprojection.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::convert_boxes at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    box_format = decode.get("box_format", "xyxy")
    if box_format not in BOX_FORMATS:
        raise ValueError(f"V-post.object.decode-5: unsupported box_format {box_format!r}")
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


def class_names(classes: Any) -> list[str | None]:
    """Shared step 1 of post.object.decode: return `object.classes` as a list of names.

    Each item is a non-empty string or None (a gap). At least one item is a string, and the
    strings are unique (V-post.object.decode-10). A `$ref` must be resolved before the call. The
    length rule needs the model, so the function does not check it.

    Source: the text of shared step 1 and of V-post.object.decode-10 (skellytracker ADR-88WQ).
    """
    if isinstance(classes, (str, Mapping)) or not isinstance(classes, (list, tuple)) or not classes:
        raise ValueError(f"V-post.object.decode-10: classes must be a resolved non-empty list of names, got {classes!r}")
    if not all(name is None or (isinstance(name, str) and name) for name in classes):
        raise ValueError(f"V-post.object.decode-10: each class must be a non-empty string or null, got {classes!r}")
    names = [name for name in classes if name is not None]
    if not names or len(set(names)) != len(names):
        raise ValueError(f"V-post.object.decode-10: the class names must be unique, with at least one, got {classes!r}")
    return list(classes)


def keep_names(classes: list[str | None], decode: Mapping[str, Any]) -> set[str] | None:
    """Shared step 1 of post.object.decode: return `object.decode.keep_classes` as a set, or None.

    None means that the host keeps each class that is not a gap. The list must be a non-empty
    list of unique, non-empty strings with no null, and each name must be in `classes`
    (V-post.object.decode-11).

    Source: the text of shared step 1 and of V-post.object.decode-11 (skellytracker ADR-88WQ).
    """
    raw = decode.get("keep_classes")
    if raw is None:
        return None
    if isinstance(raw, (str, Mapping)) or not isinstance(raw, (list, tuple)) or not raw:
        raise ValueError(f"V-post.object.decode-11: keep_classes must be a non-empty list of names, got {raw!r}")
    if not all(isinstance(name, str) and name in classes for name in raw) or len(set(raw)) != len(raw):
        raise ValueError(f"V-post.object.decode-11: keep_classes must name unique classes of object.classes, got {raw!r}")
    return set(raw)


def filter_classes(indexes: Any, classes: Any, decode: Mapping[str, Any]) -> np.ndarray:
    """Shared step 1 of post.object.decode: return the class index of each candidate, or -1.

    The result is int64. The value -1 marks a candidate that the caller must drop.

    - A floating index rounds to the nearest integer, half to even (a `class_field` column of a
      float tensor).
    - An index outside `[0, C)`, with `C = len(classes)`, gives -1.
    - An index whose class `classes[index]` is None (a gap) gives -1, also with no `keep_classes`.
    - When `keep_classes` is present, an index whose name `classes[index]` is not in
      `keep_classes` gives -1.

    Source: the text of shared step 1 (skellytracker ADR-88WQ). The rounding is the `np.rint` of
    OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder._candidates at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    names = class_names(classes)
    keep = keep_names(names, decode)
    given = np.asarray(indexes)
    if np.issubdtype(given.dtype, np.floating):
        given = np.rint(given)
    index = given.astype(np.int64)
    inside = (index >= 0) & (index < len(names))
    kept = np.asarray([name is not None and (keep is None or name in keep) for name in names], dtype=bool)
    inside &= kept[np.clip(index, 0, len(names) - 1)]
    return np.where(inside, index, -1).astype(np.int64)


def no_source_class(classes: Any) -> int:
    """Shared step 1 of post.object.decode: the class index of a candidate with no class source.

    A candidate with no class source has the class index 0. Its sidecar has exactly one name in
    `object.classes` (V-post.object.decode-9), so the function refuses another count.

    Source: the text of shared step 1 and of V-post.object.decode-9 (skellytracker ADR-88WQ).
    """
    names = class_names(classes)
    if len(names) != 1:
        raise ValueError(f"V-post.object.decode-9: a sidecar with no class source must have one class, got {names!r}")
    return 0


def clamp_enabled(decode: Mapping[str, Any]) -> bool:
    """Shared step 4 of post.object.decode: return `decode.clamp_boxes` (the default is true).

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder.__init__ at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    value = decode.get("clamp_boxes", True)
    if not isinstance(value, bool):
        raise ValueError(f"V-post.object.decode-5: clamp_boxes must be a boolean, got {value!r}")
    return value


def clamp(boxes_xyxy: Any, decode: Mapping[str, Any], src_w: float, src_h: float) -> np.ndarray:
    """Shared step 4 of post.object.decode: clamp `(..., 4)` xyxy source-image boxes.

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
    """Shared step 5 of post.object.decode: return the mask of the boxes that the size filter keeps.

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
    size = number_value(raw, "V-post.object.decode-8", "min_box_size")
    if not size >= 0:
        raise ValueError(f"V-post.object.decode-8: min_box_size must be a non-negative number, got {raw!r}")
    return ((boxes[..., 2] - boxes[..., 0]) > size) & ((boxes[..., 3] - boxes[..., 1]) > size)


def confidence_threshold(decode: Mapping[str, Any], override: float | None = None) -> float:
    """Shared step 6 of post.object.decode: return the final confidence threshold.

    The threshold is `override` when the caller gives it (host policy), else `min_score`, else
    0.7. The sidecar value must be a number in `[0, 1]`.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder.__init__ (the argument
    `confidence_threshold`) at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    rule = "V-post.object.decode-8"
    default = number_value(decode.get("min_score", DEFAULT_CONFIDENCE), rule, "min_score")
    if not 0.0 <= default <= 1.0:
        raise ValueError(f"{rule}: min_score must be in [0, 1], got {default!r}")
    if override is None:
        return default
    return number_value(override, "confidence threshold override", "the override")


def confidence_mask(scores: Any, threshold: float) -> np.ndarray:
    """Shared step 6 of post.object.decode: return the mask of the scores that stay.

    The comparison is strict: `score > threshold`. A score equal to the threshold goes. The
    comparison is in float64.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder.__init__ (the
    `score_threshold` of the NMS graph, which the host sets to `max(nms.score_threshold,
    confidence threshold)`) at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278. The host compares in
    float32.
    """
    limit = number_value(threshold, "confidence threshold", "threshold")
    return np.asarray(scores, dtype=np.float64) > limit

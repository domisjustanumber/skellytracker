"""Reference implementation of the sidecar section post.det.selection.nms.

Note:

- Section ID: post.det.selection.nms (specs/model-sidecar/post/object/selection-nms.md, heading
  "Behaviour", steps 1 to 7).
- Source commit: OpenMMLab-Exporter 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278 (ADR-H1EF). The host
  code is unchanged at 18320f4e51660fe0cb9c546441eb9be09d53f339. Host functions:
  OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder (the methods decode and map_classes,
  and the reading of the nms object in the constructor) and
  onnx_runtime/decode_nms.py::build_nms_decode_model (the ONNX NonMaxSuppression graph,
  center_point_box 0, opset 13), at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
- Imported section modules: post.det.decode (post_det_decode: shared steps 1, 2, 4, 5 and 6) and
  post.unprojection (post_unprojection: the box_scale conversion of shared step 2 and the
  unprojection of shared step 3). post_unprojection imports pre.resize.letterbox
  (pre_resize_letterbox) and has a fixture of the pre.resize.affine_person_crop Inverse.
- Fixtures: none.
- Vector results: specs/model-sidecar/vectors/post.det.selection.nms.yaml of skellytracker
  8351b7f8c20c8db74eb3e547478970e4dceb0308. All 24 cases pass through run (20 cases with
  boxes_space model_input, 4 cases with boxes_space source). make_vectors.py fill printed no
  problems, and no expect value changed. The check float32-stable passes.
- Parity: unchanged. The yolox-person parity check ran with this module in place of the host code
  (OpenMMLab-Exporter ADR-3NNK (decisions/scripts/yolox_person_reference_swap.py at 53a48480d0b715f9b726963bce002ddb503b050b)). That run used this file before this note line changed (SHA-256 b93949be81e65edac82c9714668c0f24592faac7fe1338fa442a5c6b62db87bf).
- Exclusion check: check_excluded_fields refuses class_logits_output, top_k and max_detections in
  the decode block (V-post.det.selection.nms-1). Its source is the rule text, not the host code.
  The host does not check the exclusion (host code unchanged at
  c2e610e91fee0a961032e12737ff9147697a7e53). The vector file adds 3 data-only validator cases
  (function: none), one for each field. No case runs the check. The 24 numeric cases give the
  same result as with the file before the check (skellytracker
  b065f6e6850686b65bcd08ca944116d739aa62de). The check refuses only an invalid decode block, and
  the yolox-person decode block has none of the three fields, so the parity result above does
  not change.

The functions work on one image. The batch axis B is a loop outside this module.

Differences from the host code (each one gives the same result for a valid sidecar):

- The host filters at max(nms.score_threshold, confidence threshold) before the NMS. This module
  applies the confidence threshold last (step 7), as the section text does.
- The host graph caps each class at post_nms_top_k (max_output_boxes_per_class). This module
  applies post_nms_top_k only to the sorted survivors of the image (step 5).
- The host reads a missing post_nms_top_k, and also the value 0, as "keep all". This module
  refuses a value that is not a positive integer (V-post.det.selection.nms-1).
- The host also reads class scores [B, Q, C]. The spec gives scores [B, Q] only, so this module
  does not read that layout.
- The host does not refuse class_logits_output, top_k or max_detections. It reads
  class_logits_output as the name of its scores output and ignores top_k and max_detections.
  This module refuses each of the three fields (V-post.det.selection.nms-1).

Precision: the section text states the steps in exact math. This module computes in float64.
A float16 or float32 value converts to float64 exactly, so each comparison uses the exact value,
as post_det_decode does. The host runs the NMS in float32 (ONNX Runtime) with float32 thresholds.
The two differ only for a value at a boundary: for example a float32 score equal to
float32(score_threshold) above score_threshold goes in the host and stays in this module. This is
float32 rounding of the threshold (skellytracker ADR-PHJ3). The section text does not give the
float width of a comparison.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

import post_det_decode
import post_unprojection

# The fields of the nms object. A vector case gives them at the top level of params.
NMS_KEYS = ("iou_threshold", "score_threshold", "class_agnostic", "post_nms_top_k")

# The decode fields that a sidecar with selection: nms must not have (V-post.det.selection.nms-1),
# and where the intent of each field belongs.
EXCLUDED_FIELDS = {
    "class_logits_output": "class_logits_output is valid only with selection: top_k.",
    "top_k": (
        "top_k is the pair count of selection: top_k. A candidate limit before the NMS (mmdet nms_pre)"
        " has no field."
    ),
    "max_detections": (
        "max_detections is valid only with selection: none, as the fixed row count of the graph. A cap"
        " after the NMS is nms.post_nms_top_k."
    ),
}


def float_array(values: Any) -> np.ndarray:
    """Return values as a float64 NumPy array (post.det.selection.nms, exact math).

    A float16 or float32 input converts to float64 exactly. Thus each comparison with a threshold
    uses the exact value of the model output. The host keeps float32 (see the module note).

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::convert_boxes (the dtype rule) and
    onnx_runtime/decode_nms.py::NmsDecoder (the float32 feeds of the NMS graph) at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    given = np.asarray(values)
    return given.astype(np.float64)


def nms_settings(nms: Mapping[str, Any]) -> dict[str, Any]:
    """Read and check the nms object (section post.det.selection.nms, V-post.det.selection.nms-1).

    iou_threshold and score_threshold are required. Each one must be a number in [0, 1].
    class_agnostic is a boolean. The default is false. post_nms_top_k is a positive integer, or
    None when the field is absent (keep all survivors).

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder (the constructor reads
    nms) at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278. The host does not check the ranges.
    """
    out: dict[str, Any] = {}
    for key in ("iou_threshold", "score_threshold"):
        value = nms.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
            raise ValueError(f"V-post.det.selection.nms-1: nms.{key} must be a number in [0, 1], got {value!r}")
        out[key] = float(value)
    agnostic = nms.get("class_agnostic", False)
    if not isinstance(agnostic, bool):
        raise ValueError(f"V-post.det.selection.nms-1: nms.class_agnostic must be a boolean, got {agnostic!r}")
    out["class_agnostic"] = agnostic
    top_k = nms.get("post_nms_top_k")
    if top_k is not None and (isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1):
        raise ValueError(f"V-post.det.selection.nms-1: nms.post_nms_top_k must be a positive integer, got {top_k!r}")
    out["post_nms_top_k"] = top_k
    return out


def check_excluded_fields(decode: Mapping[str, Any]) -> None:
    """Refuse a decode field that selection: nms does not allow (V-post.det.selection.nms-1).

    A sidecar with selection: nms must not have class_logits_output, top_k or max_detections. The
    check is for the key: a key with any value fails. The message tells where the intent of the
    field belongs (EXCLUDED_FIELDS).

    Source: the text of V-post.det.selection.nms-1 (section post.det.selection.nms, heading
    "Validation rules"). The host OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder does not
    check this rule at c2e610e91fee0a961032e12737ff9147697a7e53.
    """
    for key, intent in EXCLUDED_FIELDS.items():
        if key in decode:
            raise ValueError(f"V-post.det.selection.nms-1: a sidecar with selection: nms must not have {key}. {intent}")


def box_iou(box: Any, boxes: Any) -> np.ndarray:
    """Return the IoU of one xyxy box with each of the (N, 4) xyxy boxes (step 4).

    The area of a box is (x2 - x1) * (y2 - y1). Nothing is added to a side (no "+1" pixel area).
    The two corners of a box are any diagonal pair, as for the ONNX NonMaxSuppression operator
    with center_point_box 0. Thus the function sorts the two x values and the two y values first.
    When a box has zero area, or the intersection is empty, the IoU is 0.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::build_nms_decode_model at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278 (the ONNX NonMaxSuppression node of ONNX Runtime).
    """
    one = float_array(box).reshape(4)
    many = float_array(boxes).reshape(-1, 4)
    ax1, ax2 = min(one[0], one[2]), max(one[0], one[2])
    ay1, ay2 = min(one[1], one[3]), max(one[1], one[3])
    bx1, bx2 = np.minimum(many[:, 0], many[:, 2]), np.maximum(many[:, 0], many[:, 2])
    by1, by2 = np.minimum(many[:, 1], many[:, 3]), np.maximum(many[:, 1], many[:, 3])
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    inter_w = np.maximum(np.minimum(ax2, bx2) - np.maximum(ax1, bx1), 0.0)
    inter_h = np.maximum(np.minimum(ay2, by2) - np.maximum(ay1, by1), 0.0)
    inter = inter_w * inter_h
    union = area_a + area_b - inter
    valid = (area_a > 0.0) & (area_b > 0.0) & (inter > 0.0) & (union > 0.0)
    return np.where(valid, inter / np.where(union > 0.0, union, 1.0), 0.0)


def hard_nms(boxes: Any, scores: Any, iou_threshold: float) -> np.ndarray:
    """Run greedy hard NMS over one group of candidates and return the positions that stay (step 4).

    The function visits the candidates by descending score. A tie goes to the lower position.
    A candidate stays when its IoU with each box that stays before it is not greater than
    iou_threshold. IoU equal to iou_threshold does not suppress. The result is in visit order.
    The boxes are xyxy in model-input pixels and are not clamped.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::build_nms_decode_model at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278 (the ONNX NonMaxSuppression node of ONNX Runtime,
    one class).
    """
    box = float_array(boxes).reshape(-1, 4)
    score = float_array(scores).reshape(-1)
    order = np.lexsort((np.arange(score.size), -score))
    kept: list[int] = []
    for position in order:
        if not kept or not np.any(box_iou(box[position], box[kept]) > iou_threshold):
            kept.append(int(position))
    return np.asarray(kept, np.int64)


def select_nms(boxes: Any, scores: Any, class_ids: Any, nms: Mapping[str, Any]) -> np.ndarray:
    """Return the input rows that the NMS selection keeps, in output order (steps 1, 4 and 5).

    boxes are (Q, 4) xyxy in model-input pixels (after step 2). scores are (Q,) resolved scores.
    class_ids are (Q,) emitted class ids after shared step 1. The value -1 marks a candidate
    that the class mapping drops. nms is the result of nms_settings.

    1. A candidate stays only when score > score_threshold (strict) and its class id is not -1.
    4. Hard NMS for each class id, or over all candidates when class_agnostic is true.
    5. Sort the survivors by descending score. A tie goes to the lower row. Keep the first
       post_nms_top_k survivors when the field is set.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder.decode (the sort, the tie
    order and post_nms_top_k) and onnx_runtime/decode_nms.py::build_nms_decode_model (the strict
    score filter of NonMaxSuppression) at 5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    box = float_array(boxes).reshape(-1, 4)
    score = float_array(scores).reshape(-1)
    classes = np.asarray(class_ids, np.int64).reshape(-1)
    if not box.shape[0] == score.size == classes.size:
        raise ValueError(f"boxes, scores and class_ids need the same row count: {box.shape[0]}, {score.size}, {classes.size}")
    rows = np.flatnonzero((score > nms["score_threshold"]) & (classes >= 0))
    groups = [rows] if nms["class_agnostic"] else [rows[classes[rows] == c] for c in np.unique(classes[rows])]
    survivors = [group[hard_nms(box[group], score[group], nms["iou_threshold"])] for group in groups]
    found = np.concatenate([np.zeros(0, np.int64), *survivors])
    found = found[np.lexsort((found, -score[found]))]
    if nms["post_nms_top_k"] is not None:
        found = found[: nms["post_nms_top_k"]]
    return found.astype(np.int64)


def decode_image(
    boxes: Any,
    scores: Any,
    class_indexes: Any,
    decode: Mapping[str, Any],
    input_size: Any = None,
    resize: Mapping[str, Any] | None = None,
    source: Mapping[str, Any] | None = None,
    confidence_threshold: float | None = None,
) -> dict[str, Any]:
    """Run the decode of selection: nms for one image (steps 1 to 7 of post.det.selection.nms).

    Args:
        boxes: (Q, 4) boxes of the primary output, in box_format and box_scale.
        scores: (Q,) scores: the score_field column or the scores output.
        class_indexes: (Q,) model class indexes (the class_field column), or None when the
            sidecar has no class source.
        decode: the decode block, with the nms object.
            It must not have class_logits_output, top_k or max_detections (check_excluded_fields).
        input_size: [height, width] of the model input. A box_scale other than pixel needs it.
        resize: the input.resize block. None stops before shared steps 3 to 5: the boxes then
            stay in model-input pixels.
        source: the source image of post.unprojection: src_w and src_h. resize needs it.
        confidence_threshold: a caller value for the final filter (host policy). None uses
            confidence_threshold_default.

    Returns:
        rows (the input rows in output order), scores, class_ids and boxes. The boxes are in
        source-image pixels with resize, else in model-input pixels.

    The order of the steps:

    1. Drop each candidate with score <= nms.score_threshold (select_nms).
    2. Shared step 2: box_format to xyxy (post_det_decode.to_xyxy), then box_scale to
       model-input pixels (post_unprojection.to_model_pixels). No unprojection yet.
    3. Resolve the class indexes. Do shared step 1 (post_det_decode.map_classes, or
       post_det_decode.no_source_class when there is no class source).
    4. and 5. Hard NMS, the sort and post_nms_top_k (select_nms).
    6. Shared steps 3 to 5: the unprojection (post_unprojection.resize_inverse), the clamp
       (post_det_decode.clamp) and the size filter (post_det_decode.size_mask).
    7. Shared step 6: the confidence threshold (post_det_decode.confidence_threshold and
       post_det_decode.confidence_mask).

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder.decode at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    check_excluded_fields(decode)
    nms = nms_settings(decode.get("nms") or {})
    score = float_array(scores).reshape(-1)
    model = post_det_decode.to_xyxy(float_array(boxes).reshape(-1, 4), decode)
    scale = decode.get("box_scale", "pixel")
    if scale != "pixel":
        if input_size is None:
            raise ValueError(f"box_scale {scale!r} needs input_size, the model input size")
        model = np.asarray(
            [
                [*post_unprojection.to_model_pixels(scale, box[:2], input_size),
                 *post_unprojection.to_model_pixels(scale, box[2:], input_size)]
                for box in model.tolist()
            ],
            model.dtype,
        ).reshape(-1, 4)
    if class_indexes is None:
        class_ids = np.full(score.size, post_det_decode.no_source_class(decode), np.int64)
    else:
        class_ids = post_det_decode.map_classes(np.asarray(class_indexes).reshape(-1), decode)
    rows = select_nms(model, score, class_ids, nms)
    out_boxes = model[rows]
    if resize is not None:
        if source is None:
            raise ValueError("resize needs source: src_w and src_h of the source image")
        out_boxes = np.asarray(
            [
                [*post_unprojection.resize_inverse(resize, source, box[:2]),
                 *post_unprojection.resize_inverse(resize, source, box[2:])]
                for box in out_boxes.tolist()
            ],
            np.float64,
        ).reshape(-1, 4)
        out_boxes = post_det_decode.clamp(out_boxes, decode, source["src_w"], source["src_h"])
        keep = post_det_decode.size_mask(out_boxes, decode)
        rows, out_boxes = rows[keep], out_boxes[keep]
    threshold = post_det_decode.confidence_threshold(decode, confidence_threshold)
    keep = post_det_decode.confidence_mask(score[rows], threshold)
    rows, out_boxes = rows[keep], out_boxes[keep]
    return {"rows": rows, "scores": score[rows], "class_ids": class_ids[rows], "boxes": out_boxes}


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Run one vector case of post.det.selection.nms and return its expect mapping.

    params holds the decode fields, with the fields of the nms object at the top level. A case
    with resize also holds input_size and resize. input holds boxes and scores (a boxes primary
    output with no class source), or fields and rows (a detections primary output with
    score_field and an optional class_field). A case with resize also holds src_w and src_h.
    The result has kept_rows, scores, class_ids, boxes_xyxy and boxes_space.

    Source: OpenMMLab-Exporter onnx_runtime/decode_nms.py::NmsDecoder.decode at
    5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278.
    """
    decode = {key: value for key, value in params.items() if key not in NMS_KEYS}
    decode["nms"] = {key: params[key] for key in NMS_KEYS if key in params}
    if "rows" in input:
        fields = list(input["fields"])
        table = np.asarray(input["rows"], np.float64).reshape(-1, len(fields))
        boxes = table[:, 0:4]
        if "score_field" in params:
            scores = table[:, fields.index(params["score_field"])]
        else:
            scores = np.asarray(input["scores"], np.float64)
        class_field = params.get("class_field")
        class_indexes = None if class_field is None else table[:, fields.index(class_field)]
    else:
        boxes, scores, class_indexes = input["boxes"], input["scores"], None
    resize = params.get("resize")
    source = None if resize is None else {"src_w": input["src_w"], "src_h": input["src_h"]}
    found = decode_image(boxes, scores, class_indexes, decode, params.get("input_size"), resize, source)
    return {
        "kept_rows": [int(row) for row in found["rows"]],
        "scores": [float(value) for value in found["scores"]],
        "class_ids": [int(value) for value in found["class_ids"]],
        "boxes_xyxy": [[float(value) for value in box] for box in found["boxes"]],
        "boxes_space": "model_input" if resize is None else "source",
    }

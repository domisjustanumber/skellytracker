---
id: post.det.selection.nms
title: "Selection: NMS"
kind: postprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors:
  - decode.selection=nms
implemented_by:
  validate: missing
  decode: skellytracker/core/detectors/processing/object_detection_decode.py::decode_prenms  # partial: the box area adds 1 to each side; ties are not ordered by row index; one class only; no nms block, post_nms_top_k or clamp; the caller gives the thresholds
external_impl: []
tests:
  - skellytracker/tests/test_object_detection_decode.py
  - skellytracker/tests/test_yolox_detector.py
vectors: vectors/post.det.selection.nms.yaml
status: {spec: stable, validate: missing, decode: partial}
---

# Selection: NMS

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `nms` | object | conditional | Required for `selection: nms`. Invalid in all other cases. See below. |

**`nms` object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `iou_threshold` | float | yes | The host suppresses a candidate when its IoU with a higher-scoring kept box is greater than this value. |
| `score_threshold` | float | yes | A candidate filter that the host applies before NMS. It is strict: `score > score_threshold`. It is independent of `confidence_threshold_default`. |
| `class_agnostic` | bool | no | The default is `false` (per-class NMS). If there is no class source, every candidate has one class. In this case, both settings are equivalent. |
| `post_nms_top_k` | int | no | Keep at most this number of survivors for each image, highest score first. To keep all survivors, omit this field. |

`nms` is a field of [`decode`](detection-decode.md#decode-detection). That section defines the other `decode` fields. [Detection output semantics](detection-outputs.md#detection-output-semantics) defines `B`, `Q` and `C`.

## Behaviour

Score comparisons and tie-breaking: [Selection behaviour](detection-decode.md#selection-behaviour).

**`selection: nms`** — the primary output rows are pre-NMS candidates (for example RTMDet).

1. Resolve the scores. Drop each candidate with `score <= nms.score_threshold`.
2. Convert the boxes from `box_format` to `xyxy`. Apply `box_scale` to get model-input pixels. Do not unproject the boxes yet.
3. Resolve the class indices from `class_field` and map them. If there is no class source, assign `person_class_id`. Apply `is_person_only`.
4. Run hard NMS at `nms.iou_threshold` in model-input coordinates. Run it for each class, unless `class_agnostic: true`.
5. Sort the survivors by score in descending order. Keep the first `nms.post_nms_top_k` survivors if that field is set.
6. Unproject the boxes. Clamp them.
7. Apply `confidence_threshold_default`.

These decode steps correspond one-to-one to the standard ONNX `NonMaxSuppression` operator. The operator takes scores as `[B, C, Q]`. It suppresses boxes for each class when IoU is greater than `iou_threshold`. It drops candidates at or below `score_threshold`. Its box-area convention does not add `1` to pixel widths or heights.

Pose rows of a model with both roles: [Bottom-up decode](pose-bottom-up.md#bottom-up-decode).

## Validation rules

### Detection (`object_detector`)

- [ ] `V-post.det.selection.nms-1` A sidecar with `selection: nms` must have `nms` with `iou_threshold` and `score_threshold`. Each of these fields must be a float in `[0, 1]`. The sidecar must not have `class_logits_output`, `top_k` or `max_detections`. If `nms.class_agnostic` is present, it must be a boolean. If `nms.post_nms_top_k` is present, it must be a positive integer.

See also [Detection decode](detection-decode.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `decode.nms` absent with host NMS | Existing host NMS behaviour (implementation-defined). | Invalid; `nms` required for `selection: nms`. |

`decode.max_detections` before `vNEXT`: [Selection: none](selection-none.md#legacy-behaviour).

## Implementer guidance

## Authoring guidance

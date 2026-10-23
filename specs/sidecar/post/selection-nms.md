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
| `nms` | object | conditional | Required for `selection: nms`; invalid otherwise. See below. |

**`nms` object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `iou_threshold` | float | yes | A candidate is suppressed when its IoU with a higher-scoring kept box exceeds this value. |
| `score_threshold` | float | yes | Candidate filter applied before NMS (strict `score > score_threshold`). Independent of `confidence_threshold_default`. |
| `class_agnostic` | bool | no | Default `false` (per-class NMS). With no class source every candidate has one class, so both settings are equivalent. |
| `post_nms_top_k` | int | no | Keep at most this many survivors per image, highest score first. Omit to keep all survivors. |

`nms` is a field of [`decode`](detection-decode.md#decode-detection). The other `decode` fields are defined there. `B`, `Q` and `C` are defined in [Detection output semantics](detection-outputs.md#detection-output-semantics).

## Behaviour

Score comparisons and tie-breaking: [Selection behaviour](detection-decode.md#selection-behaviour).

**`selection: nms`** — the primary output rows are pre-NMS candidates (e.g. RTMDet).

1. Resolve scores; drop candidates with `score <= nms.score_threshold`.
2. Convert `box_format` to `xyxy` and apply `box_scale` (model-input pixels). Do not unproject yet.
3. Resolve and map class indices from `class_field`; with no class source assign `person_class_id`; apply `is_person_only`.
4. Run hard NMS at `nms.iou_threshold` — per class unless `class_agnostic: true` — in model-input coordinates.
5. Sort survivors by descending score; keep the first `nms.post_nms_top_k` when set.
6. Unproject and clamp.
7. Apply `confidence_threshold_default`.

These decode steps map one-to-one onto the standard ONNX `NonMaxSuppression` operator. The operator takes scores as `[B, C, Q]`, suppresses boxes per class when IoU is greater than `iou_threshold`, and drops candidates at or below `score_threshold`. Its box-area convention does not add `1` to pixel widths or heights.

Pose rows of a model with both roles: [Bottom-up decode](pose-bottom-up.md#bottom-up-decode).

## Validation rules

### Detection (`object_detector`)

- [ ] `V-post.det.selection.nms-1` `selection: nms` requires `nms` with `iou_threshold` and `score_threshold` (floats in `[0, 1]`), forbids `class_logits_output`, `top_k`, and `max_detections`; `nms.class_agnostic` (when present) is a boolean; `nms.post_nms_top_k` (when present) is a positive integer.

See also [Detection decode](detection-decode.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `decode.nms` absent with host NMS | Existing host NMS behaviour (implementation-defined). | Invalid; `nms` required for `selection: nms`. |

`decode.max_detections` before `vNEXT`: [Selection: none](selection-none.md#legacy-behaviour).

## Implementer guidance

## Authoring guidance

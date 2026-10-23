---
id: post.det.selection.none
title: "Selection: none"
kind: postprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors:
  - decode.selection=none
implemented_by:
  validate: skellytracker/core/sidecar/model.py::DetectionDecodeSpec._check_ranges  # partial: it checks only max_detections > 0; no rule for forbidden fields or the row count
  decode: skellytracker/core/detectors/processing/object_detection_decode.py::decode_nms_baked_in  # partial: the score is column 4; no class mapping, is_person_only or clamp; the caller gives the threshold
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/test_object_detection_decode.py
  - skellytracker/tests/test_yolox_detector.py
vectors: vectors/post.det.selection.none.yaml
status: {spec: stable, validate: partial, decode: partial}
---

# Selection: none

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `max_detections` | int | no | The fixed number of final rows that the graph emits (for example `300` for YOLO26). This field is valid only with `selection: none`. It is never a host-side cap. It has no default. |

`max_detections` is a field of [`decode`](detection-decode.md#decode-detection). That section defines the other `decode` fields.

## Behaviour

Score comparisons and tie-breaking: [Selection behaviour](detection-decode.md#selection-behaviour).

**`selection: none`** — the primary output rows are already final detections (for example the NMS-free head of YOLO26).

1. Resolve the score of each row (`score_field` or `scores_output`). Resolve the class index of each row (`class_field`). If this field is absent, there is no class source.
2. Map each class index with `class_id_map` or `class_id_base`. Drop each row that maps to `-1`. Apply `is_person_only`.
3. Convert the boxes from `box_format` to `xyxy`. Apply `box_scale`. Unproject the boxes. When `clamp_boxes` is true, clamp the boxes.
4. Apply `confidence_threshold_default`. Do not run NMS. The host does not pad or truncate the rows to reach `max_detections`.

Pose rows of a model with both roles: [Bottom-up decode](pose-bottom-up.md#bottom-up-decode).

## Validation rules

### Detection (`object_detector`)

- [ ] `V-post.det.selection.none-1` A sidecar with `selection: none` must not have `top_k`, `nms` or `class_logits_output`. If `max_detections` is present, it must be a positive integer. When the row dimension of the primary output is concrete, this value must equal that dimension.

See also [Detection decode](detection-decode.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `decode.max_detections` absent | Default `300`. | No default; valid only with `selection: none`. |

See also [Detection decode](detection-decode.md#legacy-behaviour) and [Bottom-up pose](pose-bottom-up.md#legacy-behaviour).

## Implementer guidance

## Authoring guidance

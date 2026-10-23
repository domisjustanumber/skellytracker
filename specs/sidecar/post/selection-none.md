---
id: post.det.selection.none
title: "Selection: none"
kind: postprocessor
---

# Selection: none

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `max_detections` | int | no | Only with `selection: none`: the fixed number of final rows the graph emits (e.g. `300` for YOLO26). Never a host-side cap. No default. |

`max_detections` is a field of [`decode`](detection-decode.md#decode-detection). The other `decode` fields are defined there.

## Behaviour

Score comparisons and tie-breaking: [Selection behaviour](detection-decode.md#selection-behaviour).

**`selection: none`** — the primary output rows are already final detections (e.g. YOLO26's NMS-free head).

1. Resolve each row's score (`score_field` or `scores_output`) and class index (`class_field`; absent → no class source).
2. Map class indices via `class_id_map` (drop `-1`) or `class_id_base`; apply `is_person_only`.
3. Convert `box_format` to `xyxy`, apply `box_scale`, unproject, and clamp when `clamp_boxes`.
4. Apply `confidence_threshold_default`. Do not run NMS; the host does not pad or truncate to `max_detections`.

Pose rows of a model with both roles: [Bottom-up decode](pose-bottom-up.md#bottom-up-decode).

## Validation rules

### Detection (`object_detector`)

- [ ] `V-post.det.selection.none-1` `selection: none` forbids `top_k`, `nms`, and `class_logits_output`. `max_detections` (when present) is a positive integer and equals the primary output's row dimension when that is concrete.

See also [Detection decode](detection-decode.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `decode.max_detections` absent | Default `300`. | No default; valid only with `selection: none`. |

See also [Detection decode](detection-decode.md#legacy-behaviour) and [Bottom-up pose](pose-bottom-up.md#legacy-behaviour).

## Implementer guidance

## Authoring guidance

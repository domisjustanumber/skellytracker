---
id: post.det.selection.top_k
title: "Selection: top-k"
kind: postprocessor
---

# Selection: top-k

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `class_logits_output` | string | conditional | Name of the `class_logits` output. Required for `selection: top_k`; invalid otherwise. |
| `score_activation` | enum | no | `none` (default) or `sigmoid`. Applied to `class_logits` before selection. |
| `top_k` | int | conditional | Required for `selection: top_k`: number of (row, class) pairs to select. |

These are fields of [`decode`](detection-decode.md#decode-detection). The other `decode` fields are defined there. `B`, `Q` and `C` are defined in [Detection output semantics](detection-outputs.md#detection-output-semantics).

## Behaviour

Score comparisons and tie-breaking: [Selection behaviour](detection-decode.md#selection-behaviour).

**`selection: top_k`** — per-row class logits with a global (row, class) top-k (e.g. RF-DETR).

1. `p = score_activation(class_logits)`; move `class_axis` last, so `p` is `[Q, C]`.
2. Flatten row-major: `flat = row * C + class`.
3. Stable sort descending by score; take the first `min(top_k, Q * C)` entries.
4. `row = flat // C`, `class = flat % C`; gather `boxes[row]`; score is `p[row, class]`.
5. Map `class` via `class_id_map` (drop `-1`, so the final count may be below `top_k`) or `class_id_base`; apply `is_person_only`.
6. Convert boxes, apply `box_scale`, unproject, clamp.
7. Apply `confidence_threshold_default`. Do not run NMS. Several selected pairs may share one row (one box, several classes); this is allowed.

## Validation rules

### Detection (`object_detector`)

- [ ] `V-post.det.selection.top_k-1` `selection: top_k` requires a `boxes` primary output, `class_logits_output`, and a positive integer `top_k`, and forbids `nms`, `max_detections`, `scores_output`, and `score_field`.

See also [Detection decode](detection-decode.md#validation-rules).

## Legacy behaviour

See [Detection decode](detection-decode.md#legacy-behaviour) and [Schema versioning](../format/versioning.md#legacy-behaviour).

## Implementer guidance

## Authoring guidance

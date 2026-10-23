---
id: post.det.selection.top_k
title: "Selection: top-k"
kind: postprocessor
since: vNEXT
changed_in: []
selectors:
  - decode.selection=top_k
implemented_by:
  validate: missing
  decode: missing
external_impl: []
tests: []
vectors: vectors/post.det.selection.top_k.yaml
status: {spec: stable, validate: missing, decode: missing}
---

# Selection: top-k

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `class_logits_output` | string | conditional | The name of the `class_logits` output. Required for `selection: top_k`. Invalid in all other cases. |
| `score_activation` | enum | no | The value is `none` (default) or `sigmoid`. The host applies it to `class_logits` before selection. |
| `top_k` | int | conditional | The number of (row, class) pairs to select. Required for `selection: top_k`. |

These are fields of [`decode`](detection-decode.md#decode-detection). That section defines the other `decode` fields. [Detection output semantics](detection-outputs.md#detection-output-semantics) defines `B`, `Q` and `C`.

## Behaviour

Score comparisons and tie-breaking: [Selection behaviour](detection-decode.md#selection-behaviour).

**`selection: top_k`** — the model gives class logits for each row. The host takes a global top-k of the (row, class) pairs (for example RF-DETR).

1. Compute `p = score_activation(class_logits)`. Move `class_axis` to the last position. Then `p` is `[Q, C]`.
2. Flatten in row-major order with `flat = row * C + class`.
3. Sort the entries by score in descending order with a stable sort. Take the first `min(top_k, Q * C)` entries.
4. Compute `row = flat // C` and `class = flat % C`. Gather `boxes[row]`. The score is `p[row, class]`.
5. Map `class` with `class_id_map` or `class_id_base`. Drop each pair that maps to `-1`. The final count can then be below `top_k`. Apply `is_person_only`.
6. Convert the boxes. Apply `box_scale`. Unproject the boxes. Clamp the boxes.
7. Apply `confidence_threshold_default`. Do not run NMS. Several selected pairs can share one row (one box, several classes). The spec allows this.

## Validation rules

### Detection (`object_detector`)

- [ ] `V-post.det.selection.top_k-1` A sidecar with `selection: top_k` must have a `boxes` primary output, `class_logits_output` and a positive integer `top_k`. It must not have `nms`, `max_detections`, `scores_output` or `score_field`.

See also [Detection decode](detection-decode.md#validation-rules).

## Legacy behaviour

See [Detection decode](detection-decode.md#legacy-behaviour) and [Schema versioning](../format/versioning.md#legacy-behaviour).

## Implementer guidance

## Authoring guidance

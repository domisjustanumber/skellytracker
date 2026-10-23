---
id: post.det.outputs
title: Detection outputs
kind: postprocessor
---

# Detection outputs

## Fields

### Detection output semantics

An `object_detector` sidecar declares exactly **one primary detection output** — either one `detections` or one `boxes` tensor — plus optional companion tensors:

| Semantic | Shape | Dtype | Meaning |
|----------|-------|-------|---------|
| `detections` | `[B, Q, F]` | float | Packed rows. `fields` names each of the `F` columns (e.g. `x1, y1, x2, y2, score, class_id`); may also carry [`packed_keypoints`](pose-bottom-up.md#packed_keypoints-bottom-up-packed-rows). Primary. |
| `boxes` | `[B, Q, 4]` | float | Box coordinates only. Scores come from a `scores` or `class_logits` companion. Primary. |
| `scores` | `[B, Q]` | float | Per-row confidence, row-aligned with the primary output. |
| `class_logits` | `[B, Q, C]` | float | Per-row, per-class logits or scores; class axis last unless `class_axis` says otherwise. |

`B` is the batch, `Q` the candidate/row count, `C` the model's class-slot count. Rules:

- At most one each of `scores` and `class_logits`.
- `scores` shape equals the primary output shape without its final dimension.
- `class_logits` requires a `boxes` primary output and `decode.selection: top_k`; its non-class axes equal the `boxes` outer axes `[B, Q]`. `C` must be concrete.

### `outputs` (detection)

The fields common to every output are in [Outputs](../common/outputs.md#fields).

Additional fields on detection output tensors:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fields` | array | conditional | Ordered field names per detection row (e.g. `[x1, y1, x2, y2, score, class_id]`). Required for `semantic: detections`, forbidden for the other detection semantics. Its length equals the last tensor dimension, unless `packed_keypoints` is present, in which case it equals `packed_keypoints.offset`. |
| `class_axis` | int | no | `class_logits` only: axis holding the class dimension; default `-1`. Negative values follow Python/ONNX indexing; it must not be the batch axis. |
| `packed_keypoints` | object | no | `detections` only, pose-capable one-stage models: see [`packed_keypoints`](pose-bottom-up.md#packed_keypoints-bottom-up-packed-rows). |

## Validation rules

### Detection (`object_detector`)

- [ ] `V-post.det.outputs-1` The sidecar declares `decode` and exactly one primary detection output (`detections` or `boxes`); at most one each of `scores` and `class_logits`.
- [ ] `V-post.det.outputs-2` A `detections` output declares `fields`; `len(fields) == shape[-1]` when `shape[-1]` is concrete and `packed_keypoints` is absent, and `len(fields) == packed_keypoints.offset` otherwise. `fields` is absent on every other semantic.
- [ ] `V-post.det.outputs-3` A `boxes` output's last dimension is `4`. `scores` shape equals the primary shape without its last dimension. `class_logits` non-class axes equal the `boxes` outer axes, `class_axis` (when present) is a valid non-batch axis, and the class dimension is concrete.
- [ ] `V-post.det.outputs-4` `scores`, `class_logits`, `boxes`, and `detections` dtypes are float types.

See also [Outputs](../common/outputs.md#validation-rules), [Detection decode](detection-decode.md#validation-rules) and [Bottom-up pose](pose-bottom-up.md#validation-rules).

## Legacy behaviour

Availability before `vNEXT`: [Schema versioning](../format/versioning.md#legacy-behaviour).

## Implementer guidance

## Authoring guidance

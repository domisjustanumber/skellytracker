---
id: post.det.outputs
title: Detection outputs
kind: postprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors:
  - outputs[].semantic=detections
  - outputs[].semantic=boxes
  - outputs[].semantic=scores
  - outputs[].semantic=class_logits
implemented_by:
  validate: skellytracker/core/sidecar/model.py::SidecarModel._check_outputs_semantics  # partial: no boxes, scores, class_logits, class_axis or packed_keypoints; no float dtype check; the fields length is not compared with the shape
  decode: skellytracker/core/detectors/object_detectors/yolox/yolox_decode.py::yolox_detection_decode  # partial: it reads the outputs by position and last dimension, not by semantic or fields
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/test_yolox_detector.py
vectors: null
status: {spec: stable, validate: partial, decode: partial}
---

# Detection outputs

## Fields

### Detection output semantics

An `object_detector` sidecar must declare exactly **one primary detection output**: either one `detections` tensor or one `boxes` tensor. It can also declare companion tensors:

| Semantic | Shape | Dtype | Meaning |
|----------|-------|-------|---------|
| `detections` | `[B, Q, F]` | float | Packed rows. `fields` lists the name of each of the `F` columns (for example `x1, y1, x2, y2, score, class_id`). The output can also carry [`packed_keypoints`](pose-bottom-up.md#packed_keypoints-bottom-up-packed-rows). Primary. |
| `boxes` | `[B, Q, 4]` | float | Box coordinates only. The scores come from a `scores` companion or a `class_logits` companion. Primary. |
| `scores` | `[B, Q]` | float | The confidence of each row. The rows align with the rows of the primary output. |
| `class_logits` | `[B, Q, C]` | float | Logits or scores for each row and each class. The class axis is last, unless `class_axis` sets a different axis. |

`B` is the batch. `Q` is the number of candidates (rows). `C` is the number of class slots of the model. Rules:

- A sidecar must have at most one `scores` output and at most one `class_logits` output.
- The shape of `scores` must equal the shape of the primary output without its final dimension.
- Use `class_logits` only with a `boxes` primary output and `decode.selection: top_k`. Its non-class axes must equal the outer axes `[B, Q]` of `boxes`. `C` must be concrete.

### `outputs` (detection)

The fields common to every output are in [Outputs](../common/outputs.md#fields).

Additional fields on detection output tensors:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fields` | array | conditional | The ordered field names for each detection row (for example `[x1, y1, x2, y2, score, class_id]`). Required for `semantic: detections`. Must not be present for the other detection semantics. If `packed_keypoints` is present, its length must equal `packed_keypoints.offset`. Otherwise, its length must equal the last tensor dimension. |
| `class_axis` | int | no | For `class_logits` only: the axis that holds the class dimension. The default is `-1`. A negative value follows Python/ONNX indexing. It must not be the batch axis. |
| `packed_keypoints` | object | no | For a `detections` output only, in one-stage models that can estimate pose. See [`packed_keypoints`](pose-bottom-up.md#packed_keypoints-bottom-up-packed-rows). |

## Validation rules

### Detection (`object_detector`)

- [ ] `V-post.det.outputs-1` The sidecar must declare `decode` and exactly one primary detection output (`detections` or `boxes`). It must declare at most one `scores` output and at most one `class_logits` output.
- [ ] `V-post.det.outputs-2` A `detections` output must declare `fields`. When `shape[-1]` is concrete and `packed_keypoints` is absent, `len(fields) == shape[-1]` must be true. In all other cases, `len(fields) == packed_keypoints.offset` must be true. `fields` must be absent on every other semantic.
- [ ] `V-post.det.outputs-3` The last dimension of a `boxes` output must be `4`. The shape of `scores` must equal the primary shape without its last dimension. The non-class axes of `class_logits` must equal the outer axes of `boxes`. If `class_axis` is present, it must be a valid non-batch axis. The class dimension must be concrete.
- [ ] `V-post.det.outputs-4` The dtypes of `scores`, `class_logits`, `boxes` and `detections` must be float types.

See also [Outputs](../common/outputs.md#validation-rules), [Detection decode](detection-decode.md#validation-rules) and [Bottom-up pose](pose-bottom-up.md#validation-rules).

## Legacy behaviour

Availability before `vNEXT`: [Schema versioning](../format/versioning.md#legacy-behaviour).

## Implementer guidance

## Authoring guidance

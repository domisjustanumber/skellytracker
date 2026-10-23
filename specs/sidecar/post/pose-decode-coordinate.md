---
id: post.pose.decode.coordinate
title: Coordinate decode
kind: postprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors:
  - pose.decode.method=coordinate
  - outputs[].semantic=keypoints
implemented_by:
  validate: skellytracker/core/sidecar/model.py::PoseDecodeSpec._check_decode
  decode: missing
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
vectors: null
status: {spec: stable, validate: implemented, decode: missing}
---

# Coordinate decode

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pose.decode.coordinate_scale` | enum | no | For `coordinate` only. The value is the scale of the decoded coordinates: `pixel` (raw pixels in the input image; default), `normalized_01` ([0, 1] fraction of the input) or `normalized_11` ([-1, 1] centered on the input). |

`pose.decode.coordinate_scale` is a field of [`pose.decode`](pose-schema.md#posedecode). That section defines the other `pose.decode` fields.

## Behaviour

- `coordinate` — the coordinates are already decoded (no argmax). They are in the scale of the model input image, as `coordinate_scale` sets. The host unprojects them to the source image. There are three forms:
  - single-person — one output with `semantic: keypoints`. The shape is `(N, K, 2)` (`x, y`), or `(N, K, 3)` (`x, y, z`) when `is_3d: true`. `z` is root-relative depth (in `depth_unit`).
  - bottom-up, separate tensors — a primary detection output plus a `poses` output.
  - bottom-up, packed — a `detections` output that carries `packed_keypoints`.

[Shape key](pose-schema.md#shape-key)

## Validation rules

### Pose (`pose_estimator`)

- [ ] `V-post.pose.decode.coordinate-1` `pose.decode.coordinate_scale` must not be present unless `pose.decode.method: coordinate`. If it is present, it must be `pixel`, `normalized_01` or `normalized_11`.

See also [Pose schema](pose-schema.md#validation-rules) and [Bottom-up pose](pose-bottom-up.md#validation-rules).

## Implementer guidance

## Authoring guidance

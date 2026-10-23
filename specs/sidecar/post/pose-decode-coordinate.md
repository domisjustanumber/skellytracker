---
id: post.pose.decode.coordinate
title: Coordinate decode
kind: postprocessor
---

# Coordinate decode

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pose.decode.coordinate_scale` | enum | no | `coordinate` only: scale of the decoded coordinates — `pixel` (raw pixels in the input image; default), `normalized_01` ([0, 1] fraction of the input), or `normalized_11` ([-1, 1] centered on the input). |

`pose.decode.coordinate_scale` is a field of [`pose.decode`](pose-schema.md#posedecode). The other `pose.decode` fields are defined there.

## Behaviour

- `coordinate` — coordinates are already decoded (no argmax) and live in the scale of the model's input image, per `coordinate_scale`; the host unprojects them to the source image. Three forms:
  - single-person — one output with `semantic: keypoints`, shape `(N, K, 2)` (`x, y`) or `(N, K, 3)` (`x, y, z`) when `is_3d: true`; `z` is root-relative depth (in `depth_unit`).
  - bottom-up, separate tensors — a primary detection output plus a `poses` output.
  - bottom-up, packed — a `detections` output carrying `packed_keypoints`.

[Shape key](pose-schema.md#shape-key)

## Validation rules

### Pose (`pose_estimator`)

- [ ] `V-post.pose.decode.coordinate-1` `pose.decode.coordinate_scale` is present only when `pose.decode.method: coordinate`, and (when present) is `pixel`, `normalized_01`, or `normalized_11`.

See also [Pose schema](pose-schema.md#validation-rules) and [Bottom-up pose](pose-bottom-up.md#validation-rules).

## Implementer guidance

## Authoring guidance

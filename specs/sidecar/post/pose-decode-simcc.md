---
id: post.pose.decode.simcc
title: SimCC decode
kind: postprocessor
---

# SimCC decode

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pose.decode.depth_range` | array[2] | required when `is_3d: true` and `method: simcc` | `[min, max]` root-relative depth (in `depth_unit`) that `Z_bins` span; the decoded bin position maps linearly to depth. |

`pose.decode.depth_range` is a field of [`pose.decode`](pose-schema.md#posedecode). The other `pose.decode` fields are defined there.

## Behaviour

- `simcc` — one `simcc_x` `(N, K, X_bins)` and one `simcc_y` `(N, K, Y_bins)` output (plus `simcc_z` `(N, K, Z_bins)` when `is_3d: true`). The bin counts are read from the output tensors; the bin→pixel scale is `input_width / X_bins` and `input_height / Y_bins` (see Shape key). Each keypoint's location is the argmax bin and its score is the max value. Decoded keypoints are in cropped image space; the host unprojects them to the source image. The `z` axis maps `Z_bins` linearly onto `depth_range` (in `depth_unit`) when `is_3d: true`.

[Shape key](pose-schema.md#shape-key)

## Validation rules

### Pose (`pose_estimator`)

- [ ] `V-post.pose.decode.simcc-1` When `pose.decode.is_3d: true` and `pose.decode.method: simcc`, `pose.decode.depth_range` is present and is a length-2 array `[min, max]` in `depth_unit`.

See also [Pose schema](pose-schema.md#validation-rules).

## Implementer guidance

## Authoring guidance

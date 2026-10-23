---
id: post.pose.decode.heatmap
title: Heatmap decode
kind: postprocessor
---

# Heatmap decode

## Behaviour

- `heatmap` — one output with `semantic: heatmap`, shape `(N, K, H, W)` (2D only); per-keypoint peaks are decoded to locations in cropped image space, then unprojected to the source image.

[Shape key](pose-schema.md#shape-key)

## Validation rules

### Pose (`pose_estimator`)

- [ ] `V-post.pose.decode.heatmap-1` `pose.decode.method: heatmap` with `pose.decode.is_3d: true` is invalid (3D heatmap is not supported).

See also [Pose schema](pose-schema.md#validation-rules).

## Implementer guidance

## Authoring guidance

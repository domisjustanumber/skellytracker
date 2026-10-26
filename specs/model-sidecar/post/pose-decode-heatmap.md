---
id: post.pose.decode.heatmap
title: Heatmap decode
kind: postprocessor
since: v2024.09.1019
changed_in: []
selectors:
  - pose.decode.method=heatmap
  - outputs[].semantic=heatmap
implemented_by:
  validate: skellytracker/core/sidecar/model.py::PoseDecodeSpec._check_decode
  decode: missing
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
vectors: null
status: {spec: stable, validate: implemented, decode: missing}
---

# Heatmap decode

## Behaviour

- `heatmap` — one output with `semantic: heatmap` and shape `(N, K, H, W)`. This method supports only 2D heatmaps. The host decodes the peak of each keypoint to a location in cropped image space. Then the host unprojects the location to the source image.

[Shape key](pose-schema.md#shape-key)

## Validation rules

### Pose (`pose_estimator`)

- [ ] `V-post.pose.decode.heatmap-1` A sidecar with `pose.decode.method: heatmap` and `pose.decode.is_3d: true` is invalid. A 3D heatmap is not supported.

See also [Pose schema](pose-schema.md#validation-rules).

## Implementer guidance

No exporter evidence yet.

## Authoring guidance

No exporter evidence yet.

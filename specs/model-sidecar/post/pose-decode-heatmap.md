---
id: post.pose.decode.heatmap
title: Heatmap decode
kind: postprocessor
selectors:
  - pose.decode.method=heatmap
  - outputs[].semantic=heatmap
implemented_by:
  validate: missing  # PoseDecodeSpec._check_decode (skellytracker/core/sidecar/model.py) keys on the removed key pose.decode.is_3d, and PoseSpec forbids pose.geometry (decisions/entries/90CE-minimal-sidecar-contract.md).
  decode: missing
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
vectors: null
status: {spec: stable, validate: missing, decode: missing}
---

# Heatmap decode

## Behaviour

- `heatmap` — one output with `semantic: heatmap` and shape `(N, K, H, W)`. This method supports only `pose.geometry: 2d`. The host decodes the peak of each keypoint to a location in cropped image space. Then the host unprojects the location to the source image.

[Shape key](pose-schema.md#shape-key)

## Validation rules

### Pose (`pose_estimator`)

- [ ] `V-post.pose.decode.heatmap-1` A sidecar with `pose.decode.method: heatmap` and `pose.geometry: 3d` is invalid. The heatmap decode is `2d` only ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

See also [Pose schema](pose-schema.md#validation-rules).

## Implementer guidance

No exporter evidence yet.

## Authoring guidance

No exporter evidence yet.

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

- The RTMO `coordinate_scale: pixel` is not verified. The probe of OpenMMLab-Exporter only checks that the sidecar says `pixel`. The kept keypoints fall inside their own box. That does not show whether the coordinates are in the 640 x 640 model-input space or in source pixels. (OpenMMLab-Exporter `notes/decisions/scripts/rtmo_sidecar_probe.py:136` and `notes/decisions/0020-rtmo-sidecar-contract.md:65-67`, 38ed76f)
- Include z in a 3D parity check. The historical landmark parity of Qualcomm-Exporter on seeded noise (max abs error): face (468 x 3, input 192) 4.58e-05 in fp32 and 0.0434 in fp16. Hand (21 x 3, input 256): 7.63e-05 in fp32 (x, y: 6.10e-05) and 6.87e-05 in fp16 (x, y: 3.81e-05). Its pass test covers x and y only (`difference[..., :2]`) with a limit of 1.0 px. z is not in the test. (Qualcomm-Exporter `exports/detectors/keypoint_detectors/mediapipe/face/mediapipe-face-default_b1_fp32.report.json`, `..._fp16.report.json` and the same files under `.../hand/`, field `artifact.parity`, untracked, HEAD 4ca4586; `qai_export.py:122-163`, 8d8e05a)

## Authoring guidance

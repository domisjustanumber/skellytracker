---
id: post.keypoint.decode.coordinate
title: Coordinate decode
kind: postprocessor
selectors:
  - keypoint.decode.method=coordinate
  - outputs[].semantic=keypoint_coordinates
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
| `keypoint.decode.coordinate_space` | enum | no | For `coordinate` only. It must not be present when an output has [`packed_keypoints`](bottom-up.md#packed_keypoints-bottom-up-packed-rows): the packed keypoints use `object.decode.box_space` ([ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md)). The value is the space of the decoded coordinates: `pixel` (raw pixels in the input image; default), `normalized_01` ([0, 1] fraction of the input) or `normalized_11` ([-1, 1] centered on the input). |

`keypoint.decode.coordinate_space` is a field of [`keypoint.decode`](schema.md#keypointdecode). That section defines the other `keypoint.decode` fields.

## Behaviour

- `coordinate` — the coordinates are already decoded (no argmax). They are in the space of the model input image, as `coordinate_space` sets, or as `object.decode.box_space` sets for packed keypoints. The host unprojects them to the source image. There are three forms:
  - single-person — one output with `semantic: keypoint_coordinates`. The shape is `(B, P, 2)` (`x, y`), or `(B, P, 3)` (`x, y, z`) when `keypoint.geometry: 3d` ([ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md)). `z` is root-relative depth (in `depth_unit`).
  - bottom-up, separate tensors — a primary detection output plus an `instance_keypoints` output.
  - bottom-up, packed — a `packed_detections` output that carries `packed_keypoints`.
- Score range ([Decoded keypoints](schema.md#decoded-keypoints)). A packed keypoint `score` is in `[0, 1]`, because the model activates it ([`packed_keypoints`](bottom-up.md#packed_keypoints-bottom-up-packed-rows)). The `score` value of an `instance_keypoints` tensor is in `[0, 1]` ([Bottom-up keypoints](bottom-up.md#fields)). A `keypoint_coordinates` output has no score: each keypoint with finite coordinates has the score `1.0`.

[Shape key](schema.md#shape-key)

## Validation rules

### Keypoint (`keypoint_detector`)

- [ ] `V-post.keypoint.decode.coordinate-1` `keypoint.decode.coordinate_space` must not be present unless `keypoint.decode.method: coordinate`. If it is present, it must be `pixel`, `normalized_01` or `normalized_11`.

See also [Keypoint schema](schema.md#validation-rules) and [Bottom-up keypoints](bottom-up.md#validation-rules).

## Implementer guidance

- The RTMO `coordinate_space: pixel` is not verified. The probe of OpenMMLab-Exporter only checks that the sidecar says `pixel`. The kept keypoints fall inside their own box. That does not show whether the coordinates are in the 640 x 640 model-input space or in source pixels. (OpenMMLab-Exporter [`notes/decisions/scripts/rtmo_sidecar_probe.py:136`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/scripts/rtmo_sidecar_probe.py#L136) and [`notes/decisions/0020-rtmo-sidecar-contract.md:65-67`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0020-rtmo-sidecar-contract.md#L65-L67))
- Include z in a 3D parity check. The historical landmark parity of Qualcomm-Exporter on seeded noise (max abs error): face (468 x 3, input 192) 4.58e-05 in fp32 and 0.0434 in fp16. Hand (21 x 3, input 256): 7.63e-05 in fp32 (x, y: 6.10e-05) and 6.87e-05 in fp16 (x, y: 3.81e-05). Its pass test covers x and y only (`difference[..., :2]`) with a limit of 1.0 px. z is not in the test. (Qualcomm-Exporter `exports/detectors/keypoint_detectors/mediapipe/face/mediapipe-face-default_b1_fp32.report.json`, `..._fp16.report.json` and the same files under `.../hand/`, field `artifact.parity`, untracked, HEAD 4ca45868431b67350c3c7ed900d5b3ff9f409905; [`qai_export.py:122-163`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/8d8e05a1c210dda5c2a1c4110bd7e4db860844fd/qai_export.py#L122-L163))

## Authoring guidance

- YOLO26-pose: `keypoint.decode` is `{method: coordinate}`. `coordinate_space` is not present, because the packed keypoints use `object.decode.box_space` (pixel) ([ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md)). The Pose26 export decode gives the keypoints as `(xy + anchor) * stride` in model-input pixels. The graph applies the sigmoid to the third value. (Ultralytics-Exporter [`yolo_sidecar.py:527`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L527); ultralytics 8.4.184 `nn/modules/head.py:765-777`, installed copy in the Ultralytics-Exporter `.venv`)
- MediaPipe landmark models (historical code of Qualcomm-Exporter): the wrapper multiplies the landmark output by `[W, H, W]` of the crop (face 192, hand 256). Thus the ONNX gives crop pixels, with z scaled by the width. The historical sidecar says `{method: coordinate, coordinate_space: pixel, is_3d: true, depth_unit: pixel}`. In this spec, that is `keypoint.geometry: 3d` and `keypoint.decode: {method: coordinate, coordinate_space: pixel, depth_unit: pixel}` ([ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md)). The README calls z relative, not metric. (Qualcomm-Exporter [`qai_catalog.py:336-361`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_catalog.py#L336-L361); [`qai_sidecar.py:251-259`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_sidecar.py#L251-L259); [`README.md:147-149`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/README.md#L147-L149); `qai_catalog.py:89, 122`, commit a095041a5e9450df18637596fbaf6409f79e9fc6 on no branch (secondary))
- The `TensorsToLandmarksCalculator` of MediaPipe divides z by the crop size and by `normalize_z` 0.4. The spec has no field for the second divisor. (the untracked hand pipeline plan of MediaPipe-Exporter (secondary))

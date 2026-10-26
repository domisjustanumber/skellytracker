---
id: post.pose.decode.simcc
title: SimCC decode
kind: postprocessor
since: v2024.09.1019
changed_in: []
selectors:
  - pose.decode.method=simcc
  - outputs[].semantic=simcc_x
  - outputs[].semantic=simcc_y
  - outputs[].semantic=simcc_z
implemented_by:
  validate: skellytracker/core/sidecar/model.py::PoseDecodeSpec._check_decode
  decode: skellytracker/core/detectors/processing/simcc_decode.py::simcc_pose_decode  # partial: no 3D (it raises); the split ratio is fixed at 2.0, not read from the bin counts; the score is the mean of the two softmax peaks
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/sidecar/test_rtmpose_body_sidecar.py
  - skellytracker/tests/sidecar/test_rtmpose_hand_sidecar.py
  - skellytracker/tests/sidecar/test_rtmpose_face_sidecar.py
  - skellytracker/tests/sidecar/test_rtmw_sidecar.py
vectors: null
status: {spec: stable, validate: implemented, decode: partial}
---

# SimCC decode

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pose.decode.depth_range` | array[2] | required when `is_3d: true` and `method: simcc` | The `[min, max]` root-relative depth (in `depth_unit`) that `Z_bins` span. The decoded bin position maps linearly to depth. |

`pose.decode.depth_range` is a field of [`pose.decode`](pose-schema.md#posedecode). That section defines the other `pose.decode` fields.

## Behaviour

- `simcc` — one `simcc_x` `(N, K, X_bins)` output and one `simcc_y` `(N, K, Y_bins)` output. When `is_3d: true`, there is also a `simcc_z` `(N, K, Z_bins)` output. The host reads the bin counts from the output tensors. The bin→pixel scale is `input_width / X_bins` and `input_height / Y_bins` (see Shape key). The location of each keypoint is the argmax bin. Its score is the max value. Decoded keypoints are in cropped image space. The host unprojects them to the source image. When `is_3d: true`, the `z` axis maps `Z_bins` linearly onto `depth_range` (in `depth_unit`).

[Shape key](pose-schema.md#shape-key)

## Validation rules

### Pose (`pose_estimator`)

- [ ] `V-post.pose.decode.simcc-1` When `pose.decode.is_3d: true` and `pose.decode.method: simcc`, `pose.decode.depth_range` must be present. It must be a length-2 array `[min, max]` in `depth_unit`.

See also [Pose schema](pose-schema.md#validation-rules).

## Implementer guidance

- The spec says that the SimCC score is the max value. Hosts use different rules. The mmpose function `get_simcc_maximum` takes `min(max(simcc_x), max(simcc_y))` on the raw outputs. The skellytracker function `get_simcc_maximum` takes the mean of the two softmax peaks. The rtmlib function takes the mean of the two raw peaks. A host with the min rule differed from mmpose by at most 0.0033 in score. The scores have different scales, so a keypoint threshold does not transfer between hosts. Decision [0024](../../../notes/decisions/0024-simcc-score-rule.md) (proposed) records this question and the sources of the three rules. (skellytracker `skellytracker/core/detectors/processing/simcc_decode.py` (`get_simcc_maximum`); secondary: OpenMMLab-Exporter `plans/hand-models-PLAN.md:101, 157-163`, a local plan file that git ignores)
- fp16 can move a SimCC keypoint to another bin. On one crop of a hand model, 4 of 21 fp16 keypoints fell in a different bin than fp32. The fp16 accuracy of the SimCC decode is not measured. (secondary: OpenMMLab-Exporter `plans/hand-models-PLAN.md:109-110`, a local plan file that git ignores)

## Authoring guidance

- RTMW: every RTMW config sets the codec `SimCCLabel` with `simcc_split_ratio=2.0`, `normalize=False` and `use_dark=False`. The contract of the exporter requires `simcc_x` to have `2 * W` bins and `simcc_y` to have `2 * H` bins. The real RTMW-M graph gives `(1, 133, 384)` and `(1, 133, 512)` for a 192 x 256 input. Thus `input_width / X_bins` is 0.5 px for each bin. `pose.decode` carries only `method: simcc`. (OpenMMLab-Exporter `rtmw/contract.py:14-15, 30, 79-81`, 68a6c6d; `mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:48-53`, 491c17b; `notes/decisions/0019-rtmw-real-export-sidecar-contract.md:27-31`, c85abf7)
- The two 384x288 RTMW configs (l and x) add `decode_visibility=True` to the codec. The sidecar has no field for it. The flag does not change the exported graph. (OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmw-x_8xb320-270e_cocktail14-384x288.py:55`, 491c17b; `notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md:77, 93`, c85abf7)

---
id: post.pose.decode.simcc
title: SimCC decode
kind: postprocessor
selectors:
  - pose.decode.method=simcc
  - outputs[].semantic=simcc_x
  - outputs[].semantic=simcc_y
implemented_by:
  validate: missing  # PoseDecodeSpec._check_decode (skellytracker/core/sidecar/model.py) keys on the removed key pose.decode.is_3d, and PoseSpec forbids pose.geometry (decisions/entries/90CE-minimal-sidecar-contract.md).
  decode: skellytracker/core/detectors/processing/simcc_decode.py::simcc_pose_decode  # partial: the split ratio is fixed at 2.0, not read from the bin counts; the score is the mean of the two softmax peaks
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/sidecar/test_rtmpose_body_sidecar.py
  - skellytracker/tests/sidecar/test_rtmpose_hand_sidecar.py
  - skellytracker/tests/sidecar/test_rtmpose_face_sidecar.py
  - skellytracker/tests/sidecar/test_rtmw_sidecar.py
vectors: null
status: {spec: stable, validate: missing, decode: partial}
---

# SimCC decode

## Fields

This section has no field of its own. [`pose.decode`](pose-schema.md#posedecode) defines the `pose.decode` fields.

## Behaviour

- `simcc` — one `simcc_x` `(N, K, X_bins)` output and one `simcc_y` `(N, K, Y_bins)` output. The host reads the bin counts from the output tensors. The bin→pixel scale is `input_width / X_bins` and `input_height / Y_bins` (see Shape key). The location of each keypoint is the argmax bin. Its score is the max value. Decoded keypoints are in cropped image space. The host unprojects them to the source image.
- The SimCC decode is 2D only. `V-post.pose.schema-7` requires `pose.geometry: 2d` with `method: simcc`. A 3D SimCC model adds a new section with its own contract ([ADR-9HBB](../../../decisions/entries/9HBB-simcc-decode-is-2d-only.md)).

[Shape key](pose-schema.md#shape-key)

## Validation rules

### Pose (`pose_estimator`)

This section has no rule of its own ([ADR-9HBB](../../../decisions/entries/9HBB-simcc-decode-is-2d-only.md)).

See also [Pose schema](pose-schema.md#validation-rules).

## Implementer guidance

- The spec says that the SimCC score is the max value. Hosts use different rules. The mmpose function `get_simcc_maximum` takes `min(max(simcc_x), max(simcc_y))` on the raw outputs. The skellytracker function `get_simcc_maximum` takes the mean of the two softmax peaks. The rtmlib function takes the mean of the two raw peaks. A host with the min rule differed from mmpose by at most 0.0033 in score. The scores have different scales, so a keypoint threshold does not transfer between hosts. (skellytracker `skellytracker/core/detectors/processing/simcc_decode.py` (`get_simcc_maximum`); the untracked hand models plan of OpenMMLab-Exporter (secondary))
- fp16 can move a SimCC keypoint to another bin. On one crop of a hand model, 4 of 21 fp16 keypoints fell in a different bin than fp32. The fp16 accuracy of the SimCC decode is not measured. (the untracked hand models plan of OpenMMLab-Exporter (secondary))

## Authoring guidance

- RTMW: every RTMW config sets the codec `SimCCLabel` with `simcc_split_ratio=2.0`, `normalize=False` and `use_dark=False`. The contract of the exporter requires `simcc_x` to have `2 * W` bins and `simcc_y` to have `2 * H` bins. The real RTMW-M graph gives `(1, 133, 384)` and `(1, 133, 512)` for a 192 x 256 input. Thus `input_width / X_bins` is 0.5 px for each bin. `pose.decode` carries only `method: simcc`. (OpenMMLab-Exporter [`rtmw/contract.py:14-15`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/68a6c6d103a63d9df10668990d937abb23de73fb/rtmw/contract.py#L14-L15), [`rtmw/contract.py:30`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/68a6c6d103a63d9df10668990d937abb23de73fb/rtmw/contract.py#L30), [`rtmw/contract.py:79-81`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/68a6c6d103a63d9df10668990d937abb23de73fb/rtmw/contract.py#L79-L81); [`mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:48-53`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/491c17b43c0f2011dfd386ab5c6345ef0f850ada/mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py#L48-L53); [`notes/decisions/0019-rtmw-real-export-sidecar-contract.md:27-31`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c85abf7da34d1e4da7c129f3382173f7153f60fa/notes/decisions/0019-rtmw-real-export-sidecar-contract.md#L27-L31))
- The two 384x288 RTMW configs (l and x) add `decode_visibility=True` to the codec. The sidecar has no field for it. The flag does not change the exported graph. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmw-x_8xb320-270e_cocktail14-384x288.py:55`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/491c17b43c0f2011dfd386ab5c6345ef0f850ada/mmdeploy-convert/model_cfgs/rtmw-x_8xb320-270e_cocktail14-384x288.py#L55); [`notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md:77`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c85abf7da34d1e4da7c129f3382173f7153f60fa/notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md#L77), [`notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md:93`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c85abf7da34d1e4da7c129f3382173f7153f60fa/notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md#L93))

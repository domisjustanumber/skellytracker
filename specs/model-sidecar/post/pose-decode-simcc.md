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
vectors: vectors/post.pose.decode.simcc.yaml
status: {spec: stable, validate: missing, decode: partial}
---

# SimCC decode

## Fields

This section has no field of its own. [`pose.decode`](pose-schema.md#posedecode) defines the `pose.decode` fields.

## Behaviour

- `simcc` — one `simcc_x` `(N, K, X_bins)` output and one `simcc_y` `(N, K, Y_bins)` output. The
  host reads the bin counts from the output tensors. For each crop `n` and each keypoint `k`, the
  host does the steps below on the raw values of `simcc_x` and `simcc_y`. The host does not apply a
  softmax.

```text
bin_x  = argmax over b of simcc_x[n, k, b]       (on a tie, the lowest b; see NaN below)
bin_y  = argmax over b of simcc_y[n, k, b]       (on a tie, the lowest b; see NaN below)
peak_x = simcc_x[n, k, bin_x]
peak_y = simcc_y[n, k, bin_y]
score  = peak_y   when peak_x > peak_y
         peak_x   otherwise                      (thus min(peak_x, peak_y) when no peak is NaN)
when score <= 0:
    bin_x = -1, bin_y = -1
x = bin_x * input_width / X_bins
y = bin_y * input_height / Y_bins
```

- The score is a raw output value. It has no fixed range: it can be negative or more than 1.
- A keypoint with a score `<= 0` keeps its score. Its position is `x = -input_width / X_bins` and
  `y = -input_height / Y_bins`. The host unprojects it as each other keypoint.
- Bin `0` gives the position `0`. The decode adds no half-bin offset.
- NaN raw values. In a row of `simcc_x` or `simcc_y` that holds a NaN, the bin is the lowest `b`
  with a NaN, and the peak is NaN. Each comparison with a NaN is false. Thus:
  - A NaN in the row of `simcc_x` gives the score NaN.
  - A NaN only in the row of `simcc_y` gives the score `peak_x`. When `peak_x <= 0`, both axes get
    the bin `-1`.
  - A NaN score is not `<= 0`. The bins stay, and the position comes from the bins. The position
    is never NaN.
- The decoded keypoints are in the model-input pixels of the crop. The host unprojects them to the
  source image ([Unprojection](unprojection.md)).
- The SimCC decode is 2D only. `V-post.pose.schema-7` requires `pose.geometry: 2d` with `method: simcc`. A 3D SimCC model adds a new section with its own contract ([ADR-9HBB](../../../decisions/entries/9HBB-simcc-decode-is-2d-only.md)).

[Shape key](pose-schema.md#shape-key)

## Validation rules

### Pose (`pose_estimator`)

This section has no rule of its own ([ADR-9HBB](../../../decisions/entries/9HBB-simcc-decode-is-2d-only.md)).

See also [Pose schema](pose-schema.md#validation-rules).

## Implementer guidance

- The score is the score of mmpose v1.3.2 `get_simcc_maximum` with `apply_softmax=False`. The
  skellytracker function `get_simcc_maximum` takes the mean of the two softmax peaks. The rtmlib
  function takes the mean of the two raw peaks. On COCO val2017 (6352 GT persons, flip test off),
  RTMW-m gave the body AP 0.7477 with the rule of this section, 0.7461 with the raw mean and 0.6560
  with the softmax mean. The detectors of skellytracker drop a keypoint below
  `confidence_threshold: 0.004`. That value fits only the softmax score. (OpenMMLab-Exporter
  [`notes/decisions/scripts/simcc_score_rule_parity.py`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/16b06c10986d2010989b101a13d56cbfebbd6748/notes/decisions/scripts/simcc_score_rule_parity.py)
  at `16b06c10986d2010989b101a13d56cbfebbd6748`,
  [OpenMMLab-Exporter ADR-0053](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d9704753a22792c32a1d3018a0c9e9ea2d279d71/decisions/entries/0053-pose-sidecar-parity-runs.md);
  skellytracker `skellytracker/core/detectors/processing/simcc_decode.py` (`get_simcc_maximum`)
  and `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py`
  (`confidence_threshold`))
- The NaN rule of Behaviour is the result of mmpose v1.3.2 on NumPy arrays. `np.argmax` gives the
  index of the first NaN, `np.amax` gives NaN, and the comparisons `max_val_x > max_val_y` and
  `vals <= 0.` are false for a NaN. In Python, `np.argmax`, `np.max` and
  `np.where(peak_x > peak_y, peak_y, peak_x)` give the rule. In another language, do not use a max
  function that skips a NaN or that gives a later NaN. Do not replace the strict `>` with a `min`
  function. When one peak is NaN, a `min` function can give NaN or the other peak, and that is
  not always the result of this rule (for example, `np.minimum` gives NaN for a NaN `peak_y`).
  ([`mmpose/codecs/utils/post_processing.py:90-99`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/codecs/utils/post_processing.py#L90-L99)
  at mmpose `5408bc76f5b848cf925a0d1857899011d8c5b497`, tag `v1.3.2`;
  [`numpy/_core/src/multiarray/argfunc.dispatch.c.src:313-345`](https://github.com/numpy/numpy/blob/c60f172b3330f76d6592362137f34c4a3030a001/numpy/_core/src/multiarray/argfunc.dispatch.c.src#L313-L345)
  at NumPy `c60f172b3330f76d6592362137f34c4a3030a001`)
- The OpenMMLab-Exporter host function `decode_simcc` follows Behaviour. It passes 15 of 15 numeric cases of the vector file. (OpenMMLab-Exporter [`onnx_runtime/simcc.py:84-108`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/onnx_runtime/simcc.py#L84-L108); [OpenMMLab-Exporter ADR-HJF1](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/decisions/entries/HJF1-host-adopts-landed-spec-text.md) item 8 and Evidence) In the RTMW parity run, its scores and coordinates are equal to those of mmpose v1.3.2 `SimCCLabel.decode`, bit for bit. The rows were the real raw rows of the 49 persons in each size and 17 crafted rows: scores `<= 0`, `-0.0`, argmax ties and NaN values. (OpenMMLab-Exporter [`decisions/scripts/rtmw_parity.py:98-105`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/decisions/scripts/rtmw_parity.py#L98-L105) and [`decisions/scripts/rtmw_parity_worker.py:235-253`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/decisions/scripts/rtmw_parity_worker.py#L235-L253) at `3e326df00726df8110773ed62cf38d02948a71a5`, run of 2026-11-09 with mmpose 1.3.2; the results are in the intake `model-rtmw-wholebody133@openmmlab-exporter` v2 (secondary)) The exporter wrote `decode_simcc` after its own reference module of the score-rule proposal. Thus it is not an independent implementation of this section. ([`proposal.md`](../proposals/simcc-score-rule/proposal.md); [ADR-03PH](../decisions/entries/03PH-simcc-score-rule.md); row K8 of the intake `model-rtmw-wholebody133@openmmlab-exporter` v2 (secondary))
- fp16 can move a SimCC keypoint to another bin. On one crop of a hand model, 4 of 21 fp16 keypoints fell in a different bin than fp32. (the untracked hand models plan of OpenMMLab-Exporter (secondary)) The RTMW parity run counted the keypoints that fell in a different bin than mmpose, on the mmpose crop tensor. Of 6517 keypoints (49 persons x 133), the counts for fp32 and fp16 are: m 183 and 812, l-256 182 and 686, x-256 263 and 1233, l-384 304 and 1494, x-384 465 and 2040. Each of these bin changes is inside the export error of the raw values. On an almost flat output row, a bin change moved a keypoint by up to 659 px in the source image. (OpenMMLab-Exporter [`decisions/scripts/rtmw_parity.py:115-126`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/decisions/scripts/rtmw_parity.py#L115-L126), [`decisions/scripts/rtmw_parity.py:905-936`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/decisions/scripts/rtmw_parity.py#L905-L936) and [`decisions/scripts/rtmw_parity_worker.py`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/decisions/scripts/rtmw_parity_worker.py) at `3e326df00726df8110773ed62cf38d02948a71a5`; run of 2026-11-09 with mmpose 1.3.2 and torch 2.0.0+cu118 against onnxruntime-gpu 1.31.1 (CUDA execution provider); the results are in the intake `model-rtmw-wholebody133@openmmlab-exporter` v2 (secondary))
- To give the steps of Behaviour, the package code needs these changes. `get_simcc_maximum` must
  not apply a softmax. Its score must be `np.where(max_x > max_y, max_y, max_x)` of the raw peaks,
  and the `-1` rule stays. With `np.argmax` and `np.max`, these steps also give the NaN rule.
  `decode_simcc` must read the bin scale from the bin counts (`input_width / X_bins`), not from
  `_SIMCC_SPLIT_RATIO`. `rtmpose_preprocessing.py` has a second copy of `get_simcc_maximum`. Its
  copy of `decode_simcc` is `rtmpose_letterbox_postprocess`. In `golden_parity.py`,
  `simcc_bin_size_px` uses `_SIMCC_SPLIT_RATIO`: the bin size must also come from the bin counts. The `confidence_threshold: 0.004` defaults of the RTMPose
  body, face and hand detectors and of the RTMW detector need a value for the raw score. The `is_3d`
  branch of `simcc_pose_decode` does not change. Stage M8 of the implementation plan removes it
  ([ADR-9HBB](../../../decisions/entries/9HBB-simcc-decode-is-2d-only.md)). No validator change is
  necessary. Run the numeric cases of the vector file through `get_simcc_maximum` and
  `decode_simcc`. Add a golden test on one RTMW crop with mmpose scores. (skellytracker
  `skellytracker/core/detectors/processing/simcc_decode.py` (`get_simcc_maximum`, `decode_simcc`,
  `simcc_pose_decode`), `skellytracker/core/detectors/keypoint_detectors/rtmpose/rtmpose_preprocessing.py`,
  `skellytracker/tests/sidecar/golden_parity.py` (`simcc_bin_size_px`),
  `skellytracker/core/detectors/keypoint_detectors/rtmpose/body/rtmpose_body_detector.py`,
  `skellytracker/core/detectors/keypoint_detectors/rtmpose/face/rtmpose_face_detector.py`,
  `skellytracker/core/detectors/keypoint_detectors/rtmpose/hand/rtmpose_hand_detector.py` and
  `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py`
  (`confidence_threshold`); part 6 of [`proposal.md`](../proposals/simcc-score-rule/proposal.md#6-skellytracker-implementation-proposal);
  [ADR-03PH](../decisions/entries/03PH-simcc-score-rule.md)) (implementation stage)

## Authoring guidance

- RTMW: every RTMW config sets the codec `SimCCLabel` with `simcc_split_ratio=2.0`, `normalize=False` and `use_dark=False`. The contract of the exporter requires `simcc_x` to have `2 * W` bins and `simcc_y` to have `2 * H` bins. For a 192 x 256 input, the RTMW-M graph gives `simcc_x` 384 bins and `simcc_y` 512 bins. Thus `input_width / X_bins` is 0.5 px for each bin. The graph declares axis 1 (the keypoint axis) as symbolic (`dim_param`). At run time, axis 1 is 133: onnxruntime 1.31.1 (CPU) gives `(N, 133, 384)` and `(N, 133, 512)`. (the graph read and the V5 step of the batch-conversion check in the intake `model-rtmw-wholebody133@openmmlab-exporter` v2, 2026-11-09 (secondary)) The example writes axis 1 as `-1` in the `output_shapes` of each size. ([`rtmw-wholebody133.yaml`](../examples/detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133.yaml)) `pose.decode` carries only `method: simcc`. (OpenMMLab-Exporter [`rtmw/contract.py:14-15`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/68a6c6d103a63d9df10668990d937abb23de73fb/rtmw/contract.py#L14-L15), [`rtmw/contract.py:30`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/68a6c6d103a63d9df10668990d937abb23de73fb/rtmw/contract.py#L30), [`rtmw/contract.py:79-81`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/68a6c6d103a63d9df10668990d937abb23de73fb/rtmw/contract.py#L79-L81); [`mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:48-53`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/491c17b43c0f2011dfd386ab5c6345ef0f850ada/mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py#L48-L53); [`notes/decisions/0019-rtmw-real-export-sidecar-contract.md:27-31`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c85abf7da34d1e4da7c129f3382173f7153f60fa/notes/decisions/0019-rtmw-real-export-sidecar-contract.md#L27-L31))
- The two 384x288 RTMW configs (l and x) add `decode_visibility=True` to the codec. The sidecar has no field for it. The flag does not change the exported graph. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmw-x_8xb320-270e_cocktail14-384x288.py:55`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/491c17b43c0f2011dfd386ab5c6345ef0f850ada/mmdeploy-convert/model_cfgs/rtmw-x_8xb320-270e_cocktail14-384x288.py#L55); [`notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md:77`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c85abf7da34d1e4da7c129f3382173f7153f60fa/notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md#L77), [`notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md:93`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c85abf7da34d1e4da7c129f3382173f7153f60fa/notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md#L93)) With the flag, `SimCCLabel.decode` also returns a softmax visibility. `BaseHead.decode` keeps the first value as `keypoint_scores` and stores the visibility as `keypoints_visible`. Thus the flag changes no keypoint and no `keypoint_scores`. (mmpose [`mmpose/codecs/simcc_label.py:193-198`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/codecs/simcc_label.py#L193-L198) and [`mmpose/models/heads/base_head.py:81-93`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/models/heads/base_head.py#L81-L93) at mmpose `5408bc76f5b848cf925a0d1857899011d8c5b497`, tag `v1.3.2`) The intake verdict of such an undeclared extra decode value is `out of scope` ([ADR-R6J9](../decisions/entries/R6J9-test-time-steps-and-unreachable-branches.md)). On COCO-WholeBody v1.0 val, the visibility of the 384x288 sizes ranks valid hands worse than the SimCC score. ([OpenMMLab-Exporter ADR-0041](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/decisions/entries/0041-rtmw-wrist-gate.md) (secondary))

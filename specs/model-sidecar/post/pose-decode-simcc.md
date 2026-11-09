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
- fp16 can move a SimCC keypoint to another bin. On one crop of a hand model, 4 of 21 fp16 keypoints fell in a different bin than fp32. The fp16 accuracy of the SimCC decode is not measured. (the untracked hand models plan of OpenMMLab-Exporter (secondary))

## Authoring guidance

- RTMW: every RTMW config sets the codec `SimCCLabel` with `simcc_split_ratio=2.0`, `normalize=False` and `use_dark=False`. The contract of the exporter requires `simcc_x` to have `2 * W` bins and `simcc_y` to have `2 * H` bins. The real RTMW-M graph gives `(1, 133, 384)` and `(1, 133, 512)` for a 192 x 256 input. Thus `input_width / X_bins` is 0.5 px for each bin. `pose.decode` carries only `method: simcc`. (OpenMMLab-Exporter [`rtmw/contract.py:14-15`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/68a6c6d103a63d9df10668990d937abb23de73fb/rtmw/contract.py#L14-L15), [`rtmw/contract.py:30`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/68a6c6d103a63d9df10668990d937abb23de73fb/rtmw/contract.py#L30), [`rtmw/contract.py:79-81`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/68a6c6d103a63d9df10668990d937abb23de73fb/rtmw/contract.py#L79-L81); [`mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:48-53`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/491c17b43c0f2011dfd386ab5c6345ef0f850ada/mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py#L48-L53); [`notes/decisions/0019-rtmw-real-export-sidecar-contract.md:27-31`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c85abf7da34d1e4da7c129f3382173f7153f60fa/notes/decisions/0019-rtmw-real-export-sidecar-contract.md#L27-L31))
- The two 384x288 RTMW configs (l and x) add `decode_visibility=True` to the codec. The sidecar has no field for it. The flag does not change the exported graph. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmw-x_8xb320-270e_cocktail14-384x288.py:55`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/491c17b43c0f2011dfd386ab5c6345ef0f850ada/mmdeploy-convert/model_cfgs/rtmw-x_8xb320-270e_cocktail14-384x288.py#L55); [`notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md:77`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c85abf7da34d1e4da7c129f3382173f7153f60fa/notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md#L77), [`notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md:93`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c85abf7da34d1e4da7c129f3382173f7153f60fa/notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md#L93))

# XXZ8 — The host frame is BGR, the precision of the geometry and the pixel math, and float32 score comparisons

**Status:** absorbed into [`input.md#fields`](../../specs/model-sidecar/common/input.md#fields), [`interpolation.md#compute-dtype`](../../specs/model-sidecar/pre/interpolation.md#compute-dtype), [`interpolation.md#precision`](../../specs/model-sidecar/pre/interpolation.md#precision), [`interpolation.md#validation-rules`](../../specs/model-sidecar/pre/interpolation.md#validation-rules), [`normalization.md#behaviour`](../../specs/model-sidecar/pre/normalization.md#behaviour), [`decode.md#selection-behaviour`](../../specs/model-sidecar/post/object/decode.md#selection-behaviour), [`selection-top-k.md#behaviour`](../../specs/model-sidecar/post/object/selection-top-k.md#behaviour), 2026-11-16 (user, 2026-11-16; PR: pending).

## Decision

1. **Host frame.** The host gets each frame as an 8-bit, 3-channel BGR image in HWC layout. It
   reverses the channels for `color_format: rgb` and keeps them for `bgr`, at any step before the
   normalization. A host that reverses the channels after the resize also reverses an array
   `pad_value` that it gives to the resize.
2. **Precision.**
   - The geometry is float64: the scale, the scaled sizes, the offsets, the warp matrix `M` of
     `fit`, each Inverse, the clamp and the size filter. The ROI and `M` of `affine_crop` keep the
     float32 steps of their section.
   - Each normalization mode computes in float32, with the float32 value of each constant, in the
     order of the formula. Then it casts to `input.dtype`.
   - New rule `V-pre.resize.interpolation-2`: with an 8-bit resize, each value of `pad_value` and
     `crop_policy.pad_value` must be an integer from 0 to 255.
3. **Score comparisons.** The host rounds the score and the threshold to float32, then it compares
   the two float32 values with strict `>`. This applies to `min_score`, `nms.score_threshold` and a
   caller override. The host computes `score_activation` in float32: `sigmoid` is
   `1 / (1 + exp(-x))` on the float32 value of each logit.
4. The references `pre_normalize.py`, `post_object_decode.py` and `post_object_selection_nms.py`,
   and the formula modules `pre_normalize.py`, `post_object_decode.py`,
   `post_object_selection_none.py`, `post_object_selection_nms.py` and
   `post_object_selection_top_k.py` of `tools/vector_formulas/` change to these rules. The
   `float32-stable` test case of `tools/tests/test_vectors.py` moves from a score to an NMS IoU.

## Reason

- The user accepted the three rules on 2026-11-16, after two reviews, and selected the float32
  activation.
- The package frame is BGR (`skellytracker/core/tracker/tracker.py`). The normalize reference
  already reverses the channels after the resize. Item 1 changes no vector.
- float32 pixel math matches upstream: the float32 host gives the RTMW tensor bit for bit
  ([Normalization](../../specs/model-sidecar/pre/normalization.md#implementer-guidance)).
- A fractional pad had two results: the letterbox reference cuts 115.5 to 115, and the
  `affine_crop` border rounds it to 116. No sidecar declares a fractional pad.
- Each upstream compares in float32. Torch, NumPy 2 and the ONNX `NonMaxSuppression` operator round
  a Python float threshold to float32.
- The upstream activation of RF-DETR, the only spec model with a host-side activation, is a torch
  float32 sigmoid (rfdetr 1.11.2 `models/postprocess.py:133`).

## Consequences

- Two conforming hosts can keep different detections near a threshold, because a float32 `exp`
  differs by a few ulps between libraries and devices. The vectors avoid such values.
- The normalize vectors change in the sixth decimal, inside the tolerance 1e-5. No other vector
  changes.
- **To change to the float64 activation later:** replace the sentence "The host computes
  `score_activation` in float32" of item 3 with "The host computes `score_activation` in float64
  from the output value, then rounds the score once to float32". Edit step 1 of
  [Top-k selection](../../specs/model-sidecar/post/object/selection-top-k.md#behaviour), the sigmoid
  of `tools/vector_formulas/post_object_selection_top_k.py` and the probe line of its Implementer
  guidance. That option gives one score on each host, within 2 to 3 ulps of torch.

## Evidence

- [`sigmoid_precision_probe.py`](../scripts/sigmoid_precision_probe.py), torch 2.14.1+cu130, NumPy
  2.5.4, ONNX Runtime 1.31.0. Against the float64 sigmoid rounded to float32, the largest
  difference is 2 ulps on torch CPU and 3 on torch CUDA and NumPy float32. The keep or drop flips
  near 8 thresholds are 2, 3 and 3 of 80,008 logits, and 13 for the ONNX Runtime CPU `Sigmoid`
  operator. Logit 0.8472979 at 0.7 is dropped on torch and kept on NumPy float32.
- A pad of 115.5 gives 115 in `pre_resize_letterbox.py` and 116 in the `affine_crop` border
  (`cv2.warpAffine` `borderValue`; OpenCV 5.0.0, NumPy 2.4.6).

## Alternatives rejected

- **The float64 activation, rounded once to float32.** It gives one result on each host. The user
  selected the float32 activation of upstream. See Consequences for the change.
- **float64 pixel math.** It moves the result away from upstream near the `float16` midpoints.
- **Convert the frame to the tensor order first.** The result is the same, and each `pixels_bgr`
  vector case changes.

## Open work

See [open-work.md](../../specs/model-sidecar/decisions/open-work.md), "Choices to revisit".

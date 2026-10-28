# 0041 — RTMDet: host `selection: nms` with the mmdet candidate filters, clamp and visit order

**Status:** proposed, 2026-10-25 (OpenMMLab-Exporter proposal).

## Decision

This entry supersedes [0011](0011-rtmdet-host-nms.md) in full. It restates each rule of 0011 that
stays. It holds no scope rule. [0042](0042-vnext-scope-nms-filters.md) adds the new fields to the
`vNEXT` scope.

**RTMDet person.**

- The graph ends before NMS. It outputs the decoded box and the sigmoid person score of each anchor
  point: `boxes` `[B, A, 4]` (`xyxy`, model-input pixels) and `scores` `[B, A]`. These outputs are the
  complete candidate set
  ([Selection behaviour](../../specs/model-sidecar/post/detection-decode.md#selection-behaviour)).
- The sidecar declares `decode.selection: nms`. The host runs the NMS.
- The `nms` block holds the upstream mmdet `test_cfg` values of the person configs:
  `iou_threshold: 0.6`, `score_threshold: 0.05` (`score_thr`) and `post_nms_top_k: 100`
  (`max_per_img`). Changed: it also holds `pre_nms_top_k: 1000` (`nms_pre`) with
  `level_strides: [8, 16, 32]`, `min_bbox_size: 0` and `clamp_to_input: true`. The decode sets
  `clamp_boxes: false`.
- `A` is 2100 at 320 and 8400 at 640. The family-level output shape uses `-1` for the row dimension.
  Each batch artifact gives the value in `output_shapes`. The rows are in three levels.
  `level_strides` gives the row count of each level from the input size.
- `selection: nms` forbids `class_logits_output`
  ([Validation rules](../../specs/model-sidecar/post/selection-nms.md#validation-rules)).

**Changed: the steps of `selection: nms`.** Each new field is optional. When it is absent, the old
meaning stays.

- The host drops each candidate with `score <= nms.score_threshold`. With `nms.pre_nms_top_k`, it
  then keeps that number of candidates in each level, highest score first. `nms.level_strides` gives
  the levels. Without it, all rows are one level.
- With `nms.clamp_to_input: true`, the host clamps each box to `[0, W_in]` and `[0, H_in]` in
  model-input pixels before the NMS. With `nms.min_bbox_size`, it then drops each candidate whose
  width or height in source pixels is `<= nms.min_bbox_size`.
- The NMS runs in model-input pixels. It visits the candidates in descending score order. The
  survivors have the same order. A tie goes to the lower row index.
- The area of a box is `max(0, x2 - x1) * max(0, y2 - y1)`. Thus an inverted box has the area 0.
  When the area of the union is 0, the IoU is 0.
- `clamp_boxes` clamps to the closed bounds `[0, src_w]` and `[0, src_h]`. It does not drop a row.
  A row with zero area stays.

## Reason

- A graph that keeps the mmdeploy NMS loses candidates. The capped graph lost 0.0114 AP and 0.027 AR
  on `rtmdet-person-medium` (OpenMMLab-Exporter 0008). A graph that ends before NMS keeps every
  candidate.
- Host NMS costs about 1 ms for each image for one class (OpenMMLab-Exporter 0016 and 0017).
- The `nms` block copies the upstream `test_cfg`. With these values, the spec decode reproduces the
  PyTorch AP.
- The spec must fully describe these models (user). mmdet clamps to the padded model input before
  the NMS, keeps 1000 candidates in each level and drops boxes with no width or height. The new
  fields change no AP. Without them, a sidecar cannot describe the decode.
- The IoU does not change under the unprojection of a resize method of the spec. Thus the NMS stays
  in model-input pixels.
- Without a defined visit order, box area and zero-union IoU, two hosts can keep different rows.
- `class_logits` with `selection: nms` has no user. The person family has one class. The 80-class
  family is not exported (OpenMMLab-Exporter 0017).

## Evidence

[evidence.md](../../specs/model-sidecar/proposals/nms-clamp-order/evidence.md) holds the
measurements: the 0011 parity and cost tables, and the COCO val2017 measurements of the proposal.
The cap and the size filter change no AP. The clamp order changes the kept rows on 668 of 5000 nano
images and 405 of 5000 medium images. With all fields, the sidecar path keeps the same rows as a
literal mmdet order on 5000 of 5000 images for both sizes.

## Alternatives rejected

- Keep mmdeploy's NMS in the graph and declare `selection: none`. It lost 0.0114 AP.
- A cap over all rows in place of `level_strides`. It is a different algorithm.
- The best class of each row for a multi-class family. It lost 0.0051 AP on tiny.
- Add `class_logits` with `selection: nms` now. No family in scope needs it.
- Spec steps equal to the ONNX `NonMaxSuppression` operator. The operator has no cap, no clamp and no
  size filter. It gives an inverted box an area that is not 0.

## Not repeated

- Write `pre_nms_top_k` with `level_strides` when the upstream cap acts on each level. Do not write a
  per-level cap without `level_strides`. A cap over all rows is a different algorithm.
- Do not use the best class of each row for a multi-class NMS-free family. Use every (row, class)
  pair. That needs `class_logits` with `selection: nms` first.
- Do not compare the in-graph NMS and the host decode at the `0.001` threshold. The in-graph variant
  caps 300 boxes for each class.
- Do not declare `class_logits_output` with `selection: nms`. The validation rules forbid it.
- Do not read "invisible in AP" as "no effect". The clamp order changes the kept rows.
- A host that uses the ONNX operator must apply the filters and the clamp to its inputs. It must give
  an inverted box the area 0.
- An RTMDet person-only family and an 80-class family are two families ([0010](0010-family-invariant.md)).

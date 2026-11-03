# Mapping hints for phase 1

- **Graph.** Record the input name, dtype, layout, and static or dynamic dims. The spec allows only an
  NCHW input (the heading "Authoring guidance" in
  `../freemocap/skellytracker/specs/model-sidecar/common/input.md`). Read the dims from the
  graph. A config name or a file name (for example "dynamic") is not evidence of the dims. Record the
  name, dtype and shape of each output. Record the batch of each file. Dim 0 is the batch axis.
  Record the I/O dtype for each precision: fp16 files often keep float32 I/O. Look for normalization
  inside the graph (Sub, Div or Mul near the input). Look for NMS or TopK near the outputs. A step
  inside the graph is a row too.
- **NMS inside the graph.** The sidecar does not declare the NMS parameters of the graph, but they
  change the outputs. Record the IoU threshold, the score threshold and the row caps of the graph.
  Compare them with the upstream test config. A different value is an export defect: write it in the
  row.
- **Identity.** Record `model_id`, `display_name` and `role`. For an object detector, `model_id` is
  the family. Thus the folder name and the file name are the same, for example
  `object_detectors/rtmdet-person/rtmdet-person.yaml`. For a keypoint detector, `model_id` is
  `{family}-{part}`, for example `rtmw-wholebody` in `keypoint_detectors/rtmw/wholebody/`. The spec
  has no rule yet for a suffix after the part, or for two models of one family and one part
  ([Spec defects](../decisions/open-work.md#spec-defects)). Until a spec change adds such a rule,
  the current text applies. A name changes no tensor and no decoded output, so the `model_id` row is
  never a `near-miss`:
  - Write `{family}-{part}` as the sidecar value. The verdict is `exact`. If the exporter or the spec
    example uses an id with a suffix, write that id in the last column.
  - If another model of the same family and part also needs the id `{family}-{part}`, the current
    text has no id for your model. The row is a `gap`.
  - If the spec has no `model_id` rule for the role of the model (a new role), the row is a `gap`.
    The proposal of the role covers it.
- **Family.** One family has one preprocessing contract and one post-processing contract. If two sizes
  need a different contract, they are two families (two sidecars). Name the files by the convention of
  the spec (the heading "File extension and naming" in
  `../freemocap/skellytracker/specs/model-sidecar/format/file-layout.md`). The spec allows any
  lowercase token as a size name. Use the size name of the upstream, also for a family with one size.
  If the upstream has no size name, choose a token and write the reason in the intake.
- **Preprocessing.** For each value, record the upstream line behind it. If the "Authoring guidance"
  heading of a spec section has text, use it. Also record:
  - the dtype of the image when the upstream resizes it (for example uint8, before the cast);
  - the arithmetic of the scale, the scaled size and the offsets: float32 or float64, and the order of
    the operations. In float64, `77 * (640 / 77)` is `639.9999999999999`. Thus a rounding at an
    integer or at a tie can change the size;
  - the arithmetic of the normalization. In float32, `pixel / 255` and `pixel * (1 / 255)` differ in
    the last bit for 126 of the 256 byte values;
  - the pixel-centre convention of each resize call. `cv2.resize` and `cv2.warpAffine` put the pixel
    centres in different places. Match the call that the spec names for the method. Record the
    convention of the upstream call in the intake
    ([Spec defects](../decisions/open-work.md#spec-defects));
  - the border value of each warp, for each channel. For `fit` and `affine_person_crop`, give one
    value for each channel, for example `pad_value: [114, 114, 114]`. This form is `exact` under the
    current text. A scalar is correct for `letterbox`. In your host code, give `cv2.warpAffine` one
    value for each channel. A scalar `borderValue` fills only the first channel
    ([Spec defects](../decisions/open-work.md#spec-defects)).
- **Outputs and decode.** Record the semantics of each output. Record the `selection`: graph-final
  rows (`none`), top-k over logits (`top_k`), or host NMS (`nms`). Record if the sigmoid is in the
  graph. Take the thresholds from the upstream test config, not from the defaults. Record the class
  IDs. Check `clamp_boxes` against the upstream: the default is `true`, so a sidecar without the field
  clamps the boxes. The clamp bounds are `[0, W]` and `[0, H]`, with `W` and `H` the source-image
  size (the heading "Selection behaviour" in
  `../freemocap/skellytracker/specs/model-sidecar/post/detection-decode.md`). Map the area filter of
  the upstream, for example `min_bbox_size` of mmdet, to `decode.min_box_size`. Omit
  `decode.min_box_size` when the upstream keeps the boxes with zero area
  ([ADR-17KN](../../../decisions/entries/17KN-one-selection-pipeline.md)). The spec does not define
  the dtype of the score comparison ([Spec defects](../decisions/open-work.md#spec-defects)).
  Record what the upstream does.
- **Pose.** Write `tracked_points` in native model output order. Record the connections, the decode
  method and the `landmark_schema`. For a bottom-up model, record how the pose rows align with the
  detection rows. The spec says that a packed keypoint `score` is already activated. The spec has no
  field for a keypoint-score activation. If the host must activate the keypoint scores, that is a gap.

## Near-misses seen so far

These cases came up in earlier intakes
([ADR-ESP4](../../../decisions/entries/ESP4-one-home-for-each-workflow-rule.md)).

- **A letterbox where the upstream code warps to a fractional size.** The upstream code warps the
  full frame with `cv2.warpAffine` to a scaled size that is not rounded. If you map it to
  `letterbox`, the verdict is `near-miss`: `letterbox` rounds the scaled size and uses a resize plus
  padding. Read the section `pre.resize.fit`
  (`../freemocap/skellytracker/specs/model-sidecar/pre/resize-fit.md`) and compare it with the
  upstream code ([ADR-0012](../decisions/entries/0012-fit-resize-for-rtmo.md);
  [OpenMMLab-Exporter ADR-0020](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0020-rtmo-sidecar-contract.md).
- **A letterbox where the upstream code cuts the scaled size with `int()` or `floor`.** The
  `rounding` field has no value for a cut. The verdict is `near-miss`.
- **An ROI refiner described as a pose estimator with two fake keypoints.** The verdict is `gap`.
  The rule is the known case of [Rules](rules.md#rules).

# 0011 — RTMDet: NMS-free graph with host `selection: nms`; no `pre_nms_top_k`

**Status:** accepted, 2026-10-22 (backfilled from
[#81, `specs/model-sidecar/sidecar-spec.md`, "RTMDet person"](../sidecar-spec.md#rtmdet-person-openmmlab-exporter-nms-free-outputs-host-nms)
and OpenMMLab-Exporter 0008, OpenMMLab-Exporter 0009, OpenMMLab-Exporter 0016 and
OpenMMLab-Exporter 0017; the measurements are dated 2026-10-20).

## Decision

- The RTMDet person graph ends before NMS. It outputs every anchor point's decoded box and
  sigmoid person score:
  - `boxes`, shape `[B, A, 4]`, `xyxy` in model-input pixels;
  - `scores`, shape `[B, A]`.
- The sidecar declares `decode.selection: nms`. The host runs the NMS.
- The `nms` block holds the upstream mmdet `test_cfg` values of the person configs:

  | Sidecar field | Value | Upstream `test_cfg` key |
  |---|---|---|
  | `nms.iou_threshold` | `0.6` | `nms.iou_threshold` |
  | `nms.score_threshold` | `0.05` | `score_thr` |
  | `nms.post_nms_top_k` | `100` | `max_per_img` |

- The row count `A` depends on the input size. It is 2100 at 320 and 8400 at 640. The family-level
  output shape uses `-1` for the row dimension. Each batch artifact gives the concrete value in
  `output_shapes`.
- The spec has no `nms.pre_nms_top_k` field. The sidecar does not express the mmdet `nms_pre` cap.
  The person configs set `nms_pre` to 1000.
- The spec does not allow `class_logits` with `selection: nms`. The rule is in
  [Validation rules](../post/selection-nms.md#validation-rules): `selection: nms` forbids
  `class_logits_output`.
- The detection outputs are the complete candidate set. The decode steps are in
  [Selection behaviour](../post/detection-decode.md#selection-behaviour).

## Reason

- **A graph that keeps its NMS loses candidates.** mmdeploy's RTMDet rewrite always adds
  `multiclass_nms` with caps. The capped graph drops candidates that PyTorch keeps. On
  `rtmdet-person-medium` it lost 0.0114 AP (0.6255 to 0.6141) and 0.027 AR (0.7247 to 0.6977)
  (OpenMMLab-Exporter 0008). A graph that ends before NMS keeps every candidate. The host can then
  reproduce the upstream decode.
- **Host NMS costs almost nothing for one class.** OpenMMLab-Exporter 0016 measured it
  (see "Evidence"). On CUDA, the host decode adds about 1 ms per image for `rtmdet-person-medium`.
  For this model, on CUDA and on CPU, the host decode and an in-graph NMS are within about 1 ms of
  each other. The person decode at the `0.05` threshold costs about 0.6 ms per image
  (OpenMMLab-Exporter 0017).
- **The upstream values are the baseline.** The `nms` block copies the person configs' `test_cfg`.
  With these values the spec decode reproduces the PyTorch AP (see "Evidence").
- **`pre_nms_top_k` has no measured benefit.** Dropping the mmdet `nms_pre` cap changed AP by 0 on
  `rtmdet-person-medium` and by +0.0001 on `rtmdet-tiny`. The cap only reduces host NMS time at
  near-zero score thresholds. A flat candidate list also cannot express a per-level cap unless a
  `level_strides` field exists. The spec does not add that field for an option that changes no AP.
- **`class_logits` with `selection: nms` has no user.** The person family has one class. The 80-class
  RTMDet family is no longer exported (OpenMMLab-Exporter 0017). The spec can add the option later as
  a non-breaking change, when a multi-class NMS-free family appears.

## Evidence

The measurements come from OpenMMLab-Exporter 0009 and OpenMMLab-Exporter 0016 (both dated
2026-10-20). The upstream values come from the exporter's person configs.

**Parity with PyTorch** (full COCO val2017, fp32, CUDA; OpenMMLab-Exporter 0009):

| Model | Decode | AP | AR | ΔAP vs PyTorch |
|---|---|---|---|---|
| person-medium | spec decode | 0.6255 | 0.7248 | 0.0000 |
| tiny | mmdet decode (per-level `nms_pre`, clamp before NMS) | 0.4113 | 0.6054 | +0.0001 |
| tiny | spec decode, every (row, class) pair | 0.4114 | 0.6056 | +0.0002 |
| tiny | spec decode, best class per row only | 0.4061 | 0.5743 | −0.0051 |

- Dropping `nms_pre` changed AP by +0.0001 on tiny and by 0 on person.
- Clamping after NMS (spec) instead of before NMS (mmdet) is invisible in AP.
- "Every (row, class) pair" is the `class_logits` with `selection: nms` decode. Only the 80-class
  family needs it. "Best class per row only" fails the 0.005 fp32 limit.

**Cost of dropping the `nms_pre` cap** (OpenMMLab-Exporter 0009): at the `0.001` validation threshold, the decode
takes about 400 ms per image with CPU torchvision NMS and no cap. It takes about 70 ms with the cap.
OpenMMLab-Exporter 0017 says the 80-class models caused this cost. At runtime thresholds the decode
takes about 1.5 ms.

**Host decode against in-graph NMS** (OpenMMLab-Exporter 0016; median of 200 COCO images, batch 1,
RTX 3070, ms per image; the in-graph variant had ONNX `NonMaxSuppression` appended at a fixed score
threshold):

| Model | Provider | Threshold | Dense inference only | Dense + host decode | In-graph NMS |
|---|---|---|---|---|---|
| person-medium (1 class) | CUDA | 0.3 | 14.0 | 15.0 | 14.4 |
| person-medium | CUDA | 0.7 | 14.0 | 14.9 | 14.3 |
| person-medium | CPU | 0.3 | 65.2 | 68.2 | 67.8 |
| person-medium | CPU | 0.7 | 68.6 | 68.1 | 68.6 |
| tiny (80 classes) | CUDA | 0.3 | 6.0 | 7.3 | 15.1 |
| tiny | CUDA | 0.7 | 6.0 | 7.2 | 16.9 |

For one class (person), or on CPU, the in-graph NMS and the host decode are within about 1 ms. For 80
classes on CUDA, the in-graph NMS adds 9 to 11 ms per image.

**Upstream values.** `mmdeploy-convert/model_cfgs/rtmdet_m_640-8xb32_coco-person.py` in
OpenMMLab-Exporter sets `test_cfg` to `nms_pre=1000`, `min_bbox_size=0`, `score_thr=0.05`,
`nms=dict(type='nms', iou_threshold=0.6)` and `max_per_img=100`. The `NMS` constant in
OpenMMLab-Exporter `rtmdet_person/identity.py` holds the three sidecar values.

**Spec.** The reference example
[RTMDet person](../examples/README.md#rtmdet-person-openmmlab-exporter-nms-free-outputs-host-nms)
shows the sidecar. The rows "`class_logits` with `selection: nms`" and "`nms.pre_nms_top_k`" in
[Considered and deliberately not added](../changelog.md#considered-and-deliberately-not-added)
record the two options that the spec does not add.

**Code.** `DetectionDecodeSpec` in `skellytracker/core/sidecar/model.py` has no `selection` field and
no `nms` field. `OutputSemantic` in the same file has no `boxes` or `scores`. `InputSpec` has no
`color_format`. `_StrictModel` sets `extra="forbid"`. `SidecarModel._check_schema_version_pattern`
rejects `schema_version: vNEXT` (`parse_skellytracker_version` in
`skellytracker/core/sidecar/versioning.py`). A `vNEXT` RTMDet person sidecar does not load in
skellytracker yet.

## Alternatives rejected

- **Keep mmdeploy's NMS in the graph and declare `selection: none`.** The capped graph loses 0.0114 AP
  on `rtmdet-person-medium`. OpenMMLab-Exporter 0016 shows that a runtime-threshold NMS in the graph
  costs nothing measurable for one class. So time is not the reason. The reason is the AP that the
  capped mmdeploy graph loses.
- **Add `nms.pre_nms_top_k`.** It changes no AP. It needs a `level_strides` field to express the
  per-level cap. The spec does not add either.
- **Declare the best class of each row (`scores` plus a class index) for a multi-class family.** It
  lost 0.0051 AP and about 0.031 AR on tiny (0.5743 against 0.6056).
- **Add `class_logits` with `selection: nms` now.** No family in scope needs it. The spec adds it as a
  non-breaking change when a multi-class NMS-free family appears.

## Not repeated

- Do not put `pre_nms_top_k` into a sidecar. The spec does not define it. A host cannot know what to do
  with it.
- Do not use the best class of each row for a multi-class NMS-free family. Use every (row, class)
  pair. This needs the `class_logits` with `selection: nms` addition first.
- Do not compare the in-graph NMS and the host decode at the `0.001` threshold. The in-graph variant
  caps 300 boxes for each class (`max_output_boxes_per_class`). The host decode has no such cap. The
  counts differ on every image (OpenMMLab-Exporter 0016).
- Do not declare `class_logits_output` with `selection: nms`. The validation rules forbid it.
- An RTMDet person-only family and an 80-class RTMDet family are two families. Their NMS contracts and
  class counts differ. See [0010](0010-family-invariant.md).

_Edited 2026-10-26 (this PR): link repair._

_Edited 2026-10-28 (this PR): link repair._

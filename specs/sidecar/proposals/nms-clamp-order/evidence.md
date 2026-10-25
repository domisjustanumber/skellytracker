# 0041 evidence — RTMDet: host `selection: nms` with the mmdet candidate filters, clamp and visit order

Evidence for [0041](../../../../notes/decisions/0041-rtmdet-host-nms-filters.md). This file is not an
entry. It has no status line and no index row.

## Evidence of 0011

This section is the section "Evidence" of [0011](../../../../notes/decisions/0011-rtmdet-host-nms.md),
moved unchanged. Only its two relative links changed, for the new folder.

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
[RTMDet person](../../examples/README.md#rtmdet-person-openmmlab-exporter-nms-free-outputs-host-nms)
shows the sidecar. The rows "`class_logits` with `selection: nms`" and "`nms.pre_nms_top_k`" in
[Considered and deliberately not added](../../changelog.md#considered-and-deliberately-not-added)
record the two options that the spec does not add.

**Code.** `DetectionDecodeSpec` in `skellytracker/core/sidecar/model.py` has no `selection` field and
no `nms` field. `OutputSemantic` in the same file has no `boxes` or `scores`. `InputSpec` has no
`color_format`. `_StrictModel` sets `extra="forbid"`. `SidecarModel._check_schema_version_pattern`
rejects `schema_version: vNEXT` (`parse_skellytracker_version` in
`skellytracker/core/sidecar/versioning.py`). A `vNEXT` RTMDet person sidecar does not load in
skellytracker yet.

A skellytracker session checked the code facts of the paragraph "Code" again on 2026-10-25, on
branch `dom/23-spec-proposals-folder`. They are still true.

## Evidence of the proposal

The measurements of the proposal `nms-clamp-order` are in [part 1](proposal.md#1-gap) and
[part 5](proposal.md#5-parity-evidence) of `proposal.md`. Part 5 is `to run`. The scripts of these
measurements are not committed, so the numbers are not evidence yet.

# 0008 — `vNEXT` scope, and the features considered and not added

**Status:** accepted, 2026-10-22 (backfilled from #81; the removal of the RF-DETR example was decided by the user on 2026-10-22); superseded by [YNX0](YNX0-vnext-scope-list.md), 2026-10-28 (user; PR: pending).

## Decision

The `vNEXT` revision of [the sidecar spec](../../sidecar-spec.md) must let a sidecar describe
every model that these exporters produce:

- OpenMMLab-Exporter: RTMDet (person-only family), RTMW and RTMO body7.
- Ultralytics-Exporter: YOLO26 detection and YOLO26 pose.
- Roboflow-Exporter: RF-DETR.

Qualcomm-Exporter is out of scope until that library is complete.

`vNEXT` adds only the features that these models need. The spec lists the other features in
[Considered and deliberately not added](../../changelog.md#considered-and-deliberately-not-added).
This entry groups them:

- Resize: `resize.antialias`, `resize.size_divisor`, `crop_policy.border_mode` and rotated crops.
- Scores and classes: `score_activation: softmax`, `class_id_map_before_selection`, and
  `class_logits` with `selection: nms`.
- NMS: `nms.pre_nms_top_k` (see [0011](0011-rtmdet-host-nms.md)) and `nms.min_bbox_size`.
- Graph and pose descriptions: `graph_candidate_limit` and `pose.decode.instance_count`.
- Soft-NMS, per-class IoU, masks, multi-input models and quantized outputs.

A later revision can add each feature as a non-breaking schema bump when a model needs it.

The spec has no RF-DETR reference example. The example returns when Roboflow-Exporter is
overhauled and writes `vNEXT` sidecars. The rules that RF-DETR motivated stay in the spec. These
rules include:

- the `stretch` resize;
- the `boxes`, `scores` and `class_logits` output semantics, with `class_axis`;
- `selection: top_k`, with `class_id_map`.

`vNEXT` is a placeholder name for this revision. [0014](../../../../decisions/entries/0014-spec-lifecycle.md) holds the rule for
when a release version replaces it.

## Reason

- No model in scope needs most of the listed features. Each row of the
  [spec table](../../changelog.md#considered-and-deliberately-not-added) gives its own reason.
- Some rows give another reason:
  - For `score_activation: softmax`, the behaviour over gap and background slots is unresolved.
  - For `nms.pre_nms_top_k`, a flat candidate list cannot express the per-level `nms_pre` cap of mmdet.
  - `graph_candidate_limit` is informational only. The host cannot act on it.
  - `pose.decode.instance_count` is not needed. The count comes from the detection row axis.
- The RF-DETR example had drifted from the output of Roboflow-Exporter, and that exporter will be
  overhauled. An example that does not match a real export misleads exporter authors. The rules stay
  because RF-DETR still needs them.

## Evidence

The spec records one measurement behind the `class_logits` with `selection: nms` row. The test model
is the NMS-free RTMDet-tiny. Each (row, class) pair above the score threshold becomes a candidate.
Per-class NMS follows. This method reproduced the PyTorch AP (0.4114 against 0.4112). A method that
keeps only the best class for each row lost 0.0051 AP and 0.031 AR.

No family in scope needs this feature, because the COCO-80 RTMDet family was dropped. A later
revision can add the feature if a multi-class NMS-free family appears.

## Alternatives rejected

- Adopt the whole Roboflow-Exporter draft that
  [the exporter coverage plan](../../../../notes/sidecar-exporter-coverage.md) starts from.
  The draft has fields that no exported model uses. The coverage plan trims them.

## Not repeated

- Do not read the list of features as a ban. A feature leaves the list when a model needs it.
- Do not remove an RF-DETR rule because the spec has no RF-DETR example.

_Edited 2026-10-26 (this PR): link repair._

_Edited 2026-10-28 (this PR): link repair._

_Edited 2026-10-29 (this PR): link repair._

# 0048 — `vNEXT` scope and the features not added; MediaPipe-Exporter joins, and rotated crops leave the list

**Status:** proposed, 2026-10-25 (MediaPipe-Exporter proposal).

## Decision

This entry supersedes [0008](0008-vnext-scope.md) in full. It restates each rule of 0008 that stays.
It holds only scope rules. [0020](0020-roi-transform-and-source.md) holds the rules of
`rotated_roi_crop`.

The `vNEXT` revision of [the sidecar spec](../../specs/model-sidecar/sidecar-spec.md) must let a sidecar describe
every model that these exporters produce:

- OpenMMLab-Exporter: RTMDet (person-only family), RTMW and RTMO body7.
- Ultralytics-Exporter: YOLO26 detection and YOLO26 pose.
- Roboflow-Exporter: RF-DETR.
- MediaPipe-Exporter: the hand landmark model and the hand ROI refinement model. Changed: 0008
  does not list this exporter.

Qualcomm-Exporter is out of scope until that library is complete.

`vNEXT` adds only the features that these models need. The spec lists the other features in
[Considered and deliberately not added](../../specs/model-sidecar/changelog.md#considered-and-deliberately-not-added).
This entry groups them:

- Resize: `resize.antialias` and `resize.size_divisor`.
- NMS: `nms.pre_nms_top_k` (see [0011](0011-rtmdet-host-nms.md)) and `nms.min_bbox_size`.
- Scores and classes: `score_activation: softmax`, `class_id_map_before_selection`, and
  `class_logits` with `selection: nms`.
- Graph and pose descriptions: `graph_candidate_limit` and `pose.decode.instance_count`.
- Soft-NMS, per-class IoU, masks, multi-input models and quantized outputs.

Changed: `crop_policy.border_mode` and rotated crops leave the Resize group of 0008. `vNEXT` adds
them in `rotated_roi_crop` ([0020](0020-roi-transform-and-source.md)).

A later revision can add each listed feature as a non-breaking schema bump when a model needs it.

The spec has no RF-DETR reference example. The example returns when Roboflow-Exporter is
overhauled and writes `vNEXT` sidecars. The rules that RF-DETR motivated stay in the spec. These
rules include:

- the `stretch` resize;
- the `boxes`, `scores` and `class_logits` output semantics, with `class_axis`;
- `selection: top_k`, with `class_id_map`.

`vNEXT` is a placeholder name for this revision. [0014](0014-spec-lifecycle.md) holds the rule for
when a release version replaces it.

## Reason

- No model in scope needs most of the listed features. Each row of the
  [spec table](../../specs/model-sidecar/changelog.md#considered-and-deliberately-not-added) gives its own reason.
- Some rows give another reason:
  - For `score_activation: softmax`, the behaviour over gap and background slots is unresolved.
  - For `nms.pre_nms_top_k`, a flat candidate list cannot express the per-level `nms_pre` cap of mmdet.
  - `graph_candidate_limit` is informational only. The host cannot act on it.
  - `pose.decode.instance_count` is not needed. The count comes from the detection row axis.
- Changed: `vNEXT` must also describe the MediaPipe Holistic hand branch (user). Its crop is a
  rotated ROI with a replicated border. No resize method of the spec describes it.
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
  [the exporter coverage plan](../sidecar-exporter-coverage.md) starts from.
  The draft has fields that no exported model uses. The coverage plan trims them.

## Not repeated

- Do not read the list of features as a ban. A feature leaves the list when a model needs it.
- Do not remove an RF-DETR rule because the spec has no RF-DETR example.
- Do not put a feature rule into a scope entry. A later scope change supersedes only the scope entry
  in force, and it restates only scope rules.

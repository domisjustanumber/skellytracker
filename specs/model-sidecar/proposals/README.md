# Spec change proposals

This folder holds the spec change proposals that skellytracker has recorded (decision
[faac](../../../decisions/faac-proposal-records.md)). Each proposal has one folder,
`<slug>/`, with the file `proposal.md`. That file holds the header and all eight parts of the
proposal, a source note and the heading "Before acceptance". The folder also holds the other files of
the exporter folder: `reference/<section_module>.py` (part 3), `vectors/<section ID>.yaml` (part 4),
and the optional `evidence.md` and `example/` (a candidate example). An older record has part 3 and
part 4 in `proposal.md` (ADR-[pykx](../../../decisions/pykx-submission-folders.md)).

The files are informative. A proposal is not normative until a content PR lands its text in the
section files. The decision entry of each proposal records its status. The skill
[`propose-sidecar-change`](../../../.claude/skills/propose-sidecar-change/SKILL.md) records a
proposal. The skill [`change-sidecar-spec`](../../../.claude/skills/change-sidecar-spec/SKILL.md)
lands it.

`state` is `recorded`, `accepted`, `landed` or `rejected`. This table is the list of the
proposals. A proposal with `state: recorded` waits for the user. The heading "Before acceptance"
of its `proposal.md` lists the work that must be done before the user can accept it.

| Proposal | Section | Exporter | Decision | State |
|---|---|---|---|---|
| [affine-crop-arithmetic](affine-crop-arithmetic/proposal.md) | `pre.resize.affine_person_crop` | OpenMMLab-Exporter | [0037](../decisions/0037-affine-crop-arithmetic.md) | recorded |
| [heatmap-decode-refinement](heatmap-decode-refinement/proposal.md) | `post.pose.decode.heatmap` | OpenMMLab-Exporter | [0038](../decisions/0038-heatmap-decode-refinement.md) | recorded |
| [keypoint-visibility](keypoint-visibility/proposal.md) | `post.pose.visibility` | OpenMMLab-Exporter | [0039](../decisions/0039-keypoint-visibility.md) | recorded |
| [landmark-depth-divisor](landmark-depth-divisor/proposal.md) | `post.pose.decode.coordinate` | MediaPipe-Exporter | [0022](../decisions/0022-landmark-depth-divisor.md) | recorded |
| [landmark-extra-outputs](landmark-extra-outputs/proposal.md) | `post.pose.extra_outputs` | MediaPipe-Exporter | [0021](../decisions/0021-landmark-extra-outputs.md) | recorded |
| [model-id-suffix](model-id-suffix/proposal.md) | `common.identity` | OpenMMLab-Exporter | [0025](../decisions/0025-model-id-suffix.md) | recorded |
| [nms-clamp-order](nms-clamp-order/proposal.md) | `post.det.selection.nms` | OpenMMLab-Exporter | [0040](../decisions/0040-nms-clamp-order.md) | recorded |
| [normalize-arithmetic](normalize-arithmetic/proposal.md) | `pre.normalize` | OpenMMLab-Exporter | [0043](../decisions/0043-normalize-arithmetic.md) | recorded |
| [omitted-upstream-output](omitted-upstream-output/proposal.md) | `none` | OpenMMLab-Exporter | [0044](../decisions/0044-omitted-upstream-output.md) | recorded |
| [pose-decode-flip-test](pose-decode-flip-test/proposal.md) | `post.pose.flip_test` | OpenMMLab-Exporter | [0045](../decisions/0045-pose-decode-flip-test.md) | recorded |
| [roi-refiner-role](roi-refiner-role/proposal.md) | `post.roi_refiner` | MediaPipe-Exporter | [0047](../decisions/0047-roi-refiner-role.md) | recorded |
| [roi-transform-and-source](roi-transform-and-source/proposal.md) | `pre.resize.rotated_roi_crop` | MediaPipe-Exporter | [0020](../decisions/0020-roi-transform-and-source.md) | recorded |
| [simcc-score-rule](simcc-score-rule/proposal.md) | `post.pose.decode.simcc` | OpenMMLab-Exporter | [0024](../decisions/0024-simcc-score-rule.md) | recorded |
| [size-codes](size-codes/proposal.md) | `common.sizes` | OpenMMLab-Exporter | [0046](../decisions/0046-size-codes.md) | recorded |

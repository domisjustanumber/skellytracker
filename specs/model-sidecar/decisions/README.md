# Decision log of the sidecar spec

This log records the decisions that apply only to the model sidecar spec
([`specs/model-sidecar/sidecar-spec.md`](../sidecar-spec.md)). It is the log of the sidecar spec
module. The [Rules](../../../decisions/README.md#rules) of the root log apply to this log. To write an
entry, use the root [template.md](../../../decisions/template.md). Read this file and
[open-work.md](open-work.md) before you change the spec, a sidecar or an example. Read an entry of
[historical.md](historical.md) only to find the reason for a decision.

## Index

### Active

These entries are `accepted` or `evidence`.

| # | Decision | Status |
|---|----------|--------|
| [0008](0008-vnext-scope.md) | `vNEXT` scope, and the features considered and not added | accepted |
| [0011](0011-rtmdet-host-nms.md) | RTMDet: NMS-free graph with host `selection: nms`; no `pre_nms_top_k` | accepted |

### Proposed

These entries are spec change proposals and gap records that wait for a decision of the user. Section
is the spec section of the change, or `none` when the change has no one section. Find the pending
proposals of a section here and in the [proposal index](../proposals/README.md).

| # | Decision | Section | Status |
|---|----------|---------|--------|
| [0017](0017-dual-role-sidecar-folder.md) | Folder of a sidecar with both roles | `format.file_layout` | proposed |
| [0018](0018-one-declaration-per-tensor.md) | One declaration for each output tensor, at every version | `common.outputs` | proposed |
| [0019](0019-output-shape-batch-axis.md) | Batch axis of `outputs[].shape` | `common.outputs` | proposed |
| [0020](0020-roi-transform-and-source.md) | ROI transform, and a crop that does not come from a detector box; spec change `roi-transform-and-source` | `pre.resize.rotated_roi_crop` | proposed |
| [0021](0021-landmark-extra-outputs.md) | Pose outputs beside the landmarks: presence, handedness and world landmarks; spec change `landmark-extra-outputs` | `post.pose.extra_outputs` | proposed |
| [0022](0022-landmark-depth-divisor.md) | Depth divisor of MediaPipe landmarks; spec change `landmark-depth-divisor` | `post.pose.decode.coordinate` | proposed |
| [0023](0023-letterbox-floor-and-scale-inverse.md) | `floor` rounding and a scale inverse for `letterbox` | `pre.resize.letterbox` | proposed |
| [0024](0024-simcc-score-rule.md) | SimCC keypoint score rule; spec change `simcc-score-rule` | `post.pose.decode.simcc` | proposed |
| [0025](0025-model-id-suffix.md) | Suffix after the part in `model_id`; spec change `model-id-suffix` | `common.identity` | proposed |
| [0037](0037-affine-crop-arithmetic.md) | Spec change: affine-crop-arithmetic (`pre.resize.affine_person_crop`) | `pre.resize.affine_person_crop` | proposed |
| [0038](0038-heatmap-decode-refinement.md) | Spec change: heatmap-decode-refinement (`post.pose.decode.heatmap`) | `post.pose.decode.heatmap` | proposed |
| [0039](0039-keypoint-visibility.md) | Spec change: keypoint-visibility (`post.pose.visibility`) | `post.pose.visibility` | proposed |
| [0040](0040-nms-clamp-order.md) | Spec change: nms-clamp-order (`post.det.selection.nms`) | `post.det.selection.nms` | proposed |
| [0041](0041-rtmdet-host-nms-filters.md) | RTMDet: host `selection: nms` with the mmdet candidate filters, clamp and visit order | `post.det.selection.nms` | proposed |
| [0042](0042-vnext-scope-nms-filters.md) | `vNEXT` scope and the features not added; `nms.pre_nms_top_k` and `nms.min_bbox_size` leave the list | none | proposed |
| [0043](0043-normalize-arithmetic.md) | Spec change: normalize-arithmetic (`pre.normalize`) | `pre.normalize` | proposed |
| [0044](0044-omitted-upstream-output.md) | Spec change: omitted-upstream-output (no section; workflow verdict `omitted`) | none | proposed |
| [0045](0045-pose-decode-flip-test.md) | Spec change: pose-decode-flip-test (`post.pose.flip_test`) | `post.pose.flip_test` | proposed |
| [0046](0046-size-codes.md) | Spec change: size-codes (`common.sizes`) | `common.sizes` | proposed |
| [0047](0047-roi-refiner-role.md) | Spec change: roi-refiner-role (`post.roi_refiner`) | `post.roi_refiner` | proposed |
| [0048](0048-vnext-scope-mediapipe-rotated-crops.md) | `vNEXT` scope and the features not added; MediaPipe-Exporter joins, and rotated crops leave the list | none | proposed |

The entries that are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done` are in [historical.md](historical.md).

## Open work

The open work of the sidecar spec and the spec defects are in [open-work.md](open-work.md).

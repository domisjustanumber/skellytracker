# 0020 — ROI transform, and a crop that does not come from a detector box

**Status:** proposed, 2026-10-23 (from the exporter evidence of MediaPipe-Exporter and
Qualcomm-Exporter; plan facts and historical code only).

## Decision

**Proposed, not decided.** This entry is a gap record (see [Rules](README.md#rules)). It does not
have the eight parts of a proposal.

Let a top-down pose model take its crop from an ROI that does not come
from an object detector, and let its sidecar declare the transform of that ROI. The proposal has
three parts. First, [`V-post.pose.schema-2`](../../specs/sidecar/post/pose-schema.md#validation-rules)
and [`V-pre.resize.affine_person_crop-2`](../../specs/sidecar/pre/resize-affine-person-crop.md#validation-rules)
allow a top-down model whose ROI comes from the output of another model, for example from body-pose
keypoints. Second, `crop_policy` gets the fields of the MediaPipe `RectTransformation`: `shift_x` and
`shift_y` along the axes of the ROI, `square_long` and `scale`. Third, the spec defines the ROI
(centre, size and rotation) that the crop receives. The rule that computes the ROI from the keypoints
stays outside the sidecar. This entry records the gap and the direction only. The exporter overhaul
must write the full proposal of [0014](0014-spec-lifecycle.md#new-model-workflow), with an ONNX file
and a committed parity script. This proposal depends on rotated crops (the changelog row
`crop_policy.border_mode, rotated crops`) and on the ROI refiner gap. The decision must also say
whether the change goes into `vNEXT` or into a later revision, because the `vNEXT` scope of
[0008](0008-vnext-scope.md) does not include MediaPipe-Exporter.

## Reason

- The MediaPipe hand landmark model is top-down: it sees one hand in a crop. But the crop does not
  come from a detector box. The pipeline makes a rotated rect from the wrist, index and pinky
  keypoints of a body pose. Then it transforms the rect.
- The spec ties `top_down_*` to `requires_object_detector: true` (`V-post.pose.schema-2`). It ties
  `requires_object_detector: true` to `affine_person_crop` (`V-pre.resize.affine_person_crop-2`). The
  `crop_policy` of that method has only `expand_ratio` and `maintain_aspect_ratio`, on an axis-aligned
  box.
- `expand_ratio` cannot express a `shift_y` of `-0.1` along the ROI axis, `square_long`, or a scale
  that changes with the stage (2.7 for the loose ROI, 1.0 for the re-crop, 2.0 for tracking).
- The table
  [Considered and deliberately not added](../../specs/sidecar/changelog.md#considered-and-deliberately-not-added)
  covers rotation and the border mode. It does not cover the shift, `square_long` or an ROI source
  that is not a detector.
- Without these fields, an exporter puts the ROI rule into a pipeline manifest outside the sidecar.
  Then a host cannot check the crop against the sidecar, and parity depends on code outside the spec.

## Evidence

No commit and no parity result exist for this evidence. MediaPipe-Exporter has no git repo, and the
Qualcomm-Exporter hand plan is not tracked.

- The untracked hand plan of MediaPipe-Exporter (plan facts): `RectTransformation`
  with `shift_x: 0.0`, `shift_y: -0.1`, `square_long: true` and `scale` 2.7 (loose ROI), 1.0
  (re-crop) and 2.0 (tracking). The shift is along the rect's own axis. The plan puts these values
  into a pipeline manifest, not into the sidecar.
- The same plan: the landmark model is `top_down_single_person`, with no `requires_object_detector`
  value. The ROI comes from the BlazePose-33 keypoints 15/17/19 and 16/18/20 (wrist, pinky and
  index). COCO-17 has no pinky and no index keypoints.
- The untracked hand plan of Qualcomm-Exporter (plan facts): `top_down_single_person`
  with `requires_object_detector: true`, and `input.resize.method: affine_rotated_crop`, because "the
  crop is rotated and comes from the pose".
- Qualcomm-Exporter at commit `c7b9132`: `README.md` (lines 129-132) says that its pipeline manifests
  carry the ROI scale, offset and rotation keypoints "because `affine_person_crop` cannot express
  MediaPipe's rotation-aware ROI". `qai_sidecar.py` (lines 268-278) writes `affine_person_crop` with
  `expand_ratio: 1.0` as an approximation.

## Alternatives rejected

- **Keep the ROI rule in a pipeline manifest outside the sidecar** (the approach of both plans). The
  host then needs a second contract to make the model input, and the spec cannot check it.
- **`affine_person_crop` with `expand_ratio`** (the historical Qualcomm-Exporter approximation). It
  has no shift, no `square_long` and no rotation. It is a near-miss.

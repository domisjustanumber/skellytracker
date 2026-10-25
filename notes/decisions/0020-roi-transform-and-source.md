# 0020 — ROI transform, and a crop that does not come from a detector box

**Status:** proposed, 2026-10-23 (from the exporter evidence of MediaPipe-Exporter and
Qualcomm-Exporter; plan facts and historical code only); completed 2026-10-25 (MediaPipe-Exporter
proposal).

## Decision

**Proposed, not decided.** This entry records the spec change proposal `roi-transform-and-source`.
The eight parts are in
[`specs/sidecar/proposals/roi-transform-and-source/proposal.md`](../../specs/sidecar/proposals/roi-transform-and-source/proposal.md).

- **Section:** a new section `pre.resize.rotated_roi_crop` ("Rotated ROI crop", file
  `specs/sidecar/pre/resize-rotated-roi-crop.md`, kind `preprocessor`). The change also edits
  `common.input`, `common.sizes_and_artifacts`, `pre.resize.interpolation`, `pre.normalize`,
  `pre.resize.affine_person_crop`, `post.pose.schema`, `post.unprojection`, `format.versioning`, the
  templates, the exporter guide and the changelog.
- **Change:** The new value `input.resize.method: rotated_roi_crop` crops a rotated ROI
  `(cx, cy, w, h, rotation)` that the host gives, with no box from an object detector.
  `crop_policy` has an optional `transform` (`shift_x`, `shift_y`, `square_long`, `scale`), a
  required `maintain_aspect_ratio` and a required `border_mode` (`constant` with `pad_value`, or
  `replicate`). The corners of the ROI map onto the model input with `linear` interpolation only,
  and the inverse is exact (rules `V-pre.resize.rotated_roi_crop-1` to `-5`). The change also
  removes `pose.requires_object_detector` at `vNEXT` (changed `V-post.pose.schema-1`,
  `V-post.pose.schema-2` and `V-pre.resize.affine_person_crop-2`). It makes the keys of an
  `affine_person_crop` `crop_policy` a closed set (changed `V-common.input-4`).
- **Version:** `vNEXT`. A sidecar with `schema_version < vNEXT` keeps its legacy meaning. The section
  states no arithmetic precision. The vectors give the tolerances.
- **Models:** the MediaPipe Holistic hand branch of MediaPipe-Exporter: the hand landmark model
  (`mediapipe-hand21`) and the input crop of the hand ROI refinement model (`mediapipe-hand-roi`).
- **On acceptance:** this entry supersedes no entry. The scope entry
  [0048](0048-vnext-scope-mediapipe-rotated-crops.md) supersedes [0008](0008-vnext-scope.md). If
  entry B of `nms-clamp-order` ([0042](0042-vnext-scope-nms-filters.md)) lands first, 0048
  supersedes 0042 with the variant text in `proposal.md`.
- **Related:** `roi-refiner-role` ([0047](0047-roi-refiner-role.md)), `landmark-extra-outputs`
  ([0021](0021-landmark-extra-outputs.md)) and `landmark-depth-divisor`
  ([0022](0022-landmark-depth-divisor.md)) depend on this proposal. This proposal and 0048 must
  land first. `model-id-suffix` ([0025](0025-model-id-suffix.md)) gives the `model_id` of the hand
  landmark model. `affine-crop-arithmetic` ([0037](0037-affine-crop-arithmetic.md)) edits the same
  text of `pre.resize.affine_person_crop` and `V-common.input-4`. Either one can land first.
  `nms-clamp-order` ([0041](0041-rtmdet-host-nms-filters.md), [0042](0042-vnext-scope-nms-filters.md))
  meets this proposal only in the scope entries.

## Reason

No resize method of the spec describes the crop of the MediaPipe hand landmark model. The crop comes
from a rotated ROI that the host gives, not from a detector box. The pipeline moves, squares and
scales the ROI, and it fills the border with the edge pixels. The nearest method,
`affine_person_crop` with `expand_ratio: 2.7`, moves the input corners up to 41.3 px away from the
rotated crop (38.2 % of the ROI size). The historical `expand_ratio: 1.0` gives up to 56.8 px. These
numbers come from an uncommitted scratch script of the exporter session, so they are not evidence.
Parity is `to run`. The parity script of MediaPipe-Exporter does not exist yet, and it cannot get a
commit while MediaPipe-Exporter has no git repo.

### Gap record (2026-10-23)

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

## Open work

See [Open work](README.md#open-work).

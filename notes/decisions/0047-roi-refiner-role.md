# 0047 — Spec change: roi-refiner-role

**Status:** proposed, 2026-10-25 (MediaPipe-Exporter proposal).

## Decision

**Proposed, not decided.** This entry records the spec change proposal `roi-refiner-role`. The eight
parts are in
[`specs/model-sidecar/proposals/roi-refiner-role/proposal.md`](../../specs/model-sidecar/proposals/roi-refiner-role/proposal.md).

- **Section:** a new section `post.roi_refiner` ("ROI refiner", file
  `specs/model-sidecar/post/roi-refiner.md`, kind `postprocessor`, selector `role=roi_refiner`). The change
  also edits `common.identity`, `common.outputs`, `common.input`, `common.sizes_and_artifacts`,
  `format.file_layout`, `format.versioning`, `post.pose.schema`, `post.unprojection`,
  `pre.resize.rotated_roi_crop`, the exporter guide and the intake template.
- **Change:** A new role `roi_refiner` is always the only role of its sidecar
  (`V-post.roi_refiner-1`). Its one output has the new semantic `roi_points`. The block `roi_decode`
  (`point_count`, `coordinate_scale`, `rect: alignment_points`, `rotation`, `transform`) makes one
  rotated ROI for each batch item. It maps the points with the inverse of the `rotated_roi_crop` input
  crop, makes the rect, applies the ROI transform and drops an ROI that is not valid. The block
  `roi_source` (`method: parent_keypoints`) makes the input ROI from named keypoints of a parent pose
  model: ordered lists of accepted names, weighted derived points and a strict gate on a named
  per-point value, with the runtime defaults `score_gate.value_default` and
  `score_gate.score_threshold_default`. A sidecar goes in `detectors/roi_refiners/{family}/{part}/`,
  with the `model_id` `{family}-{part}-roi[-{variant}]` (`V-post.roi_refiner-9`). New rules
  `V-post.roi_refiner-1` to `-16`. Changed rules: `V-common.identity-2`, `V-common.outputs-4` and
  `V-pre.resize.rotated_roi_crop-1`.
- **Version:** `vNEXT`. A sidecar with `schema_version < vNEXT` cannot declare `roi_refiner`,
  `roi_points`, `roi_decode` or `roi_source`. The five package sidecars do not change.
- **Models:** the MediaPipe hand ROI refinement model `mediapipe-hand-roi`
  (`hand_roi_refinement.tflite` of Holistic), a MediaPipe-Exporter model. The parent is BlazePose or
  a COCO-WholeBody 133 model such as RTMW.
- **On acceptance:** this entry supersedes no entry. The accepted entry
  [0014](0014-spec-lifecycle.md) says that an ROI refiner "is a `gap`". That text becomes stale. The
  user decides how to handle it. The proposal `omitted-upstream-output`
  ([0044](0044-omitted-upstream-output.md)) supersedes 0014 in full and restates that text.
- **Related:** `roi-transform-and-source` ([0020](0020-roi-transform-and-source.md)) gives
  `rotated_roi_crop`, and its scope entry [0048](0048-vnext-scope-mediapipe-rotated-crops.md) adds
  MediaPipe-Exporter to the `vNEXT` scope. `keypoint-visibility` ([0039](0039-keypoint-visibility.md))
  defines the per-point value `visibility` of the default gate. `model-id-suffix`
  ([0025](0025-model-id-suffix.md)) is related, not a dependency. The order is: 0020 with 0048, then
  0039, then this entry. Other proposals edit the same spec text. The proposal file lists them.

## Reason

- `V-common.identity-2` allows only `object_detector` and `pose_estimator`. The closed `semantic`
  set has no value for ROI points. The storage layout has no branch for the role.
- A pose estimator with two points describes the tensor. But a host then reads the points as
  keypoints, and the rect rule, the rotation target and the transform have no field. The exporter
  guide forbids that mapping.
- No section makes the input ROI of a model from the keypoints of a parent model. Gap record 0020
  keeps that rule outside the sidecar. User decision T24 (a plan fact of the untracked pose-models
  plan of OpenMMLab-Exporter) puts it in the refiner sidecar. Without it, a host cannot run the
  refiner from the sidecars alone.
- A decode with the host ROI `R` in place of the crop ROI `Rc` moves the centre of the refined ROI by
  9.31 px (18.1 % of its size). This number comes from an uncommitted script. It is not evidence.

## Evidence

- Parity: `to run`. The shared parity script `notes/decisions/scripts/hand_chain_parity.py` of
  MediaPipe-Exporter does not exist yet. MediaPipe-Exporter has no git repo, so its scripts and its
  decisions have no commit.
- The 125 vectors of part 4 pass against the part 3 code (an exporter run on 2026-10-25). They are
  `unverified`: no host implementation exists.
- The primary source of the `roi_decode` rule is `docs/mediapipe-whole-body.md` of
  MediaPipe-Exporter, by a user designation (MediaPipe-Exporter 0021 (no git repo)). The `roi_source`
  rule cites MediaPipe source at commit `e9794ef55e2509c09aa8b6ba1764b797db8eb200`. The gate value
  `score` of an RTMW parent comes from OpenMMLab-Exporter 0041.

## Open work

See [Open work](README.md#open-work).

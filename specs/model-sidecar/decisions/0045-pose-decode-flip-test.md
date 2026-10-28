# 0045 — Spec change: pose-decode-flip-test

**Status:** proposed, 2026-10-25 (OpenMMLab-Exporter proposal).

## Decision

**Proposed, not decided.** This entry records the spec change proposal `pose-decode-flip-test`. The
eight parts are in
[`specs/model-sidecar/proposals/pose-decode-flip-test/proposal.md`](../proposals/pose-decode-flip-test/proposal.md).

- **Section:** a new section `post.pose.flip_test` ("Flip test", file
  `specs/model-sidecar/post/pose-flip-test.md`, kind `postprocessor`). The change also edits
  `post.pose.schema`, `post.pose.decode.simcc`, `post.pose.decode.heatmap`, the "Implementer guidance"
  of `pre.resize.affine_person_crop`, `format.versioning`, the section map and the changelog.
- **Change:** The optional field `pose.decode.flip_test` tells the host to run the model on the crop
  and on its horizontal mirror image. `pose.decode.flip_test.flip_pairs` (required in `flip_test`)
  gives the pairs of `pose.tracked_points` names that change places in a mirror image.
  `pose.decode.flip_test.shift_heatmap` (bool, default `false`, only for `heatmap`) moves the
  flipped-back heatmap one column to the right. The host maps the mirror outputs back, computes
  `(y + y_back) * 0.5` in float32 and then decodes. Rules `V-post.pose.flip_test-1` to `-3` limit the
  field to a 2D top-down `simcc` or `heatmap` decode, and check `flip_pairs` and `shift_heatmap`.
- **Version:** `vNEXT`. The field is not available when `schema_version < vNEXT`. It goes into the
  "Not available." row of the "Legacy behaviour" table of `format.versioning`. A legacy sidecar runs
  one forward pass. Its meaning does not change.
- **Models:** the OpenMMLab-Exporter families `rtmw-wholebody133`, `rtmpose-halpe26`,
  `dwpose-wholebody133-ubody`, `vitposepp-wholebody133` and `vitpose-coco25`. The five package
  sidecars do not change.
- **On acceptance:** this entry supersedes no entry.
- **Related:** `heatmap-decode-refinement` ([0038](0038-heatmap-decode-refinement.md)) depends on
  this proposal. This proposal must land first. Part 7 uses the family IDs of `model-id-suffix`
  ([0025](0025-model-id-suffix.md)). These proposals edit the same spec text, and the second content
  PR rebases on the first: `simcc-score-rule` ([0024](0024-simcc-score-rule.md)),
  `keypoint-visibility` ([0039](0039-keypoint-visibility.md)), `affine-crop-arithmetic`
  ([0037](0037-affine-crop-arithmetic.md)), `roi-transform-and-source`
  ([0020](0020-roi-transform-and-source.md)), `roi-refiner-role` ([0047](0047-roi-refiner-role.md)),
  `landmark-extra-outputs` ([0021](0021-landmark-extra-outputs.md)) and `landmark-depth-divisor`
  ([0022](0022-landmark-depth-divisor.md)).

## Reason

- The upstream test configs of these models set the flip test: mmpose v1.3.2 for the SimCC models
  (`flip_test=True`), and ViTAE-Transformer/ViTPose `c050ed2` for ViTPose++ (`flip_test=True`,
  `shift_heatmap=True`). Part 1 of the proposal gives the file and line of each source. These code
  lines are primary evidence.
- The ONNX graph is one forward pass. `pose.decode` has no field for the second pass, for the pairs
  of a mirror image or for the heatmap shift. A host that follows the spec runs one pass. Its
  keypoints differ from the upstream test pipeline.
- The proposal measures the effect on COCO val2017 (body OKS AP, GT boxes): +0.0096 AP for DWPose-m,
  +0.0078 for RTMPose-m Halpe26 and +0.0059 for ViTPose++-S. The fp16 gate of OpenMMLab-Exporter D5
  is 0.01. These numbers come from scratch scripts that are not committed. They are not evidence.
- On the 25-point ViTPose model with `shift_heatmap=False`, the flip test lowered AP by 0.0092. With
  `shift_heatmap=True`, it added 0.0128. These numbers are also not evidence. Thus the author must
  take `shift_heatmap` and `flip_pairs` from a measured upstream pipeline, not from the default.

## Evidence

- Parity (part 5): `to run`. The gates are set before the run: per point, the export error plus
  0.5 crop px (SimCC) or plus 4 crop px (heatmap), and an aggregate AP difference of 0.005 or less.
  The script `notes/decisions/scripts/pose_flip_test_parity.py` of OpenMMLab-Exporter is planned. It
  is not written, and it has no commit.
- Reference (part 3): NumPy code with six functions. Source commit: none (no host code).
- Vectors (part 4): 8 cases, `unverified`. A runner that is not committed passed all 8 cases against
  the reference code. The case form does not agree with `tools/make_vectors.py` and
  `tools/tests/test_vectors.py`.

## Open work

See [Open work](README.md#open-work).

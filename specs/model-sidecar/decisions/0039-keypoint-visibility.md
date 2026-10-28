# 0039 — Spec change: keypoint-visibility

**Status:** proposed, 2026-10-25 (OpenMMLab-Exporter proposal).

## Decision

**Proposed, not decided.** This entry records the spec change proposal `keypoint-visibility`. The
eight parts are in
[`specs/model-sidecar/proposals/keypoint-visibility/proposal.md`](../../specs/model-sidecar/proposals/keypoint-visibility/proposal.md).

- **Section:** a new section `post.pose.visibility` ("Keypoint visibility", file
  `specs/model-sidecar/post/pose-visibility.md`, kind `postprocessor`). The change also edits
  `post.pose.schema`, `post.pose.decode.coordinate`, the "Authoring guidance" of
  `post.pose.decode.simcc`, `format.versioning`, the section map, the changelog, the mapping hints
  and the intake template.
- **Change:** The optional field `pose.decode.visibility: {source, channel, activation}` gives a
  visibility value for each keypoint of the single-person `coordinate` decode. `source` has one value,
  `keypoints_channel`. `channel` names the channel of the `keypoints` output. `activation` is `none`
  or `sigmoid` (`1 / (1 + exp(-v))`), with no default. The single-person `keypoints` output becomes
  `(N, K, C)`, and the heading "Per-point values" names the values `score` and `visibility`. Rules
  `V-post.pose.visibility-1` to `-4` check the block, the method, the channel bound and the version.
- **Version:** `vNEXT`. Rule `V-post.pose.visibility-4` refuses the field when
  `schema_version < vNEXT`, also in a size entry. The field goes into the "Not available." row of the
  "Legacy behaviour" table of `format.versioning`. The `(N, K, 2)` and `(N, K, 3)` outputs keep their
  meaning. The five package sidecars do not change.
- **Models:** the BlazePose pose landmark model of MediaPipe (lite, full and heavy), the parent of the
  score gate of the hand ROI refiner. It is a MediaPipe-Exporter model, and it is deferred. No RTMW
  size declares the field (option E, OpenMMLab-Exporter 0041).
- **On acceptance:** this entry supersedes no entry. Decision 0008 does not put MediaPipe-Exporter in
  the `vNEXT` scope. The scope entry [0048](0048-vnext-scope-mediapipe-rotated-crops.md) does not add
  BlazePose. Acceptance thus needs a scope decision first.
- **Related:** `roi-refiner-role` ([0047](0047-roi-refiner-role.md)) reads the visibility of the
  BlazePose wrist. This proposal must land first. These proposals edit the same spec text, and the
  second content PR rebases on the first: `pose-decode-flip-test`
  ([0045](0045-pose-decode-flip-test.md)), `simcc-score-rule` ([0024](0024-simcc-score-rule.md)),
  `heatmap-decode-refinement` ([0038](0038-heatmap-decode-refinement.md)),
  `landmark-extra-outputs` ([0021](0021-landmark-extra-outputs.md)), `landmark-depth-divisor`
  ([0022](0022-landmark-depth-divisor.md)), `roi-transform-and-source`
  ([0020](0020-roi-transform-and-source.md)), `nms-clamp-order` ([0040](0040-nms-clamp-order.md))
  and `omitted-upstream-output` ([0044](0044-omitted-upstream-output.md)). The mapping hint of
  `omitted-upstream-output` appends text to the hint of this proposal, so this proposal lands first.

## Reason

- The BlazePose pose landmark model gives five values for each of its 39 points: `x, y, z`, a
  visibility logit and a presence logit. MediaPipe applies a sigmoid to the visibility on the host
  (`TensorsToLandmarksCalculator`, MediaPipe `e9794ef`). The Holistic hand branch gates on the wrist
  visibility (`> 0.1`). These code lines are primary evidence.
- `pose.decode` has no field for a second value for each keypoint. The single-person coordinate
  decode gives `(N, K, 2)` or `(N, K, 3)` and no score. No field names the visibility channel or its
  activation. Thus the parent check of the proposed `V-post.roi_refiner-15` refuses each BlazePose
  parent that the gate reads with `visibility`.
- mmpose decodes `keypoints_visible` for two RTMW 384x288 configs. OpenMMLab-Exporter 0041 measured
  it on COCO-WholeBody v1.0 val (6352 persons): the visibility ranks valid hands worse than the raw
  wrist score at every RTMW size (AUC difference −0.046 to −0.094). Thus the section has no SimCC
  source.
- The BlazePose graph output `[1, 195]` with no `Sigmoid` comes from a scratch script that is not
  committed. It is not evidence.

## Evidence

- Parity (part 5): `to run`. MediaPipe-Exporter has no git repo. The gates are set before the run:
  the visibility within `0.25 * E3 + 1e-6` of the upstream value, and the same wrist gate decision as
  Holistic outside `0.25 * E3` of the threshold. `E3` is the export error of channel 3. The script is
  not written, and it has no commit.
- RTMW: OpenMMLab-Exporter 0041
  ([permalink](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/f3aeb473d3396ee79c4394646a34ed9ef419ecf1/notes/decisions/0041-rtmw-wrist-gate.md))
  is gate evidence for option E. It is not a parity run of this section.
- Reference (part 3): NumPy code with five functions. Source commit: none (no host code).
- Vectors (part 4): 31 cases, `unverified`. A runner that is not committed passed all 31 cases
  against the reference code. The case form does not agree with `tools/make_vectors.py` and
  `tools/tests/test_vectors.py`.

## Open work

See [Open work](README.md#open-work).

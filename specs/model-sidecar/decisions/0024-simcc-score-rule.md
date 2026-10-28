# 0024 — SimCC keypoint score rule

**Status:** proposed, 2026-10-23 (from the exporter evidence of OpenMMLab-Exporter, with the mmdeploy
and rtmlib sources); completed 2026-10-25 (OpenMMLab-Exporter proposal).

## Decision

**Proposed, not decided.** This entry records the spec change proposal `simcc-score-rule`. The
eight parts are in
[`specs/model-sidecar/proposals/simcc-score-rule/proposal.md`](../proposals/simcc-score-rule/proposal.md).
The proposal completes this gap record.

- **Section:** the changed section `post.pose.decode.simcc` ("SimCC decode", file
  `specs/model-sidecar/post/pose-decode-simcc.md`). The change also edits the description of
  `pose.decode.depth_range`, the "Shape key" of `post.pose.schema`, the "Version-aware compatibility"
  list of `format.versioning` and the changelog. It adds no field and no validation rule.
- **Change:** In "Behaviour", the host decodes the raw `simcc_x` and `simcc_y` outputs with no
  softmax. The location of each axis is the argmax bin, and a tie selects the lowest bin. The
  keypoint score is `min(max(simcc_x[k]), max(simcc_y[k]))`, and a score `<= 0` sets the bin -1 on
  each axis. Bin `b` maps to `b * input_width / X_bins` and `b * input_height / Y_bins`, with no
  half-bin offset. When `is_3d: true`, a `simcc_z` bin maps to
  `depth_range[0] + b * (depth_range[1] - depth_range[0]) / Z_bins`, and the `simcc_z` peak does not
  change the score.
- **Version:** `vNEXT`. A new "Legacy behaviour" heading keeps the score of the skellytracker host
  for `schema_version < vNEXT`: the mean of the two softmax peaks. The four SimCC package sidecars
  (`v2024.09.1019`) keep their meaning. The proposal applies the location, the tie order, the scale
  and the depth formula to the two versions.
- **Models:** the OpenMMLab-Exporter families `rtmw-wholebody133`, `dwpose-wholebody133-ubody` and
  `rtmpose-halpe26`. The `simcc_z` rule is for RTMW3D. No RTMW3D family is in scope.
- **On acceptance:** this entry supersedes no entry.
- **Related:** this proposal depends on no proposal, and no proposal must land first. These
  proposals edit the same spec text, and the second content PR rebases on the first:
  `pose-decode-flip-test` ([0045](0045-pose-decode-flip-test.md)) adds a sentence to the same
  "Behaviour" bullet; `keypoint-visibility` ([0039](0039-keypoint-visibility.md)) and
  `omitted-upstream-output` ([0044](0044-omitted-upstream-output.md)) change the `decode_visibility`
  guidance; `heatmap-decode-refinement` ([0038](0038-heatmap-decode-refinement.md)) and
  `keypoint-visibility` edit the "Shape key" list. The reasons of `heatmap-decode-refinement` use
  the -1 rule of this proposal.

## Reason

The section says only "The location of each keypoint is the argmax bin. Its score is the max value."
SimCC has two peaks for each keypoint, and the text does not say how they combine. It has no rule for
a score `<= 0`, no tie order and no exact depth formula. mmpose v1.3.2 takes the smaller of the two
raw peaks, with no softmax (`get_simcc_maximum`, primary). The AP numbers of the proposal come from
uncommitted scratch scripts, so they are not evidence. Parity is `to run`: the parity scripts are not
written yet.

### Gap record (2026-10-23)

Replace "Its score is the max value" in
[SimCC decode](../post/pose-decode-simcc.md#behaviour) with the mmpose rule. The
score of keypoint `k` is `min(max(simcc_x[k]), max(simcc_y[k]))`, on the raw output values, with no
softmax. The rule is **(vNEXT)**. A legacy sidecar keeps the existing host behaviour, with a row in
the legacy table. The full proposal must also give the rule for `simcc_z` when `is_3d: true`. It must
bring the vectors and the reference implementation of
[0014](../../../decisions/0014-spec-lifecycle.md#new-model-workflow).

- The spec says "Its score is the max value", but SimCC has two 1-D distributions for each keypoint.
  The text does not say how the two peaks combine, or if a softmax comes first.
- Three implementations use three rules (see "Evidence"). Their scores have different scales: a
  softmax peak is in `[0, 1]`, and a raw peak is not. Thus a keypoint threshold does not transfer from
  one host to another.
- RTMPose and RTMW come from mmpose. A host that uses the min rule matched mmpose within 0.0033 in
  score (an OpenMMLab-Exporter plan fact; see "Evidence").

## Evidence

- mmdeploy `mmdeploy/codebase/mmpose/codecs/post_processing.py` at commit `bc75c9d6` (v1.3.1),
  `get_simcc_maximum`: line 30 takes the `min` of the two raw maxima.
- rtmlib `rtmlib/tools/pose_estimation/post_processings.py` at commit `9f51b34`,
  `get_simcc_maximum`: line 41 takes `0.5 * (max_val_x + max_val_y)` of the raw maxima. The min rule
  is commented out (line 39).
- skellytracker `skellytracker/core/detectors/processing/simcc_decode.py`, `get_simcc_maximum`
  (lines 28-63): a softmax on each axis (lines 53-54), then `0.5 * (max_px + max_py)` (line 63). The
  front matter of [SimCC decode](../post/pose-decode-simcc.md) records this.
- The untracked hand-model plan of OpenMMLab-Exporter (plan facts): mmpose
  `get_simcc_maximum` uses `min(max(simcc_x), max(simcc_y))` on the raw outputs. A host with this rule
  matched mmpose with a maximum score difference of 0.0033. The plan says that the rule also applies
  to RTMW.

## Alternatives rejected

- **A field that selects the rule** (the OpenMMLab-Exporter plan also names this option). The SimCC
  models in scope come from mmpose, so one rule is sufficient. A field adds a host branch that no model
  needs.
- **The mean of the softmax peaks (skellytracker today), or the mean of the raw peaks (rtmlib).**
  Neither is the upstream rule of the SimCC models in scope.

## Open work

See [Open work](README.md#open-work).

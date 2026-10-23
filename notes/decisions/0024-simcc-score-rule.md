# 0024 — SimCC keypoint score rule

**Status:** proposed, 2026-10-23 (from the exporter evidence of OpenMMLab-Exporter, with the mmdeploy
and rtmlib sources).

## Decision

**Proposed, not decided.** This entry is a gap record (see [Rules](README.md#rules)). It does not
have the eight parts of a proposal.

Replace "Its score is the max value" in
[SimCC decode](../../specs/sidecar/post/pose-decode-simcc.md#behaviour) with the mmpose rule. The
score of keypoint `k` is `min(max(simcc_x[k]), max(simcc_y[k]))`, on the raw output values, with no
softmax. The rule is **(vNEXT)**. A legacy sidecar keeps the existing host behaviour, with a row in
the legacy table. The full proposal must also give the rule for `simcc_z` when `is_3d: true`. It must
bring the vectors and the reference implementation of
[0014](0014-spec-lifecycle.md#new-model-workflow).

## Reason

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
  front matter of [SimCC decode](../../specs/sidecar/post/pose-decode-simcc.md) records this.
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

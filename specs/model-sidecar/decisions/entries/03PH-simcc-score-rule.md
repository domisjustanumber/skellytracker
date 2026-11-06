# 03PH — Spec change: simcc-score-rule

**Status:** proposed, 2026-11-06 (proposal-simcc-score-rule@openmmlab-exporter@v2).

## Decision

**Proposed, not decided.** The proposal is
[`proposal.md`](../../proposals/simcc-score-rule/proposal.md).

- Section: [`post.pose.decode.simcc`](../../post/pose-decode-simcc.md).
- Change: the Behaviour gives the 2D SimCC decode exactly. The location of each axis is the argmax
  bin of the raw values, and a tie gives the lowest bin. The score is `min(peak_x, peak_y)` of the
  raw peaks, with no softmax. A score `<= 0` sets the bin `-1` on both axes before the scale, and
  the score stays. The pixel is `bin * input_extent / bins`, with no half-bin offset. A reference
  module and 12 vector cases are new.
- Target spec version: `2.0.0`.
- Models: RTMW (OpenMMLab-Exporter `rtmw-wholebody133`).
- Supersedes on acceptance: none.
- Related: `model-rtmw-wholebody133@openmmlab-exporter` (intake row K8 needs this proposal);
  [ADR-9HBB](../../../../decisions/entries/9HBB-simcc-decode-is-2d-only.md) (the SimCC decode is 2D
  only); [ADR-3S5G](3S5G-affine-crop-matrix.md) (it uses the same parity run).

## Reason

The current Behaviour says only "Its score is the max value". SimCC has two peaks for each keypoint.
The text does not say how they combine, whether a softmax comes first, which bin a tie selects, or
what a score `<= 0` gives. mmpose v1.3.2 takes the smaller raw peak with no softmax, and the
skellytracker host takes the mean of the two softmax peaks. Thus a keypoint threshold does not
transfer from one host to the other. The [spec defects](../open-work.md#spec-defects) list this
item.

## Evidence

Parity: `pass` in 6 of 6 runs (OpenMMLab-Exporter ADR-VB67): RTMW m-256 and x-384, RTMPose Halpe26
m-256 and m-384, DWPose m and l-384, each on 6352 COCO val2017 persons and 18 synthetic boxes. The
gates were written before the run. The decode-only check found 0 differences. The script is
`decisions/scripts/simcc_score_rule_bundle_rerun.py` at OpenMMLab-Exporter
`438138208691a522f54320961f058e61b60d54a3`. The run used the v1 module. The v2 module differs only
in its docstring. The vectors are `unverified`: no host implements the rule. v2 removes the
compiled file of v1 and rebases on the 2D-only text.

## Open work

See [open-work.md](../open-work.md).

## Before acceptance

- The user must confirm or refuse each plan decision of part 1:
  - row K8 (keypoint score) of the RTMW intake needs this proposal;
  - the proposal covers only the 2D decode. This agrees with
    [ADR-9HBB](../../../../decisions/entries/9HBB-simcc-decode-is-2d-only.md).
- The tie branch occurred only in the vectors. The score `<= 0` branch ran only on RTMPose
  Halpe26 (4 keypoints), not on RTMW.
- The text gives no rule for a NaN raw value.
- Part 2.3 cites an exporter script and OpenMMLab-Exporter ADR-0053 as plain text. The
  [Sources](../../model-addition-workflow/rules.md#sources) rule asks for full-SHA permalinks.
- Part 6 does not name the `is_3d` branch of `simcc_pose_decode` or
  `skellytracker/tests/sidecar/golden_parity.py`, which imports `_SIMCC_SPLIT_RATIO`. The plan
  item of the landing must cover them.
- The new score has no fixed range. The `confidence_threshold` default 0.004 of the package
  detectors fits only the softmax score.
- Recording this entry makes OpenMMLab-Exporter the owner of `post.pose.decode.simcc` while the
  entry is `proposed`
  ([Section owner](../../model-addition-workflow/hand-over.md#section-owner)).

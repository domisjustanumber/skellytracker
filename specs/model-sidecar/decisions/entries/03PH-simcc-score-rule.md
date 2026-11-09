# 03PH — Spec change: simcc-score-rule

**Status:** absorbed into [`post/pose-decode-simcc.md#behaviour`](../../post/pose-decode-simcc.md#behaviour), 2026-11-09 (user; PR: pending).

## Decision

The user accepted the proposal on 2026-11-09. The record is
[`proposal.md`](../../proposals/simcc-score-rule/proposal.md)
(proposal-simcc-score-rule@openmmlab-exporter@v3).

- Section: [`post.pose.decode.simcc`](../../post/pose-decode-simcc.md).
- Change: the Behaviour gives the 2D SimCC decode exactly. The location of each axis is the argmax
  bin of the raw values, and a tie gives the lowest bin. The score is `min(peak_x, peak_y)` of the
  raw peaks, with no softmax. A score `<= 0` sets the bin `-1` on both axes before the scale, and
  the score stays. The pixel is `bin * input_extent / bins`, with no half-bin offset. In a row with
  a NaN raw value, the bin is the lowest index of a NaN and the peak is NaN. A comparison with a NaN is false:
  a NaN in `simcc_x` gives the score NaN, a NaN only in `simcc_y` gives the score `peak_x`, and a
  NaN score keeps its bins. This is the result of mmpose v1.3.2 `get_simcc_maximum`. A reference
  module and 16 vector cases are new.
- Target spec version: `2.0.0`.
- Models: RTMW (OpenMMLab-Exporter `rtmw-wholebody133`).
- Supersedes: none.
- Related: `model-rtmw-wholebody133@openmmlab-exporter` (intake row K8 needs this proposal);
  [ADR-9HBB](../../../../decisions/entries/9HBB-simcc-decode-is-2d-only.md) (the SimCC decode is 2D
  only); [ADR-3S5G](3S5G-affine-crop-matrix.md) (it uses the same parity run).
- The user confirmed two plan decisions on 2026-11-06. Row K8 (keypoint score) of the RTMW intake
  needs this proposal. The proposal covers only the 2D decode. This agrees with
  [ADR-9HBB](../../../../decisions/entries/9HBB-simcc-decode-is-2d-only.md).

## Reason

The current Behaviour says only "Its score is the max value". SimCC has two peaks for each keypoint.
The text does not say how they combine, whether a softmax comes first, which bin a tie selects, or
what a score `<= 0` gives. mmpose v1.3.2 takes the smaller raw peak with no softmax, and the
skellytracker host takes the mean of the two softmax peaks. Thus a keypoint threshold does not
transfer from one host to the other. The [spec defects](../open-work.md#spec-defects) listed this
item. The content commit of this entry removes it.

## Evidence

Parity: `pass` in 6 of 6 runs (OpenMMLab-Exporter ADR-VB67): RTMW m-256 and x-384, RTMPose Halpe26
m-256 and m-384, DWPose m and l-384, each on 6352 COCO val2017 persons and 18 synthetic boxes. The
gates were written before the run. The decode-only check found 0 differences. The script is
`decisions/scripts/simcc_score_rule_bundle_rerun.py` at OpenMMLab-Exporter
`438138208691a522f54320961f058e61b60d54a3`. The run used the v1 module. The v2 and v3 modules
differ only in docstrings: part 5 says that `ast.dump` of the three modules, with no docstrings,
gives the same text. The v2 to v3 diff changes no code line. The parity run did not test the NaN branch. The 4 NaN vector cases
cover it. An uncommitted random check also ran it (secondary). The vectors are `unverified`: no host implements the rule. v2 removes the compiled file
of v1 and rebases on the 2D-only text. v3 rebases on spec commit `8fed6f3`.

## Open work

See [open-work.md](../open-work.md).

## Notes at acceptance

- The tie branch and the NaN branch did not occur on real outputs. Only the vectors and an
  uncommitted random check of v3 cover them. That check and its mmpose copy are not committed
  (secondary). The score `<= 0` branch ran only on RTMPose Halpe26 (4 keypoints), not on RTMW.
  (changed 2026-11-09)
- [x] The text gives no rule for a NaN raw value. v3 adds the rule to Behaviour and Implementer
  guidance, with an mmpose v1.3.2 full-SHA permalink and 4 vector cases. The reference code does
  not change.
- [x] Part 2.3 cites an exporter script and OpenMMLab-Exporter ADR-0053 as plain text. The
  [Sources](../../model-addition-workflow/rules.md#sources) rule asks for full-SHA permalinks.
  v3 gives full-SHA permalinks for both.
- [x] Part 6 does not name the `is_3d` branch of `simcc_pose_decode` or
  `skellytracker/tests/sidecar/golden_parity.py`, which imports `_SIMCC_SPLIT_RATIO`. v3 part 6
  names both. The plan item of the landing must still cover them.
- The new score has no fixed range. The `confidence_threshold` default 0.004 of the package
  detectors fits only the softmax score.
- Recording this entry makes OpenMMLab-Exporter the owner of `post.pose.decode.simcc` while the
  entry is `proposed`
  ([Section owner](../../model-addition-workflow/hand-over.md#section-owner)).
- Part 1 and `evidence.md` cite `numpy/_core/fromnumeric.py:3380` for `amax`. At NumPy
  `c60f172b3330f76d6592362137f34c4a3030a001`, that line is in the docstring of `numpy.min`. The
  correct anchor is `fromnumeric.py:3236` (`numpy.max`). `numpy.amax` is an alias of `numpy.max`.
  The claim that `amax` propagates a NaN is true. The landed text does not use this link, so no
  action is necessary.
  (new 2026-11-09)
- [x] The vector note says that the mmpose copy ran "on each case" with the same result. mmpose does
  not refuse the case `shapes-of-x-and-y-differ`: it reshapes `simcc_y`. The content commit must
  change the note to "each numeric case" (editorial). (new 2026-11-09) The content commit makes
  this fix.
- [x] The content commit must rewrite the relative links of the proposed text from the record path to
  the section and changelog paths (editorial, part 2). (new 2026-11-09) The content commit makes
  this fix.

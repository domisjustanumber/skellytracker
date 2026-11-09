# 3S5G — Spec change: affine-crop-matrix

**Status:** absorbed into [`pre/resize-affine-person-crop.md#behaviour`](../../pre/resize-affine-person-crop.md#behaviour), 2026-11-09 (user; PR: pending).

## Decision

The user accepted the proposal on 2026-11-09. The record is
[`proposal.md`](../../proposals/affine-crop-matrix/proposal.md)
(proposal-affine-crop-matrix@openmmlab-exporter@v2).

- Section: [`pre.resize.affine_person_crop`](../../pre/resize-affine-person-crop.md).
- Change: the Behaviour gives the warp matrix `M` in float32 steps, as mmpose v1.3.2 computes it.
  The box, the expand ratio, the centre, the crop size and the aspect ratio `a = f32(T_w / T_h)`
  are float32. `cv2.getAffineTransform` solves `M` from three float32 point pairs. With
  `maintain_aspect_ratio: true`, `M` uses the centre and the crop width only. The Inverse stays
  "the inverse of `M`". No field, selector or rule changes. Nine vector cases and a reference
  module are new. An import of that module replaces the Inverse fixture of
  `reference/post_unprojection.py`.
- Target spec version: `2.0.0`.
- Models: RTMW (OpenMMLab-Exporter `rtmw-wholebody133`).
- Supersedes: none.
- Related: `model-rtmw-wholebody133@openmmlab-exporter` (intake row T4b needs this proposal);
  `proposal-simcc-score-rule@openmmlab-exporter` (its parity run made the upstream dumps).
- The user confirmed three plan decisions on 2026-11-06. Intake row T4b (the arithmetic of the
  crop) is a `near-miss`. The proposal covers only the crop matrix `M`, not the normalization or
  the unprojection. Intake rows T10 (normalization) and D11 (unprojection) are `exact`, because
  they differ from mmpose only by the float32 rounding of a result.

## Reason

The current Behaviour gives the crop in exact math. mmpose rounds each step to float32 and solves
`M` from points that use only the centre and the width. On 6370 persons per run, the exact-math
`M` differs from the mmpose `M` by more than 1e-6 for 6226 (256x192) and 6245 (384x288) persons,
with a maximum of 2.4e-3 and 3.6e-3. This changes 5992 and 6047 crops by 1 grey level. The user
ruled intake row T4b a `near-miss`.

## Evidence

Parity: `pass` (OpenMMLab-Exporter ADR-6A8S). The script is
`decisions/scripts/affine_crop_matrix_check.py` at OpenMMLab-Exporter
`0d07c982fb6915fee6fa0b8ccac35873c77c4db2`, run with Python 3.14.2, NumPy 2.5.4 and OpenCV 5.0.0
on the mmpose v1.3.2 dumps of 6 runs. The gates were written before the measurement. The `M`, the
centre and the scale of the reference file are bit-equal to upstream for 38220 of 38220 persons.
The two exact-math controls fail their gates, as expected. Version 2 changes only docstring lines
of the reference file. Its code is the same as the code of the run, so the result applies with no
new run. The vectors are `unverified`: no host implements the proposed text.

## Open work

See [open-work.md](../open-work.md).

## Notes at acceptance

- [x] The docstring of the reference file says "No skellytracker decision entry covers it" and
  "Parity result: to run". Both notes are stale. v2 fixes both notes, as the user asked.
- [x] After `land`, the file-level `unverified` text of the vector file says that the cases come from
  the section text only. The landed text changed: only some cases list their implementations in
  `verified_against`. It stays true for the nine new cases. Part 2.1 of v2 says this.
- No parity run checks `a = f32(T_w / T_h)` for a ratio that is not exact: each run uses 0.75. The
  branch `maintain_aspect_ratio: false` has no upstream run. Only vectors cover these two points.
- The end-to-end keypoint comparison comes from the OpenMMLab-Exporter ADR-VB67 run with an
  earlier reference file. The link to this file is the bit-equal `M` of the gate G1.
- Part 2.1 of v2 does not edit the stale Implementer guidance bullet "No exporter implements the
  crop or its inverse yet". Part 7 says that the OpenMMLab-Exporter host implements the crop. The
  landing must delete or correct the bullet. (changed 2026-11-09)
- The landing also changes `tools/vector_formulas/pre_resize_affine_person_crop.py`.
- The helper `case_policy` of the reference file only maps the case params. Case code stays outside
  a reference module ([Code for the cases](../../model-addition-workflow/reference-implementations.md#code-for-the-cases)).
- The exporter host `affine_crop_geometry` implements the current exact-math text. v2 gives the
  result: the 7 new forward cases fail at `atol` 1e-6 (maximum 2.8e-3), and the 2 Inverse cases
  pass. The current cases keep this host in `verified_against`. (changed 2026-11-09)
- [x] The model bundle `model-rtmw-wholebody133@openmmlab-exporter` has a fixture of the current
  Inverse in its `post_unprojection.py`. When this proposal lands, a fixture of the Inverse must
  become an import of `pre_resize_affine_person_crop`. Part 2.1 of v2 lists this for the landed
  `reference/post_unprojection.py`.
- The 2026-11-09 session found each exporter commit that v2 cites on the default branch of
  OpenMMLab-Exporter. It did not open the permalinks, and it did not run `fill` on the bundle
  code ([ADR-AD33](../../../../decisions/entries/AD33-bundles-are-untrusted-input.md)).
  (changed 2026-11-09)
- Part 3 of v2 says that two docstring notes changed. A third note, the spec commit of "Vector
  results", also changed. Each change is a docstring line. (new 2026-11-09)

The landing session must also do these items:

- The reference file says that `pre.resize.interpolation` "has no reference module".
  `reference/pre_resize_interpolation.py` has landed. Correct the note, and replace the fixtures
  `INTERPOLATION_FLAGS` and `COMPUTE_DTYPES` with an import
  ([When the other section has no module](../../model-addition-workflow/reference-implementations.md#when-the-other-section-has-no-module)).
  (new 2026-11-09)
- The "Driven by" cell of the changelog row of part 2.6 must give the user decision date and a
  link to this entry, as the recent rows do (editorial). (new 2026-11-09)

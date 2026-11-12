# G3FA — Spec change: affine-crop-rotated-roi

**Status:** proposed, 2026-11-12 (proposal-affine-crop-rotated-roi@openmmlab-exporter@v1); recorded again 2026-11-12 (proposal-affine-crop-rotated-roi@openmmlab-exporter@v2).

## Decision

**Proposed, not decided.** The record is
[`proposal.md`](../../proposals/affine-crop-rotated-roi/proposal.md).

- Section: [`pre.resize.affine_person_crop`](../../pre/resize-affine-person-crop.md), which
  becomes `pre.resize.affine_crop` in the file `pre/resize-affine-crop.md`.
- Change: the affine crop takes an ROI `(c_x, c_y, w, h, rotation)` in source-image pixels. A box
  `[x1, y1, x2, y2]` gives the ROI with rotation 0, in float32. `crop_policy` grows the ROI along
  its own axes. The second warp point, and for `maintain_aspect_ratio: false` the third, turn with
  the rotation in float64, with one rounding to float32, as mmpose `get_warp_matrix` does. For
  rotation 0, `M` does not change bit for bit. The method value `affine_person_crop` becomes
  `affine_crop`. The section ID, the rule IDs, the vector file and the reference module follow,
  with no alias. A non-finite ROI or an empty crop is refused. The box format and the coordinate
  space of the warped box become defined.
- Target spec version: `2.0.0`.
- Models: none of OpenMMLab-Exporter needs a rotation. The pipeline spec needs it for the
  MediaPipe Holistic hand chain. The rtmw example changes by a forced edit of the method value.
- Supersedes: none. Base: [ADR-3S5G](3S5G-affine-crop-matrix.md)
  (proposal-affine-crop-matrix@openmmlab-exporter, landed).
- Related: the item "Rotated crop" of the
  [pipeline open work](../../../pipeline/decisions/open-work.md).

## Reason

The section says that the rotation of the warp is always 0, and it takes only a box. The pipeline
`roi` value has a rotation ([ADR-7NY2](../../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md)
item 8). A crop with rotation 0 of an ROI with rotation `r` turns the content by `r`. For the ROI
`[200, 250, 200, 400, π/2]` at 256x192, one model-input point maps 265.2 px away from its place.
The name `affine_person_crop` is also wrong for a hand ROI or a face ROI.

## Evidence

Parity: `pass` (OpenMMLab-Exporter ADR-WRM2). The script is
`decisions/scripts/affine_crop_rotated_check.py` at OpenMMLab-Exporter
`8448da393b8ebdae86d0b5b5b8ee3019adbc3349`, with mmpose 1.3.2 and OpenCV 4.5.4 in the exporter
container. The gates were written before the run:

- G1: rotation 0 gives the landed `M` bit for bit for 25480 of 25480 ROIs.
- G2: a rotated ROI gives the mmpose `get_warp_matrix` `M` bit for bit for 203840 of 203840 ROIs.
- G3: 784 of 784 crops equal the mmpose `TopdownAffine` crop with `bbox_rotation`, max abs diff 0.
  `TopdownAffine` always keeps the aspect ratio, so G3 covers `maintain_aspect_ratio: true` only.
- G4 (control): no RTMW keypoint fails the RTMW parity rule on the rotated crops.

The vector file stays `unverified`: no host implements a rotated ROI. The run also found that mmpose
`add_pred_to_datasample` leaves out the rotation when it maps keypoints back. The upstream
reference of G4 uses the inverse of `M`.

## Open work

[open-work.md](../open-work.md)

## Before acceptance

User decision 2026-11-12: accept when proposal bundle version 2 closes the parity item: the script
`decisions/scripts/affine_crop_rotated_check.py` of OpenMMLab-Exporter is committed and run, and its
pass gates G1, G2 and G3 pass. The user confirmed the plan decisions (a) to (d) and the choice of
the proposal below. The user approved the copy of `reference/pre_resize_affine_crop.py` of version 1
(SHA-256 `d6a5dc294908963a1ee7486a50b59c656a851ef1d262f12e3ad77da7a30e686a`). A file of version 2
with another SHA-256 needs a new review and a new approval.

The plan decisions of part 1, which the user confirmed on 2026-11-12:

- (a) the affine crop takes each ROI `(c_x, c_y, w, h, rotation)` in source-image pixels; a box is
  an ROI with rotation 0;
- (b) the rotation convention of the pipeline spec: radians in `[-π, π)`, positive turns the ROI
  clockwise in the image, ROI x axis `(cos r, sin r)`, ROI y axis `(-sin r, cos r)`;
- (c) the section file becomes `pre/resize-affine-crop.md`;
- (d) the pipeline makes the ROI first, then the detector node applies `crop_policy` right before
  the warp, and the two growth factors multiply;
- the choice of the proposal: the method value, the section ID and the rule IDs follow the new file
  name (`affine_crop`, `pre.resize.affine_crop`).

Proposal bundle version 2 closes the parity item and meets the condition. Its reference file has the
approved SHA-256. Open after the landing:

- [ ] The border mode with edge pixels of the MediaPipe hand chain stays a spec defect. It is not
  in this proposal.

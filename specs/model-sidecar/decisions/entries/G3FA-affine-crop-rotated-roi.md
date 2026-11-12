# G3FA — Spec change: affine-crop-rotated-roi

**Status:** proposed, 2026-11-12 (proposal-affine-crop-rotated-roi@openmmlab-exporter@v1).

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

Parity: `to run`. The script `decisions/scripts/affine_crop_rotated_check.py` of
OpenMMLab-Exporter is planned. It has three pass gates: rotation 0 gives the landed `M`, a rotated
ROI gives the mmpose `M` bit for bit, and the crop equals the mmpose crop. An uncommitted check of
the contributor found both equalities on 20000 random boxes and ROIs (secondary). The vector file is
`unverified`: no host implements a rotated ROI.

## Open work

[open-work.md](../open-work.md)

## Before acceptance

- [ ] Plan decisions of part 1. The user must confirm or refuse each one:
  - (a) the affine crop takes each ROI `(c_x, c_y, w, h, rotation)` in source-image pixels; a box is
    an ROI with rotation 0;
  - (b) the rotation convention of the pipeline spec: radians in `[-π, π)`, positive turns the ROI
    clockwise in the image, ROI x axis `(cos r, sin r)`, ROI y axis `(-sin r, cos r)`;
  - (c) the section file becomes `pre/resize-affine-crop.md`;
  - (d) the pipeline makes the ROI first, then the detector node applies `crop_policy` right before
    the warp, and the two growth factors multiply.
- [ ] The choice of the proposal: the method value, the section ID and the rule IDs follow the new
  file name (`affine_crop`, `pre.resize.affine_crop`).
- [ ] Parity is `to run`: the script of part 5 is not written.
- [ ] The safety review and the copy approval of `reference/pre_resize_affine_crop.py` (procedure B
  step 6 of `change-sidecar-spec`).
- [ ] The border mode with edge pixels of the MediaPipe hand chain stays a spec defect. It is not
  in this proposal.

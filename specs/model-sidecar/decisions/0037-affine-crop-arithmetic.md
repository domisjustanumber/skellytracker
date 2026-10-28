# 0037 — Spec change: affine-crop-arithmetic

**Status:** proposed, 2026-10-25 (OpenMMLab-Exporter proposal).

## Decision

**Proposed, not decided.** This entry records the spec change proposal `affine-crop-arithmetic`. The
eight parts are in
[`specs/model-sidecar/proposals/affine-crop-arithmetic/proposal.md`](../proposals/affine-crop-arithmetic/proposal.md).

- **Section:** `pre.resize.affine_person_crop`, a changed section
  ([`pre/resize-affine-person-crop.md`](../pre/resize-affine-person-crop.md)).
- **Change:** A new normative heading "Arithmetic" gives the order of the operations and the float32
  value of each step: the centre, the crop size (the aspect fix divides: `h = w / a`, with
  `a = f32(T_w / T_h)`), three float32 warp points that use only `w`, and `M` from
  `cv2.getAffineTransform`. The Inverse becomes a closed form with `w` and `h` of the forward step,
  not the inverse of `M`. A new field `input.resize.crop_policy.arithmetic` selects `direct` (the
  default, mmpose 1.x) or `pixel_std_200` (the ViTAE / mmpose 0.x `_xywh2cs` form). The new rule
  `V-pre.resize.affine_person_crop-3` rejects the field below `vNEXT`, and it rejects
  `pixel_std_200` with `maintain_aspect_ratio: false`. A scalar `crop_policy.pad_value` fills every
  channel.
- **Version:** `vNEXT`. The heading "Arithmetic" and the Inverse apply to every `schema_version`.
  This needs an exception sentence after line 51 of `format/versioning.md`. Only
  `crop_policy.arithmetic` is `vNEXT`. A new heading "Legacy behaviour" gives the table.
- **Models:** `direct`: RTMPose, RTMW and DWPose (mmpose 1.x), and the four package sidecars.
  `pixel_std_200`: ViTAE ViTPose and ViTPose++.
- **On acceptance:** The proposal supersedes no entry. It closes two spec defects of the open work
  for this section: the scalar `pad_value` and the arithmetic precision of the geometry.
- **Related:** `normalize-arithmetic` ([0043](0043-normalize-arithmetic.md)) shares the exception
  sentence. Add the sentence one time. `roi-transform-and-source`
  ([0020](0020-roi-transform-and-source.md)) changes rule -2, the sentence on rotated crops and the
  key set of `V-common.input-4`. Either proposal can land first, and the second rebases.
  `pose-decode-flip-test` ([0045](0045-pose-decode-flip-test.md)) edits the implementer guidance.
  `heatmap-decode-refinement` ([0038](0038-heatmap-decode-refinement.md)) can share the parity script.
  The conversion of the vector form comes from `simcc-score-rule` ([0024](0024-simcc-score-rule.md)).
  Order: a non-spec tools PR for the vector form, then `normalize-arithmetic`, then this proposal.

## Reason

The pseudocode of the section is exact math with no dtype. Its aspect fix multiplies, and its `M`
uses `h`. mmpose 1.x divides, and it builds `M` from three float32 points that use only `w`. The
section gives the Inverse as the inverse of `M`. mmpose and ViTAE use a closed form with `h`. The
section has no form for the ViTAE `_xywh2cs` arithmetic. Thus rows T4b and D11 of five
OpenMMLab-Exporter intakes are `near-miss`.

A NumPy copy of the upstream lines gives other crop pixels than mmpose in 1911 of 2000 crops with the
current text, and in 0 of 2000 crops with the `direct` text. The ViTAE crop differs from the `direct`
crop in 1280 of 2000 crops. These numbers come from scripts that are not committed, so they are not
evidence.

## Evidence

Parity: `to run`. The parity script does not exist yet. The gates are set before the run: parity
step 4 needs a maximum difference of 0 on the uint8 crop and on the float32 tensor. The upstream
references are mmpose v1.3.2 and ViTAE `c050ed2`. No ONNX file of the four families exists. The 43
vectors of part 4 are `unverified`, because no host implementation exists. They pass against the
reference code of the proposal.

## Open work

See [Open work](README.md#open-work).

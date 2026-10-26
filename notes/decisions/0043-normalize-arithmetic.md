# 0043 — Spec change: normalize-arithmetic

**Status:** proposed, 2026-10-25 (OpenMMLab-Exporter proposal).

## Decision

**Proposed, not decided.** This entry records the spec change proposal `normalize-arithmetic`. The
eight parts are in
[`specs/model-sidecar/proposals/normalize-arithmetic/proposal.md`](../../specs/model-sidecar/proposals/normalize-arithmetic/proposal.md).

- **Section:** `pre.normalize` (`specs/model-sidecar/pre/normalization.md`), a changed section. The change
  also edits `format.versioning` (`format/versioning.md`) and `specs/model-sidecar/changelog.md`.
- **Change:** A new sub-heading "Arithmetic" under "Behaviour" gives the value of each mode. The
  reference value `r` is the formula in float64, rounded one time to float32. A host value `t` must
  meet `abs(t - r) <= 1e-6 * max(1, abs(r))`. The host must calculate in float32 or wider, not in
  float16. `none` is exact. The host casts the result to `input.dtype` at the end. The new rule
  `V-pre.normalize-3` requires `float32` or `float16` for each precision that resolves to a mode
  other than `none`. `V-pre.normalize-1` requires a `custom` `mean` or `std` to be a list of three
  finite numbers. The note on the default `imagenet_bgr` no longer names "the RTMPose convention".
- **Version:** `vNEXT`. The heading "Arithmetic" and `V-pre.normalize-3` apply to every
  `schema_version`. A new exception sentence after `format/versioning.md:51` states this.
- **Models:** `vitposepp-wholebody133` and `vitpose-coco25` (the ViTAE order: divide by 255, then
  the ImageNet statistics in float32). Also `rtmw-wholebody133`, `dwpose-wholebody133-ubody` and
  `rtmpose-halpe26` (the mmengine float32 form). Row T10 of the five intakes is `near-miss`. It
  becomes `exact` after acceptance.
- **On acceptance:** the proposal supersedes no entry. The scope breaks the rule of
  [0009](0009-imagenet-bgr-meaning.md) "The spec never applies `vNEXT` requirements to a legacy
  sidecar". The user decides if a new entry must supersede 0009 in full.
- **Related:** `affine-crop-arithmetic` ([0037](0037-affine-crop-arithmetic.md)) has the same
  exception sentence. Add it one time. `roi-transform-and-source`
  ([0020](0020-roi-transform-and-source.md)) edits the same "Behaviour" lines.
  `heatmap-decode-refinement` ([0038](0038-heatmap-decode-refinement.md)) and
  `pose-decode-flip-test` ([0045](0045-pose-decode-flip-test.md)) can use the same ViTAE parity
  worker. This proposal has no dependency. It can land first of the OpenMMLab-Exporter proposals.

## Reason

The section gives each mode as a real-number formula. It does not give the dtype of the arithmetic,
the order of the operations or the dtype of the result. Thus a host has no exact value for a pixel.
ViTAE divides by 255 and then applies the ImageNet statistics in float32. The OpenMMLab-Exporter
host and mmengine calculate `(float32(p) - float32(mean)) / float32(std)`. Over the 256 byte values,
the ViTAE form differs from `r` by up to 4.8e-7, and the host form by up to 2.4e-7. float16
arithmetic differs by up to 2.2e-3. These numbers come from uncommitted scratch scripts of the
exporter session, so they are not evidence. Parity step 4 of the exporter guide expects a difference
of 0. Thus row T10 of the intakes is a `near-miss`. The [open work](open-work.md) also lists "the
arithmetic precision of the geometry and of the pixel math" as a spec defect.

## Evidence

- Parity: `to run`. OpenMMLab-Exporter has no ONNX file of the two ViTPose families yet. The parity
  script `notes/decisions/scripts/vitpose_normalize_parity.py` and its ViTAE worker are planned and
  not written. Their exporter commit is unknown.
- Host code: OpenMMLab-Exporter `make_normalizer`
  ([`onnx_runtime/preprocess.py:120-151`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/f3aeb473d3396ee79c4394646a34ed9ef419ecf1/onnx_runtime/preprocess.py#L120-L151))
  gives the float32 host form. The exporter session reports that it meets 10 vector cases.
- Vectors: part 4 has 30 new cases. The exporter session reports that they pass against its
  reference file. A scratch run of the skellytracker session gave the same result. A regeneration
  of the 16 existing cases from the reference file changes the text of 6 cases by 1.0e-6 or less.
  These runs are not evidence.

## Open work

See [Open work](README.md#open-work).

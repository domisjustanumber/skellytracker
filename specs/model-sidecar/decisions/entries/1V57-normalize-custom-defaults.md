# 1V57 — Spec change: normalize-custom-defaults

**Status:** accepted, 2026-11-09 (user; PR: pending).

## Decision

The user accepted the proposal on 2026-11-09. The record is
[`proposal.md`](../../proposals/normalize-custom-defaults/proposal.md)
(proposal-normalize-custom-defaults@openmmlab-exporter@v1).

- Section: [`pre.normalize`](../../pre/normalization.md).
- Change:
  - An absent key of a `custom` object has the value `scale: 1`, `mean: [0, 0, 0]` or
    `std: [1, 1, 1]`. The `custom` row of the mode table and the comments of the custom-mode YAML
    give these values.
  - The third Implementer guidance bullet (the modes of the OpenMMLab-Exporter host), as
    [ADR-XH1J](XH1J-normalize-input-dtype.md) writes it, gets one sentence on the host defaults.
  - The "Typical use" of the `none` row names graphs that take raw 0-255 pixels. YOLOX (no `mean`,
    no `std`) and RTMO (`mean` `[0, 0, 0]`, `std` `[1, 1, 1]`) are models whose upstream does not
    normalize.
  - No rule changes. The full-section `pre_normalize.py` is the XH1J v2 file with the defaults, and
    replaces that file. 2 `pre.normalize` cases are new: `custom-mean-and-std-defaults` and
    `custom-all-defaults`.
- Target spec version: `2.0.0`.
- Models: none in scope uses `custom`. `yolox-person` and RTMO keep `normalization: none`. No value
  changes.
- Supersedes: none.
- Related: [ADR-XH1J](XH1J-normalize-input-dtype.md) is in `depends_on`. Its content commit lands
  first. Also `model-yolox-person@openmmlab-exporter` (row T10, spec defect 3).
- The user confirmed the plan decision of part 1 on 2026-11-06: the `custom` defaults and the
  `none` row are not one contract unit with the dtype rules of
  [ADR-XH1J](XH1J-normalize-input-dtype.md). They get their own decision.
- `run` of `tools/vector_formulas/pre_normalize.py` reads the new text: an absent `custom` key
  gets its default.

## Reason

`V-pre.normalize-1` allows a `custom` object with no `mean` or `std`, but the text gave no value.
The XH1J v2 reference refused such a valid sidecar with no rule ID. The OpenMMLab-Exporter host and
the skellytracker package (`CustomNormalization`, `build_normalization_fn`) use the identity
values. The `none` row said that YOLOX normalizes internally, but its upstream config has no `mean`
and no `std`.

## Evidence

Parity: `pass` by equal code. Without the module docstring, the reference file is byte-equal to the
XH1J v1 file (SHA-256 `a0858722`). OpenMMLab-Exporter ADR-YR3X ran that file on `yolox-person`:
540 of 540 normalizer tensors bit-equal, 155 of 155 gate and control values equal, branch `none`,
`bgr`, `float32`, and the `imagenet` controls. No parity run covers `custom`, because no model uses
it. The 2 new cases pass 2 of 2 on the host `make_normalizer` at OpenMMLab-Exporter `c82f2f11`.

## Open work

See [open-work.md](../open-work.md).

## Notes at acceptance

- No parity run covers the `custom` branch. The evidence is the 2 cases, the host run and the
  package code.
- One box of "Before you stop" is not ticked: the intake names this bundle. The
  `model-yolox-person@openmmlab-exporter` v2 bundle meets it (intake proposal table and `related`).
- The module docstring says that skellytracker has no reference of this section, and that no
  decision entry covers the proposal. Both are stale. The content commit copies the file
  byte-equal. The non-spec commit corrects the docstring. (new 2026-11-09)
- The session did not open the mmpose and mmengine permalinks of part 1.
- [ADR-XH1J](XH1J-normalize-input-dtype.md) stays the owner of `pre.normalize`
  ([Section owner](../../model-addition-workflow/hand-over.md#section-owner)). The contributor is
  the same.
- [x] The content commit gives the changelog row the acceptance date and the link to this entry,
  and the section link relative to `changelog.md`. (new 2026-11-09)

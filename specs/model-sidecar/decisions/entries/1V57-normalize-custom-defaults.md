# 1V57 — Spec change: normalize-custom-defaults

**Status:** proposed, 2026-11-09 (proposal-normalize-custom-defaults@openmmlab-exporter@v1).

## Decision

**Proposed, not decided.** The proposal is
[`proposal.md`](../../proposals/normalize-custom-defaults/proposal.md).

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
- Supersedes on acceptance: none.
- Related: [ADR-XH1J](XH1J-normalize-input-dtype.md) is in `depends_on`. It must land first, or
  earlier in the same round. Also `model-yolox-person@openmmlab-exporter` (row T10, spec defect 3).

## Reason

`V-pre.normalize-1` allows a `custom` object with no `mean` or `std`, but the text gives no value.
The XH1J v2 reference refuses such a valid sidecar with no rule ID. The OpenMMLab-Exporter host and
the skellytracker package (`CustomNormalization`, `build_normalization_fn`) use the identity
values. The `none` row says that YOLOX normalizes internally, but its upstream config has no `mean`
and no `std`.

## Evidence

Parity: `pass` by equal code. Without the module docstring, the reference file is byte-equal to the
XH1J v1 file (SHA-256 `a0858722`). OpenMMLab-Exporter ADR-YR3X ran that file on `yolox-person`:
540 of 540 normalizer tensors bit-equal, 155 of 155 gate and control values equal, branch `none`,
`bgr`, `float32`, and the `imagenet` controls. No parity run covers `custom`, because no model uses it. The 2 new cases pass 2 of
2 on the host `make_normalizer` at OpenMMLab-Exporter `c82f2f11`.

## Open work

See [open-work.md](../open-work.md).

## Before acceptance

- The user has not decided this proposal.
- The user must confirm or refuse the plan decision of part 1: the `custom` defaults and the `none`
  row are not one contract unit with the dtype rules of [ADR-XH1J](XH1J-normalize-input-dtype.md)
  (user decision of 2026-11-06, response r2 to that bundle).
- Order: [ADR-XH1J](XH1J-normalize-input-dtype.md) must be accepted, and must land first. The
  anchor of part 2.3 is in the third Implementer guidance bullet that XH1J v2 writes. If a later
  XH1J version changes that bullet, check the anchor again. At landing, copy the reference file of this
  proposal before you run `land` for its vectors. The XH1J file refuses the 2 new cases.
- If XH1J lands alone, the reference refuses a valid `custom` object with no `mean` or `std`. No
  example has one.
- No parity run covers the `custom` branch. The evidence is the 2 cases, the host run and the
  package code.
- One box of "Before you stop" is not ticked: the intake names this bundle. The
  `model-yolox-person@openmmlab-exporter` v2 bundle meets it (intake proposal table and `related`).
- Editorial at landing: the module docstring says that skellytracker has no reference of this
  section, but part 3 builds on the XH1J file. The changelog "Driven by" cell gives the split
  decision of 2026-11-06. It needs the acceptance date and the link to this entry.
- The session did not open the mmpose and mmengine permalinks of part 1.
- [ADR-XH1J](XH1J-normalize-input-dtype.md) stays the owner of `pre.normalize`
  ([Section owner](../../model-addition-workflow/hand-over.md#section-owner)). The contributor is
  the same.

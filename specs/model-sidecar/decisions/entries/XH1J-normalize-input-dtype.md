# XH1J — Spec change: normalize-input-dtype

**Status:** proposed, 2026-11-06 (proposal-normalize-input-dtype@openmmlab-exporter@v1); recorded
again 2026-11-09 (proposal-normalize-input-dtype@openmmlab-exporter@v2).

## Decision

**Proposed, not decided.** The proposal is
[`proposal.md`](../../proposals/normalize-input-dtype/proposal.md).

- Sections: [`pre.normalize`](../../pre/normalization.md) and
  [`common.input`](../../common/input.md).
- Change:
  - Each normalization mode casts its result to the `input.dtype` entry of the selected precision,
    as the last step. Today the text casts only for `none`.
  - New rule `V-pre.normalize-3`: a `uint8` input needs the resolved normalization `none`, and
    `compute_dtype` absent or `uint8`.
  - `V-common.input-2` removes `int8` from the input dtypes. The output dtypes keep `int8`.
  - A full-section reference module `pre_normalize.py` imports the landed
    `pre_resize_interpolation`. 9 `pre.normalize` cases and a data-only `common.input.yaml` with 2
    cases are new. The 15 current cases do not change.
- Target spec version: `2.0.0`.
- Models: RTMW (`rtmw-wholebody133`) and `yolox-person`, OpenMMLab-Exporter. No value changes.
- Supersedes on acceptance: none.
- Related: the held `reference/pre_normalize.py` of `model-yolox-person@openmmlab-exporter` and
  `model-rtmw-wholebody133@openmmlab-exporter`;
  [ADR-PHJ3](PHJ3-resize-compute-dtype.md) (the proposal closes its open case of the cast of a
  float32 resize to an integer `input.dtype`); [ADR-1V57](1V57-normalize-custom-defaults.md) (the
  `custom` defaults and the `none` row, split from v1).

## Reason

The held module differed from the text in four points: it cast every mode to `input.dtype`, it
refused `uint8` with a mode other than `none`, it refused `int8`, and it accepted a missing
top-level `normalization`. For the first three, the proposal changes the text to match the code.
For the fourth, the code now follows the current `V-pre.normalize-1`.

## Evidence

Parity: `pass` for `yolox-person` (OpenMMLab-Exporter ADR-YR3X), measured with the v1 module. The
committed script `decisions/scripts/yolox_person_reference_swap.py` at OpenMMLab-Exporter
`53a48480`: 540 of 540 normalizer tensors are bit-equal to the host, and 155 of 155 gate and
control values match, on the branch `none`, `bgr`, `float32`. The v2 code differs only in the
`custom` branch, which that run does not use. RTMW: `pass` on `imagenet`, `rgb`, `float32`
(OpenMMLab-Exporter
[ADR-21VF](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/ecee56e1ea1b4d3901c76a73b713ed0256675e78/decisions/entries/21VF-rtmw-normalize-reference-check.md)):
all 768 channel and value pairs and 143769600 crop values, largest difference 2.38e-7, gate 5e-7.
The part 5 permalink of the record names a commit that does not exist. The exporter host ran 14 of
the 15 numeric cases.

## Open work

See [open-work.md](../open-work.md).

## Before acceptance

- [x] The user must confirm or refuse each plan decision of part 1:
  - this proposal replaces a module of the current text, its part 3 file becomes the
    `pre.normalize` reference, and the model bundles skip the reference step for this section;
  - `int8` leaves the input dtypes, and the output dtypes keep it.
  Closed: the user confirmed both and accepted the dtype rules on 2026-11-06 (response r2).
- The branches `unit_float`, `custom`, `float16` and `uint8` have no parity run. Only vector
  cases cover them. The RTMW check passes (Evidence). (changed 2026-11-09)
- One box of "Before you stop" is not ticked: the intake names this bundle. The
  `model-yolox-person@openmmlab-exporter` v2 intake names it. The next RTMW version must name it.
  (changed 2026-11-09)
- [x] The module docstring says that the `yolox-person` parity is `to run`, and it does not list
  `V-common.input-5` as a rule of another section. Closed: v2 gives both results and lists the rule.
- [x] Changes that part 3 does not list: the order of the checks changed, so a sidecar that breaks
  `V-pre.normalize-1` and `-2` gives another rule ID; `source_pixels` refuses fractional pixels
  for an 8-bit resize; `check_rules` and `normalize` give different rule IDs for an invalid
  `compute_dtype`. Closed: v2 part 3 lists the three changes.
- [x] One contract unit: the `custom` defaults and the YOLOX correction of the `none` row come with
  the dtype rules. The user decides if this is one unit. Closed: the user decided that they are not
  one unit (r2). [ADR-1V57](1V57-normalize-custom-defaults.md) holds them.
- `common.input.yaml` would be the first vector file of a `common.*` section.
- The other open case of [ADR-PHJ3](PHJ3-resize-compute-dtype.md) stays open: a fractional
  `pad_value` with `compute_dtype: uint8`.
- Recording this entry makes OpenMMLab-Exporter the owner of `pre.normalize` and `common.input`
  while the entry is `proposed`
  ([Section owner](../../model-addition-workflow/hand-over.md#section-owner)).
- The v2 module refuses a `custom` object with no `mean` or no `std` at run time, with no rule
  ID. `check_rules` accepts it. [ADR-1V57](1V57-normalize-custom-defaults.md) removes the refusal.
  The user has not decided it. If this entry lands alone, the refusal ships. No example and no
  vector case has such an object. (new 2026-11-09)
- The content commit must update `run` of `tools/vector_formulas/pre_normalize.py`, or delete
  it and give the reason (procedure B step 8). `run` casts only `none` to `uint8`, and it accepts
  a fractional pixel. Thus the generator cross-check fails on the cases `unit-float-float16`,
  `imagenet-float16` and `uint8-resize-pixels-are-integers`. (new 2026-11-09)
- The module computes in float64 and then casts to `float16`. The host computes in float32.
  Near a `float16` rounding midpoint, the two can differ by one `float16` step, more than the tolerance 1e-5.
  (new 2026-11-09)
- The part 2.1 anchor of `open-work.md` quotes plain text. The current text has the link of
  [ADR-PHJ3](PHJ3-resize-compute-dtype.md). The landing keeps the link. (new 2026-11-09)

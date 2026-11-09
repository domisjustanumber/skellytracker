# XH1J — Spec change: normalize-input-dtype

**Status:** absorbed into [`pre/normalization.md#behaviour`](../../pre/normalization.md#behaviour), 2026-11-09 (user; PR: pending).

## Decision

The user accepted the proposal on 2026-11-09. The record is
[`proposal.md`](../../proposals/normalize-input-dtype/proposal.md)
(proposal-normalize-input-dtype@openmmlab-exporter@v2).

- Sections: [`pre.normalize`](../../pre/normalization.md) and
  [`common.input`](../../common/input.md).
- Change:
  - Each normalization mode casts its result to the `input.dtype` entry of the selected precision,
    as the last step. Before this change, the text cast only for `none`.
  - New rule `V-pre.normalize-3`: a `uint8` input needs the resolved normalization `none`, and
    `compute_dtype` absent or `uint8`.
  - `V-common.input-2` removes `int8` from the input dtypes. The output dtypes keep `int8`.
  - A full-section reference module `pre_normalize.py` imports the landed
    `pre_resize_interpolation`. 9 `pre.normalize` cases and a data-only `common.input.yaml` with 2
    cases are new. The 15 current cases do not change.
- Target spec version: `2.0.0`.
- Models: RTMW (`rtmw-wholebody133`) and `yolox-person`, OpenMMLab-Exporter. No value changes.
- Supersedes: none.
- Related: the held `reference/pre_normalize.py` of `model-yolox-person@openmmlab-exporter` and
  `model-rtmw-wholebody133@openmmlab-exporter`;
  [ADR-PHJ3](PHJ3-resize-compute-dtype.md) (the proposal closes its open case of the cast of a
  float32 resize to an integer `input.dtype`); [ADR-1V57](1V57-normalize-custom-defaults.md) (the
  `custom` defaults and the `none` row, split from v1).
- The user confirmed two plan decisions on 2026-11-06. This proposal replaces a module of the
  current text: its part 3 file becomes the `pre.normalize` reference, and the model bundles skip
  the reference step for this section. `int8` leaves the input dtypes, and the output dtypes keep
  it.
- `run` of `tools/vector_formulas/pre_normalize.py` reads the new text: it casts each mode to
  `input.dtype`, it refuses a pixel of an 8-bit resize that is not an integer from 0 to 255, and
  it reads `resize.compute_dtype`.

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

## Notes at acceptance

- The branches `unit_float`, `custom`, `float16` and `uint8` have no parity run. Only vector
  cases cover them. The RTMW check passes (Evidence). (changed 2026-11-09)
- One box of "Before you stop" is not ticked: the intake names this bundle. The
  `model-yolox-person@openmmlab-exporter` v2 intake names it. The next RTMW version must name it.
  (changed 2026-11-09)
- The other open case of [ADR-PHJ3](PHJ3-resize-compute-dtype.md) stays open: a fractional
  `pad_value` with `compute_dtype: uint8`.
- Recording this entry makes OpenMMLab-Exporter the owner of `pre.normalize` and `common.input`
  while the entry is `proposed`
  ([Section owner](../../model-addition-workflow/hand-over.md#section-owner)).
- The v2 module refuses a `custom` object with no `mean` or no `std` at run time, with no rule
  ID. `check_rules` accepts it. [ADR-1V57](1V57-normalize-custom-defaults.md) removes the refusal.
  The user accepted it on 2026-11-09. Its content commit comes right after the content commit of
  this entry. No example and no vector case has such an object. (changed 2026-11-09)
- The module computes in float64 and then casts to `float16`. The host computes in float32.
  Near a `float16` rounding midpoint, the two can differ by one `float16` step, more than the tolerance 1e-5.
  (new 2026-11-09)
- [x] The v2 docstring, the three changes that v1 part 3 did not list, and the split of the
  `custom` defaults into [ADR-1V57](1V57-normalize-custom-defaults.md) closed three items of v1.
- [x] The content commit updates `run` (Decision), keeps the
  [ADR-PHJ3](PHJ3-resize-compute-dtype.md) link in the part 2.1 edit of `open-work.md`, sets the
  `vectors` of `common.input`, rewrites the record-relative links of part 2 and links this entry
  from `V-pre.normalize-3`, `V-common.input-2` and the changelog row. (new 2026-11-09)

# XH1J — Spec change: normalize-input-dtype

**Status:** proposed, 2026-11-06 (proposal-normalize-input-dtype@openmmlab-exporter@v1).

## Decision

**Proposed, not decided.** The proposal is
[`proposal.md`](../../proposals/normalize-input-dtype/proposal.md).

- Sections: [`pre.normalize`](../../pre/normalization.md) and
  [`common.input`](../../common/input.md).
- Change:
  - Each normalization mode casts its result to the `input.dtype` entry of the selected precision,
    as the last step. Today the text casts only for `none`.
  - The `custom` keys `scale`, `mean` and `std` get the defaults `1`, `[0, 0, 0]` and `[1, 1, 1]`.
  - New rule `V-pre.normalize-3`: a `uint8` input needs the resolved normalization `none`, and
    `compute_dtype` absent or `uint8`.
  - `V-common.input-2` removes `int8` from the input dtypes. The output dtypes keep `int8`.
  - The `none` row says that YOLOX takes raw pixels, and does not normalize in the graph.
  - A full-section reference module `pre_normalize.py` imports the landed
    `pre_resize_interpolation`. 11 `pre.normalize` cases and a data-only `common.input.yaml` with 2
    cases are new. The 15 current cases do not change.
- Target spec version: `2.0.0`.
- Models: RTMW (`rtmw-wholebody133`) and `yolox-person`, OpenMMLab-Exporter. No value changes.
- Supersedes on acceptance: none.
- Related: the held `reference/pre_normalize.py` of `model-yolox-person@openmmlab-exporter` and
  `model-rtmw-wholebody133@openmmlab-exporter`;
  [ADR-PHJ3](PHJ3-resize-compute-dtype.md) (the proposal closes its open case of the cast of a
  float32 resize to an integer `input.dtype`).

## Reason

The held module differed from the text in four points: it cast every mode to `input.dtype`, it
refused `uint8` with a mode other than `none`, it refused `int8`, and it accepted a missing
top-level `normalization`. For the first three, the proposal changes the text to match the code.
For the fourth, the code now follows the current `V-pre.normalize-1`.

## Evidence

Parity: `pass` for `yolox-person` only (OpenMMLab-Exporter ADR-YR3X). The committed reference-swap
script `decisions/scripts/yolox_person_reference_swap.py` at OpenMMLab-Exporter `53a48480` ran with
this module: 540 of 540 normalizer tensors are bit-equal to the host, and 155 of 155 gate and
control values match. The run covers only the branch `none`, `bgr`, `float32`. The exporter host
ran 16 of the 17 numeric cases.

## Open work

See [open-work.md](../open-work.md).

## Before acceptance

- The user must confirm or refuse each plan decision of part 1:
  - this proposal replaces a module of the current text, its part 3 file becomes the
    `pre.normalize` reference, and the model bundles skip the reference step for this section;
  - `int8` leaves the input dtypes, and the output dtypes keep it.
- `to run`: the RTMW reference swap. RTMW is the model in scope, and it uses `imagenet`, `rgb`.
  The branches `unit_float`, `custom`, `float16` and `uint8` have no parity run.
- Two boxes of "Before you stop" are not ticked: the model intakes do not name this bundle, and
  the note "Not packed yet" is stale.
- The module docstring says that the `yolox-person` parity is `to run`, and it does not list
  `V-common.input-5` as a rule of another section.
- Changes that part 3 does not list: the order of the checks changed, so a sidecar that breaks
  `V-pre.normalize-1` and `-2` gives another rule ID; `source_pixels` refuses fractional pixels
  for an 8-bit resize; `check_rules` and `normalize` give different rule IDs for an invalid
  `compute_dtype`.
- One contract unit: the `custom` defaults and the YOLOX correction of the `none` row come with
  the dtype rules. The user decides if this is one unit.
- `common.input.yaml` would be the first vector file of a `common.*` section.
- The other open case of [ADR-PHJ3](PHJ3-resize-compute-dtype.md) stays open: a fractional
  `pad_value` with `compute_dtype: uint8`.
- Recording this entry makes OpenMMLab-Exporter the owner of `pre.normalize` and `common.input`
  while the entry is `proposed`
  ([Section owner](../../model-addition-workflow/hand-over.md#section-owner)).

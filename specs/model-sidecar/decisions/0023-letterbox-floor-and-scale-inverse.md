# 0023 — `floor` rounding and a scale inverse for `letterbox`

**Status:** proposed, 2026-10-23 (from the exporter evidence of Qualcomm-Exporter and its installed
`qai_hub_models` 0.64.0).

## Decision

**Proposed, not decided.** This entry is a gap record (see [Rules](../../../decisions/README.md#rules)). It does not
have the eight parts of a proposal.

Add `floor` as a third value of `rounding` for
[`letterbox`](../pre/resize-letterbox.md#fields):
`n_w = max(1, floor(src_w * s))` and `n_h = max(1, floor(src_h * s))`, with `s` computed in IEEE 754
double precision. Add an inverse that divides by the unrounded scale:
`x_src = (x - left) / s` and `y_src = (y - top) / s`. This inverse goes beside the current
[inverse](../pre/resize-letterbox.md#inverse), which uses the rounded `n_w` and
`n_h`. The full proposal must choose between two forms: `rounding: floor` sets the inverse, or a
separate field selects it. The full proposal must also say whether the spec describes the integer
cut of the upstream inverse. The proposal comes with the Qualcomm-Exporter overhaul, with the parts
of [0014](../../../decisions/0014-spec-lifecycle.md#new-model-workflow). [0008](0008-vnext-scope.md) puts
Qualcomm-Exporter out of the `vNEXT` scope. Thus the change goes into a later revision, unless the
decision extends that scope.

## Reason

- The upstream `resize_pad` of the MediaPipe person detector cuts the scaled size with `math.floor`.
  The spec `letterbox` rounds with `half_even` or `half_up`. `floor` is neither, so the verdict is a
  near-miss (a gap).
- With floats, `floor` can drop a pixel on the long side. In Python, `49 * (128 / 49)` is
  `127.99999999999999`, so `floor` gives `127`, not `128`.
- The inverse differs too, also when the sizes agree. Example: a 427x640 source into 128x128 gives
  `s = 0.2`, `n_w = 85` (with `floor` and with `half_even`) and `left = 21`. The right edge of the
  content is at `x = 106`. The upstream inverse gives `(106 - 21) / 0.2 = 425`. The spec inverse gives
  `(106 - 21) * 427 / 85 = 427`.
- The centre position of the upstream agrees with the spec: `left = floor((T_w - n_w) / 2)`, and the
  odd pixel goes to the right or the bottom.
- The current Qualcomm-Exporter file is valid. It declares `v2024.09.1019`, and it has no
  `pad_position` and no `rounding`. Under the legacy rules, the rounding is implementation-defined.

## Evidence

- `qai_hub_models` 0.64.0 (installed in the `.venv` of Qualcomm-Exporter; not tracked),
  `utils/image_processing.py`: `resize_pad` (lines 262-360) sets
  `new_height = math.floor(height * scale)` and `new_width = math.floor(width * scale)` (lines
  327-328). `_split_padding` gives `pad_size // 2` to the left or the top. The function pads with
  `0.0` and resizes with torch `interpolate(mode="bilinear")`. `denormalize_coordinates` (lines
  499-538) computes `(x * W - pad) / scale` with the unrounded `scale`, then cuts the result with
  `.int()`.
- Qualcomm-Exporter at commit `4ca4586`: `qai_sidecar.py` (lines 144-149) declares
  `method: letterbox`, `preserve_aspect_ratio: true`, `pad_value: 0` and `interpolation: linear`, with
  no `pad_position` and no `rounding`. Line 12 sets `SCHEMA_VERSION = "v2024.09.1019"`.
  `qai_datasets.py`, `load_letterboxed` (lines 152-167), uses `max(1, int(src * s))`.
  `unproject_boxes` (lines 170-181) divides by the unrounded `s`. `tests/test_qai_datasets.py` (lines
  55-64) uses exact sizes, so it cannot tell the two inverses apart.
- The two worked numbers in "Reason" were computed with Python floats on 2026-10-23.

## Alternatives rejected

- **Describe the upstream with `half_even` or `half_up`.** That is a near-miss. It gives the same size
  on most inputs and a different size on others. The inverse differs also when the sizes agree.

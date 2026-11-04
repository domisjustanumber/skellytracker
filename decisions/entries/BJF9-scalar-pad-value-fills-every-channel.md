# BJF9 — A scalar pad value fills every channel

**Status:** accepted, 2026-11-04 (user; PR: pending).

## Decision

1. **The rule.** A scalar `input.resize.pad_value` or `input.resize.crop_policy.pad_value` `s`
   means `[s, s, s]` for every method. It fills each channel with `s`. An array of three numbers
   keeps its meaning: one value for each channel, in the order of `input.color_format`.
2. **Where the rule goes.** The `pad_value` row of
   [`input.resize`](../../specs/model-sidecar/common/input.md#inputresize) and the
   `crop_policy.pad_value` row of
   [`affine_person_crop`](../../specs/model-sidecar/pre/resize-affine-person-crop.md#fields) state
   item 1.
3. **The pseudocode.** The [`fit`](../../specs/model-sidecar/pre/resize-fit.md#behaviour) and
   [`affine_person_crop`](../../specs/model-sidecar/pre/resize-affine-person-crop.md#behaviour)
   pseudocode expands the value to one value for each channel, `border`, before `warpAffine`.
   `borderValue` is `border`, not the raw `pad_value`. The `letterbox` pseudocode stays the same:
   `full((T_h, T_w, 3), pad_value)` already fills each channel.
4. **No new rule ID.** `V-common.input-4` stays. A scalar and an array of three numbers stay valid.
5. **Vectors.** `pre.resize.fit` and `pre.resize.affine_person_crop` each get the case
   `scalar-pad-fills-each-channel`, with `function: border` and `pad_value: 114`. Its `expect` is
   `{border: [114, 114, 114]}`. `tools/vector_formulas/pre_resize_fit.py` and
   `pre_resize_affine_person_crop.py` get `border`, and `fit_runner` of
   `tools/tests/test_vectors.py` gets a `border` branch.
6. **Examples.** No example changes. RTMO body7 keeps `pad_value: 114`. RTMW keeps
   `crop_policy.pad_value: 0`.

## Reason

- The user decided on 2026-11-04 and chose the option "Fills every channel (Recommended)": "A
  scalar s means [s, s, s] for every method; the fit/affine pseudocode expands it before
  warpAffine. RTMO body7 stays valid with border [114,114,114], as its mmpose config (3-value pad)
  intends."
- Before this entry, the text did not say what a scalar fills. The `letterbox` pseudocode filled
  each channel. The `fit` and `affine_person_crop` pseudocode passed the scalar to `warpAffine`. In
  OpenCV, that call fills only channel 0. Thus one sidecar value had two readings.
- The upstream of the only `fit` model wants three equal values. mmpose `BottomupResize` of RTMO
  body7 has `pad_val=(114, 114, 114)`. The exporter writes the scalar `114`.
- mmpose itself expands a scalar to three values before `warpAffine` in
  `BottomupRandomAffine`. The rule follows that intent.
- A scalar gives the same value to each channel, so it does not depend on `input.color_format`.
- A border pixel far from the source image does not depend on the interpolation, so the case is
  exact. A host that passes the scalar unchanged fails it.

## Consequences

- A host must not pass a scalar `pad_value` unchanged to `cv2.warpAffine`.
- The package function `fit_preprocess` passes the scalar unchanged. It fails the new `fit` case,
  so the `forward` step of `pre.resize.fit` becomes `partial`. The file-level `verified_against`
  of `pre.resize.fit` becomes `unverified`, and each other case lists `fit_preprocess`. The
  implementation-plan item "Scalar and array pad values" of M8 holds the fix.
- A reference module of `pre.resize.fit` or `pre.resize.affine_person_crop` must define `border`.
- The guidance in `mapping-hints.md` and in the model intake template no longer asks for an array
  for `fit` and `affine_person_crop`.

## Evidence

- OpenCV 4.13.0 and numpy 2.4.6 (the skellytracker environment): `cv2.warpAffine` with
  `borderValue=114`, `114.0` or `(114,)` gives the border `[114, 0, 0]` on a `uint8` 3-channel
  image. `(114, 114, 114)` gives `[114, 114, 114]`. With no `borderValue`, the border is
  `[0, 0, 0]`. `fit_preprocess(..., pad_value=114)` gives `[114, 0, 0]`. Script:
  [`bjf9_scalar_border.py`](../scripts/bjf9_scalar_border.py).
- mmpose v1.3.2 `BottomupResize` passes `pad_val` unchanged to `cv2.warpAffine`. Its default is
  `(0, 0, 0)`
  ([`bottomup_transforms.py:471`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/bottomup_transforms.py#L471),
  [`bottomup_transforms.py:588-593`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/bottomup_transforms.py#L588-L593)).
  `BottomupRandomAffine` expands a scalar to three values
  ([`bottomup_transforms.py:232-233`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/bottomup_transforms.py#L232-L233)).
  `TopdownAffine` passes no `borderValue`, so its border is 0
  ([`topdown_transforms.py:117-118`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/topdown_transforms.py#L117-L118)).
- The RTMO body7 val pipeline has `pad_val=(114, 114, 114)` (OpenMMLab-Exporter
  [`rtmo-m_16xb16-600e_body7-640x640.py:340`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/6c494a0bcb48acc218b1edd3617b8621b35cc3f4/mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py#L340)).
  The exporter writes `PAD_VALUE = 114` (OpenMMLab-Exporter
  [`rtmo/preprocess.py:15`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/f4511f222fc94f3c6600d6fb9503e1cfa6e37855/rtmo/preprocess.py#L15)).

## Alternatives rejected

- **A scalar fills only channel 0 for `fit` and `affine_person_crop`.** This copies an OpenCV
  detail into the spec. RTMO body7 would then have the border `[114, 0, 0]`, which its config does
  not intend, and `letterbox` would read a scalar in a different way.
- **Only an array for `fit` and `affine_person_crop`.** This makes the RTMO body7 example and the
  exporter output invalid. It also adds a rule for no gain, because a scalar has one clear meaning.

## Open work

See [open-work.md](../open-work.md).

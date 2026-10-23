# 0012 — `fit` resize for RTMO; `pad_value` is required

**Status:** accepted, 2026-10-22 (backfilled from #81, which adds `fit` as change 2 of the summary in
`specs/sidecar-spec.md` and implements it in `fit_preprocess` and `ResizeSpec`, and from
OpenMMLab-Exporter 0020, dated 2026-10-21. The user decided on 2026-10-22 that `pad_value` is
required.)

## Decision

- The spec defines `input.resize.method: fit`. It is a full-frame affine fit with a fractional,
  centred offset. Neither the scaled size nor the offsets are rounded:

  ```text
  s    = min(T_w / src_w, T_h / src_h)
  left = (T_w - src_w * s) / 2
  top  = (T_h - src_h * s) / 2
  M    = [[s, 0, left],
          [0, s, top ]]
  dst  = warpAffine(src, M, (T_w, T_h), <interpolation>, borderMode=constant, borderValue=pad_value)
  ```

- The unprojection is the exact inverse of `M`: `x_src = (x - left) / s` and
  `y_src = (y - top) / s`. See [Unprojection](../../specs/sidecar-spec.md#unprojection).
- RTMO body7 uses `fit` with `pad_value: 114` and `interpolation: linear`. This matches mmpose
  `BottomupResize`.
- At `vNEXT`, a `fit` resize must declare `pad_value`. The value is a scalar or an array of three
  numbers. An array is per channel, in `input.color_format` order, as for `letterbox`. The value is
  the raw pixel value before normalization.
- `pad_position`, `rounding`, `preserve_aspect_ratio` and `crop_policy` are invalid with `fit`.
- Sidecars older than `vNEXT` do not have `fit`. See
  [Version-aware compatibility](../../specs/sidecar-spec.md#version-aware-compatibility).

## Reason

- **`letterbox` cannot describe RTMO.** mmpose `BottomupResize` warps the image with `cv2.warpAffine`
  to a fractional fit size. `letterbox` rounds the resized size and uses `cv2.resize` plus padding.
  The two give different pixels at every scale except 1, even when the resized size is an integer.
  Different rounding rules do not fix this (see "Evidence").
- **The border value changes the model input.** The upstream pipeline sets it. RTMO uses `114`. A
  sidecar that omits it leaves the value to the host. The code default for `fit` is `0` (see
  "Evidence"). So, with an omitted `pad_value`, skellytracker fills the border with `0` where mmpose
  uses `114`. Another host can use another value. No error shows. Requiring the field makes the
  exporter write the value that it checked. `letterbox` keeps its default of `114`.
- **The user decided this on 2026-10-22.**

## Evidence

**Measurements** (OpenMMLab-Exporter 0020, RTMO-M 640x640 fp32, mmpose `BottomupResize` as the
reference). The `letterbox` columns are for `pad_position: center`:

| Image (w x h) | Fit extent (w x h) | `letterbox` pixel diff | Top-box IoU | Keypoint mean / max difference |
|---|---|---|---|---|
| 586x640 | 586x640 (scale 1) | 0 | 1.000 | 0 / 0 px |
| 320x240 | 640x480 (integral, scale 2) | mean 2.07, max 81 | 0.746 (top detection changed) | 1.43 / 8.60 px |
| 333x500 | 426.24x640 | mean 0.46, max 35 | 0.988 | 2.26 / 7.90 px |
| 288x307 | 600.39x640 | mean 4.74, max 88 | 0.972 | 5.13 / 17.89 px |

- The `fit` method reproduces mmpose bit-exactly on all four images: `input_max_abs_diff: 0`. The
  detections and keypoints are identical.
- A `letterbox` with `pad_position: top_left` changes 83 to 95 percent of the input pixels. It shifts
  the keypoints of the top detection by 29 to 156 px on average. `center` is the better `letterbox`
  setting for RTMO, but it is still not equivalent to `fit`.
- The two images with fractional extents come from COCO val2017. Their top detections have scores 0.63
  and 0.18. On these images, the output difference comes from a sub-pixel resize difference that the
  model amplifies. It is not a geometry error.
- Only RTMO-M at 640x640 fp32 was probed. RTMO-T (416x416), RTMO-S, RTMO-L and the coco and
  crowdpose variants are untested.

**Exporter output.** The OpenMMLab-Exporter sidecar writer emits
`input.resize: {method: fit, pad_value: 114, interpolation: linear}` with no `pad_position`,
`rounding`, `preserve_aspect_ratio` or `crop_policy` (OpenMMLab-Exporter 0020, "Implementation").
The reference example
[RTMO body7](../../specs/sidecar-spec.md#rtmo-body7-openmmlab-exporter-bottom-up-pose-nms-in-the-graph)
shows the result.

**Spec.** The `fit` rules are in
[`input.resize`](../../specs/sidecar-spec.md#inputresize): the `method` and `pad_value` rows, the `fit`
algorithm and its closing paragraph. The check "A `fit` resize declares `pad_value`" is in
[Validation rules](../../specs/sidecar-spec.md#validation-rules). OpenMMLab-Exporter 0020 listed the
missing `fit` text as open. The normative `fit` text was added to
[`input.resize`](../../specs/sidecar-spec.md#inputresize) after #81.

**Code, checked on 2026-10-22.**

- `fit_preprocess` in `skellytracker/core/detectors/processing/image_preprocessing.py` uses the same
  formula as the spec. It computes `scale = min(target_w / src_w, target_h / src_h)`, and `left` and
  `top` as fractions. It calls `cv2.warpAffine` with `cv2.BORDER_CONSTANT`. It returns the warped
  image and `(scale, left, top)`.
- `fit_preprocess` passes a scalar `pad_value` to `cv2.warpAffine` as `float(pad_value)`. OpenCV then
  fills only channel 0 of a 3-channel image. A scalar `114` gives the border `[114, 0, 0]`. A 3-tuple
  `(114, 114, 114)` gives `[114, 114, 114]`. A 5-line OpenCV script checked this on 2026-10-22, with
  OpenCV 4.13.0. Thus, for a scalar `pad_value` such as the `114` of RTMO body7, this function fills
  channels 1 and 2 of the border with `0`.
- The signature of `fit_preprocess` has `pad_value = 0`.
- `preprocess_image` in the same file sets `pad_value = 0` for `fit` when `resize.pad_value` is `None`.
  For `letterbox` it uses `114`.
- `ResizeSpec` in `skellytracker/core/sidecar/model.py` sets `pad_value` to `None` by default.
  `_check_method_specific_fields` rejects `pad_position`, `rounding` and `preserve_aspect_ratio` with
  `fit`. It rejects `crop_policy` unless the method is `affine_person_crop`. It does not require
  `pad_value` for `fit`.

## Alternatives rejected

- **`letterbox` with another `rounding` value.** At 320x240 to 640x480 the extents are integers
  (scale 2). `cv2.resize` plus padding still differs from `cv2.warpAffine`: mean 2.07 and max 81 on
  a 0 to 255 scale.
- **`letterbox` with `pad_position: top_left`.** It is wrong for RTMO (see "Evidence").
- **`affine_person_crop`.** RTMO is bottom-up. It consumes the whole image and has no upstream person
  box.
- **A default `pad_value` for `fit`.** The code default (`0`) differs from the value that the only
  `fit` sidecar needs (`114`). The user decided on 2026-10-22 to require the field.

## Not repeated

- Do not write a `fit` sidecar without `pad_value`.
- Do not take the code default (`0`) as the rule. The spec rule is that the field is required.
- Do not write `pad_position`, `rounding`, `preserve_aspect_ratio` or `crop_policy` in a `fit`
  resize.
- Do not describe RTMO with `letterbox`. It is pixel-identical only at scale 1.

## Open work

See the [Open work](README.md#open-work) list of the decision log.

---
id: pre.resize.letterbox
title: Letterbox resize
kind: preprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors: [input.resize.method=letterbox]
implemented_by:
  validate: skellytracker/core/sidecar/model.py::ResizeSpec._check_method_specific_fields  # partial. pad_position and rounding are not required. preserve_aspect_ratio is not forced to true.
  forward: skellytracker/core/detectors/processing/image_preprocessing.py::letterbox_preprocess  # partial. Puts the image at the top left, truncates the size, and nothing reads pad_position or rounding. preprocess_image raises for the legacy alias preserve_aspect_ratio false.
  inverse: skellytracker/core/detectors/processing/object_detection_decode.py::decode_prenms  # partial. Divides by one ratio. Does not use the rounded n_w and n_h or the pad offsets.
external_impl: []
tests:
  - skellytracker/tests/test_image_preprocessing.py
  - skellytracker/tests/test_object_detection_decode.py
  - skellytracker/tests/sidecar/test_model_validation.py
vectors: vectors/pre.resize.letterbox.yaml
status: {spec: stable, validate: partial, forward: partial, inverse: partial}
---

# Letterbox resize

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pad_position` | enum | `letterbox`: yes | The value is `top_left` or `center`. It sets where the resized image sits on the padded canvas. This field applies to `letterbox` only. |
| `rounding` | enum | `letterbox`: yes | The value sets how to round the resized width and height. `half_even` is Python `round`. `half_up` is `floor(x + 0.5)`. This field applies to `letterbox` only. |
| `preserve_aspect_ratio` | bool | no | This field applies to a letterbox resize only. When the field is present, it must be `true`. `false` is a legacy alias for `stretch`. See [Version-aware compatibility](#legacy-behaviour). |

[`input.resize`](../common/input.md#inputresize) and [Interpolation](interpolation.md) define `target_size`, `pad_value` and `interpolation`.

## Behaviour

The host resizes the whole source image with a single scale factor and pads it to `target_size` `[T_h, T_w]`:

```text
s    = min(T_w / src_w, T_h / src_h)
n_w  = max(1, R(src_w * s))         # R = resize.rounding
n_h  = max(1, R(src_h * s))
dst  = full((T_h, T_w, 3), pad_value)
left, top = (0, 0)                                          # pad_position: top_left
left, top = (floor((T_w - n_w) / 2), floor((T_h - n_h) / 2))  # pad_position: center
dst[top:top+n_h, left:left+n_w] = resize(src, (n_w, n_h), <interpolation>)
```

If the position is `center`, any odd remainder goes to the right and the bottom. The pair `half_even` and `center` matches Ultralytics `LetterBox`. The pair `half_up` and `top_left` matches mmdet `Resize(keep_ratio=True)` + `Pad(size=…)`.

### Inverse

The host applies the inverse as part of [Unprojection](../post/unprojection.md).

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `letterbox` | `x_src = (x - left) * src_w / n_w`, `y_src = (y - top) * src_h / n_h` — the exact inverse of the resize, using the rounded `n_w`/`n_h` and the pad offsets from the letterbox algorithm. |

## Validation rules

Rules marked **(vNEXT)**: see [Validation rules](../README.md#validation-rules).

- [ ] `V-pre.resize.letterbox-1` **(vNEXT)** A `letterbox` resize must declare `pad_position` (`top_left` or `center`) and `rounding` (`half_even` or `half_up`). If `preserve_aspect_ratio` is present, it must be `true`.

See also [Input](../common/input.md#validation-rules) and [Sizes and artifacts](../common/sizes-and-artifacts.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `letterbox` + `preserve_aspect_ratio: false` | Alias for `method: stretch`. | Invalid; use `stretch`. |
| Letterbox `pad_position` / `rounding` absent | Existing host behaviour (implementation-defined). | Required. |

## Implementer guidance

## Authoring guidance

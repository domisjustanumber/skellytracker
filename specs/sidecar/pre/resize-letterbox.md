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

- The OpenMMLab-Exporter host rounds the scaled size as `max(1, R(x))`. `R` is `floor(x + 0.5)` for `half_up` and Python `round` for `half_even`. (OpenMMLab-Exporter `onnx_runtime/preprocess.py:77-83, 99-102`, eed3361)
- The same host fills the canvas with `pad_value`. It pastes the image at `(0, 0)` for `top_left` and at `((T_w - n_w) // 2, (T_h - n_h) // 2)` for `center`. It resizes with `cv2.resize`. (OpenMMLab-Exporter `onnx_runtime/preprocess.py:103-116`, eed3361)
- Test with `top_left` and `half_up`: an image 501 wide and 333 high, with target 640x640, gives a resized image 640 wide and 425 high (333 x 640 / 501 = 425.38). The rows from 425 down hold 114. (OpenMMLab-Exporter `tests/test_onnx_runtime.py:397-404`, adb332c)
- Test with `center`: an image 200 wide and 100 high, with target 64x64, gives `left` 0 and `top` 16. (OpenMMLab-Exporter `tests/test_onnx_runtime.py:429-432`, adb332c)
- Test of two copies of the preprocessing: the adapter copy and the runtime copy give bit-identical float32 tensors and equal `(left, top, new_w, new_h)` for six image sizes at targets 320 and 640. (OpenMMLab-Exporter `tests/test_rtmdet_person.py:271-285`, ba0c087)
- Ultralytics `LetterBox` is `half_even` with `center`. It computes `n = max(round(src * r), 1)` with Python `round`. A source 1280 wide and 853 high, with target 640, gives `n_h` 426. `half_up` gives 427. (ultralytics 8.4.184 `data/augment.py:1792-1798`, installed in the Ultralytics-Exporter `.venv`)
- The same code pads with `top = round(dh - 0.1)` and `bottom = round(dh + 0.1)`, where `dh = (T - n) / 2`. This gives `floor((T - n) / 2)` at the top and the left. The odd remainder goes to the bottom and the right. A loop over the remainders 0 to 640 found no difference from the `center` rule of this section. (ultralytics 8.4.184 `data/augment.py:1807-1812`, installed in the Ultralytics-Exporter `.venv`)
- Apply the declared `rounding`. For `half_even` and `half_up`, do not cut the scaled size with `int()` or `floor`. Float error can drop one pixel on the limiting side. Qualcomm-Exporter uses `n = max(1, int(src * s))`. With target 128, 84,828 of the 811,801 source sizes from 100 to 1000 give a limiting side of 127. For example, a source 100 wide and 103 high gives 124x127. `half_up` and `half_even` give 128 for the limiting side in all of these cases. The repo does not record the calculation. An upstream that cuts the size is neither `half_even` nor `half_up`. Do not map it to one of them. Its intake row is a `near-miss` ([decision 0023](../../../notes/decisions/0023-letterbox-floor-and-scale-inverse.md), status proposed). (Qualcomm-Exporter `qai_datasets.py:157-162`, 4ca4586)
- The `letterbox_preprocess` function of skellytracker also cuts the size with `int()`. See the Open work item "Letterbox rounding". ([Open work](../../../notes/decisions/README.md#open-work))

## Authoring guidance

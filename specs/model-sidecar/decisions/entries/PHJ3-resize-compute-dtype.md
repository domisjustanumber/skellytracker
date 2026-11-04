# PHJ3 — Resize compute dtype

**Status:** accepted, 2026-11-04 (user; PR: pending).

## Decision

The user chose a new sidecar field: "Add e.g. input.resize.dtype: uint8 | float32 (default uint8)
so Roboflow gets exact parity. One more field, rule and vectors." Then the user chose the name
`resize.compute_dtype`: "Same values and default, but named compute_dtype so it cannot be mixed up
with input.dtype (the tensor dtype map)."

1. **Field.** `input.resize.compute_dtype` is an optional enum: `uint8` or `float32`. The default
   is `uint8`. It applies to `letterbox`, `stretch`, `fit` and `affine_person_crop`. All sizes
   share it. Its row is in the Fields of [Interpolation](../../pre/interpolation.md#fields), next
   to `interpolation`. The line "Method-specific fields" of
   [`input.resize`](../../common/input.md#inputresize) links to it.
2. **Behaviour.** The host resizes and pads the image in `compute_dtype`. The
   [normalization](../../pre/normalization.md#behaviour) then takes the result and casts it to
   `input.dtype`.
   - `uint8`: the host resizes and pads the 8-bit image. The result is the 8-bit output of the
     OpenCV filter.
   - `float32`: the host casts the 8-bit image to float32 first. Then it resizes and pads in
     float32. It does not round or clamp the result. The values stay on the 0-255 scale.
   - The pad and the border of the warp have the compute dtype.
3. **Rules.** `V-pre.resize.interpolation-1`: if `input.resize.compute_dtype` is present, it must
   be `uint8` or `float32`. It is the first rule of the section. `V-pre.resize.none-1` adds
   `compute_dtype` to the fields that a `none` resize must not declare. Its ID does not change.
4. **Vectors.** A new data-only file `vectors/pre.resize.interpolation.yaml` holds two validator
   cases. `vectors/pre.resize.none.yaml` gets one case. The change has no numeric vector.
5. The content commit removes the sub-item "the resizes run on the source dtype" from the
   [spec defects](../open-work.md#spec-defects). The non-spec commit after it updates each other
   copy of that defect text.

## Reason

- The RF-DETR host and upstream resize the float image. No current field states this. With the
  `uint8` reading, the RF-DETR input differs by up to 0.73 of one 8-bit step on a gradient, and by
  up to 0.80 on noise. With `float32`, it differs only by float32 rounding (see Evidence).
- The default `uint8` keeps each reference example valid. The Ultralytics upstream and the
  OpenMMLab-Exporter letterbox host and RTMO probe resize the 8-bit image. The mmdet and mmpose
  lines are not checked.
- The name `compute_dtype` is not `dtype`. `input.dtype` is the map of the tensor dtype for each
  precision. A second `dtype` under `input` is easy to mix up.
- The field and its rule go in `pre.resize.interpolation`. That section owns the arithmetic of the
  resize call, and its selectors are the four methods that resize.
- The change has no numeric vector. Pixel-exact resize output is out of scope (skill
  `change-sidecar-spec`, "Examples and vectors").

## Consequences

- The RF-DETR sidecar must declare `compute_dtype: float32`. Roboflow-Exporter writes the resize
  block in
  [`rf_detr/sidecar.py:251`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L251).
  The spec has no RF-DETR example, so no example changes.
- The `qai_hub_models` upstream of the MediaPipe person detector resizes float frames. The
  Qualcomm-Exporter host resizes 8-bit images with PIL. A parity run must choose the value. This
  revision does not include Qualcomm-Exporter.
- The package rejects the field and resizes only the 8-bit image. Stage M8 of the implementation
  plan holds the item.
- Each filter is linear in the pixel values, and its weights sum to 1. Thus a host can divide the
  image and the pad value by 255 before a `float32` resize. The result changes only by float32
  rounding.

## Evidence

- Roboflow-Exporter divides by 255 and then resizes the float CHW image
  ([`onnx_runtime/preprocess.py:75-78`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/onnx_runtime/preprocess.py#L75-L78)).
- rfdetr 1.11.2 divides the uint8 image by 255 (`detr.py:2993-2995`). Then it resizes the float
  image with `F.resize(antialias=False)` and normalizes it (`detr.py:3020-3024`), installed in the
  Roboflow-Exporter `.venv`.
- ultralytics 8.4.184 letterboxes the uint8 image and then divides by 255
  (`engine/predictor.py:194-202`), installed in the Ultralytics-Exporter `.venv`.
- qai_hub_models 0.64.0 divides by 255 (`utils/image_processing.py:145, 165`). Then
  `models/templates/mediapipe/app.py:231-233, 323-325` resizes the float frames, installed in the
  Qualcomm-Exporter `.venv`.
- [`scripts/resize_compute_dtype_probe.py`](../scripts/resize_compute_dtype_probe.py), OpenCV
  4.13.0, NumPy 2.4.6:
  - A 480x640 gradient to 560x560 (`stretch`, `linear`, `imagenet`, `rgb`): the RF-DETR host
    differs from `float32` by at most 1.19e-6, and from `uint8` by at most 1.27e-2. One 8-bit
    step is 1.74e-2.
  - Noise, 480x640 to 560x560: the order of `/255` and the resize changes the result by at most
    3.6e-7 for each filter. `cubic` in float32 gives values from -63.66 to 314.37. Thus a clamp
    changes the result.
  - A 1.1x `cv2.warpAffine` with the border 114, against `/255` with the border 114/255: at most
    3.6e-7 for each filter.
  - The RF-DETR resize computes its source coordinates in float32. On noise, this gives up to
    2.19e-2 (0-255 scale) against the float32 `cv2.resize`. With float64 coordinates, it gives
    3.05e-5. This is the open defect of the arithmetic precision, not of the dtype.

## Alternatives rejected

- No field, and a statement that each resize runs on the 8-bit image. RF-DETR then has no exact
  description.
- The name `input.resize.dtype`. It is easy to mix up with `input.dtype` (user).

## Open work

See [open-work.md](../open-work.md).

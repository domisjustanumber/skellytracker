---
id: pre.resize.stretch
title: Stretch resize
kind: preprocessor
since: vNEXT
changed_in: []
selectors: [input.resize.method=stretch]
implemented_by:
  validate: skellytracker/core/sidecar/model.py::ResizeSpec._check_method_specific_fields  # partial. The model accepts stretch in a sidecar older than vNEXT.
  forward: skellytracker/core/detectors/processing/image_preprocessing.py::preprocess_image  # partial. No implementation has run the vectors yet.
  inverse: missing  # The stretch branch of preprocess_image sets resize_meta to 1.0. No code applies x * src_w / T_w.
external_impl: []
tests: []
vectors: vectors/pre.resize.stretch.yaml
status: {spec: stable, validate: partial, forward: partial, inverse: missing}
---

# Stretch resize

## Fields

[`input.resize`](../common/input.md#inputresize) and [Interpolation](interpolation.md) define `target_size`, `supports_dynamic_size` and `interpolation`. [Letterbox resize](resize-letterbox.md#behaviour) names `[T_h, T_w]`.

## Behaviour

The host resizes the whole source image directly to `target_size`. The x and y scale factors are independent. The host does not preserve the aspect ratio, does not crop and does not pad. The resize is:

```text
dst = resize(src, (T_w, T_h), <interpolation>)
```

### Inverse

The host applies the inverse as part of [Unprojection](../post/unprojection.md).

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `stretch` | `x_src = x * src_w / T_w`, `y_src = y * src_h / T_h`. |

## Validation rules

See [Input](../common/input.md#validation-rules) and [Sizes and artifacts](../common/sizes-and-artifacts.md#validation-rules).

## Legacy behaviour

Availability before `vNEXT`: [Schema versioning](../format/versioning.md#legacy-behaviour). The legacy alias `letterbox` + `preserve_aspect_ratio: false`: [Letterbox resize](resize-letterbox.md#legacy-behaviour).

## Implementer guidance

- The Roboflow-Exporter host implements `stretch`. It resizes a float image to the square target with independent scales `src_h / out_h` and `src_w / out_w`. It does not pad and does not crop. (Roboflow-Exporter `onnx_runtime/preprocess.py:22-55, 65-86`, d0559b9)
- The OpenMMLab-Exporter host raises an error for each resize method other than `letterbox`. (OpenMMLab-Exporter `onnx_runtime/preprocess.py:94-96`, eed3361)
- Upstream rfdetr 1.11.2 resizes each image to `[resolution, resolution]` by default, with `F.resize(..., antialias=False)`. (rfdetr 1.11.2 `detr.py:3020-3023`, installed in the Roboflow-Exporter `.venv`)

## Authoring guidance

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

`target_size`, `supports_dynamic_size` and `interpolation` are defined in [`input.resize`](../common/input.md#inputresize) and [Interpolation](interpolation.md). `[T_h, T_w]` is named in [Letterbox resize](resize-letterbox.md#behaviour).

## Behaviour

The whole source image is resized directly to `target_size`, with independent x and y scale factors; the host does not preserve aspect ratio, does not crop, and does not pad:

```text
dst = resize(src, (T_w, T_h), <interpolation>)
```

### Inverse

Applied as part of [Unprojection](../post/unprojection.md).

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `stretch` | `x_src = x * src_w / T_w`, `y_src = y * src_h / T_h`. |

## Validation rules

See [Input](../common/input.md#validation-rules) and [Sizes and artifacts](../common/sizes-and-artifacts.md#validation-rules).

## Legacy behaviour

Availability before `vNEXT`: [Schema versioning](../format/versioning.md#legacy-behaviour). The legacy alias `letterbox` + `preserve_aspect_ratio: false`: [Letterbox resize](resize-letterbox.md#legacy-behaviour).

## Implementer guidance

## Authoring guidance

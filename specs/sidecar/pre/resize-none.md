---
id: pre.resize.none
title: No resize
kind: preprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors: [input.resize.method=none]
implemented_by:
  validate: skellytracker/core/sidecar/model.py::ResizeSpec._check_method_specific_fields
  forward: missing  # preprocess_image raises NotImplementedError for method none.
  inverse: missing  # The identity inverse has no code.
external_impl: []
tests: []
vectors: null
status: {spec: stable, validate: implemented, forward: missing, inverse: missing}
---

# No resize

## Fields

[`input.resize`](../common/input.md#inputresize) defines `target_size` and `supports_dynamic_size`.

## Behaviour

The model takes the source image directly. The host applies no letterbox and no affine crop. The sidecar omits `target_size`. The host passes the source image unchanged.

If `supports_dynamic_size: true`, the model accepts any spatial size. Otherwise, the spatial dimensions of the size's `input.shape` are concrete. They declare the exact resolution that the model expects. In that case, the caller supplies frames at that size.

### Inverse

The host applies the inverse as part of [Unprojection](../post/unprojection.md).

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `none` | Identity. |

## Validation rules

See [Input](../common/input.md#validation-rules) and [Sizes and artifacts](../common/sizes-and-artifacts.md#validation-rules).

## Implementer guidance

## Authoring guidance

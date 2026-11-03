---
id: pre.resize.none
title: No resize
kind: preprocessor
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

[`input.resize`](../common/input.md#inputresize) defines `target_size`.

## Behaviour

The model takes the source image directly. The host applies no letterbox and no affine crop. The sidecar omits `target_size`. The host passes the source image unchanged.

The spatial dimensions of the size's `input.shape` are concrete. They declare the exact resolution that the model expects. The caller supplies frames at that size.

### Inverse

The host applies the inverse as part of [Unprojection](../post/unprojection.md).

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `none` | Identity. |

## Validation rules

- [ ] `V-pre.resize.none-1` Each size must omit `input.resize.target_size`. A `none` resize must not declare `pad_value`, `pad_position`, `rounding` or `crop_policy` ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

See also [Input](../common/input.md#validation-rules) and [Sizes and artifacts](../common/sizes-and-artifacts.md#validation-rules).

## Implementer guidance

No exporter evidence yet.

## Authoring guidance

No exporter evidence yet.

---
id: pre.resize.none
title: No resize
kind: preprocessor
---

# No resize

## Fields

`target_size` and `supports_dynamic_size` are defined in [`input.resize`](../common/input.md#inputresize).

## Behaviour

The model consumes the source image directly — no letterbox, no affine crop. `target_size` is omitted and the host passes the source image unchanged. The size's `input.shape` spatial dims are concrete and declare the exact resolution the model expects (the caller supplies frames at that size), unless `supports_dynamic_size: true`, in which case any spatial size is accepted.

### Inverse

Applied as part of [Unprojection](../post/unprojection.md).

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `none` | Identity. |

## Validation rules

See [Input](../common/input.md#validation-rules) and [Sizes and artifacts](../common/sizes-and-artifacts.md#validation-rules).

## Implementer guidance

## Authoring guidance

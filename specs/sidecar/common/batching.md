---
id: common.batching
title: Batching
kind: common
---

# Batching

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `batch_axis` | int | no | Batch dimension axis; default `0`. Non-zero batch axes are out of scope. |
| `supports_dynamic_batch` | bool | derived | `true` when `batch_artifacts` contains a `dynamic` key. Derived at load time — not authored. |

> `batching.batch_conversion` is **not part of this spec** and is reserved for a future change set.

`batch_artifacts`: [Sizes and artifacts](sizes-and-artifacts.md#sizessizeonnxbatch_artifacts).

## Validation rules

- [ ] `V-common.batching-1` `batching.batch_axis` (when present) is `0`.

## Implementer guidance

## Authoring guidance

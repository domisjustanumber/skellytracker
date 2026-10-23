---
id: common.batching
title: Batching
kind: common
since: v2024.09.1019
changed_in: []
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/model.py::BatchingSpec._check_batch_axis
  load: skellytracker/core/sidecar/model.py::OnnxSpec.supports_dynamic_batch
external_impl: []
tests: [skellytracker/tests/sidecar/test_model_validation.py]
vectors: null
status: {spec: stable, validate: implemented, load: implemented}
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

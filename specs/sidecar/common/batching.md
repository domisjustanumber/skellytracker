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
| `batch_axis` | int | no | The axis of the batch dimension. The default is `0`. Non-zero batch axes are out of scope. |
| `supports_dynamic_batch` | bool | derived | The value is `true` when `batch_artifacts` contains a `dynamic` key. The host derives it at load time. The author does not write it. |

> `batching.batch_conversion` is **not part of this spec**. It is reserved for a future change set.

`batch_artifacts`: [Sizes and artifacts](sizes-and-artifacts.md#sizessizeonnxbatch_artifacts).

## Validation rules

- [ ] `V-common.batching-1` If `batching.batch_axis` is present, it must be `0`.

## Implementer guidance

## Authoring guidance

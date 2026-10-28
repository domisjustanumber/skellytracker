---
id: common.batch_conversion
title: Batch conversion
kind: common
since: vNEXT
changed_in: []
selectors: []
implemented_by:
  validate: missing  # BatchingSpec forbids the key batch_conversion (skellytracker/core/sidecar/model.py::BatchingSpec). No code checks V-common.batch_conversion-1 to V-common.batch_conversion-4.
  load: skellytracker/core/sessions/batch_conversion.py::model_batch_convert  # partial. model_batch_convert implements the profile conditions (part of Behaviour item 3), the steps and the check (item 4). No host code calls it. Items 1, 2, 5, 6, 7 and the rest of item 3 have no code.
external_impl: []
tests: [skellytracker/tests/test_batch_conversion.py]
vectors: null
status: {spec: draft, validate: missing, load: partial}
---

# Batch conversion

> This section is a draft. Its fields, profiles and rules can change before the section becomes `stable`.

`batching.batch_conversion` names a conversion profile. The profile tells the host how to make a fixed-batch artifact from a native static-batch artifact, for a batch that `sizes.<size>.onnx.batch_artifacts` does not list. This section defines each profile. A sidecar does not contain graph node names, rewrite steps or shapes. One profile applies to every size of the family.

`batching`: [Batching](batching.md). `batch_artifacts`: [Sizes and artifacts](sizes-and-artifacts.md#sizessizeonnxbatch_artifacts).

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `profile_id` | string | yes | The name of a profile that this section defines. See [Profiles](#profiles). |
| `source_batch_size` | int | yes | The native batch of the source artifact. The string form of the value (for example `"2"`) is a key of `sizes.<size>.onnx.batch_artifacts`. |

## Profiles

### `static-batch-v1`

The profile changes the batch of a graph that has the batch as a fixed value. `S` is `source_batch_size`. `T` is the target batch.

Conditions on the source graph:
- Every graph input that is not an initializer has a static dim 0 that equals `S`.
- No initializer uses external data.

Conditions on the request:
- `T` is `1` or larger.

Steps, in this order:
1. `metadata_batch`. If the ONNX metadata has the key `batch` with the value `S`, change the value to `T`. If the metadata key `args` holds a dict with `batch: S`, change it to `T`. If neither key is present, do nothing.
2. `leading_dim`. For each graph input that is not an initializer, each graph output and each `value_info` entry: if dim 0 equals `S`, change it to `T`. Do not change other dims.
3. `int64_shape_first_dim`. For each 1-D `int64` tensor with 2 or more values, in the initializers and in the tensor attributes of nodes: if the first value equals `S`, change it to `T`.

Check, after the steps:
1. The graph passes `onnx.checker.check_model` with `full_check=True`. This runs strict shape inference. The check fails when an inferred shape is different from a stored shape.

Limits: the profile does not change subgraphs (`If`, `Loop`, `Scan`). It does not change a dim or a value that holds the batch in another form. It also changes a dim 0 or a first value that equals `S` but is not the batch. The check finds some of these changes, but not all. The parity check in [Authoring guidance](#authoring-guidance) finds the others.

## Behaviour

1. The host gets a request for batch `T` at size `P` and precision `Q`. If `"T"` is a key of `sizes.P.onnx.batch_artifacts` and its group has precision `Q`, the host must use that artifact. The host does not convert.
2. If the sidecar has no `batching.batch_conversion`, or the host does not support its `profile_id`, the host must use only the native batches.
3. If not, the host can make a generated artifact. The source is `sizes.P.onnx.batch_artifacts."<source_batch_size>".precision_artifacts.Q`. If the source group has no precision `Q`, the host must not convert. The host must verify the source file as [Sizes and artifacts](sizes-and-artifacts.md#sizessizeonnxbatch_artifacts) says, before the conversion. If a condition of the profile is not met, the host must not convert. It must report an error for batch `T`.
4. The host must apply the steps of the profile, in order, and then its check. If the check fails, the host must not use the generated artifact.
5. The generated artifact has the runtime contract of the source artifact at batch `T`. Its input shape is `[T] + input.shape[1:]`. Its output shapes are the `output_shapes` of the source group, with dim 0 changed by step 2 of the profile. When the size has one batch key, `outputs[].shape` replaces `output_shapes`. The generated artifact has no sidecar, no `batch_artifacts` key and no `sha256`.
6. The host can keep a generated artifact in a cache. This spec does not define its file name. A host that reuses a cached artifact must key it by the source `sha256`, `profile_id` and `T`.
7. This spec has no largest batch. The host must report a failure in conversion, session creation, warmup or inference as an error for batch `T`.

## Validation rules

- [ ] `V-common.batch_conversion-1` **(vNEXT)** If `batching.batch_conversion` is present, it must have `profile_id` and `source_batch_size`, and no other key.
- [ ] `V-common.batch_conversion-2` **(vNEXT)** `profile_id` must be a profile that this section defines.
- [ ] `V-common.batch_conversion-3` **(vNEXT)** `source_batch_size` must be an int larger than `1`.
- [ ] `V-common.batch_conversion-4` **(vNEXT)** For each size, `sizes.<size>.onnx.batch_artifacts` must have the key `"<source_batch_size>"`. No size can have the key `dynamic`.

For rules marked **(vNEXT)**, see [Validation rules](../README.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `batching.batch_conversion` | Not available. The key is invalid. | Available. |

## Implementer guidance

- `model_batch_convert` in `skellytracker/core/sessions/batch_conversion.py` implements `static-batch-v1`. It takes a resolved sidecar dict or the `batch_conversion` dict alone. It does not resolve `base` or `$ref`. See [File composition](../format/composition.md).
- The converter does not read external data. It raises `ValueError` for a source with an external-data initializer.
- `static-batch-v1` was measured on the Ultralytics-Exporter yolo26 and yolo26-body nano fp32 exports. The conversions were batch 2 to batch 1 and batch 2 to batch 3. On onnxruntime CPU, the converted outputs equal the native outputs (max abs diff 0.0, seeded random input in [0, 1)). (Measurement 2026-10-28; skellytracker `skellytracker/core/sessions/batch_conversion.py`, onnx 1.22.0, onnxruntime 1.27.0; Ultralytics-Exporter local exports `exports/detectors/object_detectors/yolo26/` and `exports/detectors/keypoint_detectors/yolo26/body/`, made with Ultralytics 8.4.173 and PyTorch 2.12.0, opset 18, not in git)

## Authoring guidance

- Write `batching.batch_conversion` only when the profile passes the parity check for each native batch other than `S`, at each precision of the source group.
- The parity check: convert the source artifact to the native batch `N`. Run the converted artifact and the native artifact on the same seeded random input in [0, 1). The outputs must agree within `rtol=atol=1e-3` for fp16 and `1e-5` for fp32.
- If the group of batch `N` has no precision `Q`, that pair has no parity check.
- A family with only the native batch `S` cannot pass the parity check. Do not write the field for it.
- If no profile passes the parity check, do not write the field. To request a new profile, follow the [model addition workflow](../model-addition-workflow/README.md).
- Ultralytics-Exporter does not write `batching.batch_conversion`. It has its own exporter-side profile (`build_batch_conversion_profile`), not `static-batch-v1`.
  - Its report field `batch_size_converts_successfully` is `True` when the exporter can build its profile (a static source batch above 1). The field is `False` for a batch 1 artifact. It does not record that a conversion ran. (Ultralytics-Exporter `README.md:95-109` (2e0280e), `export_all.py:266-271` (69499e7) and `yolo_sidecar.py:636-702` (f52ef68))
  - The `--test-conversion` check converts a batch 2 export to the batches 1 and 4. It compares the runtime outputs on seeded random input in [0, 1). It uses `rtol=atol=1e-3` for fp16 and `1e-5` for the other precisions. (Ultralytics-Exporter `README.md:35` (f52ef68) and `export_all.py:234-237, 326-349` (69499e7))

## Examples

```yaml
batching:
  batch_axis: 0
  batch_conversion:
    profile_id: static-batch-v1
    source_batch_size: 2
```

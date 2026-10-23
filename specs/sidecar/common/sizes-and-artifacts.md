---
id: common.sizes_and_artifacts
title: Sizes and artifacts
kind: common
since: v2024.09.1019
changed_in: [vNEXT]
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/model.py::SizeSpec  # partial. The checks run only inside resolved_size. No check for V-common.sizes_and_artifacts-3 (notes/decisions/0010-family-invariant.md) or -8. -9 checks only that output_shapes exists.
  load: skellytracker/core/sidecar/model.py::SidecarModel.resolved_size  # partial. Drops every key of a size entry except input and onnx. resolve_model_path in model_registry.py downloads artifacts and checks url_sha256.
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/sidecar/test_runtime.py
  - skellytracker/tests/sidecar/test_model_registry_sidecar_support.py
vectors: null
status: {spec: stable, validate: partial, load: partial}
---

# Sizes and artifacts

## Fields

### `sizes`

The top-level `sizes` map lists every scale of the model in one sidecar.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sizes.<name>.input` | object | yes per size | The input for one size. It can contain **only** `shape` and `resize.target_size`. The first is required, and its batch axis is always `-1`. The second is required when `method` is `letterbox`/`stretch`/`fit`/`affine_person_crop` and `supports_dynamic_size` is not set. |
| `sizes.<name>.onnx` | object | yes per size | The artifacts for one size. `batch_artifacts` is required. |

A size entry can contain only `input` and `onnx` (with the sub-fields above). A size entry deep-merges over the top level. The merge semantics are the same as for [`base`](../format/composition.md#base--inherit-from-another-sidecar-and-override). Any other key in a size entry is invalid. This includes `role`, `outputs`, `batching`, `decode`, `pose`, `overlay`, `input.normalization`, `input.color_format`, `input.resize.method` and other keys. Size names are lowercase tokens such as `nano`, `small` and `medium`. A size name can contain hyphens, for example `l-m` and `x-l`.

**Family invariant.** A family has exactly one contract for preprocessing and post-processing. If two sizes need a different value for any of these items, they belong to **different families** (different sidecars):

- channel order
- normalization
- resize method
- output semantics
- selection mode
- NMS parameters
- class mapping

For example, an RTMDet person-only family and an 80-class RTMDet family are separate families, because their NMS contracts and class counts differ.

When a size declares `target_size`, the spatial dimensions of its `input.shape` must equal it. For `NCHW`, `shape[2:4] == target_size`. For `NHWC`, `shape[1:3] == target_size`. With `supports_dynamic_size: true`, the size omits `target_size`. When no request names a size, the first size in the list is the default. Apart from this default, how a host selects a size or a precision at runtime is out of scope. This spec only declares what is available.

| Contract part | Where it lives |
|---------------|----------------|
| `role`, `outputs`, `input` (except `shape` / `resize.target_size`), `batching` | shared at top level |
| `decode` | top level, when `role` includes `object_detector` |
| `pose`, `overlay` | top level, when `role` includes `pose_estimator` |
| `input.shape`, `input.resize.target_size` (unless `supports_dynamic_size`), `onnx.batch_artifacts` | per size (`sizes.<size>`) |

### `sizes.<size>.onnx.batch_artifacts`

This is a mapping from **native batch size** → artifact group. A sidecar declares it **for each size** under `sizes.<size>.onnx.batch_artifacts`. The keys are **strings**: either a positive integer batch size written as a quoted string, or the literal `dynamic`. This literal means that the model accepts any runtime batch size. Each group contains a `precision_artifacts` map. The map uses the per-precision schema below.

> **YAML authors: quote integer batch keys.** The key set mixes integer-like batch sizes with the string `dynamic`. For this reason, `batch_artifacts` is a string-keyed map (`dict[str, ...]`). Write `"1":`, not `1:`. YAML parses an unquoted key as an integer, and schema validation fails (`Input should be a valid string`).

The full input tensor shape for a group is `[N] + sizes.<size>.input.shape[1:]`. The batch key `N` supplies the batch dimension. The `input.shape` of the size supplies the channels and the spatial dimensions. These are identical across all precisions and batches for that size.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sizes.<size>.onnx.batch_artifacts` | object | yes per size | The keys are quoted positive-integer native batch sizes (`"1"`, `"2"`, …) or a single `dynamic`. A size can list any number of batch keys. |
| `sizes.<size>.onnx.batch_artifacts.<N>.precision_artifacts` | object | yes per group | Each key is `fp32`, `fp16` or `int8`. Each value is the artifact descriptor for native batch `N`. |
| `sizes.<size>.onnx.batch_artifacts.<N>.output_shapes` | array[array] | when `len(batch_artifacts) > 1` | The output tensor shapes for native batch `N`. They follow the order of the top-level `outputs`. |

**Per-precision artifact fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filename` | string | yes | The ONNX filename, relative to the leaf model directory of the sidecar. |
| `url` | string | no | The download location. It can point to an archive, for example `.zip`. |
| `url_sha256` | string | yes when `url` present | The SHA-256 of the bytes at `url`, in lowercase hex. The bytes are the archive or file itself. |
| `input_dtype` | string | no | This optional field is the ONNX graph input element type for this artifact. The default is `input.dtype[precision]`. If the field is authored, its value must agree with that default. |

When the ONNX file is not present locally, the host can download it from `url`. In that case, the host must verify it against `url_sha256`. `url_sha256` is **mandatory** whenever `url` is present. `url` can point directly to an ONNX file, or to an archive. An archive can contain any number of files. It must contain exactly one ONNX file. The host extracts this file and renames it to `filename`. `url` is optional. A model that ships its ONNX files alongside the sidecar needs no download location.

Rules:

- Each size's `batch_artifacts` must have at least one key. Each key is a **string**: a quoted positive integer (`"1"`, `"2"`, …) or `dynamic`. YAML parses an unquoted `1:` as an integer, and validation rejects it.
- A size's `batch_artifacts` can contain integer-like keys **or** a single `dynamic` key, but never both. A mix of `dynamic` with integer keys is a validation error.
- Each group must list at least one precision.
- The precision keys are the closed enum `fp32`, `fp16`, `int8`.
- `batching.native_batch_sizes` is **derived** for each size. Its values are the integer-like keys of `batch_artifacts`, parsed as integers. A `dynamic` key means that any runtime batch size is accepted. It is not a separate field.
- If a precision artifact has an `input_dtype`, it must agree with `input.dtype` for that precision.

The input shape for a group is derived: `[N] + input.shape[1:]`. This is the batch key `N` plus the image shape of the size. When a size lists only one batch key, the top-level `outputs[].shape` can replace the `output_shapes` of each group.

## Behaviour

### Model sizes within a family

A family ships several sizes of the same model. For example, `yolo26` ships `nano`, `small` and `medium`. A single `yolo26.yaml` declares all of them. All sizes share these parts: `role`, `outputs` semantics, `batching`, the input tensor contract (`name`, `dtype`, `layout`, `color_format`, `normalization`, `resize` other than `target_size`), `decode` and `pose`. Only these parts are specific to each size: `input.shape`, `input.resize.target_size` and the ONNX artifacts. Some pose output dimensions depend on the spatial size. These dimensions can vary with the input size, and the host reads them at runtime.

Each size entry deep-merges over the shared top-level contract. It can set only the fields that are specific to a size (see [Sizes](#sizes)). Sizes that need any other difference are a separate family.

## Validation rules

For rules marked **(vNEXT)**, see [Validation rules](../README.md#validation-rules).

- [ ] `V-common.sizes_and_artifacts-1` `sizes` must be present, with at least one size.
- [ ] `V-common.sizes_and_artifacts-2` Each size must declare `input.shape` with `-1` as its batch axis (first dimension).
- [ ] `V-common.sizes_and_artifacts-3` **(vNEXT)** A size entry must contain only `input.shape`, `input.resize.target_size` and `onnx`.
- [ ] `V-common.sizes_and_artifacts-4` If `method` is `letterbox`, `stretch`, `fit` or `affine_person_crop` and `supports_dynamic_size` is not set, the spatial dimensions of each size's `input.shape` must equal its `resize.target_size`. When `method: none` or `supports_dynamic_size: true`, the size must omit `target_size`. When `supports_dynamic_size: true`, the spatial dimensions must be `-1`.
- [ ] `V-common.sizes_and_artifacts-5` The `onnx.batch_artifacts` of each size must use one of two key forms. The first form is quoted-string positive integer batch keys (`"1"`, `"2"`, …). The second form is a single `dynamic` key. It must not mix the two forms. Each group must have a non-empty `precision_artifacts`.
- [ ] `V-common.sizes_and_artifacts-6` The precision keys must be the closed enum `fp32`/`fp16`/`int8`.
- [ ] `V-common.sizes_and_artifacts-7` Each precision artifact must declare `filename`. If it declares `url`, it must also declare `url_sha256`.
- [ ] `V-common.sizes_and_artifacts-8` If a precision artifact has an `input_dtype`, it must agree with `input.dtype[precision]`.
- [ ] `V-common.sizes_and_artifacts-9` When a size has `len(batch_artifacts) > 1`, each group must declare `output_shapes`. The length of that array must equal `len(outputs)`. Its entries must be arrays in the same order as `outputs`.

See also [Input](input.md#validation-rules) and [Outputs](outputs.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| Size-level keys other than `input.shape`, `input.resize.target_size`, `onnx` | Deep-merged over the top level. | Invalid (family invariant). |

## Implementer guidance

## Authoring guidance

## Examples

```yaml
# Excerpt of yolo26.yaml (Ultralytics-Exporter): every YOLO26 size is exported at 640x640;
# sizes differ only in their artifacts. medium/large/xlarge follow the same pattern.
sizes:
  nano:
    input:
      shape: [-1, 3, 640, 640]
      resize:
        target_size: [640, 640]
    onnx:
      batch_artifacts:
        "1":
          precision_artifacts:
            fp32: {filename: yolo26-nano_b1_fp32.onnx}
            fp16: {filename: yolo26-nano_b1_fp16.onnx}
            int8: {filename: yolo26-nano_b1_int8.onnx}
  small:
    input:
      shape: [-1, 3, 640, 640]
      resize:
        target_size: [640, 640]
    onnx:
      batch_artifacts:
        "1":
          precision_artifacts:
            fp32: {filename: yolo26-small_b1_fp32.onnx}
            fp16: {filename: yolo26-small_b1_fp16.onnx}
            int8: {filename: yolo26-small_b1_int8.onnx}
```

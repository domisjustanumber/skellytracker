---
id: common.sizes_and_artifacts
title: Sizes and artifacts
kind: common
---

# Sizes and artifacts

## Fields

### `sizes`

The top-level `sizes` map enumerates every scale of the model in a single sidecar.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sizes.<name>.input` | object | yes per size | Size-specific input. May contain **only** `shape` (required; batch axis always `-1`) and `resize.target_size` (required when `method` is `letterbox`/`stretch`/`fit`/`affine_person_crop` and `supports_dynamic_size` is not set). |
| `sizes.<name>.onnx` | object | yes per size | Size-specific artifacts: `batch_artifacts` (required). |

A size entry may contain only `input` and `onnx` (with the sub-fields above). It is deep-merged over the top level using the same merge semantics as [`base`](../format/composition.md#base--inherit-from-another-sidecar-and-override). Any other key in a size entry — `role`, `outputs`, `batching`, `decode`, `pose`, `overlay`, `input.normalization`, `input.color_format`, `input.resize.method`, and so on — is invalid. Size names are lowercase tokens such as `nano`, `small`, `medium`; hyphens are allowed (e.g. `l-m`, `x-l`).

**Family invariant.** A family has exactly one preprocessing and post-processing contract. If two sizes need a different channel order, normalization, resize method, output semantics, selection mode, NMS parameters, or class mapping, they belong to **different families** (different sidecars). For example, an RTMDet person-only family and an 80-class RTMDet family would be separate families because their NMS contracts and class counts differ.

When `target_size` is declared, the size's `input.shape` spatial dimensions must equal it (for `NCHW`, `shape[2:4] == target_size`; for `NHWC`, `shape[1:3] == target_size`); with `supports_dynamic_size: true`, `target_size` is omitted. The first size listed is the default when no size is requested. How a host selects a size or precision at runtime is otherwise out of scope — this spec only declares what is available.

| Contract part | Where it lives |
|---------------|----------------|
| `role`, `outputs`, `input` (except `shape` / `resize.target_size`), `batching` | shared at top level |
| `decode` | top level, when `role` includes `object_detector` |
| `pose`, `overlay` | top level, when `role` includes `pose_estimator` |
| `input.shape`, `input.resize.target_size` (unless `supports_dynamic_size`), `onnx.batch_artifacts` | per size (`sizes.<size>`) |

### `sizes.<size>.onnx.batch_artifacts`

A mapping from **native batch size** → artifact group, declared **per size** under `sizes.<size>.onnx.batch_artifacts`. Keys are **strings**: either a positive integer batch size written as a quoted string, or the literal `dynamic`, which means the model accepts any runtime batch size. Each group contains a `precision_artifacts` map using the per-precision schema below.

> **YAML authors: quote integer batch keys.** The key set mixes integer-like batch sizes with the string `dynamic`, so `batch_artifacts` is a string-keyed map (`dict[str, ...]`). Write `"1":`, not `1:` — an unquoted key parses as a YAML integer and fails schema validation (`Input should be a valid string`).

The full input tensor shape for a group is `[N] + sizes.<size>.input.shape[1:]` — the batch key `N` supplies the batch dim, and the size's `input.shape` supplies the channels and spatial dims (identical across all precisions and batches for that size).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sizes.<size>.onnx.batch_artifacts` | object | yes per size | String-keyed map: quoted positive-integer native batch sizes (`"1"`, `"2"`, …) or a single `dynamic`. A size may list any number of batch keys. |
| `sizes.<size>.onnx.batch_artifacts.<N>.precision_artifacts` | object | yes per group | Map of `fp32` / `fp16` / `int8` → artifact descriptor for native batch `N`. |
| `sizes.<size>.onnx.batch_artifacts.<N>.output_shapes` | array[array] | when `len(batch_artifacts) > 1` | Output tensor shapes for native batch `N`, parallel to top-level `outputs` order. |

**Per-precision artifact fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filename` | string | yes | ONNX filename relative to the sidecar's leaf model directory. |
| `url` | string | no | Download location. May point to an archive (e.g. `.zip`). |
| `url_sha256` | string | yes when `url` present | Lowercase hex SHA-256 of the bytes at `url` (the archive or file itself). |
| `input_dtype` | string | no | Optional; ONNX graph input element type for this artifact. Defaults to `input.dtype[precision]`; when authored, must agree with it. |

When the ONNX file is not present locally, the host may download it from `url` and must verify it against `url_sha256` — `url_sha256` is **mandatory** whenever `url` is present. `url` may point directly to an ONNX file, or to an archive; an archive may contain any number of files but must contain exactly one ONNX file, which is extracted and renamed to `filename`. `url` is optional — models that ship their ONNX files alongside the sidecar need no download location.

Rules:

- Each size's `batch_artifacts` must have at least one key; each key is a **string** — a quoted positive integer (`"1"`, `"2"`, …) or `dynamic`. Unquoted `1:` parses as an integer and is rejected.
- A size's `batch_artifacts` may contain integer-like keys **or** a single `dynamic` key — never both. Mixing `dynamic` with integer keys is a validation error.
- Each group must list at least one precision.
- Precision keys are the closed enum `fp32`, `fp16`, `int8`.
- `batching.native_batch_sizes` is **derived** per size by parsing the integer-like keys of `batch_artifacts` as integers. A `dynamic` key means any runtime batch size is accepted — it is not a separate field.
- A precision artifact's `input_dtype` (when authored) must agree with `input.dtype` for that precision.

The input shape for a group is derived: `[N] + input.shape[1:]` (batch key `N` + the size's image shape). When a size lists only one batch key, the top-level `outputs[].shape` may be used instead of per-group `output_shapes`.

## Behaviour

### Model sizes within a family

A family ships several sizes of the same model — e.g. `yolo26` ships `nano`, `small`, and `medium` — all declared in a single `yolo26.yaml`. All sizes share `role`, `outputs` semantics, `batching`, the input tensor contract (`name`, `dtype`, `layout`, `color_format`, `normalization`, `resize` other than `target_size`), `decode`, and `pose`. Only `input.shape`, `input.resize.target_size`, and the ONNX artifacts are per size; spatial-dependent pose output dimensions may vary with the input size and are read at runtime.

Each size entry deep-merges over the shared top-level contract and may set only the per-size fields (see [Sizes](#sizes)). Sizes that would need any other difference are a separate family.

## Validation rules

Rules marked **(vNEXT)**: see [Validation rules](../README.md#validation-rules).

- [ ] `V-common.sizes_and_artifacts-1` `sizes` is present with at least one size.
- [ ] `V-common.sizes_and_artifacts-2` Each size declares `input.shape` with `-1` as its batch axis (first dimension).
- [ ] `V-common.sizes_and_artifacts-3` **(vNEXT)** A size entry contains only `input.shape`, `input.resize.target_size`, and `onnx`.
- [ ] `V-common.sizes_and_artifacts-4` Each size's `input.shape` spatial dims equal its `resize.target_size` when `method` is `letterbox`, `stretch`, `fit`, or `affine_person_crop` and `supports_dynamic_size` is not set. `target_size` is omitted when `method: none` or `supports_dynamic_size: true`; spatial dims are `-1` when `supports_dynamic_size: true`.
- [ ] `V-common.sizes_and_artifacts-5` Each size's `onnx.batch_artifacts` has quoted-string positive integer batch keys (`"1"`, `"2"`, …) or a single `dynamic` key (never mixed), and non-empty per-group `precision_artifacts`.
- [ ] `V-common.sizes_and_artifacts-6` Precision keys are the closed enum `fp32`/`fp16`/`int8`.
- [ ] `V-common.sizes_and_artifacts-7` Each precision artifact declares `filename`; when it declares `url`, it also declares `url_sha256`.
- [ ] `V-common.sizes_and_artifacts-8` A precision artifact's `input_dtype` (when authored) agrees with `input.dtype[precision]`.
- [ ] `V-common.sizes_and_artifacts-9` When a size has `len(batch_artifacts) > 1`, each group declares `output_shapes`, whose length equals `len(outputs)` (parallel to `outputs` order) and whose entries are arrays.

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

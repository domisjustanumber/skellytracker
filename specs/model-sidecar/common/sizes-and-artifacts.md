---
id: common.sizes_and_artifacts
title: Sizes and artifacts
kind: common
since: v2024.09.1019
changed_in: [vNEXT]
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/model.py::SizeSpec  # partial. The checks run only inside resolved_size. No check for V-common.sizes_and_artifacts-3 (specs/model-sidecar/decisions/0010-family-invariant.md) or -8. -9 checks only that output_shapes exists. No check for -10 to -12: PrecisionArtifact forbids the key sha256.
  load: skellytracker/core/sidecar/model.py::SidecarModel.resolved_size  # partial. Drops every key of a size entry except input and onnx. resolve_model_path in model_registry.py downloads artifacts and checks url_sha256. Nothing checks sha256 against the file that filename names.
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
| `sizes.<size>.onnx.batch_artifacts.<N>.precision_artifacts` | object | yes per group | Each key is `fp32` or `fp16`. Each value is the artifact descriptor for native batch `N`. |
| `sizes.<size>.onnx.batch_artifacts.<N>.output_shapes` | array[array] | when `len(batch_artifacts) > 1` | The output tensor shapes for native batch `N`. They follow the order of the top-level `outputs`. |

**Per-precision artifact fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filename` | string | yes | The ONNX filename, relative to the leaf model directory of the sidecar. |
| `sha256` | string | `vNEXT`: yes | The SHA-256 of the file that `filename` names, in lowercase hex (64 characters). When `url` points to an archive, `sha256` is the hash of the ONNX file in the archive. |
| `url` | string | no | The download location. It can point to an archive, for example `.zip`. |
| `url_sha256` | string | yes when `url` present | The SHA-256 of the bytes at `url`, in lowercase hex. The bytes are the archive or file itself. |
| `input_dtype` | string | no | This optional field is the ONNX graph input element type for this artifact. The default is `input.dtype[precision]`. If the field is authored, its value must agree with that default. |

When the ONNX file is not present locally, the host can download it from `url`. In that case, the host must verify it against `url_sha256`. `url_sha256` is **mandatory** whenever `url` is present. `url` can point directly to an ONNX file, or to an archive. An archive can contain any number of files. It must contain exactly one ONNX file. The host extracts this file and renames it to `filename`. `url` is optional. A model that ships its ONNX files alongside the sidecar needs no download location.

At `vNEXT`, every artifact has `sha256`, because every artifact has `filename`. `sha256` goes with `filename`, and `url_sha256` goes with `url`. When `url` points to an archive, `url_sha256` is the hash of the archive, and `sha256` is the hash of the ONNX file in it. When `url` points directly to an ONNX file, the two hashes have the same value. The host must verify the file that `filename` names against `sha256` when the file is present. The host must also verify it when the host downloads the file. For a download, the host first verifies the bytes at `url` against `url_sha256`. Then it verifies the ONNX file against `sha256`.

**Reserved placeholder.** The value of 64 zeros (the character `0`, 64 times) is the reserved placeholder for `sha256`. The placeholder is valid only in the reference examples of this spec, under `specs/model-sidecar/examples/`. These examples name ONNX files that nobody can download. An example from an exporter that writes real hashes keeps those hashes. The other examples use the placeholder. A sidecar in any other location that holds the placeholder is invalid.

Rules:

- Each size's `batch_artifacts` must have at least one key. Each key is a **string**: a quoted positive integer (`"1"`, `"2"`, …) or `dynamic`. YAML parses an unquoted `1:` as an integer, and validation rejects it.
- A size's `batch_artifacts` can contain integer-like keys **or** a single `dynamic` key, but never both. A mix of `dynamic` with integer keys is a validation error.
- Each group must list at least one precision.
- The precision keys are the closed enum `fp32`, `fp16`.
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
- [ ] `V-common.sizes_and_artifacts-6` The precision keys must be the closed enum `fp32`/`fp16`.
- [ ] `V-common.sizes_and_artifacts-7` Each precision artifact must declare `filename`. If it declares `url`, it must also declare `url_sha256`.
- [ ] `V-common.sizes_and_artifacts-8` If a precision artifact has an `input_dtype`, it must agree with `input.dtype[precision]`.
- [ ] `V-common.sizes_and_artifacts-9` When a size has `len(batch_artifacts) > 1`, each group must declare `output_shapes`. The length of that array must equal `len(outputs)`. Its entries must be arrays in the same order as `outputs`.
- [ ] `V-common.sizes_and_artifacts-10` **(vNEXT)** Each precision artifact must declare `sha256`. Its value must be a string of 64 lowercase hexadecimal characters.
- [ ] `V-common.sizes_and_artifacts-11` **(vNEXT)** When the file that `filename` names is present or downloaded, its SHA-256 must equal `sha256`.
- [ ] `V-common.sizes_and_artifacts-12` **(vNEXT)** A sidecar outside `specs/model-sidecar/examples/` must not hold the reserved placeholder (64 zeros) as `sha256`.

See also [Input](input.md#validation-rules) and [Outputs](outputs.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| Size-level keys other than `input.shape`, `input.resize.target_size`, `onnx` | Deep-merged over the top level. | Invalid (family invariant). |
| `sha256` of a precision artifact | Not available. Only `url_sha256` (with `url`) gives a hash. | Required on every artifact. |

## Implementer guidance

- The first size is the default, so a loader must keep the YAML mapping order.
  - OpenMMLab-Exporter writes the sizes in alphabetical key order. `rtmdet-person` lists `medium` before `nano`. RTMW lists `l-256`, `l-384`, `m`, `x-256`, `x-384`. RTMO lists `l`, `m`, `s`, `t`. A host that takes the first size gets the alphabetically first size, not the smallest. (OpenMMLab-Exporter `rtmdet_person/sidecar.py:135`, eed3361; local exports `exports/detectors/object_detectors/rtmdet-person/rtmdet-person.yaml`, `.../rtmw/wholebody/rtmw-wholebody.yaml` and `.../rtmo/body7/rtmo-body7.yaml`, not in git)
- `output_shapes` can hold `-1` for an axis that the graph leaves symbolic.
  - OpenMMLab-Exporter reads the dims that one artifact declares for each batch (the `fp16` file when present). It keeps an unknown axis as `-1`. (OpenMMLab-Exporter `rtmo/sidecar.py:170-190`, eed3361)
  - The `dets` output of the real RTMO-M graph has the shape `[1, -1, -1]` at batch 1 and `[2, -1, -1]` at batch 2. Read the concrete dims from the session output. (OpenMMLab-Exporter 0020 `notes/decisions/0020-rtmo-sidecar-contract.md:62-63`, 38ed76f; local export `rtmo-body7.yaml`, not in git)
- The fp16 file is close to the fp32 file in AP.
  - OpenMMLab-Exporter measured the full COCO val2017 person set with RTMDet-person nano and medium at batch 1 to 3. The fp16 AP is 0.000067 to 0.000190 below fp32. The fp32 AP is 0.000023 to 0.000391 above the PyTorch source. Every comparison passed its limit (0.005 or 0.01). (OpenMMLab-Exporter 0035 `notes/decisions/0035-published-artifact-reuse-and-p8-reexport.md:41-52`, c85abf7)
  - The Ultralytics-Exporter fp16 detector AP is within 0.0004 of fp32. Example: nano at batch 2 gives 0.3969 against 0.3971. (Ultralytics-Exporter local reports `exports/detectors/object_detectors/yolo26/yolo26-<size>_b<N>_fp16.report.json` and the fp32 reports, field `performance.converted.ap`, not in git, HEAD 2e0280e)
  - The Roboflow-Exporter README says that the measured change is about +0.002 AP. The only local fp16 report with an accuracy result (nano, batch 1) shows AP 0.48023 against 0.480397 for the PyTorch source (-0.000167). The repo does not reconcile the two. (Roboflow-Exporter `README.md:709-712`, b46b98f; local report `exports/detectors/object_detectors/rfdetr/rfdetr-nano_b1_fp16.onnx.model.report.json`, field `scoring.accuracy.comparisons[0].deltas`, not in git)
  - The Qualcomm-Exporter person detector ran on seeded uniform noise. The fp32 file has a maximum box error of 3.05e-05 px and a maximum score error of 1.54e-07. The fp16 file has 0.1077 px and 6.09e-04. The tolerances are 1.0 px, and 1e-3 (fp32) or 1e-2 (fp16) for the score. (Qualcomm-Exporter local reports `exports/detectors/object_detectors/mediapipe-person-detector/mediapipe-person-detector-default_b1_fp16.report.json` and `..._fp32.report.json`, field `artifact.parity`, not in git; Qualcomm-Exporter `qai_export.py:122-163`, 8d8e05a, and `export_all.py:335`, 4ca4586)
- fp16 can be slower than fp32 on the ONNX Runtime CPU backend. The Qualcomm-Exporter person detector shows this.
  - The fp16 file ran at 57.2 FPS and the fp32 file at 646.3 FPS. The FPS is the median of 50 runs after 5 warm-up runs on the first COCO image, with one run for each file. It is not a device claim. (Qualcomm-Exporter local reports `mediapipe-person-detector-default_b1_fp16.report.json` and `..._fp32.report.json`, field `performance.converted.fps`, not in git; Qualcomm-Exporter `qai_validation.py:26-27, 77-91` and `qai_export.py:106-111`, 4ca4586 and 8d8e05a)
  - The AP differs by 2.5e-06 (0.006849 against 0.006846). The fp16 file is half the size (1,728,070 B against 3,379,390 B). (same local reports, fields `performance.converted.metrics` and `artifact.filesize_bytes`)
- Verify the file that `filename` names against `sha256` when the file is present, and again after a download. Today no code checks `sha256`. `resolve_model_path` does not verify a `local_path` source, and `_resolve_from_url` returns a cached file with no hash check. It checks `url_sha256` only when it downloads the file. (skellytracker `skellytracker/core/sessions/model_registry.py` (`resolve_model_path`, `_resolve_from_url`); decision [0016](../../../decisions/0016-sidecar-catalogs.md#artifact-hashes)) (implementation stage)
- The ONNX download cache for `url` artifacts stays at `~/.cache/skellytracker/models`. It is not a sidecar root, so the catalog does not scan it. (skellytracker `skellytracker/core/sessions/model_registry.py` (`DEFAULT_CACHE_DIR`); decision [0016](../../../decisions/0016-sidecar-catalogs.md#roots)) (implementation stage)
- Git tracks the five package sidecars under `skellytracker/core/detectors/`, in the paths of the [Storage layout](../format/file-layout.md#storage-layout). Git does not track ONNX files. (Decision [0002](../../../decisions/0002-sidecars-tracked-in-package.md))
- `OnnxSession.create` gets each `url` artifact with `resolve_model_path` in `model_registry.py`. The optional argument `expected_filename` gives the cache file the name `filename`. The tail of the URL does not give the name. The optional argument `expected_sha256` checks the downloaded bytes against `url_sha256`. On a mismatch, the function deletes the temporary file, writes nothing to the cache and raises `ModelIntegrityError`. (skellytracker `skellytracker/core/sessions/model_registry.py` (`resolve_model_path`); decision [0002](../../../decisions/0002-sidecars-tracked-in-package.md))
- Do not rely on the code to reject a size entry with other keys. Today `SidecarModel.resolved_size` merges the whole size entry and keeps only `input` and `onnx`. It gives no error for the other keys. (skellytracker `skellytracker/core/sidecar/model.py` (`SidecarModel.resolved_size`); decision [0010](../decisions/0010-family-invariant.md)) (implementation stage)

## Authoring guidance

- Map the upstream input size to `sizes.<size>.input`.
  - mmpose writes `input_size` as (w, h). The RTMW-M codec `input_size = (192, 256)` and the deploy `input_shape = [192, 256]` give `input.shape: [-1, 3, 256, 192]` and `target_size: [256, 192]`. The 384x288 configs write `(288, 384)`. Reverse the pair. A test guards the order. (OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:5`, 491c17b; OpenMMLab-Exporter `tests/test_identities.py:46-54`, eed3361)
  - RTMO body7 `input_size` is `(416, 416)` for size `t` and `(640, 640)` for `s`, `m` and `l`. (OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmo-t_8xb32-600e_body7-416x416.py:52` and `mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py:52`, 6c494a0)
  - RF-DETR has the square resolutions nano 384, small 512, medium 576 and large 704. (Roboflow-Exporter `rf_detr/identity.py:81-86` and `tests/test_sidecar.py:184-203`, 4ae67c0)
  - Ultralytics-Exporter exports at `imgsz=640` and reads the shape from the ONNX input. `input.shape` is `[-1, *graph_input_shape[1:]]` and `target_size` is `graph_input_shape[2:4]`. It raises an error when the spatial dims are not integers. (Ultralytics-Exporter `yolo_sidecar.py:419-430` (f52ef68) and `export_all.py:43, 138-150` (69499e7))
  - Qualcomm-Exporter maps the upstream `get_input_spec` shape `(batch, 3, 128, 128)` to `[-1, 3, 128, 128]` and `[128, 128]`, in one size named `default`. It checks the shape against the upstream spec. (Qualcomm-Exporter `qai_sidecar.py:156-164` and `qai_catalog.py:138-152`, 4ca4586)
- Write the sizes in a deliberate order, because the first size is the default.
  - Roboflow-Exporter writes `nano`, `small`, `medium`, `large`. Ultralytics-Exporter writes `nano`, `small`, `medium`, `large`, `xlarge`. Both use a fixed order and ignore the discovery order, so the default is the smallest size present. (Roboflow-Exporter `rf_detr/identity.py:11` and `tests/test_sidecar.py:184-203`, 4ae67c0; Ultralytics-Exporter `yolo_sidecar.py:36, 280-281`, f52ef68)
  - OpenMMLab-Exporter writes alphabetical order, so the default of its `rtmdet-person` is `medium`. (OpenMMLab-Exporter `rtmdet_person/sidecar.py:135`, eed3361)
- Ultralytics-Exporter maps the weight suffixes `yolo26n`, `yolo26s`, `yolo26m`, `yolo26l` and `yolo26x` to the sizes `nano`, `small`, `medium`, `large` and `xlarge`. For `yolo26-body`, the suffixes are `yolo26n-pose` and so on. (Ultralytics-Exporter `yolo_sidecar.py:175-189`, f52ef68)
- Ultralytics-Exporter maps the precision keys to export arguments.
  - `fp32` has no `quantize`. `fp16` is `quantize=16`. (Ultralytics-Exporter `export_all.py:138-158`, 69499e7)
  - Every export passes `imgsz=640`, `batch=N`, `nms=False` and `max_det=300`. No export is dynamic: the ONNX metadata `args` shows `dynamic: False`. (Ultralytics-Exporter `export_all.py:50-57, 138-150`, 69499e7; local file `exports/detectors/object_detectors/yolo26/yolo26-nano_b2_fp32.onnx`, not in git)
- Rebuild the whole family sidecar after each run, from a scan of the family directory.
  - OpenMMLab-Exporter lists only an artifact that passes `validate_artifact`. It also leaves out an artifact whose accuracy comparison, or that of its parent artifact, failed. (OpenMMLab-Exporter `pipeline/sidecar.py:1-13, 42-77`, 0c7ec77)
  - Roboflow-Exporter does the same. A comparison fails when `abs(delta AP)` is above 0.01. (Roboflow-Exporter `pipeline/sidecar.py:71-119` and `README.md:281-287`, 4ae67c0)
  - Both exporters log a warning for each file that they leave out. (OpenMMLab-Exporter `pipeline/sidecar.py:64-66, 72-73`, 0c7ec77; Roboflow-Exporter `pipeline/sidecar.py:90-91, 102-103`, 4ae67c0)
  - A partial run keeps the sizes, batches and precisions already on disk. `precision_artifacts` lists only the precisions present. (Roboflow-Exporter `tests/test_sidecar.py:206-212, 327-359`, 4ae67c0)
  - An interrupted Ultralytics-Exporter run gives a sidecar with only the artifacts present at that moment. (Ultralytics-Exporter `yolo_sidecar.py:255-277, 615-633`, f52ef68)
- Enforce the family invariant in the writer. See [Decision 0010](../decisions/0010-family-invariant.md).
  - Roboflow-Exporter raises an error when two sizes differ in `num_queries`, `num_class_logits`, `num_select`, the decode background or `confidence_threshold_default`. (Roboflow-Exporter `rf_detr/sidecar.py:95-113` and `tests/test_sidecar.py:251-262`, b34e351)
  - Roboflow-Exporter raises an error when the artifacts disagree on the input name or on the dtype of a precision. (Roboflow-Exporter `rf_detr/sidecar.py:154-172, 220-223` and `tests/test_sidecar.py:239-248`, b34e351)
  - Ultralytics-Exporter checks three things. The input and output batch dims of each artifact equal the batch in the file name. The input has rank 4. All artifacts share the tensor names. It does not compare dtypes or non-batch shapes across sizes. (Ultralytics-Exporter `yolo_sidecar.py:288-339` and `tests/test_yolo_sidecar.py:416-434`, f52ef68)
  - The channel order is a family property. The RGB ConvNeXt-B and Swin-B RTMDet variants needed their own `rtmdet-rgb` family. OpenMMLab-Exporter dropped them with their weights. (OpenMMLab-Exporter 0004 `notes/decisions/0004-channel-order-per-family.md:7-9, 18-19`, c955162)
- Write each batch key as `str(batch)`. PyYAML then quotes the key (`'1':`).
  - The Qualcomm-Exporter test asserts that the keys reload as `["1"]`. (Qualcomm-Exporter `tests/test_qai_sidecar.py:20-52`, 4ca4586)
  - The Roboflow-Exporter test accepts either quote style. (Roboflow-Exporter `tests/test_sidecar.py:215-223`, b34e351)
- Write `output_shapes` for a size with more than one native batch.
  - OpenMMLab-Exporter, Ultralytics-Exporter and Qualcomm-Exporter write `output_shapes` only for such a size. Ultralytics-Exporter takes the shapes from the graph outputs of the first precision. (OpenMMLab-Exporter `rtmo/sidecar.py:179-190`, eed3361; Ultralytics-Exporter `yolo_sidecar.py:402-418`, f52ef68; Qualcomm-Exporter `qai_sidecar.py:79-95`, 4ca4586)
  - Roboflow-Exporter always writes `output_shapes`, also for a single batch key, for example `[[1, 300, 4], [1, 300, 91]]`. (Roboflow-Exporter `rf_detr/sidecar.py:185-196`, b34e351)
  - Ultralytics-Exporter and Qualcomm-Exporter write the smallest native batch in the top-level `outputs[].shape[0]`, and the batch keys of a size can be larger. The spec examples write `-1`. The proposal [0019](../decisions/0019-output-shape-batch-axis.md) covers the batch axis of `outputs[].shape`. (Ultralytics-Exporter `yolo_sidecar.py:342-349, 444-455`, f52ef68; Qualcomm-Exporter `qai_sidecar.py:111-113`, 4ca4586)
- Do not list an `int8` file. The spec has only the precisions `fp32` and `fp16`. The measured int8 files lose much AP.
  - At batch 2, the int8 detector AP is 0.058 to 0.123 below fp32: nano 0.3329, small 0.3487, medium 0.4272, large 0.4391, xlarge 0.5056. (Ultralytics-Exporter local reports `exports/detectors/object_detectors/yolo26/yolo26-<size>_b2_int8.report.json`, field `performance.converted.ap`, not in git, HEAD 2e0280e)
  - At batch 2, the int8 pose OKS AP is 0.109 to 0.203 below fp32. (Ultralytics-Exporter local reports `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body-<size>_b2_int8.report.json`, field `performance.converted.metrics_detail.pose_ap`, not in git, HEAD 2e0280e)
  - Roboflow-Exporter built a static QDQ int8 RF-DETR and removed it. AP went from 0.5953 to 0.4933 (-0.102), and AP50 from 0.7711 to 0.7268. (Roboflow-Exporter `README.md:678-681`, b46b98f)
- Measure each precision against its parent before you list it.
- No exporter writes `url`, `url_sha256` or `input_dtype`.
  - OpenMMLab-Exporter computes the SHA-256 of each file, but it does not write the hash into the sidecar. (OpenMMLab-Exporter `rtmdet_person/sidecar.py:139-145` (eed3361) and `pipeline/sidecar.py:75-76` (0c7ec77))
  - Qualcomm-Exporter keeps the SHA-256 and the size of each ONNX file only in the report (`artifact.sha256`, `artifact.filesize_bytes`). (Qualcomm-Exporter `qai_report.py:99-130`, 4ca4586)
  - The [model addition workflow](../model-addition-workflow/validation-and-publishing.md#source-and-hashes) says that every `filename` artifact carries a `sha256`.
- An fp16 converter can make an invalid graph.
  - The Ultralytics FP16 export can put the input `Cast` node after its consumers. Ultralytics-Exporter sorts the graph again and runs `onnx.checker` after each conversion. (Ultralytics-Exporter `export_all.py:161-188, 227-229`, 69499e7)
  - The ONNX Runtime converter appends the input `Cast` nodes, and `onnxconverter-common` 1.16 made an fp16 graph that ONNX Runtime rejects. Qualcomm-Exporter prefers `onnxruntime.transformers.float16.convert_float_to_float16`, sorts the graph again and runs `onnx.checker`. (Qualcomm-Exporter `qai_export.py:63-103` (8d8e05a) and `tests/test_qai_export.py:32-47` (4ca4586))
- Prove parity on the published bytes.
  - The published fp32 artifact of Roboflow-Exporter is byte-identical to the raw `model.export()` output, and the publish step verifies its SHA-256. (Roboflow-Exporter `pipeline/ARTIFACT_CONTRACT.md:9-18` and `rf_detr/export.py:82-98`, 4ae67c0)
  - The parity numbers of the MediaPipe-Exporter plan are for the raw tf2onnx graphs. A planned edit renames the tensors, reshapes the outputs and makes the batch symbolic after those measurements. This plan fact is the only evidence of this pitfall. (MediaPipe-Exporter plan `plans/hand-pipeline-export.md:189-193, 230-238`, no git repo)

## Examples

```yaml
# Excerpt of yolo26.yaml (Ultralytics-Exporter): every YOLO26 size is exported at 640x640;
# sizes differ only in their artifacts. medium/large/xlarge follow the same pattern.
# The excerpt leaves out the `sha256` of each artifact.
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
```

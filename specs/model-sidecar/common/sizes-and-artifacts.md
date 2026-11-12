---
id: common.sizes_and_artifacts
title: Sizes and artifacts
kind: common
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/model.py::SizeSpec  # partial. The checks run only inside resolved_size. OnnxSpec reads the removed batch_artifacts map, not precision_artifacts and output_shapes (decisions/entries/JAA4-one-batch-field.md). No check for V-common.sizes_and_artifacts-3 (decisions/entries/90CE-minimal-sidecar-contract.md). No check for -8 or -12. No check for -9 to -11: PrecisionArtifact forbids the key sha256.
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
| `sizes.<name>.input` | object | yes per size | The input for one size. It can contain **only** `shape` and `resize.target_size`. The first is required, and its batch axis is always `-1`. The section of the resize `method` tells if the second is present ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)). |
| `sizes.<name>.onnx` | object | yes per size | The artifacts for one size. `precision_artifacts` and `output_shapes` are required ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). |

A size entry can contain only `input.shape`, `input.resize.target_size` and `onnx` (with the sub-fields above). Any other key in a size entry is invalid. This includes `role`, `outputs`, `batching`, `object`, `keypoint`, `input.normalization`, `input.color_format`, `input.resize.method` and other keys. The host does not merge a size entry over the top level. It reads the three fields of the size from the size entry, and each other field from the top level ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)). Size names are lowercase tokens such as `nano`, `small` and `medium`. A size name can contain hyphens, for example `l-m` and `x-l`.

**Family invariant.** A family has exactly one contract for preprocessing and post-processing. If two sizes need a different value for any of these items, they belong to **different families** (different sidecars):

- channel order
- normalization
- resize method
- output semantics
- selection mode
- NMS parameters
- classes

For example, an RTMDet person-only family and an 80-class RTMDet family are separate families, because their NMS contracts and class counts differ. Do not add a size-level override. Make a new family instead ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

When a size declares `target_size`, the spatial dimensions of its `input.shape` must equal it: `shape[2:4] == target_size` ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)). When no request names a size, the first size in the list is the default. Apart from this default, how a host selects a size or a precision at runtime is out of scope. This spec only declares what is available.

| Contract part | Where it lives |
|---------------|----------------|
| `role`, `outputs`, `input` (except `shape` / `resize.target_size`), `batching` | shared at top level |
| `object` | top level, when `role` includes `object_detector` |
| `keypoint` | top level, when `role` includes `keypoint_detector` |
| `input.shape`, `input.resize.target_size`, `onnx.precision_artifacts`, `onnx.output_shapes` | per size (`sizes.<size>`) ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)) |

### `sizes.<size>.onnx`

This object holds the artifacts of one size. Each artifact has the batch that `batching.batch` gives ([Batching](batching.md#fields); [ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). Dim 0 is the batch axis.

The full input tensor shape of an artifact is `[B] + sizes.<size>.input.shape[1:]`. `B` is `batching.batch`. For `dynamic`, `B` is the batch of each run. The `input.shape` of the size supplies the channels and the spatial dimensions. These are the same for all precisions of the size.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sizes.<size>.onnx.precision_artifacts` | object | yes per size | Each key is `fp32` or `fp16`. Each value is the artifact descriptor of that precision ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). |
| `sizes.<size>.onnx.output_shapes` | array[array] | yes per size | The output tensor shapes of the artifacts of the size. There is one entry for each output of the top-level `outputs`, in the same order. Dim 0 of each entry equals `batching.batch`, or is `-1` for `dynamic`. An axis that the graph leaves symbolic stays `-1`. All precisions of the size use these shapes (`V-common.sizes_and_artifacts-8`; [ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). |

**Per-precision artifact fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filename` | string | yes | The ONNX filename, relative to the leaf model directory of the sidecar. |
| `sha256` | string | yes | The SHA-256 of the file that `filename` names, in lowercase hex (64 characters). When `url` points to an archive, `sha256` is the hash of the ONNX file in the archive. |
| `url` | string | no | The download location. It can point to an archive, for example `.zip`. |
| `url_sha256` | string | yes when `url` present | The SHA-256 of the bytes at `url`, in lowercase hex. The bytes are the archive or file itself. |

When the ONNX file is not present locally, the host can download it from `url`. In that case, the host must verify it against `url_sha256`. `url_sha256` is **mandatory** whenever `url` is present. `url` can point directly to an ONNX file, or to an archive. An archive can contain any number of files. It must contain exactly one ONNX file. The host extracts this file and renames it to `filename`. `url` is optional. A model that ships its ONNX files alongside the sidecar needs no download location.

Every artifact has `sha256`, because every artifact has `filename` ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)). `sha256` goes with `filename`, and `url_sha256` goes with `url`. When `url` points to an archive, `url_sha256` is the hash of the archive, and `sha256` is the hash of the ONNX file in it. When `url` points directly to an ONNX file, the two hashes have the same value. The host must verify the file that `filename` names against `sha256` when the file is present. The host must also verify it when the host downloads the file. For a download, the host first verifies the bytes at `url` against `url_sha256`. Then it verifies the ONNX file against `sha256`.

**Reserved placeholder.** The value of 64 zeros (the character `0`, 64 times) is the reserved placeholder for `sha256`. The placeholder is valid only in the reference examples of this spec, under `specs/model-sidecar/examples/`. These examples name ONNX files that nobody can download. An example from an exporter that writes real hashes keeps those hashes. The other examples use the placeholder. A sidecar in any other location that holds the placeholder is invalid.

Rules:

- Each size's `onnx.precision_artifacts` must list at least one precision.
- The precision keys are the closed enum `fp32`, `fp16`.

#### Batch forms

A sidecar has one `batching.batch`. It applies to every size and to every precision ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). These are the three batch forms:

| Form | `batching.batch` | `batching.batch_conversion` |
|------|------------------|-----------------------------|
| b3 (the goal) | `3` | required: `{profile_id: static-batch-v1}` ([Batch conversion](batch-conversion.md)) |
| b1 (a fallback) | `1` | not present |
| `dynamic` (a fallback, or the form of a model that cannot export a static graph) | `dynamic` | not present |

Any other value is invalid, for example `2` or `4`. Other batch sizes are not practical to run in production. The [file name](../format/file-layout.md#file-extension-and-naming) of an artifact has the batch of the form. A `dynamic` file name has no batch segment. A host can make another batch from a b3 artifact with the conversion profile ([Behaviour](batch-conversion.md#behaviour)). The [model addition workflow](../model-addition-workflow/validation-and-publishing.md#publishing) tells which form a family publishes.

### `sizes.<size>.onnx.batch_artifacts`

Removed. Each size has `onnx.precision_artifacts` and `onnx.output_shapes` ([`sizes.<size>.onnx`](#sizessizeonnx); [ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)).

## Behaviour

### Model sizes within a family

A family ships several sizes of the same model. For example, `yolo26` ships `nano`, `small` and `medium`. A single `yolo26.yaml` declares all of them. All sizes share these parts: `role`, `outputs` semantics, `batching`, the input tensor contract (`name`, `dtype`, `color_format`, `normalization`, `resize` other than `target_size`), `object` and `keypoint`. Only these parts are specific to each size: `input.shape`, `input.resize.target_size` and the ONNX artifacts. Some pose output dimensions depend on the spatial size. These dimensions can vary with the input size, and the host reads them at runtime.

The host reads the fields that are specific to a size from the size entry, and each other field from the top level. It does not merge a size entry over the top level ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)). A size entry can set only the fields that are specific to a size (see [Sizes](#sizes)). Sizes that need any other difference are a separate family.

## Validation rules

- [ ] `V-common.sizes_and_artifacts-1` `sizes` must be present, with at least one size.
- [ ] `V-common.sizes_and_artifacts-2` Each size must declare `input.shape` with `-1` as its batch axis (first dimension).
- [ ] `V-common.sizes_and_artifacts-3` A size entry must contain only `input.shape`, `input.resize.target_size` and `onnx`.
- [ ] `V-common.sizes_and_artifacts-4` When a size declares `input.resize.target_size`, the spatial dimensions of its `input.shape` (`shape[2:4]`) must equal it ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).
- [ ] `V-common.sizes_and_artifacts-5` Each size must have a non-empty `onnx.precision_artifacts` ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)).
- [ ] `V-common.sizes_and_artifacts-6` The precision keys must be the closed enum `fp32`/`fp16`.
- [ ] `V-common.sizes_and_artifacts-7` Each precision artifact must declare `filename`. If it declares `url`, it must also declare `url_sha256`.
- [ ] `V-common.sizes_and_artifacts-8` Each size must declare `onnx.output_shapes` ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). The length of that array must equal `len(outputs)`. Its entries must be arrays in the same order as `outputs`. When `outputs[i].shape` is present, entry `i` must have `len(outputs[i].shape)` dims, and each dim `d` with `outputs[i].shape[d] != -1` must equal `outputs[i].shape[d]` or be `-1`. Dim 0 of each entry must equal `batching.batch`. When `batching.batch` is `dynamic`, dim 0 must be `-1`.
- [ ] `V-common.sizes_and_artifacts-9` Each precision artifact must declare `sha256`. Its value must be a string of 64 lowercase hexadecimal characters.
- [ ] `V-common.sizes_and_artifacts-10` When the file that `filename` names is present or downloaded, its SHA-256 must equal `sha256`.
- [ ] `V-common.sizes_and_artifacts-11` A sidecar outside `specs/model-sidecar/examples/` must not hold the reserved placeholder (64 zeros) as `sha256`.
- [ ] `V-common.sizes_and_artifacts-12` The sidecar must use one batch form ([Batch forms](#batch-forms); [ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). `batching.batch` must be present. Its value must be the int `3`, the int `1` or the string `dynamic`. The value `3` is valid only when `batching.batch_conversion` is present.

See also [Input](input.md#validation-rules), [Outputs](outputs.md#validation-rules) and [Batch conversion](batch-conversion.md#validation-rules).

## Implementer guidance

- The first size is the default, so a loader must keep the YAML mapping order.
  - The OpenMMLab-Exporter draft writers of `rtmdet-person` and RTMO write the sizes in alphabetical key order. `rtmdet-person` lists `medium` before `nano`. RTMO lists `l`, `m`, `s`, `t`. A host that takes the first size of such a sidecar gets the alphabetically first size, not the smallest. (OpenMMLab-Exporter [`rtmdet_person/sidecar.py:136`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmdet_person/sidecar.py#L136), [`rtmo/sidecar.py:181`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmo/sidecar.py#L181), [`rtmdet_person/adapter.py:11-12`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmdet_person/adapter.py#L11-L12) and [`rtmo/adapter.py:17-19`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmo/adapter.py#L17-L19); local exports `exports/detectors/object_detectors/rtmdet-person/rtmdet-person.yaml` and `.../rtmo/body7/rtmo-body7.yaml`, not in git)
  - The OpenMMLab-Exporter rtmw writer sorts the sizes by their size rank. It writes `m`, `l-256`, `x-256`, `l-384`, `x-384`. Thus the first size is `m`. (OpenMMLab-Exporter [`rtmw/sidecar.py:237-238`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmw/sidecar.py#L237-L238) and [`rtmw/identity.py:95-151`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmw/identity.py#L95-L151))
- `output_shapes` can hold `-1` for an axis that the graph leaves symbolic.
  - OpenMMLab-Exporter reads the dims that one artifact declares for each batch (the `fp16` file when present). It keeps an unknown axis as `-1`. (OpenMMLab-Exporter [`rtmo/sidecar.py:170-190`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/sidecar.py#L170-L190))
  - The `dets` output of the real RTMO-M graph has the shape `[1, -1, -1]` at batch 1 and `[2, -1, -1]` at batch 2. Read the concrete dims from the session output. (OpenMMLab-Exporter 0020 [`notes/decisions/0020-rtmo-sidecar-contract.md:62-63`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0020-rtmo-sidecar-contract.md#L62-L63); local export `rtmo-body7.yaml`, not in git)
- The fp16 file is close to the fp32 file in AP.
  - OpenMMLab-Exporter measured the full COCO val2017 person set with RTMDet-person nano and medium at batch 1 to 3. The fp16 AP is 0.000067 to 0.000190 below fp32. The fp32 AP is 0.000023 to 0.000391 above the PyTorch source. Every comparison passed its limit (0.005 or 0.01). (OpenMMLab-Exporter 0035 [`notes/decisions/0035-published-artifact-reuse-and-p8-reexport.md:41-52`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c85abf7da34d1e4da7c129f3382173f7153f60fa/notes/decisions/0035-published-artifact-reuse-and-p8-reexport.md#L41-L52))
  - The Ultralytics-Exporter fp16 detector AP is within 0.0004 of fp32. Example: nano at batch 2 gives 0.3969 against 0.3971. (Ultralytics-Exporter local reports `exports/detectors/object_detectors/yolo26/yolo26-<size>_b<N>_fp16.report.json` and the fp32 reports, field `performance.converted.ap`, not in git, HEAD 2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4)
  - The Roboflow-Exporter README says that the measured change is about +0.002 AP. The only local fp16 report with an accuracy result (nano, batch 1) shows AP 0.48023 against 0.480397 for the PyTorch source (-0.000167). The repo does not reconcile the two. (Roboflow-Exporter [`README.md:709-712`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b46b98fa826ffdef46fdfba66c1f8b189a68f8c6/README.md#L709-L712); local report `exports/detectors/object_detectors/rfdetr/rfdetr-nano_b1_fp16.onnx.model.report.json`, field `scoring.accuracy.comparisons[0].deltas`, not in git)
  - The Qualcomm-Exporter person detector ran on seeded uniform noise. The fp32 file has a maximum box error of 3.05e-05 px and a maximum score error of 1.54e-07. The fp16 file has 0.1077 px and 6.09e-04. The tolerances are 1.0 px, and 1e-3 (fp32) or 1e-2 (fp16) for the score. (Qualcomm-Exporter local reports `exports/detectors/object_detectors/mediapipe-person-detector/mediapipe-person-detector-default_b1_fp16.report.json` and `..._fp32.report.json`, field `artifact.parity`, not in git; Qualcomm-Exporter [`qai_export.py:122-163`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/8d8e05a1c210dda5c2a1c4110bd7e4db860844fd/qai_export.py#L122-L163), and [`export_all.py:335`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/export_all.py#L335))
- fp16 can be slower than fp32 on the ONNX Runtime CPU backend. The Qualcomm-Exporter person detector shows this.
  - The fp16 file ran at 57.2 FPS and the fp32 file at 646.3 FPS. The FPS is the median of 50 runs after 5 warm-up runs on the first COCO image, with one run for each file. It is not a device claim. (Qualcomm-Exporter local reports `mediapipe-person-detector-default_b1_fp16.report.json` and `..._fp32.report.json`, field `performance.converted.fps`, not in git; Qualcomm-Exporter [`qai_validation.py:26-27`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_validation.py#L26-L27), [`qai_validation.py:77-91`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_validation.py#L77-L91) and [`qai_export.py:106-111`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/8d8e05a1c210dda5c2a1c4110bd7e4db860844fd/qai_export.py#L106-L111))
  - The AP differs by 2.5e-06 (0.006849 against 0.006846). The fp16 file is half the size (1,728,070 B against 3,379,390 B). (same local reports, fields `performance.converted.metrics` and `artifact.filesize_bytes`)
- Verify the file that `filename` names against `sha256` when the file is present, and again after a download. Today no code checks `sha256`. `resolve_model_path` does not verify a `local_path` source, and `_resolve_from_url` returns a cached file with no hash check. It checks `url_sha256` only when it downloads the file. (skellytracker `skellytracker/core/sessions/model_registry.py` (`resolve_model_path`, `_resolve_from_url`); [ADR-0016](../../../decisions/entries/0016-sidecar-catalogs.md#artifact-hashes)) (implementation stage)
- The ONNX download cache for `url` artifacts stays at `~/.cache/skellytracker/models`. It is not a sidecar root, so the catalog does not scan it. (skellytracker `skellytracker/core/sessions/model_registry.py` (`DEFAULT_CACHE_DIR`); [ADR-0016](../../../decisions/entries/0016-sidecar-catalogs.md#roots)) (implementation stage)
- Git tracks the five package sidecars under `skellytracker/core/detectors/`, in the paths of the [Storage layout](../format/file-layout.md#storage-layout). Git does not track ONNX files. ([ADR-0002](../../../decisions/entries/0002-sidecars-tracked-in-package.md))
- `OnnxSession.create` gets each `url` artifact with `resolve_model_path` in `model_registry.py`. The optional argument `expected_filename` gives the cache file the name `filename`. The tail of the URL does not give the name. The optional argument `expected_sha256` checks the downloaded bytes against `url_sha256`. On a mismatch, the function deletes the temporary file, writes nothing to the cache and raises `ModelIntegrityError`. (skellytracker `skellytracker/core/sessions/model_registry.py` (`resolve_model_path`); [ADR-0002](../../../decisions/entries/0002-sidecars-tracked-in-package.md))

## Authoring guidance

- Map the upstream input size to `sizes.<size>.input`.
  - mmpose writes `input_size` as (w, h). The RTMW-M codec `input_size = (192, 256)` and the deploy `input_shape = [192, 256]` give `input.shape: [-1, 3, 256, 192]` and `target_size: [256, 192]`. The 384x288 configs write `(288, 384)`. Reverse the pair. A test guards the order. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:5`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/491c17b43c0f2011dfd386ab5c6345ef0f850ada/mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py#L5); OpenMMLab-Exporter [`tests/test_identities.py:46-54`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/tests/test_identities.py#L46-L54))
  - RTMO body7 `input_size` is `(416, 416)` for size `t` and `(640, 640)` for `s`, `m` and `l`. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmo-t_8xb32-600e_body7-416x416.py:52`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/6c494a0bcb48acc218b1edd3617b8621b35cc3f4/mmdeploy-convert/model_cfgs/rtmo-t_8xb32-600e_body7-416x416.py#L52) and [`mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py:52`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/6c494a0bcb48acc218b1edd3617b8621b35cc3f4/mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py#L52))
  - RF-DETR has the square resolutions nano 384, small 512, medium 576 and large 704. (Roboflow-Exporter [`rf_detr/identity.py:81-86`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/rf_detr/identity.py#L81-L86) and [`tests/test_sidecar.py:184-203`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/tests/test_sidecar.py#L184-L203))
  - Ultralytics-Exporter exports at `imgsz=640` and reads the shape from the ONNX input. `input.shape` is `[-1, *graph_input_shape[1:]]` and `target_size` is `graph_input_shape[2:4]`. It raises an error when the spatial dims are not integers. (Ultralytics-Exporter [`yolo_sidecar.py:419-430`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L419-L430) and [`export_all.py:43`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/69499e7d292e6f3583ab9429c45a334af3377097/export_all.py#L43), [`export_all.py:138-150`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/69499e7d292e6f3583ab9429c45a334af3377097/export_all.py#L138-L150))
  - Qualcomm-Exporter maps the upstream `get_input_spec` shape `(batch, 3, 128, 128)` to `[-1, 3, 128, 128]` and `[128, 128]`, in one size named `default`. It checks the shape against the upstream spec. (Qualcomm-Exporter [`qai_sidecar.py:156-164`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L156-L164) and [`qai_catalog.py:138-152`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_catalog.py#L138-L152))
- Write the sizes in a deliberate order, because the first size is the default.
  - Roboflow-Exporter writes `nano`, `small`, `medium`, `large`. Ultralytics-Exporter writes `nano`, `small`, `medium`, `large`, `xlarge`. Both use a fixed order and ignore the discovery order, so the default is the smallest size present. (Roboflow-Exporter [`rf_detr/identity.py:11`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/rf_detr/identity.py#L11) and [`tests/test_sidecar.py:184-203`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/tests/test_sidecar.py#L184-L203); Ultralytics-Exporter [`yolo_sidecar.py:36`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L36), [`yolo_sidecar.py:280-281`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L280-L281))
  - The OpenMMLab-Exporter draft writer of `rtmdet-person` writes alphabetical order, so its default is `medium`. (OpenMMLab-Exporter [`rtmdet_person/sidecar.py:136`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmdet_person/sidecar.py#L136))
  - The OpenMMLab-Exporter rtmw writer uses a fixed size rank: `m`, `l-256`, `x-256`, `l-384`, `x-384`. Thus its default is `m`. (OpenMMLab-Exporter [`rtmw/sidecar.py:237-238`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmw/sidecar.py#L237-L238) and [`rtmw/identity.py:95-151`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmw/identity.py#L95-L151))
- Ultralytics-Exporter maps the weight suffixes `yolo26n`, `yolo26s`, `yolo26m`, `yolo26l` and `yolo26x` to the sizes `nano`, `small`, `medium`, `large` and `xlarge`. For `yolo26-body`, the suffixes are `yolo26n-pose` and so on. (Ultralytics-Exporter [`yolo_sidecar.py:175-189`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L175-L189))
- Keep the upstream size name. Add a token when one upstream name has more than one checkpoint.
  - The upstream RTMW size names are `m`, `l` and `x` (the config file names `rtmw-m_…`, `rtmw-l_…` and `rtmw-x_…`). The names `l` and `x` each have two checkpoints, with the inputs 256x192 and 384x288. OpenMMLab-Exporter adds the input height to the name: `l-256`, `x-256`, `l-384` and `x-384`. (OpenMMLab-Exporter [`rtmw/identity.py:47-49`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmw/identity.py#L47-L49) and [`rtmw/identity.py:95-151`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmw/identity.py#L95-L151))
  - Between the RTMW sizes, only `input.shape`, `input.resize.target_size`, the bin counts of `output_shapes` and the artifacts differ. The top-level `outputs` have no `shape`, because the bin counts change with the input size. (OpenMMLab-Exporter [`rtmw/sidecar.py:151-153`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmw/sidecar.py#L151-L153) and [`rtmw/sidecar.py:193-217`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmw/sidecar.py#L193-L217); [`rtmw-wholebody133.yaml`](../examples/detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133.yaml) `sizes`)
- Ultralytics-Exporter maps the precision keys to export arguments.
  - `fp32` has no `quantize`. `fp16` is `quantize=16`. (Ultralytics-Exporter [`export_all.py:138-158`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/69499e7d292e6f3583ab9429c45a334af3377097/export_all.py#L138-L158))
  - Every export passes `imgsz=640`, `batch=N`, `nms=False` and `max_det=300`. No export is dynamic: the ONNX metadata `args` shows `dynamic: False`. (Ultralytics-Exporter [`export_all.py:50-57`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/69499e7d292e6f3583ab9429c45a334af3377097/export_all.py#L50-L57), [`export_all.py:138-150`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/69499e7d292e6f3583ab9429c45a334af3377097/export_all.py#L138-L150); local file `exports/detectors/object_detectors/yolo26/yolo26-nano_b2_fp32.onnx`, not in git)
- Rebuild the whole family sidecar after each run, from a scan of the family directory.
  - OpenMMLab-Exporter lists only an artifact that passes `validate_artifact`. It also leaves out an artifact whose accuracy comparison, or that of its parent artifact, failed. (OpenMMLab-Exporter [`pipeline/sidecar.py:1-13`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/0c7ec77068754d98a9583fa55e957134cb489aed/pipeline/sidecar.py#L1-L13), [`pipeline/sidecar.py:42-77`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/0c7ec77068754d98a9583fa55e957134cb489aed/pipeline/sidecar.py#L42-L77))
  - Roboflow-Exporter does the same. A comparison fails when `abs(delta AP)` is above 0.01. (Roboflow-Exporter [`pipeline/sidecar.py:71-119`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/pipeline/sidecar.py#L71-L119) and [`README.md:281-287`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/README.md#L281-L287))
  - Both exporters log a warning for each file that they leave out. (OpenMMLab-Exporter [`pipeline/sidecar.py:64-66`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/0c7ec77068754d98a9583fa55e957134cb489aed/pipeline/sidecar.py#L64-L66), [`pipeline/sidecar.py:72-73`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/0c7ec77068754d98a9583fa55e957134cb489aed/pipeline/sidecar.py#L72-L73); Roboflow-Exporter [`pipeline/sidecar.py:90-91`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/pipeline/sidecar.py#L90-L91), [`pipeline/sidecar.py:102-103`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/pipeline/sidecar.py#L102-L103))
  - A partial run keeps the sizes, batches and precisions already on disk. `precision_artifacts` lists only the precisions present. (Roboflow-Exporter [`tests/test_sidecar.py:206-212`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/tests/test_sidecar.py#L206-L212), [`tests/test_sidecar.py:327-359`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/tests/test_sidecar.py#L327-L359))
  - An interrupted Ultralytics-Exporter run gives a sidecar with only the artifacts present at that moment. (Ultralytics-Exporter [`yolo_sidecar.py:255-277`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L255-L277), [`yolo_sidecar.py:615-633`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L615-L633))
- Enforce the family invariant in the writer. See [ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md).
  - Roboflow-Exporter raises an error when two sizes differ in `num_queries`, `num_class_logits`, `num_select`, the decode background or `min_score`. (Roboflow-Exporter [`rf_detr/sidecar.py:95-113`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L95-L113) and [`tests/test_sidecar.py:251-262`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/tests/test_sidecar.py#L251-L262))
  - Roboflow-Exporter raises an error when the artifacts disagree on the input name or on the dtype of a precision. (Roboflow-Exporter [`rf_detr/sidecar.py:154-172`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L154-L172), [`rf_detr/sidecar.py:220-223`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L220-L223) and [`tests/test_sidecar.py:239-248`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/tests/test_sidecar.py#L239-L248))
  - Ultralytics-Exporter checks three things. The input and output batch dims of each artifact equal the batch in the file name. The input has rank 4. All artifacts share the tensor names. It does not compare dtypes or non-batch shapes across sizes. (Ultralytics-Exporter [`yolo_sidecar.py:288-339`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L288-L339) and [`tests/test_yolo_sidecar.py:416-434`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/tests/test_yolo_sidecar.py#L416-L434))
  - The channel order is a family property. The RGB ConvNeXt-B and Swin-B RTMDet variants needed their own `rtmdet-rgb` family. OpenMMLab-Exporter dropped them with their weights. (OpenMMLab-Exporter 0004 [`notes/decisions/0004-channel-order-per-family.md:7-9`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c955162d91998b94fc52d932ab6623a9f2a89a1f/notes/decisions/0004-channel-order-per-family.md#L7-L9), [`notes/decisions/0004-channel-order-per-family.md:18-19`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c955162d91998b94fc52d932ab6623a9f2a89a1f/notes/decisions/0004-channel-order-per-family.md#L18-L19))
- Write `output_shapes` in each size (`V-common.sizes_and_artifacts-8`). Read the dims from the graph of the artifact. Today some exporters write it only in some sizes.
  - The OpenMMLab-Exporter draft writers of `rtmdet-person` and RTMO, Ultralytics-Exporter and Qualcomm-Exporter write `output_shapes` only for a size with more than one native batch. In this revision, a sidecar has one `batching.batch` for all sizes, so their rule writes no `output_shapes` for it. Ultralytics-Exporter takes the shapes from the graph outputs of the first precision. (OpenMMLab-Exporter [`rtmdet_person/sidecar.py:149-151`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmdet_person/sidecar.py#L149-L151) and [`rtmo/sidecar.py:193-195`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmo/sidecar.py#L193-L195); Ultralytics-Exporter [`yolo_sidecar.py:402-418`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L402-L418); Qualcomm-Exporter [`qai_sidecar.py:79-95`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L79-L95))
  - Roboflow-Exporter always writes `output_shapes`, also for a size with one batch, for example `[[1, 300, 4], [1, 300, 91]]`. (Roboflow-Exporter [`rf_detr/sidecar.py:185-196`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L185-L196))
  - The OpenMMLab-Exporter rtmw writer writes `output_shapes` in each size. The pipeline reads the shapes from the graph of each artifact. The writer refuses a size whose precisions have different shapes. (OpenMMLab-Exporter [`pipeline/sidecar.py:105-117`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/pipeline/sidecar.py#L105-L117), [`pipeline/sidecar.py:157-159`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/pipeline/sidecar.py#L157-L159) and [`rtmw/sidecar.py:198-214`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmw/sidecar.py#L198-L214); [`rtmw-wholebody133.yaml`](../examples/detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133.yaml) `sizes`)
  - Ultralytics-Exporter and Qualcomm-Exporter write the smallest native batch in the top-level `outputs[].shape[0]`, and an artifact can have a larger batch. The spec examples write `-1`. (Ultralytics-Exporter [`yolo_sidecar.py:342-349`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L342-L349), [`yolo_sidecar.py:444-455`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L444-L455); Qualcomm-Exporter [`qai_sidecar.py:111-113`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L111-L113))
- Do not list an `int8` file. The spec has only the precisions `fp32` and `fp16`. The measured int8 files lose much AP.
  - At batch 2, the int8 detector AP is 0.058 to 0.123 below fp32: nano 0.3329, small 0.3487, medium 0.4272, large 0.4391, xlarge 0.5056. (Ultralytics-Exporter local reports `exports/detectors/object_detectors/yolo26/yolo26-<size>_b2_int8.report.json`, field `performance.converted.ap`, not in git, HEAD 2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4)
  - At batch 2, the int8 pose OKS AP is 0.109 to 0.203 below fp32. (Ultralytics-Exporter local reports `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body-<size>_b2_int8.report.json`, field `performance.converted.metrics_detail.pose_ap`, not in git, HEAD 2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4)
  - Roboflow-Exporter built a static QDQ int8 RF-DETR and removed it. AP went from 0.5953 to 0.4933 (-0.102), and AP50 from 0.7711 to 0.7268. (Roboflow-Exporter [`README.md:678-681`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b46b98fa826ffdef46fdfba66c1f8b189a68f8c6/README.md#L678-L681))
- Measure each precision against its parent before you list it.
- No exporter writes `url` or `url_sha256`.
  - OpenMMLab-Exporter computes the SHA-256 of each file. The rtmw writer writes it as the `sha256` of each artifact. Before the write, the pipeline compares each `sha256` with the SHA-256 of its file. (OpenMMLab-Exporter [`pipeline/sidecar.py:157-159`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/pipeline/sidecar.py#L157-L159), [`rtmw/sidecar.py:210-213`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmw/sidecar.py#L210-L213) and [`pipeline/sidecar.py:343-350`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/pipeline/sidecar.py#L343-L350))
  - The `rtmdet-person` draft writer also writes `sha256`. The RTMO draft writer writes only `filename`. (OpenMMLab-Exporter [`rtmdet_person/sidecar.py:141-146`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmdet_person/sidecar.py#L141-L146) and [`rtmo/sidecar.py:186-190`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmo/sidecar.py#L186-L190))
  - Qualcomm-Exporter keeps the SHA-256 and the size of each ONNX file only in the report (`artifact.sha256`, `artifact.filesize_bytes`). (Qualcomm-Exporter [`qai_report.py:99-130`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_report.py#L99-L130))
  - The [model addition workflow](../model-addition-workflow/validation-and-publishing.md#source-and-hashes) says that every `filename` artifact carries a `sha256`.
- An fp16 converter can make an invalid graph.
  - The Ultralytics FP16 export can put the input `Cast` node after its consumers. Ultralytics-Exporter sorts the graph again and runs `onnx.checker` after each conversion. (Ultralytics-Exporter [`export_all.py:161-188`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/69499e7d292e6f3583ab9429c45a334af3377097/export_all.py#L161-L188), [`export_all.py:227-229`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/69499e7d292e6f3583ab9429c45a334af3377097/export_all.py#L227-L229))
  - The ONNX Runtime converter appends the input `Cast` nodes, and `onnxconverter-common` 1.16 made an fp16 graph that ONNX Runtime rejects. Qualcomm-Exporter prefers `onnxruntime.transformers.float16.convert_float_to_float16`, sorts the graph again and runs `onnx.checker`. (Qualcomm-Exporter [`qai_export.py:63-103`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/8d8e05a1c210dda5c2a1c4110bd7e4db860844fd/qai_export.py#L63-L103) and [`tests/test_qai_export.py:32-47`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/tests/test_qai_export.py#L32-L47))
- Prove parity on the published bytes.
  - The published fp32 artifact of Roboflow-Exporter is byte-identical to the raw `model.export()` output, and the publish step verifies its SHA-256. (Roboflow-Exporter [`pipeline/ARTIFACT_CONTRACT.md:9-18`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/pipeline/ARTIFACT_CONTRACT.md#L9-L18) and [`rf_detr/export.py:82-98`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/rf_detr/export.py#L82-L98))
  - The parity numbers of the MediaPipe-Exporter plan are for the raw tf2onnx graphs. A planned edit renames the tensors, reshapes the outputs and makes the batch symbolic after those measurements. This plan fact is the only evidence of this pitfall. (the untracked hand pipeline plan of MediaPipe-Exporter (secondary))

## Examples

```yaml
# Excerpt of yolo26.yaml (Ultralytics-Exporter): every YOLO26 size is exported at 640x640;
# sizes differ only in their artifacts. medium/large/xlarge follow the same pattern.
# The excerpt leaves out the `sha256` of each artifact.
batching:
  batch: 1
sizes:
  nano:
    input:
      shape: [-1, 3, 640, 640]
      resize:
        target_size: [640, 640]
    onnx:
      precision_artifacts:
        fp32: {filename: yolo26-nano_b1_fp32.onnx}
        fp16: {filename: yolo26-nano_b1_fp16.onnx}
      output_shapes:
        - [1, 300, 6]
  small:
    input:
      shape: [-1, 3, 640, 640]
      resize:
        target_size: [640, 640]
    onnx:
      precision_artifacts:
        fp32: {filename: yolo26-small_b1_fp32.onnx}
        fp16: {filename: yolo26-small_b1_fp16.onnx}
      output_shapes:
        - [1, 300, 6]
```

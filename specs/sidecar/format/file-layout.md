---
id: format.file_layout
title: File layout
kind: format
since: v2024.09.1019
changed_in: []
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/loader.py::load_sidecar  # partial. Checks that model_id matches the file name. No check for sidecar discovery, folder layout or shared fragments.
  load: skellytracker/core/sidecar/loader.py::_default_cache_dir  # partial. Finds the ancestor folder named core. Does not read the folder layout.
external_impl: []
tests: [skellytracker/tests/sidecar/test_yolox_sidecar.py]
vectors: null
status: {spec: stable, validate: partial, load: partial}
---

# File layout

## Behaviour

### File extension and naming

A sidecar uses the `.yaml` extension. The filename is **`{model_id}.yaml`**. The `model_id` field inside the file matches the basename.

| Artifact | Example |
|----------|---------|
| Sidecar (one per family) | `yolo26.yaml` |
| ONNX models (any size × batch × precision) | `yolo26-nano_b2_fp16.onnx`, `yolo26-small_b4_fp32.onnx` |

An ONNX filename gives the size, the batch and the precision: `{model_id}-{size}_{batch}_{precision}.onnx`. For example, in `yolo26-nano_b2_fp32.onnx`, `{batch}` is `b2`. For a `dynamic` batch, the filename omits the batch component: `{model_id}-{size}_{precision}.onnx`. For example, `rtmw-wholebody-l-m_fp32.onnx`.

### Style conventions

- The file has the document marker `---` at the top.
- Comments use the `#` prefix.
- The file uses YAML mappings and sequences. It has no trailing commas. Bare strings have no quotes.
- The top-level keys are flat. Nested objects use indentation.
- A string value has quotes only when quotes are necessary.

### Storage layout

A sidecar and its ONNX files are under a model cache directory (`{cache_dir}`). The default is `skellytracker/core`. The layout follows the detector taxonomy:

```text
{cache_dir}/
  detectors/
    calibration_detectors/          # calibration targets (e.g. Charuco boards) — hard-coded, not sidecar-defined
    object_detectors/
      {family}/                     # role: object_detector
        {model_id}.yaml
        {model_id}-{size}_{batch}_{precision}.onnx
    keypoint_detectors/
      {family}/                     # role: pose_estimator
        hand/
          {model_id}.yaml
          {model_id}-{size}_{batch}_{precision}.onnx
        face/
          {model_id}.yaml
          ...
        body/
          {model_id}.yaml
          ...
        wholebody/
          {model_id}.yaml
          {model_id}-{size}_{batch}_{precision}.onnx
    shared/                         # optional $ref fragments (no schema_version)
      skeletons/                    # tracked-point lists and skeletons
      class_ids/                    # class_id_map fragments (e.g. coco91.yaml)
```

| Branch | Role | Contents |
|--------|------|----------|
| `detectors/calibration_detectors/` | calibration | Calibration detectors, for example Charuco boards. They are hard-coded in skellytracker. Sidecars do **not** specify them. |
| `detectors/object_detectors/{family}/` | `object_detector` | One sidecar for each family, for example `yolo26/`. |
| `detectors/keypoint_detectors/{family}/{part}/` | `pose_estimator` | Keypoint models for each body region: `hand`, `face`, `body` and `wholebody`. |
| `detectors/shared/` | — | Shared `$ref` fragments. This branch is optional. The fragments carry no `schema_version`. |

```text
detectors/object_detectors/yolo26/
  yolo26.yaml
  yolo26-nano_b2_fp32.onnx
  yolo26-nano_b2_fp16.onnx
  yolo26-small_b2_fp32.onnx

detectors/keypoint_detectors/rtmw/wholebody/
  rtmw-wholebody.yaml
  rtmw-wholebody-l-m_fp32.onnx
  rtmw-wholebody-x-l_fp32.onnx
```

### File pairing rules

- A sidecar and its ONNX files are together in the leaf model directory (see [Storage layout](#storage-layout)).
- **Fragment files** are shared sections that a `$ref` pulls in. A fragment file is a plain YAML value: a mapping, a sequence or a scalar. It carries **no** `schema_version`. By convention, keep fragment files under `detectors/shared/`.
- **Base files** are the files that `base` references. A base file is an ordinary sidecar (`{model_id}.yaml`). A derived file that declares `base` is itself another `{model_id}.yaml`. The derived file must override `model_id`, so that its basename matches its own `model_id`. It must also override `schema_version`.

## Validation rules

See [Identity](../common/identity.md#validation-rules) and [File composition](composition.md#validation-rules).

## Implementer guidance

- A reader must resolve YAML anchors and aliases.
  - `yaml.safe_dump` writes a repeated value as an anchor and an alias. The generated `yolo26-body.yaml` has `shape: &id001 [1, 300, 57]` at line 16 and `shape: *id001` at line 22. `yaml.safe_load` resolves both. (Ultralytics-Exporter local export `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body.yaml:16, 22`, not in git, HEAD 2e0280e; Ultralytics-Exporter `yolo_sidecar.py:605`, f52ef68)
  - Qualcomm-Exporter turns aliases off in its dumper (`ignore_aliases` returns `True`). It writes the shared dtype map in full under `input` and under `outputs`. (Qualcomm-Exporter `qai_sidecar.py:19-21, 62-71`, 4ca4586)

## Authoring guidance

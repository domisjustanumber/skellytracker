---
id: format.file_layout
title: File layout
kind: format
since: v2024.09.1019
changed_in: [vNEXT]
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/loader.py::load_sidecar  # partial. Checks that model_id matches the file name. No check for sidecar discovery, folder layout or shared fragments.
  load: skellytracker/core/sidecar/loader.py::_default_cache_dir  # partial. Finds the ancestor folder named core (the package root). No other sidecar root and no discovery. Does not read the folder layout.
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

A sidecar and its ONNX files are under a sidecar root (`{sidecar_root}`, see [Sidecar roots](#sidecar-roots)). The package root is `skellytracker/core`. The layout follows the detector taxonomy:

```text
{sidecar_root}/
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

### Sidecar roots

A sidecar root (`{sidecar_root}`) is a folder that holds sidecars, their ONNX files and their fragments. Each sidecar root must follow the [Storage layout](#storage-layout). These folders are sidecar roots:

- the package root, `skellytracker/core`;
- each local folder that a user adds;
- each Hugging Face repo snapshot. The top folder of the snapshot is `{sidecar_root}`.

A sidecar root has no index file. The [discovery rule](#discovery) finds the sidecars in a root. A folder in which a host keeps the downloaded `url` artifacts is not a sidecar root.

A `$ref` target or a `base` target stays inside the root of the file that refers to it (`V-format.composition-6`). The resolver reads each target from that same root (see [File composition](composition.md#ref--reference-another-file-for-any-value)).

### Discovery

In each sidecar root, a `.yaml` file is a sidecar when its top level has both of these keys:

- `schema_version`;
- `model_id`, with a value that is equal to the file name without `.yaml`.

Every other YAML file is not a sidecar. Such a file is a fragment, or it is not part of the format. Examples are skeleton fragments, canonical mappings and MediaPipe point lists. A fragment has no `schema_version` (see [File pairing rules](#file-pairing-rules)), so the discovery rule never finds a fragment.

## Validation rules

See [Identity](../common/identity.md#validation-rules) and [File composition](composition.md#validation-rules).

## Implementer guidance

- The code still names the sidecar root `cache_dir` until the implementation stage renames it. Examples are the `cache_dir` argument of `load_sidecar`, `_default_cache_dir` and `_require_within_cache_dir`. (skellytracker `skellytracker/core/sidecar/loader.py` (`load_sidecar`, `_default_cache_dir`) and `skellytracker/core/sidecar/resolution.py` (`resolve_sidecar_composition`, `_require_within_cache_dir`))
- A reader must resolve YAML anchors and aliases.
  - `yaml.safe_dump` writes a repeated value as an anchor and an alias. The generated `yolo26-body.yaml` has `shape: &id001 [1, 300, 57]` at line 16 and `shape: *id001` at line 22. `yaml.safe_load` resolves both. (Ultralytics-Exporter local export `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body.yaml:16, 22`, not in git, HEAD 2e0280e; Ultralytics-Exporter `yolo_sidecar.py:605`, f52ef68)
  - Qualcomm-Exporter turns aliases off in its dumper (`ignore_aliases` returns `True`). It writes the shared dtype map in full under `input` and under `outputs`. (Qualcomm-Exporter `qai_sidecar.py:19-21, 62-71`, 4ca4586)
- The catalog scans these sidecar roots: the package root `skellytracker/core`, each local folder that the config names and each Hugging Face repo snapshot that the config names. Hugging Face snapshots stay in the Hugging Face cache. (Decision [0016](../../../decisions/0016-sidecar-catalogs.md#roots)) (implementation stage)
- A Hugging Face root is a Hugging Face model repo. The catalog lists the files of the repo through the Hugging Face API. The config gives the repo id and a commit revision. This revision is the pin. An explicit refresh command moves the pin to the head of the default branch. The refresh downloads only the YAML files (`allow_patterns=["*.yaml"]`). At startup, skellytracker reads only the Hugging Face cache. Thus offline use works. The catalog lists a configured repo that has no refresh yet as "not fetched". When a run uses an ONNX file for the first time, the host downloads the file at the pinned revision. Then the host checks the file against its `sha256`. (Decision [0016](../../../decisions/0016-sidecar-catalogs.md#remote-roots)) (implementation stage)
- In the Hugging Face cache, each file under `snapshots/<rev>/` is a symlink to a file in `blobs/`. Do not call `Path.resolve()` on a path in a snapshot. `load_sidecar` calls it today, so the resolved file is `blobs/<hash>`. Then the root check, the `$ref` resolution, the default root and the file name check fail. Resolve the paths inside the snapshot, and do not follow symlinks. As an alternative, download the snapshot to a plain folder (`snapshot_download(local_dir=...)`). Do not test this only on Windows without developer mode. There Hugging Face copies the files and makes no symlinks, so the fault does not show. (skellytracker `skellytracker/core/sidecar/loader.py` (`load_sidecar`) and `skellytracker/core/sidecar/resolution.py` (`resolve_sidecar_composition`); decision [0016](../../../decisions/0016-sidecar-catalogs.md#hugging-face-cache-paths)) (implementation stage)
- A development build of skellytracker loads `vNEXT` sidecars. A development build has a version with a pre-release tag, or an explicit opt-in setting. A release does not load `vNEXT` sidecars. The implementation stage can use a private Hugging Face test repo for `vNEXT` sidecars. This is the only exception to the publishing rule of [Schema versioning](versioning.md#authoring-guidance). (Decision [0016](../../../decisions/0016-sidecar-catalogs.md#development-builds)) (implementation stage)
- A user model is a local folder of sidecars. The user adds the folder, and the catalog scans it as a root. A user can also give one sidecar and its ONNX files in one folder. The catalog scans that folder as a root that holds one sidecar. The ONNX files are next to their sidecar, with the names that `filename` gives. (Decision [0016](../../../decisions/0016-sidecar-catalogs.md#user-models)) (implementation stage)

## Authoring guidance

- The export root of each exporter has the role of `{sidecar_root}`.
  - Roboflow-Exporter writes `<exports>/detectors/object_detectors/rfdetr/rfdetr.yaml` and the ONNX files beside it. It writes the class-id fragment to `<exports>/detectors/shared/class_ids/coco91.yaml`. (Roboflow-Exporter `rf_detr/sidecar.py:34-37, 79-86` and `rf_detr/identity.py:98`, b34e351)
  - OpenMMLab-Exporter writes `detectors/keypoint_detectors/rtmw/wholebody/` and `detectors/object_detectors/rtmdet-person/`. (OpenMMLab-Exporter `tests/test_rtmw.py:73-77`, ba0c087; OpenMMLab-Exporter `rtmdet_person/identity.py:26`, eed3361)
  - Ultralytics-Exporter writes `object_detectors/yolo26/yolo26.yaml` and `keypoint_detectors/yolo26/body/yolo26-body.yaml`. (Ultralytics-Exporter `yolo_sidecar.py:103-107`, f52ef68)
  - Qualcomm-Exporter writes `object_detectors/mediapipe-person-detector/`. (Qualcomm-Exporter `qai_catalog.py:35-42`, 4ca4586)
- Name each ONNX file `{model_id}-{size}_b{batch}_{precision}.onnx`.
  - Examples: `rtmw-wholebody-m_b3_fp32` and `rtmw-wholebody-x-384_b1_fp16`. (OpenMMLab-Exporter `tests/test_rtmw.py:73-77`, ba0c087)
  - Qualcomm-Exporter uses the size name `default` for its one-size family. (Qualcomm-Exporter `qai_catalog.py:38-39`, 4ca4586)
- Each exporter finds its artifacts with a file name pattern, and it skips other files without an error.
  - Roboflow-Exporter matches `rfdetr-(nano|small|medium|large)_b[1-9][0-9]*_(fp32|fp16).onnx`. (Roboflow-Exporter `pipeline/sidecar.py:38-41, 86-92`, 4ae67c0)
  - Qualcomm-Exporter matches `^<model_id>-default_b<N>_(fp32|fp16).onnx$`. (Qualcomm-Exporter `qai_sidecar.py:38-59`, 4ca4586)
  - Ultralytics-Exporter matches `{family}-{size}_b{batch}_{precision}.onnx`. (Ultralytics-Exporter `yolo_sidecar.py:206-211, 255-277`, f52ef68)
  - Each pattern needs a `_b` segment. Thus none of these exporters can list a `dynamic` batch file. (the sources above)
  - Roboflow-Exporter also rejects a graph whose file name differs from the name that it builds from the identity, the batch and the precision. (Roboflow-Exporter `rf_detr/sidecar.py:125-132`, 4ae67c0)
- The YAML emitters differ.
  - OpenMMLab-Exporter calls `yaml.safe_dump` with `explicit_start=True` (a leading `---`), `sort_keys=False` and `width=120`. (OpenMMLab-Exporter `pipeline/sidecar.py:80-82`, 0c7ec77)
  - Qualcomm-Exporter calls `yaml.dump` with a `SafeDumper` subclass and the same three settings. It adds `default_flow_style=None`, so a leaf mapping comes out as `{fp16: float32, fp32: float32}`. (Qualcomm-Exporter `qai_sidecar.py:62-71`, 4ca4586)
  - Roboflow-Exporter uses its own dumper. It writes block style for nested values and flow style for a list or a mapping of scalars. (Roboflow-Exporter `rf_detr/sidecar.py:289-328`, b34e351)
  - OpenMMLab-Exporter writes `schema_version` without quotes (`vNEXT`). The reference examples do not agree on the quotes either. The [decision log](../decisions/README.md#open-work) records this as a spec defect. (OpenMMLab-Exporter local export `exports/detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml:2`, not in git)
- The folder of two kinds of sidecar does not follow the [Storage layout](#storage-layout).
  - OpenMMLab-Exporter writes RTMO to `detectors/keypoint_detectors/rtmo/body7/`. The part folders of the layout are `hand`, `face`, `body` and `wholebody`. Write the RTMO sidecar to the `body` part folder. (OpenMMLab-Exporter `rtmo/identity.py:26-27`, eed3361)
  - The layout assigns `object_detectors/` to the role `object_detector` and `keypoint_detectors/` to the role `pose_estimator`. It names no folder for a sidecar with both roles. Ultralytics-Exporter writes `yolo26-body.yaml` (both roles) to `keypoint_detectors/yolo26/body/`. OpenMMLab-Exporter writes RTMO (both roles) under `keypoint_detectors/rtmo/`. The [model addition workflow](../model-addition-workflow/sidecar-files.md#path) records the gap. (Ultralytics-Exporter `yolo_sidecar.py:24-25, 103-107`, f52ef68; OpenMMLab-Exporter `rtmo/identity.py:26-27`, eed3361)
- Write LF line endings. [Decision 0016](../../../decisions/0016-sidecar-catalogs.md) requires LF, and the [model addition workflow](../model-addition-workflow/validation-and-publishing.md#source-and-hashes) says that a CRLF file fails.
  - Ultralytics-Exporter and Qualcomm-Exporter write the sidecar with `Path.write_text`, which writes CRLF on Windows. Their generated sidecars have a CRLF at the end of every line. (Ultralytics-Exporter `yolo_sidecar.py:632`, f52ef68; Qualcomm-Exporter `qai_sidecar.py:31-35`, 4ca4586; local exports `yolo26.yaml` and `mediapipe-person-detector.yaml`, not in git)
  - OpenMMLab-Exporter and Roboflow-Exporter write through `atomic_write_text` with `newline="\n"`. (OpenMMLab-Exporter `report_core/io.py:31`, HEAD cce619d; Roboflow-Exporter `report_core/io.py:29`, HEAD c64fd2a)

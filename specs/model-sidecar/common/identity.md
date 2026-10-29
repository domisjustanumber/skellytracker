---
id: common.identity
title: Identity
kind: common
since: v2024.09.1019
changed_in: [vNEXT]
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/loader.py::load_sidecar  # partial. load_sidecar checks V-common.identity-1. SidecarModel checks V-common.identity-2 and V-common.identity-3. No code checks V-common.identity-4 to V-common.identity-6: SidecarModel forbids the key source.
  load: skellytracker/core/sidecar/model.py::SidecarModel  # partial. SidecarModel has no source field. No code applies the legacy default of source.
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/sidecar/test_yolox_sidecar.py
vectors: null
status: {spec: stable, validate: partial, load: partial}
---

# Identity

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | The skellytracker release version for which the author wrote the sidecar (see [Schema versioning](../format/versioning.md)). The pattern is `vYYYY.0M.BUILD[-TAG]`. |
| `source` | object | `vNEXT`: yes | The library that wrote the sidecar. The mapping has exactly two fields: `name` and `version`. A legacy sidecar has no `source` (see [Legacy behaviour](#legacy-behaviour)). |
| `source.name` | string | `vNEXT`: yes | The package name of the library that wrote the sidecar. Examples: `openmmlab-exporter` and `skellytracker`. The pattern is `^[a-z0-9]+(-[a-z0-9]+)*$`. |
| `source.version` | string | `vNEXT`: yes | The released version of that library, for example `0.1.0`. |
| `model_id` | string | yes | The model identifier. It matches the sidecar basename. For an object detector, it is the family, for example `yolo26`. For a keypoint detector, it is `{family}-{part}`, for example `rtmw-wholebody`. |
| `display_name` | string | yes | A name that a person can read. |
| `role` | array[enum] | yes | One or both of `object_detector` and `pose_estimator`. Examples: `[object_detector]`, `[pose_estimator]` and `[object_detector, pose_estimator]`. The last example is for a one-stage model such as RTMO or YOLO26-pose. |
| `sizes` | object | yes | A map of size name → size definition (see [Sizes](sizes-and-artifacts.md#sizes)). The map must have at least one size. |

## Validation rules

- [ ] `V-common.identity-1` `model_id` must match the sidecar basename (`{model_id}.yaml`).
- [ ] `V-common.identity-2` `role` must be a non-empty subset of `object_detector`/`pose_estimator`.
- [ ] `V-common.identity-3` The sidecar must have `display_name`, `input` (with `name`) and a non-empty `outputs` array. Each entry of the array must have `name`.
- [ ] `V-common.identity-4` **(vNEXT)** The sidecar must have a top-level `source` mapping. The mapping must have exactly the keys `name` and `version`.
- [ ] `V-common.identity-5` **(vNEXT)** `source.name` must be a non-empty string. `source.version` must be a non-empty string.
- [ ] `V-common.identity-6` **(vNEXT)** `source.name` must match the pattern `^[a-z0-9]+(-[a-z0-9]+)*$`.

For rules marked **(vNEXT)**, see [Validation rules](../README.md#validation-rules).

See also [Outputs](outputs.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `source` | Absent. The default is `{name: skellytracker, version: <schema_version>}`. | Required. |

## Implementer guidance

No exporter evidence yet.

skellytracker (decision 0016):

- The catalog key of a sidecar is `<model_id>@<source.name>`, for example `rtmw-wholebody@openmmlab-exporter`. Do not use `model_id` alone as the key. Two sources can write the same `model_id`. (Decision [0016](../../../decisions/0016-sidecar-catalogs.md#source)) (implementation stage)
- The catalog can find more than one version of one key. Then compare the `source.version` values in PEP 440 order. The newest version wins. The catalog lists the other versions as superseded. (Decision [0016](../../../decisions/0016-sidecar-catalogs.md#source)) (implementation stage)
- A config can pin a version with `<key>==<version>`. A pin wins over the newest version. (Decision [0016](../../../decisions/0016-sidecar-catalogs.md#source)) (implementation stage)
- Two sidecars can have the same key and the same `source.version`, but different file bytes. Then that catalog entry is unavailable. The reason names the paths of the two files. (Decision [0016](../../../decisions/0016-sidecar-catalogs.md#source)) (implementation stage)
- The name `skellytracker` is reserved for the package root. In a different root, a sidecar with `source.name: skellytracker` is unavailable. Thus a user folder cannot silently replace a model that skellytracker ships. (Decision [0016](../../../decisions/0016-sidecar-catalogs.md#source)) (implementation stage)
- A legacy sidecar gets the name `skellytracker` by default (see [Legacy behaviour](#legacy-behaviour)). Thus a legacy sidecar loads only from the package root. In a local folder or a Hugging Face repo, the catalog lists it as unavailable with this reason:

  ```text
  schema_version <v> is older than vNEXT and has no `source`; legacy sidecars load only from the skellytracker package. Regenerate it at vNEXT with a `source` field.
  ```

  (Decision [0016](../../../decisions/0016-sidecar-catalogs.md#source)) (implementation stage)
- One key can be in more than one root. Then the catalog logs the root of the entry that it uses. (Decision [0016](../../../decisions/0016-sidecar-catalogs.md#source)) (implementation stage)
- Each run records three values in its output metadata: the chosen key, its `source.version` and the SHA-256 of the sidecar file. Thus a result names exactly the sidecar that made it. (Decision [0016](../../../decisions/0016-sidecar-catalogs.md#source)) (implementation stage)

## Authoring guidance

- Write the family id as `model_id`. The file basename is the same id. The values in use are `rtmdet-person`, `rtmw-wholebody`, `rtmo-body7`, `rfdetr`, `yolo26`, `yolo26-body` and `mediapipe-person-detector`. (OpenMMLab-Exporter [`rtmdet_person/identity.py:23-26`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmdet_person/identity.py#L23-L26), [`rtmw/identity.py:25-28`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/identity.py#L25-L28) and [`rtmo/identity.py:24-27`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/identity.py#L24-L27); Roboflow-Exporter [`rf_detr/identity.py:10`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/identity.py#L10); Ultralytics-Exporter [`yolo_sidecar.py:22-25`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L22-L25); Qualcomm-Exporter [`qai_catalog.py:49-62`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_catalog.py#L49-L62))
- Do not put a size in the sidecar `model_id`. OpenMMLab-Exporter has a `model_id` for each size, for example `rtmdet-person-nano`. That id names the artifacts and the reports. It does not go into the sidecar. (OpenMMLab-Exporter [`rtmdet_person/identity.py:117`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmdet_person/identity.py#L117), [`rtmdet_person/identity.py:129`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmdet_person/identity.py#L129), [`rtmdet_person/identity.py:146-147`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmdet_person/identity.py#L146-L147) and [`rtmdet_person/sidecar.py:188-199`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmdet_person/sidecar.py#L188-L199))
- Write a `display_name` with no size, batch or precision. The values in use are `RTMDet Person`, `RTMW WholeBody`, `RTMO Body7`, `RF-DETR`, `YOLO26`, `YOLO26 Pose` and `MediaPipe Person Detector`. (OpenMMLab-Exporter [`rtmdet_person/identity.py:24`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmdet_person/identity.py#L24), [`rtmw/identity.py:26`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/identity.py#L26) and [`rtmo/identity.py:25`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/identity.py#L25); Roboflow-Exporter [`rf_detr/sidecar.py:33`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L33); Ultralytics-Exporter [`yolo_sidecar.py:98-101`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L98-L101); Qualcomm-Exporter [`qai_catalog.py:54`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_catalog.py#L54))
- Take `role` from a constant of the family, not from the graph. `yolo26-body` and RTMO have `[object_detector, pose_estimator]`, because one pass gives boxes and keypoints. (Ultralytics-Exporter [`yolo_sidecar.py:589-593`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L589-L593); OpenMMLab-Exporter [`rtmo/sidecar.py:33`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/sidecar.py#L33), [`rtmo/sidecar.py:234`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/sidecar.py#L234))
- OpenMMLab-Exporter writes the id `rtmo-body7`, with a suffix after the part. The MediaPipe-Exporter plan names `mediapipe-hand-landmark` and `mediapipe-hand-recrop`. The Identity text gives `{family}-{part}` and cannot express a suffix. `V-common.identity-1` (the basename equals `model_id`) passes for these ids. (OpenMMLab-Exporter [`rtmo/identity.py:24-27`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/identity.py#L24-L27); the untracked hand pipeline plan of MediaPipe-Exporter (secondary))
- The MediaPipe hand re-crop model has no `role` value that fits. The plans of MediaPipe-Exporter and Qualcomm-Exporter describe it as `role: [pose_estimator]` with two points, `crop_center` and `crop_scale`. (the untracked hand pipeline plan of MediaPipe-Exporter (secondary); the untracked hand pose plan of Qualcomm-Exporter (secondary))
- Qualcomm-Exporter names the component `person_detector`. The upstream class is `PoseDetector` in `qai_hub_models` 0.64.0. (Qualcomm-Exporter [`qai_catalog.py:49-62`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_catalog.py#L49-L62); `qai_hub_models/models/mediapipe_pose/model.py:96`, installed 0.64.0, not in git)
- Write the package name of the library that writes the sidecar as `source.name`. Write the released version of that library as `source.version`. For OpenMMLab-Exporter, the values are `openmmlab-exporter` and `0.1.0`. (Decision [0016](../../../decisions/0016-sidecar-catalogs.md#exporter-impact); OpenMMLab-Exporter [`pyproject.toml:2-3`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/cce619dcfb8acae4ed66c59db935ac8cc0aa5b5b/pyproject.toml#L2-L3))
- A sidecar that a person writes by hand has no writer library. For such a sidecar, write the author's own name as `source.name`, in the pattern of `V-common.identity-6`. Write a version that the author chooses as `source.version`.
- The pattern of `source.name` is the normalized form of a Python package name (PEP 503): lowercase letters and digits, with one `-` between two parts. Thus each package has one spelling. Write this form also when the package metadata has capital letters, `_` or `.`. The package names in use match the pattern: `openmmlab-exporter`, `roboflow-exporter`, `ultralytics-exporter`, `qualcomm-exporter` and `skellytracker`. (OpenMMLab-Exporter [`pyproject.toml:2`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/cce619dcfb8acae4ed66c59db935ac8cc0aa5b5b/pyproject.toml#L2); Roboflow-Exporter [`pyproject.toml:2`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/c64fd2a32a51e29cdbf9b1b31473c8e441839d07/pyproject.toml#L2); Ultralytics-Exporter [`pyproject.toml:2`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4/pyproject.toml#L2); Qualcomm-Exporter [`pyproject.toml:2`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/pyproject.toml#L2); skellytracker `pyproject.toml:9`)
- The version of each of these exporter packages is `0.1.0`. YAML reads `0.1.0` as a string. YAML reads `1.0` as a number, so write such a version in quotes (`"1.0"`). The `--source` option of `tools/sidecar_refs.py` writes the quotes when YAML needs them. (OpenMMLab-Exporter [`pyproject.toml:3`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/cce619dcfb8acae4ed66c59db935ac8cc0aa5b5b/pyproject.toml#L3), Roboflow-Exporter [`pyproject.toml:3`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/c64fd2a32a51e29cdbf9b1b31473c8e441839d07/pyproject.toml#L3), Ultralytics-Exporter [`pyproject.toml:3`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4/pyproject.toml#L3), Qualcomm-Exporter [`pyproject.toml:3`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/pyproject.toml#L3); `tools/sidecar_refs.py` (`_yaml_scalar`))

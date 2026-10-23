---
id: common.identity
title: Identity
kind: common
since: v2024.09.1019
changed_in: []
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/loader.py::load_sidecar  # load_sidecar checks V-common.identity-1. SidecarModel checks V-common.identity-2 and V-common.identity-3.
  load: skellytracker/core/sidecar/model.py::SidecarModel
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/sidecar/test_yolox_sidecar.py
vectors: null
status: {spec: stable, validate: implemented, load: implemented}
---

# Identity

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | The skellytracker release version for which the author wrote the sidecar (see [Schema versioning](../format/versioning.md)). The pattern is `vYYYY.0M.BUILD[-TAG]`. |
| `model_id` | string | yes | The model identifier. It matches the sidecar basename. For an object detector, it is the family, for example `yolo26`. For a keypoint detector, it is `{family}-{part}`, for example `rtmw-wholebody`. |
| `display_name` | string | yes | A name that a person can read. |
| `role` | array[enum] | yes | One or both of `object_detector` and `pose_estimator`. Examples: `[object_detector]`, `[pose_estimator]` and `[object_detector, pose_estimator]`. The last example is for a one-stage model such as RTMO or YOLO26-pose. |
| `sizes` | object | yes | A map of size name → size definition (see [Sizes](sizes-and-artifacts.md#sizes)). The map must have at least one size. |

## Validation rules

- [ ] `V-common.identity-1` `model_id` must match the sidecar basename (`{model_id}.yaml`).
- [ ] `V-common.identity-2` `role` must be a non-empty subset of `object_detector`/`pose_estimator`.
- [ ] `V-common.identity-3` The sidecar must have `display_name`, `input` (with `name`) and a non-empty `outputs` array. Each entry of the array must have `name`.

See also [Outputs](outputs.md#validation-rules).

## Implementer guidance

No exporter evidence yet.

## Authoring guidance

- Write the family id as `model_id`. The file basename is the same id. The values in use are `rtmdet-person`, `rtmw-wholebody`, `rtmo-body7`, `rfdetr`, `yolo26`, `yolo26-body` and `mediapipe-person-detector`. (OpenMMLab-Exporter `rtmdet_person/identity.py:23-26`, `rtmw/identity.py:25-28` and `rtmo/identity.py:24-27`, eed3361; Roboflow-Exporter `rf_detr/identity.py:10`, b34e351; Ultralytics-Exporter `yolo_sidecar.py:22-25`, f52ef68; Qualcomm-Exporter `qai_catalog.py:49-62`, 4ca4586)
- Do not put a size in the sidecar `model_id`. OpenMMLab-Exporter has a `model_id` for each size, for example `rtmdet-person-nano`. That id names the artifacts and the reports. It does not go into the sidecar. (OpenMMLab-Exporter `rtmdet_person/identity.py:117, 129, 146-147` and `rtmdet_person/sidecar.py:188-199`, eed3361)
- Write a `display_name` with no size, batch or precision. The values in use are `RTMDet Person`, `RTMW WholeBody`, `RTMO Body7`, `RF-DETR`, `YOLO26`, `YOLO26 Pose` and `MediaPipe Person Detector`. (OpenMMLab-Exporter `rtmdet_person/identity.py:24`, `rtmw/identity.py:26` and `rtmo/identity.py:25`, eed3361; Roboflow-Exporter `rf_detr/sidecar.py:33`, b34e351; Ultralytics-Exporter `yolo_sidecar.py:98-101`, f52ef68; Qualcomm-Exporter `qai_catalog.py:54`, 4ca4586)
- Take `role` from a constant of the family, not from the graph. `yolo26-body` and RTMO have `[object_detector, pose_estimator]`, because one pass gives boxes and keypoints. (Ultralytics-Exporter `yolo_sidecar.py:589-593`, f52ef68; OpenMMLab-Exporter `rtmo/sidecar.py:33, 234`, eed3361)
- OpenMMLab-Exporter writes the id `rtmo-body7`, with a suffix after the part. The MediaPipe-Exporter plan names `mediapipe-hand-landmark` and `mediapipe-hand-recrop`. The Identity text gives `{family}-{part}` and cannot express a suffix. `V-common.identity-1` (the basename equals `model_id`) passes for these ids. Decision [0025](../../../notes/decisions/0025-model-id-suffix.md) (proposed) records this question. (OpenMMLab-Exporter `rtmo/identity.py:24-27`, eed3361; MediaPipe-Exporter plan `plans/hand-pipeline-export.md:243-250, 281-282, 295`, no git repo)
- The MediaPipe hand re-crop model has no `role` value that fits. The plans of MediaPipe-Exporter and Qualcomm-Exporter describe it as `role: [pose_estimator]` with two points, `crop_center` and `crop_scale`. The [exporter guide](../exporter-guide.md#known-open-items-for-the-exporter-overhaul) lists this gap for the exporter overhaul. (MediaPipe-Exporter plan `plans/hand-pipeline-export.md:105-107, 295`, no git repo; Qualcomm-Exporter plan `plans/hand-pose-export.md:235-240`, not tracked)
- Qualcomm-Exporter names the component `person_detector`. The upstream class is `PoseDetector` in `qai_hub_models` 0.64.0. (Qualcomm-Exporter `qai_catalog.py:49-62`, 4ca4586; `qai_hub_models/models/mediapipe_pose/model.py:96`, installed 0.64.0, not in git)

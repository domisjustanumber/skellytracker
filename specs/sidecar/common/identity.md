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
| `schema_version` | string | yes | skellytracker release version the sidecar was authored against (see [Schema versioning](../format/versioning.md)). Pattern: `vYYYY.0M.BUILD[-TAG]`. |
| `model_id` | string | yes | Model identifier; matches the sidecar basename. For object detectors it is the family (e.g. `yolo26`); for keypoint detectors it is `{family}-{part}` (e.g. `rtmw-wholebody`). |
| `display_name` | string | yes | Human-readable name. |
| `role` | array[enum] | yes | One or both of `object_detector` / `pose_estimator`, e.g. `[object_detector]`, `[pose_estimator]`, or `[object_detector, pose_estimator]` for a one-stage model such as RTMO or YOLO26-pose. |
| `sizes` | object | yes | Map of size name → size definition (see [Sizes](sizes-and-artifacts.md#sizes)). At least one size. |

## Validation rules

- [ ] `V-common.identity-1` `model_id` matches the sidecar basename (`{model_id}.yaml`).
- [ ] `V-common.identity-2` `role` is a non-empty subset of `object_detector`/`pose_estimator`.
- [ ] `V-common.identity-3` `display_name`, `input` (with `name`), and a non-empty `outputs` array (each with `name`) are present.

See also [Outputs](outputs.md#validation-rules).

## Implementer guidance

## Authoring guidance

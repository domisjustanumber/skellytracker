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

## Authoring guidance

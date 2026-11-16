# KY2J — `keypoint.estimator_type` is `top_down` or `bottom_up`

**Status:** absorbed into [`schema.md#fields`](../../specs/model-sidecar/post/keypoint/schema.md#fields), [`schema.md#keypoint-keypoint_detector`](../../specs/model-sidecar/post/keypoint/schema.md#keypoint-keypoint_detector), [`resize-affine-crop.md#validation-rules`](../../specs/model-sidecar/pre/resize-affine-crop.md#validation-rules), [`onnx_model.md#behaviour`](../../specs/pipeline/nodes/onnx_model.md#behaviour), [`onnx_model.md#validation-rules`](../../specs/pipeline/nodes/onnx_model.md#validation-rules), [`test_retired_names.py`](../../tools/tests/test_retired_names.py), 2026-11-16 (user, question R4 of 2026-11-16; PR: pending).

## Decision

1. The sidecar field `keypoint.estimator_type` has two values: `top_down` and `bottom_up`.
2. The values `top_down_single_person` and `top_down_multi_person` are removed, with no alias.
3. A top-down model sees one instance in each crop. A bottom-up model emits all instances in one
   pass.
4. `V-post.keypoint.schema-3` and `V-pre.resize.affine_crop-2` name `top_down`. Their IDs do not
   change.
5. `V-node.onnx_model-2` of the pipeline spec names `top_down`. Its ID does not change.

This entry refines item 2 of [ADR-GKD1](GKD1-estimator-type-says-the-crop.md): a `top_down` model
uses a crop of the image. It does not supersede that entry, and the other rules of that entry stay.

## Reason

- The two person values had the same rules in each section of the spec. The pipeline code read them
  as one value.
- A top-down model of a hand or of an animal must not write "person".
- The field tells how the model works. It does not tell what the model sees.
- Version 2.0.0 is not released, and the spec has no legacy layer
  ([ADR-0QKK](0QKK-no-legacy-layer.md)).

## Consequences

- The example `rtmw-wholebody133` got the new value as a spec-forced edit. Its entry in
  `specs/model-sidecar/inventory.yaml` records the edit. The package sidecar has the same bytes.
- The bytes of that sidecar changed. The built-in pipeline `yolox-rtmw-wholebody` pins the new
  `sidecar_sha256`.
- OpenMMLab-Exporter must write `top_down` at its next export. Each other exporter that writes a
  top-down keypoint sidecar must do the same.
- The old package sidecars and the old loader in `skellytracker/core/sidecar/` keep the old values.
  They are outside the spec, and phase 2 deletes them
  ([ADR-AMJ8](AMJ8-replace-package-onnx-detectors.md)).
- The frozen proposal record `affine-crop-rotated-roi` keeps the old values.

## Alternatives rejected

- Keep the two person values. Two values with one meaning stay, and a model of a hand must write
  "person".
- `top_down_single_instance`. No rule reads the instance count of a crop.

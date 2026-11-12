# GKD1 — `keypoint.estimator_type` says whether a model needs a crop; `keypoint.requires_object_detector` goes

**Status:** accepted, 2026-11-12 (user).

## Decision

1. The sidecar field `keypoint.requires_object_detector` is removed, with no alias.
2. A keypoint model with `keypoint.estimator_type` `top_down_single_person` or
   `top_down_multi_person` uses a crop of the image. A `bottom_up` model uses the full image.
3. The rule `V-post.keypoint.schema-2` is removed. Its number stays unused.
   `V-pre.resize.affine_person_crop-2` reads `keypoint.estimator_type`: a top-down model must declare
   `input.resize.method: affine_person_crop`.
4. In the pipeline spec, a `detector` node with a top-down keypoint model has a `rois` input. A
   node with a `bottom_up` model or an object detector has no `rois` input.
5. The rtmw example loses the field by a forced edit. OpenMMLab-Exporter removes the field on its
   next export. skellytracker does not change the exporter repos.

## Reason

- `V-post.keypoint.schema-2` made the field `true` for each top-down model and `false` for each
  bottom-up model. The field thus repeated `keypoint.estimator_type`, and an exporter had to write
  two fields that cannot differ.
- The name was also wrong for a top-down model whose crop comes from keypoints, not from a detector
  box, for example the MediaPipe hand model. The pipeline spec had chosen the name `requires_roi`
  for it. With no field, no name is necessary.
- [ADR-88WQ](88WQ-sidecar-vocabulary.md) removed this kind of duplicate. Spec version `2.0.0` is
  not released, so the removal costs one regeneration.

## Alternatives rejected

- A rename to `keypoint.requires_roi`: it keeps a field that another field fully sets.
- No change: the pipeline would use a sidecar name that it calls by another name.

## Open work

[open-work.md](../open-work.md)

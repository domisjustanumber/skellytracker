# 17KN — One selection pipeline

**Status:** accepted, 2026-11-02 (user; PR: pending).

## Decision

No decided entry states a rule that this entry changes. Its content commit comes after that of
[ADR-90CE](90CE-minimal-sidecar-contract.md) and before that of the spec-owned version entry, so
revision `1.0` holds it. The workflow side lands as [ADR-0QKK](0QKK-no-legacy-layer.md) item 6 says.

1. **The shared steps, stated once.**
   [Selection behaviour](../../specs/model-sidecar/post/detection-decode.md#selection-behaviour)
   states each step that the three selection modes share: the class mapping (`class_id_map` or
   `class_id_base`, the drop of `-1`, `is_person_only`), the box conversion, `box_scale`, the
   unprojection, the clamp, the size filter and `confidence_threshold_default`. Each mode file
   keeps its own steps, also how it gets the class index, and tells where the shared steps go.
2. **The clamp follows `clamp_boxes`.** `decode.clamp_boxes` stays: a bool with the default `true`.
   In each mode, also in step 6 of `top_k` and of `nms`, the shared step clamps the unprojected
   boxes only when `clamp_boxes` is `true`. A sidecar whose upstream does not clamp declares
   `clamp_boxes: false`, for example the MediaPipe person detector.
3. **The clamp bounds.** The clamp sets each `x` to `[0, W]` and each `y` to `[0, H]`, with `W` and
   `H` the source-image size. Each text that says the spec does not define the bounds goes, also
   its item in the [spec open work](../../specs/model-sidecar/decisions/open-work.md).
4. **The size filter.** The new optional field `decode.min_box_size` is a non-negative number in
   source-image pixels. When it is present, a shared step after the clamp (after the unprojection
   when `clamp_boxes` is `false`) drops each box unless its width and its height are both more
   than `min_box_size`. When it is absent, the step drops no box. A box with zero area also stays.
   A validation clause of `post.det.decode` requires a non-negative number. The field maps
   one-to-one to `min_bbox_size` of mmdet. The text under
   [Authoring guidance](../../specs/model-sidecar/post/selection-nms.md#authoring-guidance) that
   gives `min_bbox_size` no field changes and cites this entry.
5. **No class source.** The host assigns `person_class_id` only through `is_person_only`. Step 3
   of `nms` loses its own assignment. A new rule in
   [Validation rules](../../specs/model-sidecar/post/detection-decode.md#validation-rules): a
   sidecar with no class source (no `class_field` and no `class_logits_output`) must set
   `decode.is_person_only: true`. The open-work item on this class goes.
6. **Vectors and formulas.** The formula of `post_unprojection.py` in `tools/vector_formulas/`
   gets the upper bounds of the clamp and the size filter. Its defect checks of the upper bound
   and of the zero-area box go. `post.unprojection.yaml` gets cases at the upper bound, of a box
   with zero area and of the size filter. `resolve_class` loses
   `assign_person_without_source`. Each `nms` case with no class source (15 of 20) gets
   `is_person_only: true`. A refusal case covers a sidecar without it.

No example changes.

## Reason

- The user decided these points on 2026-11-02.
- Each upstream decoder that clamps uses `[0, W]` and `[0, H]`. The same bounds give the same boxes.
- After the clamp, the exporter decoders and ultralytics keep a box with zero area. mmdet, the
  upstream of RTMDet, drops it (`min_bbox_size=0`). The user decided that the sidecar sets this
  rule.
- Before this entry, only `none` followed `clamp_boxes`. Now each sidecar follows its upstream.
- For a sidecar with no class source, step 3 of `nms` and the field row of `is_person_only` gave
  two results. With `is_person_only: false`, it had no defined class.
- With one text for the shared steps, the three files cannot disagree again.

## Consequences

- mmdet applies `min_bbox_size` before NMS. In `nms` mode, the spec applies `min_box_size` after
  NMS, so a box that the filter drops can suppress another box in NMS and can use a
  `post_nms_top_k` place. This entry does not solve it.
- The RTMDet person example stays valid without `min_box_size`. The value is in the mmdet config,
  not in the ONNX graph, so [ADR-NB5F](NB5F-no-change-classes-and-one-re-export-request.md) item 3
  cannot add it. The rebuild for the re-export request adds it.
- A one-class detector of an object that is not a person has no description. This is a recorded
  gap.
- The package YOLOX sidecar ([ADR-0006](0006-yolox-native-contract.md)) has no class source. Its
  migration ([ADR-NB5F](NB5F-no-change-classes-and-one-re-export-request.md) item 1) adds
  `is_person_only: true`.
- In that rebuild, each exporter checks `clamp_boxes` and `min_box_size`
  against its upstream.

## Evidence

- The clamp lines of the exporter decoders and ultralytics 8.4.184:
  [Implementer guidance](../../specs/model-sidecar/post/detection-decode.md#implementer-guidance).
- mmdet 3.3.0, `BaseDenseHead._bbox_post_process`, clamps, rescales to the original image, keeps a
  box only when `w` and `h` are above `min_bbox_size`, then applies NMS. The RTMDet person config
  sets it to 0
  ([`model_cfgs/rtmdet_nano_320-8xb32_coco-person.py:26`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d2e68d27d2da0a4f22ddd19449df5601dcac87cc/mmdeploy-convert/model_cfgs/rtmdet_nano_320-8xb32_coco-person.py#L26)).
- qai_hub_models 0.64.0, `models/mediapipe_pose/model.py:80`: `FILTER_OOB_BOX = False`.

## Alternatives rejected

- **Always clamp, and delete `clamp_boxes`.** The upstream of the MediaPipe person detector does not
  clamp.
- **The bounds `[0, W - 1]` and `[0, H - 1]`.** No upstream decoder uses them.
- **One zero-area rule for all sidecars.** If the spec keeps the box, it differs from mmdet. If it
  drops the box, it differs from the exporter decoders and ultralytics.
- **Assign `person_class_id` with no class source in each mode.** A detector of other objects then
  gives "person" with no error.

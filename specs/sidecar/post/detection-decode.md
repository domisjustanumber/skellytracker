---
id: post.det.decode
title: Detection decode
kind: postprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors:
  - role=object_detector
implemented_by:
  validate: skellytracker/core/sidecar/model.py::DetectionDecodeSpec  # partial: no selection, output bindings, box_scale, class_id_map, is_person_only or clamp_boxes; max_detections defaults to 300
  decode: skellytracker/core/detectors/object_detectors/yolox/yolox_decode.py::yolox_detection_decode  # partial: the tensor count picks the path, not selection; no box_scale, class_id_map, is_person_only or clamp; the caller gives the thresholds
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/test_object_detection_decode.py
  - skellytracker/tests/test_yolox_detector.py
vectors: null
status: {spec: stable, validate: partial, decode: partial}
---

# Detection decode

## Fields

### `decode` (detection)

Required when `role` includes `object_detector`. It describes how the host turns the detection outputs into final detections in the source image.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `selection` | enum | yes | The value is `none`, `top_k` or `nms`. It sets how candidate rows become final detections (see [Selection behaviour](#selection-behaviour)). |
| `boxes_output` | string | no | The name of the primary `detections`/`boxes` output. The default is the single primary detection output of the sidecar. |
| `scores_output` | string | no | The name of the `scores` output. Do not use it together with `score_field` or `class_logits_output`. |
| `box_format` | enum | no | The value is `xyxy` (default), `xywh` (top-left corner and size) or `cxcywh` (centre and size). It applies to `fields[0:4]` of a `detections` output, or to the four columns of a `boxes` output. |
| `box_scale` | enum | no | The value is `pixel` (default; model-input pixels), `normalized_01` or `normalized_11`. See [Unprojection](unprojection.md). |
| `score_field` | string | conditional | The field that holds the score of each row. It must appear in `fields`. Required for a `detections` primary output, unless the sidecar uses `scores_output`. Invalid for a `boxes` primary output. |
| `class_field` | string | no | The field that holds the class index of each row. It must appear in `fields`. Invalid for a `boxes` primary output. |
| `class_id_base` | int | no | The emitted class id is `class_id_base + model class index`. The default is `0`. If `class_id_map` is present, the host ignores this field. |
| `class_id_map` | array[int] or `$ref` | no | Its length is `C`. The index is the model class index. The value is the emitted class id. The value `-1` means ignore: the host drops the candidates that have that class. This field takes precedence over `class_id_base`. |
| `is_person_only` | bool | no | The default is `false`. When `true`, the model detects only people. In this case, the host assigns `person_class_id` to each candidate that has no class source. In this case, the host also drops each candidate whose resolved class is not `person_class_id`. |
| `person_class_id` | int | no | The emitted class id of "person". The default is `0`. When `class_id_map` is present, this id must be one of the non-negative values of the map. |
| `confidence_threshold_default` | float | no | The default is `0.7`. This is the default final filter of the host. The host applies it after selection. The filter is strict: `score > threshold`. It is host policy, and callers can override it. |
| `clamp_boxes` | bool | no | The default is `true`. Clamp the unprojected boxes to the source-image bounds. |
| `requires_nms` | bool | no | A legacy alias. If it is present, it must agree with `selection`: it is `true` if and only if `selection: nms`. |

Selection-specific fields: [`max_detections`](selection-none.md#fields), [`class_logits_output`, `score_activation`, `top_k`](selection-top-k.md#fields), [`nms`](selection-nms.md#fields).

[Detection output semantics](detection-outputs.md#detection-output-semantics) defines `B`, `Q` and `C`.

## Behaviour

The detection outputs are the **complete candidate set** for the declared `selection`. The host cannot recover a candidate that the graph dropped.

### Selection behaviour

All score comparisons are strict (`>`). For `top_k`, break a tie by ascending flattened index. In any other score ordering, break a tie by ascending row index. For each batch item:

- [Selection: none](selection-none.md#behaviour)
- [Selection: top-k](selection-top-k.md#behaviour)
- [Selection: NMS](selection-nms.md#behaviour)

For a model with both roles, a step that drops a detection row also drops the corresponding pose row. A step that keeps a detection row also keeps the corresponding pose row (see [Bottom-up decode](pose-bottom-up.md#bottom-up-decode)).

## Validation rules

### Detection (`object_detector`)

Rules marked **(vNEXT)**: see [Validation rules](../README.md#validation-rules).

- [ ] `V-post.det.decode-1` If `decode.boxes_output`, `scores_output` or `class_logits_output` is present, it must name an output with the matching semantic. `boxes_output` must name the primary output.
- [ ] `V-post.det.decode-2` If `decode.score_field` or `decode.class_field` is present, it must appear in the `fields` of the primary `detections` output. When the primary output is `boxes`, these two decode fields must be absent. `score_field` and `scores_output` must not both be present. `class_field` and `class_logits_output` must not both be present.
- [ ] `V-post.det.decode-3` A `detections` primary output must have a score source (`score_field` or `scores_output`), unless `selection: top_k`. A `boxes` primary output must have `scores_output` or `class_logits_output`.
- [ ] `V-post.det.decode-4` **(vNEXT)** `decode.selection` must be present. It must be `none`, `top_k` or `nms`. If `requires_nms` is present, it must be `true` if and only if `selection: nms`. `may_include_non_person_classes` must be absent.
- [ ] `V-post.det.decode-5` If `decode.box_format` is present, it must be `xyxy`, `xywh` or `cxcywh`. If `decode.box_scale` is present, it must be `pixel`, `normalized_01` or `normalized_11`. If `decode.score_activation` is present, it must be `none` or `sigmoid`. If `decode.clamp_boxes` or `decode.is_person_only` is present, it must be a boolean.
- [ ] `V-post.det.decode-6` If `decode.class_id_map` is present, its length must be `C` (the class dimension of `class_logits`, or the model class count). Each value must be `-1` or a non-negative integer. The non-negative values must be unique.
- [ ] `V-post.det.decode-7` `decode.class_id_base` and `decode.person_class_id` must be non-negative integers. When `class_id_map` is present, `person_class_id` must be one of its non-negative values. Otherwise `person_class_id >= class_id_base` must be true.
- [ ] `V-post.det.decode-8` If `decode.confidence_threshold_default` is present, it must be in `[0, 1]`.

See also [Detection outputs](detection-outputs.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `decode.selection` | Not authored; derived: `requires_nms: true` → `nms`, otherwise `none`. | Required. `requires_nms`, when present, must agree. |
| `may_include_non_person_classes` | Accepted; `is_person_only = not may_include_non_person_classes` (default `true` → `false`). | Invalid; use `is_person_only`. |
| `clamp_boxes` absent | Existing host behaviour. | Default `true`. |

See also [Selection: none](selection-none.md#legacy-behaviour), [Selection: NMS](selection-nms.md#legacy-behaviour) and [Schema versioning](../format/versioning.md#legacy-behaviour).

## Implementer guidance

## Authoring guidance

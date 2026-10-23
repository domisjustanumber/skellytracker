---
id: post.det.decode
title: Detection decode
kind: postprocessor
---

# Detection decode

## Fields

### `decode` (detection)

Required when `role` includes `object_detector`. Describes how the host turns the detection outputs into final detections in the source image.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `selection` | enum | yes | `none`, `top_k`, or `nms` — how candidate rows become final detections (see [Selection behaviour](#selection-behaviour)). |
| `boxes_output` | string | no | Name of the primary `detections`/`boxes` output; defaults to the sidecar's single primary detection output. |
| `scores_output` | string | no | Name of the `scores` output. Mutually exclusive with `score_field` and `class_logits_output`. |
| `box_format` | enum | no | `xyxy` (default), `xywh` (top-left corner + size), or `cxcywh` (centre + size). Applies to `fields[0:4]` of a `detections` output, or to the four columns of a `boxes` output. |
| `box_scale` | enum | no | `pixel` (default; model-input pixels), `normalized_01`, or `normalized_11` (see [Unprojection](unprojection.md)). |
| `score_field` | string | conditional | Field holding per-row score; must appear in `fields`. Required for a `detections` primary output unless `scores_output` is used. Invalid for a `boxes` primary output. |
| `class_field` | string | no | Field holding per-row class index; must appear in `fields`. Invalid for a `boxes` primary output. |
| `class_id_base` | int | no | Emitted class id = `class_id_base + model class index`; default `0`. Ignored when `class_id_map` is present. |
| `class_id_map` | array[int] or `$ref` | no | Length `C`: index = model class index, value = emitted class id, `-1` = ignore (candidates with that class are dropped). Takes precedence over `class_id_base`. |
| `is_person_only` | bool | no | Default `false`. When `true`, the model detects only people: candidates without a class source are assigned `person_class_id`, and candidates whose resolved class is not `person_class_id` are dropped. |
| `person_class_id` | int | no | Emitted class id of "person"; default `0`. With `class_id_map`, it must be one of the map's non-negative values. |
| `confidence_threshold_default` | float | no | Default `0.7`. The host's default final filter, applied after selection (strict `score > threshold`). Host policy — callers may override it. |
| `clamp_boxes` | bool | no | Default `true`. Clamp unprojected boxes to the source-image bounds. |
| `requires_nms` | bool | no | Legacy alias: when present it must agree with `selection` (`true` iff `selection: nms`). |

Selection-specific fields: [`max_detections`](selection-none.md#fields), [`class_logits_output`, `score_activation`, `top_k`](selection-top-k.md#fields), [`nms`](selection-nms.md#fields).

`B`, `Q` and `C` are defined in [Detection output semantics](detection-outputs.md#detection-output-semantics).

## Behaviour

The detection outputs are the **complete candidate set** for the declared `selection`: the host cannot recover candidates a graph dropped.

### Selection behaviour

All score comparisons are strict (`>`). Ties in any score ordering are broken by ascending row index (ascending flattened index for `top_k`). For each batch item:

- [Selection: none](selection-none.md#behaviour)
- [Selection: top-k](selection-top-k.md#behaviour)
- [Selection: NMS](selection-nms.md#behaviour)

For a model with both roles, every step that drops or keeps a detection row drops or keeps the corresponding pose row (see [Bottom-up decode](pose-bottom-up.md#bottom-up-decode)).

## Validation rules

### Detection (`object_detector`)

Rules marked **(vNEXT)**: see [Validation rules](../README.md#validation-rules).

- [ ] `V-post.det.decode-1` `decode.boxes_output`, `scores_output`, and `class_logits_output` (when present) name an output with the matching semantic; `boxes_output` names the primary output.
- [ ] `V-post.det.decode-2` `decode.score_field` / `decode.class_field` (when present) appear in the primary `detections` output's `fields`, and are absent when the primary output is `boxes`. `score_field` and `scores_output` are not both present; `class_field` and `class_logits_output` are mutually exclusive.
- [ ] `V-post.det.decode-3` A `detections` primary output has a score source (`score_field` or `scores_output`) unless `selection: top_k`; a `boxes` primary output has `scores_output` or `class_logits_output`.
- [ ] `V-post.det.decode-4` **(vNEXT)** `decode.selection` is present and is `none`, `top_k`, or `nms`; `requires_nms` (when present) is `true` iff `selection: nms`; `may_include_non_person_classes` is absent.
- [ ] `V-post.det.decode-5` `decode.box_format` (when present) is `xyxy`, `xywh`, or `cxcywh`; `decode.box_scale` (when present) is `pixel`, `normalized_01`, or `normalized_11`; `decode.score_activation` (when present) is `none` or `sigmoid`; `decode.clamp_boxes` and `decode.is_person_only` (when present) are booleans.
- [ ] `V-post.det.decode-6` `decode.class_id_map` (when present) has length `C` (the class dimension of `class_logits`, or the model's class count), values are `-1` or non-negative integers, and non-negative values are unique.
- [ ] `V-post.det.decode-7` `decode.class_id_base` and `decode.person_class_id` are non-negative integers. With `class_id_map`, `person_class_id` is one of its non-negative values; otherwise `person_class_id >= class_id_base`.
- [ ] `V-post.det.decode-8` `decode.confidence_threshold_default` (when present) is in `[0, 1]`.

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

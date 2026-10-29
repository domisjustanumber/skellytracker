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

- fp16 scores drift by up to 0.04 on confident detections. That can move a detection across a 0.7 threshold without a change in AP. (OpenMMLab-Exporter [`notes/decisions/0011-ap-only-comparison.md:22-23`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/963732e271d13c0c90feb8775374ca2bba422c8d/notes/decisions/0011-ap-only-comparison.md#L22-L23))
- Parity runs do not exercise `confidence_threshold_default`. The accuracy pass of OpenMMLab-Exporter builds the decoder with `confidence_threshold=0.0`, so only `nms.score_threshold` (0.05) filters. Its benchmark builds the decoder without a threshold, so the sidecar default 0.7 applies. (OpenMMLab-Exporter [`pipeline/accuracy.py:436-437`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/ba0c0876b58650ed472559f1a77780e5da13d370/pipeline/accuracy.py#L436-L437), [`pipeline/benchmark.py:315`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/ba0c0876b58650ed472559f1a77780e5da13d370/pipeline/benchmark.py#L315) and [`pipeline/decoders.py:65-73`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/ba0c0876b58650ed472559f1a77780e5da13d370/pipeline/decoders.py#L65-L73))
- Roboflow-Exporter decodes at threshold 0.0 (strict `>`) with `num_select` 300, and its evaluator keeps 100 detections (`max_dets`). Thus its default 0.5 is not exercised. (Roboflow-Exporter [`rf_detr/ACCURACY_CONTRACT.md:57-64`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/rf_detr/ACCURACY_CONTRACT.md#L57-L64); [`rf_detr/coco_format.py:63-65`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/coco_format.py#L63-L65))
- Roboflow-Exporter clips the logits to [-88, 88] before `exp`. It casts the boxes and the logits to float32 for each image. Its fp16 artifacts already have float32 outputs. A host that decodes in float16, or without the clip, can overflow in `exp`. (Roboflow-Exporter [`rf_detr/coco_format.py:67-69`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/coco_format.py#L67-L69), [`rf_detr/coco_format.py:122-123`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/coco_format.py#L122-L123); [`pipeline/ARTIFACT_CONTRACT.md:20-27`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/pipeline/ARTIFACT_CONTRACT.md#L20-L27))
- Do not mix the two -1 conventions. In the decoders of Roboflow-Exporter, a negative `background_class_id` wraps with modulo, so -1 removes logit slot 90 (toothbrush). Its README says to decode with `background_class_id=None`. In `class_id_map`, -1 means "drop this slot". (Roboflow-Exporter [`rf_detr/coco_format.py:19-37`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/coco_format.py#L19-L37); [`README.md:528-534`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b46b98fa826ffdef46fdfba66c1f8b189a68f8c6/README.md#L528-L534))
- The decoders of Roboflow-Exporter never apply `class_id_map`. They emit the logit slot as the category id. They keep the 11 slots that its sidecar maps to -1 (slot 0 and the 10 COCO id gaps). Thus its parity numbers do not cover the drop. (Roboflow-Exporter [`rf_detr/coco_format.py:138-146`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/coco_format.py#L138-L146), [`rf_detr/sidecar.py:89-92`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L89-L92) and [`tests/test_sidecar.py:105`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/tests/test_sidecar.py#L105), [`tests/test_sidecar.py:265-277`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/tests/test_sidecar.py#L265-L277))
- The exporter decoders are partial. Do not port one as a complete decode. The reference decoder of OpenMMLab-Exporter reads only `box_format`, `box_scale`, `score_activation`, `nms.*`, `confidence_threshold_default` (fallback 0.7), `clamp_boxes` and the output names. It never reads `class_id_base`, `person_class_id` or `is_person_only`. It returns the class index of the ONNX NMS (0 for a `[B, Q]` scores tensor). Its scorer maps that index to COCO category 1 with `category_map` `{0: 1}`. (OpenMMLab-Exporter [`onnx_runtime/decode_nms.py:106-130`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d2e68d27d2da0a4f22ddd19449df5601dcac87cc/onnx_runtime/decode_nms.py#L106-L130), [`onnx_runtime/decode_nms.py:163`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d2e68d27d2da0a4f22ddd19449df5601dcac87cc/onnx_runtime/decode_nms.py#L163); [`rtmdet_person/model_report.py:143-145`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/ba0c0876b58650ed472559f1a77780e5da13d370/rtmdet_person/model_report.py#L143-L145))
- Clamp bounds in use: OpenMMLab-Exporter clips to `[0, src_w]` and `[0, src_h]`. Roboflow-Exporter clips to `[0, scale]` of the original image. Ultralytics `scale_boxes` clips to the source image. A clamp after NMS and unprojection (the spec order) instead of before NMS (mmdet) is invisible in AP. The spec does not define the bounds: see the `clamp_boxes` item in the [spec defects](../decisions/README.md#open-work). (OpenMMLab-Exporter [`onnx_runtime/decode_nms.py:163-171`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d2e68d27d2da0a4f22ddd19449df5601dcac87cc/onnx_runtime/decode_nms.py#L163-L171), and [`notes/decisions/0009-detector-output-layout-and-decode.md:81`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0009-detector-output-layout-and-decode.md#L81); Roboflow-Exporter [`rf_detr/coco_format.py:130-137`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/coco_format.py#L130-L137); ultralytics 8.4.184 `utils/ops.py:151-170, 648-664`, installed copy in the Ultralytics-Exporter `.venv`)

## Authoring guidance

- `confidence_threshold_default` is host policy. Record where the value comes from:
  - RTMO 0.1 is the `score_thr` of `test_cfg`. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py:528-532`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/6c494a0bcb48acc218b1edd3617b8621b35cc3f4/mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py#L528-L532))
  - RTMDet-person 0.7 is the runtime default of the exporter. It is not an upstream key. (OpenMMLab-Exporter [`rtmdet_person/model_report.py:24-25`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/ba0c0876b58650ed472559f1a77780e5da13d370/rtmdet_person/model_report.py#L24-L25); [`notes/decisions/0009-detector-output-layout-and-decode.md:32`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0009-detector-output-layout-and-decode.md#L32))
  - RF-DETR 0.5 is an identity constant. (Roboflow-Exporter [`rf_detr/identity.py:30`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/identity.py#L30) and [`rf_detr/sidecar.py:271-284`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L271-L284))
  - YOLO26 0.7 (detector) and 0.3 (pose) are choices of the exporter. The code gives no reason. The Ultralytics defaults are `conf` 0.25 for predict and 0.001 for val. (Ultralytics-Exporter [`yolo_sidecar.py:30-31`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L30-L31); ultralytics 8.4.184 `cfg/default.yaml:55`, installed copy in the Ultralytics-Exporter `.venv`)
  - The MediaPipe person detector 0.75 is the upstream `min_detector_pose_box_score`. (Qualcomm-Exporter [`qai_catalog.py:59`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_catalog.py#L59); qai_hub_models 0.64.0 `models/mediapipe_pose/app.py:69`, installed copy in the Qualcomm-Exporter `.venv`)
- Box and score mappings in use:
  - RF-DETR: `box_format` is `cxcywh`, `box_scale` is `normalized_01` and `score_activation` is `sigmoid`. (Roboflow-Exporter [`rf_detr/sidecar.py:271-284`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L271-L284))
  - YOLO26: `box_format` is `xyxy`, because the end-to-end head decodes with `dist2bbox(..., xywh=not end2end and not xyxy)`. (Ultralytics-Exporter [`yolo_sidecar.py:467-478`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L467-L478); ultralytics 8.4.184 `nn/modules/head.py:245-247`, installed copy in the Ultralytics-Exporter `.venv`)
  - The MediaPipe person detector: `box_format` is `xyxy`, because the upstream postprocess calls `box_xywh_to_xyxy`. `box_scale` is omitted (pixel), because the anchors decode to model-input pixels. `score_field` is `score`. (Qualcomm-Exporter [`qai_sidecar.py:124-133`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L124-L133); qai_hub_models 0.64.0 `models/templates/mediapipe/utils.py:147-171`, installed copy in the Qualcomm-Exporter `.venv`)
- Class mappings in use:
  - YOLO26: `class_id_base` is 0 and `person_class_id` is 0. The ONNX metadata `names` maps 0 to person. (Ultralytics-Exporter [`yolo_sidecar.py:29`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L29), [`yolo_sidecar.py:467-478`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L467-L478); `exports/detectors/object_detectors/yolo26/yolo26-nano_b2_fp32.onnx`, untracked, HEAD 2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4)
  - RF-DETR: `person_class_id` is 1 (the COCO category id) and `is_person_only` is `false` (an 80-class model). (Roboflow-Exporter [`rf_detr/sidecar.py:271-284`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L271-L284))
  - The legacy YOLO26 files write `may_include_non_person_classes` `true` for the 80-class detector. They write `false` for the pose model, whose `names` map is `{0: person}`. At `vNEXT`, `may_include_non_person_classes` is invalid and `is_person_only` replaces it. (Ultralytics-Exporter [`yolo_sidecar.py:475`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L475), [`yolo_sidecar.py:588`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L588); [Legacy behaviour](#legacy-behaviour); `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body-nano_b2_fp32.onnx`, untracked, HEAD 2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4)
- A class index plus 1 is a COCO category id only for a person-only model. The 80 COCO ids are not contiguous (12, 26, 29, 30, 45, 66, 68, 69, 71 and 83 are unused). The wrong mapping scored rtmdet-tiny at AP 0.066 instead of about 0.41. (OpenMMLab-Exporter [`notes/decisions/0001-coco-scorer-category-mapping.md:13-15`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c955162d91998b94fc52d932ab6623a9f2a89a1f/notes/decisions/0001-coco-scorer-category-mapping.md#L13-L15))
- `class_id_map` applies after the selection. The writer of Roboflow-Exporter refuses a model with a background slot, because a `class_id_map` cannot exclude a slot before the top-k. RF-DETR has no background slot. (Roboflow-Exporter [`rf_detr/sidecar.py:114-116`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L114-L116) and [`tests/test_sidecar.py:251-262`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/tests/test_sidecar.py#L251-L262))
- Change the `decode` block of the sidecar in the same change as any decode rule. Roboflow-Exporter does this, and it keeps its two decoder copies in lockstep. (Roboflow-Exporter [`rf_detr/DECODE_RULES.md:23-37`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/DECODE_RULES.md#L23-L37))
- The upstream of the MediaPipe person detector neither drops nor clamps boxes outside the image (`FILTER_OOB_BOX = False`). The `unproject_boxes` function of Qualcomm-Exporter does neither. At `vNEXT`, `clamp_boxes` defaults to `true`. Check `clamp_boxes` against the upstream. (Qualcomm-Exporter [`qai_catalog.py:61`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_catalog.py#L61) and [`qai_datasets.py:170-181`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_datasets.py#L170-L181); qai_hub_models 0.64.0 `models/mediapipe_pose/model.py:80` and `models/templates/mediapipe/app.py:375-382`, installed copy in the Qualcomm-Exporter `.venv`)

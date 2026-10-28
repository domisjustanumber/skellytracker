---
id: post.det.selection.none
title: "Selection: none"
kind: postprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors:
  - decode.selection=none
implemented_by:
  validate: skellytracker/core/sidecar/model.py::DetectionDecodeSpec._check_ranges  # partial: it checks only max_detections > 0; no rule for forbidden fields or the row count
  decode: skellytracker/core/detectors/processing/object_detection_decode.py::decode_nms_baked_in  # partial: the score is column 4; no class mapping, is_person_only or clamp; the caller gives the threshold
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/test_object_detection_decode.py
  - skellytracker/tests/test_yolox_detector.py
vectors: vectors/post.det.selection.none.yaml
status: {spec: stable, validate: partial, decode: partial}
---

# Selection: none

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `max_detections` | int | no | The fixed number of final rows that the graph emits (for example `300` for YOLO26). This field is valid only with `selection: none`. It is never a host-side cap. It has no default. |

`max_detections` is a field of [`decode`](detection-decode.md#decode-detection). That section defines the other `decode` fields.

## Behaviour

Score comparisons and tie-breaking: [Selection behaviour](detection-decode.md#selection-behaviour).

**`selection: none`** — the primary output rows are already final detections (for example the NMS-free head of YOLO26).

1. Resolve the score of each row (`score_field` or `scores_output`). Resolve the class index of each row (`class_field`). If this field is absent, there is no class source.
2. Map each class index with `class_id_map` or `class_id_base`. Drop each row that maps to `-1`. Apply `is_person_only`.
3. Convert the boxes from `box_format` to `xyxy`. Apply `box_scale`. Unproject the boxes. When `clamp_boxes` is true, clamp the boxes.
4. Apply `confidence_threshold_default`. Do not run NMS. The host does not pad or truncate the rows to reach `max_detections`.

Pose rows of a model with both roles: [Bottom-up decode](pose-bottom-up.md#bottom-up-decode).

## Validation rules

### Detection (`object_detector`)

- [ ] `V-post.det.selection.none-1` A sidecar with `selection: none` must not have `top_k`, `nms` or `class_logits_output`. If `max_detections` is present, it must be a positive integer. When the row dimension of the primary output is concrete, this value must equal that dimension.

See also [Detection decode](detection-decode.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `decode.max_detections` absent | Default `300`. | No default; valid only with `selection: none`. |

See also [Detection decode](detection-decode.md#legacy-behaviour) and [Bottom-up pose](pose-bottom-up.md#legacy-behaviour).

## Implementer guidance

- Ultralytics consumes the end-to-end rows with `mask = pred[:, 4] > conf_thres` and `idx = mask.nonzero()[:max_det]`. It does not sort and it does not run NMS. These are the steps of `selection: none`: a strict comparison and no NMS. The `max_det` cap does nothing for 300 rows. (ultralytics 8.4.184 `utils/nms.py:71-78`, installed copy in the Ultralytics-Exporter `.venv`)
- A YOLO26 graph gives `max_det` (300) rows for each image, in descending score order. The in-graph top-k runs over (anchor, class) pairs, so one box can repeat with different class ids. (ultralytics 8.4.184 `nn/modules/head.py:92-102, 266-288`, installed copy in the Ultralytics-Exporter `.venv`)
- The spec does not define the order of the final rows for `selection: none`. The decision log records this point ([spec defects](../decisions/README.md#open-work), item on the test vectors).
- YOLO26 box mAP50-95 on COCO val2017 at batch 2, PyTorch against fp32 ONNX: nano 0.4023 / 0.3971, small 0.4801 / 0.4717, medium 0.5238 / 0.5193, large 0.5444 / 0.5357, xlarge 0.5683 / 0.5635. The numbers come from the Ultralytics validator at its defaults (`conf` 0.001, `max_det` 300, `rect` off for a static ONNX). They do not come from a skellytracker host. (Ultralytics-Exporter `exports/detectors/object_detectors/yolo26/yolo26-nano_b2_fp32.report.json` and the reports of the other sizes, field `performance.pytorch.ap` and `performance.converted.ap`, untracked, HEAD 2e0280e; `yolo_validation.py:170-176, 271-278`, f52ef68; ultralytics 8.4.184 `engine/validator.py:144-145, 232-233`, installed copy in the Ultralytics-Exporter `.venv`)

## Authoring guidance

- RTMO keeps the in-graph NMS of mmdeploy, so it uses `selection: none` with `score_field: score`. It declares no `max_detections`: the real graph returned 4 and 11 rows on two val images. It declares `confidence_threshold_default` 0.1: an image with no person still returned one row with a score of about 6e-8. (OpenMMLab-Exporter `notes/decisions/0020-rtmo-sidecar-contract.md:64-69, 99-103`, 38ed76f)
- YOLO26: `max_detections` 300 follows from the export argument `max_det=300`. The argument `nms=False` selects the end-to-end one2one head, because Ultralytics sets `model.end2end` only for the literal `False`. The ONNX metadata shows `end2end` `True`. The exporter reads `max_detections` back from the output `shape[1]`. In a legacy file, `requires_nms: false` marks the same fact. (Ultralytics-Exporter `export_all.py:50-57`, 69499e7; `yolo_sidecar.py:481-484, 490`, 69499e7; `exports/detectors/object_detectors/yolo26/yolo26-nano_b2_fp32.onnx`, untracked, HEAD 2e0280e)
- Describe the graph, not `pipeline.json`. Record the in-graph NMS parameters and caps. The deploy config of mmdeploy for RTMO sets `pre_top_k=2000` and `keep_top_k=50`, and the deploy configs of the exporter inherit them. The AP effect is not checked, because the mmdeploy base file is not in the repo. Comparable caps cost -0.0114 AP on RTMDet-person-medium. (OpenMMLab-Exporter `rtmo/README.md:16-21`, c85abf7; `notes/decisions/0008-cut-nms-tail.md:24-35`, c955162)
- The SDK zip of the mmpose RTMDet-hand model bakes NMS into its `end2end.onnx` with IoU 0.5, `pre_top_k` 5000, 200 boxes for each class and `keep_top_k` 100. Its `pipeline.json` and the model config say IoU 0.6. (secondary: OpenMMLab-Exporter `plans/hand-models-PLAN.md:195-199`, untracked file of that repo)
- Pre-NMS anchor rows are not final rows. The MediaPipe person detector emits 896 pre-NMS anchor rows, so `selection: none` does not apply to it. Qualcomm-Exporter writes `max_detections` 896 beside `requires_nms: true`. That is valid only in a legacy file: at `vNEXT`, V-post.det.selection.nms-1 forbids `max_detections` with `selection: nms`. The changelog lists what a `vNEXT` sidecar must declare. (Qualcomm-Exporter `qai_sidecar.py:124-133`, 4ca4586; [Selection: NMS](selection-nms.md#validation-rules); [Compatibility impact](../changelog.md#compatibility-impact))

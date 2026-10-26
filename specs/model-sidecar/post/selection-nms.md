---
id: post.det.selection.nms
title: "Selection: NMS"
kind: postprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors:
  - decode.selection=nms
implemented_by:
  validate: missing
  decode: skellytracker/core/detectors/processing/object_detection_decode.py::decode_prenms  # partial: the box area adds 1 to each side; ties are not ordered by row index; one class only; no nms block, post_nms_top_k or clamp; the caller gives the thresholds
external_impl: []
tests:
  - skellytracker/tests/test_object_detection_decode.py
  - skellytracker/tests/test_yolox_detector.py
vectors: vectors/post.det.selection.nms.yaml
status: {spec: stable, validate: missing, decode: partial}
---

# Selection: NMS

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `nms` | object | conditional | Required for `selection: nms`. Invalid in all other cases. See below. |

**`nms` object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `iou_threshold` | float | yes | The host suppresses a candidate when its IoU with a higher-scoring kept box is greater than this value. |
| `score_threshold` | float | yes | A candidate filter that the host applies before NMS. It is strict: `score > score_threshold`. It is independent of `confidence_threshold_default`. |
| `class_agnostic` | bool | no | The default is `false` (per-class NMS). If there is no class source, every candidate has one class. In this case, both settings are equivalent. |
| `post_nms_top_k` | int | no | Keep at most this number of survivors for each image, highest score first. To keep all survivors, omit this field. |

`nms` is a field of [`decode`](detection-decode.md#decode-detection). That section defines the other `decode` fields. [Detection output semantics](detection-outputs.md#detection-output-semantics) defines `B`, `Q` and `C`.

## Behaviour

Score comparisons and tie-breaking: [Selection behaviour](detection-decode.md#selection-behaviour).

**`selection: nms`** — the primary output rows are pre-NMS candidates (for example RTMDet).

1. Resolve the scores. Drop each candidate with `score <= nms.score_threshold`.
2. Convert the boxes from `box_format` to `xyxy`. Apply `box_scale` to get model-input pixels. Do not unproject the boxes yet.
3. Resolve the class indices from `class_field` and map them. If there is no class source, assign `person_class_id`. Apply `is_person_only`.
4. Run hard NMS at `nms.iou_threshold` in model-input coordinates. Run it for each class, unless `class_agnostic: true`.
5. Sort the survivors by score in descending order. Keep the first `nms.post_nms_top_k` survivors if that field is set.
6. Unproject the boxes. Clamp them.
7. Apply `confidence_threshold_default`.

These decode steps correspond one-to-one to the standard ONNX `NonMaxSuppression` operator. The operator takes scores as `[B, C, Q]`. It suppresses boxes for each class when IoU is greater than `iou_threshold`. It drops candidates at or below `score_threshold`. Its box-area convention does not add `1` to pixel widths or heights.

Pose rows of a model with both roles: [Bottom-up decode](pose-bottom-up.md#bottom-up-decode).

## Validation rules

### Detection (`object_detector`)

- [ ] `V-post.det.selection.nms-1` A sidecar with `selection: nms` must have `nms` with `iou_threshold` and `score_threshold`. Each of these fields must be a float in `[0, 1]`. The sidecar must not have `class_logits_output`, `top_k` or `max_detections`. If `nms.class_agnostic` is present, it must be a boolean. If `nms.post_nms_top_k` is present, it must be a positive integer.

See also [Detection decode](detection-decode.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `decode.nms` absent with host NMS | Existing host NMS behaviour (implementation-defined). | Invalid; `nms` required for `selection: nms`. |

`decode.max_detections` before `vNEXT`: [Selection: none](selection-none.md#legacy-behaviour).

## Implementer guidance

- The reference host decode of OpenMMLab-Exporter (`NmsDecoder`) is an ONNX `NonMaxSuppression` graph. It transposes or unsqueezes the scores to `[B, C, Q]`, uses `center_point_box=0` and feeds the thresholds at run time. `max_per_class` is `post_nms_top_k` or `2**31-1`. The decoder then applies `post_nms_top_k` again to the final rows of each image. (OpenMMLab-Exporter `onnx_runtime/decode_nms.py:37-72, 125-130, 157-166`, d2e68d2)
- On random boxes with 1 and 3 classes, this decoder matches a NumPy per-class greedy NMS (IoU > threshold suppresses, no +1 in the area). The scores match at rtol 1e-6. The class ids and the clamped boxes match. (OpenMMLab-Exporter `tests/test_decode_nms.py:11-69`, d2e68d2)
- `post_nms_top_k` applies to each image: 3 images with `k=5` give 5 detections each. (OpenMMLab-Exporter `tests/test_decode_nms.py:101-107`, d2e68d2)
- The decoder raises for a `selection` other than `nms`, a `box_format` other than `xyxy`, a `box_scale` other than `pixel`, a `score_activation` other than `none`, and `class_agnostic: true`. Those options are not exercised. No reference implementation exists yet. (OpenMMLab-Exporter `onnx_runtime/decode_nms.py:108-116`, d2e68d2, and `tests/test_decode_nms.py:144-154`, d2e68d2; [known open items](../../draft/exporter-guide/sidecars/known-open-items.md#known-open-items-for-the-exporter-overhaul))
- A pre-filter at `max(nms.score_threshold, confidence threshold)` before NMS gives the same detections as NMS followed by the confidence filter (tested at 0.3 and 0.7 on 200 boxes x 4 classes). With the default 0.7, the scores 0.69 and 0.71 keep only 0.71. (OpenMMLab-Exporter `tests/test_decode_nms.py:72-83, 110-124`, d2e68d2)
- Parity of the declared preprocessing and decode of RTMDet-person (`selection: nms` at 0.05 / 0.6 / 100). The fp32 AP against the source: nano batch 1 gives 0.40359 against 0.40329, and medium batch 3 gives 0.62555 against 0.62544. The fp16 AP is 0.40350 and 0.62536. With the spec decode on full COCO val2017, person-medium gives AP 0.6255 (delta 0.0000). (OpenMMLab-Exporter `notes/decisions/0035-published-artifact-reuse-and-p8-reexport.md:41-48`, c85abf7; `notes/decisions/0009-detector-output-layout-and-decode.md:64-73`, 38ed76f; `pipeline/accuracy.py:419-446`, ba0c087)
- The host NMS of Qualcomm-Exporter is not the NMS of the spec. It is class-agnostic greedy NMS. It suppresses a box when IoU >= threshold. It adds 1 to the widths and heights. It has no tie order (`np.argsort(-scores)`). Its tests cannot tell this from the standard IoU. (Qualcomm-Exporter `qai_metrics.py:8-28, 77-89`, 4ca4586, and `tests/test_qai_metrics.py:25-28, 46-52`, 4ca4586)
- The `nms()` function of skellytracker has the same two differences from the spec: it adds 1 to the box sizes and it breaks a tie toward the higher row index. (Open work item "NMS box area" in the [decision log](../../../notes/decisions/README.md#open-work); vectors: [post.det.selection.nms](../vectors/post.det.selection.nms.yaml))
- The upstream `batched_nms` of qai_hub_models keeps scores `>= threshold`, and the benchmark of Qualcomm-Exporter filters scores `>= 0.01` before NMS. The spec uses strict comparisons. It never applies `confidence_threshold_default`. The decision log asks the same question for the strict 0.7 default ([spec defects](../../../notes/decisions/README.md#open-work), item on `confidence_threshold_default`). (Qualcomm-Exporter `qai_validation.py:25, 45-74`, 4ca4586; qai_hub_models 0.64.0 `utils/bounding_box_processing.py:85-86`, installed copy in the Qualcomm-Exporter `.venv`)
- MediaPipe person detector parity on COCO val2017 (5,000 images, 11,004 person boxes) with the full host path of the exporter: AP50 0.01568 and AP 0.006846 for PyTorch and for fp32 ONNX, and AP 0.006849 for fp16 ONNX. The absolute values are very low and the repo does not say why. The numbers show only that the ONNX matches PyTorch. (Qualcomm-Exporter `exports/detectors/object_detectors/mediapipe-person-detector/mediapipe-person-detector-default_b1_fp32.report.json` and `..._fp16.report.json`, fields `performance.pytorch.metrics` and `performance.converted.metrics`, untracked, HEAD 4ca4586; `qai_validation.py:94-133`, 4ca4586)
- Host NMS is cheap for person models: 0.1 ms to 0.3 ms for each image on CPU at threshold 0.7, and about 0.6 ms at 0.05. In-graph NMS on an 80-class model costs about 9 ms to 11 ms for each image on CUDA, even at 0.3 to 0.7. It costs little for a single class or on CPU. (OpenMMLab-Exporter `rtmdet_person/model_report.py:204-209`, ba0c087; `notes/decisions/0016-ingraph-nms-at-runtime-thresholds.md:38-43`, c955162)

## Authoring guidance

- mmdet: `test_cfg` `score_thr=0.05`, `nms=dict(type='nms', iou_threshold=0.6)` and `max_per_img=100` map to `decode.nms` with `score_threshold: 0.05`, `iou_threshold: 0.6` and `post_nms_top_k: 100`. A test checks the values against the config text. (OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmdet_nano_320-8xb32_coco-person.py:24-29`, f29d9bb; `tests/test_rtmdet_person.py:77-84`, ba0c087)
- `nms_pre=1000` and `min_bbox_size=0` have no field. Leaving out the per-level `nms_pre` changed AP by +0.0001 on rtmdet-tiny and by 0 on person-medium. It costs only decode time at a 0.001 threshold. (OpenMMLab-Exporter `notes/decisions/0009-detector-output-layout-and-decode.md:75-80`, 38ed76f)
- Ultralytics-Exporter exports only `nms=False` and writes no NMS parameters. For a raw-head YOLO artifact, the Ultralytics defaults are `iou` 0.7, `max_det` 300 and `conf` 0.25 (predict) or 0.001 (val). (Ultralytics-Exporter `export_all.py:50-57`, 69499e7; ultralytics 8.4.184 `cfg/default.yaml:55-57`, installed copy in the Ultralytics-Exporter `.venv`)
- The MediaPipe person detector has an upstream `nms_iou_threshold` of 0.3 and a `min_detector_pose_box_score` of 0.75. The upstream NMS is class-agnostic (torchvision `nms`). The upstream app keeps only the first survivor of each image, which has the highest score: a loop breaks after the first box that passes the out-of-bound filter, and the pose model switches that filter off. This is `post_nms_top_k: 1` at `vNEXT`. The legacy sidecar of Qualcomm-Exporter writes only 0.75 (as `confidence_threshold_default`), no `decode.nms` and no cap. Its benchmark scores every survivor. The changelog lists what a `vNEXT` sidecar must declare ([Compatibility impact](../changelog.md#compatibility-impact)). (Qualcomm-Exporter `qai_catalog.py:59-61` and `qai_validation.py:59-73`, 4ca4586; qai_hub_models 0.64.0 `models/mediapipe_pose/app.py:69-70`, `models/templates/mediapipe/app.py:359-386` and `utils/bounding_box_processing.py:99-108`, installed copy in the Qualcomm-Exporter `.venv`)

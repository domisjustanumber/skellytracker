---
id: post.object.selection.nms
title: "Selection: NMS"
kind: postprocessor
selectors:
  - object.decode.selection=nms
implemented_by:
  validate: missing
  decode: skellytracker/core/detectors/processing/object_detection_decode.py::decode_prenms  # partial: the box area adds 1 to each side; ties are not ordered by row index; one class only; no nms block, post_nms_top_k, clamp or size filter; the caller gives the thresholds
external_impl:
  - OpenMMLab-Exporter: onnx_runtime/decode_nms.py::NmsDecoder
tests:
  - skellytracker/tests/test_object_detection_decode.py
  - skellytracker/tests/test_yolox_detector.py
vectors: vectors/post.object.selection.nms.yaml
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
| `score_threshold` | float | yes | A candidate filter that the host applies before NMS. It is strict: `score > score_threshold`. It is independent of `min_score`. |
| `class_agnostic` | bool | no | The default is `false` (per-class NMS). If there is no class source, every candidate has one class. In this case, both settings are equivalent. |
| `post_nms_top_k` | int | no | Keep at most this number of survivors for each image, highest score first. To keep all survivors, omit this field. |

`nms` is a field of [`object.decode`](decode.md#objectdecode). That section defines the other `object.decode` fields. [Detection output semantics](outputs.md#detection-output-semantics) defines `B`, `Q` and `C`.

## Behaviour

Score comparisons and tie-breaking: [Selection behaviour](decode.md#selection-behaviour).

**`selection: nms`** — the primary output rows are pre-NMS candidates (for example RTMDet).

1. Resolve the scores. Drop each candidate with `score <= nms.score_threshold`.
2. Do shared step 2 (box conversion) of [Selection behaviour](decode.md#selection-behaviour). Do not unproject the boxes yet.
3. Resolve the class indices from `class_field`. Do shared step 1 (class filter).
4. Run hard NMS at `nms.iou_threshold` in model-input coordinates. Run it for each class, unless `class_agnostic: true`.
5. Sort the survivors by score in descending order. Keep the first `nms.post_nms_top_k` survivors if that field is set.
6. Do the shared steps 3 to 5 (unprojection, clamp and size filter).
7. Do shared step 6 (score threshold).

These decode steps correspond one-to-one to the standard ONNX `NonMaxSuppression` operator. The operator takes scores as `[B, C, Q]`. It suppresses boxes for each class when IoU is greater than `iou_threshold`. It drops candidates at or below `score_threshold`. Its box-area convention does not add `1` to pixel widths or heights.

Keypoint rows of a model with both roles: [Bottom-up decode](../keypoint/bottom-up.md#bottom-up-decode).

## Validation rules

### Object (`object_detector`)

- [ ] `V-post.object.selection.nms-1` A sidecar with `selection: nms` must have `nms` with `iou_threshold` and `score_threshold`. Each of these fields must be a float in `[0, 1]`. The sidecar must not have `class_logits_output`, `top_k` or `max_detections`. If `nms.class_agnostic` is present, it must be a boolean. If `nms.post_nms_top_k` is present, it must be a positive integer.

See also [Object decode](decode.md#validation-rules).

## Implementer guidance

- The reference host decode of OpenMMLab-Exporter (`NmsDecoder`) is an ONNX `NonMaxSuppression` graph. It transposes or unsqueezes the scores to `[B, C, Q]`, uses `center_point_box=0` and feeds the thresholds at run time. `max_per_class` is `post_nms_top_k` or `2**31-1`. The decoder then applies `post_nms_top_k` again to the final rows of each image. (OpenMMLab-Exporter [`onnx_runtime/decode_nms.py:37-72`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d2e68d27d2da0a4f22ddd19449df5601dcac87cc/onnx_runtime/decode_nms.py#L37-L72), [`onnx_runtime/decode_nms.py:125-130`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d2e68d27d2da0a4f22ddd19449df5601dcac87cc/onnx_runtime/decode_nms.py#L125-L130), [`onnx_runtime/decode_nms.py:157-166`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d2e68d27d2da0a4f22ddd19449df5601dcac87cc/onnx_runtime/decode_nms.py#L157-L166))
- On random boxes with 1 and 3 classes, this decoder matches a NumPy per-class greedy NMS (IoU > threshold suppresses, no +1 in the area). The scores match at rtol 1e-6. The class ids and the clamped boxes match. (OpenMMLab-Exporter [`tests/test_decode_nms.py:11-69`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d2e68d27d2da0a4f22ddd19449df5601dcac87cc/tests/test_decode_nms.py#L11-L69))
- `post_nms_top_k` applies to each image: 3 images with `k=5` give 5 detections each. (OpenMMLab-Exporter [`tests/test_decode_nms.py:101-107`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d2e68d27d2da0a4f22ddd19449df5601dcac87cc/tests/test_decode_nms.py#L101-L107))
- The OpenMMLab-Exporter host `onnx_runtime/decode_nms.py::NmsDecoder` passes each case of the vector file at commit `2a3334c9e7f29c82d4406eb8e03a7ceefb3003d5`, also the cases `box-format-cxcywh` and `class-agnostic-suppresses-across-classes` (the `vector-runs.yaml` of the bundle `model-yolox-person@openmmlab-exporter@v1`). The reference module `reference/post_object_selection_nms.py` comes from this host at commit `5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278`.
- A pre-filter at `max(nms.score_threshold, confidence threshold)` before NMS gives the same detections as NMS followed by the confidence filter (tested at 0.3 and 0.7 on 200 boxes x 4 classes). With the default 0.7, the scores 0.69 and 0.71 keep only 0.71. (OpenMMLab-Exporter [`tests/test_decode_nms.py:72-83`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d2e68d27d2da0a4f22ddd19449df5601dcac87cc/tests/test_decode_nms.py#L72-L83), [`tests/test_decode_nms.py:110-124`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d2e68d27d2da0a4f22ddd19449df5601dcac87cc/tests/test_decode_nms.py#L110-L124))
- Parity of the declared preprocessing and decode of RTMDet-person (`selection: nms` at 0.05 / 0.6 / 100). The fp32 AP against the source: nano batch 1 gives 0.40359 against 0.40329, and medium batch 3 gives 0.62555 against 0.62544. The fp16 AP is 0.40350 and 0.62536. With the spec decode on full COCO val2017, person-medium gives AP 0.6255 (delta 0.0000). (OpenMMLab-Exporter [`notes/decisions/0035-published-artifact-reuse-and-p8-reexport.md:41-48`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c85abf7da34d1e4da7c129f3382173f7153f60fa/notes/decisions/0035-published-artifact-reuse-and-p8-reexport.md#L41-L48); [`notes/decisions/0009-detector-output-layout-and-decode.md:64-73`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0009-detector-output-layout-and-decode.md#L64-L73); [`pipeline/accuracy.py:419-446`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/ba0c0876b58650ed472559f1a77780e5da13d370/pipeline/accuracy.py#L419-L446))
- The host NMS of Qualcomm-Exporter is not the NMS of the spec. It is class-agnostic greedy NMS. It suppresses a box when IoU >= threshold. It adds 1 to the widths and heights. It has no tie order (`np.argsort(-scores)`). Its tests cannot tell this from the standard IoU. (Qualcomm-Exporter [`qai_metrics.py:8-28`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_metrics.py#L8-L28), [`qai_metrics.py:77-89`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_metrics.py#L77-L89), and [`tests/test_qai_metrics.py:25-28`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/tests/test_qai_metrics.py#L25-L28), [`tests/test_qai_metrics.py:46-52`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/tests/test_qai_metrics.py#L46-L52))
- The `nms()` function of skellytracker has the same two differences from the spec: it adds 1 to the box sizes and it breaks a tie toward the higher row index. (Item "NMS box area" of M8 in the [implementation plan](../../../sidecar-implementation-plan.md#m8--validation-preprocessing-and-decode-gaps); vectors: [post.object.selection.nms](../../vectors/post.object.selection.nms.yaml))
- The upstream `batched_nms` of qai_hub_models keeps scores `>= threshold`, and the benchmark of Qualcomm-Exporter filters scores `>= 0.01` before NMS. The spec uses strict comparisons. It never applies `min_score`. The strict comparison is intended ([ADR-Q6W6](../../decisions/entries/Q6W6-strict-score-comparisons.md)). (Qualcomm-Exporter [`qai_validation.py:25`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_validation.py#L25), [`qai_validation.py:45-74`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_validation.py#L45-L74); qai_hub_models 0.64.0 `utils/bounding_box_processing.py:85-86`, installed copy in the Qualcomm-Exporter `.venv`)
- MediaPipe person detector parity on COCO val2017 (5,000 images, 11,004 person boxes) with the full host path of the exporter: AP50 0.01568 and AP 0.006846 for PyTorch and for fp32 ONNX, and AP 0.006849 for fp16 ONNX. The absolute values are very low and the repo does not say why. The numbers show only that the ONNX matches PyTorch. (Qualcomm-Exporter `exports/detectors/object_detectors/mediapipe-person-detector/mediapipe-person-detector-default_b1_fp32.report.json` and `..._fp16.report.json`, fields `performance.pytorch.metrics` and `performance.converted.metrics`, untracked, HEAD 4ca45868431b67350c3c7ed900d5b3ff9f409905; [`qai_validation.py:94-133`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_validation.py#L94-L133))
- Host NMS is cheap for person models: 0.1 ms to 0.3 ms for each image on CPU at threshold 0.7, and about 0.6 ms at 0.05. In-graph NMS on an 80-class model costs about 9 ms to 11 ms for each image on CUDA, even at 0.3 to 0.7. It costs little for a single class or on CPU. (OpenMMLab-Exporter [`rtmdet_person/model_report.py:204-209`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/ba0c0876b58650ed472559f1a77780e5da13d370/rtmdet_person/model_report.py#L204-L209); [`notes/decisions/0016-ingraph-nms-at-runtime-thresholds.md:38-43`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c955162d91998b94fc52d932ab6623a9f2a89a1f/notes/decisions/0016-ingraph-nms-at-runtime-thresholds.md#L38-L43))

## Authoring guidance

- mmdet: `test_cfg` `score_thr=0.05`, `nms=dict(type='nms', iou_threshold=0.6)` and `max_per_img=100` map to `object.decode.nms` with `score_threshold: 0.05`, `iou_threshold: 0.6` and `post_nms_top_k: 100`. A test checks the values against the config text. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmdet_nano_320-8xb32_coco-person.py:24-29`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/f29d9bba71d3669bfdab98597069151d42d1f5ff/mmdeploy-convert/model_cfgs/rtmdet_nano_320-8xb32_coco-person.py#L24-L29); [`tests/test_rtmdet_person.py:77-84`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/ba0c0876b58650ed472559f1a77780e5da13d370/tests/test_rtmdet_person.py#L77-L84))
- RTMDet person: the graph ends before NMS, so the sidecar declares `selection: nms`. The family `shape` has `-1` for the row count `A`, and the [`onnx.output_shapes`](../../common/sizes-and-artifacts.md#sizessizeonnx) of each size gives `A` ([Implementer guidance](outputs.md#implementer-guidance); [ADR-JAA4](../../../../decisions/entries/JAA4-one-batch-field.md)). (OpenMMLab-Exporter [`onnx_convert/nms_cut.py:7-20`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/689d3ed0a02f9ab7f40e722b979c26bfb3017f0a/onnx_convert/nms_cut.py#L7-L20))
- `nms_pre=1000` has no field. `min_bbox_size` maps one-to-one to [`object.decode.min_box_size`](decode.md#objectdecode). The RTMDet person config writes `min_bbox_size=0`, so an RTMDet person sidecar must write `min_box_size: 0`. A box with zero area then goes. mmdet applies the filter before NMS, and the spec applies it after NMS ([Implementer guidance](decode.md#implementer-guidance); [ADR-17KN](../../../../decisions/entries/17KN-one-selection-pipeline.md)). Leaving out the per-level `nms_pre` changed AP by +0.0001 on rtmdet-tiny and by 0 on person-medium. It costs only decode time at a 0.001 threshold. (OpenMMLab-Exporter [`notes/decisions/0009-detector-output-layout-and-decode.md:75-80`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0009-detector-output-layout-and-decode.md#L75-L80))
- Do not compare the host decode with an appended ONNX `NonMaxSuppression` at the `0.001` validation threshold. The OpenMMLab-Exporter variant caps 300 boxes for each class (`max_output_boxes_per_class`). The host decode has no such cap, so the box counts differ on each image ([ADR-JAA4](../../../../decisions/entries/JAA4-one-batch-field.md)). (OpenMMLab-Exporter ADR-0016 [`notes/decisions/0016-ingraph-nms-at-runtime-thresholds.md:44-46`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c955162d91998b94fc52d932ab6623a9f2a89a1f/notes/decisions/0016-ingraph-nms-at-runtime-thresholds.md#L44-L46))
- Ultralytics-Exporter exports only `nms=False` and writes no NMS parameters. For a raw-head YOLO artifact, the Ultralytics defaults are `iou` 0.7, `max_det` 300 and `conf` 0.25 (predict) or 0.001 (val). (Ultralytics-Exporter [`export_all.py:50-57`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/69499e7d292e6f3583ab9429c45a334af3377097/export_all.py#L50-L57); ultralytics 8.4.184 `cfg/default.yaml:55-57`, installed copy in the Ultralytics-Exporter `.venv`)
- The MediaPipe person detector has an upstream `nms_iou_threshold` of 0.3 and a `min_detector_pose_box_score` of 0.75. The upstream NMS is class-agnostic (torchvision `nms`). The upstream app keeps only the first survivor of each image, which has the highest score: a loop breaks after the first box that passes the out-of-bound filter, and the pose model switches that filter off. This is `post_nms_top_k: 1`. The sidecar of Qualcomm-Exporter writes only 0.75 (as `min_score`), no `object.decode.nms` and no cap. Its benchmark scores every survivor. (Qualcomm-Exporter [`qai_catalog.py:59-61`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_catalog.py#L59-L61) and [`qai_validation.py:59-73`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_validation.py#L59-L73); qai_hub_models 0.64.0 `models/mediapipe_pose/app.py:69-70`, `models/templates/mediapipe/app.py:359-386` and `utils/bounding_box_processing.py:99-108`, installed copy in the Qualcomm-Exporter `.venv`)

# Reference examples

Revision: [Changes in this revision](../changelog.md#changes-in-this-revision-vnext).

Each example is a sidecar for this revision from the named exporter. The OpenMMLab-Exporter examples (RTMDet person, RTMW, RTMO body7) come from its real `vNEXT` exports. The Ultralytics-Exporter examples (YOLO26 detection and pose) are written from that exporter's code and published artifacts: tensor names, shapes, dtypes, sizes, batches, precisions and filenames. The examples keep only batch 1, but the exporter publishes the batches 1, 2 and 3 ([Batch forms](../common/sizes-and-artifacts.md#batch-forms); [ADR-JB5J](../../../decisions/JB5J-one-batch-form-for-each-sidecar.md)). They will be replaced when it emits `vNEXT`. There is no RF-DETR example until Roboflow-Exporter is overhauled; the `stretch`, `top_k` and `class_logits` rules have no example until then. Where a family has more sizes than shown, the omitted sizes differ only in `input.shape`, `target_size` and filenames.

Each example also has a top-level [`source`](../common/identity.md#fields) and every hash: the `sha256` of each `$ref` ([Reference hashes](../format/composition.md#reference-hashes)) and of each artifact ([Sizes and artifacts](../common/sizes-and-artifacts.md#sizessizeonnxbatch_artifacts)). No exporter writes these fields yet. `tools/sidecar_refs.py --write --placeholder --source` added them. `source.version` is the current version of the exporter package, also for the YOLO26 examples. The ONNX artifacts have the reserved placeholder hash, because nobody can download the ONNX files of an example. Thus each example differs from its exporter copy until the exporter writes these fields.

## YOLO26 detector (Ultralytics-Exporter; NMS-free, graph-final rows)

Centre letterbox with half-even rounding, RGB `unit_float` input, and one packed `[B, 300, 6]` tensor of final detections (`nms=False`, `max_det=300` at export). Each precision keeps float32 I/O.

Sidecar: [`yolo26.yaml`](detectors/object_detectors/yolo26/yolo26.yaml).

## YOLO26 pose (Ultralytics-Exporter; bottom-up, packed keypoints)

The pose export emits one `[B, 300, 57]` tensor: 6 detection columns followed by 17 × `(x, y, score)`, with keypoints in model-input pixels and keypoint scores already sigmoid-activated. It is declared once, with `packed_keypoints`.

Sidecar: [`yolo26-body.yaml`](detectors/keypoint_detectors/yolo26/body/yolo26-body.yaml).

## RTMDet person (OpenMMLab-Exporter; NMS-free outputs, host NMS)

The mmdet test pipeline letterboxes into the top-left corner with half-up rounding and pad 114, normalizing BGR pixels. The graph emits every anchor point's decoded box and sigmoid person score; the host runs the family's baseline NMS (`score_thr` 0.05, IoU 0.6, `max_per_img` 100). The row count depends on input size: 2100 at 320 and 8400 at 640.

Sidecar: [`rtmdet-person.yaml`](detectors/object_detectors/rtmdet-person/rtmdet-person.yaml).

The graph ends before NMS. It emits every anchor point's decoded box and sigmoid person score, so the host applies the family's baseline NMS (mmpose `test_cfg`: score > 0.05, IoU 0.6, top 100). The row count is the anchor-point count for the input size (2100 at 320, 8400 at 640), so the family-level shape leaves it as `-1`. mmdet's per-level `nms_pre` cap (1000) is deliberately not expressed; dropping it has no measurable effect on AP.

## RTMW WholeBody (OpenMMLab-Exporter; top-down pose)

mmpose `input_size` is `(width, height)`: the `256x192` models take `[N, 3, 256, 192]` input and the `384x288` models `[N, 3, 384, 288]`. The model consumes RGB (`bgr_to_rgb=True`) normalized with ImageNet statistics. SIMCC bin counts are twice the input width/height (`simcc_split_ratio=2.0`) and are read from the output tensors, so `shape` is omitted.

Sidecar: [`rtmw-wholebody.yaml`](detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml).

For comparison, skellytracker's in-repo `rtmw/wholebody/rtmw-wholebody.yaml` describes the rtmlib `onnx_sdk` downloads (with `url`/`url_sha256`) at `schema_version: v2024.09.1019`. It uses the legacy `imagenet_bgr` meaning (see [Version-aware compatibility](../pre/normalization.md#legacy-behaviour)).

## RTMO body7 (OpenMMLab-Exporter; bottom-up pose, NMS in the graph)

mmpose `BottomupResize` warps the whole frame with `cv2.warpAffine` to a fractional fit size, centred, with pad 114: that is `fit`, not `letterbox`. RTMO normalizes with mean 0 and std 1 and keeps BGR (`bgr_to_rgb: false`), so the input is `normalization: none` with `color_format: bgr`. The deployed graph keeps NMS, so the `dets` and `keypoints` row count is dynamic and the host uses `selection: none` with no `max_detections`. `confidence_threshold_default` is the upstream `score_thr` (0.1); it drops the near-zero row that the graph can emit on an image with no person.

Sidecar: [`rtmo-body7.yaml`](detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml).

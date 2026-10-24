---
id: post.det.selection.top_k
title: "Selection: top-k"
kind: postprocessor
since: vNEXT
changed_in: []
selectors:
  - decode.selection=top_k
implemented_by:
  validate: missing
  decode: missing
external_impl: []
tests: []
vectors: vectors/post.det.selection.top_k.yaml
status: {spec: stable, validate: missing, decode: missing}
---

# Selection: top-k

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `class_logits_output` | string | conditional | The name of the `class_logits` output. Required for `selection: top_k`. Invalid in all other cases. |
| `score_activation` | enum | no | The value is `none` (default) or `sigmoid`. The host applies it to `class_logits` before selection. |
| `top_k` | int | conditional | The number of (row, class) pairs to select. Required for `selection: top_k`. |

These are fields of [`decode`](detection-decode.md#decode-detection). That section defines the other `decode` fields. [Detection output semantics](detection-outputs.md#detection-output-semantics) defines `B`, `Q` and `C`.

## Behaviour

Score comparisons and tie-breaking: [Selection behaviour](detection-decode.md#selection-behaviour).

**`selection: top_k`** — the model gives class logits for each row. The host takes a global top-k of the (row, class) pairs (for example RF-DETR).

1. Compute `p = score_activation(class_logits)`. Move `class_axis` to the last position. Then `p` is `[Q, C]`.
2. Flatten in row-major order with `flat = row * C + class`.
3. Sort the entries by score in descending order with a stable sort. Take the first `min(top_k, Q * C)` entries.
4. Compute `row = flat // C` and `class = flat % C`. Gather `boxes[row]`. The score is `p[row, class]`.
5. Map `class` with `class_id_map` or `class_id_base`. Drop each pair that maps to `-1`. The final count can then be below `top_k`. Apply `is_person_only`.
6. Convert the boxes. Apply `box_scale`. Unproject the boxes. Clamp the boxes.
7. Apply `confidence_threshold_default`. Do not run NMS. Several selected pairs can share one row (one box, several classes). The spec allows this.

## Validation rules

### Detection (`object_detector`)

- [ ] `V-post.det.selection.top_k-1` A sidecar with `selection: top_k` must have a `boxes` primary output, `class_logits_output` and a positive integer `top_k`. It must not have `nms`, `max_detections`, `scores_output` or `score_field`.

See also [Detection decode](detection-decode.md#validation-rules).

## Legacy behaviour

See [Detection decode](detection-decode.md#legacy-behaviour) and [Schema versioning](../format/versioning.md#legacy-behaviour).

## Implementer guidance

- The decoder of Roboflow-Exporter matches the steps 1 to 4 and 7. It applies the sigmoid to the logits `[Q, C]`. The function `_select_topk_multiclass` flattens the scores in row-major order and sorts with `np.lexsort((flat_index, -score))`: descending score, ties by ascending flat index. It takes the first `min(num_select, Q * C)` entries and computes `row = idx // C` and `class = idx % C`. Then it applies `score > threshold` and runs no NMS. One query can give several records (the same box with different classes). (Roboflow-Exporter `rf_detr/coco_format.py:40-64, 122-127` and `onnx_runtime/convert_rf_detr_coco.py:40-66`, b34e351)
- The decoders of Roboflow-Exporter also convert cxcywh boxes to xyxy, scale them with the original image size and clip them (the box part of step 6). They do not apply step 5 (`class_id_map`). No reference implementation exists yet. (Roboflow-Exporter `rf_detr/coco_format.py:130-146`, b34e351; [known open items](../../exporter-guide/sidecars/known-open-items.md#known-open-items-for-the-exporter-overhaul))
- The 100 detections for each image in the RF-DETR accuracy runs come from the evaluator cap (`max_dets` 100) after the 300-pair top-k. The cap is not a sidecar field and it is not part of the selection. (Roboflow-Exporter `rf_detr/ACCURACY_CONTRACT.md:57-64` and `rf_detr/model_report.py:206-215`, 4ae67c0)
- RF-DETR graph parity (nano, batch 1, COCO val2017, 5,000 images, ONNX Runtime CUDA provider, threshold 0.0, `num_select` 300, `max_dets` 100): PyTorch AP 0.480397 and AP50 0.671185. The fp32 ONNX gives AP 0.480287 and AP50 0.671145 (delta AP -0.00011). The fp16 ONNX gives AP 0.48023 (delta AP -0.000167). All passes use the same preprocessing, so the numbers show graph parity under that preprocessing. (Roboflow-Exporter `exports/detectors/object_detectors/rfdetr/rfdetr-nano_b1_fp32.onnx.model.report.json` and `rfdetr-nano_b1_fp16.onnx.model.report.json`, fields `scoring.accuracy.passes[*].metrics.values.ap` and `scoring.accuracy.comparisons[0].deltas`, untracked, HEAD c64fd2a; `rf_detr/ACCURACY_CONTRACT.md:31-38`, 4ae67c0)

## Authoring guidance

- RF-DETR: `selection: top_k` and `top_k: 300` come from `num_select` (300 queries x 91 logits = 27,300 candidate pairs). `boxes_output: dets` and `class_logits_output: labels` come from the identity outputs. The sidecar writes no `max_detections`, no `nms`, no `scores_output` and no `score_field`. (Roboflow-Exporter `rf_detr/sidecar.py:271-278`, `rf_detr/identity.py:13, 27-28` and `tests/test_sidecar.py:160-170`, b34e351)
- A TopK node inside the graph is not `selection: top_k`. The YOLO26 graph has 2 TopK nodes and 3 GatherElements nodes (nano b2 detector, from `Detect.get_topk_index`). It picks the 300 rows inside the graph, so its host selection is `none`. (Ultralytics-Exporter `exports/detectors/object_detectors/yolo26/yolo26-nano_b2_fp32.onnx`, untracked, HEAD 2e0280e; ultralytics 8.4.184 `nn/modules/head.py:266-288`, installed copy in the Ultralytics-Exporter `.venv`; `yolo_sidecar.py:467-478`, f52ef68)

# Z0CC — Exporter coverage measurements: RF-DETR graph checks, RTMDet AP, export defects of 2026-10

**Status:** evidence, 2026-11-12 (the retired note `notes/sidecar-exporter-coverage.md`, last
revised 2026-10-20).

## Decision

This entry keeps the measurements and the checks of the exporter coverage note that no other file
holds. The note was the plan of the first spec revision. The spec now states its spec changes. The
note is in the git history of this repository. Each fact below is of the exporter code of
2026-10-19 to 2026-10-20. The exporters are re-implemented later, so a code fact can be out of date.

1. **RF-DETR graphs (Roboflow-Exporter, 24 artifacts: nano 384, small 512, medium 576, large 704;
   batch 1 to 3; fp32 and fp16).** Checked in the ONNX graphs and the decode code:
   - Input `input` `[B,3,S,S]` float32. Outputs `dets` `[B,300,4]` and `labels` `[B,300,91]`,
     float32. fp16 artifacts keep float32 I/O.
   - No normalization in the graph (`input` → `Cast` → patch-embed `Conv`). The host feeds
     ImageNet-normalized RGB.
   - No decode and no `NonMaxSuppression` in the graph. The only `TopK` (K=300) is the query
     selection of the encoder.
   - Stretch resize, bilinear, half-pixel centres, no antialias. `dets` are normalized `cxcywh`.
   - Decode: sigmoid, then a stable top-300 over queries × classes (ties by ascending flat index,
     `lexsort`), then `query = i // C`, `class = i % C`, then a clamp to the image. The threshold
     applies after the top-k, with `>`.
   - 91 slots. The slot index is the COCO category id. Slot 1 is person. No slot is excluded before
     the top-k.
2. **RTMDet resize and NMS (`rtmdet-tiny_b1_fp32.onnx`, first 500 COCO val2017 images,
   onnxruntime CPU, cv2, faster-coco-eval).**

   | Preprocessing | NMS (score / IoU / max) | Category ids | AP | AP50 |
   |---|---|---|---|---|
   | letterbox (mmdet rules) | 0.001 / 0.65 / 300 | `cat_ids[label]` | 0.449 | 0.615 |
   | letterbox | 0.001 / 0.65 / 300 | `label + 1` | 0.067 | 0.096 |
   | letterbox | 0.05 / 0.6 / 100 | `cat_ids[label]` | 0.448 | 0.616 |
   | stretch | 0.001 / 0.65 / 300 | `cat_ids[label]` | 0.437 | 0.603 |

3. **COCO category defect (OpenMMLab-Exporter).** `evaluate_pkl` wrote `category_id = label + 1`.
   This is correct only for a person-only model. Each reported COCO-80 RTMDet AP was invalid: tiny
   0.066 (PyTorch) and 0.005 (ONNX), against a model-zoo AP of about 0.41. Person-only results were
   correct (`rtmdet-person-nano` 0.349 and 0.348). The ONNX path lost more than the defect explains
   (0.005 against 0.067 on the same artifact). The cause was not found.
4. **In-graph caps (OpenMMLab-Exporter).** The deploy configs set `post_processing` at the top level.
   mmdeploy reads only `codebase_config.post_processing`, so the `base_static.py` defaults
   `pre_top_k=5000` and `max_output_boxes_per_class=200` went into the graph.
5. **RTMW sizes (analysis, no export).** mmpose `input_size` and mmdeploy
   `onnx_config.input_shape` are (width, height). The registry read them as (height, width), and
   `export_fp32.py` passed (height, width) to mmdeploy. The two errors cancel in the graph, but the
   sidecar shape and the benchmark inputs were transposed.
6. **YOLO26 (Ultralytics-Exporter).** The pose model has one output `[N,300,57]`: 6 detection
   columns and 17 × (x, y, score). int8 artifacts take float32 input. The letterbox puts the image in
   the centre, rounds the new size half-even, and gives `top = round(d/2 − 0.1)`, which is
   `floor(d/2)`. mmdet `_scale_size` rounds half-up (`int(x·s + 0.5)`).

## Reason

- [ADR-5WKW](5WKW-implementation-work-in-the-plan.md) item 5 and
  [ADR-2XW6](2XW6-process-entries-consolidation.md) item 7: copy the unique measurements of the
  note to an evidence entry, then retire the note at the end of the spec-build stage.
- [ADR-b9fm](b9fm-finished-sidecar-plans.md) names the unique evidence: the RF-DETR graph checks and
  the RTMDet measurement on 500 images.

## Evidence

- Source: `notes/sidecar-exporter-coverage.md`, last revised 2026-10-20, in the git history of this
  repository. The note gives no exporter commit.
- The letterbox and stretch AP values are also in
  [Letterbox resize](../../specs/model-sidecar/pre/resize-letterbox.md#authoring-guidance).
- The experiment scripts were in a session scratchpad. They are not kept.

## Not repeated

- Item 5 was not checked on a real RTMW graph. The spec examples now use `[-1,3,256,192]`.

# Q6W6 — Strict `>` in each score comparison of the detection decode

**Status:** absorbed into [`post/detection-decode.md#selection-behaviour`](../../post/object/decode.md#selection-behaviour), 2026-11-06 (user; PR: pending).

## Decision

The user chose the option "Keep >, state it (Recommended)": "Spec states that strict > is
intended in every comparison and names the >= difference of qai_hub_models in Implementer
guidance. No vector changes (the vectors already pin strict >)."
At acceptance, the user chose the option "Guidance only, non-spec (Recommended)": "Implementer
guidance states the strict > is intended and names the >= upstreams (qai_hub_models, MediaPipe).
No normative change, no changelog row, no vector change."

1. Each score comparison of the detection decode stays strict (`>`). A score equal to
   `nms.score_threshold` or to `confidence_threshold_default` does not pass. This is intended.
2. The normative text does not change.
   [Selection behaviour](../../post/object/decode.md#selection-behaviour) already makes each
   score comparison strict.
3. The Implementer guidance of
   [Detection decode](../../post/object/decode.md#implementer-guidance) names the upstreams that
   use `>` and the two that use `>=`. The `qai_hub_models` bullet of
   [Selection: NMS](../../post/object/selection-nms.md#implementer-guidance) cites this entry, not the
   spec-defect item.
4. No vector changes. The current cases pin each strict comparison.
5. It deletes the `confidence_threshold_default` item of the
   [spec defects](../open-work.md#spec-defects).
6. The change is a non-spec commit. It adds no changelog row and no `Row` line.

## Reason

- Four of the six upstream decoders that the exporters use compare with `>`. The ONNX
  `NonMaxSuppression` operator also uses `>`. The spec mirrors this majority.
- The difference changes only a score that is exactly equal to its threshold. A change to `>=`
  would change the vectors and the reference code for no measured gain.
- The spec defect asked only if the strict `>` is intended. The guidance now says so.

## Consequences

- A sidecar of an upstream that uses `>=` keeps a different result for a score exactly at the
  threshold. The MediaPipe person detector of Qualcomm-Exporter is such a sidecar: its upstream
  keeps a score of exactly 0.75, and the host drops it.
- No example changes. No exporter must regenerate a sidecar.
- The package code under `skellytracker/` already uses `>` for the detection score thresholds.
  The implementation plan gets no item.

## Evidence

Upstreams with `>`:

- mmdet 3.3.0 (the pin of OpenMMLab-Exporter): `filter_scores_and_topk`
  ([`mmdet/models/utils/misc.py:332`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/utils/misc.py#L332)),
  which RTMDet calls through `BaseDenseHead._predict_by_feat_single`
  ([`mmdet/models/dense_heads/base_dense_head.py:391-395`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/dense_heads/base_dense_head.py#L391-L395)).
  The pin: OpenMMLab-Exporter
  [`mmdeploy-convert/Dockerfile.exporter:33-44`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/5411f455842d16ca31194948f4d57601cc0ae092/mmdeploy-convert/Dockerfile.exporter#L33-L44).
- mmpose 1.3.2 (RTMO): `filter_scores_and_topk`
  ([`mmpose/models/utils/misc.py:54`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/models/utils/misc.py#L54)),
  called by `RTMOHead.predict` with `score_thr`
  ([`mmpose/models/heads/hybrid_heads/rtmo_head.py:965-970`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/models/heads/hybrid_heads/rtmo_head.py#L965-L970)).
- ultralytics 8.4.184: `mask = pred[:, 4] > conf_thres` for the end-to-end rows (`utils/nms.py:74`,
  installed copy in the Ultralytics-Exporter `.venv`).
- rfdetr 1.11.2: `scores_i > score_threshold` (`models/postprocess.py:223`) and
  `scores > threshold` (`detr.py:3134`), installed copy in the Roboflow-Exporter `.venv`.
- onnx 1.22.0 reference `NonMaxSuppression`: `class_scores[box_index] > score_threshold`
  (`onnx/reference/ops/op_non_max_suppression.py:224`, installed in the skellytracker `.venv`).

Upstreams with `>=`:

- `qai_hub_models` 0.64.0: `batched_nms` keeps `scores >= score_threshold`
  (`utils/bounding_box_processing.py:85-86`). The MediaPipe app passes `min_detector_box_score`
  (`models/templates/mediapipe/app.py:348-352`). The pose app sets it to 0.75
  (`models/mediapipe_pose/app.py:69, 144`). Installed copy in the Qualcomm-Exporter `.venv`. The sidecar
  of Qualcomm-Exporter writes 0.75 as `confidence_threshold_default`
  ([`qai_catalog.py:59`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_catalog.py#L59);
  [`qai_sidecar.py:132`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L132)).
- MediaPipe v1.1.1 (the pin of MediaPipe-Exporter): `TensorsToDetectionsCalculator` skips only
  `scores[i] < options_.min_score_thresh()`
  ([`mediapipe/calculators/tensor/tensors_to_detections_calculator.cc:935-936`](https://github.com/google-ai-edge/mediapipe/blob/e9794ef55e2509c09aa8b6ba1764b797db8eb200/mediapipe/calculators/tensor/tensors_to_detections_calculator.cc#L935-L936)).

## Alternatives rejected

- Change each comparison to `>=`. Most upstreams use `>`, and each strict vector would change.
- A sidecar field that selects `>` or `>=`. It adds a field for a one-value difference.

## Not repeated

- The first strict rule cited mmdet from memory
  ([`notes/sidecar-exporter-coverage.md`](../../../../notes/sidecar-exporter-coverage.md), "Make every
  score threshold"). The mmdet line above is now checked.

_Edited 2026-11-11 (this PR): link repair._

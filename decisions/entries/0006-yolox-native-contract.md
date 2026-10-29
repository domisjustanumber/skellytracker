# 0006 — The YOLOX sidecar describes the native ONNX contract

**Status:** absorbed into [`format/versioning.md#implementer-guidance`](../../specs/model-sidecar/format/versioning.md#implementer-guidance), 2026-10-25 (user; the absorption review).
[specs/sidecar-implementation-plan.md](../../specs/sidecar-implementation-plan.md#key-decisions), "Key decisions" item 5).

## Decision

- `skellytracker/core/detectors/object_detectors/yolox/yolox.yaml` describes the `dets` output of the
  YOLOX checkpoint that the OpenMMLab download publishes. It does not describe the graph that the
  detector runs.
- The sidecar declares:
  - one `detections` output with `fields: [x1, y1, x2, y2, score]`;
  - `decode.box_format: xyxy`, `decode.score_field: score`, `decode.person_class_id: 0`,
    `decode.requires_nms: false` and `decode.confidence_threshold_default: 0.7`;
  - `input.normalization: none` and a `letterbox` resize with `preserve_aspect_ratio: true`,
    `pad_value: 114` and `interpolation: linear`;
  - the sizes `yolox-tiny` (416 x 416) and `yolox-m` (640 x 640), each with a `filename` and a
    `url_sha256`.
- The graph surgery stays in Python: `prepare_yolox_onnx` in `_yolox_dynamic_batch.py`. It makes the
  batch dimension dynamic and removes the NMS subgraph. No YAML field describes it.
- The choice of decode stays in Python: `yolox_detection_decode` in `yolox_decode.py`. It reads the
  output shapes of the loaded graph. No YAML field describes it.

## Reason

- The graph that the detector runs after the surgery has two outputs: pre-NMS boxes and scores.
  At `schema_version` `v2024.09.1019`, one `detections` output with `fields` cannot describe two
  tensors. The `boxes` and `scores` semantics are available only at `vNEXT`
  ([Version-aware compatibility](../../specs/model-sidecar/format/versioning.md#legacy-behaviour)).
- The sidecar therefore describes the `dets` output of the published graph: one row of five fields per
  detection. It omits the `labels` output and uses its own tensor names (see Evidence). The surgery is
  an implementation detail of the detector. Nothing declarative described it before the migration, and
  the migration did not change this.
- The decode math is the same as before the migration. The migration aims at no functional change.
  Decision [0004](0004-detectors-migrated-in-place.md) records the in-place migration.

## Evidence

Checked in the code and in the cached model files on 2026-10-22.

- The published graph and the two graphs that the surgery writes. The cache folder is
  `~/.cache/skellytracker/models`. Both sizes show the same structure. The table shows `yolox-m`.

  | File | Input | Outputs | `NonMaxSuppression` nodes |
  |---|---|---|---|
  | `yolox-m_b1_fp32.onnx` (published) | `input` `[1, 3, 640, 640]` | `dets` `[1, ?, 5]`, `labels` `[1, ?]` | 1 |
  | `yolox-m_b1_fp32.onnx.dynbatch_v2.onnx` | `input` `[N, 3, 640, 640]` | `dets`, `labels`, `_db_conf_prenms`, `_db_bbox_prenms` | 1 |
  | `yolox-m_b1_fp32.onnx.prenms.onnx` (the session loads this file) | `input` `[N, 3, 640, 640]` | `_db_bbox_prenms`, `_db_conf_prenms` | 0 |

  The two pre-NMS outputs have no declared shape.
- `YoloxPersonDetector.model_spec` passes `prepare=prepare_yolox_onnx` to `sidecar_model_spec`.
  `OnnxSession.create()` calls the function after it resolves the file. `prepare_yolox_onnx` chains
  `ensure_dynamic_batch` and `ensure_prenms_model`. It returns the dynamic-batch file when the graph
  has no NMS to remove.
- `yolox_detection_decode` chooses the decode from the loaded graph:
  - two outputs: `decode_prenms`, with NMS on the host (`multiclass_nms`);
  - any other number of outputs: the last dimension of the first output selects the decode.
    The value 5 selects `decode_nms_baked_in`. The value 4 selects `_decode_yolox_raw_anchor_grid`.
    Any other value raises `RuntimeError`.
- `_decode_yolox_raw_anchor_grid` builds anchor grids for the strides 8, 16 and 32 from the model input
  size. It runs `multiclass_nms`. It keeps person detections with a score above the constant 0.3 in
  the code.
- The code does not read `decode.requires_nms` or `decode.confidence_threshold_default`. Outside the
  tests, only `core/sidecar/model.py` mentions them. The thresholds come from `YoloxPersonDetectorConfig`:
  `score_threshold: 0.7`, `nms_threshold: 0.45` and `max_detections: 1`.
- The names in `yolox.yaml` are not the tensor names of the published graph. The sidecar declares the
  input `images` and the output `detections`. The graph has the input `input` and the outputs `dets`
  and `labels`. The detector reads the input name from the session (`get_inputs()[0].name`) and uses
  the outputs by position. It never uses the names in the sidecar.
- The sidecar has the legacy `schema_version` `v2024.09.1019`. For a legacy sidecar, `requires_nms:
  false` derives `decode.selection: none`. See
  [Version-aware compatibility](../../specs/model-sidecar/post/detection-decode.md#legacy-behaviour).

## Not repeated

- Do not run YOLOX through a generic sidecar-driven detector. The generic path cannot run YOLOX. No
  spec section describes the graph surgery, the choice of decode from the output shapes of the loaded
  graph, or the decode of the raw anchor grid. Decision [0016](0016-sidecar-catalogs.md) records that
  YOLOX claims its catalog key, so that the generic path never handles it.
- Do not read `requires_nms: false` as "the detector runs no NMS". The published graph has NMS inside
  it. The surgery removes it. The detector then runs NMS on the host.
- Do not treat the tensor names in `yolox.yaml` as the names in the graph.

_Edited 2026-10-26 (this PR): link repair._

_Edited 2026-10-28 (this PR): link repair._

_Edited 2026-10-29 (this PR): link repair._

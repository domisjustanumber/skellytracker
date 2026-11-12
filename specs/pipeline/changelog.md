# Changelog

This file records each content change of the pipeline spec. It starts with the first content commit
([ADR-3SF2](../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 5). The form of
the lines is the form of the [sidecar changelog](../model-sidecar/changelog.md#revisions).

## Summary of changes

| # | Area | Change | Driven by | Section |
|---|------|--------|-----------|---------|
| 1 | Pipeline | Draft pipeline spec: the six pipeline sections and the ten node sections. | [ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md), [ADR-99MH](../../decisions/entries/99MH-pipeline-outputs-and-running.md), [ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md), [ADR-8NVD](../../decisions/entries/8NVD-pipeline-api-warnings-and-catalog.md), [ADR-3SF2](../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) | [Section map](README.md#section-map) |
| 2 | Pipeline | The decisions of the first review. Sidecar vocabulary: `score`, `point_names`, `edges`, `port_type`, `instance_source`, tap `action`, redetect `check`, `expand_ratio`, `previous_weight`, `object_decode`, `derived_points` in the sidecar map form, `source: {name, version}` with the sidecar catalog key rules, and the `mediapipe_tasks` params `min_detection_score`, `min_presence_score`, `min_tracking_score`, `size` and `variant: body`. New node type `merge`. Prefixed point names in each param (`V-pipeline.graph-8`). `first_of` and `concat` take a list. An empty optional input does not stop a node; `concat` runs with an empty input and gives missing points in its columns. `V-node.detector-2` uses `keypoint.estimator_type`. A `mediapipe_tasks` output is `3d` with `depth_unit: pixel`. The type of an `any` output comes from its inputs. I > 1 everywhere, and crop batches of k × cameras × I. ROI rotation in radians, clockwise, in [−π, π). The crop order of the detector node; a rotated crop waits for a sidecar proposal. Outputs: no `measured`, `instance_score` of each `roi` and `keypoints` row from its instance source row, a value table for `roi`, `class_index` of each detections row with `class_names` in the output schema, `geometry` and `depth_unit`, padding values, `image_size` (width, height), `frame_index`, no `@prev` or frame port in an output or a tap. `fps` run parameter; `timestamp_ms` required in `live`; no frame interval. Timing events with `images`; header with `skellytracker_version`, `clock`, `anchor` and no `mode`; `pipeline_sha256` and `image_list_sha256` bytes. Tap layout and `tap.json` with `upstream_sha256` and the match rules; each tap line has its `row`; a keypoints or roi line has `score` = `instance_score`; a detections line has `class` in place of `category_id`. `smooth_keypoints` in time units: `max_gap_ms`, `reset_after_ms`, no back-off; `V-node.smooth_keypoints-2` removed. New rules `V-pipeline.running-6`, `V-pipeline.taps-5`, `V-pipeline.taps-6`, `V-pipeline.taps-7`, `V-node.roi_from_points-5`, `V-node.roi_tracking-2`, `V-node.first_of-2`, `V-node.concat-3` and `V-node.merge-1` to `-3`. | [ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md), [ADR-99MH](../../decisions/entries/99MH-pipeline-outputs-and-running.md), [ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md), [ADR-88WQ](../../decisions/entries/88WQ-sidecar-vocabulary.md), [ADR-6JWJ](decisions/entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md) | [Section map](README.md#section-map) |
| 3 | Detector | The `detector` node crops a rotated ROI: the sidecar crop `affine_crop` takes the ROI with its rotation. A box is an ROI with rotation 0. | user decision 2026-11-12 ([ADR-G3FA](../model-sidecar/decisions/entries/G3FA-affine-crop-rotated-roi.md)) | [Node: detector](nodes/detector.md#behaviour) |
| 4 | Running | EP keys from the EP catalog (`trt-rtx`, not `tensorrt`). The run parameter EP options and the `detector` param `ep_options`. A run never uses another EP than the requested EP: an EP that is not available or does not start stops the start. The warning `ep_partial_placement` replaces `ep_fallback`. The NMS session requests `cpu`. The timing `execution` block has `cpu_nodes` and `cpu_op_types`; the CLI has `--ep-option`. | [ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md), [ADR-48PG](../../decisions/entries/48PG-pipeline-api-ep-options-and-warnings.md) | [Running](running.md#behaviour), [Node: detector](nodes/detector.md#behaviour), [Timing](timing.md#fields) |
| 5 | Running | No session sharing: a run owns its sessions, and each node builds its own. The timing node item loses `shared_with`. `V-pipeline.running-4` checks the EP key against the EP catalog and each EP option against its allow-list. The citations of ADR-99MH go to ADR-0WJB, also in `V-node.concat-2`. | [ADR-0WJB](../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md), [ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) | [Running](running.md#behaviour), [Timing](timing.md#fields) |
| 6 | Running | Session sharing only inside one run: the nodes of one run with the same artifact, batch, EP key, EP options and device share one session; no session is shared between runs. The timing node item has `shared_with` again. The citations of ADR-0WJB go to ADR-ZYS9, also in `V-node.concat-2`. | [ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) | [Running](running.md#behaviour), [Node: detector](nodes/detector.md#implementer-guidance), [Timing](timing.md#fields) |
| 7 | Running | The run parameters device (one GPU key or a list; the run uses exactly those GPUs; default: each GPU that qualifies) and VRAM reserve (default 1 GiB, on each GPU of the run). Batch k comes from the free VRAM of each GPU minus the reserve. The CLI has a repeatable `--device`. The citations of ADR-48PG go to ADR-V7GZ, also in the `mediapipe_tasks` params table and the schema, and the citations of ADR-AQR4 go to ADR-0XW9. | [ADR-V7GZ](../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md), [ADR-P1F3](../../decisions/entries/P1F3-hardware-probe-devices-and-multi-gpu.md) | [Running](running.md#fields), [Timing](timing.md#implementer-guidance) |

## Revisions

A spec version is the skellytracker version, in SemVer, that first releases a spec change. Each
heading below is one spec version. The open target is the next skellytracker release that includes
a spec change ([ADR-6GE2](../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).

Each version heading has these lines:

- `- Released: no.` or `- Released: yes.`: the first line. The open target has `no`.
- ``- Row N: `<fingerprint>`.``: each content commit appends one such line under the open target,
  with no version bump. `N` is the highest row number of the
  [summary of changes](#summary-of-changes). The fingerprint is the SHA-256 of the headings and the
  `V-` rule lines of the section files of this spec. `tools/tests/test_pipeline_changelog.py`
  checks it. When the value is not current, that test fails and gives the new value.
- `- Pre-release X.Y.Z-<tag>: row N.`: the session of a skellytracker pre-release appends this
  line under its target. `N` is the last row that the pre-release holds.

### 2.0.0

- Released: no.
- Row 1: `c1c50d709ebb29d3fa6e100452a6635f0d9a41e4b181a79b9ef7600de471817f`.
- Row 2: `17bec6f1ff03d85db76923100e7d0f121a51a257b62cac76cfd459351a4b9952`.
- Row 3: `17bec6f1ff03d85db76923100e7d0f121a51a257b62cac76cfd459351a4b9952`.
- Row 4: `17bec6f1ff03d85db76923100e7d0f121a51a257b62cac76cfd459351a4b9952`.
- Row 5: `7426a5b07aeab25bb91ffb31706909e00d329c7520d13abcc3fb078406b21df2`.
- Row 6: `45d0f788ad97dae170e2e187ac451dfbb5a8aed4ae6bff8c54b37d1480684d57`.
- Row 7: `45d0f788ad97dae170e2e187ac451dfbb5a8aed4ae6bff8c54b37d1480684d57`.

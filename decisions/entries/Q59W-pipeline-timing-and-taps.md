# Q59W — Pipeline instrumentation: fixed timing points, JSONL events with a header, record and replay taps, and a CLI run for skellybench

**Status:** superseded by [0WTV](0WTV-system-metrics-and-pipeline-timing-helper.md), 2026-11-12 (user; PR: pending).

## Decision

1. **Timing points.** The points are fixed for each node type: `preprocess`, `inference` and
   `postprocess` for a detector node, with the boundaries of OpenMMLab-Exporter ADR-W9RE, and `run`
   for each other node. The reserved node id `pipeline` gives one `run` point for each frame call.
   The `instrumentation:` block selects the points. The run argument `timing="off"` turns them off.
   The run argument `timing_sink` is the destination.
2. **Event.** A frozen record for each point: `images` (one `{frame_index, camera_id}` for each image
   of the call), `node_id`, `point`, `batch_size` (the length of `images`), `start_ns` and `end_ns`
   (`perf_counter_ns`). A node that does not run and a warm-up pass give no event.
3. **JSONL.** A header line starts each run and process: `schema` (`skellytracker.timing/1`),
   `run_id`, `skellytracker_version`, `clock` (`name`, `implementation`, `resolution_ns` from
   `time.get_clock_info`), `anchor` (`perf_counter_ns`, `unix_ns`), `running_mode`,
   `warmup_passes`, `image_list_sha256`, `camera_ids`, `pipeline_sha256` (canonical JSON of
   `schema_version`, `nodes` and `outputs`), `points_on` and `nodes`. Each node item has `id`,
   `type`, `batching`, `inputs` with a `prev` flag, `key`, `sidecar_sha256`, `artifact_sha256`,
   `size`, `precision`, `execution` (`requested_ep`, `used_ep`, device,
   `gpu_uuid`, `ep_device_id`, the EP options that change numbers), `stage_providers` and
   `shared_with`. A session that changes during a run writes a new header.
4. **Derived values.** Helpers outside the hot path derive a task id, the parents and
   `duration_ms`. A helper in `core/metrics/` aggregates the events to the skellybench timing
   record: `stages_ms_per_image` is the sum of the model point times (detector and
   `mediapipe_tasks`) divided by the sum of `batch_size`. Glue `run` time goes to
   `excluded_ms_per_image`. Until skellybench has stages of several nodes, a pipeline is measured one
   detector node at a time, with its upstream outputs replayed.
5. **Taps.** The tap `action` `record` writes the value of a port during the run. `replay` reads the
   value of a port from files, and the upstream nodes do not run. The run argument `tap_dir` is the
   folder, with one sub-folder for each tap. There is no default folder in the repository. Crops and
   tensors of dataset images must not be committed.
   - `<port_type>.jsonl`: COCO result records (`detections`), COCO keypoint records (`keypoints`) or
     `roi:[cx,cy,w,h,rotation]` (`roi`), present rows only, in row order. `image` and `tensor`: one
     `<image_id>.npy` file for each image.
   - Each row has `image_id`, `frame_index` and `camera_id`. For video, `image_id` is
     `frame_index × n_cameras + camera_index`.
   - A record writes `tap.json` last. It holds `upstream_sha256` (canonical JSON of the configs of
     the tapped node and of each node upstream of it), `image_list_sha256`, `camera_ids`,
     `running_mode`, each node's `sidecar_sha256`, `artifact_sha256` and `used_ep`, and
     `record_count`. A replay refuses a tap where one of these does not agree, or with no
     `tap.json`, or with a null image-list hash. The device is information only.
6. **CLI for skellybench.** skellybench runs `python -m skellytracker run --pipeline … --coco
   <annotations.json> --images <dir> --out … [--ep …] [--timing on]` as a subprocess. The timing and
   tap files are the contract. v1 has only the COCO form: one camera, `image_id` from the COCO file.
   `image_list_sha256` is the SHA-256 of the sorted `image_id` values joined with `\n`.
7. **Glue ownership.** The pipeline spec of skellytracker owns the glue node definitions and their
   reference implementations. The skellybench templates are a separate concern of skellybench.

## Reason

- skellybench takes aggregates, not raw events. Its stages are `preprocess`, `inference` and
  `postprocess`, and its only image key is the COCO `image_id`. It does not compute
  `image_list_sha256`; the producer supplies it.
- skellybench does not import onnxruntime. A subprocess keeps its environment free of the runtime.
- skellybench has no video input and no runner yet. freemocap calls `start_pipeline` in its process,
  not the CLI.
- A manifest check stops a replay of outputs from another model, EP or image list.

## Alternatives rejected

- A report of partial op placement on providers in v1.
- skellybench as the owner of the glue operators, and an in-process import by skellybench.
- A video or manifest input form for the CLI in v1.

## Open work

See [open-work.md](../open-work.md).

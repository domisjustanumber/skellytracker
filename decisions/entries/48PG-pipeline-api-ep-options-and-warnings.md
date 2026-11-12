# 48PG — Pipeline API `core.pipelines` with EP options; built-ins; warnings with `ep_partial_placement`; dependency reports; Holistic for MediaPipe; the node catalog

**Status:** superseded by [V7GZ](V7GZ-pipeline-api-device-and-vram-reserve.md), 2026-11-12 (user; PR: pending).

## Decision

This entry supersedes [ADR-8NVD](8NVD-pipeline-api-warnings-and-catalog.md) in full. Items 2 to 5
and 7 to 9 restate 8NVD items 2 to 5 and 7 to 9. Items 1 and 6 change: `start_pipeline` takes
`ep_options`, and the warning `ep_partial_placement` replaces `ep_fallback`
([ADR-9NW0](9NW0-ep-keys-options-and-failures.md)).

1. **API.** `skellytracker.core.pipelines` has `list_pipelines() -> list[PipelineEntry]`,
   `load_pipeline(key | path | dict) -> PipelineConfig`, `export_pipeline(config, resolved=False)`,
   `list_node_types()` and `start_pipeline(config, *, camera_ids, running_mode, execution_provider,
   ep_options=None, timing_sink=None, timing="on", tap_dir=None, on_warning=None, user_root=None)
   -> PipelineRun`. `PipelineRun` has `output_schema`, `process`, `process_batch`, `warnings` and
   `close`. The private runtime is `core/pipelines/_runtime/`. `core/tracker/` is not renamed; the
   old run code is deleted later ([ADR-NHM3](NHM3-phases-to-the-exporter-checkpoint.md)). With no
   arguments, `python -m skellytracker` starts the webcam demo.
2. **Keys of pipelines.** Each pipeline file has a required `source:` field. The key is
   `<pipeline_id>@<source>`. When the same key is in two roots, `list_pipelines()` lists both, and a
   load by key is an error that names both paths. A load by path always works.
3. **Built-ins of v2.0.0.** `yolox-rtmw-wholebody` (YOLOX with `post_nms_top_k: 1`, then RTMW),
   `mediapipe-holistic-tasks` and, after the RTMPose replacements and the measurement of its hand
   and face ROI rules, `rtmpose-body-hands-face`. Structure-only spec examples:
   `rtmpose-hand-detector` and `mediapipe-holistic-decomposed`.
4. **MediaPipe node.** One node `mediapipe_tasks` with `variant: pose | hand | face | holistic`. It
   calls the Tasks landmarkers directly and uses the MediaPipe assets of
   [ADR-AQR4](AQR4-detectors-and-pipelines-entry-points.md). The timestamp fix and the safe close go
   into it. `mediapipe-holistic-tasks` replaces both old MediaPipe demo builders. In v1 the node has
   no ROI input. Holistic is single person, so its `max_instances` is 1. The MediaPipe built-in has
   no keypoint parity with the old builders.
5. **Sessions.** The runtime builds each ONNX session with `eps.build_session()`. The `execution`
   facts of the timing header come from that build.
6. **Warnings.** One frozen type `PipelineWarning(code, message, node_ids, details)`. Codes in v1:
   `batch_limited_by_state`, `ep_partial_placement` (a session of the node has nodes on the CPU EP;
   `details` gives the counts) and `missing_dependency`. `PipelineEntry` and the load result carry
   the warnings known before start. `PipelineRun.warnings` has the full list. The run calls
   `on_warning` once for each new warning, from the thread that calls `process_batch`, also during
   the run. The log line uses the same `message`. The Python `warnings` module is not used.
7. **Missing dependencies.** Each entry of `list_detectors()` and `list_pipelines()` has `available`
   and `unavailable_reason`, from `importlib.util.find_spec` with a literal name, the presence of each
   ONNX file and its hash. `load_pipeline` gives a `missing_dependency` warning. `start_pipeline`
   raises `MissingDependencyError(extra, node_ids)` before frame 0. The CLI prints the same message
   and exits with a non-zero code.
8. **Webcam demo.** It runs `start_pipeline` in `live` mode with `--pipeline <key>`, and one generic
   annotator draws each output from `output_schema`. The calibration demos call the standalone
   calibration classes.
9. **Node catalog.** Each node class declares a Pydantic params model (type, range, default,
   description, `live`) and its ports. Five views, all in v1: the JSON Schema
   `specs/pipeline/pipeline.schema.json`, also shipped in the package; `list_node_types()` and
   `python -m skellytracker nodes [--json]`; a spec table for each node type, made by a tool, with a
   doc test that fails when it is out of date; `describe_detector(key)` and
   `python -m skellytracker describe <key>` for an installed model; and
   `python -m skellytracker validate <file>`, which runs the load checks and prints the warnings.

## Reason

- Item 1: a run takes EP options ([ADR-9NW0](9NW0-ep-keys-options-and-failures.md) item 2).
- Item 6: skellytracker never runs a session on another EP, so a used EP that is not the requested
  EP is an error, not a warning (ADR-9NW0 item 4). CPU nodes are reported (ADR-9NW0 item 5).
- An outside author must know the node types, their params and ports, the installed models and
  their params and point names. A schema can hold only what is fixed at release.
- One warning type gives freemocap one channel for each condition that it shows to the user.
- Holistic does the hand and face crops itself. It found a small face on the full frame where
  `FaceLandmarker` found none. Its 478 face points hold each point of the 136-point face contour
  subset ([ADR-MSH0](MSH0-supported-platforms-v2.md)).

## Alternatives rejected

- Old-style MediaPipe classes for Holistic: they keep the old contract alive.
- A built-in `mediapipe-pose-cropped-hands-tasks`: it needs the ROI input, which is later work.
- A source taken from the root (`@user`): a key would change when a file moves.
- Polling only, with no `on_warning` callback.

## Open work

See [open-work.md](../open-work.md).

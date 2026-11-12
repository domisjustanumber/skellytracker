# V7GZ — Pipeline API with `device` and `vram_reserve_bytes`; built-ins; warnings; Holistic; node catalog

**Status:** accepted, 2026-11-12 (user).

## Decision

This entry supersedes [ADR-48PG](48PG-pipeline-api-ep-options-and-warnings.md) in full. It keeps
the item numbers of 48PG. Item 1 changes: `start_pipeline` takes `device` and `vram_reserve_bytes`,
and the CLI takes `--device`. The other items restate 48PG: a link for each rule that a heading
states, and text for each other rule.

1. **API.** `skellytracker.core.pipelines` has `list_pipelines() -> list[PipelineEntry]`,
   `load_pipeline(key | path | dict) -> PipelineConfig`, `export_pipeline(config, resolved=False)`,
   `list_node_types()` and `start_pipeline(config, *, camera_ids, running_mode, execution_provider,
   ep_options=None, device=None, vram_reserve_bytes=2**30, timing_sink=None, timing="on",
   tap_dir=None, on_warning=None, user_root=None) -> PipelineRun`. `PipelineRun` has
   `output_schema`, `process`, `process_batch`, `warnings` and `close`. `ep_options`:
   [ADR-9NW0](9NW0-ep-keys-options-and-failures.md) item 2. The private runtime is
   `core/pipelines/_runtime/`. `core/tracker/` is not renamed. The old run code is deleted later
   ([ADR-NHM3](NHM3-phases-to-the-exporter-checkpoint.md)). With no arguments,
   `python -m skellytracker` starts the webcam demo.
   - `device` takes one GPU key or a list of GPU keys. The run then uses exactly those GPUs. With
     `device=None`, the run uses each GPU that qualifies
     ([ADR-P1F3](P1F3-hardware-probe-devices-and-multi-gpu.md)).
   - `vram_reserve_bytes` (default 1 GiB) is the VRAM that the run leaves free. The caller sets it
     for skellycam and the player. The run sizes batch k from
     `free_vram(device)` minus the reserve
     ([ADR-ZYS9](ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 4). For now, the
     reserve applies on each GPU that the run uses.
   - The pipeline CLI takes `--device`, with the values of `device`.
2. **Keys of pipelines.** [Pipeline file: Fields](../../specs/pipeline/file.md#fields) and
   [Behaviour](../../specs/pipeline/file.md#behaviour).
3. **Built-ins of v2.0.0.** `yolox-rtmw-wholebody` (YOLOX with `post_nms_top_k: 1`, then RTMW),
   `mediapipe-holistic-tasks` and, after the RTMPose replacements and the measurement of its hand
   and face ROI rules, `rtmpose-body-hands-face`. Structure-only spec examples:
   `rtmpose-hand-detector` and `mediapipe-holistic-decomposed`.
4. **MediaPipe node.** [MediaPipe Tasks node](../../specs/pipeline/nodes/mediapipe_tasks.md#mediapipe-tasks-node),
   with its [Fields](../../specs/pipeline/nodes/mediapipe_tasks.md#fields),
   [Behaviour](../../specs/pipeline/nodes/mediapipe_tasks.md#behaviour),
   [Implementer guidance](../../specs/pipeline/nodes/mediapipe_tasks.md#implementer-guidance) and
   [Authoring guidance](../../specs/pipeline/nodes/mediapipe_tasks.md#authoring-guidance).
   `mediapipe-holistic-tasks` replaces both old MediaPipe demo builders.
5. **Sessions.** [Running: Implementer guidance](../../specs/pipeline/running.md#implementer-guidance).
6. **Warnings.** [Running: Fields](../../specs/pipeline/running.md#fields),
   [Behaviour](../../specs/pipeline/running.md#behaviour) item 8 and
   [Implementer guidance](../../specs/pipeline/running.md#implementer-guidance). Python names: one
   frozen type `PipelineWarning(code, message, node_ids, details)`; `PipelineEntry` and the load
   result carry the warnings known before start; `PipelineRun.warnings` has the full list; the
   warning receiver is `on_warning`.
7. **Missing dependencies.** [Running: Behaviour](../../specs/pipeline/running.md#behaviour) item 8,
   [Validation rules](../../specs/pipeline/running.md#validation-rules) and
   [Implementer guidance](../../specs/pipeline/running.md#implementer-guidance). Each entry of
   `list_detectors()` and `list_pipelines()` has `available` and `unavailable_reason`.
   `start_pipeline` raises `MissingDependencyError(extra, node_ids)` before frame 0. The CLI prints
   the same message and exits with a non-zero code.
8. **Webcam demo.** It runs `start_pipeline` in `live` mode with `--pipeline <key>`, and one generic
   annotator draws each output from `output_schema`. The calibration demos call the calibration
   classes.
9. **Node catalog.** [Pipeline Spec Rules](../../specs/pipeline/AGENTS.md#pipeline-spec-rules) and
   [Generated files](../../specs/pipeline/README.md#generated-files). Five views, all in v1: the JSON
   Schema, also shipped in the package; `list_node_types()` and
   `python -m skellytracker nodes [--json]`; the node tables, with a doc test for drift;
   `describe_detector(key)` and `python -m skellytracker describe <key>` for an installed model;
   `python -m skellytracker validate <file>`, which runs the load checks and prints the warnings.

## Reason

- Item 1: the user decided on 2026-11-12. The caller knows the other VRAM users, for example
  skellycam and the player. A caller that names a GPU gets only that GPU.
- An outside author must know the node types, params, ports, installed models and point names. A
  schema holds only what is fixed at release.
- One warning type gives freemocap one channel for each condition that it shows to the user.
- Holistic does the hand and face crops itself. It found a small face on the full frame where
  `FaceLandmarker` found none. Its 478 face points hold each point of the 136-point face contour
  subset ([ADR-MSH0](MSH0-supported-platforms-v2.md)).

## Alternatives rejected

- A reserve only on the display GPU: it needs a display probe.
- A fixed reserve with no run parameter: only the caller knows the other VRAM users.
- Old-style MediaPipe classes for Holistic: they keep the old contract alive.
- A built-in `mediapipe-pose-cropped-hands-tasks`: it needs the ROI input, which is later work.
- A source taken from the root (`@user`): a key would change when a file moves.
- Polling only, with no `on_warning` callback.

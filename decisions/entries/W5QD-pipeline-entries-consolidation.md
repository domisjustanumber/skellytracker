# W5QD — Consolidation of the pipeline entries

**Status:** accepted, 2026-11-12 (user).

## Decision

This entry supersedes [ADR-7NY2](7NY2-pipeline-form-graph-and-nodes.md),
[ADR-ZYS9](ZYS9-pipeline-outputs-running-sharing-inside-one-run.md),
[ADR-V7GZ](V7GZ-pipeline-api-device-and-vram-reserve.md) and
[ADR-0WTV](0WTV-system-metrics-and-pipeline-timing-helper.md) in full. It changes no decision. Each
item restates one entry: a link for each heading that states a kept rule, and text for each kept
rule that no heading states.

1. **7NY2 (form, graph, nodes).**
   - Headings: [Pipeline file](../../specs/pipeline/file.md#pipeline-file),
     [Graph](../../specs/pipeline/graph.md#graph),
     [Detector node](../../specs/pipeline/nodes/detector.md#detector-node),
     [MediaPipe Tasks node](../../specs/pipeline/nodes/mediapipe_tasks.md#mediapipe-tasks-node),
     each glue node section of [Nodes](../../specs/pipeline/README.md#nodes),
     [Running: Behaviour](../../specs/pipeline/running.md#behaviour),
     [Taps: Implementer guidance](../../specs/pipeline/taps.md#implementer-guidance) and
     [Pipeline Spec Rules](../../specs/pipeline/AGENTS.md#pipeline-spec-rules).
   - Text: `export_pipeline(config, resolved=True)` writes each param; with `False`, it writes the
     config as written. `keypoint_bbox` and `precomputed` are not models. They
     leave the `detectors` list and are deleted with the old run code.
2. **ZYS9 (outputs, running).**
   - Headings: [Outputs](../../specs/pipeline/outputs.md#outputs),
     [Running](../../specs/pipeline/running.md#running), [Graph](../../specs/pipeline/graph.md#graph),
     [Timing: Fields](../../specs/pipeline/timing.md#fields), each node section of
     [Nodes](../../specs/pipeline/README.md#nodes) and
     [Pipeline file: Validation rules](../../specs/pipeline/file.md#validation-rules).
   - Text: `InstanceKeypoints` has `instance(i)`, `single()` and `by_track()`. `start_pipeline`
     takes `camera_ids`, and it is required.
3. **V7GZ (API).**
   - Headings: [Running](../../specs/pipeline/running.md#running),
     [Timing: Implementer guidance](../../specs/pipeline/timing.md#implementer-guidance),
     [Pipeline file](../../specs/pipeline/file.md#pipeline-file),
     [MediaPipe Tasks node](../../specs/pipeline/nodes/mediapipe_tasks.md#mediapipe-tasks-node),
     [Detector node](../../specs/pipeline/nodes/detector.md#detector-node),
     [Pipeline Spec Rules](../../specs/pipeline/AGENTS.md#pipeline-spec-rules) and
     [Generated files](../../specs/pipeline/README.md#generated-files).
   - Text, API: `skellytracker.core.pipelines` has `list_pipelines() -> list[PipelineEntry]`,
     `load_pipeline(key | path | dict) -> PipelineConfig`, `export_pipeline(config,
     resolved=False)`, `list_node_types()` and `start_pipeline(config, *, camera_ids, running_mode,
     execution_provider, ep_options=None, device=None, vram_reserve_bytes=2**30, timing_sink=None,
     timing="on", tap_dir=None, on_warning=None, user_root=None) -> PipelineRun`. `PipelineRun` has
     `output_schema`, `process`, `process_batch`, `warnings` and `close`. The private runtime is
     `core/pipelines/_runtime/`. `core/tracker/` is not renamed. The pipeline CLI takes `--device`.
     With no arguments, `python -m skellytracker` starts the webcam demo.
   - Text, built-ins of v2.0.0: `yolox-rtmw-wholebody` (YOLOX with `post_nms_top_k: 1`, then RTMW),
     `mediapipe-holistic-tasks` and, after the RTMPose replacements and the measurement of its hand
     and face ROI rules, `rtmpose-body-hands-face`. Structure-only spec examples:
     `rtmpose-hand-detector` and `mediapipe-holistic-decomposed`. `mediapipe-holistic-tasks`
     replaces both old MediaPipe demo builders.
   - Text, warnings and dependencies: one frozen type `PipelineWarning(code, message, node_ids,
     details)`. `PipelineEntry` and the load result carry the warnings known before start.
     `PipelineRun.warnings` has the full list. The warning receiver is `on_warning`. Each entry of
     `list_detectors()` and `list_pipelines()` has `available` and `unavailable_reason`.
     `start_pipeline` raises `MissingDependencyError(extra, node_ids)` before frame 0. The CLI prints
     the same message and exits with a non-zero code.
   - Text, demo and catalog: the webcam demo runs `start_pipeline` in `live` mode with
     `--pipeline <key>`. One generic annotator draws each output from `output_schema`. The
     calibration demos call the calibration classes. The package ships the JSON Schema. The other
     views of the node catalog are `list_node_types()`, `python -m skellytracker nodes [--json]`,
     `describe_detector(key)`, `python -m skellytracker describe <key>` and
     `python -m skellytracker validate <file>` (the load checks and the warnings). A doc test
     checks the node tables for drift.
4. **0WTV (metrics, timing).**
   - Headings: [Timing](../../specs/pipeline/timing.md#timing) and
     [Taps](../../specs/pipeline/taps.md#taps).
   - Text: `core/metrics/` holds only system-level live metrics: CPU load, GPU load, VRAM and
     process samples. The CLI run with timing on calls `core/pipelines/timing.py`. A caller can also
     run it on a timing JSONL file. The pipeline spec owns the glue node definitions and their reference
     implementations. The skellybench templates are a separate concern of skellybench.

## Reason

- The user chose this group on 2026-11-12 (question Q19), for the consolidation entry at the gate of
  phase 0 ([Rules](../README.md#rules)).
- The entries of the EP, the hardware, the package and the phases stay. No absorb document states
  their rules yet. The package docstrings absorb them from the implementation stage
  ([ADR-W823](W823-absorb-in-the-commit-group-that-states-the-rules.md)).

## Alternatives rejected

- **Three themed consolidation entries.** The EP and hardware rules do not fit in 6,000
  characters without a change of a rule.
- **No consolidation entry.** The Rules ask for one.

# J4SH — Second consolidation of the pipeline entries: the spec headings and the Python API

**Status:** accepted, 2026-11-23 (consolidation; PR: pending).

## Decision

This entry supersedes [ADR-W5QD](W5QD-pipeline-entries-consolidation.md) in full. It changes no
decision. It keeps the item numbers of W5QD. Each item links the absorb documents of its kept
rules, and writes the text of a kept rule that no absorb document states.

1. **Form, graph, nodes** (from 7NY2).
   - Headings: [Pipeline file](../../specs/pipeline/file.md#pipeline-file),
     [Graph](../../specs/pipeline/graph.md#graph),
     [ONNX model node](../../specs/pipeline/nodes/onnx_model.md#onnx-model-node),
     [MediaPipe Tasks node](../../specs/pipeline/nodes/mediapipe_tasks.md#mediapipe-tasks-node),
     each glue node section of [Nodes](../../specs/pipeline/README.md#nodes),
     [Running: Behaviour](../../specs/pipeline/running.md#behaviour),
     [Taps: Implementer guidance](../../specs/pipeline/taps.md#implementer-guidance) and
     [Pipeline Spec Rules](../../specs/pipeline/AGENTS.md#pipeline-spec-rules).
   - Files: [`loading.py`](../../skellytracker/core/pipelines/loading.py) (`export_pipeline`).
   - Text: `keypoint_bbox` and `precomputed` are not models. They are not in the `detectors` list,
     and they go with the old run code.
2. **Outputs, running** (from ZYS9).
   - Headings: [Outputs](../../specs/pipeline/outputs.md#outputs),
     [Running](../../specs/pipeline/running.md#running), [Graph](../../specs/pipeline/graph.md#graph),
     [Timing: Fields](../../specs/pipeline/timing.md#fields), each node section of
     [Nodes](../../specs/pipeline/README.md#nodes) and
     [Pipeline file: Validation rules](../../specs/pipeline/file.md#validation-rules).
   - Files: [`values.py`](../../skellytracker/core/pipelines/values.py) (`instance(i)` and
     `single()`) and [`run.py`](../../skellytracker/core/pipelines/run.py) (the required
     `camera_ids`).
3. **API** (from V7GZ).
   - Headings: [Running](../../specs/pipeline/running.md#running),
     [Timing: Implementer guidance](../../specs/pipeline/timing.md#implementer-guidance),
     [Pipeline file](../../specs/pipeline/file.md#pipeline-file),
     [MediaPipe Tasks node](../../specs/pipeline/nodes/mediapipe_tasks.md#mediapipe-tasks-node),
     [ONNX model node](../../specs/pipeline/nodes/onnx_model.md#onnx-model-node),
     [Pipeline Spec Rules](../../specs/pipeline/AGENTS.md#pipeline-spec-rules),
     [Generated files](../../specs/pipeline/README.md#generated-files),
     [Layout](../../skellytracker/AGENTS.md#layout) and
     [Code conventions](../../skellytracker/AGENTS.md#code-conventions) (`available` and
     `unavailable_reason`).
   - Files: [`core/pipelines/__init__.py`](../../skellytracker/core/pipelines/__init__.py),
     [`run.py`](../../skellytracker/core/pipelines/run.py) (the signature of `start_pipeline` and
     the members of `PipelineRun`), [`catalog.py`](../../skellytracker/core/pipelines/catalog.py),
     [`loading.py`](../../skellytracker/core/pipelines/loading.py),
     [`warnings.py`](../../skellytracker/core/pipelines/warnings.py),
     [`annotate.py`](../../skellytracker/core/pipelines/annotate.py),
     [`errors.py`](../../skellytracker/core/errors.py),
     [`core/pipelines/cli.py`](../../skellytracker/core/pipelines/cli.py) and
     [`test_pipeline_node_catalog.py`](../../tools/tests/test_pipeline_node_catalog.py).
   - Text: `core/tracker/` is not renamed. With no arguments, `python -m skellytracker` starts the
     webcam demo. The built-ins of v2.0.0 are `yolox-rtmw-wholebody`, `mediapipe-holistic-tasks`
     and, after the RTMPose replacements and the measurement of its hand and face ROI rules,
     `rtmpose-body-hands-face`. `rtmpose-hand-detector` and `mediapipe-holistic-decomposed` are
     structure-only spec examples. The CLI prints the message of `MissingDependencyError` and exits with a non-zero
     code. The calibration demos call the calibration classes.
4. **Metrics, timing** (from 0WTV).
   - Headings: [Timing](../../specs/pipeline/timing.md#timing),
     [Taps](../../specs/pipeline/taps.md#taps),
     [Pipeline Spec Rules](../../specs/pipeline/AGENTS.md#pipeline-spec-rules) and
     [Layout](../../skellytracker/AGENTS.md#layout) (`core/metrics/` and `timing.py`).
   - Text: the CLI run with timing on calls `core/pipelines/timing.py`. A caller can also run it on
     a timing JSONL file. The skellybench templates are a separate concern of skellybench.

### Rules that do not stay

- Item 2, `by_track()`: [ADR-JHB3](JHB3-keypoints-xy-and-z-and-image-width-and-height.md) item 2.
- Item 3, the old signature of `start_pipeline`: `execution_provider=None`
  ([ADR-9PDQ](9PDQ-pipeline-renames-and-the-run-ep.md) item 4), `cpu_threads`
  ([ADR-HB8Z](HB8Z-cpu-threads-run-parameter.md) item 1), and `fps` and `preprocess` (`run.py`).
  `PipelineRun.set_params` ([ADR-N5BM](N5BM-set-during-run-and-set-params.md)).
- Item 3, "YOLOX with `post_nms_top_k: 1`, then RTMW":
  [ADR-RA0E](RA0E-built-in-box-behaviour-of-sfn26.md) item 9.
- Items 1, 2 and 3, the glue nodes, the trigger, the `outputs` block, the port types and the
  annotator: [ADR-9HTX](9HTX-pipeline-node-and-port-redesign.md). The point names:
  [ADR-4MP6](4MP6-pipeline-point-groups-and-canonical-form.md) item 1. The linked headings state
  the new rules.
- Item 3, "`mediapipe-holistic-tasks` replaces both old MediaPipe demo builders": it is open work
  ([ADR-4JAW](4JAW-rulings-of-2026-11-23-on-sessions-the-certify-prompt-and-linux.md) item 5).
- Item 3, `MissingDependencyError(extra, node_ids)`: the error also has `files` and `reason`
  ([`errors.py`](../../skellytracker/core/errors.py)).

## Reason

- Seven later entries changed the text of W5QD with no supersede. The package docstrings now state
  most of its Python API text.

## Open work

See [open-work.md](../open-work.md).

# 9PDQ — Pipeline renames: `onnx_model`, `redetect_trigger`, `roi_hold` and timing spans; the EP of a run

**Status:** absorbed into [`onnx_model.md#onnx-model-node`](../../specs/pipeline/nodes/onnx_model.md#onnx-model-node), [`redetect_trigger.md#redetect-trigger`](../../specs/pipeline/nodes/redetect_trigger.md#redetect-trigger), [`hold_boxes.md#hold-boxes`](../../specs/pipeline/nodes/hold_boxes.md#hold-boxes), [`mediapipe_tasks.md#behaviour`](../../specs/pipeline/nodes/mediapipe_tasks.md#behaviour), [`pipeline/README.md#terms`](../../specs/pipeline/README.md#terms), [`timing.md#fields`](../../specs/pipeline/timing.md#fields), [`running.md#fields`](../../specs/pipeline/running.md#fields), [`running.md#behaviour`](../../specs/pipeline/running.md#behaviour), [`running.md#validation-rules`](../../specs/pipeline/running.md#validation-rules), 2026-11-15 (user; PR: pending).

## Decision

1. **`onnx_model`.** The node type `detector` is now `onnx_model`. Its section ID is
   `node.onnx_model`, its file is `specs/pipeline/nodes/onnx_model.md`, and its rules are
   `V-node.onnx_model-<n>` with the numbers of the old rules. The Terms of the pipeline spec define
   "inference node": a node of the type `onnx_model` or `mediapipe_tasks`.
2. **`redetect_trigger` and `roi_hold`.** The node type `redetect` is now `redetect_trigger`, and
   `roi_tracking` is now `roi_hold`. Their section IDs, files, rule IDs, reference modules and
   vector files take the new names. The rule numbers do not change.
3. **Timing spans.** A "timing point" is now a "timing span". The pipeline field is
   `instrumentation.timing_spans`. The header field `points_on` is now `spans_on`, and the event
   field `point` is now `span`. The attribute of the reference model is `timing_spans`.
4. **The EP of a run.** The EP of the run applies to each `onnx_model` node that has no
   `execution_provider`. A run must give an EP when such a node exists (`V-pipeline.running-8`). A
   run of a pipeline with no `onnx_model` node must not give an EP (`V-pipeline.running-9`). A
   `mediapipe_tasks` node never uses an EP. One pipeline can hold `onnx_model` nodes and
   `mediapipe_tasks` nodes. This changes the required `execution_provider` of `start_pipeline` in
   [ADR-W5QD](W5QD-pipeline-entries-consolidation.md) to `execution_provider=None`.
5. **No alias.** The specs, the skills, the templates, the tools and the plan use only the new
   names. Decided entries, the summaries of `historical.md`, the tracked proposal records and the
   package code before stage 1.10 keep the old names.

## Reason

- A review of the pipeline spec on 2026-11-13 found these names unclear. The user decided each
  item.
- Item 1: the node runs each ONNX model of the sidecar spec, also a keypoint model. "detector" names
  only one kind of model. "inference node" names the two node types that run a model, beside "glue
  node".
- Item 2: the node `redetect` gives a trigger, and the detector runs on it. The node `roi_tracking`
  keeps no state and tracks nothing: it holds the ROI of the last frame when the new ROI is missing.
- Item 3: each event has a start and an end, so it measures a span, not a point.
- Item 4: a pipeline with only MediaPipe nodes runs no ONNX model, so an EP of the run has no use.
  Before this entry, each run had to give an EP.

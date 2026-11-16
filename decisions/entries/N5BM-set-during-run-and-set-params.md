# N5BM — The param mark `set_during_run` and `PipelineRun.set_params`

**Status:** absorbed into [`running.md#behaviour`](../../specs/pipeline/running.md#behaviour), [`running.md#validation-rules`](../../specs/pipeline/running.md#validation-rules), [`running.md#authoring-guidance`](../../specs/pipeline/running.md#authoring-guidance), [`file.md#behaviour`](../../specs/pipeline/file.md#behaviour), [`taps.md#behaviour`](../../specs/pipeline/taps.md#behaviour), [`AGENTS.md#pipeline-spec-rules`](../../specs/pipeline/AGENTS.md#pipeline-spec-rules), [`sidecar-implementation-plan.md#110-the-pipeline-api-was-p`](../../specs/sidecar-implementation-plan.md#110-the-pipeline-api-was-p), 2026-11-16 (user, design review 2026-11-13; PR: pending).

## Decision

1. **The mark.** Each param has the mark `set_during_run` (`true` or `false`). The node tables
   show it in the column `Set during run` as `yes` or `no`. It replaces the mark `live`, because
   `live` is also the name of a running mode.
2. **`set_params`.** `PipelineRun.set_params(node_id, params)` sets the params of one node. It
   checks each value against the type and the range of the param, as the load does. It refuses an
   unknown node, an unknown param and a param with `set_during_run: false`. A change applies from
   the next `process` or `process_batch` call, to each camera.
3. **When.** A run accepts `set_params` in each running mode before the first `process` call.
   After that call, it accepts `set_params` only in `live`, and only when no `record` tap is on. A
   refused call raises `SetParamsRefused` and changes nothing (`V-pipeline.running-10`).
4. **No reset.** A change never resets the state of a node. A param whose change would need a
   reset has `set_during_run: false`, for example `filter`, `reset_after_ms` and `max_gap_ms` of
   `smooth_keypoints`.
5. **Values for each mode.** The caller gives a value for each mode, in the config before the
   start or with `set_params` before the first frame. The pipeline file is the same in each mode.
   For example, `redetect_interval` is 10 in `live` and 1 in `video`.
6. **Release.** `set_params` ships in v2.0.0, as the last step of stage 1.10.

This changes the text "`PipelineRun` has `output_schema`, `process`, `process_batch`, `warnings`
and `close`" of [ADR-W5QD](W5QD-pipeline-entries-consolidation.md) item 3 to "`PipelineRun` has
`output_schema`, `process`, `process_batch`, `set_params`, `warnings` and `close`". It also
changes two rules of the headings that ADR-W5QD item 1 links: [Pipeline file](../../specs/pipeline/file.md#behaviour)
item 1 loses "Live changes of params wait for a later version", and
[Pipeline Spec Rules](../../specs/pipeline/AGENTS.md#pipeline-spec-rules) names
`set_during_run` in place of `live`. The rejected alternative "Live param changes in v1" of
[ADR-7NY2](7NY2-pipeline-form-graph-and-nodes.md) no longer applies.

## Reason

- The user decided items G4a to G4e in the design review of 2026-11-13, and approved this text on
  2026-11-16.
- A live caller tunes a filter or a threshold while it watches the result. A restart loses the
  state of each temporal node.
- One rule for each mode keeps a recorded run repeatable: a `video` run and a run with a `record`
  tap have fixed params after the first frame.
- A change with no reset keeps the rule simple. A param that needs a reset stays fixed for the run.
- The mark `live` and the running mode `live` were two meanings of one word
  ([ADR-88WQ](88WQ-sidecar-vocabulary.md): one name for each concept).

## Alternatives rejected

- **`set_params` in each mode at any time.** A `video` run and a record are then not repeatable.
- **A reset of the node state on a change.** It needs a rule for each node, and a live caller sees
  a jump on each change.
- **A value for each mode in the pipeline file.** The file is the same in each mode. The caller
  knows the mode.

# 75K2 — The text for the unclear places of the pipeline spec

**Status:** absorbed into [`running.md#fields`](../../specs/pipeline/running.md#fields), [`running.md#behaviour`](../../specs/pipeline/running.md#behaviour), [`timing.md#fields`](../../specs/pipeline/timing.md#fields), [`timing.md#implementer-guidance`](../../specs/pipeline/timing.md#implementer-guidance), [`timing.md#authoring-guidance`](../../specs/pipeline/timing.md#authoring-guidance), 2026-11-16 (user, answers to the review of the unclear places and questions K1 and K2, 2026-11-16; PR: pending).

## Decision

1. **Batch k.** The batch on a GPU is k × the camera count of that GPU. In this version, k is 1 on
   each GPU. The run uses the VRAM reserve only for the camera split.
2. **The timing of a node on two or more GPUs.** When a node has a session on each of two or more
   GPUs, the times of the node are the times of all its sessions together. The timing has no part
   for each GPU. `batching`, `execution`, `stage_providers` and `shared_with` of the node item are
   those of the session of the first GPU.
3. **`missing_dependency` with no `precision`.** For a node with no `precision`, a load gives the
   warning only when no artifact of the size is usable. A start checks the artifact of the EP
   (`V-pipeline.running-3`).
4. **The `run` span of MediaPipe.** The `run` span of a `mediapipe_tasks` node counts as the stage
   `inference` of the skellybench timing record. That value includes the preprocessing and the
   postprocessing of MediaPipe.
5. **Threads.** The calls on one run are serial: a second call waits for the first call. `close()`
   waits for the call that runs. A call after `close()` raises an error. A second `close()` does
   nothing. Two runs share no state. There is no cancel.
6. **No timing parents.** An event has no field for its parents, and no helper gives them. The gate
   of stage 1.10 of the implementation plan does not test them.
7. **The text of the code.** The spec now states these facts of the code, with no change of the
   code: the value of `warmup_passes`; the exact keys of `execution`, of an item of `inputs` and of
   `stage_providers`; the three parts of the load result; the image of a frame (BGR, `uint8`,
   `(H, W, 3)`); the glue time under the key `glue`; and the two forms of `--out`.

## Reason

- The code of `skellytracker/core/pipelines/` had a comment `# choice:` or `# open:` at each place
  where no text decided. The user accepted one sentence for each place.
- Item 1: no measurement gives the VRAM of a session at a batch, so no formula for k is safe.
- Item 2: the user, in words: the timing of a node is how long all sessions of the node took. No
  consumer reads a time for each GPU.
- Item 6: the entry that asked for the parents,
  [ADR-Q59W](Q59W-pipeline-timing-and-taps.md) item 4, is superseded. Nothing reads the parents. A
  tool can find them from `inputs` of the node items.

## Consequences

- With k = 1, a `video` run with much free VRAM does not use it for a larger batch.
- The node item of a node on two or more GPUs does not show the other GPUs.
  `PipelineRun.models` gives the device key of each GPU.
- The later work on k is in the item "Batch k" of
  [stage 1.10](../../specs/sidecar-implementation-plan.md#110-the-pipeline-api-was-p) of the
  implementation plan.

## Evidence

- The code of each item: `batch_k`, `_node_items` and the `warmup_passes` argument of
  `skellytracker/core/pipelines/_runtime/executor.py`; `skellybench_timing` and `make_node_item` of
  `skellytracker/core/pipelines/timing.py`; the `missing_dependency` warning of
  `skellytracker/core/pipelines/_runtime/resolve.py`; the lock of `PipelineRun` in
  `skellytracker/core/pipelines/run.py`; `PipelineCheck` of
  `skellytracker/core/pipelines/loading.py`; `--out` of `skellytracker/core/pipelines/cli.py`.
- The tests are in `skellytracker/tests/pipelines/`: `test_run.py` (the thread rules),
  `test_timing.py` (the times of two sessions of one node) and `test_sessions.py` (k).

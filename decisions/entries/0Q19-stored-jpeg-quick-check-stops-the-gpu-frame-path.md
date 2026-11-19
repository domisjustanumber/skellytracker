# 0Q19 — A stored JPEG quick check that failed stops a part of the GPU frame path of a run

**Status:** absorbed into [Running: Behaviour](../../specs/pipeline/running.md#behaviour), [Running: Implementer guidance](../../specs/pipeline/running.md#implementer-guidance), [Timing: Fields](../../specs/pipeline/timing.md#fields), 2026-11-19 (user; PR: pending).

## Decision

This entry extends [ADR-W4NW](W4NW-gpu-preprocess-of-a-model-node-and-its-cpu-warning.md). The
quick check stores the results of the JPEG checks `jpeg-decode` and `jpeg-preprocess` in the row of
the pair in `quick-checks.json` of the EP store
([ADR-R53H](R53H-quick-check-default-eps-and-each-gpu.md) item 5).

1. At the start of a run with the preprocess place `auto`, the run reads the stored result for the EP
   and the GPU of each device with an `onnx_model` node on `cuda` or `trt-rtx`.
2. Only a stored `fail` changes the run. A stored `pass` or `not-run`, no row, a row with no `jpeg`
   and a file that the run cannot read keep the GPU frame path, as before. The read never stops the
   start.
3. Each check stops only its own part of the GPU frame path, on that device only:
   - `jpeg-decode` is `fail`: no GPU decoder opens. The run decodes the JPEG buffers of that device
     on the CPU, and the GPU preprocess still runs on the uploaded frames. The run gives the warning
     `jpeg_decoded_on_cpu` one time for the run, at the first call with a JPEG buffer on such a
     device, with the new reason `quick_check_failed`.
   - `jpeg-preprocess` is `fail`: each `onnx_model` node on that EP uses the CPU preprocess on that
     device. The JPEG buffers of that device also decode on the CPU, and no frame of that device
     uploads. The run gives the warning `preprocessed_on_cpu` one time for each node, at the start of
     the run, with the reason `quick_check_failed` and null frame sizes. The decode moves to the CPU,
     so the run also gives `jpeg_decoded_on_cpu` as for `jpeg-decode`.
4. With `gpu`, the run does not read the stored result and uses the GPU frame path. With `cpu`, the
   run does not read it.
5. The timing header shows the preprocess at the start of the run: `stage_providers.preprocess` is
   null when the first GPU of the node has the stored `jpeg-preprocess` `fail`.

## Reason

- User ruling, 2026-11-19: a failed JPEG check stops only the GPU frame path. A decoder fault or a
  graph fault on one PC must not take the EP away from the models.
- A certification run must test the GPU frame path again after a fix, so `gpu` ignores the stored
  result.
- With no stored result, the run keeps the GPU frame path until the rule for platforms with no test
  exists ([ADR-21BK](21BK-quick-check-local-pass-and-hand-in.md) item 2).
- The run reads the file only at the start, so a call has no added cost.

## Consequences

- A PC that never ran the quick check keeps the GPU frame path.
- A stored `fail` stays until a new quick check of the same pair ends `pass` or `fail`: that check
  replaces the whole row, also its `jpeg`. A quick check that ends `not-run` writes no row. A new
  pack version gives a new pair key, so the old row no longer applies.
- Two GPUs of one model share one row ([ADR-R53H](R53H-quick-check-default-eps-and-each-gpu.md)).

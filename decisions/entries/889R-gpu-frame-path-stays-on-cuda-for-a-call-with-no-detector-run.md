# 889R — The GPU frame path stays on `cuda` for a call with no detector run

**Status:** absorbed into [Running: Behaviour](../../specs/pipeline/running.md#behaviour), 2026-11-21 (user; PR: pending).

## Decision

1. With `auto`, a run on the EP `cuda` keeps the GPU JPEG decode and the GPU preprocess for each
   call, also for a call with no detector run. The run does not change the path between calls.

## Reason

- On `cuda`, a call with no detector run is 15 to 47 % slower on the GPU path than on the CPU path
  with array input
  ([ADR-58F5](58F5-native-jpeg-numbers-on-the-pinned-versions.md) item 2). A call with a detector
  run is 35 to 40 % faster.
- That CPU path pays no JPEG decode. With JPEG input, the CPU path must also decode each frame.
- The user accepted the cost on 2026-11-21.

## Alternatives rejected

- A CPU decode on `cuda` for the calls with no detector run. A run with one path is simpler, and
  no run measured the two paths with the same JPEG input.

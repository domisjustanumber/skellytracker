# S1TG — The run decodes the JPEG buffers of a call on the CPU in a thread pool, with at most `cpu_threads` threads

**Status:** absorbed into [`running.md#fields`](../../running.md#fields), [`running.md#behaviour`](../../running.md#behaviour), [`running.md#implementer-guidance`](../../running.md#implementer-guidance), [`timing.md#implementer-guidance`](../../timing.md#implementer-guidance), 2026-11-18 (user, decision on the CPU JPEG decode of 2026-11-18; PR: pending).

## Decision

1. **Thread pool.** When a call has 2 or more JPEG buffers that the run decodes on the CPU, and the
   run parameter CPU threads is more than 1, the run decodes these buffers at the same time, with at
   most that count of threads ([Running](../../running.md#fields)). With CPU threads 1, or with fewer
   than 2 such buffers in the call, the run decodes them in a row. This adds a use to the run
   parameter of [ADR-HB8Z](../../../../decisions/entries/HB8Z-cpu-threads-run-parameter.md). It
   changes no other rule of that entry.
2. **Refused call.** The call waits for each decode. A refused call (`V-pipeline.running-12`) names
   the first camera in camera order with a buffer that no decoder can read, as a decode in a row
   does. It changes no state.
3. **Timing.** The span `frame.decode` is wall time, from before the first decode to after the last
   decode ([Timing](../../timing.md#implementer-guidance)).
4. **No other change.** No new run parameter. The GPU decode does not change.

## Reason

- The decode in a row of 6 frames at 1920 x 1080 takes 30.5 ms: almost one frame time at 30 fps. A
  decode in a thread pool is 2.3 to 3.9 times faster on 28 logical CPUs (Evidence).
- CPU threads is already the limit of the CPU threads of the run. One limit for the inference and
  the decode keeps cores free for the camera capture and the application.
- `cv2.setNumThreads` has no effect on a decode, so OpenCV cannot do this work itself.

## Consequences

- A decode in a thread pool uses 10 to 18 % more CPU time.
- The gain of a full call is not measured yet ([open work](../../../../decisions/open-work.md)).

## Evidence

Measured on 2026-11-18 on a host with 28 logical CPUs, the decode only, 1000 batches for each point. The script was a local scratch script, not in this
repository.

| Frames | Frame size | ms in a row | ms in a thread pool |
|---|---|---|---|
| 3 | 1280 x 720 | 8.2 | 3.6 |
| 6 | 1280 x 720 | 16.3 | 4.2 |
| 3 | 1920 x 1080 | 15.1 | 6.5 |
| 6 | 1920 x 1080 | 30.5 | 7.8 |

- The thread pool used 10 to 18 % more CPU time.
- Limited to 2 logical CPUs, the thread pool was 1.3 times faster. Limited to 4, it was 2.0 to 2.3
  times faster.
- `cv2.setNumThreads` did not change the time of a decode.

## Alternatives rejected

- **A new run parameter for the decode threads.** The user chose one limit for the CPU threads of
  the run.
- **`cv2.setNumThreads`.** It has no effect on a decode (Evidence).
- **The decode in a row for each call.** It is 2.3 to 3.9 times slower on 28 logical CPUs
  (Evidence).

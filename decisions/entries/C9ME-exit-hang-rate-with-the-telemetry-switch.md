# C9ME — Exit hang rate of the minimal reproducer with `ORT_DISABLE_TELEMETRY=1`

**Status:** evidence, 2026-11-21 (measurements of 2026-11-19 to 2026-11-21; PR: pending).

## Decision

Item 8 of [ADR-C6A5](C6A5-exit-hang-of-the-cuda-ep-plugin.md) names this run as not done. The
package sets the switch `ORT_DISABLE_TELEMETRY=1`
([ADR-BZ7X](BZ7X-onnx-runtime-telemetry-switch-and-scan.md)).

1. **Setup.** ONNX Runtime 1.31.1 and `cuda-cu13` 0.3.0, EP `cuda`. The minimal reproducer sleeps
   15 s before the exit. Each run is one process.
2. **Telemetry on.** 1 hang in 120 runs. A series of 60 runs on 2026-11-19 and 2026-11-20 holds the
   1 hang. 60 control runs on 2026-11-20 and 2026-11-21 had 0 hangs.
3. **Switch on.** With `ORT_DISABLE_TELEMETRY=1` set before the process starts: 0 hangs in 120
   runs. The runs were in 6 rounds, interleaved with the control runs: 10 control runs and 20 runs
   with the switch in each round.
4. **Exit latency.** The median exit latency was 0.30 s (control) and 0.29 s (switch).
5. **Result.** 1 of 120 against 0 of 120 does not separate the two cases (Fisher exact test,
   p = 1.0). The run does not show that the switch stops the hang. It also does not show the
   opposite.
6. **Limit.** The minimal reproducer hangs far less often than the full runs of ADR-C6A5 item 3
   (4.7 %). Thus this reproducer is too weak for the question. No full-length run with the switch
   was done.

## Evidence

- Conditions: Windows 11, one RTX 3070, the hardware of ADR-C6A5. Other CPU load was present
  during the runs. The run only counts hangs.
- The scripts are scratch scripts (not in git). They read the telemetry database of ONNX Runtime.
  No database content, device id or event text goes into the repository.

## Open work

See [open-work.md](../open-work.md).

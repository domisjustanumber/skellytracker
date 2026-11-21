# J9KX — Exit hang of the full run with `ORT_DISABLE_TELEMETRY=1`

**Status:** evidence, 2026-11-21 (measurement of 2026-11-21; PR: pending).

## Decision

[ADR-C9ME](C9ME-exit-hang-rate-with-the-telemetry-switch.md) names this run as not done. It is the
full run of [ADR-C6A5](C6A5-exit-hang-of-the-cuda-ep-plugin.md) item 3: 300 calls, `cuda`, array
input with the GPU preprocess, 1920x1080, 6 cameras, wrapper with a normal end.

1. **Setup.** ONNX Runtime 1.31.1 and `cuda-cu13` 0.3.0. Each run is one process. 12 rounds, each
   with 10 control runs and then 20 runs with the switch.
2. **Telemetry on (control).** 28 hangs in 120 runs (23 %).
3. **Switch on.** With `ORT_DISABLE_TELEMETRY=1` set before the process starts: 0 hangs in 240
   runs.
4. **Result.** The switch stops the exit hang in this run. With one hang rate for both cases, the
   chance of 0 hangs in the 240 runs is 4e-15 (exact test on the 28 hangs of the 360 runs).
5. **The stack.** The capture of the first hang has the stack of ADR-C6A5 item 4: `ExitProcess`,
   `LdrShutdownProcess`, the exit code of `onnxruntime_providers_cuda.dll` and `Cnd_wait`. The
   modules `winhttp.dll` and `webio.dll` are loaded.
6. **Exit latency.** The median exit latency of a run with no hang was 0.41 s (control) and 0.40 s
   (switch).
7. **Not explained.** The control rate is 23 %. ADR-C6A5 item 3 measured 4.7 % (9 of 192). No run
   examined the cause. The other load on the system was different (Evidence).

## Evidence

- 2026-11-21, 10:41 to 12:25, with a stop from 11:47 to 12:00. Windows 11, one RTX 3070, the
  hardware of ADR-C6A5. A run is a hang when its process lives 20 s after its last output.
- Other sessions ran tests on the CPU during the run. No other session used the RTX 3070.
- The package sets the switch at its import
  ([ADR-BZ7X](BZ7X-onnx-runtime-telemetry-switch-and-scan.md)). The pinned versions (ONNX Runtime
  1.30.0, `cuda-cu13` 0.2.0) were not in this run.
- The scripts are scratch scripts (not in git). They read the telemetry database of ONNX Runtime.
  No database content, device id or event text goes into the repository.

## Open work

See [open-work.md](../open-work.md).

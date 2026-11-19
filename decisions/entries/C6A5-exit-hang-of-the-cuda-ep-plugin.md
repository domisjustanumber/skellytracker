# C6A5 — Exit hang of the CUDA EP plugin `cuda-cu13` 0.3.0 on Windows

**Status:** evidence, 2026-11-19 (measurements of 2026-11-17 to 2026-11-19; PR: pending).

## Decision

1. **First sighting.** 1 of the 95 processes of
   [ADR-1SZ9](1SZ9-gpu-preprocess-and-gpu-jpeg-decode-in-the-pipeline-run.md) did not end after it
   saved its results: `cuda`, array input with the GPU preprocess, 1920x1080, 6 cameras.
2. **The study of 2026-11-17 ran another program.** 566 of its 578 runs ended. They ran the race
   script `gpu_preprocess_race.py` of the sidecar log through a wrapper (100 iterations with the
   wait, 30 without it) and a teardown variant (30 iterations), not the pipeline. The 12 other runs
   stopped by design: their child writes more than the pipe buffer into a pipe that the loop does
   not read.
3. **The night study (full: 300 calls; short: 20 calls; `cuda`, array input with the GPU
   preprocess, 1920x1080, 6 cameras).**

   | ONNX Runtime, `cuda-cu13` | Runs | How the process ends | Hangs |
   |---|---|---|---|
   | 1.31.1, 0.3.0 | full | as in ADR-1SZ9 (`measure.py`) | 3 of 92 |
   | 1.31.1, 0.3.0 | full | wrapper, normal end | 1 of 40 |
   | 1.31.1, 0.3.0 | full | wrapper, EP library unregistered first | 5 of 60 |
   | 1.31.1, 0.3.0 | full | wrapper, hard end after the flush | 0 of 60 |
   | 1.31.1, 0.3.0 | short | normal 100, objects kept 50, unregistered 60, hard end 60, `trt-rtx` 30, minimal reproducer 100 | 0 of 400 |
   | 1.30.0, 0.2.0 | full | as in ADR-1SZ9 | 0 of 43 |

   The full runs that end in the normal way or after the unregister hang in 9 of 192 runs (4.7 %).
   With that rate, 0 of 60 has a chance of about 6 % and 0 of 43 a chance of about 13 %. The
   unregister does not unload the DLL, and it does not stop the hang. The hard end
   (`TerminateProcess`) is the only variant with no hang.
4. **The stack.** In each of the 9 hangs, the last thread is in `ExitProcess`,
   `LdrShutdownProcess`, the exit handler table of `onnxruntime_providers_cuda.dll` and `Cnd_wait`.
   Python is finalized. No skellytracker code is on the stack.
5. **Measured: the byte search.** The strings `WINHTTP.dll`, `OneCollector` and
   `ORT_DISABLE_TELEMETRY` are in the 0.3.0 plugin DLL. They are not in the 0.2.0 plugin DLL and not
   in `onnxruntime.dll` of `onnxruntime-windowsml` 1.30.0.
6. **A reading of the binary without symbols, not a measurement.** The 0.3.0 plugin holds the 1DS
   telemetry client of Microsoft with a WinHTTP transport (class names in `s030.txt`). The frames of
   the hang stack map into the teardown of that client (`probe_030.txt`, `region_030.txt`). The
   0.4.0 plugin calls `RtlDllShutdownInProgress` and skips that work at the process shutdown
   (`xref_040_rtl.txt`).
7. **Reported, not verified here.** The release notes of ONNX Runtime 1.32.0, read on a mirror,
   name "resolved Windows 1DS telemetry shutdown deadlocks". A scan of another session found the
   client in the Linux core of 1.30.0 and in the Linux 0.2.0 plugin.
8. **Not done.** No run tested the hang rate with `ORT_DISABLE_TELEMETRY=1`. That run is planned
   (open work).

## Evidence

- Conditions: Windows 11, one RTX 3070, the hardware of ADR-1SZ9. The runs on 1.31.1 and 0.3.0 used
  the branch before the move to 1.30.0, in the worktree or in an export. A run on 1.30.0 printed the
  version and the loaded 0.2.0 plugin DLL. Each run is one process in `loop.py`, with a timeout
  and, for a stuck process, a capture of the stacks and the modules before the loop ends it.
- The scripts are in [`c6a5_exit_hang/`](../scripts/c6a5_exit_hang/): `loop.py`, `measure.py`,
  `wrap.py` (the end variants), `mini.py` (the minimal reproducer), `native_stacks.py`,
  `alive_check.py`, `dummy_pad.py` and `dummy_thread.py` (checks of the loop), `stage1.sh` to
  `stage3.sh`; the outputs `rows.txt` (one row for each run) and `hang_stacks.txt` (the stacks of
  the 9 hangs); `byte_search.py` (item 5). `binary_reading/` holds the scripts and outputs of
  item 6. `race_study_2026_11_17/` holds the scripts and rows of item 2.
- Not kept: the capture files (they hold local paths), the two scripts that read the telemetry
  database, and each database content, device id or event text.
- Not run: a full run on `trt-rtx`, a longer run of the minimal reproducer, and more full runs on
  1.30.0 and 0.2.0.

## Open work

See [open-work.md](../open-work.md).

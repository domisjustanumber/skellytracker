# HB8Z — A run parameter `cpu_threads` for the sessions on the CPU EP, with half of the physical cores as the default

**Status:** absorbed into [`running.md#fields`](../../specs/pipeline/running.md#fields), [`running.md#behaviour`](../../specs/pipeline/running.md#behaviour), [`running.md#validation-rules`](../../specs/pipeline/running.md#validation-rules), [`timing.md#fields`](../../specs/pipeline/timing.md#fields), [`timing.md#implementer-guidance`](../../specs/pipeline/timing.md#implementer-guidance), [`eps/session.py`](../../skellytracker/core/eps/session.py), [`generic/session.py`](../../skellytracker/core/detectors/generic/session.py), [`run.py`](../../skellytracker/core/pipelines/run.py), 2026-11-17 (user, option A of the CPU thread question of 2026-11-17; PR: pending).

## Decision

1. **Parameter.** `start_pipeline` takes the keyword parameter `cpu_threads: int | None = None`,
   after `fps`. It is the intra-op thread count of each session of the run on the built-in CPU EP
   `cpu`. Such a session has one inter-op thread. This adds a parameter to the signature of
   [ADR-W5QD](W5QD-pipeline-entries-consolidation.md) item 3. It changes no other rule of that
   entry.
2. **Default.** With None, the count is half of the physical cores of the host, at least 1:
   `max(1, physical // 2)`. `physical_cores()` of `core/system/host.py` reads the physical cores as
   `probe_host()` does, with no NVML call. When the OS gives no physical core count, the count is
   half of `os.cpu_count()`, at least 1. `cpu_thread_count()` of `core/eps/session.py` is the one
   place of the default in the code.
3. **Values.** A positive integer sets the count. Zero, a negative value and a bool fail the start
   before frame 0 with a `ValueError` of the new rule `V-pipeline.running-11`. A value of another
   type fails at the call, from the type check of the package, as for each typed run parameter.
4. **Scope.** A session of a GPU EP pack keeps one intra-op thread and one inter-op thread, and
   ignores `cpu_threads`. A session on another built-in EP, for example `coreml`, keeps the thread
   counts of ONNX Runtime. A `mediapipe_tasks` node is not an ONNX session and does not use it.
5. **Other entry points.** `eps.build_session()` and the generic detectors (`create_detector` and
   `open_session` of `core/detectors/generic/`) take the same `cpu_threads`, with the same default.
   A bad value raises `EpRequestError` there, for each EP. The two entry points thus build the
   same CPU session.
6. **Report.** `SessionReport.cpu_threads` gives the applied count, and None for another EP. Each
   item of `PipelineRun.models` has `cpu_threads`. The `execution` facts of a node item of the
   timing header and of `tap.json` have `cpu_threads`. No hash changes: `pipeline_sha256` and
   `upstream_sha256` hash only the config, and a replay compares only `used_ep` of `execution`.
7. **CLI.** `python -m skellytracker run` and the webcam demo take `--cpu-threads N`.

## Reason

- With the default of ONNX Runtime, each session on the CPU EP uses one thread for each physical
  core. A run has a session for each model. In freemocap, these threads compete with the camera
  capture and the rest of the application.
- Half of the physical cores leaves cores free and keeps most of the speed (Evidence). freemocap
  can set a different value.
- A GPU session already uses one thread: its nodes on the CPU EP are few.

## Evidence

Measured on 2026-11-17 on Windows 11, on a hybrid Intel CPU with 20 physical cores and 28 logical
CPUs: the default is thus 10. Python 3.13.18, `onnxruntime` 1.31.1, the built-in
`yolox-rtmw-wholebody` on the CPU EP, 3 cameras of the test recording of `tests/conftest.py`
(1280 x 720), the running mode `video`. Each count ran in its own process: 20 warm-up calls, then
400 timed `process_batch` calls. The 20 threads stand for the default of ONNX Runtime, one thread
for each physical core. The script was a local scratch script, not in this repository.

| `cpu_threads` | median ms for each call | p10 to p90 ms |
|---|---|---|
| 1 | 188.5 | 186.8 to 192.3 |
| 4 | 57.0 | 55.8 to 60.4 |
| 10 (default) | 35.3 | 33.9 to 38.2 |
| 20 (all physical cores) | 31.0 | 29.9 to 33.4 |

The default keeps about 88% of the speed of all cores with half of the threads.

## Alternatives rejected

- **Keep the default of ONNX Runtime.** The sessions of the models take each core, also the cores
  that the camera capture needs.
- **One thread, as for a GPU session.** One thread is too slow on the CPU EP (Evidence).

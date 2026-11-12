# D8DH — `core/errors.py`, one exit-code table, the "ready" rule and the session build

**Status:** accepted, 2026-11-12 (user).

## Decision

1. **Errors.** `core/errors.py` is the one errors module of `eps` and the pipeline runtime.
   - `EpRequestError(ValueError)`: a reserved key, an unknown key, or an option name or value that
     the catalog refuses. It raises before any ONNX Runtime call.
   - `EpUnavailableError`, `SessionCreationError(message, report)` with a failed `SessionReport`, and
     `VRAMExhaustionError` raise as [ADR-9NW0](9NW0-ep-keys-options-and-failures.md) item 4 says.
   - `VRAMExhaustionError` also subclasses `MemoryError`.
   - Stage 1.10 adds `MissingDependencyError`
     ([ADR-V7GZ](V7GZ-pipeline-api-device-and-vram-reserve.md) item 7).
   - A cancel is not an error class.
2. **Exit codes.** `skellytracker-eps` and the pipeline CLI use one table. It keeps codes 3 to 5 of
   ADR-9NW0 item 6.

   | Code | Meaning |
   |---|---|
   | 0 | ok |
   | 1 | failure |
   | 2 | usage error, no confirmation, `EpRequestError` |
   | 3 | an EP is not available |
   | 4 | a session was not created |
   | 5 | the GPU memory is exhausted |
   | 6 | cancelled |
3. **Ready.** An EP pack is ready when it is installed, it is current (the running catalog lists its
   pack id and version), it registers and it lists a device. The verification state (no trial
   session yet, `installed_unverified`, `untested-ort`) does not block. It adds one warning line for
   each process. `recommend()`, `status()`, `build_session()` and the start check of
   [ADR-ZYS9](ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 7 use this rule. A pack
   that is not ready gives `EpUnavailableError` with the install command. A stale pack (the running
   catalog does not list its pack id and version) counts as not installed for ADR-9NW0 item 4.
4. **`build_session()`** takes the model as bytes or as a path. The NMS session passes its bytes
   with `execution_provider="cpu"` (ADR-9NW0 item 7).
5. **No EP variables.** No environment variable selects the EP or the device.
   `SKELLYTRACKER_EP` and `SKELLYTRACKER_EP_DEVICE` go.
6. **Threads.** A session of a GPU EP sets `intra_op_num_threads=1` and `inter_op_num_threads=1`.
   `build_session()` sets each session value as a `SessionOptions` attribute, never as an
   `add_session_config_entry` key.
7. **CUDA floor.** The CUDA floor comes from the driver branch (R580 = CUDA 13). No code reads the
   CUDA version from NVML for the floor.
8. **CoreML.** `coreml` is a GPU EP for the precision default of
   [ADR-7NY2](7NY2-pipeline-form-graph-and-nodes.md) item 10, so fp16 is first. Before stage 1.11
   (Pre-release), check fp16 on `coreml` on an Apple Silicon Mac.
9. **No model blocks.** The catalog has no `model_constraints` rows and no `blocked` status.
10. **EP state.** The entries of `list_detectors()` and `list_pipelines()` carry no EP state.
    `eps.status()` and `eps.recommend()` give it.
11. **Probe.** `build_session()` calls the cached `probe_host()` only for a GPU EP, never for `cpu`
    or `coreml`.
12. **CPU sessions before 1.10.** The tests of stage 1.7 (Standalone generic detectors) and the
    model gate of stage 1.9 build their sessions with plain ONNX Runtime on the CPU. Stage 1.7 does
    not wait for stage 1.3 (Hardware and EP API).
13. **Old session code.** New session code goes in `core/eps/`. Stage 2.4 deletes the old
    `core/sessions/` with `core/tracker/`. Until then, `core/sessions/session_errors.py` does not
    change ([ADR-0XW9](0XW9-entry-points-layout-guard-test-and-session-code.md) item 1).
14. **Guard test.** A test in a fresh interpreter checks that `import skellytracker.core.eps` loads
    no `onnxruntime`. It tests the lazy import only. It does not restore the other import isolation
    rules ([ADR-0XW9](0XW9-entry-points-layout-guard-test-and-session-code.md) item 3).
15. **No legacy bridge.** `build_session()` serves only new code. It does not feed `OnnxSession` or
    `Tracker.create` ([ADR-NHM3](NHM3-phases-to-the-exporter-checkpoint.md) item 1).
16. **Frozen smoke test.** The smoke test of stage 1.3 checks only that the sidecar files are in the
    bundle. Stage 1.11 loads them with the new loader.

## Reason

- The user decided these items on 2026-11-12, in a grilling session of the hardware and EP track.
- A typed error lets a caller act on the cause. freemocap matches ONNX Runtime texts for an
  out-of-memory error today. A `MemoryError` subclass also catches in generic code.
- One exit-code table lets the freemocap installer read both CLIs the same way.
- A pack with no trial session yet can work. The user chose a warning, not a block.
- An environment variable is a second, hidden owner of the EP choice. The caller passes a concrete
  key (ADR-9NW0 item 3).
- The driver branch gives the CUDA floor with no extra NVML read.
- The SDK graphs that TRT-RTX could not build (YOLOX-m TopK, RTMO-s NMS) are not v2 artifacts.
- A pack can change after a list call, and `find_spec` cannot see the EP store.
- An NVML call wakes the dGPU of a hybrid laptop. A CPU session needs no GPU fact.
- Plain sessions on the CPU let stages 1.7 and 1.9 run in parallel with stage 1.3.
- A frozen smoke test on the old loader would make new code use old code (ADR-NHM3 item 1).

## Alternatives rejected

- **`EpNotInstalledError`.** `EpUnavailableError` covers it.
- **A block until the trial session passes.** The user chose one warning.
- **EP state in the list entries.** It is out of date at start.
- **`model_constraints` and `blocked` rows.** No v2 artifact needs one.
- **The stage 1.7 tests through `eps.build_session()`.** Stage 1.7 would wait for stage 1.3.
- **No guard test.** The lazy import of `onnxruntime` keeps `import skellytracker.core` fast.

## Open work

See [open-work.md](../open-work.md).

# 92BE — A temporary legacy run path for the freemocap metrics stage: task events and a `cuda` bridge of the old session

**Status:** accepted, 2026-11-17 (user).

## Decision

1. The pipeline-metrics pop-up of freemocap compares the old run code of this package with the 2.0
   pipelines. The old run code is `skellytracker.core.tracker.Tracker` with the old YOLOX person
   detector (dynamic batch) and the old RTMW wholebody detector. The comparison is realtime only.
2. Two temporary changes of the old run code serve this legacy path:
   - The old tracker gives optional task events: `core/tracker/task_events.py` and the argument
     `event_collector` of `Tracker.process_batch` (commit 75d6ee73).
   - The old `OnnxSession` takes `execution_provider="cuda"`
     (`ExecutionProviderName` in `core/sessions/execution_provider_name.py`). For this key,
     `OnnxSession.create` builds each model with `eps.build_session(model_path,
     execution_provider="cuda")`: the `cuda` pack of the EP store, the default options of the EP
     catalog and the default GPU. It keeps the `InferenceSession` and runs its own warm-up at the
     batch size of the config after it.
3. The legacy path runs on `cuda` and `cpu` only. It has no `trt-rtx` key. The user states that
   TensorRT does not work on the legacy models. This repository has no measurement of it.
4. `cuda` has no fallback. An error of `eps.build_session()` (`EpRequestError`,
   `EpUnavailableError`, `SessionCreationError` or `VRAMExhaustionError` of `core/errors.py`)
   reaches the caller with no change. The session is not built again on the CPU.
   `auto_detect_provider()` and the keys `None`, `cpu` and `coreml` do not change. `cuda` applies
   only when the caller names it.
5. This is an exception to two rules: `eps.build_session()` serves only new code and does not feed
   `OnnxSession`
   ([ADR-D8DH](D8DH-sessions-errors-and-the-ready-rule.md) item 15), and the old session code in
   `core/sessions/` does not change
   ([ADR-D8DH](D8DH-sessions-errors-and-the-ready-rule.md) item 13). The exception covers only the
   two changes of item 2.
6. Stage 2.4 of the implementation plan deletes both changes with the old run code.

## Reason

The metrics stage of freemocap must show what the move to the 2.0 pipelines changes for a user of
the old path. The old path runs only on the CPU EP and the CoreML EP. A GPU comparison needs a GPU
EP on the old path. The `cuda` pack of the EP store is the only CUDA EP of this package
([ADR-M2C6](M2C6-exact-pins-and-one-python-patch-release.md) item 2). A bridge to
`eps.build_session()` uses the same pack, the same device selection and the same errors as the new
code. Thus the two paths differ only in their run code.

## Consequences

- `core/sessions/` imports `skellytracker.core.eps` in the body of `OnnxSession.create`, only for
  `cuda`. A plain import of `core/sessions/` loads no module of `core.eps`.
- The `cuda` session has two warm-up runs: one at batch 1 in `eps.build_session()` and one at the
  batch size of the config in the old `_warmup`.

## Evidence

- `eps.build_session()` gives a dimension with no fixed size the value 1 in its zero inputs
  (`zero_inputs` in `skellytracker/core/eps/session.py`). On the CPU EP, the old files
  `yolox_m_8xb8-300e_humanart-c2c7a14a.onnx.prenms.onnx` (input `['N', 3, 640, 640]`) and
  `rtmw-x-l_256x192_b1_fp32.onnx` (input `['batch', 3, 256, 192]`) build, pass the warm-up and then
  run at batch 1 and at batch 4. Tool: `eps.build_session()` at HEAD 75d6ee73 with `onnxruntime`
  1.31, 2026-11-17. This machine has no `cuda` pack, so no run on `cuda` was made.
- `skellytracker/tests/test_onnx_session_cuda_bridge.py`: `cuda` calls `eps.build_session()` with
  the model path and `execution_provider="cuda"`; an `EpUnavailableError` reaches the caller; the
  keys `trt-rtx`, `tensorrt`, `CUDA` and `gpu` are refused; `cpu` and `coreml` make no call of
  `eps.build_session()`.

## Alternatives rejected

- A `trt-rtx` key on the old path. The user states that TensorRT does not work on the legacy models.
- An ONNX Runtime GPU package in `pyproject.toml`. A GPU EP is a plugin EP pack of the EP store
  ([ADR-M2C6](M2C6-exact-pins-and-one-python-patch-release.md) item 2).
- A second session builder for the pack in `core/sessions/`. `eps.build_session()` already takes a
  model with a dynamic batch axis, and a copy would give different checks and errors.

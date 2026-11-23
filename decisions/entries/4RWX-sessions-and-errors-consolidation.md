# 4RWX — Consolidation of the errors, exit codes, ready rule and session build entry

**Status:** accepted, 2026-11-23 (consolidation; PR: pending).

## Decision

This entry supersedes [ADR-D8DH](D8DH-sessions-errors-and-the-ready-rule.md) in full. It changes
no decision. It keeps the item numbers of D8DH. Each item links the absorb documents of its kept
rules, and writes the text of a kept rule that no absorb document states.

1. **Errors.** [Layout](../../skellytracker/AGENTS.md#layout) and
   [`errors.py`](../../skellytracker/core/errors.py). Text: a cancel is not an error class. It gives
   the exit code 6.
2. **Exit codes.** [`errors.py`](../../skellytracker/core/errors.py),
   [`core/eps/cli.py`](../../skellytracker/core/eps/cli.py) and
   [`core/pipelines/cli.py`](../../skellytracker/core/pipelines/cli.py).
3. **Ready.** [`verification.py`](../../skellytracker/core/eps/verification.py),
   [`state.py`](../../skellytracker/core/eps/state.py) and
   [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime) (the check rule, and a component that
   never blocks the EP). Text: `recommend()`, `status()`, `build_session()` and the start check of a
   run use this rule. A stale pack (the running catalog does not list its pack id and version)
   counts as not installed.
4. **`build_session()`.** [`session.py`](../../skellytracker/core/eps/session.py).
5. **No EP variables.** [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime) and
   [`core/eps/__init__.py`](../../skellytracker/core/eps/__init__.py).
6. **Threads.** [`session.py`](../../skellytracker/core/eps/session.py). Text: `build_session()`
   sets the thread counts and the graph optimization level as `SessionOptions` attributes
   ([ADR-4JAW](4JAW-rulings-of-2026-11-23-on-sessions-the-certify-prompt-and-linux.md) item 1).
7. **CUDA floor.** [`verification.py`](../../skellytracker/core/eps/verification.py). Text: the CUDA
   floor comes from the driver branch (R580 = CUDA 13). No code reads the CUDA version from NVML for
   the floor.
8. **CoreML.** Text: `coreml` is a GPU EP for the precision default of the pipeline, so fp16 is
   first. Before stage 1.11, check fp16 on `coreml` on an Apple Silicon Mac.
9. **No model blocks.** Text: the EP catalog has no `model_constraints` rows and no `blocked`
   status.
10. **EP state.** [`state.py`](../../skellytracker/core/eps/state.py).
11. **Probe.** Text: `build_session()` calls the cached `probe_host()` only for a GPU EP, never
    for `cpu`.
13. **Old session code.** [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime), with the
    exception of [ADR-92BE](92BE-legacy-path-for-the-freemocap-metrics-stage.md). The same applies
    to item 15.
14. **Guard test.** [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime),
    [Freeze rules](../../skellytracker/AGENTS.md#freeze-rules) and
    [`test_import_rules.py`](../../skellytracker/tests/test_import_rules.py). Text: the guard test
    checks the lazy import only. It does not restore the other import isolation rules.
15. **No legacy bridge.** [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime).
16. **Frozen smoke test.**
    [`frozen_smoke.py`](../../skellytracker/_pyinstaller/tests/frozen_smoke.py). Text: stage 1.11
    loads the sidecar files with the new loader.

### Rules that do not stay

- Item 1, "Stage 1.10 adds `MissingDependencyError`": done.
- Item 4, "The NMS session passes its bytes with `execution_provider="cpu"`": the runtime has no
  NMS session. The NMS runs in NumPy (`core/detectors/processing/post/object_selection_nms.py`).
- Item 6, "never as an `add_session_config_entry` key": [ADR-4JAW](4JAW-rulings-of-2026-11-23-on-sessions-the-certify-prompt-and-linux.md) item 1. Two settings have only
  the form of a config entry ([`session.py`](../../skellytracker/core/eps/session.py)).
- Item 11, "never for `coreml`": the check rule of
  [ADR-ER5X](ER5X-check-rule-unclean-exits-and-coreml.md) item 6 reads the chip of the Mac from
  `probe_host()`.
- Item 12: stages 1.7 and 1.9 are done.

## Reason

- Later entries changed items 3, 11, 13 and 15 of D8DH with no supersede. The code contradicts
  items 4 and 6 in part.

## Open work

See [open-work.md](../open-work.md).

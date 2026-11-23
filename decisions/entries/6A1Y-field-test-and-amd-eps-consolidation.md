# 6A1Y — Consolidation of the field-test state, DirectML and the AMD EP entries

**Status:** accepted, 2026-11-23 (consolidation; PR: pending).

## Decision

This entry supersedes [ADR-Z5X7](Z5X7-field-test-state-and-directml.md) and
[ADR-XSE7](XSE7-amd-eps-in-the-field-test.md) in full. It changes no decision. "Item N" is the item
N of the entry. Each item links the absorb documents of its kept rules, and writes the text of a
kept rule that no absorb document states.

1. **Z5X7 (field-test state, DirectML).**
   - Item 1: [`ep_catalog.py`](../../tools/ep_catalog.py).
   - Item 2: [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime),
     [`store.py`](../../skellytracker/core/eps/store.py) and
     [`certify_eps.py`](../../tools/certify_eps.py).
   - Item 3: [`state.py`](../../skellytracker/core/eps/state.py),
     [`session.py`](../../skellytracker/core/eps/session.py),
     [`installer.py`](../../skellytracker/core/eps/installer.py) and
     [`cli.py`](../../skellytracker/core/eps/cli.py). Text: `verify()` also raises
     `EpUnavailableError` with the opt-in command. No other EP runs in its place. A field-test pack
     does not download before the opt-in.
   - Item 4: [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime),
     [`core/eps/__init__.py`](../../skellytracker/core/eps/__init__.py) and
     [`records.py`](../../skellytracker/core/eps/records.py). Text:
     `suggest_execution_provider("directml")` stays None.
   - Item 5: [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime). Text: `directml` is a
     built-in EP for `win_amd64` with `selects_gpu: true`, the precision order fp16 then fp32,
     `l3_atol` 1.5e-2, no allowed option, and `status: field-test`. It can use each GPU of the host.
     Linux and macOS do not change.
   - Item 6: [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime) and
     [`session.py`](../../skellytracker/core/eps/session.py).
   - Item 7: [`certify_eps.py`](../../tools/certify_eps.py).
   - Item 8. Text: a person moves an EP to `ready` in a later commit, with a reviewed report as
     evidence. No code does it.
2. **XSE7 (AMD EPs).**
   - Item 1: [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime),
     [`core/eps/__init__.py`](../../skellytracker/core/eps/__init__.py) and
     [`ep_catalog.py`](../../tools/ep_catalog.py). Text: the EP row of a Windows ML EP has the floor
     `requires: {vendor: amd}`.
   - Item 2: [`certify_eps.py`](../../tools/certify_eps.py). Text: `migraphx` has one pack for each
     ROCm release: `onnxruntime-ep-migraphx` `1.0.0+rocm10.0.0`, `+rocm10.1.0` and `+rocm10.2.0`
     (cp313), with `migraphx-libs` 2.17.0, 2.18.0 and 2.19.0, from the two AMD indexes. `pack()`
     takes the pack whose `requires.rocm` is the release of `/opt/rocm/.info/version`. With no ROCm
     the EP is `unsupported` with `rocm-missing`, and with an other release `rocm-version`. The packs
     install no ROCm. 10.1 and 10.2 preload nothing. 10.0 preloads `libmigraphx_c.so.3` and, with
     `preload_ort_core: true`, the core library of the installed `onnxruntime`.
   - Item 3. Text: the ORT claim of each pack is `vendor_tested: ["1.29", "1.29"]`. On 1.30.0 an
     opted-in pack is `untested-ort`: usable, with a warning.
   - Item 4: [`windows_ml.py`](../../skellytracker/core/eps/windows_ml.py) and
     [`cli.py`](../../skellytracker/core/eps/cli.py).
   - Item 5: [`windows_ml.py`](../../skellytracker/core/eps/windows_ml.py) and
     [Codes of the certify suite](../../skellytracker/REASON_CODES.md#codes-of-the-certify-suite).
   - Item 6: [`onnx_stack.py`](../../tools/onnx_stack.py) and
     [`evidence.py`](../../skellytracker/core/eps/evidence.py).
   - Item 7. Text: the hardware class `amd-windows` lists `amdgpu`, `migraphx`, `directml` and
     `cpu`. `amd-linux` lists `migraphx` and `cpu`. `recommend()` gives `cpu` there.
   - Item 8: [`certify_eps.py`](../../tools/certify_eps.py),
     [`certify_platform.py`](../../tools/certify_platform.py) and
     [Codes of the certify suite](../../skellytracker/REASON_CODES.md#codes-of-the-certify-suite).

### Rules that do not stay

- Z5X7 item 2, the writers of the opt-in: [ADR-21BK](21BK-quick-check-local-pass-and-hand-in.md)
  item 2.
- Z5X7 item 4, `install_hint` after the opt-in: the check rule of
  [ADR-ER5X](ER5X-check-rule-unclean-exits-and-coreml.md) gives the quick-check command.
- Z5X7 item 7, section 4 and the `record-only` result:
  [ADR-SP4Z](SP4Z-certify-suite-calls-the-full-level.md) items 1 and 5.
- Z5X7 item 8, the first sentence: [ADR-P0JZ](P0JZ-certify-contract-in-each-package.md) item 5.
- XSE7 item 4, "No command removes the package":
  [ADR-K8Q0](K8Q0-platform-rulings-of-2026-11-19.md) item 4. `eps.remove(execution_provider=...)`
  and `skellytracker-eps remove --windows-ml KEY` remove it.
- XSE7 item 6, "section 5 of the suite": ADR-SP4Z item 1.
- XSE7 item 9: ADR-SP4Z item 4.

## Reason

- XSE7 builds on Z5X7, and later entries replaced parts of both with no supersede.

## Open work

See [open-work.md](../open-work.md).

# 4JAW — Rulings of 2026-11-23: session settings, the certify prompt, the CUDA graph option and Linux

**Status:** accepted, 2026-11-23 (user, answers to the questions Q64 to Q67 and to point 7 of the consolidation review; PR: pending).

## Decision

1. **Session settings.** `build_session()` sets the thread counts and the graph optimization level
   as `SessionOptions` attributes. It can set another session value with
   `add_session_config_entry` when that value has no attribute. This replaces the words "never as
   an `add_session_config_entry` key" of
   [ADR-D8DH](D8DH-sessions-errors-and-the-ready-rule.md) item 6.
2. **"Do not ask again".** freemocap stores the answer "do not ask again" of the EP prompt. This
   package stores no answer of a prompt. This replaces the stored answer of
   [ADR-MF2R](MF2R-ep-store-install-and-certification.md) item 14, whose store
   [ADR-X7WD](X7WD-certify-levels-rulings-of-2026-11-20.md) item 9 removed.
3. **The CUDA graph option.** The EP catalog must set `enable_cuda_graph` to `1` in the defaults
   of `trt-rtx`, for each precision. Today the catalog sets no default, and the option is on only
   because the EP has it on. The value stays in the allow-list, so a caller can set `0`.
4. **Linux.** Linux is tested only through the certify process in a freemocap build
   ([ADR-Q7VQ](Q7VQ-certify-rulings-of-2026-11-20.md) item 1). The run of the certify suite in a
   clone is not the Linux gate of [ADR-N6E8](N6E8-onnxruntime-1-30-on-each-os.md) item 9. This
   replaces [ADR-Y14H](Y14H-certify-suite.md) item 16. The host rules of the gate stay: bare-metal
   Ubuntu 24.04 with an NVIDIA driver of 590.48.01 or later.
5. **The old MediaPipe demos.** The sentence "`mediapipe-holistic-tasks` replaces both old
   MediaPipe demo builders" of [ADR-W5QD](W5QD-pipeline-entries-consolidation.md) item 3 is open
   work. It is done when the old detectors go.

## Reason

- Item 1: a thread count that is written as a config entry has no effect, and ONNX Runtime gives no
  error. The old words also refused the two config entries that the session needs and that have no
  attribute: `session.record_ep_graph_assignment_info` and `session.disable_cpu_ep_fallback`.
- Item 3: [ADR-NZK1](NZK1-ep-options-evidence.md) item 4 measured that the header of the EP gives
  the default `0`, and that the option struct holds `1`. With the option off, a call was 12% to 21%
  slower at batch 1. A later pack version can change the default with no failing test.
- Item 4: the user, on 2026-11-23: "linux will be tested purely via the certify process".
- The user agreed to items 1, 2, 3 and 5 on 2026-11-23.

## Consequences

- Item 3 changes the EP row of `trt-rtx`. The key of a stored verification verdict holds the digest
  of that row ([ADR-YPH2](YPH2-verdict-key-of-the-own-catalog-entry.md)), so each system verifies
  `trt-rtx` one time again. The set hash of the evidence does not change: it holds the wheels and
  the ONNX Runtime distributions only.

## Open work

- Item 3 is not built. Before the change, measure on the pinned pack `trt-rtx-cu13` 0.5.0 that the
  option is on by default and what it costs when it is off.
- Item 5: see [open-work.md](../open-work.md).

# 0Q48 — Consolidation of the certify suite entry

**Status:** accepted, 2026-11-23 (consolidation; PR: pending).

## Decision

This entry supersedes [ADR-Y14H](Y14H-certify-suite.md) in full. It changes no decision. It keeps
the item numbers of Y14H. Each item links the absorb documents of its kept rules, and writes the
text of a kept rule that no absorb document states.

1. **Command.** [`certify_platform.py`](../../tools/certify_platform.py) and
   [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime) (the suite stays until a freemocap
   build has run certify on Linux and on macOS).
3. **Report.** [`certify_platform.py`](../../tools/certify_platform.py). Text: the suite writes no
   second file and no image.
4. **Results.** [`certify_platform.py`](../../tools/certify_platform.py) and
   [The certify suite](../../skellytracker/REASON_CODES.md#the-certify-suite). Text: certification
   is per section. The platform gets no single verdict.
5. **Child processes.** [`certify_platform.py`](../../tools/certify_platform.py).
6. **Consent.** [`certify_platform.py`](../../tools/certify_platform.py). Text: the note prompt
   tells the user not to write personal details. The report has no name field and no contact
   field.
7. **Work folder.** [`certify_platform.py`](../../tools/certify_platform.py) and
   [`certify_eps.py`](../../tools/certify_eps.py).
8. **Privacy.** [`certify_platform.py`](../../tools/certify_platform.py) and
   [`certify_hardware.py`](../../tools/certify_hardware.py). Text: the report holds no camera
   frame.
9. **Section 2.** [`certify_hardware.py`](../../tools/certify_hardware.py).
11. **AMD EPs.** [`certify_eps.py`](../../tools/certify_eps.py),
    [`certify_platform.py`](../../tools/certify_platform.py) and
    [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime). Text: the suite is the test that
    certifies the AMD EPs. An AMD EP is in a field-test state until one reviewed report for the OS
    passes. Until then, the app never offers it. The app offers DirectML for AMD GPUs only. The
    suite records the DirectML result on each GPU.
12. **Model files.** [`certify_eps.py`](../../tools/certify_eps.py),
    [`ep_catalog.py`](../../tools/ep_catalog.py) and
    [`test_private_data_allowed_url.py`](../../tools/tests/test_private_data_allowed_url.py). Text:
    the suite downloads the model files into the git-ignored model folder. The sidecars do not
    change.
15. **New run.** Text: a platform needs a new run when the version set or the tests of a section
    change, not for each tag.

### Rules that do not stay

- Item 1, the certification tag: [ADR-P0JZ](P0JZ-certify-contract-in-each-package.md) item 4.
- Item 2: [ADR-SP4Z](SP4Z-certify-suite-calls-the-full-level.md) item 1 and ADR-P0JZ item 2.
- Item 3, the layout of the file: ADR-SP4Z item 3 and
  [ADR-Q7VQ](Q7VQ-certify-rulings-of-2026-11-20.md) item 3.
- Item 10: ADR-P0JZ item 2.
- Item 11, the second environment on ONNX Runtime 1.29: ADR-SP4Z item 4. The `record-only` result
  on a GPU of an other class: ADR-SP4Z item 5.
- Item 13: ADR-P0JZ item 4.
- Item 14: ADR-P0JZ item 2 and [ADR-21BK](21BK-quick-check-local-pass-and-hand-in.md) item 5. A
  person still writes the EP rows ([ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime)).
- Item 16, the suite run in a clone as the Linux gate: [ADR-4JAW](4JAW-rulings-of-2026-11-23-on-sessions-the-certify-prompt-and-linux.md) item 4. Linux is tested through the
  certify process in a freemocap build.
- Item 15, "about 30 to 40 minutes": one Windows system took 47 s for `packs` and 316 s for `full`
  ([hardware-runs.md](../hardware-runs.md#linux-with-an-nvidia-gpu)).

## Reason

- Later entries replaced items 2, 3, 10, 13 and 14 and parts of items 1, 11 and 15 of Y14H with no
  supersede.

## Open work

See [open-work.md](../open-work.md).

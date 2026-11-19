# ER5X — The check rule in the package, unclean exits, CoreML in the quick check and the pruning of reports

**Status:** absorbed into [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime), [`gate.py`](../../skellytracker/core/eps/gate.py), [`exits.py`](../../skellytracker/core/eps/exits.py), [`recommendation.py`](../../skellytracker/core/eps/recommendation.py), [`certification.py`](../../skellytracker/certification.py), 2026-11-19 (user; PR: pending).

## Decision

Built today: each item. No Mac ran item 6: a test with a fake host covers it.

1. **Check rule.** An EP runs on a GPU only when the project has a reviewed row for the GPU model and OS,
   or a quick check passed on this PC. It does not run after a quick check that failed on this PC
   ([ADR-21BK](21BK-quick-check-local-pass-and-hand-in.md) items 2 and 3). The package enforces the rule:
   `check_start()` and `build_session()` raise `EpUnavailableError` with the quick-check command
   (`skellytracker/core/eps/gate.py`). `PackStatus.usable` and `PackStatus.devices` obey the rule.
2. **Certification code.** The certification code runs an EP before the EP has a result. It runs inside
   `gate.certification_run()`, which switches the rule off for the process. Only the probe, the image run
   and the JPEG checks of the quick check, the JPEG certification and the certify suite use it. A test
   must show that a host with no reviewed row and no local result can run its check.
3. **No override.** The rule has no setting, no argument of a run and no environment variable, also for
   a developer and for a test.
4. **Recommendation.** `recommend()` names only an EP that a run can start now. A candidate with no
   reviewed row and no quick check is skipped with `needs_check`, and a candidate that failed on this PC
   is skipped with `failed_locally`. The application offers the quick check for `needs_check`.
5. **Unclean exit.** A process writes a marker in the EP store when it opens its first session on a GPU
   EP, with the EP and the GPU. A clean close and the exit notice of the application remove the marker. A
   marker of a process that is gone counts, at the next start, as one unclean exit of that EP on that GPU
   model. One unclean exit is a record only. Two in a row mark the EP as failed on this PC, with their
   own reason code. A clean exit resets the count. A passed quick check removes the mark and the count.
   The marker holds a file lock for the life of its process: a marker with no lock is of a process that
   is gone (`skellytracker/core/eps/exits.py`). The exit notice is `skellytracker.note_exit_requested()`.
   The certification code writes no marker.
6. **CoreML.** The quick check also checks `coreml`, with the probe and the image run against the CPU EP.
   The check rule applies to `coreml`. The key of its result is the chip name of the Mac, as
   `chip:<name>`, for example `chip:apple-m2-pro`, and its check has the name `coreml`. For now, a
   passed quick check is the validation of a Mac: no macOS run of CI is required, and the certify suite
   on macOS comes with the level `full`.
7. **Pruning.** The package deletes a report of a quick check that passed and that the user did not hand
   in when a newer such report of the same EP and GPU exists. It keeps each report with a failure and
   each report that the user handed in.
8. **Kept.** The check names `<key>@<device>` on each host, and one local result for two GPUs of one
   model ([ADR-R53H](R53H-quick-check-default-eps-and-each-gpu.md)).

## Reason

- User rulings, 2026-11-19. The user set the condition of item 2: the rule must not start a loop in
  which the check cannot run the EP.
- A rule that only the status shows holds only for an application that reads the status.
- The application kills its backend at close. A missed exit notice can thus give a false unclean exit.
  Two in a row, and a quick check that removes the mark, limit the cost to one more check.

## Consequences

- `skellytracker-eps install KEY --field-test` alone no longer makes a `field-test` EP usable: the EP
  also needs a passed quick check.
- A GPU test or a benchmark on a GPU model with no reviewed row fails until a quick check passes there.
- A test of an other subject on a fake GPU uses `hw_fakes.reviewed_rows_for_each_gpu()`.
- With no `device`, `check_start()` gives only the GPUs that the rule lets run, and `build_session()`
  takes the first of them.

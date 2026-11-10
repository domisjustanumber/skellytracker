# R3F1 — A time limit for the MediaPipe check

**Status:** accepted, 2026-11-10 (user; PR: pending).

## Decision

1. **The limit.** Check 7 of [`run_checks.py`](../../tools/run_checks.py), the MediaPipe test
   file, has a time limit of 300 s. Only this check has a limit.
2. **After the limit.** The tool stops the check process and each process that it started. On
   Windows it uses `taskkill /F /T`, because the venv `python.exe` is a launcher with a child
   process. Then it prints a note and runs the next checks. At the end it exits with 124, also when
   the next checks pass.
3. **The note.** On Python 3.12 the note calls the hang the known MediaPipe hang of Python 3.12 on
   Windows. On Python 3.13 or later the note calls it a regression.
4. **The tests do not change.** The MediaPipe tests keep their form. They are the regression test
   for the hang. No skip, no xfail and no timeout plugin is added.

## Reason

- On 2026-11-10, check 7 hung for more than 25 minutes on Windows with Python 3.12. The checks
  before it passed in 43 s. The next checks did not run.
- The user, 2026-11-10: the Python version goes to 3.13 or later soon. The MediaPipe test stays as
  the regression test for the bug of Python 3.12, Windows and MediaPipe. So a hang must stay a
  failure, and it must not stop the next checks.
- The root cause is the plan item "MediaPipe timestamps on Windows" of the
  [implementation plan](../../specs/sidecar-implementation-plan.md).

## Alternatives rejected

- **Skip or xfail the test on Windows.** It hides the regression.
- **`pytest-timeout`.** It adds a dependency. On Windows it ends the whole pytest process, so the
  result is the same as a stop by the tool.
- **Warn and exit 0.** The hang then shows only as a warning line, and a regression can pass.

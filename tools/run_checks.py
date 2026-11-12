#!/usr/bin/env python3
"""Run the checks that must pass before each commit, and stop at the first check that fails.

Usage::

    uv run python tools/run_checks.py

The tool runs these checks in this order, with the Python of the environment that runs it:

1. ``ruff check skellytracker/ tools/``
2. ``pytest tools/tests -q``. It also runs the private-data check.
3. ``pytest -m "not video" skellytracker/tests/test_mediapipe_detectors.py``
4. ``pytest -m "not video"`` without the MediaPipe file and without ``tools/tests``

The MediaPipe tests run in their own process. On Windows, one run of all non-video tests can stop
in them and not finish (the test notes of ``skellytracker/AGENTS.md``). The tool prints each
command before it runs it. It exits with the status of the first check that fails, or 0.
The tool is the source of this list.

Check 3 has a time limit of ``MEDIAPIPE_TIMEOUT`` seconds, because the MediaPipe tests can hang on
Windows with Python 3.12 (decision R3F1). When the limit runs out, the tool stops the process and
each process that it started, prints a note and runs the next checks. Then it exits with
``HUNG_STATUS``, also when the next checks pass, and its last line repeats the note. On Python 3.12
the note calls the hang known. On Python 3.13 or later the note calls it a regression.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MEDIAPIPE = "skellytracker/tests/test_mediapipe_detectors.py"
MEDIAPIPE_TIMEOUT = 300
HUNG_STATUS = 124
PY = sys.executable
CHECKS = [
    [PY, "-m", "ruff", "check", "skellytracker/", "tools/"],
    [PY, "-m", "pytest", "tools/tests", "-q"],
    [PY, "-m", "pytest", "-m", "not video", MEDIAPIPE],
    [PY, "-m", "pytest", "-m", "not video", "--deselect", MEDIAPIPE, "--deselect", "tools/tests"],
]


def time_limit(command: list[str]) -> float | None:
    """The time limit of a check in seconds: only the MediaPipe check (check 3) has one."""
    return MEDIAPIPE_TIMEOUT if command[-1] == MEDIAPIPE else None


def hang_note() -> str:
    if sys.version_info < (3, 13):
        return (
            "This is the known MediaPipe hang of Python 3.12 on Windows (skellytracker/AGENTS.md). A failed"
            ' MediaPipe test with "Input timestamp must be monotonically increasing" is the same known defect.'
        )
    return "This is a regression: the MediaPipe hang of Python 3.12 is back on a newer Python."


def stop(process: subprocess.Popen) -> None:
    """Stop `process` and its children. On Windows the venv python.exe is a launcher with a child."""
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], check=False, capture_output=True)  # noqa: S603, S607
    else:
        process.kill()
    process.wait()


def run(
    checks: list[list[str]], cwd: Path = REPO_ROOT, limit: Callable[[list[str]], float | None] = time_limit
) -> int:
    """Run each command in `cwd`. Return the exit status of the first command that fails.

    A command over its time limit is stopped, and the next commands run. Then the result is
    HUNG_STATUS. With no failure and no stop, the result is 0.
    """
    result = 0
    for command in checks:
        print("$ " + " ".join(["python", *command[1:]] if command[0] == PY else command), flush=True)
        process = subprocess.Popen(command, cwd=cwd)  # noqa: S603
        try:
            status = process.wait(timeout=limit(command))
        except subprocess.TimeoutExpired:
            stop(process)
            print(f"stopped after {limit(command)} s. {hang_note()}", file=sys.stderr)
            result = HUNG_STATUS
            continue
        if status:
            print(f"failed with exit status {status}", file=sys.stderr)
            return status
    if result == HUNG_STATUS:
        print(f"result: {HUNG_STATUS}. Only the stopped check failed. {hang_note()}", file=sys.stderr)
    return result


if __name__ == "__main__":
    sys.exit(run(CHECKS))

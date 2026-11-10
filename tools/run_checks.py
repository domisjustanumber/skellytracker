#!/usr/bin/env python3
"""Run the checks that must pass before each commit, and stop at the first check that fails.

Usage::

    uv run python tools/run_checks.py

The tool runs these checks in this order, with the Python of the environment that runs it:

1. ``ruff check skellytracker/ tools/ decisions/scripts/ specs/model-sidecar/decisions/scripts/ specs/model-sidecar/reference/``
2. ``tools/check_decision_log.py``
3. ``tools/sync_bootstrap_kit.py --check``
4. ``tools/make_vectors.py --check``
5. ``tools/sidecar_trace.py matrix --check``
6. ``pytest tools/tests -q``. It also runs the private-data check.
7. ``pytest -m "not video" skellytracker/tests/test_mediapipe_detectors.py``
8. ``pytest -m "not video"`` without the MediaPipe file and without ``tools/tests``

The MediaPipe tests run in their own process. On Windows, one run of all non-video tests can stop
in them and not finish (the test notes of ``skellytracker/AGENTS.md``). The tool prints each
command before it runs it. It exits with the status of the first check that fails, or 0.
The tool is the source of this list.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MEDIAPIPE = "skellytracker/tests/test_mediapipe_detectors.py"
PY = sys.executable
CHECKS = [
    [PY, "-m", "ruff", "check", "skellytracker/", "tools/", "decisions/scripts/",
     "specs/model-sidecar/decisions/scripts/", "specs/model-sidecar/reference/"],
    [PY, "tools/check_decision_log.py"],
    [PY, "tools/sync_bootstrap_kit.py", "--check"],
    [PY, "tools/make_vectors.py", "--check"],
    [PY, "tools/sidecar_trace.py", "matrix", "--check"],
    [PY, "-m", "pytest", "tools/tests", "-q"],
    [PY, "-m", "pytest", "-m", "not video", MEDIAPIPE],
    [PY, "-m", "pytest", "-m", "not video", "--deselect", MEDIAPIPE, "--deselect", "tools/tests"],
]


def run(checks: list[list[str]], cwd: Path = REPO_ROOT) -> int:
    """Run each command in `cwd`. Return the exit status of the first command that fails, or 0."""
    for command in checks:
        print("$ " + " ".join(["python", *command[1:]] if command[0] == PY else command), flush=True)
        status = subprocess.run(command, cwd=cwd, check=False).returncode  # noqa: S603
        if status:
            print(f"failed with exit status {status}", file=sys.stderr)
            return status
    return 0


if __name__ == "__main__":
    sys.exit(run(CHECKS))

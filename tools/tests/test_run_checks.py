"""The check runner `tools/run_checks.py` stops at the first check that fails, and its docstring lists each check."""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import run_checks


def test_run_stops_at_the_first_failed_check(tmp_path: Path) -> None:
    marker = tmp_path / "ran"
    checks = [
        [sys.executable, "-c", "raise SystemExit(0)"],
        [sys.executable, "-c", "raise SystemExit(3)"],
        [sys.executable, "-c", f"open({str(marker)!r}, 'w')"],
    ]
    assert run_checks.run(checks, cwd=tmp_path) == 3
    assert not marker.exists()
    assert run_checks.run(checks[:1], cwd=tmp_path) == 0


def test_a_hung_check_is_stopped_and_the_next_checks_run(tmp_path: Path, capsys) -> None:
    marker = tmp_path / "ran"
    checks = [
        [sys.executable, "-c", "import time; time.sleep(60)"],
        [sys.executable, "-c", f"open({str(marker)!r}, 'w')"],
    ]
    start = time.monotonic()
    result = run_checks.run(checks, cwd=tmp_path, limit=lambda c: 1 if "sleep" in c[-1] else None)
    assert result == run_checks.HUNG_STATUS
    assert time.monotonic() - start < 30
    assert marker.exists()
    assert "stopped after 1 s" in capsys.readouterr().err


def test_only_the_mediapipe_check_has_a_time_limit() -> None:
    limited = [c for c in run_checks.CHECKS if run_checks.time_limit(c)]
    assert limited == [[run_checks.PY, "-m", "pytest", "-m", "not video", run_checks.MEDIAPIPE]]


def test_the_docstring_lists_each_check() -> None:
    doc = run_checks.__doc__
    assert len(re.findall(r"^\d+\. ``", doc, re.MULTILINE)) == len(run_checks.CHECKS)
    for command in run_checks.CHECKS:
        assert all(word in doc for word in command[1:] if word not in ("-m", "--deselect")), command

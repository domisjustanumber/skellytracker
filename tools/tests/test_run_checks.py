"""The check runner `tools/run_checks.py` stops at the first check that fails, and its docstring lists each check."""

from __future__ import annotations

import re
import sys
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


def test_the_docstring_lists_each_check() -> None:
    doc = run_checks.__doc__
    assert len(re.findall(r"^\d+\. ``", doc, re.MULTILINE)) == len(run_checks.CHECKS)
    for command in run_checks.CHECKS:
        assert all(word in doc for word in command[1:] if word not in ("-m", "--deselect")), command

"""Ensure user-facing docs no longer reference the old rtmpose-gpu extra."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCAN_PATHS = (
  _REPO_ROOT / "GPU_SETUP_GUIDE.md",
  _REPO_ROOT / "CLAUDE.md",
  _REPO_ROOT / "pyproject.toml",
  _REPO_ROOT / "skellytracker",
)


def test_no_stale_rtmpose_gpu_extra_name() -> None:
  offenders: list[str] = []
  for base in _SCAN_PATHS:
    if base.is_file():
      paths = [base]
    else:
      paths = [p for p in base.rglob("*") if p.is_file() and p.suffix in {".py", ".md", ".toml"}]
    for path in paths:
      if path.name in {"uv.lock", "test_docs_extra_names.py"}:
        continue
      text = path.read_text(encoding="utf-8", errors="replace")
      if "rtmpose-gpu" in text:
        offenders.append(str(path.relative_to(_REPO_ROOT)))
  assert offenders == []

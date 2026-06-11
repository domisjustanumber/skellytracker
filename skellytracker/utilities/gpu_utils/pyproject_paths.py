"""Locate the skellytracker project root (directory containing pyproject.toml)."""

from __future__ import annotations

import tomllib
from pathlib import Path


def find_skellytracker_project_root(start: Path | None = None) -> Path | None:
  """Walk parents from *start* (default: cwd) for a skellytracker pyproject.toml."""
  candidates: list[Path] = []
  if start is not None:
    candidates.append(start)
  else:
    candidates.append(Path.cwd())

  package_dir = Path(__file__).resolve().parent
  candidates.extend(package_dir.parents)

  seen: set[Path] = set()
  for directory in candidates:
    resolved = directory.resolve()
    if resolved in seen:
      continue
    seen.add(resolved)
    pyproject = resolved / "pyproject.toml"
    if not pyproject.is_file():
      continue
    try:
      data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
      continue
    if data.get("project", {}).get("name") == "skellytracker":
      return resolved
  return None

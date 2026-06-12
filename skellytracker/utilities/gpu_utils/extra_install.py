"""Install RTMPose optional-dependency packages into the active environment."""

from __future__ import annotations

import importlib.metadata
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from packaging.requirements import Requirement

from skellytracker.utilities.gpu_utils.pyproject_cuda_requirements import load_optional_dependencies
from skellytracker.utilities.gpu_utils.pyproject_paths import find_skellytracker_project_root


@dataclass(frozen=True)
class InstallPlan:
  """Shell command plan for installing a pyproject extra."""

  command: list[str]
  cwd: Path | None
  description: str


def requirements_for_extra(extra: str) -> list[str]:
  """Return install specs for *extra* from installed distribution or pyproject.toml."""
  matched: list[str] = []
  try:
    requires = importlib.metadata.requires("skellytracker") or []
  except importlib.metadata.PackageNotFoundError:
    requires = []

  for req_str in requires:
    req = Requirement(req_str)
    if req.marker is not None and req.marker.evaluate({"extra": extra}):
      matched.append(str(req))

  if matched:
    return matched

  optional = load_optional_dependencies()
  if optional is not None:
    deps = optional.get(extra)
    if isinstance(deps, list):
      return [dep for dep in deps if isinstance(dep, str)]

  return []


def build_install_plan(extra: str) -> InstallPlan:
  """Build a dev-repo or consumer-venv install command for *extra*."""
  project_root = find_skellytracker_project_root(Path.cwd())
  uv_path = shutil.which("uv")

  if project_root is not None:
    if uv_path is not None:
      return InstallPlan(
        command=[uv_path, "sync", "--extra", extra],
        cwd=project_root,
        description=f"in {project_root}",
      )
    return InstallPlan(
      command=[sys.executable, "-m", "pip", "install", "-e", f".[{extra}]"],
      cwd=project_root,
      description=f"in {project_root}",
    )

  extra_reqs = requirements_for_extra(extra)
  if extra_reqs:
    if uv_path is not None:
      command = [uv_path, "pip", "install", *extra_reqs]
    else:
      command = [sys.executable, "-m", "pip", "install", *extra_reqs]
    return InstallPlan(command=command, cwd=None, description="into active environment")

  target = f"skellytracker[{extra}]"
  if uv_path is not None:
    command = [uv_path, "pip", "install", target]
  else:
    command = [sys.executable, "-m", "pip", "install", target]
  return InstallPlan(command=command, cwd=None, description="into active environment")

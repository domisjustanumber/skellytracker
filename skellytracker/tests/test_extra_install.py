"""Tests for optional-extra install planning."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from skellytracker.utilities.gpu_utils.extra_install import (
  InstallPlan,
  build_install_plan,
  requirements_for_extra,
)
from skellytracker.utilities.gpu_utils.pyproject_cuda_requirements import load_optional_dependencies


def test_requirements_for_extra_from_pyproject(tmp_path: Path, monkeypatch) -> None:
  pyproject = tmp_path / "pyproject.toml"
  pyproject.write_text(
    """
[project]
name = "skellytracker"

[project.optional-dependencies]
rtmpose-nvidia = [
  "onnxruntime-gpu",
  "nvidia-cudnn-cu12",
]
""".strip(),
    encoding="utf-8",
  )
  monkeypatch.chdir(tmp_path)
  load_optional_dependencies.cache_clear()

  with patch("skellytracker.utilities.gpu_utils.extra_install.importlib.metadata.requires", return_value=[]):
    reqs = requirements_for_extra("rtmpose-nvidia")

  assert reqs == ["onnxruntime-gpu", "nvidia-cudnn-cu12"]


def test_build_install_plan_dev_repo(tmp_path: Path, monkeypatch) -> None:
  pyproject = tmp_path / "pyproject.toml"
  pyproject.write_text('[project]\nname = "skellytracker"\n', encoding="utf-8")
  monkeypatch.chdir(tmp_path)
  load_optional_dependencies.cache_clear()

  with patch("shutil.which", return_value="/usr/bin/uv"):
    plan = build_install_plan("rtmpose-trt-rtx")

  assert plan == InstallPlan(
    command=["/usr/bin/uv", "sync", "--extra", "rtmpose-trt-rtx"],
    cwd=tmp_path,
    description=f"in {tmp_path}",
  )


def test_build_install_plan_consumer_venv() -> None:
  with patch(
    "skellytracker.utilities.gpu_utils.extra_install.find_skellytracker_project_root",
    return_value=None,
  ):
    with patch(
      "skellytracker.utilities.gpu_utils.extra_install.requirements_for_extra",
      return_value=["onnxruntime-gpu", "onnxruntime-ep-nv-tensorrt-rtx-cu12"],
    ):
      with patch("shutil.which", return_value="/usr/bin/uv"):
        plan = build_install_plan("rtmpose-trt-rtx")

  assert plan.command == [
    "/usr/bin/uv",
    "pip",
    "install",
    "onnxruntime-gpu",
    "onnxruntime-ep-nv-tensorrt-rtx-cu12",
  ]
  assert plan.cwd is None
  assert plan.description == "into active environment"

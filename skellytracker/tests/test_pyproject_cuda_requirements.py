"""Tests for CUDA version requirements parsed from pyproject.toml."""

from __future__ import annotations

from pathlib import Path

import pytest

from skellytracker.utilities.gpu_utils.pyproject_cuda_requirements import (
  cuda_majors_from_dep_spec,
  cuda_version_ge,
  load_optional_dependencies,
  min_driver_cuda_for_ep,
  min_driver_cuda_for_extra,
  nvidia_driver_cuda_compatible,
)


def test_cuda_majors_from_dep_spec_cu12() -> None:
  assert cuda_majors_from_dep_spec("nvidia-cuda-runtime-cu12") == [12]
  assert cuda_majors_from_dep_spec("onnxruntime-ep-nv-tensorrt-rtx-cu12") == [12]
  assert cuda_majors_from_dep_spec("onnxruntime-gpu") == []


def test_cuda_version_ge() -> None:
  assert cuda_version_ge((12, 9), (12, 0)) is True
  assert cuda_version_ge((12, 0), (12, 0)) is True
  assert cuda_version_ge((11, 8), (12, 0)) is False
  assert cuda_version_ge((13, 0), (12, 4)) is True


def test_min_driver_cuda_from_repo_pyproject() -> None:
  load_optional_dependencies.cache_clear()
  assert min_driver_cuda_for_extra("rtmpose-nvidia") == (12, 0)
  assert min_driver_cuda_for_extra("rtmpose-trt-rtx") == (12, 0)
  assert min_driver_cuda_for_ep("cuda") == (12, 0)
  assert min_driver_cuda_for_ep("trt-trx") == (12, 0)


def test_min_driver_cuda_from_fixture_pyproject(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
  load_optional_dependencies.cache_clear()
  pyproject = tmp_path / "pyproject.toml"
  pyproject.write_text(
    """
[project]
name = "skellytracker"

[project.optional-dependencies]
rtmpose-nvidia = ["nvidia-cuda-runtime-cu13"]
""",
    encoding="utf-8",
  )
  monkeypatch.chdir(tmp_path)
  load_optional_dependencies.cache_clear()
  assert min_driver_cuda_for_extra("rtmpose-nvidia") == (13, 0)


def test_nvidia_driver_cuda_compatible() -> None:
  load_optional_dependencies.cache_clear()
  assert nvidia_driver_cuda_compatible((12, 4), "cuda") is True
  assert nvidia_driver_cuda_compatible((11, 8), "cuda") is False
  assert nvidia_driver_cuda_compatible(None, "cuda") is None
  assert nvidia_driver_cuda_compatible((12, 0), "directml") is None

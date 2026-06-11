"""Tests for OS-native GPU enumeration."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from skellytracker.utilities.gpu_utils.gpu_enumeration import (
  GpuInfo,
  WindowsWmiGpuBackend,
  _enumerate_nvidia_smi_gpus,
  _filter_virtual_adapters,
  _parse_cuda_driver_max,
  list_installed_gpus,
)
from skellytracker.utilities.gpu_utils.pyproject_cuda_requirements import load_optional_dependencies


def test_filter_virtual_adapters_excludes_software_display() -> None:
  gpus = [
    GpuInfo(id="win32:0", name="NVIDIA GeForce RTX 4090", vendor="nvidia", vram_bytes=24_000_000_000),
    GpuInfo(id="win32:1", name="Microsoft Basic Display Adapter", vendor="unknown", vram_bytes=None),
    GpuInfo(id="win32:2", name="Parsec Virtual Display Adapter", vendor="unknown", vram_bytes=None),
  ]
  filtered = _filter_virtual_adapters(gpus)
  assert len(filtered) == 1
  assert filtered[0].name.startswith("NVIDIA")


def test_windows_wmi_vram_wrap_returns_none() -> None:
  payload = [{
    "Name": "NVIDIA GeForce RTX 4090",
    "AdapterRAM": 4294967295,
    "PNPDeviceID": "PCI\\VEN_10DE&DEV_2684",
    "Availability": 3,
  }]
  with patch("subprocess.run") as run_mock:
    run_mock.return_value = MagicMock(returncode=0, stdout=json.dumps(payload), stderr="")
    gpus = WindowsWmiGpuBackend().enumerate_gpus()
  assert len(gpus) == 1
  assert gpus[0].vram_bytes is None
  assert gpus[0].online is True


def test_parse_cuda_driver_max_from_header() -> None:
  header = (
    "+-----------------------------------------------------------------------------+\n"
    "| NVIDIA-SMI 576.52       Driver Version: 576.52       CUDA Version: 12.9     |\n"
  )
  assert _parse_cuda_driver_max(header) == (12, 9)


def test_enumerate_nvidia_smi_gpus_parses_query() -> None:
  load_optional_dependencies.cache_clear()
  header_stdout = "| NVIDIA-SMI 576.52  Driver Version: 576.52  CUDA Version: 12.9 |"
  query_stdout = "0, NVIDIA GeForce RTX 3070, 8192, 576.52\n"

  def fake_run(cmd, **kwargs):  # noqa: ANN001, ARG001
    if any(str(arg).startswith("--query-gpu") for arg in cmd):
      return subprocess.CompletedProcess(cmd, 0, query_stdout, "")
    return subprocess.CompletedProcess(cmd, 0, header_stdout, "")

  with patch("skellytracker.utilities.gpu_utils.gpu_enumeration._nvidia_smi_path", return_value="/usr/bin/nvidia-smi"):
    with patch("skellytracker.utilities.gpu_utils.gpu_enumeration.subprocess.run", side_effect=fake_run):
      gpus = _enumerate_nvidia_smi_gpus()

  assert len(gpus) == 1
  gpu = gpus[0]
  assert gpu.id == "nvidia:0"
  assert gpu.name == "NVIDIA GeForce RTX 3070"
  assert gpu.vram_bytes == 8192 * 1024 * 1024
  assert gpu.driver_version == "576.52"
  assert gpu.cuda_driver_max == (12, 9)
  assert gpu.cuda_required_min == (12, 0)
  assert gpu.cuda_meets_nvidia_eps is True
  assert gpu.online is True


def test_windows_wmi_includes_offline_intel() -> None:
  payload = [
    {
      "Name": "Intel(R) UHD Graphics 770",
      "AdapterRAM": 2147483648,
      "PNPDeviceID": "PCI\\VEN_8086&DEV_A780",
      "Availability": 8,
    },
    {
      "Name": "Parsec Virtual Display Adapter",
      "AdapterRAM": None,
      "PNPDeviceID": "ROOT\\DISPLAY\\0000",
      "Availability": 8,
    },
  ]
  with patch("subprocess.run") as run_mock:
    run_mock.return_value = MagicMock(returncode=0, stdout=json.dumps(payload), stderr="")
    gpus = _filter_virtual_adapters(WindowsWmiGpuBackend().enumerate_gpus())
  assert len(gpus) == 1
  assert gpus[0].vendor == "intel"
  assert gpus[0].online is False


def test_list_installed_gpus_merges_nvidia_smi_over_wmi(monkeypatch: pytest.MonkeyPatch) -> None:
  load_optional_dependencies.cache_clear()
  monkeypatch.setattr("sys.platform", "win32")
  wmi_payload = [
    {
      "Name": "Intel UHD Graphics 630",
      "AdapterRAM": 1073741824,
      "PNPDeviceID": "PCI\\VEN_8086&DEV_3E9B",
      "Availability": 3,
    },
    {
      "Name": "NVIDIA GeForce RTX 3070",
      "AdapterRAM": 4294967295,
      "PNPDeviceID": "PCI\\VEN_10DE&DEV_2484",
      "Availability": 3,
    },
  ]
  header_stdout = "| CUDA Version: 12.9 |"
  query_stdout = "0, NVIDIA GeForce RTX 3070, 8192, 576.52\n"

  def fake_run(cmd, **kwargs):  # noqa: ANN001, ARG001
    if cmd[0] == "powershell":
      return subprocess.CompletedProcess(cmd, 0, json.dumps(wmi_payload), "")
    if any(str(arg).startswith("--query-gpu") for arg in cmd):
      return subprocess.CompletedProcess(cmd, 0, query_stdout, "")
    return subprocess.CompletedProcess(cmd, 0, header_stdout, "")

  with patch("skellytracker.utilities.gpu_utils.gpu_enumeration._nvidia_smi_path", return_value="nvidia-smi"):
    with patch("skellytracker.utilities.gpu_utils.gpu_enumeration.subprocess.run", side_effect=fake_run):
      gpus = list_installed_gpus()

  assert len(gpus) == 2
  assert gpus[0].vendor == "intel"
  assert gpus[0].id.startswith("win32:")
  assert gpus[1].vendor == "nvidia"
  assert gpus[1].id == "nvidia:0"
  assert gpus[1].vram_bytes == 8192 * 1024 * 1024


def test_list_installed_gpus_offline_intel_with_online_nvidia_smi(monkeypatch: pytest.MonkeyPatch) -> None:
  load_optional_dependencies.cache_clear()
  monkeypatch.setattr("sys.platform", "win32")
  wmi_payload = [
    {
      "Name": "Intel(R) UHD Graphics 770",
      "AdapterRAM": 2147483648,
      "PNPDeviceID": "PCI\\VEN_8086&DEV_A780",
      "Availability": 8,
    },
    {
      "Name": "NVIDIA GeForce RTX 3070",
      "AdapterRAM": 4294967295,
      "PNPDeviceID": "PCI\\VEN_10DE&DEV_2484",
      "Availability": 3,
    },
  ]
  header_stdout = "| CUDA Version: 12.9 |"
  query_stdout = "0, NVIDIA GeForce RTX 3070, 8192, 576.52\n"

  def fake_run(cmd, **kwargs):  # noqa: ANN001, ARG001
    if cmd[0] == "powershell":
      return subprocess.CompletedProcess(cmd, 0, json.dumps(wmi_payload), "")
    if any(str(arg).startswith("--query-gpu") for arg in cmd):
      return subprocess.CompletedProcess(cmd, 0, query_stdout, "")
    return subprocess.CompletedProcess(cmd, 0, header_stdout, "")

  with patch("skellytracker.utilities.gpu_utils.gpu_enumeration._nvidia_smi_path", return_value="nvidia-smi"):
    with patch("skellytracker.utilities.gpu_utils.gpu_enumeration.subprocess.run", side_effect=fake_run):
      gpus = list_installed_gpus()

  assert len(gpus) == 2
  assert gpus[0].vendor == "intel"
  assert gpus[0].online is False
  assert gpus[1].vendor == "nvidia"
  assert gpus[1].online is True


def test_list_installed_gpus_subprocess_failure_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr("sys.platform", "win32")
  with patch("skellytracker.utilities.gpu_utils.gpu_enumeration._nvidia_smi_path", return_value=None):
    with patch("subprocess.run", side_effect=OSError("powershell missing")):
      assert list_installed_gpus() == []


def test_gpu_enumeration_module_has_no_ort_imports() -> None:
  source = Path(__file__).resolve().parents[1] / "utilities" / "gpu_utils" / "gpu_enumeration.py"
  tree = ast.parse(source.read_text(encoding="utf-8"))
  imported: set[str] = set()
  for node in ast.walk(tree):
    if isinstance(node, ast.Import):
      for alias in node.names:
        imported.add(alias.name.split(".")[0])
    elif isinstance(node, ast.ImportFrom) and node.module:
      imported.add(node.module.split(".")[0])
  assert "onnxruntime" not in imported
  assert "ort_session_utils" not in imported

"""Tests for OS-native GPU enumeration."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from skellytracker.utilities.gpu_utils.gpu_enumeration import (
  GpuInfo,
  WindowsWmiGpuBackend,
  _filter_virtual_adapters,
  list_installed_gpus,
)


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


def test_list_installed_gpus_subprocess_failure_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr("sys.platform", "win32")
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

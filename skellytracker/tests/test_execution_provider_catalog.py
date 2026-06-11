"""Tests for execution provider catalog and dual recommendation."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from skellytracker.utilities.gpu_utils.execution_provider_catalog import (
  _probe_ep_capabilities,
  list_execution_providers,
)
from skellytracker.utilities.gpu_utils.gpu_enumeration import GpuInfo
from skellytracker.utilities.gpu_utils.ort_session_utils import resolve_provider


def _mock_ep_device(ort_name: str, ep_options: dict[str, str]) -> SimpleNamespace:
  return SimpleNamespace(ep_name=ort_name, ep_options=ep_options)


@patch("skellytracker.utilities.gpu_utils.execution_provider_catalog.list_installed_gpus")
@patch("skellytracker.utilities.gpu_utils.execution_provider_catalog.prepare_ort_providers_for_probe")
@patch("skellytracker.utilities.gpu_utils.execution_provider_catalog.ort.get_ep_devices", create=True)
def test_rtx_gpu_cuda_only_shows_install_recommended(
  get_ep_devices_mock: MagicMock,
  probe_mock: MagicMock,
  gpus_mock: MagicMock,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  monkeypatch.setattr("sys.platform", "win32")
  gpus_mock.return_value = [
    GpuInfo(id="win32:0", name="NVIDIA GeForce RTX 4090", vendor="nvidia", vram_bytes=None),
  ]
  probe_mock.return_value = {"CUDAExecutionProvider", "CPUExecutionProvider"}
  get_ep_devices_mock.return_value = []

  info = list_execution_providers()
  assert info.recommended_provider_id == "cuda"
  assert info.optimal_provider_id == "trt-trx"
  assert info.install_recommended_provider_id == "trt-trx"

  by_id = {p.id: p for p in info.providers}
  assert by_id["cuda"].recommended is True
  assert by_id["trt-trx"].optimal is True
  assert by_id["trt-trx"].install_recommended is True


@patch("skellytracker.utilities.gpu_utils.execution_provider_catalog.list_installed_gpus")
@patch("skellytracker.utilities.gpu_utils.execution_provider_catalog.prepare_ort_providers_for_probe")
@patch("skellytracker.utilities.gpu_utils.execution_provider_catalog.ort.get_ep_devices", create=True)
def test_gtx_with_trt_and_cuda_optimal_differs_from_recommended(
  get_ep_devices_mock: MagicMock,
  probe_mock: MagicMock,
  gpus_mock: MagicMock,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  monkeypatch.setattr("sys.platform", "win32")
  gpus_mock.return_value = [
    GpuInfo(id="win32:0", name="NVIDIA GeForce GTX 1080", vendor="nvidia", vram_bytes=None),
  ]
  probe_mock.return_value = {
    "TensorrtExecutionProvider",
    "CUDAExecutionProvider",
    "CPUExecutionProvider",
  }
  get_ep_devices_mock.return_value = []

  info = list_execution_providers()
  assert info.recommended_provider_id == "trt"
  assert info.optimal_provider_id == "cuda"
  assert info.install_recommended_provider_id is None


@patch("skellytracker.utilities.gpu_utils.ort_session_utils.ensure_cuda_dlls_loaded")
@patch("skellytracker.utilities.gpu_utils.ort_session_utils.ort.get_available_providers")
def test_prepare_ort_probe_skips_cuda_on_coreml_only(
  get_providers_mock: MagicMock,
  preload_mock: MagicMock,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  from skellytracker.utilities.gpu_utils.ort_session_utils import prepare_ort_providers_for_probe

  monkeypatch.setattr("sys.platform", "darwin")
  get_providers_mock.return_value = ["CoreMLExecutionProvider", "CPUExecutionProvider"]
  available = prepare_ort_providers_for_probe()
  preload_mock.assert_not_called()
  assert "CoreMLExecutionProvider" in available


def test_probe_ep_capabilities_from_option_keys() -> None:
  device = _mock_ep_device(
    "TensorrtExecutionProvider",
    {"trt_fp16_enable": "0", "trt_profile_min_shapes": ""},
  )
  caps = _probe_ep_capabilities("TensorrtExecutionProvider", [device])
  assert caps.fixed_batch_sizes is True
  assert caps.downcasting is True
  assert caps.quantization is False


def test_recommended_matches_resolve_provider_auto() -> None:
  available = {"CUDAExecutionProvider", "CPUExecutionProvider"}
  with patch(
    "skellytracker.utilities.gpu_utils.execution_provider_catalog.prepare_ort_providers_for_probe",
    return_value=available,
  ):
    with patch(
      "skellytracker.utilities.gpu_utils.execution_provider_catalog.list_installed_gpus",
      return_value=[],
    ):
      with patch(
        "skellytracker.utilities.gpu_utils.execution_provider_catalog.ort.get_ep_devices",
        return_value=[],
      ):
        info = list_execution_providers()
  assert info.recommended_provider_id == resolve_provider(requested=None, available_ort=available)

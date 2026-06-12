"""Unit tests for trt-trx execution provider wiring (Feature 0)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, create_autospec, patch

import onnxruntime as ort
import pytest
from onnxruntime.capi.onnxruntime_inference_collection import InferenceSession as _OrtInferenceSession

from skellytracker.utilities.gpu_utils.ort_session_utils import (
    ExecutionProviderName,
    build_tuned_ort_session,
    migrate_legacy_trt_engine_cache,
    provider_needs_cuda_device_select,
    provider_uses_trt_engine_cache,
    resolve_engine_cache_dir,
    resolve_provider,
    resolve_yolox_provider,
)


def test_resolve_provider_trt_trx_when_available() -> None:
    available = {
        "nv_tensorrt_rtx",
        "CUDAExecutionProvider",
        "CPUExecutionProvider",
    }
    assert resolve_provider(requested="trt-trx", available_ort=available) == "trt-trx"


def test_resolve_provider_trt_trx_fallback_skips_classic_trt() -> None:
    available = {"TensorrtExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider"}
    assert resolve_provider(requested="trt-trx", available_ort=available) == "cuda"


def test_resolve_provider_trt_when_classic_available_despite_trt_trx() -> None:
    available = {
        "nv_tensorrt_rtx",
        "TensorrtExecutionProvider",
        "CUDAExecutionProvider",
        "CPUExecutionProvider",
    }
    assert resolve_provider(requested="trt", available_ort=available) == "trt"


def test_resolve_provider_trt_does_not_fallback_to_trt_trx() -> None:
    available = {
        "nv_tensorrt_rtx",
        "CUDAExecutionProvider",
        "CPUExecutionProvider",
    }
    assert resolve_provider(requested="trt", available_ort=available) == "cuda"


def test_resolve_provider_auto_linux_cuda_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    available = {"CUDAExecutionProvider", "CPUExecutionProvider"}
    assert resolve_provider(requested=None, available_ort=available) == "cuda"


def test_resolve_provider_auto_darwin_cpu(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.platform", "darwin")
    available = {"CUDAExecutionProvider", "CPUExecutionProvider"}
    assert resolve_provider(requested=None, available_ort=available) == "cpu"


def test_resolve_yolox_provider_maps_trt_family_to_cuda() -> None:
    assert resolve_yolox_provider("trt") == "cuda"
    assert resolve_yolox_provider("trt-trx") == "cuda"
    assert resolve_yolox_provider("cuda") == "cuda"
    assert resolve_yolox_provider("cpu") == "cpu"


def test_provider_helpers() -> None:
    assert provider_uses_trt_engine_cache("trt-trx") is True
    assert provider_uses_trt_engine_cache("trt") is True
    assert provider_uses_trt_engine_cache("cuda") is False
    assert provider_needs_cuda_device_select("trt-trx") is True


def test_resolve_engine_cache_dir_subdirs(tmp_path: Path) -> None:
    assert resolve_engine_cache_dir(tmp_path, "trt") == tmp_path / "classic"
    assert resolve_engine_cache_dir(tmp_path, "trt-trx") == tmp_path / "rtx"
    assert resolve_engine_cache_dir(tmp_path, "cuda") == tmp_path


def test_migrate_legacy_trt_engine_cache(tmp_path: Path) -> None:
    legacy = tmp_path / "foo.engine"
    legacy.write_text("engine", encoding="utf-8")
    migrate_legacy_trt_engine_cache(tmp_path)
    assert (tmp_path / "classic" / "foo.engine").is_file()
    assert not legacy.exists()
    migrate_legacy_trt_engine_cache(tmp_path)
    assert (tmp_path / "classic" / "foo.engine").is_file()


@patch("skellytracker.utilities.gpu_utils.ort_session_utils.ort.InferenceSession")
@patch("skellytracker.utilities.gpu_utils.ort_session_utils.ort.SessionOptions")
@patch("skellytracker.utilities.gpu_utils.ort_session_utils._trt_rtx_ep_devices")
def test_build_tuned_ort_session_trt_trx_provider(
    mock_trt_devices: MagicMock,
    mock_session_options_cls: MagicMock,
    mock_session_cls: MagicMock,
    tmp_path: Path,
) -> None:
    fake_session = create_autospec(_OrtInferenceSession, instance=True)
    fake_session.get_providers.return_value = ["nv_tensorrt_rtx"]
    mock_session_cls.return_value = fake_session
    mock_sess_options = MagicMock()
    mock_session_options_cls.return_value = mock_sess_options
    mock_trt_devices.return_value = [MagicMock(ep_name="nv_tensorrt_rtx")]

    build_tuned_ort_session(
        onnx_path="model.onnx",
        provider="trt-trx",
        engine_cache_dir=tmp_path / "trt_cache",
    )

    _args, kwargs = mock_session_cls.call_args
    assert "providers" not in kwargs
    assert kwargs["sess_options"] is mock_sess_options
    mock_sess_options.add_provider_for_devices.assert_called_once()
    trt_devices, trt_options = mock_sess_options.add_provider_for_devices.call_args[0]
    assert trt_devices == mock_trt_devices.return_value
    assert trt_options["device_id"] == "0"
    assert trt_options["nv_runtime_cache_path"].endswith("rtx")


def test_rtmpose_session_create_resolves_before_preload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_order: list[str] = []

    def _resolve(**_kwargs: object) -> ExecutionProviderName:
        call_order.append("resolve")
        return "cuda"

    def _preload() -> None:
        call_order.append("preload")

    monkeypatch.setattr(
        "skellytracker.trackers.rtmpose_tracker.rtmpose_session.resolve_provider",
        _resolve,
    )
    monkeypatch.setattr(
        "skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_cuda_dlls_loaded",
        _preload,
    )
    monkeypatch.setattr(
        "skellytracker.trackers.rtmpose_tracker.rtmpose_session.resolve_model_path",
        lambda _src: Path("det.onnx"),
    )
    monkeypatch.setattr(
        "skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_dynamic_batch",
        lambda path: path,
    )
    monkeypatch.setattr(
        "skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_prenms_model",
        lambda _path: None,
    )
    monkeypatch.setattr(
        "skellytracker.trackers.rtmpose_tracker.rtmpose_session.probe_supports_batch",
        lambda *_a, **_k: False,
    )
    def _fake_build(**_kwargs: object) -> ort.InferenceSession:
        return create_autospec(_OrtInferenceSession, instance=True)

    monkeypatch.setattr(
        "skellytracker.trackers.rtmpose_tracker.rtmpose_session.build_tuned_ort_session",
        _fake_build,
    )
    monkeypatch.setattr(
        "skellytracker.trackers.rtmpose_tracker.rtmpose_session.RTMPoseSession._warmup",
        lambda self: None,
    )

    from skellytracker.trackers.rtmpose_tracker.rtmpose_session import (
        RTMPoseSession,
        RTMPoseSessionConfig,
    )

    RTMPoseSession.create(
        RTMPoseSessionConfig(mode="lightweight", execution_provider="trt-trx"),
    )
    assert call_order.index("resolve") < call_order.index("preload")

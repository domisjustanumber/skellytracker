"""Mocked tests for RTMPoseSession.create wiring."""

from __future__ import annotations

from unittest.mock import MagicMock, create_autospec, patch

import pytest
from onnxruntime.capi.onnxruntime_inference_collection import InferenceSession as _OrtInferenceSession

from skellytracker.trackers.rtmpose_tracker.rtmpose_session import (
  RTMPoseSession,
  RTMPoseSessionConfig,
)


@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_prenms_model")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.resolve_model_path")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.build_tuned_ort_session")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_cuda_dlls_loaded")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.resolve_provider")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_dynamic_batch")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.probe_supports_batch", return_value=False)
def test_session_create_auto_resolves_before_preload(
  _probe_mock: MagicMock,
  dynamic_batch_mock: MagicMock,
  resolve_mock: MagicMock,
  preload_mock: MagicMock,
  build_mock: MagicMock,
  resolve_path_mock: MagicMock,
  prenms_mock: MagicMock,
) -> None:
  resolve_mock.return_value = "cuda"
  dynamic_batch_mock.side_effect = lambda path: path
  prenms_mock.return_value = None
  resolve_path_mock.return_value = "model.onnx"
  build_mock.return_value = create_autospec(_OrtInferenceSession, instance=True)

  RTMPoseSession.create(RTMPoseSessionConfig(execution_provider=None))

  resolve_mock.assert_called_once()
  preload_mock.assert_called_once()
  assert resolve_mock.call_args.kwargs.get("requested") is None


def test_session_config_default_execution_provider_is_auto() -> None:
  config = RTMPoseSessionConfig()
  assert config.execution_provider is None


@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_prenms_model")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.resolve_model_path")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.build_tuned_ort_session")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_cuda_dlls_loaded")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.resolve_provider")
def test_session_create_raises_when_provider_unavailable(
  resolve_mock: MagicMock,
  _preload_mock: MagicMock,
  build_mock: MagicMock,
  resolve_path_mock: MagicMock,
  prenms_mock: MagicMock,
) -> None:
  from skellytracker.utilities.gpu_utils.ort_session_utils import OnnxExecutionProviderStartupError

  resolve_mock.side_effect = OnnxExecutionProviderStartupError(
      "TRT unavailable",
      requested_provider="trt",
      expected_ort_provider="TensorrtExecutionProvider",
  )

  with pytest.raises(OnnxExecutionProviderStartupError):
    RTMPoseSession.create(RTMPoseSessionConfig(execution_provider="trt"))

  build_mock.assert_not_called()

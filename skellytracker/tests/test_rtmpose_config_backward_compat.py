"""Backward-compat tests for RTMPose config EP and device aliases."""

from __future__ import annotations

import warnings

from skellytracker.trackers.rtmpose_tracker.rtmpose_detector import RTMPoseDetectorConfig


def test_device_cuda_maps_to_explicit_provider() -> None:
  config = RTMPoseDetectorConfig(device="cuda")
  assert config.requested_provider() == "cuda"


def test_device_auto_requests_none_for_session() -> None:
  config = RTMPoseDetectorConfig()
  assert config.device == "auto"
  assert config.requested_provider() is None


def test_resolved_provider_deprecated_auto_probes_ort() -> None:
  config = RTMPoseDetectorConfig(device="auto")
  with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    provider = config.resolved_provider()
  assert any(issubclass(w.category, DeprecationWarning) for w in caught)
  assert provider in {"cpu", "cuda", "trt", "trt-trx"}


def test_explicit_execution_provider_overrides_device() -> None:
  config = RTMPoseDetectorConfig(device="cuda", execution_provider="cpu")
  assert config.requested_provider() == "cpu"

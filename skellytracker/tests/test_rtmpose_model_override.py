"""Tests for RTMPose model override validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from skellytracker.trackers.rtmpose_tracker.rtmpose_detector import RTMPoseDetectorConfig
from skellytracker.trackers.rtmpose_tracker.rtmpose_session import (
  RTMPoseSessionConfig,
  resolve_wholebody_models,
)


def test_detector_only_override_valid() -> None:
  models = resolve_wholebody_models(
    mode="performance",
    detector_model="yolox-tiny",
    pose_model=None,
  )
  assert models[0] == "yolox-tiny"


def test_invalid_pose_model_raises_validation_error() -> None:
  with pytest.raises(ValidationError):
    RTMPoseDetectorConfig(pose_model="rtmpose-hand")


def test_invalid_mode_raises_validation_error() -> None:
  with pytest.raises(ValidationError):
    RTMPoseSessionConfig(mode="turbo")  # type: ignore[arg-type]


def test_both_overrides_valid() -> None:
  config = RTMPoseDetectorConfig(
    detector_model="yolox-m",
    pose_model="rtmw-x-l_256x192",
  )
  assert config.detector_model == "yolox-m"
  assert config.pose_model == "rtmw-x-l_256x192"

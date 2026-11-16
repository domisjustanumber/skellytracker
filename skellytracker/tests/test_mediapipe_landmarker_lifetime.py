"""Tests for the timestamp fallback and the safe close of the old MediaPipe detectors (ADR-X6S9)."""
from __future__ import annotations

import numpy as np

from skellytracker.core.detectors.detection_context import DetectionContext
from skellytracker.core.detectors.keypoint_detectors.mediapipe import (
    MediapipeHandDetectorConfig,
    MediapipeHandKeypointDetector,
    MediaPipeSession,
    MediaPipeSessionConfig,
)
from skellytracker.core.detectors.keypoint_detectors.mediapipe.landmarker_lifetime import next_timestamp_ms


def test_fallback_timestamp_increases_on_each_call():
    first = next_timestamp_ms(-1)
    assert next_timestamp_ms(first) > first
    assert next_timestamp_ms(first + 10_000) == first + 10_001


def test_video_fallback_and_reset_keep_a_working_landmarker():
    session = MediaPipeSession.create(MediaPipeSessionConfig(running_mode="video"))
    detector = MediapipeHandKeypointDetector.create(MediapipeHandDetectorConfig(), session)
    image = np.zeros((64, 64, 3), np.uint8)
    for _ in range(3):  # calls in the same millisecond must not raise
        detector.detect(image)
    old_landmarker = detector.landmarker
    detector.reset_temporal_state()
    assert detector.landmarker is not old_landmarker
    assert not old_landmarker._handle
    detector.detect(image, DetectionContext(timestamp_ms=0))  # a new landmarker accepts a new sequence
    detector.close()
    detector.close()
    session.close()

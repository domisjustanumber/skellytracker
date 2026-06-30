"""Tests for RTMPoseSession exact-batch semantics."""

from __future__ import annotations

from unittest.mock import MagicMock, create_autospec, patch

import numpy as np
import pytest
from onnxruntime.capi.onnxruntime_inference_collection import InferenceSession as _OrtInferenceSession
from pydantic import ValidationError

from skellytracker.trackers.rtmpose_tracker.rtmpose_session import (
    RTMPoseSession,
    RTMPoseSessionConfig,
)
from skellytracker.trackers.rtmpose_tracker.rtmpose_session_errors import (
    BatchSizeMismatchError,
)


def _minimal_session(*, batch_size: int = 1) -> RTMPoseSession:
    return RTMPoseSession(
        config=RTMPoseSessionConfig(batch_size=batch_size),
        _active_provider="cpu",
    )


def _fake_image() -> np.ndarray:
    return np.zeros((64, 64, 3), dtype=np.uint8)


class TestRTMPoseSessionConfigBatchSize:
    def test_batch_size_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RTMPoseSessionConfig(batch_size=0)

    def test_batch_size_default_is_one(self) -> None:
        assert RTMPoseSessionConfig().batch_size == 1


@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_prenms_model")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.resolve_model_path")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.build_tuned_ort_session")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_cuda_dlls_loaded")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.resolve_provider", return_value="cpu")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_dynamic_batch", side_effect=lambda p: p)
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.probe_supports_batch", return_value=False)
@patch.object(RTMPoseSession, "_warmup")
def test_batch_size_property_matches_config_at_create(
    _warmup_mock: MagicMock,
    _probe_mock: MagicMock,
    _dynamic_mock: MagicMock,
    _resolve_mock: MagicMock,
    _preload_mock: MagicMock,
    build_mock: MagicMock,
    resolve_path_mock: MagicMock,
    prenms_mock: MagicMock,
) -> None:
    prenms_mock.return_value = None
    resolve_path_mock.return_value = "model.onnx"
    build_mock.return_value = create_autospec(_OrtInferenceSession, instance=True)

    session = RTMPoseSession.create(RTMPoseSessionConfig(batch_size=3))

    assert session.batch_size == 3


class TestPredictBatchExactBatch:
    def test_predict_batch_empty_returns_empty_list(self) -> None:
        session = _minimal_session(batch_size=2)
        assert session.predict_batch([]) == []

    def test_predict_batch_mismatch_raises_before_inference(self) -> None:
        session = _minimal_session(batch_size=2)
        with patch.object(session, "_detect_persons_batched") as detect_mock:
            with pytest.raises(BatchSizeMismatchError) as exc_info:
                session.predict_batch([_fake_image()])
        detect_mock.assert_not_called()
        assert exc_info.value.actual == 1
        assert exc_info.value.expected == 2

    def test_predict_single_on_multi_batch_session_raises(self) -> None:
        session = _minimal_session(batch_size=2)
        with pytest.raises(BatchSizeMismatchError):
            session.predict_single(_fake_image())


class TestPredictPoseFromBboxesExactBatch:
    def test_empty_returns_empty_list(self) -> None:
        session = _minimal_session(batch_size=2)
        assert session.predict_pose_from_bboxes([], []) == []

    def test_image_count_mismatch_raises(self) -> None:
        session = _minimal_session(batch_size=2)
        with patch.object(session, "_estimate_pose_batched") as estimate_mock:
            with pytest.raises(BatchSizeMismatchError):
                session.predict_pose_from_bboxes([_fake_image()], [np.zeros((1, 4))])
        estimate_mock.assert_not_called()

    def test_bboxes_count_mismatch_raises(self) -> None:
        session = _minimal_session(batch_size=2)
        images = [_fake_image(), _fake_image()]
        with patch.object(session, "_estimate_pose_batched") as estimate_mock:
            with pytest.raises(BatchSizeMismatchError):
                session.predict_pose_from_bboxes(images, [np.zeros((1, 4))])
        estimate_mock.assert_not_called()

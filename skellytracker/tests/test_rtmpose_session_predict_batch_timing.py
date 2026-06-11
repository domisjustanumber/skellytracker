"""GPU test: predict_batch populates all six generic stage timing attrs."""

import numpy as np
import pytest

from skellytracker.trackers.rtmpose_tracker.rtmpose_session import (
    RTMPoseSession,
    RTMPoseSessionConfig,
)


@pytest.mark.gpu
def test_predict_batch_exposes_six_stage_timings(test_image: np.ndarray) -> None:
    session = RTMPoseSession.create(
        RTMPoseSessionConfig(mode="lightweight", execution_provider="cuda", max_batch_size=1),
    )
    session.predict_batch([test_image])

    assert session.last_human_detection_preprocess_ms > 0.0
    assert session.last_human_detection_ms > 0.0
    assert session.last_human_detection_postprocess_ms > 0.0
    assert session.last_pose_estimation_preprocess_ms > 0.0
    assert session.last_pose_estimation_ms > 0.0
    assert session.last_pose_estimation_postprocess_ms > 0.0

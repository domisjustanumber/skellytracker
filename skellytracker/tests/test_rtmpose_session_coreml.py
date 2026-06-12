"""RTMPoseSession CoreML branch: provider forcing without ONNX/GPU."""

from pathlib import Path
from unittest.mock import create_autospec, patch

import onnxruntime as ort

from skellytracker.trackers.rtmpose_tracker.rtmpose_session import (
    RTMPoseSession,
    RTMPoseSessionConfig,
)


def test_create_forces_coreml_and_cpu_yolox_regardless_of_config_execution_provider():
    mock_ort_session = create_autospec(ort.InferenceSession, instance=True)
    build_calls: list[dict] = []

    def fake_build_tuned_ort_session(**kwargs):
        build_calls.append(kwargs)
        return mock_ort_session

    fake_dynbatch = Path("/fake/yolox.dynbatch.onnx")
    fake_prenms = Path("/fake/yolox.prenms.onnx")

    with (
        patch(
            "skellytracker.trackers.rtmpose_tracker.rtmpose_session.resolve_model_path",
            return_value=Path("/fake/model.onnx"),
        ),
        patch(
            "skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_dynamic_batch",
            return_value=fake_dynbatch,
        ),
        patch(
            "skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_prenms_model",
            return_value=fake_prenms,
        ),
        patch(
            "skellytracker.trackers.rtmpose_tracker.rtmpose_session.build_tuned_ort_session",
            side_effect=fake_build_tuned_ort_session,
        ),
        patch(
            "skellytracker.trackers.rtmpose_tracker.rtmpose_session.probe_supports_batch",
            return_value=True,
        ),
        patch.object(RTMPoseSession, "_warmup"),
    ):
        session = RTMPoseSession.create(
            RTMPoseSessionConfig(execution_provider="trt"),
        )

    assert session.active_provider == "coreml"

    providers_by_label = {call["log_label"]: call["provider"] for call in build_calls}
    assert providers_by_label["yolox"] == "cpu"
    assert providers_by_label["rtmpose"] == "coreml"
    assert providers_by_label["yolox_prenms"] == "cpu"

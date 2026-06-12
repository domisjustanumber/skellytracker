"""Table-driven YOLOX detector EP mapping tests (Feature 0)."""

from __future__ import annotations

from pathlib import Path
from typing import get_args
from unittest.mock import MagicMock, create_autospec, patch

import onnxruntime as ort
import pytest
from onnxruntime.capi.onnxruntime_inference_collection import InferenceSession as _OrtInferenceSession

from skellytracker.utilities.gpu_utils.ort_session_utils import (
    ExecutionProviderName,
    resolve_yolox_provider,
)


@pytest.mark.parametrize(
    ("active_provider", "expected_det_provider"),
    [
        ("trt", "cuda"),
        ("trt-trx", "cuda"),
        ("cuda", "cuda"),
        ("cpu", "cpu"),
    ],
)
def test_resolve_yolox_provider_matrix(
    active_provider: ExecutionProviderName,
    expected_det_provider: ExecutionProviderName,
) -> None:
    assert resolve_yolox_provider(active_provider) == expected_det_provider


def test_all_execution_providers_covered() -> None:
    for provider in get_args(ExecutionProviderName):
        resolve_yolox_provider(provider)


@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.build_tuned_ort_session")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_cuda_dlls_loaded")
@patch("skellytracker.trackers.rtmpose_tracker.rtmpose_session.resolve_provider")
def test_yolox_det_session_uses_mapped_provider_for_trt_trx(
    mock_resolve: MagicMock,
    _mock_preload: MagicMock,
    mock_build: MagicMock,
) -> None:
    mock_resolve.return_value = "trt-trx"
    fake_session = create_autospec(_OrtInferenceSession, instance=True)
    fake_session.get_providers.return_value = ["nv_tensorrt_rtx"]
    mock_build.return_value = fake_session

    from skellytracker.trackers.rtmpose_tracker.rtmpose_session import (
        RTMPoseSession,
        RTMPoseSessionConfig,
    )

    monkeypatch_paths = {
        "resolve_model_path": lambda _src: Path("model.onnx"),
        "ensure_dynamic_batch": lambda path: path,
        "ensure_prenms_model": lambda _path: None,
        "probe_supports_batch": lambda *_a, **_k: False,
    }
    with (
        patch(
            "skellytracker.trackers.rtmpose_tracker.rtmpose_session.resolve_model_path",
            monkeypatch_paths["resolve_model_path"],
        ),
        patch(
            "skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_dynamic_batch",
            monkeypatch_paths["ensure_dynamic_batch"],
        ),
        patch(
            "skellytracker.trackers.rtmpose_tracker.rtmpose_session.ensure_prenms_model",
            monkeypatch_paths["ensure_prenms_model"],
        ),
        patch(
            "skellytracker.trackers.rtmpose_tracker.rtmpose_session.probe_supports_batch",
            monkeypatch_paths["probe_supports_batch"],
        ),
        patch(
            "skellytracker.trackers.rtmpose_tracker.rtmpose_session.RTMPoseSession._warmup",
            lambda self: None,
        ),
    ):
        RTMPoseSession.create(
            RTMPoseSessionConfig(mode="lightweight", execution_provider="trt-trx"),
        )

    yolox_calls = [
        c
        for c in mock_build.call_args_list
        if c.kwargs.get("log_label") == "yolox"
    ]
    assert len(yolox_calls) == 1
    assert yolox_calls[0].kwargs["provider"] == "cuda"

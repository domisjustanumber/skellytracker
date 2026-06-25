"""Backend-free config for the RTMPose detector.

Separated from `rtmpose_detector` (which imports onnxruntime and the ORT session)
so the config can be imported — e.g. to build the SkeletonDetectorConfig union or
type a pipeline config — without loading the ONNX Runtime native library.
"""
import warnings
from typing import Literal, Self

from pydantic import model_validator

from skellytracker.trackers.base_tracker.base_tracker_abcs import BaseDetectorConfig, TrackerType
from skellytracker.utilities.gpu_utils.execution_provider_name import ExecutionProviderName

ModeName = Literal["performance", "lightweight", "balanced"]

# Backwards-compatible alias maintained for existing callers / configs that
# still pass `device="cuda"`. New code should use `execution_provider`.
_DEVICE_TO_PROVIDER: dict[str, ExecutionProviderName] = {
    "cuda": "cuda",
    "trt": "trt",
    "trt-trx": "trt-trx",
    "trt_trx": "trt-trx",
    "tensorrt": "trt",
    "mps": "coreml",
    "coreml": "coreml",
    "cpu": "cpu",
}


class RTMPoseDetectorConfig(BaseDetectorConfig):
    tracker_type: Literal[TrackerType.RTMPOSE] = TrackerType.RTMPOSE
    # Minimum SIMCC softmax peak to consider a keypoint "visible" for NaN-gating
    # and output filtering.  MUST match the tracking system's visibility threshold
    # (``rtmpose_tracking_state._DEFAULT_KPT_VISIBILITY_THRESHOLD``).
    # 0.004 = top ~50% of keypoints on a typical frame.
    confidence_threshold: float = 0.004
    mode: ModeName = "performance"
    backend: str = "onnxruntime"
    device: str = "auto"
    detector_model: str | None = None
    pose_model: str | None = None
    # When set, takes precedence over `device`. Drives the actual ORT provider selection.
    execution_provider: ExecutionProviderName | None = None
    # Which GPU to use. None = auto-select the device with the most VRAM at session creation.
    device_id: int | None = None
    # Keep only the N highest-confidence YOLOX detections. None = keep all.
    # Set to 1 for single-person use to suppress false positives from background clutter.
    max_persons: int | None = 1

    def requested_provider(self) -> ExecutionProviderName | None:
        """Explicit EP id for session config, or None for auto at session create."""
        if self.execution_provider is not None:
            return self.execution_provider
        if self.device != "auto":
            return _DEVICE_TO_PROVIDER.get(self.device, "cpu")
        return None

    def resolved_provider(self) -> ExecutionProviderName:
        """Deprecated — use ``requested_provider()`` and let session create resolve."""
        from skellytracker.utilities.gpu_utils.ort_session_utils import resolve_provider

        warnings.warn(
            "RTMPoseDetectorConfig.resolved_provider() is deprecated; "
            "use requested_provider() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        explicit = self.requested_provider()
        if explicit is not None:
            return explicit
        return resolve_provider(requested=None)

    @model_validator(mode="after")
    def _validate_model_selection(self) -> Self:
        from skellytracker.trackers.rtmpose_tracker.rtmpose_session import (
            resolve_wholebody_models,
        )

        resolve_wholebody_models(
            mode=self.mode,
            detector_model=self.detector_model,
            pose_model=self.pose_model,
        )
        return self

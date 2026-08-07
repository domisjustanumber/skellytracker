# Phase 1 — Update Dependency and Import Paths

**Risk:** Low  
**Files:** pyproject.toml + ~15 Python files  
**Strategy:** Mechanical rename — no behavioral changes

## Goal

Update freemocap's `pyproject.toml` to point at the new skellytracker branch, then update all import paths from old `trackers/` paths to new `core/` paths. No behavioral changes in this phase — just make imports compile.

## Steps

### 1.1: Update pyproject.toml

In `../freemocap/pyproject.toml`, change the skellytracker git dependency:

```toml
# Before
skellytracker = { git = "https://github.com/domisjustanumber/skellytracker", branch = "dom/rtmpose-config-models" }

# After
skellytracker = { git = "https://github.com/domisjustanumber/skellytracker", branch = "catch-up-upstream-core" }
```

Run `uv lock --upgrade-package skellytracker` to refresh.

### 1.2: Update Import Paths

Apply these mechanical renames across all freemocap files:

| Old Import Path | New Import Path |
|----------------|-----------------|
| `skellytracker.trackers.rtmpose_tracker.rtmpose_session` | `skellytracker.core.sessions.onnx_session` |
| `skellytracker.trackers.rtmpose_tracker.rtmpose_detector` | `skellytracker.core.detectors.keypoint_detectors.rtmpose.rtmpose_keypoint_detector` |
| `skellytracker.trackers.rtmpose_tracker.rtmpose_detector_config` | `skellytracker.core.detectors.keypoint_detectors.rtmpose.rtmpose_keypoint_detector` |
| `skellytracker.trackers.rtmpose_tracker.rtmpose_observation` | `skellytracker.core.data_primitives.observation` |
| `skellytracker.trackers.rtmpose_tracker.rtmpose_session_errors` | `skellytracker.core.sessions.session_errors` |
| `skellytracker.trackers.base_tracker.base_tracker_abcs` | `skellytracker.core` |
| `skellytracker.trackers.base_tracker.detector_helpers` | `skellytracker.core.detectors.detector_base_classes` |
| `skellytracker.trackers.base_tracker.task_events` | *(needs investigation — see Phase 2)* |
| `skellytracker.utilities.gpu_utils.ort_session_utils` | `skellytracker.core.sessions.ort_session_utils` |
| `skellytracker.utilities.gpu_utils` (ExecutionProviderName) | `skellytracker.core.sessions.execution_provider_name` |
| `skellytracker.trackers.charuco_tracker.*` | `skellytracker.core.detectors.keypoint_detectors.charuco.*` |
| `skellytracker.trackers.mediapipe_tracker.*` | `skellytracker.core.detectors.keypoint_detectors.mediapipe.*` |

### 1.3: Handle Symbol Renames

Some symbols were renamed in the new architecture. Update these in freemocap:

| Old Symbol | New Symbol |
|-----------|-----------|
| `RTMPoseSession` | `OnnxSession` |
| `RTMPoseSessionConfig` | `OnnxSessionConfig` |
| `RTMPoseDetector` | `RTMPoseKeypointDetector` (or the specific body/hand/face variant) |
| `RTMPoseDetectorConfig` | (varies by detector — needs Phase 4 detail) |
| `RTMPoseObservation` | `Observation` / `StageObservation` |
| `BatchSizeMismatchError` | Same name, new path: `skellytracker.core.sessions.session_errors` |
| `OnnxExecutionProviderStartupError` | Same name, new path: `skellytracker.core.sessions.session_errors` (or `skellytracker.core`) |
| `BaseObservation` | `Observation` |
| `BaseRecorder` | `DataStore` |
| `BaseDetectorConfig` | `KeypointDetectorConfig` or `ObjectDetectorConfig` |
| `SkeletonDetectorConfig` | Needs investigation — may need `KeypointDetectorConfig` union |
| `ExecutionProviderName` | Same name, new path |
| `CharucoBoardDefinition` | Same name, new path |
| `CharucoDetectorConfig` | Same name, new path |
| `CharucoObservation` | May be replaced by `Observation` with stage key |
| `MediapipeDetectorConfig` | Split into body/hands/face variants |
| `MediapipeObservation` | Replaced by `Observation` with stage key |
| `TrackerTaskEventCollector` | Needs investigation — may not exist in core/ |

### 1.4: Verify Import Resolution

```powershell
cd ../freemocap
uv run python -c "from freemocap.core.pipeline.realtime import realtime_skeleton_inference_node"
```

Expect compile errors from behavioral mismatches (session creation, predict_batch calls, etc.) — that's for Phases 2-5. This phase only ensures ALL import statements resolve.

## Deliverables

- [ ] pyproject.toml points to `catch-up-upstream-core` branch
- [ ] All `from skellytracker.*` imports updated across ~15 files
- [ ] Symbol renames applied (RTMPoseSession → OnnxSession, etc.)
- [ ] Imports compile without ModuleNotFoundError (behavioral errors expected)

## Verification

```powershell
cd ../freemocap
uv lock --upgrade-package skellytracker
uv run python -c "
from freemocap.core.pipeline.realtime.realtime_skeleton_inference_node import RealtimeSkeletonInferenceNode
from freemocap.core.pipeline.realtime.camera_node import CameraNode
from freemocap.core.tasks.mocap.posthoc_mocap_task import PosthocMocapTask
print('Phase 1 imports OK')
"
```

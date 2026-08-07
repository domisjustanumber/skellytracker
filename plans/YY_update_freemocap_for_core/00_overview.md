# Update Freemocap for New skellytracker core/ Architecture

**Status:** Planned  
**Prerequisite:** `skellytracker` branch `catch-up-upstream-core` merged to main (or at minimum, available as a dependency)

## Background

The skellytracker restructure (plan `XX_catch_up_with_upstream`) replaced the old `trackers/` architecture with the new `core/` architecture. The freemocap sibling repo (`../freemocap`) currently imports from the old API at ~20 unique import sites across ~15 files. This plan describes how to update freemocap to use the new API.

## Summary of Changes Needed

| Old Import | New Import |
|-----------|-----------|
| `skellytracker.trackers.rtmpose_tracker.rtmpose_session` | `skellytracker.core.sessions.onnx_session` |
| `skellytracker.trackers.rtmpose_tracker.rtmpose_detector` | `skellytracker.core.detectors.keypoint_detectors.rtmpose` |
| `skellytracker.trackers.base_tracker.base_tracker_abcs` | `skellytracker.core` |
| `skellytracker.trackers.base_tracker.detector_helpers` | `skellytracker.core.detectors.detector_base_classes` |
| `skellytracker.trackers.base_tracker.task_events` | `skellytracker.core.tracker` (or ported separately) |
| `skellytracker.utilities.gpu_utils.ort_session_utils` | `skellytracker.core.sessions.ort_session_utils` |
| `skellytracker.utilities.gpu_utils` (ExecutionProviderName) | `skellytracker.core.sessions.execution_provider_name` |
| `skellytracker.trackers.charuco_tracker.*` | `skellytracker.core.detectors.keypoint_detectors.charuco.*` |
| `skellytracker.trackers.mediapipe_tracker.*` | `skellytracker.core.detectors.keypoint_detectors.mediapipe.*` |

## Files Affected (by impact)

### HIGH Impact — Realtime Pipeline (core runtime path)

| File | Changes |
|------|---------|
| `core/pipeline/realtime/realtime_skeleton_inference_node.py` | Replace session creation, predict_batch calls, error handling, task events |
| `core/pipeline/realtime/realtime_skeleton_batch_logic.py` | Replace batch gating, observation types, BatchSizeMismatchError |
| `core/pipeline/realtime/camera_node.py` | Replace detector creation and detect() calls |
| `core/pipeline/realtime/camera_node_config.py` | Replace config types |
| `core/pipeline/realtime/realtime_pipeline_error.py` | Update EP error import path |

### MEDIUM Impact — Config and Types

| File | Changes |
|------|---------|
| `core/pipeline/realtime/realtime_skeleton_inference_node_config.py` | Update ExecutionProviderName import |
| `core/tasks/mocap/mocap_task_config.py` | Update detector config types |
| `core/pipeline/realtime/rtmpose_model_size.py` | Update docstring references |
| `pyproject.toml` | Update skellytracker dependency branch |

### LOW Impact — Posthoc and Calibration

| File | Changes |
|------|---------|
| `core/pipeline/posthoc/video_node.py` | Update detector helpers import |
| `core/pipeline/posthoc/posthoc_pipeline.py` | Update BaseDetectorConfig import |
| `core/tasks/mocap/posthoc_mocap_task.py` | Update observation and recorder imports |
| `core/tasks/calibration/posthoc_calibration_task.py` | Update charuco and recorder imports |
| `core/tasks/calibration/calibration_task_config.py` | Update charuco config import |
| `core/tasks/mocap/mocap_helpers/*.py` | Update recorder imports |

## Phases

| Phase | Name | Files | Risk |
|-------|------|-------|------|
| 1 | Update dependency and import paths | pyproject.toml, all 15 files | Low |
| 2 | Rewrite skeleton inference node | realtime_skeleton_inference_node.py | High |
| 3 | Rewrite skeleton batch logic | realtime_skeleton_batch_logic.py | High |
| 4 | Rewrite camera node | camera_node.py, camera_node_config.py | Medium |
| 5 | Update posthoc/calibration paths | 6 files | Low |
| 6 | End-to-end integration test | Full realtime pipeline | High |

## Implementation Documents

- [Phase 1 — Update Dependency and Import Paths](phase_1_deps_and_imports.md)
- [Phase 2 — Rewrite Skeleton Inference Node](phase_2_skeleton_node.md)
- [Phase 3 — Rewrite Skeleton Batch Logic](phase_3_batch_logic.md)
- [Phase 4 — Rewrite Camera Node](phase_4_camera_node.md)
- [Phase 5 — Update Posthoc and Calibration](phase_5_posthoc_calibration.md)
- [Phase 6 — End-to-End Integration Test](phase_6_integration_test.md)

## Key API Changes (Quick Reference)

### Session Setup
```python
# Old
from skellytracker.trackers.rtmpose_tracker.rtmpose_session import RTMPoseSession, RTMPoseSessionConfig
config = RTMPoseSessionConfig(mode="balanced", execution_provider="cuda", max_batch_size=4)
session = RTMPoseSession.create(config)

# New
from skellytracker.core.sessions.onnx_session import OnnxSession, OnnxSessionConfig, OnnxModelSpec
config = OnnxSessionConfig(
    batch_size=4,
    execution_provider="cuda",
    models=[OnnxModelSpec(name="yolox_m", source=..., input_size=(640,640), prepare=...), ...]
)
session = OnnxSession.create(config)
```

### Multi-Camera Inference
```python
# Old
keypoints_list = session.predict_batch(images)  # list of (keypoints, scores)

# New
observations, states = tracker.process_batch(images, frame_number, states)
# dict[camera_id, Observation], dict[camera_id, TrackerState]
```

### Detector
```python
# Old
from skellytracker.trackers.rtmpose_tracker.rtmpose_detector import RTMPoseDetector
detector = RTMPoseDetector.create(config=config)
observation = detector.detect(frame_number, image)

# New
from skellytracker.core import build_keypoint_detector
detector = build_keypoint_detector(config, sessions)
# Detection happens inside DetectionStage.run(), not called directly
```

### Task Events
```python
# Old
from skellytracker.trackers.base_tracker.task_events import TrackerTaskEventCollector

# New — task events may need to be ported to core/ or accessed differently
# Check if core/ has equivalent; if not, bring task_events.py into freemocap directly
```

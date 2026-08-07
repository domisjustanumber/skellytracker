# Phase 4 — Rewrite Camera Node

**Risk:** Medium — per-camera detector lifecycle  
**Files:** `camera_node.py`, `camera_node_config.py`  
**Depends on:** Phase 1

## Goal

Replace old detector creation (`RTMPoseDetector.create()`, `CharucoDetector.create()`) with new registry-based factory (`build_keypoint_detector()`).

## Current Flow

```python
# camera_node.py
from skellytracker.trackers.rtmpose_tracker.rtmpose_detector import RTMPoseDetector
from skellytracker.trackers.charuco_tracker.charuco_detector import CharucoDetector

# In CameraNode.__init__:
self.skeleton_detector = RTMPoseDetector.create(config=skel_cfg)
self.charuco_detector = CharucoDetector.create(config=charuco_cfg)

# In _run:
skeleton_obs = self.skeleton_detector.detect(frame_number, image)
charuco_obs = self.charuco_detector.detect(frame_number, image)
```

## New Flow

```python
from skellytracker.core import build_keypoint_detector
from skellytracker.core.detectors.keypoint_detectors.rtmpose.rtmpose_keypoint_detector import RTMPoseKeypointDetectorConfig
from skellytracker.core.detectors.keypoint_detectors.charuco.charuco_detector_config import CharucoDetectorConfig

# In CameraNode.__init__:
self.skeleton_detector = build_keypoint_detector(skel_config, sessions)
self.charuco_detector = build_keypoint_detector(charuco_config, sessions)

# In _run: detect() calls unchanged — both old and new detectors have the same interface
```

## Steps

### 4.1: Update Detector Config Types

`camera_node_config.py`:
```python
# Old
from skellytracker.trackers.base_tracker.detector_helpers import SkeletonDetectorConfig
from skellytracker.trackers.charuco_tracker.charuco_tracker_config import CharucoDetectorConfig
from skellytracker.trackers.rtmpose_tracker.rtmpose_detector import RTMPoseDetectorConfig

# New
from skellytracker.core.detectors.detector_base_classes import KeypointDetectorConfig
from skellytracker.core.detectors.keypoint_detectors.charuco.charuco_detector_config import CharucoDetectorConfig
from skellytracker.core.detectors.keypoint_detectors.rtmpose.rtmpose_keypoint_detector import RTMPoseKeypointDetectorConfig
```

`SkeletonDetectorConfig` (old union type from `detector_helpers.py`) no longer exists. Replace with `KeypointDetectorConfig` if the field accepts any keypoint detector, or use the specific RTMPose config type.

### 4.2: Update Detector Creation

```python
# Old
self.skeleton_detector = RTMPoseDetector.create(config=skel_cfg)

# New
self.skeleton_detector = build_keypoint_detector(skel_config, sessions)
```

The `sessions` dict must be available in `CameraNode` — pass it from the pipeline manager or skeleton node during construction.

### 4.3: Update detect() Return Type

Old `detect()` returns an `RTMPoseObservation` (subclass of `BaseObservation`). New `detect()` returns a `StageObservation` or similar. Update the return type annotation and any code that accesses observation fields.

## Relevant Files

| File | Change |
|------|--------|
| `core/pipeline/realtime/camera_node.py` | Replace detector creation, update detect() handling |
| `core/pipeline/realtime/camera_node_config.py` | Replace detector config types |

## Verification

```powershell
uv run python -c "
from freemocap.core.pipeline.realtime.camera_node import CameraNode
from freemocap.core.pipeline.realtime.camera_node_config import CameraNodeConfig
print('Phase 4 OK')
"
```

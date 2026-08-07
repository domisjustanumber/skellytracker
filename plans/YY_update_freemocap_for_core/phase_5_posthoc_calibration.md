# Phase 5 — Update Posthoc and Calibration Paths

**Risk:** Low — offline processing paths  
**Files:** ~6 files in `core/tasks/`, `core/pipeline/posthoc/`  
**Depends on:** Phase 1

## Goal

Update the posthoc (offline video processing) and calibration code paths to use new import paths and data types.

## Files and Changes

### 5.1: `core/pipeline/posthoc/video_node.py`

```python
# Old
from skellytracker.trackers.base_tracker.base_tracker_abcs import BaseDetectorConfig
from skellytracker.trackers.base_tracker.detector_helpers import create_detector_from_config, create_annotator_from_config

# New
from skellytracker.core.detectors.detector_base_classes import KeypointDetectorConfig  # or ObjectDetectorConfig
from skellytracker.core.detectors.detector_base_classes import build_keypoint_detector, build_object_detector
```

### 5.2: `core/pipeline/posthoc/posthoc_pipeline.py`

```python
# Old
from skellytracker.trackers.base_tracker.base_tracker_abcs import BaseDetectorConfig

# New
from skellytracker.core.detectors.detector_base_classes import KeypointDetectorConfig
```

### 5.3: `core/tasks/mocap/posthoc_mocap_task.py`

```python
# Old
from skellytracker.trackers.rtmpose_tracker.rtmpose_observation import RTMPoseObservation
from skellytracker.trackers.base_tracker.base_tracker_abcs import BaseObservation, BaseRecorder
from skellytracker.trackers.mediapipe_tracker import MediapipeObservation

# New
from skellytracker.core.data_primitives.observation import Observation, StageObservation
from skellytracker.core.data_primitives.data_store import DataStore
from skellytracker.core.detectors.keypoint_detectors.mediapipe import MediapipeObservation  # if still exists
```

**Note:** `RTMPoseObservation` and `MediapipeObservation` as separate classes may not exist in `core/`. The new API uses a generic `Observation` with `stages` dict keyed by stage name. Update isinstance checks accordingly.

### 5.4: `core/tasks/calibration/posthoc_calibration_task.py`

```python
# Old
from skellytracker.trackers.base_tracker.base_tracker_abcs import BaseRecorder
from skellytracker.trackers.charuco_tracker.charuco_observation import CharucoObservation
from skellytracker.trackers.charuco_tracker import CharucoBoardDefinition

# New
from skellytracker.core.data_primitives.data_store import DataStore
from skellytracker.core.data_primitives.observation import Observation
from skellytracker.core.detectors.keypoint_detectors.charuco.charuco_board_definition import CharucoBoardDefinition
```

### 5.5: `core/tasks/calibration/calibration_task_config.py`

```python
# Old
from skellytracker.trackers.charuco_tracker.charuco_tracker_config import CharucoDetectorConfig

# New
from skellytracker.core.detectors.keypoint_detectors.charuco.charuco_detector_config import CharucoDetectorConfig
```

### 5.6: `core/tasks/mocap/mocap_task_config.py`

```python
# Old
from skellytracker.trackers.base_tracker.detector_helpers import SkeletonDetectorConfig
from skellytracker.trackers.rtmpose_tracker.rtmpose_detector import RTMPoseDetectorConfig
from skellytracker.trackers.mediapipe_tracker import MediapipeDetectorConfig

# New
from skellytracker.core.detectors.detector_base_classes import KeypointDetectorConfig
from skellytracker.core.detectors.keypoint_detectors.rtmpose.rtmpose_keypoint_detector import RTMPoseKeypointDetectorConfig
from skellytracker.core.detectors.keypoint_detectors.mediapipe.body.mediapipe_pose_detector import MediapipePoseDetectorConfig
```

### 5.7: `core/tasks/mocap/mocap_helpers/*.py`

```python
# Old
from skellytracker.trackers.base_tracker.base_tracker_abcs import BaseRecorder
from skellytracker.trackers.charuco_tracker.charuco_observation import CharucoObservation

# New
from skellytracker.core.data_primitives.data_store import DataStore
from skellytracker.core.data_primitives.observation import Observation
```

## Verification

```powershell
uv run python -c "
from freemocap.core.pipeline.posthoc.video_node import VideoNode
from freemocap.core.tasks.mocap.posthoc_mocap_task import PosthocMocapTask
from freemocap.core.tasks.calibration.posthoc_calibration_task import PosthocCalibrationTask
print('Phase 5 OK')
"
```

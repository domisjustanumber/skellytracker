# Phase 1 — Bring in Upstream core/ Package

**Depends on:** Phase 0  
**Can run parallel with:** — (blocks Phases 2-6)  
**Estimated scope:** ~50+ new files across 10 sub-packages

## Goal

Copy the complete `skellytracker/core/` tree from upstream `freemocap/skellytracker` main branch into this fork. This is the foundation — all subsequent phases build on it.

## Context

The upstream has replaced the old `trackers/` architecture with a new `core/` architecture. The key structural difference:

- **Old**: `trackers/base_tracker/` — `BaseTracker`, `BaseDetector`, `BaseImageAnnotator`, `BaseRecorder`, `BaseObservation`, `PointCloud`
- **New**: `core/` — `Tracker`, `DetectionStage`, `ObjectDetector`, `KeypointDetector`, `Session`, `TrackerState`, `Keypoints`, `Observation`, `DataStore`

The new architecture is more composable: a `Tracker` contains N hierarchical `DetectionStage`s, each of which can have an `ObjectDetector` (finds regions) and multiple `KeypointDetector`s (find landmarks within regions).

## Steps

### 1.1: Fetch Upstream core/ Tree

Obtain the `skellytracker/core/` directory from the upstream `freemocap/skellytracker` repository (main branch). The Phase 0 inventory confirmed the actual structure:

```
skellytracker/core/
    __init__.py                             — public API (Tracker, Observation, Keypoints, etc.)
    annotation/
        annotator.py                        — Annotator ABC
        keypoint_annotator.py               — KeypointAnnotator
    config/
        __init__.py                         — re-exports
        detection_stage_config.py           — DetectionStageConfig
        detector_configs.py                 — ObjectDetectorConfig, KeypointDetectorConfig
        session_config.py                   — SessionConfig ABC
        tracker_config.py                   — TrackerConfig
    data_primitives/
        __init__.py                         — re-exports
        bounding_box.py                     — BoundingBox
        data_store.py                       — DataStore
        keypoints.py                        — Keypoints
        multi_person_observation.py         — MultiPersonDataStore
        observation.py                      — Observation, StageObservation
    detectors/
        __init__.py                         — re-exports
        detector_base_classes.py            — registries + build_* factories
        detection_context.py                — DetectionContext
        metadata.py                         — detector metadata
        keypoint_detectors/
            _schema_loader.py               — YAML schema loader
            aruco/                          — ArucoDetector + annotator + config + demo
            charuco/                        — CharucoDetector + board + annotator + demo
            mediapipe/                      — body/, hands/, face/ + model manager + demo
            rtmpose/                        — wholebody/, body/, hand/, face/ + preprocessing + demo
        object_detectors/
            precomputed/                    — PrecomputedObjectDetector
            yolox/                          — YoloxPersonDetector + preprocessing + dynamic batch + demo
    io/
        __init__.py                         — re-exports
        demo_manager.py                     — DemoManager
        process_video.py                    — process_video, process_folder, process_video_list
        processing_timer.py                 — ProcessingTimer
        tracker_mapping.py                  — TrackerMapping
    sessions/
        session.py                          — Session ABC
        cpu_session.py                      — CpuSession
        onnx_session.py                     — OnnxSession + OnnxSessionConfig + OnnxModelSpec
        mediapipe_session.py                — MediaPipeSession
        model_registry.py                   — ModelSource, resolve_model_path
        ort_session_utils.py                — build_tuned_ort_session, provider resolution
        session_errors.py                   — SkellytrackerSessionError hierarchy
        execution_provider_name.py          — ExecutionProviderName
    temporal_processing/
        __init__.py                         — re-exports
        bbox_policy.py                      — bbox policies
        bbox_smoothing.py                   — bbox smoothing
        keypoint_filtering.py               — Kalman/OneEuro filters
        keypoint_reset_policy.py            — reset policies
        multi_person_config.py              — multi-person config
        temporal_processing_config.py       — temporal config
        track_association.py                — IoU + keypoint association
    tracker/
        __init__.py                         — re-exports
        tracker.py                          — Tracker (process_image, process_batch)
        detection_stage.py                  — DetectionStage
        multi_person_tracker.py             — MultiPersonTracker
        person_track.py                     — PersonTrack
        tracker_state.py                    — TrackerState, StageState, smoothing states
```

Notable differences from our original expectations:
- `annotation/` has `keypoint_annotator.py` in addition to `annotator.py`
- Every detector subdirectory includes `run_demo.py` and YAML schema files
- `mediapipe/` has a top-level `mediapipe_model_manager.py`
- `rtmpose/` has top-level `rtmpose_keypoint_detector.py` and `rtmpose_preprocessing.py`
- `sessions/` has no `__init__.py` (imports are flat)
- `yolox/` has `_yolox_dynamic_batch.py` and `yolox_preprocessing.py`

### 1.2: Place in Local Fork

Copy the entire `core/` tree into `skellytracker/core/` in this repository. The package lives at:

```
c:\Users\Dom\GitHub\freemocap\skellytracker\skellytracker\core\
```

### 1.3: Check for New Dependencies

**Phase 0 findings:** The upstream actually **removed** `scipy` from dependencies (Kalman filter uses pure numpy). Key diff from local `pyproject.toml`:

| Change | Detail |
|--------|--------|
| `numpy==2.4.6` → `numpy` | Unpin numpy version |
| `scipy` removed | Kalman filter uses pure numpy; remove from dependencies |
| New extras | `legacy-mediapipe` (mediapipe 0.10.14), `yolo` (ultralytics~=8.0.202) |
| Renamed extras | `onnx-cuda` → `rtmpose-nvidia`, `onnx-cpu` → `rtmpose-cpu`, `onnx` → `rtmpose` |

Update `pyproject.toml` to match upstream dependency specs. Do **not** add `scipy`.

### 1.4: Fix Windows-Specific Issues

The upstream may have been developed on Linux/macOS. Check for:

- Path separators: replace hardcoded `/` with `pathlib.Path` or `os.path.join`
- DLL loading: ensure NVIDIA DLL preloading from `nvidia-*` pip packages works (see existing `GPU_SETUP_GUIDE.md`)
- Case sensitivity: Windows filesystem is case-insensitive, but Python imports are not — ensure consistent casing
- Subprocess calls: replace any `fork()` assumptions with `spawn()` on Windows

### 1.5: Run Import Smoke Test

```powershell
python -c "from skellytracker.core import Tracker, TrackerConfig, Observation, Keypoints"
```

### 1.6: Verify Imports

```powershell
python -c "from skellytracker.core import Tracker, TrackerConfig, Observation, Keypoints"
```

This verifies the package is importable. Expect it to fail if optional dependencies (mediapipe, onnxruntime) are not installed — that's fine; the core package should use deferred imports.

**Note:** Upstream tests are brought in during Phase 5, not here, to avoid overwriting local `conftest.py` fixtures prematurely.

## Deliverables

- [ ] `skellytracker/core/` directory exists with all upstream files
- [ ] `pyproject.toml` updated with any new dependencies
- [ ] Windows-specific import/path issues resolved
- [ ] `from skellytracker.core import Tracker` succeeds
- [ ] Upstream core tests pass (if any shipped)

## Verification

```powershell
# Import smoke test
python -c @"
from skellytracker.core import (
    Tracker, TrackerConfig, TrackerState,
    DetectionStage, DetectionStageConfig,
    Observation, StageObservation, Keypoints,
    KeypointDetector, ObjectDetector,
    build_keypoint_detector, build_object_detector,
    Session, SessionConfig,
    process_video, process_folder
)
print('All core imports OK')
"@

# Check for import errors in all subpackages
python -c @"
import skellytracker.core.annotation
import skellytracker.core.config
import skellytracker.core.data_primitives
import skellytracker.core.detectors
import skellytracker.core.io
import skellytracker.core.sessions
import skellytracker.core.temporal_processing
import skellytracker.core.tracker
print('All subpackages import OK')
"@
```

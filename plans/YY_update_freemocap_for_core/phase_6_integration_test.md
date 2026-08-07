# Phase 6 — End-to-End Integration Test

**Risk:** High — verifies the full realtime pipeline  
**Depends on:** Phases 1-5  
**Requires:** Working camera(s) or mock camera input

## Goal

Run the freemocap realtime pipeline end-to-end with the new skellytracker `core/` API and verify it produces valid keypoint data.

## Steps

### 6.1: Start Freemocap Backend

```powershell
cd ../freemocap
uv run python -m freemocap
```

### 6.2: Verify Session Creation

Check logs for:
- `OnnxSession: loaded model "yolox_m" (provider=cuda, device=0)`
- `OnnxSession: loaded model "rtmw-x-l_256x192" (provider=cuda, device=0)`
- `OnnxSession: warming up 2 model(s) on provider=cuda at batch_size=1`
- No `SessionCreationError` or `OnnxExecutionProviderStartupError`

### 6.3: Verify Real-Time Inference

With a camera connected:
1. Start realtime processing via the UI or API
2. Check that frames are processed without errors
3. Verify skeleton data appears in the frontend

Key log lines to look for:
- `Tracker.process_batch: frame=X, cameras=N` (if batch logging is enabled)
- No `BatchSizeMismatchError`
- No `KeyError` on `obs.stages["body"]`

### 6.4: Verify Error Recovery

1. Intentionally misconfigure the execution provider (e.g., request `trt` without TensorRT installed)
2. Verify `OnnxExecutionProviderStartupError` is caught and surfaced in the UI
3. Switch to a valid provider and verify recovery

### 6.5: Verify Posthoc Processing

```powershell
uv run python -c "
from freemocap.core.tasks.mocap.posthoc_mocap_task import PosthocMocapTask
# Run on a test video
task = PosthocMocapTask(...)
task.run()
print('Posthoc OK')
"
```

### 6.6: Verify Calibration

```powershell
uv run python -c "
from freemocap.core.tasks.calibration.posthoc_calibration_task import PosthocCalibrationTask
# Run on test charuco video
task = PosthocCalibrationTask(...)
task.run()
print('Calibration OK')
"
```

## Known Risks

| Risk | Mitigation |
|------|-----------|
| Model URLs changed in new architecture | Verify `MODEL_URLS` dict in `core/sessions/model_registry.py` matches what freemocap expects |
| `TrackerTaskEventCollector` missing from core/ | Ported to freemocap in Phase 2 step 2.4 |
| `RTMPoseObservation` / `MediapipeObservation` replaced by generic `Observation` | Update all isinstance checks and field accesses |
| `SkeletonDetectorConfig` union type removed | Replace with `KeypointDetectorConfig` or specific config type |
| `CharucoBoardDefinition.create_letter_size_5x3()` may have moved | Check new `charuco_board_definition.py` path |

## Verification (Full Suite)

```powershell
cd ../freemocap

# Backend unit tests
uv run pytest tests/ -x -v

# Import smoke test for all changed modules
uv run python -c "
from freemocap.core.pipeline.realtime.realtime_skeleton_inference_node import RealtimeSkeletonInferenceNode
from freemocap.core.pipeline.realtime.realtime_skeleton_batch_logic import infer_or_skip_batch
from freemocap.core.pipeline.realtime.camera_node import CameraNode
from freemocap.core.pipeline.posthoc.video_node import VideoNode
from freemocap.core.tasks.mocap.posthoc_mocap_task import PosthocMocapTask
from freemocap.core.tasks.calibration.posthoc_calibration_task import PosthocCalibrationTask
print('All modules import OK')
"
```

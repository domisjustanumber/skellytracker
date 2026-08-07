# Phase 2 — Rewrite Skeleton Inference Node

**Risk:** High — core realtime runtime path  
**Files:** `realtime_skeleton_inference_node.py`  
**Depends on:** Phase 1

## Goal

Rewrite `RealtimeSkeletonInferenceNode` to use the new `OnnxSession` / `Tracker` API instead of the old `RTMPoseSession` / `predict_batch` pattern. This is the most critical change — the skeleton worker is the heart of the realtime pipeline.

## Current Flow (Old API)

```python
# 1. Session creation
session_config = RTMPoseSessionConfig(
    mode=skel_config.mode,
    execution_provider=inf_config.execution_provider,
    max_batch_size=inf_config.max_batch_size,
)
session = RTMPoseSession.create(session_config)

# 2. Per-frame inference
images: list[np.ndarray] = [cam0_frame, cam1_frame, ...]  # positional list
keypoints_list = session.predict_batch(images)              # list of tuples

# 3. Publish results
for camera_id, (kps, scores) in zip(camera_ids, keypoints_list):
    publish(camera_id, kps, scores)
```

## New Flow (After Restructure)

```python
# 1. Session + Tracker creation
onnx_config = OnnxSessionConfig(
    batch_size=len(camera_ids),
    execution_provider=inf_config.execution_provider,
    models=[
        OnnxModelSpec(name="yolox_m", source=ModelSource(url=MODEL_URLS["yolox-m"]),
                      input_size=(640, 640), prepare=ensure_dynamic_batch),
        OnnxModelSpec(name="rtmw-x-l_256x192",
                      source=ModelSource(url=MODEL_URLS["rtmw-x-l_256x192"]),
                      input_size=(256, 192)),
    ],
)
onnx_session = OnnxSession.create(onnx_config)

tracker_config = TrackerConfig(
    stages=[
        DetectionStageConfig(
            name="body",
            object_detector=ObjectDetectorConfig(
                detector_type="yolox_person", session_backend="onnx"),
            keypoint_detectors=[
                KeypointDetectorConfig(
                    detector_type="rtmpose_body", session_backend="onnx"),
            ],
        ),
    ],
)
tracker = Tracker(stages=tracker_config.stages, sessions={"onnx": onnx_session})

# 2. Per-frame inference
camera_states: dict[str, TrackerState] = {
    cid: TrackerState() for cid in camera_ids
}
images: dict[str, np.ndarray] = dict(zip(camera_ids, frame_list))
observations, camera_states = tracker.process_batch(
    images, frame_number, camera_states, timings=ProcessingTimer()
)

# 3. Publish results
for camera_id, obs in observations.items():
    body = obs.stages["body"]
    publish(camera_id, body.keypoints, body.scores)
```

## Steps

### 2.1: Rewrite `_build_session()`

Replace `RTMPoseSession.create(RTMPoseSessionConfig(...))` with `OnnxSession.create(OnnxSessionConfig(...))`.

Key decisions:
- The `mode` field (light/medium/heavy) maps to specific model specs — define a helper `_models_for_mode(mode)` that returns the right `OnnxModelSpec` list
- `batch_size` replaces `max_batch_size`
- `detector_model` and `pose_model` fields become explicit `OnnxModelSpec` entries
- The YOLOX `ensure_dynamic_batch` prepare function needs to be imported from `core/detectors/object_detectors/yolox/_yolox_dynamic_batch.py`

### 2.2: Rewrite Per-Frame Inference

The old `infer_or_skip_batch()` in `realtime_skeleton_batch_logic.py` calls `session.predict_batch(images)`. Replace with `tracker.process_batch(images, frame_number, states)`.

Changes:
- `images` becomes `dict[str, np.ndarray]` keyed by camera ID, not a positional list
- `TrackerState` per camera must be maintained and passed through
- Return value changes from `list[tuple]` to `(dict[str, Observation], dict[str, TrackerState])`
- `Observation` has `stages` dict — extract body keypoints from `obs.stages["body"].keypoints`

### 2.3: Update Error Handling

`OnnxExecutionProviderStartupError` import path changes:
```python
# Old
from skellytracker.utilities.gpu_utils.ort_session_utils import OnnxExecutionProviderStartupError

# New
from skellytracker.core.sessions.session_errors import OnnxExecutionProviderStartupError
```
(Also importable from `skellytracker.core`)

`BatchSizeMismatchError` path changes similarly.

### 2.4: Handle Task Events

`TrackerTaskEventCollector` was imported from `skellytracker.trackers.base_tracker.task_events`. Verify if the upstream `core/` has an equivalent — from Phase 0, it does NOT appear to. Options:

1. **Port `task_events.py` into freemocap directly** (simplest)
2. **Use the new `ProcessingTimer`** from `core/io/processing_timer.py` instead (different API)
3. **Defer task events** — remove them temporarily and add back later

Recommendation: Port `task_events.py` into `freemocap/core/pipeline/realtime/task_events.py` as a local copy. It's a small file (~250 lines) with no skellytracker-internal dependencies.

### 2.5: Update Timing Access

Old code accessed `session.last_human_detection_*_ms` and `session.last_pose_estimation_*_ms` directly on the session object. The new `OnnxSession` doesn't have these fields. Instead, use `ProcessingTimer` passed to `process_batch()`:

```python
timings = ProcessingTimer()
observations, states = tracker.process_batch(images, frame_number, states, timings=timings)
# timings.stage_times has per-stage timing data
```

### 2.6: Handle Model Size/Preset Mapping

The `mode` field currently maps to `RTMPoseDetectorConfig` presets. In the new API, model selection is explicit via `OnnxModelSpec`. Create a mapping:

```python
def _model_specs_for_mode(mode: str, device_id: int) -> list[OnnxModelSpec]:
    """Map legacy mode names to OnnxModelSpec lists."""
    MODELS = {
        "light": [
            OnnxModelSpec(name="yolox_tiny", source=ModelSource(url=MODEL_URLS["yolox-tiny"]),
                          input_size=(416, 416), prepare=ensure_dynamic_batch),
            OnnxModelSpec(name="rtmw-s_256x192", source=ModelSource(url=MODEL_URLS["rtmw-s_256x192"]),
                          input_size=(256, 192)),
        ],
        "balanced": [...],
        "heavy": [...],
    }
    return MODELS.get(mode, MODELS["balanced"])
```

## Relevant Files (Freemocap)

| File | Change |
|------|--------|
| `core/pipeline/realtime/realtime_skeleton_inference_node.py` | Full rewrite of `_build_session()`, inference loop, error handling |
| `core/pipeline/realtime/realtime_skeleton_batch_logic.py` | See Phase 3 |

## Deliverables

- [ ] `_build_session()` creates `OnnxSession` + `Tracker` instead of `RTMPoseSession`
- [ ] Inference uses `tracker.process_batch()` with per-camera `TrackerState`
- [ ] Error handling updated for new import paths
- [ ] Task events ported or replaced
- [ ] Timing data sourced from `ProcessingTimer`

## Verification

```powershell
cd ../freemocap
uv run python -c "
from freemocap.core.pipeline.realtime.realtime_skeleton_inference_node import (
    RealtimeSkeletonInferenceNode, _build_session
)
print('Phase 2 imports OK')
"
# Full verification requires running the realtime pipeline end-to-end (Phase 6)
```

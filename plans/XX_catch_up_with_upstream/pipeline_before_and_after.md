# Realtime Pipeline: Before and After the Restructure

This document shows how the realtime pipeline is set up and run today (old `trackers/` architecture) compared to how it will work after catching up with upstream (new `core/` architecture). Use this as a reference when updating the freemocap sibling repo's skeleton inference node.

---

## 1. Session Setup

### Today (Old Architecture)

```python
from skellytracker.trackers.rtmpose_tracker.rtmpose_session import (
    RTMPoseSession,
    RTMPoseSessionConfig,
)

# Session config carries detector model, pose model, EP, and max_batch_size
config = RTMPoseSessionConfig(
    mode="light",                          # light / medium / heavy preset
    execution_provider="cuda",             # trt / cuda / cpu
    device_id=0,
    max_batch_size=4,                      # upper bound, actual batch varies
    engine_cache_dir=Path("./trt_engines"),
)

# Session is created; YOLOX detector + RTMPose pose models are loaded
session = RTMPoseSession.create(config)
# Internally calls build_tuned_ort_session() three times:
#   - YOLOX detector session (with TRT dynamic profiles if trt)
#   - YOLOX pre-NMS session
#   - RTMPose pose session
# Provider fallback: trt -> cuda -> cpu (silent)
```

### After Restructure (New Architecture)

```python
from skellytracker.core.sessions.onnx_session import (
    OnnxSession,
    OnnxSessionConfig,
    OnnxModelSpec,
)
from skellytracker.core.sessions.model_registry import ModelSource, MODEL_URLS
from skellytracker.core.sessions.ort_session_utils import ExecutionProviderName

# Each model is declared explicitly with its source, input size, and optional prepare step
config = OnnxSessionConfig(
    batch_size=4,                          # exact batch — must match camera count
    execution_provider="cuda",             # explicit or None for auto-detect
    device_id=0,                           # None = auto-select best GPU
    models=[
        OnnxModelSpec(
            name="yolox_m",
            source=ModelSource(url=MODEL_URLS["yolox-m"]),
            input_size=(640, 640),
            prepare=ensure_dynamic_batch,  # graph surgery for dynamic batch
        ),
        OnnxModelSpec(
            name="rtmw-x-l_256x192",
            source=ModelSource(url=MODEL_URLS["rtmw-x-l_256x192"]),
            input_size=(256, 192),
        ),
    ],
)

# Session is created; all models are loaded. If execution_provider is explicit
# and unavailable, require_provider() raises SessionCreationError immediately
# — no silent fallback.
session = OnnxSession.create(config)
# Internally calls build_tuned_ort_session() once per model.
# Provider resolution: require_provider() for explicit EP, auto_detect_provider() for None.
# After Phase 2: build_tuned_ort_session() has NO fallback chaining.
```

---

## 2. Tracker Setup

### Today (Old Architecture)

```python
from skellytracker.trackers.rtmpose_tracker.rtmpose_detector import RTMPoseDetector

# Detector wraps the session and adds tracking state
detector = RTMPoseDetector.create(
    session=session,
    tracking_mode="person",               # person / pose / none
)

# process_image() calls detector.detect() and records the observation
# No explicit state — tracking state lives inside the detector
observation = detector.detect(frame_number=0, image=frame)
```

### After Restructure (New Architecture)

```python
from skellytracker.core import (
    Tracker,
    TrackerConfig,
    TrackerState,
    DetectionStageConfig,
    KeypointDetectorConfig,
    ObjectDetectorConfig,
)

# Tracker composes N hierarchical DetectionStages.
# Each stage can have an ObjectDetector (finds people) and multiple
# KeypointDetectors (find landmarks within each person's bbox).
config = TrackerConfig(
    stages=[
        DetectionStageConfig(
            name="body",
            object_detector=ObjectDetectorConfig(
                detector_type="yolox_person",
                session_backend="onnx",
            ),
            keypoint_detectors=[
                KeypointDetectorConfig(
                    detector_type="rtmpose_body",
                    session_backend="onnx",
                ),
            ],
        ),
    ],
)

tracker = Tracker.create(
    config=config,
    sessions={"onnx": session},          # session backend keys
)

# State is explicit — passed in and returned per frame
state = TrackerState()
```

---

## 3. Single-Frame Inference

### Today (Old Architecture)

```python
# frame_number, image -> observation
observation = tracker.process_image(
    frame_number=0,
    image=frame,                          # (H, W, 3) BGR numpy array
)

# Observation carries a PointCloud with names, xyz, visibility
keypoints_2d = observation.to_2d_array()  # (N, 2)
names = observation.points.names          # tuple of landmark names
```

### After Restructure (New Architecture)

```python
# image, frame_number, state -> (observation, updated_state)
observation, state = tracker.process_image(
    image=frame,                          # (H, W, 3) BGR numpy array
    frame_number=0,
    state=state,                          # TrackerState — passed in/out explicitly
)

# Observation is a dict of StageObservations keyed by stage name
body_stage = observation.stages["body"]

# Each StageObservation has keypoints, bboxes, and metadata
keypoints = body_stage.keypoints          # Keypoints object
xyz = keypoints.xyz                       # (N, 3) array
names = keypoints.names                   # tuple of landmark names

# State carries per-stage smoothing/filtering state
# state.stage_states["body"] has bbox smoothing, keypoint filter state, etc.
```

---

## 4. Multi-Camera Batch Inference

### Today (Old Architecture)

```python
# The skeleton worker collects frames from N cameras into a list
images: list[np.ndarray] = [cam0_frame, cam1_frame, cam2_frame, cam3_frame]

# predict_batch() runs batched ORT inference
keypoints_list = session.predict_batch(images)
# Returns: list of (keypoints, scores) tuples — one per camera

# Camera-to-result association is positional — order must match camera_ids
for camera_id, (kps, scores) in zip(camera_ids, keypoints_list):
    publish_skeleton(camera_id, kps, scores)

# No cross-frame state — each batch is independent
# If batch size doesn't match session.max_batch_size, no error (silent mismatch)
```

### After Restructure (New Architecture)

```python
# States are maintained per camera across frames
camera_states: dict[str, TrackerState] = {
    "cam0": TrackerState(),
    "cam1": TrackerState(),
    "cam2": TrackerState(),
    "cam3": TrackerState(),
}

# Frames are keyed by camera_id (not positional list)
images: dict[str, np.ndarray] = {
    "cam0": cam0_frame,
    "cam1": cam1_frame,
    "cam2": cam2_frame,
    "cam3": cam3_frame,
}

# process_batch() runs all stages on all cameras simultaneously.
# ONNX detectors use a single batched ORT call.
observations, updated_states = tracker.process_batch(
    images=images,
    frame_number=frame_idx,
    states=camera_states,                 # per-camera states in, updated out
    timings=ProcessingTimer(),            # optional timing collection
)

# Results are keyed by camera_id — no positional dependency
for camera_id, obs in observations.items():
    body = obs.stages["body"]
    publish_skeleton(camera_id, body.keypoints, body.scores)

# States carry forward to next frame
camera_states = updated_states

# After Phase 3: batch size mismatch raises BatchSizeMismatchError
```

---

## 5. Webcam / Demo Loop

### Today (Old Architecture)

```python
from skellytracker.trackers.mediapipe_tracker import MediapipeHolisticTracker

# One-liner: opens webcam, runs inference, shows overlay
tracker = MediapipeHolisticTracker.create()
tracker.demo()
# Internally: WebcamDemoViewer handles the loop,
# calls tracker.process_image() and tracker.annotate_image() per frame
```

### After Restructure (New Architecture)

```python
from skellytracker.core.io.demo_manager import DemoManager
from skellytracker.core.annotation.keypoint_annotator import KeypointAnnotator

# Explicit loop — DemoManager handles camera, Tracker handles inference
tracker = Tracker.create(config, sessions={"onnx": session})
annotator = KeypointAnnotator()
state = TrackerState()

with DemoManager(camera_id=0) as demo:
    for frame in demo.frames():
        observation, state = tracker.process_image(
            image=frame,
            frame_number=demo.frame_number,
            state=state,
        )
        annotated = annotator.annotate(frame, observation)
        demo.show(annotated)
```

---

## 6. Video File Processing

### Today (Old Architecture)

```python
from skellytracker.io.process_videos.process_single_video import process_single_video

# Process a video file, save results
process_single_video(
    video_path=Path("input.mp4"),
    output_dir=Path("./output"),
    tracker=tracker,
)
```

### After Restructure (New Architecture)

```python
from skellytracker.core.io.process_video import process_video

# Same operation, new import path
process_video(
    video_path=Path("input.mp4"),
    output_dir=Path("./output"),
    tracker=tracker,
)
# Also available: process_folder(), process_video_list()
```

---

## 7. Detector Composition (New Capability)

The old architecture required a separate tracker class for each detector combination (e.g., `MediapipeHolisticTracker`, `YOLOMediapipeComboTracker`, `CompositeGPUTracker`). The new architecture composes detectors declaratively:

```python
# After restructure: compose any combination via config
config = TrackerConfig(
    stages=[
        # Stage 1: detect people with YOLOX
        DetectionStageConfig(
            name="person_detection",
            object_detector=ObjectDetectorConfig(
                detector_type="yolox_person",
                session_backend="onnx",
            ),
        ),
        # Stage 2: run body + hands + face on each person
        DetectionStageConfig(
            name="pose",
            keypoint_detectors=[
                KeypointDetectorConfig(detector_type="rtmpose_body", session_backend="onnx"),
                KeypointDetectorConfig(detector_type="rtmpose_hand", session_backend="onnx"),
                KeypointDetectorConfig(detector_type="rtmpose_face", session_backend="onnx"),
            ],
        ),
    ],
)
```

This composition is what previously required `CompositeGPUTracker` — now it's just config.

---

## 8. Temporal Filtering (New Capability)

The old architecture had no built-in filtering. The new architecture includes:

```python
from skellytracker.core.temporal_processing.temporal_processing_config import (
    TemporalProcessingConfig,
    KeypointFilterConfig,
    BBoxSmoothingConfig,
)

config = TrackerConfig(
    stages=[
        DetectionStageConfig(
            name="body",
            temporal=TemporalProcessingConfig(
                bbox_smoothing=BBoxSmoothingConfig(
                    method="ema",          # exponential moving average
                    alpha=0.3,
                ),
                keypoint_filter=KeypointFilterConfig(
                    method="one_euro",     # OneEuroFilter
                    min_cutoff=1.0,
                    beta=0.007,
                ),
            ),
            # ... detector configs ...
        ),
    ],
)
```

This replaces ad-hoc filtering that callers previously had to implement themselves.

---

## Summary: Key Differences for the Freemocap Skeleton Worker

| Aspect | Today | After Restructure |
|--------|-------|-------------------|
| Import path | `skellytracker.trackers.rtmpose_tracker` | `skellytracker.core` |
| Session type | `RTMPoseSession` | `OnnxSession` |
| Session config | `RTMPoseSessionConfig(mode=..., max_batch_size=...)` | `OnnxSessionConfig(batch_size=..., models=[...])` |
| Multi-camera API | `session.predict_batch(images: list)` → `list[tuple]` | `tracker.process_batch(images: dict, states: dict)` → `(dict[camera_id, Observation], dict[camera_id, TrackerState])` |
| State management | Implicit in detector | Explicit `TrackerState` passed per frame |
| Batch size error | Silent mismatch | `BatchSizeMismatchError` |
| EP fallback | `build_tuned_ort_session` appends CPU | `build_tuned_ort_session` single-provider only; `OnnxExecutionProviderStartupError` on failure |
| Detector composition | Hardcoded per tracker class | Declarative via `DetectionStageConfig` |
| Temporal filtering | None built-in | Configurable per stage (EMA, OneEuro, Kalman) |

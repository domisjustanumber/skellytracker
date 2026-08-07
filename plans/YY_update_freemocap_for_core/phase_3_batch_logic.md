# Phase 3 — Rewrite Skeleton Batch Logic

**Risk:** High — batch gating and inference path  
**Files:** `realtime_skeleton_batch_logic.py`  
**Depends on:** Phase 1

## Goal

Rewrite `should_run_inference()` and `infer_or_skip_batch()` to use `Tracker.process_batch()` instead of `RTMPoseSession.predict_batch()`.

## Current Flow

```python
# should_run_inference checks session.batch_size
if len(images) != session.batch_size:
    return SkeletonBatchOutcome.SKIPPED

# infer_or_skip_batch calls session.predict_batch
keypoints_list = session.predict_batch(images)
```

## New Flow

```python
# should_run_inference checks camera count against batch_size
if len(camera_states) != tracker_config.batch_size:
    return SkeletonBatchOutcome.SKIPPED

# infer_or_skip_batch calls tracker.process_batch
observations, updated_states = tracker.process_batch(
    images=images,  # dict[str, np.ndarray]
    frame_number=frame_number,
    states=camera_states,
)
```

## Steps

### 3.1: Update Function Signatures

- `should_run_inference(images, ordered_camera_ids, camera_ids, session)` → `should_run_inference(camera_states, batch_size)`
- `infer_or_skip_batch(...)` takes a `Tracker` + `dict[str, TrackerState]` instead of `RTMPoseSession`
- Return type changes from `list[BaseObservation]` to `dict[str, Observation]`

### 3.2: Update SkeletonBatchOutcome

```python
@dataclass
class SkeletonBatchOutcome:
    status: Literal["full", "partial", "skipped"]
    observations: dict[str, Observation] | None = None  # Changed from list[BaseObservation]
    updated_states: dict[str, TrackerState] | None = None  # NEW
    error: Exception | None = None
```

### 3.3: Update BatchSizeMismatchError Import

```python
# Old
from skellytracker.trackers.rtmpose_tracker.rtmpose_session_errors import BatchSizeMismatchError
# New
from skellytracker.core.sessions.session_errors import BatchSizeMismatchError
```

### 3.4: Access Keypoints from Observation

```python
# Old
for obs in observations:
    kps = obs.points.xyz  # PointCloud access

# New
for camera_id, obs in observations.items():
    body_stage = obs.stages.get("body")
    if body_stage:
        kps = body_stage.keypoints.xyz
        scores = body_stage.scores
```

## Verification

```powershell
uv run python -c "
from freemocap.core.pipeline.realtime.realtime_skeleton_batch_logic import (
    SkeletonBatchOutcome, should_run_inference, infer_or_skip_batch
)
print('Phase 3 OK')
"
```

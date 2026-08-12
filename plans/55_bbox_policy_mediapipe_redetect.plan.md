---
name: Replicate MediaPipe ROI Redetection in BBoxPolicy
overview: Make skellytracker's BBoxPolicy reuse the keypoint-derived crop while tracking holds and re-run the object detector the moment tracking is lost (previous frame produced no pose), mirroring MediaPipe PoseLandmarker's stream-mode gate — instead of relying only on a fixed frame interval.
todos:
  - id: track-loss-trigger
    content: Add a MediaPipe-style track-loss trigger to BBoxPolicy.should_redetect — redetect when keypoint tracking is enabled and bbox_state.keypoint_tracked_bbox is None (previous frame produced no tracked pose).
    status: pending
  - id: optional-redetect-interval
    content: Allow redetect_interval=None to disable periodic forced redetect (pure track-loss mode) in BBoxPolicy and BBoxPolicyConfig; keep default 1 for backward compatibility.
    status: pending
  - id: propagate-track-loss-signal
    content: In DetectionStage.run step 4b and run_batch step 5b, set keypoint_tracked_bbox=None when predict_bbox_from_keypoints returns no box (no valid keypoints) so the track-loss trigger fires next frame.
    status: pending
  - id: clear-empty-detection-state
    content: In DetectionStage.run and run_batch (batched-ONNX and per-camera branches), reset bbox state to a fresh BBoxSmoothingState when the object detector returns an empty list, clearing smooth_bbox, last_detection_frame, keypoint_tracked_bbox, last_detected_bbox.
    status: pending
  - id: docs
    content: Update rearchitecture-docs/skellytracker-architecture/11-bbox-policy-guide.md to describe the track-loss trigger and redetect_interval=None mode.
    status: pending
  - id: unit-tests
    content: Add BBoxPolicy.should_redetect unit tests in skellytracker/tests/test_temporal_processing.py for the track-loss trigger (True when keypoint_tracked_bbox is None within interval; False when present).
    status: pending
  - id: integration-tests
    content: Add a DetectionStage integration test with scripted object/keypoint detectors (reusing the test doubles pattern from test_multi_person_tracker.py): detector skipped while tracking holds; re-runs next frame and clears stale bbox state when person leaves.
    status: pending
  - id: verification
    content: Run pytest on touched test files, ruff/black/isort on changed files, and manually confirm demo_bbox_policy redetects (green box) on the frame after a person walks out of frame instead of reusing (orange box).
    status: pending
isProject: false
---

# Replicate MediaPipe ROI Redetection in BBoxPolicy

## Goal

Make skellytracker's `BBoxPolicy` behave like MediaPipe PoseLandmarker's
stream-mode ROI tracking: **reuse the keypoint-derived crop while a pose is
still being tracked, and re-run the full object detector the instant the
previous frame produced no pose.** Today skellytracker instead keys reuse off
`last_detection_frame` + a `redetect_interval`, with track loss only available
as an optional, default-off fitness check — which is why a stale bbox keeps
getting reused when nobody is in the frame.

## Reference: how latest MediaPipe implements this

From `mediapipe/tasks/cc/vision/pose_landmarker/pose_landmarker_graph.cc`
(`PoseLandmarkerGraph`, stream/VIDEO mode):

1. Two subgraphs: `PoseDetectorGraph` (full person detector) and
   `MultiplePoseLandmarksDetectorGraph` (landmark model).
2. The landmark graph always emits `POSE_RECTS_NEXT_FRAME` — the expanded rect
   enclosing this frame's landmarks. This is MediaPipe's equivalent of
   skellytracker's `keypoint_tracked_bbox`.
3. A `PreviousLoopbackCalculator` feeds those rects back into the next frame.
4. `NormalizedRectVectorHasMinSizeCalculator` sets
   `has_enough_poses = (prev rects >= num_poses)`. For `num_poses=1` this is
   simply "did last frame produce a pose?".
5. `DisallowIf(image, has_enough_poses)` **skips the full person detector**
   when there is a tracked rect, and runs it on the full image otherwise.
6. `AssociationNormRectCalculator(min_similarity_threshold=min_tracking_confidence)`
   ties detections to previous rects (identity); a back edge feeds next frame.

The rule is dead simple and cadence-free: reuse the previous ROI while
tracking holds; re-run the detector the moment the previous frame produced no
pose. A person leaving the frame triggers full re-detection on the very next
frame.

## Current skellytracker behavior

- `BBoxPolicy.should_redetect` returns `True` only when
  `last_detection_frame is None`, the `redetect_interval` has elapsed, or a
  configured fitness check fails. No track-loss check exists by default.
- `DetectionStage.run` step 4b and `run_batch` step 5b refresh
  `keypoint_tracked_bbox` only when `predict_bbox_from_keypoints` returns a
  box; when it returns `None` (no valid keypoints) the **stale** value is left
  in place, so the "track lost" signal never propagates.
- On an empty object-detection result, `last_detected_bbox` is cleared but
  `smooth_bbox` and `keypoint_tracked_bbox` keep stale values, and
  `last_detection_frame` still advances — so `predict_bbox` keeps returning
  the old crop and the next real search is postponed.
- Default `redetect_interval = 1` means the detector runs every frame by
  default; the reuse path only activates when a caller sets `> 1`.

## Changes

### 1. Track-loss-driven redetect (`bbox_policy.py`)

In `BBoxPolicy.should_redetect`, after the existing interval check, add the
MediaPipe analog: return `True` when `keypoint_bbox_expansion is not None` and
`stage_state.bbox_state.keypoint_tracked_bbox is None`. This is the direct
equivalent of MediaPipe's `has_enough_poses == False` gate. The
`keypoint_bbox_expansion is not None` guard is required so the check does not
fire every frame when keypoint tracking is disabled (where
`keypoint_tracked_bbox` is never populated).

Ordering stays: first-frame check, then interval check, then the new
track-loss check, then fitness checks.

### 2. Optional `redetect_interval` (`bbox_policy.py`, `temporal_processing_config.py`)

Change the type of `BBoxPolicy.redetect_interval` and
`BBoxPolicyConfig.redetect_interval` from `int` to `int | None`, and guard the
interval comparison with `self.redetect_interval is not None`. Default remains
`1` for backward compatibility; `None` disables periodic forced redetect so
behavior is purely track-loss driven, matching MediaPipe.

### 3. Propagate the track-loss signal (`detection_stage.py`)

In `DetectionStage.run` step 4b and `run_batch` step 5b, replace the
`if fresh_tracked is not None:` guard with an unconditional assignment:
set `keypoint_tracked_bbox = fresh_tracked` where `fresh_tracked` may be
`None` (no valid keypoints). This clears the stale tracked box so step 1 fires
on the next frame after a person leaves.

### 4. Clear stale bbox on empty detection (`detection_stage.py`)

In `DetectionStage.run`, when `object_detector.detect` returns an empty list,
rebuild the bbox state as a fresh `BBoxSmoothingState()` (all fields `None`)
instead of only blanking `last_detected_bbox`. Mirror this in `run_batch`:

- batched-ONNX path: after postprocess, reset the per-camera bbox state to a
  fresh state when that camera's result is empty (currently it keeps
  `last_detection_frame` and a stale `smooth_bbox`).
- per-camera non-ONNX path: same reset in the `should_redetect` branch when
  `detect` returns an empty list.

This prevents stale-box reuse and stale EMA blending, matching MediaPipe's
"no pose → full-frame detect next frame".

### 5. Documentation

Update `rearchitecture-docs/skellytracker-architecture/11-bbox-policy-guide.md`
(the as-built reference) to describe the track-loss trigger and the
`redetect_interval=None` mode.

### 6. Unit tests (`skellytracker/tests/test_temporal_processing.py`)

Add `BBoxPolicy.should_redetect` cases using the existing `_stage` helper:

- keypoint tracking enabled + `keypoint_tracked_bbox=None` + within interval →
  returns `True`.
- keypoint tracking enabled + `keypoint_tracked_bbox` set → returns `False`.
- keypoint tracking disabled + `keypoint_tracked_bbox=None` → returns `False`
  (guard behavior).

### 7. Integration test (new `skellytracker/tests/test_detection_stage_bbox_policy.py`)

Using scripted object/keypoint detector doubles (modeled on
`test_multi_person_tracker.py`), assert:

- while a person is present, `object_detector` is skipped on frames within the
  interval (reuse via `predict_bbox`).
- when the scripted object detector returns empty and keypoints are absent,
  the next frame re-runs the object detector and `bbox_state` fields
  (`smooth_bbox`, `last_detection_frame`, `keypoint_tracked_bbox`,
  `last_detected_bbox`) are cleared.

## Relevant files

- `skellytracker/core/temporal_processing/bbox_policy.py` — `should_redetect`,
  `redetect_interval` type
- `skellytracker/core/temporal_processing/temporal_processing_config.py` —
  `BBoxPolicyConfig.redetect_interval` type
- `skellytracker/core/tracker/detection_stage.py` — `run` steps 1/4b,
  `run_batch` steps 1/5b
- `skellytracker/core/tracker/tracker_state.py` — `BBoxSmoothingState`
  (reference; no change expected)
- `rearchitecture-docs/skellytracker-architecture/11-bbox-policy-guide.md` —
  doc update
- `skellytracker/tests/test_temporal_processing.py`,
  `skellytracker/tests/test_detection_stage_bbox_policy.py` (new) — tests

## Verification

1. `uv run pytest skellytracker/tests/test_temporal_processing.py`
2. `uv run pytest skellytracker/tests/test_detection_stage_bbox_policy.py`
3. `uv run poe lint` (or `ruff check skellytracker/`) and `black`/`isort` on
   changed files.
4. Manual: `uv run python -m skellytracker.examples.demo_bbox_policy` with a
   long `--redetect-seconds`; walk out of frame and confirm the box turns
   green (detector re-runs) on the next frame rather than staying orange
   (stale reuse).

## Decisions and out of scope

- MediaPipe parity is defined as: redetect iff the previous frame produced
  fewer than `num_poses` tracked rects; for the single-person case this means
  "no `keypoint_tracked_bbox`". No fixed cadence.
- `redetect_interval` default stays `1` for backward compatibility; `None`
  opts into pure MediaPipe-style behavior.
- Multi-person association (`min_tracking_confidence`) is out of scope —
  handled separately by `MultiPersonTracker` / `track_association.py`.
- Keep the existing anti-collapse clamps and bbox EMA; they are skellytracker
  hardening that MediaPipe lacks, and clearing state on empty detection
  removes the stale-blend problem.
- `BBoxAreaCollapseConfig` is not enabled by default; it becomes largely
  redundant with the new track-loss trigger.

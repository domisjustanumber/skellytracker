# Catch Up with Upstream — Plan Overview

**Status:** Planned  
**Parent branch goal:** Re-implement the realtime pipeline into the new upstream `core/` architecture.

## Background

The upstream `freemocap/skellytracker` main branch has undergone a complete rearchitecture from the old `trackers/` pattern (monolithic `BaseTracker`/`BaseDetector`/`BaseImageAnnotator`/`BaseRecorder`) to a new `core/` pattern (composable `Tracker` → `DetectionStage` → `ObjectDetector` + `KeypointDetector`).

This branch has realtime pipeline improvements (plans 10, 20, 30) implemented on the old architecture. The task is to restructure this codebase to match the upstream layout, porting the plan 10 and 30 invariants into the new architecture, then continue with plans 40-70 on the new foundation.

## Summary of Changes

| Old (this fork) | New (upstream target) |
|-----------------|----------------------|
| `skellytracker/trackers/` | `skellytracker/core/` |
| `BaseTracker` composes 1 detector + annotator + recorder | `Tracker` composes N hierarchical `DetectionStage`s |
| `BaseDetector` (monolithic) | `ObjectDetector` + `KeypointDetector` with registry |
| `PointCloud` | `Keypoints` |
| `BaseObservation` | `Observation` / `StageObservation` |
| `BaseRecorder` | `DataStore` / `MultiPersonDataStore` |
| Session buried in detectors | First-class `Session` (OnnxSession, MediaPipeSession, CpuSession) |
| No temporal filtering | Kalman/OneEuro filters, bbox smoothing, track association |
| No multi-person | `MultiPersonTracker` with IoU + keypoint association |
| No multi-camera batch | `process_batch()` |

## Phases

| Phase | Name | Depends On | Can Run Parallel With |
|-------|------|------------|----------------------|
| 0 | Inventory upstream `core/` package | — | — | ✅ Completed |
| 1 | Bring in upstream `core/` package | Phase 0 | — |
| 2 | Port Plan 10 strict ORT sessions | Phase 1 | Phase 3, Phase 4 |
| 3 | Port Plan 30 `batch_size` semantics | Phase 1 | Phase 2, Phase 4 |
| 4 | Remove old `trackers/` structure and migrate io/utilities/scripts | Phase 1 | Phase 2, Phase 3 |
| 5 | Port existing tests | Phases 1-4 | — |
| 6 | Clean up and document | Phase 5 | — |

## Git Strategy

All work on a dedicated branch (e.g., `catch-up-upstream-core`). Each phase is a separate commit:

```
Phase 0 → Phase 1 → Phase 2+3+4 (parallel) → Phase 5 → Phase 6
```

- **Phase 1 commit**: pure upstream copy with zero local modifications — makes `git diff` against upstream clean for future merges
- **Phases 2 and 3 both edit `ort_session_utils.py`**: complete Phase 2 before starting Phase 3, or do them sequentially by the same person. The "parallel" claim in the phase table is for Phases 3+4 running alongside Phase 2, not 2+3 running simultaneously
- **Phases 2-4 commits**: each independently revertible if issues arise
- **Do not merge to main** until Phase 6 verification passes
- **Rollback**: revert individual phase commits or reset branch to Phase 1

## How the Realtime Pipeline Is Affected

This restructure changes the architecture the realtime pipeline runs on, but preserves the invariants from plans 10 and 30. Here's what changes and what stays the same:

### What Changes for the Realtime Pipeline

| Concern | Old (`trackers/`) | New (`core/`) |
|---------|-------------------|---------------|
| **Multi-camera inference** | `RTMPoseSession.predict_batch(images)` — called directly by the skeleton worker | `Tracker.process_batch(images, frame_number, states)` — batched across cameras with per-camera `TrackerState` returned |
| **Session lifecycle** | Implicit: `RTMPoseSession.create()` happens inside the skeleton worker, hidden from the caller | Explicit: `OnnxSession.create(OnnxSessionConfig(...))` is a first-class object passed to `Tracker(sessions={"onnx": session})` |
| **Temporal filtering** | Not present — raw keypoints passed through | `TrackerState` carries Kalman/OneEuro filter state per stage, per camera. Bbox smoothing and keypoint reset policies are configurable |
| **Demo / visualization** | `BaseTracker.demo()` opens `WebcamDemoViewer` directly | `DemoManager` from `core/io/` handles webcam loop. `Tracker.process_image()` is called per frame with explicit `TrackerState` passing |
| **Video processing** | `io/process_videos/process_single_video.py` and `process_folder_of_videos.py` | `core/io/process_video.py` provides `process_video()`, `process_folder()`, `process_video_list()` |
| **Person detection** | `YOLOPoseTracker` / `YOLOObjectTracker` in `v1/` (monolithic) | `YoloxPersonDetector` as an `ObjectDetector` registered in `OBJECT_DETECTOR_REGISTRY` — feeds bboxes to downstream `KeypointDetector`s |
| **Keypoint detection** | Monolithic per-tracker: `MediapipeHolisticTracker`, `RTMPoseDetector`, etc. | Composable: `MediapipePoseKeypointDetector`, `RTMPoseBodyDetector`, `RTMPoseHandDetector`, `RTMPoseFaceDetector` — each registered in `KEYPOINT_DETECTOR_REGISTRY` |

### What Stays the Same

| Invariant | How It's Preserved |
|-----------|-------------------|
| **Strict ORT sessions (Plan 10)** | Phase 2 removes fallback chaining from `build_tuned_ort_session()`. `require_provider()` already raises `SessionCreationError` with no fallback. `OnnxExecutionProviderStartupError` is added for structured error reporting |
| **Exact batch_size semantics (Plan 30)** | Phase 3 renames `max_batch_size` → `batch_size` in the ORT utility layer, pins TRT profiles to exact batch, adds `BatchSizeMismatchError`. `OnnxSessionConfig.batch_size` already exists upstream |
| **Beartype runtime checking** | Unchanged — `skellytracker/__init__.py` keeps `beartype_this_package()` |
| **YAML-driven schemas** | Preserved: `_schema_loader.py` in `core/detectors/keypoint_detectors/` loads YAML files defining point names and connections |
| **pyproject.toml extras** | Extras renamed (`onnx-cuda` → `rtmpose-nvidia`) but resolve the same ONNX Runtime + NVIDIA DLL packages |

### What the Freemocap Sibling Repo Needs to Do (Out of Scope)

When the freemocap sibling repo (`../freemocap`) adopts this restructured skellytracker:

1. Replace `RTMPoseSession.create(config)` with `OnnxSession.create(OnnxSessionConfig(...))`
2. Replace direct `predict_batch()` calls with `Tracker.process_batch()` — this returns `(dict[camera_id, Observation], dict[camera_id, TrackerState])` instead of raw keypoint arrays
3. Pass `TrackerState` explicitly between frames instead of storing it implicitly
4. Use `from skellytracker.core import Tracker, TrackerConfig, OnnxSession, OnnxSessionConfig` instead of old tracker imports
5. The `RealtimePipelineManager` and skeleton worker need to construct a `Tracker` with `DetectionStage`s matching the desired detector composition (e.g., YOLOX person detection → RTMPose body keypoints)

This freemocap-side work is deferred to a future plan — it is NOT part of this restructure.

## What's NOT in Scope

- Freemocap sibling repo changes (plan 20 was freemocap-side only)
- Plans 40/50/60/70 implementation (sidecar spec, YOLO26, batch conversion, pose estimator spec)
- Porting `composite_gpu_tracker`, `vitpose_tracker`, `brightest_point_tracker` to new architecture
- Porting v1 legacy trackers (YOLO, OpenPose, MMPose)

## After This Plan

Once restructured, continue with the planned sequence: 40 → 60 → 50 → 70 (sidecar spec → batch conversion → YOLO26 → pose estimator spec).

## Implementation Documents

- [Phase 0 — Inventory Upstream core/ Package](phase_0_inventory_upstream.md)
- [Phase 1 — Bring in Upstream core/ Package](phase_1_core_package.md)
- [Phase 2 — Port Plan 10 Strict ORT Sessions](phase_2_strict_ort.md)
- [Phase 3 — Port Plan 30 batch_size Semantics](phase_3_batch_size.md)
- [Phase 4 — Remove Old trackers/ Structure and Migrate io/utilities/scripts](phase_4_remove_trackers.md)
- [Phase 5 — Port Existing Tests](phase_5_port_tests.md)
- [Phase 6 — Clean Up and Document](phase_6_cleanup.md)
- [Pipeline Before and After — Side-by-side code comparison](pipeline_before_and_after.md)

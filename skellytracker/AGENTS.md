# Package Instructions

These rules apply to the code and the tests under `skellytracker/`.
The root [`AGENTS.md`](../AGENTS.md) also applies.
In the spec-build stage, do not change the implementation code. You can change `tests/` to fix a test
([Stages](../specs/model-sidecar/model-addition-workflow/README.md#stages);
[Phase 3](../specs/model-sidecar/model-addition-workflow/phase-3-skellytracker.md)).
To change a package sidecar, also read [`specs/model-sidecar/AGENTS.md`](../specs/model-sidecar/AGENTS.md).

## Layout

The paths are under `skellytracker/`.

| Path | Role |
|---|---|
| `__main__.py` | Webcam demo CLI (`cli_main`) |
| `core/tracker/` | `Tracker`, `MultiPersonTracker`, `DetectionStage`, `TrackerState` |
| `core/config/` | Pydantic configs: `TrackerConfig`, `DetectionStageConfig`, `ObjectDetectorConfig`, `KeypointDetectorConfig`, `SessionConfig` |
| `core/sessions/` | ONNX Runtime, CPU and MediaPipe sessions. `model_registry.py` downloads `url` ONNX files to `~/.cache/skellytracker/models`. `hf_repo` files go to the Hugging Face cache. `batch_conversion.py` makes a fixed-batch ONNX file from a static-batch source (`static-batch-v1`). |
| `core/detectors/detector_base_classes.py` | Detector base classes, `OBJECT_DETECTOR_REGISTRY` and `KEYPOINT_DETECTOR_REGISTRY` |
| `core/detectors/keypoint_detectors/` | `aruco/`, `charuco/`, `mediapipe/`, `rtmpose/` (body, hand, face), `rtmw/wholebody/` |
| `core/detectors/object_detectors/` | `yolox/`, `keypoint_bbox/`, `precomputed/` |
| `core/detectors/processing/` | Generic preprocessing, affine crop, detection decode with NMS, SimCC decode (ADR-[0007](../decisions/entries/0007-generic-processing-package.md)) |
| `core/detectors/shared/skeletons/` | Tracked-point and skeleton fragments that sidecars include with `$ref` |
| `core/sidecar/` | `load_sidecar` (`loader.py`), `$ref` and `base` resolution (`resolution.py`), `SidecarModel` (`model.py`), version checks (`versioning.py`) |
| `core/data_primitives/` | `BoundingBox`, `Keypoints`, observations, data stores |
| `core/annotation/` | Overlay drawing (`Annotator`, `KeypointAnnotator`) |
| `core/temporal_processing/` | Box policy and smoothing, keypoint filters, track association |
| `core/io/` | `process_video.py`, `demo_manager.py` (webcam runner), tracker mapping, canonical mapping expansion |
| `examples/` | Example scripts |
| `tests/` | pytest suite. `tests/sidecar/` holds the sidecar tests and their golden fixtures. |

## Detector registries

Python adds a detector class to its registry when it imports the module.
The registry key is the `detector_type` of the detector config.
The sidecar paths are under `core/detectors/`.

| Registry | `detector_type` | Class | Sidecar |
|---|---|---|---|
| keypoint | `aruco` | `ArucoDetector` | none |
| keypoint | `charuco` | `CharucoDetector` | none |
| keypoint | `mediapipe_pose`, `mediapipe_hand`, `mediapipe_face` | MediaPipe detectors | none |
| keypoint | `rtmpose` | `RTMWWholebodyDetector` | `keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml` |
| keypoint | `rtmpose_body`, `rtmpose_hand`, `rtmpose_face` | RTMPose detectors | `keypoint_detectors/rtmpose/<part>/rtmpose-<part>.yaml` |
| object | `yolox_person` | `YoloxPersonDetector` | `object_detectors/yolox/yolox.yaml` |
| object | `keypoint_bbox` | `KeypointBoundingBoxDetector` | none |

- `PrecomputedObjectDetector` (`object_detectors/precomputed/`) is not in a registry.
- The key `rtmpose` runs RTMW (ADR-[0004](../decisions/entries/0004-detectors-migrated-in-place.md),
  ADR-[0005](../decisions/entries/0005-rtmw-moved-to-rtmw-family.md)).
- Do not change a `detector_type` string. Configs and callers select a detector with it.
- A `detector_type` key is not a catalog key. The catalog keeps each key as an alias of
  `<model_id>@skellytracker` ([Versioning](../specs/model-sidecar/format/versioning.md#implementer-guidance)).
- Shim modules under `keypoint_detectors/rtmpose/` give the RTMW detector its old names
  `RTMPoseDetectorConfig`, `RTMPoseKeypointDetector` and `RTMPOSE_MODEL_SPECS`. Do not remove a shim
  while a file imports its path.
- All five package sidecars have `schema_version: "v2024.09.1019"`.

## ONNX Runtime

- `OnnxSessionConfig.execution_provider` (`core/sessions/onnx_session.py`) selects `trt`, `cuda`,
  `coreml`, `directml` or `cpu`.
- `None` selects the first available provider in this order: `trt`, `cuda`, `coreml` (macOS only),
  `cpu` (`auto_detect_provider` in `core/sessions/ort_session_utils.py`).
- A provider that is not available raises `SessionCreationError`. There is no CPU fallback.
- On Windows, `cuda` and `trt` load the CUDA and cuDNN DLLs from the `nvidia-*` pip packages
  (`_load_nvidia_dlls_on_windows`).

## Code conventions

- `__init__.py` calls `beartype_this_package()`. Runtime type checks apply to the whole package.
- Configs are Pydantic `BaseModel` subclasses. Trackers, stages and detectors are `@dataclass` classes.
- Do not run `black` or `isort` on the package. They would change most files. Do not reformat lines
  that your change does not need.
- Do not import the `keypoint_detectors.rtmpose` package at module level in
  `rtmw_wholebody_detector.py`. The shims import that module, so the import makes a cycle.
- Put generic processing code in `core/detectors/processing/`. Generic code prepares an image or
  decodes a model output for more than one model family. Import the specific module.
  `processing/__init__.py` re-exports nothing.
- Keep the code of one model family in its folder. For example, the YOLOX anchor-grid decode and
  `yolox_detection_decode` stay in `object_detectors/yolox/yolox_decode.py`.
- Keep `core/detectors/overlay_groups.py` outside `processing/`. It groups skeleton connections for
  annotation.
- Keep only the code that parses and resolves sidecars in `core/sidecar/`. `runtime.py` holds only
  `sidecar_model_spec`.
- Do not write migration history in a docstring. Write it in a decision entry or a commit message.

## Tests

- The first test run needs network access. `tests/conftest.py` downloads the test images and the
  test recording from the `freemocap/skellysamples` releases on GitHub.
- The ONNX detectors download their ONNX files to `~/.cache/skellytracker/models`. The MediaPipe
  detectors download their model files to `~/.freemocap/skellytracker-models` (`CACHE_DIR` in
  `keypoint_detectors/mediapipe/mediapipe_model_manager.py`).
- `-o faulthandler_timeout=300` prints a stack trace when a test runs for more than 300 s.
- On Windows, run each video test file alone. These failures are known:
  - `test_data_store.py` and `test_mediapipe_video.py` fail in setup with "Input timestamp must be
    monotonically increasing". The cause is in the
    [implementation plan](../specs/sidecar-implementation-plan.md): "MediaPipe timestamps on Windows".
  - In a run of all video tests, `test_process_video.py` does not finish:
    `PoseLandmarker.__del__` runs during `detect_for_video`, and that call does not return. Alone, it
    passes.
- If a failure shows a code defect, report it. Do not fix the code in the spec-build stage.

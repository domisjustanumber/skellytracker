# Package Instructions

These rules apply to the code and the tests under `skellytracker/`.
The root [`AGENTS.md`](../AGENTS.md) also applies.
To change a package sidecar, also read [`specs/model-sidecar/AGENTS.md`](../specs/model-sidecar/AGENTS.md).

## Layout

The paths are under `skellytracker/`.

| Path | Role |
|---|---|
| `__main__.py` | Webcam demo CLI (`cli_main`), and the commands `detectors` and `describe <key>` (`core/detectors/cli.py`) |
| `core/tracker/` | `Tracker`, `MultiPersonTracker`, `DetectionStage`, `TrackerState` |
| `core/config/` | Pydantic configs: `TrackerConfig`, `DetectionStageConfig`, `ObjectDetectorConfig`, `KeypointDetectorConfig`, `SessionConfig` |
| `core/sessions/` | ONNX Runtime, CPU and MediaPipe sessions. `model_registry.py` downloads `url` ONNX files to `~/.cache/skellytracker/models`. `hf_repo` files go to the Hugging Face cache. `batch_conversion.py` makes a fixed-batch ONNX file from a static-batch source (`static-batch-v1`). |
| `core/detectors/catalog.py` | The catalog of the `detectors` entry point ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) items 1, 2 and 6): `list_detectors`, `get_detector`, `describe_detector`, `load_detector_sidecar`, the sidecar roots and `STATIC_DETECTORS`, the table of the entries with no sidecar. It imports no detector module. `core/detectors/__init__.py` exports the API. |
| `core/detectors/detector_base_classes.py` | Detector base classes, `OBJECT_DETECTOR_REGISTRY` and `KEYPOINT_DETECTOR_REGISTRY` |
| `core/detectors/keypoint_detectors/` | `mediapipe/`, `rtmpose/` (body, hand, face), `rtmw/wholebody/` |
| `core/detectors/calibration_detectors/` | `aruco/`, `charuco/` ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 4). Import `calibration_detectors` to register them. |
| `core/detectors/mediapipe_holistic.py` | `HolisticRunner`: the MediaPipe Tasks `HolisticLandmarker` for the variant `holistic` of the node `mediapipe_tasks`. It does not use the old detector contract ([ADR-X6S9](../decisions/entries/X6S9-mediapipe-close-from-the-garbage-collector.md)). |
| `core/detectors/object_detectors/` | `yolox/`, `keypoint_bbox/`, `precomputed/` |
| `core/detectors/processing/` | Generic preprocessing, affine crop, detection decode with NMS, SimCC decode (ADR-[0007](../decisions/entries/0007-generic-processing-package.md)) |
| `core/detectors/processing/pre/`, `core/detectors/processing/post/` | The spec processing modules, one module for each spec section ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 4). They take the spec model of `core/model_spec/`. `pre/preprocess.py` holds the resize dispatcher (`resize_image`, `ResizeGeometry`) and `preprocess_image`. `post/unprojection.py` holds the inverse dispatcher (`resize_inverse`). Do not import the old processing modules in them. |
| `core/detectors/generic/` | The generic detectors ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 6): `GenericObjectDetector`, `GenericKeypointDetector`, `create_detector(key, execution_provider=...)`, `open_session` (`session.py`), the download of a `url` artifact (`download.py`), the batch conversion `model_batch_convert` (`batch_conversion.py`, which needs the extra `onnx`), the batch loop (`inference.py`) and the overlay groups (`overlay.py`). They use the spec model, `processing/pre/`, `processing/post/` and `eps.build_session()`. Do not import the old detector contract, `core/tracker/` or `core/sessions/` in them. |
| `core/detectors/shared/skeletons/` | Tracked-point and skeleton fragments that sidecars include with `$ref` |
| `core/model_zoo/` | The package sidecar root, with the spec layout ([Storage layout](../specs/model-sidecar/format/file-layout.md#storage-layout); [ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 5). It holds data only. Git ignores its `.onnx` files, and no wheel or sdist holds them. |
| `core/model_zoo/landmark_schemas/` | Landmark schema files of the registry ([Landmark schema](../specs/model-sidecar/post/keypoint/landmark-schema.md); [ADR-23F5](../decisions/entries/23F5-landmark-schema-registry.md)) |
| `core/errors.py` | The errors of `eps` and of the pipeline runtime, and the exit-code table of the CLIs ([ADR-D8DH](../decisions/entries/D8DH-sessions-errors-and-the-ready-rule.md) items 1 and 2). The old `core/sessions/session_errors.py` is a different module. |
| `core/system/` | `probe_host()`, `probe_runtime()`, `probe_environment()`, `probe_loaded_libraries()` and the device keys of the GPUs. Each value is fixed while the application runs. |
| `core/metrics/` | `LiveSampler` and `free_vram(device)`: system-level live values only |
| `core/_hardware/` | Private readers: NVML, DXGI with one D3DKMT query, the Windows registry, psutil (Windows only), `/proc` and `/sys`, macOS `sysctl`, Windows PDH ([ADR-P1F3](../decisions/entries/P1F3-hardware-probe-devices-and-multi-gpu.md) items 1 and 2) |
| `core/eps/` | The EP catalog (`ep_catalog.yaml`, `ep_lock.yaml`), the EP store, `install()`, `ensure_registered()`, `verify()`, `recommend()`, `run_devices()`, `check_start()`, `status()`, `build_session()` and the CLI `skellytracker-eps` (`cli.py`) |
| `_pyinstaller/` | The PyInstaller entry points and the data-only hook. It is outside `core/`. No package module imports it. |
| `core/sidecar/` | The old loader of the old package sidecars. Do not change it, and do not import it in new code. `load_sidecar` (`loader.py`), `$ref` and `base` resolution (`resolution.py`), `SidecarModel` (`model.py`), version checks (`versioning.py`) |
| `core/model_spec/` | The spec loader at spec version 2.0.0 ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 8): `load_sidecar(path, sidecar_root, user_root)` (`loader.py`), `$ref` resolution with hash checks (`resolution.py`), the `V-` rules (`rules.py`, `check_sidecar`), `SidecarModel` (`model.py`), the landmark schema registry (`landmark_schemas.py`), the implemented versions (`versioning.py`), the SPDX check (`spdx.py`), the artifact hash check with its cache (`artifacts.py`), the selector matching (`sidecar_normalize.py`) and the section table with the capability check (`sections.py`). Remove a `postprocessor` section from `UNIMPLEMENTED_SECTIONS` of `sections.py` in the commit that adds its processing module. Stage 2.3 of the implementation plan moves it to `core/sidecar/`. |
| `core/data_primitives/` | `BoundingBox`, `Keypoints`, observations, data stores |
| `core/annotation/` | Overlay drawing (`Annotator`, `KeypointAnnotator`) |
| `core/temporal_processing/` | Box policy and smoothing, keypoint filters, track association |
| `core/io/` | `process_video.py`, `demo_manager.py` (webcam runner), tracker mapping, canonical mapping expansion |
| `examples/` | Example scripts |
| `tests/` | pytest suite. `tests/sidecar/` holds the tests of the old loader and their golden fixtures. `tests/model_spec/` holds the tests of the spec loader. `tests/processing/` holds the tests of the spec processing modules. `tests/detectors/` holds the tests of the catalog, on temporary sidecar roots, and the tests of the generic detectors, on ONNX models that `onnx.helper` makes. |

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
- A `detector_type` key is not a catalog key. The catalog has no alias for it: the old keys go with
  their detectors ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 2).
- Shim modules under `keypoint_detectors/rtmpose/` give the RTMW detector its old names
  `RTMPoseDetectorConfig`, `RTMPoseKeypointDetector` and `RTMPOSE_MODEL_SPECS`. Do not remove a shim
  while a file imports its path.
- All five package sidecars have `schema_version: "v2024.09.1019"`.

## ONNX Runtime

- `onnxruntime` is a base dependency. It gives the CPU EP, and the CoreML EP on macOS
  ([ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) item 2).
- `OnnxSessionConfig.execution_provider` (`core/sessions/onnx_session.py`) selects `coreml` or `cpu`.
- `None` selects the first available provider in this order: `coreml` (macOS only), `cpu`
  (`auto_detect_provider` in `core/sessions/ort_session_utils.py`).
- A provider that is not available raises `SessionCreationError`. There is no CPU fallback.

The four items above are the old session code in `core/sessions/`. Do not change it. Stage 2.4 of
the implementation plan deletes it. New code builds each session with `eps.build_session()`:

- New code takes the EP as `execution_provider`, a concrete key of the EP catalog: `trt-rtx`, `cuda`,
  `coreml` or `cpu`. No environment variable selects the EP or the device.
- `eps.build_session()` serves only new code. Do not connect it to `OnnxSession` or `Tracker.create`.
- A GPU EP is a plugin EP pack in the EP store. Do not add a GPU package to `pyproject.toml`.
- `core/eps/ep_catalog.yaml` is written by hand. Only `uv run python tools/ep_catalog.py --refresh`
  writes `ep_lock.yaml`, and it uses the network. Run it after each change of the catalog.
  `ort_core.version` must equal the `onnxruntime` pin: change the pin, the catalog, the lock and
  `uv.lock` in one commit.
- `eps` reads no sidecar. The caller fills `ModelRef`.
- A plain `import skellytracker.core.eps` must load no `onnxruntime`. Import `onnxruntime` in the
  function that uses it. The probes of `core.system` and the sampler of `core.metrics` make no CUDA
  call and load no EP library.
- A record of `system`, `metrics` and `eps` is a frozen dataclass with no `dict` field. Memory is
  `int` bytes, time is `int` ns, and a field that ends in `utilization` is a ratio from 0 to 1. No
  text holds an absolute path or a hostname.

## Freeze rules

A frozen application must find each module and each data file. `tests/test_import_rules.py` checks
these rules ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 3).

- Import each module with a plain statement. A lazy import is a plain statement in a function body.
  Do not use `importlib.import_module`, `__import__`, `exec` or `eval` with a computed name.
- Read the metadata of a fixed distribution with a literal call in the full form, for example
  `importlib.metadata.version("mediapipe")`. Do not alias `importlib.metadata`.
- `_pyinstaller/hook-skellytracker.py` collects `**/*.yaml`. A commit that adds a data file of an
  other type changes `includes` of the hook in the same commit.
- Do not add a hook for an other package to `_pyinstaller/`.

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
- On Python 3.13.18, all tests pass in one run, also on Windows and with the video tests.
- `tools/run_checks.py` stops the MediaPipe check after 300 s, runs the next checks and then exits
  with 124. A hang in the MediaPipe tests is a regression. Report the note that the tool prints.
  Do not change the MediaPipe tests to hide a hang, for example with a skip, an xfail or a timeout
  plugin: they are its regression test
  ([ADR-R3F1](../decisions/entries/R3F1-mediapipe-check-time-limit.md)).

- The markers `gpu`, `ep_pack` and `pyinstaller` are opt-in. `tests/conftest.py` deselects a test
  with one of them, unless the `-m` expression names the marker. `-m ep_pack` needs the network.
  `-m pyinstaller` freezes an application. `-m gpu` is the local GPU gate: it needs an NVIDIA GPU and
  the installed EP packs.
- The tests of `system`, `metrics` and `eps` use the fakes of `tests/hw_fakes.py`. They need no GPU.
- If a failure shows a code defect, report it.

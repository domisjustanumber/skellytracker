# Package Instructions

These rules apply to the code and the tests under `skellytracker/`.
The root [`AGENTS.md`](../AGENTS.md) also applies.
To change a package sidecar, also read [`specs/model-sidecar/AGENTS.md`](../specs/model-sidecar/AGENTS.md).

## Layout

The paths are under `skellytracker/`.

| Path | Role |
|---|---|
| `__main__.py` | Webcam demo CLI (`cli_main`), the commands `detectors` and `describe <key>` (`core/detectors/cli.py`), and the commands `run`, `validate` and `nodes` (`core/pipelines/cli.py`). With `--pipeline <key>`, the demo runs a pipeline in the running mode `live` ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 8). With no `--pipeline`, it runs the old demo of `--tracker`. Import each command module in its branch: `detectors` must load no pipeline module. |
| `core/tracker/` | `Tracker`, `MultiPersonTracker`, `DetectionStage`, `TrackerState` |
| `core/config/` | Pydantic configs: `TrackerConfig`, `DetectionStageConfig`, `ObjectDetectorConfig`, `KeypointDetectorConfig`, `SessionConfig` |
| `core/sessions/` | ONNX Runtime, CPU and MediaPipe sessions. `model_registry.py` downloads `url` ONNX files to `~/.cache/skellytracker/models`. `hf_repo` files go to the Hugging Face cache. `batch_conversion.py` makes a fixed-batch ONNX file from a static-batch source (`static-batch-v1`). |
| `core/detectors/catalog.py` | The catalog of the `detectors` entry point ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) items 1, 2 and 6): `list_detectors`, `get_detector`, `describe_detector`, `load_detector_sidecar`, the sidecar roots and `STATIC_DETECTORS`, the table of the entries with no sidecar. It imports no detector module. `core/detectors/__init__.py` exports the API. |
| `core/detectors/factory.py` | The one public factory `create_detector(key, **options)` ([ADR-KE1C](../decisions/entries/KE1C-one-public-detector-factory.md)). `core/detectors/__init__.py` exports it. An `onnx` key goes to `create_detector` of `core/detectors/generic/`. `charuco@skellytracker` and `aruco@skellytracker` give the calibration class, with `detect(image)` and `close()`. The charuco option `board` is a `CharucoBoardDefinition` or a mapping of its fields, and `detector.board` gives it back. A `mediapipe` key raises `DetectorUnavailableError`. The module docstring gives the options. Import each detector module in the function body: a plain `import skellytracker.core.detectors` must load no generic detector, no calibration detector, no ONNX Runtime and no MediaPipe. Keep the signature when stage 2.4 of the implementation plan changes the calibration classes. |
| `core/detectors/calibration.py` | The public calibration helpers that are not detectors: plain re-exports of the board definition, the board selector, the board pose, the anipose row, the charuco annotator, the board tags and `CHARUCO_BOARD_MAPPING`. The board model `CharucoBoardDefinition` is public data: keep it a Pydantic model that is not frozen. An application, for example freemocap, imports `create_detector` and this module. It imports no detector class, no config class of a detector, no session and no module of `calibration_detectors`. A helper that an application needs gets a re-export here. `core/detectors/__init__.py` does not import this module. |
| `core/detectors/detector_base_classes.py` | Detector base classes, `OBJECT_DETECTOR_REGISTRY` and `KEYPOINT_DETECTOR_REGISTRY` |
| `core/detectors/keypoint_detectors/` | `mediapipe/`, `rtmpose/` (body, hand, face), `rtmw/wholebody/` |
| `core/detectors/calibration_detectors/` | `aruco/`, `charuco/` ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 4). Import `calibration_detectors` to register them. `charuco/` also holds the board selector (`charuco_board_selection.py`), the board tags and the mapping file of a board with its path `CHARUCO_BOARD_MAPPING` (`charuco_board_mapping.py`). |
| `core/detectors/mediapipe_holistic.py` | `HolisticRunner`: the MediaPipe Tasks `HolisticLandmarker` for the variant `holistic` of the node `mediapipe_tasks`. It does not use the old detector contract ([ADR-X6S9](../decisions/entries/X6S9-mediapipe-close-from-the-garbage-collector.md)). |
| `core/detectors/object_detectors/` | `yolox/`, `keypoint_bbox/`, `precomputed/` |
| `core/detectors/processing/` | Generic preprocessing, affine crop, detection decode with NMS, SimCC decode (ADR-[0007](../decisions/entries/0007-generic-processing-package.md)) |
| `core/detectors/processing/pre/`, `core/detectors/processing/post/` | The spec processing modules, one module for each spec section ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 4). They take the spec model of `core/model_spec/`. `pre/preprocess.py` holds the resize dispatcher (`resize_image`, `ResizeGeometry`) and `preprocess_image`. `post/unprojection.py` holds the inverse dispatcher (`resize_inverse`). Do not import the old processing modules in them. |
| `core/detectors/generic/` | The generic detectors ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 6): `GenericObjectDetector`, `GenericKeypointDetector`, `create_detector(key, execution_provider=...)`, `open_session` (`session.py`), the download of a `url` artifact (`download.py`), the batch conversion `model_batch_convert` (`batch_conversion.py`, which needs the extra `onnx`), the batch loop (`inference.py`) and the overlay groups (`overlay.py`). They use the spec model, `processing/pre/`, `processing/post/` and `eps.build_session()`. Do not import the old detector contract, `core/tracker/` or `core/sessions/` in them. |
| `core/detectors/shared/skeletons/` | Tracked-point and skeleton fragments that sidecars include with `$ref` |
| `core/model_zoo/` | The package sidecar root, with the spec layout ([Storage layout](../specs/model-sidecar/format/file-layout.md#storage-layout); [ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 5). It holds data only. Git ignores its `.onnx` files, and no wheel or sdist holds them. |
| `core/model_zoo/detectors/` | The package sidecars `yolox-person` and `rtmw-wholebody133` of OpenMMLab-Exporter, each a byte copy of its [reference example](../specs/model-sidecar/examples/README.md). Their keys are `yolox-person@openmmlab-exporter` and `rtmw-wholebody133@openmmlab-exporter`. Put each ONNX file beside its sidecar by hand. A file with a different SHA-256 is unavailable. |
| `core/model_zoo/landmark_schemas/` | Landmark schema files of the registry ([Landmark schema](../specs/model-sidecar/post/keypoint/landmark-schema.md); [ADR-23F5](../decisions/entries/23F5-landmark-schema-registry.md)) |
| `core/pipelines/` | The pipeline API ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 1). `__init__.py` exports it. `config.py` holds `PipelineConfig` and the node configs. Its JSON Schema is the shipped `pipeline.schema.json`. `values.py` holds the values of the ports and the delivered type `OutputBoxes`. `loading.py` holds `load_pipeline`, `check_pipeline` and `export_pipeline`. `catalog.py` holds `list_pipelines` and `get_pipeline`. `nodes.py` holds `list_node_types`. `run.py` holds `start_pipeline`, `PipelineRun` and `Frame`. `canonical.py` holds `to_canonical` and the delivered type `CanonicalKeypoints`. `timing.py` holds the timing events, the header, the hashes and the skellybench aggregator ([ADR-Q59W](../decisions/entries/Q59W-pipeline-timing-and-taps.md)). `annotate.py` holds the generic annotator. `warnings.py` holds `PipelineWarning`. `cli.py` holds the commands `run`, `validate` and `nodes`, and the webcam demo of a pipeline. A plain `import skellytracker.core.pipelines` must load no `onnxruntime` and no `mediapipe`. |
| `core/pipelines/_runtime/` | The private runtime of the pipeline API: the load checks that need the sidecars (`resolve.py`), the executor (`executor.py`), the sessions (`sessions.py`), the taps (`taps.py`), and one module for each node type (`onnx_model.py`, `mediapipe_tasks.py`, `node_<type>.py`). Import nothing from it outside `core/pipelines/`. Do not import the old loader, the old processing modules, `core/tracker/`, `core/sessions/`, `core/annotation/` or the old detector contract in them. |
| `core/model_zoo/pipelines/` | The built-in pipeline files `yolox-rtmw-wholebody` and `mediapipe-holistic-tasks` ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 3). A shipped file must pin the `sidecar_sha256` of each `onnx_model` node ([ADR-7NY2](../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 10). |
| `core/errors.py` | The errors of `eps` and of the pipeline runtime, and the exit-code table of the CLIs ([ADR-D8DH](../decisions/entries/D8DH-sessions-errors-and-the-ready-rule.md) items 1 and 2). The old `core/sessions/session_errors.py` is a different module. |
| `core/system/` | `probe_host()`, `probe_runtime()`, `probe_environment()`, `probe_loaded_libraries()` and the device keys of the GPUs. Each value is fixed while the application runs. |
| `core/metrics/` | `LiveSampler` and `free_vram(device)`: system-level live values only |
| `core/_hardware/` | Private readers: NVML, DXGI with one D3DKMT query, the Windows registry, psutil (Windows only), `/proc` and `/sys`, macOS `sysctl` and IOKit, Windows PDH ([ADR-P1F3](../decisions/entries/P1F3-hardware-probe-devices-and-multi-gpu.md) items 1 and 2) |
| `core/eps/` | The EP catalog (`ep_catalog.yaml`, `ep_lock.yaml`), the certification evidence (`ep_evidence.yaml`), the EP store, `install()`, `ensure_registered()`, `verify()`, `recommend()`, `run_devices()`, `check_start()`, `status()`, `suggest_execution_provider()`, `build_session()`, `certify()`, `dismiss_certification()` and the CLI `skellytracker-eps` (`cli.py`). An application, for example freemocap, shows the EPs from `status()` and `recommend()`. It holds no EP fact of its own. A fact that an application needs gets a field of `PackStatus` or of `PipelineRun.models`. |
| `certification.py` | `certify()` and `certify_plan()`, the two functions of the contract of the repository `skellycertify` ([ADR-P0JZ](../decisions/entries/P0JZ-certify-contract-in-each-package.md)). `__init__.py` exports them as `skellytracker.certify` and `skellytracker.certify_plan`. The module imports only the standard library at module level: a plain `import skellytracker` loads no module of `core/`. `REASON_CODES.md` lists the reason codes of the report. A build can write `_build_info.py` with `COMMIT` and `TREE_MODIFIED`. Git ignores that file. |
| `_pyinstaller/` | The PyInstaller entry points and the data-only hook. It is outside `core/`. No package module imports it. |
| `core/sidecar/` | The old loader of the old package sidecars. Do not change it, and do not import it in new code. `load_sidecar` (`loader.py`), `$ref` and `base` resolution (`resolution.py`), `SidecarModel` (`model.py`), version checks (`versioning.py`) |
| `core/model_spec/` | The spec loader at spec version 2.0.0 ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 8): `load_sidecar(path, sidecar_root, user_root)` (`loader.py`), `$ref` resolution with hash checks (`resolution.py`), the `V-` rules (`rules.py`, `check_sidecar`), `SidecarModel` (`model.py`), the landmark schema registry (`landmark_schemas.py`), the implemented versions (`versioning.py`), the SPDX check (`spdx.py`), the artifact hash check with its cache (`artifacts.py`), the selector matching (`sidecar_normalize.py`) and the section table with the capability check (`sections.py`). Remove a `postprocessor` section from `UNIMPLEMENTED_SECTIONS` of `sections.py` in the commit that adds its processing module. Stage 2.3 of the implementation plan moves it to `core/sidecar/`. |
| `core/data_primitives/` | `BoundingBox`, `Keypoints`, observations, data stores |
| `core/annotation/` | Overlay drawing (`Annotator`, `KeypointAnnotator`) |
| `core/temporal_processing/` | Box policy and smoothing, keypoint filters, track association |
| `core/io/` | `process_video.py`, `demo_manager.py` (webcam runner), tracker mapping, canonical mapping expansion |
| `examples/` | Example scripts |
| `tests/` | pytest suite. `tests/sidecar/` holds the tests of the old loader and their golden fixtures. `tests/model_spec/` holds the tests of the spec loader. `tests/processing/` holds the tests of the spec processing modules. `tests/detectors/` holds the tests of the catalog, on temporary sidecar roots, and the tests of the generic detectors, on ONNX models that `onnx.helper` makes. `tests/pipelines/` holds the tests of the pipeline API, on the models of `pipeline_models.py`, and the tests of the built-in pipelines. `test_model_zoo.py` loads the package sidecars and runs one frame on each model. It skips a model whose ONNX file is not in `core/model_zoo/`. |

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

- A registry is not the public way to make a detector. A caller of the package uses
  `create_detector` of `skellytracker.core.detectors` (`core/detectors/factory.py`).
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

- ONNX Runtime 1.30.0 is a base dependency. The distribution is `onnxruntime` on Linux and macOS, and
  `onnxruntime-windowsml` on Windows. It gives the CPU EP, the CoreML EP on macOS and the DirectML
  EP on Windows ([ADR-N6E8](../decisions/entries/N6E8-onnxruntime-1-30-on-each-os.md) item 2;
  [ADR-Z5X7](../decisions/entries/Z5X7-field-test-state-and-directml.md)).
- `OnnxSessionConfig.execution_provider` (`core/sessions/onnx_session.py`) selects `coreml` or `cpu`.
- `None` selects the first available provider in this order: `coreml` (macOS only), `cpu`
  (`auto_detect_provider` in `core/sessions/ort_session_utils.py`).
- A provider that is not available raises `SessionCreationError`. There is no CPU fallback.

The four items above are the old session code in `core/sessions/`. Do not change it. Stage 2.4 of
the implementation plan deletes it. New code builds each session with `eps.build_session()`.
Exception: the legacy path of the freemocap metrics stage. `OnnxSessionConfig.execution_provider`
also takes `cuda`, and `OnnxSession.create` then builds each model with `eps.build_session()` on the
`cuda` pack, with no fallback. The old session code has no other GPU key, and stage 2.4 deletes this
bridge ([ADR-92BE](../decisions/entries/92BE-legacy-path-for-the-freemocap-metrics-stage.md)).
The same legacy path is the only caller of `describe_port(config, port)` of
`skellytracker.core.pipelines`. It gives the raw `point_names` and `groups` of one port, so that the
legacy path puts the old points in the raw names of `wholebody.keypoints` and calls
`to_canonical(value, groups)`. Do not use it in other code. Stage 2.4 deletes it with the legacy path
([ADR-C3A4](../decisions/entries/C3A4-describe-port-for-the-legacy-path.md)).

- New code takes the EP as `execution_provider`, a concrete key of the EP catalog: `trt-rtx`, `cuda`,
  `coreml`, `amdgpu`, `migraphx`, `directml` or `cpu`. No environment variable selects the EP or the
  device. The second environment of the certify suite sets `SKELLYTRACKER_EP_ORT_FALLBACK`: the EP
  store then accepts the ONNX Runtime of `certification.ort_fallback`
  ([ADR-XSE7](../decisions/entries/XSE7-amd-eps-in-the-field-test.md)).
- A session on a GPU takes the ONNX Runtime EP device of the GPU (`registration.ort_device()`).
  Never select a GPU with the option `device_id`.
- A `field-test` EP of the EP catalog (today `directml`, `amdgpu` and `migraphx`) is usable only
  after an opt-in in the EP store (`store.opt_in_field_test()`). Only `skellytracker-eps install KEY --field-test`, the
  certify suite and a passed quick check of `skellytracker.certify()` record it
  ([ADR-21BK](../decisions/entries/21BK-quick-check-local-pass-and-hand-in.md) item 2). `recommend()` never gives such an EP
  ([ADR-Z5X7](../decisions/entries/Z5X7-field-test-state-and-directml.md)).
- `eps.build_session()` serves only new code. Do not connect it to `OnnxSession` or `Tracker.create`.
  The `cuda` bridge of the exception above is the only connection.
- A GPU EP is a plugin EP pack in the EP store, `directml`, which is a part of the Windows ML
  build of ONNX Runtime, or an EP of the Windows ML catalog (`windows_ml` of the EP row). Only
  `core/eps/windows_ml.py` imports `windowsml`, in a function
  ([ADR-XSE7](../decisions/entries/XSE7-amd-eps-in-the-field-test.md)). Do not add a GPU package to
  `pyproject.toml`.
- `core/eps/ep_catalog.yaml` is written by hand. Only `uv run python tools/ep_catalog.py --refresh`
  writes `ep_lock.yaml`, and it uses the network. Run it after each change of the catalog.
  `ort_core` must equal the `onnxruntime` pin and the `onnxruntime-windowsml` pin: change the pins, the catalog, the lock and
  `uv.lock` in one commit.
- `eps` reads no sidecar. The caller fills `ModelRef`.
- A plain `import skellytracker.core.eps` must load no `onnxruntime`. Import `onnxruntime` in the
  function that uses it. The probes of `core.system` and the sampler of `core.metrics` make no CUDA
  call and load no EP library.
- A record of `system`, `metrics` and `eps` is a frozen dataclass with no `dict` field. Memory is
  `int` bytes, time is `int` ns, and a field that ends in `utilization` is a ratio from 0 to 1. No
  text holds an absolute path or a hostname.
- A person writes each row of `core/eps/ep_evidence.yaml` after a review. No code writes it, and
  the runtime never downloads it
  ([ADR-MF2R](../decisions/entries/MF2R-ep-store-install-and-certification.md) item 12).
- A certification report must hold no path, no hostname, no serial number, no bus address and no
  user id. A failure is a fixed reason code, never an error text. `certify()` sends nothing: the
  report stays in the folder `reports` of the EP store
  ([ADR-MF2R](../decisions/entries/MF2R-ep-store-install-and-certification.md) item 17).

## Freeze rules

A frozen application must find each module and each data file. `tests/test_import_rules.py` checks
these rules ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 3).

- Import each module with a plain statement. A lazy import is a plain statement in a function body.
  Do not use `importlib.import_module`, `__import__`, `exec` or `eval` with a computed name.
- Read the metadata of a fixed distribution with a literal call in the full form, for example
  `importlib.metadata.version("mediapipe")`. Do not alias `importlib.metadata`.
- `_pyinstaller/hook-skellytracker.py` collects `**/*.yaml`. A commit that adds a data file of an
  other type changes `includes` of the hook in the same commit.
- Do not add a hook for an other package to `_pyinstaller/`. The one exception is the hook
  of ONNX Runtime ([ADR-K8Q0](../decisions/entries/K8Q0-platform-rulings-of-2026-11-19.md) item 2).

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

Public names. These rules apply to each name of the public surface: the entry points `detectors`,
`pipelines` and `eps`, their records and their errors
([ADR-0YNA](../decisions/entries/0YNA-public-names-standard-and-four-renames.md)).

1. Use the case of PEP 8: `snake_case` for a function, a method and a field, `CapWords` for a
   class, and `UPPER_CASE` for a constant.
2. The name of each exception class must end in `Error`, for example `CallRefusedError` and
   `SetParamsRefusedError`.
3. An exception name is `<Subject><State>Error`. Its base is the built-in class that a caller
   catches: `KeyError` for a thing that is not found, `ValueError` for a refused input and
   `RuntimeError` for a state.
4. A module function is `verb_subject`. A bare verb is allowed only when the namespace names the
   object (`eps.install`) or the first argument is the object (`annotate(image, ...)`).
5. Use one verb for one act in each entry point:
   - `list_`: all entries.
   - `get_`: one entry by its key or its pin. It raises `<Subject>NotFoundError`
     (`get_detector`, `get_pipeline`).
   - `describe_`: the details of one entry.
   - `load_`: parse into a config or a model.
   - `check_`: run the rules and return the result.
   - `create_`: make an object.
   - `start_`: make an object that holds resources and has `close()`.
   - `export_` and `to_`: write or convert.
6. A catalog row is `<Subject>Entry`. It has `key`, `version`, `available`, `unavailable_reason`
   and `superseded`.
7. A function result in an entry point is `<Subject><Act-noun>` (`DetectorDescription`,
   `PipelineCheck`). In `eps`, where the act has no subject, it is `<Act>Result`.
8. A boolean is an adjective or a participle with no prefix (`available`, `downloaded`, `usable`).
   Use `is_<noun>` only when the bare word is a noun. Use `needs_<noun>` or `uses_<noun>` for a
   relation (`needs_execution_provider`, `uses_gpu`).
9. A collection has a plural name, and one item has a singular name. An array with one value for
   each element keeps the name of the spec.
10. One concept has one field name in each type, for example `point_names` in a `keypoints` value
    and in `CanonicalKeypoints`.
11. For an EP: a public parameter that takes the EP key is `execution_provider`. A compound name
    takes the prefix `ep_`. A CLI flag can be shorter (`--ep`).
12. To rename a name that a spec or a decision entry fixes, write an entry and change the spec text
    in the same commit. Add no alias for the old name.

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

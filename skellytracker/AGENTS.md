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
| `core/detectors/processing/pre/`, `core/detectors/processing/post/` | The spec processing modules, one module for each spec section ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 4). They take the spec model of `core/model_spec/`. `pre/preprocess.py` holds the resize dispatcher (`resize_image`, `ResizeGeometry`) and `preprocess_image`. `pre/graph.py` builds the preprocess graph (`build_preprocess_graph`): the resize step and the normalization as ONNX nodes. `affine_crop_theta` gives the `theta` input of an `affine_crop` graph from the ROIs. `post/unprojection.py` holds the inverse dispatcher (`resize_inverse`). Do not import the old processing modules in them. |
| `core/detectors/generic/` | The generic detectors ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 6): `GenericObjectDetector`, `GenericKeypointDetector`, `create_detector(key, execution_provider=...)`, `open_session` (`session.py`), the download of a `url` artifact (`download.py`), the batch conversion `model_batch_convert` (`batch_conversion.py`), the batch loop (`inference.py`) and the overlay groups (`overlay.py`). They use the spec model, `processing/pre/`, `processing/post/` and `eps.build_session()`. Do not import the old detector contract, `core/tracker/` or `core/sessions/` in them. |
| `core/detectors/shared/skeletons/` | Tracked-point and skeleton fragments that sidecars include with `$ref` |
| `core/model_zoo/` | The package sidecar root, with the spec layout ([Storage layout](../specs/model-sidecar/format/file-layout.md#storage-layout); [ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 5). It holds data only. Git ignores its `.onnx` files, and no wheel or sdist holds them. |
| `core/model_zoo/detectors/` | The package sidecars `yolox-person` and `rtmw-wholebody133` of OpenMMLab-Exporter, each a byte copy of its [reference example](../specs/model-sidecar/examples/README.md). Their keys are `yolox-person@openmmlab-exporter` and `rtmw-wholebody133@openmmlab-exporter`. Put each ONNX file beside its sidecar by hand. A file with a different SHA-256 is unavailable. |
| `core/model_zoo/landmark_schemas/` | Landmark schema files of the registry ([Landmark schema](../specs/model-sidecar/post/keypoint/landmark-schema.md); [ADR-23F5](../decisions/entries/23F5-landmark-schema-registry.md)) |
| `core/pipelines/` | The pipeline API ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 1). `__init__.py` exports it. `config.py` holds `PipelineConfig` and the node configs. Its JSON Schema is the shipped `pipeline.schema.json`. `values.py` holds the values of the ports and the delivered type `OutputBoxes`. `loading.py` holds `load_pipeline`, `check_pipeline` and `export_pipeline`. `catalog.py` holds `list_pipelines` and `get_pipeline`. `nodes.py` holds `list_node_types`. `run.py` holds `start_pipeline`, `PipelineRun` and `Frame`. `canonical.py` holds `to_canonical` and the delivered type `CanonicalKeypoints`. `timing.py` holds the timing events, the header, the hashes and the skellybench aggregator ([ADR-Q59W](../decisions/entries/Q59W-pipeline-timing-and-taps.md)). The aggregator puts the events of the reserved source `frame` in no stage. `annotate.py` holds the generic annotator. `warnings.py` holds `PipelineWarning`. `cli.py` holds the commands `run`, `validate` and `nodes`, and the webcam demo of a pipeline. A plain `import skellytracker.core.pipelines` must load no `onnxruntime` and no `mediapipe`. |
| `core/pipelines/_runtime/` | The private runtime of the pipeline API: the load checks that need the sidecars (`resolve.py`), the executor (`executor.py`), the sessions (`sessions.py`, with the preprocess sessions of `RunSessions.open_preprocess`), the taps (`taps.py`), and one module for each node type (`onnx_model.py`, `mediapipe_tasks.py`, `node_<type>.py`). `OnnxModelRunner` runs the GPU preprocess and gives the warning `preprocessed_on_cpu`. The run parameter `preprocess` selects the EPs: with `auto`, the EPs of `GRAPH_DEFAULT_EPS` of `onnx_model.py`; with `gpu`, the EPs of `GRAPH_EPS`; with `cpu`, no EP. `GRAPH_EPS` holds `cuda`, `trt-rtx` and `directml`. `GRAPH_DEFAULT_EPS` holds `cuda` and `trt-rtx`: a reviewed certification report from AMD hardware adds `directml`. On `directml`, the frame stage gives each frame to the graph in host memory, because a DML session does not always read a frame that `upload_frame` put in `dml` memory, and the graph output binds to `dml` with the device id 0 on each GPU. `Executor._frame_images` decodes and turns the frames of a call. On a device with a node that runs the GPU preprocess on `cuda` or `trt-rtx` (`JPEG_DECODER_EPS` of `executor.py`), it decodes the JPEG buffers of the call in one batch with the GPU decoder of that device, which opens at the first JPEG call. It decodes on the CPU each buffer that the GPU decoder refuses, and each buffer of a device whose decoder does not open, and gives the warning `jpeg_decoded_on_cpu`. An open that raises is such a decoder. With `auto`, `stored_jpeg_checks` of `executor.py` reads at the start the stored JPEG quick check of the EP and the GPU of each device, from `quick-checks.json` of the EP store with no lock. A stored `fail` of `jpeg-preprocess` gives each node the CPU preprocess on that device (`GraphPath.off`), and a `fail` of either check moves the JPEG decode of that device to the CPU (`Executor.decode_failed`), with the reason `quick_check_failed`. A test patches `stored_jpeg_checks`. It decodes each buffer of another device on the CPU with no warning. It decodes 2 or more CPU buffers of a call in the thread pool `Executor.decode_pool`, with at most `cpu_threads` threads, when `cpu_threads` is more than 1, and reads the results in camera order. `close()` stops the pool first. It does not catch an error of a decode. `Executor._frame_stage` uploads the frames of a call before the first node: each camera has a fixed slot, and a camera that is not in the call gets a zero frame. A frame of the GPU decoder does not upload. Both give the timing events of the reserved source `frame`. A test adds `cpu` to `GRAPH_DEFAULT_EPS` to run that path on the CPU EP. A test also adds `cpu` to `JPEG_DECODER_EPS` and patches `open_jpeg_decoder` to give a fake decoder. Import nothing from it outside `core/pipelines/`. Do not import the old loader, the old processing modules, `core/tracker/`, `core/sessions/`, `core/annotation/` or the old detector contract in them. |
| `core/decode/` | The JPEG decoders of a pipeline run ([JPEG frames](../specs/pipeline/running.md#behaviour)). `cpu.py` holds `decode_jpeg`: it decodes a JPEG buffer on the CPU, ignores the EXIF orientation, and turns the frame by `rotation_deg`. `starts_as_jpeg` is the SOI check of both decoders. `nvidia.py` holds `NvJpegDecoder`: the nvJPEG decode of a batch on `cuda` and `trt-rtx`, with the wait for its private CUDA stream and the turn in GPU memory. `NvJpegDecoder.open()` gives None when `prepare_jpeg_decoder()` gives None, when the CUDA runtime does not load, or when the decode of a test JPEG at the open fails or does not return in `SELF_TEST_TIMEOUT_S`. It never closes a decoder whose test decode does not return. A buffer that nvJPEG refuses gives None, and the caller decodes it on the CPU. A JPEG with no DHT segment is such a buffer. One run uses one decoder for each device, from one thread, and closes it after the sessions. `frame.py` holds `DecodedFrame`, the value of the port `frame.image`: a frame in host memory or in GPU memory. `host` gives the host pixels. `on_device()` uploads a host frame one time for each device. `certification.py` holds `run_jpeg_certification(ep_key, device_key=..., progress=...)`: the one entry point that a certify suite calls in a child process. It runs the checks of the JPEG decode, the preprocess graph and the built-in pipeline on synthetic images, and returns JSON-able data. `device_key` selects the GPU of each session and run on the EP, as in `build_session()`, and `facts["device"]` names the GPU of the run. `run_jpeg_quick_checks(ep_key, device_key=..., progress=...)` runs two of these checks with new names for the quick level of `certify()`: `jpeg-decode` and `jpeg-preprocess`. They need no ONNX model file. A check name is stable: a later release adds names, and does not rename or remove a name. `tests/test_decode_certification.py` holds the frozen list of the names. A check whose EP is not present gives `not-run`. The checks `preprocess_graph_amd_ep.*` and `pipeline_amd_ep.*` run on the EPs of an AMD GPU (`AMD_EPS`: `directml`, `amdgpu`, `migraphx`). Only on `directml` (`SCORED_AMD_EPS`) can they give `fail`: on the other two, each result is `record-only`, also an exception. Only the NVIDIA EPs `cuda` and `trt-rtx` have a GPU JPEG decode: on each other EP, a `gpu_decode` check gives `not-run` with the reason `no_gpu_decode_on_ep`. The result holds no absolute path, no host name and no user name. |
| `core/model_zoo/pipelines/` | The built-in pipeline files `yolox-rtmw-wholebody` and `mediapipe-holistic-tasks` ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 3). A shipped file must pin the `sidecar_sha256` of each `onnx_model` node ([ADR-7NY2](../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 10). |
| `core/errors.py` | The errors of `eps` and of the pipeline runtime, and the exit-code table of the CLIs ([ADR-D8DH](../decisions/entries/D8DH-sessions-errors-and-the-ready-rule.md) items 1 and 2). The old `core/sessions/session_errors.py` is a different module. |
| `core/system/` | `probe_host()`, `probe_runtime()`, `probe_environment()`, `probe_loaded_libraries()` and the device keys of the GPUs. Each value is fixed while the application runs. |
| `core/metrics/` | `LiveSampler` and `free_vram(device)`: system-level live values only |
| `core/_hardware/` | Private readers: NVML, DXGI with one D3DKMT query, the Windows registry, psutil (Windows only), `/proc` and `/sys`, macOS `sysctl` and IOKit, Windows PDH ([ADR-P1F3](../decisions/entries/P1F3-hardware-probe-devices-and-multi-gpu.md) items 1 and 2) |
| `core/eps/` | The EP catalog (`ep_catalog.yaml`, `ep_lock.yaml`), the certification evidence (`ep_evidence.yaml`), the EP store, `install()`, `ensure_registered()`, `verify()`, `recommend()`, `run_devices()`, `check_start()`, `status()`, `suggest_execution_provider()`, `build_session()`, `certify()`, `dismiss_certification()`, `run_session()`, `run_preprocess()` and `run_bound()` (a preprocess graph, then its model on the graph output, with IO bindings), `upload_frame()` (`session.py`), `prepare_jpeg_decoder()` (`registration.py`) and the CLI `skellytracker-eps` (`cli.py`). An application, for example freemocap, shows the EPs from `status()` and `recommend()`. It holds no EP fact of its own. A fact that an application needs gets a field of `PackStatus` or of `PipelineRun.models`. |
| `certification.py` | `certify()` and `certify_plan()`, the two functions of the contract of the repository `skellycertify` ([ADR-P0JZ](../decisions/entries/P0JZ-certify-contract-in-each-package.md)). `__init__.py` exports them as `skellytracker.certify` and `skellytracker.certify_plan`. The level `full` has the layout of the level `quick`. It adds the pipeline timings and the JPEG certification, and it installs nothing ([ADR-75J6](../decisions/entries/75J6-full-level-in-certify-and-uuid-report-id.md)). The id of a report is a version 4 UUID: the key `id`, the file name and the id of the hand-in list. `summary` holds one item for each EP that ran, with the short names of `SUMMARY_NAMES`: do not change a name ([ADR-2S52](../decisions/entries/2S52-summary-items-in-the-certify-report.md)). It also holds the hand-in list of [ADR-21BK](../decisions/entries/21BK-quick-check-local-pass-and-hand-in.md) item 5: `pending_reports()`, `read_report()` and `mark_reports()`, with the states `pending`, `opened` and `covered` in `hand-in.json` of the EP store. A new report of a quick check deletes each older report of a pass that it repeats, when the user did not hand that report in. The package sends no report. The module imports only the standard library at module level: a plain `import skellytracker` loads no module of `core/`. `REASON_CODES.md` lists the reason codes of the report. A build can write `_build_info.py` with `COMMIT` and `TREE_MODIFIED`. Git ignores that file. |
| `_pyinstaller/` | The PyInstaller entry points, the data-only hook `hook-skellytracker.py` and the hook of ONNX Runtime `hook-onnxruntime.py` ([ADR-K8Q0](../decisions/entries/K8Q0-platform-rulings-of-2026-11-19.md) item 2). The hook of ONNX Runtime collects the libraries, the data files and the metadata of the installed `onnxruntime` distribution, and of `windowsml` on Windows. It collects no GPU EP. It is outside `core/`. No package module imports it. |
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
The legacy path compares the old run code with the 2.0 pipelines, realtime only. The bridge uses the
default options of the EP catalog and the default GPU. It keeps the `InferenceSession`, and then
runs the old warm-up at the batch size of the config. `cuda` applies only when the caller names it:
`auto_detect_provider()` and the keys `None`, `cpu` and `coreml` do not change. The old tracker also
gives optional task events for this path: `core/tracker/task_events.py` and the argument
`event_collector` of `Tracker.process_batch`. Stage 2.4 deletes them too.
The same legacy path is the only caller of `describe_port(config, port)` of
`skellytracker.core.pipelines`. It gives the raw `point_names` and `groups` of one port, so that the
legacy path puts the old points in the raw names of `wholebody.keypoints` and calls
`to_canonical(value, groups)`. Do not use it in other code. Stage 2.4 deletes it with the legacy path
([ADR-C3A4](../decisions/entries/C3A4-describe-port-for-the-legacy-path.md)).

- New code takes the EP as `execution_provider`, a concrete key of the EP catalog: `trt-rtx`, `cuda`,
  `coreml`, `amdgpu`, `migraphx`, `directml` or `cpu`. No environment variable selects the EP or the
  device.
- A session on a GPU takes the ONNX Runtime EP device of the GPU (`registration.ort_device()`).
  Never select a GPU with the option `device_id`.
- A `field-test` EP of the EP catalog (today `directml`, `amdgpu` and `migraphx`) is usable only
  after an opt-in in the EP store (`store.opt_in_field_test()`). Only `skellytracker-eps install KEY --field-test`, the
  certify suite and a passed quick check of `skellytracker.certify()` record it
  ([ADR-21BK](../decisions/entries/21BK-quick-check-local-pass-and-hand-in.md) item 2). `recommend()` never gives such an EP
  ([ADR-Z5X7](../decisions/entries/Z5X7-field-test-state-and-directml.md)).
- The check rule (`core/eps/gate.py`, [ADR-ER5X](../decisions/entries/ER5X-check-rule-unclean-exits-and-coreml.md)): an EP runs
  on a GPU only with a reviewed row of `ep_evidence.yaml` or a passed quick check on this PC, and never after a quick
  check that failed there. `check_start()` and `build_session()` raise `EpUnavailableError` with the quick-check
  command. Do not add a setting, an argument or an environment variable that switches the rule off. Only the
  certification code runs inside `gate.certification_run()`. A test of an other subject on a fake GPU calls
  `hw_fakes.reviewed_rows_for_each_gpu(monkeypatch)`. The rule also applies to `coreml`, with the chip of the Mac as
  the key of its results (`gate.chip_of()`). For now, a passed quick check is the validation of a Mac: no macOS run
  of CI is required, and the certify suite on macOS comes with the level `full`.
- `core/eps/exits.py` counts the unclean exits of a process that held a session on a GPU EP. `build_session()` writes
  the marker. Two unclean exits in a row mark the EP as failed on this PC, and a passed quick check removes the mark.
  An application calls `skellytracker.note_exit_requested()` before it ends its process
  ([ADR-ER5X](../decisions/entries/ER5X-check-rule-unclean-exits-and-coreml.md) item 5).
- `eps.build_session()` serves only new code. Do not connect it to `OnnxSession` or `Tracker.create`.
  The `cuda` bridge of the exception above is the only connection.
- A GPU EP is a plugin EP pack in the EP store, `directml`, which is a part of the Windows ML
  build of ONNX Runtime, or an EP of the Windows ML catalog (`windows_ml` of the EP row). Only
  `core/eps/windows_ml.py` imports `windowsml`, in a function
  ([ADR-XSE7](../decisions/entries/XSE7-amd-eps-in-the-field-test.md)). Do not add a GPU package to
  `pyproject.toml`.
- A GPU package that two packs share is a component of the catalog (`components`), in its own store
  folder ([ADR-88ZB](../decisions/entries/88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md)).
  An install of a pack also installs its component. A failed install of a component is a warning
  of the install (`InstallResult.warnings`), not a failure. `install <key>` on a store of an older
  catalog installs only the component, `download()` includes its wheels, and `gc()` keeps each
  component of the catalog. A missing component never blocks the
  EP: it shows in `PackStatus.jpeg_decoder` (`installed`, `missing` or `other_version`), not in `PackState`. The GPU JPEG decoder `gpu-jpeg-cu13` of
  `cuda` and `trt-rtx` loads only in `prepare_jpeg_decoder()`, which gives the module and the CUDA
  runtime of the component for `cudaStreamSynchronize`. A plain `import skellytracker` loads no
  `nvidia` module.
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
- Telemetry of ONNX Runtime ([ADR-BZ7X](../decisions/entries/BZ7X-onnx-runtime-telemetry-switch-and-scan.md)):
  - `skellytracker/__init__.py` runs `os.environ.setdefault("ORT_DISABLE_TELEMETRY", "1")` as its
    first statement, before each `import onnxruntime` of the package. A value that the host process
    set stays. A host that imports `onnxruntime` before skellytracker must set the variable itself.
    `tools/intake_bundle.py` sets it before each of its `import onnxruntime` lines.
  - `RuntimeInfo.ort_disable_telemetry` holds the value or `None`. Section 1 of the certify suite
    records it in `onnx_stack`, with the check `suite:checkout:telemetry-switch`: `pass` for `1` or
    `true` (trimmed, any case), else `record-only` with `telemetry-on`.
  - The certify suite records whether the telemetry folder of ONNX Runtime exists before and after
    the run, as the two booleans of `details.suite.telemetry_database`, with no path. It deletes nothing there. The
    folder is `Microsoft\DeveloperTools\.onnxruntime` under the local app data folder on Windows. On
    Linux and macOS, it is `Microsoft/DeveloperTools/.onnxruntime` under `XDG_CACHE_HOME`, else
    under `~/.cache`.
  - `tools/onnx_stack.py` scans each native library of a wheel for the telemetry client
    (`OneCollector` or `mobile.events.data.microsoft.com`) and for the string
    `ORT_DISABLE_TELEMETRY`, as ASCII and UTF-16LE, in any case. An HTTP import is a hint only.
    `scan` and `check --wheel-dir` use the scan. A wheel that is not in the folder is `not-scanned`.
  - The `telemetry` list of `ep_evidence.yaml` holds one reviewed row for each package, version and
    OS, with `client` and `switch_verified` (an evidence reference, or `false` with a `reason`).
    `check` fails for a scanned client with no row and for a row that the scan contradicts. It warns
    for a client with `switch_verified: false`. `solve` and `apply` refuse a new package version
    with no row, or with a client and `switch_verified: false`. Each new package version of the
    stack thus needs a reviewed row before a bump.
  - The pinned set stays with a warning: the rows of ONNX Runtime 1.30.0 and of
    `onnxruntime-ep-cuda13` 0.2.0 on Linux have the client and `switch_verified: false`.
  - GPU JPEG decode is for NVIDIA only (`cuda` and `trt-rtx`). Each other EP gets frames that the
    CPU decoded.
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
  the installed EP packs. A `directml` test runs on Windows with the opt-in in a private EP store in
  `tmp_path`, and skips with no DirectML GPU.
- The tests of `system`, `metrics` and `eps` use the fakes of `tests/hw_fakes.py`. They need no GPU.
- If a failure shows a code defect, report it.

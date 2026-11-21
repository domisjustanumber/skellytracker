# Open work

This file holds the open work of the [decision log](README.md): the repository state. The
implementation-stage work is in the
[implementation plan](../specs/sidecar-implementation-plan.md). The spec defects are in the open work of the
[spec log](../specs/model-sidecar/decisions/open-work.md#spec-defects). Read the items that apply to
your task.

## Implementation stage

The implementation-stage work is in the stages of phase 1 and phase 2 of the
[implementation plan](../specs/sidecar-implementation-plan.md) ([ADR-5WKW](entries/5WKW-implementation-work-in-the-plan.md);
[ADR-NHM3](entries/NHM3-phases-to-the-exporter-checkpoint.md)).

## Repository state

- **Linux gate of ONNX Runtime 1.30.0.** [ADR-N6E8](entries/N6E8-onnxruntime-1-30-on-each-os.md) item 9: run
  the certify suite `tools/certify_platform.py` on bare-metal Ubuntu 24.04 with an NVIDIA driver of
  590.48.01 or later. It replaces `decisions/scripts/n6e8_ort_1_30/linux_ep_gate.sh`
  ([ADR-Y14H](entries/Y14H-certify-suite.md) item 16). The change of the items 2 and 3 of N6E8 lands
  only after this run passes. Then write the result in the Evidence section of N6E8.
- **Certify suite.** [ADR-SP4Z](entries/SP4Z-certify-suite-calls-the-full-level.md): the suite has four
  sections, in `tools/certify_platform.py` and `tools/certify_eps.py`, and calls `certify("full")`. These items stay open:
  - The `cleanup` step of `decisions/scripts/xse7_windows_ml_rehearsal.py` fails with
    `record-refused` without the catalog hook. It needs the wrapper
    `decisions/scripts/zgf5_session_measurements/hooked_cleanup.py`
    ([ADR-ZGF5](entries/ZGF5-certify-measurements-of-2026-11-18.md) item 5).
  - Sections 3 and 4 ran on one Windows host with an NVIDIA GPU and an Intel iGPU only. No run on
    Linux, on macOS (`coreml`), on a host with an AMD GPU or on a laptop with two GPUs.
  - The AMD EPs (item 11) are built ([ADR-XSE7](entries/XSE7-amd-eps-in-the-field-test.md)), and
    only tests with fakes prove them. The field-test state and DirectML are built
    ([ADR-Z5X7](entries/Z5X7-field-test-state-and-directml.md)). No EP has a result on an AMD GPU yet.
    A reviewed passing report for the OS moves an EP to `ready`, and changes the note of its hardware
    class (`amd-windows` or `amd-linux`). These checks stay open:
    - The removal of a Windows ML package that the suite installs is built (item 5 of
      [ADR-XSE7](entries/XSE7-amd-eps-in-the-field-test.md)) and
      rehearsed with the TensorRT RTX package of the catalog. Still open: the removal of an AMD
      package; the removal after a crash during `ensure_ready()` (a new enumeration must give the
      package family; a deployment that Windows ends after the cleanup stays); whether Windows
      downloads a package again after a removal or uses a local copy. The command that removes a
      package that `install KEY --field-test` installed is item 4 of the
      [certification build list](#certification-build-list).
    - Linux with an AMD GPU and ROCm 10.0, 10.1 or 10.2: the pack choice, the install, the
      registration with the RUNPATH of 10.1 and 10.2, the preload of 10.0 (the second ONNX Runtime
      core), the probe on ONNX Runtime 1.30.0, and the second environment on 1.29.0 (`uv export`,
      the install in hash-checking mode, the editable install with the build constraint, the child
      run, the sizes). A host with no ROCm: `rocm-missing` and the
      CPU only.
    - Windows with an AMD GPU: the EPs that the catalog offers for the GPU (`AMDGPUExecutionProvider`
      needs Windows ML 2.5.96 and an AMD driver 24.12.1 or later), `ensure_ready()` of a package
      that is on the PC and of a package that is not, `library_path`, the registration, the EP
      device of the GPU, and the removal at the end.
  - Section 4 does not measure the VRAM of an integrated GPU: the PDH counter of `LiveSampler` reads
    dedicated memory only.
  - The model list `models` (path, URL, sha256, bytes) is in the `certification` block of
    `ep_catalog.yaml` (item 12). The files are in the public model repository of the certify suite,
    on a personal Hugging Face account, not of the freemocap organisation. The term check of
    `tools/check_private_data.py` allows that one address (user, 2026-11-18). On 2026-11-18,
    `fetch_models` of section 4 downloaded the four files of the list into an empty folder: 4 files,
    sizes and sha256 right.
  - A leak that the suite cannot stop: the cache of `uv`. It belongs to the tool of the volunteer.
  - The instructions page `CERTIFY.md` is a draft. Its clone address names the fork of the user. A
    report goes to an issue of the repository `skellycertify`.
  - Section 1 still checks a certification tag. Evidence needs no tag now: the report records the
    version and the commit of each package ([ADR-P0JZ](entries/P0JZ-certify-contract-in-each-package.md)
    item 4; item 2 of the [certification build list](#certification-build-list)).
- **EP certification.** Three items of [ADR-MF2R](entries/MF2R-ep-store-install-and-certification.md)
  stay open:
  - Check the `thresholds` of the `certification` block of `ep_catalog.yaml` on more hosts and images.
    One RTX 3070 with `cuda` and `trt-rtx` on one image gave the values of 2026-11-18 (item 16).
    [ADR-ZGF5](entries/ZGF5-certify-measurements-of-2026-11-18.md) gives the spread of 10 runs.
  - Write the `maintainer` rows of `ep_evidence.yaml` for the current set hash on Linux. The two
    Windows rows are written. Until then, `tools/onnx_stack.py check` fails for each NVIDIA pack on
    Linux (item 18).
  - Later stage: a relay that opens the issue with no login. Reports go to the public repository
    `skellycertify` ([ADR-P0JZ](entries/P0JZ-certify-contract-in-each-package.md) item 1). Until
    the relay exists, the user hands in the file
    ([ADR-21BK](entries/21BK-quick-check-local-pass-and-hand-in.md) item 5).
- **ONNX Runtime telemetry.** [ADR-BZ7X](entries/BZ7X-onnx-runtime-telemetry-switch-and-scan.md):
  the switch and the static scan are built. These items stay open:
  - Runtime levels, with the validated probe that another session delivers: (b) run a session with
    and without the variable, and check that no network module is loaded and that no telemetry
    database and no device id appear; (c) N processes exit under a watchdog, with and without the
    variable. On Windows, the upload signal is `webio.dll` with a connection to port 443, or the
    database, or the registry key `SOFTWARE\Microsoft\DeveloperTools\.onnxruntime`. The parent key
    `DeveloperTools` has its own `deviceid` from another Microsoft tool: it is not of ONNX Runtime.
  - Windows: the switch is measured only for `onnxruntime-ep-cuda13` 0.3.0, and not when it is set
    after the pack registers. The exit hang with the variable set is not measured.
  - Linux: the Ubuntu run of the certify suite must record the telemetry folder and the exit time,
    with and without the variable. Then write `switch_verified` in the two Linux rows of
    `ep_evidence.yaml`. The Linux folder path is read from strings, not measured.
  - macOS: the `onnxruntime` 1.30.0 wheel is not scanned and has no row.
- **Field-test opt-in.** [ADR-Z5X7](entries/Z5X7-field-test-state-and-directml.md): there is no
  command that removes an opt-in. A user deletes `field-test.json` of the EP store.
  - freemocap work: the dialog of the download prompt (item 9).
- **DirectML GPU preprocess.** A reviewed report from an AMD GPU on Windows moves `directml` into
  `GRAPH_DEFAULT_EPS` ([ADR-W4NW](entries/W4NW-gpu-preprocess-of-a-model-node-and-its-cpu-warning.md)
  items 1 and 6). The report must show no `fail` in `preprocess_graph_amd_ep.*` and
  `pipeline_amd_ep.*` of `run_jpeg_certification("directml")`, the numbers of `frame_upload` and
  `gpu_vs_cpu_preprocess`, and the time of the span `person.preprocess` with `gpu` and with `cpu`.
  No record holds the time of that span on the RTX 3070: measure it again.
- **Dependency pins for the exporters.** `pyproject.toml` has the pins of
  [ADR-N6E8](entries/N6E8-onnxruntime-1-30-on-each-os.md). The exporters that agents build again pin
  the 2.0.0 pre-release (the draft exporter guide). On 2026-10-28, two exporters required Python 3.14
  or later, and uv could not resolve skellytracker in three of the four exporters. Until the 2.0.0
  pre-release, an exporter runs the batch tool in the checkout environment.
- **Exporter open items.** At the 2.0.0 pre-release, remove the rows of
  `specs/draft/exporter-guide/sidecars/known-open-items.md` that name a reference implementation.
  They do not apply to a new exporter, and the skill `implement-sidecar-section` uses them until
  then ([x64y](entries/x64y-draft-exporter-guide-folder.md), item 6;
  [ADR-6J8E](entries/6J8E-exporters-run-released-skellytracker.md) item 1).
- The exporters are re-implemented against the current exporter guide. This file does not track the
  old exporter copies or paths.
- **Draft exporter guide.** `specs/draft/exporter-guide/` is not complete. A local plan of the user
  owns its creation. When the guide is complete, or when an end-to-end test proves that its first
  version works, a new entry moves it to `specs/exporter-guide/`
  ([x64y](entries/x64y-draft-exporter-guide-folder.md)). Each new part of the guide goes in a new
  folder beside `sidecars/`.
- **Drift and vector-hash noise.** Two tool changes of `tools/intake_bundle.py` are later work
  ([ADR-FM0B](entries/FM0B-one-response-for-each-commit-group.md)). A section fingerprint for the
  drift finding: the section body without its front matter and without the text under
  "Implementer guidance" and "Authoring guidance". Do not reuse the changelog fingerprint: it does
  not hash the Behaviour text. A `vectors_sha256` of the parsed cases without `verified_against` and
  `unverified`, which `fill` prints and writes
  ([ADR-8DSW](entries/8DSW-vector-files-are-the-case-source.md)). An excused drift finding still
  blocks the session run of `batch` ([ADR-AD33](entries/AD33-bundles-are-untrusted-input.md)
  item 4).
- **Vector runs of a bundle that follows a proposal.** A `model` bundle that follows an accepted
  proposal cannot record a vector run on the vectors of that proposal. `verify` accepts only a
  vector file that is landed (`_payload_problems` in `tools/intake_bundle.py`). Thus the bundle
  records the run as `no vectors`. An example is version 6 of `model-rtmw-wholebody133` for
  `post.keypoint.score_map`
  ([ADR-F067](../specs/model-sidecar/decisions/entries/F067-simcc-score-map.md)).
- **Pipeline redesign** ([ADR-9HTX](entries/9HTX-pipeline-node-and-port-redesign.md)). Stages 1 to 7
  are built. [ADR-8TQT](entries/8TQT-redesign-stages-6-and-7-before-the-pre-release.md) has the
  timing of stages 6 to 8. Three items stay open:
  - Stage 8, the pipeline editor, is freemocap work that the user does in another session.
  - Later work: look into one canonical output keypoint set that becomes the only output format of
    a pipeline.
  - Later work: make one BGR to RGB conversion for each camera and frame for the decomposed
    MediaPipe pipeline.
- **Cost of the detector preprocess.** Measured on 2026-11-17 (`time.perf_counter_ns`, one desktop
  CPU, OpenCV 5.0.0.93, no other load): `preprocess_image` of
  `core/detectors/processing/pre/preprocess.py` needs about 5.2 ms for one 1280x720 frame with the
  `yolox-person` sidecar at size `m` (640x640), almost the same at 1920x1080 and 3840x2160. It needs
  about 1.2 ms with `rtmw-wholebody133` at size `m` (256x192). The known causes:
  - `letterbox` of `pre/resize_letterbox.py` needs about 1.8 ms, and its `cv2.resize` call 0.2 to
    0.4 ms. The canvas fill from a `float64` array uses most of the difference.
  - `normalize` of `pre/normalize.py` makes a cast and two or three float passes over each pixel of
    the model input.
  - A detector prepares the images of a frame one after the other in one `preprocess` span, so the
    span grows with the number of cameras. freemocap showed more than 22 ms for `person.preprocess`
    with four cameras at 1280x720.

  The built-in pipeline runs the detector one time in 150 frames. The mean cost is small, but the
  frame with a detection has this delay. No fix is decided. A change of this code
  must keep each output tensor equal.

  Since 2026-11-18, the run has the GPU preprocess graph
  ([ADR-W4NW](entries/W4NW-gpu-preprocess-of-a-model-node-and-its-cpu-warning.md)) and the GPU JPEG
  decode ([ADR-P245](../specs/pipeline/decisions/entries/P245-jpeg-frame-input.md);
  [ADR-88ZB](entries/88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md)), measured in
  [ADR-1SZ9](entries/1SZ9-gpu-preprocess-and-gpu-jpeg-decode-in-the-pipeline-run.md),
  [ADR-FBV5](entries/FBV5-gpu-path-agreement-on-the-freemocap-sample-data.md) and
  [ADR-BP5Y](entries/BP5Y-gpu-huffman-decode-threshold.md), and on the pinned versions in
  [ADR-58F5](entries/58F5-native-jpeg-numbers-on-the-pinned-versions.md). Open:
  - No run measured the keypoint preprocess with two or more boxes in a frame.
  - A model session with a dynamic batch pads the batch on the GPU path.
  - No run measured the gain of the CPU decode thread pool
    ([ADR-S1TG](../specs/pipeline/decisions/entries/S1TG-cpu-jpeg-decode-threads.md)) on a full call.
- **Repeat on the pinned versions.**
  [ADR-58F5](entries/58F5-native-jpeg-numbers-on-the-pinned-versions.md) repeats the numbers of
  ADR-1SZ9, ADR-FBV5, ADR-BP5Y and ADR-S1TG and the test counts on ONNX Runtime 1.30.0 and
  `cuda-cu13` 0.2.0. Open: repeat the Evidence of
  [ADR-88ZB](entries/88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md) and of
  [ADR-J1HK](../specs/model-sidecar/decisions/entries/J1HK-resize-pixel-tolerance.md), and the
  resize-limit runs in the [spec open work](../specs/model-sidecar/decisions/open-work.md), on these
  versions, with 3 repeats or more and the spread.
- **Intel QSV JPEG decode.** Not built:
  [ADR-71YY](entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md) shows no gain. No
  run tested the two cases that can open it again: an NV12 preprocess that converts after the resize
  to the model input size, and 4:2:2 output from the Intel VPL library.
- **nvImageCodec hang of a one-image decode**
  ([ADR-975Z](entries/975Z-nvimagecodec-one-image-decode-hang.md)). Open: the report to NVIDIA (a
  minimal reproducer is ready), a run on Linux and a run on a host with few CPU cores.
- **Exit hang of the CUDA EP plugin** ([ADR-C6A5](entries/C6A5-exit-hang-of-the-cuda-ep-plugin.md)).
  Open: more full runs on ONNX Runtime 1.30.0 with `cuda-cu13` 0.2.0 (0 of 43 is not enough); a
  full run on `trt-rtx`; a longer run of the minimal reproducer; a full-length run with
  `ORT_DISABLE_TELEMETRY=1` ([ADR-C9ME](entries/C9ME-exit-hang-rate-with-the-telemetry-switch.md):
  the minimal reproducer is too weak for this question); the report to ONNX Runtime.
- **Repair of a damaged store folder.** A damaged pack or component folder of the EP store gives a
  state whose hint is the install command, but the install does not repair a folder that exists.
  The remedy today: remove the pack or the component, then install it again
  ([ADR-88ZB](entries/88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md)).
- **Kit PR in freemocap/project.** The kit is on the branch `dom/agents-and-adr-kit` of
  freemocap/project, in a PR for its owner
  ([ADR-P3NK](entries/P3NK-bootstrap-kit-in-freemocap-project.md)). The link repairs in 0031, NB91,
  QPS7 and Z05A pin the commit `0d88941` of that branch. When the PR merges with a different SHA,
  pin the merged commit.

## Certification build list

[ADR-P0JZ](entries/P0JZ-certify-contract-in-each-package.md),
[ADR-21BK](entries/21BK-quick-check-local-pass-and-hand-in.md) and
[ADR-K8Q0](entries/K8Q0-platform-rulings-of-2026-11-19.md) are decided. The quick level of
`skellytracker.certify()` and `skellytracker.certify_plan()` is built (`skellytracker/certification.py`).
It writes the local result in `quick-checks.json` of the EP store, and a passed quick check keeps the
field-test opt-in. The level `full` is built in the package
([ADR-75J6](entries/75J6-full-level-in-certify-and-uuid-report-id.md)). Each run of this list on
a system is a run of the certify process in a freemocap build
([ADR-Q7VQ](entries/Q7VQ-certify-rulings-of-2026-11-20.md) item 1). Build in this order:

1. A run of the level `full` on Linux and on macOS. One Windows host ran it for `trt-rtx`, `cuda` and
   `directml` on an RTX 3070 and for `directml` on a UHD 770: each EP check passed. Then calibrate its
   time estimates and the time estimates of the level `quick`.
2. A run of the sections `packs` and `full` of `tools/certify_platform.py` on Linux and on macOS. One
   Windows host ran the four sections ([ADR-SP4Z](entries/SP4Z-certify-suite-calls-the-full-level.md)):
   384 checks, no `fail`, 47 s for `packs` and 316 s for `full`. The section `hardware` gave one
   difference in 17 comparisons: `vram_mib` of the UHD 770 is 128 in skellytracker and 2047 in
   `Win32_VideoController`. The two tools read two fields: skellytracker reads the dedicated memory of
   DXGI, and `AdapterRAM` of this GPU holds 2147479552 bytes. It is not a defect of the probe. A build must write
   `skellytracker/_build_info.py`: the reader exists, the build step does not. `flit build` puts the
   file in the wheel and in the sdist, also when git ignores it (one trial on Windows, 2026-11-20).
3. A run of the quick check of `coreml` on a Mac. No Mac ran it
   ([ADR-ER5X](entries/ER5X-check-rule-unclean-exits-and-coreml.md) item 6).
4. A run of an install from the Windows ML catalog with a download, its progress and its cancel. The
   code is built (`eps.install()`, `eps.remove(execution_provider=...)`,
   `skellytracker-eps remove --windows-ml KEY`). On one Windows host, only the async call on a
   package that was on the PC ran: it ended in 0.01 s with no progress value. On 2026-11-20 the same
   host ran `_ensure_ready()` on the OpenVINO EP package of the catalog, which was not on the system
   (the catalog offers no AMD EP there): a cancel after 2 s ended in 2.6 s and left no package; the
   install ended in 10.3 s with the progress values 0, 90 and 100, so the package now divides the
   value by 100; `remove_package()` gave `package-not-removed` in the process that installed, and
   the removal passed from a new process. The cause is not examined. `install()` and `remove()` with
   a catalog key of an AMD EP did not run.
5. A run of the PyInstaller hook of ONNX Runtime on Linux and on macOS. The hook is built
   (`skellytracker/_pyinstaller/hook-onnxruntime.py`), and the freeze test ran on Windows only.
   `beartype_this_package()` checks nothing in a frozen app.
6. The passive record, the shadow comparison and the calibration of its limit. They are a part of
   the 2.0.0 pre-release ([ADR-Q7VQ](entries/Q7VQ-certify-rulings-of-2026-11-20.md) item 2). The
   format of `skellycertify` must first define the fields of a `passive` record.
7. Add a marker to `ep_evidence.yaml` and to `tools/onnx_stack.py` for a row from a passive record.
   The name of the field or the value is not decided.
8. No row of the list `mediapipe` exists. No real run of `mediapipe:smoke` inside `certify()` yet.
9. A real quick run on `trt-rtx` and `cuda` with the code of
   [ADR-X7WD](entries/X7WD-certify-levels-rulings-of-2026-11-20.md), and a real run that skips a
   reviewed pair.

CI runs `test_eps_session.py` on no Linux runner: `if: runner.os != 'Linux'` in
`.github/workflows/ep-pack.yml:41`.

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
- **Certify suite.** [ADR-Y14H](entries/Y14H-certify-suite.md): the frame and sections 1 to 5 are
  built. Sections 3 and 4 are in `tools/certify_eps.py`, section 5 is in `tools/certify_jpeg.py`.
  Sections 6 and 7 leave the suite
  ([ADR-P0JZ](entries/P0JZ-certify-contract-in-each-package.md) item 2; item 3 of the
  [certification build list](#certification-build-list)). These items stay open:
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
      package that `install KEY --field-test` installed is item 6 of the
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
  - Section 5 calls `run_jpeg_certification` of the JPEG branch. Until that branch lands, the
    section is `not-run` with `not-in-this-checkout`. The section also calls it once for each EP of
    `AMD_EPS` that passed section 3. A `directml` call is `record-only` when the hardware class of a
    GPU that section 3 tested does not list `directml`.
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
  - DirectML device memory: on one Windows host with ONNX Runtime 1.30.0 and DirectML 1.15.4, an
    input from `OrtValue.ortvalue_from_numpy(x, "dml", id)` gave a wrong output in 25 of 50 repeats
    on a session that took its GPU through `add_provider_for_devices`, the output of one DirectML
    session in `dml` memory was right in 300 of 300 repeats as the input of a second session, and
    only the device id 0 of a `dml` binding worked on each adapter, so later work must not bind a
    host-made `dml` input, and must use the device id 0.
  - freemocap work: the dialog of the prompt (item 14, at the times of
    [ADR-P0JZ](entries/P0JZ-certify-contract-in-each-package.md) item 5) and of the download prompt
    (item 9).
- **Dependency pins for the exporters.** [ADR-N6E8](entries/N6E8-onnxruntime-1-30-on-each-os.md)
  decides exact pins, ONNX Runtime 1.30.0 as a base dependency with GPU EPs as CUDA 13 plugin packs,
  and `requires-python = "==3.13.18"`. The exporters that agents build again pin the 2.0.0
  pre-release (the draft exporter guide). On 2026-10-28, two exporters required Python 3.14 or later,
  and uv could not resolve skellytracker in three of the four exporters. The dependency stage of the
  implementation plan wrote the pins on 2026-11-12. Until the 2.0.0 pre-release, an exporter runs
  the batch tool in the checkout environment.
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
- **Pipeline redesign.** Stages 1 to 7 of the redesign of the node and port types are built in
  skellytracker, and the absorb documents state the rules of
  [ADR-9HTX](entries/9HTX-pipeline-node-and-port-redesign.md).
  [ADR-8TQT](entries/8TQT-redesign-stages-6-and-7-before-the-pre-release.md) records the new timing
  of stages 6 to 8. Three items stay open:
  - Stage 8, the pipeline editor, is freemocap work that the user does in another session.
  - Later work: look into one canonical output keypoint set that becomes the only output format of
    a pipeline.
  - Later work: make one BGR to RGB conversion for each camera and frame for the decomposed
    MediaPipe pipeline.
- **Cost of the detector preprocess.** Measured on 2026-11-17 with `time.perf_counter_ns` on one
  desktop CPU, with OpenCV 5.0.0.93 and no other load. `preprocess_image` of
  `core/detectors/processing/pre/preprocess.py` needs about 5.2 ms for one 1280x720 frame with the
  `yolox-person` sidecar at size `m` (640x640). The time is almost the same for a 1920x1080 and a
  3840x2160 frame. It needs about 1.2 ms with the `rtmw-wholebody133` sidecar at size `m`
  (256x192). Three causes are known:
  - The `letterbox` function of `pre/resize_letterbox.py` needs about 1.8 ms, and its `cv2.resize`
    call needs 0.2 to 0.4 ms. The canvas fill from a `float64` array uses most of the difference.
  - The `normalize` function of `pre/normalize.py` makes a cast and two or three float passes
    over each pixel of the model input.
  - A detector prepares the images of one frame one after the other, in one `preprocess` span. The
    span thus grows with the number of cameras. freemocap showed more than 22 ms for the span
    `person.preprocess` with four cameras at 1280x720.

  In the built-in pipeline, the detector runs one time in 150 frames. The mean cost is small, but
  the frame with a detection has a delay of this size. No fix is decided. A change of this code
  must keep each output tensor equal. A second implementation on the GPU must agree with this code
  within the resize limit of `pre.resize.interpolation`
  ([ADR-J1HK](../specs/model-sidecar/decisions/entries/J1HK-resize-pixel-tolerance.md)).

  Result of 2026-11-18. The pipeline run now has the GPU preprocess graph
  ([ADR-W4NW](entries/W4NW-gpu-preprocess-of-a-model-node-and-its-cpu-warning.md)) and the GPU JPEG
  decode ([ADR-P245](../specs/pipeline/decisions/entries/P245-jpeg-frame-input.md);
  [ADR-88ZB](entries/88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md)). The measurements are
  in [ADR-1SZ9](entries/1SZ9-gpu-preprocess-and-gpu-jpeg-decode-in-the-pipeline-run.md) (the calls
  and spans end to end), [ADR-FBV5](entries/FBV5-gpu-path-agreement-on-the-freemocap-sample-data.md)
  (the agreement on a recording with people) and
  [ADR-BP5Y](entries/BP5Y-gpu-huffman-decode-threshold.md) (the GPU Huffman option, 500000 in the
  package). These items stay open:
  - The keypoint preprocess with several boxes for each frame was not measured. The frames give at
    most one box.
  - A model session with a dynamic batch pads the batch on the GPU path.
  - The run decodes the CPU JPEG frames of a call in a thread pool
    ([ADR-S1TG](../specs/pipeline/decisions/entries/S1TG-cpu-jpeg-decode-threads.md)). The gain of
    a full call is not measured yet.
- **Repeat the measurements on the pinned versions (ONNX Runtime 1.30.0, `cuda-cu13` 0.2.0) with at
  least 3 repeats and the spread.** The numbers of these records come from ONNX Runtime 1.31.1 and
  `cuda-cu13` 0.3.0, before the move: [ADR-1SZ9](entries/1SZ9-gpu-preprocess-and-gpu-jpeg-decode-in-the-pipeline-run.md),
  [ADR-FBV5](entries/FBV5-gpu-path-agreement-on-the-freemocap-sample-data.md),
  [ADR-BP5Y](entries/BP5Y-gpu-huffman-decode-threshold.md),
  [ADR-S1TG](../specs/pipeline/decisions/entries/S1TG-cpu-jpeg-decode-threads.md) (the decode
  timing), the Evidence of [ADR-88ZB](entries/88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md)
  and of [ADR-J1HK](../specs/model-sidecar/decisions/entries/J1HK-resize-pixel-tolerance.md), and
  the resize-limit runs of the GPU preprocess in the
  [spec open work](../specs/model-sidecar/decisions/open-work.md).
- **Results with no saved output.** Measure these again and record them. After the move to ONNX
  Runtime 1.30.0, with `gpu-jpeg-cu13` beside `cuda-cu13` 0.2.0: the count of the GPU tests that
  pass, and the counts of `run_jpeg_certification` (52 checks) on `cuda` and `trt-rtx`.
- **nvImageCodec hang of a one-image decode.**
  [ADR-975Z](entries/975Z-nvimagecodec-one-image-decode-hang.md) gives the cause, the runs and the
  workaround. Open: the report to NVIDIA is not sent (a minimal reproducer is ready). No run on Linux
  and no run on a host with few CPU cores.
- **Exit hang of the CUDA EP plugin.** [ADR-C6A5](entries/C6A5-exit-hang-of-the-cuda-ep-plugin.md)
  gives the runs and the findings. Open:
  - A run of the hang rate with `ORT_DISABLE_TELEMETRY=1` on `cuda-cu13` 0.3.0 is planned. No run
    has tested it.
  - More full runs on ONNX Runtime 1.30.0 with `cuda-cu13` 0.2.0 (0 of 43 is not enough), a full
    run on `trt-rtx` and a longer run of the minimal reproducer.
  - The setting `ORT_DISABLE_TELEMETRY=1` and the check of the upgrade checker are planned on
    `dom/sidecar-implementation` (user, 2026-11-19). This branch has no code for them.
  - The report to ONNX Runtime is not sent.
- **Repair of a damaged store folder.** A damaged pack folder or component folder of the EP store
  reports a state whose hint is to run the install command. The install does not repair the folder,
  because the folder exists. The remedy today is to remove the pack or the component, then to install
  it again. Packs had this gap before the component
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
field-test opt-in. Build in this order:

1. The level `full` in `certify()`. Today it returns the check `full` as `not-run` with `not-built`,
   and the level `full` is `tools/certify_platform.py`.
2. The report of `tools/certify_platform.py` in the format `skellycertify.report/1.0.0`, with the
   block `package` by the rules of `skellytracker/certification.py`. Add its reason codes to
   `skellytracker/REASON_CODES.md`. Cut the suite to sections 1 to 5. A build must write
   `skellytracker/_build_info.py`: the reader exists, the build step does not.
3. The flags of `PackStatus` (not certified, passed on this PC, failed on this PC) from
   `quick-checks.json`, and `recommend()` skips an EP that failed on this PC. An EP with no reviewed
   row is usable only after a whole quick check passes
   ([ADR-21BK](entries/21BK-quick-check-local-pass-and-hand-in.md) item 2).
4. The hand-in list in the EP store and the exit notice.
5. Progress and cancel for an install from the Windows ML catalog, and a remove call with a command
   of `skellytracker-eps` for a catalog package that this package installed. It never removes a
   package that was on the PC before.
6. The PyInstaller hook of ONNX Runtime.
7. The passive record, the shadow comparison and the calibration of its limit.
8. Add a marker to `ep_evidence.yaml` and to `tools/onnx_stack.py` for a row from a passive record.
   The name of the field or the value is not decided.

CI runs `test_eps_session.py` on no Linux runner: `if: runner.os != 'Linux'` in
`.github/workflows/ep-pack.yml:41`.

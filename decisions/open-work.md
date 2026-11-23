# Open work

This file holds the open work of the [decision log](README.md): the repository state. The
implementation-stage work is in the
[implementation plan](../specs/sidecar-implementation-plan.md). The spec defects are in the open work of the
[spec log](../specs/model-sidecar/decisions/open-work.md#spec-defects). Read the items that apply to
your task. The runs that wait for hardware or an OS that this project does not have are in
[hardware-runs.md](hardware-runs.md) ([ADR-8ACK](entries/8ACK-hardware-runs-checklist.md)).

## Implementation stage

The implementation-stage work is in the stages of phase 1 and phase 2 of the
[implementation plan](../specs/sidecar-implementation-plan.md) ([ADR-5WKW](entries/5WKW-implementation-work-in-the-plan.md);
[ADR-NHM3](entries/NHM3-phases-to-the-exporter-checkpoint.md)).

## Repository state

- **Certify suite.** [ADR-SP4Z](entries/SP4Z-certify-suite-calls-the-full-level.md): the suite has four
  sections, in `tools/certify_platform.py` and `tools/certify_eps.py`, and calls `certify("full")`. These items stay open:
  - The `cleanup` step of `decisions/scripts/xse7_windows_ml_rehearsal.py` fails with
    `record-refused` without the catalog hook. It needs the wrapper
    `decisions/scripts/zgf5_session_measurements/hooked_cleanup.py`
    ([ADR-ZGF5](entries/ZGF5-certify-measurements-of-2026-11-18.md) item 5).
  - The removal of a Windows ML package that the suite installs is built (item 5 of
    [ADR-XSE7](entries/XSE7-amd-eps-in-the-field-test.md)). Still open: the removal after a crash
    during `ensure_ready()` (a new enumeration must give the package family; a deployment that
    Windows ends after the cleanup stays); whether Windows downloads a package again after a removal
    or uses a local copy.
  - Section 4 does not measure the VRAM of an integrated GPU: the PDH counter of `LiveSampler` reads
    dedicated memory only.
  - The model list `models` (path, URL, sha256, bytes) is in the `certification` block of
    `ep_catalog.yaml` (item 12). The files are in the public model repository of the certify suite,
    on a personal Hugging Face account, not of the freemocap organisation. The term check of
    `tools/check_private_data.py` allows that one address (user, 2026-11-18). The files move before
    the 2.0.0 release ([ADR-XM9C](entries/XM9C-rulings-of-2026-11-23-on-ci-models-frames-and-upstream-reports.md) item 3).
  - A leak that the suite cannot stop: the cache of `uv`. It belongs to the tool of the volunteer.
  - The instructions page `CERTIFY.md` is a draft. Its clone address names the fork of the user. A
    report goes to an issue of the repository `skellycertify`.
  - Format 1.9.0 ([ADR-2YJX](entries/2YJX-report-format-1-9-0-and-the-option-setups.md)): the check
    of each existing check against section 5.6 of the format of `skellycertify` is not done. No
    real run made a report in the format 1.6.0 or later yet.
  - Section 1 still checks a certification tag. Evidence needs no tag now: the report records the
    version and the commit of each package ([ADR-P0JZ](entries/P0JZ-certify-contract-in-each-package.md)
    item 4; item 2 of the [certification build list](#certification-build-list)).
- **EP certification.** Two items of [ADR-MF2R](entries/MF2R-ep-store-install-and-certification.md)
  stay open:
  - Check the `thresholds` of the `certification` block of `ep_catalog.yaml` on more systems and
    images. [ADR-ZGF5](entries/ZGF5-certify-measurements-of-2026-11-18.md) gives the values of one
    RTX 3070 with `cuda` and `trt-rtx` on one image (item 16) and the spread of 10 runs.
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
  - macOS: the `onnxruntime` 1.30.0 wheel is not scanned and has no row.
- **Field-test opt-in.** [ADR-Z5X7](entries/Z5X7-field-test-state-and-directml.md): there is no
  command that removes an opt-in. A user deletes `field-test.json` of the EP store.
  - freemocap work: the dialog of the download prompt (item 9).
- **DirectML GPU preprocess.** The report from an AMD GPU is in
  [hardware-runs.md](hardware-runs.md). No record holds
  the time of the span `person.preprocess` with `gpu` and with `cpu` on the RTX 3070: measure it
  again.
- **Dependency pins for the exporters.** `pyproject.toml` has the pins of
  [ADR-N6E8](entries/N6E8-onnxruntime-1-30-on-each-os.md). The exporters that agents build again pin
  the 2.0.0 pre-release (the draft exporter guide). Until the 2.0.0
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
- **Cost of the detector preprocess.** The measurements are in
  [detector-preprocess-cost-2026-11-17.md](evidence/detector-preprocess-cost-2026-11-17.md),
  [ADR-B5Z0](entries/B5Z0-yolox-preprocess-timing-on-an-intel-igpu-system.md),
  [ADR-1SZ9](entries/1SZ9-gpu-preprocess-and-gpu-jpeg-decode-in-the-pipeline-run.md),
  [ADR-FBV5](entries/FBV5-gpu-path-agreement-on-the-freemocap-sample-data.md),
  [ADR-BP5Y](entries/BP5Y-gpu-huffman-decode-threshold.md) and
  [ADR-58F5](entries/58F5-native-jpeg-numbers-on-the-pinned-versions.md). The reused batch
  (`BatchPreprocessor` of `core/detectors/processing/pre/preprocess.py`) is in the CPU path. Open:
  - Measure JPEG input on `cuda` and `trt-rtx` with the CPU decode and the reused batch against
    the GPU path. The `cpu` rows of ADR-4JFP item 5 used the CPU code before the reused batch.
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
- **Intel QSV JPEG decode**
  ([ADR-71YY](entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md)): see the research
  note [gpu-jpeg-decode-intel-qsv.md](../research/gpu-jpeg-decode-intel-qsv.md).
- **AMD JPEG decode with rocJPEG (Linux):** see the research note
  [gpu-jpeg-decode-amd-rocjpeg.md](../research/gpu-jpeg-decode-amd-rocjpeg.md).
- **nvImageCodec hang of a one-image decode**
  ([ADR-975Z](entries/975Z-nvimagecodec-one-image-decode-hang.md)). The runs are in
  [hardware-runs.md](hardware-runs.md). The project sends no report to NVIDIA
  ([ADR-XM9C](entries/XM9C-rulings-of-2026-11-23-on-ci-models-frames-and-upstream-reports.md) item 4).
- **Exit hang of the CUDA EP plugin** ([ADR-C6A5](entries/C6A5-exit-hang-of-the-cuda-ep-plugin.md)).
  Open: more full runs on ONNX Runtime 1.30.0 with `cuda-cu13` 0.2.0 (0 of 43 is not enough); a
  full run on `trt-rtx`; a longer run of the minimal reproducer
  ([ADR-J9KX](entries/J9KX-exit-hang-of-the-full-run-with-the-telemetry-switch.md) has the run with
  the telemetry switch). The project sends no report to ONNX Runtime
  ([ADR-XM9C](entries/XM9C-rulings-of-2026-11-23-on-ci-models-frames-and-upstream-reports.md) item 4).
- **Repair of a damaged store folder.** A damaged pack or component folder of the EP store gives a
  state whose hint is the install command, but the install does not repair a folder that exists.
  The remedy today: remove the pack or the component, then install it again
  ([ADR-88ZB](entries/88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md)).
- **Kit PR in freemocap/project.** The kit is on the branch `dom/agents-and-adr-kit` of
  freemocap/project, in a PR for its owner
  ([ADR-P3NK](entries/P3NK-bootstrap-kit-in-freemocap-project.md)). The link repairs in 0031, NB91,
  QPS7 and Z05A pin the commit `0d88941` of that branch. When the PR merges with a different SHA,
  pin the merged commit.
  The checkout `../project` has the two-way kit sync from 2026-11-23, and the old one-way check
  `tools/sync_bootstrap_kit.py --check` fails against it. `tools/run_checks.py` does not run that check, and
  its copy test is skipped, until this repository takes `kit_sync.py` and `kit.toml` (user, 2026-11-23).
- **Rulings of 2026-11-23**
  ([ADR-4JAW](entries/4JAW-rulings-of-2026-11-23-on-sessions-the-certify-prompt-and-linux.md)):
  - Item 3 is not built: set `enable_cuda_graph` to `1` in the defaults of `trt-rtx` in the EP
    catalog. First measure the default and the cost of `0` on the pinned pack.
  - Item 5: the built-in `mediapipe-holistic-tasks` must replace the two old MediaPipe demo builders
    of `skellytracker/__main__.py`. Do it when the old detectors go.
  - No document states some kept rules of the consolidation entries of 2026-11-23, so these entries
    stay `accepted`. Write each rule in the docstring of its module, then absorb the entries.
- **Specs move to `skellyspecs`** ([ADR-2DJ8](entries/2DJ8-spec-tools-with-no-package-import.md)). Open: the pin file and the sibling
  checkout; the delete of the two spec folders here, in the pin commit; the split of the tests of
  `tools/tests/` that move and still import the package; `--root` with no default (item 7); the
  gate runner of the reference files; the made-up sample of the reference files.
- **Certify report** ([ADR-8N03](entries/8N03-certify-report-rules-of-format-1-10.md)). Open: the judging of the GPU frame path by GPU
  model (item 8); a run of the Linux `is_integrated` reader on an AMD APU and an AMD dedicated card; `GpuInfo.is_integrated` in the facts of
  `PipelineRun.models` with `cpu_nodes`, for the metrics panel of freemocap; a real run of the level
  `full` with the new rules.
- **Frozen smoke test.** At stage 1.11, the frozen smoke test must load the sidecar files with the
  new loader ([ADR-4RWX](entries/4RWX-sessions-and-errors-consolidation.md) item 16).

## Certification build list

[ADR-P0JZ](entries/P0JZ-certify-contract-in-each-package.md),
[ADR-21BK](entries/21BK-quick-check-local-pass-and-hand-in.md) and
[ADR-K8Q0](entries/K8Q0-platform-rulings-of-2026-11-19.md) are decided. The quick level of
`skellytracker.certify()` and `skellytracker.certify_plan()` is built (`skellytracker/certification.py`).
It writes the local result in `quick-checks.json` of the EP store, and a passed quick check keeps the
field-test opt-in. The level `full` is built in the package
([ADR-75J6](entries/75J6-full-level-in-certify-and-uuid-report-id.md)). Each run of this list on
a system is a run of the certify process in a freemocap build
([ADR-Q7VQ](entries/Q7VQ-certify-rulings-of-2026-11-20.md) item 1). Items 1, 3 and 5 and the runs
of items 2 and 4 are in [hardware-runs.md](hardware-runs.md). The dated facts of items 2 and 4 are
in [8ACK-open-work-facts.md](evidence/8ACK-open-work-facts.md). Build in this order:

1. The run of the level `full` on Linux and on macOS: see the hardware runs.
2. A build must write `skellytracker/_build_info.py`: the reader exists, the build step does not.
3. The quick check of `coreml` on a Mac: see the hardware runs.
4. The install from the Windows ML catalog. The code is built (`eps.install()`,
   `eps.remove(execution_provider=...)`, `skellytracker-eps remove --windows-ml KEY`). Not built: the
   removal of a `pending` record in a new process, which gives `package-unknown`.
5. The PyInstaller hook of ONNX Runtime on Linux and on macOS: see the hardware runs.
   `beartype_this_package()` checks nothing in a frozen app.
6. The passive record, the shadow comparison and the calibration of its limit, in phase 2
   ([ADR-Q9R6](entries/Q9R6-certify-rulings-of-2026-11-21.md) item 3). The format of
   `skellycertify` must first define the fields of a `passive` record.
7. Add a marker to `ep_evidence.yaml` and to `tools/onnx_stack.py` for a row from a passive record.
   The name of the field or the value is not decided.
8. No row of the list `mediapipe` exists. No real run of `mediapipe:smoke` inside `certify()` yet.
9. A real quick run on `trt-rtx` and `cuda` with the code of
   [ADR-X7WD](entries/X7WD-certify-levels-rulings-of-2026-11-20.md), and a real run that skips a
   reviewed pair.

CI runs `test_eps_session.py` on no Linux runner: `if: runner.os != 'Linux'` in
`.github/workflows/ep-pack.yml:41`.

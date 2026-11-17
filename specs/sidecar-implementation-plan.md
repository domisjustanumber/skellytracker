# Implementation Plan: Phases to the Exporter Checkpoint

> **Decisions.** The decisions behind this plan are recorded in the decision log, [`decisions/`](../decisions/README.md). The phases and their order follow [ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md). The dependency pins and the GPU EP packs follow [ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md). The implementation-stage work follows [ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) (replace the package ONNX detectors) and [ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) (the entry points and the layout). The pipeline design is in [ADR-7NY2](../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md), [ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md), [ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md), [ADR-3SF2](../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md), [ADR-0WTV](../decisions/entries/0WTV-system-metrics-and-pipeline-timing-helper.md) and the [pipeline log](pipeline/decisions/README.md). The sidecar names follow [ADR-88WQ](../decisions/entries/88WQ-sidecar-vocabulary.md) and [ADR-GKD1](../decisions/entries/GKD1-estimator-type-says-the-crop.md). Entries 0002 to 0007 record the decisions of M1 to M5 ([History](#history)). This plan stays until the user decides to delete it ([ADR-5WKW](../decisions/entries/5WKW-implementation-work-in-the-plan.md)). Record a new decision as a decision entry, not in this plan.

> Status: **M1 to M5 are done. Phase 0 is done, except the two PRs of stage 0.5 that the user opens. Phase 1 started on 2026-11-12, and stages 1.1, 1.2 and 1.4 to 1.10 are done. Stage 1.3 is started, and its gate is open.** Phase 0 is in the spec-build stage, and phase 1 is in the implementation stage ([Stages](model-sidecar/model-addition-workflow/README.md#stages)). The [stage order](#stage-order) gives each stage. The "Status" line of each stage gives its state.

## Context

`specs/model-sidecar/sidecar-spec.md` defines a YAML "sidecar" format that describes the runtime I/O contract for ONNX detector/pose models: input tensor shape, normalization, resize, batching, output semantics, and decode logic. Two commits (`ec12b32`, `837bd09`) landed the spec document itself; this plan implements it in code.

The implementation-stage work re-implements each package ONNX detector on a fixed-batch, spec-compliant model from the exporters, starting with `yolox-person` and `rtmw-wholebody133`. The old detectors, their sidecars and their golden fixtures are deleted and replaced. They do not migrate to the spec ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md)). The new code goes beside the old code. Phase 2 deletes the old code ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md)). MediaPipe stays outside the spec and keeps working. Two entry points, `detectors` and `pipelines`, list the models and the pipelines and start a pipeline run ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md)).

Explicitly out of scope for this repo/plan: the skellycam API surface that exposes available models to FMC, and the FMC pipeline-builder UI. Those live in other repos.

## Checkpoint

At the checkpoint, agents can build the exporters again and add their new models and pipelines
([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 2). The checkpoint has:

- each dependency bumped and pinned ([1.1](#11-dependencies));
- the MediaPipe Holistic task ([1.8](#18-mediapipe-holistic-runner));
- `yolox-person` and `rtmw-wholebody133` with a fixed batch and the batch conversion
  ([1.7](#17-standalone-generic-detectors-was-n4), [1.9](#19-the-first-new-models-was-n5));
- the API for the sidecar models (`detectors`, [1.4](#14-spec-loader-was-n1) to
  [1.7](#17-standalone-generic-detectors-was-n4)), the pipelines (`pipelines`,
  [1.10](#110-the-pipeline-api-was-p)) and the hardware and EPs
  ([1.3](#13-hardware-and-ep-api));
- the pipeline spec, with its contribution and implementation process
  ([0.2](#02-pipeline-contribution-and-implementation-process));
- the sidecar spec, with its implementation process ([0.1](#01-acceptance-gate-and-patch-process));
- an up-to-date exporter kit: the draft exporter guide, the templates and the skills
  ([0.3](#03-exporter-kit)).

The pre-release of [1.11](#111-checkpoint-the-200-pre-release) marks the checkpoint. Then agents
build the exporters again ([phase 2](#phase-2--after-the-checkpoint)).

## Stage order

**Status: phase 0 is done, except the two PRs of stage 0.5. Stages 1.1, 1.2, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9 and 1.10 are done. Stage 1.3 is started, and its gate is open.**

Each stage of phase 1 and phase 2 changes package code. The gate of phase 0 is met
([ADR-V6G2](../decisions/entries/V6G2-implementation-stage.md)). The stages give the order of the
work and hold their items.

| Stage | Needs | Gate | Working ONNX code after the stage |
|---|---|---|---|
| **Phase 0, spec-build stage** | | | |
| 0.1 Acceptance gate and patch process | — | `tools/run_checks.py`; tests of the patch handling | old |
| 0.2 Pipeline contribution and implementation process | — | `tools/run_checks.py` | old |
| 0.3 Exporter kit | 0.1, 0.2 | `tools/run_checks.py`; the user accepts the kit | old |
| 0.4 Merge `hw-and-ep-work` | — | `tools/run_checks.py` after the merge; stage 1.3 is written | old |
| 0.5 Gate: the implementation stage | 0.1 to 0.4 | a new entry of the user | old |
| **Phase 1, implementation stage** | | | |
| 1.1 Dependencies | 0.5 | the gates of [ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) item 7 | old |
| 1.2 Package layout | 1.1 | full suite with no change of expected values | old |
| 1.3 Hardware and EP API | 1.2 | the default suite offline; the `ep_pack` and PyInstaller jobs; the local GPU gate | old |
| 1.4 Spec loader | 1.2 | new validation tests; each reference example validates | old |
| 1.5 Spec processing | 1.4 | the vector cases of the new entries agree; the old entries do not change | old |
| 1.6 Catalog and `detectors` | 1.4 | catalog tests on temporary roots; static-table test | old |
| 1.7 Standalone generic detectors | 1.5, 1.6 | detector tests on generated ONNX models; old tests unchanged | old, and the new detectors on a generated model |
| 1.8 MediaPipe Holistic runner | 1.2 | the expected point sets; MediaPipe tests unchanged | old |
| 1.9 `yolox-person`, `rtmw-wholebody133` | 1.7, 0.1 | the model gate at the detector level, run locally | old, and the new detectors |
| 1.10 Pipeline API | 1.3, 1.7, 1.8, 1.9, the pipeline spec | the gate of 1.10 | old, and the new pipelines |
| 1.11 Checkpoint: the 2.0.0 pre-release | 1.10, 0.3 | [ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 5 | old, and the new pipelines |
| **Phase 2, after the checkpoint** | | | |
| 2.1 Delete the old YOLOX and RTMW | 1.11 | full suite without the deleted tests | new YOLOX and RTMW pipelines, old RTMPose |
| 2.2 RTMPose `body17`, `hand21`, `face106` | 1.11, the exporter | the model gate; `rtmpose-body-hands-face` runs | all new, and old RTMPose |
| 2.3 Delete the old RTMPose, the old loader and the old processing | 2.2 | full suite; vector tests | new ONNX only, old run code |
| 2.4 Delete the old run code | 2.3 | full suite; each built-in runs as a pipeline config | new only, as pipeline configs |
| 2.5 Release 2.0.0 | 2.4 | full suite; the ruff rule review; the test coverage review | new only, as pipeline configs |

Stages 1.3 and 1.8 need only 1.1 and 1.2. They can run in parallel with 1.4 to 1.7.

Former names. The decision entries and older text use these names:

| Former name | Stage |
|---|---|
| L (layout, MediaPipe 1.2.2, Python 3.13, no Intel Mac) | 1.1 and 1.2 |
| N1, N2, N3, N4, N5 | 1.4, 1.5, 1.6, 1.7, 1.9 |
| Pre-release 2.0.0 | 1.11 |
| P | 1.10 |
| Da, N6, Db, Dc | 2.1, 2.2, 2.3, 2.4 |
| M6 to M12 | See [Moved sections](#moved-sections) |

Rules for each stage:

- Phase 0 changes no file under `skellytracker/` ([ADR-0014](../decisions/entries/0014-spec-lifecycle.md)).
- The old ONNX detectors, the old loader `core/sidecar/`, the old processing modules, `core/tracker/`
  and the old detector contract do not change until their replacements pass the gate. Then a
  deletion stage removes them.
- New code does not import the old loader, the old processing modules, `core/tracker/` or the old
  detector contract. No shared function gets a legacy switch.
- New code takes the execution provider as `execution_provider`. The old demos with `provider=` are
  replaced code ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md)).
- New code uses the current sidecar names
  ([ADR-88WQ](../decisions/entries/88WQ-sidecar-vocabulary.md);
  [ADR-GKD1](../decisions/entries/GKD1-estimator-type-says-the-crop.md)). The old package code keeps
  the old names until a deletion stage removes it.
- MediaPipe works after each stage. The MediaPipe tests keep their expected values, except in the
  one commit of the MediaPipe change (1.1) and in 2.4.
- Do not change the MediaPipe tests to close their detectors or to add teardown. These tests show
  the timestamp defect when it comes back
  ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 9).
- Each commit has one kind of change. Load the skill
  [`stack-commit`](../.claude/skills/stack-commit/SKILL.md) before a commit.

Reason for the order: the old detectors call `load_sidecar` at import (for example
`rtmpose_body_detector.py`). A change of `core/sidecar/` in place makes them fail at import. A
change of `processing/` in place changes their output.

## Phase 0 — Spec-build stage

### 0.1 Acceptance gate and patch process

**Status: DONE (2026-11-12).** It carries out [ADR-6J8E](../decisions/entries/6J8E-exporters-run-released-skellytracker.md)
and [ADR-JJ7E](../decisions/entries/JJ7E-no-upstream-case-verified-by-skellytracker.md). The new
rules apply from the pre-release of 1.11. Each one stands beside the current rule under the marker
"From the 2.0.0 pre-release". Stage 1.11 deletes the current rules that they replace.

- Done: the patch `skellytracker.patch` and the key `patch_release` in
  [Patches](model-sidecar/model-addition-workflow/hand-over.md#patches), with the checks of
  `pack` and `verify` and their tests; the
  [Patch review](model-sidecar/model-addition-workflow/hand-over.md#patch-review) and the line of
  [section 6](../AGENTS.md#6-git-rules) of `AGENTS.md`; the
  [acceptance gate](../.claude/skills/implement-sidecar-section/proposal-gate.md), with the
  response state `verified` in `hand-over.md` and `tools/intake_bundle.py`; the gate as a
  precondition of procedures A and B of `change-sidecar-spec` and in item 6 of
  [phase 3](model-sidecar/model-addition-workflow/phase-3-skellytracker.md); the
  [Independence](model-sidecar/model-addition-workflow/sidecar-files.md#independence) rules of the
  pre-release; the patch step of step 5 of `implement-sidecar-section`.
- Stage 1.9 runs steps 5 to 7 of the gate for `yolox-person` and `rtmw-wholebody133`.

### 0.2 Pipeline contribution and implementation process

**Status: DONE (2026-11-12).** It carries out [ADR-3SF2](../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md)
item 7 and [ADR-271H](../decisions/entries/271H-pipeline-bundles.md).

- Done: the workflow [Pipeline contributions](pipeline/contributions.md); the templates in
  `specs/pipeline/templates/`; `specs/pipeline/inventory.yaml`; the kind `pipeline` in
  [Pipeline bundles](model-sidecar/model-addition-workflow/hand-over.md#pipeline-bundles) and in
  `tools/intake_bundle.py` (the checks of a pipeline file, with tests); the routing of the
  `node.<type>` proposals to `specs/pipeline/` in `tools/intake_bundle.py`; the skills
  `change-pipeline-spec` (with the hash update after a re-export) and `implement-pipeline-node`.
- Open for stage 1.10: the run gate of a pipeline bundle and its tolerance, and the load checks of
  [ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 7 in `verify`. The
  exporter guide of 0.3 links the workflow.

### 0.3 Exporter kit

**Status: DONE (2026-11-12).** The user accepted the kit. Done: the pre-release pin with exact pins
(Python 3.13.18, [ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md)), the patch and the pipeline file in the templates and the skills
`author-sidecar` and `propose-sidecar-change`, the opset and fp16 GPU placement check
([ADR-NPX6](../decisions/entries/NPX6-newest-opset-and-fp16-gpu-placement-check.md); [ADR-EY4F](../decisions/entries/EY4F-acceptance-gate-checks-fp16-gpu-placement.md)) and the rewording of the example exporter names. The kit is the draft exporter guide (`specs/draft/exporter-guide/`), the
templates of `specs/model-sidecar/templates/` and the skills that exporter agents read. The user
changes the draft exporter guide ([ADR-x64y](../decisions/entries/x64y-draft-exporter-guide-folder.md)). Do not change an exporter repository.

- **Exporter runtime.** Each exporter pins the pre-release of 1.11 as its ONNX host. Its host code
  for the spec sections retires ([ADR-6J8E](../decisions/entries/6J8E-exporters-run-released-skellytracker.md) item 1). The kit gives the form of the pin. Stage 1.11
  sets the version.
- **Dependency pins.** The exporters use the pins of the pre-release ([ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) items 1 and 4): Python
  3.13.18 and ONNX Runtime 1.31. A GPU EP comes from the CUDA 13 plugin packs of the EP catalog of
  the pre-release ([ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) item 3).
- **Patches and pipelines.** The templates and the skills `author-sidecar` and
  `propose-sidecar-change` take the patch of 0.1 and the pipeline file of 0.2.
- The item "Exporter guide rewording" of the [open work](../decisions/open-work.md).
- Gate: `uv run python tools/run_checks.py` passes. The user accepts the kit.

### 0.4 Merge `hw-and-ep-work`

**Status: DONE (2026-11-12).** The six commits of the EP device check suite are on the working branch.
[ADR-V9NK](../decisions/entries/V9NK-ep-device-checks-evidence.md) names the suite. [ADR-NZK1](../decisions/entries/NZK1-ep-options-evidence.md) names the EP option scripts in
`decisions/scripts/ep_options/`. Stage 1.3 is written from [ADR-246B](../decisions/entries/246B-ep-catalog-store-and-install.md), [ADR-D8DH](../decisions/entries/D8DH-sessions-errors-and-the-ready-rule.md),
[ADR-P1F3](../decisions/entries/P1F3-hardware-probe-devices-and-multi-gpu.md), [ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) and [ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md). `tools/run_checks.py` stops only at
the known MediaPipe hang on Windows, and the doc tests pass. The user removes the worktree of
`hw-and-ep-work`.

The hardware and EP work stayed a parallel track on the branch
`hw-and-ep-work` until this stage ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 3).

- Copy the six commits of the EP device check suite to the working branch with `git cherry-pick`
  ([ADR-BH7C](../decisions/entries/BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md) item 6). On 2026-11-12 the branch has 9 commits that the
  working branch does not have: the EP device check suite in `decisions/scripts/ep_device_checks/`
  with its reports and its test, older copies of the graphify commits and one merge commit. Do not
  copy the graphify commits or the merge commit. Keep the graphify files of
  the working branch ([ADR-87B2](../decisions/entries/87B2-local-graphify-code-graph.md)). No commit of the branch changes a file under `skellytracker/`.
- The device check scripts need an entry that names them, or a move to `tools/` with a test
  ([ADR-EY8R](../decisions/entries/EY8R-tools-and-scripts.md)).
- Write stage 1.3 from the local plans of the track. Git does not track those plans, so 1.3 gets
  their content, not a link. Bring that content in line with [ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 3 (`system/`, `metrics/`
  and `eps/` under an eager `core`; the import isolation rules are withdrawn), [ADR-0WTV](../decisions/entries/0WTV-system-metrics-and-pipeline-timing-helper.md) item 1 and
  [ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) items 2 and 3 (one ONNX Runtime core; the GPU EPs are CUDA 13 plugin packs:
  the CUDA 12 floors, the CUDA 12 packs and the Pascal test go), and with [ADR-9NW0](../decisions/entries/9NW0-ep-keys-options-and-failures.md) (the EP keys, the EP
  options, the raise on a whole-EP failure and the report of CPU nodes).
- The EP option measurements that [ADR-9NW0](../decisions/entries/9NW0-ep-keys-options-and-failures.md) cites need an evidence entry with their scripts
  ([ADR-EY8R](../decisions/entries/EY8R-tools-and-scripts.md)).
- After the copy, the branch and its worktree retire. The user removes the worktree.
- Gate: `uv run python tools/run_checks.py` passes after the copy. Stage 1.3 has its items and its
  gate.

### 0.5 Gate: the implementation stage

**Status: STARTED.** It needs 0.1 to 0.4. Done: the retirement of
`notes/sidecar-exporter-coverage.md`, with its unique measurements in [ADR-Z0CC](../decisions/entries/Z0CC-exporter-coverage-measurements.md),
the consolidation entry [ADR-W5QD](../decisions/entries/W5QD-pipeline-entries-consolidation.md) of the pipeline entries, and the
declaration of the implementation stage, [ADR-V6G2](../decisions/entries/V6G2-implementation-stage.md), and the rebuild
(2026-11-12). Left: the user opens the two PRs.

- The user declares the implementation stage in a new entry. The entry changes
  [section 1](../AGENTS.md#1-purpose) of `AGENTS.md` and the "Stage" part of the skill
  `implement-sidecar-section`, and says which rules of [ADR-0014](../decisions/entries/0014-spec-lifecycle.md) end.
- The end of the spec-build stage also has a consolidation entry (the
  [Rules](../decisions/README.md#rules)).
- Then the session rebuilds the spec-build work into the two PRs `dom/52-process` and `dom/53-spec`
  ([Rebuild at the gate](../.claude/skills/stack-commit/after-spec-build.md#rebuild-at-the-gate)).
  The user opens them. Each stage of phase 1 is then one stacked PR, from `dom/54-dependencies`
  ([ADR-BH7C](../decisions/entries/BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md)).

## Phase 1 — Implementation stage

### 1.1 Dependencies

**Status: DONE (2026-11-12).** [ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) gives the rules. Each item below is its own commit group.

- **Exact pins.** Pin each dependency of `dependencies` and of each extra with `==`, at the version
  of a new `uv.lock`. Use an environment marker where a platform needs it. Today
  `opencv-contrib-python`, `onnx`, `polars` and `scipy` have no version, and other dependencies have
  ranges. The OpenCV package is `opencv-contrib-python`
  ([ADR-W09C](../decisions/entries/W09C-opencv-contrib-python.md)).
- **One ONNX Runtime core.** Make `onnxruntime` with one exact 1.31 release a base dependency.
  Remove the extras `onnx-cpu`, `onnx-cuda`, `onnx-trt` and `onnx-directml`, the `all-*` and
  `recommended-*` extras that name them, and the packages `onnxruntime-gpu`,
  `onnxruntime-directml`, `tensorrt` and `nvidia-*-cu12`. Remove the comments of `pyproject.toml`
  that explain the CUDA 12 cap. Remove the TensorRT, DirectML and CUDA library loading paths of the
  old `core/sessions/` code: the old ONNX detectors are then CPU only. Change each command that
  names a removed extra, for example `uv sync --extra all-cpu`. The gate is the suite on the CPU
  core. The GPU EPs come in stage 1.3 as plugin packs
  ([ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) items 2, 3 and 7).
- **MediaPipe 1.2.2.** This is its own commit group. Pin the `mediapipe` extra at 1.2.2
  ([ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) item 5). The gate is the
  MediaPipe tests. A change of their expected values goes in one commit, before a parity baseline.
  Then run the scripts of
  [ADR-6JWJ](pipeline/decisions/entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md) again on
  MediaPipe 1.2.2. If a VIDEO-mode landmarker then stays empty while a person is visible, write a new
  entry in the pipeline log with the evidence.
- **Python 3.13.18.** This is its own commit group. Set `requires-python = "==3.13.18"`, write
  `3.13.18` to `.python-version`, set the 3.13 classifier, make a new `uv.lock` and make CI run
  3.13.18 in place of 3.12 ([ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) item 4). The gate is the full suite on 3.13.18, with no hang in
  the MediaPipe tests. Check that each dependency has a wheel for 3.13 on each supported platform.
- **No Intel Mac.** This is its own commit group. The uv environment for macOS becomes
  `sys_platform == 'darwin' and platform_machine == 'arm64'`, with `required-environments`
  ([ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) item 6). The README says that Intel Mac is not supported. Check that
  `required-environments` fails at lock time for a missing wheel.
- Gate: the gates above. The full suite passes with no change of expected values, except the one
  MediaPipe commit.

### 1.2 Package layout

**Status: DONE (2026-11-16).** This stage has only the layout items that leave the old ONNX code alone.
The release workflow runs the check `tools/check_dist_onnx.py` after `flit build`.

- `core/__init__.py` stays eager ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 3). Stage 1.3 puts `system/`, `metrics/` and `eps/`
  under `core/`.
- Move charuco and aruco to `core/detectors/calibration_detectors/`
  ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 4).
- `core/model_zoo/` exists. It holds `landmark_schemas/`
  ([ADR-23F5](../decisions/entries/23F5-landmark-schema-registry.md)). Make it the package sidecar root
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 5). Add
  `skellytracker/core/model_zoo/**/*.onnx` to `.gitignore`. flit puts each file of the package
  folder in a wheel. Thus build each release from a clean checkout. Add a check that fails the build
  when a wheel or an sdist holds an `.onnx` file.
- `core/detectors/shared/` does not move yet, because the old sidecars `$ref` it. The new exports
  write their keypoint lists in full, so `core/model_zoo/` needs no `shared/` yet. Stage 2.3 moves it.
- `core/tracker/` keeps its name. Stage 2.4 deletes it.
- Update the paths in the README, the examples, the demos and the tests. Add no shim
  ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 7).
- Gate: the full suite passes with no change of expected values.

### 1.3 Hardware and EP API

**Status: STARTED.** Stage 0.4 (Merge `hw-and-ep-work`) wrote this stage on 2026-11-12. Steps 1 to 18
are done (2026-11-16). The gate is open:

- The default suite passes locally on Windows. The `ep_pack` test and the frozen smoke test pass
  locally on Windows.
- The job `pyinstaller` of `tests-full.yml` passed in run 43912761747. This gate part is met.
- The `ep-pack` job (`.github/workflows/ep-pack.yml`) passed on Linux, macOS and Windows in run
  43917772441. This gate part is met. In run 43910358178 the Windows job and the Linux job failed on
  runners with an AMD CPU: the OpenVINO test pack registers and lists no device.
  [ADR-FQ9A](../decisions/entries/FQ9A-selftest-test-pack-on-a-host-with-no-intel-device.md) gives
  the rule for such a host.
- The default suite did not run with the network off. This gate part is open.
- The local GPU gate ran on an RTX 3070 ([ADR-73Q4](../decisions/entries/73Q4-local-gpu-gate-of-the-ep-api.md)).
  Each part passes, with one exception: with `cuda`, 5 opset 11 files
  `rtmw-wholebody133-<size>_b4_fp16.onnx` of the local export folder have 3 `Clip` nodes on the CPU
  EP. The opset 17 files have 0.
- [ADR-0YYY](../decisions/entries/0YYY-host-reader-costs.md) has the costs of the host readers.

Not done in this stage:

- The device match of the verification by the GPU load. It needs a measurement on a host with two
  GPUs.
- `install(plan, from_dir=...)` from an unpacked pack folder. It installs from the wheels of the
  lock only.
- `InstallResult.needs_worker_restart` is always false: no code tracks the packs of other processes.
- A local run of the Linux and macOS readers, of the Linux pack preloads and of the `coreml` EP.
  Only the CI jobs run them. The IOKit reader of macOS and the `pci.ids` lookup of Linux
  ([ADR-Q4BF](../decisions/entries/Q4BF-host-probe-without-losses-for-freemocap.md)) ran only on fixtures.
  At the end of the freemocap migration work, verification scripts for Linux and macOS do this run:
  the host readers, the EP status and one pipeline run on `cpu` (user, 2026-11-16). A person runs
  them by hand on a real machine, one or two times. They are scripts in `decisions/scripts/` with
  an evidence entry, not tools ([ADR-EY8R](../decisions/entries/EY8R-tools-and-scripts.md)). Their
  report holds no hostname, no user name and no path.

Names: `run_devices()` and `RunDevice` keep their proposed names. The modules of `core/eps/` are
`recommendation.py`, `installer.py`, `registration.py`, `verification.py`, `self_test.py`, `state.py`
(`status()`, `check_start()`), `session.py` and `cli.py`. A consumer of the EP store is `environment`
or `frozen`.

It needs 1.1 and 1.2. It can run in parallel with 1.4 to 1.7. Stage 1.10 (The pipeline API) needs
it. It builds `core/system/`, `core/metrics/` and `core/eps/` under the eager `core`
([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 3), the GPU EP
packs ([ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) item 3) and
the EP rules of [ADR-9NW0](../decisions/entries/9NW0-ep-keys-options-and-failures.md). Rules of the stage:

- `eps.build_session()` serves only the new code, not `OnnxSession` or `Tracker.create`. This stage
  does not change old core files. Stage 2.4 deletes `core/sessions/`
  ([ADR-D8DH](../decisions/entries/D8DH-sessions-errors-and-the-ready-rule.md)).
- `eps` reads no sidecar. The caller fills `ModelRef` from the new loader of stage 1.4.
- `system`, `metrics` and `eps` can import `core` code. One guard test stays: a fresh
  `import skellytracker.core.eps` loads no `onnxruntime`. The freeze rule stays: no import by a
  computed name; a lazy import is a plain statement in a function body.
- New direct dependencies, with exact pins: `nvidia-ml-py`, `psutil` (Windows marker only) and
  `platformdirs`. No `certifi`.
- An EP flow has no licence accept step. A pack shows a plain licence link.

Items ([ADR-0WTV](../decisions/entries/0WTV-system-metrics-and-pipeline-timing-helper.md) item 1;
[ADR-P1F3](../decisions/entries/P1F3-hardware-probe-devices-and-multi-gpu.md)):

- **Records.** Each record is a `@dataclass(frozen=True)` with no `dict` field. Memory is `int` bytes, time is `int` ns, and a field that ends in
  `utilization` is a `float` ratio from 0 to 1. Vendor data goes in a last field
  `nvidia: Nvidia<Name> | None = None`. The join key of a GPU is `pci_bus_id`, else an OS id.
  `device_key` is `<kind>:<pci_vendor>:<pci_device>:<n>` (for example `gpu:10de:2484:0`), with `n`
  the rank by `pci_bus_id`. No text holds an absolute path or a hostname.
- **Caller rules.** The probes and the sampler make no CUDA call and load no EP library. They do not
  raise for missing hardware or ORT: the field is `None`, with one line in `probe_errors` or
  `sample_errors`. Each call is thread-safe. NVML access resets after a fork.
- **`core.system`.** `probe_host()`, `probe_runtime()`, `probe_environment()` (each cached) and
  `probe_loaded_libraries()`. `HostInfo` has the OS, `os_build`, `native_arch`, CPU, memory, `gpus`
  (PCI ids, LUID, driver, VRAM; NVIDIA UUID and compute capability), virtualization and container.
  `probe_runtime()` gives facts only. The private readers are in `core/_hardware/`: NVML, the OS
  readers, Windows PDH, DXGI, and one D3DKMT adapter-address query only for the LUID-to-bus-id join.
- **`core.metrics`.** `LiveSampler.sample(pids)` gives `LiveSample` (CPU, memory, each asked process
  with RSS and Windows PDH VRAM, each NVML GPU). `free_vram(device)` is one NVML read with no state; it gives `None` with no NVML value.
- **EP catalog.** `core/eps/ep_catalog.yaml` (by hand) and `core/eps/ep_lock.yaml` (only
  `tools/ep_catalog.py --refresh` writes it: URL, sha256 and sizes of each wheel)
  ([ADR-246B](../decisions/entries/246B-ep-catalog-store-and-install.md)):

  | Key | Kind | Pack, or the EP name | Floors |
  |---|---|---|---|
  | `trt-rtx` | plugin, GPU | `onnxruntime-ep-nv-tensorrt-rtx-cu13==0.5.0` (PyPI) | NVIDIA CC ≥ 8.0, driver branch ≥ R580 |
  | `cuda` | plugin, GPU | `onnxruntime-ep-cuda13==0.3.0` with `nvidia-cublas` and `nvidia-cudnn-cu13==9.27.0.42` (Azure feed `onnxruntime-cuda-13`) | NVIDIA CC ≥ 7.5, driver branch ≥ R580 |
  | `coreml` | built in, GPU EP | `CoreMLExecutionProvider`, macOS arm64 only | Apple Silicon |
  | `cpu` | built in | `CPUExecutionProvider` | – |

  `trt`, `directml`, `openvino`, `qnn`, `migraphx` and `vitisai` are reserved, each with a reason;
  `openvino` has only a CI test pack. `ort_core` must equal the `onnxruntime` pin;
  `tools/ep_catalog.py --check` fails on drift. A pack outside its tested ORT versions is
  `untested-ort` and stays usable, with one warning line for each process (`trt-rtx` 0.5.0 on ORT 1.31).
- **EP options.** The catalog lists the allowed names and values. Each other option is refused
  ([ADR-NZK1](../decisions/entries/NZK1-ep-options-evidence.md)):

  | EP | Allowed | Default set of `recommend("performance")` |
  |---|---|---|
  | `cuda` | `prefer_nhwc` 0/1, `use_tf32` 0/1, `arena.max_mem` (positive bytes) | `prefer_nhwc=1` for fp16 only |
  | `trt-rtx` | `enable_cuda_graph` 0/1 | EP defaults and a catalog `nv_runtime_cache_path` |
  | `coreml` | `MLComputeUnits` `ALL`, `CPUAndGPU`, `CPUAndNeuralEngine`, `CPUOnly` | EP defaults |
  | `cpu` | none | `ORT_ENABLE_ALL`, default threads |

  `device_id` is refused for each EP: the device comes from the device map. `build_session()` sets
  threads and the graph optimization level as `SessionOptions` attributes, never as session config
  entries.
- **EP store and install** ([ADR-246B](../decisions/entries/246B-ep-catalog-store-and-install.md)).
  The store is `platformdirs.user_data_dir("skellytracker", appauthor=False)/eps`, or
  `SKELLYTRACKER_EP_STORE`, with one folder `<pack_id>/<pack_ver>/` for each pack. `install()` uses the standard library. It downloads only after an
  explicit user action, only `https`, with resume by byte ranges, the system proxy (no PAC file) and
  the system trust store. The sha256 against the lock is the gate. It refuses zip-slip and a path of
  240 characters or more (never `\\?\`), then moves the folder with one `os.replace`.
  `install(plan, from_dir=...)` is "Install from folder". `ensure_registered()` prepends the Windows
  DLL folders of the `cuda` pack to `PATH`, registers the library by path, and checks that
  `get_ep_devices()` holds the catalog `ep_name`.
- **Verification.** L0 present and current, L1 floors from `probe_host()` (the CUDA floor comes from
  the driver branch), L2 registers and lists the device (`spawn` child), L3 a probe Conv+ReLU model
  with each node on the target EP and the output within `l3_atol` of CPU. "Ready" means installed,
  current, registers and lists a device. The verification state only adds one warning line for each
  process ([ADR-D8DH](../decisions/entries/D8DH-sessions-errors-and-the-ready-rule.md)).
- **CLI `skellytracker-eps`** (and the poe task `setup-eps`): `status`, `recommend`, `install`, `verify`, `remove`, `gc`, `download`, `selftest` and `doctor`.
  `status` imports no `onnxruntime` and uses no network; `--json` has the schema
  `skellytracker.eps.status/1`, and `--format ini` is UTF-16LE with a BOM. `install` takes
  `--progress jsonl` and `--cancel-file` for the freemocap installer page. The test pack step of
  `selftest` passes on a host with no Intel device when the pack registers, and its detail says that
  the device list is not checked
  ([ADR-FQ9A](../decisions/entries/FQ9A-selftest-test-pack-on-a-host-with-no-intel-device.md)).
  No environment variable picks the EP or the device. Both CLIs use one exit-code table
  ([ADR-D8DH](../decisions/entries/D8DH-sessions-errors-and-the-ready-rule.md)):

  | Code | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
  |---|---|---|---|---|---|---|---|
  | Meaning | ok | failure | usage, refused key or option | EP not available | session not created | GPU memory exhausted | cancelled |
- **`build_session(model, *, execution_provider, ep_options=None, device_key=None, model_ref=None)`**
  returns the session and its `SessionReport`. `model` is bytes or a path; the NMS session of
  stage 1.10 passes its bytes with `cpu`. The steps: refuse a reserved or unknown key and each
  option that the catalog does not list, before ORT; check the core and the pack state; register;
  set `intra_op_num_threads=1` and `inter_op_num_threads=1` for a GPU EP;
  `session.record_ep_graph_assignment_info=1`; add a plugin EP with `add_provider_for_devices`,
  never `providers=[name]`; create with `enable_fallback=0`; warm up one run; check that the
  requested EP is the first provider and has at least one node. It calls the cached `probe_host()`
  only for a GPU EP ([ADR-9NW0](../decisions/entries/9NW0-ep-keys-options-and-failures.md) items 4
  and 5; [ADR-D8DH](../decisions/entries/D8DH-sessions-errors-and-the-ready-rule.md)).
  `SessionReport` gives the requested and the used EP, the pack, `ort_version`, the device
  (`device_key`, `gpu_uuid`), the sanitized `ep_options`, `artifact_sha256`, `nodes_by_ep`,
  `cpu_nodes`, `cpu_op_types`, `build_ns` and `warmup_ns`. `cpu_nodes` and `cpu_op_types` are a
  stable contract for the fp16 placement check
  ([ADR-EY4F](../decisions/entries/EY4F-acceptance-gate-checks-fp16-gpu-placement.md)).
- **Devices** ([ADR-P1F3](../decisions/entries/P1F3-hardware-probe-devices-and-multi-gpu.md);
  [ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md)). With no
  `device_key`, a session uses the GPU with the most VRAM that the EP lists; on a tie, the lowest
  PCI bus id. `run_devices(execution_provider, device=None)` (proposed name) gives `RunDevice`
  records (`device_key`, `gpu_key`, `name`, `pci_bus_id`, `vram_total_bytes`): the GPUs that pass
  the L1 floors, in that order, restricted by `device`. A `device` that is not such a GPU raises
  `EpUnavailableError`. The GPU set of a run is the GPUs that each GPU EP of its nodes lists. Stage
  1.10 splits the cameras across them and sizes batch k on each GPU from
  `free_vram(device) - vram_reserve_bytes`
  ([ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 4).
- **`recommend(form)`.** `accuracy` gives `cpu` with fp32 on each host. `performance` gives the first
  ready candidate of the first matching hardware class of the catalog, and names each skipped
  candidate with its reason, the device and the source row. NVIDIA CC ≥ 8.0 with R580 gives
  `trt-rtx`, then `cuda`; CC 7.5 with R580 gives `cuda`; below R580 gives `cpu` with a driver update
  offer; Apple Silicon gives `coreml`; each other host, also an NVIDIA GPU older than Turing, gives
  `cpu`. No benchmark runs on the host. `select_precision()` gives the default of
  [ADR-7NY2](../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 10; `coreml` is fp16
  first.
- **`detectors` and `pipelines`.** Their entries carry no EP state; `eps.status()` and
  `eps.recommend()` give it. `eps` gives the start check of
  [ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 7:
  the EP is ready and the catalog allows each option.
- **Errors.** `core/errors.py`: `EpRequestError(ValueError)` (exit 2), `EpUnavailableError` with the
  install hint (exit 3), `SessionCreationError(message, report)` (exit 4) and `VRAMExhaustionError`,
  also a `MemoryError` (exit 5). Each pickles. Stage 1.10 adds `MissingDependencyError`.
- **PyInstaller.** `skellytracker/_pyinstaller/` (outside `core/`) has the `pyinstaller40` entry
  points and a data-only `hook-skellytracker.py` that collects `**/*.yaml`. A metadata read of a
  fixed name is a literal `importlib.metadata.version("<name>")` call.

Ordered steps. Each step is one commit group of one PR. After each step, run
`uv run pytest -m "not video"`, the ruff command and `uv run python tools/run_checks.py`.

| # | Step |
|---|---|
| 1 | Dependencies of the stage; the test markers `gpu`, `ep_pack` and `pyinstaller` |
| 2 | `core/errors.py` |
| 3 | Records and skeletons of `system`, `metrics` and `_hardware`; the guard and freeze tests |
| 4 | Host readers and `probe_host()`, with an evidence entry for their costs |
| 5 | `probe_runtime()`, `probe_environment()`, `probe_loaded_libraries()` |
| 6 | `LiveSampler`, PDH and `free_vram(device)` |
| 7 | Catalog, lock, loader, `eps` records and `tools/ep_catalog.py` with its tests |
| 8 | `recommend()`, `select_precision()` and `run_devices()` |
| 9 | Store, download engine, `install()`, `gc()` and the path guard |
| 10 | `ensure_registered()` |
| 11 | Verification L2 and L3, and the device match |
| 12 | `build_session()` and `SessionReport` |
| 13 | The start check of stage 1.10 |
| 14 | CLI, console script, poe task and the exit-code table |
| 15 | `selftest` and the `ep_pack` CI job (the OpenVINO test pack; CoreML and CPU on macOS) |
| 16 | PyInstaller hook, entry points, fast tests and the slow frozen smoke job |
| 17 | The local GPU gate, with an evidence entry |
| 18 | Docs in ASD-STE100: `README.md`, `GPU_SETUP_GUIDE.md`, `skellytracker/AGENTS.md` |
| 19 | The status of this stage |

Open data (none of it blocks the gate): the full GTX 1650 run on a driver of R580 or later
(informational only); the Linux checks (pack preloads, driver branch rule, proxy and trust store
paths); a two-GPU host; Smart App Control on a Windows host, before 1.11; CoreML fp16 on an Apple
Silicon Mac, before 1.11. [ADR-V9NK](../decisions/entries/V9NK-ep-device-checks-evidence.md) has
the GTX 1650 facts so far.

Gate:

- The default suite passes offline with no GPU: the guard and freeze tests, the host readers on
  fakes, `recommend()` for each hardware class, `run_devices()` on two fake GPUs, the engine on a
  local `http.server` with a `Range` handler, and each CLI exit code. `build_session()` tests on
  generated ONNX models: an option that the catalog does not list, and `device_id`, raise `EpRequestError` before ORT; a missing pack raises
  `EpUnavailableError`; no session is built again on the CPU; a report with the requested EP not
  first or with 0 nodes raises `SessionCreationError`
  ([ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) item 7).
- The `ep_pack` job and the slow PyInstaller job pass. CI runs no real model
  ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 8).
- The local GPU gate on an NVIDIA host with CC ≥ 8.0 and a driver of R580 or later: after
  `skellytracker-eps install`, L3 passes for `cuda` and `trt-rtx`; `eps.build_session()` builds a
  session on each pack, and the node assignment shows the requested EP; each fp16 artifact of
  `yolox-person` and `rtmw-wholebody133` has `cpu_nodes` 0; `run_devices()` and
  `build_session(device_key=...)` work on the one GPU; a frozen smoke app installs `trt-rtx` in a
  fresh store and binds `NvTensorRTRTXExecutionProvider`.

### 1.4 Spec loader (was N1)

**Status: DONE (2026-11-16).** The spec loader `core/model_spec/` is beside the old `core/sidecar/`.
The heading "Not in this stage" gives the stage that owns each item that stays.

Done:

- The package `core/model_spec/` holds the spec loader and the spec model
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 8). The old
  `core/sidecar/` did not change. Stage 2.3 moves the new package to `core/sidecar/`.
- `load_sidecar(path, sidecar_root, user_root)` takes its sidecar root as an argument. It does not
  take the nearest folder named `core`, and it does not follow a symlink.
- `resolve_sidecar_composition` accepts only the `$ref` directive form `{$ref, sha256}`. It checks
  each `$ref` hash before the parse, the bytes of each file and each duplicate key
  (`V-format.composition-1` to `-4` and `-6`).
- `check_schema_version` accepts the SemVer `schema_version` values of
  `IMPLEMENTED_SCHEMA_VERSIONS`: `"2.0.0"`. The error for each other value names the version
  (`V-format.versioning-1` and `V-format.versioning-2`).
- `check_sidecar` checks each other `V-` rule of a sidecar, with the rule ID in each failure. It
  refuses each key that the spec does not define (`V-format.composition-5`). `load_sidecar` gives it
  the path under the sidecar root for `V-common.identity-1`, `-7` and `-8`.
- `SidecarModel` is the typed model at spec version 2.0.0: one `batching.batch` with
  `batching.batch_conversion`, the sidecar vocabulary, no `heatmap` decode, no 3D SimCC decode, typed
  size entries with no merge, `output_shapes`, the `license` block and `keypoint.landmark_schema`.
  The code finds an artifact by its size and its precision.
- The landmark schema registry reads `core/model_zoo/landmark_schemas/` and `landmark_schemas/` of
  the user root. It checks `V-post.keypoint.landmark_schema-1` to `-4` and
  `V-post.keypoint.canonical_mapping-1`. `check_sidecar` checks `V-post.keypoint.schema-10` with it.
  Stage 1.6 gives the user root to `load_sidecar`.
- The check of `V-common.license-3` uses a pinned copy of the SPDX License List 3.29.0
  (`core/model_spec/spdx_license_list.json`).
- The tests are in `skellytracker/tests/model_spec/`. They hold one case or more for each rule ID
  that the loader checks, and each data-only case of the vector files. The cases of
  [`common.identity`](model-sidecar/vectors/common.identity.yaml) go to a temporary sidecar root at
  `input.path`.
- `tools/tests/test_examples.py` validates each reference example with `load_sidecar`. The
  temporary function `resolve` of `tools/sidecar_refs.py` is deleted. The trace tool resolves with
  the package resolver.
- The front matter of each section names the new `validate` function, and the new `load` function
  where the loader does that step. A test checks the line `Implements: <section-id>` of each such
  function.
- Gate: the new validation tests pass, and each reference example validates.

Not in this stage:

- Stage 1.6 does the artifact hash checks (`V-common.sizes_and_artifacts-10`).
- Done in stage 1.10 (2026-11-16): Stage 1.10 does the host load check of `V-pipeline.graph-11`, because it needs the pipeline
  loader ([ADR-TH8E](../decisions/entries/TH8E-one-person-in-v2.md)).
- Stage 1.11 moves the `--write` and `--check` commands of `tools/sidecar_refs.py` into the package.
- The loader does not apply the rules of a decoded keypoint and of a derived point at run time: a
  keypoint with a score `<= 0` or NaN is missing, and a derived point is missing when a source is
  missing ([Keypoint schema](model-sidecar/post/keypoint/schema.md#fields)). The loader checks only
  that the weights of a derived point sum to 1 within `1e-6`. The processing code of stage 1.5 must
  apply these rules.
- `REMOVED_VALUES` in `tools/tests/test_traceability.py` goes at stage 2.3
  ([ADR-9MJ6](../decisions/entries/9MJ6-remove-the-heatmap-decode.md)).
- The section [License and training data](model-sidecar/common/license.md) is `draft`, so the
  `2.0.0` release (stage 2.5) also needs its graduation or its removal from the release.
- The bump of skellytracker to `2.0.0` and the SemVer pattern of `bumpver` in `pyproject.toml` are
  the work of the user. They are not items of this plan.

- **Package sidecars deleted and replaced.** The old package sidecars `yolox`, `rtmw-wholebody`,
  `rtmpose-body`, `rtmpose-hand` and `rtmpose-face` do not migrate to the spec. They are deleted and
  replaced: stage 1.9 and stage 2.2 add the exporter models, and stage 2.1 and stage 2.3 delete the old sidecars
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 1). The old
  `base` of `rtmw_wholebody_to_canonical_mapping.yaml` goes with its sidecar.

### 1.5 Spec processing (was N2)

**Status: DONE (2026-11-16).** The spec processing modules are in `core/detectors/processing/pre/`
and `core/detectors/processing/post/`, beside the old processing modules. The heading "Not in this
stage" gives the stage that owns each item that stays.

Done:

- Each module holds one spec section
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 4). The old
  processing modules and their output did not change. No new module imports the old loader, the old
  processing modules, `core/tracker/` or the old detector contract.
- `pre/preprocess.py` holds the dispatchers. They take the spec model of stage 1.4. `resize_image`
  calls the module of `input.resize.method`. It gives the resized image and a `ResizeGeometry`.
  `preprocess_image` takes a `SidecarModel`, a size and a precision. It gives the CHW tensor of one
  frame, in the `input.dtype` entry of the precision. `resize_inverse` of `post/unprojection.py`
  calls the Inverse of the method of a `ResizeGeometry`. For `affine_crop`, the dispatchers take
  one ROI `(c_x, c_y, w, h, rotation)`.
- **Letterbox rounding.** `pre/resize_letterbox.py` rounds with `half_even` or `half_up`, places
  the image at `top_left` or `center`, and keeps each side at least 1 pixel. It agrees with each of
  the 52 cases of [`pre.resize.letterbox`](model-sidecar/vectors/pre.resize.letterbox.yaml).
- **Stretch unprojection.** `pre/resize_stretch.py` gives the scale factors. Its Inverse applies
  `x * src_w / T_w`.
- **`fit` `pad_value`, and scalar and array pad values.** `fit` of `pre/resize_fit.py` has no
  default `pad_value`. `border_values` of `pre/resize_interpolation.py` expands a scalar pad to
  three values, and accepts an array of int values
  ([ADR-BJF9](../decisions/entries/BJF9-scalar-pad-value-fills-every-channel.md)). The dispatcher
  gives the expanded `pad_value` or `crop_policy.pad_value` to each resize. The image stays BGR
  until the normalization. Thus the dispatcher reverses an array pad for `color_format: rgb`
  ([ADR-XXZ8](../decisions/entries/XXZ8-host-frame-precision-and-score-comparisons.md) item 1).
- **Resize compute dtype.** `to_compute_dtype` casts the 8-bit frame to float32 for
  `compute_dtype: float32`, before the resize and the pad. The canvas and the border keep that
  dtype. No step rounds or clamps the result
  ([ADR-PHJ3](model-sidecar/decisions/entries/PHJ3-resize-compute-dtype.md)).
- **Affine crop matrix in float32.** `pre/resize_affine_crop.py` is the port of the reference:
  `roi_from_box`, `roi_values`, `crop_size`, `warp_points`, `warp_matrix`, `crop_geometry`,
  `affine_crop` and `unproject`
  ([ADR-3S5G](model-sidecar/decisions/entries/3S5G-affine-crop-matrix.md);
  [ADR-G3FA](model-sidecar/decisions/entries/G3FA-affine-crop-rotated-roi.md)). The second warp
  point is left of the centre. The branch with `maintain_aspect_ratio: false` is the branch of the
  reference: the third point is half the crop height from the centre, against the ROI y axis. The
  module does not use the old `get_warp_matrix`. The golden test with the three COCO cases is
  `test_the_affine_crop_matrix_of_the_three_coco_cases_is_the_mmpose_matrix`.
- **Normalization modes, one `imagenet` mode and the cast to the input dtype.** `normalize` of
  `pre/normalize.py` takes the channel order from `input.color_format`, computes each mode in
  float32 and casts the result to the `input.dtype` entry of the precision as the last step
  ([ADR-XH1J](model-sidecar/decisions/entries/XH1J-normalize-input-dtype.md);
  [ADR-90CE](../decisions/entries/90CE-minimal-sidecar-contract.md)). It agrees with each numeric
  case of [`pre.normalize`](model-sidecar/vectors/pre.normalize.yaml) that holds 8-bit or float32
  pixels, also the two `custom` default cases.
- **NMS box area, and the clamp, the size filter and the class filter.** `post/object_decode.py`
  holds the shared steps of
  [Selection behaviour](model-sidecar/post/object/decode.md#selection-behaviour): the score order,
  the class filter, the box format, the clamp, the size filter and the confidence filter.
  `decode_nms` of `post/object_selection_nms.py` runs them in the order of the section. The box
  area adds no `1`, and a tie goes to the lower row
  ([ADR-17KN](../decisions/entries/17KN-one-selection-pipeline.md)).
- **SimCC score without softmax.** `decode_simcc` of `post/keypoint_decode_simcc.py` takes the
  argmax of the raw values, the score `np.where(max_x > max_y, max_y, max_x)`, the bin `-1` for a
  score `<= 0`, and the bin scale from the bin counts
  ([ADR-03PH](model-sidecar/decisions/entries/03PH-simcc-score-rule.md)).
- **Unprojection.** `post/unprojection.py` converts `normalized_01` and `normalized_11` to
  model-input pixels, then applies the Inverse of the resize method, for points and for boxes.
- **Keypoint rules at run time.** `post/keypoint_schema.py` holds the rules that stage 1.4 left.
  `mark_missing` makes a keypoint with a score `<= 0` or a NaN score missing. `derived_points`
  computes each derived point, which is missing when a source is missing
  ([Keypoint schema](model-sidecar/post/keypoint/schema.md#fields)).
- **Precision.** The geometry is float64. The ROI and the warp points of `affine_crop` keep their
  float32 steps. The normalization is float32. The score comparisons are float32
  ([ADR-XXZ8](../decisions/entries/XXZ8-host-frame-precision-and-score-comparisons.md) items 2
  and 3).
- `PACKAGE_RUNNERS` of `tools/tests/test_vectors.py` has an adapter for each new function that runs
  vector cases. Each case that a function agrees with names it in `verified_against`. The old
  entries (`letterbox_preprocess` and `fit_preprocess`) did not change. A change of
  `verified_against` needed no spec content commit: the test vectors are a non-spec change.
- The front matter of each section names the new `forward`, `inverse`, `decode` or `load`
  function. The test of the line `Implements: <section-id>` also covers the new folders.
- The tests of the modules are in `skellytracker/tests/processing/`.
- Gate: the vector cases of the new entries agree. The old entries did not change. The full suite
  passes with no change of expected values.

Not in this stage:

- Part B of stage 1.7 adds the decode of `selection: none` and `selection: top_k`, and the dispatch
  on `object.decode.selection`. `unproject_and_filter` of `post/object_decode.py` gives them shared
  steps 3 to 6. The `decode` step of
  [`post.object.decode`](model-sidecar/post/object/decode.md) is `partial` until then.
- Stage 1.7 reads the output tensors by `semantic` and `fields`, feeds the input dtype to the
  session, and decides the score threshold of the generic keypoint detector. The modules of this
  stage apply only the rule of a missing keypoint. The raw SimCC score has no fixed range, so the
  old `confidence_threshold: 0.004` does not apply to it.
- Two golden tests are not written. They need parity outputs of OpenMMLab-Exporter that this
  repository does not hold: the host tensor of one image of the `yolox-person` parity set
  ([Normalization](model-sidecar/pre/normalization.md#implementer-guidance)), and the mmpose
  scores of one RTMW crop
  ([SimCC decode](model-sidecar/post/keypoint/decode-simcc.md#implementer-guidance)). The model
  gate of stage 1.9 runs the real exports.
- [`pre.resize.stretch.yaml`](model-sidecar/vectors/pre.resize.stretch.yaml) names no package
  function. Three tests of `tools/tests/test_land_fill.py` use the file as their fixture and expect
  no entry on its cases. `skellytracker/tests/processing/test_preprocess.py` runs its numeric cases.
- [`pre.resize.fit.yaml`](model-sidecar/vectors/pre.resize.fit.yaml) keeps `unverified`, and each
  case names the new functions. A vector file has `verified_against` or `unverified` at the top,
  not the two. No exporter ran the cases. At stage 2.3, remove the case-level entries of the old
  functions `fit_preprocess` and `letterbox_preprocess`, with their adapters.
- **Run-time check IDs.** A vector case for a refused tensor or caller argument writes
  `{error: no-rule}`, because no validation rule can check that input
  ([ADR-TA0G](../decisions/entries/TA0G-vector-cases-and-reference-modules.md)). The new modules
  raise `ValueError` with no ID for these inputs. The implementation stage can give these run-time
  checks their own IDs, for example `C-<section-id>-<n>`. A sidecar before `vNEXT` that uses a
  feature that is "Not available." also gives `no-rule`. A rule `V-format.versioning-<n>` can
  replace that use. The user decides both.

### 1.6 Catalog and the `detectors` entry point (was N3)

**Status: DONE (2026-11-16), except the Open items below.** The catalog is
`core/detectors/catalog.py`, and `core/detectors/__init__.py` exports its API. The heading "Open"
gives each item that stays.

Done:

- `list_detectors(user_root)` reads the package root `core/model_zoo/` and the user root. The user
  root is the argument, then `SKELLYTRACKER_USER_ROOT`, then
  `platformdirs.user_data_dir("skellytracker", appauthor=False)` + `/models`
  (`resolve_user_root`; [ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 6).
  `platformdirs` is a direct dependency. `packaging` is also a direct dependency, for the PEP 440
  order. skellytracker keeps no settings file.
- `scan_sidecar_roots` finds the sidecars of each root with the discovery rule
  ([Discovery](model-sidecar/format/file-layout.md#discovery)). It also takes other root folders
  (`other_roots`): a local folder, a folder with one sidecar and its ONNX files, or the top folder of
  a Hugging Face snapshot. It gives the user root to the landmark schema registry
  ([ADR-23F5](../decisions/entries/23F5-landmark-schema-registry.md) item 1). The code calls each
  root a sidecar root.
- The cross-platform tasks. The list holds a CRLF sidecar as unavailable, and the reason names CRLF
  (`V-format.composition-3`). The catalog does not call `Path.resolve()`. A test reads a snapshot of
  symlinks into `blobs/`, and it skips on a host that cannot make a symlink. The docstring of the
  catalog says that each folder name is lower case. A test opens an ONNX file under a long folder
  name with non-ASCII characters with ONNX Runtime.
- Each entry has the category `onnx`, `mediapipe` or `calibration`
  ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 2).
  A sidecar has the key `<model_id>@<source.name>`. An entry with no sidecar has the key
  `<detector_type>@skellytracker`
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 6). The static
  table `STATIC_DETECTORS` holds `mediapipe_pose`, `mediapipe_hand`, `mediapipe_face`, `charuco` and
  `aruco`. The catalog imports no detector module. `keypoint_bbox` and `precomputed` are not in the
  list ([ADR-7NY2](../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 13).
- Each entry has `available` and `unavailable_reason`
  ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 7): the load
  of the sidecar, the capability check, the installed package (`importlib.util.find_spec` with a
  literal name) and the ONNX files. Each artifact of an entry also has `available` and
  `unavailable_reason`, because a user can copy only some sizes or precisions. An `onnx` entry is
  available when one artifact or more is available. From stage 1.7, an artifact with a `url` and no file is
  available, with `downloaded` false
  ([ADR-9E2A](../decisions/entries/9E2A-url-artifact-available-before-download.md)).
- The capability check. `core/model_spec/sections.py` holds the ID, the kind and the selectors of
  each spec section, and `IMPLEMENTED_SECTIONS`: the sections that the package runs. A doc test
  compares the table with the front matter of the section files. `unimplemented_sections` uses
  `normalize` and `applies` of `core/model_spec/sidecar_normalize.py`, which moved from `tools/`
  with no change. The trace tool imports it from the package
  ([ADR-0013](../decisions/entries/0013-spec-structure.md)). `IMPLEMENTED_SECTIONS` holds each
  `format`, `common` and `schema` section. It holds no `preprocessor` or `postprocessor` section.
  Stage 1.5 and stage 1.7 add each such section in the commit that adds its processing module.
  Until then, each sidecar entry is unavailable, and the reason names the sections.
- `load_detector_sidecar(key)` raises `DetectorUnavailableError` for a sidecar that is not usable.
  The message names the section, the version or the rule. `DetectorUnavailableError` and
  `DetectorNotFoundError` are in `core/detectors/catalog.py`. An unknown size is an error
  (`DetectorEntry.artifact`, `SidecarModel.size`). There are no aliases and no claims
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 2).
- The version order, the pins and the reserved name
  ([`common.identity`](model-sidecar/common/identity.md#implementer-guidance)). The newest
  `source.version` of a key wins in PEP 440 order, and the other versions have `superseded`.
  `<key>==<version>` pins a version. Two files with one key and one version but different bytes make
  the entry unavailable, and the reason names both paths. A sidecar with `source.name: skellytracker`
  outside the package root is unavailable. The catalog logs the file that it uses when a key is in
  more than one root. An entry has `key`, `version` and `sidecar_sha256`: the three values of the
  run metadata.
- The artifact hash checks. `check_artifact_hash` in `core/model_spec/artifacts.py` checks a present
  ONNX file against `sha256` (`V-common.sizes_and_artifacts-10`).
- The hash check cache `HashCache`, in the same module. One record for each hashed file: the key is
  the sidecar root and the path relative to that root, and the fields are `size`, `mtime_ns`,
  `file_id`, `sha256` and `checked_at`. The cache file is `hash-cache.json` in the user cache folder
  of `platformdirs`. The write goes to a temporary file, then `os.replace`. A cache file that does
  not parse is an empty cache, with one warning. The argument `full_hash` and the variable
  `SKELLYTRACKER_FULL_HASH=1` force a full hash. `HashCache.record` writes the record of a file whose
  hash the caller knows, with no read. The docstring of the module names the 2 s limit of FAT32 and
  exFAT. The tests cover a hit, each miss, a corrupt cache file, the atomic write, the record of a
  download and the forced full hash. The implementer guidance of
  [`common.sizes_and_artifacts`](model-sidecar/common/sizes-and-artifacts.md#implementer-guidance)
  has one line about the cache.
- `describe_detector(key)`, and the CLI commands `detectors` and `describe <key>` of
  `python -m skellytracker`
  ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 9): the sizes,
  the precisions, the `sidecar_sha256`, the ports, the params with their sidecar defaults (`size`
  and `object_decode`) and the point names.
- Gate: the catalog tests on temporary roots pass (`skellytracker/tests/detectors/`). A test checks
  that each entry of the static table has a known class. The full suite passes with no change of
  expected values.

Open:

- **Hugging Face roots.** The pin, the refresh command and the state "not fetched" are not built
  ([Sidecar roots](model-sidecar/format/file-layout.md#sidecar-roots)). The facts:
  skellytracker keeps no settings file
  ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 6).
  The guidance of [`format.file_layout`](model-sidecar/format/file-layout.md#implementer-guidance)
  says "The config gives the repo id and a commit revision". No text says who holds the pin. The
  public API has no argument for another root: only `scan_sidecar_roots` takes `other_roots`. The
  user decides the design.
- **File locks.** On Windows, a model update or a Hugging Face refresh closes the sessions first, or
  writes the new revision beside the old one. This item goes with the Hugging Face roots.
- **Hash in the Hugging Face cache.** Optional: in the Hugging Face cache, the `blobs/` file name of
  an LFS file is its SHA-256. Compare that name with `sha256` only when it is 64 lowercase hex
  characters. Hash the file in all other cases.
- **Symlink test.** The test of a snapshot of symlinks did not run on the Windows host of this
  stage, because that host cannot make a symlink. Run it on Linux or macOS.
- **Download.** Done in stage 1.7: `ensure_artifact` of `core/detectors/generic/session.py` and
  `download_artifact` of `core/detectors/generic/download.py`.
- **Dispatch.** Done in stage 1.7: `create_detector` of `core/detectors/generic/session.py` maps a
  catalog entry to a generic detector by `role` and `sections` of the entry
  ([`format.versioning`](model-sidecar/format/versioning.md#implementer-guidance)).
- **Run metadata.** Done in stage 1.10 (2026-11-16), as `PipelineRun.models`. Stage 1.10 writes `key`, `version` and `sidecar_sha256` of the entry in the
  output metadata of a run.
- **Static table.** The table names the old MediaPipe classes. The stage that adds the MediaPipe
  Holistic runner to the list adds its row. Stage 2.4 removes the rows of the deleted classes.

### 1.7 Standalone generic detectors (was N4)

**Status: DONE (2026-11-16), except the Open items below.** The generic detectors are in
`core/detectors/generic/`. The heading "Open" gives each item that stays.

Done:

- `GenericObjectDetector` and `GenericKeypointDetector` of Part A below
  ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 6). Each one
  takes a loaded spec model, a size, a precision and a session. It runs the sidecar preprocessing,
  the inference and the postprocessing on a batch of images or crops, with the modules of stage
  1.5. It has no old registry key, no `detector_type`, no old config base and no link to
  `DetectionStageConfig` or `DetectionContext`. It keeps no state between calls. The `onnx_model`
  node of stage 1.10 wraps them.
- `create_detector(key, execution_provider=...)` of `generic/session.py` maps a catalog entry to a
  generic detector by the `role` of the entry. The capability check of the catalog refuses a
  sidecar that uses a section with no processing module (the dispatch item of stage 1.6).
- **The public factory.** Added on 2026-11-16. `create_detector(key, **options)` of
  `core/detectors/factory.py` is the one public factory, and `skellytracker.core.detectors`
  exports it. An `onnx` key goes to `create_detector` of `generic/session.py`, with the same
  arguments. `charuco@skellytracker` and `aruco@skellytracker` give the calibration class, with
  `detect(image)` and `close()`. The charuco option `board` is a `CharucoBoardDefinition` or a
  mapping of its fields. `core/detectors/calibration.py` holds the board model and the public
  calibration helpers that are not detectors ([ADR-KE1C](../decisions/entries/KE1C-one-public-detector-factory.md)).
- `IMPLEMENTED_SECTIONS` of `core/model_spec/sections.py` holds each section, except the four
  sections of `UNIMPLEMENTED_SECTIONS`: `post.object.selection.none`,
  `post.object.selection.top_k`, `post.keypoint.decode.coordinate` and `post.keypoint.bottom_up`.
  Thus an `onnx` entry with `selection: nms` or a `simcc` decode can be available.
- The batch loop is `run_batches` of `generic/inference.py`. It feeds the tensors in the
  `input.dtype` of the precision to the input `input.name`, and it reads each output by its name.
  A session with a fixed batch runs groups of that batch, and zero tensors fill the last group.
  The detectors select the tensors by `semantic` and `fields` (`read_object_outputs`).
- The object detector decodes with `object.decode` of the sidecar, or with the changed block that
  the caller gives. `min_score` of a call replaces `object.decode.min_score`. The detector holds no
  threshold of its own.
- The generic keypoint detector reads `keypoint.estimator_type`
  ([ADR-GKD1](../decisions/entries/GKD1-estimator-type-says-the-crop.md) item 2). A top-down model
  takes one ROI for each image. A `bottom_up` model takes the full image. It has no score
  threshold: it applies only the rule of a missing keypoint, and it computes the derived points
  ([Decoded keypoints](model-sidecar/post/keypoint/schema.md#decoded-keypoints)). The `onnx_model`
  node has no param for a keypoint threshold
  ([ONNX model node](pipeline/nodes/onnx_model.md#fields)).
- `overlay_groups` and `overlay_edges` of `generic/overlay.py` group the edges for drawing from
  `keypoint.overlay` (`skeleton`, `parts`, the colors and the thickness) and `keypoint.skeletons`.
  The old `resolve_overlay_groups` stays until stage 2.3.
- `model_batch_convert` of `generic/batch_conversion.py` makes the generated artifact of
  `static-batch-v1` in memory. It also refuses external data in the `indices` of a sparse
  initializer. `open_session(entry, sidecar, size, precision, execution_provider=..., batch=...)`
  of `generic/session.py` converts at session start when `batch` is not `batching.batch`. Stage
  1.10 calls it. `core/tracker/`, `DetectionStage.run_batch`, `test_run_batched.py` and the old
  `core/sessions/batch_conversion.py` did not change.
- The session comes from `eps.build_session()`, with the execution provider as
  `execution_provider`.
- The download of a `url` artifact, when a session needs a file that is not present
  (`ensure_artifact`, `download_artifact` of `generic/download.py`). The file goes to
  `platformdirs.user_cache_dir("skellytracker", appauthor=False)/models/<key>/<version>/<filename>`
  (`download_path` of `core/model_spec/artifacts.py`). `fetch` of `core/eps/_download.py` gets the
  bytes, with its retries and its resume, and checks `url_sha256`. The host extracts the one ONNX
  file of a zip archive and hashes it while it writes it. It checks `sha256`, moves the file into
  place with `os.replace` and calls `HashCache.record`. The catalog reads a downloaded file from
  that folder.
- The availability rule of the catalog for a `url` artifact. A `url` artifact that is not
  downloaded is available, and `ArtifactEntry.downloaded` is false. An artifact with no `url` and
  no file stays unavailable
  ([ADR-9E2A](../decisions/entries/9E2A-url-artifact-available-before-download.md)).
- `close()` of a detector releases the session. A `detect` call that runs on an other thread keeps
  its own reference to the session and ends normally. A later call raises `RuntimeError`.
- The detector tests on generated ONNX models
  ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 8):
  `test_generic_detectors.py`, `test_generic_batch_conversion.py` and `test_generic_download.py`
  in `skellytracker/tests/detectors/`. `onnx.helper` makes tiny batch-3 models at run time
  (`onnx_models.py`), with a sidecar in a temporary root. The tests cover the loader, the catalog,
  the generic detectors, the batch loop, the batch conversion, the decode, the overlay, the
  download, calls from more than one thread and a `close()` in a `detect` call. They run no real
  model, and a fake replaces the network.
- Three catalog tests of stage 1.6 changed their sidecar: an `nms` sidecar is not unavailable now,
  so they use the `top_k` sidecar for the capability check.
- The front matter of `common.batch_conversion`, `common.outputs`, `common.sizes_and_artifacts`,
  `post.keypoint.overlay`, `post.object.outputs` and `post.object.decode` names the new functions.
- Gate: the detector tests pass on Windows. The existing tests pass with no change of expected
  values, also the old tests and the video tests.

Open:

- **`selection: none` and `selection: top_k` (Part B): blocked.** These decodes are not written.
  Step 3 of the skill
  [`implement-sidecar-section`](../.claude/skills/implement-sidecar-section/SKILL.md) blocks each
  one, because the three conditions are true:
  - no reference example uses the section
    ([Models and sections](model-sidecar/TRACEABILITY.md#models-and-sections));
  - [`post.object.selection.none.yaml`](model-sidecar/vectors/post.object.selection.none.yaml) and
    [`post.object.selection.top_k.yaml`](model-sidecar/vectors/post.object.selection.top_k.yaml)
    are `unverified`;
  - `specs/model-sidecar/reference/` has no module for them.

  Part B also asks for a real export for each new decode path. No export that this repository can
  read uses these modes. An exporter must give a reference implementation or a reference example
  first, through the model addition workflow. Then a later stage writes the decode and removes the
  section from `UNIMPLEMENTED_SECTIONS`. Until then, the catalog lists such a sidecar as
  unavailable, and the reason names the section. The `decode` step of
  [`post.object.decode`](model-sidecar/post/object/decode.md) stays `partial`.
- **`post.keypoint.decode.coordinate` and `post.keypoint.bottom_up`: blocked.** The same step
  blocks them: no reference example, no vector file and no reference module. A model with both
  roles has no generic detector. An exporter must give a reference implementation or a reference
  example first, for example with a one-stage pose model or a model with a `keypoint_coordinates`
  output. The two first models of stage 1.9 and the RTMPose models of stage 2.2 do not use these
  sections.
- **Cache of generated artifacts: no cache.** The host keeps no generated artifact. Each session
  start with an other batch converts again, in memory. The conversion takes at most about 1 s,
  against a session start of 0.3 s to 4.8 s
  ([ADR-GPW6](../decisions/entries/GPW6-model-gate-of-the-first-models.md) items 9 and 10). Examine
  the cache again only on a new measurement.
- **`close()` in a pipeline run.** Done in stage 1.10 (2026-11-16): `PipelineRun.close()` waits for the call that runs. `close()` of a detector does not wait for a `detect` call that
  runs. `PipelineRun.close()` of stage 1.10 must wait for the calls or stop them, and it decides
  the lock design.
- **Two downloads of one artifact.** Done in stage 1.10 (2026-11-16): `download_lock` of `core/detectors/generic/download.py`. Two threads or two processes that start a session for the same
  `url` artifact can download it at the same time. They write the same `.part` file, so one
  download can fail. Stage 1.10 decides the lock, with the file locks of stage 1.6.
- **The extra `onnx`.** `model_batch_convert` needs the `onnx` package, which is an extra. A host
  without it runs a b3 artifact only at batch 3. The tests of the generic detectors skip without
  it.
- **Operating systems.** The detector tests ran only on Windows. CI runs them on Linux and macOS.
- **Real exports.** No test of this stage runs a real export. Stage 1.9 runs `yolox-person` and
  `rtmw-wholebody133` at the detector level.
- **Stale guidance.** The implementer guidance of `common.batch_conversion`,
  `common.sizes_and_artifacts` and `format.versioning` still names the old code. A guidance edit
  is a spec edit of its own.

**Goal.** The generic detectors are the re-implementation of the package ONNX detectors
([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md)). A new model needs its
sidecar and its ONNX files, and no new Python, when its sidecar uses only the preprocessing and the
decode that the package implements.

**Removed from this milestone.** These parts of the earlier text go
([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md);
[ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 6):

- the generic config in the `TrackerConfig` union. The pipeline config replaces `TrackerConfig`;
- the fill of the old registries `OBJECT_DETECTOR_REGISTRY` and `KEYPOINT_DETECTOR_REGISTRY`;
- the coexistence of a hand-written detector with the generic detector, and the claim of a catalog
  key;
- the YOLOX gap (the raw-anchor-grid decode and the graph surgery of `prepare_yolox_onnx`). The
  `yolox-person` export has no NMS in the graph and uses host `selection: nms`. Stage 2.1 deletes the old
  YOLOX.

**Part A — Generic detectors:**

- Add `GenericObjectDetector` and `GenericKeypointDetector` in `core/detectors/generic/`. A loaded
  spec model, a size, a precision and a session give all their parameters. They use the new modules
  of `processing/pre/` and `processing/post/` (stage 1.5). Stage 1.7 gives their scope.
- A sidecar that uses a section that the package does not implement is unavailable in the catalog
  (the capability check of 1.6). It does not fail at run time.

**Part B — Fill decode/preprocess coverage gaps:**

Stages [1.4](#14-spec-loader-was-n1) and [1.5](#15-spec-processing-was-n2) list the known package gaps ([ADR-5WKW](../decisions/entries/5WKW-implementation-work-in-the-plan.md)). The spec also shows the gaps in these places:

- the `validate:` and `load:` notes in the front matter of each section file, and [`TRACEABILITY.md`](model-sidecar/TRACEABILITY.md);
- the skill [`implement-sidecar-section`](../.claude/skills/implement-sidecar-section/SKILL.md), which gives the steps and the order of the work.

Two rules of this part stay:

- The sidecar `object.decode` and `keypoint.decode` fields must control the decode. A detector config must not hold its own thresholds and limits (the known gap under M3).
- Test each new decode path with a real export: a sidecar, its ONNX file and an upstream reference output from the exporter. A spec reference example is never a test input, because it has no ONNX file. New decode math has no earlier output to compare with, so compare it with the output of the upstream library. CI tests the same path on generated ONNX models.

### 1.8 MediaPipe Holistic runner

**Status: DONE (2026-11-16).** This stage is new ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 4). It needs only 1.1 and 1.2, so it can run
in parallel with 1.3 to 1.7. The runner `HolisticRunner` is in `core/detectors/mediapipe_holistic.py`.
The runner and the old MediaPipe detectors close their landmarkers from the garbage collector on a
new thread ([ADR-X6S9](../decisions/entries/X6S9-mediapipe-close-from-the-garbage-collector.md)).
The runner gives the score 1.0 to a found hand or face point, which has no MediaPipe visibility,
and a present row when Holistic finds at least one part
([ADR-Y7C3](pipeline/decisions/entries/Y7C3-mediapipe-score-without-visibility-and-holistic-present-row.md)).

- A standalone module under `core/detectors/` runs the MediaPipe Tasks `HolisticLandmarker`.
  MediaPipe 1.2.2 has `mediapipe/tasks/python/vision/holistic_landmarker.py`. The module does not use
  the old MediaPipe detector classes, the old detector contract or `core/tracker/`. The
  `mediapipe_tasks` node of 1.10 wraps it ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 4).
- It gives the outputs and the point names of the `holistic` variant of
  [`mediapipe_tasks`](pipeline/nodes/mediapipe_tasks.md). Holistic is single person, so
  `max_instances` is 1. The output has `geometry: 3d` and `depth_unit: pixel` ([ADR-6DKT](pipeline/decisions/entries/6DKT-instance-rows-carry-class-and-score.md) item 6). In
  v2 it has no ROI input and no face blendshapes.
- In `VIDEO` mode it takes the `timestamp_ms` of each frame, which must increase. It has no reset
  and no back-off ([ADR-6JWJ](pipeline/decisions/entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md)).
- **MediaPipe timestamps and landmarkers on Windows.** On Windows with Python 3.11 or 3.12, the fast
  suite can hang. The cause is the Python timer, not MediaPipe: `time.monotonic()` uses
  `GetTickCount64()` there, with steps of about 16 ms. The MediaPipe detectors use
  `int(time.monotonic() * 1000)` as the timestamp when the caller gives no `timestamp_ms`. Two
  frames can then get the same millisecond timestamp, and MediaPipe raises "Input timestamp must be
  monotonically increasing". A landmarker that the test does not close is then garbage-collected
  later, and its `close()` can hang. Python 3.13 uses a finer clock
  ([ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) item 4). Make the timestamp fallback
  increase on each call. Make the detectors close their landmarkers safely, also when the garbage
  collector frees them. Put the same fix in the runner. Do not change the
  MediaPipe tests to close their detectors or to add teardown. These tests show the defect when it
  comes back ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 9).
- The `body`, `hand` and `face` variants can be in the same module, or come in 1.10.
- Gate: on a test image and a test video, the runner gives the expected point sets (body, both
  hands, face). The MediaPipe tests pass with no change of expected values.

### 1.9 The first new models (was N5)

**Status: DONE (2026-11-16), except the Open items below.** This stage replaces M10a and M10b. The
two first models are in `core/model_zoo/`, and they pass the model gate at the detector level
([ADR-GPW6](../decisions/entries/GPW6-model-gate-of-the-first-models.md)).

Done:

- The sidecars `yolox-person` and `rtmw-wholebody133` of OpenMMLab-Exporter are in
  `core/model_zoo/detectors/`, each as a byte copy of its reference example
  ([`yolox-person.yaml`](model-sidecar/examples/detectors/object_detectors/yolox-person/yolox-person.yaml),
  [`rtmw-wholebody133.yaml`](model-sidecar/examples/detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133.yaml)).
  The keys are `yolox-person@openmmlab-exporter` and `rtmw-wholebody133@openmmlab-exporter`
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) items 1, 5 and 6). The
  old keys `rtmpose` and `yolox_person` and the old `model_name` values have no alias (item 2).
- The ONNX files go beside the sidecars, by hand: the 22 published b3 files of `exports/` of a
  checkout of OpenMMLab-Exporter. Git does not track them. Each file has the `sha256` of its
  sidecar. A checkout with no ONNX file lists the two models as unavailable.
- `skellytracker/tests/detectors/test_model_zoo.py` loads each package sidecar and builds each
  detector by its catalog key for one frame, on the CPU EP. It skips a model with no ONNX file, so
  CI runs only the load test. The catalog tests of stage 1.6 scan no package root now.
- The sizes. `yolox-person` has `n`, `t`, `s`, `m`, `l` and `x`: the six HumanArt checkpoints
  `yolox_<size>_8xb8-300e_humanart`. `t` and `m` are the old `yolox-tiny` and `yolox-m`.
  `rtmw-wholebody133` has five sizes, from the mmpose 1.3.2 `cocktail14` configs:

  | Size key | Checkpoint | Old `model_name` |
  |---|---|---|
  | `m` | `rtmw-dw-l-m_simcc-cocktail14_270e-256x192-20231122` | `rtmw-l-m_256x192` |
  | `l-256` | `rtmw-dw-x-l_simcc-cocktail14_270e-256x192-20231122` | `rtmw-x-l_256x192` |
  | `x-256` | `rtmw-x_simcc-cocktail14_pt-ucoco_270e-256x192-13a2546d_20231208` | none |
  | `l-384` | `rtmw-dw-x-l_simcc-cocktail14_270e-384x288-20231122` | `rtmw-x-l_384x288` |
  | `x-384` | `rtmw-x_simcc-cocktail14_pt-ucoco_270e-384x288-f840f204_20231122` | none |

  The size key names the student model. `rtmw-dw-l-m` is the `m` model with the `l` model as its
  distillation teacher. The source of the table is `rtmw/identity.py` of OpenMMLab-Exporter and
  the `url` values of the old package sidecar.
- The RTMW model input changes. The old package sidecar declares `imagenet_bgr`, and the old code
  puts the B, G and R channels of the frame in tensor positions 0, 1 and 2. The export declares
  `normalization: imagenet` with `color_format: rgb`, which puts R, G and B there
  ([Normalization modes](model-sidecar/pre/normalization.md#behaviour)). The canonical mapping of
  `rtmw-wholebody133` is the `canonical_mapping` of
  `core/model_zoo/landmark_schemas/COCO_WholeBody.yaml`
  ([ADR-23F5](../decisions/entries/23F5-landmark-schema-registry.md)).
- The model gate (step 5 of the
  [acceptance gate](../.claude/skills/implement-sidecar-section/proposal-gate.md)) ran locally, at
  the detector level, against the upstream reference output of the exporter. It did not use the old
  golden fixtures. Each gate passes: each size, fp32 and fp16 on the CPU EP, and fp16 on `cuda` and
  `trt-rtx`, with 0 nodes on the CPU EP for each fp16 file
  ([ADR-GPW6](../decisions/entries/GPW6-model-gate-of-the-first-models.md) items 2 to 7).
- The two golden tests of stage 1.5 ran in that gate, on each image and each person of the parity
  sets: the host tensor of `yolox-person` (difference 0), and the SimCC decode against the mmpose
  scores (equal bit for bit). They are in the script of the entry, not in the test suite, because
  the repository does not hold the parity outputs.
- The batch conversion at session start takes 0.01 s to 1.02 s for a file, about 0.25 s for each
  100 MB. `create_detector` takes 0.3 s to 2.6 s with the batch of the sidecar, and at most 4.8 s
  with batch 1 on `trt-rtx`
  ([ADR-GPW6](../decisions/entries/GPW6-model-gate-of-the-first-models.md) items 9 and 10).
- Stage 1.9 wrote no Python pipeline builders
  ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 6). Stage 1.10
  adds the pipeline files.
- The trace tool scans `core/model_zoo/detectors/`, and not `core/model_zoo/landmark_schemas/`. A
  package sidecar with the key of a reference example must have the bytes of that example. The two
  files are one model with the root `example, package` in
  [`TRACEABILITY.md`](model-sidecar/TRACEABILITY.md#models). Different bytes are an error that names
  the two files. The two package sidecars need no new derivation in the normalization table.
- No response is written. [ADR-GPW6](../decisions/entries/GPW6-model-gate-of-the-first-models.md)
  is the record: the two `model` bundles are `landed`, and the path of a `model` bundle in
  [States](model-sidecar/model-addition-workflow/hand-over.md#states) ("`submitted` ->
  `needs-contributor` or `waiting` -> `landed`") has no step from `landed` to `verified`.
- No cache of generated artifacts
  ([stage 1.7](#17-standalone-generic-detectors-was-n4), Open).
- Gate: the model gate passes locally. The old detectors and their tests did not change, and they
  pass, also the video tests.

Open:

- **Golden tests and the `parity/` folder.** The two golden tests ran in
  `decisions/scripts/gpw6_first_models_gate.py`. They are not in the test suite. A tracked fixture
  needs a file with a clear license. The user decides. No bundle has a `parity/` folder. The gate
  used the worker files of the exporter in its local hand-over folder, checked by the SHA-256
  values of the intake. The
  [acceptance gate](../.claude/skills/implement-sidecar-section/proposal-gate.md) (step 5) gives
  `needs-contributor` to a bundle with no reference output. The user decides if the check by the
  hashes is sufficient.
- **Operating systems and CI.** The gate ran only on Windows. CI holds no ONNX file, so no CI job
  runs a real export.
- **Export error on `trt-rtx`.** The raw SimCC difference from the upstream output is larger on
  `trt-rtx` than on `cuda`, up to 1.47 for `x-384` fp16
  ([ADR-GPW6](../decisions/entries/GPW6-model-gate-of-the-first-models.md) item 8). The measured
  gate of the exporter still passes.

### 1.10 The pipeline API (was P)

**Status: DONE (2026-11-16), except the Open items below.** It needs 1.3 (`eps.build_session()`), 1.7, 1.8, 1.9 and the pipeline spec
([`specs/pipeline/`](pipeline/README.md)). It builds `core/pipelines/` and
`core/pipelines/_runtime/` beside the old `core/tracker/`. The old run code does not change
([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 1).

Done:

- `core/pipelines/` has the config model, the loading, the export, the catalog, the load checks,
  the executor, the eleven node types, the sessions, the warnings, the timing, the taps,
  `set_params`, `to_canonical`, the annotator `annotate`, and the commands `run`, `validate` and
  `nodes`. The two built-ins are in `core/model_zoo/pipelines/`.
- The gate ran on the Windows test host: `tools/run_checks.py` passes, and the video tests pass.
  The tests of `tests/pipelines/` cover each part of the gate list. The
  package glue nodes pass the glue vectors. The aggregator output passes
  `skellybench.schema.validate_timing`, in a run with skellybench installed for that run. The
  built-in `yolox-rtmw-wholebody` runs with the real models on the CPU EP, `cuda` and `trt-rtx`.
- Parity test A passes on each of the 200 frames of the fixture. Report B ran on the CPU EP and on
  `cuda` ([ADR-7E4Z](../decisions/entries/7E4Z-box-parity-of-the-built-in-with-sfn26.md)).
- The typed error of a refused call is `CallRefusedError`. A call on a closed run raises
  `RunClosedError`. Each run has one lock: the calls on one run are serial, and `close()` waits for
  the call that runs. The user confirmed the names on 2026-11-16
  ([ADR-0YNA](../decisions/entries/0YNA-public-names-standard-and-four-renames.md)). The thread
  rules are in [Running](pipeline/running.md#behaviour) item 12 ([ADR-75K2](../decisions/entries/75K2-unclear-places-of-the-pipeline-spec.md) item 5).
- `check_pipeline` gives the load warnings and `needs_execution_provider`, in a `PipelineCheck`.
  `PipelineEntry` also has `needs_execution_provider`. The user confirmed these names on 2026-11-16
  ([ADR-0YNA](../decisions/entries/0YNA-public-names-standard-and-four-renames.md)).

Open:

- **Batch k.** In 2.0.0, k is 1 on each GPU, and the run uses `vram_reserve_bytes` only in the
  weights of the camera split ([Running](pipeline/running.md#behaviour) item 4; [ADR-75K2](../decisions/entries/75K2-unclear-places-of-the-pipeline-spec.md) item 1). A
  later version lets a `video` or `image` call carry k frames for each camera (user, question K2 of
  2026-11-16: agreed, after 2.0.0). k for each GPU then comes from
  `k = min(k_max, floor((F − R − Q) / P))`. `F` is the free VRAM at start. `R` is the VRAM reserve.
  `P` is the VRAM of the sessions whose batch grows with k. `Q` is the VRAM of the other sessions.
  A build at k = 1 measures `P` and `Q`. This work first needs a VRAM measurement on `cuda` and on
  `trt-rtx` at several batches.
- **Cameras on two or more GPUs.** The split by VRAM of
  [ADR-AMF7](../decisions/entries/AMF7-camera-split-by-vram.md) is built and has tests on fake
  GPUs. No run on a host with two GPUs verified it. The timing header does not record the cameras
  of each GPU.
- **NMS.** The decode of stage 1.5 does NMS in NumPy. The node has no ONNX `NonMaxSuppression`
  session, so the text of the item "`onnx_model` node" and of
  [ADR-9NW0](../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 7 does not describe
  the code.
- **Timing names.** [Timing](pipeline/timing.md#fields) does not fix the form of `batching`, and
  the rules of the aggregator for `images_per_second` and for two model nodes.
- **Run gate of a pipeline bundle.** `verify` runs the load checks. The run gate and its tolerance
  are not built: no text gives the files of `run/`, the comparison or the tolerance, and
  [ADR-AD33](../decisions/entries/AD33-bundles-are-untrusted-input.md) item 4 lets the session run
  an ONNX file of a bundle only in `batch`.
- **Other port types.** A start refuses an output or a tap of the port type `image` or `tensor`,
  and a tap of a `3d` keypoints port. Their values and file forms are not fixed.
- **Taps.** `V-pipeline.taps-4` checks only that each line names an image of the run, because a
  padding row has no line. A replay compares the `used_ep` of the tap with the requested EP of a
  node that does not run. The COCO fields of a line that no text fixes follow the COCO result form,
  with the point score as the third number of a keypoint.
- **Export.** The resolved export does not write the `object.decode` fields of the sidecar. The
  export as written adds `sidecar_sha256`.
- **The reference model.** `core/pipelines/config.py` has the code of
  `specs/pipeline/reference/pipeline_config.py`, and the reference file stays, because the spec
  text and `tools/make_pipeline_schema.py` name it. A doc test keeps the schema of the package
  model equal to the committed schema.
- **Webcam demo.** `python -m skellytracker --pipeline <key>` runs the new path. With no
  `--pipeline`, the command runs the old demo. The user decides when the default changes.
- **Models that the package does not run.** A load refuses a `bottom_up` model, a model with both
  roles and a selection mode that is not `nms`.
- **Investigations.** The VRAM cost of two runs that overlap, the frame drops in `live` and
  MediaPipe LIVE_STREAM are not measured.
- **Operating systems and CI.** The gate ran only on Windows. CI holds no ONNX file, so the tests
  of the built-in with the real models skip in CI. The demo did not run on a camera.

The items of the stage:

This stage implements the node types of the pipeline spec. Use the skill
[`implement-pipeline-node`](../.claude/skills/implement-pipeline-node/SKILL.md) for each node type
([ADR-Y753](../decisions/entries/Y753-pipeline-templates-glue-vectors-and-taps-flag.md) item 2).

- **Config.** Move `PipelineConfig` and the node configs, with the union keyed on `type`, from
  `specs/pipeline/reference/pipeline_config.py` into `core/pipelines/config.py`. Add a doc test that
  checks that the committed `specs/pipeline/pipeline.schema.json` agrees
  ([ADR-3SF2](../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 3). Add load,
  export and the load checks
  ([ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 7). The export writes only the
  params that a config sets, so that a written config validates again
  ([ADR-97X9](../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) item 10). Each file has the
  required `source:` field, and its key is `<pipeline_id>@<source.name>`
  ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 2). Pipelines use
  the sidecar catalog key rules: the newest version wins, `<key>==<version>` pins, and
  `skellytracker` is reserved ([ADR-88WQ](../decisions/entries/88WQ-sidecar-vocabulary.md) item 7).
- **Discovery.** Read `*.pipeline.yaml` in `core/model_zoo/pipelines/` and in
  `<user root>/pipelines/` ([ADR-7NY2](../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md)
  item 2). `list_pipelines()` gives the load result, the availability and the warnings.
- **Executor.** The executor of `_runtime/` has these parts
  ([ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md)):
  - the DAG order and `@prev`;
  - the empty-input rule: an empty required input stops a node, and an empty optional input does
    not ([Graph](pipeline/graph.md#behaviour));
  - the instance rows, with point names `<group>/<point>`, and the `groups` and `canonical_names`
    of the output schema ([Graph](pipeline/graph.md#behaviour) item 7;
    [Outputs](pipeline/outputs.md#fields);
    [ADR-4MP6](../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md));
  - the running modes `image`, `video` and `live`;
  - the batch: `video` and `image` batch to k × cameras, `live` batches to the camera count, and a
    node that takes ROIs batches to that batch × the `I` of its instance source. `start_pipeline`
    takes `camera_ids`;
  - the batch conversion of each artifact at start, and the padding of a missed frame or crop, with
    its result dropped;
  - the batch rule of a stateful pipeline and its warning `batch_limited_by_state`;
  - the session sharing inside one run: the nodes with the same artifact SHA-256, batch, EP key, EP
    options and device share one session; no session is shared between runs ([ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 6);
  - `node_ran` in the result of each camera, a `dict[str, bool]` with one key for each inference
    node: true when the node did an inference on the frame of that camera in this call, also with
    `timing` off ([Outputs](pipeline/outputs.md#behaviour) item 8, `V-pipeline.outputs-3`;
    [ADR-Q5BN](../decisions/entries/Q5BN-node-ran-in-the-camera-result.md)).
- **Time.** Each output, timing event and tap row has `frame_index`. The `timestamp_ms` of a frame
  (a float), its `video` fallback with the run parameter `fps` (default 30.0) and the `live` rule
  are in [Running](pipeline/running.md#behaviour) item 2. Give the typed error of a refused call a name
  in the API ([Running](pipeline/running.md#behaviour);
  [ADR-97X9](../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) item 9).
- **`onnx_model` node.** The node type `onnx_model` was `detector` ([ADR-9PDQ](../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 1). It wraps the generic detectors of stage 1.7. A node with a top-down keypoint model
  has a `rois` input. A node with a `bottom_up` model or an object detector has no `rois` input
  ([ADR-GKD1](../decisions/entries/GKD1-estimator-type-says-the-crop.md) item 4). Its decode param
  is `object_decode` ([ADR-88WQ](../decisions/entries/88WQ-sidecar-vocabulary.md) item 7). NMS is an
  ONNX `NonMaxSuppression` graph on the CPU provider, with `max_output_boxes_per_class` `2**31-1`,
  in the new `processing/post/` decode of stage 1.5. `post_nms_top_k` applies to the final rows
  ([ADR-7NY2](../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 9). The gate is
  [`post.object.selection.nms`](model-sidecar/vectors/post.object.selection.nms.yaml).
- **Class and instance score.** A `detections` value has `class_index` `(I,)`, with -1 for a
  padding row. The output schema and `tap.json` give `class_names`, the `object.classes` of the
  model. Each `keypoints` and `roi` value has `instance_score` `(I,)`. The instance source sets it:
  the detection score of the row, or 1.0 from `mediapipe_tasks`. Each other node copies it from its
  input row, and `merge` copies it from its `target` input. A row that a node keeps from `@prev`
  keeps its score. A padding row has 0
  ([ADR-6DKT](pipeline/decisions/entries/6DKT-instance-rows-carry-class-and-score.md) items 1 and 2).
- **Canonical form.** `to_canonical(keypoints_value, output_schema)` in `core/pipelines/` gives
  `names` (the `canonical_names` of the output schema), `xy` `(I, C, 2)`, `z` `(I, C)` only for a `3d` output, `score` `(I, C)` and the
  passthrough groups as `{name, start, count, landmark_schema}` in the canonical columns. It applies
  [Canonical mapping](model-sidecar/post/keypoint/canonical-mapping.md#behaviour) to the groups of
  each node or slot. The groups of one schema with two or more groups come from one node. A group of
  a schema with one group stands alone. No pipeline param selects the form
  ([ADR-4MP6](../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md) item 7). Test
  it on `COCO_WholeBody`: 137 names, `feet` gives no column, and a missing `left_hip` makes
  `hips_center` missing.
- **`mediapipe_tasks` node.** One node with `variant: body | hand | face | holistic`. It wraps the
  Holistic runner of 1.8, with its timestamp fix and its safe close, and calls the Tasks
  landmarkers directly for the other variants. It uses the MediaPipe assets ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 4). Its
  params are `min_detection_score`, `min_presence_score`, `min_tracking_score` and `size`
  ([ADR-88WQ](../decisions/entries/88WQ-sidecar-vocabulary.md) item 7). It has no reset and no back-off ([ADR-6JWJ](pipeline/decisions/entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md)).
  Holistic is single person, so its `max_instances` is 1. Its output has `geometry: 3d` and
  `depth_unit: pixel` ([ADR-6DKT](pipeline/decisions/entries/6DKT-instance-rows-carry-class-and-score.md) item 6). In v2 it has no ROI input and no face blendshapes.
  It makes the groups of [MediaPipe Tasks](pipeline/nodes/mediapipe_tasks.md#behaviour), each with
  a null `landmark_schema` until stage 2.2
  ([ADR-4MP6](../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md) item 2).
- **Glue nodes.** `roi_from_points`, `roi_hold`, `gate`, `first_of`, `concat`, `merge`,
  `smooth_keypoints`, `smooth_roi` and `redetect_trigger`
  ([ADR-7NY2](../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6). The node type
  `roi_hold` was `roi_tracking`, and `redetect_trigger` was `redetect`
  ([ADR-9PDQ](../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 2).
  - [`merge`](pipeline/nodes/merge.md) takes `target` keypoints and `source` keypoints of any
    instance source, with one group. The assignment of the source rows to the slots has the most
    pairs, then the smallest total anchor distance, within the required `max_distance`. A slot with
    the name of a target group replaces it through the canonical names; another slot adds a group.
    `map` then replaces single target points
    ([ADR-KW76](../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md)).
  - [`concat`](pipeline/nodes/concat.md) never replaces a point. An empty input does not stop it.
    The columns of that input are missing points: x, y and z are NaN, and the score is 0
    ([ADR-6DKT](pipeline/decisions/entries/6DKT-instance-rows-carry-class-and-score.md) item 5).
  - `smooth_keypoints` refuses a timestamp that does not increase. It has `reset_after_ms` and no
    miss counter.
  - [`roi_from_points`](pipeline/nodes/roi_from_points.md) takes an empty `points`: it then uses
    each present point of the input. It has the optional inputs `previous_rois` and
    `reference_rois`, and the size floors `min_previous_ratio`, `min_reference_ratio` and
    `min_size_px` of its step 10 ([ADR-RA0E](../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) items 2 and 3).
  - [`redetect_trigger`](pipeline/nodes/redetect_trigger.md) has the check `roi_missing`
    ([ADR-RA0E](../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 4).
  - [`smooth_roi`](pipeline/nodes/smooth_roi.md) has the filters `ema` and `one_euro`. The filter
    `one_euro` acts on the two corners, uses `timestamp_ms`, starts again after a gap of more than
    `reset_after_ms`, and clears the state of a row that is not present
    ([ADR-RA0E](../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 5).
- **Sessions.** Build each ONNX session with `eps.build_session()`
  ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 5). `start_pipeline` takes `execution_provider=None`, `ep_options`, `device` and `vram_reserve_bytes`, and checks `V-pipeline.running-8` and `V-pipeline.running-9` ([ADR-9PDQ](../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 4). An `onnx_model` node takes
  `execution_provider` and `ep_options` ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 1; [ADR-9NW0](../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 2). The NMS session
  requests `cpu` ([ADR-9NW0](../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 7). The timing `execution` block gives `cpu_nodes` and
  `cpu_op_types` ([ADR-9NW0](../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 5).
- **Warnings.** `PipelineWarning`, `PipelineRun.warnings`, `on_warning` and `MissingDependencyError`
  ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) items 6 and 7). The warning `ep_partial_placement` fires one time for each session
  with nodes on the CPU EP ([ADR-9NW0](../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 5).
- **Timing.** The timing events, the header, the derive helpers and the skellybench aggregator in
  `core/pipelines/timing.py` ([ADR-Q59W](../decisions/entries/Q59W-pipeline-timing-and-taps.md)
  items 1 to 4; [ADR-0WTV](../decisions/entries/0WTV-system-metrics-and-pipeline-timing-helper.md)
  item 2).
- **Taps.** The tap actions `record` and `replay`
  ([ADR-Q59W](../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 5). Each JSONL line has
  `row`, its row index. A `detections.jsonl` line writes `class`, the class name, in place of
  `category_id`. A `keypoints.jsonl` line and an `roi.jsonl` line write `score`, the
  `instance_score` of the row. A tap applies no rescoring. A replay puts each line in its row, and
  refuses a bad `row` (`V-pipeline.taps-6`) and an unknown `class` (`V-pipeline.taps-7`)
  ([ADR-6DKT](pipeline/decisions/entries/6DKT-instance-rows-carry-class-and-score.md) items 3
  and 4).
- **Other port types.** The value of an output or a tap of the port type `image` or `tensor` is not
  fixed ([Outputs](pipeline/outputs.md#behaviour)). Fix it before the first output of such a port.
- **CLI.** `run` with the COCO form
  ([ADR-Q59W](../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 6), `validate` and `nodes`
  ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 9). Stage 1.6 gives
  `detectors` and `describe`. `run` takes `--ep <key>`, `--ep-option <name>=<value>`, the repeatable `--device <key>`
  ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 1) and `--taps <dir>`
  ([ADR-Y753](../decisions/entries/Y753-pipeline-templates-glue-vectors-and-taps-flag.md) item 3). It uses the exit-code table of
  [ADR-D8DH](../decisions/entries/D8DH-sessions-errors-and-the-ready-rule.md) item 2, and exits with 3 when an EP is not available, 4 when a session was not created and 5 when the GPU memory is
  exhausted ([ADR-9NW0](../decisions/entries/9NW0-ep-keys-options-and-failures.md) items 2 and 6). With no
  `--ep`, `run` uses `eps.recommend("performance")` and prints the chosen EP and its options
  ([ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 8). It does this only when the run must give an EP
  ([Running](pipeline/running.md#behaviour) item 7; [ADR-9PDQ](../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 4).
- **Node catalog.** `list_node_types()`, the tool that makes the spec table of each node type, and
  its doc test ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 9).
- **Webcam demo.** `output_schema` gives `edges` for each output, from the sidecar
  `keypoint.overlay` or the MediaPipe YAML files. Port `python -m skellytracker` to `start_pipeline`
  in `live` mode with `--pipeline <key>`, and the default EP of [ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 8 when the run must give an EP ([ADR-9PDQ](../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 4). One generic
  annotator draws each output
  ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 8).
- **Pipeline bundles.** Copy each contributed pipeline of `specs/pipeline/examples/` that has an
  entry in `specs/pipeline/inventory.yaml` to `core/model_zoo/pipelines/`. Add the load checks of
  [ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 7 and a run gate on
  `run/` to `verify` of `tools/intake_bundle.py`, and set the tolerance
  ([ADR-271H](../decisions/entries/271H-pipeline-bundles.md) item 3).
- **Built-ins.** Copy `yolox-rtmw-wholebody` and `mediapipe-holistic-tasks` from
  `specs/pipeline/examples/` to `core/model_zoo/pipelines/`
  ([ADR-3SF2](../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 2;
  [ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 3).
  The spec examples pin no `sidecar_sha256`. The copy adds the `sidecar_sha256` of each `onnx_model`
  node, because a shipped file must have it
  ([ADR-7NY2](../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 10).
  `yolox-rtmw-wholebody` is a stateful pipeline. It follows the box behaviour of the skellytracker
  branch `sfn26` with the early redetect of 03b9c1dc, and it gives the smoothed crop ROI as the
  output `person_roi` ([ADR-RA0E](../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) items 1 and 6;
  [ONNX model node](pipeline/nodes/onnx_model.md#authoring-guidance)).
- **Box parity of the built-in.** This stage makes the reference recording for
  `yolox-rtmw-wholebody` ([ADR-RA0E](../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md)). The
  working branch has neither the One Euro box filter nor the early redetect, so a script gets the
  values from the old code:
  - The script is in `decisions/scripts/`, with a patch file beside it. It makes a temporary clone
    outside the repository at the skellytracker commit 2d356a6c (branch `sfn26`). It applies the
    patch: the early redetect of 03b9c1dc, ported by hand (`BBoxPolicy.needs_recovery`,
    `StageState.needs_redetection`, its use in `should_redetect` and in `DetectionStage`).
  - It runs `human_tracker_config(preset="rtmpose", video_fps=30.0)` on the test recording with
    one camera and `timestamp_ms = frame_index × 1000 / 30`. The recording must hold frames with
    no person. If it holds none, the script blanks a run of frames.
  - It writes one fixture with, for each frame: `detector_ran`, the YOLOX box when the detector
    ran, the keypoints with their scores, the smoothed box before the clip, and
    `bounding_boxes[0]`. The values are float64. The script needs the old models, so it runs in
    this stage and not before.
- **Multi-person.** A pipeline can have more than one row (`I > 1`). But a row has no identity
  across frames, and each `track_ids` value is -1, until an `associate` node exists
  ([ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1). The temporal nodes
  filter row `i`, which can be another person on the next frame. Thus v2.0.0 tracks one person: the
  load refuses a temporal node or an `@prev` input with `I` > 1 (`V-pipeline.graph-11`;
  [ADR-TH8E](../decisions/entries/TH8E-one-person-in-v2.md)). "Later" holds the multi-person work.
- **Investigations.** Read `SharedSessionPool` and `TrackerLease` in the freemocap development-streaming
  work: what freemocap needs (a lease for each stream, the lifetime, thread safety). freemocap
  realtime already runs one pipeline with all cameras. Runs that overlap in time, for example
  realtime and posthoc, share no session: measure the VRAM cost and decide with freemocap whether it
  schedules the runs or accepts the cost ([ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 6). Study frame drops in `live` mode: a latest-frame mailbox, a count of
  dropped frames, a `drop` timing span and MediaPipe LIVE_STREAM.
- **Params during a run (the last step).** `PipelineRun.set_params(node_id, params)` and the error
  `SetParamsRefusedError` ([Running](pipeline/running.md#behaviour) item 11, `V-pipeline.running-10`;
  [ADR-N5BM](../decisions/entries/N5BM-set-during-run-and-set-params.md)). The run reads the mark
  `set_during_run` of each param from the reference model. A change applies from the next call and
  resets no node state.
- Gate: tests on generated ONNX models for each node type, the load checks, the empty-input rule,
  the `concat` empty-input fill, the instance rows with `class_index` and `instance_score`, `@prev`,
  the stateful batch rule and its warning, `ep_partial_placement`, the CLI exit codes, the default EP, `V-pipeline.running-8`, `V-pipeline.running-9`, each refusal of
  `V-pipeline.running-10` and a change that applies from the next call, and record and replay with `row`. A
  test of `node_ran`: true when the detector ran and found nobody; false for an empty required
  input, a replayed node and a padded item; present with `timing` off. The
  package glue nodes pass the glue vectors. The aggregator output passes
  `skellybench.schema.validate_timing`. `mediapipe-holistic-tasks` runs and gives the expected point
  sets. Box parity of `yolox-rtmw-wholebody` ([ADR-RA0E](../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md)):
  - Parity test A, the box logic. The test runs the graph of `yolox-rtmw-wholebody` on the fixture
    of "Box parity of the built-in", with the two `onnx_model` nodes replaced by the recorded YOLOX
    boxes and keypoints, and with the same timestamps. `node_ran` of the node `person` must equal
    `detector_ran` on each frame. `person_roi` must agree with the smoothed box before the clip
    within 1e-6 px. The clip of `person_roi` to whole pixels must give the same integers as
    `bounding_boxes[0]`.
  - Report B, end to end. A run of the built-in with the real models, in fp32, against the
    fixture: the count of frames where the flag differs, the IoU of `person_roi` and the distance
    of the points with a score of 0.4 or more on both sides. It is a report, with no pass limit on
    the keypoints: the crop pixels, the re-exported models, the points below 0.4 and the confidence
    of a carried box differ ([ADR-RA0E](../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md),
    Consequences).

### 1.11 Checkpoint: the 2.0.0 pre-release

**Status: NOT STARTED.**

- It comes after 1.10 and before any deletion ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 5). The old and the new code are side by
  side.
- Publish a skellytracker pre-release of `2.0.0` that loads `"2.0.0"` sidecars and runs a sidecar
  model with no hand-written detector. Record it as
  [ADR-6GE2](../decisions/entries/6GE2-spec-version-follows-skellytracker.md) gives.
- From this release, each exporter pins it as its ONNX host ([ADR-6J8E](../decisions/entries/6J8E-exporters-run-released-skellytracker.md) item 1). Set the version of
  the pin in the exporter kit (0.3).
- In the workflow and the skills, delete each current rule that a rule with the marker "From the
  2.0.0 pre-release" replaces, and remove the markers (0.1).
- Move the `--write` and `--check` commands of `tools/sidecar_refs.py` into the package as a
  command, and keep a thin wrapper in `tools/`
  ([`format.composition`](model-sidecar/format/composition.md#implementer-guidance)). In the same
  step, change the commands of
  [`source` and hashes](model-sidecar/model-addition-workflow/validation-and-publishing.md#source-and-hashes).
  The move waits for this stage, because the tool must run without `skellytracker` until the
  exporters pin the pre-release
  ([ADR-6J8E](../decisions/entries/6J8E-exporters-run-released-skellytracker.md) item 1).
- The keypoint score map
  ([Keypoint score map](model-sidecar/post/keypoint/score-map.md#implementer-guidance);
  [ADR-F067](model-sidecar/decisions/entries/F067-simcc-score-map.md)). The generic keypoint
  detector gives the mapped score as `scores` and the decode score as `raw_scores`. Two items are
  open:
  - The pipeline result. `specs/pipeline/outputs.md` says that the keypoint `score` is the decoded
    score of the sidecar, with no mapping. Change it: `score` is the mapped score, and a new field
    (proposed name `raw_score`, `(I, P)`) keeps the raw decode score. The `onnx_model` node then
    fills that field from `raw_scores`. `to_canonical` takes the presence of a derived point from
    the score `> 0`, so it must take it from the coordinates or the raw score, because a mapped
    score of a present keypoint can be `0.0`.
  - A golden test of the mapped score of one RTMW crop in
    `skellytracker/tests/sidecar/test_rtmw_sidecar.py` (part 6 of the proposal). It needs the
    mmpose scores of one crop, which this repository does not hold.
- Its release note says these things:
  - The new spec loader, the catalog, the generic detectors, the pipeline API and the hardware and
    EP API are in.
  - The old ONNX detectors, their `detector_type` keys and their `model_name` values go in a later
    release.
  - Intel Mac is not supported. `onnxruntime` is a base dependency. A GPU EP installs with
    `skellytracker-eps install` as a CUDA 13 plugin pack. The old ONNX detectors run on the CPU only
    ([ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md)).
  - freemocap must not move to 2.0.0 before it migrates.
- Gate: each part of the [checkpoint](#checkpoint) is done. An exporter environment pins the
  pre-release and runs one model and one pipeline. The full suite passes.

## Phase 2 — After the checkpoint

Agents build the exporters again against the exporter kit, and add their models and pipelines
through the model addition workflow. The stages below are the work of skellytracker in this phase.

### 2.1 Delete the old YOLOX and RTMW (was Da)

**Status: NOT STARTED.**

- It comes after the checkpoint ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 7). The pipeline API keeps a working YOLOX and
  YOLOX+RTMW pipeline at each step.
- Delete `object_detectors/yolox/` (with `prepare_yolox_onnx`, `_yolox_dynamic_batch.py` and
  `yolox_decode.py`) and `keypoint_detectors/rtmw/`, with the old wholebody shim in
  `keypoint_detectors/rtmpose/wholebody/`: the modules, the sidecars, the demos and the registry
  entries. Delete their tests and golden fixtures, and each `shared/` fragment that only they use.
  Check first which `shared/` fragments the new sidecars need. A new sidecar needs no canonical
  mapping file: the registry holds the mappings
  ([ADR-23F5](../decisions/entries/23F5-landmark-schema-registry.md)).
- Update the README, the examples and the demos.
- Gate: the full suite passes without the deleted tests. The old RTMPose tests and the MediaPipe
  tests pass with no change of expected values.

### 2.2 The RTMPose replacements (was N6)

**Status: NOT STARTED.**

- The replacements of RTMPose body, hand and face come from OpenMMLab-Exporter through the
  acceptance gate of 0.1, on the pre-release
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 7). They block
  v2.0.0. The `model_id` values are proposals. The exporter applies the `model_id` rules.

  | Proposed `model_id` | Replaces | Keypoints | Input | Sizes, minimum |
  |---|---|---|---|---|
  | `rtmpose-body17` | `rtmpose-body`: `rtmpose-s_256x192`, `rtmpose-m_256x192` | 17 (COCO) | 256×192 | `s`, `m` |
  | `rtmpose-hand21` | `rtmpose-hand`: one size | 21 | 256×256 | `m` |
  | `rtmpose-face106` | `rtmpose-face`: one size | 106 | 256×256 | `m` |

- Each model has the contract of the two stage 1.9 models: `schema_version: "2.0.0"`, `batching.batch: 3`
  with `batching.batch_conversion`, and an fp32 and an fp16 artifact for each size, with `filename`
  and `sha256`.
- Each model names a registered landmark schema. The exporter writes each new schema file, with its
  canonical mapping, in the `model` bundle: the 17-point COCO body, the 21-point RTMPose hand and
  `LaPa_106` (no mapping). The body and hand mappings come from
  `rtmpose_body17_to_canonical_mapping.yaml` and `rtmpose_hand_to_canonical_mapping.yaml`
  ([ADR-23F5](../decisions/entries/23F5-landmark-schema-registry.md) item 6).
- Register the MediaPipe schemas: body (33), hand (21) and the 478-point face, with a face name
  that is not `MediaPipe_FaceMesh` (the 468-point model). Take the body and hand mappings from
  `mediapipe_body_to_canonical_mapping.yaml` and `mediapipe_hand_to_canonical_mapping.yaml`. The
  face has none. Then give the schemas to the groups of `mediapipe_tasks`
  ([ADR-23F5](../decisions/entries/23F5-landmark-schema-registry.md) items 1 and 7;
  [ADR-4MP6](../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md) item 2; the
  [pipeline open work](pipeline/decisions/open-work.md)).
- The built-in pipeline `rtmpose-body-hands-face`
  ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 3). Before it
  ships, measure the body17 hand ROI rule (elbow to wrist) and the face ROI rule. No reference
  defines them. The measurement also decides whether `min_size_px` comes back.
- Gate: the model gate of 0.1, run locally. `rtmpose-body-hands-face` runs.

### 2.3 Delete the old RTMPose, the old loader and the old processing (was Db)

**Status: NOT STARTED.**

- Delete `keypoint_detectors/rtmpose/` (body, face, hand, `rtmpose_keypoint_detector.py`,
  `rtmpose_preprocessing.py` and `run_demo.py`), with its sidecars, demos, tests and golden
  fixtures.
- Delete the old loader `core/sidecar/`. Then move `core/model_spec/` to `core/sidecar/` with one
  `git mv` ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 8).
- Move `core/detectors/shared/` into `core/model_zoo/detectors/shared/` when a new sidecar `$ref`s
  it. Otherwise delete the old fragments.
- Delete the old processing modules (`image_preprocessing.py`, `affine_crop.py`,
  `object_detection_decode.py` and `simcc_decode.py`), `golden_parity.py`,
  `test_image_preprocessing.py`, `test_object_detection_decode.py`, the old entries of
  `PACKAGE_RUNNERS` and the old `resolve_overlay_groups`.
- Delete `REMOVED_VALUES` and `MERGED_IMAGENET_MODES` in `tools/tests/test_traceability.py` when the
  model at `core/sidecar/` has none of those values.
- Gate: the full suite and the vector tests pass.
- After this stage, do the item "Code citations of `sidecar-spec.md`" below. The new code cites
  section IDs.
- **Code citations of `sidecar-spec.md`.** This item carries out item 3 of
  [ADR-CN15](../decisions/entries/CN15-spec-readme-is-the-only-entry-point.md). The docstrings and
  comments of the old package cite headings of `specs/model-sidecar/sidecar-spec.md`. Stage 2.3 deletes those modules. The new code cites the
  section ID of each section file, for example `pre.normalize`. A citation of the whole spec cites `specs/model-sidecar/README.md`. In `tools/tests/test_traceability.py`, change `CITATION`
  and `citations()` to read the section-ID form, so that `test_the_code_cites_the_spec` counts the
  new citations. Replace `test_every_spec_citation_in_the_code_names_a_heading_of_the_index` with a
  test that checks that each cited section ID exists (`section_ids()`). Remove `INDEX_PATH`,
  `normalized_heading` and `test_a_citation_compares_without_case_and_backticks`.
  `defined_keys()` in `tools/tests/test_examples.py` also reads `sidecar-spec.md`. Today only that
  file defines the top-level key `batching`. First give the top-level keys another source, for
  example a `batching` heading or Field row in `common/batching.md`. Then remove that path from its
  list. Change the citation check in
  [Checks](../.claude/skills/change-sidecar-spec/SKILL.md#checks) of the `change-sidecar-spec`
  skill, and remove the rule for the frozen file from its
  [Spec structure](../.claude/skills/change-sidecar-spec/spec-edit-rules.md#spec-structure). Each changed
  rule cites
  [ADR-CN15](../decisions/entries/CN15-spec-readme-is-the-only-entry-point.md).
  The user first changes the two links to the file in
  `specs/draft/exporter-guide/sidecars/README.md`
  ([ADR-x64y](../decisions/entries/x64y-draft-exporter-guide-folder.md)). Then delete
  `sidecar-spec.md`. Each link to it goes to `specs/model-sidecar/README.md` or to a section file. A
  decided entry gets its link repairs and a link-repair `_Edited` line. A plain-text path in a
  decided entry stays, because it is history.
  One more change goes with the deletion: the "Single source of truth" bullet of
  `specs/model-sidecar/README.md` names the section files, not "this document".
  After the deletion, a new root entry states that a plain-text path `specs/sidecar-spec.md` or
  `specs/model-sidecar/sidecar-spec.md` in a decided entry means `specs/model-sidecar/README.md`
  ([ADR-CN15](../decisions/entries/CN15-spec-readme-is-the-only-entry-point.md)).

### 2.4 Delete the old run code (was Dc)

**Status: NOT STARTED.**

- It comes after 2.3, when each built-in runs as a pipeline config. Delete `core/tracker/`
  (`Tracker`, `DetectionStage`, `MultiPersonTracker`), the old `core/sessions/` code
  ([ADR-D8DH](../decisions/entries/D8DH-sessions-errors-and-the-ready-rule.md) item 13), `TrackerConfig`, `DetectionStageConfig`, the
  old detector contract and each old config base, `object_detectors/keypoint_bbox/`,
  `precomputed_object_detector.py`, the three old MediaPipe detector classes and `run_demo.py`, the
  old annotators, the demo builders, and the two MediaPipe canonical mapping files, after stage 2.2
  moved their mappings to the registry
  ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 7;
  [ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 5;
  [ADR-23F5](../decisions/entries/23F5-landmark-schema-registry.md) item 7).
- charuco and aruco become plain classes with their own frozen config dataclass and `detect(image)`.
  They subclass no base
  ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 4). The
  calibration demos call these classes. The public factory `create_detector` keeps its signature
  and its options, and the result keeps `detect(image)` and `close()`. This stage defines the
  result type of `detect` of the plain classes. `core/detectors/calibration.py` keeps its names,
  and `CharucoBoardDefinition` stays a Pydantic model that is not frozen
  ([ADR-KE1C](../decisions/entries/KE1C-one-public-detector-factory.md)).
- Move the tests that still apply to the new runtime. The cases of `test_keypoint_bbox_detector.py`
  and `test_detection_stage_hierarchy.py` seed `roi_from_points` vector cases only when their meaning
  is the same ([ADR-3SF2](../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 4). The
  minimum-size case does not move.
- Gate: the full suite passes. Each built-in runs as a pipeline config. The MediaPipe built-in gives
  the expected point sets (body, both hands, face). It has no keypoint parity with the old builders,
  because Holistic is a different graph.

### 2.5 Release 2.0.0

**Status: NOT STARTED.**

- The 2.0.0 release comes after 2.4. 2.0.0 ships with the old detectors and the old run code
  already deleted. Thus freemocap migrates one time ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 7).
- Its release note warns that these are gone: the old ONNX detectors, their `detector_type` keys and
  `model_name` values, `canonical_mapping_path()`, `Tracker`, `TrackerConfig`,
  `DetectionStageConfig` and the old MediaPipe detector classes. freemocap uses them, so it must not
  move to 2.0.0 before it migrates.
- **Ruff rule review.** Examine the rules that ruff 0.16 added to the default set, and ISC004.
  Decide which rules to adopt, and fix their findings
  ([ADR-D3VP](../decisions/entries/D3VP-ruff-0-17-with-the-old-rule-set.md) item 3).
- **Test coverage review.** Review the test coverage of the package code. Add the tests that the
  review finds missing.
- Gate: the full suite passes. The ruff rule review and the test coverage review are done.
- **The first package release.** Added on 2026-11-03. The spec version is the skellytracker
  version. The spec has no `vNEXT`, and the open target is `2.0.0`
  ([ADR-6GE2](../decisions/entries/6GE2-spec-version-follows-skellytracker.md)). Thus 2.5 is
  the first package release that ships the spec: the skellytracker `2.0.0` release, after stage 2.4. It is the first
  release that loads `"2.0.0"`, thus the new loader of stage 1.4 comes before it (the item SemVer `schema_version` of 1.4). The parts of the former M7, M8, M9 and M11 that apply before `vNEXT` are moot. In the other text of this plan, `vNEXT` means the open target `2.0.0`.

### freemocap migration

freemocap is outside this plan. It uses the old detectors and their keys, so it must not move to
2.0.0 before it migrates ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md)).
freemocap moves to `pipelines` itself. skellytracker gives no adapter to the old `Observation`
([ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1). The migration has
these parts:

- **Point names.** A pipeline point name is `<group>/<point>`, for example
  `left_hand/left_thumb1`. The output schema gives the `groups`. `to_canonical` gives the canonical
  names, which carry the side in the region, for example `left_hand/wrist` (stage 1.10;
  [ADR-4MP6](../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md)). freemocap
  needs no map of its own.
- **Frame index.** The outputs, the timing events and the taps use `frame_index`, not
  `frame_number`.
- **Charuco.** charuco runs through `detectors`, beside the pipeline, on the same frames. Pipelines
  have no calibration node
  ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 4). Remove the
  link between charuco and the tracker in the typed recording graph. freemocap makes the detector
  with `create_detector("charuco@skellytracker", board=...)` of `skellytracker.core.detectors`,
  and it imports the board model `CharucoBoardDefinition` and each calibration helper from
  `skellytracker.core.detectors.calibration`. It imports no module of `calibration_detectors`, no
  detector class and no config class of a detector. The `TrackerMapping` of this package does not
  read `CHARUCO_BOARD_MAPPING`: `from_yaml` has no `known_tracker_keypoints` argument, and it
  does not know the key `passthrough_keypoints_as_landmarks`. The port did not take that
  `TrackerMapping` change of `sfn26`. The user decides how freemocap reads the mapping ([ADR-KE1C](../decisions/entries/KE1C-one-public-detector-factory.md)).
- **Resets.** Remove `max_consecutive_misses=10`. `smooth_keypoints` has only `reset_after_ms`, and
  `mediapipe_tasks` has no reset
  ([ADR-6JWJ](pipeline/decisions/entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md)).
- **Timestamps.** A `live` caller must give a `timestamp_ms` that increases. A `live` run has no
  fallback.
- **Frame rate.** The hard-coded 30 fps goes. A `video` caller gives `timestamp_ms` or the run
  parameter `fps`.
- **Dependency pins.** freemocap pins `mediapipe==0.10.33` in a uv override. It uses the exact pins
  of skellytracker ([ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md)). freemocap gets the GPU EPs from the plugin packs of `eps`, not
  from ONNX Runtime extras. The user changes freemocap.

### Later

- Move the ONNX files of `core/model_zoo/` to a Hugging Face repo
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 5).
- Multi-person tracking with the new pipelines: an `associate` node gives the rows an identity
  across frames, and removes the limit of `V-pipeline.graph-11`. Until then, each `track_ids` value
  is -1, and v2.0.0 tracks one person.
- A better batch strategy than the padding of missed frames and crops, for example no work for a
  padded frame.
- The ROI input of `mediapipe_tasks`, with `min_size_px` on `roi_from_points` and
  `assumed_handedness` on the `hand` variant. Do it when MediaPipe on a YOLOX box or the cropped
  MediaPipe tracker of freemocap needs it.
- The decomposed ONNX Holistic. It waits for sidecar proposals: a crop that takes a rotated ROI,
  weighted NMS, detection keypoints and the `roi_refiner` role
  ([ADR-7NY2](../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 7).
- Real tiny models in CI, from the Hugging Face repo, with a trimmed upstream reference. CI uses
  generated models until then ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md)).
- Face blendshapes. This is planned work after the merge with the freemocap development-streaming
  work. The `mediapipe_tasks` node of v2 gives no blendshapes.
- **GitHub Issues.** After the Issues channel exists, the text goes in an issue and the patch in a
  fork PR. Before the first fork PR, harden CI: `pull_request` and not `pull_request_target`, a
  read-only `GITHUB_TOKEN`, an approval before a workflow of an outside contributor runs,
  CODEOWNERS for `.github/` and `tools/`, and branch protection on `development`.

## Verification

- `uv run pytest -m "not video"` passes. On Windows with Python 3.11 or 3.12, run the MediaPipe
  tests apart ([`skellytracker/AGENTS.md`](../skellytracker/AGENTS.md#tests)).
- The MediaPipe tests pass with no change of their expected values, except in the one commit of the
  MediaPipe change and in 2.4.
- The vector cases of each new `PACKAGE_RUNNERS` entry agree (`uv run pytest tools/tests`).
- The detector and pipeline tests on generated ONNX models pass on the three operating systems.
- The exporter parity tests pass locally: the acceptance gate of 0.1 for each new model, against the
  upstream reference output of the exporter.
- `uv run ruff check skellytracker/ tools/` passes. Do not run `black` or `isort` on the package.
- After 1.10, run `python -m skellytracker --pipeline <key>` against a webcam or a test video, and
  look at the drawn outputs.

## Resuming this plan in a fresh session

M1 to M5 are done ([History](#history)). Each milestone gives its file layout. The four generic processing modules are in `core/detectors/processing/` ([ADR-0007](../decisions/entries/0007-generic-processing-package.md)). `rtmpose_preprocessing.py` is still tracked, but no module imports it. Stage 2.3 deletes it. Do not create the deleted modules `yolox_preprocessing.py` and `rtmpose_simcc_decode.py` again. The next work is phase 1, from stage 1.2 ([Stage order](#stage-order)). Before you start, read [ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md), [ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md), [ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) and [ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md). Before 1.10, read the [pipeline spec](pipeline/README.md) and its [decision log](pipeline/decisions/README.md). Use the skill `implement-sidecar-section` for each sidecar section that a stage of phase 1 implements. [Stage 1.10](#110-the-pipeline-api-was-p) names the skill for its node types. No `GenericObjectDetector` or `GenericKeypointDetector` class exists yet.

## Reference examples

Moved to [Reference examples](model-sidecar/model-addition-workflow/reference-examples.md) in the model addition workflow ([ADR-B9FM](../decisions/entries/b9fm-finished-sidecar-plans.md)). That file gives what the examples are and how to provide or replace an example.

## Moved sections

The stages of this plan now hold the items of these sections.

### M6 — Generic sidecar-driven detector (drop in a YAML + ONNX, no new Python)

Moved to [1.7](#17-standalone-generic-detectors-was-n4).

### M7 — Sidecar catalog, dispatch and trace tools

Moved. "V- rule checks of the examples" is in [1.4](#14-spec-loader-was-n1). "Trace-tool functions",
"Catalog and roots" and "Capability check and dispatch" are in
[1.6](#16-catalog-and-the-detectors-entry-point-was-n3). "Package root in the trace scan" is in
[1.9](#19-the-first-new-models-was-n5).

### M8 — Validation, preprocessing and decode gaps

Moved. The model and loader items are in [1.4](#14-spec-loader-was-n1). The behaviour items are in
[1.5](#15-spec-processing-was-n2). Each item keeps its name.

### M9 — Source and hash checks

Moved. "Reference hash checks in the resolver" is in [1.4](#14-spec-loader-was-n1). "Artifact hash
checks" is in [1.6](#16-catalog-and-the-detectors-entry-point-was-n3).

### M10 — Shared runtime and the acceptance gate

Moved. The pre-release is [1.11](#111-checkpoint-the-200-pre-release). The exporter runtime is in
[0.3](#03-exporter-kit). The patch, the review, the acceptance gate, the verdict `describes` and the
independence rule are in [0.1](#01-acceptance-gate-and-patch-process). "GitHub Issues" is in
[Later](#later).

### M10a — YOLOX re-export

Moved to [1.9](#19-the-first-new-models-was-n5). The old YOLOX is deleted and replaced, not
re-exported in place ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md)).

### M10b — RTMW re-export

Moved to [1.9](#19-the-first-new-models-was-n5). The old RTMW is deleted and replaced, not
re-exported in place ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md)).

### M11 — Repository fixes

Moved. "MediaPipe timestamps and landmarkers on Windows" is in
[1.8](#18-mediapipe-holistic-runner). "Run-time check IDs" is in [1.5](#15-spec-processing-was-n2).
"Code citations of `sidecar-spec.md`" is in
[2.3](#23-delete-the-old-rtmpose-the-old-loader-and-the-old-processing-was-db).

### M12 — `vNEXT` release

Moved to [2.5](#25-release-200).

## History

M1 to M5 had the goal to "eat our own dog food": implement the sidecar system, then migrate the two existing hand-written ONNX detectors — YOLOX (person object detector) and RTMW/RTMPose wholebody (133-keypoint pose estimator) — to be driven by sidecar YAML instead of hardcoded Python constants (model URLs, mean/std, input sizes, output permutations). This was a **no-functional-change** migration: same models, same math, same detection/keypoint output — just loaded declaratively.

Note: `CLAUDE.md` at the repo root is stale — it describes a pre-rewrite architecture (`trackers/`, `TrackedObjectDefinition`, `composite_gpu_tracker`) that no longer exists after commit `2c2615c` ("Structural rewrite (#75)"). This plan targets the **current** `skellytracker/core/` package. `CLAUDE.md` now only imports `AGENTS.md`, which describes the current layout (decision 0001).

### Key decisions

These decisions apply to M1 to M5. They are history. For the new code, [ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) replaces decisions 1, 3, 4 and 5: the shipped sidecars go in `core/model_zoo/`, the old detectors are deleted with their keys and shims, and the YOLOX re-export has no NMS in the graph. Decision 2 stays: `point_names` (formerly `tracked_points`) is in the native model order ([ADR-88WQ](../decisions/entries/88WQ-sidecar-vocabulary.md)).

1. **Storage layout.** Sidecar YAML files are git-tracked inside the package tree at `skellytracker/core/detectors/object_detectors/{family}/{model_id}.yaml` and `skellytracker/core/detectors/keypoint_detectors/{family}/{group}/{model_id}.yaml`, matching the spec's layout exactly. ONNX binaries are **not** git-tracked — they still download through the existing `ModelSource`/`resolve_model_path()` (`skellytracker/core/sessions/model_registry.py`), extended to (a) save under the sidecar's own directory instead of the flat `~/.cache/skellytracker/models/`, (b) honor the sidecar's `filename` field instead of deriving it from the URL, and (c) verify `url_sha256`. This reuses the existing download/zip-extraction machinery rather than building a new one. **(a) was not implemented:** downloaded ONNX files still cache flat in `~/.cache/skellytracker/models/` under the sidecar's `filename` (see M2); decision 0016 (sidecar catalogs) keeps that location. (b) and (c) are done.

2. **`tracked_points` ordering for RTMW.** The existing `rtmpose_wholebody.yaml` point list is in a *re-ordered* "schema order" (body, right_hand, left_hand, face), requiring the hardcoded `_MODEL_TO_SCHEMA_PERM` permutation array to fix up the model's true native output order (body, face, left_hand, right_hand). The spec requires `tracked_points[i]` to equal the model's i-th native output index, so the new sidecar's `tracked_points` will be authored in **true native model order**, eliminating the permutation entirely. This changes the *array order* of the returned `Keypoints`, but not the name→value mapping (`Keypoints` is name-indexed; nothing in the codebase relies on positional order — confirmed via grep). Parity tests must therefore compare by name, not raw array equality.

3. **Detector replacement strategy.** Modify `YoloxPersonDetector` and `RTMPoseKeypointDetector`/`RTMWWholebodyDetector` *in place* — same registered `detector_type` string (`"yolox_person"`, `"rtmpose"`), same config field surface, same `detect`/`preprocess`/`postprocess`/`connections` signatures — so `build_object_detector`/`build_keypoint_detector`, `TrackerConfig`, and all existing call sites keep working unmodified. Internals swap hardcoded constants for sidecar-driven lookups, but decode math is reused verbatim from the existing pure functions in `yolox_preprocessing.py` / `rtmpose_preprocessing.py`.

4. **RTMW file relocation.** Move the wholebody detector from `keypoint_detectors/rtmpose/wholebody/` to a new `keypoint_detectors/rtmw/wholebody/` directory, matching the spec's own family naming (`model_id: rtmw-wholebody`). A grep of all importers found the following that must keep working: `skellytracker/core/detectors/keypoint_detectors/rtmpose/__init__.py`, `.../rtmpose/rtmpose_keypoint_detector.py` (already a re-export shim), `.../rtmpose/wholebody/run_demo.py`, plus test/example files importing `from skellytracker.core.detectors.keypoint_detectors.rtmpose import RTMPoseKeypointDetector` or directly from `rtmpose.wholebody.rtmpose_wholebody_detector`. Keep `rtmpose/__init__.py` and a `rtmpose/wholebody/rtmpose_wholebody_detector.py` re-export shim pointing at the new `rtmw/wholebody/rtmw_wholebody_detector.py` module so none of these break. `KEYPOINT_DETECTOR_REGISTRY["rtmpose"]` key is unchanged.

5. **YOLOX output-contract representation.** YOLOX's post-graph-surgery ONNX actually emits two tensors (pre-NMS boxes + scores), which doesn't fit the spec's single-tensor `detections`+`fields` model cleanly. Resolve by having the sidecar describe the **native, un-stripped checkpoint contract** (one `detections` output, `fields: [x1,y1,x2,y2,score]`, `requires_nms: false`) — the upstream OpenMMLab export's actual shape. The `prepare_yolox_onnx` graph-surgery step (dynamic batch + NMS-stripping optimization) stays exactly as-is, as an internal implementation detail not modeled in YAML, exactly as it isn't described by anything declarative today.

### M1 — Sidecar resolution engine + Pydantic model (no detector changes)

**Status: DONE (commit `dd10819`).**

New package `skellytracker/core/sidecar/`:

- `errors.py` — `SidecarError` base, plus `SidecarParseError`, `SidecarRefError` (missing file / cycle / sibling-key / escapes-cache_dir), `SidecarBaseError`, `SidecarSchemaVersionError`, `SidecarValidationError` (wraps Pydantic `ValidationError` with file path attached). Each error carries `.file_path` and names the offending directive, matching the spec's "recoverable catalog errors."
- `resolution.py` — pure YAML-merge logic, no Pydantic dependency:
  - `parse_sidecar_file(path) -> dict`
  - `resolve_sidecar_composition(path, cache_dir) -> dict` — resolves `$ref` for a file relative to *that file's own directory* before merging it into a `base` chain (order matters: ref-resolve top-down per file, then deep-merge bottom-up), enforcing "never escape above `cache_dir`" via `Path.resolve()` + `is_relative_to()`.
  - `_deep_merge(base, override)` — JSON Merge Patch semantics: mapping+mapping recurses key-by-key with `None`-value delete; sequence/scalar replaces wholesale. Used for both `base` inheritance and per-size `sizes.<name>` merging.
  - `_resolve_refs(node, current_file, cache_dir, stack)` — recursive `$ref` walker with cycle detection (`stack`) and strict-form enforcement (`{$ref: x, other: y}` errors).
- `model.py` — the `SidecarModel` Pydantic hierarchy (`extra="forbid"`), submodels: `InputSpec`, `CustomNormalization`, `ResizeSpec`, `CropPolicySpec`, `BatchingSpec`, `OutputSpec`, `DetectionDecodeSpec`, `PoseSpec`, `SkeletonSpec`, `PoseDecodeSpec`, `OverlaySpec`, `OverlayGroupSpec`, `SizeSpec`/`OnnxSpec`/`BatchArtifactGroup`/`PrecisionArtifact`. `SidecarModel` validates everything genuinely shared at the top level, but keeps `sizes: dict[str, dict[str, Any]]` as raw (unvalidated) dicts — `SidecarModel.resolved_size(name)` deep-merges `sizes[name]` over the top level (same `_deep_merge` as `base`) and validates the result as a `SizeSpec` where `input.shape`/`resize.target_size` become required.
  - `canonical_mapping`/`derived_points` `prefixes` + `[prefix]X: "Y"` expansion implemented as a shared, dependency-free helper (`core/io/canonical_mapping_expansion.py`), invoked as a `model_validator(mode="before")` on `PoseSpec`.
  - The spec's validation-rule checklist is mapped to field/model validators — single-field checks as `field_validator`s, single-submodel invariants as `model_validator`s on that submodel, and genuinely cross-cutting checks (role↔semantic↔decode consistency, `fields` must appear in `outputs`, overlay-vs-skeleton-vs-tracked_points) as `model_validator(mode="after")` on `SidecarModel` itself.
- `versioning.py` — `parse_skellytracker_version(v) -> (year, month, build, tag)`, `is_schema_version_supported(sidecar_version, installed_version) -> bool`, `require_stable_version(v)`, called from the loader.
- `loader.py` — `load_sidecar(path, cache_dir=None) -> SidecarModel`: `parse_sidecar_file` → `resolve_sidecar_composition` → `SidecarModel.model_validate()`, plus the `model_id == basename` check and `schema_version` support check.

Also done as part of M1: `skellytracker/core/io/canonical_mapping_expansion.py` (new, shared `prefixes`/`[prefix]` expansion helper) and `TrackerMapping.from_yaml` extended to use it.

Tests: `skellytracker/tests/sidecar/test_resolution.py` (18 tests, `tmp_path`-based fixtures covering `$ref` chains, cycles, `base`+null-delete, sibling-key errors, escape-cache_dir rejection) and `test_model_validation.py` (54 tests covering the validation-rule checklist, grouped by spec section). All passing; `ruff` clean.

### M2 — Storage/artifact plumbing

**Status: DONE (commit `dd10819`).**

- Extended `resolve_model_path()` in `skellytracker/core/sessions/model_registry.py` with optional `expected_filename` (save/lookup as `cache_dir / expected_filename` instead of deriving from the URL tail) and `expected_sha256` (verify downloaded bytes before caching, raise new `ModelIntegrityError` on mismatch — the corrupt temp file is deleted, nothing is written to the cache path). Additive/backward-compatible — existing callers unaffected (both default `None`).
- `skellytracker/core/sidecar/runtime.py`: `sidecar_model_spec(sidecar, size, batch_key, precision, name, sidecar_dir, prepare=None, coreml_options=None) -> OnnxModelSpec` (builds a lazy, pure `OnnxModelSpec` from the chosen artifact — `name` is caller-supplied, no I/O happens here; see the M3 follow-up note below for why this superseded an earlier eager version), `build_normalization_fn(input_spec, precision) -> Callable[[NDArray], NDArray]` (resolves `normalization_by_precision[precision] → normalization → "imagenet_bgr"` and returns the numpy transform for `none`/`unit_float`/`imagenet_bgr`/`imagenet_rgb`/`custom`), `resolve_normalization_mode(...)` helper.

Tests: `test_model_registry_sidecar_support.py` (sha256 verification and filename-override with mocked `requests.get`) and `test_runtime.py` (normalization dispatch, `OnnxModelSpec` construction from a local artifact) — no real downloads needed. All passing.

**Not yet built in M2** (deferred to M3/M4 since they're detector-specific): `sidecar_letterbox_preprocess`/`sidecar_detection_decode`/`sidecar_affine_crop_preprocess`/`sidecar_simcc_decode` dispatch functions in `runtime.py` — these wrap the existing preprocessing/decode functions and are added alongside each detector's migration.

### M3 — YOLOX migration

**Status: DONE, including a post-migration cleanup pass (commits `45533bd`, `8848781`, `4a22905`).** The bullets below narrate how it evolved; see "Current file layout" at the end for where things actually live now — several of the paths/names named in the earlier bullets (`yolox_preprocessing.py`, `sidecar_letterbox_preprocess`, `sidecar_detection_decode`) were later moved/renamed and no longer exist.

- New `skellytracker/core/detectors/object_detectors/yolox/yolox.yaml`: `role: [object_detector]`, `input.normalization: none` (ONNX graph normalizes internally, matching current behavior), `input.resize: {method: letterbox, preserve_aspect_ratio: true, pad_value: 114}`, `outputs` = single `detections` entry with `fields: [x1,y1,x2,y2,score]` (native contract, see decision 5), `decode: {box_format: xyxy, requires_nms: false, ...}` matching today's defaults. `sizes` keys kept identical to today's `model_name` strings (`yolox-tiny`, `yolox-m`). Real `url_sha256` computed for both checkpoint zips (downloaded once and hashed).
- Added `sidecar_letterbox_preprocess`/`sidecar_detection_decode` dispatch functions to `yolox_preprocessing.py` (**not** `runtime.py` as originally sketched — see below) — thin wrappers around the *existing* `yolox_letterbox_preprocess`, `_postprocess_prenms`, `_postprocess_yolox`, `multiclass_nms`, unchanged.
- **Deviation from the original sketch:** the plan's sketch had `runtime.py` importing from `yolox_person_detector.py`'s decode helpers while `yolox_person_detector.py` imports from `runtime.py` — a real circular import (confirmed by triggering it both ways depending on which module a test imports first). Fixed by (a) moving `_postprocess_prenms`/`_postprocess_yolox` into `yolox_preprocessing.py` (code unchanged), and (b) putting the two new `sidecar_*` dispatch wrappers in `yolox_preprocessing.py` too, which imports `build_normalization_fn` from `sidecar/runtime.py` — a one-directional dependency (`runtime.py` has zero knowledge of YOLOX). `yolox_person_detector.py` imports from both, no cycle.
- Captured a golden-output fixture from the **pre-migration** `YoloxPersonDetector` against the repo's existing test image, before touching the file: `skellytracker/tests/sidecar/fixtures/golden/yolox_m_detect.json` and `yolox_tiny_detect.json`.
- Rewrote `yolox_person_detector.py` internals: `_YOLOX_MODEL_URLS`/`_YOLOX_INPUT_SIZES` replaced by a module-level `_SIDECAR = load_sidecar(...)`; `preprocess`/`postprocess`/`detect` delegate to the sidecar + dispatch functions. `model_spec()` builds `OnnxModelSpec` directly from sidecar data rather than via `runtime.sidecar_model_spec()` — that helper eagerly downloads/verifies and renames the spec (`f"{model_id}-{size}"`), which would (a) trigger a network download merely by importing the module (`YOLOX_MODEL_SPECS` is built eagerly at import time) and (b) break the `spec.name == model_name` contract asserted by `TestYoloxPersonDetectorModelSpec`. Kept `OBJECT_DETECTOR_REGISTRY["yolox_person"]` and the config's public fields unchanged.
- **Follow-up (same working tree): `url_sha256` is now actually verified**, not just declared. `OnnxModelSpec` (`skellytracker/core/sessions/onnx_session.py`) gained two purely-additive optional fields, `expected_filename`/`expected_sha256`; `OnnxSession.create()`'s per-model loop threads `spec.expected_filename`/`spec.expected_sha256` into its (already-lazy, already-per-`create()`-call) `resolve_model_path(spec.source, ...)` call. Per user decision, the sidecar's declared filename (e.g. `yolox-m_b1_fp32.onnx`) is pinned as the cache filename instead of the old URL-tail-derived name.
- **Second follow-up (same working tree): `sidecar_model_spec()` redesigned to be the single, pure, generic builder** — the earlier YOLOX-specific hand-rolled `model_spec()` body (duplicating what `sidecar_model_spec()` does) was deleted; `YoloxPersonDetector.model_spec()` is now a direct call into `runtime.sidecar_model_spec(...)`. This was possible because the *original* reason the two diverged — `sidecar_model_spec()` eagerly downloading/verifying and renaming to `f"{model_id}-{size}"` — was itself a design flaw, not a fixed requirement: it conflated "build a declarative spec" with "resolve/cache/verify a model," work that already has a single home (`OnnxSession.create()`). Fixed by making `sidecar_model_spec()` pure (no I/O at all — not even checking a local artifact exists) and taking `name` as a required caller-supplied parameter instead of deriving it, since a fixed naming convention could collide across sidecars sharing one `OnnxSession`. `OnnxSession.create()` remains the only place resolution/verification happens for every sidecar-driven detector, present and future (e.g. M4's RTMW). No other detector calls `sidecar_model_spec()` yet, so this is a clean break with no other call sites to update.
- **Post-migration cleanup (commit `8848781`):** `detect()` had grown a second, duplicate code path (`_detect_yolox()`) that reimplemented preprocess→run→decode instead of calling `self.preprocess()`/`self.postprocess()`; folded into one path. Added guards so a sidecar declaring resize/decode options the code doesn't implement (`affine_person_crop`, non-`xyxy` box formats, etc.) fails loudly (`NotImplementedError`) instead of silently mis-processing.
- **Post-migration generalization (commit `4a22905`):** on review, decided the pre/postprocessing functions should become genuinely generic (branch on the full sidecar spec, not just guard against deviation) so future model families (RTMW in M4, and beyond) can reuse them instead of reimplementing. This moved code out of the YOLOX-specific file and out of `core/sidecar/` entirely, since preprocessing/decode aren't sidecar-*parsing* concerns even though they're configured by sidecar-described specs:
  - `core/detectors/image_preprocessing.py` (new) — `letterbox_preprocess`, `preprocess_image` (generic resize dispatch on `input.resize.method`), plus `build_normalization_fn`/`resolve_normalization_mode` (moved here from `sidecar/runtime.py`).
  - `core/detectors/object_detection_decode.py` (new) — `nms`, `multiclass_nms`, `boxes_to_xyxy`, `decode_prenms`, `decode_nms_baked_in` (moved from a short-lived `sidecar/detection_decode.py`).
  - `core/detectors/object_detectors/yolox/yolox_decode.py` (renamed from `yolox_preprocessing.py`) — now holds only what's genuinely YOLOX-specific: `_decode_yolox_raw_anchor_grid` (stride-grid reconstruction unique to YOLOX's head) and `yolox_detection_decode` (renamed from `sidecar_detection_decode` — the top-level dispatcher that picks between the generic decode strategies and the YOLOX-specific one based on what a given export emits).
  - `core/sidecar/runtime.py` trimmed to just `sidecar_model_spec` — the one genuinely sidecar-parsing concern (resolving artifact URLs/paths) left in that package.
  - Removed two dead `YoloxMetadata` fields (`original_size`, `is_prenms`) discovered during this pass — neither was read anywhere.

**Current file layout** (post-cleanup):
- `core/detectors/image_preprocessing.py` — generic resize+normalize, usable by any sidecar-driven detector.
- `core/detectors/object_detection_decode.py` — generic NMS/box-format/decode-strategy utilities, usable by any object detector.
- `core/detectors/object_detectors/yolox/yolox_decode.py` — YOLOX-specific raw-anchor-grid decode + the per-family dispatcher (`yolox_detection_decode`).
- `core/detectors/object_detectors/yolox/yolox_person_detector.py` — `preprocess()`/`postprocess()`/`detect()` call straight into the above; no YOLOX-specific preprocessing code of its own.
- `core/sidecar/runtime.py` — only `sidecar_model_spec` now.

**Known gap, not yet addressed:** `DetectionDecodeSpec` fields `requires_nms`, `max_detections`, `confidence_threshold_default`, `may_include_non_person_classes`, `class_field` are validated in `yolox.yaml` but nothing in the decode code reads them — actual thresholds/limits come from `YoloxPersonDetectorConfig`'s own Python defaults instead, which currently just happen to agree. Worth resolving (source config defaults from the sidecar, or drop the unused fields) before or during M4.

Tests: `skellytracker/tests/sidecar/test_yolox_sidecar.py` (loads/validates the real file; parity tests comparing post-migration `detect()` output against the golden fixture via `np.allclose`, run for both `yolox-m` and `yolox-tiny` — both passed, exact match within tolerance, still passing against real onnxruntime inference after the cleanup pass). `test_yolox_detector.py`/`test_image_preprocessing.py`/`test_object_detection_decode.py` cover the current module split. Full suite: `pytest skellytracker/tests` — 377 passed. `ruff`/`black`/`isort` clean on all touched files.

### M4 — RTMW migration

**Status: DONE.**

- `skellytracker/core/detectors/shared/skeletons/coco133_tracked_points.yaml` and `coco133_skeletons.yaml` — ported from the old `rtmpose_wholebody.yaml`, `tracked_points` reordered to native model order (body, face, left_hand, right_hand) per decision 2; `connections` ported unchanged (name-based, order-independent).
- `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml` — `role: [pose_estimator]`, `input.resize: {method: affine_person_crop, crop_policy: {expand_ratio: 1.25, maintain_aspect_ratio: true}}`, `input.normalization: imagenet_bgr`, `pose.tracked_points`/`connections` via `$ref` to the shared fragments, `pose.canonical_mapping` via `$ref` to a new composed mapping file, `pose.decode: {method: simcc}`, `overlay.groups` ported from `connection_groups()`'s prefix logic. `sizes` keys match the old `model_name` strings; real `url_sha256` computed from the three downloaded checkpoint zips.
- `rtmw_wholebody_to_canonical_mapping.yaml` (net-new — no wholebody canonical mapping existed before) — composes the existing body mapping via `base:` plus a hand-authored `prefixes: [right_hand_, left_hand_]` + `[prefix]X: "Y"` block (quoted — an unquoted leading `[` is a YAML flow-sequence opener, a parse error in a block-mapping key; the spec's own worked example omits the required quoting).
- **Deviation from the sketch:** `sidecar_affine_crop_preprocess`/`sidecar_simcc_decode` were not added to `runtime.py`. Following M3's established split (parsing stays in `core/sidecar/`, processing lives in `core/detectors/`), `affine_person_crop` was instead implemented as a new branch directly in the existing generic `core/detectors/image_preprocessing.py:preprocess_image()` (reusing `bbox_xyxy2cs`/`top_down_affine` from `rtmpose_preprocessing.py`), and SIMCC decode became `core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_decode.py` (family-specific, same tier as `yolox_decode.py`), reusing `rtmpose_letterbox_postprocess` unchanged. `preprocess_image()`'s return type widened to `float | tuple[NDArray, NDArray]` (letterbox's scalar `ratio` vs. affine crop's `(center, scale)`) — not a new pattern, since `YoloxMetadata.ratio` vs. `RTMPoseMetadata.center/scale` were already distinct per-family dataclasses one call-frame up.
- **New generic module** `core/detectors/overlay_groups.py` (`resolve_overlay_groups`) — generalizes the old hardcoded 4-branch prefix-matching `if/elif` in `connection_groups()` into a spec-driven version (explicit `connections` groups checked first, then `prefix` groups in declared order, remaining edges to the one default group), reusable by any future sidecar-driven pose detector.
- **Circular-import gotcha:** `rtmpose_preprocessing.py` lives under `keypoint_detectors.rtmpose`, whose `__init__.py` eagerly imports the wholebody shim (for registry side effects) — a module-load-time import of `rtmpose_preprocessing` from either `image_preprocessing.py` or the (then-named) `rtmw_decode.py` creates a real cycle back through the shim into the still-initializing `rtmw_wholebody_detector` module. Fixed by deferring both imports to inside the function body (they only run at call time, by which point everything is loaded) — see the comments at both import sites. (The same gotcha resurfaced in M4b when the decode module was promoted into the `rtmpose` package itself — see that section.)
- Moved to `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py`; deleted `_MODEL_TO_SCHEMA_PERM`. Per user decision, renamed the class/config to `RTMWWholebodyDetector`/`RTMWWholebodyDetectorConfig` (`detector_type`/registry key stay `"rtmpose"`, unchanged). Old `rtmpose/wholebody/rtmpose_wholebody_detector.py` is now a re-export shim (`as`-aliasing back to the old `RTMPoseDetectorConfig`/`RTMPoseKeypointDetector`/`RTMPOSE_MODEL_SPECS` names) — confirmed needed by `test_run_batched.py`'s direct import; `rtmpose/__init__.py` and the pre-existing `rtmpose_keypoint_detector.py` shim needed no changes. `connection_groups()` is a thin wrapper over `resolve_overlay_groups(_SIDECAR.overlay, _CONNECTIONS)`.
- Golden fixture captured from the pre-migration detector (by-name, all 3 model sizes) before touching the file: `skellytracker/tests/sidecar/fixtures/golden/rtmw_wholebody_{model_name}_detect.json`.
- Deleted the now-redundant `rtmpose_wholebody.yaml` schema file after the sidecar was validated and confirmed unreferenced (grep-checked).

Tests: `tests/sidecar/test_rtmw_sidecar.py` (loads/validates the real file; 133 tracked points in native order; `canonical_mapping` prefix-expansion produces `right_hand_wrist`/`left_hand_wrist`; `overlay.groups` has 4 entries; parity test against the golden fixture by name, `np.allclose(atol=1e-3)` — actual result: **exact match, zero numeric diff**, for all three model sizes; `model_spec()` no-network-I/O + sha256 verify/reject tests). New `tests/test_image_preprocessing.py::TestPreprocessImageAffinePersonCrop` and `tests/test_overlay_groups.py`. `test_run_batched.py`/`test_rtmpose_detectors.py`/`test_rtmpose_video.py` pass unmodified (48 tests) against the shim. Full suite: `pytest skellytracker/tests` — 400 passed. `ruff` clean; `black`/`isort` clean modulo a pre-existing repo-wide isort/black formatting disagreement on wrapped multi-name imports (already present on `main`/other M3 files before this change — left in black's formatting, matching existing convention). Manually smoke-tested the full YOLOX+RTMW+annotator demo pipeline (`build_rtmpose_demo` → `Tracker.process_image` → `KeypointAnnotator.annotate`) against the test image — skeleton and per-region overlay colors (body/right_hand/left_hand/face) render correctly.

**Superseded by M4b:** the decode helper originally landed here as `keypoint_detectors/rtmw/wholebody/rtmw_decode.py` (`rtmw_pose_decode`) was promoted to a shared, family-generic module during M4b — it turned out to have nothing RTMW-specific in it. It now lives at `keypoint_detectors/rtmpose/rtmpose_simcc_decode.py` as `simcc_pose_decode`; `rtmw_decode.py` was deleted.

### M4b — RTMPose body/hand/face migration

**Status: DONE.** Scoping correction: M4 should have migrated *all* RTM-based keypoint detectors, not just wholebody. This milestone finishes the job for `RTMPoseBodyDetector`, `RTMPoseHandDetector`, and `RTMPoseFaceDetector` (registry keys `rtmpose_body`/`rtmpose_hand`/`rtmpose_face`, unchanged), following the exact pattern M4 established, with no functional change (same models, same math; parity verified by-name against golden fixtures captured pre-migration).

- Unlike RTMW, **no directory relocation** — body/hand/face are genuine `rtmpose`-family models already living at `keypoint_detectors/rtmpose/{body,hand,face}/`, so files were edited in place with no shim needed.
- New shared skeleton fragments under `core/detectors/shared/skeletons/`: `coco17_tracked_points.yaml`/`coco17_skeletons.yaml` (body, 17 pts), `hand21_tracked_points.yaml`/`hand21_skeletons.yaml` (hand, 21 pts), `face106_tracked_points.yaml`/`face106_skeletons.yaml` (face, 106 pts, LaPa) — ported verbatim from each detector's old point/connections YAML.
- New sidecar YAMLs: `rtmpose/body/rtmpose-body.yaml`, `rtmpose/hand/rtmpose-hand.yaml`, `rtmpose/face/rtmpose-face.yaml` — same shape as `rtmw-wholebody.yaml` (`role: [pose_estimator]`, `input.normalization: imagenet_bgr` — verified identical to the pre-migration hardcoded `_RTMPOSE_MEAN`/`_STD`, `input.resize: {method: affine_person_crop, crop_policy: {expand_ratio: 1.25, maintain_aspect_ratio: true}}`, `pose.decode: {method: simcc}`). `sizes` keyed by the pre-migration `model_name` strings, with real `url_sha256` computed by downloading each checkpoint zip once. Old schema-only YAMLs (`rtmpose_body.yaml`, `rtmpose_hand.yaml`, `rtmpose_face.yaml`) deleted after porting (grep-confirmed unreferenced; `_schema_loader.py` itself is still used by the unrelated mediapipe detectors, so it was kept).
- **Canonical-mapping gap discovered by the sidecar's stricter validation:** `rtmpose_body_to_canonical_mapping.yaml` (used as the `base:` for RTMW's wholebody mapping) is authored for a 23-point body (COCO + 6 foot points) — the standalone body detector's own `tracked_points` is only 17 (no feet), so referencing that file directly fails `PoseSpec`'s "canonical_mapping sources must exist in tracked_points" validator. Pre-migration this was silently tolerated (missing keys are silently skipped per that file's own docstring); the sidecar's stricter validation doesn't allow it. Resolved by adding a new, correctly-scoped `rtmpose/body/rtmpose_body17_to_canonical_mapping.yaml` (17 direct mappings + the 4 already-foot-independent computed points) referenced from `rtmpose-body.yaml`; the original 23-point file is untouched and still serves RTMW's composition. Confirmed `canonical_mapping_path()` (the old classmethod pattern) has zero callers anywhere in the codebase — same as RTMW, which never defined it post-migration — so it was dropped for body/hand too rather than kept as dead API surface.
- **Pre-existing gap, left as-is:** face has no canonical-mapping YAML today and never defined `canonical_mapping_path()`. `pose.canonical_mapping` is optional in `SidecarModel`, so `rtmpose-face.yaml` simply omits it — same behavior as before migration.
- Golden fixtures captured from the pre-migration detectors (by-name, all model variants) before touching any detector file: `skellytracker/tests/sidecar/fixtures/golden/rtmpose_{body,hand,face}_{model_name}_detect.json`. (The hand fixture has 0 points — the test image isn't a hand crop, so every point falls below `confidence_threshold`; this is itself a valid parity case, since post-migration output must also be all-NaN.)
- Detector rewrites (`rtmpose_body_detector.py`/`rtmpose_hand_detector.py`/`rtmpose_face_detector.py`) follow RTMW's pattern exactly: hardcoded mean/std/URLs/input-sizes replaced by `_SIDECAR = load_sidecar(...)`; `preprocess()`/`postprocess()` call the shared `preprocess_image()`/`simcc_pose_decode()` instead of calling `rtmpose_letterbox_preprocess`/`rtmpose_letterbox_postprocess` inline; `model_spec()` becomes a thin `sidecar_model_spec(...)` call; the duplicate inline pre/postprocess logic each detector's `detect()` used to reimplement a second time (same duplication M3 cleaned up for YOLOX) was folded into one path. Registry keys, class names, and config field surfaces are unchanged.
- Body/hand/face detector modules import `rtmpose_simcc_decode` at plain module-load time (safe — they're already inside the `rtmpose` package's own import chain by the time `rtmpose/__init__.py` reaches them). `rtmw_wholebody_detector.py`, which lives *outside* the `rtmpose` package, hit the same circular-import gotcha M4 documented for `rtmpose_preprocessing` when its import of `rtmpose_simcc_decode` was tried at module level — fixed the same way, by deferring that one import to inside the function body.

Tests: `tests/sidecar/test_rtmpose_{body,hand,face}_sidecar.py` — sidecar loads/validates, tracked-point count/order, canonical-mapping spot checks, `model_spec()` no-network-I/O + sha256 verify/reject, and parity against the golden fixtures by name (`np.allclose(atol=1e-3)`) — all passing, including the hand detector's all-NaN case. Full suite: `pytest skellytracker/tests` — 431 passed. `ruff` clean; `black`/`isort` clean on all new/rewritten files (matching M4's convention: black-formatted, with the same pre-existing repo-wide isort/wrapped-import disagreement left alone).

### M4c — Consolidate generic preprocessing/decode helpers

**Status: DONE.** Follow-up prompted by reviewing M4b: `rtmpose_preprocessing.py` and `rtmpose_simcc_decode.py` (both under `keypoint_detectors/rtmpose/`) were named/located as if RTMPose-specific, but most of their contents weren't — the affine-crop math (`bbox_xyxy2cs`, `top_down_affine`, `get_warp_matrix`, ...) is the standard top-down bbox-crop transform used across pose architectures generally, and SIMCC decode (`get_simcc_maximum`, the sidecar-dispatching `simcc_pose_decode`) is specific to the SIMCC decode head, not to RTMPose as a family. Their location under `keypoint_detectors.rtmpose` was purely a packaging artifact of where the code was first vendored, and it's what forced the deferred-import workarounds in `image_preprocessing.py` and `rtmw_wholebody_detector.py` (importing anything from inside that package triggers `rtmpose/__init__.py`'s eager detector imports).

- Moved the two generic pieces to `core/detectors/`, alongside `image_preprocessing.py` and `object_detection_decode.py` (the existing precedent for "family-agnostic detector processing lives here"):
  - `core/detectors/affine_crop.py` — `bbox_xyxy2cs`, `top_down_affine`, `get_warp_matrix`, `_rotate_point`, `_get_3rd_point`, moved verbatim.
  - `core/detectors/simcc_decode.py` — `get_simcc_maximum`, `_stable_softmax`, `decode_simcc` (renamed from `rtmpose_letterbox_postprocess` — same math, moved verbatim), and `simcc_pose_decode` (the sidecar-dispatching entry point, merged in from the deleted `rtmpose_simcc_decode.py`).
- Deleted `rtmpose_preprocessing.py` and `rtmpose_simcc_decode.py` entirely. `rtmpose_letterbox_preprocess` (the other half of the old `rtmpose_preprocessing.py` pairing) was dead code by this point — nothing called it after M4b's detector rewrites switched body/hand/face to the generic `preprocess_image()` — so it was deleted rather than moved.
- **Correction (2026-11-12):** `rtmpose_preprocessing.py` was not deleted. It is still tracked, but no module imports it ([ADR-0007](../decisions/entries/0007-generic-processing-package.md)). Stage Db deletes it with `keypoint_detectors/rtmpose/`. `rtmpose_simcc_decode.py` is deleted.
- **The circular-import workaround is gone**, not just relocated: since `core/detectors/affine_crop.py` and `core/detectors/simcc_decode.py` sit outside the `keypoint_detectors.rtmpose` package, importing them no longer triggers `rtmpose/__init__.py`'s eager detector imports. `image_preprocessing.py`'s deferred `bbox_xyxy2cs`/`top_down_affine` import and `rtmw_wholebody_detector.py`'s deferred `simcc_pose_decode` import both became plain top-level imports.
- All import sites updated: `image_preprocessing.py`, `rtmw_wholebody_detector.py`, and the three body/hand/face detectors now import from `core.detectors.affine_crop`/`core.detectors.simcc_decode`; `tests/test_image_preprocessing.py` likewise.

Tests: full suite unmodified and still green (`pytest skellytracker/tests` — 431 passed); `ruff`/`black` clean on all touched files.

**Superseded immediately by M4d:** `core/detectors/affine_crop.py`/`simcc_decode.py`/`image_preprocessing.py`/`object_detection_decode.py` were all moved one more time, into a new `core/detectors/processing/` subpackage — see below.

### M4d — Group generic pre/post-processing under `core/detectors/processing/`

**Status: DONE.** Follow-up on M4c, per user request: once the four generic modules (`image_preprocessing.py`, `object_detection_decode.py`, `affine_crop.py`, `simcc_decode.py`) all lived flat under `core/detectors/`, mixed in with family-specific code (`detection_context.py`, `detector_base_classes.py`, `metadata.py`, `overlay_groups.py`), it made sense to group them under one dedicated subpackage rather than leave them loose.

- New package `core/detectors/processing/` (with `__init__.py`, no re-exports — callers import the specific module) holding all four files, moved verbatim (`git mv` for the two tracked from M3/M4; plain `mv` for the two untracked from M4c).
- Every import site updated to the `core.detectors.processing.*` path: `image_preprocessing.py` (self-import of `affine_crop`), `yolox_person_detector.py`, `yolox_decode.py`, the three RTMPose body/hand/face detectors, `rtmw_wholebody_detector.py`, `sidecar/runtime.py`'s docstring, and the corresponding tests (`test_image_preprocessing.py`, `test_object_detection_decode.py`, `sidecar/test_runtime.py`).
- `overlay_groups.py` was deliberately **not** moved here — it's about grouping connections for annotation/visualization, not pre/post-processing a model's tensors, so it stays a sibling of `processing/` under `core/detectors/`.
- **Docstrings trimmed by user decision:** the "Sidecar-driven (...) — see specs/sidecar-implementation-plan.md M4b/M4..." migration-history paragraphs were removed from the four detector docstrings (body/hand/face/`rtmw_wholebody_detector.py`) — that history belongs in this plan doc and commit messages, not in code comments future readers have to wade through. Don't re-add migration narrative to these docstrings; this doc is the durable record of *why*.

Tests: full suite unmodified and still green (`pytest skellytracker/tests` — 431 passed); `ruff`/`black` clean on all touched files.

### M5 — Cleanup

**Status: DONE.** The package source has none of the dead constants below. `uv run pytest -m "not video"` passes (413 tests, 2026-10-26). A `CLAUDE.md` refresh is not necessary: `CLAUDE.md` only imports `AGENTS.md`, and `AGENTS.md` describes `core/sidecar/` (decision 0001).

- Delete dead hardcoded constants once confirmed unused (`_YOLOX_MODEL_URLS`, `_INPUT_SIZES`, `_RTMPOSE_MEAN`/`_STD`, etc. — the RTMPose body/hand/face equivalents were removed as part of M4b, mirroring RTMW in M4).
- Run the full test suite (`pytest skellytracker/tests`) to catch anything transitively exercising YOLOX/RTMPose through `Tracker`/`process_video`/`process_batch`.
- Flag (don't execute) a `CLAUDE.md` refresh describing the new `core/sidecar/` package as a follow-up.

# Implementation Plan: Phases to the Exporter Checkpoint

> **Decisions.** The decisions behind this plan are recorded in the decision log, [`decisions/`](../decisions/README.md). The phases and their order follow [ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md). The dependency pins and the GPU EP packs follow [ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md). The implementation-stage work follows [ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) (replace the package ONNX detectors) and [ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) (the entry points and the layout). The pipeline design is in [ADR-7NY2](../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md), [ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md), [ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md), [ADR-3SF2](../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md), [ADR-0WTV](../decisions/entries/0WTV-system-metrics-and-pipeline-timing-helper.md) and the [pipeline log](pipeline/decisions/README.md). The sidecar names follow [ADR-88WQ](../decisions/entries/88WQ-sidecar-vocabulary.md) and [ADR-GKD1](../decisions/entries/GKD1-estimator-type-says-the-crop.md). Entries 0002 to 0007 record the decisions of M1 to M5 ([History](#history)). This plan stays until the user decides to delete it ([ADR-5WKW](../decisions/entries/5WKW-implementation-work-in-the-plan.md)). Record a new decision as a decision entry, not in this plan.

> Status: **M1 to M5 are done. Phase 0 started on 2026-11-12. Phase 1 waits for the gate of phase 0.** Phase 0 is in the spec-build stage, and phase 1 is in the implementation stage ([Stages](model-sidecar/model-addition-workflow/README.md#stages)). The [stage order](#stage-order) gives each stage. The "Status" line of each stage gives its state.

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

**Status: phase 0 started on 2026-11-12.**

Each stage of phase 1 and phase 2 changes package code, so it waits for the gate of phase 0. The
stages give the order of the work and hold their items.

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
| 1.3 Hardware and EP API | 1.2 | written by 0.4 | old |
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
| 2.5 Release 2.0.0 | 2.4 | full suite | new only, as pipeline configs |

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

**Status: NOT STARTED.** The hardware and EP work stays a parallel track on the branch
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

**Status: NOT STARTED.** It needs 0.1 to 0.4.

- The user declares the implementation stage in a new entry. The entry changes
  [section 1](../AGENTS.md#1-purpose) of `AGENTS.md` and the "Stage" part of the skill
  `implement-sidecar-section`, and says which rules of [ADR-0014](../decisions/entries/0014-spec-lifecycle.md) end.
- The end of the spec-build stage also has a consolidation entry (the
  [Rules](../decisions/README.md#rules)) and the retirement of `notes/sidecar-exporter-coverage.md`
  (the [open work](../decisions/open-work.md)).
- Then the session rebuilds the spec-build work into the two PRs `dom/52-process` and `dom/53-spec`
  ([Rebuild at the gate](../.claude/skills/stack-commit/after-spec-build.md#rebuild-at-the-gate)).
  The user opens them. Each stage of phase 1 is then one stacked PR, from `dom/54-dependencies`
  ([ADR-BH7C](../decisions/entries/BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md)).

## Phase 1 — Implementation stage

### 1.1 Dependencies

**Status: NOT STARTED.** [ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) gives the rules. Each item below is its own commit group.

- **Exact pins.** Pin each dependency of `dependencies` and of each extra with `==`, at the version
  of a new `uv.lock`. Use an environment marker where a platform needs it. Today
  `opencv-contrib-python`, `onnx`, `polars` and `scipy` have no version, and other dependencies have
  ranges. The OpenCV package (`opencv-contrib-python` or a headless package) is not decided (the
  [open work](../decisions/open-work.md)). Ask the user before you pin it.
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

**Status: NOT STARTED.** This stage has only the layout items that leave the old ONNX code alone.

- `core/__init__.py` stays eager ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 3). Stage 1.3 puts `system/`, `metrics/` and `eps/`
  under `core/`.
- Move charuco and aruco to `core/detectors/calibration_detectors/`
  ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 4).
- Create `core/model_zoo/`, the package sidecar root
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

**Status: NOT WRITTEN.** Stage 0.4 writes this stage from the plans of the hardware and EP track.
The known scope:

- `core/system/`, `core/metrics/` and `core/eps/` under the eager `core` ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 3).
  `core/metrics/` holds only system metrics ([ADR-0WTV](../decisions/entries/0WTV-system-metrics-and-pipeline-timing-helper.md) item 1).
- `eps.build_session()`. Stage 1.10 builds each ONNX session with it ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 5).
- The EP catalog owns the EP keys `trt-rtx`, `cuda`, `coreml` and `cpu`, and refuses each reserved
  key with its reason. It lists the allowed option names and values of each EP.
  `eps.build_session()` refuses an option that the catalog does not list, before it calls ONNX
  Runtime. `eps.recommend(form)` gives the forms `performance` and `accuracy` ([ADR-9NW0](../decisions/entries/9NW0-ep-keys-options-and-failures.md) items 1 to 3).
- `eps.build_session()` sets `enable_fallback=0` and `session.record_ep_graph_assignment_info=1`. It
  checks that the requested EP is the first provider and has at least one node. It raises
  `EpUnavailableError`, `SessionCreationError` or `VRAMExhaustionError` before frame 0. The session
  report gives the node count of each EP, the CPU node count and the CPU op types ([ADR-9NW0](../decisions/entries/9NW0-ep-keys-options-and-failures.md) items 4
  and 5).
- The execution provider information in `detectors` and `pipelines`.
- The `cuda` and `trt-rtx` plugin EP packs, CUDA 13 only, with the EP catalog and the EP store
  ([ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) item 3). The gate includes a local run on an NVIDIA host: `eps.build_session()`
  builds a session on each pack, and the node assignment shows the requested EP. Tests: an unknown
  option name or value is refused before ONNX Runtime, a missing pack raises `EpUnavailableError`,
  and no session is built again on the CPU
  ([ADR-M2C6](../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) item 7).
- Gate: stage 0.4 writes it.

### 1.4 Spec loader (was N1)

**Status: NOT STARTED.**

- A new package `core/model_spec/` holds the spec loader and the spec model
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 8). The old
  `core/sidecar/` does not change. Stage 2.3 moves the new package to `core/sidecar/`.
- The loader takes its sidecar root as an argument. It does not take the nearest folder named
  `core`.
- The model items below, and the validation rules that the behaviour items of 1.5 name.
- The reference hash checks and the V- rule checks of the examples, below. Stage 1.6 does the
  artifact hash checks.
- Gate: the new validation tests pass, and each reference example validates.

Each model item names the gap of the old code against the open target `2.0.0`. Do not change the old
code ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md)). Put each fix in `core/model_spec/`. The new code has no legacy parameter. The tests go beside the new code. The old golden fixtures go
with their detectors. A golden test of the new code compares with the upstream reference output of
the exporter. Stage 1.4 and stage 1.5 come before stage 1.9.

- **Batch forms.** A sidecar uses one batch form: `batching.batch: 3` with
  `batching.batch_conversion`, `1`, or `dynamic`
  ([Batch forms](model-sidecar/common/sizes-and-artifacts.md#batch-forms);
  [ADR-JB5J](../decisions/entries/JB5J-one-batch-form-for-each-sidecar.md)). The item "Flattened
  batch form" gives the fields and the rules.
- **Package model at spec version 2.0.0.** The spec cleanup removed the legacy
  layer, gave each sidecar one batch field, reduced the contract to the fields that carry
  information and made the spec version the skellytracker version
  ([ADR-0QKK](../decisions/entries/0QKK-no-legacy-layer.md);
  [ADR-JAA4](../decisions/entries/JAA4-one-batch-field.md);
  [ADR-90CE](../decisions/entries/90CE-minimal-sidecar-contract.md);
  [ADR-6GE2](../decisions/entries/6GE2-spec-version-follows-skellytracker.md)). The new model:
  - has no key that the spec does not define, for example `preserve_aspect_ratio`, `requires_nms` and
    `may_include_non_person_classes`. A key
    that the spec does not define is invalid
    (`V-format.composition-5`; [Validation rules](model-sidecar/format/composition.md#validation-rules));
  - has no `input_dtype`, `rank`, `batching.batch_axis`, `layout`, `supports_dynamic_size` or
    `is_3d` ([ADR-90CE](../decisions/entries/90CE-minimal-sidecar-contract.md));
  - has `keypoint.geometry`. A `simcc` decoder needs `keypoint.geometry: 2d`;
  - requires `input.normalization`, with no default
    ([ADR-0QKK](../decisions/entries/0QKK-no-legacy-layer.md));
  - requires the top-level `source` (`V-common.identity-4` to `V-common.identity-6`) and the
    `sha256` of each artifact (`V-common.sizes_and_artifacts-9`), with no default. Stages 1.4 and 1.6 add the hash checks of the file
    bytes;
  - gives `object.decode.max_detections` no default. The field is valid only with `selection: none` (`V-post.object.selection.none-1`);
  - accepts only the `$ref` directive form `{$ref, sha256}` (`V-format.composition-1`). The new
    resolver has no `base` directive.
- **Sidecar vocabulary.** Added on 2026-11-12. The spec uses one name for each concept, with no
  alias ([ADR-88WQ](../decisions/entries/88WQ-sidecar-vocabulary.md);
  [ADR-GKD1](../decisions/entries/GKD1-estimator-type-says-the-crop.md);
  [ADR-G3FA](model-sidecar/decisions/entries/G3FA-affine-crop-rotated-roi.md); rows 46, 47 and 48 of
  the [changelog](model-sidecar/changelog.md#summary-of-changes) give the full map). The new model:
  - takes the role `keypoint_detector`, not `pose_estimator`;
  - has the blocks `object:` (`object.decode`, `object.classes`) and `keypoint:`
    (`keypoint.decode`, `keypoint.geometry`, `keypoint.estimator_type`, `keypoint.point_names`,
    `keypoint.skeletons`, `keypoint.overlay` with `parts` and `edges`);
  - takes `min_score`, `box_space`, `coordinate_space`, the `fields` column `class_index`, and the
    semantics `packed_detections`, `keypoint_coordinates` and `instance_keypoints`;
  - has no `keypoint.requires_object_detector`. `V-pre.resize.affine_crop-2` reads
    `keypoint.estimator_type`: a top-down model must declare
    `input.resize.method: affine_crop`;
  - refuses a duplicate YAML key (`V-format.composition-6`);
  - applies the rules of a decoded keypoint and of a derived point: a keypoint with a score `<= 0`
    or NaN is missing, a derived point is missing when a source is missing, and the weights of a
    derived point sum to 1 within `1e-6`
    ([Keypoint schema](model-sidecar/post/keypoint/schema.md#fields)).
- **Heatmap decode removed.** The spec has no `heatmap` decode method and no `heatmap` output
  semantic ([ADR-9MJ6](../decisions/entries/9MJ6-remove-the-heatmap-decode.md)). The new model has
  neither. The old `core/sidecar/model.py` still accepts them. `REMOVED_VALUES` in
  `tools/tests/test_traceability.py` goes at stage 2.3.
- **3D SimCC decode removed.** The SimCC decode is 2D only: the spec has no
  `simcc_z` output semantic and no `keypoint.decode.depth_range` ([ADR-9HBB](../decisions/entries/9HBB-simcc-decode-is-2d-only.md)).
  The new model has neither. It refuses `method: simcc` with `keypoint.geometry: 3d` (`V-post.keypoint.schema-7`).
- **Sizes are plain fields.** A size entry holds only `input.shape`,
  `input.resize.target_size` and `onnx`. The host does not merge a size entry over the top level
  ([ADR-90CE](../decisions/entries/90CE-minimal-sidecar-contract.md) item 4). The new model types the size entry, so that it checks `V-common.sizes_and_artifacts-3`. It reads the
  three size fields and the other fields from the top level. It has no deep merge.
- **SemVer `schema_version`.** Each sidecar has `schema_version: "2.0.0"`, a
  quoted SemVer string ([ADR-6GE2](../decisions/entries/6GE2-spec-version-follows-skellytracker.md)). The old loader reads the CalVer
  pattern `vYYYY.0M.BUILD[-TAG]` and rejects
  `"2.0.0"`. The new loader checks the SemVer pattern `MAJOR.MINOR.PATCH` with
  an optional pre-release tag
  (item 2). The host
  must accept the SemVer `schema_version` values that it implements. Each release lists these
  values. It is not necessary for a release to implement an older version. A host lists an older version
  only while its current text reads it the same way: there is no legacy reading
  ([ADR-0QKK](../decisions/entries/0QKK-no-legacy-layer.md)). A pre-release host also
  lists its own pre-release value and the open target, for example `"2.0.0-rc.1"` and `"2.0.0"`.
  No other host accepts a pre-release value. The host must reject a `schema_version` that it does
  not implement, with an error that names that version (`V-format.versioning-1` and
  `V-format.versioning-2` of
  [Validation rules](model-sidecar/format/versioning.md#validation-rules);
  [Behaviour](model-sidecar/format/versioning.md#behaviour)). The capability check of 1.6 lists such
  a sidecar as unavailable. This loader is a requirement of the `2.0.0` release (item 4). The bump of skellytracker to `2.0.0` and the SemVer pattern of
  `bumpver` in `pyproject.toml` are the work of the user. They are not items of this plan.
- **Flattened batch form.** Each sidecar has one field `batching.batch`. Each size has
  `onnx.precision_artifacts` and `onnx.output_shapes`
  ([ADR-JAA4](../decisions/entries/JAA4-one-batch-field.md);
  [Batch forms](model-sidecar/common/sizes-and-artifacts.md#batch-forms)). The new model has
  `batching.batch` and `batching.batch_conversion`, and checks `V-common.sizes_and_artifacts-12`,
  `V-common.sizes_and_artifacts-13` and `V-common.batch_conversion-1` to
  `V-common.batch_conversion-4`. The new code finds an artifact by its size and its precision, not
  by a batch key. The batch conversion of stage 1.7 takes the batch of the source artifact from
  `batching.batch`. A sidecar with `batching.batch: 3` has no batch-1 or batch-2 artifact. To run it
  at another batch, the host makes the artifact with `model_batch_convert` (Behaviour 3 of
  [`common.batch_conversion`](model-sidecar/common/batch-conversion.md#behaviour)).
- **The `output_shapes` rule.** This item is the package item of
  [ADR-CRV0](model-sidecar/decisions/entries/CRV0-output-shapes-in-each-batch-group.md) (commit
  0881564), in the flattened batch form. The new model checks `V-common.sizes_and_artifacts-8`. Each size declares `output_shapes`, with one entry for each
  output, in the order of `outputs`. When `outputs[i].shape` is present, entry `i` has its rank, and
  each fixed dim of that shape is equal in the entry or `-1`. Dim 0 equals `batching.batch`, or is
  `-1` for `dynamic`
  ([Validation rules](model-sidecar/common/sizes-and-artifacts.md#validation-rules)). An artifact that
  `model_batch_convert` makes takes the `output_shapes` of its size, with dim 0 changed by step 2 of
  the profile ([ADR-JAA4](../decisions/entries/JAA4-one-batch-field.md) item 2).
- **Package sidecars deleted and replaced.** The old package sidecars `yolox`, `rtmw-wholebody`,
  `rtmpose-body`, `rtmpose-hand` and `rtmpose-face` do not migrate to the spec. They are deleted and
  replaced: stage 1.9 and stage 2.2 add the exporter models, and stage 2.1 and stage 2.3 delete the old sidecars
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 1). The old
  `base` of `rtmw_wholebody_to_canonical_mapping.yaml` goes with its sidecar.
- **Keypoint detector id.** The `model_id` of a keypoint detector is
  `{family}-{group}` or `{family}-{group}-{variant}` in `keypoint_detectors/{family}/{group}/`
  ([ADR-52NQ](model-sidecar/decisions/entries/52NQ-model-id-suffix.md);
  [Keypoint detector id](model-sidecar/common/identity.md#keypoint-detector-id)). No code checks
  `V-common.identity-7` or `V-common.identity-8`. In the new loader, after the basename check, check both rules on the path
  under the sidecar root when it starts with `detectors/keypoint_detectors/`. Check
  `V-common.identity-8` after the composition, because it needs the resolved
  `keypoint.point_names`. Raise a validation error with the rule ID. Add a test that writes each
  data-only case of [`common.identity`](model-sidecar/vectors/common.identity.yaml) to a temporary
  sidecar root at `input.path` and checks the failed rules. Then update the `validate` note of the front matter of the section.
- **License block.** Each sidecar has the `license` block with the model
  license and the training data ([ADR-NBG2](model-sidecar/decisions/entries/NBG2-license-and-training-data-without-the-deferred-examples.md);
  [License and training data](model-sidecar/common/license.md)). The old `SidecarModel` forbids the key `license`. The new model has a model of the block and checks `V-common.license-1` to `V-common.license-7`. The SPDX
  check of `V-common.license-3` needs a copy of the SPDX License List: pin its version (the
  Implementer guidance names 3.29.0). Add the data-only cases of
  [`common.license`](model-sidecar/vectors/common.license.yaml) to
  the validation tests. Then update the `validate` and `load`
  notes of the front matter of the section. The section is `draft`, so the `2.0.0` release also
  needs its graduation or its removal from the release.
- **Reference hash checks in the resolver.** Add the checks of the `$ref` hashes, and of
  the bytes of each file, to the new resolver in `core/model_spec/`. The spec has no `base` directive, so only the `$ref` hashes remain ([ADR-90CE](../decisions/entries/90CE-minimal-sidecar-contract.md) item 3). Then delete the temporary
  function `resolve` of `tools/sidecar_refs.py`. Move the `--write` and `--check` commands of that
  tool into the package as a command, and keep a thin wrapper in `tools/` ([`format.composition`](model-sidecar/format/composition.md#implementer-guidance)).
- **V- rule checks of the examples.** The doc tests parse and resolve each reference example, and
  check its provenance (`tools/tests/test_examples.py`). They also check that it has only keys that
  the spec defines (`V-format.composition-5`;
  [ADR-0QKK](../decisions/entries/0QKK-no-legacy-layer.md) item 11). They do not run the other
  `V-` rules on it, because the old `load_sidecar` rejects `"2.0.0"`
  ([ADR-6GE2](../decisions/entries/6GE2-spec-version-follows-skellytracker.md)). Thus no test checks the other rules after a spec-forced
  edit of an example ([ADR-KDBD](../decisions/entries/KDBD-change-classes-and-spec-forced-edits.md), item 5). In stage 1.4, validate each
  example with the new model in `tools/tests/test_examples.py`. Until then, part 7 of the proposal
  and `uv run python tools/sidecar_trace.py impact <range>` at landing are the check.

### 1.5 Spec processing (was N2)

**Status: NOT STARTED.**

- Add new modules in `processing/pre/` and `processing/post/`, one module for each spec section
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 4). Port them from
  `specs/model-sidecar/reference/`, for example `pre/resize_letterbox.py`, `pre/normalize.py`,
  `pre/resize_affine_crop.py`, `post/object_selection_nms.py`, `post/object_decode.py`,
  `post/keypoint_decode_simcc.py` and `post/unprojection.py`.
- These modules carry the behaviour items below. The dispatchers take the new spec model. The
  validation rule of each behaviour item goes in the model of 1.4.
- Port `pre/resize_affine_crop.py` from `specs/model-sidecar/reference/pre_resize_affine_crop.py`:
  `roi_from_box`, `crop_size`, `warp_points`, `warp_matrix`, `affine_crop` and `unproject`
  ([ADR-G3FA](model-sidecar/decisions/entries/G3FA-affine-crop-rotated-roi.md);
  [Implementer guidance](model-sidecar/pre/resize-affine-crop.md#implementer-guidance)). The resize
  dispatcher calls it on `input.resize.method: affine_crop`. The pipeline `detector` node gives each
  present row of its `rois` input as `(c_x, c_y, w, h, rotation)`. Do not reuse the old
  `get_warp_matrix` for a rotated crop: its `rot` argument turns a point above the centre. Add the
  module to `PACKAGE_RUNNERS` for `pre.resize.affine_crop`, with the `bbox_xyxy` and `roi` cases.
- Add each new function to `PACKAGE_RUNNERS` in `tools/tests/test_vectors.py` and to
  `verified_against`. The old entries (for example `letterbox_preprocess` and `fit_preprocess`) stay
  until stage 2.3, because the test requires that the agreeing entries equal the listed entries. Check
  whether a change of `verified_against` needs a spec content commit.
- Gate: the vector cases of the new entries agree. The old entries do not change.

Each behaviour item names the gap of the old code against the open target `2.0.0`. Do not change
the old code. Put each fix in the module of its spec section in `processing/pre/` or
`processing/post/`.

- **`fit` `pad_value`.** The spec requires `pad_value` on a `fit` resize
  ([Validation rules](model-sidecar/pre/resize-fit.md#validation-rules)). The old code does not require it: `ResizeSpec._check_method_specific_fields` accepts a `fit`
  resize without `pad_value`, and `fit_preprocess` has
  the default `pad_value=0`. The new model requires it, and the new `fit` module has no default. Test the rejection ([ADR-0012](model-sidecar/decisions/entries/0012-fit-resize-for-rtmo.md)).
- **Scalar and array pad values.** The old `fit_preprocess` passes a scalar `pad_value` to
  `cv2.warpAffine` as `float(pad_value)`. OpenCV then fills only channel 0 of a 3-channel image: a
  scalar `114` gives the border `[114, 0, 0]`. The spec requires `[114, 114, 114]`
  ([ADR-BJF9](../decisions/entries/BJF9-scalar-pad-value-fills-every-channel.md)).
  The new code expands a scalar to three values before the call. It also accepts an array of int values, for example the YAML array `[114, 114, 114]`. The new model has `crop_policy.pad_value`, and
  the new affine crop passes its expanded value to `cv2.warpAffine`. The case
  `scalar-pad-fills-each-channel` of
  [`pre.resize.fit`](model-sidecar/vectors/pre.resize.fit.yaml) fails for the old `fit_preprocess`. Add the new function to the file-level `verified_against` of that
  file. At stage 2.3, remove `unverified` and the case-level entries of the old function.
- **Letterbox rounding.** The old `letterbox_preprocess` cuts the resized size with `int()`.
  The spec rounds with `half_even` or `half_up`, places the image at `top_left` or `center`,
  and keeps each side at least 1 pixel. The old function has no `center` position and fails on a source
  that is 1 pixel wide. It reproduces 8 of the 12 `top_left` cases in
  [`pre.resize.letterbox`](model-sidecar/vectors/pre.resize.letterbox.yaml). The new module reproduces each case.
- **Stretch unprojection.** The `stretch` branch of the old `preprocess_image` returns `resize_meta = 1.0`. The
  host then has no scale factors to unproject with `x * src_w / T_w`. The new module returns the scale factors.
- **Normalization modes.** The old `build_normalization_fn` applies the `imagenet_rgb`
  statistics in the channel order of the frame, as it applies `imagenet_bgr`. The `imagenet_bgr` branch applies the RGB-ordered statistics to
  the B, G and R channels of the frame. That is the pre-spec rtmlib computation, not the spec
  meaning. The new module obeys [Normalization modes](model-sidecar/pre/normalization.md#behaviour).
  The old package sidecars keep the pre-spec computation until stage 2.1 and stage 2.3 delete them. No package sidecar moves to a new mode ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md)).
- **One `imagenet` mode.** The spec has one mode, `imagenet`. It applies the
  statistics in the channel order of `input.color_format`
  ([ADR-90CE](../decisions/entries/90CE-minimal-sidecar-contract.md);
  [Normalization modes](model-sidecar/pre/normalization.md#behaviour)). The new model has `imagenet` in
  its named modes and `input.color_format` as a required field (`V-common.input-5` and
  `V-pre.normalize-1`). It has no `CustomNormalization.color_format`. The new module takes the channel order of `imagenet` and of `custom` from
  `input.color_format`.
- **NMS box area.** The spec's `selection: nms` uses the box-area convention of the ONNX
  `NonMaxSuppression` operator, which does not add `1` to pixel widths or heights. The old `nms()`
  in `object_detection_decode.py` adds `1`. Only the
  old YOLOX path uses it. It also breaks a tie between equal scores toward the higher row index,
  but the spec breaks it toward the lower row index. The vectors in
  [`post.object.selection.nms`](model-sidecar/vectors/post.object.selection.nms.yaml) show both
  differences. Stage 1.10 uses an ONNX `NonMaxSuppression` graph for the new decode.
- **Clamp, size filter and class filter.** The new model accepts `object.decode.clamp_boxes` and `object.decode.min_box_size`, and checks them (`V-post.object.decode-5` and
  `V-post.object.decode-8`). In each selection mode, the decode clamps each unprojected box to
  `[0, W]` and `[0, H]` only when `clamp_boxes` is `true`. Then it drops each box unless its
  width and its height are both more than `min_box_size`. The new model requires `object.decode.selection` (`V-post.object.decode-4`) and the fields of each
  selection mode. It requires `object.classes` (`V-post.object.decode-10`) and checks `object.decode.keep_classes` (`V-post.object.decode-11`). A sidecar with no class source has exactly one name in `object.classes` (`V-post.object.decode-9`). The decode of each mode runs the shared steps of [Selection behaviour](model-sidecar/post/object/decode.md#selection-behaviour), with the class filter first ([ADR-17KN](../decisions/entries/17KN-one-selection-pipeline.md); [ADR-88WQ](../decisions/entries/88WQ-sidecar-vocabulary.md) item 3). Part B of 1.7 adds the modes that the package does not decode yet.
- **Resize compute dtype.** The spec has the optional
  `input.resize.compute_dtype`: `uint8` or `float32`, with the default `uint8`
  ([ADR-PHJ3](model-sidecar/decisions/entries/PHJ3-resize-compute-dtype.md);
  [Compute dtype](model-sidecar/pre/interpolation.md#compute-dtype)). The new model has the field and checks `V-pre.resize.interpolation-1`. It rejects the field for
  `method: none` (`V-pre.resize.none-1`). The new resize modules resize and pad the uint8 frame for `uint8`. For `float32`, they cast the
  frame to float32 before the resize and the pad, and keep the canvas in float32. They do not round or
  clamp the result. Add the cases of `pre.resize.interpolation.yaml` and the new case of
  `pre.resize.none.yaml` to the validation tests of the new model.
- **Affine crop matrix in float32.** The spec gives the warp matrix `M` of
  `affine_crop` in float32 steps, as mmpose v1.3.2 computes it
  ([ADR-3S5G](model-sidecar/decisions/entries/3S5G-affine-crop-matrix.md);
  [Behaviour](model-sidecar/pre/resize-affine-crop.md#behaviour)). The old code keeps the
  dtype of the box, and its `get_warp_matrix` puts the second warp point above the centre. The new module casts the person box to float32,
  also the full-frame box. It puts the second point left of the centre
  (`src_dir = [src_w * -0.5, 0]`, `dst_dir = [dst_w * -0.5, 0]`). The implementer decides the branch with `maintain_aspect_ratio: false`. Run the numeric cases of
  [`pre.resize.affine_crop`](model-sidecar/vectors/pre.resize.affine_crop.yaml)
  through the new module, and add a golden test with its
  three COCO cases. Then update the `forward` note of
  the front matter of the section.
- **SimCC score without softmax.** The spec gives the 2D SimCC decode of
  mmpose v1.3.2: the argmax of the raw values, the score `min(peak_x, peak_y)` with no softmax, the
  bin `-1` for a score `<= 0`, the NaN rule and the bin scale from the bin counts
  ([ADR-03PH](model-sidecar/decisions/entries/03PH-simcc-score-rule.md);
  [Behaviour](model-sidecar/post/keypoint/decode-simcc.md#behaviour)). The old code takes the mean
  of the two softmax peaks and a fixed split ratio of 2.0. The new module takes the score
  `np.where(max_x > max_y, max_y, max_x)`, keeps the `-1` rule, and reads the bin scale
  from the bin counts (`input_width / X_bins`). The new score has no fixed range. Thus the
  old `confidence_threshold: 0.004` defaults fit only the softmax score. The implementer decides the score threshold of the new keypoint path. Run the
  numeric cases of [`post.keypoint.decode.simcc`](model-sidecar/vectors/post.keypoint.decode.simcc.yaml) through the new module, and add a golden test on one RTMW crop with
  mmpose scores. Then update the `decode` status and
  the `partial` note of the front matter of the section.
- **Cast to the input dtype.** Each normalization mode casts its result to the
  `input.dtype` entry of the precision as the last step. A `uint8` input needs the resolved
  normalization `none`, and `input.resize.compute_dtype` absent or `uint8` (`V-pre.normalize-3`).
  `int8` is not an input dtype (`V-common.input-2`). The output dtypes keep it
  ([ADR-XH1J](model-sidecar/decisions/entries/XH1J-normalize-input-dtype.md);
  [Behaviour](model-sidecar/pre/normalization.md#behaviour)). The old code returns float32 from
  each mode, and the old `OnnxSession.run_batched` and `_warmup` feed float32. The new normalize module casts the result of each mode to `input.dtype[precision]` as the last step, and the
  new preprocessing keeps that dtype. The new sessions feed the input dtype. The new model has a type for the input dtypes (`float32`, `float16`,
  `uint8`) for `input.dtype`. The output dtype keeps `int8` (`V-common.outputs-2`). Add a validator of the
  resolved sidecar for `V-pre.normalize-3`. Run the numeric cases of
  [`pre.normalize`](model-sidecar/vectors/pre.normalize.yaml) through the new module, and
  compare the dtype and the values. These cases include the two `custom` default cases of
  [ADR-1V57](model-sidecar/decisions/entries/1V57-normalize-custom-defaults.md). Add the data-only cases of `pre.normalize.yaml` and
  [`common.input.yaml`](model-sidecar/vectors/common.input.yaml) to
  the validation tests. Add a golden test: one image of the
  `yolox-person` parity set through the new preprocessing, compared with the host
  tensor. Then update the `validate` and `forward`
  notes of the front matter of `pre.normalize`, and the `validate` and `load` notes of
  `common.input`.
- **Run-time check IDs.** A vector case for a refused tensor or caller argument writes
  `{error: no-rule}`, because no validation rule can check that input
  ([ADR-TA0G](../decisions/entries/TA0G-vector-cases-and-reference-modules.md)). The implementation stage can give these
  run-time checks their own IDs, for example `C-<section-id>-<n>`. A sidecar before `vNEXT` that uses
  a feature that is "Not available." also gives `no-rule`. A rule `V-format.versioning-<n>` can
  replace that use. The user decides both.

### 1.6 Catalog and the `detectors` entry point (was N3)

**Status: NOT STARTED.**

- The roots (the item "Catalog and roots" below): `core/model_zoo/`, the user root and Hugging Face snapshots. The user root is
  `platformdirs.user_data_dir("skellytracker", appauthor=False)` + `/models`, with the layout of
  `core/model_zoo/`. `platformdirs` becomes a direct dependency. skellytracker keeps no settings
  file. `list_detectors`, `list_pipelines`, `load_pipeline` and `start_pipeline` take
  `user_root: Path | None`. The order is the argument, then `SKELLYTRACKER_USER_ROOT`, then the
  default ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 6).
- The cross-platform tasks:
  - CRLF: the spec rejects CRLF (`V-format.composition-3`). The error names CRLF.
  - Symlinks: Hugging Face snapshot files are symlinks into `blobs/`. The new loader does not call
    `Path.resolve()` on a path in a root, because it follows a symlink out of the root.
  - Case: each folder name is lower case, as in the layout. The docs say it.
  - File locks: on Windows, a model update or a Hugging Face refresh closes the sessions first, or
    writes the new revision beside the old one.
  - Path length: test a long user name and a non-ASCII user name with ONNX Runtime.
- The capability check, for each artifact. A user can copy only some sizes or precisions. The
  item "Capability check and dispatch" below gives the rules.
- The artifact hash checks below, with the hash check cache.
- **Hash check cache.** No decision entry records this design. It is plan work.
  - Reason: `V-common.sizes_and_artifacts-10` requires that each present or downloaded ONNX file
    has the SHA-256 of its `sha256` field. An ONNX file can have several hundred MB, and the
    capability check looks at each artifact at each start. A full hash of each file at each start
    is too slow. Thus the host hashes a file only when it first sees the file and after the file
    changes.
  - Record: one record for each hashed file. The key is the sidecar root and the path of the file
    relative to that root. The fields are `size` (`st_size`), `mtime_ns` (`st_mtime_ns`), `file_id`
    (`st_dev` and `st_ino`; on Windows, NTFS gives the file index in `st_ino`), `sha256` (lowercase
    hex) and `checked_at`. The record holds the hash, not a pass or a fail. Thus a changed sidecar
    `sha256` needs no new hash.
  - Hit: `size`, `mtime_ns` and `file_id` are equal to the values of the file. The host compares the
    stored `sha256` with the sidecar `sha256`.
  - Miss: a field is different, or no record exists. The host reads the file in chunks (for example
    1 MiB) with `hashlib`, and writes a new record.
  - Download: the host hashes the bytes while it writes them. It checks `url_sha256` on the
    downloaded bytes, and `sha256` on the ONNX file that it writes or extracts. Then it writes the
    record, with no second read.
  - Location: one file, for example `hash-cache.json`, in the user cache folder of `platformdirs`,
    beside the download cache. The cache is not in a sidecar root: the package root is read-only,
    and the Hugging Face hub manages its own cache. A deleted cache file costs only a new hash of
    each file.
  - Writes: write the cache to a temporary file in the same folder, then call `os.replace`. Thus a
    reader never sees a partial file. When several processes write, the last write wins. A cache
    file that does not parse is an empty cache: log one warning, then write a new cache. An argument
    and an environment variable force a full hash of each file, for tests and for support.
  - Limits: the cache finds a corrupt file, a partial download and a wrong file. It does not protect
    against a local user with write access. FAT32 and exFAT store the modification time in steps of
    2 s. A file that changes within 2 s, with the same size and the same file id, can hit an old
    record. Accept this case, and name it in the docstring.
  - Later, optional: in the Hugging Face cache, the `blobs/` file name of an LFS file is its
    SHA-256. Compare that name with `sha256` only when it is 64 lowercase hex characters. Hash the
    file in all other cases.
  - Spec: add one line to the implementer guidance of `common.sizes_and_artifacts` in a non-spec
    commit. A host can keep the hash of a file with its size, modification time and file id, and
    hash the file again when one of these changes.
  - Tests: a hit; a miss after a change of the size, of the modification time and of the file id; a
    corrupt cache file; the atomic write; the record that a download writes; the forced full hash.
- The `detectors` list in `core/detectors`: the catalog entries and a static table of the entries
  with no sidecar (MediaPipe, charuco, aruco). Each entry has the category `onnx`, `mediapipe` or
  `calibration` ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md)
  item 2). An exporter model has the key `<model_id>@<source.name>`. A model of skellytracker has
  the key `<detector_type>@skellytracker`
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 6). The list does
  not import a detector module. `keypoint_bbox` and `precomputed` are not in the list
  ([ADR-7NY2](../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 13).
- Each entry has `available` and `unavailable_reason`: the extra (`importlib.util.find_spec` with a
  literal name), the ONNX file and its hash
  ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 7).
- `describe_detector(key)` and the CLI `detectors` and `describe`
  ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 9): the sizes,
  the precisions, the `sidecar_sha256`, the ports, the params with their sidecar defaults, and the
  point names.
- Gate: the catalog tests on temporary roots pass. A test checks that each entry of the static
  table has a known class.
- **Trace-tool functions.** Move `tools/sidecar_normalize.py` (the normalization table and the
  selector matching that the sidecar trace tool uses) into `skellytracker/core/model_spec/` without
  changes. The trace tool then imports them from the package. The capability check uses the
  same functions ([ADR-0013](../decisions/entries/0013-spec-structure.md);
  [`format.versioning`](model-sidecar/format/versioning.md#implementer-guidance)).
- **Catalog and roots.** The catalog is the `detectors` entry point (stage 1.6). Each entry has the
  category `onnx`, `mediapipe` or `calibration`
  ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 2). An
  exporter model has the key `<model_id>@<source.name>`, and a model of skellytracker has the key
  `<detector_type>@skellytracker`
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 6). Build the
  version order, the version pins, the reserved name `skellytracker`, the root log and the run
  metadata ([`common.identity`](model-sidecar/common/identity.md#implementer-guidance)). The roots
  are `core/model_zoo/`, the user root and Hugging Face repo snapshots (pin, refresh, cache paths
  without symlink resolution), with discovery in each root
  ([Sidecar roots](model-sidecar/format/file-layout.md#sidecar-roots);
  [Discovery](model-sidecar/format/file-layout.md#discovery)). The new code calls the root the
  sidecar root, not `cache_dir`
  ([`format.file_layout`](model-sidecar/format/file-layout.md#implementer-guidance)).
- **Capability check and dispatch.** Build the capability check for each artifact. Map a catalog entry to
  a generic detector by its role (`object_detector` or `keypoint_detector`) and its spec sections. There are no aliases and no claims: the old `detector_type` keys go with the old detectors ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) item 2). An unknown size
  is an error, not a silent fallback
  ([`format.versioning`](model-sidecar/format/versioning.md#implementer-guidance)).
- **Artifact hash checks.** Verify the file that `filename` names against `sha256` when the file is
  present and after a download. Use the hash check cache of stage 1.6. Today `skellytracker/core/sessions/model_registry.py` checks only
  `url_sha256`, and only during a download
  ([`common.sizes_and_artifacts`](model-sidecar/common/sizes-and-artifacts.md#implementer-guidance)).

### 1.7 Standalone generic detectors (was N4)

**Status: NOT STARTED.**

- The generic object detector and the generic keypoint detector of Part A below, in `core/detectors/generic/`
  ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 6). Each one takes a
  catalog entry, a size, a precision and a session. It runs the sidecar preprocessing, the inference
  and the postprocessing on a batch of images or crops. It has no old registry key, no
  `detector_type`, no old config base and no link to `DetectionStageConfig` or `DetectionContext`.
  The `detector` node of stage 1.10 wraps them.
- The generic keypoint detector reads `keypoint.estimator_type`. A `top_down_single_person` or
  `top_down_multi_person` model takes crops. A `bottom_up` model takes the full image
  ([ADR-GKD1](../decisions/entries/GKD1-estimator-type-says-the-crop.md) item 2).
- The generic keypoint detector groups the edges for drawing from `keypoint.overlay` (`parts`,
  `edges`) and `keypoint.skeletons`. The old `resolve_overlay_groups` stays until stage 2.3.
- The batch conversion at session start for each `batching.batch: 3` artifact
  (`model_batch_convert`), as a function that stage 1.10 calls. Stage 1.7 does not change `core/tracker/` or
  `DetectionStage.run_batch`. `test_run_batched.py` stays.
- The session takes the execution provider as `execution_provider`.
- The detector tests on generated ONNX models
  ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 8): `onnx.helper` makes
  tiny fixed-batch models at run time, with a sidecar in a temporary root. The tests cover the
  loader, the catalog, the generic detectors, the batch conversion and the decode. CI runs no real
  model.
- Gate: the detector tests pass on the three operating systems. The existing tests pass with no
  change of expected values.

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

**Status: NOT STARTED.** This stage is new ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 4). It needs only 1.1 and 1.2, so it can run
in parallel with 1.3 to 1.7.

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

**Status: NOT STARTED.** This stage replaces M10a and M10b.

- `yolox-person` and `rtmw-wholebody133` from OpenMMLab-Exporter go in `core/model_zoo/`, with their
  ONNX files beside their sidecars. Git does not track the ONNX files
  ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) items 1 and 5). The keys
  are `yolox-person@openmmlab-exporter` and `rtmw-wholebody133@openmmlab-exporter`.
- The reference examples show the form:
  [`yolox-person.yaml`](model-sidecar/examples/detectors/object_detectors/yolox-person/yolox-person.yaml)
  (`batching.batch: 3` with `batching.batch_conversion`, no NMS in the graph, host
  `selection: nms`) and
  [`rtmw-wholebody133.yaml`](model-sidecar/examples/detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133.yaml).
  OpenMMLab-Exporter re-exports both models with the names of
  [ADR-88WQ](../decisions/entries/88WQ-sidecar-vocabulary.md) and without
  `keypoint.requires_object_detector`
  ([ADR-GKD1](../decisions/entries/GKD1-estimator-type-says-the-crop.md)).
- The sizes give at least the coverage of today. `yolox-person` has `t` and `m` (the old `yolox-tiny`
  and `yolox-m`, the same HumanArt checkpoints). `rtmw-wholebody133` has the three old checkpoints:
  `rtmw-l-m_256x192`, `rtmw-x-l_256x192` and `rtmw-x-l_384x288`. The example has the size keys `m`,
  `l-256`, `x-256`, `l-384` and `x-384`. Check which checkpoint each size uses.
- The models come through the model addition workflow and pass the acceptance gate of 0.1
  ([ADR-6J8E](../decisions/entries/6J8E-exporters-run-released-skellytracker.md) item 6). Run parity
  against the upstream reference output of the exporter, at the detector level. Do not compare with
  the old golden fixtures.
- The RTMW model input changes. The old package sidecar declares `imagenet_bgr`, and the old code
  puts the B, G and R channels of the frame in tensor positions 0, 1 and 2. The export declares
  `normalization: imagenet` with `color_format: rgb`, which puts R, G and B there
  ([Normalization modes](model-sidecar/pre/normalization.md#behaviour)).
- Decided before the work: the old keys `rtmpose` and `yolox_person` and the old `model_name` values
  go, with no alias ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md)
  item 2). The host gets the ONNX files from `core/model_zoo/` (item 5). The generic keypoint
  detector of stage 1.7 runs the RTMW export.
- Open before the work: the export has no `keypoint.canonical_mapping`. The host-side canonical
  mappings are skellytracker work. The user decides how the package keeps the canonical mapping of
  `rtmw-wholebody133`. Record the decision in a decision entry before the work starts.
- Stage 1.9 writes no Python pipeline builders
  ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 6). Stage 1.10 adds the pipeline
  files.
- When the first spec sidecar is in `core/model_zoo/`, do the item "Package root in the trace scan"
  below.
- Gate: the model gate of 0.1, run locally. The old detectors still pass.

- **Package root in the trace scan.** The trace tool scans only
  `specs/model-sidecar/examples/`. The old package sidecars stay outside the spec until they are deleted ([ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md)). When the first spec sidecar is in `core/model_zoo/` (stage 1.9), add `core/model_zoo/` to the scan of
  `tools/sidecar_trace.py`. Add the derivations that the new sidecars need to
  the normalization table.

### 1.10 The pipeline API (was P)

**Status: NOT STARTED.** It needs 1.3 (`eps.build_session()`), 1.7, 1.8, 1.9 and the pipeline spec
([`specs/pipeline/`](pipeline/README.md)). It builds `core/pipelines/` and
`core/pipelines/_runtime/` beside the old `core/tracker/`. The old run code does not change
([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 1).

- **Config.** Move `PipelineConfig` and the node configs, with the union keyed on `type`, from
  `specs/pipeline/reference/pipeline_config.py` into `core/pipelines/config.py`. Add a doc test that
  checks that the committed `specs/pipeline/pipeline.schema.json` agrees
  ([ADR-3SF2](../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 3). Add load,
  export and the load checks
  ([ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 7). Each file has the
  required `source:` field, and its key is `<pipeline_id>@<source>`
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
  - the instance rows, with point names that have the id of their node as a prefix (for example
    `body.nose`);
  - the running modes `image`, `video` and `live`;
  - the batch: `video` and `image` batch to k × cameras, `live` batches to the camera count, and a
    node that takes ROIs batches to that batch × the `I` of its instance source. `start_pipeline`
    takes `camera_ids`;
  - the batch conversion of each artifact at start, and the padding of a missed frame or crop, with
    its result dropped;
  - the batch rule of a stateful pipeline and its warning `batch_limited_by_state`;
  - the session sharing inside one run: the nodes with the same artifact SHA-256, batch, EP key, EP
    options and device share one session; no session is shared between runs ([ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 6).
- **Time.** Each output, timing event and tap row has `frame_index`. In `video` and `live`, each
  frame has `timestamp_ms` (a float). A `video` frame with no `timestamp_ms` uses
  `frame_index × 1000 / fps`, with the run parameter `fps` (default 30.0). A `live` run has no
  fallback ([Running](pipeline/running.md#behaviour)).
- **`detector` node.** It wraps the generic detectors of stage 1.7. A node with a top-down keypoint model
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
- **`mediapipe_tasks` node.** One node with `variant: body | hand | face | holistic`. It wraps the
  Holistic runner of 1.8, with its timestamp fix and its safe close, and calls the Tasks
  landmarkers directly for the other variants. It uses the MediaPipe assets ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 4). Its
  params are `min_detection_score`, `min_presence_score`, `min_tracking_score` and `size`
  ([ADR-88WQ](../decisions/entries/88WQ-sidecar-vocabulary.md) item 7). It has no reset and no back-off ([ADR-6JWJ](pipeline/decisions/entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md)).
  Holistic is single person, so its `max_instances` is 1. Its output has `geometry: 3d` and
  `depth_unit: pixel` ([ADR-6DKT](pipeline/decisions/entries/6DKT-instance-rows-carry-class-and-score.md) item 6). In v2 it has no ROI input and no face blendshapes.
- **Glue nodes.** `roi_from_points`, `roi_tracking`, `gate`, `first_of`, `concat`, `merge`,
  `smooth_keypoints`, `smooth_roi` and `redetect`
  ([ADR-7NY2](../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6).
  - [`merge`](pipeline/nodes/merge.md) takes `target` keypoints and `source` keypoints of any
    instance source. Each source row goes to the slot with the nearest anchor, one row for each
    slot. The output has the target columns, with the `map` replacements, and one column set for
    each slot.
  - [`concat`](pipeline/nodes/concat.md) never replaces a point. An empty input does not stop it.
    The columns of that input are missing points: x, y and z are NaN, and the score is 0
    ([ADR-6DKT](pipeline/decisions/entries/6DKT-instance-rows-carry-class-and-score.md) item 5).
  - `smooth_keypoints` refuses a timestamp that does not increase. It has `reset_after_ms` and no
    miss counter.
- **Sessions.** Build each ONNX session with `eps.build_session()`
  ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 5). `start_pipeline` takes `ep_options`, and a `detector` node takes
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
  `detectors` and `describe`. `run` takes `--ep <key>` and `--ep-option <name>=<value>`, and exits
  with 3 when an EP is not available, 4 when a session was not created and 5 when the GPU memory is
  exhausted ([ADR-9NW0](../decisions/entries/9NW0-ep-keys-options-and-failures.md) items 2 and 6). With no
  `--ep`, `run` uses `eps.recommend("performance")` and prints the chosen EP and its options
  ([ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 8).
- **Node catalog.** `list_node_types()`, the tool that makes the spec table of each node type, and
  its doc test ([ADR-V7GZ](../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 9).
- **Webcam demo.** `output_schema` gives `edges` for each output, from the sidecar
  `keypoint.overlay` or the MediaPipe YAML files. Port `python -m skellytracker` to `start_pipeline`
  in `live` mode with `--pipeline <key>`, and the default EP of [ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 8. One generic
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
  The spec examples pin no `sidecar_sha256`. The copy adds the `sidecar_sha256` of each `detector`
  node, because a shipped file must have it
  ([ADR-7NY2](../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 10).
- **Multi-person.** A pipeline can have more than one row (`I > 1`). But a row has no identity
  across frames, and each `track_ids` value is -1, until an `associate` node exists
  ([ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1). The temporal nodes
  filter row `i`, which can be another person on the next frame. Thus the v2 pipelines run single
  person (`max_instances` 1). "Later" holds the multi-person work.
- **Investigations.** Read `SharedSessionPool` and `TrackerLease` in the freemocap development-streaming
  work: what freemocap needs (a lease for each stream, the lifetime, thread safety). freemocap
  realtime already runs one pipeline with all cameras. Runs that overlap in time, for example
  realtime and posthoc, share no session: measure the VRAM cost and decide with freemocap whether it
  schedules the runs or accepts the cost ([ADR-ZYS9](../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 6). Study frame drops in `live` mode: a latest-frame mailbox, a count of
  dropped frames, a `drop` timing point and MediaPipe LIVE_STREAM.
- Gate: tests on generated ONNX models for each node type, the load checks, the empty-input rule,
  the `concat` empty-input fill, the instance rows with `class_index` and `instance_score`, `@prev`,
  the stateful batch rule and its warning, `ep_partial_placement`, the CLI exit codes and the default EP, the timing
  parents, and record and replay with `row`. The
  glue vectors and the named tests of the glue nodes agree. The aggregator output passes
  `skellybench.schema.validate_timing`. `mediapipe-holistic-tasks` runs and gives the expected point
  sets.

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
  Check first which `shared/` fragments and canonical mapping files the new sidecars need.
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
- The host-side canonical mappings (`rtmpose_body17_to_canonical_mapping.yaml`,
  `rtmpose_hand_to_canonical_mapping.yaml`) are skellytracker work, not exporter work.
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
  (`Tracker`, `DetectionStage`, `MultiPersonTracker`), `TrackerConfig`, `DetectionStageConfig`, the
  old detector contract and each old config base, `object_detectors/keypoint_bbox/`,
  `precomputed_object_detector.py`, the three old MediaPipe detector classes and `run_demo.py`, the
  old annotators and the demo builders
  ([ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 7;
  [ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 5).
- charuco and aruco become plain classes with their own frozen config dataclass and `detect(image)`.
  They subclass no base
  ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 4). The
  calibration demos call these classes.
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
- Gate: the full suite passes.
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

- **Point names.** A pipeline point name has the id of its node as a prefix, for example
  `left_hand.wrist`. freemocap removes the prefix at the first dot, and needs names that carry the
  side. Its own map gives `left_hand.wrist` → `left_hand_wrist`. The pipeline spec has no rule for
  this map.
- **Frame index.** The outputs, the timing events and the taps use `frame_index`, not
  `frame_number`.
- **Charuco.** charuco runs through `detectors`, beside the pipeline, on the same frames. Pipelines
  have no calibration node
  ([ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 4). Remove the
  link between charuco and the tracker in the typed recording graph.
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
  across frames. Until then, each `track_ids` value is -1, and the v2 pipelines run single person.
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

M1 to M5 are done ([History](#history)). Each milestone gives its file layout. The four generic processing modules are in `core/detectors/processing/` ([ADR-0007](../decisions/entries/0007-generic-processing-package.md)). `rtmpose_preprocessing.py` is still tracked, but no module imports it. Stage 2.3 deletes it. Do not create the deleted modules `yolox_preprocessing.py` and `rtmpose_simcc_decode.py` again. The next work is phase 0. It changes no file under `skellytracker/`. Before you start, read [ADR-NHM3](../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md), [ADR-B4QR](../decisions/entries/B4QR-exact-pins-and-cuda-13.md), [ADR-AMJ8](../decisions/entries/AMJ8-replace-package-onnx-detectors.md) and [ADR-0XW9](../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md). Before 1.10, read the [pipeline spec](pipeline/README.md) and its [decision log](pipeline/decisions/README.md). Use the skill `implement-sidecar-section` for each stage of phase 1. No `GenericObjectDetector` or `GenericKeypointDetector` class exists yet.

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

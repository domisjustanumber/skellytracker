# Repository Instructions

Exporter agents: start from [`specs/sidecar/exporter-guide.md`](specs/sidecar/exporter-guide.md).
Exporter agents must not change files in this repository.

All new and changed documentation must use ASD-STE100 Simplified Technical English.
This rule applies to `AGENTS.md`, skills, decision entries, templates, the exporter guide and the
sidecar spec.
Use short sentences. Use active voice. Use one instruction per sentence.
Use "must" for a requirement.
Keep technical names, field names, enum values, formulas, code and YAML unchanged.

## 1. Purpose

skellytracker is the tracking backend for freemocap.
A `Tracker` runs its detection stages on each image. It returns an `Observation` and the new
`TrackerState`.
A `DetectionStage` has one optional object detector and one or more keypoint detectors.
A session holds the resources that detectors share, for example the ONNX Runtime sessions
(`OnnxSession`) or the MediaPipe device context (`MediaPipeSession`).
A detector that runs an ONNX model reads a sidecar.
A sidecar is one YAML file. It describes the runtime contract of one model family: input,
preprocessing, outputs and decode.
The section files under [`specs/sidecar/`](specs/sidecar/README.md) specify the sidecar format.
[`specs/sidecar-spec.md`](specs/sidecar-spec.md) is the permanent entry point and links to them.
The exporter repositories make ONNX files and write their sidecars: OpenMMLab-Exporter,
Roboflow-Exporter, Ultralytics-Exporter and Qualcomm-Exporter.
On 2026-10-22, MediaPipe-Exporter has no exporter code.

The spec is in its spec-build stage (decision [0014](notes/decisions/0014-spec-lifecycle.md)).
In this stage, the exporters add models and the spec changes.
The implementation code under `skellytracker/` does not change.

Read [`README.md`](README.md) for the install extras, the quick start and the API overview.
This file replaces the "Contributing" steps of `README.md`.
Open PRs against `development`, not `main` ([section 6](#6-git-rules)).

| Path | Role |
|---|---|
| `README.md` | Install extras, quick start, webcam demo, API overview |
| `GPU_SETUP_GUIDE.md` | The install extra and the execution provider for each GPU |
| `pyproject.toml` | Dependencies, extras, the dev group, and the pytest, ruff and poe settings |
| `skellytracker/__main__.py` | Webcam demo CLI (`cli_main`) |
| `skellytracker/core/tracker/` | `Tracker`, `MultiPersonTracker`, `DetectionStage`, `TrackerState` |
| `skellytracker/core/config/` | Pydantic configs: `TrackerConfig`, `DetectionStageConfig`, `ObjectDetectorConfig`, `KeypointDetectorConfig`, `SessionConfig` |
| `skellytracker/core/sessions/` | ONNX Runtime, CPU and MediaPipe sessions. `model_registry.py` downloads `url` ONNX files to `~/.cache/skellytracker/models`. `hf_repo` files go to the Hugging Face cache. |
| `skellytracker/core/detectors/detector_base_classes.py` | Detector base classes and the two registries, `OBJECT_DETECTOR_REGISTRY` and `KEYPOINT_DETECTOR_REGISTRY` |
| `skellytracker/core/detectors/keypoint_detectors/` | `aruco/`, `charuco/`, `mediapipe/`, `rtmpose/` (body, hand, face), `rtmw/wholebody/` |
| `skellytracker/core/detectors/object_detectors/` | `yolox/`, `keypoint_bbox/`, `precomputed/` |
| `skellytracker/core/detectors/processing/` | Generic preprocessing, affine crop, detection decode with NMS, and SimCC decode (decision [0007](notes/decisions/0007-generic-processing-package.md)) |
| `skellytracker/core/detectors/shared/skeletons/` | Tracked-point and skeleton fragments that sidecars include with `$ref` |
| `skellytracker/core/sidecar/` | Sidecar loader: `load_sidecar` (`loader.py`), `$ref` and `base` resolution (`resolution.py`), `SidecarModel` (`model.py`), version checks (`versioning.py`) |
| `skellytracker/core/data_primitives/` | `BoundingBox`, `Keypoints`, observations and data stores |
| `skellytracker/core/annotation/` | Overlay drawing (`Annotator`, `KeypointAnnotator`) |
| `skellytracker/core/temporal_processing/` | Box policy and smoothing, keypoint filters, track association |
| `skellytracker/core/io/` | `process_video.py`, `demo_manager.py` (webcam runner), tracker mapping, canonical mapping expansion |
| `skellytracker/examples/` | Example scripts |
| `skellytracker/tests/` | pytest suite. `sidecar/` holds the sidecar tests and their golden fixtures. |
| `specs/sidecar-spec.md` | The permanent index of the sidecar spec. It keeps each old heading as an anchor with a "Moved to" link to the new file. Start at [`specs/sidecar/README.md`](specs/sidecar/README.md). |
| `specs/sidecar/README.md` | The spec overview, the [section map](specs/sidecar/README.md#section-map) and the index of the validation rules. The section map gives the section ID, the file and the title of each section. |
| `specs/sidecar/format/`, `common/`, `pre/`, `post/` | The section files. Each file holds one section. Its front matter gives `id` (the section ID), `title` and `kind`. Each validation rule has a rule ID `V-<id>-<n>`, for example `V-pre.resize.letterbox-1`. |
| `specs/sidecar/changelog.md` | The `vNEXT` summary of changes and the `schema_version` history |
| `specs/sidecar/examples/`, `specs/sidecar/inventory.yaml` | The reference examples, in the `detectors/` layout of the package ([`examples/README.md`](specs/sidecar/examples/README.md)), and the provenance of each example |
| `specs/sidecar/templates/` | [`model-intake.md`](specs/sidecar/templates/model-intake.md) and [`change-proposal.md`](specs/sidecar/templates/change-proposal.md) |
| `specs/sidecar/exporter-guide.md` | The rules that exporters follow ([exporter guide](specs/sidecar/exporter-guide.md)) |
| `specs/sidecar-implementation-plan.md` | Status of the sidecar work in the package, and the procedure for reference examples |
| `notes/sidecar-exporter-coverage.md` | The plan that extended the spec to the exporter models: the evidence for the `vNEXT` revision |
| `notes/decisions/` | Decision log ([`README.md`](notes/decisions/README.md)) |
| `tools/` | `check_links.py` checks the relative links and their `#anchor` targets. `check_split_verbatim.py` checks that the split of the spec only moves text. Its input is `split_manifest.yaml`. The doc tests are in `tools/tests/`: the link check (`test_links.py`), the checks of the reference examples (`test_examples.py`) and the unit tests of the split checker (`test_check_split_verbatim.py`). |
| `rearchitecture-docs/` | Architecture notes for skellytracker and skellycam, and a rearchitecture playbook |
| `.github/workflows/` | CI: lint, fast tests, full tests, PyPI publish |

A detector module adds its class to a registry when Python imports the module.
The registry key is the `detector_type` of the detector config.
The sidecar paths in this table are under `skellytracker/core/detectors/`.

| Registry | `detector_type` | Class | Sidecar |
|---|---|---|---|
| keypoint | `aruco` | `ArucoDetector` | none |
| keypoint | `charuco` | `CharucoDetector` | none |
| keypoint | `mediapipe_pose`, `mediapipe_hand`, `mediapipe_face` | MediaPipe detectors | none |
| keypoint | `rtmpose` | `RTMWWholebodyDetector` | `keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml` |
| keypoint | `rtmpose_body`, `rtmpose_hand`, `rtmpose_face` | RTMPose detectors | `keypoint_detectors/rtmpose/<part>/rtmpose-<part>.yaml` |
| object | `yolox_person` | `YoloxPersonDetector` | `object_detectors/yolox/yolox.yaml` |
| object | `keypoint_bbox` | `KeypointBoundingBoxDetector` | none |

`PrecomputedObjectDetector` (`object_detectors/precomputed/`) is not in a registry.
The key `rtmpose` runs RTMW (decisions [0004](notes/decisions/0004-detectors-migrated-in-place.md)
and [0005](notes/decisions/0005-rtmw-moved-to-rtmw-family.md)).
All five package sidecars have `schema_version: "v2024.09.1019"`.

ONNX Runtime:

- `OnnxSessionConfig.execution_provider` in `skellytracker/core/sessions/onnx_session.py` selects the
  execution provider: `trt`, `cuda`, `coreml`, `directml` or `cpu`.
- When `execution_provider` is `None`, `OnnxSession.create` selects the first available provider in
  this order: `trt`, `cuda`, `coreml` (macOS only), `cpu` (`auto_detect_provider` in
  `skellytracker/core/sessions/ort_session_utils.py`).
- If you set a provider that is not available, `OnnxSession.create` raises `SessionCreationError`.
  It does not fall back to the CPU.
- On Windows, the `cuda` and `trt` providers load the CUDA and cuDNN DLLs from the `nvidia-*` pip
  packages (`_load_nvidia_dlls_on_windows` in `onnx_session.py`).

Code conventions:

- `skellytracker/__init__.py` calls `beartype_this_package()`. Runtime type checks apply to the whole
  package.
- Configs are Pydantic `BaseModel` subclasses. Trackers, stages and detectors are `@dataclass` classes.
- `black` and `isort` would change most package files. Do not run `black` or `isort` on the
  package. Do not reformat lines that your change does not need.

## 2. Skills

Load the skill that matches the task.
If your agent does not support skills, read the skill file.
Each skill is in `.claude/skills/<skill>/SKILL.md`.
The skills wrap the [exporter guide](specs/sidecar/exporter-guide.md) and the
[templates](specs/sidecar/templates/). They give the steps, the inputs, the outputs and the stop
points. The rules in this file also apply.
Exporter agents read the skill files in the read-only worktree
`../freemocap/skellytracker-latest/.claude/skills/`.

| Skill | Status | Runs in | Use it to |
|---|---|---|---|
| [`author-sidecar`](.claude/skills/author-sidecar/SKILL.md) | available | an exporter repo | Add a model: fill the model intake, write the sidecar and prove parity with the upstream library. Prepare the reference implementations of the sections that the exporter implements on its host side. |
| [`propose-sidecar-change`](.claude/skills/propose-sidecar-change/SKILL.md) | available | an exporter repo, or this repository | Write a spec change proposal for a model property that the spec does not describe exactly. In this repository, record it as a decision entry with status `proposed`. |
| [`change-sidecar-spec`](.claude/skills/change-sidecar-spec/SKILL.md) | available | this repository | Land a model, an accepted proposal or an exporter reference implementation. Change the normative spec text, its changelog, its vectors and its examples. |
| [`implement-sidecar-section`](.claude/skills/implement-sidecar-section/SKILL.md) | available | this repository | Implement a spec section in the package code, after the spec-build stage. In the spec-build stage, plan the work only. |

## 3. Install and Test

Run `uv sync --extra all-cpu`.
This command installs the dev tools, MediaPipe, `onnx` and the CPU build of ONNX Runtime.
For a GPU, [`GPU_SETUP_GUIDE.md`](GPU_SETUP_GUIDE.md) gives the extra for each GPU.
Use only one ONNX Runtime extra. The `onnx-*` extras conflict (`[tool.uv]` in `pyproject.toml`).
Use `uv run` for project commands.
Do not depend on an activated virtual environment.

Run `uv run pytest -m "not video"`.
This command runs the package tests and the doc tests. It does not run the slow video tests.
`testpaths` in `pyproject.toml` has `skellytracker/tests` and `tools/tests`.
`.github/workflows/tests-fast.yml` runs these tests on each push, on each PR into `main` or
`development`, and on a manual run.
On 2026-10-22, the workflow runs on `freemocap/skellytracker` end in `startup_failure`.
Link the passing CI run on the fork in each PR body (decision
[0015](notes/decisions/0015-review-discipline.md)).
These tests must pass.
Run `uv run pytest tools/tests` to run only the doc tests.
The doc tests check that each relative link and `#anchor` in `AGENTS.md`, `specs/` and `notes/`
resolves.

Run `uv run pytest -o faulthandler_timeout=300` to run all tests, with the video tests.
`.github/workflows/tests-full.yml` runs all tests on PRs into `main` and on a manual run.
The option `-o faulthandler_timeout=300` prints a stack trace when a test runs for more than 300 s.
On Windows, these video test groups are known to fail:

- The tests in `test_data_store.py` and `test_mediapipe_video.py` fail in setup. MediaPipe raises
  "Input timestamp must be monotonically increasing". These tests give no `timestamp_ms`, so the
  MediaPipe detectors use `int(time.monotonic() * 1000)` as the timestamp. On Windows,
  `time.monotonic()` has a resolution of 15.6 ms, so two frames can get the same timestamp. The
  item "MediaPipe timestamps on Windows" in the [open work](notes/decisions/README.md#open-work)
  records this code defect.
- In a run of all video tests, `test_process_video.py` does not finish. The stack trace shows that
  `PoseLandmarker.__del__` runs during `detect_for_video`, and that call does not return. The later
  video tests then do not run. When `test_process_video.py` runs alone, it passes.

To get the result of the other video tests on Windows, run each video test file alone.

Report each new test failure to the user.
Fix the failures of one root cause in one PR.
Do not put other changes in that PR (decision [0014](notes/decisions/0014-spec-lifecycle.md)).

The first test run needs network access.
`skellytracker/tests/conftest.py` downloads the test images and the test recording from the
`freemocap/skellysamples` releases on GitHub.
The ONNX detectors download their ONNX files to `~/.cache/skellytracker/models`.
The MediaPipe detectors download their model files to `~/.freemocap/skellytracker-models` (`CACHE_DIR`
in `skellytracker/core/detectors/keypoint_detectors/mediapipe/mediapipe_model_manager.py`).

Run `uv run ruff check skellytracker/ tools/`.
CI runs the same check (`.github/workflows/lint.yml`). CI also checks `specs/sidecar/reference/` when
that folder exists.

Run `uv run python -m skellytracker --list` to list the webcam demos.
Run `uv run python -m skellytracker --help` to see the demo options.
Without `--list` or `--help`, the command starts a live webcam demo (`cli_main` in
`skellytracker/__main__.py`).
The demo needs a camera and a display.

## 4. Sidecar Rules

- The section files under [`specs/sidecar/`](specs/sidecar/README.md) are normative. Read the sections
  that apply before you change a sidecar, an example or the spec.
- Link to the spec by its relative path. Do not link to a branch URL.
- Every spec change goes into the `vNEXT` revision until the first skellytracker release that ships the
  spec (decision [0014](notes/decisions/0014-spec-lifecycle.md)).
- `load_sidecar` rejects `schema_version: "vNEXT"` (`SidecarModel._check_schema_version_pattern` in
  `skellytracker/core/sidecar/model.py`). Do not publish a `vNEXT` sidecar to a shared or remote folder.
- The meaning of an older `schema_version` never changes. A sidecar with an older `schema_version`
  keeps its legacy meaning. The legacy rules are in the "Legacy behaviour" heading of each section.
  [Version-aware compatibility](specs/sidecar/format/versioning.md#version-aware-compatibility) gives
  the index of these headings.
- Make a spec change in the section file that owns the rule. The `id` in the front matter of the file
  is the section ID. The rule IDs of the section are `V-<id>-<n>`. When you move or reword a section,
  keep its section ID and its rule IDs (decision
  [0013](notes/decisions/0013-spec-structure.md#one-owner-for-each-rule)).
- A spec change needs a decision entry and a changelog row. Add a row to the
  [summary of changes](specs/sidecar/changelog.md#summary-of-changes). Add the change to the `vNEXT`
  row of the [changelog](specs/sidecar/changelog.md#schema_version-history).
- Stop on a gap. If a model property does not map exactly to a spec section, do not approximate it.
  A near-miss is a gap. Write a change proposal with the parts of
  [`specs/sidecar/templates/change-proposal.md`](specs/sidecar/templates/change-proposal.md). In this
  repository, record the proposal as a decision entry with status `proposed`. Then stop. The user
  accepts or rejects the proposal.
- Put one kind of change in each PR (decision
  [0015](notes/decisions/0015-review-discipline.md)). The kinds are: content (a change of normative
  meaning), move, rewording, and non-spec (decision log, agent files, tools, test vectors, guidance, CI,
  test fixes). A non-spec PR can also add an example that changes no normative meaning, with its
  provenance record. It can also add an exporter's reference implementation of the current spec
  text. A content PR also has the examples, vectors and reference implementations that define its
  new meaning. Put new content in a new PR on top of the PR stack. Never put it in a move PR or a
  rewording PR.
- Do not change implementation code under `skellytracker/` in the spec-build stage (decision
  [0014](notes/decisions/0014-spec-lifecycle.md)). You can change `skellytracker/tests/` to fix a
  test. Each root cause of a test failure gets its own PR. If a failure shows a code defect, report
  it. Do not fix the code in this stage.
- The [reference examples](specs/sidecar/examples/README.md) are part of the spec. To add or
  replace one, follow
  [Reference examples](specs/sidecar-implementation-plan.md#reference-examples) in
  `specs/sidecar-implementation-plan.md`.
- A sidecar goes in the path that the [storage layout](specs/sidecar/format/file-layout.md#storage-layout)
  gives.
- Do not change an exporter repository. You may read one.

## 5. Decision Log

Read [`notes/decisions/README.md`](notes/decisions/README.md) before you change sidecar code, a
sidecar, an example, the spec, the agent instructions or the PR workflow.
It records decisions and the evidence behind them.
It also has the open work, the rules and the entry template.
Then read the Active entries of the index that apply to your task.
Read a Historical entry only to find the reason for a decision.
Add one entry for each new decision or measurement.
Give the entry the next number after the highest existing entry.
Add the entry to the index in the same PR.
Do not rewrite the body of an old entry. Mark it superseded and add a new entry.
You may change the status line of an entry: `proposed` to `accepted` or `rejected`, and `accepted` to
`superseded by NNNN` or `absorbed into <path>#<anchor>`. Write the date and the PR that changed it.
Keep the log inside the limits of decision [0026](notes/decisions/0026-decision-log-size.md).
`uv run pytest tools/tests` checks the limits.
Cite tracked files, decision entries, commits on `development` or GitHub PR numbers.
Do not cite or link to `plans/`.
Until a commit is on `development`, cite its PR number and the file path. Do not cite its commit SHA.
Write the repository name before an entry number of another repository, for example
"OpenMMLab-Exporter 0020". A number without a repository name is an entry of this repository.

## 6. Git Rules

- `plans/` is a local working folder. Git ignores it. Do not commit it (decision
  [0001](notes/decisions/0001-decision-log-and-agents-md.md)).
- Do not push to a git remote without the approval of the user. One approval for a PR covers its push,
  its draft PR and its description.
- Ask the user before any other action that is visible outside this machine, for example a PR
  comment, a later change to a PR description or a change of a draft PR to ready. A force-push is a
  new push. It needs its own approval (decision [0015](notes/decisions/0015-review-discipline.md)).
- The local branch `dom/sidecar-latest` and the detached worktree `../skellytracker-latest` give
  exporter agents the top of the PR stack. After each push of a stacked branch, move the branch and
  the worktree to the new top of the stack. This needs no approval, because nothing leaves this
  machine. Do not push `dom/sidecar-latest`. Do not edit files in the worktree. Decision
  [0015](notes/decisions/0015-review-discipline.md) tells when to make the branch and the worktree,
  and gives the commands.
- Open each PR to `freemocap/skellytracker` against `development`. Decision
  [0015](notes/decisions/0015-review-discipline.md) gives the stacked draft workflow and the merge
  method.
- Do not change the commits of an open PR that other files cite. Do not add commits to it. Do not
  rebase it. #81 is such a PR: `specs/sidecar-implementation-plan.md` cites its commit SHAs
  (decision [0015](notes/decisions/0015-review-discipline.md)).

## 7. Tool Calls

Before a tool call that needs user permission, write a one-line summary of the call.
The summary must tell what the call does and what it changes.
Write the summary in the message text, not only in the tool description.

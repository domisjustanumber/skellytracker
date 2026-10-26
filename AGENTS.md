# Repository Instructions

Exporter agents: start from [`specs/draft/exporter-guide/README.md`](specs/draft/exporter-guide/README.md).
To add a model or to request a change to the sidecar spec, follow the
[model addition workflow](specs/model-sidecar/model-addition-workflow/README.md).
It is the same for an exporter agent and for a human contributor.
Exporter agents must not change files in this repository.

All new and changed documentation must use ASD-STE100 Simplified Technical English.
This rule applies to each `AGENTS.md`, skills, decision entries, templates, the model addition
workflow, the exporter guide and the sidecar spec.
Use short sentences. Use active voice. Use one instruction per sentence.
Use "must" for a requirement.
Keep technical names, field names, enum values, formulas, code and YAML unchanged.

This file holds the rules for each task. The other instructions load only when you need them
(ADR-[hxy8](notes/decisions/hxy8-scoped-agent-instructions.md)):

| Where | When it applies |
|---|---|
| [`skellytracker/AGENTS.md`](skellytracker/AGENTS.md) | Package code and tests: layout, detector registries, ONNX Runtime, code conventions, test notes |
| [`specs/model-sidecar/AGENTS.md`](specs/model-sidecar/AGENTS.md) | The sidecar spec, a sidecar or a reference example |
| [Skills](#2-skills) in `.claude/skills/` | One step of a task, for example a commit on the PR stack |

A rule that applies to one folder goes in the `AGENTS.md` of that folder.
A procedure for one step of a task goes in a skill.
Each `CLAUDE.md` only imports its `AGENTS.md`: its full content is `@AGENTS.md`.
Do not put instructions in a `CLAUDE.md`.

## 1. Purpose

skellytracker is the tracking backend for freemocap.
A `Tracker` runs its detection stages on each image. It returns an `Observation` and the new
`TrackerState`.
A `DetectionStage` has one optional object detector and one or more keypoint detectors.
A session holds the resources that detectors share, for example `OnnxSession` or `MediaPipeSession`.
A detector that runs an ONNX model reads a sidecar.
A sidecar is one YAML file. It describes the runtime contract of one model family: input,
preprocessing, outputs and decode.
The exporter repositories make ONNX files and write their sidecars: OpenMMLab-Exporter,
Roboflow-Exporter, Ultralytics-Exporter and Qualcomm-Exporter.

The spec is in its spec-build stage (ADR-[0014](notes/decisions/0014-spec-lifecycle.md)).
In this stage, the exporters add models and the spec changes.
Do not change the implementation code under `skellytracker/`.
The package layout, the detector registries and the code conventions are in
[`skellytracker/AGENTS.md`](skellytracker/AGENTS.md).

Read [`README.md`](README.md) for the install extras, the quick start and the API overview.
This file replaces the "Contributing" steps of `README.md`.

| Path | Role |
|---|---|
| `GPU_SETUP_GUIDE.md` | The install extra and the execution provider for each GPU |
| `pyproject.toml` | Dependencies, extras, the dev group, and the pytest, ruff and poe settings |
| [`specs/model-sidecar/README.md`](specs/model-sidecar/README.md) | Start of the sidecar spec: overview, [section map](specs/model-sidecar/README.md#section-map), index of validation rules. [`sidecar-spec.md`](specs/model-sidecar/sidecar-spec.md) is the permanent index with "Moved to" anchors. |
| `specs/model-sidecar/format/`, `common/`, `pre/`, `post/` | One section in each file. Front matter gives `id`, `title` and `kind`. Rule IDs are `V-<id>-<n>`. |
| `specs/model-sidecar/changelog.md` | The `vNEXT` summary of changes and the `schema_version` history |
| `specs/model-sidecar/proposals/` | Recorded spec change proposals and their [index](specs/model-sidecar/proposals/README.md) (ADR-[faac](notes/decisions/faac-proposal-records.md)). Informative. |
| `specs/model-sidecar/examples/`, `inventory.yaml` | Reference examples ([`README.md`](specs/model-sidecar/examples/README.md)) and their provenance |
| `specs/model-sidecar/templates/` | [`model-intake.md`](specs/model-sidecar/templates/model-intake.md) and [`change-proposal.md`](specs/model-sidecar/templates/change-proposal.md) |
| `specs/model-sidecar/model-addition-workflow/` | The process to add a model and to request a spec change. It is not a spec section and has no rule IDs (ADR-[x64y](notes/decisions/x64y-draft-exporter-guide-folder.md)). |
| `specs/draft/exporter-guide/` | The draft exporter guide. It is not complete. A local plan of the user owns it (ADR-[x64y](notes/decisions/x64y-draft-exporter-guide-folder.md)). |
| `specs/sidecar-implementation-plan.md` | Status of the sidecar work in the package. Tracked, not a local plan. It stays until its milestone M6 is done (ADR-[b9fm](notes/decisions/b9fm-finished-sidecar-plans.md)). |
| `notes/sidecar-exporter-coverage.md` | Frozen evidence for `vNEXT`. Proposals cite it by line number, so do not add or remove a line (ADR-[b9fm](notes/decisions/b9fm-finished-sidecar-plans.md)). |
| `notes/decisions/` | Decision log ([`README.md`](notes/decisions/README.md)) |
| `tools/` | Doc checks: links (`check_links.py`), private data (`check_private_data.py`), spec split (`check_split_verbatim.py`, input `split_manifest.yaml`), decision log, bootstrap kit. Tests in `tools/tests/`. |
| `specs/agents-and-adr-process/` | A bootstrap kit for a new repo: `AGENTS.md`, the decision log and the private-data checks (ADR-[0031](notes/decisions/0031-bootstrap-kit.md)) |
| `.github/workflows/` | CI: lint, fast tests, full tests, secret scan, PyPI publish |

## 2. Skills

Load the skill that matches the task.
If your agent does not support skills, read the file `.claude/skills/<skill>/SKILL.md`.
Git tracks `.claude/skills/` and ignores the rest of `.claude/`.
The rules in this file also apply.
Exporter agents read the skill files, read-only, in the checkout
`../freemocap/skellytracker/.claude/skills/`.

| Skill | Runs in | Use it to |
|---|---|---|
| [`author-sidecar`](.claude/skills/author-sidecar/SKILL.md) | an exporter repo | Add a model: the intake, the sidecar, parity and the host-side reference implementations |
| [`propose-sidecar-change`](.claude/skills/propose-sidecar-change/SKILL.md) | an exporter repo, or this repository | Write a spec change proposal for a near-miss or a gap, and record it as a `proposed` entry |
| [`change-sidecar-spec`](.claude/skills/change-sidecar-spec/SKILL.md) | this repository | Land a model, an accepted proposal or a reference implementation in the spec |
| [`implement-sidecar-section`](.claude/skills/implement-sidecar-section/SKILL.md) | this repository | Implement a spec section in the package code. In the spec-build stage, plan only. |
| [`stack-commit`](.claude/skills/stack-commit/SKILL.md) | this repository | Commit, rebase and push on the PR stack, and write a PR body |

## 3. Install and Test

Use `uv run` for project commands. Do not depend on an activated virtual environment.

```sh
uv sync --extra all-cpu                     # dev tools, MediaPipe, onnx, CPU ONNX Runtime
uv run pre-commit install                   # once per clone, and again after .pre-commit-config.yaml changes
uv run pytest -m "not video"                # package tests and doc tests; must pass
uv run pytest tools/tests                   # doc tests only: links, examples, decision log, private data
uv run pytest -o faulthandler_timeout=300   # all tests, with the video tests
uv run ruff check skellytracker/ tools/     # lint
uv run python -m skellytracker --list       # list the webcam demos (--help for the options)
```

- For a GPU, [`GPU_SETUP_GUIDE.md`](GPU_SETUP_GUIDE.md) gives the extra. Use only one ONNX Runtime
  extra. The `onnx-*` extras conflict (`[tool.uv]` in `pyproject.toml`).
- `pre-commit install` installs the pre-commit, commit-msg and pre-push hooks
  ([section 8](#8-private-data)).
- `tests-fast.yml` runs the fast tests on each push, on each PR into `main` or `development`, and on
  a manual run. `tests-full.yml` runs all tests on PRs into `main`. `lint.yml` runs ruff, also on
  `specs/model-sidecar/reference/` when it exists.
- The first test run needs network access. On Windows, some video tests fail
  ([`skellytracker/AGENTS.md`](skellytracker/AGENTS.md#tests)).
- Without `--list` or `--help`, `python -m skellytracker` starts a live webcam demo. It needs a
  camera and a display.
- Report each new test failure to the user. Fix the failures of one root cause in one PR. Do not put
  other changes in that PR (ADR-[0014](notes/decisions/0014-spec-lifecycle.md)).

## 4. Sidecar Rules

The sidecar rules are in [`specs/model-sidecar/AGENTS.md`](specs/model-sidecar/AGENTS.md).
Read them before you change a sidecar, an example or the spec.

## 5. Decision Log

Read [`notes/decisions/README.md`](notes/decisions/README.md) and
[`open-work.md`](notes/decisions/open-work.md) before you change sidecar code, a sidecar, an example,
the spec, the agent instructions or the PR workflow.
The [Rules](notes/decisions/README.md#rules) of the index give the read path, the entry IDs, the
allowed edits, the status changes, the limits and the citation rules.
Add one entry for each new decision or measurement.
Get its ID from `uv run python tools/check_decision_log.py --new`.
End each commit subject that adds or changes an entry with `(ADR-<id>)`.

The bootstrap kit in `specs/agents-and-adr-process/` is guidance, not a part of the sidecar spec.
It holds the final form of the rules of this decision log for a new repository.
Each kit copy is its live file with the text edits that `tools/sync_bootstrap_kit.py` lists.
When you change such a live file, run `uv run python tools/sync_bootstrap_kit.py --write`.
Commit the copy in the same PR.
The kit decision log must stay valid.
Change the kit templates by hand when a rule of this log changes.

## 6. Git Rules

- `plans/` is a local working folder. Git ignores it. Do not commit it. Do not cite or link to
  `plans/`, or cite the content of a plan.
- Do not push to a git remote without the approval of the user. One approval for a PR covers its
  push, its draft PR and its description.
- Ask the user before any other action that is visible outside this machine, for example a PR
  comment, a later change to a PR description or a change of a draft PR to ready. A force-push is a
  new push. It needs its own approval (ADR-[0027](notes/decisions/0027-single-working-branch.md)).
- Do not add AI attribution, for example a `Co-Authored-By:` trailer, to a commit or a PR.
- Commit only on the working branch `dom/sidecar-implementation`. Open PRs against `development`,
  not `main`.
- Keep the checkout `../freemocap/skellytracker` on the working branch. Exporter agents read the spec
  there. If the checkout is on a different branch, an exporter agent stops and asks the user.
- Before you commit, rebase, push or write a PR body, load the
  [`stack-commit`](.claude/skills/stack-commit/SKILL.md) skill.

## 7. Tool Calls

Before a tool call that needs user permission, write a one-line summary of the call.
The summary must tell what the call does and what it changes.
Write the summary in the message text, not only in the tool description.

## 8. Private Data

This repository is public, and git history is permanent
(ADR-[0030](notes/decisions/0030-no-private-data.md)).
Do not write these in a tracked file, a commit message or a PR body:

- a credential, a token, a password or a private key;
- an absolute path in a user folder;
- a hostname or a user name in prose;
- an email address that is not on the allowlist of `tools/check_private_data.py`;
- a private URL or a private IP address;
- a raw dump of `env`, `pip list`, `nvidia-smi` or `docker inspect`.

- Use paths relative to the repository, for example `../OpenMMLab-Exporter/notes/`.
- Give a measurement as a summary with its tool and its version.
- A report field or a test fake can contain a hostname.
- Text from `plans/` must obey these rules before it goes into a tracked file.
- To also block a hostname or a user name, put it in `.private-terms` in the repository root. Git
  ignores that file. Do not commit it.
- If you find private data in a tracked file, remove it with a redaction edit. Then tell the user,
  because git history keeps the data. Also revoke a leaked credential.
- The pre-commit hook runs `gitleaks` and `tools/check_private_data.py`. CI runs `gitleaks` on each
  push and PR. `.gitleaks.toml` holds the reviewed false positives.
- The commit-msg hook warns about AI attribution
  (ADR-[p3n3](notes/decisions/p3n3-ai-attribution-warning.md)). If you are an AI agent and you see
  this warning, tell the user.
- Turn on secret scanning and push protection for a private repository on the day that it becomes
  public.

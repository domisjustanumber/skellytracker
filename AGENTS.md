# Repository Instructions

Exporter agents: start from [`specs/draft/exporter-guide/README.md`](specs/draft/exporter-guide/README.md).
To add a model or to request a change to the sidecar spec, follow the
[model addition workflow](specs/model-sidecar/model-addition-workflow/README.md).
It is the same for an exporter agent and for a human contributor.
Exporter agents must not change files in this repository, except the new version folders of their
own bundles in `intakes/`. They run `pack` and `list` of `tools/intake_bundle.py` with Python 3.9 or
later and `python -B`. They run `pack --dry-run` and `batch` of the same tool and `fill` of
`tools/make_vectors.py` in the environment of this checkout, with
`uv run --project ../freemocap/skellytracker --no-sync python -B`.
`fill` writes only the given vector file, in the payload folder of their own bundle. They run
`fill` before `pack`.
These commands write no other file here
([ADR-ZXD7](decisions/entries/ZXD7-bundle-process.md);
[ADR-JAA4](decisions/entries/JAA4-one-batch-field.md);
[ADR-8DSW](decisions/entries/8DSW-vector-files-are-the-case-source.md)).
`fill` runs the code of its reference folder. Exporter agents run `fill` only with the reference
folder of their own bundle. `fill` refuses a folder of this checkout and a folder that is not the
`reference/` folder of the payload of the vector file
([ADR-AD33](decisions/entries/AD33-bundles-are-untrusted-input.md)).

<!-- kit:writing-rules -->
All new and changed documentation must use ASD-STE100 Simplified Technical English.
This rule applies to each `AGENTS.md`, skills, decision entries, templates, the model addition
workflow, the exporter guide and the sidecar spec.
Use short sentences. Use active voice. Use one instruction per sentence.
Use "must" for a requirement.
Keep technical names, field names, enum values, formulas, code and YAML unchanged.
<!-- /kit -->

This file holds the rules for each task. The other instructions load only when you need them
([ADR-GN3D](decisions/entries/GN3D-module-decision-logs.md)):

| Where | When it applies |
|---|---|
| [`skellytracker/AGENTS.md`](skellytracker/AGENTS.md) | Package code and tests: layout, detector registries, ONNX Runtime, code conventions, test notes |
| [`specs/model-sidecar/AGENTS.md`](specs/model-sidecar/AGENTS.md) | The sidecar spec, a sidecar or a reference example |
| [`specs/pipeline/AGENTS.md`](specs/pipeline/AGENTS.md) | The pipeline spec: the pipeline config format, its node types and its examples |
| [Skills](#2-skills) | One step of a task, for example a commit on the working branch |

A rule that applies to one folder goes in the `AGENTS.md` of that folder.
A folder with a nested `AGENTS.md` is a module.
When a rule moves out of this file, its heading stays here with a link to the new place
([ADR-2XW6](decisions/entries/2XW6-process-entries-consolidation.md)).
A procedure for one step of a task goes in a skill.
Each `CLAUDE.md` only imports its `AGENTS.md`: its full content is `@AGENTS.md`.
Do not put instructions in a `CLAUDE.md`.

## 1. Purpose

skellytracker is the tracking backend for freemocap. [`README.md`](README.md) gives the install
extras, the quick start and the API overview.
A detector that runs an ONNX model reads a sidecar: one YAML file that describes the runtime contract
of one model family. The spec starts at [`specs/model-sidecar/README.md`](specs/model-sidecar/README.md).
The exporter repositories make ONNX files and write their sidecars: OpenMMLab-Exporter,
Roboflow-Exporter, Ultralytics-Exporter and Qualcomm-Exporter.

The spec is in its spec-build stage ([Stages](specs/model-sidecar/model-addition-workflow/README.md#stages)).
In this stage, the exporters add models and the spec changes.
Do not change the implementation code under `skellytracker/`.

- The root [decision log](decisions/README.md) is in `decisions/`. The sidecar spec has its own
  [log](specs/model-sidecar/decisions/README.md) in `specs/model-sidecar/decisions/`
  ([section 5](#5-decision-log)).
- The files under `specs/model-sidecar/proposals/` are informative records. Each record is a byte copy
  of a hand-over bundle version ([Tracked records](specs/model-sidecar/model-addition-workflow/hand-over.md#tracked-records);
  [ADR-ZXD7](decisions/entries/ZXD7-bundle-process.md)).
- `specs/draft/exporter-guide/` is not complete. A local plan of the user owns it
  (ADR-[x64y](decisions/entries/x64y-draft-exporter-guide-folder.md)).
- `specs/sidecar-implementation-plan.md` is a tracked file, not a local plan. It holds the
  implementation-stage work. It stays until the user decides to delete it
  ([ADR-5WKW](decisions/entries/5WKW-implementation-work-in-the-plan.md)). Its heading "Reference
  examples" stays as a "Moved to" stub
  ([ADR-2XW6](decisions/entries/2XW6-process-entries-consolidation.md)).
- `notes/sidecar-exporter-coverage.md` is frozen evidence
  ([ADR-5WKW](decisions/entries/5WKW-implementation-work-in-the-plan.md)).

## 2. Skills

<!-- kit:skills -->
Load the skill that matches the task.
If your agent does not support skills, read the file `.claude/skills/<skill>/SKILL.md`.
Git tracks `.claude/skills/` and ignores the rest of `.claude/`.
The rules in this file also apply.
<!-- /kit -->
Exporter agents read the skill files, read-only, in the checkout
`../freemocap/skellytracker/.claude/skills/`.
Each skill or workflow step that runs a tool on bundle content gives the safety check of
[Session steps](specs/model-sidecar/model-addition-workflow/hand-over.md#session-steps) before the
run ([ADR-AD33](decisions/entries/AD33-bundles-are-untrusted-input.md)).

| Skill | Runs in | Use it to |
|---|---|---|
| [`author-sidecar`](.claude/skills/author-sidecar/SKILL.md) | an exporter repo | Add a model: the intake, the sidecar, parity and the host-side reference implementations |
| [`propose-sidecar-change`](.claude/skills/propose-sidecar-change/SKILL.md) | an exporter repo, or this repository | Write a spec change proposal for a near-miss or a gap, and record it as a `proposed` entry |
| [`change-sidecar-spec`](.claude/skills/change-sidecar-spec/SKILL.md) | this repository | Land a model, an accepted proposal or a reference implementation in the spec |
| [`implement-sidecar-section`](.claude/skills/implement-sidecar-section/SKILL.md) | this repository | Implement a spec section in the package code. In the spec-build stage, plan only. |
| [`change-pipeline-spec`](.claude/skills/change-pipeline-spec/SKILL.md) | this repository | Land a pipeline bundle or an accepted node proposal, or update pinned sidecar hashes after a re-export |
| [`implement-pipeline-node`](.claude/skills/implement-pipeline-node/SKILL.md) | this repository | Implement a node type of the pipeline spec in the package code. In the spec-build stage, plan only. |
| [`stack-commit`](.claude/skills/stack-commit/SKILL.md) | this repository | Commit, rebase and push on the working branch, and write a PR body |
| [`cite-entries`](.claude/skills/cite-entries/SKILL.md) | this repository | Cite decision entries in a reply, a plan, a PR body or a commit message |
| [`ask-the-user`](.claude/skills/ask-the-user/SKILL.md) | this repository | Ask the user a question or give options, with an example and a source for each |
| [`brief-subagent`](.claude/skills/brief-subagent/SKILL.md) | this repository | Brief a sub-agent, and check its `path:line` claims before you use them |

## 3. Install and Test

Use `uv run` for project commands. Do not depend on an activated virtual environment.

```sh
uv sync --extra all-cpu                     # dev tools, MediaPipe, onnx, CPU ONNX Runtime
uv run pre-commit install                   # hooks; once per clone, and again after .pre-commit-config.yaml changes
uv run python tools/run_checks.py           # the checks before each commit; stops at the first failure
uv run python tools/graphify_hooks.py install  # optional code graph; in each checkout, and again after tools/graphify_hook.sh changes
uv run pytest -m "not video"                # package tests and doc tests; must pass
uv run pytest tools/tests                   # doc tests only: links, examples, decision log, private data
uv run pytest -o faulthandler_timeout=300   # all tests, with the video tests
uv run ruff check skellytracker/ tools/ decisions/scripts/ specs/model-sidecar/decisions/scripts/ specs/model-sidecar/reference/ specs/pipeline/reference/  # lint
```

- `uv run python -m skellytracker` starts a live webcam demo. Do not run it without a camera and a
  display.
- The first test run needs network access. On Windows, some video tests fail, and the
  `-m "not video"` run can stop in the MediaPipe tests.
  [`skellytracker/AGENTS.md`](skellytracker/AGENTS.md#tests) gives the known failures and the split run.
- Report each new test or CI failure to the user. Fix the failures of one root cause in one PR. Do
  not put other changes in that PR. In the spec-build stage, the fix is its own commit on the working branch. Do not ask for the branch
  ([ADR-R39S](decisions/entries/R39S-test-fix-on-the-working-branch.md)).
- graphify is an optional local tool ([ADR-87B2](decisions/entries/87B2-local-graphify-code-graph.md)).
  It keeps a code graph in `graphify-out/` in the root of a checkout. Git ignores this folder.
  Do not commit a file from it. Git hooks update the graph after each commit, checkout, merge and
  rebase.
- If `graphify-out/graph.json` exists, run `uvx --from graphifyy==0.9.100 graphify query "<question>"`
  before you search the code. The subcommands `path "A" "B"` and `explain "X"` are also available.
  Run each `graphify` command of this section with the prefix `uvx --from graphifyy==0.9.100`.
  The graph can be older than the working tree. Read a file before you change it.
- Do not run `graphify install`, `graphify hook install` or a `graphify <agent> install` command.
  They write to `CLAUDE.md`, `AGENTS.md`, `.gitattributes`, the git config or agent settings.
- Do not run `/graphify`, `graphify extract`, `graphify label` or `graphify add` without the approval
  of the user. They can send files to an LLM or fetch URLs.

## 4. Sidecar Rules

The sidecar rules are in [`specs/model-sidecar/AGENTS.md`](specs/model-sidecar/AGENTS.md).
Read them before you change a sidecar, an example or the spec.

## 5. Decision Log

Read [`decisions/README.md`](decisions/README.md) and
[`open-work.md`](decisions/open-work.md) before you change sidecar code, a sidecar, an example,
the spec, the agent instructions or the PR workflow.
For spec work, also read the [`README.md`](specs/model-sidecar/decisions/README.md) and the
[`open-work.md`](specs/model-sidecar/decisions/open-work.md) of the spec log in
`specs/model-sidecar/decisions/`.
For a task in another module with a log, also read the `README.md` and the `open-work.md` of that
log. The `AGENTS.md` of a module with a log links to that log.
An entry goes in the log of a module only when each file that its Decision section names or changes
is in that module, for example `specs/model-sidecar/` for the spec log
([ADR-2XW6](decisions/entries/2XW6-process-entries-consolidation.md)).
All other entries go in the root log, also each case that you cannot decide.
A new module log needs the approval of the user. The PR that adds it also adds its folder to
`LOG_DIRS` of `tools/check_decision_log.py`.
Each log has a `README.md` with an Active table, a Proposed table and `## Open work`, a
`historical.md`, an `open-work.md` and its entry files in `entries/`
([ADR-QPS7](decisions/entries/QPS7-decision-entries-in-an-entries-folder.md)). The Rules and `template.md` are only in the root log.
All logs have one ID space. Do not add a module name to an ID.
When the scope of a module entry grows to more than one module, a new root entry supersedes it
([ADR-GN3D](decisions/entries/GN3D-module-decision-logs.md)).
A tool is code that a test, a hook, a CI job, a skill or a workflow step runs, or code that writes a
tracked file. It is in the root `tools/`, also when only one module uses it. It has tests.
A script made the evidence for an entry or did its one-off job, and the entry names it. It is in
`scripts/` of the log that holds the entry. Its own tests, if any, are in `scripts/tests/`.
A script does not change after its entry is decided. When a step starts to run it, move it to
`tools/` and add a test ([ADR-EY8R](decisions/entries/EY8R-tools-and-scripts.md)).
The [Rules](decisions/README.md#rules) of the index give the allowed edits, the status changes and
the other rules that an agent needs and that no tool checks and no loaded document states. `tools/check_decision_log.py` checks the tables, the IDs and the
limits ([ADR-Z05A](decisions/entries/Z05A-essential-decision-log-rules.md)).
Add one entry for each new decision or measurement.
Get its ID from `uv run python tools/check_decision_log.py --new`.
End each commit subject that adds or changes an entry with `(ADR-<ID>)`.
Cite each entry as a Markdown link with `ADR-<ID>` as the link text, in upper case, for example
[ADR-JB5J](decisions/entries/JB5J-one-batch-form-for-each-sidecar.md).
This rule applies to each text that you write: a tracked file, a plan, a PR body and a reply to the
user. In a reply or a plan, the path is relative to the repository root or to the file.
This rule also applies to an older entry with a lower-case file name.
A template in `specs/model-sidecar/templates/` cites a skellytracker entry as `skellytracker ADR-<ID>`,
with no link, because its copies leave this repository
([ADR-ESP4](decisions/entries/ESP4-one-home-for-each-workflow-rule.md)).
A commit message cannot hold a working link. In the commit body, write `ADR-<ID>` with no link.
Cite an entry of another repository with the repository name and `ADR-<ID>`. Also link it with a
full-SHA permalink when the entry is on the default branch of that repository
([ADR-Z05A](decisions/entries/Z05A-essential-decision-log-rules.md); see the
[Rules](decisions/README.md#rules)).

The bootstrap kit is in `agents-and-adr-process/` of the
[freemocap/project](https://github.com/freemocap/project) repository. It is guidance, not a part
of the sidecar spec.
It holds the final form of the rules of this decision log for a new repository.
The kit keeps no rule that this repository does not state.
A new repository starts with one `AGENTS.md` and one log. A repository with modules also takes the
nested `AGENTS.md` files, the `CLAUDE.md` files and the module-log rules.
Clone that repository to `../project`, or put this repository in its `repos/` folder.
`tools/sync_bootstrap_kit.py` stays in this repository. It is the reference implementation of
the kit sync ([ADR-P3NK](decisions/entries/P3NK-bootstrap-kit-in-freemocap-project.md)).
Each kit copy is its live file with the text edits that `tools/sync_bootstrap_kit.py` lists.
The kit templates also hold blocks of the live files: whole sections, and the text between the
lines `<!-- kit:<name> -->` and `<!-- /kit -->`. The tool lists them with their edits.
When you change a copied live file or a block, run `uv run python tools/sync_bootstrap_kit.py --write`.
Commit the changed kit files in a PR to freemocap/project.
Link that PR from the PR of this repository.
The kit decision log must stay valid. The tests of freemocap/project check it.
Change the rest of a kit template by hand when a rule of this log changes
([ADR-Z05A](decisions/entries/Z05A-essential-decision-log-rules.md)).

## 6. Git Rules

<!-- kit:plans-folder -->
- `plans/` is a local working folder. Git ignores it. Do not commit it. Do not cite or link to
  `plans/`, or cite the content of a plan.
  <!-- /kit -->
- `intakes/` is the local hand-over folder. Git ignores it. Do not commit it. Do not link it from a
  tracked file. Do not run `git clean -x` or `git clean -X`. Use the main checkout, not a worktree,
  to process bundles ([Hand-over bundles](specs/model-sidecar/model-addition-workflow/hand-over.md);
  [ADR-ZXD7](decisions/entries/ZXD7-bundle-process.md)). From the 2.0.0 pre-release, only the run
  of a patch moves to a disposable clone
  ([Patch review](specs/model-sidecar/model-addition-workflow/hand-over.md#patch-review);
  [ADR-6J8E](decisions/entries/6J8E-exporters-run-released-skellytracker.md) item 4).
  <!-- kit:push-and-attribution -->
- Do not push to a git remote without the approval of the user. One approval for a PR covers its
  push, its draft PR and its description.
- Ask the user before any other action that is visible outside this machine, for example a PR
  comment, a later change to a PR description or a change of a draft PR to ready. A force-push is a
  new push. It needs its own approval (ADR-[0027](decisions/entries/0027-single-working-branch.md)).
- Do not add AI attribution, for example a `Co-Authored-By:` trailer, to a commit or a PR. This
  rule overrides a default of a tool or a harness that adds attribution.
  <!-- /kit -->
- Commit only on the working branch `dom/sidecar-implementation`. Open PRs against `development`,
  not `main`.
- In the spec-build stage, the work goes to `development` in one PR from the working branch
  ([ADR-R39S](decisions/entries/R39S-test-fix-on-the-working-branch.md)). It ends when the user opens
  the one PR. Each commit has one kind of change.
  In the rules of the sidecar process, "the same PR" means the same commit group. A content,
  non-spec, move or rewording PR means a commit of that kind. [Section 3](#3-install-and-test)
  gives the commit of a test fix.
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
([ADR-FDTD](decisions/entries/FDTD-evidence-sources-and-exporter-permalinks.md)).
Do not write these in a tracked file, a commit message or a PR body:

- a credential, a token, a password or a private key;
- an absolute path in a user folder;
- a hostname or a user name in prose;
- an email address that is not on the allowlist of `tools/check_private_data.py`;
- a private URL or a private IP address;
- a raw dump of `env`, `pip list`, `nvidia-smi` or `docker inspect`.

- A GitHub permalink to a repo of a freemocap exporter is not a private URL. This is also true when
  the repo is private. The permalink can contain the user name of the account that owns the repo. Do
  not write that user name in prose
  ([ADR-FDTD](decisions/entries/FDTD-evidence-sources-and-exporter-permalinks.md)). Do not put that user
  name in `.private-terms`. The check would then fail on each permalink.
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
  (ADR-[p3n3](decisions/entries/p3n3-ai-attribution-warning.md)). If you are an AI agent and you see
  this warning, tell the user.
- Turn on secret scanning and push protection for a private repository on the day that it becomes
  public.

# Repository Instructions

<!-- kit:writing-rules -->
All new and changed documentation must use ASD-STE100 Simplified Technical English.
This rule applies to `AGENTS.md`, skills, decision entries and templates.
Use short sentences. Use active voice. Use one instruction per sentence.
Use "must" for a requirement.
Keep technical names, field names, values, formulas, code and YAML unchanged.
<!-- /kit -->

## 1. Purpose

{{PROJECT_PURPOSE: one paragraph. What the project does, who uses it, and its main parts.}}

| Path | Role |
|---|---|
| `AGENTS.md` | The root instructions file for coding agents |
| `CLAUDE.md` | Imports this file. It has no other content. |
| `decisions/` | Decision log ([`README.md`](decisions/README.md)) and its open work ([`open-work.md`](decisions/open-work.md)) |
| `tools/` | The doc checks: `check_decision_log.py`, `check_links.py` and `check_private_data.py`. Their tests are in `tools/tests/`. |
| `plans/` | A local working folder. Git ignores it. |
| `{{MODULE}}/` | {{MODULE_ROLE}}. Its `AGENTS.md` holds the rules for the work in it. Its log is in `{{MODULE}}/decisions/`. |
| {{PATH}} | {{ROLE}} |

## 2. Skills

<!-- kit:skills -->
Load the skill that matches the task.
If your agent does not support skills, read the file `.claude/skills/<skill>/SKILL.md`.
The rules in this file also apply.
<!-- /kit -->

| Skill | Use it to |
|---|---|
| {{SKILL_NAME}} | {{WHEN_TO_USE_IT}} |

## 3. Install and Test

Run `{{INSTALL_COMMAND, for example uv sync}}`.
Then run `uv run pre-commit install` once in the clone ([section 8](#8-private-data)).
It installs the pre-commit hooks, the commit-msg hook and the pre-push hook.
Run it again in each clone after `.pre-commit-config.yaml` changes.
Use `uv run` for project commands.
Do not depend on an activated virtual environment.

Run `{{TEST_COMMAND, for example uv run pytest}}`.
These tests must pass.
Run `uv run pytest tools/tests` to run only the doc checks.
The doc checks test the decision log, the relative links and the private-data rule.
Report each new test failure to the user.
Fix the failures of one root cause in one PR.

## 4. Project Rules

{{PROJECT_RULES: the code conventions, the dependency rules and the contracts of this project. Write
one instruction on each line.}}
Do not change code that your task does not need.

## 5. Decision Log

Read [`decisions/README.md`](decisions/README.md) and
[`open-work.md`](decisions/open-work.md) before you change {{AREAS}} or these instructions.
For a task in a module with a log, also read the `decisions/README.md` and the
`decisions/open-work.md` of that module. The `AGENTS.md` of the module links to its log.
An entry goes in the log of a module only when each file that its Decision section names or
changes is in that module. All other entries go in the root log, also each case that you cannot decide.
A new module log needs the approval of the user. The PR that adds it also adds its folder to
`LOG_DIRS` of `tools/check_decision_log.py`.
Each log has a `README.md` with an Active table, a Proposed table and `## Open work`, a
`historical.md` and an `open-work.md`. The Rules and `template.md` are only in the root log.
All logs have one ID space. Do not add a module name to an ID.
When the scope of a module entry grows to more than one module, a new root entry supersedes it.
A tool is code that a test, a hook, a CI job, a skill or a workflow step runs, or code that writes a
tracked file. It is in the root `tools/`, also when only one module uses it. It has tests.
A script made the evidence for an entry or did its one-off job, and the entry names it. It is in
`scripts/` of the log that holds the entry. Its own tests, if any, are in `scripts/tests/`.
A script does not change after its entry is decided. When a step starts to run it, move it to
`tools/` and add a test.
The [Rules](decisions/README.md#rules) of the index give the allowed edits, the status changes and
the rules that no tool checks. `tools/check_decision_log.py` checks the tables, the IDs and the
limits.
Add one entry for each new decision or measurement.
Get its ID from `uv run python tools/check_decision_log.py --new`.
End each commit subject that adds or changes an entry with `(ADR-<ID>)`.
Cite each entry as a Markdown link with `ADR-<ID>` as the link text, in upper case, for example
[ADR-0001](decisions/0001-decision-log-agents-md-and-private-data.md).
This rule applies to each text that you write: a tracked file, a plan, a PR body and a reply to the
user. In a reply or a plan, the path is relative to the repository root or to the file.
A commit message cannot hold a working link. In the commit body, write `ADR-<ID>` with no link.
Cite an entry of another repository with the repository name and `ADR-<ID>`. Also link it with a
full-SHA permalink when the entry is on the default branch of that repository
(see the [Rules](decisions/README.md#rules)).

## 6. Git Rules

<!-- kit:plans-folder -->
- `plans/` is a local working folder. Git ignores it. Do not commit it. Do not cite or link to
  `plans/`, or cite the content of a plan
  ([ADR-0001](decisions/0001-decision-log-agents-md-and-private-data.md)).
  <!-- /kit -->
  <!-- kit:push-and-attribution -->
- Do not push to a git remote without the approval of the user. One approval for a PR covers its
  push, its draft PR and its description.
- Ask the user before any other action that is visible outside this machine, for example a PR
  comment, a later change to a PR description, a change of a draft PR to ready, a release or a
  published image. A force-push is a new push. It needs its own approval.
- Do not add AI attribution, for example a `Co-Authored-By:` trailer, to a commit or a PR.
  <!-- /kit -->
- Open each PR against `{{DEFAULT_BRANCH}}`.
- Put one kind of change in each PR: {{CHANGE_KINDS, for example "code", "docs" and "CI"}}.

## 7. Tool Calls

Before a tool call that needs user permission, write a one-line summary of the call.
The summary must tell what the call does and what it changes.
Write the summary in the message text, not only in the tool description.

## 8. Private Data

This repository is public, or it can become public. Git history is permanent
([ADR-0001](decisions/0001-decision-log-agents-md-and-private-data.md)).
Do not write these in a tracked file, a commit message or a PR body:

- a credential, a token, a password or a private key;
- an absolute path in a user folder;
- a hostname or a user name in prose;
- an email address that is not on the allowlist of `tools/check_private_data.py`;
- a private URL or a private IP address;
- a raw dump of `env`, `pip list`, `nvidia-smi` or `docker inspect`.

- Use paths relative to the repository, for example `../{{SIBLING_REPO}}/notes/`.
- Give a measurement as a summary with its tool and its version.
- A report field or a test fake can contain a hostname.
- Text from `plans/` must obey these rules before it goes into a tracked file.
- To also block a hostname or a user name, put it in `.private-terms` in the repository root. Git
  ignores that file. Do not commit it.
- If you find private data in a tracked file, remove it with a redaction edit. Then tell the user,
  because git history keeps the data. Also revoke a leaked credential.
- The pre-commit hook runs `gitleaks` and `tools/check_private_data.py`. CI runs `gitleaks` on each
  push and PR. `.gitleaks.toml` holds the reviewed false positives.
- The commit-msg hook warns about AI attribution. If you are an AI agent and you see
  this warning, tell the user.
- Turn on secret scanning and push protection for a private repository on the day that it becomes
  public.

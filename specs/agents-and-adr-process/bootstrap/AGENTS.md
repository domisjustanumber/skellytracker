# Repository Instructions

All new and changed documentation must use ASD-STE100 Simplified Technical English.
This rule applies to `AGENTS.md`, skills, decision entries and templates.
Use short sentences. Use active voice. Use one instruction per sentence.
Use "must" for a requirement.
Keep technical names, field names, values, formulas, code and YAML unchanged.

## 1. Purpose

{{PROJECT_PURPOSE: one paragraph. What the project does, who uses it, and its main parts.}}

| Path | Role |
|---|---|
| `AGENTS.md` | The single instructions file for coding agents |
| `CLAUDE.md` | Imports this file. It has no other content. |
| `notes/decisions/` | Decision log ([`README.md`](notes/decisions/README.md)) and its open work ([`open-work.md`](notes/decisions/open-work.md)) |
| `tools/` | The doc checks: `check_decision_log.py`, `check_links.py` and `check_private_data.py`. Their tests are in `tools/tests/`. |
| `plans/` | A local working folder. Git ignores it. |
| {{PATH}} | {{ROLE}} |

## 2. Skills

Load the skill that matches the task.
If your agent does not support skills, read the skill file.
Each skill is in `.claude/skills/<skill>/SKILL.md`.
The rules in this file also apply.

| Skill | Use it to |
|---|---|
| {{SKILL_NAME}} | {{WHEN_TO_USE_IT}} |

## 3. Install and Test

Run `{{INSTALL_COMMAND, for example uv sync}}`.
Then run `uv run pre-commit install` once in the clone ([section 8](#8-private-data)).
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

Read [`notes/decisions/README.md`](notes/decisions/README.md) and
[`notes/decisions/open-work.md`](notes/decisions/open-work.md) before you change {{AREAS}} or these
instructions.
The log records decisions and the evidence behind them.
Then read the Active entries of the index that apply to your task.
Read a Deferred entry only for work in its area.
Read a Historical entry only to find the reason for a decision.
Add one entry for each new decision or measurement.
Before you add an entry, run `git fetch`.
Then run `uv run python tools/check_decision_log.py --next`.
Give the entry the number of the `next:` line.
Create the entry file immediately.
Add its index row at the end of the table for its status, in the same PR.
The number is provisional until the entry is on `{{DEFAULT_BRANCH}}`.
Run `--next` again before each push.
Act on each `renumber:` line. The index [Rules](notes/decisions/README.md#rules) give the steps.
Do not change a provisional number for a different reason, except when `{{DEFAULT_BRANCH}}` already
has the number.
Do not keep two index rows with one number when you resolve a merge conflict.
Do not rewrite the body of an entry that is not `proposed`.
Four edits are allowed: a link or anchor repair, a typo fix that keeps the meaning, the redaction of
private data, and a renumber with the repair of its citations.
Each of these edits adds an `_Edited_` line with the date and the PR.
To change a decision, add a new entry. It restates the rules that stay and supersedes the old entry
in full.
Do not supersede a part of an entry.
Keep the log inside its limits. `uv run pytest tools/tests` checks them.
Cite tracked files and decision entries with relative links.
Cite a commit, or the code of another repository, with a GitHub permalink.
The permalink must pin a full SHA on the default branch of that repository.
Do not put dated status lines in this file. Put them in the open work or in an entry.
Do not cite or link to `plans/`.
Write the repository name before an entry number of another repository, for example
"{{OTHER_REPO}} 0020". A number without a repository name is an entry of this repository.
Cite a provisional entry of another repository by the repository name, the PR number and the slug.
Do not import a file, a test or a tool from another repository.

## 6. Git Rules

- `plans/` is a local working folder. Git ignores it. Do not commit it (decision
  [0001](notes/decisions/0001-decision-log-agents-md-and-private-data.md)).
- Do not push to a git remote without the approval of the user.
- Ask the user before any other action that is visible outside this machine, for example a PR, a
  PR comment, a release or a published image.
- Open each PR against `{{DEFAULT_BRANCH}}`.
- Put one kind of change in each PR: {{CHANGE_KINDS, for example "code", "docs" and "CI"}}.

## 7. Tool Calls

Before a tool call that needs user permission, write a one-line summary of the call.
The summary must tell what the call does and what it changes.
Write the summary in the message text, not only in the tool description.

## 8. Private Data

This repository is public, or it can become public. Git history is permanent (decision
[0001](notes/decisions/0001-decision-log-agents-md-and-private-data.md)).
Do not write these in a tracked file, a commit message or a PR body:

- a credential, a token, a password or a private key;
- an absolute path in a user folder;
- a hostname or a user name in prose;
- an email address that is not on the allowlist of `tools/check_private_data.py`;
- a private URL or a private IP address;
- a raw dump of `env`, `pip list`, `nvidia-smi` or `docker inspect`.

Use paths relative to the repository, for example `../{{SIBLING_REPO}}/notes/`.
Give a measurement as a summary with its tool and its version.
Text from `plans/` must obey these rules before it goes into a tracked file.
If you find private data in a tracked file, remove it with a redaction edit.
Then tell the user, because git history keeps the data.

`uv run pytest tools/tests` runs `tools/check_private_data.py`.
To also block a hostname or a user name, put it in the file `.private-terms` in the repository root.
Git ignores that file. Do not commit it.
The pre-commit hook runs `gitleaks` and the private-data check.
`.github/workflows/secrets.yml` runs `gitleaks` on each push and PR.

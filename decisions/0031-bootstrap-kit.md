# 0031 — A bootstrap kit for `AGENTS.md` and the decision log

**Status:** absorbed into [`AGENTS.md#5-decision-log`](../AGENTS.md#5-decision-log), 2026-10-25 (user; the absorption review); superseded by [Z05A](Z05A-essential-decision-log-rules.md), 2026-10-29 (user; PR: pending).

## Decision

1. **The kit.** [`specs/agents-and-adr-process/`](../specs/agents-and-adr-process/README.md) holds
   a guide and a kit of files for a coding agent that creates a new repo. The guide gives the
   procedure, the rules and their reasons. The kit folder `bootstrap/` has the layout of the new
   repo. The kit is guidance. It is not a part of the sidecar spec, so it has no section ID and no
   changelog row.
2. **Its content.** The kit has the final form of the rules of
   [0001](0001-decision-log-and-agents-md.md), [0028](0028-entry-edits-and-citations.md),
   [0029](0029-decision-log-read-path.md) and [0030](0030-no-private-data.md). In the new repo, its
   entry 0001 records all of them. The guide also gives triggers for new tests. They are guidance.
   This repo has no decision on them yet.
3. **Copies.** The tools and the configs of the kit are copies of the live files of this repo, with
   exact text edits that remove the parts that belong only to this repo.
   [`tools/sync_bootstrap_kit.py`](../tools/sync_bootstrap_kit.py) lists each copy and its edits.
   `--write` writes the copies again. `--check` fails when a copy differs from its live file.
4. **The same PR.** A PR that changes a live file of the list also runs `--write` and commits the
   copy.
5. **Tests.** [`tools/tests/test_bootstrap_kit.py`](../tools/tests/test_bootstrap_kit.py) runs
   `--check`. It also runs the copied decision-log check on the kit, so the decision log of the kit
   must stay valid. The link test and the private-data test of this repo already cover the kit
   files.
6. **Templates.** `AGENTS.md`, `CLAUDE.md`, the kit decision log, `gitignore-additions.txt` and
   `doc-checks.yml` are templates with `{{...}}` placeholders. Change them by hand when a rule of
   this log changes.

## Reason

- The user asked for a document that an agent can use to start a new repo, with files to copy where
  possible (2026-10-24).
- A copy goes out of date when its live file changes. A test that rebuilds each copy from its live
  file finds the difference in the PR that makes it.
- An exact text edit shows what differs from the live file. A free rewrite of the copy hides it.
- The kit puts each file at the path that it has in the new repo. Then the relative links of the kit
  resolve in this repo too, and the link test checks them.

## Consequences

- A change to a live tool or config costs one more command and one more file in its PR.
- An edit of the list fails when its text no longer occurs exactly once in the live file. Then the
  maintainer must update the edit.

## Alternatives rejected

- **Link to the live files instead of copies.** The live files have parts that belong only to this
  repo, for example an allowlist entry and decision numbers. A new repo can also have no checkout of
  this repo.
- **A generator that writes a complete new repo.** It is more code, and an agent must still adapt
  the result to the project.
- **Copies with no check.** They go out of date with no signal.

_Edited 2026-10-28 (this PR): link repair._

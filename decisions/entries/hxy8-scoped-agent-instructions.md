# hxy8 — Core `AGENTS.md`, nested `AGENTS.md` files for one folder, and procedures as skills

**Status:** superseded by [GN3D](GN3D-module-decision-logs.md), 2026-10-28 (user; PR: pending).

## Decision

This entry supersedes [0001](0001-decision-log-and-agents-md.md) in full. It restates the rules of
0001 that stay.

1. **Core file.** The root `AGENTS.md` holds the rules that apply to each task: the purpose, the
   commands, the git rules that stop a wrong push, private data and the tool-call rule. It also tells
   where the other instructions are.
2. **Nested files.** A rule that applies only to the work in one folder goes in an `AGENTS.md` in that
   folder. Today these files are `skellytracker/AGENTS.md` (package code and tests) and
   `specs/model-sidecar/AGENTS.md` (the sidecar rules).
3. **`CLAUDE.md` only imports.** Each folder with an `AGENTS.md` has a `CLAUDE.md`. Its full content
   is `@AGENTS.md`. Do not put instructions in a `CLAUDE.md`.
4. **Skills.** A procedure that applies at one step of a task is a skill in `.claude/skills/`, for
   example `stack-commit` for the commit, rebase and push steps of the PR stack. Git tracks that
   folder and ignores the rest of `.claude/`. An agent that does not support skills reads the skill
   file.
5. **Old headings stay.** When a rule moves out of the root `AGENTS.md`, its heading stays with a link
   to the new place. Absorbed entries and skills link to these headings.
6. **Absorbing documents.** A nested `AGENTS.md` is an absorbing document, the same as the root file.
7. **Decision log.** This repo keeps a decision log in `notes/decisions/`. A decision that code, the
   spec or another document refers to must be in an entry.
8. **`plans/`.** `plans/` is a local working folder. Git ignores it. Do not commit it. A tracked file
   does not link to `plans/` and does not cite the content of a plan: its sections, its item numbers
   or its local PR labels.
9. **Implementation plan.** `specs/sidecar-implementation-plan.md` is a tracked file, not a local
   plan. ADR-[b9fm](b9fm-finished-sidecar-plans.md) gives the time that it stays.
10. **Bootstrap kit.** The kit does not take rules 1 to 6. A new repo starts with one `AGENTS.md`.

## Reason

- Before this entry, `AGENTS.md` had 454 lines and 4,639 words (`wc`, GNU coreutils). Each task
  loaded all of it. Most tasks used one or two sections. The registry table, the ONNX Runtime notes
  and the rebase steps applied only to package work or to a push.
- Claude Code loads a nested `CLAUDE.md` when it reads a file in that folder. Codex and other agents
  read a nested `AGENTS.md`. So a folder rule loads only when an agent works in that folder.
- A skill loads when its task matches, not when an agent opens a folder. So a skill is correct for a
  step of a task, and a nested file is correct for a folder.
- Each `CLAUDE.md` imports its `AGENTS.md`, so two instruction files cannot disagree. This reason of
  0001 stays.
- Much of section 5 repeated the [Rules](../README.md#rules) of the index. The core now links to them.

## Consequences

- A rule can be in one of three places: the root file, a nested file or a skill. The root file lists
  the nested files and the skills.
- [`tools/check_links.py`](../../tools/check_links.py) checks the links of each `AGENTS.md` at any
  depth. It skips hidden folders and `plans/`.
- An agent whose working folder is in another repo does not load a nested file of this repo. The
  rules for exporter agents stay in the exporter guide.

## Alternatives rejected

- **Skills for each folder.** A skill does not load when an agent opens a folder.
- **Claude Code rules in `.claude/rules/` with `paths:`.** Only Claude Code reads them. Other agents
  read `AGENTS.md`.
- **Shorter text in one file.** ASD-STE100 limits the length of a sentence. The size came from
  content that most tasks do not need and from text that repeated other files.

## Not repeated

- Do not add rules to a `CLAUDE.md`. Add them to the `AGENTS.md` of that folder.
- Do not remove an old heading of the root `AGENTS.md`. Absorbed entries link to it.

_Edited 2026-10-28 (this PR): link repair._

_Edited 2026-10-29 (this PR): link repair._

# GN3D — Decision logs: a root log and a log for each module

**Status:** accepted, 2026-10-28 (user).

## Decision

This entry supersedes [ADR-HXY8](hxy8-scoped-agent-instructions.md) in full. It restates the rules
of hxy8 that stay. Items 1 to 6, 8 and 9 do not change. Item 7 changes. Items 11 to 19 are new.

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
7. **Decision logs.** This repo has a root log in `decisions/` and a log for each module in
   `LOG_DIRS` of [`tools/check_decision_log.py`](../tools/check_decision_log.py). Today the only
   module log is [`specs/model-sidecar/decisions/`](../specs/model-sidecar/decisions/README.md). A
   decision that code, the spec or another document refers to must be in an entry.
8. **`plans/`.** `plans/` is a local working folder. Git ignores it. Do not commit it. A tracked file
   does not link to `plans/` and does not cite the content of a plan: its sections, its item numbers
   or its local PR labels.
9. **Implementation plan.** `specs/sidecar-implementation-plan.md` is a tracked file, not a local
   plan. [ADR-B9FM](b9fm-finished-sidecar-plans.md) gives the time that it stays.
10. **Bootstrap kit.** The kit does not take rules 1 to 6. A new repo starts with one `AGENTS.md` and
    one log.
11. **Module.** A module is a folder with a nested `AGENTS.md` (item 2).
12. **Placement.** An entry goes in the log of module M only when M has a log in `LOG_DIRS` and each
    file that its Decision section names or changes is inside M. All other entries go in the root
    log. This includes an entry for two or more modules, `tools/`, the skills, the root `AGENTS.md`,
    CI, `plans/` or the repo process, an entry for a module that has no log in `LOG_DIRS`, and each
    case that you cannot decide.
13. **A new module log.** A new module log needs the approval of the user. The PR that adds the log
    also adds its folder to `LOG_DIRS`.
14. **One ID space.** All logs of this repo have one ID space. IDs that differ only in case are one
    ID. "This log" in an older entry means all logs of this repo.
15. **Citations across logs.** Cite an entry of another log with a relative link and the usual
    `ADR-<ID>` text. Do not add a module name to the ID.
16. **Module `AGENTS.md`.** The `AGENTS.md` of a module with a log links to that log.
17. **Scope change.** When the scope of a module entry later includes more than one module, a new
    entry in the root log supersedes it.
18. **Log files.** Each log has a `README.md` with an Active table, a Proposed table and
    `## Open work`. Each log also has `historical.md` and `open-work.md`. The
    [Rules](README.md#rules) and [`template.md`](template.md) are only in the root log. A log has a
    `scripts/` folder when one of its entries has a script. The script is in `scripts/` of the log
    that holds its entry ([ADR-EY8R](EY8R-tools-and-scripts.md)).
19. **Read path.** Items 1 and 10 of [ADR-Z934](z934-decision-log-index-and-read-path.md) apply in
    each log. For a task in module M, `README.md` and `open-work.md` mean the files of the root log
    and the files of the log of M. The index, open-work and entry limits apply to each file. The tool
    checks the read-path limit as one total over all logs. So the read path of a task does not get a
    higher limit.

## Reason

- A task in one module does not load the decisions of the other modules. The spec log holds 26
  entries. 21 of them are Proposed.
- A fixed list in `LOG_DIRS` makes each log a checked log. The user approves each log.
- One ID space keeps each ID unique in the repo. So a citation needs no module name, and an entry
  can move to a different log with no re-ID.
- hxy8 keeps the reasons for items 1 to 10.

## Consequences

- [`tools/check_links.py`](../tools/check_links.py) scans each folder with the name `decisions`.
- An agent that works in a module reads two index files and two open-work files.

## Alternatives rejected

- **Find the logs with a search of the tree.** A folder that the user did not approve, or a test
  copy of a log, then becomes a log.
- **An ID space for each log.** A citation then needs the module name, and a move needs a re-ID.
- **The Rules and the template in each log.** Two copies of a rule can disagree.

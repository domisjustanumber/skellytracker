# QPS7 — Decision entries in an entries folder

**Status:** accepted, 2026-10-29 (user; PR: pending).

## Decision

1. **The layout.** The entry files of each log are in `<log>/entries/`. This applies to the root log,
   the spec log in `specs/model-sidecar/decisions/`, the kit log and the module template of
   [`specs/agents-and-adr-process/`](../../specs/agents-and-adr-process/README.md). The files that do
   something stay in the log folder: `README.md`, `historical.md`, `open-work.md`, `template.md`,
   `scripts/` and `evidence/`. IDs, file names and statuses do not change.
2. **References.** No stub stays at an old path. Each link in this repo to an old path goes to the
   new path. A decided entry gets only its link repairs and one link-repair `_Edited` line. A
   plain-text old path in a decided entry stays, because it is history. It means the same file in
   `entries/`. A plain-text path in a live document or a tool changes. A path of an exporter repo
   stays.
3. **The checker.** [`tools/check_decision_log.py`](../../tools/check_decision_log.py) reads the
   entries in `entries/` and reports an entry file in the log folder. An index row links
   `entries/<ID>-<slug>.md`. `--new` and `--collisions` also read the old layout on other branches
   and in other worktrees, so a branch from before this move still counts.
4. **Edit lines.** The size limit of an entry does not count its `_Edited` lines. The status
   paragraph already does not count
   ([ADR-Z05A](Z05A-essential-decision-log-rules.md)). Both grow after the decision, and an allowed
   edit cannot make them shorter.
5. **The sources.** [`AGENTS.md#5-decision-log`](../../AGENTS.md#5-decision-log) and
   [`template.md`](../template.md) state the layout. The docstring of the checker states items 3 and
   4. The kit gets them by [`tools/sync_bootstrap_kit.py`](../../tools/sync_bootstrap_kit.py).

## Reason

- The user decided on 2026-10-29: a listing of `decisions/` mixed 53 entry files with the files that
  do something. The user chose the name `entries/`.
- The link repairs of the move made three recent entries longer than 6,000 characters (FADS, JB5J
  and CRV0). A link repair cannot be shorter than the path that it repairs.

## Consequences

- Each link to an entry is 8 characters longer. The root index grows by about 300 characters.
- A branch from before the move must move its new entries into `entries/` when it rebases. The
  checker reports an entry file in the log folder.

## Evidence

- The move changed 61 entry files and the links in 99 Markdown files. `check_links.py`,
  `check_decision_log.py` and `uv run pytest tools/tests` pass after it.

## Alternatives rejected

- **`adr/`.** It is 4 characters shorter. The user chose `entries/`, the word of the Rules.
- **A stub at each old path.** [ADR-D9VT](D9VT-decision-log-move.md) rejected stubs for the last
  move. Git keeps the history.

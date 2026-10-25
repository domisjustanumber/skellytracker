# 0001 — Decision log; `AGENTS.md` is the single instructions file; `plans/` is local and ignored

**Status:** absorbed into [`AGENTS.md#repository-instructions`](../../AGENTS.md#repository-instructions), 2026-10-25 (user; the absorption review).

## Decision

- This repo keeps a decision log in `notes/decisions/`. The [README](README.md) has the index, the
  open work, the rules and the entry template.
- A decision that code, the spec or another document refers to must be in an entry. Entries 0002 to
  0012 record the earlier sidecar decisions. Before this log, these decisions were spread over
  `specs/sidecar-implementation-plan.md`, `specs/sidecar-spec-exporter-coverage-plan.md`, the spec
  (with its "Considered and deliberately not added" table) and exporter decision entries.
- `AGENTS.md` is the single instructions file for coding agents. `CLAUDE.md` only imports it: its
  full content is `@AGENTS.md`. Do not put instructions in `CLAUDE.md` or in a second instructions
  file.
- Agent procedures are skills in `.claude/skills/`. Git tracks that folder and ignores the rest of
  `.claude/`. An agent that does not support skills reads the skill file.
- `plans/` is a local working folder. Git ignores it. Do not commit it.
- A tracked file does not link to `plans/` and does not cite the content of a plan: its sections,
  its item numbers or its local PR labels. Cite a decision entry, a tracked file or a GitHub PR
  number.
- `specs/sidecar-implementation-plan.md` is a tracked file, not a local plan. It stays until its
  last milestones (M5 and M6) are done. Entries 0002 to 0007 record its key decisions and the move
  of the generic processing code.

## Reason

- Plans are working notes for a session. They go out of date, and they are not a record. A clone
  does not have them. A decision that code refers to must be in a tracked file, so that a clone can
  find it.
- Before this log, a reader had to search plan documents and the spec to find a decision and its
  reason. One log with one index puts every decision in one place.
- Claude Code reads `CLAUDE.md`. Other coding agents read `AGENTS.md`. The import gives all agents
  the same text, so two instruction files cannot disagree.
- The old `CLAUDE.md` describes the package before #75 ("Structural rewrite"). It names
  `trackers/`, `TrackedObjectDefinition` and the CompositeGPU tracker. `skellytracker/trackers/` does
  not exist after #75. A second instructions file goes out of date in the same way.
- Skills must be tracked so that every clone has the same procedures. The old `.gitignore` rule
  `.claude/*` ignored them.
- OpenMMLab-Exporter uses the same rules (OpenMMLab-Exporter 0038). An agent that works in both repos
  finds the same structure.

## Evidence

- `skellytracker/trackers/` does not exist on this branch. No `.py` file under `skellytracker/`
  names `TrackedObjectDefinition` or `composite_gpu`. Commit `2c2615c` ("Structural rewrite (#75)")
  is on `development`.
- `.gitignore` ignores `.claude/*`, then keeps `.claude/skills/` with the rule `!.claude/skills/`.
  It ignores `plans/`.
- The status line of `specs/sidecar-implementation-plan.md` says that M5 and M6 have not started.

## Not repeated

- Do not link to `plans/` from a tracked file. Link to a decision entry.
- Do not cite a plan's section numbers, item numbers or local PR labels in a tracked file. They have
  no meaning in a clone, and the GitHub PR numbers are different.
- Do not add rules to `CLAUDE.md`. Add them to `AGENTS.md`.

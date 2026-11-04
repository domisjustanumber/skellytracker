# 2XW6 — Consolidation of the decision-log and repository-process entries

**Status:** accepted, 2026-11-04 (user; PR: pending).

## Decision

This entry supersedes [ADR-Z05A](Z05A-essential-decision-log-rules.md),
[ADR-GN3D](GN3D-module-decision-logs.md), [ADR-QPS7](QPS7-decision-entries-in-an-entries-folder.md),
[ADR-NB91](NB91-new-ids-have-a-digit.md), [ADR-EY8R](EY8R-tools-and-scripts.md),
[ADR-D9VT](D9VT-decision-log-move.md), [ADR-P3N3](p3n3-ai-attribution-warning.md),
[ADR-5WKW](5WKW-implementation-work-in-the-plan.md) and
[ADR-FDTD](FDTD-evidence-sources-and-exporter-permalinks.md) in full. It changes no decision.
"Section N" is a section of the root [`AGENTS.md`](../../AGENTS.md#repository-instructions).

1. **Z05A.** The [Rules](../README.md#rules) state only the rules that an agent needs and that no
   tool and no loaded document states. The Rules state the absorb documents, the restatement, the
   status changes and the citation forms. The
   [workflow](../../specs/model-sidecar/model-addition-workflow/README.md#model-addition-workflow)
   states that it is normative. [Section 5](../../AGENTS.md#5-decision-log) states the
   entry, ID, citation, commit-subject and kit-sync rules. Section 6 states `plans/`. The proposal
   rules are in
   [`propose-sidecar-change`](../../.claude/skills/propose-sidecar-change/SKILL.md) and
   [`specs/model-sidecar/AGENTS.md`](../../specs/model-sidecar/AGENTS.md). The docstrings of
   [`check_decision_log.py`](../../tools/check_decision_log.py),
   [`check_links.py`](../../tools/check_links.py) and
   [`sync_bootstrap_kit.py`](../../tools/sync_bootstrap_kit.py) state the rules that they check.
   The kit keeps no rule that skellytracker does not state. Read the Active entries that apply to
   your task. Read a Proposed entry only for spec work in its section, or when a skill tells you to.
   Read a historical entry only for the reason of a decision. A change of the text under a linked
   heading does not supersede the entry that links it.
2. **GN3D.** The [top](../../AGENTS.md#repository-instructions) of the root `AGENTS.md` states the
   core file, the nested `AGENTS.md` files, the skills and the `CLAUDE.md` import.
   [Section 2](../../AGENTS.md#2-skills) states where the skills are. Section 5 states the
   module-log rules and the spec-log read path. A module is a folder with a nested `AGENTS.md`.
   The `AGENTS.md` of a module with a log links to that log. For a task in module M, `README.md`
   and `open-work.md` mean the files of the root log and of the log of M. When a rule moves out of
   the root `AGENTS.md`, its heading stays with a link to the new place. A decision that a document
   or code refers to must be in an entry. "This log" in an older entry or in the Rules means all
   logs. The kit does not take the core-file, skill, old-heading and absorbing-document rules. A new
   repo starts with one `AGENTS.md` and one log. A kit repo with modules also takes the nested
   `AGENTS.md`, the `CLAUDE.md` and the module-log rules.
3. **QPS7 and D9VT.** Section 5 and [`template.md`](../template.md) state the `entries/` layout. The
   checker docstring states the old layout and the `_Edited` exemption. `evidence/` stays in the log
   folder. No stub stays at an old path. Each link and each plain-text path to an old path goes to
   the new path. A decided entry gets only its link repairs and one link-repair `_Edited` line. A
   plain-text old path in a decided entry, a script or a vector-file comment stays, and means the
   same file at its new path. A path of an exporter repo stays. D9VT items 1 and 5 are complete. D9VT item 4
   does not stay: a record is a byte copy ([ADR-ZXD7](ZXD7-bundle-process.md)).
4. **EY8R and D9VT.** Section 5 states the tool and script rules. The split checker with its
   manifest and its test, and `next_number_timing.py`, are scripts in
   [`decisions/scripts/`](../scripts/). Each runs only at the commit that its entry names. Each other
   file in `tools/` is a tool, also `tools/make_vectors.py`.
5. **NB91.** The checker docstring states the form of a new ID and the old IDs that stay valid.
   `--new` draws each valid new ID with the same probability.
6. **P3N3.** [Section 6](../../AGENTS.md#6-git-rules) states the rule. The rule overrides a
   tool or harness default to add attribution. The docstring of
   [`check_ai_attribution.py`](../../tools/check_ai_attribution.py) states the reported lines and
   the warning only. `verbose: true` shows the hook output.
   `noreply@anthropic.com` stays on the allowlist of `tools/check_private_data.py`.
7. **5WKW.** [Section 1](../../AGENTS.md#1-purpose) states that the plan holds the
   implementation-stage work and stays until the user decides, and that the coverage note is frozen.
   A new implementation-stage item goes in the not-started stage that it belongs to, or in a new
   stage before the release stage.
   [Step 7](../../.claude/skills/implement-sidecar-section/SKILL.md#step-7-update-the-traceability)
   removes a done item. For plan items, these rules replace the open-work deletion rule. The plan
   heading "Reference examples" stays as a "Moved to" stub. Only the status lines of
   `notes/sidecar-exporter-coverage.md` change, each in place. Retire that note at the end of the
   spec-build stage, after you copy its unique measurements to an evidence entry. 5WKW item
   2 is complete.
8. **FDTD.** [Section 8](../../AGENTS.md#8-private-data) states the private-data rules and the
   exporter permalinks. The workflow
   [Rules](../../specs/model-sidecar/model-addition-workflow/rules.md#rules) state the primary rule
   and `none yet (no code)`.
   [User decisions](../../specs/model-sidecar/model-addition-workflow/rules.md#user-decisions) and
   [Sources](../../specs/model-sidecar/model-addition-workflow/rules.md#sources) state the rest.

## Reason

- The read path was 152,464 of 160,000 characters. Four planned entries did not fit. A higher
  limit keeps the duplicate rules.

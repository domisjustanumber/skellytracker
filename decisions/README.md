# Decision log

This log records the technical decisions for skellytracker that affect more than one module, with
their reasons and evidence. The [spec log](../specs/model-sidecar/decisions/README.md) holds the
decisions of the sidecar spec only ([ADR-GN3D](GN3D-module-decision-logs.md)). Read this file before you change the spec, a sidecar, the
sidecar code, the agent instructions or the PR workflow. Also read [open-work.md](open-work.md). Then
read the Active entries that apply to your task. Then you do not repeat a settled question or a
completed measurement. Read a Proposed entry only for spec work in its section, or when a skill tells
you to. Read an entry of [historical.md](historical.md) only to find the reason for a decision
([ADR-Z05A](Z05A-essential-decision-log-rules.md)).

Each entry gives the decision, its reason, the evidence (when there is evidence), the alternatives
rejected and a "Not repeated" section for pitfalls already found. Entries 0002 to 0012, here and in
the spec log, are backfilled. They record decisions made before this log existed, and they cite the original sources.
When a decision changes, add a new entry that supersedes the old entry in full. A change of the
text under a heading that an entry links does not supersede that entry
([ADR-Z05A](Z05A-essential-decision-log-rules.md)). The body of a
decided entry changes only by the edits that the [Rules](#rules) allow. To write an entry, use
[template.md](template.md).

## Index

### Active

These entries are `accepted` or `evidence`.

| # | Decision | Status |
|---|----------|--------|
| [p3n3](p3n3-ai-attribution-warning.md) | No AI attribution in check-ins; a commit-msg hook warns and does not stop the commit | accepted |
| [x64y](x64y-draft-exporter-guide-folder.md) | The workflow, with the sidecar-file, validation and publishing rules, is in `model-addition-workflow/`; the exporter-only guide is a draft; no stub | accepted |
| [b9fm](b9fm-finished-sidecar-plans.md) | The reference-examples procedure moves to the workflow; the implementation plan links to the spec backlog; the coverage note is frozen evidence | accepted |
| [yve0](yve0-example-fragments.md) | An example fragment has one source: a package copy with the same bytes, or a `fragments` entry in `inventory.yaml` | accepted |
| [GN3D](GN3D-module-decision-logs.md) | Core and nested `AGENTS.md` and skills; a root log and a log for each module in `LOG_DIRS`; placement; one ID space; supersedes hxy8 | accepted |
| [EY8R](EY8R-tools-and-scripts.md) | Tools are in the root `tools/`; a script is in `scripts/` of the log that holds its entry; a script that a later step runs becomes a tool | accepted |
| [D9VT](D9VT-decision-log-move.md) | The log moves to `decisions/` and `specs/model-sidecar/decisions/`; no stub; old plain-text paths stay; proposal-copy paths; supersedes k6dz | accepted |
| [AB79](AB79-one-pr-for-the-spec-build-work.md) | Exception to 0027: the spec-build work goes to `development` in one PR; one kind of change in each commit; no new `dom/NN-*` branch | accepted |
| [FADS](FADS-hand-over-bundles-in-intakes.md) | Hand-over bundles in `intakes/`: versions, manifest, states, responses, byte-copy proposal records; no gap records; supersedes pykx, faac and 0014 | accepted |
| [TA0G](TA0G-vector-cases-and-reference-modules.md) | Refusals as a rule ID or `no-rule`, `failed` lists, `outcome()`, 256 KiB, union landing check, module imports and fixtures; supersedes a33q and 0013 | accepted |
| [KDBD](KDBD-change-classes-and-spec-forced-edits.md) | Change classes `vnext`, `clarification` and `breaking`; the legacy index rule; spec-forced example edits and the part 7 table; supersedes 0009 | accepted |
| [FDTD](FDTD-evidence-sources-and-exporter-permalinks.md) | Exporter documents stay secondary; a checked upstream line is primary; user decisions in words; source forms; exporter permalinks; supersedes 0030 | accepted |
| [QMKS](QMKS-draft-sections-and-coverage-columns.md) | `spec: draft` rules, the graduation gate and the release stops; coverage and gate columns in `TRACEABILITY.md`; `no_model` reasons | accepted |
| [JB5J](JB5J-one-batch-form-for-each-sidecar.md) | One batch form for each `vNEXT` sidecar: b3 with `batch_conversion`, b1 or `dynamic`; the check by default; V0; publish rule for each verdict; supersedes JC4T | accepted |
| [Z05A](Z05A-essential-decision-log-rules.md) | The Rules keep only the rules that no tool or loaded document states; the kit sync writes the kit Rules; supersedes z934, JW9N, NSR2, 0031 | accepted |

### Proposed

These entries wait for a decision of the user. Section is the spec section of the change, or `none`
when the change has no one section. The spec change proposals of the sidecar spec are in the
[spec log](../specs/model-sidecar/decisions/README.md#proposed).

| # | Decision | Section | Status |
|---|----------|---------|--------|

The entries that are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done` are in [historical.md](historical.md).

## Open work

The open work and the repository state are in [open-work.md](open-work.md). The spec defects are
in the [open work of the spec log](../specs/model-sidecar/decisions/open-work.md).

## Rules

- The body of an entry that is not `proposed` changes only by four edits: a link or anchor repair, a
  typo that does not change the meaning, the redaction of private data, and a change of ID with the
  repair of its citations. Each edit adds `_Edited YYYY-MM-DD (#PR): <kind>._` at the end of the
  entry, for example `re-ID from XXXX` ([ADR-Z05A](Z05A-essential-decision-log-rules.md)). For a
  change of ID, the renamed entry gets `re-ID from XXXX`, and each repaired entry gets
  `citation repair`. Add these two lines only to an entry that is on `development`.
- An absorb document is one of these: the spec, the root or a nested `AGENTS.md`
  ([ADR-GN3D](GN3D-module-decision-logs.md)), the skills, the model addition workflow, the exporter
  guide, the templates of `specs/model-sidecar/templates/`, the Rules of this file with
  [template.md](template.md), and the docstring of a tool in `tools/` for the rules that it checks
  ([ADR-Z05A](Z05A-essential-decision-log-rules.md)). An accepted entry is absorbed when one absorb
  document states all of its rules.
- The entry that supersedes an old entry restates each rule of the old entry that stays. A link can
  restate a rule. The link must go to a heading of an absorb document, and that heading must state
  the rule. The commit that changes the text under such a heading cites its own entry next to the
  changed rule ([ADR-Z05A](Z05A-essential-decision-log-rules.md)).
- Only these status changes are allowed: `proposed` to `accepted` or `rejected`; `accepted` to
  `superseded by XXXX`, `absorbed into <path>#<anchor>` or `done`; `absorbed into <path>#<anchor>`
  to `superseded by XXXX` ([ADR-Z05A](Z05A-essential-decision-log-rules.md)); and `evidence` to
  `evidence; used by XXXX`, when an accepted entry cites the `evidence` entry for its decision.
  `done` is for an accepted entry that records a one-off action, with no rule that stays, when the
  action is complete. Each status change adds its date and the PR that made it. In the same PR,
  change the status in the index and move the row to the table for the new status
  ([ADR-Z05A](Z05A-essential-decision-log-rules.md)).
- `tools/check_decision_log.py` checks the tables, the status forms, the Section cell, the ID
  alphabet and the size limits. Its docstring states them. `tools/check_links.py` checks the links
  and the full-SHA permalinks. A tool is the source of a rule that it checks
  ([ADR-Z05A](Z05A-essential-decision-log-rules.md)).
- A consolidation entry states the rules that stay from a group of entries, and it supersedes each
  entry of the group. It changes no decision. Write one at the end of the spec-build stage, and when the read-path limit
  fails.
- Delete an open-work item when the work is done. Put a dated fact in `open-work.md` or in an
  entry, not in `AGENTS.md`.
- Put long evidence in a tracked file next to the entry, and link to it. A PR that raises a limit
  of `tools/check_decision_log.py` must add an entry.
- An ID changes only on a `re-ID:` line of `tools/check_decision_log.py`, to the ID of a new `--new`
  run. An older entry keeps its lower-case ID in its file name, heading and index row. Do not edit
  older text only to change the case ([ADR-Z05A](Z05A-essential-decision-log-rules.md)).
- Until a commit is on `development`, cite its PR number and the file path, not its SHA ([ADR-0027](0027-single-working-branch.md)).
  The `ADR-` prefix is for citations only: a file name, a
  heading, an index row and a status line hold the bare ID. Cite a provisional entry of another repo
  by the repo name, the PR number and the slug. Do not edit a decided entry only to add or move the
  prefix or the link ([ADR-Z05A](Z05A-essential-decision-log-rules.md)).

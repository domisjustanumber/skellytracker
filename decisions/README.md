# Decision log

This log records the technical decisions for skellytracker that affect more than one module, with
their reasons and evidence. The [spec log](../specs/model-sidecar/decisions/README.md) holds the
decisions of the sidecar spec only ([ADR-GN3D](entries/GN3D-module-decision-logs.md)). The
[pipeline spec log](../specs/pipeline/decisions/README.md) holds the decisions of the pipeline spec
only ([ADR-3SF2](entries/3SF2-pipeline-spec-and-node-workflow.md)). Read this file before you change the spec, a sidecar, the
sidecar code, the agent instructions or the PR workflow. Also read [open-work.md](open-work.md). The
[Rules](#rules) tell you which entries to read.

Each entry gives the decision, its reason, the evidence (when there is evidence), the alternatives
rejected and a "Not repeated" section for pitfalls already found. Entries 0002 to 0012, here and in
the spec log, are backfilled. They record decisions made before this log existed, and they cite the original sources.
When a decision changes, add a new entry that supersedes the old entry in full. The body of a
decided entry changes only by the edits that the [Rules](#rules) allow. To write an entry, use
[template.md](template.md).

## Index

### Active

These entries are `accepted` or `evidence`.

| # | Decision | Status |
|---|----------|--------|
| [AMJ8](entries/AMJ8-replace-package-onnx-detectors.md) | Replace the package ONNX detectors with exporter models; no legacy layer; shipped sidecars in `core/model_zoo/`; RTMPose replacements block v2.0.0 | accepted |
| [0XW9](entries/0XW9-entry-points-layout-guard-test-and-session-code.md) | Entry points `detectors` and `pipelines`; `system/`, `metrics/`, `eps/` under an eager `core`; one `eps` guard test; new session code in `core/eps/` | accepted |
| [NHM3](entries/NHM3-phases-to-the-exporter-checkpoint.md) | Phase 0 and phase 1 to the exporter checkpoint; pre-release at the checkpoint; new code beside old; supersedes EM74 | accepted |
| [9NW0](entries/9NW0-ep-keys-options-and-failures.md) | EP keys from the EP catalog; a run takes `ep_options`; a whole-EP failure raises before frame 0; CPU nodes are reported | accepted |
| [M2C6](entries/M2C6-exact-pins-and-one-python-patch-release.md) | Exact pins, no ranges; Python `==3.13.18`; `onnxruntime` 1.31 base dependency; GPU EPs only as CUDA 13 plugin packs; supersedes MWY9 | accepted |
| [W5QD](entries/W5QD-pipeline-entries-consolidation.md) | Consolidation of the pipeline entries 7NY2, ZYS9, V7GZ and 0WTV: links to the pipeline spec, and the Python API names that it does not state | accepted |
| [V6G2](entries/V6G2-implementation-stage.md) | The implementation stage starts at the rebuild of phase 0; the spec-build code and git rules end; the spec can still change through proposals | accepted |
| [Z0CC](entries/Z0CC-exporter-coverage-measurements.md) | Exporter coverage measurements of 2026-10: RF-DETR graph checks, RTMDet AP of resize and NMS, COCO id and in-graph cap defects | evidence |
| [246B](entries/246B-ep-catalog-store-and-install.md) | EP catalog and lock in the package; option allow-lists; one EP store; `urllib` download after a user action; no mirror; installer EP page | accepted |
| [D8DH](entries/D8DH-sessions-errors-and-the-ready-rule.md) | `core/errors.py`; one exit-code table; an EP pack is ready when installed, current, registered and with a device; no EP variables | accepted |
| [P1F3](entries/P1F3-hardware-probe-devices-and-multi-gpu.md) | Hardware probe fields; `free_vram`; `device_key`; default GPU by VRAM; a run splits its cameras across GPUs; no pre-Turing GPUs | accepted |

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
in the [open work of the spec log](../specs/model-sidecar/decisions/open-work.md). The
implementation-stage work is in the [implementation plan](../specs/sidecar-implementation-plan.md).

## Rules

- Read the Active entries that apply to your task. Then you do not repeat a settled question or a
  completed measurement. Read a Proposed entry only for spec work in its section, or when a skill
  tells you to. Read an entry of [historical.md](historical.md) only to find the reason for a
  decision ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).
- The body of an entry that is not `proposed` changes only by four edits: a link or anchor repair, a
  typo that does not change the meaning, the redaction of private data, and a change of ID with the
  repair of its citations. Each edit adds `_Edited YYYY-MM-DD (#PR): <kind>._` at the end of the
  entry, for example `re-ID from XXXX` ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)). For a
  change of ID, the renamed entry gets `re-ID from XXXX`, and each repaired entry gets
  `citation repair`. Add these two lines only to an entry that is on `development`. A plain-text
  old path in a decided entry, a script or a vector-file comment stays, and means the same file at
  its new path. A path of an exporter repo stays
  ([ADR-2XW6](entries/2XW6-process-entries-consolidation.md)).
- A decision that a document or code refers to must be in an entry. "This log" in an older entry or
  in the Rules means all logs ([ADR-2XW6](entries/2XW6-process-entries-consolidation.md)).
- An absorb document is one of these: the spec (the sidecar spec and the pipeline spec), the root or a nested `AGENTS.md`
  ([ADR-GN3D](entries/GN3D-module-decision-logs.md)), the skills, the model addition workflow, the exporter
  guide, the templates of `specs/model-sidecar/templates/`, the Rules of this file with
  [template.md](template.md), and the docstring of a tool in `tools/` for the rules that it checks
  ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)). A test in `tools/tests/` is a tool here.
  From the implementation stage, the docstring of a public module of the package is an absorb
  document for the rules of the API of that module ([ADR-W823](entries/W823-absorb-in-the-commit-group-that-states-the-rules.md)).
  The spec includes the `notes` of its vector files. An accepted entry is absorbed when the absorb
  documents together state all of its rules. Open work of the entry does not stop the absorb when
  `open-work.md` or the implementation plan states that work in full. A link to the entry is not
  enough ([ADR-5EVP](entries/5EVP-absorb-across-documents.md)).
- Absorb at landing. The commit group that writes or lands an entry, or that writes the rules of an
  entry into the absorb documents, absorbs the entry in its last commit when the absorb documents
  state all of its rules. This applies in each log, in each skill and without a skill. If an absorb
  document does not state a rule, the entry stays `accepted`. Do not ask the user
  ([ADR-W823](entries/W823-absorb-in-the-commit-group-that-states-the-rules.md)).
- The status `absorbed into` has one link for each heading that states a rule of the entry. Link a
  heading one time, also when it states two or more rules. Link a file with no anchor only when the
  rule is not under a heading, for example in a tool docstring or a YAML file. When the status
  paragraph is longer than `STATUS_EXEMPTION_LIMIT`, replace the headings of one file with the title
  heading of that file. Start with the file that has the most links. If the paragraph is still too
  long, replace the files of one document, for example the workflow, with the title heading of its
  main file. A commit that renames a heading repairs each status link to that heading. A change from
  a file link to heading links is a link repair
  ([ADR-995P](entries/995P-absorb-status-links-headings.md)).
- The entry that supersedes an old entry restates each rule of the old entry that stays. A link can
  restate a rule. The link must go to a heading of an absorb document, and that heading must state
  the rule. Link the heading of each kept rule that a heading states. Write text only for a changed
  rule and for a kept rule that no heading states ([ADR-W823](entries/W823-absorb-in-the-commit-group-that-states-the-rules.md)). The commit that changes the text under such a heading cites its own entry next to the
  changed rule. That change does not supersede the entry that links the heading
  ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).
- Only these status changes are allowed: `proposed` to `accepted` or `rejected`; `accepted` to
  `superseded by XXXX`, `absorbed into <path>#<anchor>` or `done`; `absorbed into <path>#<anchor>`
  to `superseded by XXXX` ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)); and `evidence` to
  `evidence; used by XXXX`, when an accepted entry cites the `evidence` entry for its decision.
  `done` is for an accepted entry that records a one-off action, with no rule that stays, when the
  action is complete. Each status change adds its date and the PR that made it. In the same PR,
  change the status in the index and move the row to the table for the new status
  ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).
- `tools/check_decision_log.py` checks the tables, the status forms, the Section cell, the ID
  alphabet and the size limits. Its docstring states them. `tools/check_links.py` checks the links
  and the full-SHA permalinks. A tool is the source of a rule that it checks
  ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).
- A consolidation entry states the rules that stay from a group of entries, and it supersedes each
  entry of the group. It changes no decision. Write one at the end of the spec-build stage.
- When the read path is at 90% of its limit or more, first absorb each accepted entry whose rules
  the absorb documents state ([ADR-3AM0](entries/3AM0-absorb-at-landing-and-landed-copies.md)). Then
  write each rule that no absorb document states in the absorb document where it belongs, and
  absorb its entry ([ADR-5EVP](entries/5EVP-absorb-across-documents.md)).
- A commit that only makes a workflow, skill, template or tool copy agree with a landed spec entry
  cites that entry. It needs no entry of its own. A new rule is not a copy
  ([ADR-3AM0](entries/3AM0-absorb-at-landing-and-landed-copies.md)).
- Delete an open-work item when the work is done. Put a dated fact in `open-work.md` or in an
  entry, not in `AGENTS.md`.
- Put long evidence in a tracked file in `evidence/` of the log folder, and link to it
  ([ADR-2XW6](entries/2XW6-process-entries-consolidation.md)). A PR that raises a limit
  of `tools/check_decision_log.py` must add an entry.
- An ID changes only on a `re-ID:` line of `tools/check_decision_log.py`, to the ID of a new `--new`
  run. An older entry keeps its lower-case ID in its file name, heading and index row. Do not edit
  older text only to change the case ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).
- Until a commit is on `development`, cite its PR number and the file path, not its SHA ([ADR-0027](entries/0027-single-working-branch.md)).
  The `ADR-` prefix is for citations only: a file name, a
  heading, an index row and a status line hold the bare ID. Cite a provisional entry of another repo
  by the repo name, the PR number and the slug. Do not edit a decided entry only to add or move the
  prefix or the link ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).

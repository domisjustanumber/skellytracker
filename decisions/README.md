# Decision log

This log records the technical decisions for skellytracker that affect more than one module, with
their reasons and evidence. The [spec log](../specs/model-sidecar/decisions/README.md) holds the
decisions of the sidecar spec only ([ADR-GN3D](entries/GN3D-module-decision-logs.md)). Read this file before you change the spec, a sidecar, the
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
| [6J8E](entries/6J8E-exporters-run-released-skellytracker.md) | Exporters run a pinned skellytracker release; code changes come as a patch; upstream parity is the independent check; acceptance waits for the gate | accepted |
| [x64y](entries/x64y-draft-exporter-guide-folder.md) | The workflow, with the sidecar-file, validation and publishing rules, is in `model-addition-workflow/`; the exporter-only guide is a draft; no stub | accepted |
| [R39S](entries/R39S-test-fix-on-the-working-branch.md) | Exception to 0027: one spec-build PR; one change kind per commit; no `dom/NN-*` branch; a test fix is a commit on the working branch; CI read; supersedes AB79 | accepted |
| [QMKS](entries/QMKS-draft-sections-and-coverage-columns.md) | `spec: draft` rules, the graduation gate and the release stops; coverage and gate columns in `TRACEABILITY.md`; `no_model` reasons | accepted |
| [8DSW](entries/8DSW-vector-files-are-the-case-source.md) | The vector file is the only case source; formula modules, named checks, `land` and `fill`; supersedes TA0G | accepted |
| [AD33](entries/AD33-bundles-are-untrusted-input.md) | Bundles are untrusted input: no tool imports or runs bundle code; static checks; a reviewed, user-approved copy; ONNX checks in `batch` | accepted |
| [7F6X](entries/7F6X-license-rows-in-the-model-intake.md) | The model intake gets the License rows LC1 to LC6; out of scope and parity follow R6J9; row T11 names the cast | accepted |
| [V8FK](entries/V8FK-license-evidence-and-models-with-no-license.md) | A license page is primary evidence; a model with no known weights license gets no sidecar and no proposal | accepted |
| [A2CW](entries/A2CW-dataset-owner-page-is-enough-evidence.md) | A page or README of a dataset owner is enough evidence for the license and the contents of the dataset | accepted |
| [0QKK](entries/0QKK-no-legacy-layer.md) | No legacy layer; `input.normalization` required; unknown keys invalid; no `since`; rule renumbering; supersedes 0012 and 0016 | accepted |
| [JAA4](entries/JAA4-one-batch-field.md) | One `batching.batch` field; `output_shapes` in each size; no `batch_axis`; supersedes CRV0, JB5J and 0011 | accepted |
| [6GE2](entries/6GE2-spec-version-follows-skellytracker.md) | Spec version follows skellytracker SemVer: released headings, recorded pre-releases, IDs never shift, `2.0.0` ships the loader, ban per target; supersedes SS2E | accepted |
| [ZXD7](entries/ZXD7-bundle-process.md) | Bundle process: no release step; manifest `spec_version`; entry status = proposal state; owner rule; `-2` n/a until a final release loads it; supersedes FADS | accepted |
| [CN15](entries/CN15-spec-readme-is-the-only-entry-point.md) | The spec `README.md` is the only entry point; `sidecar-spec.md` is frozen, and M11 deletes it after the code cites section IDs; the root README links the spec | accepted |
| [ESP4](entries/ESP4-one-home-for-each-workflow-rule.md) | One home for each workflow rule; skills link it; templates are forms with no relative link; new phase-1 headings; three rules move to `rules.md` | accepted |
| [0PK7](entries/0PK7-selection-boxes-space-flag.md) | Each selection vector case gives `boxes_xyxy` and `boxes_space` (`model_input` or `source`); a host reads the flag | accepted |
| [2XW6](entries/2XW6-process-entries-consolidation.md) | Consolidation: restates the rules that stay of Z05A, GN3D, QPS7, NB91, EY8R, D9VT, p3n3, 5WKW and FDTD; changes no decision | accepted |
| [9MJ6](entries/9MJ6-remove-the-heatmap-decode.md) | Remove the heatmap decode: no `heatmap` method, semantic or section until a model brings a full contract | accepted |
| [9HBB](entries/9HBB-simcc-decode-is-2d-only.md) | The SimCC decode is 2D only: no `simcc_z`, no `depth_range`; a 3D SimCC model adds its own section | accepted |
| [4KW6](entries/4KW6-onnxruntime-1-31-for-the-cpu-check.md) | `onnx-cpu` requires `onnxruntime>=1.31` (lock 1.31.1): no fp16 noise in the batch check; the GPU cap stays | accepted |
| [VV8B](entries/VV8B-fragments-have-an-inventory-entry.md) | Each example fragment has a `fragments` entry in `inventory.yaml`; no package-copy source; a forced fragment edit is `needs-export`; supersedes yve0 | accepted |
| [BQZ9](entries/BQZ9-intake-process-consolidation.md) | Consolidation: restates the rules that stay of C0YD, 3HZ4, FM0B, 3AM0 and 37CD | accepted |
| [6G6G](entries/6G6G-ci-read-before-the-push.md) | Read the fork CI before each push, not before the request; a red or empty read stops an early-approved push; narrows R39S item 9 | accepted |
| [P3NK](entries/P3NK-bootstrap-kit-in-freemocap-project.md) | The bootstrap kit moves to `agents-and-adr-process/` of freemocap/project; the sync tool stays here; `--check` skips with no checkout; one kit PR in each repo | accepted |
| [5EVP](entries/5EVP-absorb-across-documents.md) | The absorb documents together state the rules; open work in the plan or open work does not block; tests and vector notes count; no 90% consolidation | accepted |
| [R3F1](entries/R3F1-mediapipe-check-time-limit.md) | `run_checks.py` stops the MediaPipe check after 300 s, runs the next checks and exits 124; the note says known on 3.12, regression on 3.13+ | accepted |
| [P8Q0](entries/P8Q0-closed-for-a-model-with-no-license.md) | A model bundle with row LC2 `unknown` gets `closed`; a new version of a `closed` model bundle is `submitted` again | accepted |

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
- An absorb document is one of these: the spec, the root or a nested `AGENTS.md`
  ([ADR-GN3D](entries/GN3D-module-decision-logs.md)), the skills, the model addition workflow, the exporter
  guide, the templates of `specs/model-sidecar/templates/`, the Rules of this file with
  [template.md](template.md), and the docstring of a tool in `tools/` for the rules that it checks
  ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)). A test in `tools/tests/` is a tool here.
  The spec includes the `notes` of its vector files. An accepted entry is absorbed when the absorb
  documents together state all of its rules. Open work of the entry does not stop the absorb when
  `open-work.md` or the implementation plan states that work in full. A link to the entry is not
  enough. The status `absorbed into` has one link for each absorb document that states a rule of the
  entry, to the heading that holds those rules or to the file
  ([ADR-5EVP](entries/5EVP-absorb-across-documents.md)).
- The entry that supersedes an old entry restates each rule of the old entry that stays. A link can
  restate a rule. The link must go to a heading of an absorb document, and that heading must state
  the rule. The commit that changes the text under such a heading cites its own entry next to the
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

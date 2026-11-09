# Decision log

This log records the technical decisions for skellytracker that affect more than one module, with
their reasons and evidence. The [spec log](../specs/model-sidecar/decisions/README.md) holds the
decisions of the sidecar spec only ([ADR-GN3D](entries/GN3D-module-decision-logs.md)). Read this file before you change the spec, a sidecar, the
sidecar code, the agent instructions or the PR workflow. Also read [open-work.md](open-work.md). Then
read the Active entries that apply to your task. Then you do not repeat a settled question or a
completed measurement. Read a Proposed entry only for spec work in its section, or when a skill tells
you to. Read an entry of [historical.md](historical.md) only to find the reason for a decision
([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).

Each entry gives the decision, its reason, the evidence (when there is evidence), the alternatives
rejected and a "Not repeated" section for pitfalls already found. Entries 0002 to 0012, here and in
the spec log, are backfilled. They record decisions made before this log existed, and they cite the original sources.
When a decision changes, add a new entry that supersedes the old entry in full. A change of the
text under a heading that an entry links does not supersede that entry
([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)). The body of a
decided entry changes only by the edits that the [Rules](#rules) allow. To write an entry, use
[template.md](template.md).

## Index

### Active

These entries are `accepted` or `evidence`.

| # | Decision | Status |
|---|----------|--------|
| [x64y](entries/x64y-draft-exporter-guide-folder.md) | The workflow, with the sidecar-file, validation and publishing rules, is in `model-addition-workflow/`; the exporter-only guide is a draft; no stub | accepted |
| [yve0](entries/yve0-example-fragments.md) | An example fragment has one source: a package copy with the same bytes, or a `fragments` entry in `inventory.yaml` | accepted |
| [AB79](entries/AB79-one-pr-for-the-spec-build-work.md) | Exception to 0027: the spec-build work goes to `development` in one PR; one kind of change in each commit; no new `dom/NN-*` branch | accepted |
| [QMKS](entries/QMKS-draft-sections-and-coverage-columns.md) | `spec: draft` rules, the graduation gate and the release stops; coverage and gate columns in `TRACEABILITY.md`; `no_model` reasons | accepted |
| [8DSW](entries/8DSW-vector-files-are-the-case-source.md) | The vector file is the only case source; formula modules, named checks, `land` and `fill`; supersedes TA0G | accepted |
| [AD33](entries/AD33-bundles-are-untrusted-input.md) | Bundles are untrusted input: no tool imports or runs bundle code; static checks; a reviewed, user-approved copy; ONNX checks in `batch` | accepted |
| [YS4C](entries/YS4C-example-removal-by-a-user-ruling.md) | A user ruling that names an example removes it in place of the rebuild wait; the 2026-11-09 ruling names four examples; supersedes NB5F | accepted |
| [1TR6](entries/1TR6-workflow-copies-of-the-keypoint-detector-id.md) | The workflow copies of the id rule follow 52NQ: `{family}-{group}[-{variant}]` in `{family}/{group}/` | accepted |
| [7F6X](entries/7F6X-license-rows-in-the-model-intake.md) | The model intake gets the License rows LC1 to LC6; out of scope and parity follow R6J9; row T11 names the cast | accepted |
| [V8FK](entries/V8FK-license-evidence-and-models-with-no-license.md) | A license page is primary evidence; a model with no known weights license gets no sidecar and no proposal | accepted |
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
| [JY47](entries/JY47-verification-batch-6-in-the-workflow.md) | The workflow, the templates, the skills and `intake_bundle.py` use the verification batches 1, 2, 3 and 6 and 6 input B items (after 50BW) | accepted |
| [4KW6](entries/4KW6-onnxruntime-1-31-for-the-cpu-check.md) | `onnx-cpu` requires `onnxruntime>=1.31` (lock 1.31.1): no fp16 noise in the batch check; the GPU cap stays | accepted |
| [M3RY](entries/M3RY-answers-version-names-an-existing-version.md) | `answers_version` is the version a response answers; `verify` refuses a higher number in the latest response; run `verify` after each response | accepted |

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

- The body of an entry that is not `proposed` changes only by four edits: a link or anchor repair, a
  typo that does not change the meaning, the redaction of private data, and a change of ID with the
  repair of its citations. Each edit adds `_Edited YYYY-MM-DD (#PR): <kind>._` at the end of the
  entry, for example `re-ID from XXXX` ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)). For a
  change of ID, the renamed entry gets `re-ID from XXXX`, and each repaired entry gets
  `citation repair`. Add these two lines only to an entry that is on `development`.
- An absorb document is one of these: the spec, the root or a nested `AGENTS.md`
  ([ADR-GN3D](entries/GN3D-module-decision-logs.md)), the skills, the model addition workflow, the exporter
  guide, the templates of `specs/model-sidecar/templates/`, the Rules of this file with
  [template.md](template.md), and the docstring of a tool in `tools/` for the rules that it checks
  ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)). An accepted entry is absorbed when one absorb
  document states all of its rules.
- The entry that supersedes an old entry restates each rule of the old entry that stays. A link can
  restate a rule. The link must go to a heading of an absorb document, and that heading must state
  the rule. The commit that changes the text under such a heading cites its own entry next to the
  changed rule ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).
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
  entry of the group. It changes no decision. Write one at the end of the spec-build stage, and when the read-path limit
  fails.
- Delete an open-work item when the work is done. Put a dated fact in `open-work.md` or in an
  entry, not in `AGENTS.md`.
- Put long evidence in a tracked file next to the entry, and link to it. A PR that raises a limit
  of `tools/check_decision_log.py` must add an entry.
- An ID changes only on a `re-ID:` line of `tools/check_decision_log.py`, to the ID of a new `--new`
  run. An older entry keeps its lower-case ID in its file name, heading and index row. Do not edit
  older text only to change the case ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).
- Until a commit is on `development`, cite its PR number and the file path, not its SHA ([ADR-0027](entries/0027-single-working-branch.md)).
  The `ADR-` prefix is for citations only: a file name, a
  heading, an index row and a status line hold the bare ID. Cite a provisional entry of another repo
  by the repo name, the PR number and the slug. Do not edit a decided entry only to add or move the
  prefix or the link ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).

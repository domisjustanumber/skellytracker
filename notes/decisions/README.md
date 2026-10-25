# Decision log

This log records technical decisions for skellytracker, with their reasons and evidence. Most entries
are about the model sidecar spec ([`specs/sidecar-spec.md`](../../specs/sidecar-spec.md)), the sidecar
code and the workflow that changes them. Read this file before you change the spec, a sidecar, the
sidecar code, the agent instructions or the PR workflow. Also read [open-work.md](open-work.md). Then
read the Active entries that apply to your task. Then you do not repeat a settled question or a
completed measurement. Read a Deferred entry only for spec work in its area. Read a Historical entry
only to find the reason for a decision ([0035](0035-decision-log-limits.md)).

Each entry gives the decision, its reason, the evidence (when there is evidence), the alternatives
rejected and a "Not repeated" section for pitfalls already found. Entries 0002 to 0012 are
backfilled. They record decisions made before this log existed, and they cite the original sources.
When a decision changes, add a new entry that supersedes the old entry in full. The body of a
decided entry changes only by the edits that the [Rules](#rules) allow.

## Index

### Active

| # | Decision | Status |
|---|----------|--------|
| [0001](0001-decision-log-and-agents-md.md) | Decision log; `AGENTS.md` is the single instructions file; `plans/` is local and ignored | accepted |
| [0002](0002-sidecars-tracked-in-package.md) | Sidecars are tracked in the package tree; ONNX files are not | accepted |
| [0003](0003-tracked-points-native-order.md) | `tracked_points` are in native model output order | accepted |
| [0004](0004-detectors-migrated-in-place.md) | Detectors migrated to sidecars in place; registry keys unchanged | accepted |
| [0005](0005-rtmw-moved-to-rtmw-family.md) | RTMW moved to `keypoint_detectors/rtmw/` with import shims | accepted |
| [0006](0006-yolox-native-contract.md) | The YOLOX sidecar describes the native ONNX contract | accepted |
| [0007](0007-generic-processing-package.md) | Generic pre- and post-processing live in `core/detectors/processing/` | accepted |
| [0008](0008-vnext-scope.md) | `vNEXT` scope, and the features considered and not added | accepted |
| [0010](0010-family-invariant.md) | Family invariant: a size sets only its shape, target size and artifacts | accepted |
| [0011](0011-rtmdet-host-nms.md) | RTMDet: NMS-free graph with host `selection: nms`; no `pre_nms_top_k` | accepted |
| [0013](0013-spec-structure.md) | Spec structure: section files, rule owners, examples, reference implementations, traceability, STE | accepted |
| [0014](0014-spec-lifecycle.md) | Spec lifecycle, the `vNEXT` rule and the new-model workflow | accepted |
| [0016](0016-sidecar-catalogs.md) | Sidecar catalogs: source, reference hashes, roots, discovery and the capability check | accepted |
| [0017](0017-dual-role-sidecar-folder.md) | Folder of a sidecar with both roles | proposed |
| [0018](0018-one-declaration-per-tensor.md) | One declaration for each output tensor, at every version | proposed |
| [0019](0019-output-shape-batch-axis.md) | Batch axis of `outputs[].shape` | proposed |
| [0020](0020-roi-transform-and-source.md) | ROI transform, and a crop that does not come from a detector box | proposed |
| [0021](0021-landmark-extra-outputs.md) | Pose outputs beside the landmarks: presence, handedness and world landmarks | proposed |
| [0022](0022-landmark-depth-divisor.md) | Depth divisor of MediaPipe landmarks | proposed |
| [0023](0023-letterbox-floor-and-scale-inverse.md) | `floor` rounding and a scale inverse for `letterbox` | proposed |
| [0024](0024-simcc-score-rule.md) | SimCC keypoint score rule | proposed |
| [0025](0025-model-id-suffix.md) | Suffix after the part in `model_id` | proposed |
| [0027](0027-single-working-branch.md) | One working branch for the PR stack; one kind of change per PR, stacked PRs, merge method | accepted |
| [0030](0030-no-private-data.md) | No private data in tracked files, commits or PR text; the private-data check and gitleaks | accepted |
| [0031](0031-bootstrap-kit.md) | A bootstrap kit for `AGENTS.md` and the decision log in a new repo; its copies stay in sync with the live files | accepted |
| [0032](0032-entry-numbers-and-edits.md) | Entry numbers with `--next` on parallel branches; four allowed edits, complete supersession, permalinks, `Depends on`, evidence scripts | accepted |
| [0035](0035-decision-log-limits.md) | Higher limits for the decision log: index 18,000 and read path 330,000; the bootstrap kit keeps the 0029 limits | accepted |
| [0036](0036-spec-proposals-folder.md) | The spec keeps its change proposals in `specs/sidecar/proposals/`; each one has a short decision entry "Spec change: <slug>" | accepted |
| [0033](0033-short-sidecars-block.md) | The exporter `AGENTS.md` copies a short fenced "Sidecars" block, not the full Sidecars section | accepted |
| [0034](0034-sidecar-guide-folder.md) | The sidecar guide moves to `specs/exporter-guide/sidecars/`, split at its headings with no change of text | accepted |

### Deferred

These entries are `proposed`. The latest date in their status line is more than 183 days old.

| # | Decision | Status |
|---|----------|--------|

### Historical

These entries are `rejected`, `superseded by NNNN`, `absorbed into <path>#<anchor>` or
`evidence; used by NNNN`.

| # | Decision | Status |
|---|----------|--------|
| [0009](0009-imagenet-bgr-meaning.md) | `imagenet_bgr` changes meaning at `vNEXT`; the legacy meaning stays | absorbed into [`pre/normalization.md#legacy-behaviour`](../../specs/sidecar/pre/normalization.md#legacy-behaviour) |
| [0012](0012-fit-resize-for-rtmo.md) | `fit` resize for RTMO; `pad_value` is required | absorbed into [`pre/resize-fit.md#behaviour`](../../specs/sidecar/pre/resize-fit.md#behaviour) |
| [0015](0015-review-discipline.md) | Review discipline: one kind of change per PR, stacked drafts, merge method | superseded by 0027 |
| [0026](0026-decision-log-size.md) | Size limits for the decision log: read path, absorbed status, consolidation | superseded by 0029 |
| [0028](0028-entry-edits-and-citations.md) | Allowed edits to entries, complete supersession, permalinks, `Depends on`, a mirror rule that 0032 retires | superseded by 0032 |
| [0029](0029-decision-log-read-path.md) | Read path, Deferred proposals, status forms, the open-work file and the size limits | superseded by 0035 |

## Open work

The open work, the repository state and the spec defects are in [open-work.md](open-work.md).

## Rules

- Write one entry for each decision or measurement.
- The body of an entry that is not `proposed` does not change, except for four edits: a link or
  anchor repair, a typo that does not change the meaning, the redaction of private data, and a
  renumber with the repair of its citations. Each edit adds `_Edited YYYY-MM-DD (#PR): <kind>._` at
  the end of the entry. `<kind>` is `link repair`, `typo`, `redaction`, `renumber from NNNN` or
  `citation repair` ([0032](0032-entry-numbers-and-edits.md)).
- A `proposed` entry can change until the user decides it.
- To change a decision, add a new entry. It restates each rule of the old entry that stays, and it
  supersedes the old entry in full. Do not supersede a part of an entry.
- The status line of an entry can change. These changes are allowed: `proposed` to `accepted` or
  `rejected`, `accepted` to `superseded by NNNN`, `accepted` to `absorbed into <path>#<anchor>`, and
  `evidence` to `evidence; used by NNNN`. Each change adds its date and the PR that made it. In the
  same PR, change the status in the index and move the row to the table for the new status.
- The Status cell of an index row has only a status form of its table. The Decision cell has 160
  characters or fewer ([0035](0035-decision-log-limits.md)).
- Move a `proposed` row to Deferred when the latest date in its status line is more than 183 days
  old.
- An accepted entry is absorbed when the spec, `AGENTS.md` or a skill states all of its rules. Then
  that document is the source of the rules.
- A consolidation entry states the rules that stay from a group of entries, and it supersedes each
  entry of the group. Write one at the end of the spec-build stage, and when the read-path limit fails.
- Delete an open-work item when the work is done. Delete a spec defect when its content PR lands.
- Keep the log inside its limits: 18,000 characters for this file, 20,000 for `open-work.md`, 6,000
  for each entry after 0025, and 330,000 for this file, `open-work.md` and all Active entries
  together. Put long evidence in a tracked file next to the entry, and link to it. Put the script
  that produced a measurement in `notes/decisions/scripts/`. The Evidence section names it. Run
  `uv run python tools/check_decision_log.py` to see the read-path size and the warnings at 80% of a
  limit. The doc tests run the same check.
- A decision can be accepted before its spec text lands. Its spec text then comes in a later content
  PR.
- Before you add an entry, run `git fetch --all`. Then run
  `uv run python tools/check_decision_log.py --next`. Give the entry the number of the `next:` line.
  Create its file immediately. Add its index row at the end of the table for its status, in the same
  PR. Gaps in the numbers are allowed.
- Run `--next` again before each push. Act on each `renumber:` line. Both sides of a collision get the
  same verdict ([0032](0032-entry-numbers-and-edits.md)).
- A number is provisional until its entry is on `development`. Change a provisional number only for a
  `renumber:` line, or when `development` already has the number. This change is not an edit of the
  body, so it adds no `_Edited` line.
- To renumber, run `--next`. Rename the file to the new number. Change the number in its heading and
  in its index row. Find the citations with `git grep -n -E "\bNNNN\b|NNNN-"`, and repair each one.
  Ask the user before you change a PR title or a PR body.
- If two entries on `development` have one number, renumber the entry that merged later, in a new
  PR. This command shows the later merge first:
  `git log --first-parent --diff-filter=A --name-only --format=%h upstream/development -- "notes/decisions/NNNN-*.md"`.
  Add `_Edited YYYY-MM-DD (#PR): renumber from NNNN._` to the entry. Add a `citation repair` line to
  each entry on `development` that you repair.
- Do not give a number that an entry had on `development` to a different entry. Do not keep two index
  rows with one number.
- Cite a tracked file with a relative link. Cite a commit, or the code of another repo, with a GitHub
  permalink that pins a full SHA on the default branch of that repo
  ([0032](0032-entry-numbers-and-edits.md)). Do not cite or link `plans/`. Git does not track it
  ([0001](0001-decision-log-and-agents-md.md)).
- Until a commit is on `development`, cite its PR number and the file path, not its SHA
  ([0027](0027-single-working-branch.md)).
- Write the number of another repo's entry with the repo name, for example "OpenMMLab-Exporter 0020".
  A bare number, for example 0016, is always an entry of this log. Cite a provisional entry of another
  repo by the repo name, the PR number and the slug.
- A spec change proposal is an entry with the status `proposed`. The new-model workflow in
  [0014](0014-spec-lifecycle.md) gives its parts.
- A gap record is also an entry with the status `proposed`. It gives a gap or a conflict with the
  spec text, its evidence and the direction of a change, but not all eight parts of a proposal. Its
  Decision section says that it is a gap record. The user can accept or reject a gap record.
- A later proposal for a gap record edits the gap record. It adds the parts that the gap record does
  not have, and the status stays `proposed`. The status line adds the date and the source, for
  example `completed 2026-11-02 (OpenMMLab-Exporter proposal)`. Do not add a second entry for the
  same gap.
- An entry that waits for a decision of another repo has a `**Depends on:**` line under its status
  line.
- Do not import a file, a test or a tool from another repo.
- Write entries in ASD-STE100 Simplified Technical English. Use short sentences, the active voice and
  one instruction in each sentence. "must" is the requirement word. Technical names, field names, enum
  values, formulas, code and YAML stay unchanged.

## Entry template

The file name is `NNNN-<short-slug>.md`.

```markdown
# NNNN — <title>

**Status:** <proposed | accepted | evidence>, <YYYY-MM-DD> (<source>).
**Depends on:** <repo> NNNN (<status> on YYYY-MM-DD), <permalink>

## Decision

## Reason

## Consequences

## Evidence

## Alternatives rejected

## Not repeated

## Open work
```

- **Status.** `accepted` is a decision. `evidence` is a measurement. `proposed` is a spec change
  proposal or a gap record that waits for a decision. A later status change sets `rejected`,
  `superseded by NNNN`, `absorbed into <path>#<anchor>` or `evidence; used by NNNN` (see "Rules").
  The source says who decided or where the entry comes from, for example "user" or "backfilled from
  #81".
- **Depends on.** Optional. Write it only when the entry waits for a decision of another repo. Use a
  permalink ([0032](0032-entry-numbers-and-edits.md)).
- **Decision.** What is decided, written so that a reader can apply it.
- **Reason.** Why. Each entry gives its own reasons.
- **Consequences.** Optional. What becomes harder, what must change later and what the decision
  costs.
- **Evidence.** Write this section only when there is evidence: measurements with their tool, its
  version and the script in `notes/decisions/scripts/`, or code facts with their file and function.
- **Alternatives rejected.** The options that were examined and not used, with the reason for each.
  Omit the section when there are none.
- **Not repeated.** Pitfalls already found. Omit the section when there are none.
- **Open work.** Optional. Write only a link to the [Open work](#open-work) list of this README. Put
  the open-work items in that list, not in the entry.

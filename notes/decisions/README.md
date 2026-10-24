# Decision log

This log records technical decisions for skellytracker, with their reasons and evidence. Most entries
are about the model sidecar spec ([`specs/sidecar-spec.md`](../../specs/sidecar-spec.md)), the sidecar
code and the workflow that changes them. Read this file before you change the spec, a sidecar, the
sidecar code, the agent instructions or the PR workflow. Also read [open-work.md](open-work.md). Then
read the Active entries that apply to your task. Then you do not repeat a settled question or a
completed measurement. Read a Deferred entry only for spec work in its area. Read a Historical entry
only to find the reason for a decision ([0029](0029-decision-log-read-path.md)).

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
| [0009](0009-imagenet-bgr-meaning.md) | `imagenet_bgr` changes meaning at `vNEXT`; the legacy meaning stays | accepted |
| [0010](0010-family-invariant.md) | Family invariant: a size sets only its shape, target size and artifacts | accepted |
| [0011](0011-rtmdet-host-nms.md) | RTMDet: NMS-free graph with host `selection: nms`; no `pre_nms_top_k` | accepted |
| [0012](0012-fit-resize-for-rtmo.md) | `fit` resize for RTMO; `pad_value` is required | accepted |
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
| [0028](0028-entry-edits-and-citations.md) | Allowed edits to entries, complete supersession, permalinks, `Depends on`, the same rules in each repo | accepted |
| [0029](0029-decision-log-read-path.md) | Read path, Deferred proposals, status forms, the open-work file and the size limits | accepted |

### Deferred

These entries are `proposed`. The latest date in their status line is more than 183 days old.

| # | Decision | Status |
|---|----------|--------|

### Historical

These entries are `rejected`, `superseded by NNNN`, `absorbed into <path>#<anchor>` or
`evidence; used by NNNN`.

| # | Decision | Status |
|---|----------|--------|
| [0015](0015-review-discipline.md) | Review discipline: one kind of change per PR, stacked drafts, merge method | superseded by 0027 |
| [0026](0026-decision-log-size.md) | Size limits for the decision log: read path, absorbed status, consolidation | superseded by 0029 |

## Open work

The open work, the repository state and the spec defects are in [open-work.md](open-work.md).

## Rules

- Write one entry for each decision or measurement.
- The body of an entry that is not `proposed` does not change, except for three edits: a link or
  anchor repair, a typo that does not change the meaning, and the redaction of private data. Each
  edit adds `_Edited YYYY-MM-DD (#PR): <kind>._` at the end of the entry
  ([0028](0028-entry-edits-and-citations.md)).
- A `proposed` entry can change until the user decides it.
- To change a decision, add a new entry. It restates each rule of the old entry that stays, and it
  supersedes the old entry in full. Do not supersede a part of an entry.
- The status line of an entry can change. These changes are allowed: `proposed` to `accepted` or
  `rejected`, `accepted` to `superseded by NNNN`, `accepted` to `absorbed into <path>#<anchor>`, and
  `evidence` to `evidence; used by NNNN`. Each change adds its date and the PR that made it. In the
  same PR, change the status in the index and move the row to the table for the new status.
- The Status cell of an index row has only a status form of its table. The Decision cell has 160
  characters or fewer ([0029](0029-decision-log-read-path.md)).
- Move a `proposed` row to Deferred when the latest date in its status line is more than 183 days
  old.
- An accepted entry is absorbed when the spec, `AGENTS.md` or a skill states all of its rules. Then
  that document is the source of the rules.
- A consolidation entry states the rules that stay from a group of entries, and it supersedes each
  entry of the group. Write one at the end of the spec-build stage, and when the read-path limit fails.
- Delete an open-work item when the work is done. Delete a spec defect when its content PR lands.
- Keep the log inside its limits: 14,000 characters for this file, 20,000 for `open-work.md`, 6,000
  for each entry after 0025, and 220,000 for this file, `open-work.md` and all Active entries
  together. Put long evidence in a tracked file next to the entry, and link to it. Run
  `uv run python tools/check_decision_log.py` to see the read-path size and the warnings at 80% of a
  limit. The doc tests run the same check.
- A decision can be accepted before its spec text lands. Its spec text then comes in a later content
  PR.
- Give a new entry the number after the highest number in the index. Add the entry to the index in
  the same PR.
- Cite a tracked file with a relative link. Cite a commit, or the code of another repo, with a GitHub
  permalink that pins a full SHA on the default branch of that repo
  ([0028](0028-entry-edits-and-citations.md)). Do not cite or link `plans/`. Git does not track it
  ([0001](0001-decision-log-and-agents-md.md)).
- Until a commit is on `development`, cite its PR number and the file path, not its SHA
  ([0027](0027-single-working-branch.md)).
- Write the number of another repo's entry with the repo name, for example "OpenMMLab-Exporter 0020".
  A bare number, for example 0016, is always an entry of this log.
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
- OpenMMLab-Exporter uses the same rules. Each repo keeps its own copy. A change of these rules needs
  a matching PR in the other repo. No file of one repo imports from the other repo.
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
  permalink ([0028](0028-entry-edits-and-citations.md)).
- **Decision.** What is decided, written so that a reader can apply it.
- **Reason.** Why. Each entry gives its own reasons.
- **Consequences.** Optional. What becomes harder, what must change later and what the decision
  costs.
- **Evidence.** Write this section only when there is evidence: measurements, or code facts with
  their file and function.
- **Alternatives rejected.** The options that were examined and not used, with the reason for each.
  Omit the section when there are none.
- **Not repeated.** Pitfalls already found. Omit the section when there are none.
- **Open work.** Optional. Write only a link to the [Open work](#open-work) list of this README. Put
  the open-work items in that list, not in the entry.

# Decision log

This log records technical decisions for skellytracker, with their reasons and evidence. Most entries
are about the model sidecar spec ([`specs/sidecar-spec.md`](../../specs/sidecar-spec.md)), the sidecar
code and the workflow that changes them. Read this file before you change the spec, a sidecar, the
sidecar code, the agent instructions or the PR workflow. Also read [open-work.md](open-work.md). Then
read the Active entries that apply to your task. Then you do not repeat a settled question or a
completed measurement. Read a Proposed entry only for spec work in its section, or when a skill tells
you to. Read an entry of [historical.md](historical.md) only to find the reason for a decision
([z934](z934-decision-log-index-and-read-path.md)).

Each entry gives the decision, its reason, the evidence (when there is evidence), the alternatives
rejected and a "Not repeated" section for pitfalls already found. Entries 0002 to 0012 are
backfilled. They record decisions made before this log existed, and they cite the original sources.
When a decision changes, add a new entry that supersedes the old entry in full. The body of a
decided entry changes only by the edits that the [Rules](#rules) allow. To write an entry, use
[template.md](template.md).

## Index

### Active

These entries are `accepted` or `evidence`.

| # | Decision | Status |
|---|----------|--------|
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

### Proposed

These entries are spec change proposals and gap records that wait for a decision of the user. Section
is the spec section of the change, or `none` when the change has no one section. Find the pending
proposals of a section here and in the [proposal index](../../specs/sidecar/proposals/README.md).

| # | Decision | Section | Status |
|---|----------|---------|--------|
| [0017](0017-dual-role-sidecar-folder.md) | Folder of a sidecar with both roles | `format.file_layout` | proposed |
| [0018](0018-one-declaration-per-tensor.md) | One declaration for each output tensor, at every version | `common.outputs` | proposed |
| [0019](0019-output-shape-batch-axis.md) | Batch axis of `outputs[].shape` | `common.outputs` | proposed |
| [0020](0020-roi-transform-and-source.md) | ROI transform, and a crop that does not come from a detector box; spec change `roi-transform-and-source` | `pre.resize.rotated_roi_crop` | proposed |
| [0021](0021-landmark-extra-outputs.md) | Pose outputs beside the landmarks: presence, handedness and world landmarks; spec change `landmark-extra-outputs` | `post.pose.extra_outputs` | proposed |
| [0022](0022-landmark-depth-divisor.md) | Depth divisor of MediaPipe landmarks; spec change `landmark-depth-divisor` | `post.pose.decode.coordinate` | proposed |
| [0023](0023-letterbox-floor-and-scale-inverse.md) | `floor` rounding and a scale inverse for `letterbox` | `pre.resize.letterbox` | proposed |
| [0024](0024-simcc-score-rule.md) | SimCC keypoint score rule; spec change `simcc-score-rule` | `post.pose.decode.simcc` | proposed |
| [0025](0025-model-id-suffix.md) | Suffix after the part in `model_id`; spec change `model-id-suffix` | `common.identity` | proposed |
| [0037](0037-affine-crop-arithmetic.md) | Spec change: affine-crop-arithmetic (`pre.resize.affine_person_crop`) | `pre.resize.affine_person_crop` | proposed |
| [0038](0038-heatmap-decode-refinement.md) | Spec change: heatmap-decode-refinement (`post.pose.decode.heatmap`) | `post.pose.decode.heatmap` | proposed |
| [0039](0039-keypoint-visibility.md) | Spec change: keypoint-visibility (`post.pose.visibility`) | `post.pose.visibility` | proposed |
| [0040](0040-nms-clamp-order.md) | Spec change: nms-clamp-order (`post.det.selection.nms`) | `post.det.selection.nms` | proposed |
| [0041](0041-rtmdet-host-nms-filters.md) | RTMDet: host `selection: nms` with the mmdet candidate filters, clamp and visit order | `post.det.selection.nms` | proposed |
| [0042](0042-vnext-scope-nms-filters.md) | `vNEXT` scope and the features not added; `nms.pre_nms_top_k` and `nms.min_bbox_size` leave the list | none | proposed |
| [0043](0043-normalize-arithmetic.md) | Spec change: normalize-arithmetic (`pre.normalize`) | `pre.normalize` | proposed |
| [0044](0044-omitted-upstream-output.md) | Spec change: omitted-upstream-output (no section; workflow verdict `omitted`; supersedes 0014 on acceptance) | none | proposed |
| [0045](0045-pose-decode-flip-test.md) | Spec change: pose-decode-flip-test (`post.pose.flip_test`) | `post.pose.flip_test` | proposed |
| [0046](0046-size-codes.md) | Spec change: size-codes (`common.sizes`) | `common.sizes` | proposed |
| [0047](0047-roi-refiner-role.md) | Spec change: roi-refiner-role (`post.roi_refiner`) | `post.roi_refiner` | proposed |
| [0048](0048-vnext-scope-mediapipe-rotated-crops.md) | `vNEXT` scope and the features not added; MediaPipe-Exporter joins, and rotated crops leave the list | none | proposed |

The entries that are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done` are in [historical.md](historical.md).

## Open work

The open work, the repository state and the spec defects are in [open-work.md](open-work.md).

## Rules

- Write one entry for each decision or measurement. Use [template.md](template.md).
- The read path is this file, `open-work.md` and the Active entries that apply to your task. Read a
  Proposed entry only for spec work in its section, or when a skill tells you to. Read an entry of
  `historical.md` only to find the reason for a decision.
- The body of an entry that is not `proposed` does not change, except for four edits: a link or
  anchor repair, a typo that does not change the meaning, the redaction of private data, and a
  change of ID with the repair of its citations. Each edit adds `_Edited YYYY-MM-DD (#PR): <kind>._`
  at the end of the entry. `<kind>` is `link repair`, `typo`, `redaction`, `re-ID from XXXX` or
  `citation repair` ([gtwq](gtwq-random-entry-ids.md)). An old `renumber from NNNN` line stays.
- A `proposed` entry can change until the user decides it.
- To change a decision, add a new entry. It restates each rule of the old entry that stays, and it
  supersedes the old entry in full. Do not supersede a part of an entry.
- The status line of an entry can change. These changes are allowed: `proposed` to `accepted` or
  `rejected`, `accepted` to `superseded by XXXX`, `accepted` to `absorbed into <path>#<anchor>`,
  `accepted` to `done`, and `evidence` to `evidence; used by XXXX`. Each change adds its date and the
  PR that made it. In the same PR, change the status in the index and move the row to the table for
  the new status. An `evidence` entry becomes `evidence; used by XXXX` when an accepted entry cites
  it for its decision. Its Decision cell keeps the one-line result.
- The tables and their status forms: Active (`accepted`, `evidence`) and Proposed (`proposed`) in this
  file, and Historical (`rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
  `evidence; used by XXXX`, `done`) in [historical.md](historical.md). The Status cell has only a
  status form of its table. `XXXX` must be an entry that is not `proposed` or `rejected`. The
  Decision cell has 160 characters or fewer
  ([z934](z934-decision-log-index-and-read-path.md)).
- A Proposed row has a Section cell: the section ID of the change in backticks, or `none`. A new
  section ID is allowed.
- An accepted entry is absorbed when one of these documents states all of its rules: the spec,
  `AGENTS.md`, the skills, the exporter guide, the templates of `specs/sidecar/templates/`, and the
  Rules of this file with [template.md](template.md). Then that document is the source of the rules.
- An accepted entry that records a one-off action, with no rule that stays, is `done` when the action
  is complete.
- A consolidation entry states the rules that stay from a group of entries, and it supersedes each
  entry of the group. It changes no decision. Write one at the end of the spec-build stage, and when
  the read-path limit fails.
- Delete an open-work item when the work is done. Delete a spec defect when its content PR lands.
- Keep the log inside its limits: 18,000 characters for this file, 20,000 for `open-work.md`, 6,000
  for each entry after 0025, and 330,000 for the read path: this file, `open-work.md` and the Active
  entries. Proposed and Historical entries are not in the read path. Put long evidence in a tracked
  file next to the entry, and link to it. Put the script that produced a measurement in
  `notes/decisions/scripts/`. The Evidence section names it. Run
  `uv run python tools/check_decision_log.py` to see the read-path size and the warnings at 80% of a
  limit. The doc tests run the same check.
- The tool counts characters after it changes CRLF to LF. It checks the rows, the tables, the cells,
  the status forms, the `XXXX` of each status and the limits. A warning does not fail the doc tests.
  An entry does not warn. A PR can lower a limit. A PR that raises a limit must add an entry. After
  the first consolidation, lower the read-path limit to 160,000 characters.
- The exporter guide is normative for the workflow. The sidecar spec is normative for the meaning of
  a sidecar.
- The bootstrap kit takes these rules. Its tool keeps the limits 14,000 for the index and 220,000 for
  the read path. The kit keeps an optional mirror rule.
- A decision can be accepted before its spec text lands. Its spec text then comes in a later content
  PR.
- An entry ID has 4 characters from `0123456789abcdefghjkmnpqrstvwxyz`. The first character of a new
  ID is a letter. The entries 0001 to 0048 keep their numbers. Do not make a new all-digit ID
  ([gtwq](gtwq-random-entry-ids.md)).
- Before you add an entry, run `git fetch --all` when you can. Then run
  `uv run python tools/check_decision_log.py --new`. Give the entry the ID of the `new:` line. Create
  its file immediately. Add its index row at the end of the table for its status, in the same PR. The
  index order is the order of addition.
- The pre-push hook runs `--collisions`, the same check without the `new:` line. Act on each `re-ID:`
  line. Both sides of a collision get the same verdict: an entry on `development` wins, then an entry
  on a remote-tracking branch, then the entry whose first commit has the earlier author date, then
  the file name that sorts first. An uncommitted file loses to a committed file. Refs merged into
  `HEAD`, the upstream and push refs of the branch, `backup/` branches and an old file name of an
  entry are not collisions. An ID does not change for a different reason.
- To change an ID, run `--new`. Rename the file to the new ID. Change the ID in its heading and in its
  index row. Find the citations with `git grep -n -E "\bXXXX\b|XXXX-"`, and repair each one. Ask the
  user before you change a PR title or a PR body. If the entry is on `development`, add
  `_Edited YYYY-MM-DD (#PR): re-ID from XXXX._` to it, and a `citation repair` line to each entry on
  `development` that you repair.
- Do not give an ID that an entry had on `development` to a different entry. Do not keep two index
  rows with one ID.
- Cite a tracked file with a relative link. Cite a commit, or the code of another repo, with a GitHub
  permalink that pins a full SHA on the default branch of that repo
  ([gtwq](gtwq-random-entry-ids.md)). Do not cite or link `plans/`. Git does not track it
  ([0001](0001-decision-log-and-agents-md.md)).
- Until a commit is on `development`, cite its PR number and the file path, not its SHA
  ([0027](0027-single-working-branch.md)).
- Write the ID of another repo's entry with the repo name, for example "OpenMMLab-Exporter 0020". A
  bare ID, for example 0016 or gtwq, is always an entry of this log. Write an ID in YAML front matter
  in quotes. Cite a provisional entry of another repo by the repo name, the PR number and the slug.
  End each commit subject that adds or changes an entry with `(<id>)`.
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
- Do not put a dated status line in `AGENTS.md`. Put a dated fact in `open-work.md` or in an entry.
- Do not import a file, a test or a tool from another repo. The rules of this log do not follow the
  log of another repo.
- Write entries in ASD-STE100 Simplified Technical English. Use short sentences, the active voice and
  one instruction in each sentence. "must" is the requirement word. Technical names, field names, enum
  values, formulas, code and YAML stay unchanged.

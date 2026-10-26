# Decision log: historical entries

These entries are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done`. They are not in the read path. Read an entry here only to find
the reason for a decision. The [index](README.md) has the Active and Proposed entries and the
[Rules](README.md#rules).

### Historical

| # | Decision | Status |
|---|----------|--------|
| [0009](0009-imagenet-bgr-meaning.md) | `imagenet_bgr` changes meaning at `vNEXT`; the legacy meaning stays | absorbed into [`pre/normalization.md#legacy-behaviour`](../../specs/model-sidecar/pre/normalization.md#legacy-behaviour) |
| [0012](0012-fit-resize-for-rtmo.md) | `fit` resize for RTMO; `pad_value` is required | absorbed into [`pre/resize-fit.md#behaviour`](../../specs/model-sidecar/pre/resize-fit.md#behaviour) |
| [0015](0015-review-discipline.md) | Review discipline: one kind of change per PR, stacked drafts, merge method | superseded by 0027 |
| [0026](0026-decision-log-size.md) | Size limits for the decision log: read path, absorbed status, consolidation | superseded by 0029 |
| [0028](0028-entry-edits-and-citations.md) | Allowed edits to entries, complete supersession, permalinks, `Depends on`, a mirror rule that 0032 retires | superseded by 0032 |
| [0029](0029-decision-log-read-path.md) | Read path, Deferred proposals, status forms, the open-work file and the size limits | superseded by 0035 |
| [0032](0032-entry-numbers-and-edits.md) | Entry numbers with `--next` on parallel branches; four allowed edits, complete supersession, permalinks, `Depends on`, evidence scripts | superseded by gtwq |
| [0035](0035-decision-log-limits.md) | Higher limits for the decision log: index 18,000 and read path 330,000; the bootstrap kit keeps the 0029 limits | superseded by z934 |
| [0036](0036-spec-proposals-folder.md) | The spec keeps its change proposals in `specs/model-sidecar/proposals/`; each one has a short decision entry "Spec change: <slug>" | superseded by faac |
| [0001](0001-decision-log-and-agents-md.md) | Decision log; `AGENTS.md` is the single instructions file; `plans/` is local and ignored | absorbed into [`AGENTS.md#repository-instructions`](../../AGENTS.md#repository-instructions) |
| [0027](0027-single-working-branch.md) | One working branch for the PR stack; one kind of change per PR, stacked PRs, merge method | absorbed into [`AGENTS.md#6-git-rules`](../../AGENTS.md#6-git-rules) |
| [0030](0030-no-private-data.md) | No private data in tracked files, commits or PR text; the private-data check and gitleaks | absorbed into [`AGENTS.md#8-private-data`](../../AGENTS.md#8-private-data) |
| [0031](0031-bootstrap-kit.md) | A bootstrap kit for `AGENTS.md` and the decision log in a new repo; its copies stay in sync with the live files | absorbed into [`AGENTS.md#5-decision-log`](../../AGENTS.md#5-decision-log) |
| [0033](0033-short-sidecars-block.md) | The exporter `AGENTS.md` copies a short fenced "Sidecars" block, not the full Sidecars section | absorbed into [`draft/exporter-guide/sidecars/README.md#the-block-for-the-exporter-agentsmd`](../../specs/draft/exporter-guide/sidecars/README.md#the-block-for-the-exporter-agentsmd) |
| [0034](0034-sidecar-guide-folder.md) | The sidecar guide moves to `specs/exporter-guide/sidecars/`, split at its headings with no change of text | superseded by x64y |
| [gtwq](gtwq-random-entry-ids.md) | Random 4-character entry IDs with `--new`; four allowed edits, complete supersession, permalinks, `Depends on`, evidence scripts | superseded by b1c0 |
| [z934](z934-decision-log-index-and-read-path.md) | Index and read path: Proposed table off the read path, `historical.md`, `template.md`, `done`, absorbing documents | absorbed into [`decisions/README.md#rules`](README.md#rules) |
| [faac](faac-proposal-records.md) | Spec change proposals in `specs/model-sidecar/proposals/`; a short `proposed` entry for each; no open-work line for each proposal | absorbed into [`propose-sidecar-change/SKILL.md#step-3-copy-the-proposal-into-the-spec-folder`](../../.claude/skills/propose-sidecar-change/SKILL.md#step-3-copy-the-proposal-into-the-spec-folder) |
| [0014](0014-spec-lifecycle.md) | Spec lifecycle, the `vNEXT` rule and the new-model workflow | absorbed into [`model-sidecar/model-addition-workflow/README.md#model-addition-workflow`](../../specs/model-sidecar/model-addition-workflow/README.md#model-addition-workflow) |
| [0013](0013-spec-structure.md) | Spec structure: section files, rule owners, examples, reference implementations, traceability, STE | absorbed into [`change-sidecar-spec/SKILL.md#rules-for-each-spec-edit`](../../.claude/skills/change-sidecar-spec/SKILL.md#rules-for-each-spec-edit) |
| [0002](0002-sidecars-tracked-in-package.md) | Sidecars are tracked in the package tree; ONNX files are not | absorbed into [`common/sizes-and-artifacts.md#implementer-guidance`](../../specs/model-sidecar/common/sizes-and-artifacts.md#implementer-guidance) |
| [0003](0003-tracked-points-native-order.md) | `tracked_points` are in native model output order | absorbed into [`post/pose-schema.md#posetracked_points`](../../specs/model-sidecar/post/pose-schema.md#posetracked_points) |
| [0004](0004-detectors-migrated-in-place.md) | Detectors migrated to sidecars in place; registry keys unchanged | absorbed into [`AGENTS.md#1-purpose`](../../AGENTS.md#1-purpose) |
| [0005](0005-rtmw-moved-to-rtmw-family.md) | RTMW moved to `keypoint_detectors/rtmw/` with import shims | absorbed into [`AGENTS.md#1-purpose`](../../AGENTS.md#1-purpose) |
| [0006](0006-yolox-native-contract.md) | The YOLOX sidecar describes the native ONNX contract | absorbed into [`format/versioning.md#implementer-guidance`](../../specs/model-sidecar/format/versioning.md#implementer-guidance) |
| [0007](0007-generic-processing-package.md) | Generic pre- and post-processing live in `core/detectors/processing/` | absorbed into [`AGENTS.md#1-purpose`](../../AGENTS.md#1-purpose) |
| [0010](0010-family-invariant.md) | Family invariant: a size sets only its shape, target size and artifacts | absorbed into [`common/sizes-and-artifacts.md#sizes`](../../specs/model-sidecar/common/sizes-and-artifacts.md#sizes) |
| [0016](0016-sidecar-catalogs.md) | Sidecar catalogs: source, reference hashes, roots, discovery and the capability check | absorbed into [`model-sidecar/README.md#section-map`](../../specs/model-sidecar/README.md#section-map) |
| [vac0](vac0-record-a-changed-proposal.md) | A changed exporter proposal: a full new copy, the same entry, a ticked "Before acceptance" list | superseded by b1c0 |

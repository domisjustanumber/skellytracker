# Decision log: historical entries

These entries are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done`. They are not in the read path. Read an entry here only to find
the reason for a decision. The [index](README.md) has the Active and Proposed entries and the
[Rules](README.md#rules).

### Historical

| # | Decision | Status |
|---|----------|--------|
| [0015](entries/0015-review-discipline.md) | Review discipline: one kind of change per PR, stacked drafts, merge method | superseded by 0027 |
| [0026](entries/0026-decision-log-size.md) | Size limits for the decision log: read path, absorbed status, consolidation | superseded by 0029 |
| [0028](entries/0028-entry-edits-and-citations.md) | Allowed edits to entries, complete supersession, permalinks, `Depends on`, a mirror rule that 0032 retires | superseded by 0032 |
| [0029](entries/0029-decision-log-read-path.md) | Read path, Deferred proposals, status forms, the open-work file and the size limits | superseded by 0035 |
| [0032](entries/0032-entry-numbers-and-edits.md) | Entry numbers with `--next` on parallel branches; four allowed edits, complete supersession, permalinks, `Depends on`, evidence scripts | superseded by gtwq |
| [0035](entries/0035-decision-log-limits.md) | Higher limits for the decision log: index 18,000 and read path 330,000; the bootstrap kit keeps the 0029 limits | superseded by z934 |
| [0036](entries/0036-spec-proposals-folder.md) | The spec keeps its change proposals in `specs/model-sidecar/proposals/`; each one has a short decision entry "Spec change: <slug>" | superseded by faac |
| [0001](entries/0001-decision-log-and-agents-md.md) | Decision log; `AGENTS.md` is the single instructions file; `plans/` is local and ignored | superseded by hxy8 |
| [0027](entries/0027-single-working-branch.md) | One working branch for the PR stack; one kind of change per PR, stacked PRs, merge method | absorbed into [`AGENTS.md#6-git-rules`](../AGENTS.md#6-git-rules) |
| [0030](entries/0030-no-private-data.md) | No private data in tracked files, commits or PR text; the private-data check and gitleaks | superseded by FDTD |
| [0031](entries/0031-bootstrap-kit.md) | A bootstrap kit for `AGENTS.md` and the decision log in a new repo; its copies stay in sync with the live files | superseded by Z05A |
| [0033](entries/0033-short-sidecars-block.md) | The exporter `AGENTS.md` copies a short fenced "Sidecars" block, not the full Sidecars section | absorbed into [`draft/exporter-guide/sidecars/README.md#the-block-for-the-exporter-agentsmd`](../specs/draft/exporter-guide/sidecars/README.md#the-block-for-the-exporter-agentsmd) |
| [0034](entries/0034-sidecar-guide-folder.md) | The sidecar guide moves to `specs/exporter-guide/sidecars/`, split at its headings with no change of text | superseded by x64y |
| [gtwq](entries/gtwq-random-entry-ids.md) | Random 4-character entry IDs with `--new`; four allowed edits, complete supersession, permalinks, `Depends on`, evidence scripts | superseded by b1c0 |
| [z934](entries/z934-decision-log-index-and-read-path.md) | Index and read path: Proposed table off the read path, `historical.md`, `template.md`, `done`, absorbing documents | superseded by Z05A |
| [faac](entries/faac-proposal-records.md) | Spec change proposals in `specs/model-sidecar/proposals/`; a short `proposed` entry for each; no open-work line for each proposal | superseded by FADS |
| [0014](entries/0014-spec-lifecycle.md) | Spec lifecycle, the `vNEXT` rule and the new-model workflow | superseded by FADS |
| [0013](entries/0013-spec-structure.md) | Spec structure: section files, rule owners, examples, reference implementations, traceability, STE | superseded by TA0G |
| [0002](entries/0002-sidecars-tracked-in-package.md) | Sidecars are tracked in the package tree; ONNX files are not | absorbed into [`common/sizes-and-artifacts.md#implementer-guidance`](../specs/model-sidecar/common/sizes-and-artifacts.md#implementer-guidance) |
| [0003](entries/0003-tracked-points-native-order.md) | `tracked_points` are in native model output order | absorbed into [`post/pose-schema.md#posetracked_points`](../specs/model-sidecar/post/pose-schema.md#posetracked_points) |
| [0004](entries/0004-detectors-migrated-in-place.md) | Detectors migrated to sidecars in place; registry keys unchanged | absorbed into [`AGENTS.md#1-purpose`](../AGENTS.md#1-purpose) |
| [0005](entries/0005-rtmw-moved-to-rtmw-family.md) | RTMW moved to `keypoint_detectors/rtmw/` with import shims | absorbed into [`AGENTS.md#1-purpose`](../AGENTS.md#1-purpose) |
| [0006](entries/0006-yolox-native-contract.md) | The YOLOX sidecar describes the native ONNX contract | absorbed into [`format/versioning.md#implementer-guidance`](../specs/model-sidecar/format/versioning.md#implementer-guidance) |
| [0007](entries/0007-generic-processing-package.md) | Generic pre- and post-processing live in `core/detectors/processing/` | absorbed into [`AGENTS.md#1-purpose`](../AGENTS.md#1-purpose) |
| [0016](entries/0016-sidecar-catalogs.md) | Sidecar catalogs: source, reference hashes, roots, discovery and the capability check | absorbed into [`model-sidecar/README.md#section-map`](../specs/model-sidecar/README.md#section-map) |
| [vac0](entries/vac0-record-a-changed-proposal.md) | A changed exporter proposal: a full new copy, the same entry, a ticked "Before acceptance" list | superseded by b1c0 |
| [b1c0](entries/b1c0-adr-citation-prefix.md) | Cite an entry as `ADR-<id>`; commit subjects end with `(ADR-<id>)`; restates the ID and edit rules of gtwq and the record-again rules of vac0 | superseded by HJNP |
| [hxy8](entries/hxy8-scoped-agent-instructions.md) | Core root `AGENTS.md`; folder rules in a nested `AGENTS.md` with an importing `CLAUDE.md`; procedures as skills; supersedes 0001 | superseded by GN3D |
| [k6dz](entries/k6dz-model-sidecar-folder.md) | The sidecar spec folder and its entry point `sidecar-spec.md` move to `specs/model-sidecar/`; a move with no change of rule | superseded by D9VT |
| [CNSN](entries/CNSN-spec-build-actions-after-the-fact.md) | Records three past spec-build actions: the `int8` removal with its package code, the in-package batch converter, the draft batch-conversion section | done |
| [ngnb](entries/ngnb-supersede-an-absorbed-entry.md) | An absorbed entry can be superseded: its status changes from `absorbed into <path>#<anchor>` to `superseded by XXXX` | superseded by JW9N |
| [HJNP](entries/HJNP-upper-case-entry-ids.md) | Upper-case entry IDs in new entries and new citations; older IDs stay; restates the prefix, ID, edit and record-again rules of b1c0 | superseded by JW9N |
| [pykx](entries/pykx-submission-folders.md) | Submission files in `plans/sidecar/`: a folder for each model and each proposal, with target file names; candidate examples allowed | superseded by FADS |
| [a33q](entries/a33q-vector-case-form.md) | One vector case form: optional `function` and `compare`, errors by rule ID, NaN, exporter entries; 64 KiB; one writer | superseded by TA0G |
| [SR1E](entries/SR1E-reset-of-the-spec-build-proposals.md) | Deletes the 21 proposed spec-log entries 0017-0025 and 0037-0048, the 14 old proposal records and the `proposed:` inventory list | done |
| [JC4T](entries/JC4T-parity-gates-and-batch-conversion-check.md) | Measured gates as controls; step 5 by role; the batch-conversion check (`S = 3`, b1 to b4, V0 to V6); the publish rule; the exporter run in the checkout | superseded by JB5J |
| [JW9N](entries/JW9N-restate-a-kept-rule-by-a-link.md) | A link to a heading that states a kept rule restates it; later edits there cite their entry; the chain rule; supersedes ngnb and HJNP | superseded by Z05A |
| [NSR2](entries/NSR2-adr-citations-as-links-in-each-text.md) | Cite an entry as a link with `ADR-<ID>` as link text in each text: files, plans, PR bodies, replies; commit bodies with no link | superseded by Z05A |
| [b9fm](entries/b9fm-finished-sidecar-plans.md) | The reference-examples procedure moves to the workflow; the implementation plan links to the spec backlog; the coverage note is frozen evidence | superseded by 5WKW |

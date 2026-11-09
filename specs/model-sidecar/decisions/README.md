# Decision log of the sidecar spec

This log records the decisions that apply only to the model sidecar spec
([`specs/model-sidecar/README.md`](../README.md)). It is the log of the sidecar spec
module. The [Rules](../../../decisions/README.md#rules) of the root log apply to this log. To write an
entry, use the root [template.md](../../../decisions/template.md). Read this file and
[open-work.md](open-work.md) before you change the spec, a sidecar or an example. Read an entry of
[historical.md](historical.md) only to find the reason for a decision.

## Index

### Active

These entries are `accepted` or `evidence`.

| # | Decision | Status |
|---|----------|--------|
| [NBG2](entries/NBG2-license-and-training-data-without-the-deferred-examples.md) | New draft section `common.license`; RTMW rebuild replaces its example, three deferred examples go; supersedes SE3Y | accepted |
| [50BW](entries/50BW-verification-batches.md) | Spec change: the verification batches of `static-batch-v1` are 1, 2, 3 and 6, not 1, 2, 3 and 4 (guidance only) | accepted |
| [1VMX](entries/1VMX-nms-key-exclusion.md) | Spec change: the NMS reference refuses the keys of `V-post.det.selection.nms-1` | accepted |
| [R6J9](entries/R6J9-test-time-steps-and-unreachable-branches.md) | `out of scope` covers a test-time augmentation and an undeclared extra decode value; parity needs no image for an unreachable branch | accepted |

### Proposed

These entries are spec change proposals that wait for a decision of the user. Section is the spec
section of the change, or `none` when the change has no one section. Find the pending
proposals of a section here.

| # | Decision | Section | Status |
|---|----------|---------|--------|
| [52NQ](entries/52NQ-model-id-suffix.md) | Spec change: keypoint detector id `{family}-{group}[-{variant}]` | `common.identity` | proposed |
| [KZ9J](entries/KZ9J-model-id-suffix-rtmo-removed.md) | Spec change: follow-up of 52NQ; the example `rtmo-body7` is removed, not rebuilt | `common.identity` | proposed |

The entries that are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done` are in [historical.md](historical.md).

## Open work

The open work of the sidecar spec and the spec defects are in [open-work.md](open-work.md).

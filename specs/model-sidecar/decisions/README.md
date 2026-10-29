# Decision log of the sidecar spec

This log records the decisions that apply only to the model sidecar spec
([`specs/model-sidecar/sidecar-spec.md`](../sidecar-spec.md)). It is the log of the sidecar spec
module. The [Rules](../../../decisions/README.md#rules) of the root log apply to this log. To write an
entry, use the root [template.md](../../../decisions/template.md). Read this file and
[open-work.md](open-work.md) before you change the spec, a sidecar or an example. Read an entry of
[historical.md](historical.md) only to find the reason for a decision.

## Index

### Active

These entries are `accepted` or `evidence`.

| # | Decision | Status |
|---|----------|--------|
| [0011](0011-rtmdet-host-nms.md) | RTMDet: NMS-free graph with host `selection: nms`; no `pre_nms_top_k` | accepted |
| [YNX0](YNX0-vnext-scope-list.md) | `vNEXT` scope: one list in the changelog; acceptance or a `describes` landing adds a model; a proposal gives `vNEXT` text only | accepted |

### Proposed

These entries are spec change proposals that wait for a decision of the user. Section is the spec
section of the change, or `none` when the change has no one section. Find the pending
proposals of a section here and in the [proposal index](../proposals/README.md).

| # | Decision | Section | Status |
|---|----------|---------|--------|

The entries that are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done` are in [historical.md](historical.md).

## Open work

The open work of the sidecar spec and the spec defects are in [open-work.md](open-work.md).

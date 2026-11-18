# Decision log of the sidecar spec

This log records the decisions that apply only to the model sidecar spec
([`specs/model-sidecar/README.md`](../README.md)). It is the log of the sidecar spec
module. The [Rules](../../../decisions/README.md#rules) of the root log apply to this log. To write an
entry, use the root [template.md](../../../decisions/template.md). Read this file and
[open-work.md](open-work.md) before you change the spec, a sidecar or an example. Read an entry of
[historical.md](historical.md) only to find the reason for a decision.

## Index

### Active

These entries are `accepted`.

| # | Decision | Status |
|---|----------|--------|
| [J1HK](entries/J1HK-resize-pixel-tolerance.md) | Spec change: resize limit, before the normalization: at most 1 step with `uint8`, at most 0.05 with `float32` | accepted |

### Evidence

These entries are `evidence`: measurements. They are not in the read path. Scan these rows before
you make a measurement ([Rules](../../../decisions/README.md#rules)).

| # | Decision | Status |
|---|----------|--------|

### Proposed

These entries are spec change proposals that wait for a decision of the user. Section is the spec
section of the change, or `none` when the change has no one section. Find the pending
proposals of a section here.

| # | Decision | Section | Status |
|---|----------|---------|--------|

The entries that are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done` are in [historical.md](historical.md).

## Open work

The open work of the sidecar spec and the spec defects are in [open-work.md](open-work.md).

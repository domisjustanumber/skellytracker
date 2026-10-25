# Decision log: historical entries

These entries are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done`. They are not in the read path. Read an entry here only to find
the reason for a decision. The [index](README.md) has the Active and Proposed entries and the
[Rules](README.md#rules).

### Historical

| # | Decision | Status |
|---|----------|--------|
| [0009](0009-imagenet-bgr-meaning.md) | `imagenet_bgr` changes meaning at `vNEXT`; the legacy meaning stays | absorbed into [`pre/normalization.md#legacy-behaviour`](../../specs/sidecar/pre/normalization.md#legacy-behaviour) |
| [0012](0012-fit-resize-for-rtmo.md) | `fit` resize for RTMO; `pad_value` is required | absorbed into [`pre/resize-fit.md#behaviour`](../../specs/sidecar/pre/resize-fit.md#behaviour) |
| [0015](0015-review-discipline.md) | Review discipline: one kind of change per PR, stacked drafts, merge method | superseded by 0027 |
| [0026](0026-decision-log-size.md) | Size limits for the decision log: read path, absorbed status, consolidation | superseded by 0029 |
| [0028](0028-entry-edits-and-citations.md) | Allowed edits to entries, complete supersession, permalinks, `Depends on`, a mirror rule that 0032 retires | superseded by 0032 |
| [0029](0029-decision-log-read-path.md) | Read path, Deferred proposals, status forms, the open-work file and the size limits | superseded by 0035 |
| [0032](0032-entry-numbers-and-edits.md) | Entry numbers with `--next` on parallel branches; four allowed edits, complete supersession, permalinks, `Depends on`, evidence scripts | superseded by gtwq |
| [0035](0035-decision-log-limits.md) | Higher limits for the decision log: index 18,000 and read path 330,000; the bootstrap kit keeps the 0029 limits | superseded by z934 |

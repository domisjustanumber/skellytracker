# Decision log of the sidecar spec: historical entries

These entries are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done`. They are not in the read path. Read an entry here only to find
the reason for a decision. The [index](README.md) has the Active and Proposed entries. The
[Rules](../../../decisions/README.md#rules) are in the root log.

### Historical

| # | Decision | Status |
|---|----------|--------|
| [0009](0009-imagenet-bgr-meaning.md) | `imagenet_bgr` changes meaning at `vNEXT`; the legacy meaning stays | superseded by KDBD |
| [0012](0012-fit-resize-for-rtmo.md) | `fit` resize for RTMO; `pad_value` is required | absorbed into [`pre/resize-fit.md#behaviour`](../pre/resize-fit.md#behaviour) |
| [0010](0010-family-invariant.md) | Family invariant: a size sets only its shape, target size and artifacts | absorbed into [`common/sizes-and-artifacts.md#sizes`](../common/sizes-and-artifacts.md#sizes) |
| [0008](0008-vnext-scope.md) | `vNEXT` scope, and the features considered and not added | superseded by YNX0 |

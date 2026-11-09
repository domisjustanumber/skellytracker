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
| [SE3Y](entries/SE3Y-license-and-training-data.md) | New draft section `common.license`: mandatory model license and training data, SPDX ids, `unknown` with a reason; examples `needs-export` | accepted |
| [50BW](entries/50BW-verification-batches.md) | Spec change: the verification batches of `static-batch-v1` are 1, 2, 3 and 6, not 1, 2, 3 and 4 (guidance only) | accepted |
| [1VMX](entries/1VMX-nms-key-exclusion.md) | Spec change: the NMS reference refuses the keys of `V-post.det.selection.nms-1` | accepted |
| [3S5G](entries/3S5G-affine-crop-matrix.md) | Spec change: the warp matrix `M` of `affine_person_crop` in the float32 steps of mmpose | accepted |
| [03PH](entries/03PH-simcc-score-rule.md) | Spec change: the 2D SimCC score is the smaller raw peak | accepted |
| [XH1J](entries/XH1J-normalize-input-dtype.md) | Spec change: each normalization casts to `input.dtype`; no `int8` input | accepted |

### Proposed

These entries are spec change proposals that wait for a decision of the user. Section is the spec
section of the change, or `none` when the change has no one section. Find the pending
proposals of a section here.

| # | Decision | Section | Status |
|---|----------|---------|--------|
| [52NQ](entries/52NQ-model-id-suffix.md) | Spec change: keypoint detector id `{family}-{group}[-{variant}]` | `common.identity` | proposed |
| [1V57](entries/1V57-normalize-custom-defaults.md) | Spec change: an absent `custom` key defaults to identity; YOLOX takes raw pixels | `pre.normalize` | proposed |

The entries that are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done` are in [historical.md](historical.md).

## Open work

The open work of the sidecar spec and the spec defects are in [open-work.md](open-work.md).

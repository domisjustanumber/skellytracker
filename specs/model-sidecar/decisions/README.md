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
| [Q6W6](entries/Q6W6-strict-score-comparisons.md) | Keep strict `>` in each score comparison of the detection decode, by intent; guidance names the `>=` upstreams | accepted |
| [G79P](entries/G79P-pixel-centres-per-resize-method.md) | Pixel centres follow the OpenCV call of the resize method: `cv2.resize` for `letterbox` and `stretch`, `cv2.warpAffine` for `fit` and `affine_person_crop` | accepted |
| [PHJ3](entries/PHJ3-resize-compute-dtype.md) | New optional `input.resize.compute_dtype`: `uint8` (default) or `float32`; the dtype of the resize and the pad; `V-pre.resize.interpolation-1` | accepted |
| [SE3Y](entries/SE3Y-license-and-training-data.md) | New draft section `common.license`: mandatory model license and training data, SPDX ids, `unknown` with a reason; examples `needs-export` | accepted |

### Proposed

These entries are spec change proposals that wait for a decision of the user. Section is the spec
section of the change, or `none` when the change has no one section. Find the pending
proposals of a section here.

| # | Decision | Section | Status |
|---|----------|---------|--------|
| [3S5G](entries/3S5G-affine-crop-matrix.md) | Spec change: the warp matrix `M` of `affine_person_crop` in the float32 steps of mmpose | `pre.resize.affine_person_crop` | proposed |
| [50BW](entries/50BW-verification-batches.md) | Spec change: the verification batches of `static-batch-v1` are 1, 2, 3 and 6, not 1, 2, 3 and 4 (guidance only) | `common.batch_conversion` | proposed |
| [52NQ](entries/52NQ-model-id-suffix.md) | Spec change: keypoint detector id `{family}-{group}[-{variant}]` | `common.identity` | proposed |
| [03PH](entries/03PH-simcc-score-rule.md) | Spec change: the 2D SimCC score is the smaller raw peak | `post.pose.decode.simcc` | proposed |

The entries that are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done` are in [historical.md](historical.md).

## Open work

The open work of the sidecar spec and the spec defects are in [open-work.md](open-work.md).

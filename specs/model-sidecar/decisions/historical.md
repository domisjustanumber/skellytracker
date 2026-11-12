# Decision log of the sidecar spec: historical entries

These entries are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done`. They are not in the read path. Read an entry here only to find
the reason for a decision. The [index](README.md) has the Active and Proposed entries. The
[Rules](../../../decisions/README.md#rules) are in the root log.

### Historical

| # | Decision | Status |
|---|----------|--------|
| [0009](entries/0009-imagenet-bgr-meaning.md) | `imagenet_bgr` changes meaning at `vNEXT`; the legacy meaning stays | superseded by KDBD |
| [0012](entries/0012-fit-resize-for-rtmo.md) | `fit` resize for RTMO; `pad_value` is required | superseded by 0QKK |
| [0010](entries/0010-family-invariant.md) | Family invariant: a size sets only its shape, target size and artifacts | superseded by 90CE |
| [0008](entries/0008-vnext-scope.md) | `vNEXT` scope, and the features considered and not added | superseded by YNX0 |
| [0011](entries/0011-rtmdet-host-nms.md) | RTMDet: NMS-free graph with host `selection: nms`; no `pre_nms_top_k` | superseded by JAA4 |
| [CRV0](entries/CRV0-output-shapes-in-each-batch-group.md) | `vNEXT`: `output_shapes` in each batch group, one entry for each output; a symbolic axis stays `-1`; legacy keeps the old rule | superseded by JAA4 |
| [YNX0](entries/YNX0-vnext-scope-list.md) | `vNEXT` scope: one list in the changelog; acceptance or a `describes` landing adds a model; a proposal gives `vNEXT` text only | superseded by SS2E |
| [Q6W6](entries/Q6W6-strict-score-comparisons.md) | Keep strict `>` in each score comparison of the detection decode, by intent; guidance names the `>=` upstreams | absorbed into [`post/detection-decode.md#selection-behaviour`](../post/object/decode.md#selection-behaviour) |
| [G79P](entries/G79P-pixel-centres-per-resize-method.md) | Pixel centres follow the OpenCV call of the resize method: `cv2.resize` for `letterbox` and `stretch`, `cv2.warpAffine` for `fit` and `affine_person_crop` | absorbed into [`pre/interpolation.md#pixel-centres`](../pre/interpolation.md#pixel-centres) |
| [PHJ3](entries/PHJ3-resize-compute-dtype.md) | New optional `input.resize.compute_dtype`: `uint8` (default) or `float32`; the dtype of the resize and the pad; `V-pre.resize.interpolation-1` | absorbed into [`pre/interpolation.md#compute-dtype`](../pre/interpolation.md#compute-dtype) |
| [3S5G](entries/3S5G-affine-crop-matrix.md) | Spec change: the warp matrix `M` of `affine_person_crop` in the float32 steps of mmpose | absorbed into [`pre/resize-affine-person-crop.md#behaviour`](../pre/resize-affine-crop.md#behaviour) |
| [03PH](entries/03PH-simcc-score-rule.md) | Spec change: the 2D SimCC score is the smaller raw peak | absorbed into [`post/pose-decode-simcc.md#behaviour`](../post/keypoint/decode-simcc.md#behaviour) |
| [XH1J](entries/XH1J-normalize-input-dtype.md) | Spec change: each normalization casts to `input.dtype`; no `int8` input | absorbed into [`pre/normalization.md#behaviour`](../pre/normalization.md#behaviour) |
| [1V57](entries/1V57-normalize-custom-defaults.md) | Spec change: an absent `custom` key defaults to identity; YOLOX takes raw pixels | absorbed into [`pre/normalization.md#behaviour`](../pre/normalization.md#behaviour) |
| [SE3Y](entries/SE3Y-license-and-training-data.md) | New draft section `common.license`: mandatory model license and training data, SPDX ids, `unknown` with a reason; examples `needs-export` | superseded by NBG2 |
| [50BW](entries/50BW-verification-batches.md) | Spec change: the verification batches of `static-batch-v1` are 1, 2, 3 and 6, not 1, 2, 3 and 4 (guidance only) | absorbed into [`common/batch-conversion.md#authoring-guidance`](../common/batch-conversion.md#authoring-guidance) |
| [1VMX](entries/1VMX-nms-key-exclusion.md) | Spec change: the NMS reference refuses the keys of `V-post.det.selection.nms-1` | absorbed into [`post/selection-nms.md#validation-rules`](../post/object/selection-nms.md#validation-rules) |
| [52NQ](entries/52NQ-model-id-suffix.md) | Spec change: keypoint detector id `{family}-{group}[-{variant}]` | absorbed into [`common/identity.md#keypoint-detector-id`](../common/identity.md#keypoint-detector-id) |
| [1BS2](entries/1BS2-distillation-teacher-is-a-start-checkpoint.md) | `common.license`: the datasets of a distillation teacher count, with `use: pretraining` | absorbed into [`common/license.md#fields`](../common/license.md#fields) |
| [KZ9J](entries/KZ9J-model-id-suffix-rtmo-removed.md) | Spec change: follow-up of 52NQ; the example `rtmo-body7` is removed, not rebuilt | done |
| [NBG2](entries/NBG2-license-and-training-data-without-the-deferred-examples.md) | New draft section `common.license`; RTMW rebuild replaces its example, three deferred examples go; supersedes SE3Y | absorbed into [`license.md#fields`](../common/license.md#fields), [`license.md#behaviour`](../common/license.md#behaviour), [`license.md#validation-rules`](../common/license.md#validation-rules), [`license.md#implementer-guidance`](../common/license.md#implementer-guidance), [`model-sidecar/README.md#section-status`](../README.md#section-status) |
| [R6J9](entries/R6J9-test-time-steps-and-unreachable-branches.md) | `out of scope` covers a test-time augmentation and an undeclared extra decode value; parity needs no image for an unreachable branch | absorbed into [`phase-1-intake.md#verdicts`](../model-addition-workflow/phase-1-intake.md#verdicts), [`parity.md#parity`](../model-addition-workflow/parity.md#parity) |

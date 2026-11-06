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
| [Q6W6](entries/Q6W6-strict-score-comparisons.md) | Keep strict `>` in each score comparison of the detection decode, by intent; guidance names the `>=` upstreams | absorbed into [`post/detection-decode.md#selection-behaviour`](../post/detection-decode.md#selection-behaviour) |
| [G79P](entries/G79P-pixel-centres-per-resize-method.md) | Pixel centres follow the OpenCV call of the resize method: `cv2.resize` for `letterbox` and `stretch`, `cv2.warpAffine` for `fit` and `affine_person_crop` | absorbed into [`pre/interpolation.md#pixel-centres`](../pre/interpolation.md#pixel-centres) |
| [PHJ3](entries/PHJ3-resize-compute-dtype.md) | New optional `input.resize.compute_dtype`: `uint8` (default) or `float32`; the dtype of the resize and the pad; `V-pre.resize.interpolation-1` | absorbed into [`pre/interpolation.md#compute-dtype`](../pre/interpolation.md#compute-dtype) |

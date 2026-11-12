# Change proposal: affine-crop-matrix

This file uses ASD-STE100 Simplified Technical English.

## Header

| Field | Value |
|---|---|
| Title | The float32 warp matrix `M` of the affine person crop |
| Slug | `affine-crop-matrix` |
| Date | 2026-11-06 |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `ecee56e1ea1b4d3901c76a73b713ed0256675e78` |
| Model, and its `model` bundle ID | `rtmw-wholebody133`, `model-rtmw-wholebody133@openmmlab-exporter` |
| Intake rows with the verdict `near-miss` or `gap` | T4b (arithmetic of the crop), `near-miss` |
| Kind (`new section`, `changed section`, `contribution` or `follow-up`) | `changed section` |
| Base bundle of a follow-up (`base`, or `none`) | none |
| Proposed section ID (the `id` in the section file's front matter) | `pre.resize.affine_person_crop` |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | `specs/model-sidecar/pre/resize-affine-person-crop.md` |
| Depends on (`depends_on`: bundle IDs that must land first, or `none`) | none |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | skellytracker ADR-3S5G only. It is the entry of version 1 of this proposal. The user accepted the proposal on 2026-11-06. The entry keeps the status `proposed` until the proposal lands. The other entries of the Proposed table of the spec log do not cover this property: skellytracker ADR-52NQ (`common.identity`), skellytracker ADR-03PH (`post.pose.decode.simcc`) and skellytracker ADR-XH1J (`pre.normalize`). The Proposed table of the root log is empty. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `8fed6f34eb22643e0b6cc38a7c6b80014bfe1d75` |
| Target spec version: the newest version heading under "Revisions" in `specs/model-sidecar/changelog.md`, today the open target `2.0.0`. `pack` writes it to the manifest as `spec_version`. | `2.0.0` |

## 1. Gap

| Item | Value |
|---|---|
| Property | The arithmetic of the warp matrix `M` of the top-down person crop of mmpose v1.3.2: (1) the box, the centre and the crop size are float32, and each operation rounds to float32; (2) the order: expand, then fix the aspect ratio with `a = f32(T_w / T_h)`. The branch `w = h * a` changes `w`, and thus `M`. The branch `h = w / a` and the strict `>` set only `crop_h` (the crop height that mmpose returns as `input_scale`), not `M`; (3) `M` comes from three float32 point pairs. The second point is left of the centre, and the third point comes from a 90-degree turn of the first two. Thus, with `maintain_aspect_ratio: true`, `M` uses `c` and `w` only, not `h`. The proposal does not change the normalization, the Inverse or the unprojection. |
| Upstream evidence (file and line, or config key; full upstream SHA, then the tag) | mmpose `5408bc76f5b848cf925a0d1857899011d8c5b497` (tag `v1.3.2`). (1) `bbox_xyxy2cs`: [`mmpose/structures/bbox/transforms.py:66-67`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L66-L67) (`scale = (bbox[..., 2:] - bbox[..., :2]) * padding`, `center = (bbox[..., 2:] + bbox[..., :2]) * 0.5`, in the dtype of the box); `GetBBoxCenterScale`: [`mmpose/datasets/transforms/common_transforms.py:52`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/common_transforms.py#L52), [`:76-80`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/common_transforms.py#L76-L80) (`padding=1.25`). (2) `TopdownAffine._fix_aspect_ratio`: [`mmpose/datasets/transforms/topdown_transforms.py:67-70`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/topdown_transforms.py#L67-L70) (`np.where(w > h * aspect_ratio, [w, w / aspect_ratio], [h * aspect_ratio, h])`), [`:85-90`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/topdown_transforms.py#L85-L90) (`aspect_ratio=w / h` of `input_size`, a Python float), [`:107-118`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/topdown_transforms.py#L107-L118) (`get_warp_matrix`, then `cv2.warpAffine(..., flags=cv2.INTER_LINEAR)`). (3) `get_warp_matrix`: [`mmpose/structures/bbox/transforms.py:406-435`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L406-L435) (`src_dir = [src_w * -0.5, 0.]`; `src` and `dst` are float32 arrays; `src[1] = center + src_dir`; the third points from `_get_3rd_point` when `fix_aspect_ratio=True`; the `fix_aspect_ratio=False` branch uses `src_h`; `cv2.getAffineTransform(np.float32(src), np.float32(dst))`), `_get_3rd_point`: [`:509-525`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L509-L525). The box dtype: `inference_topdown` keeps the dtype of the boxes of the caller ([`mmpose/apis/inference.py:160-176`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/apis/inference.py#L160-L176)). The upstream dumps of part 5 give float32 boxes. |
| Plan decisions about the spec that this proposal uses, in words (or `none`) (heading "User decisions" in `specs/model-sidecar/model-addition-workflow/rules.md`) | The user decided on 2026-11-06 that row T4b of the RTMW intake is a `near-miss`, because the float32 matrix changes the crop by 1 grey level on most COCO boxes. The user decided on 2026-11-06 that the proposal covers only the crop matrix. The user decided on 2026-11-06 that the rows T10 (normalization) and D11 (unprojection) are `exact`, because they differ only by float32 rounding of a result (skellytracker ADR-PHJ3). ([OpenMMLab-Exporter ADR-W2Y4](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/W2Y4-intake-rulings-yolox-rtmw.md)) |
| Nearest section ID (the `id` in the section file's front matter) | `pre.resize.affine_person_crop` |
| Why the nearest section is wrong | The pseudocode of Behaviour is exact math. It gives no dtype. Its aspect fix multiplies, `h = w * (T_h / T_w)`. It defines `M` as "the affine map taking the (w, h) box around center onto [0, T_w] x [0, T_h]", so its `M` uses `h`. mmpose rounds each step to float32, divides by `a`, and makes `M` from three float32 points that use only `w`. The sentence "This matches mmpose `GetBBoxCenterScale(padding=1.25)` + `TopdownAffine`" is true in exact math only. A detail that the spec does not define, and that changes the output for some input, is a `near-miss` ("Verdicts" in `specs/model-sidecar/model-addition-workflow/phase-1-intake.md`). The spec log lists "the arithmetic precision of the geometry and of the pixel math" as a fact that the spec does not state ("Spec defects" in `specs/model-sidecar/decisions/open-work.md`). |
| Measured difference (number, image and script) | Primary: the gated run of part 5, [OpenMMLab-Exporter ADR-6A8S](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/6A8S-affine-crop-matrix-evidence.md). Script [`decisions/scripts/affine_crop_matrix_check.py`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/0d07c982fb6915fee6fa0b8ccac35873c77c4db2/decisions/scripts/affine_crop_matrix_check.py) at `0d07c982fb6915fee6fa0b8ccac35873c77c4db2`, host CPU (NumPy 2.5.4, OpenCV 5.0.0). Data: the upstream dumps of mmpose v1.3.2 of the [OpenMMLab-Exporter ADR-VB67](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/VB67-simcc-score-rule-bundle-rerun.md) run: 6 runs (RTMW m and x-384, RTMPose Halpe26 m-256 and m-384, DWPose m and l-384) with 6370 persons each (6352 COCO val2017 persons and 18 synthetic boxes). (1) The `M`, the centre and the crop size of the reference file of part 3 equal the upstream values bit for bit for 38220 of 38220 persons (G1). (2) The exact-math `M` of the current text (OpenMMLab-Exporter `onnx_runtime/preprocess.py::affine_crop_geometry`) differs from the upstream `M` by more than 1e-6 for 6226 of 6370 persons at 256x192 and for 6245 of 6370 persons at 384x288. The maximum is 2.4e-3 at 256x192 and 3.6e-3 at 384x288 (G2). That is more than the vector tolerance 1e-4 of the section. (3) On the host OpenCV 5.0.0, the crop with the exact-math `M` differs from the crop with the upstream `M` in 5992 of 6370 crops at 256x192 and in 6047 of 6370 crops at 384x288, by 1 grey level at most (G3). In the 318 persons of the committed box set `decisions/scripts/pose_parity_boxes.json`, 292 (256x192) and 293 (384x288) crops differ. (4) Secondary (an uncommitted check of this draft, NumPy 2.5.4; not a gate of part 5): the skellytracker `get_warp_matrix` (second point above the centre) differs from the `M` of part 3 on 317 of 318 boxes of the box set at 256x192 with a float32 box (max 1.0e-3). It also differs on 317 of 318 when the float32 box is cast to float64 first (max 3.5e-3). `evidence.md` gives the files. Historic note: row T4b of the RTMW intake first cited a deleted scratch check (up to 3e-3, and 1 grey level on 289 of 318 boxes). Items (2) and (3) replace those numbers. |
| Model in "Scope of this revision" (`specs/model-sidecar/changelog.md`): yes, or no (it joins the list on acceptance; do not write a scope entry) | yes (OpenMMLab-Exporter: RTMW) |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none. The row `crop_policy.border_mode`, rotated crops is about other features. This proposal adds no field, no border mode and no rotation. |

**Primary evidence.** The gated run of part 5 (OpenMMLab-Exporter ADR-6A8S). Only item (4) is
secondary. It supports only the alternative "The skellytracker form" of part 8.

## 2. Spec change

The relative links of the proposed text resolve from the record path
`specs/model-sidecar/proposals/<slug>/`. At landing, the session changes them to the path of the
section file (an editorial fix).

### 2.1 Sections

Changed section `pre.resize.affine_person_crop`, title "Affine person crop", file
`specs/model-sidecar/pre/resize-affine-person-crop.md`. The section ID, the title, the kind, the
selectors and the fields do not change. No section-map row changes.

Front matter: the comment of `implemented_by.forward` gets this sentence at its end: "The arithmetic
of `M` is not met: the box keeps the dtype of the caller, and the second warp point is above the
centre (the rtmlib form)." The other keys do not change.

**Places that the change edits.**

| Place | Heading | Edit |
|---|---|---|
| `pre.resize.affine_person_crop` | front matter | The comment of `implemented_by.forward` (above). |
| `pre.resize.affine_person_crop` | Behaviour | Replace the text from "The rotation of the warp is always `0`." to the sentence "This matches mmpose `GetBBoxCenterScale(padding=1.25)` + `TopdownAffine`." with the text of 2.3. The heading "Inverse" and its table stay. |
| `pre.resize.affine_person_crop` | Inverse | No edit. "Apply the inverse of the affine warp `M`" now names the `M` of 2.3. |
| `pre.resize.affine_person_crop` | Implementer guidance | Add the bullets of 2.3, "Guidance", at the end. |
| `pre.resize.affine_person_crop` | Fields, Validation rules, Authoring guidance | No edit. |
| `specs/model-sidecar/changelog.md` | Summary of changes | The row of 2.6. |
| `specs/model-sidecar/decisions/open-work.md` | Spec defects, the item "The spec does not state these facts, but a host needs them", the sub-item "the arithmetic precision of the geometry and of the pixel math" | The content commit changes the start of the sub-item to "the arithmetic precision of the geometry (except the warp matrix `M` of `affine_person_crop`) and of the pixel math". The rest of the sub-item stays. |
| `specs/model-sidecar/decisions/open-work.md` | Spec defects, the item "The test vectors found these points that the spec does not define", the sub-item "the box format and the coordinate space of the person box that `affine_person_crop` warps" | No edit. The sub-item stays. The proposal covers only the arithmetic of the crop matrix `M` (the user ruling of 2026-11-06). The box format and the coordinate space of the box that a host gives to the crop are a different property: a contract between the detector output and the crop. Thus they are outside the scope of this proposal, and a separate decision must close the sub-item. The steps use the xyxy names of the current vector file as the input of the float32 steps. They do not state the coordinate space of the box, or which detector box the host gives to the crop. Thus the sub-item stays. An earlier draft of this proposal removed the sub-item. This version keeps it. |
| `specs/model-sidecar/vectors/pre.resize.affine_person_crop.yaml` | existing file | `land` adds the 9 cases of part 4 at the end. It replaces no case. `land` keeps the file keys of the current file, so the landing session also adds the last note of the part 4 file to `notes`. The current `unverified` text says that only some cases list their implementations in `verified_against`. `land` keeps that text. It stays true, because the 9 new cases list no implementation. |
| `tools/vector_formulas/pre_resize_affine_person_crop.py` | `run`, `inverse` | The formula module must read the new text: the float32 steps and `M` from the three points. Keep `border` and `CHECKS`. Else the cross-check of `land` fails on the 7 new forward cases (their `compare` has `atol` 1e-6): a scratch run of `land` with the current formulas stopped at `coco-tall-box-float32-steps`. The same scratch run, with `run` and `inverse` of the formulas from the new text, found no problems and wrote 29 cases. |
| `specs/model-sidecar/reference/pre_resize_affine_person_crop.py` | new file | The file of part 3. |
| `specs/model-sidecar/reference/post_unprojection.py` | the fixture `affine_person_crop_inverse` and the fixture values `DEFAULT_EXPAND_RATIO` and `DEFAULT_MAINTAIN_ASPECT_RATIO` | The fixtures implement the current exact-math Inverse. When the file of part 3 lands, skellytracker replaces them with an import of `pre_resize_affine_person_crop` and a call ("When the other section has no module" in `specs/model-sidecar/model-addition-workflow/reference-implementations.md`: a fixture is temporary). The affine cases of `post.unprojection.yaml` keep their values (next row). |
| `specs/model-sidecar/vectors/post.unprojection.yaml` | cases `pixel-affine-person-crop` and `normalized-11-affine-person-crop` | No value changes. Their box values are exact in float32, and the reference of part 3 gives `source_xy` `[148, 264]`. |
| `specs/model-sidecar/TRACEABILITY.md` | generated | Run the generator after the content commit. |
| `pre.resize.interpolation`, `post.unprojection`, `common.input`, `pre.normalize` | all headings | No edit. The proposal does not change the pixel centres, `compute_dtype`, the scalar `pad_value`, the unprojection or the normalization. |

### 2.2 Fields table

No change.

### 2.3 Behaviour

Replace the text of Behaviour before the heading "Inverse" with this text:

````text
The rotation of the warp is always `0`. Rotated crops are out of scope. The steps write the person box as `bbox_xyxy = [x1, y1, x2, y2]`. The normative warp is:

```text
# float32: each value is float32, and the host rounds the result of each operation to float32
x1, y1, x2, y2 = f32(bbox_xyxy)
e   = f32(expand_ratio)
c_x = (x1 + x2) * 0.5
c_y = (y1 + y2) * 0.5
w   = (x2 - x1) * e
h   = (y2 - y1) * e
if maintain_aspect_ratio:
    a = f32(T_w / T_h)
    if w > h * a: h = w / a
    else:         w = h * a

# three point pairs, float32: P in source pixels, Q in model-input pixels
P0 = (c_x, c_y)                          Q0 = (T_w / 2, T_h / 2)
P1 = (c_x - w * 0.5, c_y)                Q1 = (0, T_h / 2)
if maintain_aspect_ratio:
    P2 = (P1.x, P1.y + (P0.x - P1.x))    Q2 = (0, T_h / 2 + T_w / 2)
else:
    P2 = (c_x, c_y - h * 0.5)            Q2 = (T_w / 2, 0)

M        = the affine map that takes P0, P1, P2 onto Q0, Q1, Q2, solved in float64
pad      = crop_policy.pad_value
border   = [pad] * 3 if pad is a scalar else pad
dst      = warpAffine(src, M, (T_w, T_h), <interpolation>, borderMode=constant, borderValue=border)
```

- `f32(v)` rounds one value to float32 (IEEE 754 binary32, round to nearest, ties to even). `T_w / T_h` is a float64 division of the two integers, then one rounding.
- `w > h * a` is a strict comparison of two float32 values. When `w` equals `h * a`, `h` does not change.
- With `maintain_aspect_ratio: true`, `M` uses `c` and `w` only, not `h`. The branch `h = w / a` and the strict `>` set only `h`: the crop height that mmpose returns as `input_scale`. The y scale of `M` comes from the float32 points. It can differ from the x scale and from `T_h / h`. Do not make `M` from `T_w / w` and `T_h / h`.
- `cv2.getAffineTransform(src, dst)` with the float32 arrays `src = [P0, P1, P2]` and `dst = [Q0, Q1, Q2]` gives `M`.

`warpAffine` is `cv2.warpAffine`. Its pixel centres are at integer coordinates ([Pixel centres](../../pre/interpolation.md#pixel-centres)). For a float32 box and `maintain_aspect_ratio: true`, `M` is the matrix of mmpose `GetBBoxCenterScale(padding=expand_ratio)` + `TopdownAffine`.
````

**Guidance** (new bullets at the end of Implementer guidance):

- For a float32 box and `maintain_aspect_ratio: true`, the float32 steps of Behaviour give the `M` of
  mmpose v1.3.2 bit for bit with `cv2.getAffineTransform`. Another float64 solver can differ in the
  last bits. On 6370 persons (6352 COCO val2017 persons and 18 synthetic boxes), the exact-math `M`
  differed from the mmpose `M` by more than 1e-6 for 6226 persons at 256x192 and for 6245 persons at
  384x288. The maximum was 2.4e-3 and 3.6e-3. On OpenCV 5.0.0, 5992 crops (256x192) and 6047 crops
  (384x288) of the 6370 differed, by 1 grey level at most.
  (OpenMMLab-Exporter [`decisions/scripts/affine_crop_matrix_check.py`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/0d07c982fb6915fee6fa0b8ccac35873c77c4db2/decisions/scripts/affine_crop_matrix_check.py)
  at `0d07c982fb6915fee6fa0b8ccac35873c77c4db2`, gates G2 and G3;
  [OpenMMLab-Exporter ADR-6A8S](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/6A8S-affine-crop-matrix-evidence.md); mmpose
  [`mmpose/structures/bbox/transforms.py:66-67`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L66-L67),
  [`mmpose/structures/bbox/transforms.py:406-435`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L406-L435),
  [`mmpose/datasets/transforms/topdown_transforms.py:67-70`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/topdown_transforms.py#L67-L70)
  and [`mmpose/datasets/transforms/topdown_transforms.py:85-118`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/topdown_transforms.py#L85-L118))
- mmpose computes `P1.x` as `c_x + (-0.5 * w)` in float64 (NumPy 1.24.4 in the exporter image) and
  stores the result in a float32 array. The float64 result, rounded to float32, always equals the
  float32 operation of Behaviour (double rounding from binary64 to binary32 is exact for `+` and
  `-`). The same holds for `P2.y` of the branch with `maintain_aspect_ratio: false`. mmpose
  `inference_topdown` keeps the dtype of the boxes of the caller. A float64 box gives a float64
  centre and crop size; the warp points still round to float32. For a parity run, give mmpose
  float32 boxes. (mmpose
  [`mmpose/structures/bbox/transforms.py:411-416`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L411-L416)
  and [`mmpose/apis/inference.py:169-170`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/apis/inference.py#L169-L170))
- The vectors compare `M`, not crop pixels. OpenCV 4.5.4 and 5.0.0 warp one `M` to different
  pixels: 0 of 6370 crops equal on each of 6 runs, up to 7 grey levels.
  (OpenMMLab-Exporter `decisions/scripts/affine_crop_matrix_check.py`, record R1;
  [OpenMMLab-Exporter ADR-6A8S](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/6A8S-affine-crop-matrix-evidence.md);
  [OpenMMLab-Exporter ADR-0053](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/0053-pose-sidecar-parity-runs.md)
  found 0 of 318 crops equal, up to 6 grey levels)
- mmpose maps the keypoints back with a closed form of the float32 centre and crop size, not with the
  inverse of `M`. The two differ by float32 rounding only: 9.6e-5 px at most on 6 runs.
  (OpenMMLab-Exporter `decisions/scripts/affine_crop_matrix_check.py`, record R2;
  [OpenMMLab-Exporter ADR-6A8S](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/6A8S-affine-crop-matrix-evidence.md); mmpose
  [`mmpose/models/pose_estimators/topdown.py:150-156`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/models/pose_estimators/topdown.py#L150-L156))

The change does not edit the Inverse. The Inverse is the inverse of the `M` of Behaviour.

### 2.4 Validation rules

No new rule. No existing rule names a value that the change adds or changes:

- `V-pre.resize.affine_person_crop-1` (`expand_ratio`, `maintain_aspect_ratio`): unchanged.
- `V-pre.resize.affine_person_crop-2` (`requires_object_detector`): unchanged.
- `V-pre.resize.affine_person_crop-3` (`target_size`; no `pad_value`, `pad_position` or `rounding`):
  unchanged.

### 2.5 Selectors

No change: `input.resize.method=affine_person_crop`.

### 2.6 Changelog row

| # | Area | Change | Driven by | Section |
|---|------|--------|-----------|---------|
| (next) | Resize | `affine_person_crop` gives the steps of its warp matrix `M` in float32: the box rounds to float32; the centre, the crop size and the aspect fix with `a = f32(T_w / T_h)` are float32; `M` comes from three float32 point pairs that use `c` and `w` only. The branch `h = w / a` and the strict `>` set only the crop height (mmpose `input_scale`), not `M`. The Inverse stays the inverse of `M`. | RTMW (mmpose `TopdownAffine`) | [Affine person crop](../../pre/resize-affine-person-crop.md#behaviour) |

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the proposal bundle (`reference/<section_module>.py`) | `reference/pre_resize_affine_person_crop.py` |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | `specs/model-sidecar/reference/pre_resize_affine_person_crop.py` (new file) |
| Functions (one for each algorithm) | `crop_size` (the float32 centre and crop size), `warp_points` (the three point pairs), `warp_matrix` (`M`), `policy_values`, `crop_geometry`, `border_value` (the scalar or per-channel border), `warp_image` (the warp), `affine_person_crop` (the full forward step), `unproject` (the Inverse), `check_rules` (rules -1, -2 and -3); `run`, `inverse` and `border` for the cases |

The section has no reference implementation yet. Thus the file implements the full section as
changed: the forward step, the Inverse and every value ("Full section" in
`specs/model-sidecar/model-addition-workflow/reference-implementations.md`). It imports no other
section. It holds two fixtures of `pre.resize.interpolation` (`INTERPOLATION_FLAGS` and
`COMPUTE_DTYPES`), because that section has no reference module. `source commit: none (no host
code)`: the exporter host implements the current text, not the proposed text. `check_rules` gives
the expected result of the 5 data-only validator cases of the current vector file (a scratch run).
`reference_problems` of skellytracker `tools/intake_bundle.py` (at `8fed6f34`) finds no problem in
the file. `crop_size` refuses a box that gives an empty crop with `ValueError`. The text has no such
rule (part 8). Version 2 of the file changes only two notes of its module docstring: the decision
entry (skellytracker ADR-3S5G) and the parity result (`pass`, part 5). The code is the same as in the
file of the run of part 5. Part 5 gives the two SHA-256 values and the proof.

## 4. Vectors

| Item | Value |
|---|---|
| Vector file in the proposal bundle | `vectors/pre.resize.affine_person_crop.yaml` |
| Target file in skellytracker | `specs/model-sidecar/vectors/pre.resize.affine_person_crop.yaml` (existing file) |
| `verified_against` | `unverified`: no host code implements the proposed text. The OpenMMLab-Exporter host implements the current text. |
| Replaced case ids (`--replaces`) | none |

The file starts from the file keys of the current vector file. It holds only the 9 new cases:
`coco-tall-box-float32-steps` and its Inverse (the `else` branch, `w = h * a`),
`coco-wide-box-float32-steps` (the branch `h = w / a`), `coco-box-target-384x288-float32-steps`,
`aspect-fix-divides-by-a` (`a = f32(256 / 384)` is not exact; `w / a` differs from
`w * (T_h / T_w)`), `aspect-fix-tie-keeps-h` (the strict `>` at a float32 tie; exact math takes the
other branch), `aspect-ratio-not-kept-float32-steps` and its Inverse (`maintain_aspect_ratio:
false`), and `expand-ratio-rounds-to-float32` (`expand_ratio: 1.1`). The COCO boxes are decimal
values, so each of these cases also tests the float32 rounding of the box.

- Each forward case has `compare` `atol` 1e-6 for `center`, `crop_w`, `crop_h` and `matrix`. At
  least one value of each such case differs from the exact-math value by more than 1e-6 (in
  `aspect-fix-tie-keeps-h`, only `crop_h`), so the case separates the two texts. The Inverse cases
  keep the file tolerance 1e-4, because the Inverse text does not change, and the mmpose closed form
  differs from the inverse of `M` by float32 rounding only (2.3, Guidance).
- `fill` of skellytracker `tools/make_vectors.py` (at `8fed6f34`) wrote `expect` with the reference
  file of part 3 and found no problems. It changed no byte of the file of version 1.
- The 20 current cases keep their values. `fill` (at `8fed6f34`) on a scratch copy of the current
  file and the 9 new cases, with the reference file of part 3, changed only one value, inside the
  tolerance 1e-4: `crop_h` of `wide-box-grows-height`, 666.666667 to 666.666687. The 5 data-only
  cases do not run.
- The `M` of the three COCO cases equals the upstream `M` of the same persons in the mmpose v1.3.2
  dumps (gate G1 of part 5). An uncommitted case-level comparison gives the same result (a secondary
  note, `evidence.md`). The other cases come from the text only.
- The case `scalar-pad-fills-each-channel` of the current file covers the scalar `pad_value` on a
  3-channel input. The proposal does not change it.

## 5. Parity evidence

The result is `pass` on each of the 6 runs
([OpenMMLab-Exporter ADR-6A8S](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/6A8S-affine-crop-matrix-evidence.md)).
The run used existing upstream dumps of the OpenMMLab-Exporter ADR-VB67 run, so it needed no
container. The script wrote the gates below to `gates.json` at 2026-11-06T19:44:54Z, before the
measurement, with the SHA-256 of version 1 of the reference file of part 3 (`62bd8750`). The
measurement started after that time. `evidence.md` gives the inputs, the values of each run and the
result files.

**Version 2.** The reference file of version 2 differs from the file of the run only in lines of
its module docstring. The run used the file with the SHA-256
`62bd8750eb82b0f8c5204900e646b6e412d1d6b9eda9a8f34baed9fbb5883219`. The file of version 2 has the
SHA-256 `dd06867f3e4aaea0d2a2a06dd4ea1556d95f6e3103aab722535dda8f37e8b302`. With the docstrings
removed, `ast.dump` gives the same result for the two files. Thus the code is the same, and the
result of OpenMMLab-Exporter ADR-6A8S applies to version 2. This version has no new run.

| Item | Value |
|---|---|
| Gates, set before the run, their source, and pass gate or control | Set in `gates.json` (SHA-256 `d54ac053`) at 2026-11-06T19:44:54Z, before the measurement. G0 branches: each aspect branch (`w > h * a`, label `h`, and its `else`, label `w`) runs on at least one person of each run (pass gate; parity rule "each branch of the changed algorithm must run"). G1 matrix: for each person, the `M` of the reference file equals the upstream `M` bit for bit (max abs difference 0), and its centre and crop size equal the upstream `input_center` and `input_scale` (pass gate; source: 2.3, "For a float32 box and `maintain_aspect_ratio: true`, `M` is the matrix of mmpose"). G2: the exact-math `M` of the current text (OpenMMLab-Exporter `onnx_runtime/preprocess.py::affine_crop_geometry`, the committed file at the script commit) differs from the upstream `M` by more than 1e-6 (the `compare` atol of part 4) for at least one person of each run; the count and the maximum are recorded (control: else the run cannot see the change; float64 noise alone does not count). G3: on the host OpenCV (`cv2.warpAffine`, linear, constant border 0), the crop with the exact-math `M` differs from the crop with the upstream `M` in at least one crop of each run; the count and the maximum grey-level difference are recorded (control; the near-miss of part 1). Records with no gate: R0, the exporter host crop (`onnx_runtime.preprocess.affine_person_crop`) against the warp with the exact-math `M`; R1, the host crop with the reference `M` against the container reference crop and the SHA-256 of the upstream crop (OpenCV 5.0.0 on the host, 4.5.4 in the container); R2, the inverse of each `M` (`cv2.invertAffineTransform`, float64) on the upstream crop-space keypoints against the upstream source keypoints; R3, the host crop with the reference `M` against the host crop with the upstream `M` (R3 cannot differ when G1 passes, because the same `M` goes to the same `cv2.warpAffine` call, so it is not a gate). |
| Test images (paths or dataset IDs), and the branch that each image runs | COCO val2017 person instances (2346 images, 6352 GT persons) and 18 synthetic boxes on COCO images, as in OpenMMLab-Exporter ADR-VB67: the box set `pose-parity-full.json` (SHA-256 `7a36a2ee`), box rule `f32_xyxy`. On each run, 1827 persons run the branch `h = w / a` (label `h`) and 4543 persons run the branch `w = h * a` (label `w`). Each result also gives the values for the 318 persons of the committed box set `decisions/scripts/pose_parity_boxes.json` (SHA-256 `b74c6aa0`): 110 in the branch `h` and 208 in the branch `w`. `maintain_aspect_ratio: false` has no upstream model (`TopdownAffine` always fixes the aspect ratio); the vectors cover it. All runs use `T_w / T_h = 0.75` (256x192 and 384x288), which is exact in float32. Thus no run tests the rounding `a = f32(T_w / T_h)` for a ratio that is not exact. That rounding comes from the code reading of `_fix_aspect_ratio` (a float32 array times a Python float gives a float32 loop in NumPy 1.24.4) and from the vector case `aspect-fix-divides-by-a` only. |
| Upstream reference: library, version, config and command | mmpose v1.3.2 (`5408bc76f5b848cf925a0d1857899011d8c5b497`), mmengine 0.10.3, torch 2.0.0, NumPy 1.24.4, OpenCV 4.5.4, in the published exporter image with the tag `df-dcab32049439` ([OpenMMLab-Exporter ADR-F5VE](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/F5VE-docker-image.md)); the upstream RTMW, RTMPose Halpe26 and DWPose configs; `GetBBoxCenterScale` and `TopdownAffine(use_udp=False)`; box rule `f32_xyxy`. The dumps of the ADR-VB67 run (`pose_parity_mmpose_worker.py`, `dump` subcommand, `--device cuda --threads 4`) hold the upstream `M`, centre and scale of each person, the container reference crop, the SHA-256 of the upstream crop and the keypoints. Each run file records that the installed mmpose files equal the clone at that commit. The check reads the dumps. It does not run mmpose again. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | Not measured by this check: the change does not touch the ONNX file or its input order. The ADR-VB67 run measured it on the same crops (part 5 of the proposal `simcc-score-rule`): RTMW-m 0.0229, RTMW-x-384 3.909 (TF32 on), max abs difference of `simcc_x` and `simcc_y`. |
| Preprocessed input: maximum absolute difference for each image | G1 (`M`): max abs difference 0 for 38220 of 38220 persons (6370 on each run); the centre and the crop size are equal for each person. R3: 0 crops differ on each run (max 0). R0: 0 crops differ on each run: the exporter host crop is the warp with the exact-math `M`. G3 (exact-math `M` against upstream `M`, host OpenCV): 5992 of 6370 crops differ at 256x192 and 6047 of 6370 at 384x288, max 1 grey level; in the 318-person box set, 292 and 293 crops. R1: the host crop with the reference `M` equals the container reference crop in 0 of 6370 crops of each run, max 7 grey levels (318-person box set: max 6), and its SHA-256 equals the SHA-256 of the upstream crop in 0 of 6370 crops. The `M` is the same (G1), so the OpenCV build (5.0.0 against 4.5.4) causes this difference. The ADR-VB67 run found the container reference crop equal to the upstream crop in 6370 of 6370 crops of each run. With the OpenCV cause removed (the container reference crop), the host tensor equals the upstream tensor bit for bit in 6370 of 6370 crops of each run, max abs difference 0 ([OpenMMLab-Exporter ADR-VB67](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/VB67-simcc-score-rule-bundle-rerun.md)). |
| Row count for each image: sidecar path and upstream | One crop for each box: 6370 on each side, each run. |
| Final outputs of each role (Parity, step 5): the compared output, metric and value | The keypoints in source pixels, R2: the max abs difference in px of the inverse of each `M` on the upstream `kpt_crop`, against the upstream `kpt_src`. With the reference `M`: 8.7e-5 (RTMW m), 9.5e-5 (RTMW x-384), 8.3e-5 (Halpe26 m-256), 8.0e-5 (Halpe26 m-384), 8.7e-5 (DWPose m), 8.1e-5 (DWPose l-384); thus below 9.6e-5 px on all runs. With the exact-math `M`: 7.3e-5 px at most. The points: 847210 on each RTMW and DWPose run, 165620 on each Halpe26 run. R2 checks the Inverse alone. The sidecar path end to end with the same `M` (G1; the [OpenMMLab-Exporter ADR-VB67](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/VB67-simcc-score-rule-bundle-rerun.md) run, whose reference `M` equals the upstream `M` for 6370 of 6370 persons): body OKS AP, host on the reference crop against upstream, at most 7.9e-4 on each run (RTMW m-256 0.74769 against 0.74766, RTMW x-384 0.79523 against 0.79530). The change does not change the decode. |
| Result (`pass`, `fail` or `to run`) | `pass`: G0, G1, G2 and G3 pass on each of the 6 runs (`summary.json`, `result: pass`). |
| Script path in the exporter repo | [`decisions/scripts/affine_crop_matrix_check.py`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/0d07c982fb6915fee6fa0b8ccac35873c77c4db2/decisions/scripts/affine_crop_matrix_check.py) (SHA-256 `87f07b9b`). It imports only committed exporter code (`onnx_runtime.preprocess`, `decisions/scripts/pose_parity_common.py`) and the reference file of part 3 by its path. Host only, CPU (Python 3.14.2, NumPy 2.5.4, OpenCV 5.0.0). The run recorded each repository file of the check as `committed`. |
| Exporter commit of the script | [`0d07c982fb6915fee6fa0b8ccac35873c77c4db2`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/0d07c982fb6915fee6fa0b8ccac35873c77c4db2) |
| Command | `uv run python decisions/scripts/affine_crop_matrix_check.py gates --out <work>/affine-crop-matrix --reference <payload>/reference/pre_resize_affine_person_crop.py`, then `uv run python decisions/scripts/affine_crop_matrix_check.py measure --out <work>/affine-crop-matrix --reference <payload>/reference/pre_resize_affine_person_crop.py --images <dump work>/images --runs <dump work>/runs/rtmw-wholebody133-m-full-noflip <dump work>/runs/rtmw-wholebody133-x-384-full-noflip <dump work>/runs/rtmpose-halpe26-m-256-full-noflip <dump work>/runs/rtmpose-halpe26-m-384-full-noflip <dump work>/runs/dwpose-wholebody133-ubody-m-full-noflip <dump work>/runs/dwpose-wholebody133-ubody-l-384-full-noflip` (`--boxset` keeps its default, the committed `decisions/scripts/pose_parity_boxes.json`). |

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | `skellytracker/core/detectors/processing/affine_crop.py`: `get_warp_matrix` must put the second point left of the centre (`src_dir = [src_w * -0.5, 0]`, `dst_dir = [dst_w * -0.5, 0]`), as mmpose does. `bbox_xyxy2cs` and `top_down_affine` compute in the dtype of the box. With a float32 box, the current aspect fix already rounds `a` to float32. `skellytracker/core/detectors/processing/image_preprocessing.py::preprocess_image`, the `affine_person_crop` branch: cast the box to float32 (also the full-frame box, now float64). Thus the changes are the float32 cast of the box and the second warp point left of the centre. The `maintain_aspect_ratio: false` branch (now `NotImplementedError`) is for the implementer. |
| Dispatch point | `preprocess_image` (`input.resize.method: affine_person_crop`). No new dispatch. |
| Validator changes (`model.py`, with rule IDs) | none |
| Tests (the vectors of part 4, and a golden parity test, for example in `skellytracker/tests/sidecar/`) | A test that runs the numeric cases of `vectors/pre.resize.affine_person_crop.yaml` through `bbox_xyxy2cs`, `top_down_affine` and `get_warp_matrix`. A golden test with the three COCO cases of part 4: their `M` is the mmpose `M`. |
| Existing code that the change touches | `skellytracker/core/detectors/processing/affine_crop.py` (`get_warp_matrix`, `bbox_xyxy2cs`, `top_down_affine`); `skellytracker/core/detectors/processing/image_preprocessing.py` (`preprocess_image`); the second copy in `skellytracker/core/detectors/keypoint_detectors/rtmpose/rtmpose_preprocessing.py` (`get_warp_matrix`, `bbox_xyxy2cs`, `top_down_affine`). The Inverse in `skellytracker/core/detectors/processing/simcc_decode.py::decode_simcc` (the closed form with the centre and the scale) needs no change: it differs from the inverse of `M` by float32 rounding only. |

## 7. Exporter impact

| Owner repo | Inventory key or model | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmw-wholebody133` | none. The sidecar has no new field. | Today the host crop [`onnx_runtime/preprocess.py`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/onnx_runtime/preprocess.py) (`affine_crop_geometry`, `AffineCropMeta.matrix`, `AffineCropMeta.inverse_matrix`) uses the exact-math `M` of the current text, not the float32 `M` of mmpose: its crop equals the warp with the exact-math `M` in each crop of the 6 runs (R0 of part 5: 0 of 6370 crops differ on each run). Thus its `M` differs from the mmpose `M` (G2 of part 5). When the proposal lands, the host crop must change to the float32 steps and the three points of 2.3. Until then it fails the 7 forward cases of part 4 at `atol` 1e-6. It passes the 2 Inverse cases at the file tolerance 1e-4. |
| OpenMMLab-Exporter | `rtmpose-halpe26`, `dwpose-wholebody133-ubody` (draft writers, no sidecar yet) | none | the same host crop as above |

**Reference examples that the change makes invalid.** none. The change adds no field and no rule.
The example `detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml` declares
`affine_person_crop`. It stays valid, and its crop now has the `M` of 2.3.

| Example (`inventory.yaml` key) | Rule ID | Impact (`forced-edit` or `needs-export`) | Edit text |
|---|---|---|---|
| none | none | none | none |

**Candidate example.**

| Item | Value |
|---|---|
| Candidate example in the proposal bundle (`example/detectors/...`, or `none`) | none |
| Writer code (file, function and commit) | none (the sidecar does not change) |
| `sidecar_refs.py --check` result | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| The near-miss: the exact-math text, with float32 rounding treated as no difference (as for rows T10 and D11). | The exact-math `M` differs from the mmpose `M` by up to 3.6e-3. That is more than the vector tolerance 1e-4 of the section and the case `atol` 1e-6. It is a different matrix, not a rounding of one result. On OpenCV 5.0.0, it also changes the crop pixels: 5992 or 6047 of 6370 crops of each run, by 1 grey level (G3). The user ruled T4b a `near-miss` on 2026-11-06. | Part 1; part 5 (OpenMMLab-Exporter ADR-6A8S); OpenMMLab-Exporter ADR-W2Y4 |
| One proposal for the crop, the normalization and the unprojection (the dropped proposal `arithmetic-precision`). | Rows T10 and D11 differ only by float32 rounding of one result. The user ruled them `exact`. | OpenMMLab-Exporter ADR-W2Y4 |
| Also change the Inverse to the mmpose closed form (`x / T_w * w + c_x - 0.5 * w`). | The closed form and the inverse of `M` differ by float32 rounding only (row D11, `exact`). The user ruled row D11 (unprojection) `exact`. The proposal covers only the crop matrix. | 2.3, Guidance; part 5, R2 |
| A new field `crop_policy.arithmetic` with an exact and a float32 value. | No model needs the exact-math value. One more field needs a rule and vectors. | Part 1 |
| `M` from `T_w / w` and `T_h / h` in float32 (only the dtype changes). | mmpose makes `M` from three float32 points that use only `w`. The y scale differs. This form does not give the mmpose `M`. | Part 1, Property, (3); 2.3 |
| The skellytracker form (the second point above the centre, the dtype of the caller). | It gives another `M` on 317 of 318 boxes, with a float32 box and with the float32 box cast to float64. | Part 1, Measured difference, (4) (secondary) |
| Keep the exact-math text for `maintain_aspect_ratio: false`. | One rule for both branches is easier for a host. mmpose `get_warp_matrix(fix_aspect_ratio=False)` gives the float32 form of 2.3. No model uses the branch, so a parity run cannot test it. | mmpose `get_warp_matrix`, the `fix_aspect_ratio=False` branch: [`mmpose/structures/bbox/transforms.py:425-429`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L425-L429) |
| A rule that refuses a box with an empty crop. | Not in the scope of this proposal. The reference file refuses such a box with `ValueError` (no rule ID), because `M` does not exist. | Part 3 |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake names the bundle ID of this proposal: row T4b of the RTMW intake (`payload/intake.md` of `model-rtmw-wholebody133@openmmlab-exporter`) is `near-miss` and names `proposal-affine-crop-matrix@openmmlab-exporter`.
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or `none`. This proposal builds on such an entry. It does not compete with it.
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing. It cites the gated run of part 5 (OpenMMLab-Exporter ADR-6A8S).
- [x] Part 1 gives each plan decision about the spec in words, with no item number, or `none`.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the proposal bundle.
- [x] Part 4 names the vector file, and the file exists in the proposal bundle. `fill` wrote its `expect`.
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a: no pixel case.
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the script. It gives the numbers of the 6 runs, the script path and the commit `0d07c982fb6915fee6fa0b8ccac35873c77c4db2`.
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter repo. The result is `pass`. The script is in commit `0d07c982fb6915fee6fa0b8ccac35873c77c4db2`, on the default branch.
- [x] Part 7 lists each example that the change makes invalid, or says `none` with the reason.
- [x] Each citation of a spec text, a base file or a record names a heading or a case `id`, not a line number of a copy.
- [x] No file in skellytracker changed, except the version folder that `pack` wrote in `intakes/`.

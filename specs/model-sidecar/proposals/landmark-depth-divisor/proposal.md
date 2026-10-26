---
slug: landmark-depth-divisor
section: post.pose.decode.coordinate
exporter: MediaPipe-Exporter
decision: "0022"
state: recorded
---
# Change proposal: landmark-depth-divisor

This file is informative. It is not part of the normative spec until a content PR lands its text in the section files (decision [0036](../../../../notes/decisions/0036-spec-proposals-folder.md)).

**Source.** The MediaPipe-Exporter file of the proposal `landmark-depth-divisor`, and its reference file, which is the `python` code block of part 3. Commit `none (no git repo)`. Copied on 2026-10-25. MediaPipe-Exporter has no git repo. Its paths in this file are not pinned. The copy changes only the items of decision 0036, item 3. The session wrote no part.

This file uses ASD-STE100 Simplified Technical English. It is a local working note of
MediaPipe-Exporter (decision 0001). Git does not track it. It is the full phase 2 proposal of the
skellytracker gap record 0022. It gives the eight parts that skellytracker 0022 does not have.

Labels in this file:

- **User decision (2026-10-23)** and **user decision (2026-10-24)** mark a decision of the user. "Plan
  T<n>" is a user decision in section 2.1 of the untracked pose-models plan of OpenMMLab-Exporter (plan facts)
  (secondary). Do not change a user decision without the user.
- **Proposal choice** marks a choice of this proposal. On 2026-10-24 the user decided the three open
  questions (plan T28: H2, H7 and H8) and the parity script (H6). "Open questions for the user" lists each decision.
- "The 0020 proposal" is `specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`. "The extra-outputs
  proposal" is `specs/model-sidecar/proposals/landmark-extra-outputs/proposal.md`. "The intake" is
  the untracked intake of `mediapipe-hand21` of MediaPipe-Exporter (plan facts).
- "MediaPipe source" means the cached copies of MediaPipe commit
  `e9794ef55e2509c09aa8b6ba1764b797db8eb200` in
  `model_cache/sources/e9794ef55e2509c09aa8b6ba1764b797db8eb200/` (the pin of MediaPipe-Exporter
  0002). Paths are relative to that folder.

Line numbers of skellytracker files are at commit `dom/21-move-sidecar-guide` (the
cited lines are the same at `dom/18-agents-adr-bootstrap-kit`). Line numbers of `docs/mediapipe-whole-body.md` are in
MediaPipe-Exporter on 2026-10-24.

## Header

| Field | Value |
|---|---|
| Title | The depth of a `coordinate` decode with `depth_unit: pixel`: a divisor of the raw depth, and the unprojection of the depth to the source image |
| Slug | `landmark-depth-divisor`. This is the slug of the skellytracker gap record 0022 (`notes/decisions/0022-landmark-depth-divisor.md`; index row at `notes/decisions/README.md:41`). The exporter guide says: use the slug of a `proposed` entry that covers your rows (`specs/exporter-guide/sidecars/workflow/phase-2-proposal.md:13-20`). |
| Date | 2026-10-24; updated 2026-10-24 (user decisions plan T28: H2, H6, H7, H8); updated 2026-10-25 (re-pinned to skellytracker `dom/21-move-sidecar-guide`; decision citations name the repo; the reference file cites the section ID in each docstring) |
| Exporter repo | MediaPipe-Exporter |
| Exporter commit | none (no git repo) |
| Model, and its intake file | The hand landmark model of the MediaPipe Holistic hand branch, `hand_landmark_full` (size `full`; `lite` has the same output contract, intake row F4). `model_id` `mediapipe-hand21` (plan T14). ONNX probe file `model_cache/onnx/hand_landmark_full.onnx` (sha256 `5c7c9fcbba12039ef6a28f676272b5fbfc19693c12f099722a44554fb2623c17`). Intake: the untracked intake of `mediapipe-hand21` of MediaPipe-Exporter (plan facts) (2026-10-24). |
| Intake rows with the verdict `near-miss` or `gap` | K4 decode method and its parameters (`near-miss`): the field `depth_unit` exists, but `pixel` cannot carry the divisor `0.4`, and the spec does not say how the host unprojects a `pixel` depth. The `x` and `y` part of K4 is `exact`. Also row K4 of the untracked intake of `mediapipe-pose39` of MediaPipe-Exporter (plan facts) (2026-10-24; deferred: the untracked blazepose plan of MediaPipe-Exporter (plan facts), BlazePose, `near-miss`): the pose graph decodes with `normalize = false` (`pose_landmarks_detector_graph.cc:411-413`), so the divisor is the default `1.0`. The model needs the heading "Depth" and no `depth_normalize`. |
| Kind | `changed section` (`post.pose.decode.coordinate`: a new field and a new heading "Depth"), with edits to `post.pose.schema` (the text of `depth_unit` and rule `V-post.pose.schema-9`), `post.unprojection` (one sentence), `format.versioning`, the changelog and the model intake template |
| Proposed section ID | `post.pose.decode.coordinate` (the `id` of `specs/model-sidecar/post/pose-decode-coordinate.md:2`) |
| Section file | `specs/model-sidecar/post/pose-decode-coordinate.md` |
| Depends on | `specs/model-sidecar/proposals/roi-transform-and-source/proposal.md` (the full proposal of skellytracker 0020): the factor `k` of `rotated_roi_crop` uses its crop ROI `Rc` (Behaviour step 3). The 0020 proposal lands first. Without it, the rule holds for the five current resize methods, and the hand landmark model has no resize method. The 0020 proposal gives this input in its part 7 ("Input for skellytracker 0022"): the factor from input pixels to source pixels along `x` is `wc / T_w`. This proposal uses that factor. |
| Needed by | none |
| Related, not a dependency | The extra-outputs proposal (`landmark-extra-outputs`, skellytracker 0021): the other outputs of the same model. The OpenMMLab-Exporter proposal `keypoint-visibility` (in progress; section `post.pose.visibility`): a per-point visibility value read from a channel of the `keypoints` output. The depth of this proposal is the third value of each keypoint (`z`). The two proposals do not overlap. **Related (merge points; review-readiness audit 2, 2026-10-24).** Other proposals edit the same spec text as this proposal. The content PR that lands second rebases on the first and keeps the edits of both. Line numbers are at skellytracker `dom/21-move-sidecar-guide`, as in the rest of this file. Each cited line is the same at `dom/18-agents-adr-bootstrap-kit` and at `dom/21-move-sidecar-guide`. `format/versioning.md:74` (the legacy row "Not available."): `pose-decode-flip-test` (OpenMMLab-Exporter), `heatmap-decode-refinement` (OpenMMLab-Exporter), `keypoint-visibility` (OpenMMLab-Exporter), `roi-transform-and-source`, `roi-refiner-role`, `landmark-extra-outputs`; `post/pose-schema.md:89-95` (the `pose.decode` fields table and "Method-specific fields"): `pose-decode-flip-test` (OpenMMLab-Exporter), `heatmap-decode-refinement` (OpenMMLab-Exporter), `keypoint-visibility` (OpenMMLab-Exporter); `post/pose-schema.md:117-127` ("Validation rules": `-1` and `-2` owned by `roi-transform-and-source`, `-7`, `-9`, the "See also" line): `roi-transform-and-source`, `landmark-extra-outputs`, `pose-decode-flip-test` (OpenMMLab-Exporter), `keypoint-visibility` (OpenMMLab-Exporter); `post/pose-decode-coordinate.md:33` (the single-person form): `keypoint-visibility` (OpenMMLab-Exporter), `landmark-extra-outputs`; `post/pose-decode-coordinate.md:55-56` ("Authoring guidance"): `keypoint-visibility` (OpenMMLab-Exporter); `post/unprojection.md:21-36` ("Behaviour" and the list of inverses): `roi-transform-and-source`, `roi-refiner-role`; `templates/model-intake.md:300` (row D11): `roi-transform-and-source`; `templates/model-intake.md:314` (row K4): `heatmap-decode-refinement` (OpenMMLab-Exporter); `changelog.md:55-59` ("Compatibility impact"): `simcc-score-rule` (OpenMMLab-Exporter), `heatmap-decode-refinement` (OpenMMLab-Exporter), `normalize-arithmetic` (OpenMMLab-Exporter), `affine-crop-arithmetic` (OpenMMLab-Exporter), `model-id-suffix` (OpenMMLab-Exporter), `roi-transform-and-source`, `landmark-extra-outputs`. All 13 proposals add a row to "Summary of changes" (row `N`, the next free number at merge time) and a sentence to the `vNEXT` row of the `schema_version` history (`changelog.md:68`). |
| skellytracker decision entries with the status `proposed` that cover the same property | **skellytracker 0022** (gap record, `0022-landmark-depth-divisor.md:8-9`). This file is its full proposal. Part 8 says where it differs from the direction of skellytracker 0022 (`:11-20`), with the reasons. **skellytracker 0020** (gap record; full proposal: the 0020 proposal): the crop and its inverse. **skellytracker 0021** (gap record; full proposal: the extra-outputs proposal): the other outputs. |
| Evidence basis | **User decision (2026-10-23): the user designated `docs/mediapipe-whole-body.md` as checked primary evidence** (the header rows "Evidence basis" of the 0020 proposal and the refiner proposal). This proposal cites it with `path:line` as primary evidence. Part 1 names the other sources, each for a fact that the document does not cover. |
| skellytracker folder that you read | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read | `dom/21-move-sidecar-guide` (`git status --porcelain` lists no tracked change; re-pinned on 2026-10-25 from `dom/18-agents-adr-bootstrap-kit`). `git diff --stat dom/18-agents-adr-bootstrap-kit dom/21-move-sidecar-guide -- specs/model-sidecar/post specs/model-sidecar/format specs/model-sidecar/changelog.md notes/decisions/0022-landmark-depth-divisor.md notes/decisions/0008-vnext-scope.md skellytracker` names no file that this proposal cites by line. In `specs/model-sidecar/templates/model-intake.md` only the header paragraph (`:2-8`) changed, so rows D11 (`:300`) and K4 (`:314`) keep their lines. `specs/model-sidecar/TRACEABILITY.md` changed only at `:107-108` (link text), so `:42, 92` keep their lines. `notes/decisions/README.md:41` is still the index row of skellytracker 0022. Guide citations point to the layout of skellytracker 0034 (`specs/exporter-guide/sidecars/`). History: the pin before was `dom/18-agents-adr-bootstrap-kit` (re-pinned on 2026-10-24 from `dom/17-gitignore-python-version`; `git diff --stat dom/17-gitignore-python-version dom/18-agents-adr-bootstrap-kit -- specs/model-sidecar .claude` is empty). The intake also reads `dom/18-agents-adr-bootstrap-kit` (re-pinned from `dom/16-private-data`). `git diff --stat dom/16-private-data dom/17-gitignore-python-version -- specs notes/decisions .claude` is empty. The spec text did not change after the pin (only link repairs). |

## 1. Gap

This part cites skellytracker 0022 (gap record). Skellytracker 0022 gives the gap and the direction: an optional
divisor of the raw depth in `pose.decode` for a `coordinate` decoder with `depth_unit: pixel`, named
`depth_normalize` (`:11-13`); the decoded depth `z = z_raw / depth_normalize` in pixels of the model
input, with the default `1.0` (`:13-15`); and the proposal must state how the host unprojects a
`pixel` depth to the source image (`:15-16`). This proposal gives the eight parts.

**Evidence basis.** **User decision (2026-10-23):** `docs/mediapipe-whole-body.md` is checked
primary evidence. This part cites it as primary, and it does not check its facts again upstream.

| Item | Value |
|---|---|
| Property | The hand landmark model gives `(x, y, z)` for each of 21 points in crop pixels (224² input). MediaPipe decodes the depth as `z / input_width / normalize_z`, with `normalize_z = 0.4` for the hand graph (the default is 1.0, and the pose and face graphs do not set it). Then the landmark projection multiplies `z` by the width of the hand rect. Thus `z` has the scale of `x`. In source-image pixels, the depth is `z_raw / 224 / 0.4 · roi_size`. |
| Upstream evidence (file and line, or config key; upstream commit or release) | **Primary** (`docs/mediapipe-whole-body.md`, user designation): `:138-145` (`TensorsToLandmarksCalculator`: `x / input_width`, `y / input_height`; `z / input_width / normalize_z` gives the depth; the default `normalize_z` is 1.0; the hand graph sets 0.4; the pose graph and the face graph do not set it); `:147-149` (`LandmarkProjectionCalculator` rotates by the rect rotation, scales by the rect size and adds the rect centre; it multiplies `z` by the rect width; thus `z` is in the same units as `x`); `:404-406` (the hand landmark model: `z` in image units is `z_raw / 224 / 0.4 · roi_size`). **Other sources, for facts that the document does not cover:** (a) MediaPipe source: `calculators/tensor/tensors_to_landmarks_calculator.cc:169-171` (the raw `z` is the third value) and `:188-192` (`z / input_image_width / normalize_z`, with the comment "Scale Z coordinate as X + allow additional uniform normalization"); `calculators/tensor/tensors_to_landmarks_calculator.proto:36-40` ("Z coordinate is scaled as X assuming a weak perspective projection camera model") and `:55-58` (`normalize_z`, default 1.0); `tasks/cc/vision/hand_landmarker/hand_landmarks_detector_graph.cc:73` (`kLandmarksNormalizeZ = 0.4`) and `:118-127, 289-294` (the landmark decode sets the input width, the input height and `normalize_z`); `calculators/util/landmark_projection_calculator.cc:84-101` (with `NORM_RECT` alone: `new_z = landmark.z() * input_rect.width(); // Scale Z coordinate as X.`), `:47-66` and `:121-139` (with `IMAGE_DIMENSIONS` or a projection matrix: `z_scale` is the length of the projected segment from `(0, 0)` to `(1, 0)`, `CalculateZScale`). (b) MediaPipe-Exporter 0005 ("These rules did not change": the landmark `z` in image units is `z_raw / 224 / 0.4 * roi_size`). (c) The probe geometry `notes/decisions/scripts/hand_roi_reference.py:31, 165-168` (`NORMALIZE_Z = 0.4`; `z / n / NORMALIZE_Z * size`), no commit. |
| Nearest section ID | `post.pose.schema` (field `pose.decode.depth_unit`), with `post.pose.decode.coordinate` and `post.unprojection` |
| Why the nearest section is wrong | (1) `depth_unit: pixel` means "MediaPipe, scaled by the image width" (`specs/model-sidecar/post/pose-schema.md:93`). The text does not say which width (the model input, the crop or the source image), and it has no place for a second divisor. (2) No field of `pose.decode` holds the divisor: `pose.decode` has `method`, `is_3d`, `depth_unit`, `coordinate_scale` and `depth_range` (`post/pose-schema.md:91-95`; `post/pose-decode-coordinate.md:26`; skellytracker 0022 `:27-29`). (3) `post.unprojection` converts and maps `x` and `y` only (`specs/model-sidecar/post/unprojection.md:23-36`). A depth in model-input pixels has no rule to the source image. (4) Thus two hosts can report depths that differ by a factor of 2.5 (skellytracker 0022 `:28-29`), and by the crop scale. |
| Measured difference (number, image and script) | Scratch measurement of this session (secondary: no commit; the scratch script `hand21-outputs\measure_extra.py` of the session of 2026-10-24, not committed, output `out\measure_extra.json`; mediapipe 1.1.1, onnxruntime 1.31.0, OpenCV 5.0.0, NumPy 2.5.4; the image set (60 COCO images) and the video set (300 frames) of MediaPipe-Exporter 0006; the path A chain of the 0020 proposal). The quantity: for each hand that both give, the largest `|z_src − z_mp · W|` over the 21 points, in source pixels. `z_src` is `decode_depth` of the reference file of part 3, with the crop ROI `Rc` of the 0020 reference file. `z_mp` is the `z` of the hand landmarks of `HolisticLandmarker` (normalized like `x`, so `z_mp · W` is in source pixels). **With `depth_normalize: 0.4`:** image (85 hands) median 0.216 px, p95 0.954 px, largest 2.16 px (1.6 % of the ROI size); video (334 hand-frames) median 0.154 px, p95 1.051 px, largest 6.25 px (6.5 % of the ROI). **Without the divisor** (`depth_normalize` 1.0, the near-miss): image median 13.4 px, p95 35.1 px, largest 60.1 px; video median 8.8 px, p95 17.9 px. The median over the points of `z_mp · W / z_src(1.0)`, for points with `|z| > 1` px: image median 2.504, video median 2.499 (`1 / 0.4 = 2.5`). For comparison, the `x`, `y` error of the same chain: image median 0.335 px, video median 0.184 px. **The factor of `rotated_roi_crop`.** For 10,000 random crop ROIs and input sizes, `k = wc / T_w` equals the length of the image of the segment from `(0, 0)` to `(1, 0)` under `unproject_points` of the 0020 reference file within a relative `2.7e-11`. |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now | none. The table (`specs/model-sidecar/changelog.md:38-53`) has no row for a depth divisor or a depth unprojection. The `vNEXT` scope: skellytracker 0008 (accepted) does not include MediaPipe-Exporter (`notes/decisions/0008-vnext-scope.md:8-15`). The 0020 proposal adds it with a new entry (user decision 2026-10-23 (4)). **User decision (plan T28 (H2), 2026-10-24):** this change also goes into `vNEXT`, on the same scope extension (Q1). Skellytracker 0022 asks for this decision (`:18-20`). |

**Missing primary evidence.**

- The exporter export does not exist. The probe file has the flat layout `[1, 63]`. The plan reshapes
  it to `[B, 21, 3]` with `z` raw (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts), secondary). The intake
  rows G5a and K5 record this.
- The case `maintain_aspect_ratio: true` with a non-square ROI. MediaPipe removes the letterbox
  padding (`LandmarkLetterboxRemovalCalculator`) before the projection. Its source is not in the cache,
  so this proposal does not know what it does to `z`. No model of this proposal uses that case: the
  hand landmark crop has `maintain_aspect_ratio: false`, and every hand ROI is square (0020 proposal,
  part 2.3 notes). Part 2.3 gives the geometric rule.

## 2. Spec change

### 2.1 Sections

**Changed section.** `post.pose.decode.coordinate`, title "Coordinate decode", file
`specs/model-sidecar/post/pose-decode-coordinate.md`. It gets the field `pose.decode.depth_normalize`
(heading "Fields"), a new heading "Depth" (after "Behaviour"), a new rule
`V-post.pose.decode.coordinate-2`, and a heading "Legacy behaviour". Its front matter gets
`vectors: vectors/post.pose.decode.coordinate.yaml` (now `null`, `:16`). The section ID, the title
and the selectors do not change.

**Places that the change edits.** Line numbers are at skellytracker `dom/21-move-sidecar-guide` (the same at `dom/18-agents-adr-bootstrap-kit`).

| Place | Heading | Edit |
|---|---|---|
| `specs/model-sidecar/post/pose-decode-coordinate.md:16` | Front matter, `vectors` | `vectors/post.pose.decode.coordinate.yaml` |
| `specs/model-sidecar/post/pose-decode-coordinate.md:24-28` | Fields | Add the row `pose.decode.depth_normalize` (part 2.2). Change the sentence of `:28`: "`pose.decode.coordinate_scale` and `pose.decode.depth_normalize` are fields of `pose.decode`." |
| `specs/model-sidecar/post/pose-decode-coordinate.md:33` | Behaviour, the single-person form | "`z` is root-relative depth (in `depth_unit`)" becomes "`z` is root-relative depth (in `depth_unit`). For `depth_unit: pixel`, see Depth (`#depth`)." |
| `specs/model-sidecar/post/pose-decode-coordinate.md`, after `:37` | New heading "Depth" | The normative text of part 2.3. |
| `specs/model-sidecar/post/pose-decode-coordinate.md:41-43` | Validation rules | Add `V-post.pose.decode.coordinate-2` (part 2.4). |
| `specs/model-sidecar/post/pose-decode-coordinate.md`, after the validation rules | New heading "Legacy behaviour" | "Availability before `vNEXT`: Schema versioning (`../format/versioning.md#legacy-behaviour`)." |
| `specs/model-sidecar/post/pose-decode-coordinate.md:50` | Implementer guidance (non-spec PR) | Add: "A 3D parity check compares `z` after the Depth (`#depth`) rule with the upstream depth in source pixels." |
| `specs/model-sidecar/post/pose-decode-coordinate.md:55-56` | Authoring guidance (non-spec PR) | Replace the bullet on the skellytracker 0022 gap (`:56`) with the mapping: MediaPipe hand: `depth_unit: pixel`, `depth_normalize: 0.4` (`kLandmarksNormalizeZ`); MediaPipe pose and face: no `depth_normalize` (the graphs do not set `normalize_z`). Keep the Qualcomm-Exporter bullet (`:55`) as a historical fact. |
| `specs/model-sidecar/post/pose-schema.md:93` | `pose.decode`, field `depth_unit` | "`pixel` (MediaPipe, scaled by the image width)" becomes "`pixel` (the depth has the scale of `x`: Coordinate decode (`pose-decode-coordinate.md#depth`))". |
| `specs/model-sidecar/post/pose-schema.md:95` | `pose.decode`, method-specific fields | Add `pose.decode.depth_normalize` (`pose-decode-coordinate.md#fields`). |
| `specs/model-sidecar/post/pose-schema.md:125` | `V-post.pose.schema-9` | Changed (part 2.4). |
| `specs/model-sidecar/post/unprojection.md:23-36` | Behaviour | Add after the list of inverses: "A depth in `depth_unit: pixel` has the scale of `x`. Coordinate decode (`pose-decode-coordinate.md#depth`) gives its unprojection. The host does not unproject a depth in `m` or `mm`." |
| `specs/model-sidecar/format/versioning.md:72-74` | Legacy behaviour | Add `pose.decode.depth_normalize` to the first column of the existing row (part 2.6). |
| `specs/model-sidecar/format/versioning.md:51-63` | Version-aware compatibility | No link: the new heading "Legacy behaviour" points to `format.versioning`, as `pre.resize.fit` does. |
| `specs/model-sidecar/changelog.md:14-36` | Summary of changes | New row N, the next free number at merge time (part 2.7). 13 open proposals (9 of OpenMMLab-Exporter, 4 of MediaPipe-Exporter) add a summary row, so the numbers depend on the merge order. |
| `specs/model-sidecar/changelog.md:55-59` | Compatibility impact | Add: "At `vNEXT`, `depth_unit: pixel` is valid only with `pose.decode.method: coordinate`. A `pixel` depth has the scale of `x`, and the host unprojects it with the factor of `x` of the resize inverse." |
| `specs/model-sidecar/changelog.md:68` | `schema_version` history, row `vNEXT` | Add text (part 2.7). |
| `specs/model-sidecar/templates/model-intake.md:314` | Row K4 | Add `depth_normalize` to the list of parameters. Add: "For `depth_unit: pixel`, record the divisor of the raw depth and the width that scales it." |
| `specs/model-sidecar/templates/model-intake.md:300` | Row D11 | Add: "and the depth for `depth_unit: pixel` (Coordinate decode (`../post/pose-decode-coordinate.md#depth`))". |
| `specs/model-sidecar/TRACEABILITY.md:42, 92` | Section tables | Regenerated: the section gets a vector file. |
| `tools/make_vectors.py`, `tools/tests/test_vectors.py` | Vector builders and tests | The vectors come from the reference file of part 3. The content PR commits the YAML of part 4, or adds a builder that imports `specs/model-sidecar/reference/post_pose_decode_coordinate.py`. For the implementer. |
| skellytracker `notes/decisions/0022-landmark-depth-divisor.md` | The gap record | A skellytracker session adds this proposal to the gap record. |

`specs/model-sidecar/sidecar-spec.md` (the permanent index) needs no edit.

### 2.2 Fields table

| Field | Type | Required | Description |
|---|---|---|---|
| `pose.decode.depth_normalize` | float | no | For `method: coordinate` with `is_3d: true` and `depth_unit: pixel` only. The divisor of the raw depth (Depth (`#depth`), step 1). A finite number `> 0`. The default is `1.0`. The MediaPipe hand landmark model has `0.4` (`kLandmarksNormalizeZ`). |
| `pose.decode.depth_unit` (changed text, `post.pose.schema`) | enum | required when `is_3d: true` | `m`, `mm` or `pixel`. `pixel`: the depth has the scale of `x`. At `vNEXT`, `pixel` is valid only with `method: coordinate` (changed `V-post.pose.schema-9`). |

YAML excerpt (the decode of `hand_landmark_full`; the `keypoints` output is `[-1, 21, 3]` after the
reshape of the plan, and its other outputs are the extra-outputs proposal):

```yaml
pose:
  decode:
    method: coordinate
    coordinate_scale: pixel   # x, y in 224 crop pixels (hand_landmarks_detector_graph.cc:118-127)
    is_3d: true
    depth_unit: pixel
    depth_normalize: 0.4      # kLandmarksNormalizeZ (hand_landmarks_detector_graph.cc:73)
```

### 2.3 Behaviour

Normative text of the new heading "Depth" of `post.pose.decode.coordinate`:

```text
## Depth

This heading applies when pose.decode.is_3d is true and pose.decode.depth_unit is pixel. It applies
to each z value of a coordinate decode: the third value of a single-person keypoints output, the z
of a poses tensor (B, I, K, 4), and the z component of packed_keypoints.

A pixel depth has the scale of x. The model defines the direction of z and its reference point
(root-relative depth). For each z value z_raw, with the model input size [T_h, T_w]:

1. Model-input pixels.
     z_in = c * z_raw / depth_normalize
   c is the factor of x of pose.decode.coordinate_scale:
     pixel:          c = 1
     normalized_01:  c = T_w
     normalized_11:  c = T_w / 2
   The offset of normalized_11 does not apply to a depth. depth_normalize has the default 1.0.
2. Source pixels.
     z_src = z_in * k
   k is the length, in source pixels, of the image of the model-input segment from (0, 0) to (1, 0)
   under the inverse of input.resize.method (Unprojection):
     letterbox:           k = src_w / n_w        (the rounded n_w of the letterbox algorithm)
     stretch:             k = src_w / T_w
     fit:                 k = 1 / s              (the unrounded s of the fit algorithm)
     none:                k = 1
     affine_person_crop:  k = w / T_w            (w of the warp, after expand_ratio and the
                                                  aspect step)
     rotated_roi_crop:    k = wc / T_w           (the crop ROI Rc, Rotated ROI crop, step 3)
   The depth uses the factor of x also when the factors of x and y differ.

The host reports z_src with the keypoint, in source pixels. It does not add an offset.
```

Which upstream rule each part describes:

| Part | Upstream rule (primary: `docs/mediapipe-whole-body.md`; other sources as named in part 1) |
|---|---|
| "A pixel depth has the scale of x" | `TensorsToLandmarksCalculator` divides `z` by the input width, as `x` (`:141-142`; `tensors_to_landmarks_calculator.cc:188-192`; `.proto:36-40`: "Z coordinate is scaled as X assuming a weak perspective projection camera model") |
| Step 1, `depth_normalize` | `normalize_z` (`:141-143`; `.proto:55-58`, default 1.0); `kLandmarksNormalizeZ = 0.4` (`hand_landmarks_detector_graph.cc:73`) |
| Step 1, `c` | MediaPipe gives normalized landmarks (`x / input_width`). A model whose `x` is already normalized needs the factor `T_w` to give model-input pixels, as `post.unprojection` does for `x` (`specs/model-sidecar/post/unprojection.md:25-28`). |
| Step 2, `k` | `LandmarkProjectionCalculator`: with `NORM_RECT`, `z · rect.width` (`landmark_projection_calculator.cc:93-101`; `:147-149`); with a matrix, `CalculateZScale`, the length of the projected segment from `(0, 0)` to `(1, 0)` (`:47-66, 121-139`). The definition of `k` is the matrix form. For `rotated_roi_crop` it gives `wc / T_w`, the `NORM_RECT` form (0020 proposal, part 7). |

Notes, not normative:

- **The MediaPipe form.** For the hand landmark model, steps 1 and 2 give
  `z_src = z_raw / 0.4 · wc / 224`. That is `z_raw / 224 / 0.4 · roi_size`
  (`docs/mediapipe-whole-body.md:405-406`) in source pixels. MediaPipe reports `z` normalized like
  `x`, so its value in source pixels is `z · W` (the source width). The vector
  `decode-hand-mediapipe-form` gives both forms.
- **Work with the inverse of `rotated_roi_crop`.** The factor `k = wc / T_w` uses the same crop ROI
  `Rc` as the inverse of `x` and `y` (0020 proposal, heading "Inverse"). The inverse maps the
  model-input vector `(1, 0)` to `(c · wc / T_w, s · wc / T_w)`, with `c = cos(rotation)` and
  `s = sin(rotation)`. Its length is `wc / T_w`. The scratch check of part 1 confirms it within
  `2.7e-11` (relative) for 10,000 random crop ROIs.
- **`maintain_aspect_ratio: true`.** The rule uses the enlarged crop ROI `Rc`, as the inverse of the
  0020 proposal does. For a square ROI on a square input, `Rc` is the ROI. MediaPipe removes the
  letterbox padding before the projection, and the projection uses the rect width. This proposal did
  not read the source of that step (part 1, missing evidence). No model in scope has this case.
- **`normalized_11` (user decision plan T28 (H8)).** The factor `c` of step 1 is `T_w / 2` with no
  offset, as for the scale of `x`. The rule does not reject a `pixel` depth with `normalized_11`. No
  model in scope uses this case. The vector of `normalized_11` tests the factor only.
- **The precision.** The section states no arithmetic precision (the rule of user decision Q7 = (c)
  of the 0020 proposal). MediaPipe computes in float32. The vectors give the tolerance `1e-4` px for
  a depth.

### 2.4 Validation rules

New rule of `post.pose.decode.coordinate`:

- [ ] `V-post.pose.decode.coordinate-2` **(vNEXT)** `pose.decode.depth_normalize` must not be present
  unless `pose.decode.method` is `coordinate`, `pose.decode.is_3d` is `true` and
  `pose.decode.depth_unit` is `pixel`. If it is present, it must be a finite number (not a boolean)
  `> 0`.

Changed rules:

- `V-post.pose.schema-9` (`specs/model-sidecar/post/pose-schema.md:125`), new text: "If
  `pose.decode.is_3d` is present, it must be a boolean. When `true`, `pose.decode.depth_unit` must be
  present and must be one of `m`, `mm` or `pixel`. `depth_unit` and `depth_range` must not be present
  unless `is_3d: true`. **(vNEXT)** `depth_unit: pixel` is valid only with
  `pose.decode.method: coordinate`." (The new last sentence is **user decision plan T28 (H7)**, Q2.
  The reason: the heading "Depth" is in the `coordinate` section, and no `simcc` model in scope
  has a `pixel` depth: RTMW3D uses `m`, `post/pose-schema.md:93`.)

Existing rules that name a changed value, and the effect:

| Rule | Effect |
|---|---|
| `V-post.pose.decode.coordinate-1` (`post/pose-decode-coordinate.md:43`) | unchanged. |
| `V-post.pose.decode.simcc-1` (`post/pose-decode-simcc.md:46`) | unchanged. `depth_range` stays for `simcc`. |
| `V-post.pose.decode.heatmap-1` (`post/pose-decode-heatmap.md:32`) | unchanged. |
| `V-post.pose.bottom_up-2` (`post/pose-bottom-up.md:70`) | unchanged. A packed `z` with `depth_unit: pixel` uses the heading "Depth". |
| `V-post.pose.schema-7` | unchanged by this proposal (the extra-outputs proposal changes it). |
| `V-format.versioning-1`, `-2` | unchanged. `n/a at vNEXT`. |

### 2.5 Selectors

No change: `pose.decode.method=coordinate` and `outputs[].semantic=keypoints`
(`specs/model-sidecar/post/pose-decode-coordinate.md:7-9`). The heading "Depth" applies also to the
bottom-up forms of the same method.

### 2.6 Legacy behaviour and version effect

- A sidecar with `schema_version < vNEXT` cannot declare `pose.decode.depth_normalize`. The new
  sentence of `V-post.pose.schema-9` is marked **(vNEXT)**, so a legacy `simcc` sidecar with
  `depth_unit: pixel` stays valid. No package sidecar declares `is_3d` (a search of
  `skellytracker/` at `dom/17-gitignore-python-version`; no package file changes up to `dom/21-move-sidecar-guide`).
- The heading "Depth" applies at `vNEXT`. Before `vNEXT`, the spec gives no unprojection of a depth,
  and that does not change.
- The change goes into the `vNEXT` revision (**user decision plan T28 (H2)**, Q1).

Changed row of the "Legacy behaviour" table of `format.versioning`
(`specs/model-sidecar/format/versioning.md:74`; the 0020 and extra-outputs proposals add to the same row):

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|---|---|---|
| `boxes`/`scores`/`class_logits` semantics, `packed_keypoints`, `stretch`, `fit`, `class_id_map`, `pose.decode.depth_normalize` and the unprojection of a `pixel` depth | Not available. | Available. |

### 2.7 Changelog row

Summary of changes (`specs/model-sidecar/changelog.md:14-36`), row N (the next free number at merge time):

```markdown
| N | Decode | A `pixel` depth of a `coordinate` decode has the scale of `x`. New optional `pose.decode.depth_normalize` (default `1.0`): `z_in = c · z_raw / depth_normalize`, with the factor `c` of `x` for `coordinate_scale`. The host unprojects it with `z_src = z_in · k`, where `k` is the length of the image of a unit `x` step under the resize inverse (`src_w / n_w`, `src_w / T_w`, `1 / s`, `1`, `w / T_w`, `wc / T_w`). `depth_unit: pixel` is valid only with `method: coordinate`. | MediaPipe hand landmark model (`normalize_z` 0.4) | [Coordinate decode](post/pose-decode-coordinate.md#depth) |
```

`schema_version` history (`specs/model-sidecar/changelog.md:68`), text to add to the `vNEXT` row: "Added
`pose.decode.depth_normalize` and the decode and unprojection of a `pixel` depth (the scale of `x`,
the factor of `x` of the resize inverse); `depth_unit: pixel` only with `coordinate`."

No row of "Considered and deliberately not added" changes.

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the exporter repo | the part 3 code of `specs/model-sidecar/proposals/landmark-depth-divisor/proposal.md` (exists) |
| Target file in skellytracker | `specs/model-sidecar/reference/post_pose_decode_coordinate.py` |
| Functions (one for each algorithm) | `validate_coordinate_decode`: rules `V-post.pose.decode.coordinate-1`, the new `-2` and the changed `V-post.pose.schema-9`. `split_single_person`: the single-person form of "Behaviour" (`(N, K, 2)` or `(N, K, 3)`). `depth_to_model_pixels`: heading "Depth", step 1. `depth_scale_factor`: step 2, the factor `k` for each resize method. `unproject_depth`: step 2. `decode_depth`: steps 1 and 2. |

- The note at the top of the file says `source commit: none (no host code)`. The functions come from
  the text of part 2.
- The section has no reference implementation today (`specs/model-sidecar/reference/` does not exist). The
  file implements the full section as changed: the field rules, the single-person read and the
  heading "Depth". The conversion of `x` and `y` and their inverse are `post.unprojection` and the
  resize sections, so they are not in this file. The bottom-up forms read their values with
  `post.pose.bottom_up`. Their `z` uses the same functions.
- The file uses NumPy and the Python standard library only. It does not load the 0020 reference
  file: `depth_scale_factor` takes the crop ROI `Rc` as an input.
- The file computes in float64. The section states no precision.

```python
"""Reference implementation of the section ``post.pose.decode.coordinate`` as the proposal changes it.

This file uses ASD-STE100 Simplified Technical English.

Note:
- Section ID: ``post.pose.decode.coordinate`` (changed). Proposal:
  ``specs/model-sidecar/proposals/landmark-depth-divisor/proposal.md`` (the full proposal of the skellytracker gap
  record 0022).
- Target file in skellytracker: ``specs/model-sidecar/reference/post_pose_decode_coordinate.py``.
- The section has no reference implementation today, so this file implements the full section as
  changed: the field rules, the single-person read, and the new heading "Depth" (the decode of a
  ``pixel`` depth and its unprojection). The bottom-up forms read their values with
  ``post.pose.bottom_up``. Their ``z`` uses the same ``Depth`` functions. The conversion of ``x`` and
  ``y`` to model-input pixels and their inverse are in ``post.unprojection`` and in the resize
  sections. They are not in this file.
- source commit: none (no host code). MediaPipe-Exporter has no git repo and no exporter code. The
  functions come from the text of part 2 of the proposal.
- Vector results: the 47 vectors of part 4 of the proposal pass against this file (47 of 47,
  2026-10-24; again 47 of 47 on 2026-10-25 after the docstring edits). They are
  ``unverified: no host implementation``.
- Parity result: to run (MediaPipe-Exporter has no git repo, so no script can be committed). The
  parity script is ``notes/decisions/scripts/hand_chain_parity.py`` (to write), one script for the four
  MediaPipe proposals (user decision plan T28 (H6)). A scratch measurement (secondary, part 1 of the proposal; part 5 takes its gates from it) used ``decode_depth`` of this file with the
  crop ROI of the part 3 code of ``specs/model-sidecar/proposals/roi-transform-and-source/proposal.md``.
- Precision: the section states no arithmetic precision (the rule of user decision Q7 = (c) of the
  0020 proposal). The vectors give the tolerances in ``compare``. This file computes in float64.

Conventions: ``target_hw`` is ``[T_h, T_w]``. Depths are root-relative values along the axis that
``z`` names. A ``pixel`` depth has the scale of ``x``.

Only NumPy and the Python standard library are used.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np

COORDINATE_SCALES = ("pixel", "normalized_01", "normalized_11")
DEPTH_UNITS = ("m", "mm", "pixel")
METHODS = ("simcc", "heatmap", "coordinate")
RESIZE_METHODS = ("letterbox", "stretch", "fit", "none", "affine_person_crop", "rotated_roi_crop")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_coordinate_decode(decode: Mapping[str, Any], schema_is_vnext: bool = True) -> bool:
    """``post.pose.decode.coordinate``, Validation rules: the rules of the fields of ``pose.decode`` that this section uses.

    ``V-post.pose.decode.coordinate-1`` (``coordinate_scale``), the new ``-2`` (``depth_normalize``) and
    the changed ``V-post.pose.schema-9`` (``is_3d``, ``depth_unit``, ``depth_range``; a ``pixel`` depth
    only with ``coordinate`` at ``vNEXT``, user decision plan T28 (H7)). ``decode`` is the ``pose.decode`` mapping. Raises
    ``ValueError`` at the first rule that fails. Returns ``True`` when all rules pass.
    """
    method = decode.get("method")
    if method not in METHODS:
        raise ValueError("pose.decode.method must be simcc, heatmap or coordinate")
    # V-post.pose.decode.coordinate-1
    if "coordinate_scale" in decode:
        if method != "coordinate":
            raise ValueError("coordinate_scale is valid only with method coordinate")
        if decode["coordinate_scale"] not in COORDINATE_SCALES:
            raise ValueError("coordinate_scale must be pixel, normalized_01 or normalized_11")
    # V-post.pose.schema-9 (changed)
    is_3d = decode.get("is_3d", False)
    if not isinstance(is_3d, bool):
        raise ValueError("pose.decode.is_3d must be a boolean")
    if is_3d:
        if decode.get("depth_unit") not in DEPTH_UNITS:
            raise ValueError("depth_unit must be m, mm or pixel when is_3d is true")
        if schema_is_vnext and decode["depth_unit"] == "pixel" and method != "coordinate":
            raise ValueError("depth_unit pixel is valid only with method coordinate")
    elif "depth_unit" in decode or "depth_range" in decode:
        raise ValueError("depth_unit and depth_range need is_3d true")
    # V-post.pose.decode.coordinate-2 (new)
    if "depth_normalize" in decode:
        if not schema_is_vnext:
            raise ValueError("depth_normalize needs schema_version >= vNEXT")
        if not (method == "coordinate" and is_3d and decode.get("depth_unit") == "pixel"):
            raise ValueError("depth_normalize needs method coordinate, is_3d true and depth_unit pixel")
        d = decode["depth_normalize"]
        if not (_is_number(d) and math.isfinite(d) and d > 0):
            raise ValueError("depth_normalize must be a finite number > 0")
    return True


def split_single_person(keypoints: Any, is_3d: bool) -> tuple[np.ndarray, np.ndarray | None]:
    """``post.pose.decode.coordinate``, Behaviour, the single-person form: split a ``keypoints`` tensor into ``(x, y)`` and ``z``.

    The shape is ``(N, K, 2)``, or ``(N, K, 3)`` when ``is_3d`` is true. Returns ``(xy, z)``. ``z`` is
    ``None`` when ``is_3d`` is false.
    """
    k = np.asarray(keypoints, dtype=np.float64)
    want = 3 if is_3d else 2
    if k.ndim != 3 or k.shape[2] != want:
        raise ValueError(f"a single-person keypoints output must have the shape (N, K, {want})")
    return k[..., :2], (k[..., 2] if is_3d else None)


def depth_to_model_pixels(
    z_raw: Any, coordinate_scale: str, target_hw: Sequence[int], depth_normalize: float = 1.0
) -> np.ndarray:
    """``post.pose.decode.coordinate``, heading "Depth", step 1: a ``pixel`` depth in model-input pixels.

    ``z_in = c * z_raw / depth_normalize``. ``c`` is the factor of ``x`` for ``coordinate_scale``:
    ``1`` for ``pixel``, ``T_w`` for ``normalized_01`` and ``T_w / 2`` for ``normalized_11``. The
    offset of ``normalized_11`` does not apply to a depth (user decision plan T28 (H8)).
    """
    t_w = float(target_hw[1])
    if coordinate_scale == "pixel":
        c = 1.0
    elif coordinate_scale == "normalized_01":
        c = t_w
    elif coordinate_scale == "normalized_11":
        c = t_w / 2.0
    else:
        raise ValueError("coordinate_scale must be pixel, normalized_01 or normalized_11")
    if not (_is_number(depth_normalize) and math.isfinite(depth_normalize) and depth_normalize > 0):
        raise ValueError("depth_normalize must be a finite number > 0")
    return c * np.asarray(z_raw, dtype=np.float64) / float(depth_normalize)


def depth_scale_factor(resize_method: str, inverse: Mapping[str, Any]) -> float:
    """``post.pose.decode.coordinate``, heading "Depth", step 2: the factor ``k`` from model-input pixels to source pixels.

    ``k`` is the length, in source pixels, of the image of the model-input segment from ``(0, 0)`` to
    ``(1, 0)`` under the inverse of the resize. ``inverse`` holds the values that the inverse of the
    method uses:

    - ``letterbox``: ``src_w``, ``n_w`` (the rounded scaled width). ``k = src_w / n_w``.
    - ``stretch``: ``src_w``, ``target_w``. ``k = src_w / T_w``.
    - ``fit``: ``s`` (the unrounded scale). ``k = 1 / s``.
    - ``none``: no value. ``k = 1``.
    - ``affine_person_crop``: ``crop_w`` (the width ``w`` of the warp, after ``expand_ratio`` and the
      aspect step), ``target_w``. ``k = w / T_w``.
    - ``rotated_roi_crop``: ``crop_roi`` (the crop ROI ``Rc``), ``target_w``. ``k = wc / T_w``.
    """
    if resize_method == "letterbox":
        k = float(inverse["src_w"]) / float(inverse["n_w"])
    elif resize_method == "stretch":
        k = float(inverse["src_w"]) / float(inverse["target_w"])
    elif resize_method == "fit":
        k = 1.0 / float(inverse["s"])
    elif resize_method == "none":
        k = 1.0
    elif resize_method == "affine_person_crop":
        k = float(inverse["crop_w"]) / float(inverse["target_w"])
    elif resize_method == "rotated_roi_crop":
        roi = inverse["crop_roi"]
        if len(roi) != 5:
            raise ValueError("rotated_roi_crop needs the crop ROI (cx, cy, wc, hc, rotation)")
        k = float(roi[2]) / float(inverse["target_w"])
    else:
        raise ValueError(f"unknown resize method {resize_method}")
    if not (math.isfinite(k) and k > 0):
        raise ValueError("the depth factor must be a finite number > 0")
    return k


def unproject_depth(z_model: Any, k: float) -> np.ndarray:
    """``post.pose.decode.coordinate``, heading "Depth", step 2: ``z_src = z_in * k``, in source pixels."""
    return np.asarray(z_model, dtype=np.float64) * float(k)


def decode_depth(
    z_raw: Any,
    decode: Mapping[str, Any],
    target_hw: Sequence[int],
    resize_method: str,
    inverse: Mapping[str, Any],
) -> np.ndarray:
    """``post.pose.decode.coordinate``, heading "Depth", steps 1 and 2: a raw ``pixel`` depth to source pixels.

    ``decode`` is the ``pose.decode`` mapping (``coordinate_scale`` default ``pixel``,
    ``depth_normalize`` default ``1.0``). It must have ``method: coordinate``, ``is_3d: true`` and
    ``depth_unit: pixel``.
    """
    validate_coordinate_decode(decode)
    if not (decode.get("method") == "coordinate" and decode.get("is_3d") is True
            and decode.get("depth_unit") == "pixel"):
        raise ValueError("the depth rule needs method coordinate, is_3d true and depth_unit pixel")
    z_in = depth_to_model_pixels(z_raw, decode.get("coordinate_scale", "pixel"), target_hw,
                                 decode.get("depth_normalize", 1.0))
    return unproject_depth(z_in, depth_scale_factor(resize_method, inverse))
```

## 4. Vectors

The reference file made the cases. The scratch generator of this session
(`hand21-outputs\gen_vectors.py` in the session scratchpad, not committed)
gives each case its inputs and its comment, and it takes the expected values from the reference file.
It rounds each value with a tolerance to 12 decimals. The hand-calculated values in the comments agree
with the expected values (for example `-10 / 0.4 · 448 / 224 = -50`, and
`-10 / 224 / 0.4 · 150 = -16.741071...`).

**The tolerances.** The section states no arithmetic precision. Each case whose result has a
floating-point value has its tolerance in `compare`: `1e-4` px for a depth (`z`) and `1e-6` for the
factor `k`. The bounds are above the float32 rounding of the values of the cases (a depth below
100 px has a float32 rounding below `4e-6` px). The flag `valid` and the `xy` values of
`split_single_person` must match exactly.

The scratch runner of this session (`hand21-outputs\run_vectors.py`, with `common.py` beside it)
read this YAML block back from this file and ran each case through the reference file. Result on
2026-10-24: **47 of 47 pass** (`validate_coordinate_decode` 19, `split_single_person` 4,
`depth_to_model_pixels` 7, `depth_scale_factor` 11, `unproject_depth` 1, `decode_depth` 5). A
mutation check changed one expected value (heading "Before you stop"): exactly one case failed.
Environment: the `uv` environment of OpenMMLab-Exporter (Python 3.14.2, NumPy 2.5.4, PyYAML 6.0.3).
Run again on 2026-10-25, after the docstring edits of the reference file, with a scratch runner that
reads this YAML block from this file: **47 of 47 pass** (the same counts for each function).

Cross-checks (not an independent implementation): the scratch measurement of part 1 ran
`decode_depth` on the real outputs of the model with the crop ROI of the 0020 reference file. The
depth agrees with `HolisticLandmarker` within a median of 0.216 px (image) and 0.154 px (video).

Coverage: the rules (the hand decode, no divisor, 2D, a metric depth, a legacy `simcc` `pixel` depth,
the same at `vNEXT` (an error), the divisor 0, negative, infinite, a boolean, a string, with `m`,
without `is_3d`, at a legacy version, `coordinate_scale` on `simcc` and with an unknown value,
`is_3d` without `depth_unit`, `depth_unit` without `is_3d`, a string for `is_3d`); the single-person
read for 3D and 2D, the flat `(N, 63)` layout and too few values; step 1 for `pixel` with and
without the divisor, `normalized_01`, `normalized_11` (the factor only), a non-square input (`T_w`,
not `T_h`), a zero divisor and an unknown scale; step 2 for each of the six resize methods, a
rounded letterbox width (the 427 × 640 example of skellytracker 0023), a non-square crop ROI (`wc`,
not `hc`), an unknown method, an ROI with four values and a zero factor; the full decode of the hand
(two ROIs, one in the MediaPipe form), the near-miss without the divisor (2.5 times smaller), a
`normalized_01` letterbox model and a metric depth (an error).

The target file is `specs/model-sidecar/vectors/post.pose.decode.coordinate.yaml`.

```yaml
section: post.pose.decode.coordinate
spec_revision: vNEXT
generated_by: the part 3 code of `specs/model-sidecar/proposals/landmark-depth-divisor/proposal.md`
unverified: no host implementation. MediaPipe-Exporter has no git repo and no exporter code.
cases:
  # the MediaPipe hand decode: kLandmarksNormalizeZ = 0.4
  - id: validate-hand
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: pixel, depth_normalize: 0.4}}
    expect: {valid: true}
  # depth_normalize is optional (default 1.0)
  - id: validate-no-divisor
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: pixel}}
    expect: {valid: true}
  # a 2D coordinate decode
  - id: validate-2d
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate}}
    expect: {valid: true}
  # depth_unit m with no divisor
  - id: validate-metric-depth
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: m}}
    expect: {valid: true}
  # legacy: the new pixel rule does not apply below vNEXT
  - id: validate-simcc-pixel-legacy
    function: validate_coordinate_decode
    params: {schema_is_vnext: false}
    input: {decode: {method: simcc, is_3d: true, depth_unit: pixel, depth_range: [-1, 1]}}
    expect: {valid: true}
  # changed V-post.pose.schema-9: a pixel depth needs method coordinate (vNEXT)
  - id: error-simcc-pixel
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: simcc, is_3d: true, depth_unit: pixel, depth_range: [-1, 1]}}
    expect: {error: depth_unit pixel is valid only with method coordinate}
  # -2: depth_normalize must be > 0
  - id: error-divisor-zero
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: pixel, depth_normalize: 0}}
    expect: {error: depth_normalize must be a finite number > 0}
  # -2: depth_normalize must be > 0
  - id: error-divisor-negative
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: pixel, depth_normalize: -0.4}}
    expect: {error: depth_normalize must be a finite number > 0}
  # -2: depth_normalize must be finite
  - id: error-divisor-infinite
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: pixel, depth_normalize: .inf}}
    expect: {error: depth_normalize must be a finite number > 0}
  # -2: a boolean is not a number
  - id: error-divisor-bool
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: pixel, depth_normalize: true}}
    expect: {error: depth_normalize must be a finite number > 0}
  # -2: a string is not a number
  - id: error-divisor-string
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: pixel, depth_normalize: '0.4'}}
    expect: {error: depth_normalize must be a finite number > 0}
  # -2: depth_normalize needs depth_unit pixel
  - id: error-divisor-metric
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: m, depth_normalize: 0.4}}
    expect: {error: 'depth_normalize needs method coordinate, is_3d true and depth_unit pixel'}
  # -2: depth_normalize needs is_3d true (and no depth_unit without is_3d)
  - id: error-divisor-2d
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate, depth_normalize: 0.4}}
    expect: {error: 'depth_normalize needs method coordinate, is_3d true and depth_unit pixel'}
  # -2: depth_normalize needs vNEXT
  - id: error-divisor-legacy
    function: validate_coordinate_decode
    params: {schema_is_vnext: false}
    input: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: pixel, depth_normalize: 0.4}}
    expect: {error: depth_normalize needs schema_version >= vNEXT}
  # -1: coordinate_scale only with coordinate
  - id: error-scale-on-simcc
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: simcc, coordinate_scale: pixel}}
    expect: {error: coordinate_scale is valid only with method coordinate}
  # -1: an unknown coordinate_scale
  - id: error-scale-value
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate, coordinate_scale: normalized, is_3d: true, depth_unit: pixel, depth_normalize: 0.4}}
    expect: {error: 'coordinate_scale must be pixel, normalized_01 or normalized_11'}
  # -9: is_3d true needs depth_unit
  - id: error-no-depth-unit
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true}}
    expect: {error: 'depth_unit must be m, mm or pixel when is_3d is true'}
  # -9: depth_unit needs is_3d true
  - id: error-depth-unit-2d
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate, depth_unit: pixel}}
    expect: {error: depth_unit and depth_range need is_3d true}
  # -9: is_3d must be a boolean
  - id: error-is3d-string
    function: validate_coordinate_decode
    params: {schema_is_vnext: true}
    input: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: 'true', depth_unit: pixel, depth_normalize: 0.4}}
    expect: {error: pose.decode.is_3d must be a boolean}
  # (N, K, 3): x, y and z
  - id: split-3d
    function: split_single_person
    params: {is_3d: true}
    input: {keypoints: [[[10.0, 20.0, 0.5], [30.0, 40.0, -1.0]]]}
    expect: {xy: [[[10.0, 20.0], [30.0, 40.0]]], z: [[0.5, -1.0]]}
    compare: {z: {atol: 0.0001}}
  # (N, K, 2): no z
  - id: split-2d
    function: split_single_person
    params: {is_3d: false}
    input: {keypoints: [[[10.0, 20.0], [30.0, 40.0]]]}
    expect: {xy: [[[10.0, 20.0], [30.0, 40.0]]], z: null}
  # the flat (N, 63) layout is not (N, K, 3)
  - id: error-split-flat
    function: split_single_person
    params: {is_3d: true}
    input: {keypoints: [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62]]}
    expect: {error: 'a single-person keypoints output must have the shape (N, K, 3)'}
  # is_3d true needs three values for each keypoint
  - id: error-split-2d-for-3d
    function: split_single_person
    params: {is_3d: true}
    input: {keypoints: [[[10.0, 20.0]]]}
    expect: {error: 'a single-person keypoints output must have the shape (N, K, 3)'}
  # pixel: -10 / 0.4 = -25
  - id: model-pixel-divisor
    function: depth_to_model_pixels
    params: {coordinate_scale: pixel, target_hw: [224, 224], depth_normalize: 0.4}
    input: {z_raw: [-10.0, 0.0, 4.0]}
    expect: {z: [-25.0, 0.0, 10.0]}
    compare: {z: {atol: 0.0001}}
  # pixel, the default divisor 1.0
  - id: model-pixel-default
    function: depth_to_model_pixels
    params: {coordinate_scale: pixel, target_hw: [224, 224]}
    input: {z_raw: [-10.0, 0.0, 4.0]}
    expect: {z: [-10.0, 0.0, 4.0]}
    compare: {z: {atol: 0.0001}}
  # normalized_01: 0.1 * 224 / 0.4 = 56
  - id: model-normalized-01
    function: depth_to_model_pixels
    params: {coordinate_scale: normalized_01, target_hw: [224, 224], depth_normalize: 0.4}
    input: {z_raw: [0.1, -0.05]}
    expect: {z: [56.0, -28.0]}
    compare: {z: {atol: 0.0001}}
  # normalized_11: the factor T_w / 2 only, no offset: 0.1 * 112 = 11.2
  - id: model-normalized-11
    function: depth_to_model_pixels
    params: {coordinate_scale: normalized_11, target_hw: [224, 224]}
    input: {z_raw: [0.1, 0.0]}
    expect: {z: [11.2, 0.0]}
    compare: {z: {atol: 0.0001}}
  # normalized_01 uses T_w (192), not T_h (256)
  - id: model-non-square
    function: depth_to_model_pixels
    params: {coordinate_scale: normalized_01, target_hw: [256, 192]}
    input: {z_raw: [0.5]}
    expect: {z: [96.0]}
    compare: {z: {atol: 0.0001}}
  # depth_normalize must be > 0
  - id: error-model-divisor-zero
    function: depth_to_model_pixels
    params: {coordinate_scale: pixel, target_hw: [224, 224], depth_normalize: 0.0}
    input: {z_raw: [1.0]}
    expect: {error: depth_normalize must be a finite number > 0}
  # an unknown coordinate_scale
  - id: error-model-scale
    function: depth_to_model_pixels
    params: {coordinate_scale: normalized, target_hw: [224, 224]}
    input: {z_raw: [1.0]}
    expect: {error: 'coordinate_scale must be pixel, normalized_01 or normalized_11'}
  # src_w / n_w = 1920 / 640
  - id: factor-letterbox
    function: depth_scale_factor
    params: {resize_method: letterbox}
    input: {inverse: {src_w: 1920, n_w: 640}}
    expect: {k: 3.0}
    compare: {k: {atol: 1.0e-06}}
  # the rounded n_w: 427 / 85 (the example of skellytracker 0023)
  - id: factor-letterbox-rounded
    function: depth_scale_factor
    params: {resize_method: letterbox}
    input: {inverse: {src_w: 427, n_w: 85}}
    expect: {k: 5.023529411765}
    compare: {k: {atol: 1.0e-06}}
  # src_w / T_w = 1000 / 640; the y scale does not matter
  - id: factor-stretch
    function: depth_scale_factor
    params: {resize_method: stretch}
    input: {inverse: {src_w: 1000, target_w: 640}}
    expect: {k: 1.5625}
    compare: {k: {atol: 1.0e-06}}
  # 1 / s with the unrounded s
  - id: factor-fit
    function: depth_scale_factor
    params: {resize_method: fit}
    input: {inverse: {s: 0.25}}
    expect: {k: 4.0}
    compare: {k: {atol: 1.0e-06}}
  # identity
  - id: factor-none
    function: depth_scale_factor
    params: {resize_method: none}
    input: {inverse: {}}
    expect: {k: 1.0}
    compare: {k: {atol: 1.0e-06}}
  # w / T_w after expand_ratio and the aspect step: 288 / 192
  - id: factor-affine-person-crop
    function: depth_scale_factor
    params: {resize_method: affine_person_crop}
    input: {inverse: {crop_w: 288, target_w: 192}}
    expect: {k: 1.5}
    compare: {k: {atol: 1.0e-06}}
  # wc / T_w = 448 / 224; the rotation does not change k
  - id: factor-rotated-roi-crop
    function: depth_scale_factor
    params: {resize_method: rotated_roi_crop}
    input: {inverse: {crop_roi: [300.0, 200.0, 448.0, 448.0, 0.5], target_w: 224}}
    expect: {k: 2.0}
    compare: {k: {atol: 1.0e-06}}
  # wc / T_w, not hc / T_h, for a non-square crop ROI
  - id: factor-rotated-roi-crop-non-square
    function: depth_scale_factor
    params: {resize_method: rotated_roi_crop}
    input: {inverse: {crop_roi: [300.0, 200.0, 300.0, 150.0, 1.0], target_w: 224}}
    expect: {k: 1.339285714286}
    compare: {k: {atol: 1.0e-06}}
  # an unknown resize method
  - id: error-factor-method
    function: depth_scale_factor
    params: {resize_method: warp}
    input: {inverse: {}}
    expect: {error: unknown resize method warp}
  # the crop ROI must have five values
  - id: error-factor-roi
    function: depth_scale_factor
    params: {resize_method: rotated_roi_crop}
    input: {inverse: {crop_roi: [300.0, 200.0, 448.0, 448.0], target_w: 224}}
    expect: {error: 'rotated_roi_crop needs the crop ROI (cx, cy, wc, hc, rotation)'}
  # k must be > 0
  - id: error-factor-zero
    function: depth_scale_factor
    params: {resize_method: affine_person_crop}
    input: {inverse: {crop_w: 0, target_w: 192}}
    expect: {error: the depth factor must be a finite number > 0}
  # z_src = z_in * k
  - id: unproject-depth
    function: unproject_depth
    params: {k: 2.0}
    input: {z_model: [-25.0, 0.0, 10.0]}
    expect: {z: [-50.0, 0.0, 20.0]}
    compare: {z: {atol: 0.0001}}
  # MediaPipe hand: -10 / 0.4 * 448 / 224 = -50
  - id: decode-hand
    function: decode_depth
    params: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: pixel, depth_normalize: 0.4}, target_hw: [224, 224], resize_method: rotated_roi_crop}
    input: {z_raw: [-10.0, 0.0, 4.0], inverse: {crop_roi: [300.0, 200.0, 448.0, 448.0, 0.5], target_w: 224}}
    expect: {z: [-50.0, 0.0, 20.0]}
    compare: {z: {atol: 0.0001}}
  # z_raw / 224 / 0.4 * roi_size (docs/mediapipe-whole-body.md:405-406), roi 150
  - id: decode-hand-mediapipe-form
    function: decode_depth
    params: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: pixel, depth_normalize: 0.4}, target_hw: [224, 224], resize_method: rotated_roi_crop}
    input: {z_raw: [-10.0, 7.5], inverse: {crop_roi: [50.0, 60.0, 150.0, 150.0, -2.0], target_w: 224}}
    expect: {z: [-16.741071428571, 12.555803571429]}
    compare: {z: {atol: 0.0001}}
  # the near-miss: no depth_normalize gives 2.5 times less
  - id: decode-no-divisor
    function: decode_depth
    params: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: pixel}, target_hw: [224, 224], resize_method: rotated_roi_crop}
    input: {z_raw: [-10.0, 0.0, 4.0], inverse: {crop_roi: [300.0, 200.0, 448.0, 448.0, 0.5], target_w: 224}}
    expect: {z: [-20.0, 0.0, 8.0]}
    compare: {z: {atol: 0.0001}}
  # normalized_01 and letterbox: 0.1 * 640 / 1 * 1920 / 640 = 192
  - id: decode-letterbox-normalized
    function: decode_depth
    params: {decode: {method: coordinate, coordinate_scale: normalized_01, is_3d: true, depth_unit: pixel}, target_hw: [640, 640], resize_method: letterbox}
    input: {z_raw: [0.1], inverse: {src_w: 1920, n_w: 640}}
    expect: {z: [192.0]}
    compare: {z: {atol: 0.0001}}
  # the depth rule needs depth_unit pixel
  - id: error-decode-metric
    function: decode_depth
    params: {decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: m}, target_hw: [224, 224], resize_method: rotated_roi_crop}
    input: {z_raw: [1.0], inverse: {crop_roi: [300.0, 200.0, 448.0, 448.0, 0.5], target_w: 224}}
    expect: {error: 'the depth rule needs method coordinate, is_3d true and depth_unit pixel'}
```

## 5. Parity evidence

One parity script serves the four MediaPipe proposals (user decision plan T28 (H6),
`specs/exporter-guide/sidecars/workflow/phase-2-proposal.md:24-26`): `notes/decisions/scripts/hand_chain_parity.py`
(to write). The extra-outputs proposal, part 5, describes its outputs part. This proposal adds the depth gate. Each proposal keeps its gates.

| Item | Value |
|---|---|
| Gates, set before the run, and their source | Set on 2026-10-24, before the run of the committed parity script. The scratch measurement of part 1 ran before these gates were set. Its numbers are the source of the gates, as in the 0020 proposal (part 5, gate (3): 1.1 times the measured value, rounded up to 0.01 px; a count of outliers). **Depth**, for each hand that both give: the largest `|z_src − z_mp · W|` over the 21 points, in source pixels. Image set: median `<= 0.24` px, p95 `<= 1.05` px, 0 hands above 10 % of the ROI size. Video set: median `<= 0.17` px, p95 `<= 1.16` px, 0 hand-frames above 10 % of the ROI size. Measured: image median 0.216, p95 0.954, largest 1.6 % of the ROI; video median 0.154, p95 1.051, largest 6.5 % of the ROI. **Control** (not a gate): the same chain with `depth_normalize: 1.0` must fail the depth gate (measured image median 13.4 px), and the median of `z_mp · W / z_src(1.0)` must be in `[2.45, 2.55]` (measured 2.504 and 2.499). The `x`, `y` gate and the presence gate are gate (3) of the 0020 proposal and gate (1) of the extra-outputs proposal. |
| Test images (paths or dataset IDs), and the branch that each image runs | The sets of MediaPipe-Exporter 0006 (`notes/decisions/0006-holistic-end-to-end-parity.md:31-35`): 60 COCO val2017 images (IMAGE mode) and 300 frames of `sesh_2022-09-19_16_16_50_in_class_jsm_synced_Cam1.mp4` (VIDEO mode). Branches that run: `coordinate_scale: pixel`, `depth_normalize: 0.4`, `rotated_roi_crop` with square ROIs of many sizes (`k` from small to large) and both signs of `z`. Not run on a real image: `normalized_01`, `normalized_11`, the five other resize methods, a non-square crop ROI. The vectors cover these branches. |
| Upstream reference: library, version, config and command | `mediapipe` 1.1.1, `HolisticLandmarker` with `holistic_landmarker.task` `float16/1` (MediaPipe-Exporter 0016). The `z` of its hand landmarks. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | to run (MediaPipe-Exporter 0003 gives 2.5e-4 px for the landmarks of `full`, from an uncommitted probe; it does not give `z` alone) |
| Preprocessed input: maximum absolute difference for each image | to run. The input crop is the scope of the 0020 proposal (its part 5, gate (1)). |
| Row count for each image: sidecar path and upstream | to run. The presence gate of the extra-outputs proposal. |
| Final outputs in source-image coordinates: metric and value for each role | to run. `pose_estimator`: the depth in source pixels (the gate above). Scratch (secondary): the values in the gates row. |
| Result (`pass`, `fail` or `to run`) | to run (MediaPipe-Exporter has no git repo, so a script cannot be committed) |
| Script path in the exporter repo | `notes/decisions/scripts/hand_chain_parity.py` (to write; user decision plan T28 (H6): the script of the four MediaPipe proposals, named also in part 5 of the 0020, refiner and extra-outputs proposals). It applies `decode_depth` of this reference file with the crop ROI `Rc` of the 0020 reference file. It writes `model_cache/probes/hand_chain_parity.json`. |
| Exporter commit of the script | none (no git repo) |
| Command | `uv run --script notes/decisions/scripts/hand_chain_parity.py --n-images 60 --n-frames 300` (to run) |

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | New module `skellytracker/core/detectors/processing/coordinate_decode.py` with the functions of the reference file: `split_single_person`, `depth_to_model_pixels`, `depth_scale_factor`, `unproject_depth` and `decode_depth`. |
| Dispatch point | For the implementer. The `coordinate` decode has no package code today (`specs/model-sidecar/post/pose-decode-coordinate.md:12`: `decode: missing`). The decode must call `decode_depth` for each `z` when `is_3d` is true and `depth_unit` is `pixel`, with the `resize_meta` of the resize method: the rounded `n_w` (letterbox), the scale `s` (fit), the crop width `w` (affine crop) or the crop ROI `Rc` (the 0020 proposal, part 6). `preprocess_image` (`skellytracker/core/detectors/processing/image_preprocessing.py:158-244`) returns `(tensor, resize_meta)`, and `resize_meta` depends on the method (`:174, 191`). The `stretch` branch returns `resize_meta = 1.0` today (`:206-210`), so it needs `src_w / T_w` too. The `affine_person_crop` branch returns `(center, scale)` (`:233`); the implementer derives the crop width `w` from it. |
| Validator changes (`model.py`, with rule IDs) | `PoseDecodeSpec` (`skellytracker/core/sidecar/model.py:259-279`): add `depth_normalize: float \| None = None`. `_check_decode`: reject it unless `method == "coordinate"`, `is_3d` and `depth_unit == "pixel"`; require a finite number `> 0` (`V-post.pose.decode.coordinate-2`). Reject `depth_unit == "pixel"` with a method other than `coordinate` at `schema_version >= vNEXT` (changed `V-post.pose.schema-9`); this check needs the version, so it goes in a `SidecarModel` validator. |
| Tests | The vectors `specs/model-sidecar/vectors/post.pose.decode.coordinate.yaml` against `coordinate_decode.py`; the runner compares each field with the `atol` of its `compare`. Validation tests in `skellytracker/tests/sidecar/test_model_validation.py` next to `test_is_3d_requires_depth_unit` (`:231`). A golden parity test: one hand crop, the 21 `z` values of the ONNX model after the rule, in source pixels. |
| Existing code that the change touches | `skellytracker/core/sidecar/model.py`: `PoseDecodeSpec` (`:259-279`). `skellytracker/core/detectors/processing/simcc_decode.py:127-128`: `is_3d` raises `NotImplementedError` today; no change. `skellytracker/core/data_primitives/keypoints.py:19-20`: `xyz` is `(N, 3)` with "z filled by triangulation". A monocular depth of one camera needs a separate place, or a rule that keeps it apart from the triangulated `z` (for the implementer). |

## 7. Exporter impact

| Exporter | Affected sidecars | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | none (no 3D model) | none | none |
| Roboflow-Exporter | none | none | none |
| Ultralytics-Exporter | none (the YOLO26-pose keypoints are 2D with a score) | none | none |
| Qualcomm-Exporter | The historical MediaPipe hand and face landmark sidecars (`depth_unit: pixel`; the wrapper multiplies `(x, y, z)` by `(W, H, W)`, skellytracker 0022 `:41-43`) | Out of the `vNEXT` scope (skellytracker 0008 `:15`). If it writes the sidecars again, it declares the `depth_normalize` that its graph needs. This proposal did not read its graph, so it does not know if its `z` keeps the MediaPipe divisor. | none (no host decoder today) |
| MediaPipe-Exporter (proposing) | The hand landmark sidecar (`full`, `lite`) | New field: `depth_normalize: 0.4` (the YAML excerpt of part 2.2). The plan has the same value (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts), secondary). A later face or pose landmark sidecar has no `depth_normalize` (the graphs do not set `normalize_z`, `docs/mediapipe-whole-body.md:142-143`). | The host depth is `decode_depth` of the reference file, with the crop ROI `Rc` of the 0020 reference file. The probe geometry `hand_roi_reference.py:165-168` (no commit) uses the same formula for a square ROI. |
| skellytracker package sidecars | none | none. No package sidecar declares `is_3d`. | none |
| skellytracker spec examples | none | none. No example declares `is_3d`. | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| **The near-miss: `depth_unit: pixel` with no divisor** (the current field) | The depth is 2.5 times too small: on the sets of MediaPipe-Exporter 0006 the depth error is a median of 13.4 px (image) and 8.8 px (video), against 0.216 px and 0.154 px with the divisor. The text also does not say which width scales the depth. | Part 1, measured difference |
| **Scale `z` in an exporter wrapper** (the historical Qualcomm-Exporter approach) | Each exporter can choose a different scale, and the sidecar does not show which one (skellytracker 0022 `:47-48`). It also changes the graph that the upstream gives. | skellytracker 0022 `:30-31, 47-48` |
| **A multiplier `depth_scale` in place of a divisor** | The two forms are equivalent. The divisor has the upstream name and value (`normalize_z: 0.4`), so an exporter copies it without a calculation. It is the name of the gap record (skellytracker 0022 `:13`). | `tensors_to_landmarks_calculator.proto:55-58` |
| **A new `depth_unit` value** (for example `pixel_normalized`) | One value for each divisor does not scale. The unit is the same (the scale of `x`); only the divisor differs. | — |
| **`depth_normalize` required, with no default** | MediaPipe has the default 1.0, and its pose and face graphs do not set the option (`docs/mediapipe-whole-body.md:141-143`). A default 1.0 gives their sidecars the right value with no field, and the gap record asks for it (skellytracker 0022 `:14-15`). | `.proto:58` |
| **Report the depth in model-input pixels only** (no unprojection) | The `x` and `y` of the keypoints are in source pixels after the unprojection. A depth in another scale cannot be combined with them. The gap record asks for the unprojection (skellytracker 0022 `:15-16`). | skellytracker 0022 `:15-16` |
| **Scale the depth with the factor of `y`, or with the mean of the two factors** | MediaPipe scales `z` as `x` ("Scale Z coordinate as X"), with the rect width or with the length of the projected unit `x` segment. For a square crop the three are the same. For `stretch` or a non-square crop they differ, and only the `x` factor follows the upstream. | `landmark_projection_calculator.cc:47-66, 95-96`; `.proto:36-40` |
| **The `NORM_RECT` width of MediaPipe (the ROI before the aspect step) for `rotated_roi_crop`** | The 0020 proposal uses the exact inverse with `Rc` (its user decision T23, Q6). `k` must use the same `Rc`, so that `z` and `x` have one scale. For every hand ROI in scope the two are the same. | 0020 proposal, heading "Inverse" and part 7 |
| **Put the depth rule into `post.unprojection`** | The divisor is a field of the `coordinate` decode, and the depth exists only for that method at `vNEXT` (changed `V-post.pose.schema-9`). One heading keeps the decode and the unprojection of the depth in one place, with one reference module. `post.unprojection` gets one sentence with a link. | `specs/exporter-guide/sidecars/reference-implementations.md:30-32` (a section and its inverse in one module) |
| **Reject a `pixel` depth with `coordinate_scale: normalized_11`** | Not needed. The factor `T_w / 2` with no offset gives the scale of `x`. Rejected by user decision plan T28 (H8), Q3. | Part 2.3, step 1 |
| **Allow `depth_unit: pixel` for `simcc`** (keep `V-post.pose.schema-9` as it is) | No `simcc` model in scope has a `pixel` depth, and the `simcc` depth uses `depth_range`. The heading "Depth" would need a rule for it with no evidence. Rejected by user decision plan T28 (H7), Q2. | `post/pose-decode-simcc.md:32, 46` |

## Open questions for the user

Decided by the user on 2026-10-24 (plan T28). No question of this proposal stays open.

- **Q1 (the revision) = H2.** The change goes into `vNEXT`, on the scope extension of the 0020
  proposal (user decision 2026-10-23 (4)). Skellytracker 0022 asks for this decision (`:18-20`). Parts 1 and 2.6.
- **Q2 (`pixel` only with `coordinate`) = H7.** At `vNEXT`, `depth_unit: pixel` is valid only with
  `method: coordinate` (changed `V-post.pose.schema-9`, part 2.4). No sidecar uses `pixel` today.
- **Q3 (`normalized_11`) = H8.** For a depth of a `normalized_11` model, the factor is `T_w / 2`, with
  no offset (part 2.3, step 1). The rule does not reject that case. No model in scope uses it.
- **H6 (the parity script).** One script serves the four MediaPipe proposals:
  `notes/decisions/scripts/hand_chain_parity.py` (part 5). This proposal keeps its depth gate.

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake links to this proposal (row K4, and "Proposals and reference files", 2026-10-24).
- [x] The header gives the dependencies (the 0020 proposal) and `Needed by: none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property
      (skellytracker 0022; also skellytracker 0020 and 0021). This proposal builds on skellytracker
      0022. It does not compete with it.
- [x] Part 1 cites primary evidence (`docs/mediapipe-whole-body.md`, user designation, and the
      MediaPipe source), and it names the primary evidence that is missing (the exporter export, the
      letterbox removal of MediaPipe).
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the untracked plans of MediaPipe-Exporter (plan facts).
- [x] Part 4 gives `unverified: no host implementation`.
- [x] Each pixel case in part 4 has its tolerance in `compare` (`z`: `1e-4` px).
- [x] Part 5 says `to run` and describes the script and its gates.
- [x] n/a: the result of part 5 is `to run`, so no script needs a commit.
- [x] No file in skellytracker changed. No file in OpenMMLab-Exporter changed.
- [x] Mutation check (2026-10-24): one expected value changed in a copy of this file
      (`decode-hand`: the depth `-50.0` to `-49.0`). The scratch runner gave 46 of 47 pass, with the
      one failure `decode-hand`. Run again after the edits of plan T28: 47 of 47 pass, and the same
      mutation gave 46 of 47 with the one failure `decode-hand`.
- [x] The user decisions of plan T28 (H2, H6, H7, H8) are applied in parts 1, 2.3, 2.4, 2.6, 5 and 8
      and in "Open questions for the user".
- [x] No private data in the text of the proposed spec change. The scratch paths in parts 1 and 4
      are local notes of this exporter, not spec text. A skellytracker session must not copy them
      into a decision entry.

A proposal with `to run` in part 5 is ready for a skellytracker session to record. It is not ready
for the user to accept. It stays incomplete until part 5 has the numbers, the script and the commit.

## Before acceptance

The user cannot accept this proposal until this work is done.

**Parts**

- [ ] Part 5 is `to run`. MediaPipe-Exporter must write the parity script
  `notes/decisions/scripts/hand_chain_parity.py`, run it on the image set and the video set of
  MediaPipe-Exporter 0006, and record the result against the gates of part 5. The one script serves
  the four MediaPipe-Exporter proposals.
- [ ] MediaPipe-Exporter has no git repo. Thus the parity script, the reference file and the
  exporter decisions have no commit. A commit must exist before the user can accept the proposal.
- [ ] Part 2.1 does not list the front matter `status` of `specs/model-sidecar/post/pose-decode-coordinate.md`.
  It says `validate: implemented`. `PoseDecodeSpec` rejects `depth_normalize` as an unknown field. It
  does not check `V-post.pose.decode.coordinate-2` or the `vNEXT` sentence of `V-post.pose.schema-9`.
  The content PR must set `validate: partial` and add a comment. The validate column of
  `specs/model-sidecar/TRACEABILITY.md` then also changes.
- [ ] Part 2.1 does not list the comment on `implemented_by.validate` in the front matter of
  `specs/model-sidecar/post/pose-schema.md`. The comment must say that the version check of
  `depth_unit: pixel` is not implemented.
- [ ] Part 2.5 applies the heading "Depth" to the bottom-up forms. Part 2.1 gives no edit and no link
  in `specs/model-sidecar/post/pose-bottom-up.md`. Add the edit, or record why none is necessary.
- [ ] Part 1 (the row of "Considered and deliberately not added") says that the
  `roi-transform-and-source` proposal adds the `vNEXT` scope "with a new entry" (user decision
  2026-10-23 (4)). The answer Q1 cites the same old decision. The scope change is now the scope entry
  0048 (`vnext-scope-mediapipe-rotated-crops`), which supersedes 0008 in full. The exporter must
  update this text.
- [ ] The header row "Depends on" names only the `roi-transform-and-source` proposal (0020). It must
  also name the scope entry 0048. The `vNEXT` decision (H2) needs that entry.
- [ ] The header says that part 8 gives each difference from the direction of 0022. Part 8 does not
  give two differences. (1) The field is a method-specific field of `post.pose.decode.coordinate`.
  0022 points it at `pose.decode` in `post.pose.schema`. (2) The factor `c` changes
  `z = z_raw / depth_normalize` for the normalized scales. The exporter must add these to part 8.

**Evidence**

- [ ] The measured numbers of part 1 (for example the depth error median 0.216 px with the divisor
  and 13.4 px without it) and the gates of part 5 come from an uncommitted scratch script. They are
  not evidence. The committed parity script must give them again.
- [ ] Missing primary evidence: the exporter export (the probe file is `[1, 63]`; the plan reshapes
  it to `[B, 21, 3]`), the source of `LandmarkLetterboxRemovalCalculator` for
  `maintain_aspect_ratio: true` with a non-square ROI, and the ONNX export error of `z` alone.
- [ ] No host implementation exists. The vectors stay `unverified`.
- [ ] The effect on Qualcomm-Exporter is not known. The proposal did not read its graph. Thus it does
  not know if its `z` keeps the divisor `0.4`.
- [ ] `docs/mediapipe-whole-body.md:404` says that the hand landmark model is `full` only. The
  proposal also claims `lite`, with only intake row F4 as the source. Give primary evidence for
  `lite`, or remove `lite`.
- [ ] "No `depth_normalize`" for the face landmark model has only `docs/mediapipe-whole-body.md:142-143`
  as its source. Check it in the MediaPipe source. The claim for the pose graph is checked
  (`pose_landmarks_detector_graph.cc:150-152` and `:411-413`).
- [ ] The MediaPipe source lines are at commit `e9794ef55e2509c09aa8b6ba1764b797db8eb200`. Make sure
  that this commit is on the default branch of the MediaPipe repo. Then cite the lines with
  permalinks.
- [ ] The docstrings of the reference file give no exporter commit (skill `change-sidecar-spec`,
  Procedure C step 3). This needs a git repo in MediaPipe-Exporter.

**Template checklist**

- [ ] "Part 2.1 lists each place that the change edits" is ticked. The places of **Parts** above are
  not in part 2.1.
- [ ] "Part 4 gives `unverified: no host implementation`" is ticked. The YAML of part 4 cannot land
  in the form of the template (see **Vectors and tooling**).
- [ ] The closing text of "Before you stop" says that the proposal stays incomplete until part 5 has
  the numbers, the script and the commit. This is not done.

**Vectors and tooling**

- [ ] The YAML of part 4 uses the form of the template: `function`, `compare`, `generated_by` set to
  the reference file, and error results. `tools/tests/test_vectors.py` rejects this form. `CASE_KEYS`
  has no `function` and no `compare`. `generated_by` must be `tools/make_vectors.py`. A case has
  `tolerance` only when it has a fraction. A file must be smaller than 16 KiB. One `tolerance`
  cannot hold the two tolerances (`1e-4` px for `z`, `1e-6` for `k`). Only the key `function` selects
  one of the six functions. One non-spec tools PR must decide the form for all proposals.
- [ ] Part 2.1 gives the builder in `tools/make_vectors.py` and the test in `tools/tests/` as an
  option "for the implementer". The skill `change-sidecar-spec` requires both. It also does not
  allow a vector file that is edited by hand. Thus the option "commits the YAML of part 4" is not
  available.
- [ ] `specs/model-sidecar/reference/` does not exist. Decide how `tools/make_vectors.py` and the tests
  import a file from it. When the folder exists, the lint CI also checks it.
- [ ] The comment of the vector `error-divisor-legacy` names rule `-2`. Rule `-2` is marked
  **(vNEXT)**. At a legacy version, the legacy row of `format.versioning` rejects the field. The
  comment names the wrong owner.

**Decisions for the user**

- [ ] The user decisions H2, H6, H7 and H8 (plan T28) are only in the untracked pose-models plan of
  OpenMMLab-Exporter (plan facts). The designation of `docs/mediapipe-whole-body.md` as primary
  evidence (2026-10-23), and Q7 = (c) and T23 of the `roi-transform-and-source` proposal, are only in
  untracked MediaPipe-Exporter plans. Confirm these decisions, so that a tracked file can record them.
- [ ] Accept `docs/mediapipe-whole-body.md` as primary evidence, or not. The exporter guide classes
  an exporter document as secondary evidence.
- [ ] The single-person form (`post/pose-decode-coordinate.md:33`): the `keypoint-visibility` proposal
  (0039) replaces it with `(N, K, C)`. This proposal edits the old text. Its `split_single_person`
  and its vectors accept only `(N, K, 2)` and `(N, K, 3)`. Decide which form is normative.
- [ ] The legacy rejection policy: this proposal rejects `depth_normalize` below `vNEXT` only with the
  legacy row of `format.versioning`. Other proposals add a rule for it. Decide one policy for all
  proposals.
- [ ] The index "Version-aware compatibility": this proposal adds no link for its new heading "Legacy
  behaviour", as `pre/resize-fit.md` and `pre/resize-stretch.md` do. The skill `change-sidecar-spec`
  requires the link. Decide one rule for all proposals.
- [ ] The scope of the reference module: the file also checks `V-post.pose.schema-9` and the method
  enum of `post.pose.schema`, and it applies the legacy row of `format.versioning`. It also holds
  the inverse factors of six resize sections. The exporter guide puts one section in one module.
  Accept this scope, or not.
- [ ] 0022 waits for the `roi-transform-and-source` proposal (0020), for the scope entry 0048 and for
  MediaPipe-Exporter commits that do not exist yet. Decide if 0022 gets a `**Depends on:**` line.
- [ ] Part 5 names the video `sesh_2022-09-19_16_16_50_in_class_jsm_synced_Cam1.mp4`. The file is in
  the public skellysamples test recording that `skellytracker/tests/conftest.py` downloads. Decide if
  a tracked file can name it.

**Merge points**

- [ ] The `roi-transform-and-source` proposal (0020) and the scope entry 0048 must land first. The
  heading "Depth" names `rotated_roi_crop` and "Rotated ROI crop, step 3". The factor `k = wc / T_w`
  uses its crop ROI `Rc`.
- [ ] The header does not name gap record 0023 (letterbox floor and scale inverse). If 0023 adds a
  letterbox inverse with the unrounded scale, the `letterbox` row of `k` and the vector
  `factor-letterbox-rounded` change. Add 0023 to the merge points, or record why not.
- [ ] Other proposals edit the same text. The content PR that lands second rebases on the first and
  keeps the edits of both. The places: `format/versioning.md:74`; `post/pose-schema.md:89-95` and
  `:117-127`; `post/pose-decode-coordinate.md:33` and `:55-56`; `post/unprojection.md:21-36`;
  `templates/model-intake.md:300` and `:314`; `changelog.md:55-59`, the summary row and the `vNEXT`
  row. The header row "Related, not a dependency" names the proposals for each place:
  `pose-decode-flip-test` (0045), `heatmap-decode-refinement` (0038), `keypoint-visibility` (0039),
  `roi-transform-and-source` (0020), `roi-refiner-role` (0047), `landmark-extra-outputs` (0021),
  `simcc-score-rule` (0024), `normalize-arithmetic` (0043), `affine-crop-arithmetic` (0037) and
  `model-id-suffix` (0025).

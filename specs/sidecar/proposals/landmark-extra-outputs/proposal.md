---
slug: landmark-extra-outputs
section: post.pose.extra_outputs
exporter: MediaPipe-Exporter
decision: "0021"
state: recorded
---
# Change proposal: landmark-extra-outputs

This file is informative. It is not part of the normative spec until a content PR lands its text in the section files (decision [faac](../../../../notes/decisions/faac-proposal-records.md)).

**Source.** The MediaPipe-Exporter file of the proposal `landmark-extra-outputs`, in its version of 2026-10-25 16:49, and its reference file, which is the `python` code block of part 3. Both files are in the git-ignored `plans/` folder of MediaPipe-Exporter, so they have no commit. The MediaPipe-Exporter repo is at commit `8f708a1ddecd8e035de15a5a9a7b652af035a58a` on `main`; its tracked files (for example `docs/mediapipe-whole-body.md`) are at that commit. The exporter file still gives `none (no git repo)`. First copied on 2026-10-25. Copied again on 2026-10-25 (decision [vac0](../../../../notes/decisions/vac0-record-a-changed-proposal.md)). The reference file did not change after the first copy. The copy changes only the items of decision faac, item 3. The session wrote no part.

This file uses ASD-STE100 Simplified Technical English. It is a local working note of
MediaPipe-Exporter (decision 0001). Git does not track it. It is the full phase 2 proposal of the
skellytracker gap record 0021. It gives the eight parts that skellytracker 0021 does not have.

Labels in this file:

- **User decision (2026-10-23)** and **user decision (2026-10-24)** mark a decision of the user. "Plan
  T<n>" is a user decision in section 2.1 of the untracked pose-models plan of OpenMMLab-Exporter (plan facts)
  (secondary). Do not change a user decision without the user.
- **Proposal choice** marks a choice of this proposal. On 2026-10-24 the user decided the five open
  questions (plan T28: H2 to H6). "Open questions for the user" lists each decision.
- "The 0020 proposal" is `specs/sidecar/proposals/roi-transform-and-source/proposal.md`. "The refiner proposal"
  is `specs/sidecar/proposals/roi-refiner-role/proposal.md`. "The depth proposal" is
  `specs/sidecar/proposals/landmark-depth-divisor/proposal.md`. "The intake" is
  the untracked intake of `mediapipe-hand21` of MediaPipe-Exporter (plan facts).
- "MediaPipe source" means the cached copies of MediaPipe commit
  `e9794ef55e2509c09aa8b6ba1764b797db8eb200` in
  `model_cache/sources/e9794ef55e2509c09aa8b6ba1764b797db8eb200/` (the pin of MediaPipe-Exporter
  0002). Paths are relative to that folder.

Line numbers of skellytracker files are at commit `dom/21-move-sidecar-guide` (the line
numbers are the same as at `dom/18-agents-adr-bootstrap-kit`, the earlier pin). Line
numbers of `docs/mediapipe-whole-body.md` are in MediaPipe-Exporter on 2026-10-24.

## Header

| Field | Value |
|---|---|
| Title | Extra outputs of a single-person `coordinate` pose model: an instance presence score with a runtime gate, a binary class probability, and world keypoints |
| Slug | `landmark-extra-outputs`. This is the slug of the skellytracker gap record 0021 (`notes/decisions/0021-landmark-extra-outputs.md`; index row at `notes/decisions/README.md:40`). The exporter guide says: use the slug of a `proposed` entry that covers your rows (`specs/exporter-guide/sidecars/workflow/phase-2-proposal.md:13-20`). One entry covers the three rows D1b, D1c and D1d, so one proposal covers them. |
| Date | 2026-10-24; updated 2026-10-24 (user decisions plan T28: H2, H3, H4, H5, H6); updated 2026-10-24 (the committed evidence of H3: OpenMMLab-Exporter 0041); updated 2026-10-25 (0041 is on `main` and on the remote; pin `dom/21-move-sidecar-guide`; the legacy MediaPipe documentation sentence on a mirrored input; repo names on decision numbers); updated 2026-10-25 (OpenMMLab-Exporter 0052: the upstream `HandLandmarker` run and the two label maps; the labels come from the inference graph, not the model metadata; user decision OpenMMLab-Exporter plan T45) |
| Exporter repo | MediaPipe-Exporter |
| Exporter commit | none (no git repo) |
| Model, and its intake file | The hand landmark model of the MediaPipe Holistic hand branch, `hand_landmark_full` (size `full`; the size `lite` has the same four outputs, intake row F4). `model_id` `mediapipe-hand21` (plan T14). ONNX probe file `model_cache/onnx/hand_landmark_full.onnx` (sha256 `5c7c9fcbba12039ef6a28f676272b5fbfc19693c12f099722a44554fb2623c17`). Intake: the untracked intake of `mediapipe-hand21` of MediaPipe-Exporter (plan facts) (2026-10-24). |
| Intake rows with the verdict `near-miss` or `gap` | D1b the hand flag `Identity_1` and its gate `> 0.5` (`gap`); D1c the handedness `Identity_2` (`gap`); D1d the world landmarks `Identity_3` (`gap`). The graph rows G5b, G5c and G5d (`unverified`, the exporter export does not exist) give the names, dtypes and shapes of the same outputs. This proposal gives their semantic. Also the untracked intake of `mediapipe-pose39` of MediaPipe-Exporter (plan facts) (2026-10-24; deferred: the untracked blazepose plan of MediaPipe-Exporter (plan facts), BlazePose): D1b the pose flag `[1, 1]` (`gap`; the sigmoid is in the graph; the upstream graph accepts a threshold in `[0, 1]`, and this proposal allows `[0, 1)`) and D1e the world landmarks `[1, 117]` (`gap`). |
| Kind | `new section`, with edits to `common.outputs` (the closed `semantic` set and its rule), `post.pose.schema` (rule `V-post.pose.schema-7`, the pose output fields), `post.pose.decode.coordinate` (the single-person form), `format.versioning`, the section map, the changelog and the model intake template |
| Proposed section ID | `post.pose.extra_outputs` (proposal choice) |
| Section file | `specs/sidecar/post/pose-extra-outputs.md` |
| Depends on | `specs/sidecar/proposals/roi-transform-and-source/proposal.md` (the full proposal of skellytracker 0020). Behaviour step 4 rotates the world keypoints by the rotation of its crop ROI `Rc` for `rotated_roi_crop`. The 0020 proposal lands first (user decision 2026-10-23 (3) for the refiner; this proposal follows the same order). Without it, every resize method has the rotation 0, and step 4 does not change the world keypoints. |
| Needed by | none |
| Related, not a dependency | The depth proposal (`landmark-depth-divisor`, skellytracker 0022): the same model, the `z` of the `keypoints` output. The refiner proposal: its `roi_source.score_gate` has the same runtime-threshold pattern (plan T26 (6)); this proposal uses the same field name `score_threshold_default` and the same range `[0, 1)`. The OpenMMLab-Exporter proposal `keypoint-visibility` (in progress; section `post.pose.visibility`, reference file: the part 3 code of `specs/sidecar/proposals/keypoint-visibility/proposal.md`): a per-point visibility value. The presence score of this proposal is one value for each instance, not for each point. Thus the two proposals do not overlap. **Related (merge points; review-readiness audit 2, 2026-10-24).** Other proposals edit the same spec text as this proposal. The content PR that lands second rebases on the first and keeps the edits of both. Line numbers are at skellytracker `dom/21-move-sidecar-guide` (the same as at `dom/18-agents-adr-bootstrap-kit`), as in the rest of this file. Each cited spec line is the same at `dom/21-move-sidecar-guide` (checked 2026-10-25): under `specs/sidecar/` only link text changed after `dom/18-agents-adr-bootstrap-kit`, and the guide moved to `specs/exporter-guide/sidecars/` with no change of text (skellytracker 0034). (History: an earlier check at `dom/12-single-working-branch` found, in the cited files, only one line less in the old `specs/sidecar/exporter-guide.md` after line 445, and this row cites no line there.) `common/outputs.md:29, 35, 44` (the closed `semantic` set, the routing paragraph, `V-common.outputs-4`): `roi-refiner-role`; `format/versioning.md:74` (the legacy row "Not available."): `pose-decode-flip-test` (OpenMMLab-Exporter), `heatmap-decode-refinement` (OpenMMLab-Exporter), `keypoint-visibility` (OpenMMLab-Exporter), `roi-transform-and-source`, `roi-refiner-role`, `landmark-depth-divisor`; `post/pose-schema.md:117-127` ("Validation rules": `-1` and `-2` owned by `roi-transform-and-source`, `-7`, `-9`, the "See also" line): `roi-transform-and-source`, `landmark-depth-divisor`, `pose-decode-flip-test` (OpenMMLab-Exporter), `keypoint-visibility` (OpenMMLab-Exporter); `post/pose-schema.md:137-144` ("Authoring guidance"): `roi-transform-and-source`; `post/pose-decode-coordinate.md:33` (the single-person form): `keypoint-visibility` (OpenMMLab-Exporter), `landmark-depth-divisor`; `specs/sidecar/README.md` (the section-map row and the validation-index link after "Coordinate decode", `:93`, `:121`): `pose-decode-flip-test` (OpenMMLab-Exporter), `keypoint-visibility` (OpenMMLab-Exporter); `exporter-guide/sidecars/workflow/mapping-hints.md:55-65` ("Mapping hints", Outputs and decode, Pose): `nms-clamp-order` (OpenMMLab-Exporter), `keypoint-visibility` (OpenMMLab-Exporter); `templates/model-intake.md:290` (row D1): `roi-refiner-role`; `templates/model-intake.md:318` (row K8 and the new row K8a after it): `keypoint-visibility` (OpenMMLab-Exporter); `inventory.yaml:98-129` (the `proposed` entries): `model-id-suffix` (OpenMMLab-Exporter), `roi-transform-and-source`, `roi-refiner-role`; `changelog.md:55-59` ("Compatibility impact"): `simcc-score-rule` (OpenMMLab-Exporter), `heatmap-decode-refinement` (OpenMMLab-Exporter), `normalize-arithmetic` (OpenMMLab-Exporter), `affine-crop-arithmetic` (OpenMMLab-Exporter), `model-id-suffix` (OpenMMLab-Exporter), `roi-transform-and-source`, `landmark-depth-divisor`. All 13 proposals add a row to "Summary of changes" (row `N`, the next free number at merge time) and a sentence to the `vNEXT` row of the `schema_version` history (`changelog.md:68`). |
| skellytracker decision entries with the status `proposed` that cover the same property | **skellytracker 0021** (gap record, `0021-landmark-extra-outputs.md:8-9`). This file is its full proposal. Part 8 says where it differs from the direction of skellytracker 0021 (`:11-24`), with the reasons. **skellytracker 0020** (gap record; full proposal: the 0020 proposal): the crop ROI and its rotation. **skellytracker 0022** (gap record; full proposal: the depth proposal): the depth of the `keypoints` output. **skellytracker 0019** (proposed): the batch axis of `outputs[].shape`. The shapes of this proposal write `-1` for the batch axis, as the spec examples do. |
| Evidence basis | **User decision (2026-10-23): the user designated `docs/mediapipe-whole-body.md` as checked primary evidence** (the header rows "Evidence basis" of the 0020 proposal and the refiner proposal). This proposal cites it with `path:line` as primary evidence. Part 1 names the other sources, each for a fact that the document does not cover. |
| skellytracker folder that you read | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read | `dom/18-agents-adr-bootstrap-kit` (`git status --porcelain` is empty; re-pinned on 2026-10-24 from `dom/17-gitignore-python-version`). `git diff --stat dom/17-gitignore-python-version dom/18-agents-adr-bootstrap-kit -- specs/sidecar .claude` is empty. In `notes/decisions`, only the index row of skellytracker 0031 (`README.md:49` at `dom/18-agents-adr-bootstrap-kit`; `:48` at `dom/21-move-sidecar-guide`) and its entry file are new, so the cited lines of this file are still valid. The intake also reads `dom/18-agents-adr-bootstrap-kit` (re-pinned from `dom/16-private-data`). `git diff --stat dom/16-private-data dom/17-gitignore-python-version -- specs notes/decisions .claude` is empty, so the line numbers of the intake are still valid. Guide citations point to the 0034 layout at skellytracker `dom/21-move-sidecar-guide`. The spec text did not change after the pin (only link repairs). Checked again on 2026-10-25 at `dom/21-move-sidecar-guide` (`git status --porcelain` lists no tracked change): every cited spec, template, guide, decision-entry and package line is unchanged; in `notes/decisions/README.md` the index row of skellytracker 0021 is still `:40`, and the index row of skellytracker 0031 is now `:48`. `inventory.yaml:113` and `:129` changed link text only. So this proposal reads `dom/21-move-sidecar-guide`. |

## 1. Gap

This part cites skellytracker 0021 (gap record). skellytracker 0021 gives the gap and the direction: a
single-person `coordinate` pose model declares three kinds of output beside its one `keypoints`
output (`:11-13`); the closed `semantic` set gets a value for each kind (`:13-14`); a presence output
declares its activation and a default threshold, and the host drops the landmarks of a crop whose
score fails it (`:15-16`); a class-probability output declares its class (`:17-18`); a world-keypoint
output declares its unit (`:18`); `V-common.outputs-4` and `V-post.pose.schema-7` change (`:19-21`).
This proposal gives the eight parts. It also corrects two facts of skellytracker 0021 (below, "Corrections to the
gap record").

**Evidence basis.** **User decision (2026-10-23):** `docs/mediapipe-whole-body.md` is checked
primary evidence. This part cites it as primary, and it does not check its facts again upstream.

| Item | Value |
|---|---|
| Property | The hand landmark model has four outputs. The graph splits them in tensor order: landmarks, hand flag, handedness, world landmarks. (1) **Hand flag** (`Identity_1`, `[1, 1]`): the probability that the crop holds a hand. The sigmoid is in the graph. MediaPipe keeps the hand only when the flag is `> min_hand_landmarks_confidence` (strict), default `0.5`. The value is an option of the user. When the hand is not present, MediaPipe gives no landmarks, no world landmarks and no handedness for the crop. (2) **Handedness** (`Identity_2`, `[1, 1]`): one probability. MediaPipe reads it with binary classification: the value is the probability of label item 0, `Right`, and `1 - value` is the probability of label item 1, `Left`. (3) **World landmarks** (`Identity_3`, `[1, 63]`, 21 × 3): 3D points in metres. MediaPipe decodes them without a normalization and rotates `x` and `y` by the rotation of the hand rect. It does not scale and does not translate them in the landmark graph. (Holistic then translates them to the pose world wrist, a step outside this model: intake row X5.) |
| Upstream evidence (file and line, or config key; upstream commit or release) | **Primary** (`docs/mediapipe-whole-body.md`, user designation): `:199` (the four outputs: `[1,63]` 21 × (x, y, z), `[1,1]` hand flag, `[1,1]` handedness, `[1,63]` world); `:350-353` (outputs in this order: the 21 points, the hand flag, the handedness and 21 world points; `> min_hand_presence_confidence` keeps the hand); `:362-363` (Tasks reads the handedness score as the probability of "Right", label item 0; `1 − score` is the probability of "Left"); `:378` (Holistic: hand flag `> 0.5`); `:404-408` (the hand is present when the flag is `> min_hand_landmarks_confidence`, default 0.5); `:409-410` (world landmarks: rotate by the ROI rotation, then translate to the pose world wrist); `:411-412` (Holistic does not output the handedness); `:148-151` (`WorldLandmarkProjectionCalculator` rotates world landmarks by the rect rotation only; world landmarks are in metres); `:155-157` (`ThresholdingCalculator` tests `value > threshold`, strict); `:307-309` and `:429-430` (the pose flag gets no sigmoid; the face flag gets a sigmoid; both are compared with a threshold). **Other sources, for facts that the document does not cover:** (a) MediaPipe source: `tasks/cc/vision/hand_landmarker/hand_landmarks_detector_graph.cc:94-104` (`min_detection_confidence` must be in `[0.0, 1.0]`), `:106-116` and `:276-285` (the split into four streams: landmarks, hand flag, handedness, world landmarks), `:129-141` (`top_k` 1, `binary_classification`, label item 0 `Right`, label item 1 `Left`), `:296-304` (the world landmarks: `TensorsToLandmarksCalculator` with `normalize = false`), `:306-319` (`TensorsToFloatsCalculator` with no activation, then `ThresholdingCalculator` with `min_detection_confidence`), `:321-331` (the handedness passes only when the hand is present: `AllowIf`), `:350-352` and `:362-364` (the landmarks and the world landmarks pass only when the hand is present); `calculators/tensor/tensors_to_classification_calculator.proto:58-63` (binary classification: "The single score(float) represent the probability of first label, and 1 - score is the probabilility of the second label"); `calculators/util/thresholding_calculator.cc:115-124` (`static_cast<double>(...Get<float>()) > threshold_`); `calculators/util/world_landmark_projection_calculator.cc:41-64` (with a rect: `x' = cos(a)·x − sin(a)·y`, `y' = sin(a)·x + cos(a)·y`, float `cosa` and `sina`; `z` and every other value are copied); `calculators/tensor/tensors_to_landmarks_calculator.cc:152-171, 203-206` (the absolute landmarks are the raw values); `tasks/cc/components/containers/landmark.h:28-30` ("The landmark coordinates are in meters"); `tasks/cc/vision/holistic_landmarker/holistic_landmarker.cc:236-238` and `holistic_landmarker.h:66-67` (Holistic sets `min_detection_confidence` from `min_hand_landmarks_confidence`, default `0.5`); `tasks/cc/vision/face_landmarker/face_landmarks_detector_graph.cc:306-320` (the face flag: `TensorsToFloatsCalculator` with `SIGMOID`, then `ThresholdingCalculator`); `tasks/cc/vision/pose_landmarker/pose_landmarks_detector_graph.cc:380-394` (the pose flag: `TensorsToFloatsCalculator` with no activation). (b) The Python API of `mediapipe` 1.1.1 (the installed copy in the scratch venv of the 0020 proposal, `mediapipe/tasks/python/vision/holistic_landmarker.py:185, 203, 218, 250, 268`): `min_hand_landmarks_confidence: float = 0.5` is an option of `HolisticLandmarkerOptions`. Thus the threshold is a runtime input of the user. (c) The ONNX graph, read with `onnx` 1.23.2 by the scratch script `hand21-outputs/read_outputs.py` of this session (run in the `uv` environment of OpenMMLab-Exporter): input `input_1` float `[1, 3, 224, 224]`; `Identity` float `[1, 63]` from `Gemm` `Identity_Gemm__977`; `Identity_1` float `[1, 1]` from `Sigmoid` `Identity_1` after `Gemm` `model_1/model/conv_handflag/...`; `Identity_2` float `[1, 1]` from `Sigmoid` `Identity_2` after `Gemm` `model_1/model/conv_handedness/...`; `Identity_3` float `[1, 63]` from `Gemm` `Identity_3_Gemm__976`. (d) MediaPipe-Exporter 0003: the ONNX outputs agree with the TFLite outputs within 3.1e-6 (flag), 2.9e-6 (handedness) and 6.0e-7 m (world) for `full`; the flag on noise inputs is 0.0031 to 0.0108. MediaPipe-Exporter 0005: the presence test is strict (`hand_score > 0.5`). MediaPipe-Exporter 0019: the metadata names of the outputs are in the wrong order; use the tensor index and shape. MediaPipe-Exporter 0021 (item 2): the earlier text "Left" and "mirrored image" for the handedness came from the legacy label file. |
| Nearest section ID | `common.outputs` (the closed `semantic` set), with `post.pose.schema` (rule `V-post.pose.schema-7`) |
| Why the nearest section is wrong | (1) The `semantic` set is closed: `detections`, `boxes`, `scores`, `class_logits`, `simcc_x`, `simcc_y`, `simcc_z`, `heatmap`, `keypoints`, `poses` (`specs/sidecar/common/outputs.md:29`, rule `V-common.outputs-4` at `:44`). No value describes a presence score of a crop, a class probability of an instance or 3D world points. `scores` is a detection semantic and requires `role: object_detector` (`:35, :44`). (2) `V-post.pose.schema-7` allows exactly one `keypoints` output for a `coordinate` decoder (`specs/sidecar/post/pose-schema.md:123`). (3) The spec has no field for a presence threshold, an activation of a pose output, a class label or a world unit, and no rule that drops the pose of a crop. (4) `post.unprojection` maps image points to the source image (`specs/sidecar/post/unprojection.md:23-36`). World points are not image points: they need a rotation only. (5) Thus a sidecar can describe only the landmarks. A host that runs the model without the flag gives landmarks for every crop, also for a crop with no hand (skellytracker 0021 `:34-36`). |
| Measured difference (number, image and script) | Scratch measurement of this session (secondary; no commit; the scratch script `hand21-outputs\measure_extra.py` of the session of 2026-10-24, not committed, output `out\measure_extra.json`; mediapipe 1.1.1, onnxruntime 1.31.0, OpenCV 5.0.0, NumPy 2.5.4; the image set (60 COCO images, 116 hand crops) and the video set (300 frames, 438 hand-frames) of MediaPipe-Exporter 0006; the path A chain of the 0020 proposal, which gives the same landmark errors as the 0020 measurement: image median 0.335 px, p95 1.722 px; video median 0.184 px, p95 1.486 px). **Presence.** With the gate `> 0.5` of this proposal, the presence decision differs from `HolisticLandmarker` for 0 of 116 image crops and 4 of 438 video hand-frames. Without a gate, the host gives landmarks for every crop: 31 of the 116 image crops and 101 of the 438 video hand-frames have no hand in `HolisticLandmarker`, and the model ran on each of them (the wrist gate of the refiner passed for all 116 and 438). **World keypoints.** The largest difference over the 21 points and 3 axes, after the subtraction of the wrist from both sides (Holistic translates its world landmarks to the pose wrist): with the rotation of step 4, image median 0.85 mm, p95 3.93 mm; video median 0.91 mm, p95 5.33 mm. Without the rotation: image median 107.5 mm, p95 247.0 mm; video median 161.9 mm, p95 317.5 mm. **Handedness.** `HolisticLandmarker` does not output the handedness, so no upstream comparison exists. The value (the probability of `Right`) is `> 0.5` for 34 of 41 present image hands of the Holistic right side (pose 16, 18, 20; `docs/mediapipe-whole-body.md:381`) and for 3 of 44 of the left side (pose 15, 17, 19); video: 168 of 185 (right) and 29 of 150 (left). These are not mirrored images (COCO photos and one camera video). **The physical side (user decision plan T28 (H3)).** **Committed evidence (secondary; committed script): OpenMMLab-Exporter decision 0041** (`notes/decisions/0041-rtmw-wrist-gate.md`, headings "Method" and "H3 (Qd)"; script `notes/decisions/scripts/rtmw_wrist_gate_handedness.py`; OpenMMLab-Exporter commit `9deff61`, merged in `32ab848`). The ground truth is the COCO-WholeBody v1.0 val annotation (`coco_wholebody_val_v1.0.json`, SHA-256 `f8272e9c…` in 0041 "Data checks"): the left and right hand labels (`lefthand_valid`, `righthand_valid`) and the hand root of each valid hand. These labels use the sides of the person: a valid hand root is nearer its own body wrist than the other body wrist for 97.3 % of the left hands and 95.9 % of the right hands (0041 "Data checks"). Images: 417 single-person COCO val2017 images (`num_keypoints >= 12`, at least one valid hand), each as is and mirrored left to right. Chain: the BlazePose pose of `HolisticLandmarker` (`mediapipe` 1.1.1, IMAGE mode, CPU), the loose ROI, `hand_roi_refinement.onnx`, `hand_landmark_full.onnx` (the path A chain of MediaPipe-Exporter 0006 and of the 0020 proposal). The MediaPipe hand ROI model and hand landmark model ran as ONNX files on CUDA (ONNX Runtime in the `uv` environment of OpenMMLab-Exporter). A present landmark hand (pose wrist visibility `> 0.1`, then hand flag `Identity_1 > 0.5`) matches the nearer GT hand root (distance below 0.35 of the ROI size, and the other root, when it exists, more than 2 times that distance away). The rule of the script: H3 is confirmed when `share(q_right > 0.5 | GT right) - share(q_right > 0.5 | GT left)` is `>= 0.6` on the images that are not mirrored and `<= -0.6` on the mirrored images. Result: not mirrored 184/197 − 23/181 = **+0.807**; mirrored 26/199 − 156/174 = **−0.766**. Both pass. The H3 script reads these MediaPipe-Exporter files by path, read only: `notes/decisions/scripts/hand_roi_reference.py`, the part 3 code of `specs/sidecar/proposals/roi-transform-and-source/proposal.md`, the part 3 code of `specs/sidecar/proposals/roi-refiner-role/proposal.md`, `model_cache/onnx/hand_roi_refinement.onnx`, `model_cache/onnx/hand_landmark_full.onnx` and `model_cache/assets/holistic_landmarker.task` (SHA-256 `e2dab61191e2dcd0…`, 0041 "Method"). MediaPipe-Exporter has no git history, so 0041 ("Method" and "Files") lists each file with its SHA-256 (the output `handedness.json` records the full SHA-256 and the time of each). **The kind of this evidence.** 0041 is an exporter measurement of the model behaviour on a dataset, with a committed script and a commit that a reader can cite (guide "Parity", step 6: commit the script so that a commit can be cited; step 7: numbers of a run without a commit are not evidence; `specs/exporter-guide/sidecars/workflow/parity.md:43-49`). It is not upstream evidence. The guide names three kinds of primary evidence: an upstream file and line, an upstream config key, and a read of the ONNX graph ("Rules", `exporter-guide/sidecars/rules.md:9-13`). A measurement on a dataset is none of these. The cached upstream sources state no mirror convention for the hand model; the legacy documentation at the pin (`docs/solutions/hands.md`, secondary) says that the model assumes a mirrored input, which the two measurements contradict (part 2.3, notes). Limits: the commit is in OpenMMLab-Exporter, not in MediaPipe-Exporter (it has no git repo). On 2026-10-24 the commit is only on the local OpenMMLab-Exporter branches `rtmw-wrist-gate` and `rtmo-model-id-variant` (merged in `32ab848`). It is not on `main` and not on the remote. On 2026-10-25 the commit is on the OpenMMLab-Exporter branch `main` and on the remote `origin/main` (merge `32ab848`, then the merge of PR #2, `7763f72`). Two of the files that the script loads are in the untracked plans folder of MediaPipe-Exporter (pinned by SHA-256 only). **Earlier check (secondary).** Before 0041, a second scratch measurement (secondary; no commit; the scratch script `mp-h\handedness_gt.py` of the session of 2026-10-24, not committed, output `out\handedness_gt.json`; the same versions) used the ground-truth body keypoints of COCO val2017 (`person_keypoints_val2017.json`). At the time of that run, the COCO-WholeBody hand annotations were not on this computer, and the session had no network. Images: the 400 largest single-person COCO val2017 images with 12 or more labelled keypoints and a visible wrist. Chain: the BlazePose pose of `HolisticLandmarker`, then the path A chain (loose ROI, refiner, `rotated_roi_crop` to 224², `hand_landmark_full.onnx`). The probe matched each present hand (gate `> 0.5`) to the nearer ground-truth wrist (distance below 0.35 of the crop size and below half of the distance to the other wrist): 369 of 390 hands. Images that are not mirrored: `q > 0.5` for 178 of 193 right hands of the person (median `q` 0.982) and for 22 of 176 left hands (median 0.026). The same images, mirrored left to right: `q > 0.5` for 159 of 175 left hands of the person and for 22 of 194 right hands (differences +0.80 and −0.80; 0041 "H3 (Qd)" cites this earlier check). The two measurements agree. Thus `Right` names the hand that has the form of a right hand in the image. The ground truth names the sides of the person: of the 2245 non-crowd persons of COCO val2017 with the nose, both eyes and both shoulders labelled visible (the face is to the camera), 2190 have `left_shoulder` to the right of `right_shoulder` in the image. |
| Row in "Considered and deliberately not added" (`specs/sidecar/changelog.md`), and the evidence that a model needs it now | none. The table (`specs/sidecar/changelog.md:38-53`) has no row for a presence score, a class probability or world keypoints. The `vNEXT` scope: skellytracker 0008 (accepted) does not include MediaPipe-Exporter (`notes/decisions/0008-vnext-scope.md:8-15`). The 0020 proposal adds MediaPipe-Exporter to the scope with a new entry (user decision 2026-10-23 (4); its part 2.1). **User decision (plan T28 (H2), 2026-10-24):** this change also goes into `vNEXT`, on the same scope extension. The user goal of plan T27 is that the spec describes these models so that the user can test them (Q1). |

**Corrections to the gap record.** A skellytracker session that adds this proposal to skellytracker 0021 must
change two facts of skellytracker 0021:

1. **The gate comparison.** skellytracker 0021 says "MediaPipe uses `>= 0.5`" (`:16-17`). MediaPipe uses `> 0.5`
   (strict): `thresholding_calculator.cc:123-124`; `docs/mediapipe-whole-body.md:155-157`;
   MediaPipe-Exporter 0005 item 1, which also says that skellytracker 0021 copied `>= 0.5` from the plan.
2. **The handedness class.** skellytracker 0021 says, from the untracked hand plan of MediaPipe-Exporter, that
   `handedness` is "the probability of `Left` (MediaPipe label 0) for a mirrored image" (`:46-47`).
   The plan says the same (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts), secondary). The primary source says
   that the value is the probability of label item 0, and label item 0 is `Right`
   (`hand_landmarks_detector_graph.cc:134-141`; `tensors_to_classification_calculator.proto:58-63`;
   `docs/mediapipe-whole-body.md:362-363`). MediaPipe-Exporter 0021 (item 2) records that "Left" and
   "mirrored image" came from the legacy label file. The legacy API and the Tasks API run the same
   model file with opposite label maps (OpenMMLab-Exporter 0052). The label file in the model
   metadata has `Left` at item 0 (`handedness.txt`, a read of `hand_landmark_full.tflite`; also
   `mediapipe/modules/hand_landmark/handedness.txt:1-2` of the legacy `mediapipe` 0.10.14 package).
   The legacy API assumes a mirrored input (`mediapipe/python/solutions/hands.py:79-83`, 0.10.14;
   the same sentence is in `docs/solutions/hands.md`, heading "multi_handedness"; secondary). The
   Tasks graph does not read the metadata (`hand_landmarks_detector_graph.cc:133`) and puts `Right` at
   item 0 (`:140-141`). Thus legacy item 0 (`Left` in a mirrored image) and Tasks item 0 (`Right` in an
   image that is not mirrored) name the same hand of the person. The legacy sentence agrees with the
   measurements. History (2026-10-25): an earlier text of this file said that the measurements do
   not agree with the legacy sentence. That reading compared the legacy sentence with the Tasks
   labels. The committed measurement of user decision H3 (OpenMMLab-Exporter
   0041 (secondary; committed script), commit `9deff61`, script `notes/decisions/scripts/rtmw_wrist_gate_handedness.py`; above,
   "Measured difference") shows on the COCO-WholeBody hand labels that `Right` is the right hand of
   the person in an image that is not mirrored. It is an exporter measurement, not upstream evidence.
   An earlier scratch measurement (secondary) agrees. The Qualcomm-Exporter plan (`positive_class: right`, skellytracker 0021 `:53-54`)
   agrees with the primary source.

**Missing primary evidence.** These facts have no primary source yet:

- No upstream output of the handedness exists for a known crop. `HolisticLandmarker` does not output
  it (`docs/mediapipe-whole-body.md:411-412`). `HandLandmarker` outputs it, but it does not output
  the ROI of its crop. Thus the class probabilities cannot be compared with the upstream library
  (part 5).
- The physical side that `Right` names. The cached sources set only the label items. User decision
  plan T28 (H3) puts the side into the spec. Its evidence is now the committed measurement
  OpenMMLab-Exporter 0041 (secondary; committed script; commit `9deff61`; script
  `notes/decisions/scripts/rtmw_wrist_gate_handedness.py`) on the COCO-WholeBody hand labels: +0.807
  not mirrored and −0.766 mirrored, against the rule `>= 0.6` and `<= -0.6` (above, "Measured
  difference"). The scratch measurement on the COCO body keypoints is an earlier, secondary check.
  0041 is not upstream evidence. It is an exporter measurement of the model on a dataset, and the
  guide does not list a measurement as primary evidence ("Rules", `exporter-guide/sidecars/rules.md:9-13`).
  Added 2026-10-25: OpenMMLab-Exporter 0052 (secondary; an upstream library output; commit
  `118699f` on `main`, script `notes/decisions/scripts/hand_handedness_upstream.py`) runs the
  upstream `HandLandmarker` of `mediapipe` 1.1.1 end to end with the hand landmark model of
  `holistic_landmarker.task` (SHA-256 `11c272b891e1a99a…`, the source of the ONNX probe) on the
  images of 0041. No exporter code is in that path. Result: +0.861 not mirrored and −0.862 mirrored,
  against the same gate. The primary sources give the names of the labels (the Tasks graph,
  `hand_landmarks_detector_graph.cc:133-141`; the score is the probability of the first label,
  `tensors_to_classification_calculator.proto:61-63`; no flip before the model,
  `image_to_tensor_calculator.cc:180`). The physical side comes from the legacy docstring
  (`hands.py:79-83`, secondary) and from the measurements 0041 and 0052 (secondary). Thus this item
  stays in this list. The guide requires part 1 to cite the primary evidence before the user accepts
  the proposal (guide "Rules", `exporter-guide/sidecars/rules.md:16-17`). Decided (user, 2026-10-25,
  OpenMMLab-Exporter plan T45): the user accepts OpenMMLab-Exporter 0041 and 0052 in place of a
  primary source for the physical side. This is the explicit exception of plan T31. History
  (2026-10-25): this item was an open question for the user, and it said that the legacy sentence
  states the opposite convention. OpenMMLab-Exporter 0052 shows that it does not.
- The origin of the world keypoints. The document removed the claim "world landmarks centred at the
  hips" (MediaPipe-Exporter 0021). No source that this proposal read gives the origin of the hand
  world landmarks. The section does not define the origin.
- The exporter export does not exist. The probe file has the flat layout `[1, 63]` for the world
  landmarks. The plan reshapes it to `[B, 21, 3]` (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts),
  secondary). This proposal requires `[N, K, 3]` (rule `-5`), as the `keypoints` output needs
  `(N, K, 3)` (`specs/sidecar/post/pose-decode-coordinate.md:33`).

## 2. Spec change

### 2.1 Sections

**New section.** `post.pose.extra_outputs`, title "Extra pose outputs", file
`specs/sidecar/post/pose-extra-outputs.md`.

```yaml
---
id: post.pose.extra_outputs
title: Extra pose outputs
kind: postprocessor
since: vNEXT
changed_in: []
selectors:
  - outputs[].semantic=presence
  - outputs[].semantic=binary_class
  - outputs[].semantic=world_keypoints
implemented_by:
  validate: missing
  decode: missing
external_impl: []
tests: []
vectors: vectors/post.pose.extra_outputs.yaml
status: {spec: draft, validate: missing, decode: missing}
---
```

Row of the section map (`specs/sidecar/README.md:83-95`, heading "Pose-estimation fields"), after
the row of `post.pose.decode.coordinate` (`:93`):

```markdown
| `post.pose.extra_outputs` | [post/pose-extra-outputs.md](post/pose-extra-outputs.md) | Extra pose outputs |
```

**Places that the change edits.** Line numbers are at skellytracker `dom/21-move-sidecar-guide` (the same as at `dom/18-agents-adr-bootstrap-kit`). "Content PR" and
"non-spec PR" follow the template ("What happens next", `specs/sidecar/templates/change-proposal.md:56-71`).

| Place | Heading | Edit |
|---|---|---|
| `specs/sidecar/README.md:83-95` | Section map, "Pose-estimation fields" | Add the row above after `:93`. |
| `specs/sidecar/README.md:121` | Validation rules (the index) | Add `- [Extra pose outputs](post/pose-extra-outputs.md#validation-rules)` after "Coordinate decode" (`:121`). |
| `specs/sidecar/common/outputs.md:29` | Fields, `semantic` | Add `presence`, `binary_class` and `world_keypoints` to the closed set. Add: "The Extra pose outputs (`../post/pose-extra-outputs.md#fields`) section defines them." |
| `specs/sidecar/common/outputs.md:35` | Behaviour, the routing paragraph | Add `presence`/`binary_class`/`world_keypoints` to the pose semantics. Add: "They go to Extra pose outputs (`../post/pose-extra-outputs.md#behaviour`), not to `pose.decode`." |
| `specs/sidecar/common/outputs.md:44` | `V-common.outputs-4` | Changed (part 2.4). |
| `specs/sidecar/common/outputs.md:69-72` | Authoring guidance (non-spec PR) | Replace the bullet on the skellytracker 0021 gap (`:72`) with the mapping of the MediaPipe hand outputs (part 2.2, YAML excerpt). Keep the bullets on the `Identity_N` numbering (`:69-71`): they still apply. |
| `specs/sidecar/post/pose-schema.md:53` | `outputs` (pose), field `keypoint_axis` | Add `world_keypoints` to the `(N, K, …)` semantics with the default `1`. |
| `specs/sidecar/post/pose-schema.md:54` | `outputs` (pose), field `keypoint_count` | No change. A `world_keypoints` output is a pose output, so the field applies. |
| `specs/sidecar/post/pose-schema.md:123` | `V-post.pose.schema-7` | Changed (part 2.4). |
| `specs/sidecar/post/pose-schema.md:143` | Authoring guidance (non-spec PR) | Replace "The output semantics of the spec are a closed set with no presence score and no handedness ... Decision 0021 (proposed) records this gap." with a pointer to Extra pose outputs (`pose-extra-outputs.md`). Keep the Qualcomm-Exporter fact. |
| `specs/sidecar/post/pose-decode-coordinate.md:33` | Behaviour, the single-person form | Add: "A single-person model can also declare the outputs of Extra pose outputs (`pose-extra-outputs.md`). They do not change this decode." |
| `specs/sidecar/format/versioning.md:72-74` | Legacy behaviour | Add the semantics `presence`, `binary_class` and `world_keypoints` to the first column of the existing row (part 2.6). |
| `specs/sidecar/format/versioning.md:51-63` | Version-aware compatibility | No link: the new section has a "Legacy behaviour" heading that points to `format.versioning`, as `pre.resize.fit` does. |
| `specs/sidecar/changelog.md:14-36` | Summary of changes | New row N, the next free number at merge time (part 2.7). 13 open proposals (9 of OpenMMLab-Exporter, 4 of MediaPipe-Exporter) add a summary row, so the numbers depend on the merge order. |
| `specs/sidecar/changelog.md:55-59` | Compatibility impact | Add: "A `vNEXT` single-person `coordinate` model can declare one `presence`, one `binary_class` and one `world_keypoints` output. A `presence` output must declare `activation` and `score_threshold_default`." |
| `specs/sidecar/changelog.md:68` | `schema_version` history, row `vNEXT` | Add text (part 2.7). |
| `specs/sidecar/templates/model-intake.md:290` | Row D1 | Add `presence`, `binary_class` and `world_keypoints` to the list of semantics, with a link to the new section. |
| `specs/sidecar/templates/model-intake.md:318` | Row K8 | Add: "An instance presence score is not a keypoint score. Record it in row D1 (`presence`)." |
| `specs/exporter-guide/sidecars/workflow/mapping-hints.md:55-61` | Mapping hints, "Outputs and decode" (non-spec PR) | Add: "Record a presence output, its activation, its comparison and its default threshold. Record the labels of a binary class output in the order of the upstream label items. Record the unit of world keypoints and the rotation that the upstream applies." |
| `specs/sidecar/TRACEABILITY.md:38-43, 88-95` | Section tables | Regenerated with the new section. |
| `specs/sidecar/inventory.yaml:115-121` | `mediapipe-hand-landmark@mediapipe-exporter` (non-spec PR) | The notes name the new semantics. (The key changes with skellytracker 0025; not this proposal.) |
| `tools/make_vectors.py`, `tools/tests/test_vectors.py`, `tools/tests/test_traceability.py` | Vector builders and tests | The vectors of this section come from the reference file of part 3. The content PR commits the YAML of part 4, or adds a builder that imports `specs/sidecar/reference/post_pose_extra_outputs.py`. For the implementer. |
| skellytracker `notes/decisions/0021-landmark-extra-outputs.md` | The gap record | A skellytracker session adds this proposal to the gap record and makes the two corrections of part 1. |

`specs/sidecar-spec.md` (the permanent index) needs no edit. It keeps old headings, and this section
has no old heading.

### 2.2 Fields table

These fields are fields of an `outputs` entry. The common fields (`name`, `dtype`, `shape`, `rank`,
`semantic`) are in Outputs (`../common/outputs.md#fields`).

| Field | Type | Required | Description |
|---|---|---|---|
| `outputs[].semantic` | enum | yes | The new values `presence`, `binary_class` and `world_keypoints`. |
| `outputs[].activation` | enum | yes (`presence`) | `none` or `sigmoid`. The host applies it to the value of a `presence` output before the gate. `none`: the graph gives the probability. `sigmoid`: the graph gives a logit. No default. |
| `outputs[].score_threshold_default` | float | yes (`presence`) | The default of the runtime presence threshold `t`. A finite number with `0 <= t < 1`. It is host policy: the host or the user can set another value at run time, in the same range. The comparison is strict: `p > t`. The name and the range follow `roi_source.score_gate.score_threshold_default` of the refiner proposal (plan T26 (6)) and `decode.confidence_threshold_default` (`post/detection-decode.md:42`). No default in the spec: the value depends on the model. |
| `outputs[].labels` | array[2] of string | yes (`binary_class`) | Two different, non-empty labels. The value `q` of the output is the probability of `labels[0]`. `1 - q` is the probability of `labels[1]`. The labels are the upstream label items, in their order. |
| `outputs[].unit` | enum | yes (`world_keypoints`) | `m` or `mm`. The unit of the three values of each world keypoint. |
| `outputs[].keypoint_axis` | int | no (`world_keypoints`) | As in Pose schema (`pose-schema.md#outputs-pose`). It must be `1`. |
| `outputs[].keypoint_count` | int | no (`world_keypoints`) | As in Pose schema (`pose-schema.md#outputs-pose`). It must equal `len(pose.tracked_points)`. |

**The runtime presence threshold.** The host must let the caller set the presence threshold `t` of
a model at run time. When the caller sets no value, `t` is `score_threshold_default`. The host must
refuse a runtime value that is not a finite number in `[0, 1)`. (User decision plan T26 (6) gives this
pattern for the refiner score gate. This proposal applies it to the presence gate, with the same
range `[0, 1)`: **user decision plan T28 (H4)**, Q3. MediaPipe also makes the value an option of the user:
`min_hand_landmarks_confidence`, part 1 other source (b).)

**The shapes.** A `presence` or `binary_class` output has one value for each batch item: shape `[N]`
or `[N, 1]`. A `world_keypoints` output has the shape `[N, K, 3]`, with `K = len(pose.tracked_points)`
and the values `X, Y, Z` of each keypoint in `unit`.

YAML excerpt (the outputs of `hand_landmark_full` after the reshape of the plan; the names are the
names of the probe file, and the plan renames them, the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts),
secondary; the `keypoints` output and its depth are the depth proposal):

```yaml
outputs:
  - name: Identity                 # landmarks; tensor 0 of the split (hand_landmarks_detector_graph.cc:282)
    dtype: {fp32: float32}
    shape: [-1, 21, 3]
    rank: 3
    semantic: keypoints
    keypoint_axis: 1
    keypoint_count: 21
  - name: Identity_1               # hand flag; the Sigmoid is in the graph
    dtype: {fp32: float32}
    shape: [-1, 1]
    rank: 2
    semantic: presence
    activation: none
    score_threshold_default: 0.5   # min_hand_landmarks_confidence (holistic_landmarker.h:67); strict >
  - name: Identity_2               # handedness; the Sigmoid is in the graph
    dtype: {fp32: float32}
    shape: [-1, 1]
    rank: 2
    semantic: binary_class
    labels: [Right, Left]          # label items 0 and 1 (hand_landmarks_detector_graph.cc:134-141)
  - name: Identity_3               # world landmarks
    dtype: {fp32: float32}
    shape: [-1, 21, 3]
    rank: 3
    semantic: world_keypoints
    unit: m                        # tasks/cc/components/containers/landmark.h:28-30
    keypoint_axis: 1
    keypoint_count: 21
```

### 2.3 Behaviour

Normative text of `post.pose.extra_outputs`:

```text
## Fields

A pose model with pose.estimator_type: top_down_single_person and pose.decode.method: coordinate can
declare extra outputs beside its keypoints output. Each extra output has its values for each batch
item (one crop). The sidecar can declare at most one output of each extra semantic:

- presence: the probability that the crop holds an instance. Shape [N] or [N, 1].
- binary_class: the probability of one of two classes of the instance. Shape [N] or [N, 1].
- world_keypoints: the 3D keypoints of the instance in a metric unit. Shape [N, K, 3].

A binary_class output gives the probability of labels[0] (Behaviour, step 3). The labels are the
label items of the upstream inference graph, in their order. A label file in the model metadata can
differ from them. The host takes the labels from the sidecar only. A label names a class of the
input image as the model sees it. The host does not mirror the image and does not swap the labels. For the MediaPipe hand
landmark model (labels [Right, Left]), Right names the right hand of the person in an image that is
not mirrored, and the left hand of the person in a mirrored image.

## Behaviour

For each batch item, after the model runs:

1. Presence probability. If the sidecar declares a presence output, v is its value for the item.
     activation none:    p = v
     activation sigmoid: p = 1 / (1 + exp(-v))
2. Gate. t is the presence threshold. The caller can set t at run time. If the caller sets no value,
   t = score_threshold_default. The host must refuse a value of t that is not a finite number in
   [0, 1). The item is present if p > t (strict). If p is NaN, the item is not present.
   If the item is not present, the item has no pose: the host gives no keypoints, no class
   probabilities and no world keypoints for it. The host can report p.
   If the sidecar declares no presence output, every item is present.
3. Class probabilities. If the item is present and the sidecar declares a binary_class output, q is
   its value for the item. If 0 <= q <= 1:
     probability of labels[0] = q
     probability of labels[1] = 1 - q
   Else the item has no class probabilities. This section does not choose a label.
4. World keypoints. If the item is present and the sidecar declares a world_keypoints output,
   (X, Y, Z) are the values of each keypoint, in unit. theta is the rotation of the crop:
     input.resize.method rotated_roi_crop: theta = the rotation of the crop ROI Rc
                                           (Rotated ROI crop, Behaviour step 3)
     every other method:                   theta = 0
   For each keypoint:
     X' = cos(theta) * X - sin(theta) * Y
     Y' = sin(theta) * X + cos(theta) * Y
     Z' = Z
   The host does not scale and does not translate the world keypoints. The unit does not change.
   This section does not define the origin of the world keypoints. The model defines it.

The decode of the keypoints output and its unprojection do not change (Coordinate decode,
Unprojection).

Inverse: none. The host does not map world keypoints back to the model frame. A reader who needs
the model-frame values rotates by -theta (the transpose of the rotation of step 4).
```

Which upstream rule each part describes:

| Part | Upstream rule (primary: `docs/mediapipe-whole-body.md`; other sources as named in part 1) |
|---|---|
| The three semantics | The split of the four outputs in tensor order (`:350-353`; `hand_landmarks_detector_graph.cc:106-116, 276-285`) |
| Step 1 | The hand flag has its sigmoid in the graph (part 1, other source (c)), and `TensorsToFloatsCalculator` has no activation (`hand_landmarks_detector_graph.cc:306-310`): `activation: none`. The face flag gets `SIGMOID` in the calculator (`face_landmarks_detector_graph.cc:306-320`; `:429-430`): `activation: sigmoid`. |
| Step 2 | `ThresholdingCalculator`: `static_cast<double>(score) > threshold_` (`thresholding_calculator.cc:115-124`; `:155-157`); the default `0.5` (`holistic_landmarker.h:66-67`; `:404-408`); a user option (part 1, other source (b)); `AllowIf(..., hand_presence)` on the landmarks and the world landmarks (`hand_landmarks_detector_graph.cc:350-352, 362-364`) |
| Step 3 | `binary_classification` and the label items (`hand_landmarks_detector_graph.cc:129-141`; `tensors_to_classification_calculator.proto:58-63`; `:362-363`); `AllowIf` on the handedness (`:329-331`) |
| The physical side of `Right` (Fields) | The names: the Tasks label items (`hand_landmarks_detector_graph.cc:133-141`; the model metadata label file has the opposite order, notes below). The side: the legacy docstring (`mediapipe/python/solutions/hands.py:79-83`, 0.10.14; secondary), which agrees when it is read with the legacy label map (notes below); the upstream `HandLandmarker` run OpenMMLab-Exporter 0052 (secondary; an upstream library output). The user accepts these in place of a primary source (OpenMMLab-Exporter plan T45, 2026-10-25). The committed measurement of user decision plan T28 (H3): OpenMMLab-Exporter 0041 (secondary; committed script), commit `9deff61`, script `notes/decisions/scripts/rtmw_wrist_gate_handedness.py`, on the COCO-WholeBody hand labels (part 1, measured difference; an exporter measurement, not upstream evidence). Earlier: the scratch measurement of part 1 (secondary) |
| Step 4 | `WorldLandmarkProjectionCalculator` with the hand rect (`world_landmark_projection_calculator.cc:41-64`; `hand_landmarks_detector_graph.cc:357-364`; `:148-151, 409`); metres (`landmark.h:28-30`; `:150-151`) |
| Inverse | none: MediaPipe has no inverse step for the world landmarks (`world_landmark_projection_calculator.cc:41-64` rotates forward only) |

Notes, not normative:

- **The rotation of step 4.** The landmark graph gives the hand rect to the world-landmark projection
  (`hand_landmarks_detector_graph.cc:361`). That rect is the ROI that the crop receives, with no
  transform in this graph (intake row T8). For the hand landmark model, `Rc` is that ROI, because
  `maintain_aspect_ratio` is `false` (0020 proposal, excerpt 1), and the aspect step does not change
  the rotation in any case (0020 proposal, Behaviour step 3). The scratch measurement of part 1 shows
  the rule on real hands.
- **The comparison of step 2.** MediaPipe casts the float32 score to double and compares it with the
  double threshold (`thresholding_calculator.cc:123-124`). A host that compares the float32 value of
  the model with a float64 `t` makes the same decision. The section states no arithmetic precision
  (the rule of user decision Q7 = (c) of the 0020 proposal). The vectors give the tolerances.
- **No label choice in step 3 (user decision plan T28 (H5)).** MediaPipe sets `top_k` 1
  (`hand_landmarks_detector_graph.cc:131`). The code that picks the label
  (`tensors_to_classification_calculator.cc`) is not in the cache, so this proposal does not know its
  tie rule at `q = 0.5`. Holistic does not use the handedness. Thus the section gives only the
  probability of `labels[0]` (and `1 - q` for `labels[1]`), and no label rule.
- **The physical side of `Right` (user decision plan T28 (H3)).** The committed measurement of part 1
  (OpenMMLab-Exporter 0041 (secondary; committed script), commit `9deff61`) gives the sentence of "Fields". On 417 COCO-WholeBody
  val images that are not mirrored, `q > 0.5` for 184 of 197 right hands and 23 of 181 left hands of
  the person (difference +0.807). On the same images mirrored, `q > 0.5` for 26 of 199 right hands
  and 156 of 174 left hands (difference −0.766). The rule is `>= 0.6` and `<= -0.6`, so both pass.
  It is an exporter measurement of the model on a dataset, not upstream evidence. The earlier scratch
  measurement of part 1 (secondary, on the COCO body keypoints) agrees: on images that are not
  mirrored, `q > 0.5` for 178 of 193 right hands and 22 of 176 left hands of the person; on the same
  images mirrored, for 159 of 175 left hands and 22 of 194 right hands. The statement is a fact about the class, not about each value:
  the model gives the wrong side for some hands. Upstream: the cached sources at the pin state no
  mirror convention for the hand model (a search for `mirror` and `selfie` in
  `model_cache/sources/e9794ef55e2509c09aa8b6ba1764b797db8eb200/` finds only the stream mirrors of
  `framework/` and the file names of the selfie segmentation model). The installed `mediapipe` 1.1.1
  package has one sentence on a mirrored input, for the face blendshapes: "*Left and *Right
  blendshapes correspond to the subject's face, not the viewer. Passing a horizontally mirrored image
  will invert these outputs." (`mediapipe/tasks/python/vision/face_landmarker.py:51-52`). The
  legacy MediaPipe documentation at the pin, `docs/solutions/hands.md` (commit `e9794ef`, heading
  "multi_handedness" under "Output"; secondary, not in the cache; read on 2026-10-25 from GitHub),
  says: "Note that handedness is determined assuming the input image is mirrored, i.e., taken with a
  front-facing/selfie camera with images flipped horizontally. If it is not the case, please swap
  the handedness output in the application." The Tasks documentation page and
  `mediapipe/tasks/python/vision/hand_landmarker.py` at the pin do not mention a mirrored input. The
  legacy sentence applies to the legacy label map. The model metadata has one associated file,
  `handedness.txt`, with `Left` at item 0 and `Right` at item 1, and the legacy package uses that file.
  The Tasks graph ignores it ("TODO: use model Metadata to set label_items",
  `hand_landmarks_detector_graph.cc:133`) and puts `Right` at item 0 (`:140-141`). Legacy item 0 is
  the left hand of the person in a mirrored image. That is the right hand of the person in an image
  that is not mirrored, which Tasks calls `Right`. So the legacy sentence and the measurements agree
  (OpenMMLab-Exporter 0052). The upstream `HandLandmarker` with the model of this proposal gives
  +0.861 not mirrored and −0.862 mirrored (0052). The section follows the measurements (user
  decision plan T28 (H3), confirmed in plan T31; the evidence exception is plan T45). A host must not
  take the labels from the model metadata: they have the legacy order. History (2026-10-25): this note
  first said that the measurements do not agree with the legacy sentence.
- **The alignment of Holistic.** Holistic translates the hand world landmarks so that the hand wrist
  is at the pose world wrist (`AlignHandToPoseInWorldCalculator`, `:409-410`;
  `holistic_hand_tracking.cc:250-258`). That step uses the output of another model. It is outside
  this section (intake row X5, `out of scope`).
- **The presence score is not a keypoint score.** The keypoint score of the spec is a value for each
  point (`post.pose.decode.*`; the visibility proposal `keypoint-visibility` of OpenMMLab-Exporter
  adds a per-point visibility). The presence score is one value for each crop.

### 2.4 Validation rules

New rules of `post.pose.extra_outputs`:

- [ ] `V-post.pose.extra_outputs-1` **(vNEXT)** An output with the semantic `presence`,
  `binary_class` or `world_keypoints` requires `role` to include `pose_estimator`,
  `pose.estimator_type: top_down_single_person` and `pose.decode.method: coordinate`.
- [ ] `V-post.pose.extra_outputs-2` **(vNEXT)** A sidecar must declare at most one output of each of
  the semantics `presence`, `binary_class` and `world_keypoints`.
- [ ] `V-post.pose.extra_outputs-3` **(vNEXT)** A `presence` output must declare `activation`, with
  the value `none` or `sigmoid`. It must declare `score_threshold_default`, a finite number (not a
  boolean) with `0 <= score_threshold_default < 1`.
- [ ] `V-post.pose.extra_outputs-4` **(vNEXT)** A `binary_class` output must declare `labels`: a list
  of exactly two non-empty strings that are different.
- [ ] `V-post.pose.extra_outputs-5` **(vNEXT)** A `world_keypoints` output must declare `unit`, with
  the value `m` or `mm`. If `shape` is present, it must have rank 3, its last dimension must be `3`,
  and its keypoint dimension must be `-1` or `len(pose.tracked_points)`. If `keypoint_axis` is
  present, it must be `1`.
- [ ] `V-post.pose.extra_outputs-6` **(vNEXT)** If a `presence` or `binary_class` output declares
  `shape`, the shape must be `[N]` or `[N, 1]`.
- [ ] `V-post.pose.extra_outputs-7` The fields `activation` and `score_threshold_default` are valid
  only on a `presence` output. `labels` is valid only on a `binary_class` output. `unit` is valid only
  on a `world_keypoints` output.

Rule `-7` has no **(vNEXT)** mark. The four fields do not exist below `vNEXT`, so a legacy sidecar
with one of them is not valid at any version. The package validator already rejects an unknown
field of an output: `OutputSpec` is a `_StrictModel` with `extra="forbid"`
(`skellytracker/core/sidecar/model.py:31-32, 187`). Thus the rule changes no legacy result.

Changed rules:

- `V-common.outputs-4` (`specs/sidecar/common/outputs.md:44`), new text: "The `semantic` of each
  output must be one of `detections`, `boxes`, `scores`, `class_logits`, `simcc_x`, `simcc_y`,
  `simcc_z`, `heatmap`, `keypoints`, `poses`, `presence`, `binary_class`, `world_keypoints`. The
  values `boxes`/`scores`/`class_logits` and `presence`/`binary_class`/`world_keypoints` are marked
  **(vNEXT)**. The detection semantics require `role` to include `object_detector`. The pose
  semantics require `role` to include `pose_estimator`." (The 0020 and refiner proposals also change
  this rule: the refiner adds `roi_points`. The proposal that lands second merges the lists.)
- `V-post.pose.schema-7` (`specs/sidecar/post/pose-schema.md:123`), new text of the `coordinate`
  sentence: "A `coordinate` decoder must declare exactly one `keypoints` output (single-person). It
  can also declare the outputs of Extra pose outputs (`pose-extra-outputs.md`)
  (`V-post.pose.extra_outputs-1` to `-7`)."

Existing rules that name a changed value, and the effect:

| Rule | Effect |
|---|---|
| `V-post.pose.schema-8` (`post/pose-schema.md:124`) | unchanged. It applies to `keypoint_count` on every pose output, so also on `world_keypoints`. Rule `-5` repeats it for the vectors. |
| `V-common.outputs-1`, `-2`, `-3`, `-5` (`common/outputs.md:41-45`) | unchanged. They apply to the new outputs: unique names, the `dtype` map, `rank`, and the same outputs in all sizes. |
| `V-post.pose.decode.coordinate-1` (`post/pose-decode-coordinate.md:43`) | unchanged. |
| `V-post.det.*` | unchanged. `presence` is not a detection semantic, so it does not need `role: object_detector`. |
| `V-post.pose.bottom_up-*` | unchanged. Rule `-1` allows the extra semantics only for `top_down_single_person`. |
| `V-format.versioning-1`, `-2` | unchanged. `n/a at vNEXT` (`specs/exporter-guide/sidecars/validation-and-publishing.md:13-16`). |

### 2.5 Selectors

`outputs[].semantic=presence`, `outputs[].semantic=binary_class` and
`outputs[].semantic=world_keypoints`. The section `post.unprojection` keeps its selectors. The world
keypoints do not use it.

### 2.6 Legacy behaviour and version effect

- A sidecar with `schema_version < vNEXT` cannot declare the semantics `presence`, `binary_class` or
  `world_keypoints`, or the fields `activation`, `score_threshold_default`, `labels` and `unit` on
  an output. The legacy meaning of every other field does not change.
- The change goes into the `vNEXT` revision (**user decision plan T28 (H2)**, Q1). It adds no new
  `schema_version` value, because `vNEXT` is not released yet (skellytracker 0014).
- The new section has the heading "Legacy behaviour" with one sentence: "Availability before
  `vNEXT`: Schema versioning (`../format/versioning.md#legacy-behaviour`)." (the form of
  `specs/sidecar/pre/resize-fit.md`).

Changed row of the "Legacy behaviour" table of `format.versioning`
(`specs/sidecar/format/versioning.md:74`; the 0020 proposal adds `rotated_roi_crop` to the same row):

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|---|---|---|
| `boxes`/`scores`/`class_logits` semantics, `packed_keypoints`, `stretch`, `fit`, `class_id_map`, `presence`/`binary_class`/`world_keypoints` semantics | Not available. | Available. |

### 2.7 Changelog row

Summary of changes (`specs/sidecar/changelog.md:14-36`), row N (the next free number at merge time):

```markdown
| N | Outputs | New pose semantics `presence`, `binary_class` and `world_keypoints` for a single-person `coordinate` model. A `presence` output declares `activation` (`none` \| `sigmoid`) and `score_threshold_default`; the threshold is a runtime input of the host, the test is strict (`p > t`), and an item that fails it has no pose. A `binary_class` output declares `labels`: the value is the probability of `labels[0]`. A `world_keypoints` output `[N, K, 3]` declares `unit` (`m` \| `mm`); the host rotates it by the rotation of the crop ROI and does not scale or translate it. | MediaPipe hand landmark model (hand flag, handedness, world landmarks) | [Extra pose outputs](post/pose-extra-outputs.md) |
```

`schema_version` history (`specs/sidecar/changelog.md:68`), text to add to the `vNEXT` row: "Added
the pose semantics `presence` (with `activation` and `score_threshold_default`, a runtime threshold
and a strict gate that drops the pose of an item), `binary_class` (with `labels`) and
`world_keypoints` (with `unit`, rotated by the crop rotation) for single-person `coordinate` models."

No row of "Considered and deliberately not added" changes. A new row records what this proposal does
not add:

```markdown
| A label choice for `binary_class`, more than two classes, a mirror flag for a class, an origin of `world_keypoints`, and extra outputs for bottom-up or multi-person models | No model in scope needs them. The MediaPipe hand model gives one binary probability, and Holistic does not use it. |
```

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the exporter repo | the part 3 code of `specs/sidecar/proposals/landmark-extra-outputs/proposal.md` (exists) |
| Target file in skellytracker | `specs/sidecar/reference/post_pose_extra_outputs.py` |
| Functions (one for each algorithm) | `validate_extra_outputs`: the rules `-1` to `-7`. `presence_probability`: step 1. `presence_threshold`: step 2, the threshold `t` (the runtime value or the default, and its range). `presence_gate`: steps 1 and 2. `class_probabilities`: step 3. `world_rotation`: step 4, the angle `theta`. `rotate_world_keypoints`: step 4, the rotation. `decode_extra_outputs`: steps 1 to 4 for one batch item. |

- The note at the top of the file says `source commit: none (no host code)`. MediaPipe-Exporter has
  no git repo and no exporter code. The functions come from the text of part 2.
- The file uses NumPy and the Python standard library only. It does not import from an exporter or
  from skellytracker. It does not load the 0020 reference file: `world_rotation` takes the crop ROI
  `Rc` as an input.
- This is a new section, so the file implements the full section.
- The file computes in float64. The section states no precision, so float64 is a choice of the file.
- `presence_probability` computes the sigmoid in a form that does not overflow for a large `|v|`.

```python
"""Reference implementation of the proposed section ``post.pose.extra_outputs`` (extra pose outputs).

This file uses ASD-STE100 Simplified Technical English.

Note:
- Section ID: ``post.pose.extra_outputs`` (proposed). Proposal:
  ``specs/sidecar/proposals/landmark-extra-outputs/proposal.md`` (the full proposal of the skellytracker gap
  record 0021).
- Target file in skellytracker: ``specs/sidecar/reference/post_pose_extra_outputs.py``.
- source commit: none (no host code). MediaPipe-Exporter has no git repo and no exporter code. The
  functions come from the text of part 2 of the proposal.
- Vector results: the 81 vectors of part 4 of the proposal pass against this file (81 of 81,
  2026-10-24). They are ``unverified: no host implementation``.
- Parity result: to run (MediaPipe-Exporter has no git repo, so no script can be committed). The
  parity script is ``notes/decisions/scripts/hand_chain_parity.py`` (to write), one script for the four
  MediaPipe proposals (user decision plan T28 (H6)). A scratch measurement (secondary, part 1 of the proposal) used ``presence_gate``,
  ``world_rotation`` and ``rotate_world_keypoints`` of this file on the real model outputs.
- The presence threshold is a runtime input with the sidecar default ``score_threshold_default``
  in ``[0, 1)``. This is the pattern of the refiner score gate (plan T26 (6)), with its range (user
  decision plan T28 (H4)).
- Precision: the section states no arithmetic precision (the rule of user decision Q7 = (c) of the
  0020 proposal). The vectors give the tolerances in ``compare``. This file computes in float64.
  That is a choice of this file, not a rule of the section.
- The crop ROI ``Rc`` of ``world_rotation`` is the crop ROI of ``pre.resize.rotated_roi_crop``
  (proposal ``specs/sidecar/proposals/roi-transform-and-source/proposal.md``, Behaviour step 3). This file does
  not compute it. It takes it as an input, so it does not load the 0020 reference file.

Conventions: one batch item at a time. A per-item value of a ``presence`` or ``binary_class`` output
is the single value of that item (shape ``[]`` or ``[1]``). A per-item ``world_keypoints`` value has
the shape ``[K, 3]``. A rotation is in radians, clockwise on the image (the ROI convention of
``pre.resize.rotated_roi_crop``).

Only NumPy and the Python standard library are used.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np

EXTRA_SEMANTICS = ("presence", "binary_class", "world_keypoints")
ACTIVATIONS = ("none", "sigmoid")
WORLD_UNITS = ("m", "mm")
# The fields that belong to one extra semantic. No other semantic can have them (rule -7).
OWN_FIELDS = {
    "presence": ("activation", "score_threshold_default"),
    "binary_class": ("labels",),
    "world_keypoints": ("unit",),
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _single_value(value: Any) -> float:
    arr = np.asarray(value, dtype=np.float64).ravel()
    if arr.size != 1:
        raise ValueError("a presence or binary_class value must have one value for each batch item")
    return float(arr[0])


def validate_extra_outputs(
    outputs: Sequence[Mapping[str, Any]],
    role: Sequence[str],
    estimator_type: str,
    method: str,
    keypoint_count: int,
    schema_is_vnext: bool = True,
) -> bool:
    """``post.pose.extra_outputs``: rules ``V-post.pose.extra_outputs-1`` to ``-7``.

    ``outputs`` is the ``outputs`` list of the sidecar. ``role``, ``estimator_type`` and ``method``
    are ``role``, ``pose.estimator_type`` and ``pose.decode.method``. ``keypoint_count`` is
    ``len(pose.tracked_points)``. ``schema_is_vnext`` is true when ``schema_version >= vNEXT``.
    Raises ``ValueError`` at the first rule that fails. Returns ``True`` when all rules pass.
    """
    extra = [o for o in outputs if o.get("semantic") in EXTRA_SEMANTICS]
    # rule -7: the own fields of each extra semantic are not valid on another output
    for o in outputs:
        for semantic, fields in OWN_FIELDS.items():
            if o.get("semantic") != semantic:
                for field in fields:
                    if field in o:
                        raise ValueError(f"{field} is valid only on a {semantic} output")
    if not extra:
        return True
    # rule -1: the context of an extra output
    if not schema_is_vnext:
        raise ValueError("the semantics presence, binary_class and world_keypoints need vNEXT")
    if "pose_estimator" not in role or estimator_type != "top_down_single_person" or method != "coordinate":
        raise ValueError(
            "an extra pose output needs role pose_estimator, top_down_single_person and method coordinate"
        )
    # rule -2: at most one output of each extra semantic
    for semantic in EXTRA_SEMANTICS:
        if sum(1 for o in extra if o["semantic"] == semantic) > 1:
            raise ValueError(f"at most one {semantic} output")
    for o in extra:
        semantic = o["semantic"]
        shape = o.get("shape")
        if semantic in ("presence", "binary_class"):
            # rule -6: one value for each batch item
            if shape is not None and not (len(shape) == 1 or (len(shape) == 2 and shape[1] == 1)):
                raise ValueError(f"a {semantic} output must have the shape [N] or [N, 1]")
        if semantic == "presence":
            # rule -3
            if o.get("activation") not in ACTIVATIONS:
                raise ValueError("presence.activation must be none or sigmoid")
            t = o.get("score_threshold_default")
            if not (_is_number(t) and math.isfinite(t) and 0.0 <= t < 1.0):
                raise ValueError("presence.score_threshold_default must be a finite number in [0, 1)")
        elif semantic == "binary_class":
            # rule -4
            labels = o.get("labels")
            if not (
                isinstance(labels, (list, tuple))
                and len(labels) == 2
                and all(isinstance(x, str) and x for x in labels)
                and labels[0] != labels[1]
            ):
                raise ValueError("binary_class.labels must be two different non-empty strings")
        else:
            # rule -5
            if o.get("unit") not in WORLD_UNITS:
                raise ValueError("world_keypoints.unit must be m or mm")
            if shape is not None and not (len(shape) == 3 and shape[2] == 3):
                raise ValueError("a world_keypoints output must have the shape [N, K, 3]")
            if shape is not None and shape[1] not in (-1, keypoint_count):
                raise ValueError("the keypoint axis of world_keypoints must have len(tracked_points) values")
            if o.get("keypoint_axis", 1) != 1:
                raise ValueError("world_keypoints.keypoint_axis must be 1")
            if "keypoint_count" in o and o["keypoint_count"] != keypoint_count:
                raise ValueError("keypoint_count must equal len(pose.tracked_points)")
    return True


def presence_probability(value: Any, activation: str) -> float:
    """``post.pose.extra_outputs``, Behaviour step 1: the presence probability ``p``."""
    v = _single_value(value)
    if activation == "none":
        return v
    if activation == "sigmoid":
        if math.isnan(v):
            return v
        # 1 / (1 + exp(-v)), in a form that does not overflow
        if v >= 0:
            return 1.0 / (1.0 + math.exp(-v))
        e = math.exp(v)
        return e / (1.0 + e)
    raise ValueError("presence.activation must be none or sigmoid")


def presence_threshold(score_threshold_default: float, threshold: Any = None) -> float:
    """``post.pose.extra_outputs``, Behaviour step 2: the threshold ``t``.

    ``threshold`` is the runtime input of the host. ``None`` means that the caller set no value, and
    ``t`` is ``score_threshold_default``.
    """
    t = score_threshold_default if threshold is None else threshold
    if not (_is_number(t) and math.isfinite(t) and 0.0 <= t < 1.0):
        raise ValueError("the presence threshold must be a finite number in [0, 1)")
    return float(t)


def presence_gate(value: Any, activation: str, score_threshold_default: float, threshold: Any = None) -> dict:
    """``post.pose.extra_outputs``, Behaviour steps 1 and 2: the presence gate of one batch item.

    Returns ``{"probability": p, "present": p > t}``. The test is strict. A NaN ``p`` is not present.
    """
    p = presence_probability(value, activation)
    t = presence_threshold(score_threshold_default, threshold)
    return {"probability": p, "present": bool(p > t)}


def class_probabilities(value: Any, labels: Sequence[str]) -> dict | None:
    """``post.pose.extra_outputs``, Behaviour step 3: the class probabilities of one batch item.

    ``q`` is the probability of ``labels[0]``. ``1 - q`` is the probability of ``labels[1]``. A ``q``
    that is not in ``[0, 1]`` (also NaN) gives no class (``None``). The function chooses no label (user
    decision plan T28 (H5)).
    """
    q = _single_value(value)
    if not (0.0 <= q <= 1.0):
        return None
    return {labels[0]: q, labels[1]: 1.0 - q}


def world_rotation(resize_method: str, crop_roi: Sequence[float] | None = None) -> float:
    """``post.pose.extra_outputs``, Behaviour step 4: the rotation ``theta`` of the world keypoints.

    For ``rotated_roi_crop``, ``theta`` is the rotation of the crop ROI ``Rc``
    (``pre.resize.rotated_roi_crop``, Behaviour step 3). For every other method, ``theta`` is 0.
    """
    if resize_method == "rotated_roi_crop":
        if crop_roi is None or len(crop_roi) != 5:
            raise ValueError("rotated_roi_crop needs the crop ROI of the item")
        return float(crop_roi[4])
    return 0.0


def rotate_world_keypoints(world: Any, rotation: float) -> np.ndarray:
    """``post.pose.extra_outputs``, Behaviour step 4: rotate the world keypoints of one batch item.

    ``X' = cos(theta) * X - sin(theta) * Y``, ``Y' = sin(theta) * X + cos(theta) * Y``, ``Z' = Z``.
    No scale and no translation. The unit does not change.
    """
    w = np.asarray(world, dtype=np.float64)
    if w.ndim != 2 or w.shape[1] != 3:
        raise ValueError("world keypoints of one batch item must have the shape [K, 3]")
    c, s = math.cos(rotation), math.sin(rotation)
    out = w.copy()
    out[:, 0] = c * w[:, 0] - s * w[:, 1]
    out[:, 1] = s * w[:, 0] + c * w[:, 1]
    return out


def decode_extra_outputs(
    outputs: Sequence[Mapping[str, Any]],
    tensors: Mapping[str, Any],
    resize_method: str,
    crop_roi: Sequence[float] | None = None,
    threshold: Any = None,
) -> dict:
    """``post.pose.extra_outputs``, Behaviour steps 1 to 4 for one batch item.

    ``outputs`` is the ``outputs`` list of the sidecar. ``tensors`` maps each output name to the value
    of this batch item. ``keypoints`` is the value of the ``keypoints`` output, unchanged (the
    coordinate decode and the unprojection are other sections). ``threshold`` is the runtime input of
    the presence gate.

    Returns ``{"present", "presence", "keypoints", "classes", "world_keypoints"}``. An item that is not
    present has ``None`` for ``keypoints``, ``classes`` and ``world_keypoints``.
    """
    by_semantic = {o["semantic"]: o for o in outputs}
    result: dict = {"present": True, "presence": None, "keypoints": None, "classes": None,
                    "world_keypoints": None}
    if "presence" in by_semantic:
        o = by_semantic["presence"]
        gate = presence_gate(tensors[o["name"]], o["activation"], o["score_threshold_default"], threshold)
        result["presence"] = gate["probability"]
        result["present"] = gate["present"]
    if not result["present"]:
        return result
    if "keypoints" in by_semantic:
        result["keypoints"] = np.asarray(tensors[by_semantic["keypoints"]["name"]], dtype=np.float64)
    if "binary_class" in by_semantic:
        o = by_semantic["binary_class"]
        result["classes"] = class_probabilities(tensors[o["name"]], o["labels"])
    if "world_keypoints" in by_semantic:
        o = by_semantic["world_keypoints"]
        theta = world_rotation(resize_method, crop_roi)
        result["world_keypoints"] = rotate_world_keypoints(tensors[o["name"]], theta)
    return result
```

## 4. Vectors

The reference file made the cases. A scratch generator of this session
(`hand21-outputs\gen_vectors.py` in the session scratchpad, not committed)
gives each case its inputs and its comment, and it takes the expected values from the reference file
(the template: "Make the vectors with the reference implementation"). It rounds each value with a
tolerance to 12 decimals.

**The tolerances.** The section states no arithmetic precision. Each case whose result has a
floating-point value has its tolerance in `compare`: `1e-6` for a probability (`probability`,
`presence`, `classes`), for an angle (`rotation`) and for a world value in metres (`world`,
`world_keypoints`). A float32 host stays inside these bounds: the float32 rounding of a value below 1
is below `6e-8`. The flags `valid` and `present` and the passed-through `keypoints` must match
exactly.

A scratch runner of this session (`hand21-outputs\run_vectors.py`, with `common.py` beside it) read
this YAML block back from this file and ran each case through the reference file (loaded with
`importlib.util.spec_from_file_location`). Result on 2026-10-24: **81 of 81 pass**
(`validate_extra_outputs` 36, `presence_gate` 20, `class_probabilities` 8, `world_rotation` 4,
`rotate_world_keypoints` 7, `decode_extra_outputs` 6). A mutation check changed one expected value
(heading "Before you stop"): exactly one case failed. Environment: the `uv` environment of
OpenMMLab-Exporter (Python 3.14.2, NumPy 2.5.4, PyYAML 6.0.3).

Cross-checks (not an independent implementation): the scratch measurement of part 1 ran
`presence_gate`, `world_rotation` and `rotate_world_keypoints` on the real outputs of the model. The gate agrees with
the presence of `HolisticLandmarker` for 116 of 116 image crops and 434 of 438 video hand-frames, and
the rotated world keypoints agree within a median of 0.85 mm (image) and 0.91 mm (video).

Coverage: each rule `-1` to `-7` with a pass and a fail (the legacy version, `bottom_up`,
`top_down_multi_person`, `simcc`, no pose role, two presence outputs, a missing or unknown activation,
a missing default, the range ends 0 (in) and 1 (out), above 1, negative, a boolean, NaN, a shape with
two values, rank 3 for a class, the label list (missing, one, the same twice, empty), the world unit
(missing, `pixel`, `mm`), the flat `[N, 63]` world layout, a wrong keypoint count or axis, and the
own fields on other outputs, also at a legacy version); the gate above, at the strict tie, below
(the noise value of MediaPipe-Exporter 0003), a `[1]` value, the runtime threshold lower and higher
than the default, `t = 0` at the tie and above it, `t` near 1, NaN, the sigmoid at the tie, above and
at `±800` (no overflow), and the runtime errors (1, 1.5, −0.1, a boolean, NaN, two values); the
class probabilities above and below 0.5, at the tie, at 0 and 1, and three values that are not
probabilities; the rotation angle for `rotated_roi_crop`, for two other methods and without an ROI;
the rotation by 0, ±π/2, π, 0.5 and 3π, and a flat layout; the full decode of a present item, of an
item that is not present, with a runtime threshold, without a presence output, with another method,
and with a NaN class value.

The target file is `specs/sidecar/vectors/post.pose.extra_outputs.yaml`.

```yaml
section: post.pose.extra_outputs
spec_revision: vNEXT
generated_by: the part 3 code of `specs/sidecar/proposals/landmark-extra-outputs/proposal.md`
unverified: no host implementation. MediaPipe-Exporter has no git repo and no exporter code.
cases:
  # the four outputs of hand_landmark_full (after the reshape of the plan)
  - id: validate-hand-outputs
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right, Left]}, {name: Identity_3, shape: [-1, 21, 3], semantic: world_keypoints, unit: m}]}
    expect: {valid: true}
  # no extra output: the rules pass at every version
  - id: validate-no-extra-legacy
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: false}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}]}
    expect: {valid: true}
  # a presence output of shape [N] (the plan reshape to [B])
  - id: validate-presence-rank-1
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1], semantic: presence, activation: none, score_threshold_default: 0.5}]}
    expect: {valid: true}
  # the shape is optional
  - id: validate-no-shape
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, semantic: presence, activation: none, score_threshold_default: 0.5}, {name: Identity_3, semantic: world_keypoints, unit: m}]}
    expect: {valid: true}
  # score_threshold_default 0 is in [0, 1)
  - id: validate-threshold-zero
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0}]}
    expect: {valid: true}
  # rule -3: 1 is not in [0, 1) (with the strict test no item could pass)
  - id: error-threshold-one
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 1.0}]}
    expect: {error: 'presence.score_threshold_default must be a finite number in [0, 1)'}
  # activation sigmoid (the MediaPipe face flag gets a sigmoid outside the graph)
  - id: validate-sigmoid
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: sigmoid, score_threshold_default: 0.5}]}
    expect: {valid: true}
  # unit mm
  - id: validate-world-mm
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_3, shape: [-1, 21, 3], semantic: world_keypoints, unit: mm}]}
    expect: {valid: true}
  # rule -1: an extra semantic needs vNEXT
  - id: error-legacy
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: false}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right, Left]}, {name: Identity_3, shape: [-1, 21, 3], semantic: world_keypoints, unit: m}]}
    expect: {error: 'the semantics presence, binary_class and world_keypoints need vNEXT'}
  # rule -1: bottom_up is not top_down_single_person
  - id: error-bottom-up
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: bottom_up, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right, Left]}, {name: Identity_3, shape: [-1, 21, 3], semantic: world_keypoints, unit: m}]}
    expect: {error: 'an extra pose output needs role pose_estimator, top_down_single_person and method coordinate'}
  # rule -1: top_down_multi_person
  - id: error-multi-person
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_multi_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right, Left]}, {name: Identity_3, shape: [-1, 21, 3], semantic: world_keypoints, unit: m}]}
    expect: {error: 'an extra pose output needs role pose_estimator, top_down_single_person and method coordinate'}
  # rule -1: the decode method must be coordinate
  - id: error-simcc
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: simcc, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right, Left]}, {name: Identity_3, shape: [-1, 21, 3], semantic: world_keypoints, unit: m}]}
    expect: {error: 'an extra pose output needs role pose_estimator, top_down_single_person and method coordinate'}
  # rule -1: role must include pose_estimator
  - id: error-no-pose-role
    function: validate_extra_outputs
    params: {role: [object_detector], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right, Left]}, {name: Identity_3, shape: [-1, 21, 3], semantic: world_keypoints, unit: m}]}
    expect: {error: 'an extra pose output needs role pose_estimator, top_down_single_person and method coordinate'}
  # rule -2: at most one presence output
  - id: error-two-presence
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5}, {name: flag2, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5}]}
    expect: {error: at most one presence output}
  # rule -3: activation is required
  - id: error-no-activation
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, score_threshold_default: 0.5}]}
    expect: {error: presence.activation must be none or sigmoid}
  # rule -3: activation is none or sigmoid
  - id: error-softmax
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: softmax, score_threshold_default: 0.5}]}
    expect: {error: presence.activation must be none or sigmoid}
  # rule -3: score_threshold_default is required
  - id: error-no-threshold
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none}]}
    expect: {error: 'presence.score_threshold_default must be a finite number in [0, 1)'}
  # rule -3: 1.5 is not in [0, 1)
  - id: error-threshold-above-one
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 1.5}]}
    expect: {error: 'presence.score_threshold_default must be a finite number in [0, 1)'}
  # rule -3: -0.1 is not in [0, 1)
  - id: error-threshold-negative
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: -0.1}]}
    expect: {error: 'presence.score_threshold_default must be a finite number in [0, 1)'}
  # rule -3: a boolean is not a number
  - id: error-threshold-bool
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: true}]}
    expect: {error: 'presence.score_threshold_default must be a finite number in [0, 1)'}
  # rule -3: NaN is not finite
  - id: error-threshold-nan
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: .nan}]}
    expect: {error: 'presence.score_threshold_default must be a finite number in [0, 1)'}
  # rule -6: one value for each batch item
  - id: error-presence-two-values
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 2], semantic: presence, activation: none, score_threshold_default: 0.5}]}
    expect: {error: 'a presence output must have the shape [N] or [N, 1]'}
  # rule -6: [N, 1, 1] is not [N] or [N, 1]
  - id: error-class-shape-rank-3
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_2, shape: [-1, 1, 1], semantic: binary_class, labels: [Right, Left]}]}
    expect: {error: 'a binary_class output must have the shape [N] or [N, 1]'}
  # rule -4: labels is required
  - id: error-labels-missing
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_2, shape: [-1, 1], semantic: binary_class}]}
    expect: {error: binary_class.labels must be two different non-empty strings}
  # rule -4: exactly two labels
  - id: error-labels-one
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right]}]}
    expect: {error: binary_class.labels must be two different non-empty strings}
  # rule -4: the two labels must differ
  - id: error-labels-same
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right, Right]}]}
    expect: {error: binary_class.labels must be two different non-empty strings}
  # rule -4: a label must not be empty
  - id: error-labels-empty
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right, '']}]}
    expect: {error: binary_class.labels must be two different non-empty strings}
  # rule -5: unit is required
  - id: error-world-no-unit
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_3, shape: [-1, 21, 3], semantic: world_keypoints}]}
    expect: {error: world_keypoints.unit must be m or mm}
  # rule -5: unit is m or mm
  - id: error-world-pixel
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_3, shape: [-1, 21, 3], semantic: world_keypoints, unit: pixel}]}
    expect: {error: world_keypoints.unit must be m or mm}
  # rule -5: the flat [N, 63] layout of the probe conversion
  - id: error-world-flat
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_3, shape: [-1, 63], semantic: world_keypoints, unit: m}]}
    expect: {error: 'a world_keypoints output must have the shape [N, K, 3]'}
  # rule -5: 20 keypoints for 21 tracked points
  - id: error-world-count
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_3, shape: [-1, 20, 3], semantic: world_keypoints, unit: m}]}
    expect: {error: the keypoint axis of world_keypoints must have len(tracked_points) values}
  # rule -5: keypoint_axis must be 1
  - id: error-world-axis
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_3, shape: [-1, 21, 3], semantic: world_keypoints, unit: m, keypoint_axis: 2}]}
    expect: {error: world_keypoints.keypoint_axis must be 1}
  # rule -5: keypoint_count must equal len(tracked_points)
  - id: error-world-keypoint-count
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_3, shape: [-1, 21, 3], semantic: world_keypoints, unit: m, keypoint_count: 20}]}
    expect: {error: keypoint_count must equal len(pose.tracked_points)}
  # rule -7: score_threshold_default on a keypoints output
  - id: error-own-field-keypoints
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints, score_threshold_default: 0.5}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5}]}
    expect: {error: score_threshold_default is valid only on a presence output}
  # rule -7: labels on a presence output
  - id: error-own-field-presence
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: true}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5, labels: [a, b]}]}
    expect: {error: labels is valid only on a binary_class output}
  # rule -7 applies also without an extra output, and at every version
  - id: error-own-field-no-extra
    function: validate_extra_outputs
    params: {role: [pose_estimator], estimator_type: top_down_single_person, method: coordinate, keypoint_count: 21, schema_is_vnext: false}
    input: {outputs: [{name: Identity, shape: [-1, 21, 3], semantic: keypoints, unit: m}]}
    expect: {error: unit is valid only on a world_keypoints output}
  # 0.51 > 0.5
  - id: gate-above
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: 0.51}
    expect: {probability: 0.51, present: true}
    compare: {probability: {atol: 1.0e-06}}
  # 0.5 > 0.5 is false: the test is strict (ThresholdingCalculator)
  - id: gate-tie
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: 0.5}
    expect: {probability: 0.5, present: false}
    compare: {probability: {atol: 1.0e-06}}
  # 0.0031: the hand flag on a noise input (MediaPipe-Exporter 0003)
  - id: gate-noise
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: 0.0031}
    expect: {probability: 0.0031, present: false}
    compare: {probability: {atol: 1.0e-06}}
  # a [1] value of one batch item
  - id: gate-one-value-list
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: [0.7]}
    expect: {probability: 0.7, present: true}
    compare: {probability: {atol: 1.0e-06}}
  # the runtime threshold 0.2 replaces the default 0.5
  - id: gate-runtime-lower
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: 0.3, threshold: 0.2}
    expect: {probability: 0.3, present: true}
    compare: {probability: {atol: 1.0e-06}}
  # the runtime threshold 0.9 replaces the default 0.5
  - id: gate-runtime-higher
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: 0.7, threshold: 0.9}
    expect: {probability: 0.7, present: false}
    compare: {probability: {atol: 1.0e-06}}
  # t = 0 and p = 0: the strict test fails
  - id: gate-runtime-zero-tie
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: 0.0, threshold: 0.0}
    expect: {probability: 0.0, present: false}
    compare: {probability: {atol: 1.0e-06}}
  # t = 0 and a small p > 0
  - id: gate-runtime-zero-above
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: 1.0e-06, threshold: 0.0}
    expect: {probability: 1.0e-06, present: true}
    compare: {probability: {atol: 1.0e-06}}
  # t = 0.999 and p = 1: present
  - id: gate-runtime-near-one
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: 1.0, threshold: 0.999}
    expect: {probability: 1.0, present: true}
    compare: {probability: {atol: 1.0e-06}}
  # the runtime threshold 1 is not in [0, 1) (the range of the refiner score gate)
  - id: error-runtime-one
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: 1.0, threshold: 1.0}
    expect: {error: 'the presence threshold must be a finite number in [0, 1)'}
  # a NaN value is not present
  - id: gate-nan
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: .nan}
    expect: {probability: .nan, present: false}
  # sigmoid(0) = 0.5, and 0.5 > 0.5 is false
  - id: gate-sigmoid-tie
    function: presence_gate
    params: {activation: sigmoid, score_threshold_default: 0.5}
    input: {value: 0.0}
    expect: {probability: 0.5, present: false}
    compare: {probability: {atol: 1.0e-06}}
  # sigmoid(2) = 0.8808
  - id: gate-sigmoid-above
    function: presence_gate
    params: {activation: sigmoid, score_threshold_default: 0.5}
    input: {value: 2.0}
    expect: {probability: 0.880797077978, present: true}
    compare: {probability: {atol: 1.0e-06}}
  # sigmoid(-800) = 0 with no overflow
  - id: gate-sigmoid-large-negative
    function: presence_gate
    params: {activation: sigmoid, score_threshold_default: 0.5}
    input: {value: -800.0}
    expect: {probability: 0.0, present: false}
    compare: {probability: {atol: 1.0e-06}}
  # sigmoid(800) = 1 with no overflow; 1 > 0.5
  - id: gate-sigmoid-large-positive
    function: presence_gate
    params: {activation: sigmoid, score_threshold_default: 0.5}
    input: {value: 800.0}
    expect: {probability: 1.0, present: true}
    compare: {probability: {atol: 1.0e-06}}
  # the runtime threshold must be in [0, 1)
  - id: error-runtime-above-one
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: 0.7, threshold: 1.5}
    expect: {error: 'the presence threshold must be a finite number in [0, 1)'}
  # the runtime threshold must be in [0, 1)
  - id: error-runtime-negative
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: 0.7, threshold: -0.1}
    expect: {error: 'the presence threshold must be a finite number in [0, 1)'}
  # a boolean is not a number
  - id: error-runtime-bool
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: 0.7, threshold: true}
    expect: {error: 'the presence threshold must be a finite number in [0, 1)'}
  # a NaN threshold is not finite
  - id: error-runtime-nan
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: 0.7, threshold: .nan}
    expect: {error: 'the presence threshold must be a finite number in [0, 1)'}
  # two values for one batch item
  - id: error-two-values
    function: presence_gate
    params: {activation: none, score_threshold_default: 0.5}
    input: {value: [0.7, 0.2]}
    expect: {error: a presence or binary_class value must have one value for each batch item}
  # q = 0.9 is the probability of labels[0]
  - id: class-right
    function: class_probabilities
    params: {labels: [Right, Left]}
    input: {value: 0.9}
    expect: {classes: {Right: 0.9, Left: 0.1}}
    compare: {classes: {atol: 1.0e-06}}
  # q = 0.2: the probability of labels[1] is 0.8
  - id: class-left
    function: class_probabilities
    params: {labels: [Right, Left]}
    input: {value: 0.2}
    expect: {classes: {Right: 0.2, Left: 0.8}}
    compare: {classes: {atol: 1.0e-06}}
  # q = 0.5: no label choice; both probabilities are 0.5
  - id: class-tie
    function: class_probabilities
    params: {labels: [Right, Left]}
    input: {value: 0.5}
    expect: {classes: {Right: 0.5, Left: 0.5}}
    compare: {classes: {atol: 1.0e-06}}
  # q = 0
  - id: class-zero
    function: class_probabilities
    params: {labels: [Right, Left]}
    input: {value: 0.0}
    expect: {classes: {Right: 0.0, Left: 1.0}}
    compare: {classes: {atol: 1.0e-06}}
  # q = 1
  - id: class-one
    function: class_probabilities
    params: {labels: [Right, Left]}
    input: {value: 1.0}
    expect: {classes: {Right: 1.0, Left: 0.0}}
    compare: {classes: {atol: 1.0e-06}}
  # q = 1.2 is not a probability: no class
  - id: class-above-one
    function: class_probabilities
    params: {labels: [Right, Left]}
    input: {value: 1.2}
    expect: {classes: null}
  # q = -0.1: no class
  - id: class-negative
    function: class_probabilities
    params: {labels: [Right, Left]}
    input: {value: -0.1}
    expect: {classes: null}
  # q = NaN: no class
  - id: class-nan
    function: class_probabilities
    params: {labels: [Right, Left]}
    input: {value: .nan}
    expect: {classes: null}
  # theta is the rotation of the crop ROI Rc
  - id: rotation-rotated-roi-crop
    function: world_rotation
    params: {resize_method: rotated_roi_crop}
    input: {crop_roi: [301.918, 196.49, 108.0, 108.0, 0.5]}
    expect: {rotation: 0.5}
    compare: {rotation: {atol: 1.0e-06}}
  # every other method has rotation 0
  - id: rotation-affine-person-crop
    function: world_rotation
    params: {resize_method: affine_person_crop}
    input: {}
    expect: {rotation: 0.0}
    compare: {rotation: {atol: 1.0e-06}}
  # every other method has rotation 0
  - id: rotation-letterbox
    function: world_rotation
    params: {resize_method: letterbox}
    input: {}
    expect: {rotation: 0.0}
    compare: {rotation: {atol: 1.0e-06}}
  # rotated_roi_crop needs the crop ROI of the item
  - id: error-rotation-no-roi
    function: world_rotation
    params: {resize_method: rotated_roi_crop}
    input: {}
    expect: {error: rotated_roi_crop needs the crop ROI of the item}
  # rotation 0: no change
  - id: world-rotation-zero
    function: rotate_world_keypoints
    params: {rotation: 0.0}
    input: {world: [[0.01, 0.0, 0.002], [0.0, -0.02, 0.004]]}
    expect: {world: [[0.01, 0.0, 0.002], [0.0, -0.02, 0.004]]}
    compare: {world: {atol: 1.0e-06}}
  # +pi/2 (clockwise on the image): the x axis goes to +y; z does not change
  - id: world-quarter-turn
    function: rotate_world_keypoints
    params: {rotation: 1.5707963267948966}
    input: {world: [[1.0, 0.0, 0.3], [0.0, 1.0, -0.3]]}
    expect: {world: [[0.0, 1.0, 0.3], [-1.0, 0.0, -0.3]]}
    compare: {world: {atol: 1.0e-06}}
  # -pi/2: the x axis goes to -y
  - id: world-minus-quarter-turn
    function: rotate_world_keypoints
    params: {rotation: -1.5707963267948966}
    input: {world: [[1.0, 0.0, 0.3]]}
    expect: {world: [[0.0, -1.0, 0.3]]}
    compare: {world: {atol: 1.0e-06}}
  # pi: x and y change sign
  - id: world-half-turn
    function: rotate_world_keypoints
    params: {rotation: 3.141592653589793}
    input: {world: [[1.0, 2.0, 3.0]]}
    expect: {world: [[-1.0, -2.0, 3.0]]}
    compare: {world: {atol: 1.0e-06}}
  # 0.5 rad on two points; no scale and no translation
  - id: world-general
    function: rotate_world_keypoints
    params: {rotation: 0.5}
    input: {world: [[0.01, 0.0, 0.002], [0.0, -0.02, 0.004]]}
    expect: {world: [[0.008775825619, 0.004794255386, 0.002], [0.009588510772, -0.017551651238, 0.004]]}
    compare: {world: {atol: 1.0e-06}}
  # 3 pi gives the same result as pi
  - id: world-no-range-limit
    function: rotate_world_keypoints
    params: {rotation: 9.42477796076938}
    input: {world: [[1.0, 2.0, 3.0]]}
    expect: {world: [[-1.0, -2.0, 3.0]]}
    compare: {world: {atol: 1.0e-06}}
  # the flat 63 values of one item are not [K, 3]
  - id: error-rotate-flat
    function: rotate_world_keypoints
    params: {rotation: 0.0}
    input: {world: [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62]]}
    expect: {error: 'world keypoints of one batch item must have the shape [K, 3]'}
  # present: keypoints unchanged, classes, world rotated by pi/2
  - id: decode-present
    function: decode_extra_outputs
    params: {outputs: [{name: Identity, shape: [-1, 2, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right, Left]}, {name: Identity_3, shape: [-1, 2, 3], semantic: world_keypoints, unit: m}], resize_method: rotated_roi_crop}
    input: {tensors: {Identity: [[10.0, 20.0, 0.5], [30.0, 40.0, -1.0]], Identity_1: [0.97], Identity_2: [0.12], Identity_3: [[0.01, 0.0, 0.002], [0.0, -0.02, 0.004]]}, crop_roi: [301.918, 196.49, 108.0, 108.0, 1.5707963267948966]}
    expect: {present: true, presence: 0.97, keypoints: [[10.0, 20.0, 0.5], [30.0, 40.0, -1.0]], classes: {Right: 0.12, Left: 0.88}, world_keypoints: [[0.0, 0.01, 0.002], [0.02, 0.0, 0.004]]}
    compare: {presence: {atol: 1.0e-06}, classes: {atol: 1.0e-06}, world_keypoints: {atol: 1.0e-06}}
  # 0.2 fails 0.5: no keypoints, no class, no world keypoints
  - id: decode-not-present
    function: decode_extra_outputs
    params: {outputs: [{name: Identity, shape: [-1, 2, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right, Left]}, {name: Identity_3, shape: [-1, 2, 3], semantic: world_keypoints, unit: m}], resize_method: rotated_roi_crop}
    input: {tensors: {Identity: [[10.0, 20.0, 0.5], [30.0, 40.0, -1.0]], Identity_1: [0.2], Identity_2: [0.12], Identity_3: [[0.01, 0.0, 0.002], [0.0, -0.02, 0.004]]}, crop_roi: [301.918, 196.49, 108.0, 108.0, 1.5707963267948966]}
    expect: {present: false, presence: 0.2, keypoints: null, classes: null, world_keypoints: null}
    compare: {presence: {atol: 1.0e-06}}
  # the runtime threshold 0.1: 0.2 passes
  - id: decode-runtime-threshold
    function: decode_extra_outputs
    params: {outputs: [{name: Identity, shape: [-1, 2, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right, Left]}, {name: Identity_3, shape: [-1, 2, 3], semantic: world_keypoints, unit: m}], resize_method: rotated_roi_crop}
    input: {tensors: {Identity: [[10.0, 20.0, 0.5], [30.0, 40.0, -1.0]], Identity_1: [0.2], Identity_2: [0.12], Identity_3: [[0.01, 0.0, 0.002], [0.0, -0.02, 0.004]]}, crop_roi: [301.918, 196.49, 108.0, 108.0, 1.5707963267948966], threshold: 0.1}
    expect: {present: true, presence: 0.2, keypoints: [[10.0, 20.0, 0.5], [30.0, 40.0, -1.0]], classes: {Right: 0.12, Left: 0.88}, world_keypoints: [[0.0, 0.01, 0.002], [0.02, 0.0, 0.004]]}
    compare: {presence: {atol: 1.0e-06}, classes: {atol: 1.0e-06}, world_keypoints: {atol: 1.0e-06}}
  # without a presence output every item is present
  - id: decode-no-presence-output
    function: decode_extra_outputs
    params: {outputs: [{name: Identity, shape: [-1, 2, 3], semantic: keypoints}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right, Left]}, {name: Identity_3, shape: [-1, 2, 3], semantic: world_keypoints, unit: m}], resize_method: rotated_roi_crop}
    input: {tensors: {Identity: [[10.0, 20.0, 0.5], [30.0, 40.0, -1.0]], Identity_1: [0.97], Identity_2: [0.12], Identity_3: [[0.01, 0.0, 0.002], [0.0, -0.02, 0.004]]}, crop_roi: [301.918, 196.49, 108.0, 108.0, 1.5707963267948966]}
    expect: {present: true, presence: null, keypoints: [[10.0, 20.0, 0.5], [30.0, 40.0, -1.0]], classes: {Right: 0.12, Left: 0.88}, world_keypoints: [[0.0, 0.01, 0.002], [0.02, 0.0, 0.004]]}
    compare: {classes: {atol: 1.0e-06}, world_keypoints: {atol: 1.0e-06}}
  # affine_person_crop: rotation 0, the world keypoints do not change
  - id: decode-other-method
    function: decode_extra_outputs
    params: {outputs: [{name: Identity, shape: [-1, 2, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right, Left]}, {name: Identity_3, shape: [-1, 2, 3], semantic: world_keypoints, unit: m}], resize_method: affine_person_crop}
    input: {tensors: {Identity: [[10.0, 20.0, 0.5], [30.0, 40.0, -1.0]], Identity_1: [0.97], Identity_2: [0.12], Identity_3: [[0.01, 0.0, 0.002], [0.0, -0.02, 0.004]]}}
    expect: {present: true, presence: 0.97, keypoints: [[10.0, 20.0, 0.5], [30.0, 40.0, -1.0]], classes: {Right: 0.12, Left: 0.88}, world_keypoints: [[0.01, 0.0, 0.002], [0.0, -0.02, 0.004]]}
    compare: {presence: {atol: 1.0e-06}, classes: {atol: 1.0e-06}, world_keypoints: {atol: 1.0e-06}}
  # present, but q is NaN: no class
  - id: decode-class-nan
    function: decode_extra_outputs
    params: {outputs: [{name: Identity, shape: [-1, 2, 3], semantic: keypoints}, {name: Identity_1, shape: [-1, 1], semantic: presence, activation: none, score_threshold_default: 0.5}, {name: Identity_2, shape: [-1, 1], semantic: binary_class, labels: [Right, Left]}, {name: Identity_3, shape: [-1, 2, 3], semantic: world_keypoints, unit: m}], resize_method: rotated_roi_crop}
    input: {tensors: {Identity: [[10.0, 20.0, 0.5], [30.0, 40.0, -1.0]], Identity_1: [0.97], Identity_2: [.nan], Identity_3: [[0.01, 0.0, 0.002], [0.0, -0.02, 0.004]]}, crop_roi: [301.918, 196.49, 108.0, 108.0, 1.5707963267948966]}
    expect: {present: true, presence: 0.97, keypoints: [[10.0, 20.0, 0.5], [30.0, 40.0, -1.0]], classes: null, world_keypoints: [[0.0, 0.01, 0.002], [0.02, 0.0, 0.004]]}
    compare: {presence: {atol: 1.0e-06}, world_keypoints: {atol: 1.0e-06}}
```

## 5. Parity evidence

One parity script serves the four MediaPipe proposals (user decision plan T28 (H6);
`specs/exporter-guide/sidecars/workflow/phase-2-proposal.md:24-26`): `notes/decisions/scripts/hand_chain_parity.py` (to write).
It runs the hand branch as the 0020 proposal and the refiner proposal describe it, and it adds the
outputs of this proposal and of the depth proposal. The four parts 5 cite it. Each proposal keeps
its gates. This part gives the gates of the extra outputs.

| Item | Value |
|---|---|
| Gates, set before the run, and their source | Set on 2026-10-24, before the run of the committed parity script. The scratch measurement of part 1 ran before these gates were set. Its numbers are the source of the gates, as in the 0020 proposal (part 5, gate (3): 1.1 times the measured value, rounded up to 0.01; a count of outliers). (1) **Presence decisions** against `HolisticLandmarker`: the hand is present in both or in neither. Image set: 0 disagreements of 116 crops. Video set: at most 5 of 438 hand-frames. These are the presence gates of the 0020 proposal (part 5, gate (3)); measured 0 and 4. (2) **World keypoints**, for each hand that both give: the largest absolute difference over the 21 points and the 3 axes, in mm, after the subtraction of the wrist (point 0) from both sides. Image set: median `<= 0.94` mm, p95 `<= 4.33` mm, 0 hands above 10 mm. Video set: median `<= 1.00` mm, p95 `<= 5.87` mm, at most 6 hand-frames above 10 mm. Measured: image median 0.847, p95 3.933, largest 6.40, 0 above 10 mm; video median 0.907, p95 5.328, largest 20.73, 5 above 10 mm. The largest video value is the hand-frame whose landmark error is 16.99 px (frame 35, the outlier of the 0020 proposal: a different ROI choice). A path without the rotation of step 4 must fail gate (2) (measured median 107.5 mm). (3) **Class probabilities**: no gate against the upstream library, because no upstream output exists for a known crop (part 1). The physical side of `Right` has its own committed check, OpenMMLab-Exporter 0041 (secondary; committed script; part 1, measured difference). The parity script does not repeat it. The export error of the handedness (gate of step 3 of "Parity") is `<= 1e-5` against TFLite, above the 2.9e-6 of MediaPipe-Exporter 0003. |
| Test images (paths or dataset IDs), and the branch that each image runs | The sets of MediaPipe-Exporter 0006 (`notes/decisions/0006-holistic-end-to-end-parity.md:31-35`): the 60 largest single-person COCO val2017 images with a visible wrist (IMAGE mode), and the first 300 frames of `sesh_2022-09-19_16_16_50_in_class_jsm_synced_Cam1.mp4` (VIDEO mode). Branches that run: present and not present (31 image crops and 101 video hand-frames have no Holistic hand), the rotation of step 4 at many angles (left and right hands in many poses), `activation: none`. Not run on a real image: `activation: sigmoid` (no model in scope), a runtime threshold other than 0.5, a class value that is not a probability, `unit: mm`, a resize method other than `rotated_roi_crop`. The vectors cover these branches. |
| Upstream reference: library, version, config and command | `mediapipe` 1.1.1, `HolisticLandmarker` with `holistic_landmarker.task` `float16/1` (MediaPipe-Exporter 0016), default options (`min_hand_landmarks_confidence` 0.5). It outputs the hand landmarks and the hand world landmarks (`holistic_landmarker.py:52-53, 78-94`, installed copy). It does not output the hand flag, the handedness or the ROI. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | to run (MediaPipe-Exporter 0003 gives, from an uncommitted probe on random inputs and COCO crops: flag 3.1e-6, handedness 2.9e-6, world 6.0e-7 m for `full`) |
| Preprocessed input: maximum absolute difference for each image | to run. The input crop is the scope of the 0020 proposal (its part 5, gate (1)). |
| Row count for each image: sidecar path and upstream | to run. One pose or no pose for each hand crop, compared with the presence of the Holistic hand (gate (1)). Scratch (secondary): image 85 and 85 hands present, 31 and 31 not present; video 335 and 337 present. |
| Final outputs in source-image coordinates: metric and value for each role | to run. `pose_estimator`: the world keypoints (gate (2)). The landmarks `x`, `y` are gate (3) of the 0020 proposal; their depth is the depth proposal. Scratch (secondary): the values in the gates row. |
| Result (`pass`, `fail` or `to run`) | to run (MediaPipe-Exporter has no git repo, so a script cannot be committed) |
| Script path in the exporter repo | `notes/decisions/scripts/hand_chain_parity.py` (to write; user decision plan T28 (H6): the script of the four MediaPipe proposals). It copies the chain of `holistic_parity.py` (MediaPipe-Exporter 0006) with the crops and the inverse of the 0020 reference file and the refiner decode of the refiner reference file (the path A of the scratch measurement). It runs the four outputs of `hand_landmark_full`. It applies `decode_extra_outputs` of this reference file (the gate with the default threshold, the rotation with the crop ROI `Rc`) and `decode_depth` of the depth reference file. It compares the presence decisions, the world keypoints after the wrist subtraction (gate (2)) and the depth (gate of the depth proposal) with `HolisticLandmarker`. It writes `model_cache/probes/hand_chain_parity.json`. The scratch script `measure_extra.py` (part 1) is a draft of it. |
| Exporter commit of the script | none (no git repo) |
| Command | `uv run --script notes/decisions/scripts/hand_chain_parity.py --n-images 60 --n-frames 300` (to run) |

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | New module `skellytracker/core/detectors/processing/pose_extra_outputs.py` with the functions of the reference file: `presence_gate` (with `presence_probability` and `presence_threshold`), `class_probabilities`, `world_rotation`, `rotate_world_keypoints` and `decode_extra_outputs`. |
| Dispatch point | For the implementer. The `coordinate` decode has no package code today: the front matter of `post.pose.decode.coordinate` says `decode: missing` (`specs/sidecar/post/pose-decode-coordinate.md:12`). The decode of a single-person `coordinate` model must call `decode_extra_outputs` for each batch item after the model runs, and before it unprojects the keypoints. An item that is not present gives no observation. The runtime threshold is a config field of the keypoint detector, with the sidecar default. The MediaPipe hand detector of the package has the same kind of field today: `min_hand_presence_confidence: float = 0.5` (`skellytracker/core/detectors/keypoint_detectors/mediapipe/hands/mediapipe_hand_detector.py:38`). The world rotation needs the crop ROI `Rc` of `rotated_roi_crop` (the `resize_meta` of the 0020 proposal, its part 6). |
| Validator changes (`model.py`, with rule IDs) | `OutputSemantic` (`skellytracker/core/sidecar/model.py:27`): add `presence`, `binary_class` and `world_keypoints` (`V-common.outputs-4`). `OutputSpec` (`:187-208`): add the optional fields `activation`, `score_threshold_default`, `labels` and `unit`. Its `_check_output` checks rules `-3` to `-7` (each field only on its semantic, the required fields, the ranges, the shapes). `SidecarModel._check_pose_output_shapes` (`:553-581`): in the `coordinate` branch, count at most one output of each extra semantic (`-2`), and require `top_down_single_person` for them (`-1`); add `world_keypoints` to the list of semantics whose `keypoint_count` it checks (`:575-581`, `V-post.pose.schema-8`). Gate every new rule on `schema_version >= vNEXT`, except rule `-7`. |
| Tests | The vectors `specs/sidecar/vectors/post.pose.extra_outputs.yaml` against `pose_extra_outputs.py`; the runner compares each field with the `atol` of its `compare`. Validation tests in `skellytracker/tests/sidecar/test_model_validation.py` for each new and changed rule. A golden parity test: one hand crop with a hand and one without, with the flag, the class probabilities and the rotated world keypoints of the ONNX model. |
| Existing code that the change touches | `skellytracker/core/sidecar/model.py`: `OutputSemantic`, `OutputSpec`, `SidecarModel._check_pose_output_shapes`. `skellytracker/core/data_primitives/keypoints.py:10-20`: `Keypoints` has `xyz` and a per-point `visibility` only, so a presence score of the instance, class probabilities and world keypoints need a place in the observation (for the implementer). `skellytracker/core/detectors/keypoint_detectors/mediapipe/hands/mediapipe_hand_detector.py:36-48, 118-160`: the package runs the MediaPipe library today, not the ONNX file; its `assumed_handedness` ignores the label of MediaPipe for a crop of one known side. That is a host choice, and it stays valid with this section. |

## 7. Exporter impact

| Exporter | Affected sidecars | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | none (no model with these outputs) | none | none |
| Roboflow-Exporter | none | none | none |
| Ultralytics-Exporter | none | none | none |
| Qualcomm-Exporter | The historical MediaPipe hand and face landmark sidecars (skellytracker 0021 `:55-56`: the wrapper keeps only the landmarks) | Out of the `vNEXT` scope (skellytracker 0008 `:15`). If it writes the sidecars again, it can keep the flag, the handedness and the world landmarks in the ONNX file and declare them with this section. Its plan uses `positive_class: right` (skellytracker 0021 `:53-54`): with this section, `labels: [Right, Left]`. | none (no host decoder today) |
| MediaPipe-Exporter (proposing) | The hand landmark sidecar (`full`, `lite`) | New fields: the YAML excerpt of part 2.2. The plan contract must change: `handedness` is the probability of `Right` (label item 0), not "the probability of `Left` (assumes a mirrored image)" (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts), secondary), and `Right` is the right hand of the person in an image that is not mirrored (part 2.3, "Fields"); the plan reshapes `hand_score` and `handedness` to `[B]` (`:203-204`), which rule `-6` allows; `world_landmarks` is `[B, 21, 3]` in metres (`:205`), which rule `-5` requires. The face landmark model (a later family) has a face flag that needs `activation: sigmoid` (part 2.3). | The host gate, class probabilities and world rotation are `decode_extra_outputs` of the reference file. The tracking ROI of the next frame (intake row X2) uses only the landmarks of an item that is present. |
| skellytracker package sidecars | none | none. They have `schema_version: "v2024.09.1019"`, and no package sidecar declares these semantics. | none |
| skellytracker spec examples | none | none. No example has these outputs. | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| **The near-miss: declare only the `keypoints` output** (and drop the other outputs in the exporter, the historical Qualcomm-Exporter wrapper) | The host cannot reject a crop with no hand. On the 0006 sets, 31 of 116 image crops and 101 of 438 video hand-frames have no Holistic hand, and the model still gives 21 landmarks for each. The world landmarks and the handedness are lost. skellytracker 0021 rejects it too (`:60-61`). | Part 1, measured difference; skellytracker 0021 `:34-36` |
| **The semantic `score` for the flag and the handedness** (the direction of skellytracker 0021, `:13-14`, from the two exporter plans) | `scores` is a detection semantic that requires `object_detector` (`common/outputs.md:35, 44`). A second value `score` with another meaning is easy to confuse with it. The flag and the handedness also need different fields (a gate, labels). Two semantics with their own fields are clearer. | `specs/sidecar/common/outputs.md:29, 35, 44` |
| **The semantic `keypoints_3d` for the world landmarks** (skellytracker 0021 `:13-14`) | A `keypoints` output with `is_3d: true` already gives 3D keypoints in the image (`post/pose-schema.md:92`). `keypoints_3d` does not tell the two apart. `world_keypoints` names the metric frame. | `specs/sidecar/post/pose-schema.md:92-93` |
| **A fixed threshold in the sidecar** (no runtime input) | Plan T26 (6) makes the refiner gate a runtime input with a default. MediaPipe makes the presence threshold an option of the user (`min_hand_landmarks_confidence`, part 1 other source (b)). A test of another body parent, or another threshold, needs another value (plan T27). | Plan T26 (6), T27; `holistic_landmarker.py:268` |
| **The comparison `>=`** (skellytracker 0021 `:16-17`) | MediaPipe uses a strict `>` (`thresholding_calculator.cc:123-124`; MediaPipe-Exporter 0005). The spec uses strict thresholds elsewhere (`post/detection-decode.md:42`). | Part 1 |
| **The range `[0, 1]` for the threshold** (as `V-post.det.decode-8` and the MediaPipe option check) | With the strict test, `t = 1` drops every item. The refiner proposal uses `[0, 1)` for the same pattern. One range for the two gates of the same pipeline is simpler. Rejected by user decision plan T28 (H4), Q3. | `post/detection-decode.md:77`; `hand_landmarks_detector_graph.cc:94-104`; refiner proposal `:308` |
| **No `activation` field** (the hand flag has its sigmoid in the graph) | The face landmark model of the same pipeline gets its sigmoid outside the graph (`face_landmarks_detector_graph.cc:306-320`). Without the field, its sidecar has no value. A required field removes a wrong default (the lesson of `fit` `pad_value`, skellytracker 0012). | Part 1 |
| **`positive_class: right` only** (skellytracker 0021 `:17-18, 53-54`, the Qualcomm-Exporter plan) | One label does not give the name of the other class. `labels` keeps both upstream label items in their order, as the upstream `label_items` do. | `hand_landmarks_detector_graph.cc:134-141` |
| **`assumes_mirrored_input`** (skellytracker 0021 `:17-18, 48-49`, from the MediaPipe-Exporter plan) | The legacy documentation at the pin (`docs/solutions/hands.md`, secondary) says that the model assumes a mirrored input. That sentence applies to the legacy label map, which has `Left` at item 0; with the Tasks labels it gives the same hand as the measurements (OpenMMLab-Exporter 0052; part 1, corrections; part 2.3, notes). The plan fact "probability of `Left` for a mirrored image" came from a legacy label file (MediaPipe-Exporter 0021 item 2). User decision plan T28 (H3): the section states the physical side of the label as a fact of the model (part 2.3, "Fields"). The committed measurement OpenMMLab-Exporter 0041 (secondary; committed script; part 1) shows that `Right` is the right hand of the person in an image that is not mirrored. A field would let a sidecar state the other side. | Part 1; part 2.3 notes |
| **A label choice** (`labels[0]` if `q > 0.5`) | The upstream tie rule is not in the cache, and Holistic does not use the handedness. The host can choose a label from the two probabilities. Rejected by user decision plan T28 (H5), Q4. | Part 2.3 notes |
| **Unproject the world keypoints like image points**, or leave them unrotated | World points are metric points, not image points: the crop scale and centre do not apply. Unrotated world keypoints differ from Holistic by a median of 107.5 mm (image) and 161.9 mm (video); the rotation of step 4 gives 0.85 mm and 0.91 mm. | Part 1, measured difference; `world_landmark_projection_calculator.cc:41-64` |
| **Put the alignment to the pose world wrist into this section** | It uses the output of another model (the pose world landmarks). It is a step of the Holistic pipeline, not of this model (intake row X5, `out of scope`). | `docs/mediapipe-whole-body.md:409-410` |
| **The extra fields in `pose.decode`** (for example `pose.decode.presence_threshold_default`) | The fields describe one output tensor (its activation, its labels, its unit). The spec puts the fields of a tensor on its `outputs` entry (`fields`, `keypoint_axis`, `packed_keypoints`). | `specs/sidecar/common/outputs.md:21-29`; `post/pose-schema.md:51-54` |
| **Three proposals, one for each output** | Skellytracker 0021 is one gap record for the three outputs, and the guide says: use its slug and do not compete. The three outputs share one contract unit: one section with one reference module. | `specs/exporter-guide/sidecars/workflow/phase-2-proposal.md:13-23` |
| **Allow the extra outputs for bottom-up and multi-person models** | No model in scope has them. A bottom-up model has a per-row score already (`post/pose-bottom-up.md`). A later proposal can extend rule `-1`. | `post/pose-bottom-up.md:25` |

## Open questions for the user

Decided by the user on 2026-10-24 (plan T28). No question of plan T28 stays open. The question on
the kind of the H3 evidence was decided on 2026-10-25 (plan T45; Q2 below; part 1, "Missing primary
evidence"). No question stays open.

- **Q1 (the revision) = H2.** The change goes into `vNEXT`, on the scope extension of the 0020
  proposal (user decision 2026-10-23 (4)). skellytracker 0021 asks for this decision (`:23-25`). Parts 1 and 2.6.
- **Q2 (the physical side) = H3.** The spec states which physical hand the label `Right` names:
  the right hand of the person in an image that is not mirrored, and the left hand of the person in
  a mirrored image (part 2.3, "Fields"). The evidence is OpenMMLab-Exporter decision 0041 (secondary; committed
  script; commit `9deff61`, merged in `32ab848`; script `notes/decisions/scripts/rtmw_wrist_gate_handedness.py`).
  The ground truth is the COCO-WholeBody annotation (the left and right hand labels). The MediaPipe
  hand ROI and hand landmark ONNX models ran on CUDA. Result: +0.807 not mirrored and −0.766
  mirrored, against `>= 0.6` and `<= -0.6` (part 1). It is a committed exporter measurement of the
  model on a dataset, not upstream evidence. An earlier scratch measurement on the COCO val2017 body
  keypoints (secondary, no committed script) agrees. OpenMMLab-Exporter 0052 (2026-10-25) runs the
  upstream `HandLandmarker` with the model of this proposal: +0.861 and −0.862. It also shows that the
  legacy sentence on a mirrored input agrees, because it applies to the legacy label map (part 2.3,
  notes). Decided (user, 2026-10-25, plan T45): plan T31 is the exception that accepts
  OpenMMLab-Exporter 0041 and 0052 in place of a primary source for the physical side (part 1,
  "Missing primary evidence"). History: this was open until 2026-10-25.
- **Q3 (the threshold) = H4.** The presence threshold is a runtime input with the default
  `score_threshold_default`, in `[0, 1)`, the range of the refiner gate (parts 2.2, 2.3 and 2.4,
  rule `-3`).
- **Q4 (a label) = H5.** The section has no label rule. It gives only the probability of `labels[0]`
  (and `1 - q` for `labels[1]`) (part 2.3, step 3 and notes).
- **Q5 (the parity script) = H6.** One script for the four MediaPipe proposals:
  `notes/decisions/scripts/hand_chain_parity.py` (part 5). The 0020, refiner and depth proposals cite
  it in their parts 5. Each proposal keeps its gates.

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake links to this proposal (rows D1b, D1c and D1d, and "Proposals and reference files",
      2026-10-24).
- [x] The header gives the dependencies (the 0020 proposal) and `Needed by: none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property
      (skellytracker 0021; also skellytracker 0019, 0020 and 0022). This proposal builds on
      skellytracker 0021. It does not compete with it.
- [x] Part 1 cites primary evidence (`docs/mediapipe-whole-body.md`, user designation, and the
      MediaPipe source), and it names the primary evidence that is missing (the upstream handedness
      for a known crop, an upstream source for the physical side, the origin of the world keypoints,
      the exporter export). Updated 2026-10-24: the physical side has the committed measurement
      OpenMMLab-Exporter 0041 (secondary; committed script; commit `9deff61`). It is not upstream
      evidence, so the item stays in the list. Acceptance needs an upstream source or an explicit
      user exception for 0041 (guide "Rules", `exporter-guide/sidecars/rules.md:16-17`). Updated
      2026-10-25: part 2.3 (notes) cites the legacy MediaPipe sentence and the two label maps; the
      sentence agrees with the measurements (OpenMMLab-Exporter 0052). The user accepts
      OpenMMLab-Exporter 0041 and 0052 in place of a primary source (plan T45). 0052 is committed
      (OpenMMLab-Exporter commit `118699f` on `main`, 2026-10-25).
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the untracked plans of MediaPipe-Exporter (plan facts).
- [x] Part 4 gives `unverified: no host implementation`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a: no case has pixels; each
      floating-point result has its tolerance.
- [x] Part 5 says `to run` and describes the script and its gates.
- [x] n/a: the result of part 5 is `to run`, so no script needs a commit.
- [x] No file in skellytracker changed. No file in OpenMMLab-Exporter changed. In MediaPipe-Exporter,
      only this file, its reference file, the depth proposal and its reference file, and the rows
      and lists of the intake changed.
- [x] Mutation check (2026-10-24): one expected value changed in a copy of this file
      (`gate-tie`: `present: false` to `present: true`). The scratch runner gave 80 of 81 pass, with
      the one failure `gate-tie`. Run again after the edits of plan T28: 81 of 81 pass, and the same
      mutation gave 80 of 81 with the one failure `gate-tie`.
- [x] The user decisions of plan T28 (H2 to H6) are applied in parts 1, 2.2, 2.3, 2.6, 5, 7 and 8
      and in "Open questions for the user".
- [x] No private data in the text of the proposed spec change (`author-sidecar` step 3.4). The
      scratch paths in parts 1, 4 and 5 are local notes of this exporter, not spec text. A
      skellytracker session must not copy them into a decision entry.

A proposal with `to run` in part 5 is ready for a skellytracker session to record. It is not ready
for the user to accept. It stays incomplete until part 5 has the numbers, the script and the commit.

## Before acceptance

The first copy was on 2026-10-25. The record again of 2026-10-25 (decision
[vac0](../../../../notes/decisions/vac0-record-a-changed-proposal.md)) keeps each item of the first
list. It marks each item that the exporter version of 16:49 changes `(changed 2026-10-25)`, and each
new item `(new 2026-10-25)`. The new version closes no item.

**Parts**

- [ ] (changed 2026-10-25) Part 5 is `to run`. MediaPipe-Exporter must write and run its parity
  script `notes/decisions/scripts/hand_chain_parity.py`. Part 5 must then give the numbers against
  the gates, the script and a commit. MediaPipe-Exporter has a git repo since 2026-10-25 (commit
  `8f708a1ddecd8e035de15a5a9a7b652af035a58a` on `main`), but the script is not written, and part 5
  still says that no script can be committed.
- [ ] Part 5 also gives `to run` for the export error, the preprocessed input, the row count and the
  final outputs. Each needs a result.
- [ ] Part 2.1 does not list all the places that the change edits. Add the new row of "Considered and
  deliberately not added" (`specs/sidecar/changelog.md:38-53`) that part 2.7 proposes. Add the
  front-matter comment of `common/outputs.md:9` ("OutputSemantic lacks ..."). Add the "For
  reviewers" note of `changelog.md:5-10`, which names the exporters of the `vNEXT` scope, or say
  that the scope entry owns it.
- [ ] Rule `V-post.pose.extra_outputs-5` has no `keypoint_count` clause. Part 2.4 says that rule `-5`
  repeats `V-post.pose.schema-8`. The reference code checks `keypoint_count` under its "rule -5"
  comment, and the vector `error-world-keypoint-count` names rule `-5`. Make the rule text, the code
  and the vectors agree.
- [ ] Rule `-1` is marked **(vNEXT)**. A rule with this mark applies only when
  `schema_version >= vNEXT` (`specs/sidecar/README.md`, "Validation rules"). The reference code
  rejects a legacy sidecar under its "rule -1" comment, and the vector `error-legacy` names rule
  `-1`. The legacy rejection comes from the **(vNEXT)** mark of the changed `V-common.outputs-4`.
  Give the legacy rejection to one rule ID.
- [ ] Part 2.3 gives normative prose under the heading "## Fields". Part 2.2 gives the fields
  table. Say where the prose goes relative to the table.
- [ ] (new 2026-10-25) The file still says that MediaPipe-Exporter has no git repo: the header row
  "Exporter commit" (`none (no git repo)`), the note of part 3, the YAML header of part 4, and the
  part 5 rows "Result" and "Exporter commit of the script". Part 1 says "MediaPipe-Exporter has no
  git history". MediaPipe-Exporter has commit `8f708a1` on `main`. Give the commit, or say that the
  file is in the git-ignored `plans/` folder.
- [ ] (new 2026-10-25) The new sentences of part 2.3 "Fields" on the label source ("A label file in
  the model metadata can differ from them. The host takes the labels from the sidecar only.") and
  the note "A host must not take the labels from the model metadata" have no "must" in "Fields", no
  rule of part 2.4, no vector and no place in part 2.1. Write them as a rule, or move them to
  "Authoring guidance".

**Evidence**

- [ ] (changed 2026-10-25) The normative sentence of "Fields" on the physical side of `Right` has no
  primary source. The primary sources give only the names of the labels (the Tasks graph,
  `hand_landmarks_detector_graph.cc:133-141`). The side comes from secondary evidence: the legacy
  docstring (`hands.py:79-83` of `mediapipe` 0.10.14), OpenMMLab-Exporter 0041 (commit `9deff61`, on
  `main`) and OpenMMLab-Exporter 0052 (an upstream `HandLandmarker` run). The version of 16:49 no
  longer says that the legacy sentence states the opposite convention: 0052 shows that it applies
  to the legacy label map. Acceptance needs a primary source or an explicit user exception. The
  exporter records the exception as plan decision T45 (see **Decisions for the user**).
- [ ] (changed 2026-10-25) Part 1 uses `docs/mediapipe-whole-body.md` of MediaPipe-Exporter as
  primary evidence by a user designation. The guide classes the notes of an exporter as secondary
  evidence ("Rules", `specs/exporter-guide/sidecars/rules.md:9-13`). The file is tracked at
  MediaPipe-Exporter `8f708a1`, so a citation can pin it now. The designation is in no tracked
  MediaPipe-Exporter entry.
- [ ] No upstream output of the handedness exists for a known crop. Part 5 has no gate for the class
  probabilities.
- [ ] No source gives the origin of the world keypoints. The section does not define it.
- [ ] The exporter export does not exist. The probe file has the flat layout `[1, 63]` for the world
  landmarks. Rule `-5` requires `[N, K, 3]`.
- [ ] The measured numbers of part 1 (presence, world keypoints and the earlier handedness check) and
  the vector run of part 4 come from scratch scripts with no commit. They are not evidence.
- [ ] (changed 2026-10-25) The proposal cites the MediaPipe source at commit
  `e9794ef55e2509c09aa8b6ba1764b797db8eb200` in a local cache folder. It gives no permalink. A
  citation of the code of another repository must be a GitHub permalink that pins a full SHA on the
  default branch of that repository. A skellytracker session checked on 2026-10-25 that the commit
  is on `master`, the default branch of MediaPipe. Add the permalinks. The version of 16:49 adds
  more citations at that commit (`hand_landmarks_detector_graph.cc:133` and `:140-141`,
  `tensors_to_classification_calculator.proto:61-63`, `image_to_tensor_calculator.cc:180`).
- [ ] (new 2026-10-25) OpenMMLab-Exporter 0052 is cited as commit `118699f` "on `main`", by the short
  SHA only. On 2026-10-25, that commit is on the local OpenMMLab-Exporter branch `main`, but not on
  `origin/main`. A tracked file can cite it by permalink only when it is on the default branch of
  the remote. Give the full SHA.
- [ ] (new 2026-10-25) The citations of the legacy `mediapipe` 0.10.14 package
  (`mediapipe/python/solutions/hands.py:79-83`, `mediapipe/modules/hand_landmark/handedness.txt:1-2`)
  have no pin, and they are not in the cache of `e9794ef`. The SHA-256 of the hand landmark model is
  shortened (`11c272b891e1a99a…`). Give a citation form for a file of a released package, and the
  full SHA-256.

**Template checklist**

- [ ] (changed 2026-10-25) "Part 1 cites primary evidence": the box is ticked only under a user
  exception. The version of 16:49 names the exception: plan decision T45 accepts OpenMMLab-Exporter
  0041 and 0052 in place of a primary source. T45 is in an untracked plan, and 0052 is not on
  `origin/main` (see **Evidence**).
- [ ] "Part 2.1 lists each place that the change edits": the box is ticked, but places are missing
  (see **Parts**).
- [ ] "Part 4 gives `unverified: <reason>`": the box is correct, but the vector form does not agree
  with the tools (see **Vectors and tooling**).
- [ ] The header row "skellytracker commit of the spec text that you read" gives two commits:
  `dom/18-agents-adr-bootstrap-kit` first and `dom/21-move-sidecar-guide` at the end. The template
  asks for one commit.
- [ ] (changed 2026-10-25) "The intake links to this proposal": the links exist. The intake row D1c
  of `mediapipe-hand21` still names a scratch measurement as the evidence for the side of `Right`.
  Change it to OpenMMLab-Exporter 0041 and 0052.
- [ ] (new 2026-10-25) "No file in OpenMMLab-Exporter changed": the update of 2026-10-25 uses the new
  OpenMMLab-Exporter commit of 0052 (`118699f`). The item does not name it.

**Vectors and tooling**

- [ ] `tools/tests/test_vectors.py` requires `generated_by: tools/make_vectors.py`. Part 4 names
  the reference code.
- [ ] The case keys `function` and `compare` are not in `CASE_KEYS` of `tools/tests/test_vectors.py`.
  The tools use one scalar `tolerance` for each case, not an `atol` for each field. Part 6 says that
  the runner uses the `atol` of `compare`. Change part 6 to the form of the tools.
- [ ] The YAML of part 4 has approximately 35 KB. The limit of `tools/tests/test_vectors.py` is
  16 KiB.
- [ ] The cases `gate-nan`, `class-nan`, `decode-class-nan`, `error-threshold-nan` and
  `error-runtime-nan` have NaN values. A NaN is not equal to a NaN, so the test that compares the
  file with the generator data fails. `gate-nan` has a NaN expected value with no tolerance.
- [ ] `tools/make_vectors.py` rounds to 6 digits (`ROUND_DIGITS = 6`). Part 4 rounds to 12 decimals.
  Generated values differ in text from part 4.
- [ ] Add a builder to `tools/make_vectors.py` that calls
  `specs/sidecar/reference/post_pose_extra_outputs.py`. Add a test that runs the reference functions
  against the vectors. The folder `specs/sidecar/reference/` does not exist yet. Decide how the tools
  import it.
- [ ] Regenerate `TRACEABILITY.md` with `tools/sidecar_trace.py matrix`. Put the section-map row in
  the order that `tools/tests/test_traceability.py` checks.
- [ ] Keep "Inverse: none." of part 2.3 as text. An "Inverse" heading in a section of kind
  `postprocessor` fails `tools/tests/test_traceability.py`.

**Decisions for the user**

- [ ] (changed 2026-10-25) Part 5 needs a committed parity script and its numbers. MediaPipe-Exporter
  has a git repo since 2026-10-25, but `hand_chain_parity.py` is not written. Must the exporter
  commit and run it before acceptance, or do you make an explicit exception?
- [ ] (changed 2026-10-25) Do you accept OpenMMLab-Exporter 0041 and 0052 in place of a primary
  source for the side of `Right`? The exporter records this as the untracked plan decision T45 of
  OpenMMLab-Exporter, the exception of plan T31. Do the sentence on the MediaPipe hand model and the
  new sentences on the label source go in "Fields" or in "Authoring guidance"?
- [ ] (changed 2026-10-25) Do you accept `docs/mediapipe-whole-body.md` as primary evidence in
  skellytracker? The file is tracked at MediaPipe-Exporter `8f708a1`, and a permalink to the private
  repo is allowed (user, 2026-10-25). The files in the git-ignored `plans/` folder still have no
  commit.
- [ ] The `vNEXT` scope of [0008](../../../../notes/decisions/0008-vnext-scope.md) does not include
  MediaPipe-Exporter. This proposal needs the scope entry `vnext-scope-mediapipe-rotated-crops`
  (0048). Must that entry be accepted before this proposal?
- [ ] Confirm that `roi-transform-and-source` (0020) lands first. Step 4 uses `rotated_roi_crop`, its
  crop ROI `Rc` and its rotation sign. Without it, the link "Rotated ROI crop, Behaviour step 3" has
  no target.
- [ ] Completing 0021 changes its direction: it drops `score`, `keypoints_3d`, `positive_class`,
  `assumes_mirrored_input` and `>= 0.5`. Do you accept this change of the gap record?
- [ ] Legacy policy: rule `-7` has no **(vNEXT)** mark, and other proposals use other policies.
  Decide one policy for the rejection of a `vNEXT` field below `vNEXT`.
- [ ] The new "Legacy behaviour" heading gets no link in "Version-aware compatibility". The skill
  `change-sidecar-spec` requires the link. The proposal follows `pre.resize.fit`, which has no link.
- [ ] Confirm the section ID `post.pose.extra_outputs`, the file `post/pose-extra-outputs.md` and the
  rules `-1` to `-7`.
- [ ] BlazePose: the header names rows of the deferred `mediapipe-pose39` intake. That model has a
  flat world layout `[1, 117]` (39 rows against 33 tracked points), and its upstream threshold range
  is `[0, 1]`. Rule `-5` and the range `[0, 1)` do not describe it. Is BlazePose a driver of this
  proposal?
- [ ] The name of the test video in part 5 can contain the initials of a person. May the name stay in
  this file?
- [ ] The change proposal template gives the case keys `function` and `compare` and
  `generated_by: <reference file>`. The tools reject them (see **Vectors and tooling**). Decide one
  vector form for all proposals: change the tools to the template form in a non-spec PR, or change
  the vectors to the form of the tools. Decide also the 16 KiB limit: raise it, split the file or
  remove cases. Decide how a case with a NaN value is written.
- [ ] (changed 2026-10-25) Must 0021 get a `**Depends on:**` line? It waits for the parity result of
  MediaPipe-Exporter. MediaPipe-Exporter has a git repo now, so the line can give a permalink when
  the parity entry exists. No such entry exists yet.
- [ ] (changed 2026-10-25) The guidance edits of part 2.1 (`common/outputs.md:72`,
  `post/pose-schema.md:143`, `mapping-hints.md`, the intake row K8) have no commit of
  MediaPipe-Exporter. The skill `change-sidecar-spec` asks for a repo, a file and a commit for each
  guidance statement. The tracked MediaPipe-Exporter files have commit `8f708a1`. The files in
  `plans/` have none. Which form do you accept? (`post/pose-schema.md:143` is line 144 at
  `dom/32-absorb-remaining-entries`.)
- [ ] The kept bullets of `common/outputs.md:69-71` and other spec files cite a MediaPipe-Exporter
  plan file that moved to the archive folder of its plans. Must the non-spec PR repair them?
- [ ] When MediaPipe-Exporter writes the sidecar, remove the `proposed` entry
  `mediapipe-hand-landmark@mediapipe-exporter` from `specs/sidecar/inventory.yaml`.
- [ ] (new 2026-10-25) The evidence exception for the side of `Right` rests on plan decision T45 of
  OpenMMLab-Exporter (2026-10-25). It is in an untracked plan. Do you confirm it, or must the
  exporter record it in a tracked entry first?

**Merge points**

- [ ] `common/outputs.md:29`, `:35` and `:44` (the closed `semantic` set, the routing paragraph,
  `V-common.outputs-4`): `roi-refiner-role` (0047) adds `roi_points`. Merge the lists.
- [ ] The scope entry `vnext-scope-mediapipe-rotated-crops` (0048) supersedes the scope entry in
  force at merge time: 0008, or `vnext-scope-nms-filters` (0042) of `nms-clamp-order` (0040).
  This proposal goes into `vNEXT` on the scope of 0048. Decide which scope entry lands first.
- [ ] `format/versioning.md:74`, the legacy row "Not available.": `pose-decode-flip-test` (0045),
  `heatmap-decode-refinement` (0038), `keypoint-visibility` (0039), `roi-transform-and-source`
  (0020), `roi-refiner-role` (0047) and `landmark-depth-divisor` (0022).
- [ ] `post/pose-schema.md:117-127` ("Validation rules" and "See also"): 0020, 0022, 0045 and 0039.
  `post/pose-schema.md:137-144` ("Authoring guidance"): 0020.
- [ ] `post/pose-decode-coordinate.md:33`, the single-person form: `keypoint-visibility` (0039)
  replaces the form with `(N, K, C)`. `landmark-depth-divisor` (0022) edits its depth phrase. Decide
  the normative form. The coordinate decode of 0022 must call `decode_extra_outputs`.
- [ ] `specs/sidecar/README.md:93` and `:121` (the section map and the validation index): 0045 and
  0039.
- [ ] `mapping-hints.md:55-65` ("Outputs and decode"): `nms-clamp-order` (0040), 0039 and
  `omitted-upstream-output` (0044).
- [ ] `templates/model-intake.md:290` (row D1): 0047. `:318` (row K8): 0039 adds the row K8a.
- [ ] `inventory.yaml:98-129` (the `proposed` entries): `model-id-suffix` (0025), 0020 and 0047.
- [ ] `changelog.md`: the summary row `N` and the `vNEXT` row `:68` (all 13 spec proposals);
  "Compatibility impact" `:55-59` (`simcc-score-rule` (0024), 0038, `normalize-arithmetic` (0043),
  `affine-crop-arithmetic` (0037), 0025, 0020, 0022); "Considered and deliberately not added"
  (0040, 0020). 0020 removes the row on rotated crops (`:45`). Step 4 needs that removal.
- [ ] Parts 2.2 and 8 cite `post/detection-decode.md:42` and `:77`. `nms-clamp-order` (0040) edits
  the lines near them. Check the line numbers after it lands.
- [ ] `roi-refiner-role` (0047) uses the same field name `score_threshold_default` and the same range
  `[0, 1)`. Keep the two definitions equal.
- [ ] `pose-decode-flip-test` (0045) excludes `coordinate` in `V-post.pose.flip_test-1`. An average of
  a handedness after a mirror pass is wrong. Keep this limit.

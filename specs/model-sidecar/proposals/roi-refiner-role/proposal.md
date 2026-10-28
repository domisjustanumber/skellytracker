---
slug: roi-refiner-role
section: post.roi_refiner
exporter: MediaPipe-Exporter
decision: "0047"
state: recorded
---
# Change proposal: roi-refiner-role

This file is informative. It is not part of the normative spec until a content PR lands its text in the section files (decision [0036](../../../../decisions/0036-spec-proposals-folder.md)).

**Source.** The MediaPipe-Exporter file of the proposal `roi-refiner-role`, and its reference file, which is the `python` code block of part 3. Commit `none (no git repo)`. Copied on 2026-10-25. MediaPipe-Exporter has no git repo. Its paths in this file are not pinned. The copy changes only the items of decision 0036, item 3. The session wrote no part.

This file uses ASD-STE100 Simplified Technical English. It is a local working note of
MediaPipe-Exporter (decision 0001). Git does not track it.

Labels in this file:

- **User decision (2026-10-23)** and **user decision (2026-10-24)** mark a decision of the user. Do
  not change it without the user. The decisions of 2026-10-24 are T22, T23, T24, T26 (6) and T27 of
  the untracked pose-models plan of OpenMMLab-Exporter (plan facts) (section 2.1, secondary), and Q7 = (c) of
  the 0020 proposal. T23 names the two open questions of this file R1 (this file's Q6) and R2 (this
  file's Q7). T26 (6) makes the threshold of the score gate a runtime input with a default. T27 gives
  each parent point an ordered list of accepted names. T28 of the same plan gives H1 (a third name in the pinky and index lists, the spelling of the skellytracker spec example) and H6 (one parity script for the four MediaPipe proposals). T37 of the same plan gives both RTMW gate thresholds of OpenMMLab-Exporter 0041 for each size (part 1), and T38 records the hand-mean gate value only as a measured option (part 8).
- **"The visibility proposal"** is the OpenMMLab-Exporter proposal `keypoint-visibility`
  (OpenMMLab-Exporter `specs/model-sidecar/proposals/keypoint-visibility/proposal.md`, section `post.pose.visibility`, read only). Its part 2.8 lists the edits that
  this file needed for the named per-point value of the gate (`score_gate.value`). Those edits are
  applied (2026-10-24), and its items 11 to 13 for option E are applied too.
- **User decision T33 (2026-10-24, the untracked pose-models plan of OpenMMLab-Exporter (plan facts))** makes the gate value a runtime input
  too: the sidecar gives its default in `score_gate.value_default` (Holistic: `visibility`), and the
  host or the user can set another value for a run. One refiner sidecar then serves BlazePose and
  RTMW parents. The threshold range follows the value in effect. The same decision took the interim
  V1 = A1 of the visibility proposal (replaced by option E, below). Under E, an RTMW parent gives
  `score` at every size and no `visibility`. The parent check reads the parent size in use. **User decision T34 (2026-10-24,
  the untracked pose-models plan of OpenMMLab-Exporter (plan facts))** rejects Q8 (c): when the parent gives no value for the gate value in
  effect, the host refuses the parent; it never skips the gate. Q8 is decided in full. **Measured result (2026-10-24):** OpenMMLab-Exporter decision 0041 (at `32ab848`) replaces A1 with option E of the visibility proposal: no RTMW size declares `pose.decode.visibility`. An RTMW parent uses the runtime gate value `score` with a threshold for each size (part 1). T33 and T34 do not change.
- **Proposal choice** marks a choice of this proposal. The user can change it (see "Open questions
  for the user").

"The 0020 proposal" in this file is the full proposal of skellytracker 0020,
`specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`, with its reference file
the part 3 code of `specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`. A line number after "0020 proposal" is a
line of that file on 2026-10-24, after its last edit of that day (the notes on the affine-crop proposal), checked again after the edits of T26 (6) and T27. Line numbers of skellytracker files are at commit `dom/18-agents-adr-bootstrap-kit` (re-pinned on 2026-10-24 from `dom/12-single-working-branch`). The
cited spec files have no change since `dom/12-single-working-branch`, except
`specs/model-sidecar/exporter-guide.md:441-445` at `dom/18-agents-adr-bootstrap-kit` (one line less; history note of 2026-10-25: that file does not exist at skellytracker `dom/21-move-sidecar-guide`, because skellytracker 0034 moved the guide to `specs/exporter-guide/sidecars/`; the guide citations of this file now point to that folder at `dom/21-move-sidecar-guide`) and
`specs/model-sidecar/templates/change-proposal.md:62` (one line changed). The "Open work" of the decision-log index
`notes/decisions/README.md` moved to `notes/decisions/open-work.md`; the citations of both files are
at `dom/18-agents-adr-bootstrap-kit`. Package code of skellytracker that this file cites for
the first time on 2026-10-24 is at `dom/14-decision-log-growth` (the same at `dom/18-agents-adr-bootstrap-kit`). MediaPipe source is at commit
`e9794ef55e2509c09aa8b6ba1764b797db8eb200` (the cached copy in `model_cache/sources/`; the files cited
on 2026-10-24 are the same at `v1.1.1`, a `diff` of the cached copies).

## Header

| Field | Value |
|---|---|
| Title | A sidecar role for an ROI refiner: a model that gives the region of interest (ROI) of the next model |
| Slug | `roi-refiner-role`. MediaPipe-Exporter 0015 (accepted) fixes this file name (`notes/decisions/0015-recrop-new-sidecar-role.md:9-13`). The skellytracker decision log has no entry with an ROI-refiner slug (index of `notes/decisions/README.md` at `dom/18-agents-adr-bootstrap-kit`). The OpenMMLab-Exporter proposal `model-id-suffix` names the same file (its question Q1). |
| Date | 2026-10-23; updated 2026-10-24 (user decisions T22, T23, T24, T26 (6), T27, T28 (H1, H6), T33 and Q7 = c of the 0020 proposal); updated 2026-10-24 for the measured result of OpenMMLab-Exporter 0041 (option E); updated 2026-10-24 for user decisions T37 and T38 (the two RTMW gate thresholds of OpenMMLab-Exporter 0041 in part 1; the hand-mean gate value as an option in part 8) and for OpenMMLab-Exporter 0050 (part 7, T39); updated 2026-10-25 (re-read at skellytracker `dom/21-move-sidecar-guide`, no change of content; the repo name `OpenMMLab-Exporter` added before each bare decision number `0041`) |
| Exporter repo | MediaPipe-Exporter |
| Exporter commit | none (no git repo) |
| Model, and its intake file | `mediapipe-hand-roi` (user decision Q3 = a, 2026-10-23, part 2.1; the inventory key today is `mediapipe-hand-recrop@mediapipe-exporter`), from `hand_roi_refinement.tflite` in `holistic_landmarker.task` (MediaPipe-Exporter 0016). Intake file: the untracked intake of `mediapipe-hand-roi` of MediaPipe-Exporter (plan facts) (written 2026-10-24). The intake of the hand landmark model, the untracked intake of `mediapipe-hand21` of MediaPipe-Exporter (plan facts), has no row for this proposal. |
| Intake rows with the verdict `near-miss` or `gap` | the untracked intake of `mediapipe-hand-roi` of MediaPipe-Exporter (plan facts) (2026-10-24), all `gap`: F1 `model_id` (no rule for the role); F2 `role` (no value fits); D1 semantic of `Identity` (no value for ROI points); D1a read of the points; D11 map of the points to the source image (use `Rc`; with the 0020 proposal); D11a rect from the two points; D11b transform of the refined ROI; D11c an ROI that is not valid; L1 sidecar path (no branch of the storage layout for the role); R1a parent points by name (an ordered list of accepted names for each point, T27), R1b derived point `middle`, R1c loose rect, R1d visibility gate (a runtime threshold with the default 0.1, T26 (6); a runtime gate value with the default `visibility`, T33) (the `roi_source` rows; under the current text alone these steps are `out of scope`; user decision T24 puts them in the contract). The input crop rows T2 to T8 are `gap` rows of the 0020 proposal. Row R2 (the per-point value of a BlazePose parent, its visibility) is a `gap`. The visibility proposal (OpenMMLab-Exporter `specs/model-sidecar/proposals/keypoint-visibility/proposal.md`, section `post.pose.visibility`) covers it (part 1, "Missing primary evidence"; Header, "Depends on" (2)). |
| Kind | `new section` (with edits to `common.identity`, `common.outputs`, `common.input`, `common.sizes_and_artifacts`, `format.file_layout`, `format.versioning`, `post.pose.schema` (guidance), and the rule `V-pre.resize.rotated_roi_crop-1` and the heading "ROI source" of the section `pre.resize.rotated_roi_crop` that the 0020 proposal adds). The section has two parts: the output decode (`roi_decode`) and the ROI source of the input (`roi_source`: the loose ROI from named parent keypoints, user decision T24, 2026-10-24). |
| Proposed section ID | `post.roi_refiner` |
| Section file | `specs/model-sidecar/post/roi-refiner.md` |
| Depends on | (1) The 0020 proposal: `specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`, new section `pre.resize.rotated_roi_crop` with the method `input.resize.method: rotated_roi_crop` (the name is a user decision, its Q1 = a of 2026-10-24, `:1801-1803`), and its reference file the part 3 code of `specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`. **User decision (2026-10-23, Q4 = a):** the two proposals stay separate, and the 0020 proposal goes into `vNEXT` before this one (0020 proposal `:44, 48`). The dependency is one-way: this proposal depends on the 0020 proposal, and the 0020 proposal does not depend on this one. This proposal uses five items of it. It has no copy of them. The items are: the heading "ROI" (the ROI and its validity test, `:300-313`); the heading "ROI transform" (`:325-337`); the crop ROI `Rc` of its Behaviour steps 1 to 3 (`:339-351`); the heading "Inverse" (`:369-379`); the transform checks of its rule `V-pre.resize.rotated_roi_crop-4` (`:442-444`). Part 3 loads its reference file. (2) **For the gate on the visibility:** the visibility proposal (OpenMMLab-Exporter `specs/model-sidecar/proposals/keypoint-visibility/proposal.md`, section `post.pose.visibility`, the new optional field `pose.decode.visibility`). It gives each pose point the named values `score` and `visibility` (its heading "Per-point values"). A refiner sidecar with `score_gate.value_default: visibility`, or a run with the runtime gate value `visibility`, needs it, because without it no parent gives a visibility. The refiner section can land first. Until the visibility proposal lands, only the value `score` can pass the parent check (user decision T33: `value_default` and the runtime gate value). The Holistic hand gate names `visibility`. **Related (not a dependency):** the OpenMMLab-Exporter proposal `model-id-suffix` (OpenMMLab-Exporter `specs/model-sidecar/proposals/model-id-suffix/proposal.md`, skellytracker 0025). Its `model_id` grammar `{family}-{keypoints}[-{training}]` applies only under `detectors/keypoint_detectors/{family}/{keypoints}/` (its rule `V-common.identity-7`, `:131-144`), and `{keypoints}` must end in a point count (`:137-139`). OpenMMLab-Exporter commit `d0f4343` (decision 0039) uses that grammar in code (`notes/decisions/0039-keypoint-model-id-format.md:10-11`; `rtmo/identity.py:39, 42`). The refiner id `{family}-{part}-roi[-{variant}]` in `detectors/roi_refiners/{family}/{part}/` (user decision Q3 = a, 2026-10-23, part 2.1) is outside that grammar. That proposal records this: its row "Needed by" (`:20`), its id table (`:366`) and its answered Q1 ("`V-common.identity-7` does not apply under `roi_refiners/`", `:406`). Its "Depends on" is `none` (`:19`). Thus neither proposal must land before the other. The user decision Q3 = a answers its Q1. |
| Needed by | the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts) ("Blocked on: the role proposal (0015)"). The OpenMMLab-Exporter proposal `model-id-suffix` does not depend on this proposal (its "Depends on": `none`, `specs/model-sidecar/proposals/model-id-suffix/proposal.md`). The user decision Q3 = a of this proposal answers its question Q1 (the pipeline stage), and that proposal records Q1 as answered (`:373-406`). See "Related (not a dependency)" in the row "Depends on". **Related (merge points; review-readiness audit 2, 2026-10-24).** Other proposals edit the same spec text as this proposal. The content PR that lands second rebases on the first and keeps the edits of both. Line numbers are at skellytracker `dom/18-agents-adr-bootstrap-kit`, as in the rest of this file. The guide lines are an exception: they are at skellytracker `dom/21-move-sidecar-guide`, in the folder `specs/exporter-guide/sidecars/` of skellytracker 0034. Each cited spec line is the same at `dom/12-single-working-branch`, except the skellytracker 0025 item (at `dom/12-single-working-branch` in `notes/decisions/README.md:159-165`). (History note of 2026-10-25: at `dom/18-agents-adr-bootstrap-kit`, the guide was the single file `specs/model-sidecar/exporter-guide.md`, with one line less after line 445 than at `dom/12-single-working-branch`. That file does not exist at `dom/21-move-sidecar-guide`.) `common/outputs.md:29, 35, 44` (the closed `semantic` set, the routing paragraph, `V-common.outputs-4`): `landmark-extra-outputs`; `format/versioning.md:74` (the legacy row "Not available."): `pose-decode-flip-test` (OpenMMLab-Exporter), `heatmap-decode-refinement` (OpenMMLab-Exporter), `keypoint-visibility` (OpenMMLab-Exporter), `roi-transform-and-source`, `landmark-extra-outputs`, `landmark-depth-divisor`; `post/unprojection.md:21-36` ("Behaviour" and the list of inverses): `roi-transform-and-source`, `landmark-depth-divisor`; `common/identity.md:29, 36-41, 47-51, 76-81` (the `model_id` row, the rules, the legacy rows, the authoring guidance): `model-id-suffix` (OpenMMLab-Exporter); `format/file-layout.md:44-89` (the storage tree, the branch table, the examples): `model-id-suffix` (OpenMMLab-Exporter), `size-codes` (OpenMMLab-Exporter); `format/file-layout.md:155-157` ("Authoring guidance"): `model-id-suffix` (OpenMMLab-Exporter); `exporter-guide/sidecars/workflow/phase-1-intake.md:14-16, 30-32` (phase 1 step 1, the verdict `gap`): `roi-transform-and-source`; `exporter-guide/sidecars/workflow/mapping-hints.md:13-32` ("Mapping hints", Identity and Family): `model-id-suffix` (OpenMMLab-Exporter), `size-codes` (OpenMMLab-Exporter); `exporter-guide/sidecars/sidecar-files.md:33-50` ("Path"): `model-id-suffix` (OpenMMLab-Exporter); `templates/model-intake.md:113, 118-119` (verdicts): `roi-transform-and-source`; `templates/model-intake.md:229, 355` (rows F1, L1): `model-id-suffix` (OpenMMLab-Exporter); `templates/model-intake.md:290` (row D1): `landmark-extra-outputs`; `inventory.yaml:98-129` (the `proposed` entries): `model-id-suffix` (OpenMMLab-Exporter), `roi-transform-and-source`, `landmark-extra-outputs`; skellytracker `notes/decisions/open-work.md:125-131` (the 0025 item): `model-id-suffix` (OpenMMLab-Exporter). All 13 proposals add a row to "Summary of changes" (row `N`, the next free number at merge time) and a sentence to the `vNEXT` row of the `schema_version` history (`changelog.md:68`). |
| skellytracker decision entries with the status `proposed` that cover the same property | **0020** (gap record, `0020-roi-transform-and-source.md:8-23`). It covers the consumer side: the ROI transform and an ROI that does not come from a detector box. It does not cover the refiner itself. It names the refiner gap as a dependency. This proposal is a separate role proposal. It depends on the full proposal of 0020 (`specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`), which lands first (user decision, 2026-10-23, Q4 = a). It does not compete with 0020: it uses the ROI, the ROI transform, the crop and the inverse of the 0020 proposal (part 8 gives where it differs). **0025** (gap record): the `model_id` of a second model of one family and one part (`0025-model-id-suffix.md:13-17`, and the open-work item at `notes/decisions/open-work.md:125-131`, which names the re-crop model). **0021** (gap record): the extra outputs of the hand landmark model. It does not cover the refiner, which has one output. **0017** (gap record): the folder of a dual-role sidecar. This proposal adds a branch for a third role. It does not change 0017. |
| Evidence basis | **The user designated `docs/mediapipe-whole-body.md` as checked primary evidence (2026-10-23).** The exporter guide classes the notes of an exporter as secondary (`specs/exporter-guide/sidecars/rules.md:9-13`). This document is an exception by a user decision: each of its claims has a source check at MediaPipe commit `e9794ef55e2509c09aa8b6ba1764b797db8eb200` and at `v1.1.1` (`docs/mediapipe-whole-body.md:14-24`; MediaPipe-Exporter 0021). This proposal cites it with `path:line` as primary evidence. It does not repeat its source checks. Other sources are named for the facts that the document does not cover. |
| User decisions (2026-10-23) | Q1 = (a): the change goes into `vNEXT`. The `vNEXT` scope of skellytracker 0008 must add MediaPipe-Exporter (part 2.1, part 2.6). Q2 = (c): the face rule `points_bounds` is deferred until a face model needs it (part 8). Q3 = (a): the folder `detectors/roi_refiners/{family}/{part}/` and the id `{family}-{part}-roi[-{variant}]` (part 2.1). Q4 = (a): keep this proposal separate from the full proposal of skellytracker 0020; the 0020 proposal goes into `vNEXT` before this one (row "Depends on"). Q5 = (a): an ROI with a width or a height of 0 or less gives "no ROI" (part 2.3, step 5). |
| User decisions (2026-10-24) | T23, R1 (this file's Q6 = a): the reference file loads the 0020 reference file by its path. T23, R2 (this file's Q7 = a): the clamp keeps the rotation exactly in `[-pi, pi)`. T24: the refiner sidecar declares how the host makes the loose hand ROI from the body pose: the input points by name, the derived point `middle`, the rect rule and the visibility gate (part 2.2 and part 2.3, heading "ROI source"). The tracking ROI from the previous hand landmarks and the ROI choice (`RoiTrackingCalculator`) stay outside the sidecar as host tracking policy (part 8, "Not proposed"). Q7 = (c) of the 0020 proposal: the spec states no arithmetic precision; the vectors give the tolerances (part 2.3, part 4). T22 (1) of the 0020 proposal: `pose.requires_object_detector` leaves the spec (part 2.1, the row of the heading "ROI source"). T26 (6): the threshold of `roi_source.score_gate` is a runtime input that the host or the user can set. The sidecar gives the default in `score_gate.score_threshold_default`, and the default is the Holistic value 0.1 (part 2.2, part 2.3 heading "ROI source", rules `-14` and `-16`). T27: each local point of `roi_source.instances[].points` takes an ordered list of accepted parent names, and the host uses the first name that the parent has. The lists name the BlazePose point first and the COCO-WholeBody 133 point of mmpose (OpenMMLab-Exporter RTMW) second (part 2.2, "The point names"). T28 (H1): the pinky and index lists name the spelling of the skellytracker spec example third (`left_hand_pinky_finger1`, `left_hand_forefinger1`, and the right side). The wrist list has no third name, because the example spells the wrist and the hand root as mmpose does. T28 (H6): one parity script for the four MediaPipe proposals, `notes/decisions/scripts/hand_chain_parity.py` (part 5). The hand-keypoint accuracy with the COCO-WholeBody names is not measured (part 1, part 5). The gate value of an RTMW parent is measured: `score` (OpenMMLab-Exporter 0041 at `32ab848`; part 1). From the visibility proposal (its part 2.8; a proposal choice there, not a user decision): `score_gate.value` (`score` or `visibility`, required, no default), the threshold range for each value, and the parent check of the named value. T33 (supersedes the "no default" of that choice): the gate value is a runtime input with the sidecar default `score_gate.value_default` (Holistic: `visibility`); the threshold range follows the value in effect; the parent check uses the value in effect and the parent size in use (part 2.2, part 2.3 heading "ROI source", rules `-14` to `-16`). T34: Q8 (c) rejected; the host refuses a parent that gives no value for the gate value in effect, and never skips the gate (part 2.3, rule `-15`). T31: Q8 (b) rejected. The other T23 answers to the 0020 proposal (Q1 a, Q2 a, Q4, Q5, Q6, Q8, Q9, Q10 a, Q11, Q12 a) match the text of this file. T35: Q13 (a): a runtime gate value other than `value_default` needs a runtime threshold; without one, the host refuses the run (rule `-16`). T37: the proposals give both RTMW gate thresholds of OpenMMLab-Exporter 0041 for each size, `t_recall` (the default recommendation) and `t_J` (the selective option); neither is a sidecar field (U4) (part 1, table "RTMW gate thresholds"). T38: the hand-mean gate value `s_h` of OpenMMLab-Exporter 0041 is only a measured option (part 8); no spec change now. |
| skellytracker folder that you read | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read | `dom/21-move-sidecar-guide` (re-read on 2026-10-25; `git status --porcelain` lists only an untracked `grep.exe.stackdump`, which this file does not read; `git diff --stat dom/18-agents-adr-bootstrap-kit dom/21-move-sidecar-guide -- specs/model-sidecar` changes link text in nine files and removes `specs/model-sidecar/exporter-guide.md`, which skellytracker 0034 moved to `specs/exporter-guide/sidecars/`, so the spec line numbers of this file stay at `dom/18-agents-adr-bootstrap-kit`). Pinned on 2026-10-24 at `dom/18-agents-adr-bootstrap-kit` (`git status --porcelain` was empty). First read at `dom/12-single-working-branch`. Re-read on 2026-10-24 at `dom/14-decision-log-growth`: see the note at the top of this file. At that re-read, `git status --porcelain` listed `AGENTS.md`, `decisions/0026-decision-log-size.md`, `notes/decisions/README.md` and a new `decisions/0029-decision-log-read-path.md`. `git diff --stat dom/14-decision-log-growth dom/18-agents-adr-bootstrap-kit -- specs/model-sidecar` is empty, and this file cites no `.claude` line. This file cites `notes/decisions/README.md` and `notes/decisions/open-work.md` at `dom/18-agents-adr-bootstrap-kit`. Guide citations point to the 0034 layout at skellytracker `dom/21-move-sidecar-guide`. The spec text did not change after the pin (only link repairs). |

## 1. Gap

| Item | Value |
|---|---|
| Property | The MediaPipe Holistic hand ROI refinement model reads a loose rotated ROI crop (256², [0, 1], `keep_aspect_ratio`, `BORDER_REPLICATE`; the 0020 proposal describes this crop as `rotated_roi_crop`) and outputs two points: `p0` (centre) and `p1` (scale point), in crop pixels. The host maps the points to the image with the crop matrix. Then it makes a rect: centre `p0`, size `2 · |p1 − p0|`, rotation from `p0` to `p1` with target −90°. Then it applies `shift_y` −0.1, `square_long` and scale 1.0. The result is the ROI of the hand landmark model. The refiner runs on every frame that passes the wrist gate. **The input ROI (user decision T24, 2026-10-24).** The host makes the loose ROI of the refiner from three points of the body pose for each hand: wrist, pinky and index (BlazePose 15, 17, 19 for the left hand; 16, 18, 20 for the right hand). The branch runs only when the wrist visibility is `> 0.1`. Else that hand has no ROI. Holistic fixes the value 0.1 in the graph. In the sidecar it is the default of a runtime threshold (user decision T26 (6)). The value that the gate reads is the BlazePose visibility (a logit in the graph, with a sigmoid on the host), not a keypoint score (the visibility proposal, part 1). **Other parents (user decision T27).** BlazePose 17 and 19 are the pinky MCP and the index MCP joints (`docs/mediapipe-whole-body.md:372`). A COCO-WholeBody 133 parent has the same joints with other names: `left_pinky_finger1` and `left_forefinger1` (and the right side), and the hand root `left_hand_root` next to the body wrist `left_wrist`. The skellytracker spec example spells the two MCP points `left_hand_pinky_finger1` and `left_hand_forefinger1` (user decision T28 (H1): a third name in the lists). Thus each point of `roi_source` takes an ordered list of accepted names. `middle = (2·index + pinky) / 3`. The loose rect has the centre `middle`, the size `2 · |middle − wrist|` and the rotation from the wrist to `middle` with target 90°. Then `shift_y` −0.1, `square_long` and scale 2.7 apply (the `crop_policy.transform` of the input crop, 0020 proposal). No section of the spec says how the host makes this ROI. |
| Upstream evidence | Primary (user designation, see the Header), in `docs/mediapipe-whole-body.md`. `:390-394`: the refined ROI. `:371-379`: the branch diagram. `:200`: the catalogue row (256², [0, 1], output `[1,1,1,4]` two points, used by Holistic). `:65-77`: the rect from two points (the rotation formula, `NormalizeRadians`, centre at the start point, size `2 · |end − start|`). `:81-90`: `RectTransformation` (shift along the rect axes, then `square_long`, then scale). `:94-112`: the rotated crop, its border, `keep_aspect_ratio`, and the matrix that maps the two points. `:58-61`: a rect is `(x_center, y_center, width, height, rotation)`, rotation clockwise in radians, computed in pixels. `:705-718`: the `HandRoiRefinementGraph` node in the Holistic hand branch. `:609`: the hand finder of Holistic is this 88 KB model. Facts that the document does not cover: (1) The ONNX graph. A scratch script read it with `onnx` 1.x (read again on 2026-10-23 after the review fix, with the same values). The file is `model_cache/onnx/hand_roi_refinement.onnx`, 128,769 bytes, sha256 `1e6f0cb8d2101bbe39572f3d56f608be37882afa1fc05455d31afa4794a5e1ab`, opset 17, 77 nodes. Its input is `input_1` float32 `[1, 3, 256, 256]`. Its output is `Identity` float32 `[1, 1, 1, 4]`. The last nodes are `Conv` `Identity` and `Reshape` `Identity__537`. (2) The source asset and its sha256 (MediaPipe-Exporter 0016). (3) The end-to-end agreement (MediaPipe-Exporter 0006). **For the input ROI:** primary `docs/mediapipe-whole-body.md:381-389` (the pose points, the visibility gate, the loose ROI) and `:371-379` (the branch diagram). MediaPipe source at `e9794ef` (cached copy; the same at `v1.1.1`): `tasks/cc/vision/pose_landmarker/pose_topology.h:37-42` (the names `kLeftWrist`, `kRightWrist`, `kLeftPinky1`, `kRightPinky1`, `kLeftIndex1`, `kRightIndex1`, indices 15 to 20); `tasks/cc/vision/holistic_landmarker/holistic_landmarker_graph.cc:430-435, 459-464` (the three indices for each side); `tasks/cc/vision/holistic_landmarker/holistic_hand_tracking.cc:80-91` (`GetPosePalmVisibility`: the wrist, `LandmarkVisibilityCalculator`, and at `:91` the fixed value `IsOverThreshold(score, /*threshold=*/0.1, graph)`, the source of the default of T26 (6)), `:201-216` (the gate drops the pose palm landmarks before the ROI), `:94-111` (the loose ROI, then scale 2.7 and `shift_y` −0.1); `calculators/util/thresholding_calculator.cc:123-124` (`static_cast<double>(score) > threshold_`: strict, and false for NaN); `modules/holistic_landmark/calculators/hand_detections_from_pose_to_rects_calculator.cc:56-58` (the order wrist, pinky, index), `:69` (target `M_PI * 0.5f`), `:93-113` (`middle`, centre, `box_size`), `:124-152` (the rotation from the wrist to `middle`, `NormalizeRadians`). The probe of MediaPipe-Exporter 0006 uses the same rule (`notes/decisions/scripts/hand_roi_reference.py:27-29, 47-52`). **For the second names of the lists (user decision T27):** `docs/mediapipe-whole-body.md:372` (pose 15/17/19 and 16/18/20 are the wrist, the pinky MCP and the index MCP). The COCO-WholeBody 133 names of RTMW: OpenMMLab-Exporter `rtmw/keypoints.py:22-23` (`left_wrist`, `right_wrist`, body points), `:104, 109, 121` (`left_hand_root`, `left_forefinger1`, `left_pinky_finger1`), `:125, 130, 142` (the right side), and the edges `[91, 96]` and `[91, 108]` at `:178, 190` (the root to the first point of the forefinger and of the pinky; each finger is a chain of the points 1 to 4 from the root), at `d0f4343` (the same at `32ab848`), read only. The skellytracker package maps the canonical hand names `index_finger_mcp` and `pinky_mcp` to `forefinger1` and `pinky_finger1`, and `wrist` to `root` (`skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_to_canonical_mapping.yaml:18, 23, 35`). Thus the second names name the same joints as the BlazePose names. No copy of the mmpose dataset info `coco_wholebody.py` was read. **For the third names (user decision T28 (H1)):** the skellytracker spec example `specs/model-sidecar/examples/detectors/shared/skeletons/coco133_tracked_points.yaml` at `dom/17-gitignore-python-version` (secondary: a spec reference example). Its header says that the list is in the RTMW output order and that it was ported from `rtmpose_wholebody.yaml` (`:2-5`). Its names: `left_wrist`, `right_wrist` (`:15-16`, output indices 9 and 10); `left_hand_root`, `left_hand_forefinger1`, `left_hand_pinky_finger1` (`:97, 102, 114`, output indices 91, 96 and 108); `right_hand_root`, `right_hand_forefinger1`, `right_hand_pinky_finger1` (`:118, 123, 135`). The indices 91, 96 and 108 are the root and the first points of the forefinger and of the pinky in the RTMW edges (`rtmw/keypoints.py:178, 190`). Thus the example and mmpose spell the two MCP points differently (`left_hand_forefinger1` and `left_forefinger1`, `left_hand_pinky_finger1` and `left_pinky_finger1`). They spell the body wrist and the hand root the same. |
| Nearest section ID | `common.identity` (`role`), `common.outputs` (`semantic`), `post.pose.schema` with `post.pose.decode.coordinate` (the two-keypoint workaround) |
| Why the nearest section is wrong | `V-common.identity-2` allows only `object_detector` and `pose_estimator` (`specs/model-sidecar/common/identity.md:37`). The closed `semantic` set has no value for ROI points (`common/outputs.md:29, 44`). A pose estimator with the points `crop_center` and `crop_scale` describes the tensor, but a host then reads the points as keypoints of the user. The rect rule, the rotation target and the transform then have no place in the sidecar. The exporter guide forbids this mapping (`exporter-guide/sidecars/rules.md:6-8`, `exporter-guide/sidecars/workflow/mapping-hints.md:71`; skellytracker `0014-spec-lifecycle.md:282`). The storage layout has no branch for the role (`format/file-layout.md:44-76`). No section makes an ROI from points. No section makes the input ROI of a model from the keypoints of a parent model: skellytracker 0020 keeps that rule outside the sidecar (`0020-roi-transform-and-source.md:18-19`). The skellytracker package does it with the object detector `KeypointBoundingBoxDetector`, configured in code, not in a sidecar (an axis-aligned square box from named parent points, `skellytracker/core/detectors/object_detectors/keypoint_bbox/keypoint_bbox_detector.py:53-70, 90-122`; the MediaPipe demo, `skellytracker/core/detectors/keypoint_detectors/mediapipe/run_demo.py:96-100`). Thus a host cannot run the refiner from the sidecars alone. |
| Measured difference | none for the workaround: the two-keypoint form gives the same tensor, but it gives no ROI. The ROI rule is the property that is missing. The probe geometry with this rule follows `HolisticLandmarker` within a median of 0.33 px (image) and 0.18 px (video) per hand (MediaPipe-Exporter `notes/decisions/0006-holistic-end-to-end-parity.md:40-45`). The measured difference of this section is for the case `decode-hand-from-loose-crop-roi` (part 2.3). A decode with the ROI `R` in place of the crop ROI `Rc` moves the centre of the refined ROI by 9.31 px (18.1 % of its size). The 40.6 px of 0006 (`:56-59`) is for a superseded form of the tracking rule. That rule makes the ROI from the previous landmarks (`docs/mediapipe-whole-body.md:395-399`). It is outside this section. For the input ROI: with `roi_source` (part 2.3, heading "ROI source"), the crop ROI of the reference files equals the crop ROI of the 0006 probe (`roi_from_pose`) for the 6 hands of the `source-upstream-*` vectors (maximum difference 0; scratch run of 2026-10-24). Without a declared rule, a host uses another rule, for example the axis-aligned box of `KeypointBoundingBoxDetector` (no rotation, no shift; centre the mean of index and pinky, size 3 times the largest pair distance in the docstring example, `keypoint_bbox_detector.py:16-20, 57-68`). No image run compares such a rule with the declared rule (part 5). |
| Row in "Considered and deliberately not added" | `crop_policy.border_mode`, rotated crops (`specs/model-sidecar/changelog.md:45`). The refiner input is a rotated crop with `BORDER_REPLICATE` (`docs/mediapipe-whole-body.md:390`). That row is the scope of skellytracker 0020. The 0020 proposal changes the row (its part 2.7, `:558-563`), and this proposal depends on it. The user decided on 2026-10-23 that the spec must describe face and hand ROI refiners. That is the evidence that a model needs the feature now. No row covers a role for an ROI refiner. |

**The face.** The user asked that the spec can describe a face ROI refiner. The primary document names
no dedicated face ROI refiner model:

- The Holistic face branch has no refiner model. It runs the short-range face detector (128²) inside a
  loose face ROI from the pose. It makes the face ROI from the detection. The ROI is the tight box
  of the 6 detection keypoints, with the rotation from keypoint 0 to keypoint 1 at target 0°. Then
  it applies scale 2.0 and `square_long`, with no shift (`docs/mediapipe-whole-body.md:445-464`). When the detector finds no face,
  there is no ROI and no face output in that frame (`:467-471`). The detector maps its detections to
  the image with the crop matrix (`:108-109`).
- Thus in Holistic, the face detector has the function of an ROI refiner. But it is an SSD object
  detector: 896 anchors, a score threshold, weighted NMS and `num_faces = 1` (`:201`, `:418-425`,
  `:458-461`, `:120-134`).
- The standalone FaceLandmarker makes its face rect from a full-image detection, and its next-frame
  ROI from the previous mesh (`:418-436`). Neither step is an ROI refiner model.
- The catalogue lists no other face model with an ROI output (`:194-205`).

This proposal does not invent a face refiner model. By user decision (Q2 = c, 2026-10-23), it also
defers the face rule: at `vNEXT`, `roi_decode.rect` has only the hand value `alignment_points`. The
section stays general. `rect` is an enum, so a later proposal can add a face value when a face model
needs it, without a new section. Part 8 gives the reason for the deferral.

**Missing primary evidence.** These facts have only secondary sources or no source:

- No ONNX file of a face model with an ROI output exists. No face refiner graph was read.
- The archived hand plan says "the face refines with a detector ... the hand refines with a 2-point
  regressor" (the untracked hand pipeline export plan of MediaPipe-Exporter (plan facts), secondary). The primary
  document gives the same facts (above).
- The archived plan says that `face_landmark_with_attention.tflite` refines landmarks, not an ROI
  (the untracked hand pipeline export plan of MediaPipe-Exporter (plan facts), secondary). The primary document does
  not cover it (it names the model only as "Not converted" in the conversion plan,
  the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts), secondary).
- No upstream output of the refined ROI exists. `HolisticLandmarker` gives the hand landmarks, not the
  ROI. Thus parity can compare the ROI only through the landmarks (part 5).
- The arithmetic precision: the primary document gives the formulas, not the float32 arithmetic of
  the calculators. **User decision (2026-10-24, Q7 = c of the 0020 proposal):** the spec states no
  precision, and the vectors give the tolerances (part 4). The 0020 proposal gives the scratch
  measurement (its part 1, the precision bullet; secondary): float32 against float64 changes the
  refined ROI by at most 0.049 px and 3.5e-4 rad over the real and random sets (the refiner output changes with the 1-level crop differences), and the hand
  landmarks after the inverse by a median of about 0.005 px.
- No real Holistic case for a vector of `roi_source`. The data of MediaPipe-Exporter 0006
  (`model_cache/probes/holistic_parity.json`) holds only the aggregate errors and counts, not the
  pose landmarks of a hand. Thus the vectors of `roi_source` use small synthetic points, with the
  expected values from the upstream formula (part 4). The parity run of part 5 uses the real sets.
- The per-point value of the parent. The Holistic gate reads the visibility of the BlazePose wrist
  (`holistic_hand_tracking.cc:80-91`). The current spec has no field for that visibility: the
  single-person `coordinate` decode gives `x, y` (and `z`) only
  (`specs/model-sidecar/post/pose-decode-coordinate.md:33`), and skellytracker 0021 covers a presence
  score, a class probability and world keypoints, not a visibility for each point
  (`specs/model-sidecar/decisions/0021-landmark-extra-outputs.md:11-18`). The visibility proposal adds it: a
  BlazePose parent declares `pose.decode.visibility: {source: keypoints_channel, channel: 3,
  activation: sigmoid}` (its part 2.2), and the gate has `value_default: visibility`. Until that proposal
  lands, a BlazePose parent cannot pass the parent check of the gate (`V-post.roi_refiner-15`). The
  BlazePose intake is the untracked intake of `mediapipe-pose39` of MediaPipe-Exporter (plan facts) (2026-10-24; deferred: the untracked blazepose plan of MediaPipe-Exporter (plan facts)). Its rows K5 and K8a link the visibility
  proposal. The flat `[1, 195]` output is a conditional gap there (rows G5a and K5).
- The hand-keypoint accuracy with the COCO-WholeBody names of the lists (user decisions T27 and T28 (H1)) is not
  measured. MediaPipe tuned the loose rect (`middle`, the size rule, scale 2.7) and the gate value 0.1 on BlazePose points and on
  the BlazePose visibility. A COCO-WholeBody parent gives hand MCP points from a whole-body model and
  a SimCC score (`post/pose-decode-simcc.md:38`), not a BlazePose visibility. Under option E (it
  replaced the interim A1 of T33), no RTMW size declares `pose.decode.visibility`, and only a
  BlazePose parent gives a `visibility` (`source: keypoints_channel`). Thus an RTMW parent
  gives only `score` at every size (OpenMMLab-Exporter decision 0041, rule S7, at `32ab848`; the visibility proposal records E in its status note).
  Thus the default gate value `visibility` and the default 0.1 do not fit such a parent.
  The runtime threshold of T26 (6) and the runtime gate value of T33 let a run read `score` with another threshold. A run with an RTMW parent sets the value `score`
  and a threshold for that RTMW size, because the RTMW score scale differs by size: on COCO val2017
  body points the raw score median is about 0.7 at 256x192, 4.1 for l-384 and 7.2 for x-384
  (secondary: the untracked pose-models plan of OpenMMLab-Exporter (plan facts), row "V-check"; scratch, not
  evidence). The same investigation found that the raw score ranks body visibility better than the
  RTMW visibility (AUC 0.86 to 0.87 against 0.70 to 0.76). The gate value is now measured
  (OpenMMLab-Exporter decision `notes/decisions/0041-rtmw-wrist-gate.md` at `32ab848`, 2026-10-24, evidence;
  COCO-WholeBody v1.0 val, 12704 hands, GT boxes): on the hands of the persons that Holistic can
  track (36.6 %), the RTMW body-wrist `score` ranks valid hands (`*hand_valid`) better than the
  BlazePose wrist visibility at every RTMW size (AUC 0.813 to 0.840 against 0.719; difference +0.094
  to +0.121), and a per-size threshold matches the Holistic gate recall, also in fp16. Thus an RTMW
  parent uses the gate value `score`. The RTMW `visibility` ranks worse than the `score` at every size and is
  dropped for all sizes (OpenMMLab-Exporter 0041, S7: option E). The hand root is not better than the body wrist (the T27 order stays).
  OpenMMLab-Exporter 0041 gives two thresholds of the RTMW `score` for each size (fit split; OpenMMLab-Exporter 0041, table
  "Thresholds"). **User decision T37 (2026-10-24):** the proposals give both. `t_recall` is the
  default recommendation: it gives the recall of the Holistic gate on valid hands. `t_J` (the
  Youden threshold) is the selective option. The fp32 threshold of a size also serves its fp16
  artifact (OpenMMLab-Exporter 0041, Qc). Table "RTMW gate thresholds":

  | RTMW size | `t_recall` (default recommendation) | `t_J` (selective option, Youden) |
  |---|---|---|
  | m | 0.256 | 0.686 |
  | l-256 | 0.290 | 0.724 |
  | x-256 | 0.276 | 0.726 |
  | l-384 | 1.912 | 3.702 |
  | x-384 | 2.974 | 7.198 |

  On all hands, `t_recall` opens 81 to 84 % of the hands (recall 0.986 to 0.990, false open 0.727 to
  0.771). `t_J` opens 28 to 34 % of the hands (recall 0.640 to 0.723, false open 0.112 to 0.170). The
  reason: once Holistic has a pose, its gate opens 96 % of the hands, so a threshold with its recall
  closes few hands (OpenMMLab-Exporter 0041, "Observations"). Neither threshold is a sidecar field (user decision U4),
  and the sidecar default stays the Holistic value (`visibility`, 0.1).
  OpenMMLab-Exporter 0041 did not measure the hand-keypoint accuracy of the paths (a), (b) and (c) of part 5, the loose rect on COCO-WholeBody points, a person-detector crop or video. The
  hand-keypoint accuracy of part 5 is still a later evaluation. It is not a parity gate.
- What MediaPipe does with a refined rect of size 0: the primary document does not say. The 0020
  proposal read `ValidateRoi` of MediaPipe (`calculators/tensor/image_to_tensor_utils.cc:92-102`,
  fetched at commit `e9794ef`; 0020 proposal `:72`, other source (b)). At the crop of the next model,
  a NaN value, `width <= 0` or `height <= 0` is an error, and MediaPipe makes no tensor (0020
  proposal `:390`). This session did not read that file again.

## 2. Spec change

### 2.1 Sections

**New section.** `post.roi_refiner`, title "ROI refiner", file `specs/model-sidecar/post/roi-refiner.md`.

```yaml
---
id: post.roi_refiner
title: ROI refiner
kind: postprocessor
since: vNEXT
changed_in: []
selectors:
  - role=roi_refiner
implemented_by:
  validate: missing
  decode: missing
external_impl: []
tests: []
vectors: vectors/post.roi_refiner.yaml
status: {spec: draft, validate: missing, decode: missing}
---
```

Row of the section map (`specs/model-sidecar/README.md`), under a new heading after "Pose-estimation
fields":

```markdown
### ROI refiner fields (`roi_refiner` role)

These fields apply when `role` includes `roi_refiner`.

| Section ID | File | Title |
|------------|------|-------|
| `post.roi_refiner` | [post/roi-refiner.md](post/roi-refiner.md) | ROI refiner |
```

**The `model_id` and the folder of a refiner (user decision Q3 = a, 2026-10-23).**

- A refiner sidecar goes under a new branch: `detectors/roi_refiners/{family}/{part}/{model_id}.yaml`.
  `{part}` is the body region whose ROI the model gives: `hand`, `face`, `body` or `wholebody`.
- `model_id` is `{family}-{part}-roi`, or `{family}-{part}-roi-{variant}` for a second refiner of one
  family and one part. Example: `detectors/roi_refiners/mediapipe/hand/mediapipe-hand-roi.yaml`.
- Reason: the role is not a keypoint role. The proposal `model-id-suffix` gives each id under
  `keypoint_detectors/` a `{keypoints}` token with a point count (its rule `V-common.identity-7` and
  `V-common.identity-9`). A refiner has no keypoints, so that grammar has no id for it (its Q1). A
  separate branch keeps that grammar unchanged. The token `roi` keeps the catalog key
  `<model_id>@<source.name>` (`common/identity.md:59`) different from a keypoint model of the same
  family and part. Qualcomm-Exporter names its hand landmark model `mediapipe-hand`
  (`0025-model-id-suffix.md:40-44`), so `{family}-{part}` alone can collide.
- The ONNX file names follow the existing rule: `{model_id}-{size}_{batch}_{precision}.onnx`
  (`format/file-layout.md:30`).
- This decision answers the pipeline-stage question Q1 of the OpenMMLab-Exporter proposal
  `model-id-suffix`. A pipeline stage can give no keypoints and give the ROI of the next model. Such
  a stage is an ROI refiner. It takes this branch and this id. That proposal keeps its grammar for
  `keypoint_detectors/`.

**Places that the change edits.** The line numbers are at skellytracker `dom/18-agents-adr-bootstrap-kit`.

| Place | Heading | Edit |
|---|---|---|
| `specs/model-sidecar/README.md:7-14` | Overview, the role table | Add the row `roi_refiner`: "ROI refinement, for example the MediaPipe hand ROI refinement model. The model reads a crop of an ROI and outputs points. The host makes the ROI of the next model from the points." Change "Sidecars support two model **roles**" to "three". Add: "`roi_refiner` is always the only role of its sidecar." |
| `specs/model-sidecar/README.md:36-95` | Section map | Add the heading and the row above. |
| `specs/model-sidecar/README.md:97-123` | Validation rules (the index) | Add `- [ROI refiner](post/roi-refiner.md#validation-rules)` after "Bottom-up pose". |
| `specs/model-sidecar/common/identity.md:29` | Fields, `model_id` | Add: "For an ROI refiner, it is `{family}-{part}-roi` or `{family}-{part}-roi-{variant}`, for example `mediapipe-hand-roi` (see ROI refiner (`../post/roi-refiner.md#fields`))." |
| `specs/model-sidecar/common/identity.md:31` | Fields, `role` | New text: "One or both of `object_detector` and `pose_estimator`, or `roi_refiner` alone. ..." |
| `specs/model-sidecar/common/identity.md:37` | `V-common.identity-2` | Changed (see 2.4). |
| `specs/model-sidecar/common/identity.md:47-51` | Legacy behaviour | New row (see 2.6). |
| `specs/model-sidecar/common/identity.md:80-81` | Authoring guidance | Replace the bullet "The MediaPipe hand re-crop model has no `role` value that fits ..." (`:81`) with this text: "Write `role: [roi_refiner]` for a model that gives the ROI of the next model. An example is the MediaPipe hand ROI refinement model. Do not write `pose_estimator` with two points." Cite the accepted decision. The bullet of `:80` also names the plan id `mediapipe-hand-recrop`: write `mediapipe-hand-roi` there (user decision Q3 = a). |
| `specs/model-sidecar/common/outputs.md:29` | Fields, `semantic` | Add `roi_points` to the closed set. Add: "`roi_points` goes to `roi_decode`. It requires `role: [roi_refiner]`." |
| `specs/model-sidecar/common/outputs.md:35` | Behaviour | Add the routing sentence for `roi_points`. |
| `specs/model-sidecar/common/outputs.md:44` | `V-common.outputs-4` | Changed (see 2.4). |
| `specs/model-sidecar/common/input.md:37` | Fields | Change "`input` is required for `object_detector` and `pose_estimator` sidecars" to include `roi_refiner`. |
| `specs/model-sidecar/common/sizes-and-artifacts.md:49-54` | The table "Contract part \| Where it lives" | Add the row "`roi_decode` \| top level, when `role` is `[roi_refiner]`". `V-common.sizes_and_artifacts-3` (`:111`) does not change in this proposal. The A1 text of the visibility proposal (user decision T33) changed the same table and rule. Its rewrite for option E (OpenMMLab-Exporter 0041) edits no place of `common/sizes-and-artifacts.md` (its part 2.1), so this is not a merge point. |
| `specs/model-sidecar/format/file-layout.md:44-76` | Storage layout (tree and branch table) | Add the branch `roi_refiners/{family}/{part}/` with `{model_id}.yaml` and the ONNX files, and the table row: "`detectors/roi_refiners/{family}/{part}/` \| `roi_refiner` \| ROI refiners for each body region: `hand`, `face`, `body` and `wholebody`." |
| `specs/model-sidecar/format/file-layout.md:155-157` | Authoring guidance | Add the MediaPipe-Exporter path `roi_refiners/mediapipe/hand/` when the exporter writes it. |
| `specs/model-sidecar/format/versioning.md:51-63` | Version-aware compatibility | No new link. The new section has a heading "Legacy behaviour" that points to `format.versioning`, as `pre.resize.fit` does (`pre/resize-fit.md:57-59`) and as the 0020 proposal does for its section (0020 proposal `:194`). See part 2.6. |
| `specs/model-sidecar/format/versioning.md:72-74` | Legacy behaviour | Add `roi_refiner` role and `roi_points` semantic to the "Not available" row (see 2.6). |
| `specs/model-sidecar/pre/resize-rotated-roi-crop.md` (new in the 0020 proposal) | Validation rules, `V-pre.resize.rotated_roi_crop-1` | Changed (see 2.4): the rule also allows `role: [roi_refiner]`. |
| `specs/model-sidecar/pre/resize-rotated-roi-crop.md` (new in the 0020 proposal) | ROI source | The heading already names an ROI refiner as a source (0020 proposal `:318`). After its last sentence "A model with rotated_roi_crop needs no box from an object detector." (0020 proposal `:320`) add: "An roi_refiner sidecar declares how the host makes the ROI of its own input from the keypoints of a parent pose model (ROI refiner (`../post/roi-refiner.md#roi-source`))." No other edit. (Before T22 (1), this row changed a sentence on `pose.requires_object_detector`. The 0020 proposal removed that field and that sentence, user decision 2026-10-24.) |
| `specs/model-sidecar/post/pose-schema.md:58-60` | `pose.tracked_points` | Add: "Another sidecar can name these points, for example `roi_source` of an ROI refiner (ROI refiner (`roi-refiner.md#roi-source`)). The host checks such a name against this list. Thus a renamed point breaks that sidecar." (User decision T24: names, not indices.) |
| `specs/model-sidecar/post/pose-decode-simcc.md:38`, `specs/model-sidecar/post/pose-bottom-up.md:25, 36`, `specs/model-sidecar/post/pose-decode-heatmap.md:24`, `specs/model-sidecar/post/pose-decode-coordinate.md:33` | Behaviour | No edit. The heading "ROI source" of `post.roi_refiner` names the per-point values of a parent through the heading "Per-point values" of `post.pose.visibility` (the visibility proposal), which edits only `pose-decode-coordinate.md:33` of these (its part 2.1). Under option E it does not edit `pose-decode-simcc.md:38`, `pose-bottom-up.md` or `pose-decode-heatmap.md`. |
| `specs/exporter-guide/sidecars/workflow/phase-1-intake.md:14-16` | Phase 1, step 1 (the start of the runtime contract) | After the edit of the 0020 proposal, add: "For an ROI refiner, the contract starts at the keypoints and the named per-point value of the parent pose model that `roi_source` names." |
| `specs/exporter-guide/sidecars/workflow/phase-1-intake.md:36-38` | Phase 1, the verdict `out of scope` | The examples "a step that makes the box from the outputs of another model, a gate that decides if the model runs" stay. Add: "For an ROI refiner, the steps and the gate that `roi_source` declares are in the contract (`post.roi_refiner`)." |
| `specs/model-sidecar/templates/model-intake.md:113, 368-370` | Verdicts, and the out-of-scope rows (X1) | The same two edits as in the exporter guide. |
| `specs/model-sidecar/templates/model-intake.md` (a new row after F2, or a new group "R" for `roi_refiner`) | Rows | Add a row: "R1 ROI source of the input (`roi_source`): the parent points by name (an ordered list of accepted names for each point), the derived points, the rect rule and the score gate (the named per-point value and the default threshold)" with the section `post.roi_refiner`. The layout of the rows is for the implementer of the template. |
| `specs/model-sidecar/post/unprojection.md:21-36` | Behaviour | Add: "An ROI refiner gives its ROI in source-image pixels. The host maps its points with the inverse of its input crop first (ROI refiner (`roi-refiner.md#behaviour`))." The front matter `selectors` gets `role=roi_refiner`. The 0020 proposal adds the inverse of `rotated_roi_crop` to the list of inverses (its part 2.1, `:191`). |
| `specs/model-sidecar/changelog.md:14-36` | Summary of changes | New row N, the next free number at merge time (see 2.7). The 0020 proposal adds its row first (its part 2.7, `:552-556`). 13 open proposals (9 of OpenMMLab-Exporter, 4 of MediaPipe-Exporter) add a summary row, so the numbers depend on the merge order. |
| `specs/model-sidecar/changelog.md:65-68` | `schema_version` history | Add text to the `vNEXT` row (see 2.7). |
| `specs/exporter-guide/sidecars/rules.md:6-8` | Rules, "Known case" | Replace with: "Known case: an ROI refiner is a model that gives a region of interest to the next model, for example the MediaPipe hand ROI refinement model. Write `role: [roi_refiner]` and the section `post.roi_refiner`. Do not describe it as a pose estimator with two fake keypoints." |
| `specs/exporter-guide/sidecars/workflow/phase-1-intake.md:30-31` | Phase 1, verdict `gap` | Remove "or a role for an ROI refiner" from the examples. |
| `specs/exporter-guide/sidecars/workflow/mapping-hints.md:13-26` | Mapping hints, Identity | Add the `model_id` rule of the refiner. |
| `specs/exporter-guide/sidecars/workflow/mapping-hints.md:71` | Near-misses seen so far | Keep the bullet. Add "Write `role: [roi_refiner]`." |
| `specs/exporter-guide/sidecars/sidecar-files.md:34-43` | Path | Add `roi_refiners/{family}/{part}/{model_id}.yaml` for an ROI refiner. |
| `specs/exporter-guide/sidecars/known-open-items.md:13` | Known open items | Change the MediaPipe-Exporter and Qualcomm-Exporter row: the hand re-crop model takes `role: [roi_refiner]`. |
| `specs/model-sidecar/templates/model-intake.md:118, 175-178, 355, 362` | Verdicts, near-misses, row L1 | Remove "a model that gives a crop region" from the gap examples. Point the near-miss bullet to `post.roi_refiner`. Add the `roi_refiners/` path to row L1. |
| `specs/model-sidecar/templates/model-intake.md:229` | Row F1 (`model_id`) | Add: "An ROI refiner uses `{family}-{part}-roi`, or `{family}-{part}-roi-{variant}` for a second refiner of one family and one part (`post.roi_refiner`)." |
| `specs/model-sidecar/templates/model-intake.md:230` | Row F2 (`role`) | New text: "`role`: `object_detector`, `pose_estimator`, or both; or `roi_refiner` alone". Add `post.roi_refiner` to the section column. |
| `specs/model-sidecar/templates/model-intake.md:290` | Row D1 (semantic of each output) | Add `roi_points` to the list. Add `post.roi_refiner` to the section column. |
| `specs/model-sidecar/inventory.yaml:107-113, 123-129` | `proposed` | Change the notes of `mediapipe-hand-recrop@*`. The key becomes `mediapipe-hand-roi@mediapipe-exporter` (user decision Q3 = a). The non-spec PR removes the entries when an example exists. |
| `specs/model-sidecar/TRACEABILITY.md:107-108` | Proposed models | Regenerated from the inventory. Add the new section to the section tables. |
| `tools/sidecar_normalize.py` | selector matching | `role=roi_refiner` must match the new section. For the implementer. |
| `notes/decisions/open-work.md:125-131` | Open work, "Spec defects", the 0025 item | The user decision Q3 = a of this proposal answers its sentence on the re-crop model. |
| skellytracker `specs/model-sidecar/decisions/0008-vnext-scope.md:8-15` (accepted) | Decision, the exporters of the `vNEXT` scope | No edit from this proposal. The scope must include MediaPipe-Exporter (user decision Q1 = a). The 0020 proposal lands first, and its small scope entry makes the change: it supersedes in full the scope entry in force (0008, or the scope entry of the OpenMMLab-Exporter proposal `nms-clamp-order`), names the hand landmark model and the hand ROI refinement model, and holds only scope rules (0020 proposal part 2.1, `:138-151`; the form is its Q10, revised by the user, T34 (N2) and T35, `:1831-1833`; the text is its heading "Scope entry (user decision T35)"). The entry of this proposal cites that scope entry. |
| `specs/model-sidecar/changelog.md:5-10` | Changes in this revision, the note "For reviewers" | No edit from this proposal. The 0020 proposal adds MediaPipe-Exporter, with the hand ROI refinement model, to the note (its part 2.1, `:195`; part 2.7, `:572-573`). |

### 2.2 Fields table

| Field | Type | Required | Description |
|---|---|---|---|
| `role` | array[enum] | yes | `[roi_refiner]`. `roi_refiner` is always the only value. |
| `outputs[].semantic` | enum | yes | `roi_points` for the one output of the refiner. |
| `roi_decode` | object | yes (`roi_refiner`) | How the host makes one ROI from the output of each batch item. Its keys are a closed set: `point_count`, `coordinate_scale`, `rect`, `rotation` and `transform` (`V-post.roi_refiner-4`). |
| `roi_decode.point_count` | int | yes | The number of points `P` in each batch item. It must be at least 2. |
| `roi_decode.coordinate_scale` | enum | yes | `pixel` (model-input pixels) or `normalized_01` (multiply `x` by `T_w` and `y` by `T_h`). The same meaning as `pose.decode.coordinate_scale` (`post.unprojection`). |
| `roi_decode.rect` | enum | yes | `alignment_points`, the only value at `vNEXT`. See "Behaviour". The set is closed. A later proposal can add a value (for example a face rule). |
| `roi_decode.rotation` | object | yes | The rotation vector. |
| `roi_decode.rotation.start_point` | int | yes (in `rotation`) | The index of the start point, `0 <= i < P`. For `alignment_points`, it is also the centre. |
| `roi_decode.rotation.end_point` | int | yes (in `rotation`) | The index of the end point, `0 <= i < P`, not equal to `start_point`. For `alignment_points`, it also sets the size. |
| `roi_decode.rotation.target_angle_deg` | float | yes (in `rotation`) | The direction, in degrees, that the vector from the start point to the end point has after the next crop is made upright. `90` means up. `-90` means down. |
| `roi_decode.transform` | object | no | An ROI transform, as the heading "ROI transform" of `pre.resize.rotated_roi_crop` defines it (0020 proposal `:325-337`). It is the same object type as `input.resize.crop_policy.transform` (0020 proposal `:224-228`). It has the same keys `shift_x`, `shift_y`, `square_long` and `scale`, and the same types. It has the same defaults (`0.0`, `0.0`, `false`, `1.0`) and the same order of the steps. `scale` must be a finite number `> 0`. Without the field, the ROI does not change. |
| `roi_source` | object | yes (`roi_refiner`) | How the host makes the ROI `R` of each input crop from the keypoints of a parent pose model (heading "ROI source"). Its keys are a closed set: `method`, `instances`, `derived_points`, `score_gate`, `rect` and `rotation` (`V-post.roi_refiner-10`). User decision T24 (2026-10-24). |
| `roi_source.method` | enum | yes | `parent_keypoints`, the only value at `vNEXT`. The set is closed. A later proposal can add a value (for example an ROI from a detector box). |
| `roi_source.instances` | array[object] | yes | One item for each ROI that the host makes from one parent pose, in this order. For the hand: `left` and `right`. At least one item. |
| `roi_source.instances[].name` | string | yes | The name of the instance, unique in the list (for example `left`). The host tags the ROI, and the output of the next model, with it. |
| `roi_source.instances[].points` | map[string, array[string]] | yes | A map from a local name (for example `wrist`) to an ordered list of accepted names of the `pose.tracked_points` of the parent sidecar (for example `[left_wrist, left_hand_root]`). Names, not indices. The list has at least one name. The host uses the first name of the list that the parent has (user decision T27). Every instance has the same local names. In one instance, a name must not be in one list twice or in two lists. |
| `roi_source.derived_points` | map[string, map[string, number]] | no | Derived points: a new local name to a map of weights over the local names of `points`. The point is `(w1 * q1 + w2 * q2 + ...) / (w1 + w2 + ...)`. This is the weighted form of `pose.derived_points` (`post/pose-schema.md:73-81`), with no dropped point. Each weight is a finite number `> 0`. A derived name must not be a local name of `points`. A weight names a point of `points`, not another derived point. |
| `roi_source.score_gate` | object | no | `{point, value_default, score_threshold_default}`. An instance runs only when the per-point value `v` of the parent point that the local name `point` names is `> t` (strict). `v` is the gate value: a runtime value of the host or of the user, or `value_default` when no runtime value is set (user decision T33). `t` is the gate threshold: a runtime value of the host or of the user, or `score_threshold_default` when no runtime value is set (user decision T26 (6)). `point` names a local point of `points`, not a derived point. Without the field, every instance runs, and the host has no gate value and no gate threshold. |
| `roi_source.score_gate.value_default` | enum | yes (in `score_gate`) | The default gate value: the per-point value of the parent that the gate reads when no runtime gate value is set. `score` or `visibility` (heading "Per-point values" of `post.pose.visibility`, the visibility proposal). It is host policy, and the host or the user can override it at run time with `score` or `visibility` (user decision T33). It has no default in the spec. For the hand: `visibility`, the Holistic value (`holistic_hand_tracking.cc:80-91`). |
| `roi_source.score_gate.score_threshold_default` | float | yes (in `score_gate`) | The default gate threshold `t`, for `value_default`. For `value_default: visibility`, a finite number with `0 <= t < 1`. For `value_default: score`, any finite number (a SimCC score has no fixed range). It is host policy, and the host or the user can override it at run time. The range of a runtime threshold follows the gate value in effect (rule `-16`). A runtime gate value other than `value_default` needs a runtime threshold, because this default goes with `value_default`. The comparison stays strict: `v > t`. The name follows `decode.confidence_threshold_default` (`post/detection-decode.md:42`). Unlike that field, it has no default in the spec: the value depends on the score of the parent. For the hand: `0.1`, the Holistic value (`holistic_hand_tracking.cc:91`). |
| `roi_source.rect` | enum | yes | `alignment_points`: the rect rule of `roi_decode` (heading "Behaviour", step 3). The only value at `vNEXT`. |
| `roi_source.rotation` | object | yes | `{start_point, end_point, target_angle_deg}`, as `roi_decode.rotation`, but `start_point` and `end_point` are local names (of `points` or of `derived_points`), not indices. They must be different. `target_angle_deg` is a finite number. |

**The point names (proposal choice, from user decision T24; the lists are user decisions T27 and T28 (H1)).**
`roi_source` names the parent points with the names of the `pose.tracked_points` of the parent
sidecar. Each local point has an ordered list of accepted names. It does not use the canonical names
of `post.pose.canonical_mapping` as the key, and it does not use both. The reasons:

- `tracked_points` is required for every `pose_estimator` (`V-post.pose.schema-1`,
  `post/pose-schema.md:117`), and its names are the names of the model outputs in output order
  (`:58-60`). Thus the host can check each name against the parent sidecar, and refuse a parent
  that has none of the names of a list (`V-post.roi_refiner-15`). That is the purpose of T24.
- No canonical body name exists for the BlazePose pinky and index points. The canonical body names
  are the COCO-WholeBody body names plus four computed markers (`post/canonical-mapping.md:80`). The
  skellytracker MediaPipe body mapping maps `left_wrist` and `right_wrist`, and no `left_pinky`,
  `left_index`, `right_pinky` or `right_index`
  (`skellytracker/core/detectors/keypoint_detectors/mediapipe/body/mediapipe_body_to_canonical_mapping.yaml:17-48`).
- The canonical hand names `index_finger_mcp` and `pinky_mcp` (`post/canonical-mapping.md:81`;
  `.../mediapipe/hands/mediapipe_hand_to_canonical_mapping.yaml:14, 26`) name the same joints as
  BlazePose 19 and 17 (the index MCP and the pinky MCP, `docs/mediapipe-whole-body.md:372`) and as
  the COCO-WholeBody `forefinger1` and `pinky_finger1` (the skellytracker RTMW mapping,
  `rtmw_wholebody_to_canonical_mapping.yaml:23, 35`). But they are names of the hand region. The
  spec does not map a body point to them.
- `pose.canonical_mapping` is optional (`post/pose-schema.md:42`), and no exporter writes it
  (`post/canonical-mapping.md:99`). Its names will change to the VRM 1.0 names
  (`post/canonical-mapping.md:85`).
- Thus a canonical name cannot be the key today, and "both" adds a second name set that no parent
  writes. The lists of T27 reach the same parents with names that the parents write.

The lists of the hand excerpt (user decisions T27 and T28 (H1)):

| Local name | Left instance | Right instance |
|---|---|---|
| `wrist` | `[left_wrist, left_hand_root]` | `[right_wrist, right_hand_root]` |
| `pinky` | `[left_pinky, left_pinky_finger1, left_hand_pinky_finger1]` | `[right_pinky, right_pinky_finger1, right_hand_pinky_finger1]` |
| `index` | `[left_index, left_forefinger1, left_hand_forefinger1]` | `[right_index, right_forefinger1, right_hand_forefinger1]` |

- The first name of each list is the BlazePose name of the skellytracker package
  (`skellytracker/core/detectors/keypoint_detectors/mediapipe/body/mediapipe_body.yaml:24-29`:
  `left_wrist`, `right_wrist`, `left_pinky`, `right_pinky`, `left_index`, `right_index`, at the
  output indices 15 to 20). MediaPipe names them `kLeftWrist`, `kRightWrist`, `kLeftPinky1`,
  `kRightPinky1`, `kLeftIndex1` and `kRightIndex1` (`pose_topology.h:37-42`). No MediaPipe pose
  sidecar exists yet. The intake of that model must use these names, or this sidecar must change
  with it.
- The second name is the COCO-WholeBody 133 name of OpenMMLab-Exporter RTMW (`rtmw/keypoints.py:104,
  109, 121, 125, 130, 142` at `d0f4343`; the same at `32ab848`). The user decision T27 names RTMW, DWPose and ViTPose++ as
  parents with these names. This file read the names of RTMW only.
- An RTMW parent has both `left_wrist` (a body point, `rtmw/keypoints.py:22`) and `left_hand_root`
  (the root of the hand points, `:104`). The host takes the first name, so the wrist of an RTMW
  parent is the body wrist (vector `source-alias-second-name-wholebody`). The pinky and the index of
  an RTMW parent use the second names.
- The host accepts an RTMW parent (vector `parent-wholebody-names-accepted`). Before T27, the host
  refused it. The hand-keypoint accuracy with the COCO-WholeBody names is **not measured**: MediaPipe tuned the loose rect and the
  gate default on BlazePose points and visibility (part 1, "Missing primary evidence"; part 5, the
  later evaluation). The gate value of an RTMW parent is measured: `score` at every size, with a threshold for each size (OpenMMLab-Exporter 0041 at `32ab848`; part 1).
- The third name of the pinky and index lists is the spelling of the skellytracker spec example
  (`specs/model-sidecar/examples/detectors/shared/skeletons/coco133_tracked_points.yaml:102, 114, 123, 135`:
  `left_hand_forefinger1`, `left_hand_pinky_finger1`, and the right side; user decision T28 (H1)).
  The example and mmpose spell these two points differently (part 1). The example spells the body
  wrist (`:15-16`) and the hand root (`:97, 118`) as mmpose does, so the wrist list has no third
  name: a third name would repeat a name, and rule `-11` refuses one name twice in one list. The
  host accepts a parent with the example names (vectors `parent-example-names-accepted` and
  `source-alias-third-name-example`). A parent with none of the names of a list is still refused
  (vectors `parent-error-no-accepted-name` and `source-error-no-accepted-name`).

The input of a refiner is a crop: `input.resize.method: rotated_roi_crop`
(Rotated ROI crop (`../pre/resize-rotated-roi-crop.md`)). The host gives one ROI `R` for each batch
item (its heading "ROI source"). For a refiner, `roi_source` says how the host makes `R` (heading "ROI
source" of this section). The crop changes `R` with `crop_policy.transform` and
`maintain_aspect_ratio`, and gives the crop ROI `Rc` (its Behaviour steps 1 to 3). The decode maps the
points with the inverse of that crop (its heading Inverse (`../pre/resize-rotated-roi-crop.md#inverse`))
and `Rc`. An item with no crop has no output. The refiner gives one ROI, or no ROI, for each batch
item, in the same order.

YAML excerpt (the MediaPipe hand ROI refinement model). The `input` block is excerpt 2 of the 0020
proposal (`:274-287`):

```yaml
input:
  name: input_1
  layout: NCHW
  resize:
    method: rotated_roi_crop
    interpolation: linear
    crop_policy:
      transform: {shift_y: -0.1, square_long: true, scale: 2.7}   # docs/mediapipe-whole-body.md:387-389
      maintain_aspect_ratio: true                                 # docs/mediapipe-whole-body.md:390
      border_mode: replicate                                      # docs/mediapipe-whole-body.md:390
role: [roi_refiner]
outputs:
  - name: Identity
    dtype: {fp32: float32}
    shape: [-1, 1, 1, 4]
    rank: 4
    semantic: roi_points
roi_decode:
  point_count: 2
  coordinate_scale: pixel
  rect: alignment_points
  rotation: {start_point: 0, end_point: 1, target_angle_deg: -90}
  transform: {shift_x: 0.0, shift_y: -0.1, square_long: true, scale: 1.0}
roi_source:                                  # user decision T24 (2026-10-24)
  method: parent_keypoints
  instances:                                 # docs/mediapipe-whole-body.md:381-383
    - name: left                             # the lists: user decision T27
      points:                                # (BlazePose; mmpose COCO-WholeBody 133; spec example, T28 (H1))
        wrist: [left_wrist, left_hand_root]
        pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1]
        index: [left_index, left_forefinger1, left_hand_forefinger1]
    - name: right
      points:
        wrist: [right_wrist, right_hand_root]
        pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1]
        index: [right_index, right_forefinger1, right_hand_forefinger1]
  derived_points:
    middle: {index: 2, pinky: 1}             # (2·index + pinky) / 3, docs/mediapipe-whole-body.md:387
  score_gate:                                # strict >, docs/mediapipe-whole-body.md:384-386
    point: wrist
    value_default: visibility                # a runtime input (T33); the BlazePose visibility (pose.decode.visibility of the parent)
    score_threshold_default: 0.1             # a runtime input (T26 (6)); holistic_hand_tracking.cc:91
  rect: alignment_points                     # the rule of roi_decode step 3
  rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90}
```

The batch axis of the ONNX file is 1 today (`[1, 1, 1, 4]`). The `-1` in the excerpt follows the
spec examples. Skellytracker 0019 (proposed) covers the batch axis of `outputs[].shape`.

The excerpt has two transforms. They do not overlap:

- `input.resize.crop_policy.transform` (scale 2.7) changes the loose ROI before the crop. With it,
  the host gives the raw loose rect that `roi_source` makes. This place is the user decision T23,
  Q2 = a, of the 0020 proposal (2026-10-24; 0020 proposal `:1804-1807`).
- `roi_decode.transform` (scale 1.0) changes the refined ROI after the decode (step 4). It is the
  output rule of the refiner (`docs/mediapipe-whole-body.md:391-394`).

### 2.3 Behaviour

Normative text of `post.roi_refiner`, heading "Behaviour":

```text
An ROI is (cx, cy, w, h, rotation) in source-image pixels, as the heading "ROI" of
Rotated ROI crop (pre.resize.rotated_roi_crop) defines it. The ROI that this section outputs has a
rotation in [-pi, pi) (step 3).

The input crop. The host crops the input of each batch item b with rotated_roi_crop. Rc[b] is the
crop ROI of that crop: the result of steps 1 to 3 of Rotated ROI crop, after crop_policy.transform
and maintain_aspect_ratio. If Rotated ROI crop gives no crop for item b, the item has no input
tensor, and the output for item b is "no ROI".

For each batch item b that has a crop, with the crop ROI Rc[b] and the model input size [T_h, T_w]:

1. Read the points.
   v = the elements of item b of the roi_points output, in row-major order.
   P = roi_decode.point_count. D = len(v) / P. D must be an integer and D >= 2.
   pts = v reshaped to [P, D]. Use columns 0 and 1 (x, y). Do not use the other columns.
   If coordinate_scale is normalized_01: x = x * T_w, y = y * T_h.
   Now pts are in model-input pixels.
   If a value of pts is not finite, the output for item b is "no ROI". Do not do steps 2 to 5.

2. Map the points to the source image.
   pts_src = the inverse of Rotated ROI crop (its heading "Inverse") with Rc[b], applied to pts.
   Use Rc[b]. Do not use the ROI that the host gave.
   If a value of pts_src is not finite, the output for item b is "no ROI". Do not do steps 3 to 5.

3. Make the rect from pts_src (rect: alignment_points).
   (x0, y0) = pts_src[start_point], (x1, y1) = pts_src[end_point]
   target   = target_angle_deg * pi / 180
   theta    = normalize(target - atan2(-(y1 - y0), x1 - x0))
   normalize(a):
     r = a - 2 * pi * floor((a + pi) / (2 * pi))
     if r < -pi:  r = r + 2 * pi
     if r >= pi:  r = r - 2 * pi
     the result is r
   (cx, cy) = (x0, y0)
   w = h = 2 * sqrt((x1 - x0)^2 + (y1 - y0)^2)
   ROI = (cx, cy, w, h, theta)

4. Transform the ROI, if roi_decode.transform is present. Apply the ROI transform of Rotated ROI
   crop (its heading "ROI transform") with the fields of roi_decode.transform. Without
   roi_decode.transform, the ROI does not change.

5. Check the ROI with the validity test of Rotated ROI crop (its heading "ROI"): the ROI is valid
   only when its five values are finite, w > 0 and h > 0 (strict). A valid ROI is the output for
   item b. For an ROI that is not valid, the output for item b is "no ROI". The host does not crop
   for that item.

The section states no arithmetic precision. The vectors give the tolerances.
```

Normative text of `post.roi_refiner`, heading "ROI source" (user decision T24, 2026-10-24):

```text
## ROI source

roi_source tells the host how to make the ROI R of each input crop of the refiner from the
keypoints of a parent pose model. The host gives R to the input crop (Rotated ROI crop, heading
"ROI source"). The crop then applies crop_policy.transform and its validity test.

At vNEXT, roi_source.method is parent_keypoints.

The gate value and the gate threshold. If roi_source.score_gate is present:
- The gate value g is a runtime value that the host or the user sets (score or visibility), or
  score_gate.value_default when no runtime value is set.
- The gate threshold t is a runtime value that the host or the user sets, or
  score_gate.score_threshold_default when no runtime value is set. score_threshold_default goes
  with value_default: if g is not score_gate.value_default, a runtime threshold must be set.
- t must be in the range of g: a finite number with 0 <= t < 1 for visibility, and a finite number
  for score.
The host must refuse a runtime value that does not obey these rules. It must not clamp it, and it
must not use another value in its place. If roi_source.score_gate is absent, the host must refuse a
runtime gate value and a runtime gate threshold. The comparison of step 1 is strict for every
value of t.

The parent. The parent is a pose_estimator sidecar that the host runs before the refiner. Before the
first run, the host must check the parent at the size of the parent that the run uses:
- For each instance i and each local name n, the parent name p[i][n] is the first name of the list
  instances[i].points[n] that is in pose.tracked_points of the parent. If no name of the list is
  in pose.tracked_points, the check fails.
- If roi_source.score_gate is present, the decode of the parent at that size must give the
  per-point value g (Keypoint visibility, heading "Per-point values"). For example, an RTMW parent
  gives only score at every size, and a BlazePose parent gives only visibility.
If a check fails, the host must refuse the parent, with a message that names the failed check (the
local point with no accepted name, or the gate value g and the parent size). The host must not run
the refiner with it. When the parent gives no value g, the host must not skip the gate and must not
read another value in its place.

The per-point values of the parent are the named values of Keypoint visibility (post.pose.visibility,
heading "Per-point values"): score, and visibility when the parent declares pose.decode.visibility.
The host must not give one value in the place of the other.

For each pose of the parent (one person), and for each instance i in the order of
roi_source.instances:

1. Gate. If score_gate is present:
     s = the per-point value g of the parent point p[i][score_gate.point]
   If s > t is false, instance i has no ROI. (A NaN value gives false.) Do not do steps 2 to 5.
2. Read the points. For each local name n of instances[i].points:
     q[n] = (x, y) of the parent point p[i][n], in source-image pixels (after the unprojection of
            the parent)
   If a value of q is not finite, instance i has no ROI. Do not do steps 3 to 5.
3. Derived points. For each entry d: {n1: w1, n2: w2, ...} of derived_points:
     q[d] = (w1 * q[n1] + w2 * q[n2] + ...) / (w1 + w2 + ...)     (for x and for y)
4. Rect. Make the ROI with the rect rule of step 3 of "Behaviour" (rect: alignment_points), with
     (x0, y0) = q[rotation.start_point], (x1, y1) = q[rotation.end_point],
     target_angle_deg = rotation.target_angle_deg.
   The result is R = (cx, cy, w, h, theta), with theta in [-pi, pi).
5. Check. If R is not valid (Rotated ROI crop, heading "ROI"), instance i has no ROI.

The host tags R, and the output of the models that use it, with instances[i].name. An instance with
no ROI has no crop of the refiner in that frame.
```

Notes on "ROI source", not normative:

- **One rect rule, proved by vectors.** The loose rect of Holistic has the centre `middle`, the size
  `2 · |middle − wrist|`, and the rotation from the wrist to `middle` with the target 90°
  (`docs/mediapipe-whole-body.md:387-389`; `hand_detections_from_pose_to_rects_calculator.cc:69,
  93-113, 124-152`). The rule `alignment_points` of step 3 has the centre at the start point and the
  rotation from the start point to the end point. With start `middle`, end `wrist` and target −90°,
  it gives the same centre and the same size. The rotation is the same angle: the vector from
  `middle` to the wrist is the negative of the vector from the wrist to `middle`, so `atan2` changes
  by `pi`, and the target changes by `pi` too. Thus `roi_source` reuses the rule of `roi_decode`,
  and the section has no second rect rule. The vectors `source-upstream-up-and-right`,
  `source-upstream-down-and-left` and `source-upstream-diagonal` prove it: their expected values
  come from a transcription of the upstream formula (not from the reference file), and the
  reference file gives them within `1e-9` px and `1e-12` rad (directions up, right, down at the
  `+pi` tie, left, and a diagonal). A scratch sweep of 2026-10-24 (200,000 random hands and
  near-ties, float64) gave at most `2.9e-14` px for the centre and the size and `8.9e-16` rad for the
  rotation modulo 2π. In 49 cases the two values differed by 2π: at the `±pi` tie, the clamp of
  step 3 gives a value in `[-pi, pi)` (user decision R2), and the upstream formula without a clamp
  gave a value out of that range in 29 cases. The crop uses only the cosine and the sine
  (0020 proposal `:310-311`), so the crops are the same.
- **The full loose ROI.** `roi_from_keypoints`, then `crop_roi` of the 0020 reference file with the
  `crop_policy` of the excerpt, gives the same crop ROI as `roi_from_pose` of the 0006 probe
  (`notes/decisions/scripts/hand_roi_reference.py:47-52`) for the 6 hands of the three
  `source-upstream-*` vectors: maximum difference 0 (scratch run of 2026-10-24).
- **The gate.** MediaPipe compares the float32 visibility, cast to double, with the double `0.1`:
  `static_cast<double>(score) > threshold_` (`calculators/util/thresholding_calculator.cc:123-124`).
  The vector `source-gate-tie-no-roi` gives the score `0.1` as a float64 value, so the strict test
  fails. A float32 score of `0.1` is `0.10000000149011612` as a float64 value (a NumPy check), and it
  passes the test. Thus a tie depends on the value that the parent decode gives, not on this rule.
- **The gate threshold is a runtime input (user decision T26 (6)).** Holistic fixes the value 0.1 in
  the graph: `IsOverThreshold(score, /*threshold=*/0.1, graph)` (`holistic_hand_tracking.cc:91`;
  `docs/mediapipe-whole-body.md:384-386`). The sidecar gives that value as
  `score_threshold_default`, and the host or the user can set another value at run time. The name
  and the form follow `decode.confidence_threshold_default`: a default in the sidecar, host policy
  that callers can override, and a strict `score > threshold` (`post/detection-decode.md:42`). The
  range of a runtime value follows the gate value in effect (rule `-16`; user decision T33): `[0, 1)`
  for `visibility`, and any finite number for `score`. The spec range of `confidence_threshold_default` is `[0, 1]`
  (`V-post.det.decode-8`, `post/detection-decode.md:77`). The default is tuned for the BlazePose
  visibility, a sigmoid value (`docs/mediapipe-whole-body.md:144-145`). Another parent, for example
  a COCO-WholeBody model with a SimCC score, may need another threshold and another value. The
  vectors `source-threshold-*` test the default, three runtime values and a runtime value out of
  the range.
- **The named value (the visibility proposal, its part 2.8).** The two values have other scales.
  The visibility proposal measured RTMW x 384x288 on 300 COCO persons (scratch, not evidence): the
  raw SimCC score had p50 7.56 and a maximum of 10.73, the visibility p50 0.974 (its part 1 before
  the rewrite for E). Thus a threshold in `[0, 1)` fits only `visibility`.
- **The gate value is a runtime input (user decision T33).** The first form had `score_gate.value`
  with no default and no runtime value. With T33, the sidecar gives `value_default`, and the host
  or the user can set `score` or `visibility` for a run. Thus one refiner sidecar serves a BlazePose
  parent (`visibility`, the default) and an RTMW parent (`score`). A run with an RTMW parent sets
  the value `score` and a threshold for that RTMW size: the RTMW score scale differs by size (a
  median of about 0.7 at 256x192, 4.1 for l-384 and 7.2 for x-384 on COCO val2017 body points;
  secondary: the untracked pose-models plan of OpenMMLab-Exporter (plan facts), row "V-check"; the measured thresholds for each size are in OpenMMLab-Exporter 0041 at `32ab848`, and part 1 gives both, `t_recall` and `t_J`, user decision T37). Under option E (OpenMMLab-Exporter 0041), every RTMW size
  gives only `score` (no RTMW size declares `pose.decode.visibility`), so the default value and the runtime value `visibility`
  with such a parent fail the parent check (vectors `parent-error-wholebody-score-only` and `parent-error-wholebody-256-gate-value-visibility`).
- **The name `value_default` (proposal choice).** The spec names a sidecar value that a host or a
  user can override at run time with the suffix `_default`: `decode.confidence_threshold_default`
  (`post/detection-decode.md:42`) and `score_gate.score_threshold_default` of this block. The key
  `value` without the suffix would read as a fixed value, as it was in the first form. The runtime
  input is "the gate value". The threshold keeps its name `score_threshold_default` (user decision
  T26 (6)); "score" there names the gate, not the per-point value `score`.
- **The default threshold goes with the default value (user decision T35, Q13 (a)).** A runtime gate value
  other than `value_default`, with no runtime threshold, is an error (rule `-16`). The reason: the
  default threshold is tuned for `value_default`, and the two values have other scales. For
  example, the hand default 0.1 with the runtime value `score` passes more than 95 % of the RTMW
  points: the p5 of the raw score is 0.109 to 0.116 at 256x192 and 0.823 to 1.09 at 384x288 (all
  133 points; same secondary source). Vector `source-error-gate-value-override-no-threshold`.
- **The name lists (user decision T27).** The host resolves the lists once, when it checks the
  parent, because they depend only on `pose.tracked_points`. A list keeps its order: when the parent
  has two or three names of one list, the earliest name in the list wins (vectors
  `source-alias-both-present-takes-first` and `source-alias-second-before-third`).
  A name in two lists of one instance is an error of the sidecar (rule `-11`), so two local names
  never read one parent point.
- **The order of gate and points.** MediaPipe drops the three pose points before it makes the ROI
  when the gate fails (`holistic_hand_tracking.cc:201-213`). Step 1 comes before step 2 for the same
  reason: a pose point that is not finite does not matter when the gate fails.
- **What stays outside the sidecar** (user decision T24): the tracking ROI from the previous hand
  landmarks (`docs/mediapipe-whole-body.md:395-399`) and the choice between that ROI and the refined
  ROI (`RoiTrackingCalculator`, `:400-403`). They are host tracking policy, because they use an
  earlier frame. Holistic also smooths the pose landmarks before the hand branch (`:382-383`). The
  smoothing is host policy too. Part 8 ("Not proposed") gives the evidence.

The host makes the rect after it maps the points to the source image (step 2 before step 3). This is
the MediaPipe order. The graph maps the two points with the crop matrix before it makes the rect
(`docs/mediapipe-whole-body.md:112, 391-393`). The crop matrix belongs to the crop that the model
read, so step 2 uses `Rc`. With the excerpt of part 2.2, `R` is the raw loose rect. `Rc` is 2.7
times larger, and it is shifted. Use the case `decode-hand-from-loose-crop-roi` of part 4 with `R`
in place of `Rc`. Then the centre of the refined ROI moves by 9.31 px (18.1 % of its size). The size
is 19.01 px in place of 51.32 px. (Scratch run with the reference file, 2026-10-23.)

Which upstream rule each value describes:

| Value | Upstream rule (primary: `docs/mediapipe-whole-body.md`) |
|---|---|
| `alignment_points` | `AlignmentPointsRectsCalculator`: centre at the start point, size `2 · |end − start|` (`:75-77`) |
| `rotation` | the rotation formula and `NormalizeRadians` (`:68-74`). The clamp of `normalize` is not upstream (user decision T23, R2 = Q7 = a). |
| `transform` | `RectTransformationCalculator`: shift, then `square_long`, then scale (`:81-87`); the heading "ROI transform" of the 0020 proposal describes the same rule (0020 proposal `:389`) |
| step 2 | the hand ROI refinement graph maps its points with the crop matrix (`:112, 391-392`); the heading "Inverse" of the 0020 proposal is the exact inverse of that crop (0020 proposal `:393`) |
| hand values | `rect: alignment_points`, points 0 and 1, target −90°, `shift_y` −0.1, `square_long`, scale 1.0 (`:391-394`) |

Notes, not normative:

- `NormalizeRadians` maps `+pi` to `-pi`. Thus the range is `[-pi, pi)` (vectors
  `wrap-pi-tie-goes-to-minus-pi`, `alignment-target-plus-90-wraps`).
- The clamp in `normalize`: **user decision (2026-10-24, T23, R2 = this file's Q7 = a).** In float64, the formula alone can give a value
  one ulp below `-pi`. An example is the input `3.1415926535897927`, one ulp below `pi`. Ordinary
  points can give such an input (vector `alignment-near-tie-stays-in-range`). The clamp keeps the
  result in `[-pi, pi)`. It changes only a result that is out of that range. The new angle is the
  same angle (modulo `2 * pi`). A scratch sweep of 224,400 inputs (random angles and inputs near
  each odd multiple of `pi`) gave 7 results out of range without the clamp and 0 with it. Only those
  7 results changed. The upstream formula has no clamp (`docs/mediapipe-whole-body.md:68-71`). The
  crop and the inverse of the next model use only the cosine and the sine of the rotation (0020
  proposal `:310-311`). Thus the clamp does not change a crop.
- Step 2, the finite check of `pts_src`: **proposal choice.** Finite points can give values that
  are not finite in the source image. An example is `1e308` with a crop ROI of size 1000 (vector
  `decode-overflow-none`). The check gives "no ROI", as step 5 does for an ROI that is not finite.
  Steps 3 and 4 then never compute with a value that is not finite.
- Step 5, "no ROI" for `w <= 0` or `h <= 0`: **user decision (2026-10-23, Q5 = a).** The primary
  document does not say what MediaPipe does with a rect of size 0. At the crop of the next model,
  MediaPipe `ValidateRoi` makes no tensor for such a rect (part 1, "Missing primary evidence"). "No
  ROI" is the host form of that result.
- Step 5, the test for finite values: it comes from the validity test of the 0020 proposal
  (`:313`). That test is stricter than `ValidateRoi`, which tests NaN only. It is a user decision
  of the 0020 proposal (T23, its Q9, `:1828-1830`).
- Step 1, the finite check of the points: **proposal choice.** A point that is not finite gives
  values in the source image that are not finite. The check of step 2 would then give "no ROI". The
  check in step 1 gives the same result earlier.
- MediaPipe `RectTransformationCalculator` also has a `rotation` option. No refiner graph in the
  primary document uses it (`:81-90`). This proposal does not add it. The 0020 proposal does not add
  it to the ROI transform either (its changelog row, `:562`).

**Inverse.** The refiner output is already in source-image pixels. It has no inverse of its own. Step
2 uses the inverse of the input crop: the heading "Inverse" of `pre.resize.rotated_roi_crop`, with
`Rc` (0020 proposal `:369-379`).

### 2.4 Validation rules

New rules of `post.roi_refiner`:

- [ ] `V-post.roi_refiner-1` **(vNEXT)** If `role` includes `roi_refiner`, `role` must be exactly
  `[roi_refiner]`. The sidecar must declare `roi_decode` and `roi_source`. It must not declare
  `decode`, `pose` or `overlay`.
- [ ] `V-post.roi_refiner-2` **(vNEXT)** A sidecar must not declare `roi_decode` or `roi_source`
  unless `role` is `[roi_refiner]`.
- [ ] `V-post.roi_refiner-3` **(vNEXT)** A `roi_refiner` sidecar must declare exactly one output. Its
  `semantic` must be `roi_points`.
- [ ] `V-post.roi_refiner-4` **(vNEXT)** The keys of `roi_decode` must be a subset of
  `point_count`, `coordinate_scale`, `rect`, `rotation` and `transform`. `point_count`,
  `coordinate_scale`, `rect` and `rotation` must be present. `roi_decode.point_count` must be an
  integer `>= 2`. If the `roi_points` output has a `shape`, and each axis after the batch axis is a
  positive integer, the product of those axes must be a multiple of `point_count`. The quotient must
  be `>= 2`.
- [ ] `V-post.roi_refiner-5` **(vNEXT)** `roi_decode.coordinate_scale` must be `pixel` or
  `normalized_01`. `roi_decode.rect` must be `alignment_points`.
- [ ] `V-post.roi_refiner-6` **(vNEXT)** `roi_decode.rotation` must be present. It must have exactly
  the keys `start_point`, `end_point` and `target_angle_deg`. `start_point` and `end_point` must be
  different integers in `[0, point_count)`. `target_angle_deg` must be a finite number.
- [ ] `V-post.roi_refiner-7` **(vNEXT)** If `roi_decode.transform` is present, it must pass the
  checks of `V-pre.resize.rotated_roi_crop-4` for `crop_policy.transform`: its keys must be a subset
  of `shift_x`, `shift_y`, `square_long` and `scale`. `shift_x` and `shift_y` must be finite numbers.
  `square_long` must be a boolean. `scale` must be a finite number `> 0`.
- [ ] `V-post.roi_refiner-8` **(vNEXT)** A `roi_refiner` sidecar must declare
  `input.resize.method: rotated_roi_crop`. (The rules of `pre.resize.rotated_roi_crop` then apply to
  its `crop_policy` and `interpolation`.)
- [ ] `V-post.roi_refiner-9` **(vNEXT)** A `roi_refiner` sidecar must be at
  `detectors/roi_refiners/{family}/{part}/{model_id}.yaml`. `{part}` must be `hand`, `face`, `body`
  or `wholebody`. `model_id` must be `{family}-{part}-roi` or `{family}-{part}-roi-{variant}`, where
  `{variant}` matches `^[a-z0-9]+(-[a-z0-9]+)*$`. (User decision Q3 = a.)
- [ ] `V-post.roi_refiner-10` **(vNEXT)** The keys of `roi_source` must be a subset of `method`,
  `instances`, `derived_points`, `score_gate`, `rect` and `rotation`. `method`, `instances`, `rect`
  and `rotation` must be present. `method` must be `parent_keypoints`. `rect` must be
  `alignment_points`.
- [ ] `V-post.roi_refiner-11` **(vNEXT)** `roi_source.instances` must be a non-empty list. Each item
  must have exactly the keys `name` and `points`. The names must be unique non-empty strings.
  `points` must be a non-empty map from a non-empty string (the local name) to a non-empty list of
  non-empty strings (the accepted parent point names, in order; user decision T27). A single string
  is not a list. An index is not a name. Every item must have the same set of local names. In one
  item, the parent point names of all lists must be unique: a name must not be in one list twice or
  in two lists.
- [ ] `V-post.roi_refiner-12` **(vNEXT)** If `roi_source.derived_points` is present, it must be a map.
  Each name must be a non-empty string that is not a local name of `points`. Each value must be a
  non-empty map whose keys are local names of `points`. Each weight must be a finite number `> 0`.
- [ ] `V-post.roi_refiner-13` **(vNEXT)** `roi_source.rotation` must have exactly the keys
  `start_point`, `end_point` and `target_angle_deg`. `start_point` and `end_point` must be different
  local names of `points` or names of `derived_points`. `target_angle_deg` must be a finite number.
- [ ] `V-post.roi_refiner-14` **(vNEXT)** If `roi_source.score_gate` is present, it must have exactly
  the keys `point`, `value_default` and `score_threshold_default`. `point` must be a local name of
  `points` (not a derived point). `value_default` must be `score` or `visibility`. For
  `value_default: visibility`, `score_threshold_default` must be a finite number with `0 <= v < 1`.
  For `value_default: score`, it must be a finite number.
- [ ] `V-post.roi_refiner-15` **(vNEXT)** (A host check, when the host joins the refiner to a parent
  pose model.) For each list in `roi_source.instances[].points`, at least one name must be in
  `pose.tracked_points` of the parent sidecar. The host uses the first such name (user decision
  T27). If `roi_source.score_gate` is present, the decode of the parent, at the parent size that
  the run uses, must give the gate value in effect: the runtime gate value, else
  `score_gate.value_default` (heading "Per-point values" of `post.pose.visibility`; user decision
  T33; each size of a parent gives the same values). Else the host must refuse the parent with a
  message. It must not skip the gate (user decision T34: Q8 (c) rejected).
- [ ] `V-post.roi_refiner-16` **(vNEXT)** (A host check of the runtime gate inputs, user decisions
  T26 (6) and T33.) A runtime gate value or a runtime gate threshold needs `roi_source.score_gate`.
  A runtime gate value must be `score` or `visibility`. If the gate value in effect is not
  `score_gate.value_default`, a runtime gate threshold must be set. A runtime gate threshold must
  be in the range of the gate value in effect: a finite number with `0 <= t < 1` for `visibility`,
  and a finite number for `score`. Else the host must refuse the runtime value. The host must not
  clamp it.

The ranges of the gate threshold in rules `-14` and `-16` are a **proposal choice** (the range for
each value is item 4 of part 2.8 of the visibility proposal). With user decision T33, the range of
the default follows `value_default`, and the range of a runtime threshold follows the gate value in
effect. A visibility is in `[0, 1]` (the
visibility proposal, heading "Behaviour": a sigmoid). With a strict `>`, a
threshold of `1` never passes it, and a negative value always passes. `0` passes every positive
value. A `score` has no fixed range: a SimCC score is the peak of the raw outputs
(`post/pose-decode-simcc.md:38`), and the visibility proposal measured values up to 10.73 for RTMW
(its part 1 before the rewrite for E, scratch). Thus a `score` threshold is any finite number. A runtime threshold has the range of the value that it goes with, so a value that the
sidecar cannot declare for that gate value is not a valid runtime value either. Rules `-15` and `-16` are host rules, as
the path rule `-9` is: `-15` needs a second sidecar, and `-16` needs the runtime values.

The closed key set of `roi_decode` in rule `-4` is a **proposal choice**. The 0020 proposal closes
the key set of its `crop_policy` in the same way (its rule `-2`, `:435-438`). Without it, a typo
such as `rotaton` passes the rules. The package validator already rejects unknown keys
(`_StrictModel`, `extra="forbid"`, `skellytracker/core/sidecar/model.py:32-33`). In rules `-4` to
`-7`, a boolean is not an integer and not a number.

Changed rules:

- `V-common.identity-2` (`common/identity.md:37`), new text: "`role` must be a non-empty subset of
  `object_detector`/`pose_estimator`, or exactly `[roi_refiner]`. The value `roi_refiner` is marked
  **(vNEXT)**."
- `V-common.outputs-4` (`common/outputs.md:44`), new text: add `roi_points` to the list. Add: "The
  value `roi_points` is marked **(vNEXT)**. It requires `role: [roi_refiner]`."
- `V-pre.resize.rotated_roi_crop-1` (new in the 0020 proposal, `:432-434`), new text: "If
  `input.resize.method` is `rotated_roi_crop`, `role` must be `[pose_estimator]` or `[roi_refiner]`.
  With `[pose_estimator]`, `pose.estimator_type` must be `top_down_single_person` or
  `top_down_multi_person`. With `[roi_refiner]`, the sidecar has no `pose` block
  (`V-post.roi_refiner-1`)." The 0020 proposal asks for this change (`:507`). (Before T22 (1), the
  text also said "`pose.requires_object_detector` must be `false`". The 0020 proposal removed that
  field, user decision 2026-10-24.)

Existing rules that name a changed value, and the effect:

| Rule | Effect |
|---|---|
| `V-common.identity-1` (basename equals `model_id`) | unchanged. It applies to the refiner as written. |
| `V-common.identity-3` (`display_name`, `input`, `outputs`) | unchanged. A refiner has all three. |
| `V-common.input-3` (the resize methods) | unchanged here. The 0020 proposal adds `rotated_roi_crop` to it (its changed `V-common.input-3`, `:452-455`). |
| `V-common.input-4` (fields per method) | unchanged here. The 0020 proposal allows `crop_policy` with `rotated_roi_crop` (its changed `V-common.input-4`, `:456-472`). Its rules `V-pre.resize.rotated_roi_crop-2` and `-3` give the keys of that `crop_policy`, with `border_mode` (`BORDER_REPLICATE` for the refiner, `docs/mediapipe-whole-body.md:390`). |
| `V-pre.resize.rotated_roi_crop-2` to `-5` (0020 proposal `:435-448`) | unchanged. They apply to the `input` block of a refiner as written. |
| `V-common.outputs-5` (all sizes share the outputs) | unchanged. It applies to the refiner as written. |
| `V-common.sizes_and_artifacts-3` (the family invariant, `common/sizes-and-artifacts.md:111`) | unchanged by this proposal. `roi_decode` is a top-level key. A size entry must not set it. The table "Contract part \| Where it lives" (`:49-54`) gets a row for `roi_decode` (part 2.1). The A1 text of the visibility proposal (user decision T33) added `pose.decode.visibility` to the keys of a size entry. Its rewrite for option E (OpenMMLab-Exporter 0041) removed that change, so the rule is unchanged by both proposals. |
| `V-post.pose.schema-1`, `V-post.pose.schema-2` and `V-pre.resize.affine_person_crop-2` | unchanged here. They apply only to a `pose_estimator`. A refiner has no `pose` block. The 0020 proposal changes the three rules, because it removes `pose.requires_object_detector` (user decision T22 (1), 2026-10-24; 0020 proposal `:475-495`). The changed `V-pre.resize.affine_person_crop-2` allows `rotated_roi_crop` for a top-down consumer (the hand landmark model). |
| `V-post.det.decode-*` | unchanged. They do not apply to a refiner (`V-post.roi_refiner-1` forbids `pose` and `decode`). |
| `V-post.pose.schema-4`, `-6` and `V-post.pose.canonical_mapping-1` (the names of `tracked_points` and of `derived_points`) | unchanged. They apply to the parent. Rule `V-post.roi_refiner-15` reads the `tracked_points` of the parent. `roi_source.derived_points` is a field of the refiner, not of the parent, so `V-post.pose.schema-6` does not apply to it. |

### 2.5 Selectors

`role=roi_refiner`. Every `roi_refiner` sidecar uses all of `post.roi_refiner`. At `vNEXT`,
`roi_decode.rect` has one value. A value that a later proposal adds selects a branch inside the
section, not another section.

### 2.6 Legacy behaviour and version effect

- A sidecar with `schema_version < vNEXT` cannot declare `roi_refiner`, `roi_points`, `roi_source` or
  `roi_decode`. The legacy meaning of every other field does not change.
- The change goes into the `vNEXT` revision (user decision Q1 = a, 2026-10-23). It adds no new
  `schema_version` value, because `vNEXT` is not released yet (skellytracker 0014).
- The `vNEXT` scope of skellytracker 0008 does not include MediaPipe-Exporter today
  (`0008-vnext-scope.md:8-15`). The scope must add it (user decision Q1 = a). The scope entry of the
  0020 proposal makes that change, because it lands first (part 2.1; T35).
- This proposal lands after the 0020 proposal (user decision Q4 = a). A `roi_refiner` sidecar needs
  `rotated_roi_crop` (`V-post.roi_refiner-8`).
- A refiner sidecar declares `schema_version: vNEXT` until the release step. After the release step,
  it declares the release that ships `vNEXT` (`exporter-guide/sidecars/validation-and-publishing.md`, "Publishing").

New row of the "Legacy behaviour" table of `common.identity` (`common/identity.md:47-51`):

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|---|---|---|
| `role: [roi_refiner]`, `semantic: roi_points`, `roi_decode`, `roi_source` | Not available. | Available. |

`format/versioning.md:74`: add "`roi_refiner` role, `roi_points` semantic, `roi_decode`, `roi_source`" to the
first column of the existing row.

The heading "Legacy behaviour" of `post.roi_refiner` has one sentence: "Availability before `vNEXT`:
Schema versioning (`../format/versioning.md#legacy-behaviour`)." This is the form of `pre.resize.fit`
(`pre/resize-fit.md:57-59`). The section gets no link in the list "Version-aware compatibility"
(`format/versioning.md:51-63`). That list holds only sections with a legacy meaning. The 0020
proposal does the same for its new section (0020 proposal `:194`).

### 2.7 Changelog row

Summary of changes (`specs/model-sidecar/changelog.md`), row N (the next free number at merge time). The 0020 proposal adds its row
(`:552-556`) first, because it lands first:

```markdown
| N | Role | New role `roi_refiner` for a model that gives the ROI of the next model. Its input is a `rotated_roi_crop`. New output semantic `roi_points` and a `roi_decode` block (`point_count`, `coordinate_scale`, `rect`: `alignment_points`, `rotation`, `transform`). The host maps the points to the source image with the inverse of the input crop, makes one rotated ROI for each batch item, applies the ROI transform of `rotated_roi_crop` and drops an ROI that is not valid. A `roi_source` block declares how the host makes the input ROI from named keypoints of a parent pose model (`method: parent_keypoints`: an ordered list of accepted parent names for each point, weighted derived points, the same rect rule, a strict gate on a named per-point value (`score` or `visibility`) with a runtime gate value and a runtime threshold, and the sidecar defaults `value_default` and `score_threshold_default`); the host uses the first accepted name that the parent has, and refuses a parent with none of the names of a point. New storage branch `detectors/roi_refiners/{family}/{part}/`. | MediaPipe hand ROI refinement (Holistic) | [ROI refiner](post/roi-refiner.md) |
```

`schema_version` history, text to add to the `vNEXT` row: "Added the `roi_refiner` role. Added the
`roi_points` output semantic. Added `roi_decode`: an ROI from two alignment points and a rotation
vector, then the ROI transform of `rotated_roi_crop`, then its ROI validity test. Added the
`detectors/roi_refiners/` branch. Added `roi_source`: the ROI of the input from named keypoints of a parent pose model (ordered lists of accepted parent names, weighted derived points, the rect rule of `roi_decode`, a strict gate on a named per-point value with a runtime gate value, a runtime threshold and their sidecar defaults), with a host check of the parent at the parent size in use and of the runtime gate inputs."

The note "For reviewers" needs no text from this proposal. The 0020 proposal names
MediaPipe-Exporter and the hand ROI refinement model (part 2.1).

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the exporter repo | the part 3 code of `specs/model-sidecar/proposals/roi-refiner-role/proposal.md` (exists) |
| Target file in skellytracker | `specs/model-sidecar/reference/post_roi_refiner.py` |
| Functions (one for each algorithm) | Owned by this section: `validate_roi_decode` (rules `-4` to `-7`); `read_roi_points` (step 1); `normalize_radians` (the wrap and the clamp of step 3); `rect_from_points` (step 3, `alignment_points`); `decode_roi` (steps 1 to 5 for one batch item); `validate_roi_source` (rules `-10` to `-14`); `resolve_parent_points` (the first accepted name of each list, heading "ROI source", "The parent"; user decision T27); `check_parent` (rule `-15`, the host check of the parent); `weighted_point` (step 3 of "ROI source", one derived point); `roi_from_keypoints` (heading "ROI source", the gate value and the gate threshold with rule `-16`, and steps 1 to 5, for one parent pose; it calls `rect_from_points` for its rect, so the section has one rect rule). Used from the reference file of `pre.resize.rotated_roi_crop` (0020 proposal part 3, `:581`), with no copy: `unproject_points` (step 2, heading "Inverse"); `transform_roi` (step 4, heading "ROI transform"); `roi_is_valid` (step 5, heading "ROI"); `validate_crop_policy` (the transform checks of rule `-7`). |

- The note at the top of the file says `source commit: none (no host code)`. MediaPipe-Exporter has no
  git repo and no exporter code.
- The file uses NumPy and the Python standard library. Through the reference file of
  `pre.resize.rotated_roi_crop`, it also uses OpenCV. It does not import from an exporter or from
  the skellytracker package.
- The PROVISIONAL functions `crop_points_to_source` and `transform_roi` of the first draft are
  deleted. The file has no copy of an algorithm of `pre.resize.rotated_roi_crop`. Before the
  deletion, the 0020 proposal showed that the two copies gave the same results as its reference
  file (0020 proposal `:647-652`, a past result).
- Stale text in the 0020 files: fixed on 2026-10-23. The 0020 proposal `:40` (row "Needed by"),
  `:591-592`, `:642-647` (now a past result) and `:1671-1672` (the list of part 7, now marked as
  applied; line numbers of 2026-10-24), and its reference file the part 3 code of `specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`,
  no longer name the deleted functions or the 10 deleted `provisional` vectors as current. A run
  after the fix gave 78 of 78 (0020 proposal part 4) and 47 of 47 (part 4 of this file).
- **User decision (2026-10-24, T23, R1 = Q6 = a):** the file loads the reference file of `pre.resize.rotated_roi_crop` with
  one helper, `_load_rotated_roi_crop`. It is a loader, not an algorithm, and the vectors do not call
  it. The loader looks next to the file and loads by the path. It tries the exporter name
  `sidecar-reference-pre_resize_rotated_roi_crop.py` (the name has hyphens) first. Then it tries the
  target name `pre_resize_rotated_roi_crop.py`. Thus the folder `specs/model-sidecar/reference/` need not
  be on `sys.path`. Only if neither file exists, it imports the module by its name. A scratch test
  copied both files to a folder `specs/model-sidecar/reference/` under their target names. A load of
  `post_roi_refiner.py` by its path passed, with the folder not on `sys.path`. The vector runner
  then gave 47 of 47.
- The file binds `unproject_points`, `transform_roi` and `roi_is_valid` as names of its module. Thus
  a vector runner that calls a function by its name finds them.
- `validate_roi_decode` checks the rules `-4` to `-7` completely, except the shape part of rule `-4`.
  That part needs the `outputs` block. `read_roi_points` checks the element count at run time.
  `decode_roi` calls `validate_roi_decode` first. Thus a typo such as `shfit_y`, the string
  `'false'` for `square_long`, or a start point of `-1` is an error. It is not ignored. This agrees
  with `validate_crop_policy` of the 0020 reference file (0020 proposal `:589-593`).
- Rule `-7` reuses the transform checks of `validate_crop_policy` of the 0020 reference file, with
  no copy. `validate_roi_decode` gives that function a policy with only the transform, and it
  replaces `crop_policy.transform` with `roi_decode.transform` in the error message. A separate
  transform validator in the 0020 reference file would be simpler. That is a possible change of the
  0020 files, not of this file.
- Rules `-1` to `-3`, `-8` and `-9` need the full sidecar (`role`, `outputs`, `input`, the path). The
  validator checks them, not this file.
- `roi_from_keypoints` takes the parent keypoints as a map from a parent point name to `(x, y)` in
  source-image pixels, and the per-point values as a map from a value name (`score`, `visibility`)
  to a map from a parent point name to the value (the form of `point_values` of
  the part 3 code of `specs/model-sidecar/proposals/keypoint-visibility/proposal.md` of OpenMMLab-Exporter, with point names; `None`
  or an empty map when the parent decode gives no value). `check_parent` takes the set of the value
  names that the parent decode gives at the parent size in use, in place of the earlier `has_point_scores`
  (for an RTMW parent: `[score]` at every size under option E, OpenMMLab-Exporter 0041 at `32ab848`; for a BlazePose parent: `[visibility]`; the docstring of `check_parent` in the reference file gives these examples).
  Its argument `gate_value` is the runtime gate value (`None` means `score_gate.value_default`).
  `roi_from_keypoints` has the same argument `gate_value`. The private helper
  `_gate_value_in_effect` gives the gate value in effect and checks the runtime value (rule `-16`).
  It calls `validate_roi_source` first. It resolves the name lists with
  `resolve_parent_points` against the names of the keypoint map (the map has every parent point,
  so its names are the `tracked_points`). A parent pose with none of the names of a list is an
  error of the host: rule `-15` refuses such a parent before the run. Its argument
  `score_threshold` is the runtime gate threshold (user decision T26 (6)). `None` means the default
  `score_gate.score_threshold_default`. A runtime threshold out of the range of the gate value in
  effect, a runtime gate value that is not `score` or `visibility`, a runtime value without
  `score_gate`, or a runtime gate value other than `value_default` without a runtime threshold is an
  error (rule `-16`). The vectors call `resolve_parent_points` only through
  `check_parent` and `roi_from_keypoints`. An undetected
  point (NaN coordinates, the convention of the skellytracker `Keypoints`,
  `skellytracker/core/data_primitives/keypoints.py:13-14`) gives "no ROI" for its instance.
- The file computes in float64. The section states no precision (user decision Q7 = c of the 0020
  proposal), so float64 is a choice of the file.
- `decode_roi` takes the crop ROI `Rc` (the result of `crop_roi` of the 0020 reference file), not the
  ROI that the host gave. A crop ROI that is not valid is an error of the host, because the item then
  has no crop and no model output.
- The first draft said "The 0020 proposal must define the letterbox case." That is done.
  `maintain_aspect_ratio` enlarges the ROI to `Rc` (0020 proposal step 3, `:347-351`). The inverse
  uses `Rc` (`:379`). This file needs no letterbox code.

```python
"""Reference implementation of the proposed section ``post.roi_refiner`` (ROI refiner decode).

Note:
- Section ID: ``post.roi_refiner`` (proposed). Proposal: ``specs/model-sidecar/proposals/roi-refiner-role/proposal.md``.
- Target file in skellytracker: ``specs/model-sidecar/reference/post_roi_refiner.py``.
- source commit: none (no host code). MediaPipe-Exporter has no git repo and no exporter code. The
  functions come from the text of part 2 of the proposal.
- Vector results: 125 of 125 vectors of part 4 of the proposal pass against this file (run on
  2026-10-25). The count for each function: ``read_roi_points`` 6, ``normalize_radians`` 6,
  ``rect_from_points`` 9, ``validate_roi_decode`` 17, ``decode_roi`` 9, ``validate_roi_source`` 31,
  ``check_parent`` 11, ``weighted_point`` 3 and ``roi_from_keypoints`` 33. The command, from the
  OpenMMLab-Exporter root: ``uv run python <scratchpad>/roi-note/run_vectors.py
  specs/model-sidecar/proposals/roi-refiner-role/proposal.md
  <the part 3 code of specs/model-sidecar/proposals/roi-refiner-role/proposal.md>``. The runner is a scratch file
  in the session scratchpad. It is not committed. It reads the YAML block of part 4 from the
  proposal (Python 3.14.2, NumPy 2.5.4, OpenCV 5.0.0, PyYAML 6.0.3). An earlier run on 2026-10-24
  also gave 125 of 125 (part 4 of the proposal). The vectors are
  ``unverified: no host implementation``. The probe geometry
  ``notes/decisions/scripts/hand_roi_reference.py`` (no commit) gives the same results for the hand
  cases. It is not an independent implementation.
- Parity result: to run (MediaPipe-Exporter has no git repo).
- Dependency: the section ``pre.resize.rotated_roi_crop`` (the full proposal of skellytracker 0020,
  ``specs/model-sidecar/proposals/roi-transform-and-source/proposal.md``) owns the ROI, its validity test, the ROI
  transform and the inverse of the crop. This file has no copy of them. It uses ``roi_is_valid``,
  ``transform_roi`` and ``unproject_points`` of the reference file of that section
  (the part 3 code of ``specs/model-sidecar/proposals/roi-transform-and-source/proposal.md``; in skellytracker
  ``specs/model-sidecar/reference/pre_resize_rotated_roi_crop.py``). ``_load_rotated_roi_crop`` loads it.
  It is a loader, not a copy of an algorithm (proposal choice, Q6 of the proposal).
- ``validate_roi_decode`` checks the transform with ``validate_crop_policy`` of that file (rule
  ``V-pre.resize.rotated_roi_crop-4``). It has no copy of those checks.
- This file owns only the algorithms of ``post.roi_refiner``: ``validate_roi_decode``,
  ``read_roi_points``, ``normalize_radians``, ``rect_from_points`` and ``decode_roi`` (the output
  decode), and ``validate_roi_source``, ``resolve_parent_points``, ``check_parent``,
  ``weighted_point`` and ``roi_from_keypoints`` (the ROI source: the loose ROI from named parent
  keypoints, user decision T24, 2026-10-24). ``roi_from_keypoints`` uses ``rect_from_points`` for its
  rect. It has no second rect rule.
- Each local point of ``roi_source`` has an ordered list of accepted parent names. The host uses the
  first name that the parent has (user decision T27, 2026-10-24). The gate threshold is a runtime
  input with the sidecar default ``score_gate.score_threshold_default`` (user decision T26 (6),
  2026-10-24). The comparison stays strict. The gate reads a named per-point value (``score`` or
  ``visibility``) of the parent: the OpenMMLab-Exporter proposal ``keypoint-visibility`` (section
  ``post.pose.visibility``, its part 2.8). The gate value is a runtime input too, with the sidecar
  default ``score_gate.value_default`` (user decision T33, 2026-10-24). The threshold range follows
  the value in effect. The parent check uses the value in effect and the parent size in use.
- Precision (user decision Q7 = (c) of the 0020 proposal, 2026-10-24): the section states no
  arithmetic precision. The vectors give the tolerances in ``compare``. This file computes in
  float64. That is a choice of this file, not a rule of the section.

Conventions: all geometry is in float64 pixels of the source image, with a top-left origin, ``x`` to
the right and ``y`` down. An ROI is ``(cx, cy, w, h, rotation)`` as the heading "ROI" of
``pre.resize.rotated_roi_crop`` defines it. ``rect_from_points`` gives a rotation in ``[-pi, pi)``.
``target_hw`` is ``[T_h, T_w]``, the ``target_size`` of the model input. A boolean is not an integer
and not a number.

Only NumPy, OpenCV (through the reference file of ``pre.resize.rotated_roi_crop``) and the Python
standard library are used.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, Sequence

import numpy as np

ROI = tuple[float, float, float, float, float]

_SKELLYTRACKER_MODULE = "pre_resize_rotated_roi_crop"
# The exporter name (with hyphens) first, then the target name in specs/model-sidecar/reference/.
_SIBLING_FILES = ("sidecar-reference-pre_resize_rotated_roi_crop.py", "pre_resize_rotated_roi_crop.py")

ROI_DECODE_KEYS = ("point_count", "coordinate_scale", "rect", "rotation", "transform")
ROI_DECODE_REQUIRED = ("point_count", "coordinate_scale", "rect", "rotation")
ROTATION_KEYS = ("start_point", "end_point", "target_angle_deg")
COORDINATE_SCALES = ("pixel", "normalized_01")
RECTS = ("alignment_points",)


def _load_rotated_roi_crop() -> ModuleType:
    """Load the reference file of ``pre.resize.rotated_roi_crop``. It is a loader, not an algorithm.

    The file is next to this file. Load it by its path: the exporter name has hyphens, and the folder
    ``specs/model-sidecar/reference/`` need not be on ``sys.path``. If no sibling file exists, import it by
    its module name.
    """
    for name in _SIBLING_FILES:
        path = Path(__file__).with_name(name)
        if path.is_file():
            spec = importlib.util.spec_from_file_location(_SKELLYTRACKER_MODULE, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    return importlib.import_module(_SKELLYTRACKER_MODULE)


_rotated_roi_crop = _load_rotated_roi_crop()

# Owned by ``pre.resize.rotated_roi_crop``: heading "ROI" (validity), "ROI transform" and "Inverse".
roi_is_valid = _rotated_roi_crop.roi_is_valid
transform_roi = _rotated_roi_crop.transform_roi
unproject_points = _rotated_roi_crop.unproject_points


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_roi_decode(roi_decode: Any) -> bool:
    """``post.roi_refiner``, rules ``V-post.roi_refiner-4`` to ``-7`` for the ``roi_decode`` block.

    Raises ``ValueError`` at the first rule that fails. Returns ``True`` when all rules pass. The
    shape part of rule ``-4`` needs the ``outputs`` block; ``read_roi_points`` checks it at run time.
    Rule ``-7`` uses the transform checks of ``validate_crop_policy`` of ``pre.resize.rotated_roi_crop``
    (rule ``V-pre.resize.rotated_roi_crop-4``), with no copy of them.
    """
    if not isinstance(roi_decode, Mapping):
        raise ValueError("roi_decode must be a mapping")
    unknown = sorted(set(roi_decode) - set(ROI_DECODE_KEYS))
    if unknown:
        raise ValueError(f"unknown roi_decode key(s): {unknown}")
    for key in ROI_DECODE_REQUIRED:
        if key not in roi_decode:
            raise ValueError(f"roi_decode.{key} is required")
    count = roi_decode["point_count"]
    if not (_is_int(count) and count >= 2):
        raise ValueError("roi_decode.point_count must be an integer >= 2")
    if roi_decode["coordinate_scale"] not in COORDINATE_SCALES:
        raise ValueError("roi_decode.coordinate_scale must be pixel or normalized_01")
    if roi_decode["rect"] not in RECTS:
        raise ValueError("roi_decode.rect must be alignment_points")
    rotation = roi_decode["rotation"]
    if not isinstance(rotation, Mapping):
        raise ValueError("roi_decode.rotation must be a mapping")
    if set(rotation) != set(ROTATION_KEYS):
        raise ValueError("roi_decode.rotation must have exactly the keys start_point, end_point and target_angle_deg")
    for key in ("start_point", "end_point"):
        if not (_is_int(rotation[key]) and 0 <= rotation[key] < count):
            raise ValueError(f"roi_decode.rotation.{key} must be an integer in [0, point_count)")
    if rotation["start_point"] == rotation["end_point"]:
        raise ValueError("roi_decode.rotation.start_point and end_point must be different")
    if not _is_finite_number(rotation["target_angle_deg"]):
        raise ValueError("roi_decode.rotation.target_angle_deg must be a finite number")
    if "transform" in roi_decode:
        policy = {"transform": roi_decode["transform"], "maintain_aspect_ratio": False, "border_mode": "replicate"}
        try:
            _rotated_roi_crop.validate_crop_policy(policy)
        except ValueError as exc:
            raise ValueError(str(exc).replace("crop_policy.transform", "roi_decode.transform")) from None
    return True


def read_roi_points(
    values: Sequence[float],
    point_count: int,
    coordinate_scale: str,
    target_hw: Sequence[int],
) -> np.ndarray:
    """``post.roi_refiner``, step 1: read the points of one batch item.

    ``values`` are the elements of one batch item of the ``roi_points`` output, in row-major order.
    The function reshapes them to ``[P, D]`` with ``P = point_count`` and ``D = len(values) / P``.
    Columns 0 and 1 are ``x`` and ``y``. Other columns are not used. Returns ``[P, 2]`` points in
    model-input pixels.
    """
    flat = np.asarray(values, dtype=np.float64).reshape(-1)
    if point_count < 2:
        raise ValueError("point_count must be at least 2")
    if flat.size % point_count != 0:
        raise ValueError("the element count is not a multiple of point_count")
    dims = flat.size // point_count
    if dims < 2:
        raise ValueError("each point must have at least 2 values")
    pts = flat.reshape(point_count, dims)[:, :2].copy()
    t_h, t_w = float(target_hw[0]), float(target_hw[1])
    if coordinate_scale == "pixel":
        return pts
    if coordinate_scale == "normalized_01":
        pts[:, 0] *= t_w
        pts[:, 1] *= t_h
        return pts
    raise ValueError(f"unknown coordinate_scale {coordinate_scale!r}")


def normalize_radians(angle: float) -> float:
    """``post.roi_refiner``: wrap an angle to ``[-pi, pi)``.

    ``r = a - 2 pi floor((a + pi) / (2 pi))``. Then the clamp: if ``r < -pi``, ``r = r + 2 pi``; if
    ``r >= pi``, ``r = r - 2 pi``. In float64, the formula alone can give a value one ulp below ``-pi``
    for an input near ``+pi``. The clamp keeps the result in ``[-pi, pi)``. A value that is not finite
    gives NaN.
    """
    a = float(angle)
    if not math.isfinite(a):
        return math.nan
    r = a - 2.0 * math.pi * math.floor((a + math.pi) / (2.0 * math.pi))
    if r < -math.pi:
        r += 2.0 * math.pi
    elif r >= math.pi:
        r -= 2.0 * math.pi
    return float(r)


def rect_from_points(points_src: np.ndarray, rect: str, rotation: dict | None = None) -> ROI:
    """``post.roi_refiner``, step 3: make one ROI from the points in source-image pixels.

    ``rect`` has one value at ``vNEXT``: ``alignment_points``. ``rotation`` is
    ``{start_point, end_point, target_angle_deg}``. It is required.

    - rotation: ``normalize_radians(radians(target_angle_deg) - atan2(-(y1 - y0), x1 - x0))`` from
      the start point to the end point.
    - ``alignment_points``: the centre is the start point. ``w = h = 2 * |end - start|``.

    A later proposal can add another ``rect`` value (for example a face rule) as a new branch here.
    """
    if rect != "alignment_points":
        raise ValueError(f"unknown rect {rect!r}")
    if rotation is None:
        raise ValueError("alignment_points needs rotation")
    pts = np.asarray(points_src, dtype=np.float64)
    sx, sy = pts[int(rotation["start_point"])]
    ex, ey = pts[int(rotation["end_point"])]
    target = float(rotation["target_angle_deg"]) * math.pi / 180.0
    theta = normalize_radians(target - math.atan2(-(ey - sy), ex - sx))
    size = 2.0 * math.hypot(ex - sx, ey - sy)
    return (float(sx), float(sy), size, size, theta)


def decode_roi(
    values: Sequence[float],
    roi_decode: dict,
    roi_c: Sequence[float],
    target_hw: Sequence[int],
) -> ROI | None:
    """``post.roi_refiner``: the full decode of one batch item, steps 1 to 5.

    ``roi_decode`` holds the sidecar block: ``point_count``, ``coordinate_scale``, ``rect``,
    ``rotation`` and ``transform`` (optional). ``validate_roi_decode`` checks it first. ``roi_c`` is
    the crop ROI ``Rc`` of the input crop of this batch item: the result of steps 1 to 3 of
    ``pre.resize.rotated_roi_crop`` (``crop_roi``), after ``crop_policy.transform`` and
    ``maintain_aspect_ratio``. It is not the ROI that the host gave. Returns the refined ROI in
    source-image pixels, or ``None`` ("no ROI").
    """
    validate_roi_decode(roi_decode)
    if not roi_is_valid(roi_c):
        raise ValueError("roi_c must be a valid crop ROI")
    pts = read_roi_points(values, roi_decode["point_count"], roi_decode["coordinate_scale"], target_hw)
    if not np.all(np.isfinite(pts)):
        return None
    with np.errstate(over="ignore", invalid="ignore"):
        pts_src = unproject_points(pts, roi_c, target_hw)
    if not np.all(np.isfinite(pts_src)):
        return None
    roi = rect_from_points(pts_src, roi_decode["rect"], roi_decode["rotation"])
    t = roi_decode.get("transform", {})
    roi = transform_roi(
        roi,
        shift_x=float(t.get("shift_x", 0.0)),
        shift_y=float(t.get("shift_y", 0.0)),
        square_long=t.get("square_long", False),
        scale=float(t.get("scale", 1.0)),
    )
    return roi if roi_is_valid(roi) else None


ROI_SOURCE_KEYS = ("method", "instances", "derived_points", "score_gate", "rect", "rotation")
ROI_SOURCE_REQUIRED = ("method", "instances", "rect", "rotation")
ROI_SOURCE_METHODS = ("parent_keypoints",)
SCORE_GATE_KEYS = ("point", "value_default", "score_threshold_default")
# The named per-point values of a parent decode (heading "Per-point values" of post.pose.visibility,
# the OpenMMLab-Exporter proposal keypoint-visibility).
POINT_VALUES = ("score", "visibility")


def _is_name(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def _is_name_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0 and all(_is_name(n) for n in value)


def _is_score_threshold(value: Any, value_name: str) -> bool:
    """A gate threshold: the sidecar default or a runtime value.

    ``value_name`` is the gate value that the threshold goes with (``value_default`` for the
    default, the gate value in effect for a runtime threshold). For ``visibility`` it is a finite
    number in ``[0, 1)``. For ``score`` it is any finite number: a SimCC score has no fixed range.
    """
    if not _is_finite_number(value):
        return False
    return 0.0 <= value < 1.0 if value_name == "visibility" else True


def _threshold_range(value_name: str) -> str:
    return "a finite number in [0, 1)" if value_name == "visibility" else "a finite number"


def _gate_value_in_effect(gate: Mapping[str, Any] | None, gate_value: Any) -> str | None:
    """``post.roi_refiner``, rule ``V-post.roi_refiner-16``: the gate value in effect.

    ``gate_value`` is the runtime gate value of the host or the user, or ``None``. ``None`` means
    the sidecar default ``score_gate.value_default``. Returns ``None`` when the sidecar has no gate.
    """
    if gate_value is None:
        return None if gate is None else gate["value_default"]
    if gate is None:
        raise ValueError("roi_source has no score_gate, so a gate_value override does not apply")
    if gate_value not in POINT_VALUES:
        raise ValueError("the gate_value override must be score or visibility")
    return gate_value


def validate_roi_source(roi_source: Any) -> bool:
    """``post.roi_refiner``, rules ``V-post.roi_refiner-10`` to ``-14`` for the ``roi_source`` block.

    Raises ``ValueError`` at the first rule that fails. Returns ``True`` when all rules pass. Rule
    ``-15`` needs the parent sidecar; ``check_parent`` checks it.
    """
    if not isinstance(roi_source, Mapping):
        raise ValueError("roi_source must be a mapping")
    unknown = sorted(set(roi_source) - set(ROI_SOURCE_KEYS))
    if unknown:
        raise ValueError(f"unknown roi_source key(s): {unknown}")
    for key in ROI_SOURCE_REQUIRED:
        if key not in roi_source:
            raise ValueError(f"roi_source.{key} is required")
    if roi_source["method"] not in ROI_SOURCE_METHODS:
        raise ValueError("roi_source.method must be parent_keypoints")
    if roi_source["rect"] not in RECTS:
        raise ValueError("roi_source.rect must be alignment_points")
    # rule -11: the instances
    instances = roi_source["instances"]
    if not isinstance(instances, list) or not instances:
        raise ValueError("roi_source.instances must be a non-empty list")
    names, local = [], None
    for item in instances:
        if not isinstance(item, Mapping) or set(item) != {"name", "points"}:
            raise ValueError("each roi_source.instances item must have exactly the keys name and points")
        names.append(item["name"])
        pts = item["points"]
        if not (isinstance(pts, Mapping) and pts and all(_is_name(k) and _is_name_list(v) for k, v in pts.items())):
            raise ValueError(
                "roi_source.instances[].points must map each local name to a non-empty list of parent point names"
            )
        # one name must not be in one list twice, or in two lists of one instance (user decision T27)
        flat = [n for names_of_point in pts.values() for n in names_of_point]
        if len(set(flat)) != len(flat):
            raise ValueError("the parent point names of one instance must be unique")
        if local is None:
            local = set(pts)
        elif set(pts) != local:
            raise ValueError("every roi_source.instances item must have the same local names")
    if not all(_is_name(n) for n in names) or len(set(names)) != len(names):
        raise ValueError("roi_source.instances names must be unique non-empty strings")
    # rule -12: the derived points
    derived = roi_source.get("derived_points", {})
    if not isinstance(derived, Mapping):
        raise ValueError("roi_source.derived_points must be a mapping")
    for dname, weights in derived.items():
        if not _is_name(dname):
            raise ValueError("roi_source.derived_points names must be non-empty strings")
        if dname in local:
            raise ValueError(f"roi_source.derived_points name {dname!r} is also a local point name")
        if not (isinstance(weights, Mapping) and weights):
            raise ValueError(f"roi_source.derived_points.{dname} must be a non-empty name->weight map")
        unknown = sorted(set(weights) - local)
        if unknown:
            raise ValueError(f"unknown point name(s) in roi_source.derived_points.{dname}: {unknown}")
        if not all(_is_finite_number(w) and w > 0 for w in weights.values()):
            raise ValueError("roi_source.derived_points weights must be finite numbers > 0")
    # rule -13: the rotation
    rotation = roi_source["rotation"]
    if not isinstance(rotation, Mapping) or set(rotation) != set(ROTATION_KEYS):
        raise ValueError("roi_source.rotation must have exactly the keys start_point, end_point and target_angle_deg")
    known = local | set(derived)
    for key in ("start_point", "end_point"):
        if rotation[key] not in known:
            raise ValueError(f"roi_source.rotation.{key} must name a local point or a derived point")
    if rotation["start_point"] == rotation["end_point"]:
        raise ValueError("roi_source.rotation.start_point and end_point must be different")
    if not _is_finite_number(rotation["target_angle_deg"]):
        raise ValueError("roi_source.rotation.target_angle_deg must be a finite number")
    # rule -14: the score gate
    if "score_gate" in roi_source:
        gate = roi_source["score_gate"]
        if not isinstance(gate, Mapping) or set(gate) != set(SCORE_GATE_KEYS):
            raise ValueError(
                "roi_source.score_gate must have exactly the keys point, value_default and score_threshold_default"
            )
        if gate["point"] not in local:
            raise ValueError("roi_source.score_gate.point must name a local point")
        if gate["value_default"] not in POINT_VALUES:
            raise ValueError("roi_source.score_gate.value_default must be score or visibility")
        if not _is_score_threshold(gate["score_threshold_default"], gate["value_default"]):
            raise ValueError(
                "roi_source.score_gate.score_threshold_default must be "
                f"{_threshold_range(gate['value_default'])} for value_default: {gate['value_default']}"
            )
    return True


def resolve_parent_points(roi_source: dict, parent_names: Any) -> list[dict[str, str]]:
    """``post.roi_refiner``, heading "ROI source", "The parent": the parent name of each local point.

    For each instance and each local name, the result is the first name of its list that is in
    ``parent_names`` (the ``pose.tracked_points`` of the parent). Raises ``ValueError`` when a local
    point has none of its names in the parent: the host must refuse the parent. The vectors test this
    function through ``check_parent`` and ``roi_from_keypoints``.
    """
    available = set(parent_names)
    resolved: list[dict[str, str]] = []
    missing: list[str] = []
    for item in roi_source["instances"]:
        names: dict[str, str] = {}
        for local, accepted in item["points"].items():
            hit = next((n for n in accepted if n in available), None)
            if hit is None:
                missing.append(f"{item['name']}.{local}")
            else:
                names[local] = hit
        resolved.append(names)
    if missing:
        raise ValueError(f"the parent has none of the names of point(s): {sorted(missing)}")
    return resolved


def check_parent(
    roi_source: dict, tracked_points: Sequence[str], point_values: Sequence[str], gate_value: str | None = None
) -> bool:
    """``post.roi_refiner``, rule ``V-post.roi_refiner-15``: the host check of a parent pose model.

    ``tracked_points`` is the ``pose.tracked_points`` list of the parent sidecar. ``point_values``
    is the set of the names of the per-point values that the parent decode gives at the parent size
    in use (``score``, ``visibility``; for example ``["visibility"]`` for a BlazePose parent with
    ``pose.decode.visibility``, and ``["score"]`` for an RTMW parent at every size, OpenMMLab-Exporter
    decision 0041). ``gate_value`` is the runtime gate value, or ``None`` for
    ``score_gate.value_default`` (rule ``-16``). Raises ``ValueError`` when the host must refuse the
    parent or the runtime gate value.
    """
    validate_roi_source(roi_source)
    resolve_parent_points(roi_source, tracked_points)
    value = _gate_value_in_effect(roi_source.get("score_gate"), gate_value)
    if value is not None and value not in set(point_values):
        raise ValueError(f"the parent decode gives no per-point value {value!r} for roi_source.score_gate")
    return True


def weighted_point(points: Mapping[str, Sequence[float]], weights: Mapping[str, float]) -> tuple[float, float]:
    """``post.roi_refiner``, heading "ROI source", step 3: one derived point.

    ``(w1 * q1 + w2 * q2 + ...) / (w1 + w2 + ...)`` for ``x`` and for ``y``. With the weights
    ``{index: 2, pinky: 1}`` this is ``(2 * index + pinky) / 3``.
    """
    total = sum(float(w) for w in weights.values())
    x = sum(float(w) * float(points[n][0]) for n, w in weights.items()) / total
    y = sum(float(w) * float(points[n][1]) for n, w in weights.items()) / total
    return (x, y)


def roi_from_keypoints(
    roi_source: dict,
    keypoints: Mapping[str, Sequence[float]],
    values: Mapping[str, Mapping[str, float]] | None = None,
    score_threshold: float | None = None,
    gate_value: str | None = None,
) -> list[ROI | None]:
    """``post.roi_refiner``, heading "ROI source": the ROI ``R`` of each instance from one parent pose.

    ``keypoints`` maps each parent point name to ``(x, y)`` in source-image pixels (an undetected
    point has NaN values; its name is still a key). ``values`` maps each name of a per-point value of
    the parent decode (``score``, ``visibility``) to a map from a parent point name to that value,
    for example the output of ``point_values`` of the reference file of ``post.pose.visibility``.
    ``None`` means that the parent decode gives no value. ``score_threshold`` is the
    runtime gate threshold of the host or the user. ``None`` means the sidecar default
    ``score_gate.score_threshold_default``. ``gate_value`` is the runtime gate value (``score`` or
    ``visibility``). ``None`` means the sidecar default ``score_gate.value_default``. A runtime gate
    value other than ``value_default`` needs a runtime threshold, because the default threshold goes
    with ``value_default`` (rule ``-16``). Each local point uses the first name of its list that is a
    key of ``keypoints`` (``resolve_parent_points``). Returns one ROI or ``None`` ("no ROI") for each
    instance, in the order of ``roi_source.instances``. ``validate_roi_source`` checks the block first.
    """
    validate_roi_source(roi_source)
    gate = roi_source.get("score_gate")
    value = _gate_value_in_effect(gate, gate_value)
    threshold = None
    if score_threshold is not None:
        if gate is None:
            raise ValueError("roi_source has no score_gate, so a score_threshold override does not apply")
        if not _is_score_threshold(score_threshold, value):
            raise ValueError(
                f"the score_threshold override must be {_threshold_range(value)} for the gate value {value}"
            )
        threshold = float(score_threshold)
    elif gate is not None:
        if value != gate["value_default"]:
            raise ValueError("a gate_value override other than value_default needs a score_threshold override")
        threshold = float(gate["score_threshold_default"])
    derived = roi_source.get("derived_points", {})
    rot = roi_source["rotation"]
    resolved = resolve_parent_points(roi_source, keypoints.keys())
    out: list[ROI | None] = []
    for names in resolved:
        # step 1: the gate (strict >; NaN fails)
        if gate is not None:
            if not values or value not in values:
                raise ValueError(f"the parent decode gives no per-point value {value!r} for roi_source.score_gate")
            s = float(values[value][names[gate["point"]]])
            if not s > threshold:
                out.append(None)
                continue
        # step 2: read the points
        q = {local: (float(keypoints[parent][0]), float(keypoints[parent][1])) for local, parent in names.items()}
        if not all(math.isfinite(v) for xy in q.values() for v in xy):
            out.append(None)
            continue
        # step 3: the derived points
        for dname, weights in derived.items():
            q[dname] = weighted_point(q, weights)
        # step 4: the rect (the rule of roi_decode step 3, with named points)
        pts = np.array([q[rot["start_point"]], q[rot["end_point"]]], dtype=np.float64)
        roi = rect_from_points(
            pts, roi_source["rect"], {"start_point": 0, "end_point": 1, "target_angle_deg": rot["target_angle_deg"]}
        )
        # step 5: the validity test of Rotated ROI crop
        out.append(roi if roi_is_valid(roi) else None)
    return out


if __name__ == "__main__":
    hand = {
        "point_count": 2,
        "coordinate_scale": "pixel",
        "rect": "alignment_points",
        "rotation": {"start_point": 0, "end_point": 1, "target_angle_deg": -90.0},
        "transform": {"shift_y": -0.1, "square_long": True, "scale": 1.0},
    }
    loose_policy = {
        "transform": {"shift_y": -0.1, "square_long": True, "scale": 2.7},
        "maintain_aspect_ratio": True,
        "border_mode": "replicate",
    }
    rc = _rotated_roi_crop.crop_roi((300.0, 200.0, 40.0, 40.0, 0.5), loose_policy, (256, 256))
    print("crop ROI", rc)
    print("refined ROI", decode_roi([128.0, 128.0, 128.0, 192.0], hand, rc, (256, 256)))
```

## 4. Vectors

The reference file made these vectors, except the expected ROIs of the three `source-upstream-*`
cases (below). A scratch runner of this session
(`mp-proposals\run_vectors.py` in the session scratchpad, not committed) read this YAML block back from this file. It ran each case
through the reference file, loaded with `importlib.util.spec_from_file_location`. Result on
2026-10-24, after T26 (6), T27, the named gate value of the visibility proposal, T28 (H1), T33 and
the option E edits (OpenMMLab-Exporter 0041, below): **125 of 125 pass**. Run again on 2026-10-25, after the edits that add the repo name before each bare decision number `0041` (comment text only, no case changed): 125 of 125 pass, with the same counts. The counts for each function are `read_roi_points` 6, `normalize_radians` 6,
`rect_from_points` 9, `validate_roi_decode` 17, `decode_roi` 9, `validate_roi_source` 31,
`check_parent` 11, `weighted_point` 3 and `roi_from_keypoints` 33. Before T33: 113 of 113
(`validate_roi_source` 30, `check_parent` 7, `roi_from_keypoints` 26). Before T28 (H1): 110 of 110
(`check_parent` 6, `roi_from_keypoints` 24). After T26 (6) and T27 only: 102 of
102. Before T26 (6) and T27: 90 of 90. Before the changes of 2026-10-24: 47 of 47
(the first five functions). The 43 cases of T24 are the cases of `roi_source` (user decision T24).

**The changes of T26 (6) and T27 (2026-10-24).** A scratch script
(`mp-gate\edit_vectors.py` in the session scratchpad, not committed) changed the cases of `roi_source` and wrote 12 new cases. It ran each new
case through the reference file before it wrote the expected value.

- Every `roi_source` block has the lists of part 2.2 in `points`, and `score_gate` has
  `score_threshold_default: 0.1` in place of `min_score: 0.1`. The ids `source-validate-*-min-score-*`
  became `source-validate-*-threshold-default-*`. The error texts name `score_threshold_default`.
- `parent-error-wholebody-names` became `parent-wholebody-names-accepted`: the same RTMW names, now
  accepted (T27).
- New cases of rule `-11`: `source-validate-error-points-empty-list`,
  `source-validate-error-points-plain-string` and `source-validate-error-duplicate-name-in-list`.
  The case `source-validate-error-duplicate-parent-name` now has one name in two lists, and
  `source-validate-error-index-not-name` has an index in a list (a list item that is not a string).
- New case of rule `-15`: `parent-error-no-accepted-name` (the coco133 names of the spec example).
- New cases of the name lists: `source-alias-second-name-wholebody`,
  `source-alias-both-present-takes-first` and `source-error-no-accepted-name`. The first name is used
  in every BlazePose case, for example `source-upstream-up-and-right`. The expected ROIs of the two
  alias cases equal the ROIs of `source-gate-reads-only-the-gate-point`, a case of T24 with the same
  positions under the BlazePose names.
- New cases of the gate threshold: `source-threshold-default` (no runtime value),
  `source-threshold-override-lower`, `source-threshold-override-strict` (a runtime value equal to the
  score gives no ROI), `source-error-threshold-override-range` (1.0) and
  `source-error-threshold-override-without-gate`.

**The named gate value (the visibility proposal, part 2.8; 2026-10-24).** A second scratch script
(`mp-gate\edit_vectors_vis.py` in the session scratchpad, not committed) changed the cases again and wrote 8 new cases. It ran each new case
through the reference file before it wrote the expected value.

- Every `score_gate` has `value: visibility`. The parent values are a map from a value name to a
  map of points (`values: {visibility: {...}}` in place of `scores: {...}`; `values: {}` in
  place of `scores: null`). `check_parent` takes `point_values` (for example `[visibility]`, or
  `[]` for a decode with no value) in place of `has_point_scores`. The RTMW case
  `parent-wholebody-names-accepted` first had a parent with both values (the interim A1). Option E
  gives it `[score]` (below). The error texts name the value and the range for `visibility`.
- New cases of rule `-14`: `source-validate-error-gate-no-value`,
  `source-validate-error-gate-unknown-value` and `source-validate-score-threshold-above-one`
  (`value: score` with 5.0: valid). The range error for `visibility` is
  `source-validate-error-threshold-default-one` and `-negative`.
- New case of rule `-15`: `parent-error-wholebody-score-only` (an RTMW parent with only `score`).
- New cases of `roi_from_keypoints`: `source-gate-value-score` and `source-gate-value-visibility`
  (one parent with both values in other orders: each gate reads only its value),
  `source-error-gate-value-missing` and `source-threshold-override-score-above-one` (a runtime value
  7.0 for `value: score`).

**The third names (user decision T28 (H1), 2026-10-24).** A scratch script
(`mp-h\edit_refiner_vectors.py` in the session scratchpad, not committed) changed the cases and wrote 3 new cases.
The runner ran the cases through the reference file. The reference file did not change.

- Every `roi_source` block has the lists of part 2.2: the pinky and index lists have the third name.
- `parent-error-no-accepted-name` (the example names, refused) became `parent-example-names-accepted`
  (the same names, accepted). A new `parent-error-no-accepted-name` uses names that are in no list
  (`left_index_mcp`, `left_pinky_mcp`, and the right side; made up for the test).
- `source-error-no-accepted-name` (the example names) became `source-alias-third-name-example`.
  Its expected ROIs equal the ROIs of `source-gate-reads-only-the-gate-point` (the same positions).
  A new `source-error-no-accepted-name` uses the names that are in no list.
- New case `source-alias-second-before-third`: the parent has the second and the third names at
  other positions, and the second name is used.
- `source-alias-both-present-takes-first` also has the third names, at other positions. Its
  expected ROIs do not change.

**The runtime gate value (user decision T33, 2026-10-24).** A scratch script
(`v1-gate\edit_ref_vectors.py` in the session scratchpad, not committed)
changed the cases and wrote 12 new cases. The runner ran every case through the changed reference
file.

- Every `score_gate` has `value_default` in place of `value`. The error texts name `value_default`
  for rule `-14`, and "the gate value" for a runtime threshold. `source-validate-error-gate-no-value`
  now has a gate without `value_default`.
- New case of rule `-14`: `source-validate-error-gate-old-key-value` (the key `value` of the first
  form).
- New cases of rules `-15` and `-16` (`check_parent` with the argument `gate_value`):
  `parent-wholebody-256-gate-value-score` (an RTMW 256x192 parent size gives `[score]`; the runtime
  value `score`: accepted), `parent-error-wholebody-256-gate-value-visibility` (the same size and the
  runtime value `visibility`: refused), `parent-error-gate-value-unknown` and
  `parent-error-gate-value-without-gate`. The existing `parent-error-wholebody-score-only` is the same
  parent with no runtime value (the default `visibility`: refused), and `parent-wholebody-names-accepted`
  first had both values and the default. Option E gives it `[score]` and the runtime value `score` (below).
- New cases of `roi_from_keypoints`: `source-gate-value-override-score` (the override is used: the
  runtime value `score` with the threshold 0.5 on 256x192-like scores),
  `source-error-gate-value-override-no-threshold`, `source-gate-value-override-equal-default` (the
  runtime value equal to the default needs no threshold; the default 0.1 is used),
  `source-threshold-range-follows-gate-value-score` (threshold 4.0 is valid for `score` when the
  default is `visibility`), `source-error-threshold-range-follows-gate-value-visibility` (threshold
  1.5 is refused for `visibility` when the default is `score`),
  `source-error-gate-value-override-unknown` and `source-error-gate-value-override-without-gate`.
  The default is used in `source-threshold-default` and `source-gate-value-visibility` (no runtime
  value).
- The expected ROIs of the new cases equal the ROIs of `source-gate-value-score` and
  `source-gate-value-visibility` (the same positions).
- **Mutation check (T33):** a copy of this file with one changed expected value (the left ROI of
  `source-gate-value-override-score`, `cy` `242.0` to `242.5`; scratch `v1-gate\mutate_ref.py`)
  gives 124 of 125, and only that case fails. This file is unchanged by the check.
- **Control (T33):** a copy of the reference file whose `roi_from_keypoints` ignores `gate_value`
  (it always uses `value_default`) gives 119 of 125. The 6 cases that fail are
  `source-gate-value-override-score`, `source-error-gate-value-override-no-threshold`,
  `source-threshold-range-follows-gate-value-score`,
  `source-error-threshold-range-follows-gate-value-visibility`,
  `source-error-gate-value-override-unknown` and `source-error-gate-value-override-without-gate`.

**Option E (OpenMMLab-Exporter decision 0041 at `32ab848`, 2026-10-24).** Under E, no RTMW size
declares `pose.decode.visibility`, so an RTMW parent gives only `score` at every size. A scratch
script (`fu-refiner\edit_vectors_e.py` in the session scratchpad, not committed) changed 15 cases.
It added no case and removed no case. The expected results do not change. The runner ran every case
through the reference file. The reference file did not change.

- RTMW parents with a visibility now give only `score`. `parent-wholebody-names-accepted` and
  `parent-example-names-accepted` (the coco133 list is in the RTMW output order) have
  `point_values: [score]` and the runtime gate value `score`. They stay accepted. The input of
  `parent-wholebody-names-accepted` now equals the input of `parent-wholebody-256-gate-value-score`.
  `parent-error-gate-value-unknown` has `[score]`.
- The alias cases `source-alias-second-name-wholebody`, `source-alias-third-name-example` and
  `source-alias-second-before-third` read `score` with the runtime gate value `score` and the
  example threshold 0.5. The hand root of the first case keeps the score 0.05, so the body wrist
  still wins.
- The cases that need one parent with both values (`source-gate-value-score`,
  `source-gate-value-visibility`, `source-gate-value-override-equal-default`) use a test parent
  with the BlazePose names, at the same positions. No current parent gives both values.
  `source-error-threshold-range-follows-gate-value-visibility` and
  `source-error-gate-value-override-unknown` keep the RTMW names with `score` only: their error
  comes before the gate reads a value.
- The comments of `parent-error-wholebody-score-only`,
  `parent-wholebody-256-gate-value-score`, `parent-error-wholebody-256-gate-value-visibility` and
  `source-gate-value-override-score` say that every RTMW size gives only `score`.
- **Mutation check (E):** a copy with one changed expected value (the left ROI of
  `source-alias-second-name-wholebody`, `cy` `242.0` to `242.5`) gives 124 of 125, and only that
  case fails.
- **Controls (E):** a copy of the reference file that ignores every runtime gate value gives 111 of
  125 (14 cases fail, among them the three alias cases and the two accepted RTMW parents). A copy
  whose `resolve_parent_points` takes the last accepted name gives 119 of 125 (6 cases fail:
  `source-alias-second-name-wholebody`, `source-alias-both-present-takes-first`,
  `source-alias-second-before-third`, `source-threshold-override-score-above-one`,
  `source-gate-value-override-score` and `source-threshold-range-follows-gate-value-score`).
- The earlier controls and mutation checks of this part ran on the vectors before E.

The generator
(`mp-proposals\gen_cases_yaml.py` in the session scratchpad, not committed) ran each new case through the reference file before it
wrote the case.

**The `source-upstream-*` cases are the proof that one rect rule is enough.** Their expected ROIs
come from a transcription of the upstream formula
(`hand_detections_from_pose_to_rects_calculator.cc:93-113, 124-152`: `middle`, centre `middle`, size
`2 · |middle − wrist|`, `NormalizeRadians(pi/2 − atan2(−(y_m − y_w), x_m − x_w))`; script
`mp-proposals\gen_roi_source.py` in the session scratchpad, not committed). The reference file gives them with `roi_source.rect:
alignment_points` and the rotation from `middle` to the wrist at −90°, within `1e-9` px and `1e-12`
rad. A control: the same three cases with the rotation from the wrist to `middle` at +90° (the
centre then is the wrist) fail, all three. Thus the cases tell the two forms apart.

**The tolerances (user decision Q7 = c of the 0020 proposal, 2026-10-24).** The section states no
arithmetic precision. On 2026-10-24 the output ROI of each case became two fields: `roi` (`cx`, `cy`,
`w`, `h`) with `atol: 1e-3` px, and `rotation` with `atol: 1e-6` rad. `normalize_radians` cases
compare `angle` with `atol: 1e-6`. `roi_from_keypoints` gives `rois` (`atol: 1e-3`) and `rotations`
(`atol: 1e-6`). `weighted_point` compares `point` with `atol: 1e-3`. The input ROI keeps its five
values. Before, the tolerance was `1e-9` (and `1e-12` for an angle). `read_roi_points` and the
validation cases keep their exact form. Two cases test the clamp of R2 with inputs one ulp from the
`+pi` tie in float64: `wrap-pi-minus-ulp-stays` and `alignment-near-tie-stays-in-range`. Their inputs
have no float32 form (in float32, `3.1415926535897927` is the float32 value of pi). A host in another
precision runs these two cases in float64, or it makes the same tie in its own precision. This is
the one place where a vector of this section depends on the precision.

**Mutation check (2026-10-24, the final vectors).** After T28 (H1): a copy of this file with one
changed expected value (the left ROI of `source-alias-third-name-example`, `cy` `242.0` to `242.5`)
gave 112 of 113, and only that case failed. This file is unchanged by the check. Before T28 (H1): one
changed expected value (the right ROI of `source-gate-value-visibility`, `cy` `100.0` to `100.5`) gave
109 of 110 (exit 1), and only that case failed. Earlier checks: after T26
(6) and T27, one changed value in `source-threshold-override-lower` gave 101 of 102; before, one
changed rotation of `source-upstream-diagonal` gave 89 of 90.

Negative controls of T26 (6), T27 and the named value (copies of the reference file, each with one
changed line, in the scratch folder `mp-gate` of the session, not committed):

- `resolve_parent_points` takes the last accepted name in place of the first: 105 of 110. The cases
  that failed are `source-alias-second-name-wholebody`, `source-alias-both-present-takes-first`,
  `source-gate-value-score`, `source-gate-value-visibility` and
  `source-threshold-override-score-above-one` (the last three use the hand root of the RTMW names).
- `roi_from_keypoints` ignores the runtime threshold and uses the default: 108 of 110. The cases that
  failed are `source-threshold-override-lower` and `source-threshold-override-strict`.
- `roi_from_keypoints` reads `score` when it exists, not the named value: 109 of 110. The case that
  failed is `source-gate-value-visibility`.
- Each control ran on the vectors of 110 cases. After T28 (H1), the first control (the last accepted
  name) ran again on the 113 cases: 107 of 113. The cases that failed are the five above and
  `source-alias-second-before-third`.

Negative controls:

- A copy of this file with 4 wrong expected values gave 43 of 47 (exit 1). Thus the runner detects a
  failure.
- A copy of the reference file without the clamp of `normalize_radians`, and without the call of
  `validate_roi_decode` in `decode_roi`, gave 44 of 47. The 3 cases that failed are
  `wrap-pi-minus-ulp-stays`, `alignment-near-tie-stays-in-range` and `decode-error-transform-typo`.
  Thus the new cases detect the two defects of the earlier file.

Environment: the `uv` environment of OpenMMLab-Exporter (Python 3.14.2, NumPy 2.5.4, OpenCV 5.0.0,
PyYAML 6.0.3), as the task gave.

**Cases that moved to `pre.resize.rotated_roi_crop`.** The first draft had 15 cases of functions that
the 0020 proposal owns: 3 `crop_points_to_source`, 7 `transform_roi` and 5 `roi_is_valid`. They are
deleted from this file. An earlier run of 2026-10-23 ran them through the functions that the
reference file takes from the 0020 reference file (`unproject_points` in place of
`crop_points_to_source`). The result was **15 of 15 pass**. This session did not run them again,
because they are no longer in this file. The 0020 vectors cover the same branches (0020 proposal
part 4, `:604-1632`):

| First-draft case | Case of the 0020 proposal |
|---|---|
| `inverse-centre-maps-to-roi-centre` | `unproject-centre` (a rotated, non-square ROI) |
| `inverse-corner-no-rotation` | `unproject-corner-convention` (the same two points and ROI, and one more point) |
| `inverse-rotation-plus-half-pi` | `unproject-rotation-half-pi` (the same case) |
| `transform-shift-y-no-rotation` | `transform-shift-uses-size-before-square` (the same case) |
| `transform-shift-y-rotated-half-pi` | `transform-shift-y-rotation-half-pi` (without `square_long`) and `transform-shift-uses-size-before-square` |
| `transform-shift-x-and-y` | `transform-shift-x-and-y-rotation-pi-6` (the same case) |
| `transform-no-square-scale-2` | `transform-scale-keeps-aspect` (the same case) |
| `transform-square-long-tie`, `transform-square-long-takes-h`, `transform-defaults-identity` | the same ids (the same cases) |
| `valid-positive`, `invalid-w-zero`, `invalid-h-zero`, `valid-tiny`, `invalid-negative` | `valid-positive`, `invalid-w-zero`, `invalid-h-zero`, `valid-tiny`, `invalid-w-negative` (other values, the same branches), and also NaN, infinity and four values |

**Cross-checks** (neither is an independent implementation):

- The probe geometry `notes/decisions/scripts/hand_roi_reference.py` (MediaPipe-Exporter 0006; no
  commit). Its `project_landmarks` with `n=256`, then its `rect_from_recrop_points`, gives the
  expected ROI of the 3 hand `decode_roi` cases. These cases have a square `Rc` and the hand
  transform: `decode-hand-upright`, `decode-hand-rotated-crop-roi` and
  `decode-hand-from-loose-crop-roi`. Result: **3 of 3 pass** within `1e-9`. (Rerun on 2026-10-23
  after the review fix. The largest difference is `3.6e-14`.) Its
  `_shift_square_scale` with scale 2.7 gives the same `Rc` as the `roi_c` of
  `decode-hand-from-loose-crop-roi` within `1e-9` (rerun: difference 0).
- The probe `roi_from_pose` (`hand_roi_reference.py:47-52`), against `roi_from_keypoints` and then
  `crop_roi` of the 0020 reference file with the `crop_policy` of part 2.2: the same crop ROI for the
  6 hands of the `source-upstream-*` cases (maximum difference 0; 2026-10-24).
- The scratch sweep of part 2.3 (200,000 hands): the reused rule against the upstream formula,
  at most `2.9e-14` px and `8.9e-16` rad modulo 2π
  (`mp-proposals\loose_rect_equivalence.py` in the session scratchpad, not committed).
- The probe is in the same exporter, and it has no commit. Thus the vectors stay `unverified`.

Coverage:

- `read_roi_points`: each branch (`pixel`, `normalized_01`, `D = 2`, `D = 3`) and three errors.
- `normalize_radians`: the range ties (`+pi` gives `-pi`, `-pi` stays, `3pi`) and the clamp (one
  ulp below `+pi` stays).
- `rect_from_points` (`alignment_points`): four directions, the `+pi` wrap tie, and a direction one
  ulp from that tie (the clamp). Also a zero-length vector, the missing-rotation error, and the
  deferred value `points_bounds` as an error.
- `validate_roi_decode`: the hand block, and one error case for each check of rules `-4` to `-7`.
  The rule `-7` cases use the transform checks of the 0020 reference file.
- `decode_roi`, end to end: the hand upright; the hand with a rotated `Rc`; the hand from the crop
  ROI of the raw loose rect (the input `crop_policy.transform` of part 2.2); `normalized_01` with no
  `roi_decode.transform` and a non-square `Rc` on a non-square input.
- `decode_roi`, no ROI and errors: a zero-size ROI (no ROI, user decision Q5 = a); a NaN point (no
  ROI, step 1); finite points that overflow in the source image (no ROI, step 2); a crop ROI that is
  not valid (an error); a typo in `roi_decode.transform` (an error).
- `validate_roi_source` (rules `-10` to `-14`): the hand block; an unknown key; no `rotation`; a
  method and a `rect` that are not in the set; no instance; an extra instance key; indices in place of
  names (in a list); an empty list; a string in place of a list; one name twice in one list;
  instances with other local names; two instances with one name; one name in two lists of one
  instance; a derived name that hides a local name; a weight with an unknown name; the weights 0,
  `true` and infinity; a rotation with an unknown name, with an index and with the same point twice;
  a gate on a derived point; for `value_default: visibility`, `score_threshold_default` 1 and −0.1
  (out of `[0, 1)`) and 0 (in range); for `value_default: score`, 5.0 (in range); a gate without
  `score_threshold_default`; a gate without `value_default`; an unknown `value_default`; the old key
  `value` (T33).
- `check_parent` (rule `-15`): the 33 MediaPipe_Pose names with `visibility` and the default gate
  (accepted, the first names); a part of the
  RTMW names (accepted, the second names of the pinky and index lists; refused before T27); the
  coco133 names of the spec example (accepted, the third names; refused before T28 (H1)); names in no
  list (refused); a parent with no
  per-point value and a gate (refused); an RTMW parent with only `score` and a gate on `visibility`
  (refused); no gate and no value (accepted). The runtime gate value (T33): an RTMW parent
  size with the runtime value `score` (accepted) and `visibility` (refused); an unknown runtime
  value; a runtime value without a gate. Under option E (OpenMMLab-Exporter 0041), every RTMW parent gives only `score`,
  so the accepted RTMW and coco133 parents set the runtime gate value `score`.
- `weighted_point`: the hand weights `{index: 2, pinky: 1}`, equal weights, fractional weights.
- `roi_from_keypoints`: the upstream formula in five directions (up, `+x`, down at the `+pi` tie,
  `−x`, a diagonal with fractional values) for both instances; the strict gate at the tie (no ROI);
  a NaN score (no ROI) and a score just above `score_threshold_default`; low scores of the points
  that the gate does not read; no gate and no scores; a gate with no scores (an error); a NaN point
  (no ROI); a zero size (`middle` on the wrist: no ROI); a missing parent point (an error); a block
  that is not valid (an error). The name lists (T27, T28 (H1)): a COCO-WholeBody parent (the second
  names; the wrist takes the first name; the gate value `score`, option E); a parent with the spec example names (the third names); a
  parent with every name of every list (the first name); a parent with the second and the third
  names (the second name); a parent with none of the names (an error). The gate threshold (T26 (6)): the default; a lower runtime
  value; a runtime value at the tie (strict); a runtime value out of range (an error); a runtime
  value without a gate (an error); a runtime value above 1 for `value_default: score`. The named value (the
  visibility proposal): a gate on `score` and a gate on `visibility` with one test parent that gives
  both (BlazePose names; no current parent gives both); a parent without the named value (an error). The runtime gate value (T33): the default used
  (no runtime value); the override `score` used, with a threshold for that size; an override equal
  to the default with no threshold; an override other than the default with no threshold (an
  error); the threshold range by the value in effect (4.0 valid for `score`, 1.5 refused for
  `visibility`); an unknown override and an override without a gate (errors). Each "no ROI" case of
  T24 gives an ROI for the other instance.

The ROI transform and the validity test have their branch cases in the 0020 vectors. The user
decision Q2 = c removed the four `points_bounds` cases of the first draft. The cases have no images
and no ONNX files. Each fractional value has its tolerance in `compare` (above). The rotation is
compared without a period. The clamp makes the range `[-pi, pi)` exact, so a rotation of `-pi` and a
rotation near `+pi` are different results (user decision T23, R2). Vector params use
`target_size` (`[T_h, T_w]`), as the 0020 vectors do. An error case gives the full error message. The
0020 error cases do the same.

The target file is `specs/model-sidecar/vectors/post.roi_refiner.yaml`. A note on a case is a YAML comment
line above the case, as in the 0020 vectors (0020 proposal `:693`, the first case). The cases have no `comment` key.
They use only the keys of the template (`templates/change-proposal.md:254-260`).

```yaml
section: post.roi_refiner
spec_revision: vNEXT
generated_by: the part 3 code of `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`
unverified: no host implementation. MediaPipe-Exporter has no git repo and no exporter code. The probe
  geometry notes/decisions/scripts/hand_roi_reference.py (no commit) gives the same results for the hand
  cases.
cases:
  # the raw [1,1,1,4] output of hand_roi_refinement: D = 4 / 2 = 2
  - id: read-pixel-flat-1x1x1x4
    function: read_roi_points
    params:
      point_count: 2
      coordinate_scale: pixel
      target_size: [256, 256]
    input:
      values: [10.0, 20.0, 30.0, 40.0]
    expect:
      points:
      - [10.0, 20.0]
      - [30.0, 40.0]
  # D = 3; column 2 is not used
  - id: read-pixel-d3-drops-z
    function: read_roi_points
    params:
      point_count: 2
      coordinate_scale: pixel
      target_size: [256, 256]
    input:
      values: [1.0, 2.0, 9.0, 3.0, 4.0, 9.0]
    expect:
      points:
      - [1.0, 2.0]
      - [3.0, 4.0]
  # x times T_w = 256, y times T_h = 192
  - id: read-normalized01-non-square
    function: read_roi_points
    params:
      point_count: 2
      coordinate_scale: normalized_01
      target_size: [192, 256]
    input:
      values: [0.5, 0.25, 1.0, 0.0]
    expect:
      points:
      - [128.0, 48.0]
      - [256.0, 0.0]
  - id: read-error-not-a-multiple
    function: read_roi_points
    params:
      point_count: 2
      coordinate_scale: pixel
      target_size: [256, 256]
    input:
      values: [1.0, 2.0, 3.0, 4.0, 5.0]
    expect: {error: the element count is not a multiple of point_count}
  - id: read-error-one-value-per-point
    function: read_roi_points
    params:
      point_count: 2
      coordinate_scale: pixel
      target_size: [256, 256]
    input:
      values: [1.0, 2.0]
    expect: {error: each point must have at least 2 values}
  - id: read-error-point-count-1
    function: read_roi_points
    params:
      point_count: 1
      coordinate_scale: pixel
      target_size: [256, 256]
    input:
      values: [1.0, 2.0]
    expect: {error: point_count must be at least 2}
  # inside the range
  - id: wrap-zero
    function: normalize_radians
    params: {}
    input: {angle: 0.0}
    expect: {angle: 0.0}
    compare:
      angle: {atol: 1.0e-06}
  # the range is [-pi, pi): +pi gives -pi
  - id: wrap-pi-tie-goes-to-minus-pi
    function: normalize_radians
    params: {}
    input: {angle: 3.141592653589793}
    expect: {angle: -3.141592653589793}
    compare:
      angle: {atol: 1.0e-06}
  # -pi is inside the range
  - id: wrap-minus-pi-stays
    function: normalize_radians
    params: {}
    input: {angle: -3.141592653589793}
    expect: {angle: -3.141592653589793}
    compare:
      angle: {atol: 1.0e-06}
  # floor((3pi + pi) / 2pi) = 2
  - id: wrap-3pi
    function: normalize_radians
    params: {}
    input: {angle: 9.42477796076938}
    expect: {angle: -3.141592653589793}
    compare:
      angle: {atol: 1.0e-06}
  # gives +pi/2
  - id: wrap-minus-3pi-half
    function: normalize_radians
    params: {}
    input: {angle: -4.71238898038469}
    expect: {angle: 1.5707963267948966}
    compare:
      angle: {atol: 1.0e-06}
  # the clamp: one ulp below +pi is inside the range and stays (the formula alone gives a value one
  # ulp below -pi)
  - id: wrap-pi-minus-ulp-stays
    function: normalize_radians
    params: {}
    input: {angle: 3.1415926535897927}
    expect: {angle: 3.1415926535897927}
    compare:
      angle: {atol: 1.0e-06}
  # hand: the end point below the centre gives rotation 0, size 2 * 40
  - id: alignment-end-below-start-upright
    function: rect_from_points
    params:
      rect: alignment_points
      rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
    input:
      points_src:
      - [100.0, 100.0]
      - [100.0, 140.0]
    expect:
      roi: [100.0, 100.0, 80.0, 80.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # rotation -pi/2 (counter-clockwise on the image)
  - id: alignment-end-right-of-start
    function: rect_from_points
    params:
      rect: alignment_points
      rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
    input:
      points_src:
      - [100.0, 100.0]
      - [140.0, 100.0]
    expect:
      roi: [100.0, 100.0, 80.0, 80.0]
      rotation: -1.5707963267948966
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # -pi/2 - pi/2 = -pi, inside [-pi, pi)
  - id: alignment-end-above-start-tie
    function: rect_from_points
    params:
      rect: alignment_points
      rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
    input:
      points_src:
      - [100.0, 100.0]
      - [100.0, 60.0]
    expect:
      roi: [100.0, 100.0, 80.0, 80.0]
      rotation: -3.141592653589793
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # pi/2 + pi/2 = +pi wraps to -pi
  - id: alignment-target-plus-90-wraps
    function: rect_from_points
    params:
      rect: alignment_points
      rotation: {start_point: 0, end_point: 1, target_angle_deg: 90.0}
    input:
      points_src:
      - [100.0, 100.0]
      - [100.0, 140.0]
    expect:
      roi: [100.0, 100.0, 80.0, 80.0]
      rotation: -3.141592653589793
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # atan2(-0, 0) = 0; size 0 (step 5 rejects it)
  - id: alignment-zero-length
    function: rect_from_points
    params:
      rect: alignment_points
      rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
    input:
      points_src:
      - [100.0, 100.0]
      - [100.0, 100.0]
    expect:
      roi: [100.0, 100.0, 0.0, 0.0]
      rotation: -1.5707963267948966
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # atan2(-40, 40) = -pi/4: rotation -pi/2 + pi/4 = -pi/4; size 2 * 40 * sqrt(2)
  - id: alignment-end-lower-right-clockwise
    function: rect_from_points
    params:
      rect: alignment_points
      rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
    input:
      points_src:
      - [100.0, 100.0]
      - [140.0, 140.0]
    expect:
      roi: [100.0, 100.0, 113.13708498984761, 113.13708498984761]
      rotation: -0.7853981633974483
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # the clamp on ordinary points: the direction is one ulp from the +pi tie; the rotation stays in
  # [-pi, pi)
  - id: alignment-near-tie-stays-in-range
    function: rect_from_points
    params:
      rect: alignment_points
      rotation: {start_point: 0, end_point: 1, target_angle_deg: 90.0}
    input:
      points_src:
      - [100.0, 100.0]
      - [100.00000000000005, 223.456]
    expect:
      roi: [100.0, 100.0, 246.91199999999998, 246.91199999999998]
      rotation: 3.1415926535897927
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  - id: alignment-error-no-rotation
    function: rect_from_points
    params: {rect: alignment_points}
    input:
      points_src:
      - [0.0, 0.0]
      - [1.0, 1.0]
    expect: {error: alignment_points needs rotation}
  # the face rule points_bounds is deferred (user decision Q2 = c); the closed set has one value
  - id: rect-error-value-not-in-vnext
    function: rect_from_points
    params:
      rect: points_bounds
      rotation: {start_point: 0, end_point: 1, target_angle_deg: 0.0}
    input:
      points_src:
      - [0.0, 0.0]
      - [1.0, 1.0]
    expect: {error: unknown rect 'points_bounds'}
  # the roi_decode block of the hand model passes rules -4 to -7
  - id: validate-hand-block
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
        transform: {shift_y: -0.1, square_long: true, scale: 1.0}
    input: {}
    expect: {valid: true}
  # V-post.roi_refiner-4: the key set of roi_decode is closed (scale belongs in transform)
  - id: validate-error-unknown-key
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
        scale: 1.0
    input: {}
    expect: {error: 'unknown roi_decode key(s): [''scale'']'}
  # V-post.roi_refiner-6: rotation is required
  - id: validate-error-no-rotation
    function: validate_roi_decode
    params:
      roi_decode: {point_count: 2, coordinate_scale: pixel, rect: alignment_points}
    input: {}
    expect: {error: roi_decode.rotation is required}
  # V-post.roi_refiner-4: a boolean is not an integer
  - id: validate-error-point-count-bool
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: true
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_decode.point_count must be an integer >= 2}
  # V-post.roi_refiner-4: at least 2 points
  - id: validate-error-point-count-1
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 1
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_decode.point_count must be an integer >= 2}
  # V-post.roi_refiner-5: the coordinate_scale set is closed
  - id: validate-error-coordinate-scale
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: normalized
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_decode.coordinate_scale must be pixel or normalized_01}
  # V-post.roi_refiner-5: points_bounds is deferred (user decision Q2 = c)
  - id: validate-error-rect-points-bounds
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: points_bounds
        rotation: {start_point: 0, end_point: 1, target_angle_deg: 0.0}
    input: {}
    expect: {error: roi_decode.rect must be alignment_points}
  # V-post.roi_refiner-6: rotation has exactly three keys
  - id: validate-error-rotation-key
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle: -90.0}
    input: {}
    expect: {error: 'roi_decode.rotation must have exactly the keys start_point, end_point and target_angle_deg'}
  # V-post.roi_refiner-6: a negative index is not in [0, point_count)
  - id: validate-error-start-point-negative
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: -1, end_point: 0, target_angle_deg: -90.0}
    input: {}
    expect: {error: 'roi_decode.rotation.start_point must be an integer in [0, point_count)'}
  # V-post.roi_refiner-6: an index must be an integer
  - id: validate-error-start-point-float
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 1.5, end_point: 0, target_angle_deg: -90.0}
    input: {}
    expect: {error: 'roi_decode.rotation.start_point must be an integer in [0, point_count)'}
  # V-post.roi_refiner-6: end_point = point_count is out of range
  - id: validate-error-end-point-out-of-range
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 2, target_angle_deg: -90.0}
    input: {}
    expect: {error: 'roi_decode.rotation.end_point must be an integer in [0, point_count)'}
  # V-post.roi_refiner-6: the two points must be different
  - id: validate-error-same-points
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 1, end_point: 1, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_decode.rotation.start_point and end_point must be different}
  # V-post.roi_refiner-6: target_angle_deg must be finite
  - id: validate-error-target-not-finite
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: .inf}
    input: {}
    expect: {error: roi_decode.rotation.target_angle_deg must be a finite number}
  # V-post.roi_refiner-7 (the checks of V-pre.resize.rotated_roi_crop-4): a typo is an error
  - id: validate-error-transform-typo
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
        transform: {shfit_y: -0.1}
    input: {}
    expect: {error: 'unknown roi_decode.transform key(s): [''shfit_y'']'}
  # V-post.roi_refiner-7: a string is not a boolean
  - id: validate-error-transform-square-long-string
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
        transform: {square_long: 'false'}
    input: {}
    expect: {error: roi_decode.transform.square_long must be a boolean}
  # V-post.roi_refiner-7: a boolean is not a number
  - id: validate-error-transform-scale-bool
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
        transform: {scale: true}
    input: {}
    expect: {error: roi_decode.transform.scale must be a finite number > 0}
  # V-post.roi_refiner-7: transform must be a mapping
  - id: validate-error-transform-null
    function: validate_roi_decode
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
        transform: null
    input: {}
    expect: {error: roi_decode.transform must be a mapping}
  # p0 at the crop centre, p1 64 crop px below: size 2 * 50 = 100, shift up by 10; roi_c is the crop
  # ROI Rc
  - id: decode-hand-upright
    function: decode_roi
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
        transform: {shift_y: -0.1, square_long: true, scale: 1.0}
      target_size: [256, 256]
    input:
      values: [128.0, 128.0, 128.0, 192.0]
      roi_c: [500.0, 400.0, 200.0, 200.0, 0.0]
    expect:
      roi: [500.0, 390.0, 100.0, 100.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # the points go to the source image with Rc first, then the rect is made
  - id: decode-hand-rotated-crop-roi
    function: decode_roi
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
        transform: {shift_y: -0.1, square_long: true, scale: 1.0}
      target_size: [256, 256]
    input:
      values: [128.0, 100.0, 160.0, 164.0]
      roi_c: [300.0, 200.0, 256.0, 256.0, 0.5235987755982988]
    expect:
      roi: [314.8574374157796, 161.46616352559488, 143.10835055998655, 143.10835055998655]
      rotation: 0.059951166597492556
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # p0 == p1: size 0, so no ROI
  - id: decode-hand-degenerate-none
    function: decode_roi
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
        transform: {shift_y: -0.1, square_long: true, scale: 1.0}
      target_size: [256, 256]
    input:
      values: [128.0, 128.0, 128.0, 128.0]
      roi_c: [500.0, 400.0, 200.0, 200.0, 0.0]
    expect: {roi: null}
  # roi_c is crop_roi of pre.resize.rotated_roi_crop for the raw loose rect (300, 200, 40, 40, 0.5)
  # with the crop_policy of the part 2.2 excerpt (the 0020 case transform-hand-loose-roi)
  - id: decode-hand-from-loose-crop-roi
    function: decode_roi
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
        transform: {shift_y: -0.1, square_long: true, scale: 1.0}
      target_size: [256, 256]
    input:
      values: [130.0, 120.0, 140.0, 180.0]
      roi_c: [301.9177021544168, 196.48966975243852, 108.0, 108.0, 0.5]
    expect:
      roi: [305.9628551363898, 189.0850668864885, 51.32330884939123, 51.32330884939123]
      rotation: 0.33485132258537487
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # no transform: the rect does not change; normalized_01 on a 192 x 256 input with a non-square Rc
  - id: decode-normalized01-no-transform-non-square
    function: decode_roi
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: normalized_01
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
      target_size: [192, 256]
    input:
      values: [0.5, 0.5, 0.75, 0.5]
      roi_c: [500.0, 400.0, 200.0, 100.0, 0.0]
    expect:
      roi: [500.0, 400.0, 100.0, 100.0]
      rotation: -1.5707963267948966
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # a point that is not finite: no ROI (step 1)
  - id: decode-hand-nan-point-none
    function: decode_roi
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
        transform: {shift_y: -0.1, square_long: true, scale: 1.0}
      target_size: [256, 256]
    input:
      values: [.nan, 128.0, 128.0, 192.0]
      roi_c: [500.0, 400.0, 200.0, 200.0, 0.0]
    expect: {roi: null}
  # an item with no crop has no model output: Rc with w = 0 is an error of the host
  - id: decode-error-crop-roi-not-valid
    function: decode_roi
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
        transform: {shift_y: -0.1, square_long: true, scale: 1.0}
      target_size: [256, 256]
    input:
      values: [128.0, 128.0, 128.0, 192.0]
      roi_c: [500.0, 400.0, 0.0, 200.0, 0.0]
    expect: {error: roi_c must be a valid crop ROI}
  # decode_roi checks roi_decode first: a typo in the transform is an error, not an ROI with no shift
  - id: decode-error-transform-typo
    function: decode_roi
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
        transform: {shfit_y: -0.1}
      target_size: [256, 256]
    input:
      values: [128.0, 128.0, 128.0, 192.0]
      roi_c: [500.0, 400.0, 200.0, 200.0, 0.0]
    expect: {error: 'unknown roi_decode.transform key(s): [''shfit_y'']'}
  # finite points whose source-image values overflow: no ROI (step 2)
  - id: decode-overflow-none
    function: decode_roi
    params:
      roi_decode:
        point_count: 2
        coordinate_scale: pixel
        rect: alignment_points
        rotation: {start_point: 0, end_point: 1, target_angle_deg: -90.0}
        transform: {shift_y: -0.1, square_long: true, scale: 1.0}
      target_size: [256, 256]
    input:
      values: [1.0e+308, 1.0e+308, 1.0e+308, 1.0e+308]
      roi_c: [0.0, 0.0, 1000.0, 1000.0, 0.0]
    expect: {roi: null}
  # the roi_source block of the hand model passes rules -10 to -14
  - id: source-validate-hand-block
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {valid: true}
  # V-post.roi_refiner-10: the key set of roi_source is closed
  - id: source-validate-error-unknown-key
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
        gate: {point: wrist, score_threshold_default: 0.1}
    input: {}
    expect: {error: 'unknown roi_source key(s): [''gate'']'}
  # V-post.roi_refiner-10: rotation is required
  - id: source-validate-error-no-rotation
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
    input: {}
    expect: {error: roi_source.rotation is required}
  # V-post.roi_refiner-10: parent_keypoints is the only method at vNEXT
  - id: source-validate-error-method
    function: validate_roi_source
    params:
      roi_source:
        method: detector_box
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_source.method must be parent_keypoints}
  # V-post.roi_refiner-10: the rect rule is the alignment_points rule of roi_decode
  - id: source-validate-error-rect
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: points_bounds
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_source.rect must be alignment_points}
  # V-post.roi_refiner-11: at least one instance
  - id: source-validate-error-no-instances
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances: []
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_source.instances must be a non-empty list}
  # V-post.roi_refiner-11: an instance has exactly name and points
  - id: source-validate-error-instance-key
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
          side: left
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: each roi_source.instances item must have exactly the keys name and points}
  # V-post.roi_refiner-11: a point index is not a name (names, not indices): a list item must be a string
  - id: source-validate-error-index-not-name
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [15], pinky: [17], index: [19]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: 'roi_source.instances[].points must map each local name to a non-empty list of parent point names'}
  # V-post.roi_refiner-11 (T27): each list has at least one name
  - id: source-validate-error-points-empty-list
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: 'roi_source.instances[].points must map each local name to a non-empty list of parent point names'}
  # V-post.roi_refiner-11 (T27): a single name is a list of one name, not a string
  - id: source-validate-error-points-plain-string
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: left_wrist, pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: 'roi_source.instances[].points must map each local name to a non-empty list of parent point names'}
  # V-post.roi_refiner-11 (T27): one list must not name a parent point twice
  - id: source-validate-error-duplicate-name-in-list
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_wrist], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: the parent point names of one instance must be unique}
  # V-post.roi_refiner-11: every instance has the same local names
  - id: source-validate-error-local-names-differ
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], thumb: [right_thumb]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: every roi_source.instances item must have the same local names}
  # V-post.roi_refiner-11: the instance names are unique
  - id: source-validate-error-duplicate-instance-name
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: left
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_source.instances names must be unique non-empty strings}
  # V-post.roi_refiner-11: two local names must not read the same parent point: one name in two lists
  - id: source-validate-error-duplicate-parent-name
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_forefinger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: the parent point names of one instance must be unique}
  # V-post.roi_refiner-12: a derived name must not hide a local name
  - id: source-validate-error-derived-name-collision
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          wrist: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_source.derived_points name 'wrist' is also a local point name}
  # V-post.roi_refiner-12: a weight must name a local point
  - id: source-validate-error-derived-unknown-name
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, ring: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: 'unknown point name(s) in roi_source.derived_points.middle: [''ring'']'}
  # V-post.roi_refiner-12: a weight must be > 0
  - id: source-validate-error-weight-zero
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 0}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_source.derived_points weights must be finite numbers > 0}
  # V-post.roi_refiner-12: a boolean is not a weight
  - id: source-validate-error-weight-bool
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: true}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_source.derived_points weights must be finite numbers > 0}
  # V-post.roi_refiner-12: a weight must be finite
  - id: source-validate-error-weight-inf
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: .inf, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_source.derived_points weights must be finite numbers > 0}
  # V-post.roi_refiner-13: the rotation names a local point or a derived point
  - id: source-validate-error-rotation-unknown-name
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: elbow, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_source.rotation.end_point must name a local point or a derived point}
  # V-post.roi_refiner-13: an index is not a name
  - id: source-validate-error-rotation-index
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: 0, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_source.rotation.start_point must name a local point or a derived point}
  # V-post.roi_refiner-13: the two points must be different
  - id: source-validate-error-rotation-same-point
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: wrist, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_source.rotation.start_point and end_point must be different}
  # V-post.roi_refiner-14: the gate reads a score of the parent, so not a derived point
  - id: source-validate-error-gate-derived-point
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: middle, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: roi_source.score_gate.point must name a local point}
  # V-post.roi_refiner-14: score_threshold_default = 1 is out of [0, 1)
  - id: source-validate-error-threshold-default-one
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 1.0}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: 'roi_source.score_gate.score_threshold_default must be a finite number in [0, 1) for value_default: visibility'}
  # V-post.roi_refiner-14: a negative score_threshold_default is out of range
  - id: source-validate-error-threshold-default-negative
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: -0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: 'roi_source.score_gate.score_threshold_default must be a finite number in [0, 1) for value_default: visibility'}
  # V-post.roi_refiner-14: score_threshold_default = 0 is in range (the lower end)
  - id: source-validate-threshold-default-zero
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.0}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {valid: true}
  # V-post.roi_refiner-14 (T33): value_default is required (the sidecar default of the runtime gate value)
  - id: source-validate-error-gate-no-value
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: 'roi_source.score_gate must have exactly the keys point, value_default and score_threshold_default'}
  # V-post.roi_refiner-14: value_default is score or visibility
  - id: source-validate-error-gate-unknown-value
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: confidence, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: 'roi_source.score_gate.value_default must be score or visibility'}
  # V-post.roi_refiner-14: for value_default: score the threshold is any finite number (a SimCC score has
  # no fixed range)
  - id: source-validate-score-threshold-above-one
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: score, score_threshold_default: 5.0}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {valid: true}
  # V-post.roi_refiner-14: the gate has exactly point, value_default and score_threshold_default
  - id: source-validate-error-gate-keys
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: 'roi_source.score_gate must have exactly the keys point, value_default and score_threshold_default'}
  # V-post.roi_refiner-14 (T33): the key value of the first form is not a key of score_gate any more
  - id: source-validate-error-gate-old-key-value
    function: validate_roi_source
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input: {}
    expect: {error: 'roi_source.score_gate must have exactly the keys point, value_default and score_threshold_default'}
  # V-post.roi_refiner-15: the 33 MediaPipe_Pose names of the skellytracker package have all six points,
  # and the BlazePose decode gives a visibility (pose.decode.visibility, keypoints_channel 3, sigmoid)
  - id: parent-mediapipe-pose-accepted
    function: check_parent
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      tracked_points: [nose, left_eye_inner, left_eye, left_eye_outer, right_eye_inner, right_eye, right_eye_outer,
        left_ear, right_ear, mouth_left, mouth_right, left_shoulder, right_shoulder, left_elbow, right_elbow, left_wrist,
        right_wrist, left_pinky, right_pinky, left_index, right_index, left_thumb, right_thumb, left_hip, right_hip,
        left_knee, right_knee, left_ankle, right_ankle, left_heel, right_heel, left_foot_index, right_foot_index]
      point_values: [visibility]
    expect: {valid: true}
  # V-post.roi_refiner-15 with T27: a COCO-WholeBody parent (a part of the RTMW names of
  # OpenMMLab-Exporter rtmw/keypoints.py) has the second name of the pinky and index lists, and both
  # names of the wrist list. Refused before T27, accepted now. Option E (OpenMMLab-Exporter 0041): an
  # RTMW parent gives only score at every size, so the run sets the runtime gate value score
  - id: parent-wholebody-names-accepted
    function: check_parent
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      tracked_points: [left_wrist, right_wrist, left_hand_root, left_forefinger1, left_pinky_finger1, right_hand_root,
        right_forefinger1, right_pinky_finger1]
      point_values: [score]
      gate_value: score
    expect: {valid: true}
  # V-post.roi_refiner-15: an RTMW parent gives only score at every size (option E, OpenMMLab-Exporter
  # 0041: no RTMW size declares pose.decode.visibility). With no runtime gate value, the hand gate reads
  # value_default: visibility, so the host refuses the parent
  - id: parent-error-wholebody-score-only
    function: check_parent
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      tracked_points: [left_wrist, right_wrist, left_hand_root, left_forefinger1, left_pinky_finger1, right_hand_root,
        right_forefinger1, right_pinky_finger1]
      point_values: [score]
    expect: {error: 'the parent decode gives no per-point value ''visibility'' for roi_source.score_gate'}
  # V-post.roi_refiner-15 with T28 (H1): the coco133 names of the skellytracker spec example (examples/
  # detectors/shared/skeletons/coco133_tracked_points.yaml) are the third names of the pinky and index
  # lists. The wrist list takes left_wrist (the first name). Refused before T28 (H1), accepted now. The
  # list is in the RTMW output order: the parent gives only score (option E), the run sets score
  - id: parent-example-names-accepted
    function: check_parent
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      tracked_points: [left_wrist, right_wrist, left_hand_root, left_hand_forefinger1, left_hand_pinky_finger1,
        right_hand_root, right_hand_forefinger1, right_hand_pinky_finger1]
      point_values: [score]
      gate_value: score
    expect: {valid: true}
  # V-post.roi_refiner-15: the parent has none of the names of the pinky and index lists. These names
  # are in no list (made up for the test)
  - id: parent-error-no-accepted-name
    function: check_parent
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      tracked_points: [left_wrist, right_wrist, left_hand_root, left_index_mcp, left_pinky_mcp,
        right_hand_root, right_index_mcp, right_pinky_mcp]
      point_values: [visibility]
    expect: {error: 'the parent has none of the names of point(s): [''left.index'', ''left.pinky'', ''right.index'', ''right.pinky'']'}
  # V-post.roi_refiner-15: the gate needs the named per-point value (a single-person coordinate
  # decode without pose.decode.visibility gives no value)
  - id: parent-error-no-point-scores
    function: check_parent
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      tracked_points: [nose, left_eye_inner, left_eye, left_eye_outer, right_eye_inner, right_eye, right_eye_outer,
        left_ear, right_ear, mouth_left, mouth_right, left_shoulder, right_shoulder, left_elbow, right_elbow, left_wrist,
        right_wrist, left_pinky, right_pinky, left_index, right_index, left_thumb, right_thumb, left_hip, right_hip,
        left_knee, right_knee, left_ankle, right_ankle, left_heel, right_heel, left_foot_index, right_foot_index]
      point_values: []
    expect: {error: 'the parent decode gives no per-point value ''visibility'' for roi_source.score_gate'}
  # V-post.roi_refiner-15: without score_gate, the parent needs no per-point value
  - id: parent-no-gate-no-scores
    function: check_parent
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      tracked_points: [nose, left_eye_inner, left_eye, left_eye_outer, right_eye_inner, right_eye, right_eye_outer,
        left_ear, right_ear, mouth_left, mouth_right, left_shoulder, right_shoulder, left_elbow, right_elbow, left_wrist,
        right_wrist, left_pinky, right_pinky, left_index, right_index, left_thumb, right_thumb, left_hip, right_hip,
        left_knee, right_knee, left_ankle, right_ankle, left_heel, right_heel, left_foot_index, right_foot_index]
      point_values: []
    expect: {valid: true}
  # V-post.roi_refiner-15 and -16 (T33): an RTMW 256x192 parent size gives only score (under option E,
  # OpenMMLab-Exporter 0041, every RTMW size does; the input equals parent-wholebody-names-accepted). A run sets the
  # runtime gate value score (and a threshold for that size), so the host accepts the parent
  - id: parent-wholebody-256-gate-value-score
    function: check_parent
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      tracked_points: [left_wrist, right_wrist, left_hand_root, left_forefinger1, left_pinky_finger1, right_hand_root,
        right_forefinger1, right_pinky_finger1]
      point_values: [score]
      gate_value: score
    expect: {valid: true}
  # V-post.roi_refiner-15 (T33): the same RTMW 256x192 parent size with the runtime gate value
  # visibility: no RTMW size gives a visibility (option E, OpenMMLab-Exporter 0041), so the host refuses the parent
  - id: parent-error-wholebody-256-gate-value-visibility
    function: check_parent
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      tracked_points: [left_wrist, right_wrist, left_hand_root, left_forefinger1, left_pinky_finger1, right_hand_root,
        right_forefinger1, right_pinky_finger1]
      point_values: [score]
      gate_value: visibility
    expect: {error: 'the parent decode gives no per-point value ''visibility'' for roi_source.score_gate'}
  # V-post.roi_refiner-16 (T33): a runtime gate value is score or visibility
  - id: parent-error-gate-value-unknown
    function: check_parent
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      tracked_points: [left_wrist, right_wrist, left_hand_root, left_forefinger1, left_pinky_finger1, right_hand_root,
        right_forefinger1, right_pinky_finger1]
      point_values: [score]
      gate_value: confidence
    expect: {error: the gate_value override must be score or visibility}
  # V-post.roi_refiner-16 (T33): without score_gate the sidecar has no gate, so a runtime gate value is an
  # error
  - id: parent-error-gate-value-without-gate
    function: check_parent
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      tracked_points: [left_wrist, right_wrist, left_hand_root, left_forefinger1, left_pinky_finger1, right_hand_root,
        right_forefinger1, right_pinky_finger1]
      point_values: [score]
      gate_value: score
    expect: {error: 'roi_source has no score_gate, so a gate_value override does not apply'}
  # (2 * index + pinky) / 3 = ((424 + 176) / 3, (480 + 246) / 3)
  - id: weighted-hand-middle
    function: weighted_point
    params:
      weights: {index: 2, pinky: 1}
    input:
      points:
        index: [212.0, 240.0]
        pinky: [176.0, 246.0]
    expect:
      point: [200.0, 242.0]
    compare:
      point: {atol: 0.001}
  # equal weights give the mean
  - id: weighted-equal-mean
    function: weighted_point
    params:
      weights: {a: 1, b: 1, c: 1}
    input:
      points:
        a: [0.0, 0.0]
        b: [3.0, 0.0]
        c: [0.0, 6.0]
    expect:
      point: [1.0, 2.0]
    compare:
      point: {atol: 0.001}
  # the weights are normalised by their sum: 0.25 * 0 + 0.75 * 8 = 6
  - id: weighted-fractional
    function: weighted_point
    params:
      weights: {a: 0.25, b: 0.75}
    input:
      points:
        a: [0.0, 4.0]
        b: [8.0, 0.0]
    expect:
      point: [6.0, 1.0]
    compare:
      point: {atol: 0.001}
  # upstream formula (hand_detections_from_pose_to_rects_calculator.cc): left points up (rotation 0,
  # size 2 * 58), right points to +x (rotation pi/2, size 2 * 48). The parent has only the first name
  # of each list (BlazePose), so the first name is used (T27)
  - id: source-upstream-up-and-right
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {visibility: {left_wrist: 0.9, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.9, right_pinky: 0.9, right_index: 0.9}}
    expect:
      rois:
      - [200.0, 242.0, 116.0, 116.0]
      - [148.0, 100.0, 96.0, 96.0]
      rotations: [0.0, 1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # upstream formula: left points down (the tie: pi/2 + pi/2 = pi gives -pi in both forms), right
  # points to -x (3 pi/2 gives -pi/2)
  - id: source-upstream-down-and-left
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [100.0, 100.0]
        left_pinky: [88.0, 140.0]
        left_index: [106.0, 140.0]
        right_wrist: [300.0, 200.0]
        right_pinky: [256.0, 188.0]
        right_index: [250.0, 206.0]
      values: {visibility: {left_wrist: 0.9, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.9, right_pinky: 0.9, right_index: 0.9}}
    expect:
      rois:
      - [100.0, 140.0, 80.0, 80.0]
      - [252.0, 200.0, 96.0, 96.0]
      rotations: [-3.141592653589793, -1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # upstream formula: a diagonal hand with fractional input (upstream value 333.333333333333,
  # 156.666666666667, 109.133582773081, 0.645639162958)
  - id: source-upstream-diagonal
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [300.5, 200.25]
        left_pinky: [320.0, 150.0]
        left_index: [340.0, 160.0]
        right_wrist: [200.0, 300.0]
        right_pinky: [176.0, 246.0]
        right_index: [212.0, 240.0]
      values: {visibility: {left_wrist: 0.9, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.9, right_pinky: 0.9, right_index: 0.9}}
    expect:
      rois:
      - [333.3333333333333, 156.66666666666666, 109.13358277308085, 109.13358277308085]
      - [200.0, 242.0, 116.0, 116.0]
      rotations: [0.6456391629575133, 0.0]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # the default gate (no runtime value) is strict: a wrist score equal to score_threshold_default
  # gives no ROI for that instance only
  # (float32(0.1) is 0.10000000149011612 and passes)
  - id: source-gate-tie-no-roi
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {visibility: {left_wrist: 0.1, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.9, right_pinky: 0.9, right_index: 0.9}}
    expect:
      rois:
      - null
      - [148.0, 100.0, 96.0, 96.0]
      rotations: [null, 1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # a NaN score fails the gate; a score just above score_threshold_default passes
  - id: source-gate-nan-no-roi
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {visibility: {left_wrist: .nan, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.11, right_pinky: 0.9, right_index: 0.9}}
    expect:
      rois:
      - null
      - [148.0, 100.0, 96.0, 96.0]
      rotations: [null, 1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # only the wrist score counts: low pinky and index scores do not stop the instance
  - id: source-gate-reads-only-the-gate-point
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {visibility: {left_wrist: 0.9, left_pinky: 0.0, left_index: 0.0, right_wrist: 0.9, right_pinky: 0.9, right_index: 0.9}}
    expect:
      rois:
      - [200.0, 242.0, 116.0, 116.0]
      - [148.0, 100.0, 96.0, 96.0]
      rotations: [0.0, 1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # without score_gate the host needs no values
  - id: source-no-gate
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {}
    expect:
      rois:
      - [200.0, 242.0, 116.0, 116.0]
      - [148.0, 100.0, 96.0, 96.0]
      rotations: [0.0, 1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # a score_gate with no parent values is an error of the host (rule -15 refuses such a parent)
  - id: source-error-gate-without-scores
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {}
    expect: {error: 'the parent decode gives no per-point value ''visibility'' for roi_source.score_gate'}
  # T27: a COCO-WholeBody parent (RTMW names). The pinky and the index use the second name of their
  # lists. The wrist list has both names: the first (left_wrist, right_wrist) is used, not the hand root
  # at another position with a score that fails the gate. The ROIs equal those of source-gate-reads-only-
  # the-gate-point (the same positions with BlazePose names). An RTMW parent gives only score (option
  # E, OpenMMLab-Exporter 0041), so the run sets the gate value score and an example threshold 0.5
  - id: source-alias-second-name-wholebody
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_hand_root: [206.0, 296.0]
        left_pinky_finger1: [176.0, 246.0]
        left_forefinger1: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_hand_root: [104.0, 97.0]
        right_pinky_finger1: [144.0, 112.0]
        right_forefinger1: [150.0, 94.0]
      values: {score: {left_wrist: 0.9, left_hand_root: 0.05, left_pinky_finger1: 0.9, left_forefinger1: 0.9, right_wrist: 0.9, right_hand_root: 0.05, right_pinky_finger1: 0.9, right_forefinger1: 0.9}}
      score_threshold: 0.5
      gate_value: score
    expect:
      rois:
      - [200.0, 242.0, 116.0, 116.0]
      - [148.0, 100.0, 96.0, 96.0]
      rotations: [0.0, 1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # T27 and T28 (H1): the parent has every name of every list, at other positions. The first name
  # (BlazePose) is used: the ROIs equal those of the BlazePose-only case above
  - id: source-alias-both-present-takes-first
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
        left_hand_root: [206.0, 296.0]
        left_pinky_finger1: [170.0, 250.0]
        left_forefinger1: [220.0, 236.0]
        right_hand_root: [104.0, 97.0]
        right_pinky_finger1: [140.0, 116.0]
        right_forefinger1: [156.0, 90.0]
        left_hand_pinky_finger1: [166.0, 254.0]
        left_hand_forefinger1: [226.0, 232.0]
        right_hand_pinky_finger1: [136.0, 120.0]
        right_hand_forefinger1: [160.0, 86.0]
      values: {visibility: {left_wrist: 0.9, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.9, right_pinky: 0.9, right_index: 0.9, left_hand_root: 0.9, left_pinky_finger1: 0.9, left_forefinger1: 0.9, right_hand_root: 0.9, right_pinky_finger1: 0.9, right_forefinger1: 0.9, left_hand_pinky_finger1: 0.9, left_hand_forefinger1: 0.9, right_hand_pinky_finger1: 0.9, right_hand_forefinger1: 0.9}}
    expect:
      rois:
      - [200.0, 242.0, 116.0, 116.0]
      - [148.0, 100.0, 96.0, 96.0]
      rotations: [0.0, 1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # T28 (H1): a parent with the coco133 names of the skellytracker spec example. The pinky and the index
  # use the third name of their lists, the wrist the first. The ROIs equal those of
  # source-gate-reads-only-the-gate-point (the same positions with BlazePose names). The list is in the
  # RTMW output order: the parent gives only score (option E, OpenMMLab-Exporter 0041), gate value score, threshold 0.5
  - id: source-alias-third-name-example
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_hand_forefinger1: [212.0, 240.0]
        left_hand_pinky_finger1: [176.0, 246.0]
        right_wrist: [100.0, 100.0]
        right_hand_forefinger1: [150.0, 94.0]
        right_hand_pinky_finger1: [144.0, 112.0]
      values: {score: {left_wrist: 0.9, left_hand_forefinger1: 0.9, left_hand_pinky_finger1: 0.9, right_wrist: 0.9, right_hand_forefinger1: 0.9, right_hand_pinky_finger1: 0.9}}
      score_threshold: 0.5
      gate_value: score
    expect:
      rois:
      - [200.0, 242.0, 116.0, 116.0]
      - [148.0, 100.0, 96.0, 96.0]
      rotations: [0.0, 1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # T28 (H1): the parent has the second and the third names of the pinky and index lists, the third at
  # other positions. The second name (mmpose) is used: the ROIs equal those of the case above. An RTMW
  # parent gives only score (option E, OpenMMLab-Exporter 0041): gate value score, threshold 0.5
  - id: source-alias-second-before-third
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky_finger1: [176.0, 246.0]
        left_forefinger1: [212.0, 240.0]
        left_hand_pinky_finger1: [166.0, 254.0]
        left_hand_forefinger1: [226.0, 232.0]
        right_wrist: [100.0, 100.0]
        right_pinky_finger1: [144.0, 112.0]
        right_forefinger1: [150.0, 94.0]
        right_hand_pinky_finger1: [136.0, 120.0]
        right_hand_forefinger1: [160.0, 86.0]
      values: {score: {left_wrist: 0.9, left_pinky_finger1: 0.9, left_forefinger1: 0.9, left_hand_pinky_finger1: 0.9, left_hand_forefinger1: 0.9, right_wrist: 0.9, right_pinky_finger1: 0.9, right_forefinger1: 0.9, right_hand_pinky_finger1: 0.9, right_hand_forefinger1: 0.9}}
      score_threshold: 0.5
      gate_value: score
    expect:
      rois:
      - [200.0, 242.0, 116.0, 116.0]
      - [148.0, 100.0, 96.0, 96.0]
      rotations: [0.0, 1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # T27: the parent has none of the names of the pinky and index lists (names in no list, made up for
  # the test): an error of the host (rule -15 refuses such a parent)
  - id: source-error-no-accepted-name
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_index_mcp: [212.0, 240.0]
        left_pinky_mcp: [176.0, 246.0]
        right_wrist: [100.0, 100.0]
        right_index_mcp: [150.0, 94.0]
        right_pinky_mcp: [144.0, 112.0]
      values: {visibility: {left_wrist: 0.9, left_index_mcp: 0.9, left_pinky_mcp: 0.9, right_wrist: 0.9, right_index_mcp: 0.9, right_pinky_mcp: 0.9}}
    expect: {error: 'the parent has none of the names of point(s): [''left.index'', ''left.pinky'', ''right.index'', ''right.pinky'']'}
  # T26 (6): no runtime threshold, so the default 0.1 applies: left 0.3 passes, right 0.05 fails
  - id: source-threshold-default
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {visibility: {left_wrist: 0.3, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.05, right_pinky: 0.9, right_index: 0.9}}
    expect:
      rois:
      - [200.0, 242.0, 116.0, 116.0]
      - null
      rotations: [0.0, null]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # T26 (6): the runtime threshold 0.04 replaces the default: both 0.3 and 0.05 pass
  - id: source-threshold-override-lower
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {visibility: {left_wrist: 0.3, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.05, right_pinky: 0.9, right_index: 0.9}}
      score_threshold: 0.04
    expect:
      rois:
      - [200.0, 242.0, 116.0, 116.0]
      - [148.0, 100.0, 96.0, 96.0]
      rotations: [0.0, 1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # T26 (6): the runtime threshold 0.3 equals the left score: the comparison stays strict, so no ROI;
  # right 0.05 fails
  - id: source-threshold-override-strict
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {visibility: {left_wrist: 0.3, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.05, right_pinky: 0.9, right_index: 0.9}}
      score_threshold: 0.3
    expect:
      rois:
      - null
      - null
      rotations: [null, null]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # T26 (6): a runtime threshold must be in [0, 1), as the default (1.0 never passes a score in [0, 1])
  - id: source-error-threshold-override-range
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {visibility: {left_wrist: 0.3, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.05, right_pinky: 0.9, right_index: 0.9}}
      score_threshold: 1.0
    expect: {error: 'the score_threshold override must be a finite number in [0, 1) for the gate value visibility'}
  # T26 (6): without score_gate the sidecar has no gate, so a runtime threshold is an error
  - id: source-error-threshold-override-without-gate
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {}
      score_threshold: 0.2
    expect: {error: 'roi_source has no score_gate, so a score_threshold override does not apply'}
  # keypoint-visibility: a gate with value_default: score and the threshold 5.0 (a SimCC-like score). A
  # test parent with the BlazePose names gives both values in the other order (no RTMW size gives a
  # visibility: option E, OpenMMLab-Exporter 0041). The gate reads only the named value: left
  # 7.56 passes, right 1.29 fails
  - id: source-gate-value-score
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: score, score_threshold_default: 5.0}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {score: {left_wrist: 7.56, left_pinky: 6.0, left_index: 6.0, right_wrist: 1.29, right_pinky: 6.0, right_index: 6.0}, visibility: {left_wrist: 0.05, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.97, right_pinky: 0.9, right_index: 0.9}}
    expect:
      rois:
      - [200.0, 242.0, 116.0, 116.0]
      - null
      rotations: [0.0, null]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # keypoint-visibility: the same parent and a gate with value_default: visibility (0.1): left 0.05 fails, right
  # 0.97 passes. The score does not count
  - id: source-gate-value-visibility
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {score: {left_wrist: 7.56, left_pinky: 6.0, left_index: 6.0, right_wrist: 1.29, right_pinky: 6.0, right_index: 6.0}, visibility: {left_wrist: 0.05, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.97, right_pinky: 0.9, right_index: 0.9}}
    expect:
      rois:
      - null
      - [148.0, 100.0, 96.0, 96.0]
      rotations: [null, 1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # keypoint-visibility: the parent gives only score, and the gate reads visibility: an error of the
  # host (rule -15 refuses such a parent)
  - id: source-error-gate-value-missing
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_hand_root: [206.0, 296.0]
        left_pinky_finger1: [176.0, 246.0]
        left_forefinger1: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_hand_root: [104.0, 97.0]
        right_pinky_finger1: [144.0, 112.0]
        right_forefinger1: [150.0, 94.0]
      values: {score: {left_wrist: 7.56, left_hand_root: 9.0, left_pinky_finger1: 6.0, left_forefinger1: 6.0, right_wrist: 1.29, right_hand_root: 9.0, right_pinky_finger1: 6.0, right_forefinger1: 6.0}}
    expect: {error: 'the parent decode gives no per-point value ''visibility'' for roi_source.score_gate'}
  # T26 (6) with keypoint-visibility: for value_default: score a runtime threshold above 1 is valid. 7.0: left
  # 7.56 passes, right 1.29 fails
  - id: source-threshold-override-score-above-one
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: score, score_threshold_default: 5.0}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_hand_root: [206.0, 296.0]
        left_pinky_finger1: [176.0, 246.0]
        left_forefinger1: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_hand_root: [104.0, 97.0]
        right_pinky_finger1: [144.0, 112.0]
        right_forefinger1: [150.0, 94.0]
      values: {score: {left_wrist: 7.56, left_hand_root: 9.0, left_pinky_finger1: 6.0, left_forefinger1: 6.0, right_wrist: 1.29, right_hand_root: 9.0, right_pinky_finger1: 6.0, right_forefinger1: 6.0}}
      score_threshold: 7.0
    expect:
      rois:
      - [200.0, 242.0, 116.0, 116.0]
      - null
      rotations: [0.0, null]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # T33: the runtime gate value score replaces value_default: visibility. An RTMW parent (only score at
  # every size, option E, OpenMMLab-Exporter 0041) with an example threshold 0.5 for a 256x192 size (OpenMMLab-Exporter 0041 has the values):
  # left 0.74 passes, right 0.31 fails
  - id: source-gate-value-override-score
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_hand_root: [206.0, 296.0]
        left_pinky_finger1: [176.0, 246.0]
        left_forefinger1: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_hand_root: [104.0, 97.0]
        right_pinky_finger1: [144.0, 112.0]
        right_forefinger1: [150.0, 94.0]
      values: {score: {left_wrist: 0.74, left_hand_root: 0.9, left_pinky_finger1: 0.8, left_forefinger1: 0.8, right_wrist: 0.31, right_hand_root: 0.9, right_pinky_finger1: 0.8, right_forefinger1: 0.8}}
      score_threshold: 0.5
      gate_value: score
    expect:
      rois:
      - [200.0, 242.0, 116.0, 116.0]
      - null
      rotations: [0.0, null]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # T33 (rule -16): a runtime gate value other than value_default needs a runtime threshold, because the
  # default threshold goes with value_default
  - id: source-error-gate-value-override-no-threshold
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_hand_root: [206.0, 296.0]
        left_pinky_finger1: [176.0, 246.0]
        left_forefinger1: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_hand_root: [104.0, 97.0]
        right_pinky_finger1: [144.0, 112.0]
        right_forefinger1: [150.0, 94.0]
      values: {score: {left_wrist: 0.74, left_hand_root: 0.9, left_pinky_finger1: 0.8, left_forefinger1: 0.8, right_wrist: 0.31, right_hand_root: 0.9, right_pinky_finger1: 0.8, right_forefinger1: 0.8}}
      gate_value: score
    expect: {error: a gate_value override other than value_default needs a score_threshold override}
  # T33: a runtime gate value equal to value_default needs no runtime threshold; the default 0.1 applies.
  # The result of source-gate-value-visibility: left 0.05 fails, right 0.97 passes
  - id: source-gate-value-override-equal-default
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {score: {left_wrist: 7.56, left_pinky: 6.0, left_index: 6.0, right_wrist: 1.29, right_pinky: 6.0, right_index: 6.0}, visibility: {left_wrist: 0.05, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.97, right_pinky: 0.9, right_index: 0.9}}
      gate_value: visibility
    expect:
      rois:
      - null
      - [148.0, 100.0, 96.0, 96.0]
      rotations: [null, 1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # T33: the threshold range follows the gate value in effect. value_default is visibility, the runtime
  # gate value is score, so the threshold 4.0 is valid (an RTMW l-384 score; median about 4.1): left 7.56
  # passes, right 1.29 fails
  - id: source-threshold-range-follows-gate-value-score
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_hand_root: [206.0, 296.0]
        left_pinky_finger1: [176.0, 246.0]
        left_forefinger1: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_hand_root: [104.0, 97.0]
        right_pinky_finger1: [144.0, 112.0]
        right_forefinger1: [150.0, 94.0]
      values: {score: {left_wrist: 7.56, left_hand_root: 9.0, left_pinky_finger1: 6.0, left_forefinger1: 6.0, right_wrist: 1.29, right_hand_root: 9.0, right_pinky_finger1: 6.0, right_forefinger1: 6.0}}
      score_threshold: 4.0
      gate_value: score
    expect:
      rois:
      - [200.0, 242.0, 116.0, 116.0]
      - null
      rotations: [0.0, null]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # T33: the threshold range follows the gate value in effect. value_default is score, the runtime gate
  # value is visibility, so the threshold 1.5 is out of [0, 1)
  - id: source-error-threshold-range-follows-gate-value-visibility
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: score, score_threshold_default: 5.0}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_hand_root: [206.0, 296.0]
        left_pinky_finger1: [176.0, 246.0]
        left_forefinger1: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_hand_root: [104.0, 97.0]
        right_pinky_finger1: [144.0, 112.0]
        right_forefinger1: [150.0, 94.0]
      values: {score: {left_wrist: 7.56, left_hand_root: 9.0, left_pinky_finger1: 6.0, left_forefinger1: 6.0, right_wrist: 1.29, right_hand_root: 9.0, right_pinky_finger1: 6.0, right_forefinger1: 6.0}}
      score_threshold: 1.5
      gate_value: visibility
    expect: {error: 'the score_threshold override must be a finite number in [0, 1) for the gate value visibility'}
  # T33 (rule -16): a runtime gate value is score or visibility
  - id: source-error-gate-value-override-unknown
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_hand_root: [206.0, 296.0]
        left_pinky_finger1: [176.0, 246.0]
        left_forefinger1: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_hand_root: [104.0, 97.0]
        right_pinky_finger1: [144.0, 112.0]
        right_forefinger1: [150.0, 94.0]
      values: {score: {left_wrist: 7.56, left_hand_root: 9.0, left_pinky_finger1: 6.0, left_forefinger1: 6.0, right_wrist: 1.29, right_hand_root: 9.0, right_pinky_finger1: 6.0, right_forefinger1: 6.0}}
      score_threshold: 0.5
      gate_value: confidence
    expect: {error: the gate_value override must be score or visibility}
  # T33 (rule -16): without score_gate the sidecar has no gate, so a runtime gate value is an error
  - id: source-error-gate-value-override-without-gate
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_hand_root: [206.0, 296.0]
        left_pinky_finger1: [176.0, 246.0]
        left_forefinger1: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_hand_root: [104.0, 97.0]
        right_pinky_finger1: [144.0, 112.0]
        right_forefinger1: [150.0, 94.0]
      values: {}
      gate_value: score
    expect: {error: 'roi_source has no score_gate, so a gate_value override does not apply'}
  # a point that is not finite (an undetected parent point): no ROI for that instance
  - id: source-nan-point-no-roi
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [.nan, .nan]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {visibility: {left_wrist: 0.9, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.9, right_pinky: 0.9, right_index: 0.9}}
    expect:
      rois:
      - null
      - [148.0, 100.0, 96.0, 96.0]
      rotations: [null, 1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # middle = wrist: size 0 fails the validity test, no ROI
  - id: source-zero-size-no-roi
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
        left_wrist: [50.0, 60.0]
        left_pinky: [50.0, 60.0]
        left_index: [50.0, 60.0]
      values: {visibility: {right_wrist: 0.9, right_pinky: 0.9, right_index: 0.9, left_wrist: 0.9, left_pinky: 0.9, left_index: 0.9}}
    expect:
      rois:
      - null
      - [148.0, 100.0, 96.0, 96.0]
      rotations: [null, 1.5707963267948966]
    compare:
      rois: {atol: 0.001}
      rotations: {atol: 1.0e-06}
  # a parent pose with none of the names of a point is an error of the host, not 'no ROI'
  - id: source-error-missing-parent-point
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: 1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
      values: {visibility: {left_wrist: 0.9, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.9, right_pinky: 0.9}}
    expect: {error: 'the parent has none of the names of point(s): [''right.index'']'}
  # roi_from_keypoints checks roi_source first
  - id: source-error-invalid-block
    function: roi_from_keypoints
    params:
      roi_source:
        method: parent_keypoints
        instances:
        - name: left
          points: {wrist: [left_wrist, left_hand_root], pinky: [left_pinky, left_pinky_finger1, left_hand_pinky_finger1], index: [left_index, left_forefinger1, left_hand_forefinger1]}
        - name: right
          points: {wrist: [right_wrist, right_hand_root], pinky: [right_pinky, right_pinky_finger1, right_hand_pinky_finger1], index: [right_index, right_forefinger1, right_hand_forefinger1]}
        derived_points:
          middle: {index: 2, pinky: -1}
        score_gate: {point: wrist, value_default: visibility, score_threshold_default: 0.1}
        rect: alignment_points
        rotation: {start_point: middle, end_point: wrist, target_angle_deg: -90.0}
    input:
      keypoints:
        left_wrist: [200.0, 300.0]
        left_pinky: [176.0, 246.0]
        left_index: [212.0, 240.0]
        right_wrist: [100.0, 100.0]
        right_pinky: [144.0, 112.0]
        right_index: [150.0, 94.0]
      values: {visibility: {left_wrist: 0.9, left_pinky: 0.9, left_index: 0.9, right_wrist: 0.9, right_pinky: 0.9, right_index: 0.9}}
    expect: {error: roi_source.derived_points weights must be finite numbers > 0}
```

## 5. Parity evidence

| Item | Value |
|---|---|
| Gates, set before the run, and their source | Set on 2026-10-24, before the run of the parity script. One parity script serves the four MediaPipe proposals: the 0020 proposal, this proposal, `landmark-extra-outputs` and `landmark-depth-divisor` (user decision T28 (H6); `specs/exporter-guide/sidecars/workflow/phase-2-proposal.md:24-26`). Each proposal keeps its gates. The gates (1) and (2) of the 0020 proposal apply to the 256² refiner input too (0020 proposal `:1642`): the crop within 1 grey level for each value, and the crop ROI `Rc` of each hand against the probe within `1e-3` px and `1e-6` rad (user decision Q7 = c). This proposal adds these gates. (1) The decode alone. For each hand, give the same refiner output (the output of the ONNX model on the crop of the probe) to `decode_roi` of this reference file and to `rect_from_recrop_points` of the probe of MediaPipe-Exporter 0006. Gate: `<= 1e-3` px for `cx`, `cy`, `w`, `h` and `<= 1e-6` rad for the rotation modulo 2π (the tolerances of part 4). The earlier gate (`<= 1e-9` on the refined ROI of the two full paths) is replaced: the two paths make crops that differ by 1 grey level in some values, so the refiner outputs differ. A scratch measurement of 2026-10-24 (secondary, `q7-precision\out\tables.md` in the session scratchpad, not committed) gives up to 0.0151 px (image) and 0.0130 px (video) between the refined ROIs of the reference path and of the 0006 probe crop. Record that number as information, not as a gate. (2) Final outputs: the gate (3) of the 0020 proposal (0020 proposal `:1642`; user decision 2026-10-24: a median and a p95 with a margin, and a count of outliers, no maximum). Image: median `<= 0.37` px, p95 `<= 1.92` px, 0 outliers, 0 presence disagreements of 116. Video: median `<= 0.21` px, p95 `<= 1.79` px, at most 2 outliers, at most 5 presence disagreements of 438. An outlier is a hand or a hand-frame whose largest landmark error is above 10 % of its hand-landmark ROI size. The 0020 proposal gives the source of the numbers. The earlier gate (not above the 0006 numbers, the maximum included) is replaced, because the proposal path fails it on one threshold decision (video maximum 16.99 px against 5.05 px). (3) The loose ROI from the body pose (user decision T24). For each hand that passes the gate, `roi_from_keypoints` of this reference file with the `roi_source` of part 2.2, then `crop_roi` of the 0020 reference file with the `crop_policy` of part 2.2, must give the crop ROI of `roi_from_pose` of the 0006 probe, from the same pose landmarks: `<= 1e-3` px for `cx`, `cy`, `w`, `h` and `<= 1e-6` rad modulo 2π. The set of hands that pass the gate (wrist visibility `> 0.1`: `value_default: visibility` and the default `score_threshold_default`, no runtime gate value and no runtime threshold) must be the same in both. Source: the vectors `source-upstream-*` and the cross-check of part 4 (difference 0). (4) The export error of the refiner: ONNX against LiteRT `<= 1.1e-4` px (MediaPipe-Exporter 0016 and 0003). |
| Test images (paths or dataset IDs), and the branch that each image runs | The sets of MediaPipe-Exporter 0006. Images: the 60 largest single-person COCO val2017 images with a visible wrist (IMAGE mode, a new landmarker for each image). Video: the first 300 frames of `sesh_2022-09-19_16_16_50_in_class_jsm_synced_Cam1.mp4` (VIDEO mode). Branches: `rect: alignment_points` with `rotation` and `transform` on every hand; the rotation sign and the wrap on left and right hands in many poses; the image set has ROIs near the image border. `roi_source` on every hand of every image and frame: both instances and the gate (in MediaPipe-Exporter 0006, 100 of the 438 video hand-frames have no hand in both paths; the run must report how many hands fail the gate). The parent is BlazePose, so each point uses the first name of its list. The second and third names (T27, T28 (H1)), a runtime threshold and a runtime gate value (`score`, T33) are not run on a real image. Not run on a real image: `normalized_01` (the hand model gives pixels), step 5 with an ROI of size 0 (not seen in 0006), a NaN pose point, and a parent check that fails. The vectors cover these branches. |
| Upstream reference: library, version, config and command | `mediapipe` 1.1.1, `HolisticLandmarker` with `holistic_landmarker.task` `float16/1` (sha256 `e2dab611…50c3f8`, MediaPipe-Exporter 0016). The upstream does not output the refined ROI. Thus gate (2) compares the hand landmarks after the ROI. The upstream does not output the loose ROI either. Gate (3) compares it with the 0006 probe, which follows `HolisticLandmarker` end to end (MediaPipe-Exporter 0006). A build of MediaPipe that writes the `NORM_RECT` output of `HandRoiRefinementGraph` would give a direct ROI reference (`docs/mediapipe-whole-body.md:705-713`). It does not exist. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | to run (MediaPipe-Exporter 0016 gives 1.1e-4 px from an uncommitted probe) |
| Preprocessed input: maximum absolute difference for each image | to run. The crop is `rotated_roi_crop` of the 0020 reference file, with the `crop_policy` of part 2.2. The gate is gate (1) of the 0020 proposal (`:1642`). It needs a build of MediaPipe that writes the input tensor, which does not exist (0020 proposal `:1644`). MediaPipe-Exporter 0006 shows that the `warpAffine` crop of its probe and a transcription of the upstream crop (a control, not upstream) differ by at most 1 grey level. The scratch measurement of 2026-10-24 (secondary) gives the cause: the float32 geometry, not the warp function (0020 proposal, part 1). |
| Row count for each image: sidecar path and upstream | to run (one ROI or no ROI for each hand; compared with the presence of the upstream hand) |
| Final outputs in source-image coordinates: metric and value for each role | to run. `roi_refiner`: the decode against the probe decode on the same output (gate 1), and the loose ROI against the probe (gate 3). Downstream: the per-hand maximum landmark error in px and in % of the ROI size against `HolisticLandmarker`, as a median, a p95 and a count of outliers (gate 2). |
| Result | to run (MediaPipe-Exporter has no git repo, so a script cannot be committed) |
| Script path in the exporter repo | `notes/decisions/scripts/hand_chain_parity.py` (to write; user decision T28 (H6)). The 0020 proposal, `landmark-extra-outputs` and `landmark-depth-divisor` name the same script in their parts 5. This proposal gives its refiner gates (1) and (3) and the final-output gate (2). It copies `holistic_parity.py` (MediaPipe-Exporter 0006). For both hand models, it replaces the crops and the projection with `rotated_roi_crop` and `unproject_points` of the 0020 reference file. It makes the raw loose rect with `roi_from_keypoints` of this reference file and the `roi_source` of part 2.2, from the pose landmarks of `HolisticLandmarker` (the input of the 0006 probe), and gives it to the refiner crop with the `crop_policy` of part 2.2. It compares that crop ROI with `roi_from_pose` of the probe (gate 3). It replaces `rect_from_recrop_points` and the crop inverse of the refiner with `decode_roi` of this reference file, with the crop ROI `Rc` of each hand. It compares the two decodes for each hand on the same refiner output (gate 1). It writes `model_cache/probes/hand_chain_parity.json`. |
| Exporter commit of the script | none (no git repo) |
| Command | `uv run --script notes/decisions/scripts/hand_chain_parity.py --n-images 60 --n-frames 300` (to run) |

**A later evaluation (user decision T27), not a parity gate.** The hand-keypoint accuracy with the
COCO-WholeBody names of the lists is not measured (part 1). The gate value for an RTMW parent is measured: OpenMMLab-Exporter
decision 0041 (at `32ab848`) gives the runtime gate value `score` at every size, with two thresholds for each size: `t_recall` (the default recommendation) and `t_J` (the selective option) (user decision T37; part 1, table "RTMW gate thresholds"; OpenMMLab-Exporter 0041, "Thresholds"; not a sidecar field, user decision U4). A later run measures the hand-keypoint accuracy on the hand annotations
of COCO-WholeBody val for three paths: (a) a BlazePose parent, then the refiner and the hand
landmark model; (b) an RTMW parent (the gate value `score` and the OpenMMLab-Exporter 0041 threshold `t_recall` or `t_J` of its size), then the refiner and the hand landmark model; (c) the 21 hand
points of RTMW itself, with no hand models. The run needs the host sections and the MediaPipe hand
ONNX files (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), T27, secondary). It also shows if the
loose rect (`middle`, the size rule, scale 2.7) fits COCO-WholeBody points, and if the OpenMMLab-Exporter 0041 thresholds hold for a person-detector crop
and for video (OpenMMLab-Exporter 0041 used GT boxes, single images and only the 36.6 % of the hands that Holistic can track). Its result does not change the gates of this part.

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | New module `skellytracker/core/detectors/processing/roi_refiner_decode.py` with `decode_roi` and its steps, from the reference file. The crop inverse (`unproject_points`), the ROI transform (`transform_roi`) and the validity test (`roi_is_valid`) come from a module of the 0020 proposal (its part 6, `:1658`). That module is `skellytracker/core/detectors/processing/rotated_roi_crop.py`, with the ROI primitive `RotatedRoi`. The input crop is its `preprocess_image` branch for `rotated_roi_crop` (its part 6, row "Dispatch point", `:1659`). Its `resize_meta` is the crop ROI `Rc` that `decode_roi` needs. The ROI source (user decision T24): `validate_roi_source`, `check_parent`, `weighted_point` and `roi_from_keypoints` in the same module. `roi_from_keypoints` takes the parent `Keypoints` (`skellytracker/core/data_primitives/keypoints.py:10-19`): the names (`has_name`, `index_of`, `:60-64`), `xyz` in pixels, and the named per-point value of the gate value in effect (the runtime gate value, else `score_gate.value_default`; T33). `Keypoints.visibility` is not that value today: it holds the keypoint score ("confidence scores 0.0–1.0", `keypoints.py:17-19`), and the RTMW detector fills it from `kpt_scores` and sets it to 0 below the threshold (`skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py:103-106`). For the implementer: the visibility proposal (its part 6, "A name conflict") names two choices, a map of named per-point values or a rename of the field. Do not read `Keypoints.visibility` as the BlazePose visibility without that decision. It returns one `RotatedRoi` or `None` for each instance, tagged with the instance name. The runtime gate threshold (T26 (6), rule `-16`) is a setting of the stage, with the default `score_threshold_default`. The runtime gate value (T33, rule `-16`) is a setting of the stage too, with the default `value_default`. |
| Dispatch point | (1) The stage. `DetectionStageConfig` has one optional `object_detector`, `keypoint_detectors` and `children`, and no slot between them (`skellytracker/core/config/detection_stage_config.py:18-28`). `DetectionStage.run` makes the crop with `crop_bbox.to_crop(image)`, an axis-aligned slice (`skellytracker/core/tracker/detection_stage.py:113-146`). Proposed: a new optional `roi_refiner` slot in `DetectionStageConfig`. `DetectionStage.run` calls it after the object detector (or the parent ROI) and before the keypoint detectors. The keypoint detectors then crop the refined ROI. This needs the `RotatedRoi` primitive and the `rotated_roi_crop` branch of the 0020 proposal (its part 6, `:1658-1659`; `BoundingBox` has no rotation). The 0020 proposal names this slot as one ROI source (`:1659`, item 5). Its Q3 is decided (user decision T22 (1), `:1808-1814`): the field `pose.requires_object_detector` leaves the spec, and `input.resize.method` gives the input that a model needs. Thus a stage reads `rotated_roi_crop` and gives the model an ROI, not a detector box. For the implementer: the tracking choice between the refined ROI and the ROI from the previous landmarks (`RoiTrackingCalculator`, `docs/mediapipe-whole-body.md:400-403`) is out of scope of the spec (an earlier frame). It belongs near `BBoxPolicy`. (2) The registry. `OBJECT_DETECTOR_REGISTRY` and `KEYPOINT_DETECTOR_REGISTRY` (`skellytracker/core/detectors/detector_base_classes.py:165-166`) have no place for a refiner. Proposed: the catalog dispatch of skellytracker 0016 by role (`format/versioning.md:84`), with the role `roi_refiner`. (3) The ROI source (user decision T24). Today a hand child stage gets its crop from `KeypointBoundingBoxDetector`, an object detector configured in code (`skellytracker/core/detectors/keypoint_detectors/mediapipe/run_demo.py:94-110`; `keypoint_bbox_detector.py:53-70, 90-122`). For a refiner, the stage reads `roi_source` from the refiner sidecar instead, and makes `R` with `roi_from_keypoints` from the parent keypoints that `DetectionStage.run` already has (`detection_stage.py:96-122`). Then it crops the refiner input with `rotated_roi_crop`, runs the refiner, decodes the refined ROI, and crops the keypoint detectors with it. Each instance of `roi_source` is one child crop (for the hand: `left` and `right`). (4) The parent check (`V-post.roi_refiner-15`) runs when the host builds the stage: it reads `pose.tracked_points`, the decode method and `pose.decode.visibility` of the parent sidecar. It resolves the name lists (T27), and it checks that the parent, at the parent size of the stage, gives the gate value in effect (T33 asked for the check at the parent size in use because the A1 form declared `pose.decode.visibility` per size. Under option E, OpenMMLab-Exporter 0041 at `32ab848`, the field is top level, so every size of a parent gives the same values, and every RTMW size gives only `score`.). If not, the stage build fails with a message that names the value and the size (user decision T34: the host never skips the gate). `Keypoints.visibility` exists for every decoder and holds the score (`keypoints.py:17-19`), so the check must look at the sidecar of the parent, not at the field. |
| Validator changes (`model.py`, with rule IDs) | `Role` (`skellytracker/core/sidecar/model.py:25`): add `"roi_refiner"`. `OutputSemantic` (`:27`): add `"roi_points"`. `_check_role` (`:488-494`): `V-common.identity-2`. `_check_role_requirements` (`:503-512`): `V-post.roi_refiner-1` and `-2`. `_check_outputs_semantics` (`:524-540`): `V-common.outputs-4` and `V-post.roi_refiner-3`. New `RoiDecodeSpec` with `RoiRotationSpec` and the transform model that the 0020 proposal adds for `crop_policy.transform` (its part 6, row "Validator changes", `:1660`): `V-post.roi_refiner-4` to `-7`. Both are `_StrictModel` (`:32-33`), so an unknown key is an error. `validate_roi_decode` of the reference file gives the expected result of each check. `V-post.roi_refiner-8`: the 0020 proposal adds `rotated_roi_crop` to `ResizeSpec.method` (`:79`); a `SidecarModel` validator checks the method with the role. The changed `V-pre.resize.rotated_roi_crop-1` goes in the `SidecarModel` validator that the 0020 proposal adds for that rule (`:1660`): it also allows `role: [roi_refiner]`. `V-post.roi_refiner-9` goes in `load_sidecar` (`skellytracker/core/sidecar/loader.py`) with the other path checks. Gate every new rule on `schema_version >= vNEXT`. A new `RoiSourceSpec` (`_StrictModel`) with `method`, `instances` (a list of `{name, points}`), `derived_points`, `score_gate`, `rect` and `rotation` (`V-post.roi_refiner-10` to `-14`; `validate_roi_source` gives the expected result of each check). `_check_role_requirements` also requires `roi_source` for `roi_refiner` and forbids it for other roles (`V-post.roi_refiner-1`, `-2`). `V-post.roi_refiner-15` is not a check of one sidecar: it goes in the code that builds a stage from a refiner and its parent. |
| Tests | The vectors `specs/model-sidecar/vectors/post.roi_refiner.yaml` against `roi_refiner_decode.py`. Validation tests in `skellytracker/tests/sidecar/test_model_validation.py` for each new rule. A golden parity test, as the tests in `skellytracker/tests/sidecar/` do for the detectors. It has one hand crop fixture (a 256² tensor and the ONNX output of the refiner) and the expected ROI. The vectors of `roi_source` (78 cases: `validate_roi_source` 31, `check_parent` 11, `weighted_point` 3, `roi_from_keypoints` 33). A stage test: a body `Keypoints` with the six BlazePose names, a refiner with the excerpt of part 2.2, and the expected `R` of each side (the vector `source-upstream-up-and-right`). A test that a parent without `left_pinky` is refused. The runner compares each field with the `atol` of its `compare` (user decision Q7 = c of the 0020 proposal). |
| Existing code that the change touches | `skellytracker/core/sidecar/model.py` (`Role`, `OutputSemantic`, `SidecarModel` validators); `skellytracker/core/config/detection_stage_config.py` (`DetectionStageConfig`); `skellytracker/core/tracker/detection_stage.py` (`DetectionStage.run`, `run_batch`); `skellytracker/core/detectors/detector_base_classes.py` (the registries); `skellytracker/core/data_primitives/bounding_box.py` (no rotation; the 0020 proposal adds `RotatedRoi`); `tools/sidecar_normalize.py` (`_roles` and the selector `role=roi_refiner`). The new module of the 0020 proposal, `rotated_roi_crop.py`, does not change: this module imports from it. `skellytracker/core/detectors/object_detectors/keypoint_bbox/keypoint_bbox_detector.py` (`KeypointBoundingBoxDetector`): no change. It stays for the models whose sidecar has no `roi_source`. `skellytracker/core/detectors/keypoint_detectors/mediapipe/run_demo.py` (the hand child stage of the demo): for the implementer, when skellytracker runs the refiner. `skellytracker/core/data_primitives/keypoints.py` (`Keypoints`): no change. |

## 7. Exporter impact

| Exporter | Affected sidecars | Change | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | none from this proposal (the removal of `pose.requires_object_detector` by the 0020 proposal regenerates `rtmw-wholebody133` and `rtmo-coco17-body7`, 0020 proposal part 7). OpenMMLab-Exporter decision 0050 (local commit `f3aeb47`, user decision T39) writes no sidecar for a family while its sidecar intake is not `describes`: `rtmdet-person`, `rtmw-wholebody133` and `rtmo-coco17-body7` set `capabilities["sidecar"]` to False. Thus OpenMMLab-Exporter writes no RTMW sidecar, and regenerates none, until the RTMW intake is `describes` and a later decision sets the family back to True (0050 item 8). | none | none. With T27, an RTMW sidecar as a parent of this refiner passes the name check: its `tracked_points` have `left_wrist`, `left_pinky_finger1` and `left_forefinger1` (vector `parent-wholebody-names-accepted`; before T27 it was refused). Under option E of the visibility proposal (OpenMMLab-Exporter decision 0041 at `32ab848`), no RTMW size declares `pose.decode.visibility`. Thus every RTMW parent, at every size, fails the value check of the default gate value `visibility` (vector `parent-error-wholebody-score-only`). A run with an RTMW parent sets the runtime gate value `score` and an OpenMMLab-Exporter 0041 threshold for its size: `t_recall` (the default recommendation; it gives the Holistic gate recall) or `t_J` (the selective option, Youden) (user decision T37; part 1, table "RTMW gate thresholds"; OpenMMLab-Exporter 0041, "Thresholds"; the fp32 threshold of a size also serves its fp16 artifact) (vectors `parent-wholebody-names-accepted`, `parent-wholebody-256-gate-value-score` and `source-gate-value-override-score`). The thresholds are not a sidecar field (user decision U4), and the refiner sidecar default stays the Holistic value (`visibility`, 0.1). The hand-keypoint accuracy with a COCO-WholeBody parent is not measured (part 1, part 5). Its proposal `model-id-suffix` gets the answer to its Q1 from part 2.1 (user decision Q3 = a). That proposal already records Q1 as answered, and it already cites this file (`specs/model-sidecar/proposals/model-id-suffix/proposal.md`). Its line references into this file (its `:399-404`, "lines of 2026-10-24 11:26": "its line 34", "its lines 158-163", "lines 565-568", "lines 173-176 and 2528-2530"; and its header row "Depends on", `:19`, with the lines 34, 158-163, 565-568, 47 and 2528-2530) were stale after the edits of T26 (6), T27 and the visibility proposal. The slug is now at line 47, the folder and the id at lines 216-221, the answer to its Q1 at lines 231-234, `V-post.roi_refiner-9` at lines 725-728, and Q3 = (a) at line 60 (header) and lines 3928-3930 ("Open questions for the user") (lines of 2026-10-24 after the edits of T37 and T38). The review-readiness audit 2 (2026-10-24) corrected them in that file to the earlier lines 191-196, 206-209, 700-703 and 3856-3858. Those are stale again: the OpenMMLab-Exporter 0041 result in part 1 moved the lines after line 144 by 8, the option E edits moved the lines after part 4 again, the T37 table in part 1 moved the lines after line 150 by 17, and the T38 row in part 8 moved the lines after part 8 by 1 more. Its row at `:105` cites this file at `:256` for the 0025 item; that row is now at line 281. A session that may edit that file corrects them. |
| Roboflow-Exporter | none | none | none |
| Ultralytics-Exporter | none | none | none |
| Qualcomm-Exporter | the planned `mediapipe-hand-recrop` (the untracked hand pose export plan of Qualcomm-Exporter (plan facts), untracked; HEAD `4ca4586`) | Its plan drops the re-crop model: MediaPipe-Exporter owns it (MediaPipe-Exporter 0012). If Qualcomm-Exporter still writes it, it writes `role: [roi_refiner]` with `roi_decode`, not `pose_estimator` with two points. | none (no host decoder for the re-crop model) |
| MediaPipe-Exporter (proposing) | `mediapipe-hand-roi` (new), at `detectors/roi_refiners/mediapipe/hand/` | new sidecar with `role: [roi_refiner]`, `roi_points` and `roi_decode`. The plan path `keypoint_detectors/mediapipe/hand-recrop/` (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts)) changes. The pipeline manifest keeps only the steps outside the sidecars: the tracking ROI from the previous landmarks, the tracking choice and the presence gate of the landmark model (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts)). Its `recrop.rect_from_points` and `recrop.transform` (`:331-332`) move into `roi_decode`. By user decision T24 (2026-10-24), the ROI from pose (the pose indices, `middle`, the loose rect) and the visibility gate also move into the sidecar (`roi_source`); with Q2 = a of the 0020 proposal, its transform moves into `crop_policy.transform`. The writer must write the name lists of part 2.2 (user decision T27: the six BlazePose names first, the COCO-WholeBody 133 names second), `score_gate.value_default: visibility` (T33) and `score_gate.score_threshold_default: 0.1` (T26 (6)). The intake of the MediaPipe pose model (none yet) must use the BlazePose names, and the BlazePose sidecar must declare `pose.decode.visibility` (the visibility proposal). | The host decoder of the refiner is `decode_roi` (the reference file), with the crop ROI `Rc` from `crop_roi` and `rotated_roi_crop` of the 0020 reference file. The input `crop_policy` of the refiner sidecar holds the loose-ROI transform (part 2.2; Q2 = a of the 0020 proposal, decided by the user, T23). The probe `hand_roi_reference.py` gives the same results for the hand cases (part 4). |
| skellytracker package sidecars | none | none. They have `schema_version: "v2024.09.1019"`, and their legacy meaning does not change. | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| **The near-miss: `role: [pose_estimator]` with two keypoints** (`crop_center`, `crop_scale`, `decode: coordinate`) | It describes the tensor, but not the function. A host reads the points as keypoints of the user. The rect rule, the rotation target and the transform have no field, so they go into a pipeline manifest outside the spec. The exporter guide forbids it. The user rejected it. | `exporter-guide/sidecars/rules.md:6-8`, `exporter-guide/sidecars/workflow/mapping-hints.md:71`; MediaPipe-Exporter 0011 (rejected) and 0015 |
| **Extend 0020 only**: make the refined ROI a rule of the consumer (the ROI source of the hand landmark model) | The refiner is a model with its own ONNX file. Without a role, it has no valid sidecar (`V-common.identity-2`), so a host cannot load or run it from the catalog. Also, the landmark model gets its ROI from two sources with different transforms: the refiner (scale 1.0) and the previous landmarks (scale 2.0). One consumer `crop_policy` cannot hold both. MediaPipe applies the refiner transform inside the refinement graph. 0020 itself names "the ROI refiner gap" as a dependency. By user decision (2026-10-23), the full proposal of 0020 lands first and does not depend on the refiner (0020 proposal `:44`). | `docs/mediapipe-whole-body.md:390-399`; `0020-roi-transform-and-source.md:21-22` |
| **One proposal with 0020** (the role, the ROI, the rotated crop and the transform in one contract unit) | Rejected by **user decision (2026-10-23, Q4 = a)**: keep the two proposals separate; the 0020 proposal goes into `vNEXT` first. The reasons: the guide asks for one proposal for each contract unit (one section), and the rotated crop and its inverse are a resize method of their own. The consumer (the hand landmark model) needs the ROI and the transform without a refiner. This proposal depends on the 0020 proposal, and it has no copy of its algorithms (part 3). | `exporter-guide/sidecars/workflow/phase-2-proposal.md:3-4, 49-50`; `templates/change-proposal.md:18`; 0020 proposal `:44, 48` |
| **Keep copies of `transform_roi` and the crop inverse in this reference file** (the PROVISIONAL functions of the first draft) | Two copies of one algorithm can drift apart. The 0020 reference file is the single executable meaning of the ROI, the transform and the inverse. This file loads it (user decision T23, R1 = Q6 = a). | `exporter-guide/sidecars/reference-implementations.md:1-64` ("Reference implementations"); 0020 proposal `:596-597` |
| **Decode with the ROI that the host gave** (`R`, as the first draft did) | The model read the crop of `Rc`, not of `R`. With the input `crop_policy.transform` of part 2.2, an inverse with `R` moves the refined centre by 9.31 px (18.1 % of its size) on the case `decode-hand-from-loose-crop-roi` (part 2.3). | `docs/mediapipe-whole-body.md:112, 390-392`; 0020 proposal `:379` |
| **`object_detector` with a rotated box output** | The refiner gives no boxes, no scores and no classes. `decode.selection`, NMS and `clamp_boxes` do not apply. `BoundingBox` has no rotation. | `common/outputs.md:35`; `skellytracker/core/data_primitives/bounding_box.py` |
| **Hard-code the MediaPipe hand rule** (no `rect`, `rotation` or `transform` fields) | The fields keep the section general. A later proposal can add a face rule as a new `rect` value, with no new section. The face rule differs from the hand rule: the tight box of the points, target 0°, scale 2.0. | `docs/mediapipe-whole-body.md:391-394` and `:462-464` |
| **The rect from the points in model-input pixels, then the crop inverse of the ROI** | For `alignment_points` with a square ROI, the result is the same. A later bounds rule (the deferred face rule) is different. When the crop is rotated, the axis-aligned bounds in the crop and in the image differ. MediaPipe maps the points first. | `docs/mediapipe-whole-body.md:108-112, 392-393` |
| **The refiner folder under `keypoint_detectors/{family}/{part}/` with a stage suffix** (for example `mediapipe-hand-recrop`) | The refiner is not a keypoint detector. The proposal `model-id-suffix` gives each id under that branch a point count, and it has no token for a stage (its Q1). | OpenMMLab-Exporter `specs/model-sidecar/proposals/model-id-suffix/proposal.md` (Q1, `V-common.identity-7`, `-9`; untracked) |
| **Allow `[object_detector, roi_refiner]` now** (the Holistic face detector) | The detection outputs of the spec have no keypoints, and the face detector needs weighted NMS. Both are separate gaps (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts), secondary). The role stays alone. The user deferred the face rule (Q2 = c). | `docs/mediapipe-whole-body.md:120-134, 458-464` |
| **The face rule `points_bounds` now** (the tight box of the points and a rotation from two points, as in the Holistic face branch) | Deferred by user decision (Q2 = c, 2026-10-23) until a face model needs it. The reason is the Holistic face-detector evidence. No face model with an ROI-point output exists. In Holistic, the face ROI comes from the short-range face detector, which runs inside the loose face ROI from the pose. That detector is an SSD object detector: 896 anchors, a score threshold, weighted NMS and `num_faces = 1`. The face ROI is the tight box of its 6 detection keypoints, with the rotation from keypoint 0 to keypoint 1 at target 0°. Then scale 2.0 and `square_long` apply. When it finds no face, there is no ROI. The detector cannot use this role: it is an object detector, and the spec has no keypoints on a detection output. Thus the rule has no model to describe and no parity run. The first draft had the rule, its reference branch, its rules and four vectors. They are removed. | `docs/mediapipe-whole-body.md:120-134, 201, 445-471` |
| **Keep the loose-ROI rule outside the sidecar** (0020 `:18-19`; the first form of this proposal and of the 0020 proposal) | Rejected by user decision T24 (2026-10-24). Without the rule, a host cannot run the refiner from the sidecars alone: it needs the pose indices, `middle`, the rect rule and the gate from a pipeline manifest or from code. The spec cannot check them. | `docs/mediapipe-whole-body.md:381-389`; the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts) (secondary, the manifest form); `keypoint_bbox_detector.py:53-70` |
| **A second rect rule for the loose ROI** (centre at the end point, rotation from the start point to the end point, as `HandDetectionsFromPoseToRectsCalculator` writes it) | Not needed. The rule `alignment_points` of `roi_decode` with start `middle`, end `wrist` and target −90° gives the same ROI. The vectors `source-upstream-*` prove it within `1e-9` px and `1e-12` rad (expected values from the upstream formula), and a sweep of 200,000 hands within `2.9e-14` px and `8.9e-16` rad modulo 2π (part 2.3). One rule has one implementation and one set of vectors. | part 2.3, notes on "ROI source"; part 4 |
| **Point indices** (`wrist: 15`, as the manifest of the conversion plan writes them) | Rejected by user decision T24: names, so that the host can check the parent and refuse a parent without the points. An index has a meaning only for one model: index 15 is `left_wrist` in BlazePose-33 (`pose_topology.h:37`) and `left_ankle` in COCO-WholeBody (OpenMMLab-Exporter `rtmw/keypoints.py:28` at `d0f4343`, the same at `32ab848`). A name check catches a wrong parent at load time (vector `parent-error-no-accepted-name`; the earlier id `parent-error-wholebody-names` is now `parent-wholebody-names-accepted`, T27). | the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts) (secondary); `post/pose-schema.md:58-60` |
| **Canonical names, or both the parent names and the canonical names** | Rejected as the key (unchanged by T27). No canonical body name exists for the BlazePose pinky and index points (part 2.2, "The point names"). The canonical hand names `index_finger_mcp` and `pinky_mcp` name the same joints as BlazePose 19 and 17 and as COCO-WholeBody `forefinger1` and `pinky_finger1` (`docs/mediapipe-whole-body.md:372`; `rtmw_wholebody_to_canonical_mapping.yaml:23, 35`), but no exporter writes `canonical_mapping`, and the spec maps no body point to a hand name. The canonical names are optional in a sidecar and will change to the VRM 1.0 names. | `post/canonical-mapping.md:80-85, 99`; `mediapipe_body_to_canonical_mapping.yaml:17-48` |
| **The derived point in the parent sidecar** (`pose.derived_points` of the BlazePose sidecar, `middle: {left_index: 2, left_pinky: 1}`) | `pose.derived_points` serves the skeleton edges of the parent (`post/pose-schema.md:73-75`). The point `middle` is a rule of the refiner, not of the pose model: another refiner can need another point from the same parent. Also, the canonical weighted form drops missing points (`post/canonical-mapping.md:51`); the ROI source must give no ROI then. The ROI source uses the same weighted form, with its own missing-point rule. | `post/pose-schema.md:73-83`; `post/canonical-mapping.md:51` |
| **No range rule for the threshold of a `visibility` gate** (any finite number) | A value `>= 1` never passes a visibility in `[0, 1]`, and a negative value always passes. Such a value is an authoring error. (Proposal choice.) A `score` gate has no range rule, because a SimCC score has no fixed range (the visibility proposal, part 2.8, item 4). | `skellytracker/core/data_primitives/keypoints.py:19` |
| **A fixed threshold in the sidecar** (`min_score: 0.1`, the first form of this proposal) | Rejected by user decision T26 (6) (2026-10-24): the threshold is a runtime input with a default in the sidecar. Holistic fixes 0.1 in the graph (`holistic_hand_tracking.cc:91`), but another parent can need another value, and a test must be able to set it without a new sidecar. The form follows `decode.confidence_threshold_default`. | `post/detection-decode.md:42`; the untracked pose-models plan of OpenMMLab-Exporter (plan facts), T26 (6) (secondary) |
| **One parent name for each point** (the form before T27) | Rejected by user decision T27 (2026-10-24): it refuses every COCO-WholeBody parent, so the user cannot test RTMW, DWPose or ViTPose++ as the parent. The lists keep the name check: a parent with none of the names of a list is still refused. | `rtmw/keypoints.py:104-142` of OpenMMLab-Exporter (`d0f4343`; the same at `32ab848`); the untracked pose-models plan of OpenMMLab-Exporter (plan facts), T27 (secondary) |
| **A default for `score_gate.value`** (`score`) | A default `score` makes the Holistic gate read a value that BlazePose does not give, and `score` and `visibility` have other scales. (The visibility proposal, part 2.8, item 3; a proposal choice there.) User decision T33 keeps the point: the sidecar default is `value_default: visibility` for the hand, and a run can set `score`. | the visibility proposal, part 1 before the rewrite for E (RTMW x 384x288: score p50 7.56, visibility p50 0.974; scratch) |
| **A fixed gate value in the sidecar** (`score_gate.value` with no runtime value, the form before T33) | Rejected by user decision T33 (2026-10-24): one refiner sidecar must serve BlazePose parents (`visibility`) and RTMW parents (`score`; under option E, OpenMMLab-Exporter 0041, no RTMW size gives a visibility). | the untracked pose-models plan of OpenMMLab-Exporter (plan facts), T33 (secondary) |
| **Skip the gate when the parent gives no value for it** (Q8 (c)) | Rejected by user decision T34 (2026-10-24). It runs the refiner on hands that the gate drops, with no message. The host refuses the parent instead (rule `-15`). | the untracked pose-models plan of OpenMMLab-Exporter (plan facts), T34 (secondary) |
| **A gate value from the decode method** (the parent check looks only at the decode method) | One decode can give two values (heading "Per-point values": a decode gives `visibility` only when the sidecar declares `pose.decode.visibility`). Under option E (OpenMMLab-Exporter 0041), an RTMW parent gives only `score` at every size, a BlazePose parent gives only `visibility`, and no current parent gives both. The gate must name the value it reads. | the visibility proposal, heading "Per-point values" |
| **A gate on the mean score of several parent points** (`s_h`: the mean RTMW `score` of the 21 hand points of one side) | Not added now (user decision T38). OpenMMLab-Exporter 0041 measured it as an option: `s_h` ranks valid hands (`*hand_valid`) better than the body-wrist score `s_w` at every RTMW size (AUC, common set, fp32: m 0.852 against 0.817, l-256 0.858 against 0.813, x-256 0.858 against 0.838, l-384 0.883 against 0.822, x-384 0.882 against 0.840). The reasons: `score_gate` reads one point (`score_gate.point`), so a gate on several points is a spec change of `roi_source.score_gate`. OpenMMLab-Exporter 0041 measured no threshold for `s_h`. A BlazePose parent has no hand points, so the Holistic gate cannot use it. It is a possible later extension, with its own thresholds, in a later proposal. | OpenMMLab-Exporter `notes/decisions/0041-rtmw-wrist-gate.md` (table "Ranking", column `s_h`; "Observations"); user decision T38 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary) |

Where this proposal differs from 0020: 0020 says "The rule that computes the ROI from the keypoints
stays outside the sidecar" (`0020-roi-transform-and-source.md:18-19`). That sentence is about the ROI
from another model's keypoints (pose to hand). This proposal differs from it in two places. (1) The
rect rule of the refiner is inside the refiner sidecar, because the rule is the decode of the
refiner's own output (`docs/mediapipe-whole-body.md:391-394`). (2) **User decision (2026-10-24,
T24):** the rule that makes the loose ROI from the body pose is inside the refiner sidecar too
(`roi_source`). The reason: without it, the sidecars are not enough to run the model. A host that
has the refiner sidecar and a body-pose sidecar must still get the pose indices, the derived point,
the rect rule and the gate from somewhere else (a pipeline manifest, or code such as the
`KeypointBoundingBoxDetector` configuration of the skellytracker demo), and the spec cannot check
them (the reason of 0020 itself, `0020-roi-transform-and-source.md:41-42`). The full proposal of
0020 keeps the 0020 line for its own section: `rotated_roi_crop` does not say how the host makes the
ROI. Its heading "ROI source" names an ROI refiner as one source of an ROI (0020 proposal
`:315-323`). Thus the rule is in the sidecar of the model that consumes the loose ROI, not in the
crop section. The decision is taken, so this file has no open question for it.

**Not proposed: the tracking ROI and the ROI choice** (user decision T24). These steps stay outside
the sidecars, as host tracking policy:

- The ROI from the previous hand landmarks: `HandLandmarksToRectCalculator` with the 12-point palm
  subset, the rotation to the MCP joints, a tight box, then `shift_y` −0.1, `square_long`, scale 2.0
  (`docs/mediapipe-whole-body.md:395-399`; MediaPipe-Exporter 0005).
- The ROI choice: `RoiTrackingCalculator` keeps the previous-landmark ROI only when the rotation, the
  offsets, the size differences and the landmark margin are inside its limits
  (`docs/mediapipe-whole-body.md:400-403`; `holistic_hand_tracking.cc:128-160` at `e9794ef`, [C 4.2-g]
  of MediaPipe-Exporter 0021).
- The reason: both use an earlier frame. The exporter guide calls "a choice that uses an earlier
  frame" `out of scope` (`specs/exporter-guide/sidecars/workflow/phase-1-intake.md:36-38` at `dom/21-move-sidecar-guide`). This proposal keeps
  that example (part 2.1). They change the result: in MediaPipe-Exporter 0006 the reference keeps the
  previous-frame ROI for 136 of 438 video hand-frames (`0006-holistic-end-to-end-parity.md:54`), and
  one keep decision gives the 17 px outlier of the parity gate (part 5, gate (2)).
- Also outside: the smoothing of the pose landmarks before the hand branch
  (`docs/mediapipe-whole-body.md:382-383`), and the next-frame state when the gate fails (`:385-386`).
  A known gap for a later proposal, if the user wants the sidecars to describe tracking.

Where this proposal differs from the full proposal of 0020: the heading "ROI" of that proposal does
not limit the range of the rotation (`:310-311`). This section states the range `[-pi, pi)` for its
own output only, because its step 3 computes a rotation. That heading allows it: "A section that
computes a rotation states the range of its result" (`:310-311`).

## Open questions for the user

Decided by the user on 2026-10-23:

- **Q1 = (a).** The change goes into `vNEXT`. The `vNEXT` scope of skellytracker 0008 must add
  MediaPipe-Exporter (parts 2.1 and 2.6).
- **Q2 = (c).** The face rule `points_bounds` is deferred until a face model needs it (parts 1 and 8).
- **Q3 = (a).** `detectors/roi_refiners/{family}/{part}/` with `{family}-{part}-roi[-{variant}]`, for
  example `mediapipe-hand-roi` (part 2.1). It answers the pipeline-stage question Q1 of the
  OpenMMLab-Exporter proposal `model-id-suffix`.
- **Q4 = (a).** Keep this proposal separate from the full proposal of skellytracker 0020
  (`specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`). The 0020 proposal goes into `vNEXT` before
  this one. The dependency is one-way: this proposal depends on the 0020 proposal (Header, "Depends
  on"; parts 2, 3, 4 and 8).
- **Q5 = (a).** An ROI with a width or a height of 0 or less gives "no ROI" (part 2.3, step 5). The
  test for finite values in the same step comes from the validity test of the 0020 proposal.
  Q5 = (a) answers the `w` and `h` part of Q9 of the 0020 proposal (`:1828-1830`).

Decided by the user on 2026-10-24 (T23, T24, T26 (6), T27, T28 (H1, H6), T31, T33, T34, T37 and T38 of the untracked pose-models plan of OpenMMLab-Exporter (plan facts)):

- **Q6 (R1 in T23) = (a).** This reference file loads the 0020 reference file by its path, with the
  loader `_load_rotated_roi_crop`. It has no copy of its functions. This was the proposal choice. The
  guide says "Do not import from the exporter or from skellytracker" (`exporter-guide/sidecars/reference-implementations.md:45`;
  `templates/change-proposal.md:193-194`). The decision reads that rule as a rule about exporter code
  and package code, not about another file in `specs/model-sidecar/reference/`.
- **Q7 (R2 in T23) = (a).** A normative clamp after the formula keeps the rotation exactly in
  `[-pi, pi)`, and the vectors compare the rotation with no period. This was the proposal choice.
- **T24 (new).** The refiner sidecar declares how the host makes the loose hand ROI from the body
  pose: `roi_source` (parts 2.2, 2.3, 2.4, 3, 4, 5 and 6). The tracking ROI and the ROI choice stay
  outside (part 8, "Not proposed"). The names are the `tracked_points` names of the parent (part
  2.2, "The point names"; proposal choice, from T24). The rect rule is the rule of `roi_decode`
  (proved by the vectors `source-upstream-*`).
- **T26 (6) (new).** The threshold of `roi_source.score_gate` is a runtime input of the host or the
  user, with the default `score_gate.score_threshold_default` in the sidecar. The hand default is
  the Holistic value 0.1 (`holistic_hand_tracking.cc:91`). The comparison stays strict (parts 2.2,
  2.3, 2.4 rules `-14` and `-16`, 3, 4).
- **T27 (new).** Each local point of `roi_source.instances[].points` takes an ordered list of
  accepted parent names. The host uses the first name that the parent has. The hand lists name the
  BlazePose point first and the COCO-WholeBody 133 point second (part 2.2). The hand-keypoint accuracy with the COCO-WholeBody names
  is not measured (parts 1 and 5). The gate value of an RTMW parent is measured: `score` (OpenMMLab-Exporter 0041 at `32ab848`).
- **T28 (H1) (new).** The pinky and index lists get a third name: the spelling of the skellytracker
  spec example (`left_hand_pinky_finger1`, `left_hand_forefinger1`, and the right side). The wrist
  list keeps two names, because the example spells the wrist and the hand root as mmpose does (part
  2.2). This closes the item "the coco133 names of the spec example" of Q8 with option (ii). The
  vectors `parent-example-names-accepted`, `source-alias-third-name-example` and
  `source-alias-second-before-third` test it. The refusal cases `parent-error-no-accepted-name` and
  `source-error-no-accepted-name` now use names that are in no list (part 4).
- **T28 (H6) (new).** One parity script serves the four MediaPipe proposals:
  `notes/decisions/scripts/hand_chain_parity.py` (part 5). Each proposal keeps its gates.
- **T33 (new).** The gate value is a runtime input of the host or the user, with the default
  `score_gate.value_default` in the sidecar (the hand: `visibility`, Holistic). The threshold range
  follows the gate value in effect. A runtime gate value other than `value_default` needs a runtime
  threshold (proposal choice; decided by the user, T35, Q13 (a)). The parent check uses the gate value in effect and the parent size in
  use (parts 1, 2.2, 2.3, 2.4 rules `-14` to `-16`, 3, 4, 6, 7 and 8). T33 took the interim V1 = A1
  of the visibility proposal. The measured result (OpenMMLab-Exporter 0041 at `32ab848`) replaces A1 with option E: an RTMW parent gives `score` at every size and no `visibility`. T33 does not change.
- **T34 (new).** Q8 (c) is rejected: when the parent, at the size in use, gives no value for the
  gate value in effect, the host refuses the parent with a message. It never skips the gate (part
  2.3, heading "ROI source"; rule `-15`; Q8 below).
- **T37 (new).** The proposals give both RTMW gate thresholds of OpenMMLab-Exporter 0041 for each
  size. `t_recall` is the default recommendation: it gives the Holistic gate recall. `t_J` (Youden)
  is the selective option. Neither goes into the sidecar (U4) (part 1, table "RTMW gate
  thresholds"; parts 2.3 notes, 5 and 7).
- **T38 (new).** The hand-mean gate value `s_h` of OpenMMLab-Exporter 0041 is only a measured option in part 8
  (alternatives). The spec does not change now.
- **From the visibility proposal (its part 2.8; not a user decision; T33 supersedes its "no
  default").** `score_gate.value` (`score`
  or `visibility`, no default), the threshold range for each value, and the parent check of the
  named value (parts 2.2 to 4, 6 and 8).

The questions of the 0020 proposal that changed this proposal are decided too (user, 2026-10-24;
0020 proposal, "Open questions for the user"): Q1 (a) `rotated_roi_crop`, the name in
`V-post.roi_refiner-8`, part 2.2 and the reference file; Q2 (a) the loose-ROI transform in the
`crop_policy.transform` of the refiner input (part 2.2); Q3: `pose.requires_object_detector` is
removed (T22 (1)), so the 0020 heading "ROI source" no longer names it (part 2.1); Q4: `border_mode`
and `maintain_aspect_ratio` are required, so the excerpt keeps `border_mode: replicate`; Q5: one
`scale` in `roi_decode.transform`; Q6: the exact inverse (step 2); Q7 = (c): no precision in the
text, and the tolerances in the vectors (the float64 sentence of part 2.3 is removed; part 4); Q9:
an ROI with a NaN or an infinite value gives "no ROI" (step 5).

Decided in full on 2026-10-24 (T31 and T34 of the untracked pose-models plan of OpenMMLab-Exporter (plan facts)):

- **Q8. How strictly the host checks the parent of `roi_source`** (new on 2026-10-24; changed by
  user decisions T27 and T28 (H1) and by the visibility proposal). **Decided: option (a).** The host
  checks the names through the lists of T27 and T28 (H1) (the first name that the parent has; a
  parent with none of the names of a list is refused), and it checks that the parent, at the size
  in use, gives the per-point value of the gate value in effect (the runtime gate value, else
  `score_gate.value_default`; user decision T33; rule `V-post.roi_refiner-15`). A parent with the
  same names and other meanings still passes. (b) is rejected (user decision T31). (c) is rejected
  (user decision T34): the host refuses such a parent with a message, and it never skips the gate.
  The record of the options:
  - (b) A field `roi_source.parent_landmark_schema` (for example `MediaPipe_Pose`) that must equal
    the `pose.landmark_schema` of the parent. `pose.landmark_schema` is optional today
    (`post/pose-schema.md:38`), so a parent without it is refused. The conversion plan writes
    `landmark_schema: BlazePose33` for the pose input (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts),
    secondary). The tracker file of the skellytracker MediaPipe body detector (package code, not a
    sidecar) writes `MediaPipe_Pose`
    (`skellytracker/core/detectors/keypoint_detectors/mediapipe/body/mediapipe_body.yaml:6`). With
    T27, one schema value refuses the COCO-WholeBody parents that T27 accepts. Thus (b) works
    against the goal of T27, unless the field takes a list. **Rejected (user decision T31):** the
    host does not require a parent `landmark_schema`.
  - (c) No value check: with a parent that does not give the named value, the host skips the gate.
    This runs the refiner on hands that Holistic drops. With the visibility proposal, a BlazePose
    parent can give the visibility, so (c) is not needed for the Holistic case. **Rejected (user
    decision T34):** the host refuses the parent (heading "ROI source", "The parent"; vectors
    `parent-error-no-point-scores`, `parent-error-wholebody-score-only`,
    `parent-error-wholebody-256-gate-value-visibility`, and `source-error-gate-value-missing` for
    the run-time form).
  - The item "the coco133 names of the skellytracker spec example" is decided: user decision T28
    (H1) chose option (ii), a third name in the pinky and index lists (above).

Decided on 2026-10-24 (T35 of the untracked pose-models plan of OpenMMLab-Exporter (plan facts)):

- **Q13. A runtime gate value with no runtime threshold** (new with T33). (The number is after Q12,
  so that it does not repeat a number of the 0020 questions that this file names.) **Decided (user,
  T35, 2026-10-24): option (a).** A runtime gate value other than `value_default` needs a runtime
  threshold. When a run sets such a gate value and no threshold, the host refuses the run values.
  Rule `V-post.roi_refiner-16` already says so, and the vector
  `source-error-gate-value-override-no-threshold` tests it. The text and the vectors agree, so they
  do not change. The reason: the default threshold is tuned for `value_default`, and the RTMW score
  scale differs by size (part 2.3, notes). Option (b) is rejected: the host does not use
  `score_threshold_default` with the range of the gate value in effect. (a) was the proposal
  choice.

Still open: none.

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake links to this proposal. Done on 2026-10-24:
      the untracked intake of `mediapipe-hand-roi` of MediaPipe-Exporter (plan facts) links it in its table "Proposals and reference
      files".
- [x] The header gives the dependencies, or `none`: the full proposal of 0020 (user decision
      Q4 = a: it lands first). The OpenMMLab-Exporter proposal `model-id-suffix` is related, not a
      dependency (Header, "Depends on").
- [x] The header names each `proposed` skellytracker decision entry that covers the same property
      (0020, 0025, 0021, 0017). This proposal builds on 0020 and on its full proposal. It does not
      compete with them. Part 8 says where it differs from 0020 `:18-19` (T24) and why.
- [x] Part 1 cites primary evidence (`docs/mediapipe-whole-body.md`, by user designation, the
      MediaPipe source for the loose ROI and the gate, and the ONNX graph read), and it names the
      primary evidence that is missing (no real Holistic case in the 0006 data; no spec field for the
      BlazePose visibility).
- [x] Part 2.1 lists each place that the change edits, with the changed rule
      `V-pre.resize.rotated_roi_crop-1`, the heading "ROI source" of the 0020 proposal (the sentence
      after T22 (1)), `pose.tracked_points`, and the start of the runtime contract and the
      `out of scope` examples in the exporter guide and the intake template (T24).
- [x] Part 2.2 has the fields of `roi_source`, and the reason for the point names.
- [x] Part 2.4 has the rules `V-post.roi_refiner-10` to `-16` (unknown names, the name lists of
      T27, a name missing in the parent, the weights, the named gate value, the threshold range for
      each value, the runtime threshold of T26 (6)), and the changed `-1` and `-2`.
- [x] Part 3 names the reference file, and the file exists in the untracked plans of MediaPipe-Exporter (plan facts). It has no PROVISIONAL
      function. It loads the part 3 code of `specs/model-sidecar/proposals/roi-transform-and-source/proposal.md` by its path (R1).
      `roi_from_keypoints` uses `rect_from_points`: one rect rule.
- [x] Part 4 gives `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a for pixel images: no case uses an
      image. Every precision-dependent case has its tolerance (`1e-3` px, `1e-6` rad; Q7 = c).
- [x] Part 4 uses only the case keys of the template. Notes are YAML comment lines.
- [x] The vectors were run again on 2026-10-24 after the option E edits (OpenMMLab-Exporter 0041): 125 of 125 pass, also after the edits of items 11 and 12 of part 2.8 of the visibility proposal (the citations and the `check_parent` docstring). Run again on 2026-10-25 after the re-pin to skellytracker `dom/21-move-sidecar-guide` and the repo-name edits: 125 of 125 pass (no case changed).
      The E mutation copy gives 124 of 125, the E control that ignores every runtime gate value gives 111 of 125,
      and the E control with the last accepted name gives 119 of 125 (part 4). After T33: 125 of 125 pass. The mutation copy gives
      124 of 125 (only the changed case fails). The control that ignores the runtime gate value
      gives 119 of 125 (part 4). Before T33, after T28 (H1): 113 of 113 pass (110 of 110 after
      T26 (6), T27 and the named gate value; 90 of 90 before, 47 of 47 before the 43 cases of T24). Mutation check: one changed
      expected value gave 112 of 113, and only that case failed (109 of 110 before T28 (H1)). Three controls with one changed
      line of the reference file fail the cases of their change (part 4). A control with the other
      rect form fails the three `source-upstream-*` cases.
- [x] Part 5 says `to run` and describes the script. The script is shared with the other three
      MediaPipe proposals (user decision T28 (H6)).
      The gates are set before the run (2026-10-24): the decode alone, the final outputs (median,
      p95, outlier count), the loose ROI from the body pose (new), and the export error.
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed. n/a: the result is
      `to run`.
- [x] The user decisions of 2026-10-23 (Q1 to Q5) and of 2026-10-24 (R1 = Q6, R2 = Q7, T24, T26 (6),
      T27, T28 (H1, H6), T31, T33, T34, T35, T37, T38, and the 0020 decisions T22, T23 and Q7 = c) are applied in
      the header and in parts 1 to 8.
      The edits of part 2.8 of the visibility proposal are applied. Q8 is decided in full ((a) with
      T27, T28 (H1) and the visibility proposal; (b) rejected, T31; (c) rejected, T34). Q13 is
      decided: (a), user decision T35. No question stays open.
- [x] The items of the list "What the refiner proposal had to change" of the 0020 proposal
      (`:1676-1745`) are applied (items 1 to 16). Item 7 names `V-post.pose.schema-2`; after
      T22 (1) the 0020 proposal changes that rule and two more (part 2.4).
- [x] Stale line numbers into the 0020 proposal: updated to its lines of 2026-10-24. The
      OpenMMLab-Exporter proposal `model-id-suffix` cites this file with the lines of 2026-10-23
      (its `:19` and `:399-404`, lines of 2026-10-24 11:26). Those lines moved again on 2026-10-24
      (the slug is now at line 47; part 7, the row OpenMMLab-Exporter, gives the new lines). A
      session that may edit that file corrects them. The citations of this file into the 0020
      proposal were checked against its current lines on 2026-10-24 (after T26 (6) and T27). The 0020 proposal cites this file with lines before the OpenMMLab-Exporter 0041 result (2026-10-24): its `:45` gives `:855-858` (now 880-883, after the edits of T37 and T38) and `:4018-4020` (now 4098-4100), and its `:1764` gives `:274` (now 299). Its list "What the refiner proposal had to change" (`:1676-1745`) cites the lines of the first draft, as a past record. A session that may edit that file corrects them.
- [x] No file in skellytracker changed.

This proposal has `to run` in part 5. A skellytracker session can record it. It is not ready for the
user to accept.

## Before acceptance

This list gives the work that must be done before the user can accept the proposal. The proposal
itself says: "It is not ready for the user to accept."

**Parts**

- [ ] Part 5 is `to run`. The parity script `notes/decisions/scripts/hand_chain_parity.py` of
  MediaPipe-Exporter does not exist. One script serves this proposal, `roi-transform-and-source`,
  `landmark-extra-outputs` and `landmark-depth-divisor`. The exporter must write the script, run the
  gates (1) to (4) and record the results.
- [ ] Part 2.1 does not list each place that the change edits. Add these places:
  - `tools/make_vectors.py` and `tools/tests/test_vectors.py`. The vector file cannot land without
    them.
  - The new folder `specs/model-sidecar/reference/`. It does not exist yet. CI lints it with ruff when it
    exists.
  - A `roi_source` row in the table "Contract part | Where it lives" of
    `specs/model-sidecar/common/sizes-and-artifacts.md:49-54`. Part 2.1 adds a row only for `roi_decode`.
    `roi_source` is also a required top-level block (`V-post.roi_refiner-1`).
  - `specs/exporter-guide/sidecars/reference-implementations.md:45-46` ("Do not import from the
    exporter or from skellytracker"). The sibling load of user decision R1 reads this rule in a new
    way.
  - The parity comparisons by role. `specs/exporter-guide/sidecars/workflow/parity.md:33-40` and
    `specs/model-sidecar/templates/change-proposal.md:276` compare only the boxes of `object_detector`
    and the keypoints of `pose_estimator`. They have no ROI comparison for `roi_refiner`.
  - `specs/model-sidecar/templates/model-intake.md`: the validation rows by role (`:445-449`) and the
    parity rows by role (`:505-509`) have no `roi_refiner` row. The "not used" instructions (`:283`,
    `:307`) do not cover a refiner. Row K1 (`:311`) names `requires_object_detector`, which
    `roi-transform-and-source` removes.
  - The heading "Per-point values" of `specs/model-sidecar/post/pose-visibility.md` (new in
    `keypoint-visibility`), as a merge point.
  - Optional: the word "re-crop" in `specs/model-sidecar/common/input.md:103`, and a `post.roi_refiner`
    row in `EXPECTED_APPLICABILITY` of `tools/tests/test_traceability.py`.
- [ ] The inventory edit of part 2.1 changes only the notes and the key of
  `mediapipe-hand-recrop@mediapipe-exporter`. The `plan` field of the two entries
  (`specs/model-sidecar/inventory.yaml:117` and `:125`) names a MediaPipe-Exporter plan file that
  MediaPipe-Exporter moved to its archive. The edit must also change the `plan` field.
  `tools/tests/test_traceability.py` requires that field.
- [ ] Rule `V-post.roi_refiner-14` writes the range of `score_threshold_default` as `0 <= v < 1`.
  The fields table uses `v` for the gate value and `t` for the threshold. Rule `-16` uses `t`. The
  exporter must correct the rule. The landing session must not correct normative text.
- [ ] The docstring of the part 3 code has stale text. It calls the loader `_load_rotated_roi_crop`
  a "proposal choice" (Q6), but Q6 = (a) is the user decision T23, R1. It also cites a scratch
  runner and the probe `notes/decisions/scripts/hand_roi_reference.py`, which has no commit. The
  exporter must correct the docstring before the file goes to
  `specs/model-sidecar/reference/post_roi_refiner.py`.
- [ ] The item on the dependencies in "Before you stop" names only `roi-transform-and-source` and
  `model-id-suffix`. The header also names `keypoint-visibility` as dependency (2). The two texts
  must agree.
- [ ] Part 7 calls the OpenMMLab-Exporter 0050 commit `f3aeb47` a "local commit". That commit is now
  on the default branch of OpenMMLab-Exporter. Part 7 also keeps line numbers of the
  `model-id-suffix` file. These line numbers change again with each edit of that file.

**Evidence**

- [ ] The rule of `roi_decode` (the refined ROI, the target −90° and the transform) has only one
  primary source: `docs/mediapipe-whole-body.md` of MediaPipe-Exporter. That file is exporter notes.
  A user designation makes it primary, but `specs/exporter-guide/sidecars/rules.md:9-11` classes
  exporter notes as secondary. MediaPipe-Exporter has no git repo, so no permalink can cite the
  file. The `roi_source` facts cite MediaPipe source at commit
  `e9794ef55e2509c09aa8b6ba1764b797db8eb200`. A permalink can cite them when that commit is on the
  default branch of MediaPipe.
- [ ] The read of the ONNX graph of `hand_roi_refinement.onnx` gives no command.
  `specs/exporter-guide/sidecars/rules.md:9-11` asks for the command and the node or tensor name.
- [ ] No upstream output of the refined ROI or of the loose ROI exists. Gate (2) compares only the
  hand landmarks.
- [ ] No real Holistic case exists for the `roi_source` vectors. They use synthetic points.
- [ ] The hand-keypoint accuracy with a COCO-WholeBody parent is not measured. The loose rect on
  COCO-WholeBody points, a person-detector crop and video are not measured either.
- [ ] The export error of 1.1e-4 px (MediaPipe-Exporter 0016), the 9.31 px of the decode with `R`
  and the 0.0151 px of the refined ROIs come from uncommitted scripts. They are not evidence.
- [ ] The second names of the lists come from `rtmw/keypoints.py` of OpenMMLab-Exporter. Nobody read
  the mmpose dataset info `coco_wholebody.py`.
- [ ] Only the session of `roi-transform-and-source` read what MediaPipe `ValidateRoi` does with an
  ROI of size 0.
- [ ] The header pins the spec text at one stack branch (`dom/18-agents-adr-bootstrap-kit`) and the
  guide at another (`dom/21-move-sidecar-guide`). Neither is on `development`. Read the cited lines
  again at one commit on `development`. On the working branch, the 0025 item of
  `notes/decisions/open-work.md` is at lines 130-136, not 125-131. The "Path" bullets of
  `specs/exporter-guide/sidecars/sidecar-files.md` are at lines 38-43, not 34-43.

**Template checklist**

- [ ] "Part 2.1 lists each place that the change edits" fails (see **Parts**).
- [ ] "The header gives the dependencies" is not consistent. The header says that the refiner
  section "can land first", before `keypoint-visibility`. But the "ROI source" text and rule `-15`
  use the heading "Per-point values" of `post.pose.visibility`. That section defines `visibility`.
  The note of rule `-15` ("each size of a parent gives the same values") also depends on option E
  of that proposal.
- [ ] "Part 1 cites primary evidence" passes only through the user designation of exporter notes
  (see **Evidence**).
- [ ] "Part 4 uses only the case keys of the template" is true for the template. But
  `tools/tests/test_vectors.py` refuses the keys `function` and `compare` (see **Vectors and
  tooling**).
- [ ] "If the result of part 5 is `pass` or `fail`, the parity script is committed" cannot pass
  while MediaPipe-Exporter has no git repo.

**Vectors and tooling**

- [ ] The 125 cases use the form of the template: `function`, `compare` with an `atol` for each
  field, error expects, and a `generated_by` that names the reference file.
  `tools/tests/test_vectors.py` refuses `function` and `compare`. It requires one scalar
  `tolerance` when `expect` has a fraction, `generated_by: tools/make_vectors.py`, a file equal to
  the output of `tools/make_vectors.py`, and a file size below 16 KiB. The YAML block of part 4 is
  about 121.6 KB. Decide the vector form one time for all proposals. Then change the tools or
  convert the cases.
- [ ] The map from a case to a function call is only in an uncommitted runner of the exporter. For
  example, `target_size` becomes the argument `target_hw`, `roi` and `rotation` come from one
  5-tuple, and an expect is `valid: true` or `error: <message>`. skellytracker has no runner that
  calls a function by its name. Without one, the result "125 of 125" cannot be repeated in tracked
  code.
- [ ] The vectors are `unverified`. The probe that gives the same hand results is in the same
  exporter, and it has no commit.
- [ ] The part 3 code loads the part 3 code of `roi-transform-and-source` as a sibling file. Decide
  how `tools/make_vectors.py` and the tests import the files of `specs/model-sidecar/reference/`.

**Decisions for the user**

- [ ] Gap record [0020](../../decisions/0020-roi-transform-and-source.md) (proposed)
  says: "The rule that computes the ROI from the keypoints stays outside the sidecar." `roi_source`
  (user decision T24) puts that rule in the refiner sidecar. Decide if the completion of 0020
  changes that sentence. Decide if this entry can contradict it.
- [ ] One contract unit: the section holds two algorithms, `roi_decode` and `roi_source`. Decide if
  `roi_source` must be its own section or its own proposal.
- [ ] Accepted entry [0014](../../../../decisions/0014-spec-lifecycle.md) says: "Do not
  describe an ROI refiner as a pose estimator with two fake keypoints. It is a `gap`." This text is
  stale after the landing, and the body of an accepted entry cannot change. Decide: supersede 0014
  in full, add an open-work note, or keep it. The proposal `omitted-upstream-output`
  ([0044](../../decisions/0044-omitted-upstream-output.md)) also supersedes 0014 in full
  on acceptance. Its draft restatement of 0014 keeps this sentence. The two proposals must agree on
  the text.
- [ ] Decide if a reference file can load another reference file (user decision R1), against
  "Do not import from the exporter or from skellytracker" and one section for each module. Decide
  if the guide gets a sentence in the same PR.
- [ ] Decide if `docs/mediapipe-whole-body.md` is primary evidence in tracked text. Decide how
  tracked text cites MediaPipe-Exporter decisions 0006, 0011, 0012, 0015, 0016 and 0021 and the
  MediaPipe-Exporter scripts with no permalink.
- [ ] Confirm the user decisions that exist only in untracked exporter files: Q1 to Q5 of this
  proposal (2026-10-23); T22 to T39 and U4 of the untracked pose-models plan of OpenMMLab-Exporter;
  Q1 to Q10 of `roi-transform-and-source`.
- [ ] Decide if MediaPipe-Exporter must get a git repo before acceptance.
- [ ] Scope. Decision [0008](../../decisions/0008-vnext-scope.md) (accepted) does not
  include MediaPipe-Exporter. The scope entry of `roi-transform-and-source` adds the hand landmark
  model and the hand ROI refinement model, but not BlazePose. The default gate value of this
  proposal is the BlazePose `visibility` of `keypoint-visibility`. Decide how the scope covers
  BlazePose: a third scope change, a longer scope entry, or a later `keypoint-visibility`.
- [ ] Confirm the landing order: `roi-transform-and-source` (with its scope entry), then
  `keypoint-visibility`, then this proposal.
- [ ] Decide if the entry gets a `**Depends on:**` line, and its form for MediaPipe-Exporter, which
  has no permalinks.
- [ ] The new section has a heading "Legacy behaviour", but the proposal adds no link to the list
  "Version-aware compatibility" of `specs/model-sidecar/format/versioning.md`. It follows
  `pre.resize.fit`. The skill `change-sidecar-spec` requires the link. Decide one rule for all
  proposals.
- [ ] Decide if `mediapipe-hand-recrop@qualcomm-exporter` keeps its key or also becomes
  `mediapipe-hand-roi@qualcomm-exporter`.
- [ ] Decide if tracked text can give the file name of the parity video. The file is in the public
  test recording that `skellytracker/tests/conftest.py` downloads. Its name has the letters `jsm`,
  which can be initials.

**Merge points**

- [ ] Other proposals edit the same text. The content PR that lands second rebases on the first and
  keeps the edits of both:
  - `specs/model-sidecar/common/outputs.md:29, 35, 44`: `landmark-extra-outputs`.
  - `specs/model-sidecar/format/versioning.md:74` (the legacy row): `pose-decode-flip-test`,
    `heatmap-decode-refinement`, `keypoint-visibility`, `roi-transform-and-source`,
    `landmark-extra-outputs`, `landmark-depth-divisor`.
  - `specs/model-sidecar/post/unprojection.md:21-36`: `roi-transform-and-source`,
    `landmark-depth-divisor`.
  - `specs/model-sidecar/common/identity.md` and `specs/model-sidecar/format/file-layout.md` (the storage tree,
    the branch table and the authoring guidance): `model-id-suffix`, `size-codes`.
  - `specs/model-sidecar/common/sizes-and-artifacts.md`: `roi-transform-and-source`, `size-codes` and
    `model-id-suffix` edit other lines of the same file.
  - The section map and the validation index of `specs/model-sidecar/README.md`: `keypoint-visibility`,
    `pose-decode-flip-test`, `landmark-extra-outputs`, `size-codes`, `roi-transform-and-source`.
    `tools/tests/test_traceability.py` checks the order.
  - `specs/exporter-guide/sidecars/workflow/phase-1-intake.md`, `workflow/mapping-hints.md`,
    `rules.md`, `sidecar-files.md` and `known-open-items.md`: `roi-transform-and-source`,
    `omitted-upstream-output`, `model-id-suffix`, `size-codes`.
  - `specs/model-sidecar/templates/model-intake.md` (the verdicts and the rows F1, L1 and D1):
    `roi-transform-and-source`, `omitted-upstream-output`, `model-id-suffix`,
    `landmark-extra-outputs`.
  - `specs/model-sidecar/inventory.yaml:98-129`: `model-id-suffix`, `roi-transform-and-source`,
    `landmark-extra-outputs`.
  - The 0025 item of `notes/decisions/open-work.md`: `model-id-suffix`. The item closes only after
    both proposals are accepted.
  - `specs/model-sidecar/changelog.md`: the summary row N and the `vNEXT` row (all proposals).
  - `specs/model-sidecar/pre/resize-rotated-roi-crop.md` (new in `roi-transform-and-source`): rule
    `V-pre.resize.rotated_roi_crop-1` and the heading "ROI source".
  - `specs/model-sidecar/post/pose-visibility.md` (new in `keypoint-visibility`): the heading "Per-point
    values".
- [ ] `model-id-suffix`: its reference code and its role vectors know only two roles. This proposal
  changes `V-common.identity-2` to allow `roi_refiner`. Neither proposal lists this. This proposal
  uses `{part}` folders. `model-id-suffix` moves the keypoint folders to `{keypoints}`.

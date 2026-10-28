---
slug: nms-clamp-order
section: post.det.selection.nms
exporter: OpenMMLab-Exporter
decision: "0040"
state: recorded
---

# Change proposal: nms-clamp-order

This file is informative. It is not part of the normative spec until a content PR lands its text in
the section files (decision [0036](../../../../decisions/0036-spec-proposals-folder.md)).

**Source.** The OpenMMLab-Exporter file of the proposal `nms-clamp-order`, at OpenMMLab-Exporter commit
[`f3aeb47`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/f3aeb473d3396ee79c4394646a34ed9ef419ecf1),
copied on 2026-10-25. Part 3 also holds the code of the OpenMMLab-Exporter reference file of part 3, copied on
the same date (decision 0036, item 2). The copy changes only the items of decision 0036, item 3.
The session wrote no part.

This file uses ASD-STE100 Simplified Technical English. It follows the change proposal template
(`specs/model-sidecar/templates/change-proposal.md` of the skellytracker repo) and the skill
`propose-sidecar-change`. It answers the intake rows D4a, D12, D9a and D12a of `rtmdet-person` (the
untracked pose-models plan of OpenMMLab-Exporter (plan facts), T26 (4), T28 N2). It is one proposal for one contract unit
(`post.det.selection.nms`): the user merged the earlier proposal `nms-candidate-filters` into it
(plan T32 P1 (a), 2026-10-24). The slug stays `nms-clamp-order`. The title is wider.

**Short form.** mmdet filters and clamps the RTMDet candidates before the NMS, and the spec has none of
these steps. (1) mmdet keeps the top `nms_pre` (1000) candidates of each feature level. (2) It clamps
each box to the padded model input. It does not clamp the boxes to the source image. (3) It drops each
box with a width or a height `<= min_bbox_size` (0) in source pixels. The current spec clamps after the
NMS, to the source image, and it has no cap and no size filter. This proposal adds four optional fields
to the `nms` object of `post.det.selection.nms`: `clamp_to_input` (default `false`), `pre_nms_top_k`,
`level_strides` and `min_bbox_size`. When a field is absent, the current meaning stays. It keeps the NMS
in model-input pixels, because the IoU does not change under the unprojection of any resize method of
the spec (measured: 0 of 10000 image decodes change). It defines the closed bounds of `clamp_boxes`,
keeps a zero-area row, and defines the visit order, the box area (an inverted box has the area 0) and
the IoU of a zero union. With all fields, the sidecar path keeps the same rows as a literal copy of the
mmdet order on 5000 of 5000 COCO val2017 images for both sizes.

## Header

| Field | Value |
|---|---|
| Title | Candidate filters and clamp order of `selection: nms`: a clamp to the model input before the NMS (`nms.clamp_to_input`), a per-level pre-NMS cap (`nms.pre_nms_top_k` with `nms.level_strides`), a box-size filter (`nms.min_bbox_size`), the NMS visit order, box area and zero-union IoU, and the bounds and the zero-area result of `clamp_boxes` |
| Slug | `nms-clamp-order` (new: no `proposed` skellytracker entry covers this property). It holds the earlier proposal `nms-candidate-filters` of 2026-10-24 (plan T32 P1 (a)). That proposal and its reference file are deleted (T32 P2 (a)). |
| Date | 2026-10-24; updated 2026-10-25 (mmdet and mmcv code lines cited by permalink; `unverified` in part 4; re-pinned to skellytracker `dom/21-move-sidecar-guide`; log citations moved to skellytracker 0032 and the current checker lines; "Merge points" and "Exporter commit history" split out of the Header) |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `f3aeb473d3396ee79c4394646a34ed9ef419ecf1` (branch `rtmo-model-id-variant`, OpenMMLab-Exporter decision 0050). Checked again on 2026-10-25: `git rev-parse HEAD` gives this commit, and `git status --porcelain` is empty. The commit is now on `origin/main` (merge commit `7763f72`, PR #2, with no change of content). See "Exporter commit history" below the Header. |
| Model, and its intake file (the untracked intake of `<model>` of OpenMMLab-Exporter (plan facts)) | `rtmdet-person` (the untracked intake of `rtmdet-person` of OpenMMLab-Exporter (plan facts)). No other family of this exporter needs this proposal now. |
| Intake rows with the verdict `near-miss` or `gap` | D4a (`near-miss`: the order of the clamp, the rescale and the NMS), D12 (`near-miss`: the clamp bounds and the zero-area result), D9a (`gap`: the per-level pre-NMS cap `nms_pre=1000`) and D12a (`gap`: the zero-size box filter `min_bbox_size=0`) |
| Kind (`new section` or `changed section`) | `changed section` |
| Proposed section ID (the `id` in the section file's front matter) | `post.det.selection.nms` |
| Section file | `specs/model-sidecar/post/selection-nms.md`. The change also edits the `clamp_boxes` row of `post.det.decode` (`specs/model-sidecar/post/detection-decode.md:43`), because step 6 of the NMS section applies that row (see part 2.1 and part 8, alternative 17). |
| Depends on (proposal files that must land first, or `none`) | none |
| Needed by (proposal files that depend on this one, or `none`) | none. See "Merge points" below the Header. |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | none. The index (`notes/decisions/README.md:36-44`) lists skellytracker 0017 to 0025 as `proposed`. A search of those nine entries for `nms`, `min_bbox`, `pre_nms` and `clamp` finds no entry that covers the NMS, the candidate filters or `clamp_boxes`. The **accepted** entry skellytracker 0011 (`specs/model-sidecar/decisions/0011-rtmdet-host-nms.md`) decided not to add `pre_nms_top_k`. The accepted entry skellytracker 0008 (`specs/model-sidecar/decisions/0008-vnext-scope.md:24`) lists `nms.pre_nms_top_k` and `nms.min_bbox_size` as considered and not added. Entry A supersedes skellytracker 0011 in full, and entry B supersedes skellytracker 0008 in full (plan T30 F2; user decision T35, which revises T32 P4 (a) and T34 N1 (a)). The open-work item on `clamp_boxes` (`notes/decisions/open-work.md:148-153` at skellytracker `dom/21-move-sidecar-guide`, a spec defect, not a decision entry) is the D12 part of this proposal. (History: until 2026-10-25 this cell cited lines 143-148, the lines of the item at skellytracker `dom/18-agents-adr-bootstrap-kit`.) |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `dom/21-move-sidecar-guide` (re-pinned on 2026-10-25; see the last note of this cell). History: `dom/18-agents-adr-bootstrap-kit` at the merge; `git status --porcelain` was empty. The two earlier proposals read `dom/16-private-data` and `dom/17-gitignore-python-version`. `git log dom/17-gitignore-python-version..dom/18-agents-adr-bootstrap-kit` has one commit (the bootstrap kit, skellytracker 0031). It changes no file under `specs/model-sidecar/` or `skellytracker/`. It adds one index row to `notes/decisions/README.md` after line 48 (the skellytracker 0031 row, now line 49; checked again on 2026-10-24). Guide citations point to the skellytracker 0034 layout at skellytracker `dom/21-move-sidecar-guide`. The spec text did not change after the pin (only link repairs). **Checked again on 2026-10-25 at skellytracker `dom/21-move-sidecar-guide`** (branch `dom/sidecar-implementation`). The spec text under `specs/model-sidecar/` did not change. The cited spec, template and guide lines did not move. `git status --porcelain` lists only the untracked `grep.exe.stackdump`, which is not a file that this proposal read. The decision log changed: the Active index now holds skellytracker 0032 (accepted, supersedes skellytracker 0028) and skellytracker 0033 and 0034. `tools/check_decision_log.py` changed (commit `dom/19-decision-log-numbers`). The log citations of this proposal now point to `dom/21-move-sidecar-guide`. |

### Exporter commit history

These facts were in the Header cell "Exporter commit" until 2026-10-25.

- At the merge the commit was `01d9b3dfa8c57454dd5d9195ddefdd47f92db254`. `git status --porcelain`
  was empty.
- Every exporter line that this proposal cites is the line at
  `d0f4343812cc582b4b0020e5b532c83572d11fd2`.
- `git diff --stat d0f4343 01d9b3d` changes no cited file except `tests/test_rtmdet_person.py`. It
  changes line 52 only. The cited lines 74 and 77-84 do not change.
- During the scratch runs, the working tree held uncommitted changes of another agent in
  `onnx_runtime/` and other files.
- Thus the GPU runs and the host vectors used a scratch copy of `onnx_runtime/` from
  `git archive d0f4343`. The scripts check that `onnx_runtime` loads from that copy.
- The control decode of each GPU dump equals the stored predictions of run `20261021T231118Z-<host>`
  exactly.
- **Checked again on 2026-10-24 at `f3aeb47`.** Commit `1dfec48` (OpenMMLab-Exporter decision 0042)
  adds one line near the top of `tests/test_rtmdet_person.py` (line 24). With OpenMMLab-Exporter 0042, the pipeline
  writes `source`, and the RTMDet and RTMW writers write `{filename, sha256}`.
- Thus the cited lines 74 and 77-84 are now 75 and 78-85. Part 7 cites the new lines.
- Commit `f3aeb47` (OpenMMLab-Exporter decision 0050) changes only line 53 of that file.
- `onnx_runtime/`, `rtmdet_person/model_report.py`, `rtmdet_person/identity.py`,
  `rtmdet_person/DECODE_RULES.md` and the configs do not change.
- In `notes/decisions/scripts/`, commit `9deff61` (OpenMMLab-Exporter 0041) adds the
  `rtmw_wrist_gate_*` scripts. The cited file `onnx_coco_eval_dense.py` does not change.
- No text of this proposal says that the RTMDet writer writes no `source` or no `sha256`.
- On 2026-10-24 the branch was not pushed.
- **Checked again on 2026-10-25 at `f3aeb47`.** `git diff --stat d0f4343 f3aeb47` over
  `onnx_runtime/`, `rtmdet_person/`, `mmdeploy-convert/model_cfgs/`, `onnx_coco_eval_dense.py` and
  `tests/test_rtmdet_person.py` changes only `rtmdet_person/adapter.py`, `rtmdet_person/sidecar.py` and
  `tests/test_rtmdet_person.py`. This proposal cites no line of the first two files.
- On 2026-10-25, `git log --all -- notes/decisions/scripts/rtmdet_nms_clamp_parity.py` is empty. The
  parity script is not committed yet (T28 N5, part 5).

### Merge points

Other proposals edit the same spec text as this proposal. These facts were in the Header cell
"Needed by" until 2026-10-25.

- The content PR that lands second rebases on the first. It keeps the edits of both.
- The line numbers below were at skellytracker `dom/18-agents-adr-bootstrap-kit` (checked again at the merge). A session
  checked the line numbers again at skellytracker `dom/21-move-sidecar-guide` on 2026-10-25. The line numbers did not
  move.
- `post/unprojection.md:51-66` ("Implementer guidance"): `roi-transform-and-source`
  (MediaPipe-Exporter).
- `exporter-guide/sidecars/workflow/mapping-hints.md:55-65` ("Mapping hints", Outputs and decode,
  Pose): `landmark-extra-outputs` (MediaPipe-Exporter) and `keypoint-visibility`.
- `changelog.md:38-53` ("Considered and deliberately not added"): `roi-transform-and-source`
  (MediaPipe-Exporter).
- `templates/model-intake.md:298, 301` (rows D9 and D12).
- skellytracker `notes/decisions/README.md` (Index): every proposal adds an entry.
- All proposals add a row to "Summary of changes" (row `N`, the next free number at merge time).
- All proposals add a sentence to the `vNEXT` row of the `schema_version` history
  (`changelog.md:68`).

**Scope entry (merge point; user decisions T34 N2 and T35, the untracked pose-models plan of OpenMMLab-Exporter (plan facts), 2026-10-24).**

- This proposal and the MediaPipe-Exporter proposal `roi-transform-and-source`
  (`specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`) both change rules of
  skellytracker 0008.
- These rules are the scope list of exporters (`0008-vnext-scope.md:8-15`) and the "not added" groups
  (`:21` and `:24`).
- The skellytracker log allows no "extends" relation. An entry that changes a rule of an older entry
  restates the rules that stay. It supersedes the older entry in full (`notes/decisions/README.md:86-87`,
  "Rules"; skellytracker 0032, item 3 (it supersedes skellytracker 0028)).
- By T35, each proposal puts its scope change into a small scope entry. That entry holds only scope
  rules.
- The feature rules of each proposal stay in its own entry: entry A here, and the skellytracker 0020
  entry of the ROI-transform proposal there.
- Thus only the two scope entries meet at this merge point.
- Entry A supersedes no scope entry.
- The feature entry of the ROI-transform proposal supersedes no scope entry. It does not touch
  skellytracker 0011 or entry A.
- **Rule:** the scope change that lands second supersedes the scope entry in force (skellytracker 0008, or the scope
  entry of the first proposal). It restates the scope rules of that entry with its own change.
- **If entry B lands second,** it supersedes the ROI-transform scope entry in full. It restates
  MediaPipe-Exporter (the hand landmark model and the hand ROI refinement model) in the scope list.
- It also restates `crop_policy.border_mode` and rotated crops out of the Resize group ("Effect on
  skellytracker decisions 0011 and 0008", "Variant of entry B").
- **If entry B lands first,** the ROI-transform scope entry supersedes entry B in full. It restates the
  NMS change: `nms.pre_nms_top_k` and `nms.min_bbox_size` are not in the "not added" list, and `vNEXT`
  adds them (its part 2.1, the variant of its scope entry).
- The ROI-transform proposal says the same in its Header "Related", its part 2.1 and its Q10 (revised
  by T35).

### Superseded skellytracker plans

Two plans in the local `plans/` folder of skellytracker described the same host NMS. Neither was
implemented in skellytracker. This proposal supersedes both (plan T30, T32 P3 (a)). Git does not track
the skellytracker `plans/` folder (`.gitignore:177`, `plans/`). The table stays as the record of what
this proposal does with each plan.

| Plan (skellytracker `plans/`) | Date and origin | What it describes | What this proposal does with it |
|---|---|---|---|
| the untracked sidecar NMS decode (ONNX Runtime) plan of skellytracker (plan facts) | Status line "plan, 2026-10-20. Nothing implemented yet." | The host `selection: nms` as a small ONNX decode graph with the `NonMaxSuppression` operator, built at load time; the threshold pre-filter at `max(nms.score_threshold, confidence threshold)`; a provider table; tests with AP targets 0.4036 and 0.6255; YOLOX stays on `decode_prenms`. | Part 6 keeps the useful host advice: the operator is allowed if the host applies steps 1 and 2 to its inputs, gives an inverted box the area 0 and sorts by step 5; the optional `onnx` extra; the threshold-equivalence test (now with the cap); the CPU against CUDA test (now with no tie exemption); YOLOX stays on `decode_prenms` (T32 P7, P9). Part 6 replaces the AP targets with the mmdet-row golden test and an AP gate on the T17 stems (T32 P10). It does not keep the provider table: no row of it was measured (T32 P9). It rejects the `[B, Q, C]` scores from `class_logits_output` with `selection: nms` and the class-agnostic `ReduceMax` path (part 8, alternative 19). Its "per-level `nms_pre`: deliberately not in the spec" changes (part 2). |
| the untracked nms-tool plan of skellytracker (plan facts) | No date in the file. OpenMMLab-Exporter commit `5b0ee2c` (2026-05-27) added it as `.opencode/plans/nms-tool-PLAN.md`. OpenMMLab-Exporter commit `fc6146b` (2026-10-21, "Move the nms-tool plan to skellytracker") removed it from `plans/nms-tool-PLAN.md`. The skellytracker copy equals `git show fc6146b^:plans/nms-tool-PLAN.md` except the line endings. | A tool that appends an NMS to a no-NMS detection graph: the standard ONNX `NonMaxSuppression` or the TensorRT plugin `EfficientNMS_TRT`. | Part 8, alternative 20 rejects it: skellytracker 0011 puts the NMS on the host, and the plugin is not an ONNX operator. |

**State of the two plans.** The user deleted both files from the local skellytracker `plans/` on
2026-10-24. The skellytracker session has nothing to delete. Do not cite or link the two plans in the
decision entry, the spec, the changelog or any tracked file. Copies of the text stay outside the
skellytracker `plans/` folder: `nms-tool-PLAN.md` in the OpenMMLab-Exporter history (`5b0ee2c`,
`fc6146b^`), and the untracked sidecar NMS decode (ONNX Runtime) plan of skellytracker (plan facts) in local skellytracker agent checkpoint refs
(`<local commit>`, `<local commit>`; `refs/agents/...`, not on a remote).

### Effect on skellytracker decisions 0011 and 0008

The skellytracker log rule says: "To change a decision, add a new entry. It restates each rule of the
old entry that stays, and it supersedes the old entry in full. Do not supersede a part of an entry."
(`notes/decisions/README.md:86-87`, "Rules"; skellytracker 0032, item 3 (it supersedes skellytracker 0028)). **User decision T35 (the
untracked pose-models plan of OpenMMLab-Exporter (plan facts), 2026-10-24; P4 revised).** T35 supersedes T32 P4 (a) and T34 N1 (a) in part.
This proposal gives two skellytracker entries:

- **Entry A, the NMS entry.** It supersedes skellytracker 0011 in full. It restates each rule of
  skellytracker 0011 that stays,
  with the changes of this proposal: the clamp to the input, the candidate filters, the visit order,
  the box area, the IoU of a zero union, the bounds of `clamp_boxes` and the inverted box. Its
  evidence goes to one tracked evidence file beside it.
- **Entry B, the `vNEXT` scope entry.** It supersedes skellytracker 0008 in full. It restates each
  rule of skellytracker 0008: the scope list of exporters, the "not added" groups and the other rules
  of skellytracker 0008. It has one
  change: `nms.pre_nms_top_k` and `nms.min_bbox_size` leave the "not added" NMS group. It holds only
  scope rules.

Thus the feature rules and the scope rules are in different entries. A later scope change (for
example the ROI-transform proposal) supersedes only the scope entry in force, and it restates only
scope rules. It does not restate the NMS rules of entry A ("Merge points").

When the entries become `accepted`, the status of skellytracker 0011 becomes `superseded by NNNN`
(entry A), and the status of skellytracker 0008 becomes `superseded by SSSS` (entry B). Their index rows move to "Historical" in the
same PR. The checker rejects `superseded by NNNN` when entry NNNN is `proposed` or `rejected`
(`NOT_DECIDED`, `tools/check_decision_log.py:78`; the check at `:162-163`; the docstring at `:16`).

| Rule of skellytracker 0011 (`0011-rtmdet-host-nms.md`) | Line | In entry A |
|---|---|---|
| The graph ends before NMS. It outputs `boxes` `[B, A, 4]` (`xyxy`, model-input pixels) and `scores` `[B, A]`. | 10-13 | stays (restate) |
| The sidecar declares `decode.selection: nms`. The host runs the NMS. | 14 | stays |
| The `nms` block holds the upstream `test_cfg` values: `iou_threshold` 0.6, `score_threshold` 0.05, `post_nms_top_k` 100. | 15-21 | stays, and extends: `pre_nms_top_k: 1000` (`nms_pre`), `level_strides: [8, 16, 32]`, `min_bbox_size: 0`, `clamp_to_input: true`, and `clamp_boxes: false` (user decision T28 N1) |
| `A` depends on the input size (2100 at 320, 8400 at 640). The family-level shape uses `-1`. Each batch artifact gives the value in `output_shapes`. | 23-25 | stays. New: the rows are in three levels, and `level_strides` gives the count of each level from the input size (no size-level field, skellytracker decision 0010) |
| "The spec has no `nms.pre_nms_top_k` field. The sidecar does not express the mmdet `nms_pre` cap." | 26-27 | **changes**: the spec has `nms.pre_nms_top_k` with `nms.level_strides`, and the sidecar expresses the cap |
| `selection: nms` forbids `class_logits_output`. | 28-30 | stays |
| The detection outputs are the complete candidate set. | 31-32 | stays |
| (none: skellytracker 0011 has no rule for these points) | none | **new**: the steps of `selection: nms` (part 2.3): the score filter and the per-level cap, the clamp to the input, the size filter in source pixels, the NMS in model-input pixels, the visit order and the tie rule, the box area (an inverted box has the area 0), the IoU of a zero union, and the closed bounds of `clamp_boxes` with the zero-area row (part 2.2) |
| Reason "`pre_nms_top_k` has no measured benefit ... The spec does not add that field for an option that changes no AP." | 48-51 | **changes**: the reason to add it is not AP. The user goal is a spec that fully describes the model (T28 N2). The new measurement shows that the field changes no kept row on these two models (part 1). |
| Evidence "Clamping after NMS (spec) instead of before NMS (mmdet) is invisible in AP." | 71 | stays as a fact about AP. New: the clamp changes the kept rows on 668 of 5000 nano images and 405 of 5000 medium images (part 5). |
| Alternative rejected "Add `nms.pre_nms_top_k`" | 120-121 | **changes**: it becomes the decision |
| Not repeated "Do not put `pre_nms_top_k` into a sidecar. The spec does not define it." | 129-130 | **changes**: "Write `pre_nms_top_k` with `level_strides` when the upstream cap acts on each level. Do not write a per-level cap without `level_strides`: a cap over all rows is a different algorithm (part 8, alternative 9)." |
| The other "Not repeated" items (best class per row, the `0.001` comparison, `class_logits_output`, two families) | 131-138 | stay |
| Evidence tables (OpenMMLab-Exporter 0009 and 0016) | section "Evidence" | stay; they move to the evidence file of entry A, with the measurements of part 1 and part 5 |

| Rule of skellytracker 0008 (`0008-vnext-scope.md`) | Line | In entry B |
|---|---|---|
| The `vNEXT` scope: OpenMMLab-Exporter (RTMDet person-only family, RTMW, RTMO body7), Ultralytics-Exporter (YOLO26 detection and pose), Roboflow-Exporter (RF-DETR). Qualcomm-Exporter is out of scope until that library is complete. | 8-15 | stays (restate). See the scope merge point ("Merge points"). |
| `vNEXT` adds only the features that these models need. The changelog table lists the other features, in groups. | 17-26 | stays, except the NMS group (`:24`): `nms.pre_nms_top_k` and `nms.min_bbox_size` **leave** the list. The other groups stay. |
| A later revision can add each feature as a non-breaking schema bump when a model needs it. | 28 | stays. This proposal adds the two NMS features to `vNEXT` itself, because the user goal is a full description of the models in scope (T28 N2). |
| The spec has no RF-DETR example; the rules that RF-DETR motivated stay (`stretch`, the `boxes`, `scores` and `class_logits` semantics with `class_axis`, `selection: top_k` with `class_id_map`). | 30-36 | stays |
| `vNEXT` is a placeholder name (skellytracker 0014). | 38-39 | stays |
| Reason "For `nms.pre_nms_top_k`, a flat candidate list cannot express the per-level `nms_pre` cap of mmdet." | 47 | **changes**: `nms.level_strides` expresses the levels |
| The other reasons, the evidence (the `class_logits` with `selection: nms` measurement), the alternative and the "Not repeated" items | 41-73 | stay in entry B (restated). Entry B also adds one "Not repeated" item: a scope entry holds no feature rule (T35). |

**Form of the two entries (user decision T35, 2026-10-24).** Each entry restates each rule of the entry
that it supersedes and that stays. The evidence of entry A goes into one tracked evidence file beside
it. Thus each entry stays under the limit of 6,000 characters for each entry after skellytracker 0025
(`notes/decisions/README.md:101-104`, "Rules"; skellytracker 0029, item 8; `tools/check_decision_log.py:60`,
`ENTRY_LIMIT = 6_000`). For comparison, skellytracker 0011 has 8,411 characters and skellytracker 0008
has 3,668 (after CRLF to LF). A skellytracker session writes the three files when it records this proposal. This proposal only
describes them. No skellytracker file changes in this work.

| Item | Entry A (NMS) | Entry B (`vNEXT` scope) |
|---|---|---|
| Entry file | `notes/decisions/NNNN-rtmdet-host-nms-filters.md`. The skill `propose-sidecar-change` (Step 3, item 2) names an entry after the proposal slug. Two entries cannot both have that name. The skellytracker session sets the final file names. If it changes them, it also changes the links in both entry texts, the evidence-file name, and the variant in the MediaPipe-Exporter proposal `roi-transform-and-source`. | `notes/decisions/SSSS-vnext-scope-nms-filters.md` |
| Number | `NNNN` is the number that `uv run python tools/check_decision_log.py --next` prints after `git fetch --all` (`notes/decisions/README.md:109-112`; skellytracker 0032, item 8). At skellytracker `dom/21-move-sidecar-guide` the highest number in the index is skellytracker 0034, so `NNNN` is at least skellytracker 0035. A number is provisional until the entry is on `development`. (At `dom/18-agents-adr-bootstrap-kit` the highest number was skellytracker 0031.) | `SSSS` is the next `--next` number after entry A. Both entries land in one PR, entry A first. Thus entry A and entry B are skellytracker 0035 and 0036 if no other entry lands first. If the ROI-transform scope entry lands first as skellytracker 0035, entry A and entry B are skellytracker 0036 and 0037. |
| Title | The heading line of the entry text below. The Decision cell of its index row has the same words: RTMDet: host `selection: nms` with the mmdet candidate filters, clamp and visit order (85 characters; limit 160, `tools/check_decision_log.py:64`). | The heading line of the entry text below. The Decision cell: `vNEXT` scope and the features not added; `nms.pre_nms_top_k` and `nms.min_bbox_size` leave the list (100 characters). |
| Status | `proposed`, with an Active index row in the same PR. At acceptance (the content PR): `accepted`. In the same PR, skellytracker 0011 becomes `superseded by NNNN`, and its row moves to "Historical". | `proposed`, with an Active index row in the same PR. At acceptance: `accepted`. In the same PR, the scope entry that it supersedes (skellytracker 0008, or the ROI-transform scope entry) becomes `superseded by SSSS`, and its row moves to "Historical". |
| Size (after CRLF to LF) | 5,610 characters (94% of 6,000). Real numbers in place of `NNNN` and `SSSS` give the same count. | 4,309 characters (72%). The variant below has 4,691 characters with the real file names. |
| Evidence | The evidence file `notes/decisions/NNNN-rtmdet-host-nms-filters.evidence.md` (the table "Evidence file" below). | No evidence file. Entry B restates the one evidence paragraph of skellytracker 0008. |
| Links | Links entry B (`SSSS`), skellytracker 0010, the spec and the evidence file. | Links entry A (`NNNN`), skellytracker 0008, 0011 and 0014, the spec and `../sidecar-exporter-coverage.md`, as skellytracker 0008 does. |

**Checker run (2026-10-24, scratch, not committed).** The script `t35\run_checker.py` copies
`notes/decisions/` and `tools/check_decision_log.py` of skellytracker `dom/18-agents-adr-bootstrap-kit` to a scratch folder. It
adds the entries with real numbers and their index rows, and it runs `tools/check_decision_log.py`.
Result: exit 0 in four scenarios. (1) Entries A (skellytracker 0032) and B (skellytracker 0033)
`proposed`: read path 211,835 of 220,000 characters (96%; warning at 80%). (2) Both `accepted`,
skellytracker 0011 `superseded by 0032` and skellytracker 0008 `superseded by 0033` in "Historical":
read path 199,776 (91%). (3) Also the ROI-transform scope entry as skellytracker 0034 (its variant,
4,622 characters): read path 216,627 (98%). (4) The ROI-transform scope entry first as skellytracker
0032, entry A as skellytracker 0033 and the variant of entry B as skellytracker 0034: read path 216,855
(99%). The read
path is near its limit while the entries are `proposed`. A skellytracker session must run the checker
again before it adds more entries. **Check of 2026-10-25.** The run used the log and the checker at
`dom/18-agents-adr-bootstrap-kit`. The log at `dom/21-move-sidecar-guide` has three more Active entries (skellytracker 0032 to 0034), and the
checker changed (commit `dom/19-decision-log-numbers`). The four scenarios are runs on the `dom/18-agents-adr-bootstrap-kit` log only. With the
current numbers, entry A and entry B become skellytracker 0035 and 0036 (or skellytracker 0036 and 0037
after an ROI-transform scope entry). A
skellytracker session must run the four scenarios again on the current log before it records the
entries.

**Entry A text** (the NMS entry; the rules come from the earlier one-entry text of T34 N1 (a), which
came from the scratch drafts `entry_draft_rules.md` and `entry_draft_rest.md`, corrected against
skellytracker 0011 at skellytracker `dom/18-agents-adr-bootstrap-kit`):

```markdown
# NNNN — RTMDet: host `selection: nms` with the mmdet candidate filters, clamp and visit order

**Status:** proposed, 2026-10-24 (OpenMMLab-Exporter proposal `nms-clamp-order`).

## Decision

This entry supersedes [0011](0011-rtmdet-host-nms.md) in full. It restates each rule of 0011 that
stays. It holds no scope rule. [SSSS](SSSS-vnext-scope-nms-filters.md) adds the new fields to the
`vNEXT` scope.

**RTMDet person.**

- The graph ends before NMS. It outputs the decoded box and the sigmoid person score of each anchor
  point: `boxes` `[B, A, 4]` (`xyxy`, model-input pixels) and `scores` `[B, A]`. These outputs are the
  complete candidate set
  ([Selection behaviour](../../specs/model-sidecar/post/detection-decode.md#selection-behaviour)).
- The sidecar declares `decode.selection: nms`. The host runs the NMS.
- The `nms` block holds the upstream mmdet `test_cfg` values of the person configs:
  `iou_threshold: 0.6`, `score_threshold: 0.05` (`score_thr`) and `post_nms_top_k: 100`
  (`max_per_img`). Changed: it also holds `pre_nms_top_k: 1000` (`nms_pre`) with
  `level_strides: [8, 16, 32]`, `min_bbox_size: 0` and `clamp_to_input: true`. The decode sets
  `clamp_boxes: false`.
- `A` is 2100 at 320 and 8400 at 640. The family-level output shape uses `-1` for the row dimension.
  Each batch artifact gives the value in `output_shapes`. The rows are in three levels.
  `level_strides` gives the row count of each level from the input size.
- `selection: nms` forbids `class_logits_output`
  ([Validation rules](../../specs/model-sidecar/post/selection-nms.md#validation-rules)).

**Changed: the steps of `selection: nms`.** Each new field is optional. When it is absent, the old
meaning stays.

- The host drops each candidate with `score <= nms.score_threshold`. With `nms.pre_nms_top_k`, it
  then keeps that number of candidates in each level, highest score first. `nms.level_strides` gives
  the levels. Without it, all rows are one level.
- With `nms.clamp_to_input: true`, the host clamps each box to `[0, W_in]` and `[0, H_in]` in
  model-input pixels before the NMS. With `nms.min_bbox_size`, it then drops each candidate whose
  width or height in source pixels is `<= nms.min_bbox_size`.
- The NMS runs in model-input pixels. It visits the candidates in descending score order. The
  survivors have the same order. A tie goes to the lower row index.
- The area of a box is `max(0, x2 - x1) * max(0, y2 - y1)`. Thus an inverted box has the area 0.
  When the area of the union is 0, the IoU is 0.
- `clamp_boxes` clamps to the closed bounds `[0, src_w]` and `[0, src_h]`. It does not drop a row.
  A row with zero area stays.

## Reason

- A graph that keeps the mmdeploy NMS loses candidates. The capped graph lost 0.0114 AP and 0.027 AR
  on `rtmdet-person-medium` (OpenMMLab-Exporter 0008). A graph that ends before NMS keeps every
  candidate.
- Host NMS costs about 1 ms for each image for one class (OpenMMLab-Exporter 0016 and 0017).
- The `nms` block copies the upstream `test_cfg`. With these values, the spec decode reproduces the
  PyTorch AP.
- The spec must fully describe these models (user). mmdet clamps to the padded model input before
  the NMS, keeps 1000 candidates in each level and drops boxes with no width or height. The new
  fields change no AP. Without them, a sidecar cannot describe the decode.
- The IoU does not change under the unprojection of a resize method of the spec. Thus the NMS stays
  in model-input pixels.
- Without a defined visit order, box area and zero-union IoU, two hosts can keep different rows.
- `class_logits` with `selection: nms` has no user. The person family has one class. The 80-class
  family is not exported (OpenMMLab-Exporter 0017).

## Evidence

[NNNN-rtmdet-host-nms-filters.evidence.md](NNNN-rtmdet-host-nms-filters.evidence.md) holds the
measurements: the 0011 parity and cost tables, and the COCO val2017 measurements of the proposal.
The cap and the size filter change no AP. The clamp order changes the kept rows on 668 of 5000 nano
images and 405 of 5000 medium images. With all fields, the sidecar path keeps the same rows as a
literal mmdet order on 5000 of 5000 images for both sizes.

## Alternatives rejected

- Keep mmdeploy's NMS in the graph and declare `selection: none`. It lost 0.0114 AP.
- A cap over all rows in place of `level_strides`. It is a different algorithm.
- The best class of each row for a multi-class family. It lost 0.0051 AP on tiny.
- Add `class_logits` with `selection: nms` now. No family in scope needs it.
- Spec steps equal to the ONNX `NonMaxSuppression` operator. The operator has no cap, no clamp and no
  size filter. It gives an inverted box an area that is not 0.

## Not repeated

- Write `pre_nms_top_k` with `level_strides` when the upstream cap acts on each level. Do not write a
  per-level cap without `level_strides`. A cap over all rows is a different algorithm.
- Do not use the best class of each row for a multi-class NMS-free family. Use every (row, class)
  pair. That needs `class_logits` with `selection: nms` first.
- Do not compare the in-graph NMS and the host decode at the `0.001` threshold. The in-graph variant
  caps 300 boxes for each class.
- Do not declare `class_logits_output` with `selection: nms`. The validation rules forbid it.
- Do not read "invisible in AP" as "no effect". The clamp order changes the kept rows.
- A host that uses the ONNX operator must apply the filters and the clamp to its inputs. It must give
  an inverted box the area 0.
- An RTMDet person-only family and an 80-class family are two families ([0010](0010-family-invariant.md)).
```

**Entry B text** (the `vNEXT` scope entry; it restates skellytracker 0008 at skellytracker `dom/18-agents-adr-bootstrap-kit`
almost word for word):

```markdown
# SSSS — `vNEXT` scope and the features not added; `nms.pre_nms_top_k` and `nms.min_bbox_size` leave the list

**Status:** proposed, 2026-10-24 (OpenMMLab-Exporter proposal `nms-clamp-order`).

## Decision

This entry supersedes [0008](0008-vnext-scope.md) in full. It restates each rule of 0008 that stays.
It holds only scope rules. [NNNN](NNNN-rtmdet-host-nms-filters.md) holds the NMS rules.

The `vNEXT` revision of [the sidecar spec](../../specs/model-sidecar/sidecar-spec.md) must let a sidecar describe
every model that these exporters produce:

- OpenMMLab-Exporter: RTMDet (person-only family), RTMW and RTMO body7.
- Ultralytics-Exporter: YOLO26 detection and YOLO26 pose.
- Roboflow-Exporter: RF-DETR.

Qualcomm-Exporter is out of scope until that library is complete.

`vNEXT` adds only the features that these models need. The spec lists the other features in
[Considered and deliberately not added](../../specs/model-sidecar/changelog.md#considered-and-deliberately-not-added).
This entry groups them:

- Resize: `resize.antialias`, `resize.size_divisor`, `crop_policy.border_mode` and rotated crops.
- Scores and classes: `score_activation: softmax`, `class_id_map_before_selection`, and
  `class_logits` with `selection: nms`.
- Graph and pose descriptions: `graph_candidate_limit` and `pose.decode.instance_count`.
- Soft-NMS, per-class IoU, masks, multi-input models and quantized outputs.

Changed: the NMS group of 0008 (`nms.pre_nms_top_k` and `nms.min_bbox_size`) leaves the list.
`vNEXT` adds both fields for `rtmdet-person` ([NNNN](NNNN-rtmdet-host-nms-filters.md)).

A later revision can add each listed feature as a non-breaking schema bump when a model needs it.

The spec has no RF-DETR reference example. The example returns when Roboflow-Exporter is
overhauled and writes `vNEXT` sidecars. The rules that RF-DETR motivated stay in the spec. These
rules include:

- the `stretch` resize;
- the `boxes`, `scores` and `class_logits` output semantics, with `class_axis`;
- `selection: top_k`, with `class_id_map`.

`vNEXT` is a placeholder name for this revision. [0014](0014-spec-lifecycle.md) holds the rule for
when a release version replaces it.

## Reason

- No model in scope needs most of the listed features. Each row of the
  [spec table](../../specs/model-sidecar/changelog.md#considered-and-deliberately-not-added) gives its own reason.
- Some rows give another reason:
  - For `score_activation: softmax`, the behaviour over gap and background slots is unresolved.
  - `graph_candidate_limit` is informational only. The host cannot act on it.
  - `pose.decode.instance_count` is not needed. The count comes from the detection row axis.
- Changed: the spec must fully describe the models in scope (user). The mmdet decode of
  `rtmdet-person` has a per-level cap and a box-size filter. `nms.level_strides` expresses the
  levels. Thus the 0008 reason for `nms.pre_nms_top_k` (a flat candidate list cannot express the
  per-level cap) does not stay.
- The RF-DETR example had drifted from the output of Roboflow-Exporter, and that exporter will be
  overhauled. An example that does not match a real export misleads exporter authors. The rules stay
  because RF-DETR still needs them.

## Evidence

The spec records one measurement behind the `class_logits` with `selection: nms` row. The test model
is the NMS-free RTMDet-tiny. Each (row, class) pair above the score threshold becomes a candidate.
Per-class NMS follows. This method reproduced the PyTorch AP (0.4114 against 0.4112). A method that
keeps only the best class for each row lost 0.0051 AP and 0.031 AR.

No family in scope needs this feature, because the COCO-80 RTMDet family was dropped. A later
revision can add the feature if a multi-class NMS-free family appears.

## Alternatives rejected

- Adopt the whole Roboflow-Exporter draft that
  [the exporter coverage plan](../sidecar-exporter-coverage.md) starts from.
  The draft has fields that no exported model uses. The coverage plan trims them.

## Not repeated

- Do not read the list of features as a ban. A feature leaves the list when a model needs it.
- Do not remove an RF-DETR rule because the spec has no RF-DETR example.
- Do not put a feature rule into a scope entry. A later scope change supersedes only the scope entry
  in force, and it restates only scope rules.
```

**Corrections to the scratch drafts.**

- `clamp_boxes` is a field of `post.det.decode` (`specs/model-sidecar/post/detection-decode.md:43`), not of the
  `nms` object. Entry A says "The decode sets `clamp_boxes: false`."
- The drafts did not restate the rejected alternative of skellytracker 0008 (the whole Roboflow-Exporter draft,
  `0008-vnext-scope.md:66-68`). Entry B restates it.
- Restated from skellytracker 0011 in entry A: the decoded box and the sigmoid person score of each anchor point
  (`:10-13`), the link to "Selection behaviour" (`:31-32`), the reason "the upstream values are the
  baseline" (`:46-47`), the row dimension of the `-1` shape (`:23-25`), the link to the validation rule
  (`:28-30`), the 80-class family that is not exported (`:52-54`), the reason of the `0.001` pitfall (the
  in-graph variant caps 300 boxes for each class, `:133-135`) and the item "Do not declare
  `class_logits_output` with `selection: nms`" (`:136`).
- Restated from skellytracker 0008 in entry B: the scope list, the groups of "not added" features and
  the reasons of skellytracker 0008 in their own words, the link to "Considered and deliberately not
  added" (`:17-19`), the condition "is overhauled and writes `vNEXT` sidecars" for the RF-DETR example
  (`:30-31`), the skellytracker 0014 rule for the placeholder name (`:38-39`), the evidence paragraphs (`:56-62`), the "not a ban"
  item in "Not repeated" (`:72`) and the reason that a drifted example misleads exporter authors
  (`:50-51`).
- T35 split the one entry of T34 N1 (a). Entry A adds the rules of the visit order, the box area, the
  IoU of a zero union, the inverted box and the bounds of `clamp_boxes` (parts 2.2 and 2.3). The one
  entry had no room for them.
- The draft link `nnnn-evidence.md` becomes a checker error when it has a real number (the table
  "Evidence file" below).

**Variant of entry B: the ROI-transform scope entry lands first** ("Merge points"; user decision
T35). `RRRR` is the number of that scope entry (MediaPipe-Exporter proposal `roi-transform-and-source`,
file `RRRR-vnext-scope-mediapipe-rotated-crops.md`). Entry A does not change. Entry B changes in five
places:

1. The supersedes sentence: "This entry supersedes RRRR (`RRRR-vnext-scope-mediapipe-rotated-crops.md`)
   in full. It restates each rule of RRRR that stays." (skellytracker 0008 is then `superseded by RRRR`.)
2. The scope list adds "- MediaPipe-Exporter: the hand landmark model and the hand ROI refinement
   model."
3. The Resize group becomes "Resize: `resize.antialias` and `resize.size_divisor`."
4. Before "Changed: ...", a new paragraph: "`crop_policy.border_mode` and rotated crops are not in the
   list. `vNEXT` adds them in `rotated_roi_crop` (0020 (`0020-roi-transform-and-source.md`))." In the
   paragraph "Changed: ...", "the NMS group of 0008" becomes "the NMS group of RRRR".
5. Before the Reason bullet "Changed: ...", a new bullet: "`vNEXT` must also describe the MediaPipe
   Holistic hand branch (user). Its crop is a rotated ROI with a replicated border. No resize method
   of the spec describes it." In that "Changed" bullet, "the 0008 reason" becomes "the RRRR reason".

In each merge order, the last scope entry has the same scope rules. The ROI-transform proposal gives
its scope entry and its variant for the other order (its part 2.1).

**Evidence file.**

| Item | Value |
|---|---|
| Name | `NNNN-rtmdet-host-nms-filters.evidence.md` (`NNNN` and the slug of entry A, then `.evidence.md`). |
| Location | `notes/decisions/`, beside entry A. The log rule: "Put long evidence in a tracked file next to the entry, and link to it" (`notes/decisions/README.md:101-104`; skellytracker 0029, item 8). |
| Why this name | The log has no evidence file beside an entry yet. At `dom/18-agents-adr-bootstrap-kit`, `notes/decisions/` held only the entries, `README.md` and `open-work.md`. At `dom/21-move-sidecar-guide` it also holds `scripts/` (`next_number_timing.py`, skellytracker 0032). It still holds no evidence file, so there is no example to follow. The checker reads each file that matches `^(\d{4})-[a-z0-9-]+\.md$` as an entry (`ENTRY_NAME`, `tools/check_decision_log.py:80`; `entry_files`, `:135`). A name such as `NNNN-evidence.md` matches. The check then fails with "0 index rows, expected 1", and the entry limit applies. The `.evidence.md` name does not match. The checker does not read it as an entry, applies no limit to it and does not add it to the read path. The name sorts next to the entry. The checker run above had the file beside entry A, with no error. |
| Form | The heading `# NNNN evidence — ` and the title of entry A. The first paragraph: "Evidence for NNNN (`NNNN-rtmdet-host-nms-filters.md`). This file is not an entry. It has no status line and no index row." ASD-STE100, as an entry. The citation rules of the log apply: relative links for tracked files, permalinks for a commit or the code of another repo (skellytracker 0032, item 4), no `plans/` citation. The edit rules of an entry apply to it (skellytracker 0032, item 1). |
| From skellytracker 0011 (moved unchanged) | The section "Evidence" of skellytracker 0011 (3,316 characters): (1) the parity table with PyTorch (OpenMMLab-Exporter 0009) and its three bullets; (2) the cost of dropping the `nms_pre` cap (OpenMMLab-Exporter 0009 and 0017); (3) the table of the host decode against the in-graph NMS (OpenMMLab-Exporter 0016) and its result; (4) the upstream values (the person config `test_cfg`, the `NMS` constant of `rtmdet_person/identity.py`); (5) the spec references. The content PR deletes the changelog rows `nms.pre_nms_top_k` and `nms.min_bbox_size`, so (5) names the new changelog row (part 2.7); (6) the code facts (`DetectionDecodeSpec` and the other classes of `skellytracker/core/sidecar/model.py`), checked again at the commit of the session. |
| From skellytracker 0008 | Nothing. Entry B restates the evidence paragraph of skellytracker 0008 (the `class_logits` with `selection: nms` measurement, 0.4114 against 0.4112). It is the same measurement as rows 3 and 4 of the parity table of skellytracker 0011 in this file. |
| New (this proposal) | Part 1: the config keys, the graph read of the three levels (strides 8, 16 and 32; 1600 + 400 + 100 = 2100 and 6400 + 1600 + 400 = 8400 rows), the prior-point check, the bounds of the upstream output (boxes past the source image, the bound `T * src_w / n_w` to 3.05e-5, no box with `w <= 0` or `h <= 0`) and the IoU invariance (0 of 10000 image decodes change). Part 5: the clamp changes the kept rows on 668 of 5000 nano images and 405 of 5000 medium images; the cap (largest level 1003 and 2142 candidates; it removes 3 candidates on 1 nano image and 13560 on 34 medium images; no kept row changes); the size filter (1 nano candidate, image 328430, row 1008; 1 row on 1 image); the AP of the current text, of the full mapping and of the source pass; the same rows as a literal mmdet order on 5000 of 5000 images for both sizes; the host gap of vector `inverted-box-has-area-zero`. The mmdet v3.3.0 and mmcv 2.1.0 code lines (part 1, permalinks). |
| Scripts | The scratch scripts of part 1 and part 5 are not evidence. The file cites the OpenMMLab-Exporter parity script `notes/decisions/scripts/rtmdet_nms_clamp_parity.py` by permalink after it is on the default branch (T28 N5), and the OpenMMLab-Exporter decision entry on the mmdet clamp (T28 N3) by repo name and number. skellytracker 0032 item 9 asks for the script of each measurement. The measurements of this evidence file come from OpenMMLab-Exporter. The evidence file names the OpenMMLab-Exporter script by a full-SHA permalink (skellytracker 0032 item 4). It does not copy the script into skellytracker `notes/decisions/scripts/` (skellytracker 0032 item 10). |
| Link | The section "Evidence" of entry A links the file with a relative link and gives a short summary (entry A text above). |
| Size | No limit applies to the file. It is not on the read path. |

## 1. Gap

| Item | Value |
|---|---|
| Property | Four properties of the mmdet RTMDet test decode, before the NMS. (1) **Per-level pre-NMS cap.** After the score filter (`score > score_thr`), mmdet keeps the top `nms_pre` candidates of each feature level by score. (2) **Clamp to the padded input.** mmdet clamps each decoded box to the padded model input, `[0, T_w] x [0, T_h]` in model-input pixels, with closed bounds: many boxes end exactly on the bound. (3) **Rescale, no clamp to the source.** mmdet then rescales the boxes to the source image. It does not clamp the rescaled boxes to the source image: a box can end past `src_w` or `src_h`. (4) **Box-size filter.** After the rescale, mmdet drops each box with `w <= min_bbox_size` or `h <= min_bbox_size`. With `min_bbox_size=0`, this drops a box with zero or negative width or height. Then mmdet runs the NMS. |
| Upstream evidence (file and line, or config key; upstream commit or release) | **Config keys (primary).** `test_cfg` `nms_pre=1000` and `min_bbox_size=0`: `mmdeploy-convert/model_cfgs/rtmdet_nano_320-8xb32_coco-person.py:25-26` and `rtmdet_m_640-8xb32_coco-person.py:11-12` (mmpose v1.3.2 person configs; the medium file is a byte copy, the nano file an adapted copy, `mmdeploy-convert/CONFIG_SOURCES.md:21-22`). **Graph read (primary): the levels.** In `rtmdet-person-nano_b1_fp32.onnx`, the `scores` output comes from `/Concat_14` (axis 1) with three inputs. Each input is a `Reshape` of a `Transpose` (to NHWC) of a one-channel `Conv` output: `[1, 1, 40, 40]`, `[1, 1, 20, 20]` and `[1, 1, 10, 10]`, in this order. `rtmdet-person-medium_b1_fp32.onnx` has the same chain with `[1, 1, 80, 80]`, `[1, 1, 40, 40]` and `[1, 1, 20, 20]` (scratch `inspect_levels.py`). Thus the rows are level-major (strides 8, 16, 32 at inputs 320 and 640), row-major in each level, one row for each cell: 1600 + 400 + 100 = 2100 and 6400 + 1600 + 400 = 8400. The mmdeploy rewriter that made the graph does the same: `cls_score.permute(0, 2, 3, 1).reshape(batch_size, -1, ...)` for each level, then `torch.cat(..., dim=1)` (`mmdeploy/codebase/mmdet/models/dense_heads/rtmdet_head.py:66-81`, a local clone of mmdeploy (a sibling folder of the exporter repo) at `bc75c9d6c8940aa03d0e1e5b5962bd930478ba77`). **Graph run (primary): the prior points.** RTMDet boxes are `prior - d` and `prior + d` (`rtmdet_head.py:82-86`). On all 5000 COCO val2017 images, the medium graph puts each prior point `(x * s, y * s)` of this layout inside its box on 42000000 of 42000000 rows (scratch `dump.py`). The medium graph has 3 `Exp` nodes, the nano graph none. On nano, 111352 of 10500000 rows have the prior point outside the box (by up to 11.21 px): without `Exp` a distance can be negative. That is also the source of the inverted nano box below. **Upstream output (primary input of the workflow: "one reference output of the upstream library").** The source passes of run `20261021T231118Z-<host>`: mmdet 3.3.0 `tools/test.py` (clone `44ebd17b145c2372c4b700bfb9cb20dbd28ab64a`), mmcv 2.1.0, mmengine 0.10.3, image `<user>/openmmlab-exporter:df-dcab32049439` (digest `sha256:fe297e9fa18dd31738994209217f124f9f27357e89414aa432c607e3f08807bc`), batch 1, all 5000 COCO val2017 images. Files: `exports/detectors/object_detectors/rtmdet-person/benchmarks/rtmdet-person-{nano,medium}_source/rtmdet-person-{nano,medium}_source.accuracy.torch-cuda.b1.20261021T231118Z-<host>.predictions.json` (not tracked; producer commit `e67fc2a`, `git_dirty: false`). Measured on these files (scratch `bounds.py`, `canvas_bound.py`): **nano** 290882 boxes: `min(x1) = 0`, `min(y1) = 0`; 2214 boxes with `x2 > src_w + 0.001` and 6064 with `y2 > src_h + 0.001`; the largest overshoot is 213.5 px (x) and 212 px (y); `max(x2 - T * src_w / n_w) = 3.05e-5` and `max(y2 - T * src_h / n_h) = 3.05e-5` (float32 noise); 9120 boxes end within 0.01 px of `T * src_w / n_w` and 3181 of `T * src_h / n_h`; 0 boxes with `w <= 0` or `h <= 0` (smallest height 0.129 px). **medium** 182515 boxes: 1193 and 2070 boxes past the source image, up to 172.9 px and 281 px; the same bound to 3.05e-5; 9649 and 2463 boxes on the bound; 0 boxes with `w <= 0` or `h <= 0`. `T * src_w / n_w` is the right edge of the padded input (`T` = 320 or 640) mapped to the source with the letterbox scale. Thus (2), (3) and the result of (4) are shown by the upstream output. The place of (2) before the NMS is shown by the decode of part 5: the order "clamp to the input, rescale, NMS" reproduces the source rows better than every other order that part 8 tests (alternatives 1, 3 and 4). The host output of the same run (current text, `clamp_boxes: true`) has 5 nano rows with `w <= 0` and 5 with `h <= 0`. On nano image 328430, mmdet gives 96 rows; the sidecar path with the clamp mapping gives 97, and with all fields 96 (part 5). **Upstream code (primary; read on GitHub at the tags mmdet v3.3.0 and mmcv v2.1.0 on 2026-10-25).** The tag v3.3.0 is the commit `44ebd17b145c2372c4b700bfb9cb20dbd28ab64a`. It is the mmdet clone in the image `df-dcab32049439`, so these lines are the code of the source pass. The tag v2.1.0 of mmcv is the commit `57c4e25e06e2d4f8a9357c84bcd24089a284dc88`. `RTMDetHead` (`rtmdet_head.py:22`, a subclass of `ATSSHead`), `RTMDetSepBNHead` (`:530`), `ATSSHead` and `AnchorHead` define no `_predict_by_feat_single` and no `_bbox_post_process`. Thus `BaseDenseHead` applies. The lines: (a) [`base_dense_head.py:348`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/dense_heads/base_dense_head.py#L348) `img_shape = img_meta['img_shape']`; [`:349`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/dense_heads/base_dense_head.py#L349) `nms_pre = cfg.get('nms_pre', -1)`. (b) [`:393-395`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/dense_heads/base_dense_head.py#L393-L395) the per-level `filter_scores_and_topk(scores, score_thr, nms_pre, ...)`. (c) [`:414`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/dense_heads/base_dense_head.py#L414) `bboxes = self.bbox_coder.decode(priors, bbox_pred, max_shape=img_shape)`. The cap of `:393-395` comes before the decode and its clamp. (d) [`:467`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/dense_heads/base_dense_head.py#L467) `results.bboxes = scale_boxes(results.bboxes, scale_factor)` (the rescale). (e) [`:476`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/dense_heads/base_dense_head.py#L476) `if cfg.get('min_bbox_size', -1) >= 0:`; [`:478`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/dense_heads/base_dense_head.py#L478) `valid_mask = (w > cfg.min_bbox_size) & (h > cfg.min_bbox_size)`. The test is strict. It acts on source pixels, after the rescale. (f) [`:485-486`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/dense_heads/base_dense_head.py#L485-L486) `batched_nms(...)`; [`:490`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/dense_heads/base_dense_head.py#L490) `results = results[:cfg.max_per_img]`. (g) [`mmdet/models/utils/misc.py:308`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/utils/misc.py#L308) `filter_scores_and_topk`; [`:332`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/utils/misc.py#L332) `valid_mask = scores > score_thr` (strict); [`:336`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/utils/misc.py#L336) `num_topk = min(topk, valid_idxs.size(0))`; [`:338`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/utils/misc.py#L338) `scores, idxs = scores.sort(descending=True)`; [`:339-340`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/utils/misc.py#L339-L340) the `[:num_topk]` slices. (h) [`mmdet/models/task_modules/coders/distance_point_bbox_coder.py:24`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/task_modules/coders/distance_point_bbox_coder.py#L24) `clip_border` has the default `True`; [`:79-81`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/task_modules/coders/distance_point_bbox_coder.py#L79-L81) `if self.clip_border is False: max_shape = None`, then `bboxes = distance2bbox(points, pred_bboxes, max_shape)`. (i) [`mmdet/structures/bbox/transforms.py:147`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/structures/bbox/transforms.py#L147) `distance2bbox`; [`:179-180`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/structures/bbox/transforms.py#L179-L180) `bboxes[:, 0::2].clamp_(min=0, max=max_shape[1])` and `bboxes[:, 1::2].clamp_(min=0, max=max_shape[0])` (closed bounds). (j) mmcv [`mmcv/transforms/processing.py:275`](https://github.com/open-mmlab/mmcv/blob/57c4e25e06e2d4f8a9357c84bcd24089a284dc88/mmcv/transforms/processing.py#L275) `class Pad`; [`:375`](https://github.com/open-mmlab/mmcv/blob/57c4e25e06e2d4f8a9357c84bcd24089a284dc88/mmcv/transforms/processing.py#L375) `size = self.size[::-1]`; [`:388`](https://github.com/open-mmlab/mmcv/blob/57c4e25e06e2d4f8a9357c84bcd24089a284dc88/mmcv/transforms/processing.py#L388) `results['img_shape'] = padded_img.shape[:2]`. Thus `max_shape` is the padded input. (k) Strides: [`configs/rtmdet/rtmdet_l_8xb32-300e_coco.py:36-37`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/configs/rtmdet/rtmdet_l_8xb32-300e_coco.py#L36-L37) `anchor_generator=dict(type='MlvlPointGenerator', offset=0, strides=[8, 16, 32])`; [`:38`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/configs/rtmdet/rtmdet_l_8xb32-300e_coco.py#L38) `bbox_coder=dict(type='DistancePointBBoxCoder')`; [`rtmdet_m_8xb32-300e_coco.py:1`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/configs/rtmdet/rtmdet_m_8xb32-300e_coco.py#L1) `_base_ = './rtmdet_l_8xb32-300e_coco.py'`. The person configs inherit them: `mmdeploy-convert/model_cfgs/rtmdet_nano_320-8xb32_coco-person.py:1` `_base_ = 'mmdet::rtmdet/rtmdet_l_8xb32-300e_coco.py'` and `rtmdet_m_640-8xb32_coco-person.py:1` `_base_ = 'mmdet::rtmdet/rtmdet_m_8xb32-300e_coco.py'`. mmdet gives no tie rule for the cap: `scores.sort(descending=True)` has no `stable=True` (`misc.py:338`). The tie rule of step 1 is a rule of the spec. **Secondary.** `notes/decisions/scripts/onnx_coco_eval_dense.py:7-12` (docstring: "per level ... filter_scores_and_topk: (anchor, class) pairs with score > score_thr, top nms_pre by score; concat levels -> rescale to the original image -> drop boxes with w or h <= min_bbox_size (0)"), `:41` (`STRIDES = (8, 16, 32)`), `:60` (`(TH // s) * (TW // s)` rows for each level), `:91-112` (commit `c955162`). **That copy clips to `[0, n_w] x [0, n_h]` (lines 92-94), the resized image, not to the padded input.** The upstream output above disagrees with that copy: with the copy, no mmdet box could end past the source image. skellytracker `notes/sidecar-exporter-coverage.md:185` (secondary): "mmdet applies it in source-image pixels". |
| Nearest section ID (the `id` in the section file's front matter) | `post.det.selection.nms` (with the `clamp_boxes` row of `post.det.decode`) |
| Why the nearest section is wrong | The section has one candidate filter before the NMS: `score <= nms.score_threshold` (`specs/model-sidecar/post/selection-nms.md:45`). It has no cap for each level, no clamp before the NMS and no size filter. The `nms` object has four fields (`:32-35`). The rows of the primary output are a flat list: no field groups them in levels. The section runs the NMS on unclamped boxes in model-input pixels, then unprojects, then clamps to the source image (`:46-50`). A clamp changes the IoU of a box that crosses the input edge, so the NMS keeps other rows. Step 6 says "Clamp them" without the condition `clamp_boxes` (`:50`). The `clamp_boxes` row says "Clamp the unprojected boxes to the source-image bounds" (`specs/model-sidecar/post/detection-decode.md:43`). It does not say if the upper bound is `src_w` or `src_w - 1`, and it does not say what happens to a box with zero area after the clamp (open-work item, `notes/decisions/open-work.md:148-153` at skellytracker `dom/21-move-sidecar-guide`). Step 4 does not give the visit order, the box area or the IoU of a zero union. The changelog lists `nms.pre_nms_top_k` and `nms.min_bbox_size` as not added (`specs/model-sidecar/changelog.md:49-50`), and the "Authoring guidance" says "`nms_pre=1000` and `min_bbox_size=0` have no field" (`selection-nms.md:90`). A sidecar thus cannot describe the mmdet decode of RTMDet. |
| Measured difference (number, image and script) | COCO val2017, 5000 images, the published `rtmdet-person-{nano,medium}_b1_fp32.onnx` files on ONNX Runtime 1.31.0 `CUDAExecutionProvider` (RTX 3070), the host letterbox, then the reference file of part 3 (part 5 gives the full table). **Clamp.** With `clamp_to_input: true` the NMS keeps other rows than the current text on **668 of 5000 images (nano)** and **405 of 5000 (medium)**. Against the mmdet source output, the source rows with no partner box at IoU >= 0.9 fall from 4350 to 3809 of 290882 (nano) and from 2461 to 2238 of 182515 (medium), and the images with an equal row count rise from 3513 to 3651 and from 3788 to 3867. The coordinate space of the NMS alone changes no image: "unproject, NMS in source pixels, clamp" keeps the same rows as the current text on 5000 of 5000 images for both sizes. **Cap** (`pre_nms_top_k: 1000`, `level_strides: [8, 16, 32]`): the largest level has 1003 candidates above 0.05 (nano) and 2142 (medium). The cap removes 3 candidates on 1 nano image and 13560 candidates on 34 medium images. It changes no kept row (0 of 5000 images, both sizes). **Size filter** (`min_bbox_size: 0`): it removes 1 nano candidate (image 328430, row 1008, score 0.0865, model box `[60.82, 200.60, 64.43, 200.07]`, `y2 < y1`), with or without `clamp_to_input`. It removes no medium candidate. It changes the kept rows on 1 nano image (1 row). **AP**: current text 0.403585 (nano), 0.625492 (medium); the full mmdet mapping (`clamp_to_input: true`, `clamp_boxes: false`, the cap and the size filter) 0.403350 and 0.625439, the same as the clamp mapping alone to 6 decimals; the source pass 0.403290 and 0.625469. With all fields, the sidecar path keeps the same rows in the same order as a literal copy of the mmdet order on 5000 of 5000 images for both sizes (box difference 0 px). Scripts: scratch `dump_candidates.py`, `variants.py`, `parity_ref.py`, `diff_b_mmdet.py`, `check_nms_pre.py` in `...\scratchpad\rtmdet-nms\` (`...` is the local temporary folder of session `3bd420c5`, not in a repo), and `dump.py`, `analyze.py`, `global_cap.py`, `one_image.py` in `...\scratchpad\nms-pre\` (not committed, so not evidence). |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | Two rows. `nms.pre_nms_top_k` (`changelog.md:49`): "A flat candidate list cannot express mmdet's per-level `nms_pre` cap without a `level_strides` field. It had no measured AP effect ...". This proposal adds `level_strides`. `nms.min_bbox_size` (`changelog.md:50`): "No in-scope model uses it; the value is `0` everywhere." The value `0` is not a no-op: it drops an inverted box, and the nano graph makes one on COCO val2017 (above). No row for the clamp. **Why now.** The user decision T28 N2 sets the goal: the spec must fully describe these models. Without the fields, intake rows D4a, D12, D9a and D12a stay `near-miss` or `gap`, and the intake verdict of `rtmdet-person` stays `does not describe` (the untracked intake of `rtmdet-person` of OpenMMLab-Exporter (plan facts), "Final verdict"). The measurements show that the AP does not need the cap and the size filter. The description needs them. |

**Why the IoU does not need source pixels.** Every unprojection of the spec maps each axis with a
scale and an offset (`letterbox`, `stretch`, `fit`, `none`, `affine_person_crop` with rotation 0). Such
a map multiplies every area by the same factor, and it maps the intersection of two boxes to the
intersection of their images. Thus the IoU of two boxes is the same in model-input pixels and in
source pixels. Only the float rounding differs. The measurement agrees: 0 images change.

The primary evidence is complete: the config keys, the graph, the upstream output and the mmdet and
mmcv code lines. The order of the cap and the size filter, the source-pixel space of the size filter
and the clamp to the padded input now rest on the code lines, not on the secondary copy. mmdet has no
tie rule for the cap (`misc.py:338`). The tie rule is a rule of the spec. (History: until 2026-10-24
this paragraph named the code lines as missing. A session read them on GitHub at the tags on
2026-10-25.)

## 2. Spec change

### 2.1 Sections

One section changes: `post.det.selection.nms` (`specs/model-sidecar/post/selection-nms.md`, title
"Selection: NMS", kind `postprocessor`). No section is new. The section map row
(`specs/model-sidecar/README.md:81`) does not change.

**Places that the change edits.**

| File (section ID) | Heading | Edit |
|---|---|---|
| `specs/model-sidecar/post/selection-nms.md` (`post.det.selection.nms`) | front matter | `implemented_by.decode` comment (`:11`): add "no `clamp_to_input`, `pre_nms_top_k`, `level_strides` or `min_bbox_size`". `implemented_by.decode` stays `decode_prenms` until the new function of part 6 exists. `changed_in` stays `[vNEXT]`. |
| same | Fields, `nms` object table (`:35`) | Add the rows `clamp_to_input`, `pre_nms_top_k`, `level_strides` and `min_bbox_size` after `post_nms_top_k` (2.2). |
| same | Behaviour, steps 1, 2, 4, 5 and 6 (`:45-50`) | Replace with the steps of 2.3. The step numbers do not change. Add the notes "Levels" and "IoU and coordinates" after the step list. |
| same | Behaviour, the paragraph on the ONNX operator (`:53`) | "These decode steps correspond one-to-one to the standard ONNX `NonMaxSuppression` operator" is not true with the cap, the clamp, the size filter and the area of an inverted box. Replace the paragraph with the text of 2.3. |
| same | Validation rules (`:61`) | Change `V-post.det.selection.nms-1`. Add `V-post.det.selection.nms-2` (2.4). |
| same | Legacy behaviour (`:65-71`) | Add two rows (2.6). |
| same | Implementer guidance (`:73-86`) | Add the bullets of 2.8. |
| same | Authoring guidance, the bullet of `:90` | Replace it with the mmdet mapping of 2.8. |
| `specs/model-sidecar/post/detection-decode.md` (`post.det.decode`) | Fields, the `clamp_boxes` row (`:43`) | Replace with the row of 2.2. |
| same | Implementer guidance, the bullet "Clamp bounds in use" (`:100`) | Replace with the text of 2.8. The current bullet says that mmdet clamps before the NMS and that this is invisible in AP. The upstream output shows that mmdet clamps to the padded input, and the order changes the kept rows on 668 of 5000 images. |
| `specs/model-sidecar/post/selection-none.md` (`post.det.selection.none`) | Behaviour, step 3 (`:39`) | Link "clamp the boxes" to the `clamp_boxes` row. The meaning does not change. |
| `specs/model-sidecar/post/selection-top-k.md` (`post.det.selection.top_k`) | Behaviour, step 6 (`:41`) | "Clamp the boxes." becomes "When `clamp_boxes` is true, clamp the boxes (`clamp_boxes` (`detection-decode.md#decode-detection`))." The same condition as `selection: none`. |
| `specs/model-sidecar/post/unprojection.md` (`post.unprojection`) | Implementer guidance, the bullet on the open bound (`:51`) and `:55` | `:51`: the bound is now defined (2.2). `:55`: "clamp after the unprojection" stays true for `clamp_boxes`; add "A clamp before the NMS is `nms.clamp_to_input` in model-input pixels." |
| `specs/model-sidecar/vectors/post.det.selection.nms.yaml` and `tools/make_vectors.py` | the header comment (`:9-14`) and `cases` | The file says "Generated by tools/make_vectors.py. Do not edit this file by hand." (`:2`). Add the 29 cases of part 4 to `build_selection_nms` (`tools/make_vectors.py:1786`), or let the tool read them, and regenerate the file. The comment says that the cases stop before the unprojection and the clamp (`:9-11`): the new cases go to the end of step 7 with an axis-aligned inverse. The comment lists the `nms` fields that the cases give without the `nms` key (`:12-14`): add `clamp_to_input`, `pre_nms_top_k`, `level_strides` and `min_bbox_size`. |
| `specs/model-sidecar/vectors/post.unprojection.yaml` | header comment (`:18-20`) | The bound and the zero-area result are now defined (`post.det.decode`). |
| `specs/model-sidecar/changelog.md` | "Summary of changes" | Add the row of 2.7. |
| same | "Considered and deliberately not added" (`:49-50`) | Delete the rows `nms.pre_nms_top_k` and `nms.min_bbox_size`. Add the row "NMS in source pixels" (2.7). |
| same | "`schema_version` history", `vNEXT` row (`:68`) | The sentence of 2.7. |
| `specs/model-sidecar/README.md` | section map, validation index | No edit. No new section. The validation index links each section, not each rule ID (`README.md:116`). |
| `specs/model-sidecar/TRACEABILITY.md` | all | No hand edit. `tools/sidecar_trace.py matrix` generates the file (its line 3). |
| `specs/model-sidecar/format/versioning.md` | "Version-aware compatibility" (`:62` links the legacy table of Selection: NMS) | No edit: the new legacy rows are in the section table. |
| `specs/model-sidecar/common/sizes-and-artifacts.md` | Validation rules | No edit. `V-post.det.selection.nms-2` reads `input.shape`, `outputs[].shape` and `output_shapes`. No size-level field is new, so the family invariant (`V-common.sizes_and_artifacts-3`, skellytracker decision 0010) does not change. |
| Non-spec (documentation PR) | `specs/exporter-guide/sidecars/workflow/mapping-hints.md:55-61` ("Mapping hints", Outputs and decode) | The guide says that the clamp bound is not defined. Change it to name `clamp_boxes` (closed bounds, zero-area row stays) and `nms.clamp_to_input`. Add: "Record the pre-NMS candidate filters of the upstream test config, for example mmdet `nms_pre` and `min_bbox_size`. Record if a cap acts on each feature level." |
| Non-spec (documentation PR) | `specs/model-sidecar/templates/model-intake.md:285, 298, 301` | `:285` and row D12 (`:301`): the bound is now defined; name `clamp_boxes` and `nms.clamp_to_input`. Row D9 (`:298`): "Row limits: graph-final row count (`max_detections`), `top_k`, `nms.post_nms_top_k`" becomes "... `nms.post_nms_top_k`, and a per-level pre-NMS cap (`nms.pre_nms_top_k` with `nms.level_strides`)". Add a row D12b "Box-size filter before the NMS (`nms.min_bbox_size`): the bound, `>` or `>=`, and the pixel space" with the link to `post.det.selection.nms` (Authoring guidance). |
| Non-spec (documentation PR) | `notes/decisions/open-work.md:148-153` (at skellytracker `dom/21-move-sidecar-guide`) | Close the `clamp_boxes` item. |
| Non-spec (documentation PR) | `specs/model-sidecar/examples/README.md:27` | The last sentence ("mmdet's per-level `nms_pre` cap (1000) is deliberately not expressed; dropping it has no measurable effect on AP.") becomes: "The sidecar declares the mmdet decode: `nms.clamp_to_input: true`, `clamp_boxes: false`, `nms.pre_nms_top_k: 1000` with `nms.level_strides: [8, 16, 32]`, and `nms.min_bbox_size: 0`." It changes when the example changes (follow-up row). |
| Decision log, entry A (skellytracker, when the session records this proposal) | `notes/decisions/NNNN-rtmdet-host-nms-filters.md` | A new entry (status `proposed`) supersedes skellytracker 0011 in full. It has the text "Entry A text" of "Effect on skellytracker decisions 0011 and 0008" (user decision T35). It holds no scope rule, and it does not change when the ROI-transform scope entry lands first. Add its Active index row in the same PR. When the content PR sets the entry to `accepted`, the status of skellytracker 0011 becomes `superseded by NNNN`, and its row moves to "Historical". `notes/sidecar-exporter-coverage.md:184-185` (S5, "Defer `pre_nms_top_k`", "Defer `min_bbox_size`") is a plan note; the session decides if it needs a pointer to entry A. |
| Decision log, entry B (skellytracker, in the same PR as entry A) | `notes/decisions/SSSS-vnext-scope-nms-filters.md` (`SSSS` is `NNNN` + 1) | A new scope entry (status `proposed`) supersedes in full the scope entry in force: skellytracker 0008, or the ROI-transform scope entry if that lands first. It has the text "Entry B text", or the text "Variant of entry B" if the ROI-transform scope entry lands first ("Merge points"; user decision T35). It holds only scope rules. Add its Active index row in the same PR. When the content PR sets the entry to `accepted`, the scope entry that it supersedes becomes `superseded by SSSS`, and its row moves to "Historical". |
| Decision log evidence file (skellytracker, in the same PR as entry A) | `notes/decisions/NNNN-rtmdet-host-nms-filters.evidence.md` | A new tracked file beside entry A (user decisions T34 N1 (a) and T35). It holds the evidence of skellytracker 0011 and the measurements of part 1 and part 5 ("Effect on skellytracker decisions 0011 and 0008", table "Evidence file"). The section "Evidence" of entry A links it. It has no index row. Entry B has no evidence file. |
| Local files, not tracked (skellytracker `plans/`) | the untracked sidecar NMS decode (ONNX Runtime) plan of skellytracker (plan facts), the untracked nms-tool plan of skellytracker (plan facts) | Deleted by the user, 2026-10-24; no action ("Superseded skellytracker plans"). No PR. No tracked file cites them. |
| Follow-up, not in this content PR | `specs/model-sidecar/examples/detectors/object_detectors/rtmdet-person/rtmdet-person.yaml:42` | The example is a byte copy of the exporter sidecar (phase 3). It changes when the exporter writes the new fields (part 7). |

Searches done (skellytracker `dom/17-gitignore-python-version`; the cited files are the same at `dom/18-agents-adr-bootstrap-kit`): `clamp` in
`specs/model-sidecar/` (all files), `post_nms_top_k`, `nms` in `format/versioning.md` and `README.md`;
`pre_nms_top_k`, `min_bbox_size`, `nms_pre`, `level_strides`, `pre_nms` and `pre-NMS` in `specs/`,
`notes/`, `skellytracker/` and `.claude/`. The hits in `skellytracker/core/temporal_processing/`
(`min_bbox_size_px`) are a crop policy of the tracker, not the decode. The `role`, `semantic` and
resize-method sets do not change. `post.pose.bottom_up` does not change: a pose row follows its kept
detection row (`selection-nms.md:55`), and a row that a filter drops is not a kept row.

### 2.2 Fields table

New rows of the `nms` object (`post.det.selection.nms`, after `post_nms_top_k`):

| Field | Type | Required | Description |
|---|---|---|---|
| `clamp_to_input` | bool | no | The default is `false`. When `true`, the host clamps each candidate box to the model input before the NMS (Behaviour, step 2). The bounds are `[0, W_in]` for `x1` and `x2`, and `[0, H_in]` for `y1` and `y2`, in model-input pixels. `W_in` and `H_in` are the width and the height of the model input (the spatial dimensions of `input.shape`). The bounds are closed. The clamp does not drop a candidate. |
| `pre_nms_top_k` | int | no | When present, the host keeps at most this number of candidates in each level after the score filter, highest score first (Behaviour, step 1). The value must be a positive integer. When absent, there is no cap. |
| `level_strides` | array[int] | no | The levels of the rows of the primary output (Behaviour, "Levels"). Each value is the stride of one level in model-input pixels, in row order. Only `pre_nms_top_k` uses it. When absent, all rows of an image are one level. |
| `min_bbox_size` | float | no | When present, the host drops each candidate whose width or height in source pixels is `<= min_bbox_size` (Behaviour, step 2). The value must be `>= 0`. The value `0` drops each candidate with zero or negative width or height. When absent, there is no size filter. |

Changed row of `decode` (`post.det.decode`, `detection-decode.md:43`):

| Field | Type | Required | Description |
|---|---|---|---|
| `clamp_boxes` | bool | no | The default is `true`. When `true`, the host clamps each unprojected box to the source image: `x1` and `x2` to `[0, src_w]`, `y1` and `y2` to `[0, src_h]`. `src_w` and `src_h` are the width and the height of the source image in pixels. The bounds are closed. The upper bound is `src_w` (or `src_h`), not `src_w - 1`. The clamp does not drop a row. A box can have zero area after the clamp. That row stays, with its score and its class. When `false`, the host does not clamp the unprojected boxes. |

### 2.3 Behaviour

Normative text of "Behaviour" in `post.det.selection.nms`. Steps 3 and 7 do not change.

```text
**`selection: nms`** — the primary output rows are pre-NMS candidates (for example RTMDet).

1. Resolve the scores. Drop each candidate with `score <= nms.score_threshold`. When
   `nms.pre_nms_top_k` is set, then keep in each level only the `nms.pre_nms_top_k` remaining
   candidates with the highest scores. A tie goes to the lower row index. Drop the other candidates
   of the level.
2. Convert the boxes from `box_format` to `xyxy`. Apply `box_scale` to get model-input pixels.
   When `nms.clamp_to_input` is true, clamp each box: `x1` and `x2` to `[0, W_in]`, `y1` and `y2`
   to `[0, H_in]`. The next steps use the clamped box. Do not unproject the boxes yet.
   When `nms.min_bbox_size` is set, unproject a copy of each box (Unprojection). The width of the
   candidate is `x2 - x1` of that copy, and its height is `y2 - y1`. Drop each candidate whose
   width or height is `<= nms.min_bbox_size`. The next steps use the box in model-input pixels.
3. Resolve the class indices from `class_field` and map them. If there is no class source, assign
   `person_class_id`. Apply `is_person_only`.
4. Run hard NMS at `nms.iou_threshold` in model-input coordinates. Run it for each class, unless
   `class_agnostic: true`. Visit the candidates in descending score order. A tie goes to the lower
   row index. A kept box suppresses each later candidate when their IoU is greater than
   `nms.iou_threshold`. The area of a box is `max(0, x2 - x1) * max(0, y2 - y1)`. Thus a box with
   `x2 < x1` or `y2 < y1` (an inverted box) has the area 0. The IoU is the area of the intersection
   divided by the area of the union. The intersection of two boxes is
   `max(0, min(x2, x2') - max(x1, x1')) * max(0, min(y2, y2') - max(y1, y1'))`. When the area of the
   union is 0, the IoU is 0.
5. Sort the survivors by score in descending order. A tie goes to the lower row index. Keep the
   first `nms.post_nms_top_k` survivors if that field is set. Each survivor keeps its row index `q`.
6. Unproject the boxes (Unprojection). When `clamp_boxes` is true, clamp them to the source image
   (`clamp_boxes` in Detection decode).
7. Apply `confidence_threshold_default`.

**Levels.** When `nms.level_strides` is present, the rows of the primary output of each image are
in levels: one level for each stride, in the order of `nms.level_strides`. The level with the stride
`s` holds `(H_in / s) * (W_in / s)` consecutive rows. `W_in` and `H_in` are the width and the height
of the model input. The first level starts at row 0. Each next level starts after the last row of
the level before it. The order of the rows in a level does not change the cap. When
`nms.level_strides` is absent, all rows of the image are one level. The host must stop with an error
when the sum of the level row counts is not the row count `Q` of the primary output.

**IoU and coordinates.** The unprojection of each resize method maps each axis with a scale and an
offset. The IoU of two boxes does not change under such a map. Thus the NMS in model-input pixels
keeps the same candidates as an NMS in source pixels, except for float rounding.
```

Changed paragraph after the step list (`selection-nms.md:53`):

"Steps 1, 4 and 5 are near the standard ONNX `NonMaxSuppression` operator. The operator takes scores as
`[B, C, Q]`. It suppresses boxes for each class when IoU is greater than `iou_threshold`. It drops
candidates at or below `score_threshold`. Its box-area convention does not add `1` to pixel widths or
heights. The operator reads a box as any diagonal pair of corners. Thus it gives an inverted box a
non-zero area, and step 4 gives it the area 0. The operator does not clamp. It has no per-level cap and
no size filter. A host that uses the operator must apply the score filter, the cap, the clamp and the
size filter of steps 1 and 2 to its inputs. It must give an inverted box the area 0. It must sort the
survivors as step 5 says."

There is no inverse in this section. The size filter of step 2 unprojects a copy of each box only to
measure it. The coordinate change of step 6 is the inverse of the resize (`post.unprojection`). The
clamp of step 2 changes the box that step 6 unprojects.

**Why the size filter uses source pixels.** mmdet rescales the boxes first
(`base_dense_head.py:467`, primary, part 1) and then compares `w` and `h` with `min_bbox_size`
(`:476-478`). The secondary copy does the same (`onnx_coco_eval_dense.py:107-109`, secondary; skellytracker
`notes/sidecar-exporter-coverage.md:185`, secondary). For the value `0` the pixel space does not change
the result, because every unprojection of the spec has a positive scale on each axis. For a value above
`0` it does (vector `min-bbox-size-is-strict-in-source-pixels`).

**Why the cap acts before the clamp, the size filter and the classes.** mmdet takes the top `nms_pre`
of each level (`base_dense_head.py:393-395`, primary, part 1) before the decode and its clamp (`:414`),
the rescale (`:467`) and the size filter (`:476-478`). The secondary copy does the same
(`onnx_coco_eval_dense.py:96-109`). A candidate that the size filter drops later still takes a slot of
the cap (vector `mmdet-mapping-cap-comes-before-the-size-filter`). The size filter acts on the clamped
box (vector `min-bbox-size-after-the-clamp-to-input`: a candidate that is fully outside the model input
gets the width 0 from the clamp, and `min_bbox_size: 0` drops it). mmdet has no class map. The section
keeps the order "scores, cap, boxes, clamp, size filter, classes" so that the cap depends only on the
scores and the levels.

**A run-time threshold above `nms.score_threshold`.** A host can filter at
`max(nms.score_threshold, confidence threshold)` before step 1 (`selection-nms.md:79`, Implementer
guidance). With the cap, this still gives the same detections. In each level, the candidates above the
higher threshold are the first candidates of the score order. The cap keeps the first
`pre_nms_top_k` candidates of that order. Thus the kept candidates above the higher threshold are the
same in both orders. The clamp and the size filter act on each candidate alone.

### 2.4 Validation rules

Changed rule (the added sentences are the last four):

- [ ] `V-post.det.selection.nms-1` A sidecar with `selection: nms` must have `nms` with
  `iou_threshold` and `score_threshold`. Each of these fields must be a float in `[0, 1]`. The
  sidecar must not have `class_logits_output`, `top_k` or `max_detections`. If `nms.class_agnostic`
  is present, it must be a boolean. If `nms.post_nms_top_k` is present, it must be a positive
  integer. If `nms.clamp_to_input` is present, it must be a boolean. If `nms.pre_nms_top_k` is
  present, it must be a positive integer. If `nms.level_strides` is present, it must be a non-empty
  array of positive integers, and `nms.pre_nms_top_k` must be present. If `nms.min_bbox_size` is
  present, it must be a number `>= 0`.

New rule:

- [ ] `V-post.det.selection.nms-2` If `nms.level_strides` is present, each stride must divide the
  height `H_in` and the width `W_in` of the model input of each size (the spatial dimensions of
  `input.shape`). For each size and each batch artifact with a known row count `Q` of the primary
  output (in `outputs[].shape` or in `output_shapes`), `Q` must equal the sum of
  `(H_in / s) * (W_in / s)` over the strides `s`.

Example: `rtmdet-person` with `level_strides: [8, 16, 32]` gives 2100 at `input.shape` `[B, 3, 320,
320]` and 8400 at `[B, 3, 640, 640]`, the values of its `output_shapes`.

`V-post.det.decode-5` already checks that `clamp_boxes` is a boolean. It does not change.

Existing rules that name a changed value: none. No rule names `clamp_boxes` values, the clamp order,
`nms_pre`, `min_bbox_size` or the candidate filters. `V-common.sizes_and_artifacts-3` (the family
invariant) does not change: the new fields are family-level. `V-post.pose.bottom_up-1` and `-2` do not
change: the pose rows still follow the kept rows.

### 2.5 Selectors

`decode.selection=nms` (no change). The new fields act when `decode.nms.clamp_to_input=true`, or when
`decode.nms.pre_nms_top_k` or `decode.nms.min_bbox_size` is present.

### 2.6 Legacy behaviour and version effect

- A sidecar with `schema_version < vNEXT` has no `decode.nms` (legacy: "Existing host NMS behaviour
  (implementation-defined)", `selection-nms.md:69`). Its meaning does not change.
- `clamp_boxes` absent before `vNEXT` stays "Existing host behaviour" (`detection-decode.md:87`). The
  closed bounds and the zero-area rule apply at `vNEXT`.
- The change goes into the `vNEXT` revision. A `vNEXT` sidecar without the new fields keeps the
  current behaviour: no clamp before the NMS, no cap and no size filter. The current reference
  examples do not change meaning.

New rows of the "Legacy behaviour" table of `post.det.selection.nms`:

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|---|---|---|
| `decode.nms.clamp_to_input` | Not available. | Default `false`. When `true`, clamp the candidate boxes to the model input before the NMS. |
| `decode.nms.pre_nms_top_k`, `decode.nms.level_strides`, `decode.nms.min_bbox_size` | Not available. | Optional. When absent: no per-level cap and no size filter. |

### 2.7 Changelog row

"Summary of changes" (`changelog.md`). `N` is the next free number at merge time (rows 1 to 19 exist):

| # | Area | Change | Driven by | Section |
|---|---|---|---|---|
| N | Decode | New optional `nms` fields: `clamp_to_input` (default `false`; clamp the candidate boxes to the model input before the NMS), `pre_nms_top_k` (a cap for each level after the score filter, ties to the lower row), `level_strides` (the levels of the candidate rows; without it, one level) and `min_bbox_size` (drop a candidate with a width or a height `<=` the value in source pixels, before the NMS). `clamp_boxes` has closed bounds `[0, src_w]` and `[0, src_h]`, and a zero-area row stays. The NMS step defines the visit order, the box area (an inverted box has the area 0) and the IoU of a zero union. | RTMDet person (mmdet `nms_pre=1000`, `min_bbox_size=0`, and the clamp to the padded input before the NMS) | Selection: NMS (`post/selection-nms.md#behaviour`), `decode` (`post/detection-decode.md#decode-detection`) |

"Considered and deliberately not added": delete the rows `nms.pre_nms_top_k` (`:49`) and
`nms.min_bbox_size` (`:50`). Add the row:

| Field / feature | Reason |
|---|---|
| NMS in source pixels (a field for the coordinates of the NMS) | The IoU does not change under the axis-aligned unprojection of every resize method. On COCO val2017, an NMS in source pixels kept the same rows as the NMS in model-input pixels on 5000 of 5000 images for `rtmdet-person` nano and medium. |

"`schema_version` history", the `vNEXT` row (`:68`): after "`nms` (`iou_threshold`, `score_threshold`,
`class_agnostic`, `post_nms_top_k`)" write "`nms` (`iou_threshold`, `score_threshold`,
`class_agnostic`, `post_nms_top_k`, `clamp_to_input`, `pre_nms_top_k`, `level_strides`,
`min_bbox_size`)", and after "`clamp_boxes`" add "(closed bounds, zero-area rows stay)".

### 2.8 Guidance text (informative)

Implementer guidance of `post.det.selection.nms`, new bullets:

- With `clamp_to_input: true`, the NMS of RTMDet-person keeps other rows than without it on 668 of
  5000 COCO val2017 images (nano) and 405 of 5000 (medium). The AP changes by -0.000038 (nano) and
  -0.000011 (medium) when `clamp_boxes` stays `true`. (OpenMMLab-Exporter, this proposal, part 5; to
  run: the script is not committed yet.)
- On COCO val2017 (5000 images), RTMDet-person has at most 1003 candidates above 0.05 in one level
  (nano) and 2142 (medium). `pre_nms_top_k: 1000` removes 3 candidates on 1 nano image and 13560 on 34
  medium images, but it keeps the same rows. A cap of 1000 over all rows (no `level_strides`) keeps
  other rows than the per-level cap on 10 medium images. (the same source)
- `min_bbox_size: 0` removes one nano candidate with `y2 < y1` and keeps the same rows on the other
  4999 images. (the same source)
- The host decoder of OpenMMLab-Exporter gives the same results as the reference implementation on
  COCO val2017 with the current text: 291170 (nano) and 182560 (medium) rows, maximum coordinate
  difference 6.8e-5 px, score difference 0. (OpenMMLab-Exporter `onnx_runtime/decode_nms.py`, d0f4343;
  this proposal, part 5.)
- The ONNX `NonMaxSuppression` operator reads a box as any diagonal pair of corners (onnx 1.23.2
  `onnx/defs/object_detection/defs.cc:140`, the `center_point_box` attribute: "the coordinates of any
  diagonal pair of box corners"; the reference operator `onnx/reference/ops/op_non_max_suppression.py:56-67`
  sorts the two values of each axis with `max_min`). Thus it gives an inverted box a non-zero area.
  With the boxes `[10, 10, 0, 0]` (score 0.875) and `[0, 0, 10, 10]` (score 0.75) at IoU threshold 0.6,
  the host decoder of OpenMMLab-Exporter keeps only the first box. Step 4 gives the first box the area
  0, so both boxes stay (vector `inverted-box-has-area-zero`). A host that uses the operator must give
  an inverted box the area 0. For example, keep it out of the operator input and add it to the
  survivors of the operator, because its IoU with each box is 0. Drop it only when `nms.min_bbox_size`
  is set. (onnx 1.23.2, installed copy in the OpenMMLab-Exporter `.venv`; OpenMMLab-Exporter
  `onnx_runtime/decode_nms.py`, `d0f4343`, ONNX Runtime 1.31.0, CPU; this proposal, part 4)

Authoring guidance of `post.det.selection.nms`. The bullet of `:90` becomes:

- mmdet RTMDet: the box coder clamps the decoded boxes to the padded input. The rescaled boxes are not
  clamped to the source image. Write `nms.clamp_to_input: true` and `clamp_boxes: false`. `test_cfg`
  `nms_pre` maps to `nms.pre_nms_top_k`, with `nms.level_strides` from the strides of the head (one
  level for each feature map, in the order of the graph outputs). `min_bbox_size` maps to
  `nms.min_bbox_size`. Write `min_bbox_size: 0` when the config has `0`: the value drops boxes with no
  width or no height. Read the level layout from the graph (the `Concat` of the per-level outputs).
  For RTMDet-person: `clamp_to_input: true`, `clamp_boxes: false`, `pre_nms_top_k: 1000`,
  `level_strides: [8, 16, 32]`, `min_bbox_size: 0`. The mmdet output of rtmdet-person ends at
  `T * src_w / n_w` (the right edge of the padded input in source pixels) to 3.1e-5 px, and 2214 of
  290882 nano boxes end past the source width. (OpenMMLab-Exporter
  `mmdeploy-convert/model_cfgs/rtmdet_nano_320-8xb32_coco-person.py:25-26`, `d0f4343`; source pass
  `rtmdet-person-nano_source.accuracy.torch-cuda.b1.20261021T231118Z-<host>.predictions.json`,
  untracked, producer e67fc2a; mmdet v3.3.0 `base_dense_head.py:393-395, 414, 467, 476-478`,
  `transforms.py:179-180`; mmcv v2.1.0 `processing.py:388`; this proposal, part 1)

Implementer guidance of `post.det.decode`, the bullet of `:100` becomes:

- Clamp bounds in use: OpenMMLab-Exporter clips to `[0, src_w]` and `[0, src_h]`. Roboflow-Exporter
  clips to `[0, scale]` of the original image. Ultralytics `scale_boxes` clips to the source image.
  mmdet RTMDet clamps to the padded model input before the NMS and does not clamp to the source image
  (`nms.clamp_to_input: true`, `clamp_boxes: false`). (the current citations, plus this proposal,
  part 1)

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the exporter repo (the part 3 code of `specs/model-sidecar/proposals/<slug>/proposal.md`) | the part 3 code of `specs/model-sidecar/proposals/nms-clamp-order/proposal.md` |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | `specs/model-sidecar/reference/post_det_selection_nms.py` |
| Functions (one for each algorithm) | `to_xyxy` (box formats), `to_model_pixels` (`box_scale`), `clamp_xyxy` (the closed clamp of step 2 and of `clamp_boxes`), `box_area` (an inverted box has the area 0), `iou_one_to_many` (a zero union gives 0), `score_order` (the tie order), `level_row_counts` (the "Levels" note and `V-post.det.selection.nms-2`), `level_of_rows` (the level of each row), `pre_nms_cap` (step 1, the cap), `min_size_keep` (step 2, the size filter), `hard_nms` (step 4), `resolve_classes` (step 3), `split_detection_rows` (a `detections` primary output), `select_nms` (steps 1 to 5), `axis_affine_unprojector` (a test inverse for the vectors; the resize sections own the real inverse), `decode_nms` (steps 1 to 7). Constant `NMS_KEYS` (the `nms` fields that a vector case can give without the `nms` key). |

The section `post.det.selection.nms` has no reference implementation yet
(`specs/model-sidecar/reference/` does not exist). Thus the file implements the full section as changed:
every `box_format`, every `box_scale`, a `boxes` + `scores` output and a `detections` output, the
class sources, `class_id_map`, `class_id_base`, `is_person_only`, `class_agnostic` both ways,
`post_nms_top_k`, `clamp_to_input`, `pre_nms_top_k`, `level_strides`, `min_bbox_size`, `clamp_boxes`
and `confidence_threshold_default` with its default. It is also the reference-implementation step of
this section (exporter guide, "Reference implementations": "Skip the step if one of your proposals
changes the section"). Source commit: the host code `onnx_runtime/decode_nms.py` at `d0f4343` for the
parts of the current text. The new fields have no host code (`source commit: none (no host code)` for
them, in the note at the top of the file). The file uses NumPy and the standard library only. It
computes in float64.

`clamp_xyxy` also does the clamp of `clamp_boxes` (`post.det.decode`), because step 6 applies it. The
guide puts one section in one module (`exporter-guide/sidecars/reference-implementations.md:30-32`). Thus, when skellytracker lands a
reference file for `post.det.decode` (`post_det_decode.py`), step 6 imports the clamp from that file
(plan T32 P8). The file was merged from the two part 3 files of the earlier proposals. The merged file
is the superset file of `nms-candidate-filters` with a new note at the top. It has no
`gather_pose_rows` (removed with the bottom-up notes; see part 4). Part 4 shows that it gives the same
outputs as both earlier files.

```python
"""Reference implementation of the section `post.det.selection.nms`, as changed by the proposal
`specs/model-sidecar/proposals/nms-clamp-order/proposal.md` (part 2).

This file uses ASD-STE100 Simplified Technical English in its comments.

- Section ID: `post.det.selection.nms` (changed section). The file implements the full section as the
  proposal changes it: every `box_format` and `box_scale`, a `boxes` + `scores` output and a
  `detections` output, the class fields, `class_agnostic`, `post_nms_top_k`, the new fields
  `nms.clamp_to_input`, `nms.pre_nms_top_k`, `nms.level_strides` and `nms.min_bbox_size`, the new rule
  `V-post.det.selection.nms-2` (in `level_row_counts`), `clamp_boxes` and
  `confidence_threshold_default`.
- It also implements the `clamp_boxes` text of `post.det.decode` that the proposal defines (the closed
  bounds and the zero-area result), because step 6 of this section applies it (`clamp_xyxy`). When
  skellytracker lands a reference file for `post.det.decode` (`post_det_decode.py`), step 6 imports
  the clamp from that file, and `clamp_xyxy` stays here only for the clamp of step 2.
- Target file: `specs/model-sidecar/reference/post_det_selection_nms.py`.
- Source commit: OpenMMLab-Exporter `d0f4343812cc582b4b0020e5b532c83572d11fd2`,
  `onnx_runtime/decode_nms.py` (`NmsDecoder`, `build_nms_decode_model`), for the parts of the current
  text. The host code has no `clamp_to_input`, `pre_nms_top_k`, `level_strides` or `min_bbox_size`.
  The functions for these fields come from the text of part 2 of the proposal (source commit for
  them: none, no host code).
- Vector results (2026-10-24): part 4 of the proposal (the 20 cases of the skellytracker vector file
  and the 29 new cases pass).
- Parity result: part 5 of the proposal (`to run`; the numbers of an uncommitted scratch run are
  given there).
- Only NumPy and the Python standard library. Do not import from the exporter or from skellytracker.
  The file name has hyphens: load it with `importlib.util.spec_from_file_location`.

The functions work on one image. `B` is a loop outside this file.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

import numpy as np

DEFAULT_CONFIDENCE_THRESHOLD = 0.7
"""`decode.confidence_threshold_default` when the field is absent (`post.det.decode`)."""

NMS_KEYS = (
    "iou_threshold",
    "score_threshold",
    "class_agnostic",
    "post_nms_top_k",
    "clamp_to_input",
    "pre_nms_top_k",
    "level_strides",
    "min_bbox_size",
)
"""The fields of the `nms` object. A vector case can give them at the top level of `params`."""


def to_xyxy(boxes: Any, box_format: str = "xyxy") -> np.ndarray:
    """`post.det.selection.nms` step 2: convert the boxes from `box_format` to `xyxy` (float64)."""
    b = np.asarray(boxes, np.float64).reshape(-1, 4)
    if box_format == "xyxy":
        return b.copy()
    if box_format == "xywh":
        return np.stack([b[:, 0], b[:, 1], b[:, 0] + b[:, 2], b[:, 1] + b[:, 3]], axis=1)
    if box_format == "cxcywh":
        half_w, half_h = b[:, 2] / 2.0, b[:, 3] / 2.0
        return np.stack([b[:, 0] - half_w, b[:, 1] - half_h, b[:, 0] + half_w, b[:, 1] + half_h], axis=1)
    raise ValueError(f"unknown box_format {box_format!r}")


def to_model_pixels(boxes_xyxy: np.ndarray, box_scale: str, input_w: int, input_h: int) -> np.ndarray:
    """`post.det.selection.nms` step 2: apply `box_scale` (`post.unprojection`) to get model-input pixels."""
    b = np.asarray(boxes_xyxy, np.float64).copy()
    if box_scale == "pixel":
        return b
    if box_scale == "normalized_01":
        b[:, 0::2] *= input_w
        b[:, 1::2] *= input_h
        return b
    if box_scale == "normalized_11":
        b[:, 0::2] = (b[:, 0::2] + 1.0) / 2.0 * input_w
        b[:, 1::2] = (b[:, 1::2] + 1.0) / 2.0 * input_h
        return b
    raise ValueError(f"unknown box_scale {box_scale!r}")


def clamp_xyxy(boxes_xyxy: np.ndarray, width: float, height: float) -> np.ndarray:
    """Clamp each coordinate to closed bounds: `x1`, `x2` to `[0, width]`; `y1`, `y2` to `[0, height]`.

    One function serves two steps of `post.det.selection.nms`:
    - step 2 with `nms.clamp_to_input: true`: the bounds are the model input (`W_in`, `H_in`);
    - step 6 with `clamp_boxes: true` (`post.det.decode`): the bounds are the source image
      (`src_w`, `src_h`), not `src_w - 1` or `src_h - 1`.
    The clamp never drops a row. A box can have zero area after the clamp. It stays.
    When a reference file of `post.det.decode` exists, step 6 imports its clamp in place of this one.
    """
    b = np.asarray(boxes_xyxy, np.float64).copy()
    b[:, 0::2] = np.clip(b[:, 0::2], 0.0, float(width))
    b[:, 1::2] = np.clip(b[:, 1::2], 0.0, float(height))
    return b


def box_area(boxes_xyxy: np.ndarray) -> np.ndarray:
    """`post.det.selection.nms` step 4: `max(0, x2 - x1) * max(0, y2 - y1)`. No `+ 1` on a side."""
    b = np.asarray(boxes_xyxy, np.float64)
    return np.maximum(b[:, 2] - b[:, 0], 0.0) * np.maximum(b[:, 3] - b[:, 1], 0.0)


def iou_one_to_many(box: np.ndarray, boxes: np.ndarray) -> np.ndarray:
    """`post.det.selection.nms` step 4: IoU of one box with each box. A union of 0 gives an IoU of 0."""
    box = np.asarray(box, np.float64).reshape(4)
    boxes = np.asarray(boxes, np.float64).reshape(-1, 4)
    inter_w = np.maximum(np.minimum(box[2], boxes[:, 2]) - np.maximum(box[0], boxes[:, 0]), 0.0)
    inter_h = np.maximum(np.minimum(box[3], boxes[:, 3]) - np.maximum(box[1], boxes[:, 1]), 0.0)
    inter = inter_w * inter_h
    union = box_area(box[None, :])[0] + box_area(boxes) - inter
    out = np.zeros(len(boxes), np.float64)
    positive = union > 0.0
    out[positive] = inter[positive] / union[positive]
    return out


def score_order(scores: np.ndarray, rows: np.ndarray) -> np.ndarray:
    """`post.det.decode` Selection behaviour: descending score; a tie goes to the lower row index."""
    return np.lexsort((np.asarray(rows), -np.asarray(scores, np.float64)))


def level_row_counts(input_size: tuple[int, int], level_strides: Sequence[int] | None, row_count: int) -> list[int]:
    """`post.det.selection.nms` "Levels": the row count of each level of one image.

    With `nms.level_strides`, level `l` with stride `s` holds `(H_in / s) * (W_in / s)` rows. Each
    stride must divide `H_in` and `W_in`, and the sum must equal the row count `Q` of the primary
    output (`V-post.det.selection.nms-2`). Without `nms.level_strides`, all `Q` rows are one level.
    """
    if not level_strides:
        return [int(row_count)]
    input_h, input_w = int(input_size[0]), int(input_size[1])
    counts = []
    for stride in level_strides:
        stride = int(stride)
        if stride <= 0 or input_h % stride or input_w % stride:
            raise ValueError(f"stride {stride} does not divide the model input {input_h}x{input_w}")
        counts.append((input_h // stride) * (input_w // stride))
    if sum(counts) != int(row_count):
        raise ValueError(f"the levels hold {sum(counts)} rows, the primary output has {row_count}")
    return counts


def level_of_rows(rows: np.ndarray, counts: Sequence[int]) -> np.ndarray:
    """`post.det.selection.nms` "Levels": the level index of each row. Level 0 starts at row 0."""
    return np.searchsorted(np.cumsum(counts), np.asarray(rows, np.int64), side="right")


def pre_nms_cap(scores: np.ndarray, rows: np.ndarray, levels: np.ndarray, top_k: int) -> np.ndarray:
    """`post.det.selection.nms` step 1 with `nms.pre_nms_top_k`: a keep mask over the given candidates.

    In each level, keep the `top_k` candidates with the highest scores. A tie goes to the lower row
    index (`score_order`). Drop the other candidates of the level.
    """
    scores = np.asarray(scores, np.float64)
    keep = np.zeros(len(scores), bool)
    for level in np.unique(levels):
        mine = np.flatnonzero(levels == level)
        keep[mine[score_order(scores[mine], rows[mine])][: int(top_k)]] = True
    return keep


def min_size_keep(
    boxes_model: np.ndarray, unproject: Callable[[np.ndarray], np.ndarray], min_bbox_size: float
) -> np.ndarray:
    """`post.det.selection.nms` step 2 with `nms.min_bbox_size`: a keep mask over the candidates.

    Unproject a copy of each box (model-input pixels, after the clamp of `nms.clamp_to_input` when it
    applies) to source pixels. Keep a candidate only when `x2 - x1 > min_bbox_size` and
    `y2 - y1 > min_bbox_size` of that copy (strict). The value 0 drops each box with zero or negative
    width or height.
    """
    if not len(boxes_model):
        return np.zeros(0, bool)
    source = unproject(np.asarray(boxes_model, np.float64))
    width = source[:, 2] - source[:, 0]
    height = source[:, 3] - source[:, 1]
    return (width > float(min_bbox_size)) & (height > float(min_bbox_size))


def hard_nms(
    boxes_xyxy: np.ndarray,
    scores: np.ndarray,
    rows: np.ndarray,
    class_ids: np.ndarray,
    iou_threshold: float,
    class_agnostic: bool = False,
) -> np.ndarray:
    """`post.det.selection.nms` step 4: greedy hard NMS. Return the positions of the survivors.

    The host visits the candidates in `score_order`. A kept box suppresses each later candidate of the
    same class (of any class with `class_agnostic: true`) when their IoU is greater than
    `iou_threshold` (strict `>`).
    """
    order = score_order(scores, rows)
    alive = np.ones(len(order), bool)
    kept: list[int] = []
    for i, position in enumerate(order):
        if not alive[i]:
            continue
        kept.append(int(position))
        later = order[i + 1 :]
        mask = alive[i + 1 :].copy()
        if not class_agnostic:
            mask &= class_ids[later] == class_ids[position]
        if not mask.any():
            continue
        targets = np.flatnonzero(mask)
        iou = iou_one_to_many(boxes_xyxy[position], boxes_xyxy[later[targets]])
        alive[i + 1 + targets[iou > iou_threshold]] = False
    return np.asarray(kept, np.int64)


def resolve_classes(
    count: int,
    class_indices: Sequence[int] | None,
    params: Mapping[str, Any],
) -> tuple[np.ndarray, np.ndarray]:
    """`post.det.selection.nms` step 3: emitted class ids and a keep mask (`post.det.decode` fields).

    No class source: every candidate gets `person_class_id`. With a class source: `class_id_map`
    (the value `-1` drops the candidate) takes precedence over `class_id_base`. With
    `is_person_only: true`, the host drops each candidate whose class is not `person_class_id`.
    """
    person = int(params.get("person_class_id", 0))
    if class_indices is None:
        return np.full(count, person, np.int64), np.ones(count, bool)
    model = np.asarray(class_indices, np.float64).astype(np.int64)
    id_map = params.get("class_id_map")
    if id_map is not None:
        emitted = np.asarray(id_map, np.int64)[model]
    else:
        emitted = model + int(params.get("class_id_base", 0))
    keep = emitted >= 0
    if params.get("is_person_only", False):
        keep &= emitted == person
    return emitted, keep


def split_detection_rows(
    rows: Any,
    fields: Sequence[str],
    score_field: str,
    class_field: str | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """Read a `detections` primary output (`post.det.outputs`): boxes `fields[0:4]`, the score and the class."""
    table = np.asarray(rows, np.float64).reshape(-1, len(fields))
    boxes = table[:, 0:4]
    scores = table[:, list(fields).index(score_field)]
    classes = table[:, list(fields).index(class_field)] if class_field else None
    return boxes, scores, classes


def select_nms(
    boxes: Any,
    scores: Any,
    params: Mapping[str, Any],
    *,
    input_size: tuple[int, int],
    class_indices: Sequence[int] | None = None,
    unproject: Callable[[np.ndarray], np.ndarray] | None = None,
) -> dict[str, np.ndarray]:
    """`post.det.selection.nms` steps 1 to 5 for one image.

    Args:
        boxes: `[Q, 4]` boxes of the primary output, in `box_format` and `box_scale`.
        scores: `[Q]` resolved scores.
        params: the `decode` fields, with the `nms` fields at the top level or under `nms`.
        input_size: `[H_in, W_in]` of the model input.
        class_indices: `[Q]` model class indices, or `None` when there is no class source.
        unproject: the inverse of the resize (`post.unprojection`). Only `nms.min_bbox_size` uses it
            in these steps.

    Returns:
        `kept_rows` (row index `q` of each survivor, in output order), `scores`, `class_ids` and
        `boxes_model` (`xyxy` in model-input pixels, after the clamp of step 2 when it applies).
    """
    nms = dict(params.get("nms") or {})
    for key in NMS_KEYS:
        if key in params:
            nms.setdefault(key, params[key])
    input_h, input_w = int(input_size[0]), int(input_size[1])
    score = np.asarray(scores, np.float64).reshape(-1)
    rows = np.arange(len(score), dtype=np.int64)

    # Step 1: the strict score filter.
    live = score > float(nms["score_threshold"])

    # Step 1, continued: the per-level cap `pre_nms_top_k` over the candidates that stay.
    if nms.get("pre_nms_top_k") is not None:
        counts = level_row_counts(input_size, nms.get("level_strides"), len(score))
        index = np.flatnonzero(live)
        cap = pre_nms_cap(score[index], rows[index], level_of_rows(rows[index], counts), int(nms["pre_nms_top_k"]))
        live[index[~cap]] = False
    elif nms.get("level_strides"):
        raise ValueError("nms.level_strides needs nms.pre_nms_top_k (V-post.det.selection.nms-1)")

    # Step 2: xyxy in model-input pixels; the optional clamp to the model input. No unprojection yet.
    box = to_model_pixels(to_xyxy(boxes, params.get("box_format", "xyxy")), params.get("box_scale", "pixel"),
                          input_w, input_h)
    if nms.get("clamp_to_input", False):
        box = clamp_xyxy(box, input_w, input_h)

    # Step 2, continued: the size filter `min_bbox_size` on an unprojected copy of the box.
    if nms.get("min_bbox_size") is not None:
        if unproject is None:
            raise ValueError("nms.min_bbox_size needs the inverse of the resize")
        index = np.flatnonzero(live)
        live[index[~min_size_keep(box[index], unproject, float(nms["min_bbox_size"]))]] = False

    # Step 3: the class of each candidate, the class map and `is_person_only`.
    class_ids, class_keep = resolve_classes(len(score), class_indices, params)
    live &= class_keep

    # Step 4: hard NMS in model-input pixels.
    index = np.flatnonzero(live)
    kept = index[hard_nms(box[index], score[index], rows[index], class_ids[index],
                          float(nms["iou_threshold"]), bool(nms.get("class_agnostic", False)))]

    # Step 5: sort the survivors (descending score, then the lower row) and keep the first k.
    kept = kept[score_order(score[kept], rows[kept])]
    top_k = nms.get("post_nms_top_k")
    if top_k is not None:
        kept = kept[: int(top_k)]
    return {"kept_rows": rows[kept], "scores": score[kept], "class_ids": class_ids[kept], "boxes_model": box[kept]}


def axis_affine_unprojector(ax: float, bx: float, ay: float, by: float) -> Callable[[np.ndarray], np.ndarray]:
    """An axis-aligned inverse `x_src = ax * x + bx`, `y_src = ay * y + by` (for a vector case).

    The resize sections give the real inverse (for `letterbox`: `ax = src_w / n_w`,
    `bx = -left * src_w / n_w`). This file does not implement the resize sections.
    """

    def unproject(boxes_xyxy: np.ndarray) -> np.ndarray:
        b = np.asarray(boxes_xyxy, np.float64).copy()
        b[:, 0::2] = b[:, 0::2] * ax + bx
        b[:, 1::2] = b[:, 1::2] * ay + by
        return b

    return unproject


def decode_nms(
    boxes: Any,
    scores: Any,
    params: Mapping[str, Any],
    *,
    input_size: tuple[int, int],
    source_size: tuple[int, int],
    unproject: Callable[[np.ndarray], np.ndarray],
    class_indices: Sequence[int] | None = None,
    confidence_threshold: float | None = None,
) -> dict[str, np.ndarray]:
    """`post.det.selection.nms` steps 1 to 7 for one image.

    Args:
        source_size: `[src_h, src_w]` of the source image.
        unproject: the inverse of the resize (`post.unprojection`), model-input pixels to source pixels.
        confidence_threshold: a caller override of `confidence_threshold_default` (host policy).

    Returns:
        The result of :func:`select_nms` after steps 6 and 7, plus `boxes_source` (the unprojected
        boxes) and `boxes` (the final boxes: `boxes_source` clamped when `clamp_boxes` is true).
    """
    out = select_nms(boxes, scores, params, input_size=input_size, class_indices=class_indices,
                     unproject=unproject)

    # Step 6: unproject; then the clamp to the source image when `clamp_boxes` is true (default true).
    source = unproject(out["boxes_model"]) if len(out["boxes_model"]) else np.zeros((0, 4), np.float64)
    final = source
    if params.get("clamp_boxes", True):
        final = clamp_xyxy(source, source_size[1], source_size[0])

    # Step 7: the final filter. It is strict.
    threshold = params.get("confidence_threshold_default", DEFAULT_CONFIDENCE_THRESHOLD)
    if confidence_threshold is not None:
        threshold = confidence_threshold
    keep = out["scores"] > float(threshold)
    result = {key: value[keep] for key, value in out.items()}
    result["boxes_source"] = source[keep]
    result["boxes"] = final[keep]
    return result


__all__ = [
    "DEFAULT_CONFIDENCE_THRESHOLD",
    "NMS_KEYS",
    "axis_affine_unprojector",
    "box_area",
    "clamp_xyxy",
    "decode_nms",
    "hard_nms",
    "iou_one_to_many",
    "level_of_rows",
    "level_row_counts",
    "min_size_keep",
    "pre_nms_cap",
    "resolve_classes",
    "score_order",
    "select_nms",
    "split_detection_rows",
    "to_model_pixels",
    "to_xyxy",
]
```

## 4. Vectors

**Results (2026-10-24).** Scratch `run_merge.py` (not committed, in
`...\scratchpad\nms-merge\`, in the local temporary folder of session `3bd420c5`)
loads the reference file with `importlib.util.spec_from_file_location`. It reads the cases from the
YAML block below and from the vector file of skellytracker `dom/18-agents-adr-bootstrap-kit`.

| Set | Reference file | Host `NmsDecoder` (`onnx_runtime/decode_nms.py`, `d0f4343`, ONNX Runtime 1.31.0, CPU provider) |
|---|---|---|
| The 20 cases of `specs/model-sidecar/vectors/post.det.selection.nms.yaml` | 20 of 20 pass | Not run again. The intake records a scratch run: 13 of the 14 runnable cases pass; `no-class-source-uses-person-class-id` fails (the host never reads `person_class_id`); 6 cases need options that the host does not have (the untracked intake of `rtmdet-person` of OpenMMLab-Exporter (plan facts), "Proposals and reference files"). |
| The 29 new cases below | 29 of 29 pass | 10 cases need no new field. 9 of them pass: `clamp-to-input-absent-keeps-the-raw-boxes`, `zero-union-gives-iou-zero`, the 5 `clamp-boxes-*` cases, `pre-nms-top-k-absent-keeps-every-candidate`, `min-bbox-size-absent-keeps-an-inverted-box`. 1 fails: `inverted-box-has-area-zero` (the host gives `kept_rows [0]`, a known host gap, plan T30 F3; `onnx_runtime/` is not changed). 19 cases not run: they need `clamp_to_input`, `pre_nms_top_k`, `level_strides` or `min_bbox_size` (no host code). |

**The merged file gives the outputs of both earlier files** (scratch `run_merge.py`, full output
equality: every returned array, not only the expected keys):

- The 20 existing cases: equal to the earlier `nms-clamp-order` file and to the earlier
  `nms-candidate-filters` file, 20 of 20 each.
- The 14 `decode_nms` cases of the earlier `nms-clamp-order` set: equal to both earlier files, 14 of
  14 each. The 14 cases of the earlier `nms-candidate-filters` set: equal to that file, 14 of 14.
- `inverted-box-has-area-zero`: equal to both earlier files.
- 3000 random problems (random boxes, some inverted; random scores with ties; all fields; random
  levels and inverses): equal to the earlier `nms-candidate-filters` file on 3000 of 3000, and to the
  earlier `nms-clamp-order` file on the 887 problems without a field that it does not have. 0
  differences.
- Each earlier file still passes its own cases.

**Removed case.** The earlier `nms-clamp-order` set had a 15th case, `kept-rows-select-the-pose-rows`
(function `gather_pose_rows`, `post.pose.bottom_up`). No family in scope of this proposal is a
bottom-up model, so the case and the function are not in this proposal (plan T32 P5 (b)). Both earlier
files passed it.

The host gives the scores at rtol 1e-6 and the boxes at atol 1e-4 (its float32 output). The reference
gives every expected value exactly in float64: each value is a small integer or a dyadic fraction.

**Host tie order (measured 2026-10-24, scratch, secondary).** The host `NmsDecoder` keeps the order of
the ONNX Runtime `NonMaxSuppression` output, with a stable sort by score (`onnx_runtime/decode_nms.py`
at `d0f4343`). ONNX Runtime 1.31.0 visits tied scores lower row first, on CPU and on CUDA. Thus for
rank-2 (single-class) scores the host gives the order of steps 4 and 5: against a host copy with the
explicit rule and against `select_nms`, 0 rows differ on all 5000 val2017 images for the four
rtmdet-person files (nano and medium, fp32 and fp16). Exact score ties are common in fp16 (about 32 %
of the rtmdet-person candidates above the threshold) and rare in fp32 (about 0.03 %). The host differs
only for rank-3 scores with a tie across classes, because ONNX Runtime groups its output by class; no
family in scope uses rank-3 scores. This proposal keeps the rule. A host whose NMS output is grouped by
class must sort by the rule (part 6). The tie order was measured only on ONNX Runtime 1.31.0.

**Mutation check of the expected values.** The runner changed one expected value at a time. Each time,
exactly one case of the 49 fails, the changed case: `pre-nms-top-k-keeps-the-top-of-each-level`
(`kept_rows` `[1, 4]` to `[1, 3]`), `clamp-to-input-suppresses-a-box-that-crosses-the-edge` (`boxes`
`[[0, 0, 10, 10]]` to `[[0, 0, 10, 11]]`) and `inverted-box-has-area-zero` (`kept_rows` `[0, 1]` to
`[0]`).

**Mutation check of the code.** 28 mutants of the reference file: the 15 mutants of the earlier
`nms-clamp-order` file (M), the 12 of the earlier `nms-candidate-filters` file (K and S) and one new
mutant (D1). Each mutant fails at least one case of the 49 (20 existing and 29 new):

| Mutant | Cases that fail |
|---|---|
| M1 no clamp before the NMS | 8 (for example `clamp-to-input-suppresses-a-box-that-crosses-the-edge`) |
| M2 input bound `W_in - 1` | 3 (`clamp-to-input-closed-bounds-width-and-height` and 2 more) |
| M3 source bound `src_w - 1` | 4 (`clamp-boxes-upper-bound-is-the-image-size` and 3 more) |
| M4 drop zero-area rows after the clamp | 5 (`clamp-to-input-zero-area-box-stays`, `zero-union-gives-iou-zero`, `clamp-boxes-zero-area-row-stays`, `min-bbox-size-absent-keeps-an-inverted-box`, `inverted-box-has-area-zero`) |
| M5 suppress at IoU `>=` | 3 (`iou-equal-to-threshold-is-kept`, `box-format-cxcywh`, `clamp-to-input-iou-equal-to-threshold-is-kept`) |
| M6 `+ 1` on each side (area and intersection) | 5 (`box-area-adds-nothing` and 4 more) |
| M7 a tie goes to the higher row | 3 (`equal-scores-lower-row-wins`, `post-nms-top-k-keeps-the-highest`, `pre-nms-top-k-tie-goes-to-the-lower-row`) |
| M8 the input clamp after the unprojection | 9 (`clamp-to-input-comes-before-the-unprojection` and 8 more) |
| M9 never clamp to the source | 4 |
| M10 a zero union gives IoU 1 | 1 (`zero-union-gives-iou-zero`) |
| M11 `clamp_boxes` default `false` | 1 (`clamp-boxes-default-is-true-with-an-offset`) |
| M12 always clamp to the input | 1 (`clamp-to-input-absent-keeps-the-raw-boxes`) |
| M13 clamp to the source before the NMS | 14 (`clamp-boxes-comes-after-the-nms` and 13 more) |
| M14 final filter `>=` | 1 (`confidence-threshold-is-strict`) |
| M15 score filter `>=` | 1 (`score-equal-to-score-threshold-is-dropped`) |
| K1 the cap over all rows (ignore `level_strides`) | 6 (for example `pre-nms-top-k-keeps-the-top-of-each-level`) |
| K2 no cap | 7 |
| K3 a tie of the cap goes to the higher row | 1 (`pre-nms-top-k-tie-goes-to-the-lower-row`) |
| K4 the levels in reversed stride order | 5 |
| K5 level rows `(W_in / s) ** 2` | 1 (`pre-nms-top-k-non-square-input`) |
| K6 the cap after the NMS | 2 (`pre-nms-top-k-acts-before-the-nms`, `mmdet-mapping-cap-comes-before-the-size-filter`) |
| S1 the size filter keeps `w >= min_bbox_size` | 5 |
| S2 the size filter in model-input pixels | 1 (`min-bbox-size-is-strict-in-source-pixels`) |
| S3 the size filter before the clamp to the input | 2 (`min-bbox-size-after-the-clamp-to-input`, `mmdet-mapping-cap-comes-before-the-size-filter`) |
| S4 no size filter | 6 |
| S5 the size filter after the NMS | 1 (`min-bbox-size-acts-before-the-nms`) |
| S6 the size filter before the cap | 1 (`mmdet-mapping-cap-comes-before-the-size-filter`) |
| D1 read the corners as any diagonal pair (sort the two values of each axis before the area and the intersection, as the ONNX operator does) | 1 (`inverted-box-has-area-zero`) |

The first version of M6 added `+ 1` only to the areas and survived. The `+ 1` convention adds it to the
intersection too. The corrected mutant fails 5 cases. The first version of K6 left the original cap in
place and survived. The corrected mutant removes the cap of step 1 and applies it to the survivors.

**New cases** (add to `specs/model-sidecar/vectors/post.det.selection.nms.yaml` through
`tools/make_vectors.py`; part 2.1). `input_size` is `[H_in, W_in]`, `source_size` is `[src_h, src_w]`.
`unproject: [ax, bx, ay, by]` is the inverse `x_src = ax * x + bx`, `y_src = ay * y + by` (for
`letterbox`, `ax = src_w / n_w` and `bx = -left * src_w / n_w`). `boxes_model` holds the kept boxes in
model-input pixels after step 2, `boxes_source` the unprojected boxes, `boxes` the final boxes after
step 6. A case without one of these keys does not check it. The `nms` fields are given without the
`nms` key. The 20 existing cases do not change. They give no `function` key. They run through
`decode_nms` with `clamp_boxes: false`, an identity inverse and a large source (their `boxes_xyxy` is
`boxes_model`).

```yaml
section: post.det.selection.nms
spec_revision: vNEXT
generated_by: the part 3 code of `specs/model-sidecar/proposals/nms-clamp-order/proposal.md`   # specs/model-sidecar/reference/post_det_selection_nms.py on acceptance
unverified: "no implementation gives the same results on all 29 cases. The host NmsDecoder (OpenMMLab-Exporter onnx_runtime/decode_nms.py, exporter commit d0f4343) gives the same results on the 9 cases that use no new nms field and have no inverted box. It differs on inverted-box-has-area-zero (known host gap, plan T30 F3). It has no code for clamp_to_input, pre_nms_top_k, level_strides or min_bbox_size (19 cases). The reference file comes from this host code, so they count as one implementation."
  # The host gives the same results on 9 cases: the 9 cases with function decode_nms and no new
  # nms field (clamp-to-input-absent-keeps-the-raw-boxes, zero-union-gives-iou-zero, the 5
  # clamp-boxes-* cases, pre-nms-top-k-absent-keeps-every-candidate,
  # min-bbox-size-absent-keeps-an-inverted-box). It does not give the expected result on
  # inverted-box-has-area-zero (kept_rows [0]; see the case). The other 19 cases: unverified: no host
  # implementation of clamp_to_input, pre_nms_top_k, level_strides or min_bbox_size. The reference
  # file comes from this host code, so they count as one implementation.
  # History: until 2026-10-25 this block listed the host under verified_against. The template allows
  # verified_against only for an implementation that gives the same results on the cases.
cases:
  - id: clamp-to-input-suppresses-a-box-that-crosses-the-edge
    # row 0 becomes [0, 0, 10, 10] before the NMS: IoU 100 / 120 = 0.833 > 0.6 suppresses row 1.
    # Without the clamp the IoU is 100 / 220 = 0.4545 and both rows stay (next case).
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_to_input: true, clamp_boxes: false}
    input: {input_size: [20, 20], source_size: [20, 20], unproject: [1, 0, 1, 0], boxes: [[-10, 0, 10, 10], [0, 0, 12, 10]], scores: [0.875, 0.75]}
    expect: {kept_rows: [0], scores: [0.875], class_ids: [0], boxes_model: [[0, 0, 10, 10]], boxes: [[0, 0, 10, 10]]}
  - id: clamp-to-input-absent-keeps-the-raw-boxes
    # clamp_to_input is absent (default false): the NMS sees [-10, 0, 10, 10]; IoU 0.4545 <= 0.6
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false}
    input: {input_size: [20, 20], source_size: [20, 20], unproject: [1, 0, 1, 0], boxes: [[-10, 0, 10, 10], [0, 0, 12, 10]], scores: [0.875, 0.75]}
    expect: {kept_rows: [0, 1], scores: [0.875, 0.75], class_ids: [0, 0], boxes_model: [[-10, 0, 10, 10], [0, 0, 12, 10]], boxes: [[-10, 0, 10, 10], [0, 0, 12, 10]]}
  - id: clamp-to-input-iou-equal-to-threshold-is-kept
    # after the clamp the IoU is 100 / 200 = 0.5, equal to the threshold: suppression needs IoU > 0.5
    function: decode_nms
    params: {iou_threshold: 0.5, score_threshold: 0.05, confidence_threshold_default: 0, clamp_to_input: true, clamp_boxes: false}
    input: {input_size: [20, 20], source_size: [20, 20], unproject: [1, 0, 1, 0], boxes: [[-10, 0, 10, 10], [0, 0, 20, 10]], scores: [0.875, 0.75]}
    expect: {kept_rows: [0, 1], scores: [0.875, 0.75], class_ids: [0, 0], boxes_model: [[0, 0, 10, 10], [0, 0, 20, 10]], boxes: [[0, 0, 10, 10], [0, 0, 20, 10]]}
  - id: clamp-to-input-closed-bounds-width-and-height
    # input_size is [H_in, W_in] = [20, 30]: x goes to [0, 30] and y to [0, 20]; a value equal to the
    # bound stays (the bound is W_in, not W_in - 1)
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_to_input: true, clamp_boxes: false}
    input: {input_size: [20, 30], source_size: [20, 30], unproject: [1, 0, 1, 0], boxes: [[25, 15, 35, 25], [0, 0, 30, 20]], scores: [0.875, 0.75]}
    expect: {kept_rows: [0, 1], scores: [0.875, 0.75], class_ids: [0, 0], boxes_model: [[25, 15, 30, 20], [0, 0, 30, 20]], boxes: [[25, 15, 30, 20], [0, 0, 30, 20]]}
  - id: clamp-to-input-zero-area-box-stays
    # row 0 is outside the input and becomes [20, 0, 20, 10] (zero area). Its IoU with row 1 is 0,
    # so it does not suppress row 1 and row 1 does not suppress it. Both rows stay.
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_to_input: true, clamp_boxes: false}
    input: {input_size: [20, 20], source_size: [20, 20], unproject: [1, 0, 1, 0], boxes: [[22, 0, 30, 10], [15, 0, 20, 10]], scores: [0.875, 0.75]}
    expect: {kept_rows: [0, 1], scores: [0.875, 0.75], class_ids: [0, 0], boxes_model: [[20, 0, 20, 10], [15, 0, 20, 10]], boxes: [[20, 0, 20, 10], [15, 0, 20, 10]]}
  - id: zero-union-gives-iou-zero
    # two equal boxes with zero width: the union is 0, so the IoU is 0 and nothing is suppressed
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false}
    input: {input_size: [20, 20], source_size: [20, 20], unproject: [1, 0, 1, 0], boxes: [[5, 5, 5, 10], [5, 5, 5, 10]], scores: [0.875, 0.75]}
    expect: {kept_rows: [0, 1], scores: [0.875, 0.75], class_ids: [0, 0], boxes_model: [[5, 5, 5, 10], [5, 5, 5, 10]], boxes: [[5, 5, 5, 10], [5, 5, 5, 10]]}
  - id: clamp-boxes-upper-bound-is-the-image-size
    # source_size is [src_h, src_w] = [50, 100]; the unprojected box [90, 40, 130, 70] becomes
    # [90, 40, 100, 50] (the bound is src_w, not src_w - 1)
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: true}
    input: {input_size: [40, 80], source_size: [50, 100], unproject: [2, 0, 2, 0], boxes: [[45, 20, 65, 35]], scores: [0.875]}
    expect: {kept_rows: [0], scores: [0.875], class_ids: [0], boxes_model: [[45, 20, 65, 35]], boxes_source: [[90, 40, 130, 70]], boxes: [[90, 40, 100, 50]]}
  - id: clamp-boxes-zero-area-row-stays
    # row 0 is in the pad: [110, 0, 120, 20] becomes [100, 0, 100, 20] (zero area). The row stays.
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: true}
    input: {input_size: [40, 80], source_size: [50, 100], unproject: [2, 0, 2, 0], boxes: [[55, 0, 60, 10], [10, 5, 20, 15]], scores: [0.875, 0.75]}
    expect: {kept_rows: [0, 1], scores: [0.875, 0.75], class_ids: [0, 0], boxes_source: [[110, 0, 120, 20], [20, 10, 40, 30]], boxes: [[100, 0, 100, 20], [20, 10, 40, 30]]}
  - id: clamp-boxes-false-keeps-the-unprojected-box
    # the same input with clamp_boxes false: the box stays outside the image
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false}
    input: {input_size: [40, 80], source_size: [50, 100], unproject: [2, 0, 2, 0], boxes: [[55, 0, 60, 10], [10, 5, 20, 15]], scores: [0.875, 0.75]}
    expect: {kept_rows: [0, 1], scores: [0.875, 0.75], class_ids: [0, 0], boxes: [[110, 0, 120, 20], [20, 10, 40, 30]]}
  - id: clamp-boxes-default-is-true-with-an-offset
    # clamp_boxes is absent (default true). Inverse x_src = 2 * x - 20 (left 10), y_src = 2 * y:
    # [5, 0, 15, 10] gives [-10, 0, 10, 20] and the clamp gives [0, 0, 10, 20]
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0}
    input: {input_size: [20, 40], source_size: [20, 40], unproject: [2, -20, 2, 0], boxes: [[5, 0, 15, 10]], scores: [0.875]}
    expect: {kept_rows: [0], scores: [0.875], class_ids: [0], boxes_source: [[-10, 0, 10, 20]], boxes: [[0, 0, 10, 20]]}
  - id: clamp-to-input-comes-before-the-unprojection
    # [-10, 0, 15, 10] becomes [0, 0, 15, 10] in model-input pixels, then [0, 0, 30, 20] in the source.
    # A clamp after the unprojection would give [0, 0, 20, 20].
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_to_input: true, clamp_boxes: false}
    input: {input_size: [20, 20], source_size: [40, 40], unproject: [2, 0, 2, 0], boxes: [[-10, 0, 15, 10]], scores: [0.875]}
    expect: {kept_rows: [0], scores: [0.875], class_ids: [0], boxes_model: [[0, 0, 15, 10]], boxes: [[0, 0, 30, 20]]}
  - id: clamp-boxes-comes-after-the-nms
    # the content of the input is x in [0, 10] (src_w 20, scale 2). In model-input pixels the IoU is
    # 40 / 120 = 0.333, so both rows stay. A clamp to the source before the NMS would make the two
    # boxes equal (IoU 1) and suppress row 1.
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: true}
    input: {input_size: [20, 20], source_size: [20, 20], unproject: [2, 0, 2, 0], boxes: [[6, 0, 18, 10], [6, 0, 10, 10]], scores: [0.875, 0.75]}
    expect: {kept_rows: [0, 1], scores: [0.875, 0.75], class_ids: [0, 0], boxes_source: [[12, 0, 36, 20], [12, 0, 20, 20]], boxes: [[12, 0, 20, 20], [12, 0, 20, 20]]}
  - id: mmdet-mapping-boxes-can-leave-the-image
    # clamp_to_input true and clamp_boxes false (the mmdet RTMDet mapping): the box stays inside the
    # model input but its unprojection [12, 0, 36, 20] passes the source width 20
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_to_input: true, clamp_boxes: false}
    input: {input_size: [20, 20], source_size: [20, 20], unproject: [2, 0, 2, 0], boxes: [[6, 0, 18, 10], [6, 0, 10, 10]], scores: [0.875, 0.75]}
    expect: {kept_rows: [0, 1], scores: [0.875, 0.75], class_ids: [0, 0], boxes_model: [[6, 0, 18, 10], [6, 0, 10, 10]], boxes: [[12, 0, 36, 20], [12, 0, 20, 20]]}
  - id: clamp-to-input-before-post-nms-top-k
    # the clamp makes row 1 equal to row 0 (IoU 1; without the clamp 120 / 300 = 0.4), so row 1 is
    # suppressed and takes no slot of post_nms_top_k 2
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_to_input: true, clamp_boxes: false, post_nms_top_k: 2}
    input: {input_size: [20, 20], source_size: [20, 20], unproject: [1, 0, 1, 0], boxes: [[-20, 0, 10, 10], [-2, 0, 10, 10], [12, 0, 18, 6]], scores: [0.875, 0.75, 0.625]}
    expect: {kept_rows: [0, 2], scores: [0.875, 0.625], class_ids: [0, 0], boxes_model: [[0, 0, 10, 10], [12, 0, 18, 6]], boxes: [[0, 0, 10, 10], [12, 0, 18, 6]]}
  - id: pre-nms-top-k-keeps-the-top-of-each-level
    # input 16 x 16, level_strides [8, 16]: level 0 is rows 0-3 (2 x 2), level 1 is row 4 (1 x 1).
    # The cap of 1 keeps row 1 (0.875) of level 0 and row 4 (0.75) of level 1. A cap over all rows
    # would keep only row 1.
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false, pre_nms_top_k: 1, level_strides: [8, 16]}
    input: {input_size: [16, 16], source_size: [16, 16], unproject: [1, 0, 1, 0], boxes: [[0, 0, 2, 2], [4, 0, 6, 2], [8, 0, 10, 2], [12, 0, 14, 2], [0, 8, 2, 10]], scores: [0.5, 0.875, 0.25, 0.625, 0.75]}
    expect: {kept_rows: [1, 4], scores: [0.875, 0.75], class_ids: [0, 0], boxes: [[4, 0, 6, 2], [0, 8, 2, 10]]}
  - id: pre-nms-top-k-absent-keeps-every-candidate
    # the same input without pre_nms_top_k and level_strides: no cap
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false}
    input: {input_size: [16, 16], source_size: [16, 16], unproject: [1, 0, 1, 0], boxes: [[0, 0, 2, 2], [4, 0, 6, 2], [8, 0, 10, 2], [12, 0, 14, 2], [0, 8, 2, 10]], scores: [0.5, 0.875, 0.25, 0.625, 0.75]}
    expect: {kept_rows: [1, 4, 3, 0, 2], scores: [0.875, 0.75, 0.625, 0.5, 0.25], class_ids: [0, 0, 0, 0, 0], boxes: [[4, 0, 6, 2], [0, 8, 2, 10], [12, 0, 14, 2], [0, 0, 2, 2], [8, 0, 10, 2]]}
  - id: pre-nms-top-k-level-order-follows-level-strides
    # level_strides [16, 8]: level 0 is row 0 (1 x 1), level 1 is rows 1-4 (2 x 2). The cap of 1 keeps
    # row 0 (0.5) and row 1 (0.875). With [8, 16] the result is rows 1 and 4 (first case).
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false, pre_nms_top_k: 1, level_strides: [16, 8]}
    input: {input_size: [16, 16], source_size: [16, 16], unproject: [1, 0, 1, 0], boxes: [[0, 0, 2, 2], [4, 0, 6, 2], [8, 0, 10, 2], [12, 0, 14, 2], [0, 8, 2, 10]], scores: [0.5, 0.875, 0.25, 0.625, 0.75]}
    expect: {kept_rows: [1, 0], scores: [0.875, 0.5], class_ids: [0, 0], boxes: [[4, 0, 6, 2], [0, 0, 2, 2]]}
  - id: pre-nms-top-k-without-level-strides-is-one-level
    # no level_strides: all 5 rows are one level. The cap of 2 keeps rows 1 and 4. With
    # level_strides [8, 16] the cap of 2 keeps rows 1, 3 and 4.
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false, pre_nms_top_k: 2}
    input: {input_size: [16, 16], source_size: [16, 16], unproject: [1, 0, 1, 0], boxes: [[0, 0, 2, 2], [4, 0, 6, 2], [8, 0, 10, 2], [12, 0, 14, 2], [0, 8, 2, 10]], scores: [0.5, 0.875, 0.25, 0.625, 0.75]}
    expect: {kept_rows: [1, 4], scores: [0.875, 0.75], class_ids: [0, 0], boxes: [[4, 0, 6, 2], [0, 8, 2, 10]]}
  - id: pre-nms-top-k-tie-goes-to-the-lower-row
    # rows 1 and 2 of level 0 have the same score 0.625: the cap of 1 keeps row 1
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false, pre_nms_top_k: 1, level_strides: [8, 16]}
    input: {input_size: [16, 16], source_size: [16, 16], unproject: [1, 0, 1, 0], boxes: [[0, 0, 2, 2], [4, 0, 6, 2], [8, 0, 10, 2], [12, 0, 14, 2], [0, 8, 2, 10]], scores: [0.5, 0.625, 0.625, 0.25, 0.75]}
    expect: {kept_rows: [4, 1], scores: [0.75, 0.625], class_ids: [0, 0], boxes: [[0, 8, 2, 10], [4, 0, 6, 2]]}
  - id: pre-nms-top-k-acts-before-the-nms
    # the cap of 2 keeps rows 0 and 1 of level 0 and drops rows 2 and 3. Then row 0 suppresses
    # row 1 (IoU 100 / 110 = 0.909 > 0.6). A cap after the NMS would keep rows 0 and 2.
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false, pre_nms_top_k: 2, level_strides: [8, 16]}
    input: {input_size: [16, 16], source_size: [16, 16], unproject: [1, 0, 1, 0], boxes: [[0, 0, 10, 10], [0, 0, 10, 11], [12, 0, 14, 2], [12, 4, 14, 6], [0, 12, 2, 14]], scores: [0.875, 0.75, 0.5, 0.25, 0.625]}
    expect: {kept_rows: [0, 4], scores: [0.875, 0.625], class_ids: [0, 0], boxes: [[0, 0, 10, 10], [0, 12, 2, 14]]}
  - id: pre-nms-top-k-non-square-input
    # input_size is [H_in, W_in] = [8, 16], level_strides [4, 8]: level 0 holds (8 / 4) * (16 / 4) = 8
    # rows (0-7), level 1 holds (8 / 8) * (16 / 8) = 2 rows (8-9). The cap of 1 keeps rows 3 and 9.
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false, pre_nms_top_k: 1, level_strides: [4, 8]}
    input: {input_size: [8, 16], source_size: [8, 16], unproject: [1, 0, 1, 0], boxes: [[0, 0, 1, 1], [2, 0, 3, 1], [4, 0, 5, 1], [6, 0, 7, 1], [8, 0, 9, 1], [10, 0, 11, 1], [12, 0, 13, 1], [14, 0, 15, 1], [0, 4, 1, 5], [2, 4, 3, 5]], scores: [0.25, 0.5, 0.375, 0.875, 0.125, 0.625, 0.3125, 0.1875, 0.5625, 0.75]}
    expect: {kept_rows: [3, 9], scores: [0.875, 0.75], class_ids: [0, 0], boxes: [[6, 0, 7, 1], [2, 4, 3, 5]]}
  - id: min-bbox-size-zero-drops-an-inverted-box
    # row 0 has y2 < y1 (height -2 <= 0): min_bbox_size 0 drops it
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false, min_bbox_size: 0}
    input: {input_size: [20, 20], source_size: [20, 20], unproject: [1, 0, 1, 0], boxes: [[10, 10, 12, 8], [0, 0, 4, 4]], scores: [0.875, 0.75]}
    expect: {kept_rows: [1], scores: [0.75], class_ids: [0], boxes: [[0, 0, 4, 4]]}
  - id: min-bbox-size-absent-keeps-an-inverted-box
    # the same input without min_bbox_size: the inverted row stays (its area is 0, so its IoU is 0)
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false}
    input: {input_size: [20, 20], source_size: [20, 20], unproject: [1, 0, 1, 0], boxes: [[10, 10, 12, 8], [0, 0, 4, 4]], scores: [0.875, 0.75]}
    expect: {kept_rows: [0, 1], scores: [0.875, 0.75], class_ids: [0, 0], boxes: [[10, 10, 12, 8], [0, 0, 4, 4]]}
  - id: min-bbox-size-zero-drops-a-zero-width-box
    # row 0 has width 0 (0 <= 0): min_bbox_size 0 drops it
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false, min_bbox_size: 0}
    input: {input_size: [20, 20], source_size: [20, 20], unproject: [1, 0, 1, 0], boxes: [[5, 5, 5, 10], [0, 0, 4, 4]], scores: [0.875, 0.75]}
    expect: {kept_rows: [1], scores: [0.75], class_ids: [0], boxes: [[0, 0, 4, 4]]}
  - id: min-bbox-size-is-strict-in-source-pixels
    # scale 2: row 0 is 2 x 2 in model-input pixels and 4 x 4 in source pixels (4 <= 4: dropped);
    # row 1 is 2.5 x 2.5 and 5 x 5 (kept). A filter in model-input pixels would drop both rows.
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false, min_bbox_size: 4}
    input: {input_size: [20, 20], source_size: [40, 40], unproject: [2, 0, 2, 0], boxes: [[0, 0, 2, 2], [10, 0, 12.5, 2.5]], scores: [0.875, 0.75]}
    expect: {kept_rows: [1], scores: [0.75], class_ids: [0], boxes: [[20, 0, 25, 5]]}
  - id: min-bbox-size-acts-before-the-nms
    # row 0 (4 x 4 <= 4) is dropped before the NMS, so it cannot suppress row 1 (IoU 16 / 25 = 0.64).
    # A filter after the NMS would give no row.
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false, min_bbox_size: 4}
    input: {input_size: [20, 20], source_size: [20, 20], unproject: [1, 0, 1, 0], boxes: [[0, 0, 4, 4], [0, 0, 5, 5]], scores: [0.875, 0.75]}
    expect: {kept_rows: [1], scores: [0.75], class_ids: [0], boxes: [[0, 0, 5, 5]]}
  - id: min-bbox-size-after-the-clamp-to-input
    # row 0 is left of the model input: the clamp gives [0, 0, 0, 10] (width 0), then min_bbox_size 0
    # drops it. A filter before the clamp would keep it (width 10).
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false, clamp_to_input: true, min_bbox_size: 0}
    input: {input_size: [20, 20], source_size: [20, 20], unproject: [1, 0, 1, 0], boxes: [[-12, 0, -2, 10], [2, 0, 6, 4]], scores: [0.875, 0.75]}
    expect: {kept_rows: [1], scores: [0.75], class_ids: [0], boxes_model: [[2, 0, 6, 4]], boxes: [[2, 0, 6, 4]]}
  - id: mmdet-mapping-cap-comes-before-the-size-filter
    # the full mmdet mapping (clamp_to_input true, clamp_boxes false, pre_nms_top_k, level_strides,
    # min_bbox_size 0). The cap of 1 keeps row 0 of level 0 and row 4 of level 1. Then the clamp
    # gives row 0 the width 0 and the size filter drops it. Row 1 does not come back.
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false, clamp_to_input: true, pre_nms_top_k: 1, level_strides: [8, 16], min_bbox_size: 0}
    input: {input_size: [16, 16], source_size: [32, 32], unproject: [2, 0, 2, 0], boxes: [[-6, 0, -1, 4], [2, 2, 6, 6], [8, 0, 12, 4], [12, 8, 14, 10], [0, 10, 4, 14]], scores: [0.875, 0.75, 0.625, 0.5, 0.25]}
    expect: {kept_rows: [4], scores: [0.25], class_ids: [0], boxes_model: [[0, 10, 4, 14]], boxes: [[0, 20, 8, 28]]}
  - id: inverted-box-has-area-zero
    # row 0 is inverted: step 4 gives it the area 0, so its IoU with row 1 is 0 and both rows stay.
    # A host that reads a box as any diagonal pair of corners gets IoU 1 and drops row 1. The host
    # NmsDecoder (ONNX NonMaxSuppression, ONNX Runtime 1.31.0, CPU) gives kept_rows [0]: a known host
    # gap; onnx_runtime/ is not changed (plan T30 F3).
    function: decode_nms
    params: {iou_threshold: 0.6, score_threshold: 0.05, confidence_threshold_default: 0, clamp_boxes: false}
    input: {input_size: [20, 20], source_size: [20, 20], unproject: [1, 0, 1, 0], boxes: [[10, 10, 0, 0], [0, 0, 10, 10]], scores: [0.875, 0.75]}
    expect: {kept_rows: [0, 1], scores: [0.875, 0.75], class_ids: [0, 0], boxes: [[10, 10, 0, 0], [0, 0, 10, 10]]}
```

Every expected value is a small integer or a dyadic fraction, so it is exact in float32 and float64. No
case is a pixel case, so no case has `compare`. The validation rule `V-post.det.selection.nms-2` (a
stride that does not divide the input, or a row count that is not the sum) has no vector: the vector
files of the spec have no error form. The reference function `level_row_counts` raises `ValueError`
for both.

## 5. Parity evidence

Result: **`to run`**. The numbers below come from two scratch runs on the host GPU on 2026-10-24 (the
two earlier proposals). The scripts are not committed, so the numbers are not evidence yet (exporter
guide, "Parity", step 7). This session may write only the files in `plans/`. The scripts go to
`notes/decisions/scripts/rtmdet_nms_clamp_parity.py` with the next code change (plan T28 N5).

| Item | Value |
|---|---|
| Gates, set before the run, and their source | Set for the committed run (the first scratch run had no gates set before it; the second run named its settings and comparisons in its docstring before the run). The committed script must assert: (a) the AP gate of the exporter, fp32 against the source pass, `abs(ΔAP) <= 0.005` (OpenMMLab-Exporter decision D5, `rtmdet_person/ACCURACY_CONTRACT.md` "Comparison thresholds"); (b) the reference file with the current text must equal the host decoder: the same row count, coordinates within 1e-4 px (the float32 output of the host), scores equal; (c) the clamp mapping (`clamp_to_input: true`, `clamp_boxes: false`) must be at least as close to the mmdet output as the current text: no more source rows with no partner box at IoU >= 0.9, and no fewer images with an equal row count; (d) the full mmdet mapping (the clamp mapping and the cap and the size filter) must keep the same rows in the same order as a literal copy of the mmdet order of the secondary source (`onnx_coco_eval_dense.py:91-112`, with the clip at the padded input), on every image; (e) the cap and the size filter must not make the match with the mmdet output worse than the clamp mapping alone. The export error (step 3) is not measured, so no gate can separate the decode error from the export error yet. |
| Test images (paths or dataset IDs), and the branch that each image runs | COCO val2017, all 5000 images in file-name order (`../_datasets/coco_data/coco_val2017/coco/images/val2017`), batch 1. Branches: boxes that cross the input edge (`clamp_to_input` changes 668 nano and 405 medium images); boxes past the source image (8293 nano and 3261 medium rows with `clamp_boxes: false`); zero-area rows after `clamp_boxes` (10 nano rows, 1 medium row); a level above the cap (1 nano image, 34 medium images) and levels at or below the cap (all other images); the size filter drops a candidate (nano image 328430, an inverted box) and drops nothing (all other images); an image with no detection (one medium image); images with many detections (up to the cap of 100). Landscape and portrait images, downscales and upscales: the 5000 images have all of them. |
| Upstream reference: library, version, config and command | mmdet 3.3.0 `tools/test.py` in `<user>/openmmlab-exporter:df-dcab32049439` (mmcv 2.1.0, mmengine 0.10.3), the configs `mmdeploy-convert/model_cfgs/rtmdet_nano_320-8xb32_coco-person.py` and `rtmdet_m_640-8xb32_coco-person.py`, batch 1, run `20261021T231118Z-<host>`: the source predictions files of part 1. Scored with skellybench 0.4.0 `score_predictions` (faster-coco-eval 1.8.0): AP 0.403290, AR100 0.520674 (nano); AP 0.625469, AR100 0.724691 (medium). |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | to run (needs the PyTorch head outputs on the same tensor; torch is not on the host and Docker did not run in these sessions) |
| Preprocessed input: maximum absolute difference for each image | to run (needs the mmdet preprocessed tensor). The host letterbox is the one of the 2026-10-21 ONNX passes: the control decode of each dump equals the stored fp32 b1 predictions of that run exactly (291170 and 182560 rows, maximum difference 0 in x, y, w, h and score). |
| Row count for each image: sidecar path and upstream | Images with the same row count as mmdet: nano 3513 of 5000 (current text), 3651 (`clamp_to_input: true`, either `clamp_boxes`), 3652 (the full mmdet mapping); medium 3788, 3867 and 3867. Image 328430 (nano): mmdet 96 rows; the clamp mapping 97; the full mmdet mapping 96. Total rows: nano 291170 (current), 290778 (clamp mapping) and 290777 (full mapping) against 290882 (mmdet); medium 182560, 182364 and 182364 against 182515. |
| Final outputs in source-image coordinates: metric and value for each role | `object_detector` only. See the table below. |
| Result (`pass`, `fail` or `to run`) | `to run` |
| Script path in the exporter repo | unknown (not committed). Scratch, first run (`...\scratchpad\rtmdet-nms\`): `dump_candidates.py` (the ONNX run on CUDA, preload first, and the host decoder control), `parity_ref.py` (the reference file in place of the host decoder), `variants.py` (the other orders of part 8), `diff_b_mmdet.py`, `check_nms_pre.py`. Second run (`...\scratchpad\nms-pre\`): `dump.py` (the ONNX run on CUDA, `ort.preload_dlls()` first through the committed `create_session`, the host decoder control, the layout check), `analyze.py` (all settings, AP, the comparison with mmdet, the literal mmdet order), `global_cap.py` (part 8, alternative 9), `one_image.py` (image 328430), `inspect_levels.py` (the graph read). Vectors: `...\scratchpad\nms-merge\run_merge.py`. Proposed committed name: `notes/decisions/scripts/rtmdet_nms_clamp_parity.py` (T28 N5), one script for all settings. |
| Exporter commit of the script | none (not committed) |
| Command | First run: `uv run python -I dump_candidates.py <repo> {nano,medium} fp32 <out.npz>`, then `uv run python -I parity_ref.py <repo> <out.npz> {nano,medium} "<repo>/exports/detectors/object_detectors/rtmdet-person/benchmarks/rtmdet-person-{size}_source/*b1*.predictions.json"`. Second run: `uv run python -I dump.py <repo> <committed onnx_runtime parent> {nano,medium} fp32 <out.npz>`, then `uv run python -I analyze.py <repo> <out.npz> {nano,medium}`. From the repo root. `<committed onnx_runtime parent>` is a folder with `git archive d0f4343 onnx_runtime` unpacked in it. |

**Final outputs** (scratch runs, 2026-10-24; ONNX Runtime 1.31.0, `CUDAExecutionProvider`, NVIDIA
GeForce RTX 3070; the session code of `onnx_runtime/` sets no TF32 option, so the ONNX Runtime default
applies; NumPy 2.5.4; scored with skellybench `score_predictions` (faster-coco-eval), person category,
`max_dets` 100; confidence threshold 0, as in the accuracy pass). The two runs give the same numbers for
the decodes that both measured (current text and the clamp mapping). "No partner" counts the mmdet rows
with no sidecar row at IoU >= 0.9. "Partner diff" is the largest coordinate difference of each matched
pair, in source pixels (first run only). "Clamp" is `clamp_to_input: true`. "Cap" is
`pre_nms_top_k: 1000` with `level_strides: [8, 16, 32]`. "Size" is `min_bbox_size: 0`.

| Size | Decode (reference file of part 3) | AP | AR100 | Rows | Equal row count | No partner | Partner diff median / p99 / max |
|---|---|---|---|---|---|---|---|
| nano | current text (`clamp_boxes: true`) | 0.403585 | 0.521063 | 291170 | 3513 / 5000 | 4350 / 290882 | 0.0556 / 2.50 / 36.2 px |
| nano | current text + cap + size | 0.403585 | 0.521063 | 291169 | 3514 / 5000 | 4350 / 290882 | not measured |
| nano | clamp, `clamp_boxes: true` | 0.403547 | 0.520980 | 290778 | 3651 / 5000 | 4000 / 290882 | 0.0556 / 2.47 / 39.0 px |
| nano | clamp, `clamp_boxes: false` (the clamp mapping) | 0.403350 | 0.520674 | 290778 | 3651 / 5000 | 3809 / 290882 | 0.0538 / 1.92 / 39.0 px |
| nano | clamp mapping + cap | 0.403350 | 0.520674 | 290778 | 3651 / 5000 | 3809 / 290882 | not measured |
| nano | clamp mapping + size | 0.403350 | 0.520674 | 290777 | 3652 / 5000 | 3809 / 290882 | not measured |
| nano | clamp mapping + cap + size (the full mmdet mapping) | 0.403350 | 0.520674 | 290777 | 3652 / 5000 | 3809 / 290882 | not measured |
| medium | current text | 0.625492 | 0.724766 | 182560 | 3788 / 5000 | 2461 / 182515 | 0.0226 / 1.63 / 44.5 px |
| medium | current text + cap + size | 0.625492 | 0.724766 | 182560 | 3788 / 5000 | 2461 / 182515 | not measured |
| medium | clamp, `clamp_boxes: true` | 0.625481 | 0.724691 | 182364 | 3867 / 5000 | 2295 / 182515 | 0.0226 / 1.56 / 44.5 px |
| medium | the clamp mapping | 0.625439 | 0.724664 | 182364 | 3867 / 5000 | 2238 / 182515 | 0.0221 / 1.25 / 30.3 px |
| medium | clamp mapping + cap, + size, + cap + size (each) | 0.625439 | 0.724664 | 182364 | 3867 / 5000 | 2238 / 182515 | not measured |

Kept rows, against the same decode without the field (images that differ; rows in the symmetric
difference): clamp mapping against + cap: 0; 0 (both sizes). Against + size: 1; 1 (nano), 0; 0
(medium). Against + cap + size: 1; 1 (nano), 0; 0 (medium). Current text against + cap + size: 1; 1
(nano), 0; 0 (medium).

- Gate (a): every row is within 0.0003 AP of the source pass.
- Gate (b): the reference file with the current text gives the same 291170 and 182560 rows as the
  host decoder. The largest differences are 4.6e-5 (x), 4.4e-5 (y), 6.8e-5 (w) and 6.2e-5 (h) px on
  nano and 4.3e-5, 3.7e-5, 6.1e-5 and 5.8e-5 px on medium (the host is float32, the reference
  float64). The scores are equal. The parity result of the host decoder does not change with the
  reference file.
- Gate (c): the clamp mapping has fewer rows with no partner on both sizes (-541 nano, -223 medium)
  and more images with an equal row count (+138, +79).
- Gate (d): the full mmdet mapping and the literal mmdet order keep the same rows in the same order on
  5000 of 5000 images for both sizes, and the boxes are equal (difference 0 px). The literal copy
  multiplies by `src_w / n_w` like the reference unprojection, so this gate checks the order of the
  steps, not the float arithmetic of mmdet. Without the size filter, the clamp mapping agreed with the
  literal order on 4999 of 5000 nano images; the one image was the inverted box of part 1.
- Gate (e): the cap and the size filter do not change the "no partner" counts, and they add one nano
  image with an equal row count (3651 to 3652).
- The rest of the difference from the mmdet output is not from the decode (gate (d)). It is the export
  error (fp32 ONNX against PyTorch), which step 3 must measure.

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | `skellytracker/core/detectors/processing/object_detection_decode.py`: a new function (for example `decode_selection_nms`) next to `decode_prenms`. It follows `select_nms` and `decode_nms` of the reference file: the score filter and the cap (`pre_nms_cap`), the box conversion, the clamp to the input and the size filter (`min_size_keep`), the classes, the NMS of step 4, the sort of step 5, the unprojection and `clamp_boxes`. `decode_prenms` (lines 155-227) stays for YOLOX until the YOLOX open-work item is done (`notes/decisions/open-work.md:71-77`): the YOLOX decoder calls it (`skellytracker/core/detectors/object_detectors/yolox/yolox_decode.py:112-120`), and its golden fixtures depend on its `+ 1` area (plan T32 P7). `decode_prenms` today divides the boxes by the letterbox `ratio` before the NMS (line 205), runs `multiclass_nms` with the `+ 1` area of `nms` (lines 55, 68-69) and a tie order of `argsort()[::-1]` (line 56), has one filter `scores > score_thr` (line 215), and does not clamp. |
| Dispatch point | for the implementer. The caller of `decode_prenms` passes `ratio`, `score_thr` and `nms_thr` from outside the sidecar (`:155-160`). The new function needs the `decode` block, the model input size (`H_in`, `W_in`) for `clamp_to_input` and the levels, `level_strides`, the source size for `clamp_boxes`, and the inverse of the resize for the size filter and step 6. skellytracker has no shared unprojection function (`post.unprojection` front matter). |
| Validator changes (`model.py`, with rule IDs) | `DetectionDecodeSpec` (`skellytracker/core/sidecar/model.py:217-244`) has no `selection`, no `nms` and no `clamp_boxes` field (skellytracker decision 0011, "Code"). When the implementer adds the `nms` model: `clamp_to_input: bool = False`, `pre_nms_top_k: PositiveInt | None = None`, `level_strides: list[PositiveInt] | None = None` (non-empty, and only with `pre_nms_top_k`), `min_bbox_size: NonNegativeFloat | None = None` (`V-post.det.selection.nms-1`); and `clamp_boxes: bool = True` (`V-post.det.decode-5`). `V-post.det.selection.nms-2` needs `input.shape` and the output shapes of each size, so it goes into a sidecar-level check (`SidecarModel`) or into `resolved_size`, not into the `nms` model. |
| Tests | The 20 existing vectors and the 29 vectors of part 4 (`specs/model-sidecar/vectors/post.det.selection.nms.yaml`). A validator test for each sentence of `V-post.det.selection.nms-1` and `-2` (a stride that does not divide 320; a sum that is not 2100). A golden parity test: the rtmdet-person outputs of a few COCO images with the full mmdet mapping against the rows of the mmdet source predictions file (part 5). Include nano image 328430 (the inverted box) and one medium image with a level above 1000 candidates. An AP check on COCO val2017 with the fp32 files of the T17 stems (`rtmdet-person-n_b1_fp32.onnx`, `rtmdet-person-m_b1_fp32.onnx`): the AP of the sidecar path against the AP of the source pass, with the gate `abs(ΔAP) <= 0.005` (the D5 gate of OpenMMLab-Exporter, `rtmdet_person/ACCURACY_CONTRACT.md`). This replaces fixed AP targets (plan T32 P10). |
| Existing code that the change touches | `object_detection_decode.py`: `nms` (lines 33-76, the `+ 1` area and the tie order), `multiclass_nms` (line 79), `decode_prenms` (it stays for YOLOX). `skellytracker/core/sidecar/model.py`: `DetectionDecodeSpec`. |

**A host that uses the ONNX `NonMaxSuppression` operator (advisory).** The operator is allowed in the
host, for example in a small decode graph that runs in ONNX Runtime. Such a host must do these things:

- Apply steps 1 and 2 to the operator inputs: the score filter, the cap of each level, the clamp to
  the input and the size filter. The operator has none of them.
- Give an inverted box (`x2 < x1` or `y2 < y1`) the area 0. The operator reads a box as any diagonal
  pair of corners (2.8). For example, keep each inverted box out of the operator input, and add it to
  the survivors of the operator: its IoU with each box is 0. Drop it only when `nms.min_bbox_size` is
  set. The vector `inverted-box-has-area-zero` checks this.
- Sort the survivors by score in descending order, then by the lower row (step 5). Do not use the
  output order of the operator: for rank-3 scores, ONNX Runtime groups its output by class (part 4,
  "Host tie order").
- Run the vector `equal-scores-lower-row-wins` on the ONNX Runtime that skellytracker uses. The
  `onnx-cuda` and `onnx-trt` extras pin `onnxruntime-gpu<1.27` (`pyproject.toml:101-102, 116-117`);
  the `onnx-cpu` extra has no pin (`:88`). The tie order was measured only on ONNX Runtime 1.31.0.
- A decode graph that the host builds needs the `onnx` package. In skellytracker it is the optional
  `onnx` extra (`pyproject.toml:81`).
- Add a threshold-equivalence test: on random inputs, the decode with the pre-filter at
  `max(nms.score_threshold, confidence threshold)` gives the same detections as the decode at
  `nms.score_threshold` followed by the final filter. Include the cap (2.3, "A run-time threshold").
- Add a provider test: the same inputs give the same detections on the CPU provider and on the CUDA
  provider. Do not exempt score ties.

This part gives no provider table for the decode session: no provider was measured for it.

## 7. Exporter impact

| Exporter | Affected sidecars | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmdet-person` (`exports/detectors/object_detectors/rtmdet-person/rtmdet-person.yaml`) | New fields in `rtmdet_person/model_report.py` `decode_params()` (`:159-178` at `d0f4343`): `nms.clamp_to_input: true`, `nms.pre_nms_top_k: 1000`, `nms.level_strides: [8, 16, 32]`, `nms.min_bbox_size: 0`, and `clamp_boxes: false` (today `true`, `:171`; user decision T28 N1, the exact mmdet mapping). Take `nms_pre` and `min_bbox_size` from `identity.MMDET_TEST_CFG` (`rtmdet_person/identity.py:44-50`). Add a constant for the strides, with a test that the sum of the level rows equals `anchors` of each size (2100 and 8400, `tests/test_rtmdet_person.py:75` at `f3aeb47`; `:74` at `d0f4343`). The config test (`tests/test_rtmdet_person.py:78-85` at `f3aeb47`; `:77-84` at `d0f4343`) checks `nms_pre`, `score_thr`, `iou_threshold` and `max_per_img` in the config text, but not `min_bbox_size`: add it. Regenerate the sidecar. OpenMMLab-Exporter decision 0050 (`f3aeb47`) writes no `rtmdet-person` sidecar until the `rtmdet-person` intake is `describes` (this proposal is one of its open gaps), so the regeneration happens at that later round. Until then the file in `exports/` keeps its earlier content. | `onnx_runtime/decode_nms.py` `NmsDecoder`, before the ONNX `NonMaxSuppression` graph, for each image: (1) keep the top `pre_nms_top_k` rows of each level after the score filter (ties to the lower row; NumPy); (2) when `nms.clamp_to_input` is true, clip `boxes[..., 0::2]` to `[0, W_in]` and `boxes[..., 1::2]` to `[0, H_in]` (in NumPy, or a `Clip` node in `build_nms_decode_model`); (3) drop the rows whose unprojected width or height is `<= min_bbox_size` (the letterbox scale `src_w / n_w` and `src_h / n_h`, after the clamp). For rank-3 scores, sort the NMS output by the rule of steps 4 and 5 (for rank-2 scores the host already gives that order, part 4). The pre-filter at `max(score_threshold, confidence threshold)` stays correct (2.3). **Known host gap (F3):** the host gives an inverted box a non-zero area (part 4, vector `inverted-box-has-area-zero`). `min_bbox_size: 0` removes inverted boxes before the NMS, so the gap does not reach the `rtmdet-person` output with this mapping. The user decided: do not change `onnx_runtime/` in this work (plan T28 N3/N4, T30 F3); this proposal records the gap for skellytracker (part 6). Also update `rtmdet_person/DECODE_RULES.md:33` ("clamps the boxes to the image before NMS": the bound is the padded input) and `:52-58` ("`nms_pre` is not in the sidecar decode. The spec cannot express it." and the list of the sidecar values), `ACCURACY_NOTES` (`model_report.py`), and add a decision entry with the measurements of part 5. OpenMMLab-Exporter decision 0009, line 81 ("Clamping after NMS ... is invisible in AP") and the "mmdet" mode of `notes/decisions/scripts/onnx_coco_eval_dense.py` (it clips to `[0, n_w] x [0, n_h]`, lines 92-94) do not describe the upstream bound: mark them in the new entry (T28 N3). The accuracy gate of OpenMMLab-Exporter decision D5 still passes (part 5). |
| Roboflow-Exporter | RF-DETR (`selection: top_k`) | none (no `selection: nms`). Its clamp `[0, scale]` already has closed bounds (`detection-decode.md:100`). Check that its decoder keeps a zero-area row. | none |
| Ultralytics-Exporter | YOLO26 (`selection: none`) | none. Ultralytics clips to the source image after the inverse (`detection-decode.md:100`). | none |
| Qualcomm-Exporter | MediaPipe person detector | none from this proposal. Its upstream does not clamp (`detection-decode.md:121`): that is `clamp_boxes: false` today. Its upstream `batched_nms` setting has no per-level cap and no size filter in the spec text that this proposal read (`selection-nms.md:83, 92`). Its intake decides. | none |
| MediaPipe-Exporter | none (no code) | none | none |
| The proposing exporter, if it is not in this table | (in the table) | | |
| skellytracker package sidecars | the legacy sidecars (`schema_version: "v2024.09.1019"`) | none. They have no `decode.nms`, and `clamp_boxes` absent stays "Existing host behaviour" before `vNEXT`. | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| 1. Keep the current order and only define the bounds of `clamp_boxes` (the near-miss: `post.det.selection.nms` steps 4 and 6 as today) | The NMS keeps other rows than mmdet on 668 of 5000 nano images and 405 of 5000 medium images. The sidecar cannot describe the upstream. | Part 1; part 5: 4350 against 3809 rows with no partner (nano), 2461 against 2238 (medium). |
| 2. Always clamp to the input before the NMS (no field) | It changes the meaning of every `vNEXT` sidecar with `selection: nms`. An upstream that runs the NMS on unclamped boxes would need a new field. A field with the default `false` keeps the current meaning. | No measurement of other upstreams in these sessions. |
| 3. Follow mmdet literally: run the NMS in source pixels | The IoU does not change under the axis-aligned unprojection of the spec. It gives the same rows. One algorithm (model-input pixels) stays, and it matches the use of the ONNX operator on the graph output. | 5000 of 5000 images for both sizes: the same rows (part 1). |
| 4. Clamp to the source image before the NMS (the intake reading of mmdet, and the "mmdet" mode of `onnx_coco_eval_dense.py`, which clamps to the resized image `[0, n_w] x [0, n_h]`) | It does not describe the upstream: the mmdet output has boxes past the source image (2214 nano, 1193 medium in x). It also matches the mmdet rows less well than the clamp to the input. | Scratch `variants.py`: 4305 rows with no partner (nano) and 2395 (medium), against 3809 and 2238. |
| 5. Drop a zero-area row in the clamp of `clamp_boxes` | It makes the clamp change the row count. The effect is small: 10 nano rows and 1 medium row; AP unchanged to 6 decimals. The upstream filter `min_bbox_size` acts before the NMS. It is the separate field `nms.min_bbox_size` (step 2). | Scratch `variants.py`, variant `spec_drop0`: AP 0.403585 and 0.625492, the same as the current text. |
| 6. Upper bound `src_w - 1` (or `W_in - 1`) | No upstream and no exporter uses it. The mmdet output ends exactly on the padded-input edge `T * src_w / n_w` (9120 nano boxes within 0.01 px). | Part 1; `detection-decode.md:100` (OpenMMLab-Exporter, Roboflow-Exporter, Ultralytics clip to `W`). |
| 7. An enum `nms.clamp: none | input | content | source` | Only `input` has an upstream user. `content` (the resized image) is the secondary copy that the upstream output disproves. `source` before the NMS has no user. A boolean is enough. A later revision can widen it. | Part 1. |
| 8. Keep skellytracker 0011 and the changelog rows: no cap and no size filter (rows D9a and D12a stay `gap`) | The spec then cannot describe the mmdet decode, and the intake verdict stays `does not describe`. The user goal (T28 N2) is a full description. The AP does not need the fields, but the description does. | Part 1; part 5: no AP change, 1 nano row from the size filter. |
| 9. `nms.pre_nms_top_k` over all rows (no `level_strides`) | It is a different algorithm (skellytracker `notes/sidecar-exporter-coverage.md:184`, secondary). A cap of 1000 over all rows removes 1132 candidates on 13 nano images and 42160 on 91 medium images, and it keeps other rows than the per-level cap on 10 medium images (0 nano). This proposal keeps the one-level form only for an upstream with a cap over all rows (the default when `level_strides` is absent). | Scratch `global_cap.py`, with the full mmdet mapping. |
| 10. A row count for each level in each size (for example `sizes.<size>.level_rows`) | A size sets only its shape, its target size and its artifacts (the family invariant, skellytracker decision 0010; `V-common.sizes_and_artifacts-3`). The strides are a property of the family. The counts follow from the strides and `input.shape`. | `rtmdet-person`: 2100 and 8400 from `[8, 16, 32]` (part 1, graph read). |
| 11. Put `level_strides` on the output declaration (`outputs[]`) | Only the cap uses it, and the cap is a step of this section. One field in one section keeps the algorithm in one place. A later proposal can move it if a second user appears. | none |
| 12. A count of priors for each cell (anchor-based heads) | No model in scope has more than one prior for each cell. The RTMDet graphs have one-channel score maps for each level (part 1). A later revision can add the field. | Part 1, graph read. |
| 13. The size filter in model-input pixels | The secondary copy of mmdet compares the rescaled boxes (`onnx_coco_eval_dense.py:107-109`). For `0` the result is the same; for a value above `0` it is not. | Vector `min-bbox-size-is-strict-in-source-pixels`. |
| 14. The size filter after the NMS | mmdet filters before the NMS: a small box that it drops cannot suppress another box. | Vector `min-bbox-size-acts-before-the-nms`. |
| 15. `min_bbox_size` with the default `0` when absent | It changes the meaning of every `vNEXT` sidecar with `selection: nms` that does not have the field. An absent field must keep the current meaning. | Part 2.6. |
| 16. `>=` in the size filter (keep `w >= min_bbox_size`) | The secondary copy keeps `w > 0` and `h > 0` (`onnx_coco_eval_dense.py:108`). With `0`, `>=` keeps the boxes with zero width, which mmdet drops; the mmdet output has none (part 1). | Part 1, upstream output: 0 rows with `w <= 0` or `h <= 0`. |
| 17. More than one proposal: one for the clamp before the NMS and one for the bounds of `clamp_boxes` in `post.det.decode`; one for each candidate filter; or a separate candidate-filters proposal that depends on the clamp proposal (the state before the merge) | All the fields are steps of one section, with one step list, one validation rule, one vector file and one reference file. The size filter acts on the clamped box. Two proposals gave two files for one target reference module. The bound text of `clamp_boxes` is one field row with no algorithm of its own beyond the one clamp function; step 6 applies it, and the vectors of this section test it. A skellytracker session can split the `clamp_boxes` row out if it wants one unit for each section file. | Exporter guide, "Phase 2": "Write one proposal for each new or changed contract unit (one section)"; vector `min-bbox-size-after-the-clamp-to-input`; plan T32 P1 (a). |
| 18. Make the spec steps equal the ONNX `NonMaxSuppression` operator (the current sentence "These decode steps correspond one-to-one to the standard ONNX `NonMaxSuppression` operator") | The operator has no cap, no clamp and no size filter, and it gives an inverted box a non-zero area. Steps equal to the operator cannot describe the mmdet decode. The spec defines the steps, and a host can use the operator when it applies the rules of 2.3 to its inputs and outputs. | Part 1; 2.8 (onnx 1.23.2 `defs.cc:140`, `op_non_max_suppression.py:56-67`); vector `inverted-box-has-area-zero` (the host keeps 1 row, the spec 2). |
| 19. `[B, Q, C]` scores from `class_logits_output` with `selection: nms`, with a class-agnostic path that takes the `ReduceMax` over the classes | `V-post.det.selection.nms-1` forbids `class_logits_output` with `selection: nms` (`selection-nms.md:61`). skellytracker 0011 keeps that rule, and the changelog lists "`class_logits` with `selection: nms`" as not added (`changelog.md:48`). No family in scope needs it. | skellytracker 0011 "Decision" and "Not repeated"; part 2.4. |
| 20. Append an NMS to the graph with a tool (the standard ONNX `NonMaxSuppression` or `EfficientNMS_TRT`) and declare `selection: none` | skellytracker 0011 puts the NMS on the host: the capped mmdeploy graph lost 0.0114 AP on `rtmdet-person-medium` (OpenMMLab-Exporter 0008). A graph-final NMS also has fixed caps and the inverted-box area of the operator. `EfficientNMS_TRT` is a TensorRT plugin, not an ONNX operator, so ONNX Runtime without TensorRT cannot run it. | skellytracker 0011, "Reason" and "Alternatives rejected"; OpenMMLab-Exporter 0008. |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake links to this proposal (the untracked intake of `rtmdet-person` of OpenMMLab-Exporter (plan facts), rows D4a, D12, D9a and D12a, "Gaps with no proposal" and "Proposals and reference files").
- [x] The header gives the dependencies, or `none`. (`none`; the merge points, and the scope-entry merge point with `roi-transform-and-source` (user decisions T34 N2 and T35), are in "Merge points" below the Header.)
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or `none`. This proposal builds on such an entry. It does not compete with it. (`none`; the accepted entries skellytracker 0011 and 0008 are named, with the rules that change; the open-work item on `clamp_boxes` is named.)
- [x] The subsection "Superseded skellytracker plans" names both skellytracker plans and what this proposal does with each. It records that the user deleted both files on 2026-10-24 (the skellytracker session has nothing to delete), where copies of the text stay, and that no tracked file may cite them.
- [x] Part 2.1 has a row for the two local plan files (deleted by the user, 2026-10-24; no action). No text that this proposal gives for a tracked skellytracker file (part 2, the decision entry) cites a skellytracker `plans/` file.
- [x] "Effect on skellytracker decisions 0011 and 0008" gives the form of the two entries (user decision T35): for each, the file name, the title, the status, the entry text with the restated rules (entry A: skellytracker 0011; entry B: skellytracker 0008; corrected against both entries at skellytracker `dom/18-agents-adr-bootstrap-kit`) and its size (entry A 5,610 and entry B 4,309 of 6,000 characters). It gives the variant of entry B for the case that the ROI-transform scope entry lands first (4,691 characters) and the checker result (exit 0 in four scenarios; scratch `t35\run_checker.py`). The checker ran on the `dom/18-agents-adr-bootstrap-kit` log. A skellytracker session must run it again on the current log (skellytracker 0032 to 0034 are new). The entries skellytracker 0008 and 0011 did not change between `dom/18-agents-adr-bootstrap-kit` and `dom/21-move-sidecar-guide`.
- [x] The same subsection gives the evidence file: its name (`NNNN-rtmdet-host-nms-filters.evidence.md`, which the checker does not read as an entry), its location beside entry A, the evidence that moves into it, and the link from entry A. A skellytracker session writes the three files. This proposal only describes them.
- [x] Part 2.1 has a row for entry A, a row for entry B and a row for the evidence file.
- [x] The subsection "Merge points" (below the Header) gives the merge point with `roi-transform-and-source` (user decisions T34 N2 and T35): only the scope entries meet there. The scope change that lands second supersedes the scope entry in force and restates its scope rules with its own change. Entry A has no merge point there.
- [x] The inverted-box finding is in 2.3 (the operator paragraph and step 4), 2.8 (implementer guidance, with the onnx lines), part 4 (vector `inverted-box-has-area-zero`, mutant D1 and the host result), part 6 (the advisory notes) and part 7 (the known host gap; `onnx_runtime/` is not changed).
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing. (The config keys, the graph read, the upstream output and the mmdet v3.3.0 and mmcv v2.1.0 code lines are cited by permalink.)
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in `plans/`.
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`. (`unverified`: the host matches 9 cases, differs on `inverted-box-has-area-zero`, and has no code for the other 19.)
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a: no pixel case; every value is exact.
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the script. Tick this box also for `to run` with a description of the script.
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter repo. n/a: the result is `to run`.
- [x] No file in skellytracker changed.

A proposal with `to run` in part 5 is ready for a skellytracker session to record. It is not ready for
the user to accept: part 5 needs the committed script and the export error.

**Decisions of the user (2026-10-24).**

- `clamp_boxes` for `rtmdet-person`: `false`, the exact mmdet mapping (plan T28 N1).
- Write the candidate filters as a proposal that supersedes skellytracker 0011 (T28 N2), and also
  skellytracker 0008 in full, with the other rules restated (T30 F2, T32 P4 (a)). T35 revises the form (last item).
- Correct the exporter notes about the mmdet clamp in a new decision entry (T28 N3). Do not change
  `onnx_runtime/` in this work (T28 N3/N4, T30 F3). The host tie order needs no change for rank-2
  scores (T28 N4).
- Commit the parity script `notes/decisions/scripts/rtmdet_nms_clamp_parity.py` with the next code
  change, and read the mmdet lines when Docker runs (T28 N5). The lines were read on GitHub at the
  tag on 2026-10-25 (part 1).
- Merge the two NMS proposals into this file with one reference file (T32 P1 (a), P2 (a)). The
  user deleted the two skellytracker NMS plans on 2026-10-24 (T32 P3 (a), T34). Remove
  the RTMO notes (T32 P5 (b)). Add the vector `inverted-box-has-area-zero` (T32 P6). Keep
  `decode_prenms` for YOLOX (P7). Keep `clamp_xyxy` here (P8). Keep the useful host advice of the old
  plan, with no provider table (P9). Replace the AP targets (P10).
- The NMS entry is one entry that supersedes skellytracker 0011 and 0008 in full, with its evidence in
  one tracked file beside it (T34 N1 (a); revised by T35, next item). The two proposals that change
  skellytracker 0008 (this one and
  `roi-transform-and-source`) each say that the entry that lands second restates the change of the
  first (T34 N2; T35 limits this to the scope entries, next item).
- P4 revised (T35; it supersedes T32 P4 (a) and T34 N1 (a) in part): two skellytracker entries. Entry
  A, the NMS entry, supersedes skellytracker 0011 in full, with the evidence file. Entry B, a small
  `vNEXT` scope entry, supersedes skellytracker 0008 in full. It restates the scope list and the "not added" groups, with the NMS
  change. A later scope change (for example the ROI-transform proposal) supersedes only the scope
  entry in force and restates only scope rules. Thus the feature rules never couple.

**Open questions for the user.** None. User decision T35 solved the earlier question 1 (complete
supersession at the skellytracker 0008 merge point): the feature rules and the scope rules are in different
entries, so the second scope entry restates only the scope rules of the first.

## Before acceptance

This list gives the work that must be done before the user can accept the proposal. A skellytracker
session made it from a check of the proposal on 2026-10-25.

**Parts**

- [ ] Part 2.1 must list each place that the change edits. These places are not in the table:
  `specs/model-sidecar/post/selection-nms.md:78` ("No reference implementation exists yet"), the
  `external_impl` front matter of `selection-nms.md`, `specs/exporter-guide/sidecars/known-open-items.md:7`
  (no reference implementation exists for `selection: nms`), the open-work item "NMS box area",
  `notes/sidecar-exporter-coverage.md:128, 237, 267`, the heading "Selection behaviour" of
  `specs/model-sidecar/post/detection-decode.md` (it owns the tie rule), `tools/make_vectors.py`
  (`_selection_notes` and the `post.unprojection` notes) and `tools/tests/test_vectors.py`.
- [ ] Part 3: each function docstring of the reference code must cite its section ID. The guide
  ("Reference implementations") also asks for the exporter commit. `score_order` cites
  `post.det.decode`, `split_detection_rows` cites `post.det.outputs`, and `axis_affine_unprojector`
  cites no section. Only the module note cites the commit `d0f4343`.
- [ ] Part 3: the reference code also holds code of other sections: `clamp_xyxy` (the clamp of
  `clamp_boxes`, `post.det.decode`), `resolve_classes` and `DEFAULT_CONFIDENCE_THRESHOLD`
  (`post.det.decode` fields), `split_detection_rows` (`post.det.outputs`) and a test inverse of
  `post.unprojection`. The guide says: "Do not put two sections together in one module." Part 3 gives
  a reason only for `clamp_xyxy`.
- [ ] Part 7 must name the RTMO body7 reference example
  (`specs/model-sidecar/examples/detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml`). It is an
  OpenMMLab-Exporter `vNEXT` sidecar with `selection: none` and `clamp_boxes: true`. The closed bounds
  and the zero-area row of `clamp_boxes` apply to it.
- [ ] Part 7 must give the effect on RF-DETR of the new condition in step 6 of
  `post.det.selection.top_k` ("When `clamp_boxes` is true, clamp the boxes").

**Evidence**

- [ ] Part 5 is `to run`. OpenMMLab-Exporter must commit the parity script (proposed name
  `notes/decisions/scripts/rtmdet_nms_clamp_parity.py`) and give its commit. Until then, the numbers
  of part 1, part 4 and part 5 come from scratch scripts. They are not evidence.
- [ ] The export error (the ONNX file against the PyTorch head outputs on the same tensor) is
  `to run`.
- [ ] The difference of the preprocessed input against the mmdet tensor is `to run`.
- [ ] The part 5 result must be `pass` or `fail`, with the gates (a) to (e) asserted by the committed
  script.
- [ ] The mmdet source predictions files of part 1 are not tracked (producer `e67fc2a`). Part 1 cites
  them by file name only. Decide how the evidence cites them.
- [ ] Check that the mmdet commit `44ebd17b145c2372c4b700bfb9cb20dbd28ab64a` (tag v3.3.0) and the
  mmcv commit `57c4e25e06e2d4f8a9357c84bcd24089a284dc88` (tag v2.1.0) are on the default branch of
  their repos. A permalink must pin such a commit. The mmdeploy lines come from a local clone at
  `bc75c9d6c8940aa03d0e1e5b5962bd930478ba77`, with no permalink.
- [ ] The heading "Effect on skellytracker decisions 0011 and 0008" names the evidence file
  `notes/decisions/NNNN-rtmdet-host-nms-filters.evidence.md`. Decision 0036, item 5, puts it at `specs/model-sidecar/proposals/nms-clamp-order/evidence.md`. That file
  holds the evidence of 0011. For the measurements of the proposal, it only links to part 1 and
  part 5. The Evidence section of 0041 says that the file holds the COCO val2017 measurements of the
  proposal. Put the measurements of the row "New (this proposal)" in the evidence file, or change
  the text of 0041.
- [ ] The new guidance bullets of part 2.8 give "this proposal, part 1", "part 4" or "part 5" as
  their source. The part 5 numbers are `to run`. The Authoring guidance bullet also names an
  untracked predictions file. Before the content PR copies these bullets into `selection-nms.md`,
  replace each source with a tracked source, for example the committed script by permalink or the
  evidence file.

**Template checklist**

- [ ] "One contract unit for each proposal": the proposal changes `post.det.selection.nms`, the
  `clamp_boxes` row of `post.det.decode`, step 6 of `post.det.selection.top_k`, step 3 of
  `post.det.selection.none` and the guidance of `post.unprojection`. Part 8, alternative 17, gives
  the reason.
- [ ] "Part 2.1 lists each place that the change edits" is ticked. It is not fully true (see
  **Parts**).
- [ ] The checker run of "Effect on skellytracker decisions 0011 and 0008" used an older decision
  log. Run `uv run python tools/check_decision_log.py` again with 0040, 0041, 0042 and the other
  recorded proposals.
- [ ] Part 2.4: the changed rule `V-post.det.selection.nms-1` and the new rule
  `V-post.det.selection.nms-2` have no `(vNEXT)` mark. The current rule has no mark either, and the
  section has no line "Rules marked (vNEXT)". Decide one form for the section.

**Vectors and tooling**

- [ ] `tools/tests/test_vectors.py` rejects the case form of part 4. `CASE_KEYS` has no `function`
  key. `generated_by` must be `tools/make_vectors.py`. Each vector file must be smaller than 16 KiB.
  The current file has 9,850 bytes. With the 29 new cases, it has about 28 KB.
- [ ] `_iou` in `tools/tests/test_vectors.py` divides by zero on the case `zero-union-gives-iou-zero`.
  `test_nms_result_obeys_the_rules` uses the input boxes, not the clamped boxes.
- [ ] The 20 existing cases use `boxes_xyxy`. The new cases use `boxes_model`, `boxes_source` and
  `boxes`, and they put `unproject` in `input`. The case key `unproject` has a different meaning in
  `tools/make_vectors.py` and `tools/tests/test_vectors.py`. Use one form, or define both forms in
  the header notes.
- [ ] The header notes of the vector file come from `_selection_notes` in `tools/make_vectors.py`.
  The vector files of `selection: none` and `selection: top_k` use the same helper. A change of the
  NMS note needs a note for NMS only. The `post.unprojection` note on the open clamp bound is at
  `tools/make_vectors.py:2392-2395`.
- [ ] `post.det.decode` has `vectors: null`. Decide where the five `clamp-boxes-*` cases go.
  `specs/model-sidecar/vectors/post.unprojection.yaml` still says that no case reaches the upper bound or
  loses its area.
- [ ] The content PR needs a test that runs the reference functions against the vectors
  (`change-sidecar-spec`, Procedure B, step 7). `specs/model-sidecar/reference/` does not exist yet.

**Decisions for the user**

- [ ] Accept the two extra entries, [0041](../../decisions/0041-rtmdet-host-nms-filters.md)
  (supersedes 0011) and [0042](../../decisions/0042-vnext-scope-nms-filters.md)
  (supersedes 0008), and the evidence file [`evidence.md`](evidence.md). The exporter plan records
  this form as the user decisions T35 and T34 N1 (plan facts). Decision 0035 also defines the status
  `evidence` for an entry.
- [ ] Choose the order of 0042 and the scope entry 0048 of `roi-transform-and-source`. Both supersede
  0008 in full. If 0048 lands first, 0042 must use the text "Variant of entry B" and supersede 0048.
- [ ] Accept the change of more than one section, or split the `clamp_boxes` row and the edit of
  step 6 of `post.det.selection.top_k` into a separate proposal.
- [ ] Steps 1, 4 and 5 restate the tie rule that "Selection behaviour" of `post.det.decode` owns
  (decision 0013, one owner for each rule). Accept the restatement, or link to the owner.
- [ ] Decide if the reference code keeps the helpers of `post.det.decode`, `post.det.outputs` and
  `post.unprojection`, or if the content PR moves them out.
- [ ] Decide if `selection-nms.md` gets `external_impl` for the host `NmsDecoder`. The host fails the
  case `inverted-box-has-area-zero` and has no code for the new fields.
- [ ] Decide if 0041 gets a "Depends on" line for the commit of the OpenMMLab-Exporter parity script
  and for the planned OpenMMLab-Exporter entry on the mmdet clamp.

**Merge points**

- [ ] `roi-transform-and-source` (0020, scope entry 0048): the chain of 0008 supersessions; the table
  "Considered and deliberately not added" of `specs/model-sidecar/changelog.md` (this proposal deletes the
  rows `nms.pre_nms_top_k` and `nms.min_bbox_size`); the Implementer guidance of
  `specs/model-sidecar/post/unprojection.md`; rows D11 and D12 of `specs/model-sidecar/templates/model-intake.md`.
- [ ] `landmark-extra-outputs` (0021) and `roi-refiner-role` (0047): `detection-decode.md:42` and
  `:77`, next to the `clamp_boxes` row (`:43`) and `V-post.det.decode-5` (`:74`).
- [ ] `keypoint-visibility` (0039), `landmark-extra-outputs` (0021) and `omitted-upstream-output`
  (0044): "Outputs and decode" of `specs/exporter-guide/sidecars/workflow/mapping-hints.md`.
- [ ] `model-id-suffix` (0025): `specs/model-sidecar/examples/README.md`.
- [ ] `affine-crop-arithmetic` (0037): it regenerates `specs/model-sidecar/vectors/post.unprojection.yaml`.
  This proposal changes the header notes of that file.
- [ ] All proposals: row N of "Summary of changes" and the `vNEXT` row of the `schema_version` history
  in `specs/model-sidecar/changelog.md`.
- [ ] `notes/decisions/open-work.md`: this proposal closes the spec defect on `clamp_boxes`. The item
  "NMS box area" can need new words.

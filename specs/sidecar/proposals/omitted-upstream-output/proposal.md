---
slug: omitted-upstream-output
section: none
exporter: OpenMMLab-Exporter
decision: "0044"
state: recorded
---
# Change proposal: omitted-upstream-output

This file is informative. It is not part of the normative spec until a content PR lands its text in the section files (decision [0036](../../../../notes/decisions/0036-spec-proposals-folder.md)).

**Source.** The OpenMMLab-Exporter file of the proposal `omitted-upstream-output`, at OpenMMLab-Exporter commit [`f3aeb47`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/f3aeb473d3396ee79c4394646a34ed9ef419ecf1), copied on 2026-10-25. The copy changes only the items of decision 0036, item 3. The session wrote no part.

This file uses ASD-STE100 Simplified Technical English. It follows the change proposal template
(`specs/sidecar/templates/change-proposal.md` of the skellytracker repo), "Phase 2" of the exporter
guide (`specs/exporter-guide/sidecars/workflow/phase-2-proposal.md`) and the skill `propose-sidecar-change`. It is the phase 2
proposal of user decision T36 (2026-10-24, the untracked pose-models plan of OpenMMLab-Exporter (plan facts), row T36).

This proposal asks for a change of the workflow rules, not of a spec section. The exporter guide, the
model intake template and the skill `author-sidecar` are informative. The verdict list is also a rule
of skellytracker decision 0014 (accepted). The change has no algorithm, no sidecar field and no
vectors (parts 3 to 5).

**User decision T36 (2026-10-24, question 1).** RTMW intake row K8a (the 384x288 configs set
`decode_visibility=True`) gets the verdict `out of scope (0041)`. The tag `(0041)` in a verdict
names OpenMMLab-Exporter decision 0041. This is an explicit user decision:
the guide lets the user decide such a row (guide, Phase 1 step 4, `exporter-guide/sidecars/workflow/phase-1-intake.md:50-51`). This
proposal asks skellytracker for a guide rule for such a row, so that the next row of this kind needs
no user decision. Until skellytracker accepts a rule, T36 stays in force. This proposal does not
change T36.

## Header

| Field | Value |
|---|---|
| Title | A verdict for an upstream output that the exporter deliberately leaves out of the sidecar (`omitted`) |
| Slug | `omitted-upstream-output` |
| Date | 2026-10-24, updated 2026-10-25 (pin moved to `dom/21-move-sidecar-guide`; `none` forms in part 5; repo names with decision numbers) |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `f3aeb473d3396ee79c4394646a34ed9ef419ecf1` (branch `rtmo-model-id-variant`, local, not pushed; OpenMMLab-Exporter decision 0050). OpenMMLab-Exporter decision 0041 is commit `9deff61c3299c9cd06f933f01d7be07ed3fe0167` (merged in `32ab848`). `git status --porcelain` is empty. |
| Model, and its intake file (the untracked intake of `<model>` of OpenMMLab-Exporter (plan facts)) | `rtmw-wholebody133`, the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts) |
| Intake rows with the verdict `near-miss` or `gap` | Row K8a (keypoint visibility of the 384x288 sizes, line 193). Its first verdict was `gap`. User decision T36 gives it `out of scope (0041)` (OpenMMLab-Exporter decision 0041), and the intake now has that verdict. It is the only row of this kind. This proposal asks for the verdict `omitted (0041)` (part 2). |
| User decisions | T36 (2026-10-24, the untracked pose-models plan of OpenMMLab-Exporter (plan facts), row T36): see the note above the header. T37, T38, T39 and T40 do not apply to this proposal. |
| Kind (`new section` or `changed section`) | Neither: changed workflow text. The informative exporter guide, the model intake template, the skill `author-sidecar`, and a new skellytracker decision entry that supersedes skellytracker decision 0014 in full (part 2.1). No section file changes. |
| Proposed section ID (the `id` in the section file's front matter) | none (no spec section; the change is a verdict rule of the workflow) |
| Section file | none. The changed files: `specs/exporter-guide/sidecars/rules.md`, `specs/exporter-guide/sidecars/workflow/phase-1-intake.md`, `specs/exporter-guide/sidecars/workflow/parity.md`, `specs/exporter-guide/sidecars/workflow/mapping-hints.md`, `specs/sidecar/templates/model-intake.md`, `.claude/skills/author-sidecar/SKILL.md`, `notes/decisions/NNNN-<slug>.md` (new) and `notes/decisions/README.md` (part 2.1). |
| Depends on (proposal files that must land first, or `none`) | none |
| Needed by (proposal files that depend on this one, or `none`) | none. **Related (merge point, no order):** `specs/sidecar/proposals/keypoint-visibility/proposal.md`. Its header names this file for row K8a. Its part 2.1 adds a sentence to the guide hint "Pose" (`exporter-guide/sidecars/workflow/mapping-hints.md:62-65` at `dom/21-move-sidecar-guide`): "Another value, or a value that the host must compute from other outputs, is a gap." That sentence conflicts with the verdict `omitted`. Part 2.1 (place G8) gives the merged text. The content PR or the documentation PR that lands second keeps the edits of both. |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | none. The index (`notes/decisions/README.md:21-51` at `dom/21-move-sidecar-guide`) has no entry about intake verdicts or an omitted output. Near entries: **skellytracker decision 0021** (proposed, gap record) lets a model declare outputs beside its landmarks. It is about outputs that the sidecar declares, not about an output that it leaves out (`0021-landmark-extra-outputs.md:11-26`). **skellytracker decision 0018** (proposed, gap record) is about a tensor that a sidecar declares two times (`0018-one-declaration-per-tensor.md:7-17`). Neither covers this row. The accepted entry **skellytracker decision 0014** states the verdict list (`0014-spec-lifecycle.md:81-92, 94, 110-117`). This proposal changes it (part 2.1). `open-work.md` has no item about verdicts. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `dom/21-move-sidecar-guide` (branch `dom/sidecar-implementation`, skellytracker decision 0034). On 2026-10-25 `git status --porcelain` lists only an untracked `grep.exe.stackdump`; it is not a spec file and I did not read it. First written at `dom/20-sidecar-copy-block` (skellytracker decision 0033). From `dom/18-agents-adr-bootstrap-kit` to `dom/20-sidecar-copy-block`, `git diff --stat -- specs/sidecar .claude` lists only `exporter-guide.md` (the new heading "The block for the exporter `AGENTS.md`": the lines after line 67 move down by 31; the Phase 1 text does not change) and one citation line of `propose-sidecar-change/SKILL.md` (skellytracker decision 0028 to skellytracker decision 0032). From `dom/18-agents-adr-bootstrap-kit` to `dom/20-sidecar-copy-block` the templates do not change. From `dom/20-sidecar-copy-block` to `dom/21-move-sidecar-guide`, the guide moved from `specs/sidecar/exporter-guide.md` to `specs/exporter-guide/sidecars/*` with no change of text (skellytracker decisions 0033 and 0034). Under `specs/sidecar/`, in the skills and in `AGENTS.md` only link text changed (`templates/change-proposal.md:4-7`, `templates/model-intake.md:2-8`, five section files, `TRACEABILITY.md`, `inventory.yaml`, `author-sidecar/SKILL.md`, `propose-sidecar-change/SKILL.md`, `AGENTS.md`). The cited lines of the templates, the skills and `AGENTS.md` did not move. The guide, template, skill and decision-log line numbers in this file are at `dom/21-move-sidecar-guide`. The spec text did not change after the first pin (only link repairs). |

**Upstream copies.** This session has no network. The mmpose v1.3.2 lines in part 1 are the lines
that RTMW intake row K8a cites, in the same copies ("copy B" of the intake: the scratch folder
`upstream/` of a session of 2026-10-23, not committed; the intake, "Upstream copies", lines 9-26).
I read each cited line again in copy B on 2026-10-24. The config lines are lines of the exporter
copies under `mmdeploy-convert/model_cfgs/`, which differ from upstream only in `_base_` and the val
image prefix (`mmdeploy-convert/CONFIG_SOURCES.md:23-27`).

## 1. Gap

The verdicts of phase 1 (exporter guide, Phase 1 step 3, `exporter-guide/sidecars/workflow/phase-1-intake.md:23-44`; model intake
template, "Verdicts", `model-intake.md:105-124`) have no verdict for an upstream decode output that
the exporter deliberately leaves out of the sidecar. Such an output is inside the runtime contract, so
it is not `out of scope`. The exporter does not want a spec field for it, because no consumer uses it
and a measurement shows that it is not useful. Today the row is a `gap` (it blocks the final verdict
`describes` and needs a proposal for a field that nobody wants), or the user gives it `out of scope`
by an explicit decision (T36). Two agents can give such a row different verdicts.

| Item | Value |
|---|---|
| Property | The per-keypoint softmax visibility `keypoints_visible` that the upstream decode of the two RTMW 384x288 configs gives beside `keypoint_scores`. The sidecar does not declare it (OpenMMLab-Exporter decision 0041, option E). In general: an upstream decode output that the exporter deliberately leaves out of the sidecar. |
| Upstream evidence (file and line, or config key; upstream commit or release) | mmpose v1.3.2 (the image clones the tag at commit `5408bc76f5b848cf925a0d1857899011d8c5b497`, `mmdeploy-convert/Dockerfile.exporter:34, 42-44`). The 384 configs set `decode_visibility=True` in the codec (line 55 of `rtmw-l_8xb320-270e_cocktail14-384x288.py` and `rtmw-x_8xb320-270e_cocktail14-384x288.py`). `SimCCLabel.decode` then returns `(scores, visibility)`, with `visibility` from `get_simcc_maximum(simcc_x * decode_beta * sigma[0], simcc_y * decode_beta * sigma[1], apply_softmax=True)` (`simcc_label.py:193-198`; `decode_beta = 150.0`, line 77; `sigma=(6., 6.93)`, 384 config line 51). `BaseHead.decode` keeps the first value as `keypoint_scores` and stores the second as `keypoints_visible` (`base_head.py:81-83, 91-93`, copy B). For the 256x192 sizes, `add_pred_to_datasample` sets `keypoints_visible = keypoint_scores` (`topdown.py:157-159`). The COCO-WholeBody metric reads `keypoint_scores` (`coco_metric.py:210-219, 450`, copy B). These are the citations of RTMW intake row K8a (the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts)). |
| Nearest section ID (the `id` in the section file's front matter) | none (no section holds a verdict). The nearest rules: the verdict `gap` (`exporter-guide/sidecars/workflow/phase-1-intake.md:30-33`; `model-intake.md:111`) and the verdict `out of scope` (`exporter-guide/sidecars/workflow/phase-1-intake.md:36-38`; `model-intake.md:113`). The nearest spec section for the property is `post.pose.decode.simcc`: its authoring guidance says that the sidecar has no field for `decode_visibility` (`specs/sidecar/post/pose-decode-simcc.md:58`). |
| Why the nearest section is wrong | **`gap`.** The spec has no field for the visibility, so the test of step 3 gives `gap` (`exporter-guide/sidecars/workflow/phase-1-intake.md:42-44`). A `gap` row goes to phase 2 (step 4, `:46-48`) and gives the final verdict `does not describe` (step 6, `:63`). But the exporter does not need a field. OpenMMLab-Exporter 0041 measured the visibility and dropped it for all sizes (option E of `specs/sidecar/proposals/keypoint-visibility/proposal.md`: the proposed field `pose.decode.visibility` has no SimCC source). A proposal for a SimCC visibility field would ask for a feature that no consumer reads. **`out of scope`.** The test of this verdict is the position of the step: "before or after the runtime contract" (`exporter-guide/sidecars/workflow/phase-1-intake.md:36`; `model-intake.md:113`). The contract "ends at the decoded outputs in source-image coordinates" (`exporter-guide/sidecars/workflow/phase-1-intake.md:14-16`; `model-intake.md:113`). The visibility comes from the same decode call that gives the keypoints and `keypoint_scores` (`simcc_label.py:193-198`), so it is inside the contract. The user had to decide the row (T36). The tag `(0041)` (OpenMMLab-Exporter 0041) in the T36 verdict shows that the verdict alone does not tell the reason. **The result.** The guide has the goal that two agents give the same verdict (`model-intake.md:115`). For this row, one agent gives `gap` and the user gives `out of scope`. |
| Measured difference (number, image and script) | **The omission changes no declared output.** `BaseHead.decode` keeps the first value as `keypoint_scores` and stores the visibility as a separate field (`base_head.py:81-83, 91-93`). The keypoints are the same with and without the flag (`simcc_label.py:191-198`: `keypoints /= self.simcc_split_ratio` comes before the branch). The graph has no extra output: the 384x288 old-id exports have only `simcc_x` and `simcc_y` (intake row K8a, old-id graph, secondary). The difference of the declared outputs is thus 0 by the code. No parity run measured it (part 5). **The output is not useful (OpenMMLab-Exporter decision 0041, evidence, commit `9deff61`; scripts `notes/decisions/scripts/rtmw_wrist_gate_*.py`; COCO-WholeBody v1.0 val, 12704 hands, GT boxes; the ranking on the 4656 hands (36.6 %) that Holistic can track).** The visibility of each size, with its own config `sigma`, ranks valid hands worse than the raw score: AUC difference `vis_w - s_w` −0.046 to −0.094, each 95 % upper bound below 0 (OpenMMLab-Exporter 0041, table "Ranking"; l-384 −0.091 [−0.105, −0.077], x-384 −0.094 [−0.106, −0.080]). At 384x288 it saturates on most wrists: one threshold opens almost every hand (recall 1.000, false open 0.997 and 1.000). At 256x192, 95 % of the wrists with visibility `>= 0.995` have `v = 0`. Four of the five sizes fail the fp16 test (x-384: AUC difference −0.051). Every size fails rule S7 (OpenMMLab-Exporter 0041, table "S7: visibility for all sizes"). **No consumer reads it.** The COCO-WholeBody metric reads `keypoint_scores` only (`coco_metric.py:210-219, 450`). The skellytracker RTMW detector fills `Keypoints.visibility` from the keypoint scores (`skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py:103-106`). The one consumer that could read a visibility is the score gate of the MediaPipe hand ROI refiner. With an RTMW parent it reads `score` at every size (MediaPipe-Exporter `specs/sidecar/proposals/roi-refiner-role/proposal.md`; OpenMMLab-Exporter 0041, Qa and S4). |
| Row in "Considered and deliberately not added" (`specs/sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none. The table (`changelog.md:42-53`) lists spec features. It has no row about verdicts, and no row for a keypoint visibility. This proposal adds no spec feature. The rule "a property that the spec lists in 'Considered and deliberately not added' is a `gap`" (`exporter-guide/sidecars/workflow/phase-1-intake.md:31-33`) does not change (part 2.1, condition 2). |

## 2. Spec change

The change is in the informative workflow text and in one decision entry. It changes no normative
spec text and no sidecar. The exact text of each edit is in part 2.1.

**The choice: option (a), a new verdict `omitted`.** Part 8 gives option (b), a wider
`out of scope`, and the reasons to reject it. The reasons for (a):

1. `out of scope` has one test: the position of the step relative to the runtime contract. An agent
   applies it with no evidence other than the step. `omitted` needs evidence: the upstream lines and
   a measurement. One verdict with two tests of different strength hides which test a row passed.
2. An `out of scope` row goes to the table "Steps outside the model contract" (`model-intake.md:366-375`)
   with the section `none`. An omitted output is a property of a section inside the contract (row K8a
   is in the "Pose" table, section `post.pose.decode.simcc`). The row stays in its table.
3. The user reads the two verdicts for different decisions. For `out of scope`, the user decides if
   the spec must describe such steps (`exporter-guide/sidecars/workflow/phase-1-intake.md:50-51`). For `omitted`, an exporter
   decision has already accepted a known loss, with its measurement. The user decides only if a
   consumer now needs a field.
4. A reader of the intake sees the known loss in the verdict itself. A later consumer can find it.

**Places that the change edits.** I searched the skellytracker checkout for the verdict list, for
the rules that name `out of scope` as a verdict, and for the rules that send each property that the
spec does not describe exactly to `near-miss`, `gap` or a proposal:
`git -C ../freemocap/skellytracker grep -n -i -e "out of scope" -e "describes" -e "approximat" -e "exactly" dom/21-move-sidecar-guide -- specs .claude notes/decisions AGENTS.md`.
The hits that use `out of scope` in its normal meaning (for example "Multi-input models are out of
scope", `specs/sidecar/common/input.md:37`) do not change. The hits of "approximat" and "exactly"
that do not change are about a `near-miss` or `gap` row, about parity or about other subjects (for
example `model-intake.md:110, 471, 520`; `author-sidecar/SKILL.md:150`; `exporter-guide/sidecars/workflow/phase-1-intake.md:26`, `exporter-guide/sidecars/workflow/parity.md:7`;
`0014-spec-lifecycle.md:84`, which D1 restates). The four rules on an exact mapping are T0, G10 and
the two "no change" lines below.

### 2.1 Sections

No section file changes. No row of the section map changes. These are the edits.

**G. `specs/exporter-guide/sidecars/` (informative; heading "Sidecars").**

- **G1. Phase 1, step 1 (`exporter-guide/sidecars/workflow/phase-1-intake.md:14-16`).** No change. The runtime contract and its boundaries stay.
- **G2. Phase 1, step 3 (`exporter-guide/sidecars/workflow/phase-1-intake.md:23-38`), after the bullet `out of scope` (`:36-38`).** Add:

  ```markdown
     - `omitted`: the upstream decode gives an output that the sidecar deliberately does not
       declare, and each of these conditions is true:
       1. The output is a value beside the outputs that the sidecar declares, for example a second
          value for each keypoint. Its omission changes no declared output: the tensors, the boxes,
          the scores, the keypoints and the row counts that the sidecar declares are the same with
          and without it. Cite the upstream line that shows this.
       2. The spec does not require the output. The spec does not call it out of scope, and
          "Considered and deliberately not added" does not list it. Such an output stays a `gap`.
       3. The upstream evaluation metric of the model does not read the output. Cite the line that
          reads the metric input.
       4. No known consumer needs the output. A consumer is a host or a model that reads the
          outputs of this model, for example a refiner that gates on a point of its parent. For
          each known consumer that could use the output, a committed measurement shows that a
          declared output serves that consumer at least as well. Cite the measurement.
       5. The sidecar declares nothing for the output: no output, no field and no channel.
       6. An exporter decision entry records the omission, its reason and its evidence. Write its
          number after the verdict, for example `omitted (0041)` for OpenMMLab-Exporter decision
          0041.
  ```

- **G3. Phase 1, step 3, the paragraph "To choose between `near-miss` and `gap`" (`exporter-guide/sidecars/workflow/phase-1-intake.md:42-44`).**
  Add before it:

  ```markdown
     Before you choose between `near-miss` and `gap`, check the conditions of `omitted`. If each
     condition is true, the verdict is `omitted`. If a condition is false, the row is not
     `omitted`: use the test below. A sidecar that leaves out an output that changes a declared
     output is an approximation, not an omission.
  ```

- **G4. Phase 1, step 4 (`exporter-guide/sidecars/workflow/phase-1-intake.md:45-51`), after the bullet "An `out of scope` row".** Add:

  ```markdown
     - An `omitted` row: write no proposal. Tell the user about the row when you stop. The user
       decides if the spec must describe the output. A later proposal can add a field for it when
       a consumer needs it.
  ```

- **G5. Phase 1, step 5 (`exporter-guide/sidecars/workflow/phase-1-intake.md:52-60`).** Add a bullet after the first bullet:

  ```markdown
     - The sidecar declares nothing for an `omitted` row.
  ```

- **G6. Phase 1, step 6 (`exporter-guide/sidecars/workflow/phase-1-intake.md:61-64`).** Old: "- `describes`: every row is `exact` or
  `out of scope`, and parity passes." New: "- `describes`: every row is `exact`, `out of scope` or
  `omitted`, and parity passes." The bullets `does not describe` and `pending` do not change.
- **G7. "Parity", step 5 (`exporter-guide/sidecars/workflow/parity.md:33-41`).** After "A model with both roles needs both comparisons. A
  keypoint metric does not check the boxes." add: "Do not compare an `omitted` output. The
  comparisons of the declared outputs pass with the output left out (condition 1 of `omitted`)."
- **G8. "Mapping hints for phase 1", "Pose" (`exporter-guide/sidecars/workflow/mapping-hints.md:62-65`).** No change at `dom/21-move-sidecar-guide`. **Merge point:**
  the keypoint-visibility proposal adds "Another value, or a value that the host must compute from
  other outputs, is a gap." The merged sentence: "Another value, or a value that the host must
  compute from other outputs, is a gap, unless each condition of `omitted` is true (Phase 1,
  step 3)."
- **G9. "Mapping hints for phase 1", after "Near-misses seen so far" (`exporter-guide/sidecars/workflow/mapping-hints.md:66-71`).** Add:

  ```markdown
  - **Omitted outputs seen so far.**
    - The softmax visibility of the two RTMW 384x288 configs (`decode_visibility=True` in the codec
      `SimCCLabel`). The head stores it as `keypoints_visible` beside `keypoint_scores`. The
      COCO-WholeBody metric reads only `keypoint_scores`. On COCO-WholeBody the visibility ranks
      valid hands worse than the raw score at every size (OpenMMLab-Exporter 0041). The verdict is
      `omitted`.
  ```

- **G10. "Rules" (`exporter-guide/sidecars/rules.md:4-5`).** Old: "If a model property does not map exactly to the spec, do not use
  an approximate mapping. Write a change proposal (phase 2) and stop." New: "If a model property does
  not map exactly to the spec, do not use an approximate mapping. Write a change proposal (phase 2)
  and stop. An output that meets each condition of `omitted` (Phase 1, step 3) is `omitted`, not an
  approximation."

**T. `specs/sidecar/templates/model-intake.md`.**

- **T0. "How to use", step 5 (`:29-30`).** Old: "Do not approximate a property. If the spec does not
  describe a property exactly, the verdict is `near-miss` or `gap`." New: "Do not approximate a
  property. If the spec does not describe a property exactly, the verdict is `near-miss` or `gap`. An
  output that meets each condition of "Omitted output" is `omitted`, not an approximation."
- **T1. "Verdicts", the table (`:105-113`).** Add a row after `out of scope`:

  ```markdown
  | `omitted` | The upstream decode gives an output that the sidecar deliberately does not declare, and each condition of "Omitted output" below is true. Write the number of the exporter decision entry after the verdict, for example `omitted (0041)` for OpenMMLab-Exporter decision 0041. |
  ```

- **T2. "Verdicts", after the test "Near-miss or gap" (`:115-124`).** Add:

  ```markdown
  **Omitted output.** Check these conditions before the test "Near-miss or gap". If each condition
  is true, the verdict is `omitted`. If a condition is false, use the test.

  1. The output is a value beside the outputs that the sidecar declares, for example a second value
     for each keypoint. Its omission changes no declared output: the tensors, the boxes, the scores,
     the keypoints and the row counts that the sidecar declares are the same with and without it.
     Cite the upstream line that shows this.
  2. The spec does not require the output. The spec does not call it out of scope, and "Considered
     and deliberately not added" (`specs/sidecar/changelog.md`) does not list it. Such an output
     stays a `gap`.
  3. The upstream evaluation metric of the model does not read the output. Cite the line that reads
     the metric input.
  4. No known consumer needs the output. A consumer is a host or a model that reads the outputs of
     this model, for example a refiner that gates on a point of its parent. For each known consumer
     that could use the output, a committed measurement shows that a declared output serves that
     consumer at least as well. Cite the measurement.
  5. The sidecar declares nothing for the output: no output, no field and no channel.
  6. An exporter decision entry records the omission, its reason and its evidence.

  An `omitted` row needs no proposal. Keep the row in the table of its property. Tell the user about
  the row when you stop.
  ```

- **T3. "Verdicts", after "Near-misses seen so far" (`:164-179`).** Add:

  ```markdown
  **Omitted outputs seen so far.**

  - **The softmax visibility of the two RTMW 384x288 configs.** The configs set
    `decode_visibility=True` in the codec `SimCCLabel`. The head stores the visibility as
    `keypoints_visible` beside `keypoint_scores`. The COCO-WholeBody metric reads only
    `keypoint_scores`. On COCO-WholeBody the visibility ranks valid hands worse than the raw score at
    every size (OpenMMLab-Exporter 0041). The verdict is `omitted`.
  ```

- **T4. "Property table", "Rules for the rows" (`:193-194`).** Old: "The verdicts are `exact`,
  `near-miss`, `gap`, `unverified` and `out of scope`". New: "The verdicts are `exact`, `near-miss`,
  `gap`, `unverified`, `out of scope` and `omitted`".
- **T5. "The sidecar" (`:377-379`).** After "Fill in this section when no row is `near-miss` or
  `gap`." add: "The sidecar declares nothing for an `omitted` row."
- **T6. "Parity proof" (`:471-472`).** After "Run the ONNX model. Do the preprocessing and the decode
  exactly as the sidecar declares. Compare the result with the upstream library." add: "Do not
  compare an `omitted` output."
- **T7. "Final verdict", the rule (`:518`).** Old: "- `describes`: every row is `exact` or
  `out of scope`, **and** parity passes." New: "- `describes`: every row is `exact`, `out of scope`
  or `omitted`, **and** parity passes."
- **T8. "Final verdict", the table (`:528-534`).** After the row "`out of scope` rows to tell the
  user" add the row "| `omitted` rows to tell the user, with their exporter decision entries (or
  `none`) | |".
- **T9. The checklist.** The model intake template has no checklist (no `- [ ]` item in the file).
  No change. The change proposal template ("Before you stop") does not name the verdicts. No change.

**S. `.claude/skills/author-sidecar/SKILL.md`.**

- **S1. "Outputs" (`:62`).** Old: "Only when every row is `exact` or `out of scope`." New: "Only when
  every row is `exact`, `out of scope` or `omitted`."
- **S2. Step 3, item 7 (`:132-133`).** Old: "Give each row a verdict. Use the test in [Verdicts]."
  New: "Give each row a verdict. Use the test in [Verdicts]. Check the conditions of `omitted` before
  the test "Near-miss or gap"."
- **S3. Step 4, the table (`:152`).** Old: "| Every row is `exact` or `out of scope`. | Go to step 5.
  |" New: "| Every row is `exact`, `out of scope` or `omitted`. | Go to step 5. |"
- **S4. Step 4 (`:154`).** Old: "A row that is `out of scope` needs no proposal." New: "A row that is
  `out of scope` or `omitted` needs no proposal."
- **S5. Step 8, item 4 (`:232`).** Old: "- the `out of scope` rows;" New: "- the `out of scope` rows
  and the `omitted` rows, with their exporter decision entries;"
- **S6. "Stop points" (`:247`).** Old: "Parity fails while every row is `exact` or `out of scope`."
  New: "Parity fails while every row is `exact`, `out of scope` or `omitted`."

**Files that do not change, with the reason.**

- `.claude/skills/propose-sidecar-change/SKILL.md`: it names only `near-miss` and `gap` (`:3, 54, 111`).
  An `omitted` row needs no proposal.
- `.claude/skills/change-sidecar-spec/SKILL.md`: Procedure A reads only the final verdict
  `describes` (`:55-59`). Its step 6 already moves the new guidance of an intake to the "Authoring
  guidance" of its section.
- `specs/sidecar/templates/change-proposal.md`: it names no verdict list.
- The section files, the section map, the validation index and the changelog: they hold no verdict.
- `notes/decisions/open-work.md`: no item changes.
- `specs/exporter-guide/sidecars/README.md`, "The block for the exporter `AGENTS.md`" (`:75-95`), the
  sentence "If a model property does not map exactly to the spec, do not use an approximate mapping.
  Write a change proposal and stop." (`:89-90`): an `omitted` output is not mapped to the spec, so no
  approximate mapping exists, and the sentence does not apply to it. The block sends each session to
  the workflow of the guide, which holds the verdict `omitted` (G2, G10). Each exporter `AGENTS.md`
  copies the block, and it must stay shorter than 2,000 characters (skellytracker 0033, item 3,
  `0033-short-sidecars-block.md:13-17`). Thus no exporter `AGENTS.md` must sync.
- skellytracker `AGENTS.md` (`:210-211`), "Stop on a gap. If a model property does not map exactly to
  a spec section, do not approximate it.": the same reason. An `omitted` output is not mapped, so
  nothing is approximated. The rule applies to a `near-miss` or `gap` row, which stays a stop point.

**D. The skellytracker decision log.**

- **D1. A new entry, `notes/decisions/NNNN-<slug>.md`, status `accepted` after the user accepts.**
  skellytracker decision 0014 (accepted) states the verdict list and the final verdict rule (`0014-spec-lifecycle.md:81-92`
  step 3, `:94` step 4, `:110-117` step 5). The log does not allow a partial supersession
  (`notes/decisions/README.md:86-87`, "Rules"; skellytracker 0032, item 3). Thus the new entry restates each rule
  of skellytracker decision 0014 that stays, and it supersedes skellytracker decision 0014 in full. Its changes: step 3 adds the verdict `omitted`
  with the six conditions of G2; step 4 reads "If each row is `exact`, `out of scope` or `omitted`";
  step 5 reads "`describes`: each row is `exact`, `out of scope` or `omitted`, and parity passes";
  `:116` reads "If parity fails while each row is `exact`, `out of scope` or `omitted`". The
  skellytracker session sets the number with `uv run python tools/check_decision_log.py --next`.
- **D2. `notes/decisions/README.md`.** Add the index row of the new entry. Move the row of skellytracker decision 0014 to
  "Historical" with the status `superseded by NNNN`.
- **D3. Open question for the recording session (not decided here).** skellytracker decision 0014 has 18,953
  characters at `dom/21-move-sidecar-guide` (unchanged since `dom/20-sidecar-copy-block`). An entry after skellytracker decision 0025 has a limit of 6,000 characters (`notes/decisions/README.md`, "Rules", the size
  limits). A full restatement of skellytracker decision 0014 does not fit. The skellytracker session or the user chooses the
  form, for example the form of user decision T34 N1 (a) of this exporter for the NMS entry (one entry
  that supersedes in full, with its long text in a tracked file beside it). I do not know if the
  log allows rules in such a file. Its rule names only "long evidence".

### 2.2 Fields table

none. The change adds no sidecar field.

| Field | Type | Required | Description |
|---|---|---|---|
| none | none | none | No sidecar field. |

### 2.3 Behaviour

none (no algorithm). The verdict is a judgment of the intake author on cited evidence. The order of
the checks is in G3: the conditions of `omitted` come before the test "Near-miss or gap".

```text
none
```

### 2.4 Validation rules

none. The validation rules check sidecars, not intake verdicts. An `omitted` output is not in the
sidecar, so no rule sees it. No existing rule names a verdict. Condition 5 (the sidecar declares
nothing for the output) needs no new rule: a declared output must have a `semantic` of the closed set
(`common.outputs`), and this change adds none.

### 2.5 Selectors

none. No sidecar key selects this rule.

### 2.6 Legacy behaviour and version effect

none. No sidecar changes meaning, at any `schema_version`. The change does not touch `vNEXT`. No
"Legacy behaviour" table changes.

### 2.7 Changelog row

none. The changelog records the contract changes of the spec (`changelog.md`, "`schema_version`
history" and "Summary of changes"). This change is in the informative workflow text and the decision
log. It goes into a non-spec PR (documentation only; skellytracker `AGENTS.md:215-218`, skellytracker 0027).

## 3. Reference implementation

none (no algorithm). A verdict rule has no function to implement. The template asks for a reference
file only for a section with an algorithm (`model-intake.md`, "Reference implementations": "A part of
the spec without an algorithm needs no reference implementation").

| Item | Value |
|---|---|
| Reference file in the exporter repo (the part 3 code of `specs/sidecar/proposals/<slug>/proposal.md`) | none (no algorithm) |
| Target file in skellytracker (`specs/sidecar/reference/<section_module>.py`) | none (no algorithm) |
| Functions (one for each algorithm) | none (no algorithm) |

## 4. Vectors

none (no algorithm). A test vector gives the inputs of a section algorithm and its exact output. A
verdict rule has no inputs of that kind. No file `specs/sidecar/vectors/<section ID>.yaml` is added.

```yaml
none
```

## 5. Parity evidence

none (no run: this change adds no algorithm, no sidecar field and changes no declared output). Parity
compares the sidecar path with the upstream library on real images. The evidence of part 1 is the upstream
code (the omission changes no declared output) and the committed measurement of OpenMMLab-Exporter
0041 (the output is not useful). The RTMW parity of the intake ("Parity proof") compares the declared
outputs only. It runs when the RTMW intake has no `near-miss` or `gap` row left.

| Item | Value |
|---|---|
| Gates, set before the run, and their source | none (no run; the reason is above) |
| Test images (paths or dataset IDs), and the branch that each image runs | none |
| Upstream reference: library, version, config and command | none |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | none |
| Preprocessed input: maximum absolute difference for each image | none |
| Row count for each image: sidecar path and upstream | none |
| Final outputs in source-image coordinates: metric and value for each role | none. The declared outputs do not depend on the omitted output (`base_head.py:81-83, 91-93`; `simcc_label.py:191-198`). |
| Result (`pass`, `fail` or `to run`) | none (no run; the reason is above) |
| Script path in the exporter repo | none. The measurement of the evidence: `notes/decisions/scripts/rtmw_wrist_gate_measure.py` and `rtmw_wrist_gate_analyse.py` (OpenMMLab-Exporter decision 0041). |
| Exporter commit of the script | none. The OpenMMLab-Exporter 0041 scripts are in commit `9deff61`. |
| Command | none. The OpenMMLab-Exporter 0041 commands are in its section "Run". |

## 6. skellytracker implementation proposal

none; documentation only. The skellytracker code has no intake verdicts. The verdicts exist only in
the workflow text, the templates and the skills. The validator (`skellytracker/core/sidecar/model.py`)
sees only the sidecar, and an `omitted` output is not in it. The skellytracker RTMW detector already
gives the keypoint score as `Keypoints.visibility`
(`skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py:103-106`).
It reads no upstream visibility.

| Item | Value |
|---|---|
| Module and function | none; documentation only |
| Dispatch point | none |
| Validator changes (`model.py`, with rule IDs) | none |
| Tests | none. The doc tests of the decision log run on the new entry (`uv run pytest tools/tests -q`). |
| Existing code that the change touches | none |

## 7. Exporter impact

| Exporter | Affected sidecars | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | none. RTMW writes no sidecar now (OpenMMLab-Exporter decision 0050: `capabilities["sidecar"]` is False, `rtmw/adapter.py:41`). When it writes one, its pose block declares only `decode: {method: simcc}` (`rtmw/sidecar.py:164`), with no visibility. | none. After acceptance, RTMW intake row K8a changes from `out of scope (0041)` (T36) to `omitted (0041)` (both tags name OpenMMLab-Exporter decision 0041), and the intake lists it under "`omitted` rows to tell the user". | none. The host decoder does not compute the visibility. |
| Roboflow-Exporter | none known | none | none |
| Ultralytics-Exporter | none known | none | none |
| Qualcomm-Exporter | none known | none | none |
| MediaPipe-Exporter | none known. The refiner proposal reads `score` from an RTMW parent (`specs/sidecar/proposals/roi-refiner-role/proposal.md`). | none | none |
| The proposing exporter, if it is not in this table | not applicable (OpenMMLab-Exporter is in the table) | | |
| skellytracker package sidecars | none | none. Their legacy meaning does not change. | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| **(b) A wider `out of scope`.** Add to the bullet `out of scope` (`exporter-guide/sidecars/workflow/phase-1-intake.md:36-38`; `model-intake.md:113`): "An upstream output inside the contract that the sidecar deliberately does not declare is also `out of scope` when each condition of 'Omitted output' is true." | It needs fewer edits: no new verdict word, and G6, T7, S1, S3, S4 and S6 do not change. But it gives one verdict two tests: the position test, which needs no evidence, and the six conditions, which need a measurement. A reader cannot tell from the verdict which test a row passed. The intake must then hold such a row in the table "Steps outside the model contract" (section `none`), or the verdict `out of scope` is in a table of a section inside the contract. The user report "`out of scope` rows" asks if the spec must describe a step. For an omitted output, an exporter decision has already decided it. It also needs the same supersession of skellytracker decision 0014 as option (a) (part 2.1, D1). | T36 had to add the tag `(0041)` (OpenMMLab-Exporter 0041) to `out of scope` to give the reason. |
| **Keep `gap` and propose a field** (the A1 form of the keypoint-visibility proposal: a SimCC source of `pose.decode.visibility` on the two 384x288 sizes, with an exception to skellytracker 0010) | No consumer needs the field, and the measurement shows that the output is worse than the declared score. The A1 form also needed a size-level exception to the family invariant. | OpenMMLab-Exporter 0041, S7 (option E); `specs/sidecar/proposals/keypoint-visibility/proposal.md`, status note. |
| **Status quo: a user decision for each such row** (T36) | It works, but each new model with such an output needs a user question, and two agents give different verdicts until the user answers. The guide has no rule that tells the agent to ask. | T36; `model-intake.md:115`. |
| **`exact` with a note** | `exact` means that a section describes the property with these values (`exporter-guide/sidecars/workflow/phase-1-intake.md:24`). The spec does not describe the visibility. | `pose-decode-simcc.md:58` |
| **`unverified`** | The evidence is complete. `unverified` is for missing evidence (`exporter-guide/sidecars/workflow/phase-1-intake.md:34-35`). | part 1 |
| **A row in "Considered and deliberately not added" for the SimCC visibility** | The table lists spec features that a later bump can add. By the current rule, such a row makes the property a `gap` (`exporter-guide/sidecars/workflow/phase-1-intake.md:31-33`). Thus the row stays a `gap`. | `changelog.md:38-53` |
| **Declare the output with no host use** (the direction of skellytracker 0021 for extra outputs) | The graph has no tensor for the visibility. The host must compute it from `simcc_x` and `simcc_y` with `beta` and `sigma`. A declaration needs a new section with an algorithm that no consumer uses. | intake row K8a (graph read, secondary); skellytracker 0021 `:11-26` |
| **`omitted` with no measurement** (conditions 1, 2, 3, 5 and 6 only) | Without condition 4, an exporter can leave out an output that a consumer needs, for example a visibility that a refiner gate reads. The measurement makes the loss a known loss. | OpenMMLab-Exporter 0041, Qa and S7; refiner proposal `:306-307` (`score_gate.value_default` can be `visibility`) |
| **`omitted` for an output that "Considered and deliberately not added" lists** (drop the second sentence of condition 2) | It changes the rule that makes such a property a `gap` (`exporter-guide/sidecars/workflow/phase-1-intake.md:31-33`). Of the rows of that table, only `masks` (`changelog.md:53`) is an output beside the declared outputs. Condition 2 keeps such a model a `gap`, as today. The skellytracker session can relax condition 2 later if a row needs it. | `changelog.md:42-53` |
| **The hand-mean value `s_h` as an RTMW gate value** | Not an alternative of this proposal. User decision T38 records it as a measured option in part 8 of the refiner proposal. | OpenMMLab-Exporter 0041, "Observations" |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason. Parts 3, 4, 5 and 6 say `none`,
      each with the reason.
- [x] The intake links to this proposal: the table "Proposals and reference files" of
      the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts) (line 316, row K8a).
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or
      `none`. It names none. It names the accepted entry skellytracker decision 0014 that the change supersedes.
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing. The mmpose lines
      are lines of a local copy of v1.3.2 (copy B). The graph fact (no extra output) is secondary
      (old-id graph).
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the untracked plan folder of OpenMMLab-Exporter (plan facts). n/a (no algorithm).
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`. n/a (no vectors).
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the
      script. n/a (part 5 says `none`, with the reason: no run).
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter
      repo. n/a
- [x] No file in skellytracker changed.

## Before acceptance

This list is in ASD-STE100. The recording session wrote it on 2026-10-25. Line numbers of
skellytracker files are on the branch `dom/sidecar-implementation`.

**Parts**

- [x] Part 2, D1 to D3: the supersession of [0014](../../../../notes/decisions/0014-spec-lifecycle.md).
  The user decided on 2026-10-25 to absorb 0014 into the exporter guide. An absorbed entry is not
  superseded. Thus D1, D2 and D3 do not apply, and `supersedes-0014.md` is deleted. On acceptance,
  the change edits the guide, the model intake template and the skill `author-sidecar` (G1 to G10).
  The places that name 0014 keep it: its file stays, and each link resolves.

**Evidence**

- [ ] The mmpose v1.3.2 lines of part 1 come from a local copy that is not committed ("copy B"). Its
  origin cannot be checked again. The decision log needs GitHub permalinks that pin a full SHA on the
  default branch. Add permalinks to `open-mmlab/mmpose` at
  `5408bc76f5b848cf925a0d1857899011d8c5b497`. Make sure that this commit is on the default branch of
  `open-mmlab/mmpose`.
- [ ] The fact "the 384x288 graphs have no extra output" comes from the old-id graphs (secondary).
  Read the graphs of the new-id 384x288 exports.
- [ ] Condition 1 for row K8a rests on a code reading only. No run shows that the declared outputs
  (`keypoints` and `keypoint_scores`) are the same with `decode_visibility` on and off. The user must
  decide if a measurement is necessary.
- [ ] Part 5 names two scripts of OpenMMLab-Exporter 0041: `rtmw_wrist_gate_measure.py` and
  `rtmw_wrist_gate_analyse.py`. OpenMMLab-Exporter 0041 lists five scripts (`rtmw_wrist_gate_data.py`,
  `_measure`, `_blazepose`, `_handedness` and `_analyse`), and commit `9deff61` adds all five. Part 5
  must name each script that the evidence uses.
- [ ] The RTMW parity of the declared outputs is not run. It runs when the RTMW intake has no
  `near-miss` row and no `gap` row. The user must decide if acceptance waits for it.

**Template checklist**

- [ ] Header "Kind": the template allows only `new section` or `changed section`. The value is
  "Neither: changed workflow text".
- [ ] Header "Proposed section ID" is `none`. "Section file" lists files that are not section files
  (the guide, the template, a skill and the decision log). The template covers one section.
- [ ] Header "Intake rows with the verdict `near-miss` or `gap`": no such row exists now. Row K8a
  has `out of scope (0041)` by user decision T36. Phase 2 starts only from a `near-miss` row or a
  `gap` row (`phase-1-intake.md:46-48`).
- [ ] The note above the header says that the guide lets the user decide row K8a
  (`phase-1-intake.md:50-51`). That text lets the user decide if the spec must describe out-of-scope
  steps. It does not give `out of scope` to a step inside the runtime contract
  (`phase-1-intake.md:36-38`). Part 1 says that the visibility is inside the contract. Thus, by the
  current guide, row K8a is a `gap` row.
- [ ] Header "Exporter commit" says that the branch is "local, not pushed". The commits `f3aeb47`,
  `9deff61` and `32ab848` are on `origin/main` of OpenMMLab-Exporter. The exporter must correct the
  text.
- [ ] Checklist item "Part 2.1 lists each place that the change edits": see the third item of
  **Parts**.
- [ ] Checklist item "All eight parts are filled in": D3 is an open question. See the first item of
  **Parts**.

**Vectors and tooling**

- [ ] Part 4 has no vectors, and no `verified_against` line or `unverified:` line. The user must agree
  that a workflow rule needs no vectors.
- [ ] The change has only a non-spec PR. Procedure B of the skill `change-sidecar-spec` expects a
  content PR (normative text, a changelog row and vectors). The user must decide which procedure
  lands this proposal, and which PR sets entry 0044 to `accepted`.
- [ ] After acceptance, the restated rules of an accepted entry are in an informative file of the
  proposal folder. The user must decide if they stay there, or move to a tracked file next to the
  entry in `notes/decisions/`. Entry 0044 must stay inside 6,000 characters.

**Decisions for the user**

- [ ] Decide if a change of a workflow verdict goes through the spec change proposal process. The
  template covers one section.
- [ ] Choose option (a), the verdict `omitted`; option (b), a wider `out of scope`; or the status quo
  (a user decision for each such row, as T36).
- [ ] Confirm user decision T36 of OpenMMLab-Exporter. It is a fact of the untracked pose-models plan
  of OpenMMLab-Exporter (plan facts).
- [ ] The example `omitted (0041)` in G2 and T1 has a bare number of an OpenMMLab-Exporter entry.
  `AGENTS.md` section 5 reads a bare number as a skellytracker entry. Decide if the tag must be
  `omitted (OpenMMLab-Exporter 0041)`, or if the guide must say that the tag is the number of the
  exporter entry.
- [ ] Condition 6 needs an exporter decision entry. OpenMMLab-Exporter 0041 has the status
  `evidence`. Decide if an `evidence` entry meets condition 6.
- [ ] Conditions 4 and 6 need a committed measurement and an exporter decision entry. MediaPipe-Exporter
  has no git repo, so it cannot give a row the verdict `omitted`. Decide if this is the intention.
- [ ] Condition 4 says "No known consumer". Decide which consumers count, and who decides that a
  consumer is known.
- [ ] Untracked plans of MediaPipe-Exporter name `omitted` as the rule for the segmentation mask
  (pose39 intake, row D1c) and for the heatmap (row D1d), if the exporter drops them. Condition 2
  keeps the mask a `gap`, because "Considered and deliberately not added" lists masks. Condition 1
  fails for the heatmap, because it refines the declared `x` and `y`. Decide if those plans must
  change. Decide also if `omitted` can apply to the per-point presence of BlazePose and to the
  outputs of gap record [0021](../../../../notes/decisions/0021-landmark-extra-outputs.md).
- [ ] Decide if the Authoring guidance of `post.pose.decode.simcc` (`pose-decode-simcc.md:58`) names
  the verdict `omitted`. The proposals `keypoint-visibility` and `simcc-score-rule` also change that
  text.
- [ ] The change edits files outside `specs/`: the skill `author-sidecar` and the decision log.
  Confirm that the landing PR can change them. G1-G10 edit files in `specs/exporter-guide/`, not in
  `specs/sidecar/`. Confirm that "the spec folder" includes `specs/exporter-guide/`.

**Merge points**

- [ ] `keypoint-visibility` (0039): G8 gives the merged sentence of the hint "Pose" in
  `mapping-hints.md`. That sentence exists only after `keypoint-visibility` lands its sentence. The
  proposal sets no order: the PR that lands second must keep the edits of both. The recommended
  order lands `keypoint-visibility` first. It also adds row K8a to `model-intake.md`.
- [ ] `nms-clamp-order` (0040): "Outputs and decode" of `mapping-hints.md` (lines 55-65), which holds
  the hint "Pose" of G8.
- [ ] `roi-refiner-role` (0047): the same text in `phase-1-intake.md` (the bullet `out of scope`),
  `model-intake.md` (the table "Verdicts"), `rules.md` (lines 6-8, next to G10) and
  `mapping-hints.md` (line 71, where G9 adds text). Its `score_gate.value_default` can be
  `visibility`. This is the reason for condition 4.
- [ ] `roi-transform-and-source` (0020): `phase-1-intake.md:14-16` and `:30-32`, and the table
  "Verdicts" and the test "Near-miss or gap" in `model-intake.md`.
- [ ] `landmark-extra-outputs` (0021): row K8 of `model-intake.md` and `mapping-hints.md:55-61`. It
  declares outputs beside the landmarks. A model could also leave such outputs out as `omitted`.
- [ ] `normalize-arithmetic` (0043): step 4 of `parity.md`, next to G7.
- [ ] `model-id-suffix` (0025), `size-codes` (0046) and `affine-crop-arithmetic` (0037): other edits
  in `mapping-hints.md` and `model-intake.md`.
- [ ] `simcc-score-rule` (0024) and `keypoint-visibility` (0039): the `decode_visibility` text of
  `pose-decode-simcc.md:58`.

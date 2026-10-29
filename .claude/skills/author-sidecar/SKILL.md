---
name: author-sidecar
description: Use this skill in an exporter repo when you add a model. Use it to fill in the model intake and to write the sidecar. Use it also to prove parity with the upstream library and to prepare the reference implementations of the host-side sections.
---

# Author a sidecar

This skill uses ASD-STE100 Simplified Technical English.

This skill is phase 1 of the new-model workflow. Phase 1 answers one question: can the current sidecar
spec describe the model exactly?

This skill wraps the
[model addition workflow](../../../specs/model-sidecar/model-addition-workflow/README.md#model-addition-workflow), the "Sidecars" section
of the [exporter guide](../../../specs/draft/exporter-guide/sidecars/README.md#sidecars) and the
[model intake template](../../../specs/model-sidecar/templates/model-intake.md). The workflow, the
guide and the template give the rules and the details. This skill gives the order of the steps, the
inputs, the outputs and the stop points. If this skill and the workflow or the guide do not agree,
follow the workflow or the guide. The spec is normative.

## Where this skill runs

- Run this skill in an exporter repo, for example OpenMMLab-Exporter. A contributor that is not an
  exporter can follow the same steps in its own repo
  ([Paths and words](../../../specs/model-sidecar/model-addition-workflow/README.md#paths-and-words)).
- This skill file is in the skellytracker repo. Read it, read-only, in the skellytracker checkout
  `../freemocap/skellytracker`. From the root of an exporter repo, the path of this file is
  `../freemocap/skellytracker/.claude/skills/author-sidecar/SKILL.md`.
- Read the files of the checkout as normal files. Do not edit them. Do not commit to skellytracker.
  Do not change its branch.
- A relative link in this file starts at the folder of this file. In the checkout, the link
  `../../../specs/draft/exporter-guide/sidecars/README.md` opens the file
  `../freemocap/skellytracker/specs/draft/exporter-guide/sidecars/README.md`.
- If your agent does not support skills, read this file. Then do its steps in order.

## Files

| File | Link | Path from the root of an exporter repo |
|---|---|---|
| Exporter guide, section "Sidecars" | [README.md](../../../specs/draft/exporter-guide/sidecars/README.md#sidecars) | `../freemocap/skellytracker/specs/draft/exporter-guide/sidecars/README.md` |
| Model intake template | [model-intake.md](../../../specs/model-sidecar/templates/model-intake.md) | `../freemocap/skellytracker/specs/model-sidecar/templates/model-intake.md` |
| Section map | [README.md](../../../specs/model-sidecar/README.md#section-map) | `../freemocap/skellytracker/specs/model-sidecar/README.md` |
| The model addition workflow | [README.md](../../../specs/model-sidecar/model-addition-workflow/README.md#model-addition-workflow) | `../freemocap/skellytracker/specs/model-sidecar/model-addition-workflow/README.md` |
| The skill for phase 2 | [propose-sidecar-change](../propose-sidecar-change/SKILL.md) | `../freemocap/skellytracker/.claude/skills/propose-sidecar-change/SKILL.md` |

## Inputs

Get these inputs before you start
([Inputs](../../../specs/model-sidecar/model-addition-workflow/README.md#inputs)):

- the ONNX files of every size and precision, also at the verification batches 1, 2, 3 and 4 (not
  needed for a forced fallback form or a model that cannot export a static graph);
- the upstream inference config (the test pipeline);
- the upstream preprocessing code and postprocessing code;
- one reference output of the upstream library on a known image.

If an input is missing, do not stop. Write `missing` for it in the intake.

## Outputs

Write these files in a `model` bundle, or in the exporter repo where the table says so
([Hand-over bundles](../../../specs/model-sidecar/model-addition-workflow/hand-over.md)):

| Output | When |
|---|---|
| `intake.md` of the bundle `model-<model>@<contributor>` | Always. One bundle for each family. `<model>` is the `model_id` of the family. |
| The sidecar, from the sidecar writer code of the exporter | Only when no row is blocking and no row is `unverified`. |
| A draft of the sidecar, the rule walk and the parity plan, in the intake | When no row is blocking, and a row is `unverified`. The results are provisional. |
| `vector-runs.yaml` of the bundle | When a section that the model uses has numeric vector cases. |
| The parity script, committed in the exporter repo | When you can run the parity check. |
| `reference/<section_module>.py` of the bundle | For each section that the exporter implements on its host side and that has no reference implementation. |
| `example/` of the bundle | When the verdict is `describes`. |
| `batch/` of the bundle | When you run the batch-conversion check. It runs by default. You can skip it only for `batch_forced: 1`. A `dynamic` form still runs it for the dynamic check. |
| A `proposal` bundle | The skill `propose-sidecar-change` writes one bundle for each contract unit with a `near-miss` or a `gap`. |

Keep your working draft where you like. The bundle is the hand-over
([Pack a version](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#pack-a-version)).

## Procedure

### Step 1: Prepare

1. Before the overhaul of the exporter, run this workflow only when the user asks. Then write only the
   files of your bundles, unless the user permits more
   ([How to use this guide](../../../specs/draft/exporter-guide/sidecars/README.md#how-to-use-this-guide)).
2. Do the steps of
   [Where to read the spec](../../../specs/draft/exporter-guide/sidecars/where-to-read.md#where-to-read-the-spec). Get the
   commit of the checkout
   ([The commit of the spec text](../../../specs/model-sidecar/model-addition-workflow/reading-the-spec.md#the-commit-of-the-spec-text)).
3. If the checkout does not exist, or it is not on the branch `dom/sidecar-implementation`, stop.
   Ask the user what to do.
4. Read the [model addition workflow](../../../specs/model-sidecar/model-addition-workflow/README.md#model-addition-workflow) and
   [Read the spec](../../../specs/model-sidecar/model-addition-workflow/reading-the-spec.md#read-the-spec) before your first intake.
5. Read the [Rules](../../../specs/model-sidecar/model-addition-workflow/rules.md#rules) of the workflow.
6. If the exporter has no git repo, follow
   [A contributor with no git repo](../../../specs/model-sidecar/model-addition-workflow/README.md#a-contributor-with-no-git-repo).

### Step 2: Start the intake

1. Copy the model intake template to `intake.md` of your working draft of the `model` bundle.
2. Read the responses of your bundles and the
   [Re-export requests](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#re-export-requests). Do the open items first.
3. Follow [How to use this template](../../../specs/model-sidecar/templates/model-intake.md#how-to-use-this-template).
4. Fill in [Inputs before you start](../../../specs/model-sidecar/templates/model-intake.md#inputs-before-you-start).
5. Fill in the [Header](../../../specs/model-sidecar/templates/model-intake.md#header). Write the
   skellytracker commit from step 1.

### Step 3: Fill in the property table

1. Do step 1 of
   [Phase 1](../../../specs/model-sidecar/model-addition-workflow/phase-1-intake.md#phase-1-can-the-current-spec-describe-the-model).
   Then do step 1b of phase 1, the batch-conversion check
   ([Batch-conversion check](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#batch-conversion-check)).
   Fill in
   [Batch conversion check](../../../specs/model-sidecar/templates/model-intake.md#batch-conversion-check)
   with its evidence. Then do step 2 of phase 1. Write one row for each property of the runtime
   contract, and also row G6b.
2. Use the hint for each part of the
   [property table](../../../specs/model-sidecar/templates/model-intake.md#property-table). The hints are
   in [Mapping hints for phase 1](../../../specs/model-sidecar/model-addition-workflow/mapping-hints.md#mapping-hints-for-phase-1):

   | Part of the property table | Hints to use |
   |---|---|
   | [Graph](../../../specs/model-sidecar/templates/model-intake.md#graph) | "Graph" and "NMS inside the graph" |
   | [Family](../../../specs/model-sidecar/templates/model-intake.md#family) | "Identity" and "Family" |
   | [Preprocessing](../../../specs/model-sidecar/templates/model-intake.md#preprocessing) | "Preprocessing" |
   | [Outputs and decode](../../../specs/model-sidecar/templates/model-intake.md#outputs-and-decode) | "Outputs and decode" |
   | [Pose](../../../specs/model-sidecar/templates/model-intake.md#pose) | "Pose" |
   | [YAML](../../../specs/model-sidecar/templates/model-intake.md#yaml) | [Sidecar YAML](../../../specs/model-sidecar/model-addition-workflow/sidecar-files.md#sidecar-yaml) |
   | [Path in the storage layout](../../../specs/model-sidecar/templates/model-intake.md#path-in-the-storage-layout) | [Path](../../../specs/model-sidecar/model-addition-workflow/sidecar-files.md#path) |
   | [Steps outside the model contract](../../../specs/model-sidecar/templates/model-intake.md#steps-outside-the-model-contract) | Step 1 of phase 1 (the runtime contract) |

3. Read the "Authoring guidance" heading of each section that a row names. If the heading has text,
   use it.
4. Record the upstream evidence of each row. Follow the evidence rule in
   [Rules](../../../specs/model-sidecar/model-addition-workflow/rules.md#rules). Do not paste private data: no user
   paths, hostnames, email addresses or raw environment dumps
   ([Private data](../../../AGENTS.md#8-private-data)).
5. For a value that the exporter chooses (a name, a YAML rule or a path), follow "Values that the
   exporter chooses" in [Verdicts](../../../specs/model-sidecar/templates/model-intake.md#verdicts). Such a
   row is not `unverified` only because the exporter code does not exist or you cannot read it.
6. Do not copy a value from a reference example. Reference examples are not evidence.
7. Give each row a verdict. Use the test in
   [Verdicts](../../../specs/model-sidecar/templates/model-intake.md#verdicts).
8. Compare each row with "Near-misses seen so far" in the hints. A known near-miss must not get the
   verdict `exact`.
9. In each row that is not `exact`, write what differs or what is missing.
10. If you find a spec defect that no row of this model needs, do not propose it. Write it in the
    [Final verdict](../../../specs/model-sidecar/templates/model-intake.md#final-verdict) table. Tell the
    user in step 8.

### Step 4: Choose the next step

First, try to get the missing evidence of each `unverified` row. Then give the row its verdict.

Then use the first row of this table that applies. A blocking row is a `near-miss` or `gap` row other
than row G6b (step 3 of
[Phase 1](../../../specs/model-sidecar/model-addition-workflow/phase-1-intake.md#phase-1-can-the-current-spec-describe-the-model)).
A blocking row comes before an `unverified` row.

| The rows | The next step |
|---|---|
| A row is blocking. Other rows can be `unverified`. | The final verdict is `does not describe`. Do not write a sidecar that approximates the model. Write `skipped` in "The sidecar", "Validation checklist" and "Parity proof" of the intake. List the `unverified` rows in "Missing evidence and runs" of the final verdict. Go to step 6. |
| No row is blocking. A row is `unverified`. | The final verdict is `pending`. Go to step 5. Use the value that you expect for each `unverified` row. Mark each result that depends on an `unverified` row as provisional. |
| No row is blocking, and row G6b is `gap`. | Go to step 5. Write the sidecar without `batching.batch_conversion`, in a fallback form (b1 or `dynamic`). Then do step 6 for row G6b only: the proposal for a new profile. |
| Every row is `exact` or `out of scope`. | Go to step 5. |

A row that is `out of scope` needs no proposal. Tell the user about the row in step 8.

### Step 5: Write and check the sidecar

Do this step when no row is blocking (step 5 of
[Phase 1](../../../specs/model-sidecar/model-addition-workflow/phase-1-intake.md#phase-1-can-the-current-spec-describe-the-model)).

1. Let the sidecar writer code of the exporter write the sidecar. Do not write the sidecar by hand.
   Follow [Sidecar YAML](../../../specs/model-sidecar/model-addition-workflow/sidecar-files.md#sidecar-yaml).
2. If you cannot change the writer code yet, write the exact YAML as a draft in
   [The sidecar](../../../specs/model-sidecar/templates/model-intake.md#the-sidecar).
3. If a row is `unverified`, do not change the writer code for that row. Write the draft with the
   value that you expect. Name each `unverified` row in "The sidecar" of the intake.
4. Check the path of the sidecar against [Path](../../../specs/model-sidecar/model-addition-workflow/sidecar-files.md#path). The
   spec path is the sidecar value of row L1.
5. If the exporter writes the sidecar to a different folder, write the exporter path in row L1 as an
   exporter defect. An example is a model-specific folder such as `rtmo/body7/`. Report the defect to
   the user in step 8.
6. Compare your values with the reference example of the same family, if one exists. Write each
   difference in "The sidecar" of the intake.
7. Choose the published batch artifacts. Follow
   [Publishing](../../../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing).
   The sidecar uses one batch form: b3 with `batching.batch_conversion` (needs `converts`), b1 or
   `dynamic`. A fallback form needs the verdict `does not convert`, or the choice of the user with
   its reason in `batch_forced` and `batch_forced_reason`. A model that cannot export a static
   graph publishes `dynamic` without `batch_forced`. Write why in `no_static_reason`.
8. Do each item of the [Validation checklist](../../../specs/model-sidecar/templates/model-intake.md#validation-checklist).
   Follow [Validation](../../../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#validation). Write the rule ID of each
   rule that you checked.
9. Run the numeric vector cases of each section that the model uses through the host code. Record
   each section in `vector-runs.yaml` of the bundle
   ([Payload](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#payload)). An `error`
   case and a `failed` case are not host runs.
10. Prove parity. Follow [Parity](../../../specs/model-sidecar/model-addition-workflow/parity.md#parity). Fill in
   [Parity proof](../../../specs/model-sidecar/templates/model-intake.md#parity-proof). Fill in each cell
   that you can, also when the result is `to run`: the gates, the test images, the upstream reference
   and the script.
11. Commit the parity script in the exporter repo. If you cannot run the script or commit it, write
    `to run` as the result. If you do not know the path or the commit of the script, write
    `unknown (<reason>)`.
12. If parity fails, you missed or misjudged a property. Go back to step 3. Do not make the tolerance
    larger.

### Step 6: Hand over each `near-miss` and `gap`

Do this step when a row is blocking, also when other rows are `unverified`. Do it also for row G6b
when it is `gap`. A near-miss is a gap.

1. Group the `near-miss` rows and the `gap` rows by contract unit. A unit can change more than one
   section.
2. For each group, run the skill [`propose-sidecar-change`](../propose-sidecar-change/SKILL.md). Give
   it the intake file and the rows of the group.
3. Write each proposal file in
   [Proposals and reference files](../../../specs/model-sidecar/templates/model-intake.md#proposals-and-reference-files).

### Step 7: Prepare the reference implementations

Do this step for every final verdict, also after step 6. Follow
[Reference implementations](../../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#reference-implementations).

1. List each section that the exporter implements on its host side.
2. Skip a section that has a reference implementation:
   `../freemocap/skellytracker/specs/model-sidecar/reference/<section_module>.py`. Use it or match it
   in the host code.
3. If your host code and that reference implementation do not agree, do not write a second reference.
   Hand over the section to `propose-sidecar-change`.
4. Skip a section that one of your proposals changes. The part 3 file of the proposal is the reference
   implementation.
5. Skip a part of the spec that has no algorithm, for example `input.layout`.
6. For each other section, do "The step" of Reference implementations. Write
   `reference/<section_module>.py` of the `model` bundle.
7. If the host code is not committed, write `to run`. Do the step after the commit.
8. Fill in the reference table in
   [Proposals and reference files](../../../specs/model-sidecar/templates/model-intake.md#proposals-and-reference-files).

### Step 8: Write the final verdict and stop

1. Write the [Final verdict](../../../specs/model-sidecar/templates/model-intake.md#final-verdict):
   `describes`, `does not describe` or `pending`. A blocking row gives `does not describe`, also
   when other rows are `unverified`.
2. Pack the `model` bundle
   ([Pack a version](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#pack-a-version)). Then stop. Do not change
   another file in skellytracker.
3. Do not publish a `vNEXT` sidecar to a shared or remote folder
   ([Publishing](../../../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing)).
4. Tell the user these items:
   - the final verdict;
   - the files that you wrote;
   - the missing inputs;
   - the `unverified` rows, and the evidence that each row needs;
   - the `out of scope` rows;
   - the exporter defects;
   - the spec defects that you found and did not propose;
   - each result that is `to run`;
   - the bundle ID and the version that you packed;
   - each bundle that the user can delete
     ([Retention](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#retention)).
5. A skellytracker session does phase 3
   ([Phase 3](../../../specs/model-sidecar/model-addition-workflow/phase-3-skellytracker.md#phase-3-what-skellytracker-does-next)).

## Stop points

| Condition | Action |
|---|---|
| The checkout does not exist, or it is not on the branch `dom/sidecar-implementation`. | Stop. Ask the user what to do. |
| A row is blocking, also when other rows are `unverified`. | Do not write the sidecar. Run `propose-sidecar-change` (step 6). Then do steps 7 and 8, and stop. |
| No row is blocking, and you cannot get the evidence of an `unverified` row. | Do steps 5, 7 and 8 with provisional results. The final verdict is `pending`. |
| Parity fails while every row is `exact` or `out of scope`. | Go back to step 3. Do not make the tolerance larger. |
| You wrote the intake, the proposals and the reference files. | Stop. Report to the user. |

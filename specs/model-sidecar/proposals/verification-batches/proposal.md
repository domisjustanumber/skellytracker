# Change proposal: verification-batches

## Header

| Field | Value |
|---|---|
| Title | The verification batches of the batch-conversion parity check are 1, 2, 3 and 6 |
| Slug | `verification-batches` |
| Date | 2026-11-06 |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | 9810e483c69efddea7a8b93e671d6250eb47c5f0 (the commit that adds `decisions/scripts/batch_conversion_n_variant.py`) |
| Model, and its `model` bundle ID | No one model. The change applies to each family with a b3 sidecar. The measured families are `yolox-person` and `rtmw-wholebody133`. Their `model` bundles `model-yolox-person@openmmlab-exporter` and `model-rtmw-wholebody133@openmmlab-exporter` are not packed yet. |
| Intake rows with the verdict `near-miss` or `gap` | none. The change does not come from a model property. It comes from a user decision about the verification batches (part 1). |
| Kind (`new section`, `changed section`, `contribution` or `follow-up`) | `changed section` |
| Base bundle of a follow-up (`base`, or `none`) | none |
| Proposed section ID (the `id` in the section file's front matter) | `common.batch_conversion` |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | `specs/model-sidecar/common/batch-conversion.md` |
| Depends on (`depends_on`: bundle IDs that must land first, or `none`) | none |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | none. The Proposed table of `specs/model-sidecar/decisions/README.md` is empty. `intake_bundle.py list` gives `no bundles`. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `8351b7f8c20c8db74eb3e547478970e4dceb0308` |
| Target spec version: the newest version heading under "Revisions" in `specs/model-sidecar/changelog.md`, today the open target `2.0.0`. `pack` writes it to the manifest as `spec_version`. | `2.0.0` |

## 1. Gap

The Authoring guidance of `common.batch_conversion` sets the verification batches 1, 2, 3 and 4. The
parity check converts the b3 source to `N` = 1, 2 and 4. Batch 4 is not a batch that an end user
runs, and its files have no use after the check. The user wants the verification batches 1, 2, 3
and 6. These are more representative of the batch sizes of end users. Thus the same files are also
useful benchmark values later.

The change keeps the coverage of the check:

- Batch 1 is the b1 fallback form ("Batch forms" in `common.sizes_and_artifacts`) and the
  degenerate down-conversion. At batch 1, broadcasting can hide an error.
- Batch 2 is a down-conversion that is not degenerate and that is not a multiple of `S` = 3. A
  rule that works only for a multiple of `S` fails at batch 2.
- Batch 6 is an up-conversion and a multiple of `S`. It finds a batch-axis `Slice` or `Gather` end
  that stays at 3: the converted b6 output has 3 rows where the native output has 6. A
  down-conversion can hide such an end, because the runtime clamps it to the batch.
- `S` stays 3. The profile `static-batch-v1`, its steps, its check, Behaviour and the validation
  rules do not change.

| Item | Value |
|---|---|
| Property | The verification batches of the parity check of `static-batch-v1`, and the number of input B items |
| Upstream evidence (file and line, or config key; full upstream SHA, then the tag) | none: the property is a rule of the spec, not of an upstream model. The current text is the Authoring guidance of `common.batch_conversion` at skellytracker `8351b7f8c20c8db74eb3e547478970e4dceb0308`. |
| Plan decisions about the spec that this proposal uses, in words (or `none`) (heading "User decisions" in `specs/model-sidecar/model-addition-workflow/rules.md`) | User decision, 2026-11-06: change the verification batches from 1, 2, 3 and 4 to 1, 2, 3 and 6. Reason (the words of the user): b1, b2, b3 and b6 are more representative of end-user batch sizes, so the same files double as useful benchmark values later. Batch 4 goes. `S` stays 3. The user agreed the coverage argument of this part. |
| Nearest section ID (the `id` in the section file's front matter) | `common.batch_conversion` |
| Why the nearest section is wrong | The section is not wrong. It names batch 4, which has no use after the check. Batch 6 gives the same kind of check (an up-conversion) and a file that an end user can run. |
| Measured difference (number, image and script) | none: the two sets give the same verdict. `static-batch-v1` passes V3 and V5 at `N` = 1, 2, 4 and 6 for each size and precision of `yolox-person` (6 sizes) and `rtmw-wholebody133` (5 sizes), with max abs diff 0.0 on input A and input B. One run of `N` = 4 (`yolox-person` `l` fp16) failed once from run-to-run noise of onnxruntime CPU, and passed when repeated. Part 5 and `evidence.md` give the numbers. |
| Model in "Scope of this revision" (`specs/model-sidecar/changelog.md`): yes, or no (it joins the list on acceptance; do not write a scope entry) | `rtmw-wholebody133` (RTMW): yes. `yolox-person`: no. It joins the list with its own `model` bundle. This proposal does not need a model in the list, because it changes no feature that a model needs. |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none |

## 2. Spec change

### 2.1 Sections

One changed section: `common.batch_conversion`, "Batch conversion",
`specs/model-sidecar/common/batch-conversion.md`. Only the heading "Authoring guidance" changes.
The front matter, Fields, Profiles, Behaviour, Validation rules, Implementer guidance and Examples
do not change.

The new text of the first three items of "Authoring guidance". The other items do not change.

```markdown
- `S` is `batching.batch`, and a sidecar with `batching.batch_conversion` has the batch `3` (`V-common.batch_conversion-3`; [ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). Export each size at the verification batches 1, 2, 3 and 6. Each verification batch other than `S` checks one case. Batch 1 is the b1 fallback form and the smallest batch. Batch 2 is a smaller batch that is not a multiple of `S`. Batch 6 checks the conversion to a larger batch that is a multiple of `S`. It is never published.
- Write `batching.batch_conversion` only when the profile passes the parity check for each verification batch other than `S` (batches 1, 2 and 6), at each size and each precision of the source artifacts.
- The parity check: convert the source artifact to the batch `N` = 1, 2 and 6. Run the converted artifact and the native artifact of batch `N` on the same input A and on the first `N` items of input B. Input A is seeded random data (seed 42): uniform in [0, 1) for a float input, integers in [0, 256) for a uint8 input. Input B holds 6 different preprocessed images of each size, for example the reference image of phase 1 and five other images. Do not copy one image more than once. The outputs must agree within `rtol=atol=1e-3` for fp16 and `1e-5` for fp32.
```

The edits in the three items:

1. "verification batches 1, 2, 3 and 4" becomes "verification batches 1, 2, 3 and 6". "Batch 4
   checks the conversion to a larger batch. It is never published." becomes the three sentences
   about batches 1, 2 and 6 and "It is never published."
2. "(batches 1, 2 and 4)" becomes "(batches 1, 2 and 6)".
3. "`N` = 1, 2 and 4" becomes "`N` = 1, 2 and 6". "Input B holds 4 different preprocessed images
   of each size, for example the reference image of phase 1 and three other images." becomes
   "Input B holds 6 different preprocessed images of each size, for example the reference image of
   phase 1 and five other images."

**Places that the change edits.** In the spec (this proposal):

- `common.batch_conversion`, heading "Authoring guidance": the three items above.
- `specs/model-sidecar/changelog.md`, heading "Summary of changes": the row of 2.6.

No role, `semantic` value, resize method, storage layout, Overview, section map or validation index
changes. No `V-` rule names a verification batch.

**Follow-up edits for the skellytracker session.** These files restate the verification batches.
They are workflow files or tools. A bundle never holds a workflow change ("Workflow changes" in
`specs/model-sidecar/model-addition-workflow/hand-over.md`). This proposal does not change them. The
session makes these edits in one non-spec commit with a decision entry, in the same change as the
landing of this proposal, so that the spec and the tool agree:

| File | Heading or place | Edit |
|---|---|---|
| `specs/model-sidecar/model-addition-workflow/batch-conversion-check.md` | First paragraph | "to the batches 1, 2 and 4" becomes "to the batches 1, 2 and 6". |
| same | "Inputs", second item | "the verification batches 1, 2, 3 and 4" becomes "the verification batches 1, 2, 3 and 6". |
| same | "Inputs", input B item | "Its shape is `[4] + input.shape[1:]`" becomes "Its shape is `[6] + input.shape[1:]`". |
| same | "Steps", row V0 | "A (size, precision) pair without batch 1, 2, 3 or 4" becomes "without batch 1, 2, 3 or 6". |
| same | "Steps", row V3 | "`N` = 1, 2 and 4" becomes "`N` = 1, 2 and 6". |
| `specs/model-sidecar/model-addition-workflow/hand-over.md` | "Manifest", verify rule 4 | "`external` has the batches 1, 2, 3 and 4 of each pair" becomes "the batches 1, 2, 3 and 6 of each pair". |
| same | "The session run", row `to run` with `missing-verification-batch` | "export the verification batches 1, 2, 3 and 4" becomes "1, 2, 3 and 6". |
| `specs/model-sidecar/model-addition-workflow/validation-and-publishing.md` | "Publishing", b3 item | "the verification batches 1, 2, 3 and 4" becomes "1, 2, 3 and 6". |
| `specs/model-sidecar/model-addition-workflow/README.md` | "Inputs" | "the verification batches 1, 2, 3 and 4" becomes "1, 2, 3 and 6". |
| `specs/model-sidecar/templates/model-intake.md` | Inputs table, rows "The ONNX files" and "Input B" | "1, 2, 3 and 4" becomes "1, 2, 3 and 6". "with 4 different preprocessed images" becomes "with 6 different preprocessed images". |
| `.claude/skills/author-sidecar/SKILL.md` | "Inputs" | "the verification batches 1, 2, 3 and 4" becomes "1, 2, 3 and 6". |
| `tools/intake_bundle.py` | constants | `VERIFICATION_BATCHES = (1, 2, 3, 6)`, `TARGETS = (1, 2, 6)`, `INPUT_B_ITEMS = 6`. `DYNAMIC_BATCHES` and `SOURCE_BATCH` do not change. |
| same | `_publish_problems` message; `_input_items` docstring | "export the verification batches 1, 2, 3 and 4, or set batch_forced" becomes "1, 2, 3 and 6". "4 different items" becomes "6 different items" (or the text of `INPUT_B_ITEMS`). |
| `tools/tests/test_intake_bundle.py` | the family fixtures and the asserts | Each batch set `(1, 2, 3, 4)` becomes `(1, 2, 3, 6)`. The assert `[1, 2, 4]` of the targets becomes `[1, 2, 6]`. The `gone` cases `(4,)` and `(1, 2, 4)` become `(6,)` and `(1, 2, 6)`. The expected message becomes "1, 2, 3 and 6". The input B fixtures write 6 items. |

Do not change these restatements. They are records: skellytracker ADR-JC4T and ADR-JB5J (both
superseded) and the CRV0 item numbers in ADR-JAA4.

The change has no effect on V6 (the dynamic check at the batches 1, 2 and 3), on `S` or on the
tolerance.

### 2.2 Fields table

none. The change adds or changes no field.

### 2.3 Behaviour

none. Behaviour and the profile `static-batch-v1` do not change. A host converts to each batch `T`
of 1 or larger, as before. The verification batches apply only to the parity check of the
Authoring guidance.

```text
none
```

### 2.4 Validation rules

none. No new rule, no changed rule. `V-common.batch_conversion-1` to `-3` do not name a
verification batch. `V-common.batch_conversion-3` (`batching.batch` is `3`) does not change.

### 2.5 Selectors

none. The selector `batching.batch_conversion` does not change.

### 2.6 Changelog row

| # | Area | Change | Driven by | Section |
|---|------|--------|-----------|---------|
| (next) | Batching | The verification batches of the parity check of `static-batch-v1` are 1, 2, 3 and 6. Batch 6 replaces batch 4 as the conversion to a larger batch. Input B holds 6 different preprocessed images of each size. `S`, the profile and the tolerance do not change. | user decision 2026-11-06: b1, b2, b3 and b6 are more representative of end-user batch sizes, so the verification files are also benchmark values | [Batch conversion](../../common/batch-conversion.md#authoring-guidance) |

## 3. Reference implementation

none. The change has no algorithm. The profile steps and the check of `static-batch-v1` do not
change. `common.batch_conversion` has no reference module (`vectors: null` in its front matter),
and the change does not need one. The parity check runs in `tools/intake_bundle.py batch`.

| Item | Value |
|---|---|
| Reference file in the proposal bundle (`reference/<section_module>.py`) | none (no algorithm changes) |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | none |
| Functions (one for each algorithm) | none |

## 4. Vectors

none. The change has no algorithm and no new value that a case can test. Pixel-free cases of
`static-batch-v1` would test the profile steps, which do not change. The parity check of part 5
uses ONNX files, which a vector file must not hold.

## 5. Parity evidence

The script repeats V3 and V5 of `tools/intake_bundle.py batch` for a set of target batches. It uses
the `_Runner` of the tool (input A, input B, the run and the V5 comparison), its `TOLERANCE`, its
`SOURCE_BATCH` and its `PROFILE`, and `model_batch_convert` of the checkout. `evidence.md` gives
each number.

| Item | Value |
|---|---|
| Gates, set before the run, their source, and pass gate or control | Pass gates: V3 passes, and V5 passes on input A and on input B with `rtol=atol=1e-3` (fp16) and `1e-5` (fp32), for each size, precision and `N` = 1, 2 and 6. Source: "Authoring guidance" of `common.batch_conversion` and the table "Steps" of `batch-conversion-check.md`. Control: the runs of `N` = 1, 2 and 4 must give the same source and native SHA-256, the same V3 and V5 results and the same `max_abs` of each output as the hand-over `report.json` of `tools/intake_bundle.py batch` for the same files and the same 4 input B items. |
| Test images (paths or dataset IDs), and the branch that each image runs | Input B: the 6 COCO val2017 images with the lowest ids that have a non-crowd person box: 139, 785, 872, 885, 1000 and 1268. Items 1 to 4 are byte-equal to the hand-over input B (4 items). Items 5 and 6 come from the same host functions (`select_images` with `count=6` and `write_input_b` of `pipeline/handover.py`). `N` = 6 is the only run that uses items 5 and 6. Input A: seed 42, uniform in [0, 1). |
| Upstream reference: library, version, config and command | not applicable: the reference is the native bN export of the same family (the exports of OpenMMLab-Exporter, 2026-11-04). The check compares the converted b3 file with the native bN file. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | not applicable: the change does not change an export. The export errors of the families are in their model bundles. |
| Preprocessed input: maximum absolute difference for each image | 0 for items 1 to 4 against the hand-over input B (`np.array_equal`, each size of both families). |
| Row count for each image: sidecar path and upstream | not applicable: V5 compares each full output tensor, with the same shape. |
| Final outputs of each role (Parity, step 5): the compared output, metric and value | Each graph output: `yolox-person` `boxes` and `scores`; `rtmw-wholebody133` `simcc_x` and `simcc_y`. Metric: max abs diff and `np.allclose` with the tolerance above. Value: 0.0 in each of the 132 V5 runs (66 tuples, input A and input B) of `N` = 1, 2 and 6. In the 132 runs of `N` = 1, 2 and 4, 0.0 in 131 runs. The other run is `yolox-person` `l` fp16, `N` = 4, input A: `boxes` 0.75, `scores` 3.3e-07 (see the next rows). |
| Result (`pass`, `fail` or `to run`) | `pass` for `N` = 1, 2 and 6: 66 of 66 (size, precision, `N`) tuples pass V3 and V5. Control: the 44 tuples of `N` = 1 and 2 of this run are equal to the hand-over report. The run of `N` = 1, 2 and 4 gives 65 of 66 tuples equal to the hand-over report. The one difference is the `l` fp16 `N` = 4 tuple above: the hand-over report of the same two files gives 0.0, and repeats of that tuple pass. It is run-to-run noise of onnxruntime CPU on fp16 at the tolerance, not a property of `N` = 4. `evidence.md` ("Run-to-run noise") gives the repeat counts. |
| Script path in the exporter repo | `decisions/scripts/batch_conversion_n_variant.py` |
| Exporter commit of the script | 9810e483c69efddea7a8b93e671d6250eb47c5f0 |
| Command | `uv run python decisions/scripts/batch_conversion_n_variant.py inputs --out <evidence>/inputs --items 6 --handover <hand-over root>`, then `uv run --project ../freemocap/skellytracker --no-sync python -B decisions/scripts/batch_conversion_n_variant.py check --inputs <evidence>/inputs --targets 1,2,6 --out <evidence>/check-1-2-6.json --handover <hand-over root>` and the same with `--targets 1,2,4`; the repeat run with `--models yolox-person --only yolox-person:l:fp16,yolox-person:x:fp16 --targets 4,6 --repeats 20`. All from the exporter repo root. `evidence.md` ("Commands") gives each full command. |

## 6. skellytracker implementation proposal

The package code does not change. `model_batch_convert` takes each `target_batch` of 1 or larger.
The change is in the tool and the workflow only (the follow-up edits of 2.1).

| Item | Value |
|---|---|
| Module and function | none in the package. `tools/intake_bundle.py`: the constants `VERIFICATION_BATCHES`, `TARGETS` and `INPUT_B_ITEMS` (follow-up edits of 2.1). |
| Dispatch point | none |
| Validator changes (`model.py`, with rule IDs) | none |
| Tests (the vectors of part 4, and a golden parity test, for example in `skellytracker/tests/sidecar/`) | none in the package. `tools/tests/test_intake_bundle.py`: the batch sets, the targets and the input B fixtures (follow-up edits of 2.1). |
| Existing code that the change touches | `tools/intake_bundle.py` (`VERIFICATION_BATCHES`, `TARGETS`, `INPUT_B_ITEMS`, `_publish_problems`, `_input_items`). Not `skellytracker/core/sessions/batch_conversion.py`. |

## 7. Exporter impact

| Owner repo | Inventory key or model | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `yolox-person` (model bundle not packed) | none in the sidecar. The verification exports are b1, b2, b3 and b6 (the b6 files exist). The fields file lists b6 in place of b4. Input B holds 6 images. | none. The hand-over tool changes: `VERIFICATION_BATCHES` and `INPUT_B_ITEMS` of `pipeline/handover.py`, its tests, and OpenMMLab-Exporter ADR-3Y2Y. |
| OpenMMLab-Exporter | `rtmw-wholebody133` (model bundle not packed) | none in the sidecar. The same verification and input B changes as `yolox-person`. | none |
| each exporter | each future `model` bundle with a b3 publish | Export b6 in place of b4. Write 6 input B items. | none |

The sidecars do not change. A sidecar holds no verification batch. Only the b3 file is published.

**Reference examples that the change makes invalid.**

| Example (`inventory.yaml` key) | Rule ID | Impact (`forced-edit` or `needs-export`) | Edit text |
|---|---|---|---|
| none | none | none | No example has `batching.batch_conversion` (each example has `batching.batch: 1`; `specs/model-sidecar/examples/README.md`), and the change adds or changes no `V-` rule. |

**Candidate example.**

| Item | Value |
|---|---|
| Candidate example in the proposal bundle (`example/detectors/...`, or `none`) | none: the change adds no field. |
| Writer code (file, function and commit) | none |
| `sidecar_refs.py --check` result | not applicable |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| Keep 1, 2, 3 and 4 (the near-miss: the current text) | Batch 4 is not a representative end-user batch, and its files have no use after the check. Batch 6 is an up-conversion as batch 4 is, and batch 2 already covers a batch that is not a multiple of `S`. Both sets give the same verdict on the two families. | `evidence.md`: `N` = 4 and `N` = 6 pass with max abs diff 0.0 at each size and precision (one noise failure of `N` = 4, which passes when repeated). |
| 1, 2, 3, 4 and 6 | One more export and two more files for each size and precision, with no case that batch 2 and batch 6 do not cover. The user dropped batch 4. | User decision 2026-11-06 (part 1). |
| 1, 3 and 6 (drop batch 2) | No batch that is not a multiple of `S`. A rule that works only for a multiple of `S` then passes. | Coverage argument of part 1. |
| Change `S` from 3 | `V-common.batch_conversion-3` and the published b3 form depend on `S` = 3 (skellytracker ADR-JAA4). The user keeps `S` = 3. | User decision 2026-11-06. |
| Put the new batches in the tool only | The verification batches are in the Authoring guidance of the spec, and the workflow restates them. A tool change without the spec text makes the spec and the tool disagree. A bundle cannot change the tool. | "Workflow changes" in `hand-over.md`. |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake names the bundle ID of this proposal. n/a: the change has no model intake row. The
      `model` bundles of `yolox-person` and `rtmw-wholebody133` are not packed yet.
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or
      `none`. This proposal builds on such an entry. It does not compete with it.
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing. (The property is a
      spec rule. Part 1 cites the current text and the user decision.)
- [x] Part 1 gives each plan decision about the spec in words, with no item number, or `none`.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the proposal bundle. n/a: no algorithm.
- [x] Part 4 names the vector file, and the file exists in the proposal bundle. `fill` wrote its `expect`. n/a: no algorithm.
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`. n/a: no vector file.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a
- [x] Part 5 gives the numbers, the script path and the commit
      (9810e483c69efddea7a8b93e671d6250eb47c5f0).
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter
      repo: `decisions/scripts/batch_conversion_n_variant.py` at
      9810e483c69efddea7a8b93e671d6250eb47c5f0.
- [x] Part 7 lists each example that the change makes invalid, or says `none` with the reason.
- [x] Each citation of a spec text, a base file or a record names a heading or a case `id`, not a
      line number of a copy.
- [x] No file in skellytracker changed, except the version folder that `pack` wrote in `intakes/`.

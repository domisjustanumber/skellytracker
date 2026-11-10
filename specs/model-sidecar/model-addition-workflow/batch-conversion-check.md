# Batch-conversion check

The `batch` sub-command checks if the profile `static-batch-v1` converts the batch 3 export of a
family to the batches 1, 2 and 6 ([`common.batch_conversion`](../common/batch-conversion.md);
[ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). Do it
in step 1b of [phase 1](phase-1-intake.md). It gives the evidence of row G6b of the intake and the
value of `batch_conversion` in the manifest ([Manifest](hand-over.md#manifest)). The converter is
`skellytracker/core/sessions/batch_conversion.py::model_batch_convert`.

## Run the tool

Run `batch` from your repo root, in the skellytracker environment of the checkout:

```sh
uv run --project ../freemocap/skellytracker --no-sync python -B ../freemocap/skellytracker/tools/intake_bundle.py batch --fields <fields file> --out <payload folder>/batch
```

- The user syncs the checkout one time: `uv sync --extra all-cpu` in `../freemocap/skellytracker`.
  If the import of skellytracker fails, stop. Ask the user to sync the checkout.
- The command writes no file in the checkout. `--no-sync` stops uv from writing `uv.lock` and
  `.venv`. `-B` stops the `__pycache__` files.
- A relative path in the arguments starts at the current folder. An `external` path starts at the
  skellytracker root, as in the manifest.
- `batch` refuses to run in an environment that is not the `.venv` of the checkout. The reason: uv
  runs a command with a wrong `--project` path in another environment, with only a warning.
- Do not set `UV_PROJECT_ENVIRONMENT`. Do not add `--active`.
- Do not add skellytracker as a dependency of your repo yet. Your own code cannot import
  skellytracker yet.

## Inputs

- `--fields` is your fields file. `batch` reads its `external` list: each ONNX file of the family,
  with its `size`, `batch`, `precision` and `published`. The tolerance comes from `precision`.
- A family needs each size and each precision at the verification batches 1, 2, 3 and 6. This is
  also true for a family that plans b3 only. [Publishing](validation-and-publishing.md#publishing) gives the two
  exemptions: `batch_forced` and `no_static_reason` ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md);
  [ADR-ESP4](../../../decisions/entries/ESP4-one-home-for-each-workflow-rule.md)). `published` follows [Publishing](validation-and-publishing.md#publishing). Add the
  `dynamic` export if you plan to publish it.
- The verification batches, input A, input B and the tolerance are in
  [Authoring guidance](../common/batch-conversion.md#authoring-guidance) of `common.batch_conversion`
  ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)).
- `batch` reads input B from `<out>/inputs/<size>.npy`, one file for each size (`--inputs` gives
  another folder). Your writer code writes it. Its shape is `[6] + input.shape[1:]`. Its dtype is the
  dtype of the graph input (float32 or uint8). For an fp16 graph with a float16 input, `batch` casts
  float32 items to float16. A dim of the graph input that is not a number takes its value from
  input B.

## Steps

| Step | What `batch` does |
|---|---|
| V0 | Applicability, for the whole family. A family with only dynamic files: `not applicable` when the fields give `no_static_reason`, else the pair rule below. A family with no file: `to run` with the reason `missing-verification-batch`. A (size, precision) pair without batch 1, 2, 3 or 6: `not applicable` when the fields give `batch_forced`, else `to run` with the reason `missing-verification-batch`. A family with only b3 files also gets `to run` ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). |
| V0b | It checks that the onnx and onnxruntime of the environment can load each file: `ir_version`, each `opset_import` version and an onnxruntime CPU session. If not: `to run` with the reason `host-runtime-cannot-load`. |
| V1 | It compares the native batch 3 graph with each native batch `N` graph (`differences.json`). This is evidence only. |
| V2 | It makes the fragment `batching.batch_conversion: {profile_id: static-batch-v1}`. |
| V3 | It converts batch 3 to `N` = 1, 2 and 6 with `model_batch_convert`. It records the summary or the `ValueError` text. |
| V4 | It compares each converted graph with the native graph of the same batch. This is evidence only. |
| V5 | Numeric parity on onnxruntime CPU, with input A and the first `N` items of input B: the same output names, dtypes and shapes, with the tolerance of the [Authoring guidance](../common/batch-conversion.md#authoring-guidance). A run in which each output is empty does not count. A converted file that does not run fails V5. A native file that does not run gives `to run` with the reason `host-runtime-cannot-load`. |
| V6 | The dynamic check, for each `dynamic` file. (a) It compares the `dynamic` file with each static file of the same size and precision at the batches 1, 2 and 3 that exists. A missing static file of these batches does not block V6. (b) It runs the `dynamic` file at batch 1 on three items, then at the batches 2 and 3 on the same items. Row `i` must equal the batch 1 output of item `i`. An output with no leading batch dim gets `no check`. If V6 compares no output that is not empty, the result is `to run` with the reason `no-signal`. If `batch` cannot feed the file, the result is `to run` and the reason gives the error. |

The result of V6 does not change the verdict. If V6 does not pass, do not publish the `dynamic`
export. Publish another form that [Publishing](validation-and-publishing.md#publishing) allows, or
fix the export.

## Verdicts

| Verdict | When | Row G6b | Next |
|---|---|---|---|
| `converts` | V3 and V5 pass for each size, precision and `N` | `exact` | Apply [Publishing](validation-and-publishing.md#publishing) ([ADR-ESP4](../../../decisions/entries/ESP4-one-home-for-each-workflow-rule.md)). With b3, the writer code writes the fragment of `conversion.yaml`. |
| `does not convert` | V3 or V5 fails on a complete set of inputs | `gap` | Leave `batching.batch_conversion` out. Apply [Publishing](validation-and-publishing.md#publishing). Write a `proposal` bundle for a new profile. `differences.json` and `residual-diff.json` are its part 5 evidence. |
| `not applicable` | V0 gives `not applicable`, or you skip the check. Both need `batch_forced` or `no_static_reason`. | `out of scope` | Apply [Publishing](validation-and-publishing.md#publishing). |
| `to run` | A reason: `missing-verification-batch`, `host-runtime-cannot-load` or `no-signal` (each run of a pair is empty) | `unverified` | Write the reason in `batch_conversion_reason`. The skellytracker session runs the check again ([The session run](hand-over.md#the-session-run)). Apply [Publishing](validation-and-publishing.md#publishing). |

## Output

`batch` writes these files to `--out`. Put the folder in the bundle as `batch/`
([Payload](hand-over.md#payload)):

- `report.json`: the versions of Python, NumPy, onnx and onnxruntime, the skellytracker commit,
  `profile_id`, `S`, the results of V0 to V6 for each file and each `N`, and the verdict;
- `differences.json`: the V1 report of each pair;
- `conversion.yaml`: the fragment, only for `converts`;
- `residual-diff.json`: only for `does not convert`.

`batch` first removes these four files from an earlier run. The bundle folder `batch/` also holds
`inputs/<size>.npy`: input B. `batch` does not write it. Your writer code writes it before the run.
If you gave `--inputs`, copy that folder to `batch/inputs/`.

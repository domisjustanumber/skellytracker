# JC4T — Parity gates and the batch-conversion check

**Status:** accepted, 2026-10-28 (user; PR: pending).

## Decision

1. **Gates.** A pass gate comes from an own accuracy gate or from a numeric floor of the upstream.
   A gate measured on the sidecar path is a control. It is a pass gate only when nobody can
   calculate a floor (give the reason) and a negative control in the same run fails it. The
   contributor sets the gates before the run and records a replaced gate. A scope change needs a
   new run.
2. **Roles.** Parity step 5 compares each final output of each role, in the unit of the quantity,
   against the change that the export error causes. When the upstream gives no value for an output,
   step 5 compares the first later output. The sentence "A model with both roles ..." stays word for
   word.
3. **Batch-conversion check.** A static-batch family exports each size and precision at the
   verification batches 1, 2, 3 and 4. `S = 3`. The `batch` sub-command of
   `tools/intake_bundle.py` converts b3 to `N` = 1, 2 and 4 with
   `skellytracker/core/sessions/batch_conversion.py::model_batch_convert`, the only converter. It
   runs V0 (applicability), V0b (the environment can load each file), V1 and V4 (graph diffs,
   evidence only), V2 (the fragment), V3 (convert), V5 (numeric parity on input A and on input B, 4
   different preprocessed images) and V6 (the dynamic check at batches 1, 2 and 3). The family
   `converts` only when V3 and V5 pass for each tuple. A reason of `to run` (`missing-verification-batch`,
   `host-runtime-cannot-load`, `no-signal`) comes first. V6 gates only the publication of a
   `dynamic` file. b4 checks the upward conversion and is never published.
4. **Publish rule.** With `converts`, the exporter publishes one batch artifact for each size and
   precision. The whole family is the b3 export with `source_batch_size: 3`, or the `dynamic`
   export with no `batch_conversion`. b1, b2 and b4 are verification-only. `verify` checks the
   rule. No `V-` rule checks it.
5. **Hosts.** A b3 publish depends on host conversion (Behaviour 3 of `common.batch_conversion`)
   for batches 1 and 2. The spec-build stage does not implement it.
6. **The exporter run.** Until the dependency pins of skellytracker change, an exporter runs `batch`
   from the local checkout, in its `.venv`, with
   `uv run --project ../freemocap/skellytracker --no-sync python -B`. `batch` refuses another
   environment. The target rule after the pin change: the exporter takes skellytracker as a
   dependency from a uv path source. The pin change is an item of the
   [open work](open-work.md#repository-state).
7. **onnx in part 3.** A proposal of a new batch-conversion profile gives part 3 as a standalone
   module with onnx and NumPy and the signature of `model_batch_convert`.
8. **Profile text.** In `common/batch-conversion.md` (a draft section, class `vnext`): "No
   initializer" becomes "No tensor"; the text names the tensors that the steps do not touch; Limits
   notes the `[S, ...]` constants.
9. **Where the rules are.** Items 1 and 2:
   [Parity](../specs/model-sidecar/model-addition-workflow/parity.md) and part 5 of the
   templates. Items 3 and 6:
   [Batch-conversion check](../specs/model-sidecar/model-addition-workflow/hand-over.md#batch-conversion-check)
   and step 1b of
   [phase 1](../specs/model-sidecar/model-addition-workflow/phase-1-intake.md). Item 4:
   [Publishing](../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing).
   Item 6 also: the draft exporter guide. Item 7:
   [Imports of other sections](../specs/model-sidecar/model-addition-workflow/reference-implementations.md#imports-of-other-sections).
   The tolerance and the method: the Authoring guidance of
   [`common.batch_conversion`](../specs/model-sidecar/common/batch-conversion.md#authoring-guidance).

## Reason

- Four proposals set gates from a scratch run of the path that they test. Such a gate shows only
  that the code gives the same numbers again. Nobody can calculate a floor for a chain output.
- Step 5 had one closed list of two roles and compared in pixels against an error in output units.
- No step checked that a conversion profile gives the native outputs. The old check used `S = 2`
  and skipped a pair with a missing precision.
- `V-common.batch_conversion-4` needs the key `"<S>"` for each size, and b3 is the only published
  static artifact. So `S` is 3.
- A batch 3 constant can also be a channel count. V5 finds such a change.
- The exporters cannot resolve the pins of skellytracker (Python, NumPy, OpenCV), so the run uses
  the checkout environment. A wrong `--project` path only gives a uv warning, so `batch` checks
  `sys.prefix`.
- An onnx version above the session lock must not give `does not convert`. V0b gives `to run`.

## Consequences

- A family that publishes only b3 runs at batch 1 or 2 only on a host that implements Behaviour 3.
  Today no host does. Publish `dynamic` when V6 passes and a host needs batch 1 or 2 now.
- A host can still make b5 or more with no evidence: the spec has no largest batch.
- The exporter and the session use the onnx and onnxruntime of `uv.lock`.

## Alternatives rejected

- **Floor gates only.** A floor of a chain output is not practical.
- **`S = 2` with a retry at 3.** The published static artifact is b3.
- **A `V-` rule for the publish rule.** The rule is about publication, not about one sidecar.
- **The exporter takes the dependency now.** uv cannot resolve it in three of four exporters.

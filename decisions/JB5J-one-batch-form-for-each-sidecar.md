# JB5J — One batch form for each sidecar

**Status:** accepted, 2026-10-29 (user; PR: pending).

## Decision

This entry supersedes [ADR-JC4T](JC4T-parity-gates-and-batch-conversion-check.md) in full. Items 1
to 4 are new. Item 3 changes the V0 rule of JC4T item 3. Item 4 changes JC4T item 4 (the publish
rule). Item 5 restates the other rules of JC4T by links
([ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md)).

1. **Batch forms.** Change class `vnext`. A `vNEXT` sidecar uses exactly one batch form for every
   size and every precision: b3 (the goal), with only the key `"3"` and
   `batching.batch_conversion: {profile_id: static-batch-v1, source_batch_size: 3}`; b1, with only
   the key `"1"`; or `dynamic`, with only the key `dynamic`. Any other key set is invalid: `"2"`,
   `"4"`, two keys in one size, `"1"` with `"3"`, or a different form in two sizes.
   `V-common.sizes_and_artifacts-13` checks the key set. `V-common.batch_conversion-3` fixes
   `source_batch_size` at `3`. `V-common.batch_conversion-4` allows only the key `"3"` with
   `batch_conversion`. A sidecar before `vNEXT` keeps the old key rules.
2. **The check by default.** The batch-conversion check (export b1, b2, b3 and b4; convert b3) runs
   by default. b3 needs the verdict `converts`. b1 and `dynamic` are fallbacks. A fallback is allowed
   with the verdict `does not convert`, or when the person who runs the exporter forces it. The
   manifest records that choice in `batch_forced` (`1` or `dynamic`) and its reason in
   `batch_forced_reason`. With `batch_forced`, the check can be skipped. A family with only
   `dynamic` files and no `batch_forced` records in `no_static_reason` why the model cannot export a
   static graph. `dynamic` still needs a passed dynamic check (V6).
3. **V0.** V0 gives `not applicable` for a family with only `dynamic` files and
   `no_static_reason`, or when `batch_forced` is set and a verification batch is missing. Otherwise
   a missing verification batch gives `to run` with the reason `missing-verification-batch`. This
   is also true for a family with only b3 files. The manifest verdict `not applicable` needs
   `batch_forced` or `no_static_reason`.
4. **The publish rule, for every verdict.** Each (size, precision) pair has one published file.
   All published files have the same batch: `3`, `1` or `dynamic`. With `batch_forced`, the batch
   equals it. Without it, `converts` needs `3`, `does not convert` needs `1` or `dynamic`, and
   `not applicable` needs `dynamic`. A b3 publish needs the verification batches 1 to 4 of each
   pair in `external`. The example sidecar lists exactly the published files. It has
   `source_batch_size: 3` if and only if the batch is `3`.
   A `to run` bundle marks the files of the form that it plans. `verify` checks that form. The
   session verdict then decides. The other verification files are never published. `verify`
   checks this rule.
5. **The rules that stay.** JC4T items 1 and 2:
   [Parity](../specs/model-sidecar/model-addition-workflow/parity.md) and part 5 of the templates.
   Item 3, except V0:
   [Batch-conversion check](../specs/model-sidecar/model-addition-workflow/hand-over.md#batch-conversion-check)
   and step 1b of [phase 1](../specs/model-sidecar/model-addition-workflow/phase-1-intake.md).
   Item 6: [Run the tool](../specs/model-sidecar/model-addition-workflow/hand-over.md#run-the-tool)
   and the draft exporter guide
   ([Run the skellytracker tools](../specs/draft/exporter-guide/sidecars/README.md#run-the-skellytracker-tools)).
   Item 7:
   [Imports of other sections](../specs/model-sidecar/model-addition-workflow/reference-implementations.md#imports-of-other-sections).
   Item 8: [`static-batch-v1`](../specs/model-sidecar/common/batch-conversion.md#static-batch-v1).
   The tolerance and the method: the
   [Authoring guidance](../specs/model-sidecar/common/batch-conversion.md#authoring-guidance) of
   `common.batch_conversion`. Items 1 and 4 of this entry:
   [Batch forms](../specs/model-sidecar/common/sizes-and-artifacts.md#batch-forms) and
   [Publishing](../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing).
   JC4T item 5 stays in full: a b3 sidecar depends on host conversion (Behaviour 3 of
   `common.batch_conversion`) for the batches 1 and 2. The spec-build stage does not implement it.

## Reason

- The user decided on 2026-10-29: "Allowed batch sizes are dynamic, b3 with conversion section, b1
  only. Anything else is rejected, as it will be impractical to run in production." Also: "The goal
  is b3+conversion. If a model cannot convert, or the user wants to force a fixed or dynamic batch
  size, they are supported as fallbacks." The form must be the same for the whole family.
- Under JC4T, the publish rule applied only to `converts`. With another verdict, the exporter
  published its native batches, for example b1, b2 and b3 in one size.
- Under JC4T, V0 skipped a b3-only family. Its b3 publish then had no conversion evidence (audit
  finding C15).
- The user added on 2026-10-29: a dynamic-only family needs no `batch_forced` if it states why the
  model cannot export a static graph. The tool cannot see a left-out static export.

## Consequences

- The examples `yolo26`, `yolo26-body` and `rtmdet-person` lose their batch 2 and 3 groups
  (spec-forced edits). Ultralytics-Exporter and OpenMMLab-Exporter must write one form.
- The package detectors use the batch key `"1"`. A b3-only `vNEXT` sidecar needs host conversion
  ([open work](open-work.md)).
- The exporter and the session use the onnx and onnxruntime of `uv.lock`.

## Alternatives rejected

- **Any set of static batches (JC4T).** It is not practical to run in production.
- **b1 and b3 in one sidecar.** That is two forms in one family.
- **A new verdict `skipped`.** `not applicable` with `batch_forced` gives the same information.
- **A `V-` rule for the publish rule.** The rule is about publication, not about one sidecar.

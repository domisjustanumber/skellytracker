# JAA4 — One batch field for each sidecar

**Status:** accepted, 2026-11-02 (user; PR: pending).

## Decision

This entry supersedes
[ADR-CRV0](../../specs/model-sidecar/decisions/entries/CRV0-output-shapes-in-each-batch-group.md),
[ADR-JB5J](JB5J-one-batch-form-for-each-sidecar.md) and
[ADR-0011](../../specs/model-sidecar/decisions/entries/0011-rtmdet-host-nms.md) in full. Items 1
to 3 are new. Item 1 replaces JB5J item 1. Item 2 states CRV0 items 1, 2 and 4 in the new form.
Item 4 restates the other rules ([ADR-Z05A](Z05A-essential-decision-log-rules.md)).

1. **One batch field.** Each sidecar must have one `batching.batch`: `3`, `1` or `dynamic`. It
   applies to each size and each precision. `batching.batch_conversion: {profile_id}` is present if
   and only if `batch` is `3`. `source_batch_size`, `batching.batch_axis`, the derived
   `native_batch_sizes` and `sizes.<size>.onnx.batch_artifacts` go. Dim 0 is the batch axis. Each
   size has `onnx.precision_artifacts.<fp32|fp16>` and `onnx.output_shapes`. The `S` of
   `static-batch-v1` is `batching.batch`. The source of a conversion is the
   `precision_artifacts` entry of its size and precision. A file name is
   `{model_id}-{size}_b{N}_{precision}.onnx`. A `dynamic` file name has no batch segment.
2. **`output_shapes` in each size.** `onnx.output_shapes` has one entry for each output of
   `outputs`, in the same order. Entry `i` has `len(outputs[i].shape)` dims. Each dim that is not
   `-1` in `outputs[i].shape` has the same value or `-1` in entry `i`. An axis that the graph
   leaves symbolic stays `-1`. Dim 0 of each entry equals `batching.batch`, or is `-1` for
   `dynamic`. A generated artifact of `common.batch_conversion` takes the `output_shapes` of its
   size, with dim 0 changed by step 2 of the profile.
3. **Example values.** The spec-forced edits of `rtmo-body7` and `rtmw-wholebody` add their
   `output_shapes` from the graphs of the OpenMMLab-Exporter export files, under
   [ADR-NB5F](NB5F-no-change-classes-and-one-re-export-request.md) item 3 (a graph read only;
   [ADR-AD33](AD33-bundles-are-untrusted-input.md)).
4. **The rules that stay.**
   - CRV0 item 3 goes with [ADR-0QKK](0QKK-no-legacy-layer.md) item 1. Item 3 of this entry
     replaces CRV0 item 5. CRV0 item 6 goes.
   - JB5J items 2 to 4, and the JC4T item 3 rules of JB5J item 5:
     [Publishing](../../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing),
     [Manifest](../../specs/model-sidecar/model-addition-workflow/hand-over.md#manifest),
     [Batch-conversion check](../../specs/model-sidecar/model-addition-workflow/hand-over.md#batch-conversion-check)
     and step 1b of [phase 1](../../specs/model-sidecar/model-addition-workflow/phase-1-intake.md).
     Until the workflow commit of ADR-0QKK item 6, these headings name `batch_artifacts` keys and
     `source_batch_size`. Item 1 replaces those names.
   - The other rules of JB5J item 5:
     [Parity](../../specs/model-sidecar/model-addition-workflow/parity.md), template part
     [5](../../specs/model-sidecar/templates/change-proposal.md#5-parity-evidence),
     [Run the tool](../../specs/model-sidecar/model-addition-workflow/hand-over.md#run-the-tool),
     [Imports](../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#imports-of-other-sections),
     and [`static-batch-v1`](../../specs/model-sidecar/common/batch-conversion.md#static-batch-v1),
     [Behaviour](../../specs/model-sidecar/common/batch-conversion.md#behaviour) and
     [Authoring guidance](../../specs/model-sidecar/common/batch-conversion.md#authoring-guidance)
     of `common.batch_conversion`. The target rule of JC4T item 6 stays: after the pin change, an
     exporter takes skellytracker as a dependency from a uv path source to the local checkout.
   - ADR-0011: the RTMDet person graph ends before NMS. It gives `boxes` `[B, A, 4]` (`xyxy`,
     model-input pixels) and `scores` `[B, A]`. The sidecar declares `decode.selection: nms`. The
     other rules: [RTMDet person](../../specs/model-sidecar/examples/README.md#rtmdet-person-openmmlab-exporter-nms-free-outputs-host-nms),
     [Authoring guidance](../../specs/model-sidecar/post/selection-nms.md#authoring-guidance) and
     [Validation rules](../../specs/model-sidecar/post/selection-nms.md#validation-rules) of
     `post.det.selection.nms`,
     [Behaviour](../../specs/model-sidecar/post/detection-decode.md#behaviour) of the detection
     decode,
     [Not added](../../specs/model-sidecar/changelog.md#considered-and-deliberately-not-added)
     and [`sizes`](../../specs/model-sidecar/common/sizes-and-artifacts.md#sizes). Item 2 gives the
     row count `A` of each size. Do not compare the host decode with an appended ONNX
     `NonMaxSuppression` at the `0.001` threshold: it caps 300 boxes for each class.

## Reason

- On 2026-11-02, the user chose the flattened batch form. The user also decided that all contract
  simplifications land in the spec cleanup.
- `source_batch_size` had one valid value, `3`. `batch_axis` had one valid value, `0`.
- `outputs[].shape` has `-1` for an axis that changes with the size, for example the RTMDet row
  count `A`. Without `output_shapes`, a host cannot get that value from the sidecar.
- The user decided that the CRV0 content lands with the `output_shapes` of the current export
  graphs. The rebuilt bundles replace them.

## Consequences

- The spec-owned version entry that follows adds this entry to the re-export request of
  [ADR-NB5F](NB5F-no-change-classes-and-one-re-export-request.md) item 2. The frozen package reads
  `batch_artifacts` until it migrates.

## Alternatives rejected

- **Keep a batch key in each size.** It states one value again in each size.
- **A value from the sidecar for a symbolic axis**, for example `keypoint_count` 133. The entry then
  does not agree with the graph.

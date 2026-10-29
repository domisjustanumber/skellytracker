# CRV0 — `output_shapes` in each batch group

**Status:** accepted, 2026-10-29 (user; PR: pending).

## Decision

Change class `vnext`.

1. A `vNEXT` sidecar declares `output_shapes` in each batch group of each size. It has one entry
   for each output that `outputs` declares, in the same order. An axis that the graph leaves
   symbolic stays `-1`. `V-common.sizes_and_artifacts-9` checks the rule at `vNEXT`.
2. **Consistency.** When the family `outputs[].shape` declares a shape for an output, each
   `output_shapes` entry of that output has the same rank. Where a family dim is fixed (not `-1`),
   the group dim equals it or is `-1`. An `output_shapes` entry is a shape, with `-1` for a
   symbolic axis. It is not always a concrete shape.
3. A sidecar before `vNEXT` keeps the old rule. Only a size with more than one batch key must
   declare `output_shapes` in each group. With one key, the top-level `outputs[].shape` can replace
   it.
4. Behaviour 5 of [`common.batch_conversion`](../common/batch-conversion.md#behaviour) always takes
   the output shapes of a generated artifact from the `output_shapes` of the source group.
5. **Examples: `needs-export`.** The rule makes the examples `rtmo-body7` and `rtmw-wholebody`
   invalid. Their groups need values that only an export can give. The forced-edit rules allow no
   added value ([ADR-KDBD](../../../decisions/KDBD-change-classes-and-spec-forced-edits.md) item 5;
   [When a spec change makes an example invalid](../model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid)).
   Thus the content commit of this entry waits for the re-export bundles of these two examples from
   OpenMMLab-Exporter ([Re-export requests](open-work.md#re-export-requests)). The examples `yolo26`,
   `yolo26-body` and `rtmdet-person` already obey the rule.
6. **Where the rules go.** The content commit puts items 1 to 3 in the `output_shapes` row of
   [`batch_artifacts`](../common/sizes-and-artifacts.md#sizessizeonnxbatch_artifacts),
   `V-common.sizes_and_artifacts-9` and
   [Legacy behaviour](../common/sizes-and-artifacts.md#legacy-behaviour) of
   `common.sizes_and_artifacts`, and the wording of item 2 in
   [Behaviour](../common/outputs.md#behaviour) of `common.outputs`. It puts item 4 in
   [Behaviour](../common/batch-conversion.md#behaviour) of `common.batch_conversion`.

## Reason

- The user decided on 2026-10-29: every `vNEXT` sidecar gives `output_shapes` in each batch group of
  each size, with one entry for each output that the sidecar declares in `outputs`, in the same
  order. An axis that the graph leaves symbolic stays `-1`. The user added the consistency rule and
  chose `needs-export` for the two examples on the same day.
- Under [ADR-JB5J](../../../decisions/JB5J-one-batch-form-for-each-sidecar.md), each size of a
  `vNEXT` sidecar has exactly one batch key. Thus the old rule required `output_shapes` nowhere at
  `vNEXT`.
- `outputs[].shape` has `-1` for an axis that changes with the size, for example the RTMDet row count
  `A` (2100 at 320, 8400 at 640). Without `output_shapes`, a host cannot get `A` from the sidecar.
  This gap kept [ADR-0011](0011-rtmdet-host-nms.md) from absorption.
- The spec gives no batch rule for `outputs[].shape`. Thus the one-key replacement was ambiguous
  ([Spec defects](open-work.md#spec-defects)).

## Consequences

- OpenMMLab-Exporter, Ultralytics-Exporter and Qualcomm-Exporter write `output_shapes` only for a
  size with more than one batch key. Their `vNEXT` sidecars must write it in each group.
- `SizeSpec` in the package checks only the old rule. The implementation stage must add the `vNEXT`
  rule and the consistency rule. The landing records this in the root
  [open work](../../../decisions/open-work.md).
- [ADR-0011](0011-rtmdet-host-nms.md) stays Active until the content commit lands.

## Evidence

These values are evidence only. They are not example edits. The re-export bundles replace them
(graph dims read with onnx 1.22.0, 2026-10-29):

- `rtmo-body7`, size `m`, batch 1: `[[1, -1, -1], [1, -1, 17, 3]]`. OpenMMLab-Exporter
  ADR-0020 records this graph for the real RTMO-M batch 1 export, at the commit of the tracked copy
  ([`notes/decisions/0020-rtmo-sidecar-contract.md:59-63`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0020-rtmo-sidecar-contract.md#L59-L63)).
  A test at the inventory commit pins that export by its SHA-256 prefix `0dbaad50`
  ([`tests/test_rtmo.py:283-291`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/tests/test_rtmo.py#L283-L291)).
  The local export file of size `m`, batch 1, `fp32` (not in git) has that hash and these dims.
  `dets` has a symbolic last axis, so its entry is `-1` and not `5`.
- `rtmw-wholebody`, batch 1: size `m` `[[1, -1, 384], [1, -1, 512]]`, size `l-384`
  `[[1, -1, 576], [1, -1, 768]]`. The local export sidecar that the inventory entry names (not in
  git) has these `output_shapes` in its batch 1 groups. The four batch 1 ONNX files next to it have
  the same dims. OpenMMLab-Exporter ADR-0019 records `[1, symbolic, 384]` and `[1, symbolic, 512]`
  for RTMW-M
  ([`notes/decisions/0019-rtmw-real-export-sidecar-contract.md:24-28`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/notes/decisions/0019-rtmw-real-export-sidecar-contract.md#L24-L28)).
  The keypoint axis is symbolic, so its entry is `-1` and not `133`.

## Alternatives rejected

- **Keep the one-key replacement.** `outputs[].shape` has `-1` for the RTMDet rows and the RTMW
  SimCC bins, so the sidecar does not give these values.
- **Write a value from the sidecar for a symbolic axis**, for example `keypoint_count` 133 or the
  `dets` field count 5. The entry then does not agree with the graph.
- **Forced edits with the values above.** The forced-edit rules allow no added value.

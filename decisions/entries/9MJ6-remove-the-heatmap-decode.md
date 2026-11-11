# 9MJ6 — Remove the heatmap decode

**Status:** accepted, 2026-11-04 (user; PR: pending).

## Decision

1. **The user decision.** On 2026-11-04, the user chose "Remove heatmap for now": delete the
   heatmap method and its section until a model needs it. No sidecar uses it, and the spec keeps no
   backward compatibility.
2. **What goes.** The section `post.pose.decode.heatmap` and its file `post/pose-decode-heatmap.md`.
   The value `heatmap` of `pose.decode.method`. The value `heatmap` of `outputs[].semantic`, because
   only this method used it. The rule `V-post.pose.decode.heatmap-1`. Its number stays unused.
3. **What changes.** [`post.pose.schema`](../../specs/model-sidecar/post/keypoint/schema.md) and
   [`common.outputs`](../../specs/model-sidecar/common/outputs.md) do not list `heatmap`, also in
   `V-post.pose.schema-3`, `V-post.pose.schema-7` and `V-common.outputs-3`. These rule IDs stay. The
   section map, the validation index and the model intake template do not list the section. The
   changelog lists the method under "Considered and deliberately not added".
4. **What stays.** The methods `simcc` and `coordinate`, and each other rule. No example changes.
   The sentence "The heatmap decode is `2d` only" of [ADR-90CE](90CE-minimal-sidecar-contract.md) item 5 has no effect while the method is
   absent. This entry does not supersede 90CE. The next consolidation entry restates 90CE without
   that sentence.
5. **A future heatmap model.** It brings a full contract through the model addition workflow: the
   fields, the behaviour, the rules and the vectors of a new section. The parked evidence is the
   proposal `heatmap-decode-refinement` of OpenMMLab-Exporter and its parity scripts
   (OpenMMLab-Exporter ADR-0053,
   [`0053-pose-sidecar-parity-runs.md`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/aa33093c76168e4f5badea1e6dd03217debbdd12/notes/decisions/0053-pose-sidecar-parity-runs.md)).
   That section also states the geometry rule of [ADR-90CE](90CE-minimal-sidecar-contract.md)
   item 5: the heatmap decode is `2d` only.
6. **The frozen package.** `skellytracker/core/sidecar/model.py` still accepts `heatmap`. The
   `Literal` coverage test of `tools/tests/test_traceability.py` skips it (`REMOVED_VALUES`). The M8
   item "Heatmap decode removed" of the
   [implementation plan](../../specs/sidecar-implementation-plan.md) removes it from the package and
   removes the skip.

## Reason

- The section was `stable`, but a host could not implement it. It had no tie rule, no sub-pixel
  refinement, no scale from the heatmap to the model input, no score definition and no vectors.
- No sidecar of this repo or of an exporter uses `heatmap`. The user parked the ViTPose families on
  2026-10-26.
- A contract that no host can implement and no model needs gives no value. The first model that
  needs it gives the evidence for the full contract.

## Alternatives rejected

- **Complete the section now.** No model in scope needs it, so no export can verify the new text.
- **Keep the section and record the defect.** The spec then keeps a `stable` contract that a host
  cannot implement.

_Edited 2026-11-11 (this PR): link repair._

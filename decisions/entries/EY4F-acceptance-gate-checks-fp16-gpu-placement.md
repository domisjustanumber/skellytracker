# EY4F — The acceptance gate checks the fp16 GPU placement of each model

**Status:** absorbed into [`proposal-gate.md#steps`](../../.claude/skills/implement-sidecar-section/proposal-gate.md#steps), [`proposal-gate.md#a-model-with-the-verdict-describes`](../../.claude/skills/implement-sidecar-section/proposal-gate.md#a-model-with-the-verdict-describes), [`proposal-gate.md#the-first-models`](../../.claude/skills/implement-sidecar-section/proposal-gate.md#the-first-models), 2026-11-12 (absorb at 90%; PR: pending).

## Decision

This entry adds a skellytracker check to the exporter rules of
[ADR-NPX6](NPX6-newest-opset-and-fp16-gpu-placement-check.md). It does not change them.

1. **The check.** Step 5 of the [acceptance gate](../../.claude/skills/implement-sidecar-section/proposal-gate.md)
   (the model gate) also runs each fp16 file of the model on the EP packs `cuda` and `trt-rtx`, at
   each published batch form, on a host with an NVIDIA GPU. It reads the count of the nodes of each
   session on the CPU EP and their op types
   ([ADR-9NW0](9NW0-ep-keys-options-and-failures.md) item 5).
2. **The result.** A count above 0 gives the response `needs-contributor`, with the op types. The
   contributor exports again, as NPX6 item 3 says.
3. **No GPU host.** With no NVIDIA GPU host, the session writes `to run` for the check in the
   response. The other parts of the model gate still decide.
4. **Scope.** The check applies to each model that passes step 5: a model with the verdict
   `describes`, a proposal for acceptance, and the first models of stage 1.9 of the implementation
   plan.

## Reason

- The user chose this check on 2026-11-12. NPX6 left a gap: an exporter with no GPU can apply only
  the opset rule, and a CPU node then shows only as the run warning `ep_partial_placement`, after the
  model lands.
- The parity run of the model gate compares outputs. It does not find a node on the CPU EP.
- The first fp16 `rtmw-wholebody133` export put 3 `Clip` nodes on the CPU EP with the CUDA plugin
  ([ADR-MWY9](MWY9-one-onnxruntime-core-and-plugin-ep-packs.md) Evidence). This check gives
  `needs-contributor` for that file, and a pass for the opset 17 re-export.

## Alternatives rejected

- **The exporter kit only.** A CPU node of an exporter with no GPU then lands.
- **A sidecar field for the placement.** The placement depends on the ONNX Runtime version, the EP
  pack and the GPU, not on the meaning of the sidecar.

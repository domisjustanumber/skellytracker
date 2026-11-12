# NPX6 — Exporters use the newest opset and check that each fp16 file runs fully on the GPU

**Status:** absorbed into [`validation-and-publishing.md#opset-and-gpu-placement`](../../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#opset-and-gpu-placement), [`model-intake.md#batch-conversion-check`](../../specs/model-sidecar/templates/model-intake.md#batch-conversion-check), [`author-sidecar/SKILL.md#step-5-write-and-check-the-sidecar`](../../.claude/skills/author-sidecar/SKILL.md#step-5-write-and-check-the-sidecar), 2026-11-12 (absorb at 90%; PR: pending).

## Decision

1. **Newest opset.** An exporter exports each ONNX file at the newest opset that its export tool
   and the pinned ONNX Runtime both support. An older opset needs a reason in the intake.
2. **fp16 GPU placement.** An exporter runs each fp16 file on each GPU EP that it can run, at each
   published batch form, and records the count of the nodes on the CPU EP and their op types. From
   the 2.0.0 pre-release, the GPU EPs are the packs of the EP catalog (`cuda` and `trt-rtx`), and the
   counts come from `cpu_nodes` and `cpu_op_types` of the run timing
   ([ADR-9NW0](9NW0-ep-keys-options-and-failures.md) item 5).
3. **A node on the CPU EP is an exporter defect.** The exporter exports again at a newer opset, or
   changes the graph, until no node is on the CPU EP. If no change removes the node, the intake names
   the node and the reason.
4. **No GPU.** An exporter that cannot run a GPU EP writes `to run` with the reason. Item 1 is then
   the minimum.
5. **Where.** The heading "Opset and GPU placement" of the model addition workflow states these
   rules. The model intake template records them. The skill `author-sidecar` runs them in step 5.

## Reason

- The user, on 2026-11-12, after the hardware and EP work: the exporter kit must make sure that an
  exporter "tests full fp16 running, or at least uses the latest supported onnx opset".
- The fp16 `rtmw-wholebody133` file of the first export put 3 `Clip` nodes on the CPU EP with the
  CUDA plugin ([ADR-M2C6](M2C6-exact-pins-and-one-python-patch-release.md) keeps this evidence in
  [ADR-MWY9](MWY9-one-onnxruntime-core-and-plugin-ep-packs.md)). The opset 17 re-export, bundle v4,
  put no node on the CPU EP on `cuda` and on `trt-rtx`.
- A node on the CPU EP copies data between the GPU and the CPU in each frame. The parity check and
  the vector runs do not find it, because they compare outputs, not placement.

## Consequences

- An exporter with no NVIDIA GPU can only apply item 1. The skellytracker session then runs the
  placement check before the model lands, or records `to run`.

## Alternatives rejected

- **The opset rule only.** A new opset does not prove the placement on each EP.
- **The placement check only.** An exporter with no GPU then has no rule.

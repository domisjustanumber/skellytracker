**Stop if you are an exporter agent. Only a skellytracker session uses this file.**

# Acceptance gate

This file uses ASD-STE100 Simplified Technical English.

The gate applies from the 2.0.0 pre-release
([ADR-6J8E](../../../decisions/entries/6J8E-exporters-run-released-skellytracker.md) items 6 and 7).
Until then, the current rules of [`change-sidecar-spec`](../change-sidecar-spec/SKILL.md) apply. No
workflow file links to this file.

The gate turns a `recorded` proposal into a `verified` proposal. The user accepts only a `verified`
proposal (6J8E item 6).

## Steps

1. **Triage.** Ask the user if skellytracker implements the `recorded` proposal for acceptance. Use
   the skill [`ask-the-user`](../ask-the-user/SKILL.md).
2. **Plan.** Do steps 1 to 4 of [`implement-sidecar-section`](SKILL.md). Use the proposed text of
   the record (part 2 of `specs/model-sidecar/proposals/<slug>/proposal.md`), not the current spec
   text.
3. **Apply the patch.** If the record has `skellytracker.patch`, follow
   [Patch review](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#patch-review).
4. **Section gate.** Each vector case of the bundle agrees through its `PACKAGE_RUNNERS` adapter. Add
   the skellytracker `path::symbol` to `verified_against`. On a disagreement, never edit `expect`.
   Find the cause. Text that is not clear, or an exporter defect, gives `needs-contributor`. A defect
   of skellytracker gets a fix. A case with no upstream output is verified when skellytracker agrees
   and its `note` names the spec rule that it tests
   ([ADR-JJ7E](../../../decisions/entries/JJ7E-no-upstream-case-verified-by-skellytracker.md)).
5. **Model gate.** The package loads the sidecar with no V- rule failure. Get each `external` ONNX
   file and check its SHA-256. The run on the reference image matches the `parity/` output of the
   bundle within the tolerances of
   [Parity](../../../specs/model-sidecar/model-addition-workflow/parity.md), for at least one size.
   A bundle with no reference output gets `needs-contributor`. On a host with an NVIDIA GPU, run
   each fp16 file on the EP packs `cuda` and `trt-rtx`, at each published batch form. Read the count
   of the nodes of each session on the CPU EP. A count above 0 gives `needs-contributor`, with the op
   types. With no NVIDIA GPU host, write `to run` for this check in the response
   ([ADR-EY4F](../../../decisions/entries/EY4F-acceptance-gate-checks-fp16-gpu-placement.md)).
6. **Catalog.** Put the sidecar in the package sidecar root `core/model_zoo/`. Add a test that
   builds the detector by its catalog key and runs one frame.
7. **Report.** Write the response `verified`
   ([Responses](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#responses)). The
   user accepts. Then land the content commit (procedure B of `change-sidecar-spec`), the
   implementation commit and the catalog commit, in this order.

## A model with the verdict `describes`

Do only steps 5 to 7. Procedure A of `change-sidecar-spec` makes the content commit.

## The first models

Stage 1.9 of the [implementation plan](../../../specs/sidecar-implementation-plan.md) runs steps 5
to 7 for `yolox-person` and `rtmw-wholebody133`, before the pre-release
([ADR-NHM3](../../../decisions/entries/NHM3-phases-to-the-exporter-checkpoint.md) item 3). Each one
comes in a `model` bundle with the verdict `describes`.

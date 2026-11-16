# Q5BN — The result of a camera has `node_ran` for each inference node

**Status:** absorbed into [`outputs.md#fields`](../../specs/pipeline/outputs.md#fields), [`outputs.md#behaviour`](../../specs/pipeline/outputs.md#behaviour), [`outputs.md#validation-rules`](../../specs/pipeline/outputs.md#validation-rules), [`sidecar-implementation-plan.md#110-the-pipeline-api-was-p`](../../specs/sidecar-implementation-plan.md#110-the-pipeline-api-was-p), 2026-11-16 (user, question F5; PR: pending).

## Decision

1. **The field.** The result of one camera for one call has the field `node_ran`: a mapping of
   node id to a boolean, with one key for each inference node of the file. An inference node is a
   node of the type `onnx_model` or `mediapipe_tasks`
   ([Terms](../../specs/pipeline/README.md#terms)). In the Python API, the type is
   `dict[str, bool]`.
2. **Ran.** An inference node ran for a camera when it did an inference on the frame of that
   camera in this call. The value is then true, also when the node found no instance and its
   outputs are empty.
3. **Did not run.** The value is false for a node that got an empty required input, for a node
   that the run does not use, and for a node whose outputs are all replayed. A padded batch item
   is not a run.
4. **Timing.** The run gives `node_ran` also when the timing is off.
5. **Names.** An output name must not be `frame_index`, `image_size`, `timestamp_ms` or
   `node_ran` (new rule `V-pipeline.outputs-3`). The reference model checks it at load.
6. **Stage.** The executor of stage 1.10 of the implementation plan gives `node_ran`, and the gate
   of that stage tests it.

This decision changes no example and no node section. The built-in pipelines do not change here.

## Reason

- The user decided this on 2026-11-16 (question F5): the new API must give the redetect flag, and
  each spec change that it needs is approved.
- freemocap shows the person box in green when the detector ran on the frame and in orange when
  the box is carried over. It stores a `DETECTOR_RAN` column and counts `object_detector_runs`.
- The outputs could not give this fact. A detector that did not run and a detector that ran and
  found nobody both gave an empty `detections` value.
- The result of a camera holds the outputs and the fixed fields in one mapping. An output with
  the name of a fixed field would hide that field.

## Alternatives rejected

- **A new output port of `redetect_trigger`.** The trigger asks for a detection. It does not know
  that the detector ran. A pipeline with no trigger has no signal.
- **A field on the `detections` value.** It needs a change of three value tables, and a rule for
  `gate`, `first_of` and `@prev`.
- **The timing events only.** freemocap needs the fact also when the timing is off.

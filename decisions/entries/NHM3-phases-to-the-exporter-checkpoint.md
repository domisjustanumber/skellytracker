# NHM3 — Two phases to the exporter checkpoint; the pre-release at the checkpoint; new code beside old code

**Status:** accepted, 2026-11-12 (user).

## Decision

This entry supersedes [ADR-EM74](EM74-stage-order-and-ci-models.md) in full. Items 1, 6, 8, 9
and 10 restate EM74 items 1, 3, 5, 6 and 7. Items 2 to 5 and 7 replace EM74 items 2 and 4.

1. **Beside, then delete.** The new code is built beside the old code. The old ONNX detectors, the
   old loader `core/sidecar/`, the old processing modules, `core/tracker/` and the old detector
   contract do not change until their replacements pass the gate. Then a deletion stage removes
   them. No new code imports them. No shared function gets a legacy switch.
2. **Checkpoint.** At the checkpoint, agents can build the exporters again and add their models and
   pipelines. The checkpoint has: each dependency bumped and pinned
   ([ADR-B4QR](B4QR-exact-pins-and-cuda-13.md)); the MediaPipe Holistic task; `yolox-person` and
   `rtmw-wholebody133` with a fixed batch and the batch conversion; the API for the sidecar models
   (`detectors`), the pipelines (`pipelines`) and the hardware and EPs; the pipeline spec with its
   contribution and implementation process; the sidecar spec with its implementation process; and an
   up-to-date exporter kit (the draft exporter guide, the templates and the skills).
3. **Phase 0, in the spec-build stage.** No file under `skellytracker/` changes.
   1. Split the acceptance gate of [ADR-6J8E](6J8E-exporters-run-released-skellytracker.md): the
      model gate for the first models, and the patch process for the exporters.
   2. The pipeline contribution process: the node workflow of
      [ADR-3SF2](3SF2-pipeline-spec-and-node-workflow.md) item 7, and a path for an exporter to
      send a pipeline file.
   3. The exporter kit. The guide tells an exporter to pin the pre-release.
   4. The hardware and EP work stays a parallel track on the branch `hw-and-ep-work`. Before the
      gate, that branch merges into the working branch, and its API work becomes a stage of the
      implementation plan, under `core/`
      ([ADR-AQR4](AQR4-detectors-and-pipelines-entry-points.md) item 3).
   5. Gate: the user declares the implementation stage in a new entry.
4. **Phase 1, in the implementation stage.** The order:
   1. Dependencies ([ADR-B4QR](B4QR-exact-pins-and-cuda-13.md)).
   2. Package layout.
   3. Hardware and EP API.
   4. Spec loader.
   5. Spec processing.
   6. Catalog and `detectors`.
   7. Standalone generic detectors, with the batch conversion.
   8. Standalone MediaPipe Holistic runner on the Tasks API, with the timestamp fix and the safe
      close.
   9. `yolox-person` and `rtmw-wholebody133`, with the model gate at the detector level.
   10. Pipeline API. Its `mediapipe_tasks` node wraps the runner of step 8.
   11. The checkpoint.

   Steps 3 and 8 need only steps 1 and 2. They can run in parallel with steps 4 to 7.
5. **Pre-release.** The 2.0.0 pre-release is at the checkpoint, after the pipeline API and before
   any deletion. Its gate: each part of item 2 is done, and an exporter environment pins the
   pre-release and runs one model and one pipeline. Its release note says that the old ONNX
   detectors, their keys and their `model_name` values go in a later release, and that freemocap
   must not move to 2.0.0 before it migrates.
6. **Standalone generic detectors.** They have no old registry key, no `detector_type`, no old
   config base and no link to `DetectionStageConfig`. The batch path of a run (batch at start,
   padding) is in the pipeline runtime. No stage writes Python pipeline builders. Step 7 does not
   change `core/tracker/`.
7. **Phase 2, after the checkpoint.** The order: delete the old YOLOX and RTMW; the RTMPose
   replacements from the exporters, with their pipeline; delete the old RTMPose, the old loader and
   the old processing; delete the old run code (`core/tracker/`, the old configs and contract,
   `keypoint_bbox`, `precomputed`, the old MediaPipe classes, annotators and demo builders); the
   2.0.0 release, with the old code deleted, so freemocap moves one time.
8. **CI.** CI tests the ONNX path with tiny fixed-batch models that `onnx.helper` makes at run time,
   with a sidecar in a temporary root. CI runs no real model. Parity against the upstream reference
   output is a local gate.
9. **MediaPipe at each stage.** MediaPipe works after each stage. Its tests keep their expected
   values, except in the one commit of the MediaPipe change and in the deletion of the old run code.
   Do not change the MediaPipe tests to close their detectors or to add teardown. Fix the timestamp
   fallback of the old detectors and of the runner, and make them close their landmarkers safely,
   also when the garbage collector frees them.
10. **Gates.** The deletion of the old run code checks that each built-in pipeline runs as a config.
    The MediaPipe built-in has no keypoint parity with the old builders.

## Reason

- The user gave the checkpoint list, "so that I can then use agents to rebuild all of the model
  exporters and add their new models and relevant pipelines", and of `hw-and-ep-work`: "Merging it in should be a gate
  before phase 0 is complete."
- The exporters add pipelines, so the release that they pin needs the pipeline API and the EP API.
  One pre-release at the checkpoint replaces a pre-release with no pipeline API and a second pin.
- The Holistic runner needs only the dependencies and the layout. It gives a tested result before
  the pipeline API, which is the largest stage.
- The Reason of EM74 applies to items 1 and 6 to 10.

## Consequences

- The exporters get a release later than in EM74.

## Alternatives rejected

- **The EM74 order, with the pre-release after the first models.** The exporters then pin a release
  with no pipeline API and no EP API.
- **Holistic only in the pipeline API stage.** It ties the MediaPipe change to the largest stage.

## Open work

See [open-work.md](../open-work.md).

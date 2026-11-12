# Open work

This file holds the open work of the [decision log](README.md) of the pipeline spec. The
implementation-stage work is in the
[implementation plan](../../sidecar-implementation-plan.md). The other repository state is in the
root [open-work.md](../../../decisions/open-work.md).

## Draft spec

- **Node workflow.** After the draft lands: one workflow file and one node-proposal template in
  `specs/pipeline/`, the landing skill `change-pipeline-spec`, and the `node.` mapping of
  `tools/intake_bundle.py` ([ADR-3SF2](../../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md)
  item 7).
- **Crop border.** A detector node crops a rotated ROI with `affine_crop`
  ([ADR-G3FA](../../model-sidecar/decisions/entries/G3FA-affine-crop-rotated-roi.md)). Its border is
  constant. The MediaPipe hand chain fills the border with the edge pixels. That border mode waits
  for a sidecar proposal (the spec defects of the
  [sidecar open work](../../model-sidecar/decisions/open-work.md#spec-defects)). The decomposed
  MediaPipe example needs it.
- **Multi-person identity.** I > 1 is allowed everywhere. Without an `associate` node, a row has no
  identity across frames, and each `track_ids` value is -1
  ([Graph](../graph.md#behaviour) item 8;
  [ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1). A later
  `associate` node type gives the rows an identity. Until then, the temporal nodes filter row `i`,
  which can be another person on the next frame.
- **Values of other port types.** The value of an output or a tap of the port type `image` or
  `tensor` is not fixed ([Outputs](../outputs.md#behaviour) item 6). Fix it in the
  implementation stage P, before the first output of such a port.
- **Video replay.** A replay refuses a tap with no image list hash, so only the COCO input form can
  be replayed ([Taps](../taps.md#behaviour) item 5). A video replay needs an image list hash for
  video.
- **ROI input of `mediapipe_tasks`.** The node has no ROI input in v1
  ([ADR-8NVD](../../../decisions/entries/8NVD-pipeline-api-warnings-and-catalog.md) item 4).
- **Face blendshapes.** The `mediapipe_tasks` node gives no face blendshapes. They are planned
  work after the development-streaming merge.
- **MediaPipe 1.2.2.** Run the scripts of
  [ADR-6JWJ](entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md) again on MediaPipe 1.2.2.

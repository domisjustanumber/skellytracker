# Open work

This file holds the open work of the [decision log](README.md) of the pipeline spec. The
implementation-stage work is in the
[implementation plan](../../sidecar-implementation-plan.md). The other repository state is in the
root [open-work.md](../../../decisions/open-work.md).

## Draft spec

- **Crop border.** An `onnx_model` node crops a rotated box with `affine_crop`
  ([ADR-G3FA](../../model-sidecar/decisions/entries/G3FA-affine-crop-rotated-roi.md)). Its border is
  constant. The MediaPipe hand chain fills the border with the edge pixels. That border mode waits
  for a sidecar proposal (the spec defects of the
  [sidecar open work](../../model-sidecar/decisions/open-work.md#spec-defects)). The decomposed
  MediaPipe example needs it.
- **Multi-person identity.** v2.0.0 tracks one person (`V-pipeline.graph-11`;
  [ADR-TH8E](../../../decisions/entries/TH8E-one-person-in-v2.md)). Each `track_ids` value is -1
  ([Graph](../graph.md#behaviour) item 8). A later `associate` node type gives the rows an identity
  and removes the limit.
- **Tap form of the port type `flag`.** A flag is not an output: the `outputs` block has no key for
  it ([Outputs](../outputs.md#behaviour) item 6). Stage 7 of the
  [build order](../proposals/node-and-port-redesign.md#10-build-order) of the redesign gives the tap
  form of a flag. Until then the start of a run refuses a tap on a `flag` port.
- **Video replay.** A replay refuses a tap with no image list hash, so only the COCO input form can
  be replayed ([Taps](../taps.md#behaviour) item 5). A video replay needs an image list hash for
  video.
- **Box input of `mediapipe_tasks`.** The node has no `boxes` input in v1
  ([ADR-V7GZ](../../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 4).
- **Face blendshapes.** The `mediapipe_tasks` node gives no face blendshapes. They are planned
  work after the development-streaming merge.
- **MediaPipe landmark schemas.** The groups of a `mediapipe_tasks` node have a null
  `landmark_schema`, so they pass through in the canonical form. Stage 2.2 of the
  [implementation plan](../../sidecar-implementation-plan.md) registers the MediaPipe schemas. Then
  the spec gives them to these groups
  ([ADR-4MP6](../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md) item 2).
- **Side label in `assign_keypoints`.** MediaPipe gives a handedness label for each hand: the side
  of the hand of the subject. A mirrored input image inverts the label. `assign_keypoints` uses only
  the anchor distance. A later change can use a side label of the source in `assign_keypoints`, for
  example to put a left hand only
  in the slot `left_hand`
  ([ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 8).

## Ideas

These ideas are optional. They have no stage.

- **OpenPose export.** An adapter can write a `keypoints` output in the OpenPose `POSE_KEYPOINT`
  form, so that ComfyUI nodes can read it
  ([ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 8).

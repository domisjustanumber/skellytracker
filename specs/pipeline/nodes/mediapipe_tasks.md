---
id: node.mediapipe_tasks
title: MediaPipe Tasks node
kind: node
vectors: null
status: {spec: draft}
---

# MediaPipe Tasks node

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A `mediapipe_tasks` node wraps one MediaPipe Tasks landmarker: pose, hand, face or holistic. It calls the Tasks landmarker directly and uses the MediaPipe assets of [ADR-0XW9](../../../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) ([ADR-V7GZ](../../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 4). The landmarker does its own detection, crops and tracking. The pipeline spec does not define them ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 7). The node has no reset and no back-off ([ADR-6JWJ](../decisions/entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md)).

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Set during run | Description | Source |
|---|---|---|---|---|---|---|
| `variant` | `Literal['body', 'hand', 'face', 'holistic']` |  | required | no | The Tasks landmarker: pose (`body`), hand, face or holistic. | ADR-V7GZ item 4; ADR-88WQ item 4 |
| `max_instances` | `int` | >= 1 | `1` | no | `num_poses`, `num_hands` or `num_faces`. Holistic is single person: 1. | MediaPipe `num_poses`, `num_hands`, `num_faces` (Tasks default 1); ADR-V7GZ item 4 |
| `size` | `Literal['lite', 'full', 'heavy']` |  | `"heavy"` | no | The model size of the pose landmarker. Only the variant `body` takes it (V-node.mediapipe_tasks-2). | MediaPipe asset `pose_landmarker_<size>`; MediapipePoseDetectorConfig.model_complexity |
| `min_detection_score` | `float` | >= 0.0, <= 1.0 | `0.5` | no | The minimum detection score (Holistic: the pose and the face detection). | MediaPipe `min_*_detection_confidence` (Tasks default 0.5) |
| `min_presence_score` | `float` | >= 0.0, <= 1.0 | `0.5` | no | The minimum presence score (Holistic: the landmark score of each part). | MediaPipe `min_*_presence_confidence`, Holistic `min_*_landmarks_confidence` (Tasks default 0.5) |
| `min_tracking_score` | `float` | >= 0.0, <= 1.0 | `0.5` | no | The minimum tracking score in VIDEO mode. Holistic has no tracking option. | MediaPipe `min_tracking_confidence` (Tasks default 0.5) |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `image` | input | `image` |
| `run_if` | input | `flag` |
| `keypoints` | output | `keypoints` |
<!-- /node-table:ports -->

The params use the shared names of the pipeline spec, not the MediaPipe option names, so a node swap is simple ([ADR-88WQ](../../../decisions/entries/88WQ-sidecar-vocabulary.md) item 7). The Source column of the params table names the MediaPipe option of each param. The node gives the three thresholds to the options of the landmarker of its `variant`. The option names are those of MediaPipe 1.2.2 (`mediapipe/tasks/python/vision/*_landmarker.py`):

| `variant` | MediaPipe landmarker | `min_detection_score` | `min_presence_score` | `min_tracking_score` |
|---|---|---|---|---|
| `body` | `PoseLandmarker` | `min_pose_detection_confidence` | `min_pose_presence_confidence` | `min_tracking_confidence` |
| `hand` | `HandLandmarker` | `min_hand_detection_confidence` | `min_hand_presence_confidence` | `min_tracking_confidence` |
| `face` | `FaceLandmarker` | `min_face_detection_confidence` | `min_face_presence_confidence` | `min_tracking_confidence` |
| `holistic` | `HolisticLandmarker` | `min_face_detection_confidence`, `min_pose_detection_confidence` | `min_face_landmarks_confidence`, `min_pose_landmarks_confidence`, `min_hand_landmarks_confidence` | none |

- `run_if` is an optional `flag` input for the variants `body`, `hand` and `face`. When it is connected and false, the node does not run, and the output is empty. The variant `holistic` takes no `run_if` (`V-node.mediapipe_tasks-3`; [ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 7).
- `max_instances` sets `num_poses`, `num_hands` or `num_faces`. `HolisticLandmarkerOptions` has no such option.
- `HolisticLandmarkerOptions` has no tracking option. The node ignores `min_tracking_score` for the variant `holistic`.
- The other options of a landmarker keep their Tasks defaults, for example `min_face_suppression_threshold` and `min_pose_suppression_threshold` of Holistic.
- `size` selects the asset `pose_landmarker_lite`, `pose_landmarker_full` or `pose_landmarker_heavy` (`skellytracker/core/detectors/keypoint_detectors/mediapipe/mediapipe_model_manager.py`). It applies only to the variant `body` (`V-node.mediapipe_tasks-2`).

## Behaviour

- The running mode of the landmarker follows the `running_mode` of the run: `IMAGE` for `image`, and `VIDEO` for `video` and `live` ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) items 2 and 5).
- In `VIDEO` mode the node gives the `timestamp_ms` of each frame to the landmarker ([Running](../running.md#behaviour)).
- In `VIDEO` mode the node is stateful. In the running mode `video`, a pipeline with this node upstream of an `onnx_model` node thus runs at batch = camera count ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 5).
- The `instance_score` of each present row is 1.0, because the Tasks results have no instance score ([Graph](../graph.md#behaviour) item 8). The rows keep the order of MediaPipe.
- The output is one `keypoints` set with `max_instances` rows, in the instance format of [Graph](../graph.md#behaviour) item 8. The node is the instance source of its output. The score of a point is the landmark visibility of MediaPipe ([ADR-88WQ](../../../decisions/entries/88WQ-sidecar-vocabulary.md) item 4). A found point with no visibility value has the score 1.0 ([ADR-Y7C3](../decisions/entries/Y7C3-mediapipe-score-without-visibility-and-holistic-present-row.md) item 1). The node makes the groups of this table ([Graph](../graph.md#behaviour) item 7; [ADR-4MP6](../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md)). Each point name is `<group>/<name>`:

  | `variant` | Groups | Point names | Points |
  |---|---|---|---|
  | `body` | `<node id>` | `<node id>/<name>` | 33 |
  | `hand` | `<node id>` | `<node id>/<name>` | 21 |
  | `face` | `<node id>` | `<node id>/face_0000` to `<node id>/face_0477` | 478 |
  | `holistic` | `body`, `right_hand`, `left_hand`, `face` | `body/<name>`, then `right_hand/<name>`, then `left_hand/<name>`, then `face/face_0000` to `face/face_0477` | 33 + 21 + 21 + 478 |

  The `landmark_schema` of each group is null. The registry has no MediaPipe schema yet ([open work](../decisions/open-work.md)).

- The holistic order body, right hand, left hand, face is the order of freemocap.
- The output schema has `geometry: 3d` and `depth_unit: pixel` ([Outputs](../outputs.md#fields)). The node gives source-image pixels: it multiplies the normalised x and z of a landmark by the image width, and y by the image height. Thus z is the relative depth of MediaPipe, scaled by the image width, as the sidecar spec describes for the MediaPipe landmark models ([Coordinate decode](../../model-sidecar/post/keypoint/decode-coordinate.md#implementer-guidance)).
- The body names are the point names of `body/mediapipe_body.yaml`. The hand names are the point names of `hands/mediapipe_hand.yaml`. A face name is `face_` and the four-digit index of the point, as in `face/mediapipe_face_contour.yaml`. These files are in `skellytracker/core/detectors/keypoint_detectors/mediapipe/`.
- The 478 face points include the 10 iris points. They hold each point of the 136-point face contour subset ([ADR-V7GZ](../../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) Reason).
- The variant `holistic` is single person ([ADR-V7GZ](../../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 4). Its row is present when MediaPipe finds one or more of its parts: the body, the right hand, the left hand or the face ([ADR-Y7C3](../decisions/entries/Y7C3-mediapipe-score-without-visibility-and-holistic-present-row.md) item 2).
- The node has no `boxes` input in v1. A `boxes` input is open work ([ADR-V7GZ](../../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 4).
- The node never uses an execution provider. The EP of the run applies only to `onnx_model` nodes ([Running](../running.md#behaviour) item 7; [ADR-9PDQ](../../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 4). `MediapipeTasksParams` in `specs/pipeline/reference/pipeline_config.py` has no `execution_provider`.
- The timing span is `run`. Its time counts as model time in the skellybench timing record ([Timing](../timing.md#implementer-guidance); [ADR-Q59W](../../../decisions/entries/Q59W-pipeline-timing-and-taps.md) items 1 and 4; [ADR-9PDQ](../../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 3).

## Validation rules

- [ ] `V-node.mediapipe_tasks-1` The variant `holistic` is single person. When `variant` is `holistic`, `max_instances` must be 1.
- [ ] `V-node.mediapipe_tasks-2` Only the variant `body` takes `size`. When `variant` is not `body`, the params must not write `size`, also not the default value `heavy` ([ADR-97X9](../../../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) item 10).
- [ ] `V-node.mediapipe_tasks-3` The variant `holistic` must have no `run_if` input. The `run_if` input of another variant must name a port of the type `flag` ([ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 7).

## Implementer guidance

- In `VIDEO` mode, the landmarker needs strictly increasing integer timestamps. The node gives the `timestamp_ms` of the frame, which increases ([`V-node.smooth_keypoints-3`](smooth_keypoints.md#validation-rules) gives the same rule for the smoother). Today's code makes the timestamp from `int(time.monotonic() * 1000)`. Two frames less than 1 ms apart can get the same value, and MediaPipe then raises `ValueError: Input timestamp must be monotonically increasing`. No supported Python has the coarse Windows clock of Python 3.11 and 3.12, so the timestamp of the frame is a guard ([ADR-M2C6](../../../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) item 8; [ADR-EM74](../../../decisions/entries/EM74-stage-order-and-ci-models.md) item 6).
- The node must close its landmarker safely, also when the garbage collector frees the node. The gate of the Python change is the full suite on Python 3.13.18 with no hang in the MediaPipe tests, so a hang at exit is a regression ([ADR-M2C6](../../../decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) item 7; [ADR-EM74](../../../decisions/entries/EM74-stage-order-and-ci-models.md) item 6; [ADR-V7GZ](../../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 4).
- When `run_if` stops the node in `VIDEO` mode, the landmarker gets no frame and no timestamp for that frame. The measurement of [ADR-6JWJ](../decisions/entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md) did not measure a landmarker that gets no frame for a time.
- Today's package closes and builds a VIDEO-mode landmarker again after frames with no keypoints. The node does not do this. The measurement found no stuck landmarker on MediaPipe 0.10.33. Its scripts ran again on MediaPipe 1.2.2 (Windows, CPU), in the commit that pins `mediapipe==1.2.2`, with the same result ([ADR-6JWJ](../decisions/entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md)).
- In `live` mode, `frame_index` can skip, and a call can hold a subset of the cameras ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) items 2 and 3).
- The cameras stay separate ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1). In `VIDEO` mode, each camera thus needs its own landmarker state ([Running](../running.md#behaviour) item 5) and its own timestamp sequence.
- The output edges come from the MediaPipe YAML files ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).

## Authoring guidance

- The built-in `mediapipe-holistic-tasks` uses the variant `holistic`. It has no keypoint parity with the old MediaPipe builders ([ADR-V7GZ](../../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) items 3 and 4).
- For a face on the full frame, prefer `holistic` to `face`. Holistic found a small face on the full frame where `FaceLandmarker` found none ([ADR-V7GZ](../../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) Reason).

## Examples

```yaml
nodes:
  - id: holistic
    type: mediapipe_tasks
    inputs: {image: frame.image}
    params:
      variant: holistic
outputs:
  holistic: holistic.keypoints
```

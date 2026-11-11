---
id: node.mediapipe_tasks
title: MediaPipe Tasks node
kind: node
vectors: null
status: {spec: draft}
---

# MediaPipe Tasks node

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A `mediapipe_tasks` node wraps one MediaPipe Tasks landmarker: pose, hand, face or holistic. It calls the Tasks landmarker directly and uses the MediaPipe assets of [ADR-AQR4](../../../decisions/entries/AQR4-detectors-and-pipelines-entry-points.md) ([ADR-8NVD](../../../decisions/entries/8NVD-pipeline-api-warnings-and-catalog.md) item 4). The landmarker does its own detection, crops and tracking. The pipeline spec does not define them ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 7).

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Live | Description | Source |
|---|---|---|---|---|---|---|
| `variant` | `Literal['pose', 'hand', 'face', 'holistic']` |  | required | no | The Tasks landmarker. | ADR-8NVD item 4 |
| `max_instances` | `int` | >= 1 | `1` | no | `num_poses`, `num_hands` or `num_faces`. Holistic is single person: 1. | MediaPipe Tasks default; ADR-8NVD item 4 |
| `pose_model` | `Literal['lite', 'full', 'heavy']` |  | `"heavy"` | no | The pose landmarker model. Only for the variant `pose`. | MediapipePoseDetectorConfig.model_complexity |
| `min_detection_confidence` | `float` | >= 0.0, <= 1.0 | `0.5` | no | The minimum detection score (Holistic: the pose and the face detection). | MediaPipe Tasks default |
| `min_presence_confidence` | `float` | >= 0.0, <= 1.0 | `0.5` | no | The minimum presence score (Holistic: the landmark confidence of each part). | MediaPipe Tasks default |
| `min_tracking_confidence` | `float` | >= 0.0, <= 1.0 | `0.5` | no | The minimum tracking score in VIDEO mode. Holistic has no tracking option. | MediaPipe Tasks default |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `image` | input | `image` |
| `keypoints` | output | `keypoints` |
<!-- /node-table:ports -->

The node gives the three generic thresholds to the options of the landmarker of its `variant`. The option names are those of MediaPipe 0.10.33 (`mediapipe/tasks/python/vision/*_landmarker.py`):

| `variant` | `min_detection_confidence` | `min_presence_confidence` | `min_tracking_confidence` |
|---|---|---|---|
| `pose` | `min_pose_detection_confidence` | `min_pose_presence_confidence` | `min_tracking_confidence` |
| `hand` | `min_hand_detection_confidence` | `min_hand_presence_confidence` | `min_tracking_confidence` |
| `face` | `min_face_detection_confidence` | `min_face_presence_confidence` | `min_tracking_confidence` |
| `holistic` | `min_face_detection_confidence`, `min_pose_detection_confidence` | `min_face_landmarks_confidence`, `min_pose_landmarks_confidence`, `min_hand_landmarks_confidence` | none |

- `max_instances` sets `num_poses`, `num_hands` or `num_faces`. `HolisticLandmarkerOptions` has no such option.
- `HolisticLandmarkerOptions` has no tracking option. The node ignores `min_tracking_confidence` for the variant `holistic`.
- The other options of a landmarker keep their Tasks defaults, for example `min_face_suppression_threshold` and `min_pose_suppression_threshold` of Holistic.
- `pose_model` selects the asset `pose_landmarker_lite`, `pose_landmarker_full` or `pose_landmarker_heavy` (`skellytracker/core/detectors/keypoint_detectors/mediapipe/mediapipe_model_manager.py`).

## Behaviour

- The running mode of the landmarker follows the `running_mode` of the run: `IMAGE` for `image`, and `VIDEO` for `video` and `live` ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) items 2 and 5).
- In `VIDEO` mode the node is stateful. In `video` mode, a pipeline with this node upstream of a detector node thus runs at batch = camera count ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 5).
- The output is one `keypoints` set with `max_instances` rows, in the instance format of [ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1. Each point name has a prefix:

  | `variant` | Point names | Points |
  |---|---|---|
  | `pose` | `<node id>.<name>` | 33 |
  | `hand` | `<node id>.<name>` | 21 |
  | `face` | `<node id>.face_0000` to `<node id>.face_0477` | 478 |
  | `holistic` | `body.<name>`, then `left_hand.<name>`, then `right_hand.<name>`, then `face.face_0000` to `face.face_0477` | 33 + 21 + 21 + 478 |

- The body names are the `tracked_points` of `body/mediapipe_body.yaml`. The hand names are the `tracked_points` of `hands/mediapipe_hand.yaml`. A face name is `face_` and the four-digit index of the point, as in `face/mediapipe_face_contour.yaml`. These files are in `skellytracker/core/detectors/keypoint_detectors/mediapipe/`.
- The 478 face points include the 10 iris points. They hold each point of the 136-point face contour subset ([ADR-8NVD](../../../decisions/entries/8NVD-pipeline-api-warnings-and-catalog.md) Reason; [ADR-MSH0](../../../decisions/entries/MSH0-supported-platforms-v2.md)).
- The variant `holistic` is single person ([ADR-8NVD](../../../decisions/entries/8NVD-pipeline-api-warnings-and-catalog.md) item 4).
- The node has no ROI input in v1. An ROI input is open work ([ADR-8NVD](../../../decisions/entries/8NVD-pipeline-api-warnings-and-catalog.md) item 4).
- The node does not use an execution provider. It ignores the EP of the run (`MediapipeTasksParams` in `specs/pipeline/reference/pipeline_config.py` has no `execution_provider`).
- The timing point is `run` ([ADR-Q59W](../../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 1).

## Validation rules

- [ ] `V-node.mediapipe_tasks-1` The variant `holistic` is single person. When `variant` is `holistic`, `max_instances` must be 1.

## Implementer guidance

- In `VIDEO` mode, the node must give strictly increasing timestamps to the landmarker. On Windows with Python 3.11 or 3.12, `int(time.monotonic() * 1000)` can give the same value for two frames. `time.monotonic()` then uses `GetTickCount64()`, with steps of 15.625 ms. MediaPipe then raises `ValueError: Input timestamp must be monotonically increasing` ([ADR-MSH0](../../../decisions/entries/MSH0-supported-platforms-v2.md) Evidence; [ADR-EM74](../../../decisions/entries/EM74-stage-order-and-ci-models.md) item 6).
- The node must close its landmarker safely, also when the garbage collector frees the node. On Python 3.12, `PoseLandmarker.__del__` → `close()` can wait for a MediaPipe dispatcher future that does not complete, and the process hangs at exit ([ADR-MSH0](../../../decisions/entries/MSH0-supported-platforms-v2.md) Evidence; [ADR-EM74](../../../decisions/entries/EM74-stage-order-and-ci-models.md) item 6; [ADR-8NVD](../../../decisions/entries/8NVD-pipeline-api-warnings-and-catalog.md) item 4).
- In `live` mode, the temporal nodes use `timestamp_ms` of the frame, and `frame_number` can skip ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 2).
- The cameras stay separate ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1). In `VIDEO` mode, each camera thus needs its own landmarker state and its own timestamp sequence.
- The output connections come from the MediaPipe YAML files ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).

## Authoring guidance

- The built-in `mediapipe-holistic-tasks` uses the variant `holistic`. It has no keypoint parity with the old MediaPipe builders ([ADR-8NVD](../../../decisions/entries/8NVD-pipeline-api-warnings-and-catalog.md) items 3 and 4).
- For a face on the full frame, prefer `holistic` to `face`. Holistic found a small face on the full frame where `FaceLandmarker` found none ([ADR-8NVD](../../../decisions/entries/8NVD-pipeline-api-warnings-and-catalog.md) Reason).

## Examples

```yaml
nodes:
  - id: holistic
    type: mediapipe_tasks
    inputs: {image: frame.image}
    params:
      variant: holistic
outputs:
  keypoints: holistic.keypoints
```

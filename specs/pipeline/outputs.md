---
id: pipeline.outputs
title: Outputs
kind: pipeline
vectors: null
status: {spec: draft}
---

# Outputs

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The `outputs` block maps public output names to ports. For each call, the run gives one result for each camera of the call. The result holds the value of each output, with an instance dimension. The output schema describes each output before frame 0 ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `outputs` | mapping | yes | Public output name (a name) to port reference (`<node>.<port>`), with no `@prev`. The frame port `frame.image` is not an output. |

`I` is the number of instance rows. `P` is the number of points ([README](README.md#terms)). [Graph](graph.md#behaviour) item 8 gives the instance rows.

The value of a `keypoints` port (`InstanceKeypoints`):

| Field | Shape | Description |
|-------|-------|-------------|
| `point_names` | `(P,)` | The point names, with the prefix that [Graph](graph.md#behaviour) item 7 gives, for example `body.nose`. |
| `xyz` | `(I, P, 3)` | The coordinates of each point, in source-image pixels. z is NaN for a `2d` output. For a `3d` output, z is the root-relative depth in `depth_unit`, as the sidecar [`keypoint.geometry`](../model-sidecar/post/keypoint/schema.md#fields) gives it. A missing point is NaN. |
| `score` | `(I, P)` | The score of each point: the decoded score of the sidecar, with no mapping, or the landmark visibility of MediaPipe. A missing point has 0 ([Decoded keypoints](../model-sidecar/post/keypoint/schema.md#decoded-keypoints)). |
| `instance_score` | `(I,)` | The instance score of each row, from its instance source row ([Graph](graph.md#behaviour) item 8). |
| `present` | `(I,)` | True for a present row, false for a padding row. |
| `track_ids` | `(I,)` | The track id of each row. -1 without an `associate` node. |

The value of a `roi` port:

| Field | Shape | Description |
|-------|-------|-------------|
| `rois` | `(I, 5)` | The ROI of each row, `(cx, cy, w, h, rotation)` in source-image pixels ([Graph](graph.md#behaviour) item 3). |
| `instance_score` | `(I,)` | The instance score of each row, from its instance source row ([Graph](graph.md#behaviour) item 8). |
| `present` | `(I,)` | True for a present row, false for a padding row. |

The value of a `detections` port (`InstanceBoxes`):

| Field | Shape | Description |
|-------|-------|-------------|
| `xyxy` | `(I, 4)` | The box of each row, in source-image pixels. |
| `score` | `(I,)` | The score of each row. |
| `class_index` | `(I,)` | The class index of each row, as the sidecar decode keeps it ([Selection behaviour](../model-sidecar/post/object/decode.md#selection-behaviour) shared step 1). The `class_names` of the output schema give the name of each index. |
| `present` | `(I,)` | True for a present row, false for a padding row. |
| `track_ids` | `(I,)` | The track id of each row. -1 without an `associate` node. |

The values of a padding row:

| Field | Padding value |
|-------|---------------|
| `xyz`, `xyxy`, `rois` | NaN |
| `score`, `instance_score` | 0 |
| `present` | false |
| `track_ids`, `class_index` | -1 |

The result of one camera for one call:

| Field | Description |
|-------|-------------|
| `<output name>` | The value of the output. |
| `frame_index` | The frame index of the call. |
| `image_size` | The size of the source image, `(width, height)` in pixels. |
| `timestamp_ms` | The timestamp of the frame, in milliseconds, as a float ([Running](running.md#behaviour)). |

The output schema gives these fields for each output:

| Field | Description |
|-------|-------------|
| `port_type` | The port type of the output: `keypoints`, `detections` or `roi`. |
| `point_names` | The point names, with the prefix. Only for `keypoints`. |
| `geometry` | `2d` or `3d`, as the sidecar [`keypoint.geometry`](../model-sidecar/post/keypoint/schema.md#fields). Only for `keypoints`. |
| `depth_unit` | `m`, `mm` or `pixel`, as the sidecar [`keypoint.decode.depth_unit`](../model-sidecar/post/keypoint/schema.md#keypointdecode). Only for a `3d` output. |
| `class_names` | The class names of the model, in class index order: [`object.classes`](../model-sidecar/post/object/decode.md#objectclasses) of the sidecar of the detector node that makes the rows. A gap is null. Only for `detections`. |
| `max_instances` | `I`. |
| `tracked` | True when the track ids come from an `associate` node. |
| `instance_source` | The node id of the instance source of the output ([Graph](graph.md#behaviour) item 8). |
| `edges` | The pairs of point names to draw, with the prefix. Only for `keypoints`. |

## Behaviour

1. The run gives the output schema before frame 0 ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).
2. The `edges` come from the [overlay](../model-sidecar/post/keypoint/overlay.md#fields) of the sidecar of the node that makes the points: the skeleton that `keypoint.overlay.skeleton` names, else the first of `keypoint.skeletons`. For a `mediapipe_tasks` node, they come from the MediaPipe YAML files in `core/detectors/keypoint_detectors/mediapipe/` ([ADR-0XW9](../../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 5).
3. Each output has the same shapes on each frame ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).
4. The cameras stay separate. No output joins the values of two cameras ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1). In `live`, a call can hold a subset of the cameras of the run. The run then gives a result only for each camera of the call ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 3).
5. A detector node fills `class_index` in each `detections` row. `gate` and `first_of` pass a `detections` value with its rows unchanged, so they keep `class_index`. No other node type makes or passes a `detections` value.
6. This draft defines the value of a `keypoints` port, a `detections` port and a `roi` port. The value of an output of the port type `image` or `tensor` is not fixed yet ([open work](decisions/open-work.md)).

## Validation rules

- [ ] `V-pipeline.outputs-1` Each output name must be a name. Its port reference must name an existing node and an output port of the type of that node. It must not have `@prev`, and it must not be the frame port `frame.image`.
- [ ] `V-pipeline.outputs-2` Each point name of an output must be unique in that output. The host checks this rule at load, with the sidecars.

## Implementer guidance

- The reference model checks `V-pipeline.outputs-1` in `check_structure`. It does not check `V-pipeline.outputs-2`, because the point names come from the sidecars and the MediaPipe assets. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- The result has no adapter to the old `Observation` type ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).

## Authoring guidance

- `I` can be more than 1, also for an output. Without an `associate` node, a row has no identity across frames: row `i` of two frames can be two persons ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).

## Examples

```yaml
outputs:
  wholebody: wholebody.keypoints
  person_box: person.detections
```

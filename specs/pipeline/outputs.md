---
id: pipeline.outputs
title: Outputs
kind: pipeline
vectors: null
status: {spec: draft}
---

# Outputs

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The `outputs` block maps public output names to ports. For each call, the run gives one result for each camera. The result holds the value of each output, with an instance dimension. The output schema describes each output before frame 0 ([ADR-99MH](../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `outputs` | mapping | yes | Public output name (a name) to port reference (`<node>.<port>`). |

`I` is the number of instance rows. `P` is the number of points. [Graph](graph.md#behaviour) gives the instance rows.

The value of a `keypoints` port (`InstanceKeypoints`):

| Field | Shape | Description |
|-------|-------|-------------|
| `names` | `(P,)` | The point names, with the prefix that [Graph](graph.md#behaviour) gives, for example `body.nose`. |
| `xyz` | `(I, P, 3)` | The coordinates of each point. A missing point is NaN. |
| `visibility` | `(I, P)` | The visibility of each point. A missing point has 0. |
| `present` | `(I,)` | True for a present row, false for a padding row. |
| `track_ids` | `(I,)` | The track id of each row. -1 without an `associate` node. |

The value of a `detections` port (`InstanceBoxes`):

| Field | Shape | Description |
|-------|-------|-------------|
| `xyxy` | `(I, 4)` | The box of each row, in source-image pixels. |
| `confidence` | `(I,)` | The score of each row. |
| `measured` | `(I,)` | A flag for each row. This draft does not fix its meaning. |
| `present` | `(I,)` | True for a present row, false for a padding row. |
| `track_ids` | `(I,)` | The track id of each row. -1 without an `associate` node. |

The result of one camera for one call:

| Field | Description |
|-------|-------------|
| `<output name>` | The value of the output. |
| `frame_number` | The frame number of the call. |
| `image_size` | The size of the source image. |
| `timestamp_ms` | The timestamp of the frame, in milliseconds. |

The output schema gives these fields for each output:

| Field | Description |
|-------|-------------|
| `kind` | The port type of the output: `keypoints` or `detections`. |
| `point_names` | The point names, with the prefix. Only for `keypoints`. |
| `max_instances` | `I`. |
| `tracked` | True when the track ids come from an `associate` node. |
| `root` | The node id of the root of the output ([Graph](graph.md#behaviour)). |
| `connections` | The pairs of point names to draw. Only for `keypoints`. |

## Behaviour

1. The run gives the output schema before frame 0 ([ADR-99MH](../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).
2. The `connections` come from the [overlay](../model-sidecar/post/overlay.md) of the sidecar of the node that makes the points. For a `mediapipe_tasks` node, they come from the MediaPipe YAML files in `core/detectors/keypoint_detectors/mediapipe/` ([ADR-AQR4](../../decisions/entries/AQR4-detectors-and-pipelines-entry-points.md) item 5).
3. Each output has the same shapes on each frame ([ADR-99MH](../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).
4. The cameras stay separate. No output joins the values of two cameras ([ADR-99MH](../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).
5. This draft defines the value of a `keypoints` port and of a `detections` port. The value of an output of another port type is not fixed yet.

## Validation rules

- [ ] `V-pipeline.outputs-1` Each output name must be a name. Its port reference must name an existing node and an output port of the type of that node, or the frame port `frame.image`.
- [ ] `V-pipeline.outputs-2` Each point name of an output must be unique in that output. Two outputs must not give the same point name after the prefix is removed. The host checks this rule at load, with the sidecars.

## Implementer guidance

- The reference model checks `V-pipeline.outputs-1` in `check_structure`. It does not check `V-pipeline.outputs-2`, because the point names come from the sidecars and the MediaPipe assets. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- The result has no adapter to the old `Observation` type ([ADR-99MH](../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).

## Authoring guidance

- This version runs with `I = 1` ([ADR-99MH](../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).

## Examples

```yaml
outputs:
  wholebody: wholebody.keypoints
  person_box: person.detections
```

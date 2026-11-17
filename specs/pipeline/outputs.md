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
| `point_names` | `(P,)` | The point names `<group>/<point>` ([Graph](graph.md#behaviour) item 7), for example `body/nose`. |
| `xy` | `(I, P, 2)` | x and y of each point, in source-image pixels. A missing point is NaN. |
| `z` | `(I, P)` | Only for a `3d` output: the root-relative depth of each point in `depth_unit`, as the sidecar [`keypoint.geometry`](../model-sidecar/post/keypoint/schema.md#fields) gives it. A missing point is NaN. A `2d` output has no `z`. |
| `geometry` | none | `2d` or `3d`: the `geometry` of the output schema. A consumer needs no schema to know if the value has `z` ([ADR-JHB3](../../decisions/entries/JHB3-keypoints-xy-and-z-and-image-width-and-height.md)). |
| `score` | `(I, P)` | The score of each point. When the size of the sidecar has a [score map](../model-sidecar/post/keypoint/score-map.md#behaviour), it is the mapped score, a value in `[0, 1]`. Else it is the decoded score of the sidecar. For a `mediapipe_tasks` node, it is the landmark visibility of MediaPipe. A missing point has 0 ([Decoded keypoints](../model-sidecar/post/keypoint/schema.md#decoded-keypoints); [ADR-PX6Z](../../decisions/entries/PX6Z-keypoint-raw-score-in-the-pipeline-result.md)). |
| `raw_score` | `(I, P)` | The score of each point before the score map: the decode score of the sidecar. When the size of the sidecar has no score map, and for a `mediapipe_tasks` node, it is equal to `score`. A missing point has 0 ([Behaviour](#behaviour) item 9; [ADR-PX6Z](../../decisions/entries/PX6Z-keypoint-raw-score-in-the-pipeline-result.md)). |
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
| `xy`, `z` (only for a `3d` output), `xyxy`, `rois` | NaN |
| `score`, `raw_score`, `instance_score` | 0 |
| `present` | false |
| `track_ids`, `class_index` | -1 |

The result of one camera for one call:

| Field | Description |
|-------|-------------|
| `<output name>` | The value of the output. |
| `frame_index` | The frame index of the call. |
| `image_width` | The width of the source image, in pixels. |
| `image_height` | The height of the source image, in pixels. |
| `timestamp_ms` | The timestamp of the frame, in milliseconds, as a float ([Running](running.md#behaviour)). |
| `node_ran` | A mapping of node id to a boolean, with one key for each inference node of the file ([README](README.md#terms)). The value is true when the node ran for this camera on this frame ([Behaviour](#behaviour) item 8). |

The output schema gives these fields for each output:

| Field | Description |
|-------|-------------|
| `port_type` | The port type of the output: `keypoints`, `detections` or `roi`. |
| `point_names` | The point names, `<group>/<point>`. Only for `keypoints`. |
| `groups` | The groups of the points, in column order: a list of `{name, start, count, landmark_schema}`. Group `k` holds the columns `start` to `start + count - 1`. The first group starts at 0, each next group starts where the previous group ends, and the counts sum to `P`. `landmark_schema` is the name of a registered landmark schema, or null for a group of a `mediapipe_tasks` node and for a `merge` slot that adds such a group ([Graph](graph.md#behaviour) item 7; [ADR-4MP6](../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md)). Only for `keypoints`. |
| `canonical_names` | The point names of the canonical form of the output ([Behaviour](#behaviour) item 7). Only for `keypoints`. |
| `geometry` | `2d` or `3d`, as the sidecar [`keypoint.geometry`](../model-sidecar/post/keypoint/schema.md#fields). Only for `keypoints`. |
| `depth_unit` | `m`, `mm` or `pixel`, as the sidecar [`keypoint.decode.depth_unit`](../model-sidecar/post/keypoint/schema.md#keypointdecode). Only for a `3d` output. |
| `class_names` | The class names of the model, in class index order: [`object.classes`](../model-sidecar/post/object/decode.md#objectclasses) of the sidecar of the `onnx_model` node that makes the rows. A gap is null. Only for `detections`. |
| `max_instances` | `I`. |
| `tracked` | True when the track ids come from an `associate` node. |
| `instance_source` | The node id of the instance source of the output ([Graph](graph.md#behaviour) item 8). |
| `edges` | The pairs of point names to draw, `<group>/<point>`. Only for `keypoints`. |
| `canonical_edges` | The pairs of `edges`, with each point name in its canonical form. An edge with a point that has no canonical name is left out ([Behaviour](#behaviour) item 7). Only for `keypoints`. |

## Behaviour

1. The run gives the output schema before frame 0 ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).
2. The `edges` come from the [overlay](../model-sidecar/post/keypoint/overlay.md#fields) of the sidecar of the node that makes the points: the skeleton that `keypoint.overlay.skeleton` names, else the first of `keypoint.skeletons`. For a `mediapipe_tasks` node, they come from the MediaPipe YAML files in `core/detectors/keypoint_detectors/mediapipe/` ([ADR-0XW9](../../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 5). Each name of an edge gets the group of its point: `<group>/<point>`. An edge with a name of `keypoint.derived_points` is not in `edges`, because a derived point has no column ([ADR-4MP6](../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md)). A `merge` node keeps the edges of `target` and adds the edges of each adding slot ([Node: merge](nodes/merge.md#behaviour) item 8; [ADR-KW76](../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 3).
3. Each output has the same shapes on each frame ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).
4. The cameras stay separate. No output joins the values of two cameras ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1). In `live`, a call can hold a subset of the cameras of the run. The run then gives a result only for each camera of the call ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 3).
5. An `onnx_model` node fills `class_index` in each `detections` row. `gate` and `first_of` pass a `detections` value with its rows unchanged, so they keep `class_index`. No other node type makes or passes a `detections` value.
6. This draft defines the value of a `keypoints` port, a `detections` port and a `roi` port. The value of an output of the port type `image` or `tensor` is not fixed yet ([open work](decisions/open-work.md)).
7. **Canonical form.** The canonical form maps the groups that one node or one `merge` slot made together, with the canonical mapping of their schema ([Canonical mapping](../model-sidecar/post/keypoint/canonical-mapping.md#behaviour)). These are the groups with one `landmark_schema`. A schema with two or more groups comes from one node, because group names are unique in a file (`V-pipeline.graph-10`). A group of a schema with one group stands alone. For example, the region `body` of `COCO_WholeBody` reads the toes of the group `feet` of the same node. Each canonical region comes from at most one group: the group with its name. A group with a null `landmark_schema` passes through. `canonical_names` gives the names in the order of that section. The run gives `canonical_names` before frame 0. No param selects the canonical form ([ADR-4MP6](../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md) items 6 and 7). The canonical form has `xy`, and it has `z` only for a `3d` output. It has `score` and no `raw_score` (item 9) ([ADR-JHB3](../../decisions/entries/JHB3-keypoints-xy-and-z-and-image-width-and-height.md)). `canonical_edges` gives the pairs of `edges` in canonical names, in the order of `edges`. Each point that the canonical form copies or renames has a canonical name. A point with two or more canonical names takes the first of them in `canonical_names`. A computed canonical point, for example a centre point, is in no edge. `canonical_edges` leaves out an edge with a point that has no canonical name, an edge whose two points get the same canonical name, and a pair that an earlier edge gave, also in the other direction. The run gives `canonical_edges` before frame 0 ([ADR-QD6G](../../decisions/entries/QD6G-canonical-edges-in-the-output-schema.md)).
8. **`node_ran`.** An inference node ran for a camera when it did an inference on the frame of that camera in this call. A node that got an empty required input did not run ([Graph](graph.md#behaviour) item 6). A node that the run does not use, or whose outputs are all replayed, did not run ([Running](running.md#behaviour) item 9). A padded batch item is not a run ([Running](running.md#behaviour) item 4). A node that ran and found no instance has the value true, and its outputs are empty. A node that did not run has the value false. The run gives `node_ran` also when the timing is off ([ADR-Q5BN](../../decisions/entries/Q5BN-node-ran-in-the-camera-result.md)).
9. **`raw_score`.** Each node that copies, moves, holds or passes the score of a point does the same with its `raw_score`. Each node that sets the score of a point to 0 also sets its `raw_score` to 0. A missing point thus has the score 0 and the `raw_score` 0. A point of a model with a score map can have the score `0.0` and a `raw_score` greater than 0: the mapped score of a present point can round to `0.0` in float32 ([Keypoint score map](../model-sidecar/post/keypoint/score-map.md#behaviour)). Thus the canonical form takes a point as missing when its `raw_score` is 0 or less, not from its score. A mean or a weighted canonical point uses this rule for its sources, and its score is the minimum of the scores of its sources. The canonical form has no `raw_score`: a computed canonical point has no decode score, and the sidecar gives the score of a derived point only from the mapped scores ([Decoded keypoints](../model-sidecar/post/keypoint/schema.md#decoded-keypoints)) ([ADR-PX6Z](../../decisions/entries/PX6Z-keypoint-raw-score-in-the-pipeline-result.md)).

## Validation rules

- [ ] `V-pipeline.outputs-1` Each output name must be a name. Its port reference must name an existing node and an output port of the type of that node. It must not have `@prev`, and it must not be the frame port `frame.image`.
- [ ] `V-pipeline.outputs-2` Each point name of an output must be unique in that output. The host checks this rule at load, with the sidecars.
- [ ] `V-pipeline.outputs-3` An output name must not be `frame_index`, `image_width`, `image_height`, `timestamp_ms` or `node_ran`. The result of a camera holds these fields next to the outputs ([ADR-Q5BN](../../decisions/entries/Q5BN-node-ran-in-the-camera-result.md); [ADR-JHB3](../../decisions/entries/JHB3-keypoints-xy-and-z-and-image-width-and-height.md)).

## Implementer guidance

- The reference model checks `V-pipeline.outputs-1` and `V-pipeline.outputs-3` in `check_structure`. It does not check `V-pipeline.outputs-2`, because the point names come from the sidecars and the MediaPipe assets. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- The result has no adapter to the old `Observation` type ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).

## Authoring guidance

- `I` can be more than 1, also for an output. Without an `associate` node, a row has no identity across frames: row `i` of two frames can be two persons ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).

- This version tracks one person ([ADR-TH8E](../../decisions/entries/TH8E-one-person-in-v2.md)). To read that person, read row 0. Check `present[0]` first, because a padding row has NaN in `xy` ([ADR-JHB3](../../decisions/entries/JHB3-keypoints-xy-and-z-and-image-width-and-height.md)):

  ```python
  body = result["wholebody"]
  if body.present[0]:
      nose_x, nose_y = body.xy[0, body.point_names.index("body/nose")]
  ```

- A consumer must take a point by its name or by `groups`. It must not use a fixed column index. `point_names` has the names of the exporter, which can differ between two models of one body region. `canonical_names` has names that do not depend on the model. Use the canonical form to map points to an application skeleton. The canonical form can have a different point count and order from `point_names`. For example, the output `wholebody` of `yolox-rtmw-wholebody` has 133 point names in 5 groups and 137 canonical names:

  | `point_names` | Group in `groups` | `canonical_names` |
  |---------------|-------------------|-------------------|
  | `left_hand/left_thumb1` | `left_hand` | `left_hand/thumb_cmc` |
  | `left_hand/left_hand_root` | `left_hand` | `left_hand/wrist` |
  | `feet/left_big_toe` | `feet` | `body/left_big_toe` |
  | `face/face-0` | `face` | `face/face-0` |

  The canonical form has no group `feet`: the region `body` holds the toes and the heels. It adds four computed points, for example `body/neck_center`. (skellytracker `skellytracker/core/model_zoo/landmark_schemas/COCO_WholeBody.yaml`, `canonical_mapping`; `skellytracker/core/pipelines/canonical.py`, `to_canonical`)

## Examples

```yaml
# The outputs of `yolox-rtmw-wholebody`. `person_roi` is the smoothed crop ROI of each frame.
outputs:
  wholebody: wholebody.keypoints
  person_box: person.detections
  person_roi: crop.rois
```

```yaml
# The groups of the output schema of `wholebody` (yolox-rtmw-wholebody)
groups:
  - {name: body, start: 0, count: 17, landmark_schema: COCO_WholeBody}
  - {name: feet, start: 17, count: 6, landmark_schema: COCO_WholeBody}
  - {name: face, start: 23, count: 68, landmark_schema: COCO_WholeBody}
  - {name: left_hand, start: 91, count: 21, landmark_schema: COCO_WholeBody}
  - {name: right_hand, start: 112, count: 21, landmark_schema: COCO_WholeBody}
```

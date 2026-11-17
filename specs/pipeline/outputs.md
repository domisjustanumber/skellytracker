---
id: pipeline.outputs
title: Outputs
kind: pipeline
vectors: null
status: {spec: draft}
---

# Outputs

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The `outputs` block names the delivered outputs of a pipeline. It is a block of the pipeline file, not a node type. Each file must have it. Its only keys are `wholebody`, `holistic` and `boxes`. The run converts the value of each named port to its delivered form at this block. For each call, the run gives one result for each camera of the call. The result holds the delivered value of each key, with an instance dimension. The output schema describes each delivered value before frame 0 ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1; [ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 14).

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `outputs` | mapping | yes | One key or more of `wholebody`, `holistic` and `boxes`. Each key names a port reference `<node>.<port>`, with no `@prev`. The block has no other key. |

The keys of the block:

| Key | Port type | Checked at load | Delivered value |
|-----|-----------|-----------------|-----------------|
| `wholebody` | `keypoints` | The port has a group `body`. A group with a null `landmark_schema` gives the load warning `output_group_without_landmark_schema`. | `CanonicalKeypoints`: the canonical form of the value, with the canonical point names ([Behaviour](#behaviour) item 7). A group with a null `landmark_schema` passes through with its names. |
| `holistic` | `keypoints` | The groups of the port are exactly `body`, `right_hand`, `left_hand` and `face`, in this order. | `CanonicalKeypoints`: the canonical form of the value. The groups of a `mediapipe_tasks` node have a null `landmark_schema`, so each name passes through. |
| `boxes` | `boxes` | The port cannot hold a rotated box (`V-pipeline.outputs-5`). | `OutputBoxes`: the upright corners of each box, with `detector_ran` ([Behaviour](#behaviour) item 6). |

A file can thus give at most one `boxes` output. A `record` tap gives the value of each other port ([Taps](taps.md)).

`I` is the number of instance rows. `P` is the number of points ([README](README.md#terms)). `C` is the number of canonical points. [Graph](graph.md#behaviour) item 8 gives the instance rows.

The value of a `keypoints` port (`InstanceKeypoints`). The ports and the taps hold this value. The result does not hold it:

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

The value of a `boxes` port (`InstanceBoxes`; [ADR-2RWC](../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md)). The ports and the taps hold this value. The result does not hold it:

| Field | Shape | Description |
|-------|-------|-------------|
| `boxes` | `(I, 5)` | The box of each row, `(cx, cy, w, h, rotation)` in source-image pixels ([Graph](graph.md#behaviour) item 3). |
| `instance_score` | `(I,)` | The instance score of each row, from its instance source row ([Graph](graph.md#behaviour) item 8). For an object detector, it is the detection score. |
| `class_index` | `(I,)` | The class index of each row, as the sidecar decode keeps it ([Selection behaviour](../model-sidecar/post/object/decode.md#selection-behaviour) shared step 1). -1 when no detector made the row. The `class_names` of the output schema give the name of each index. |
| `present` | `(I,)` | True for a present row, false for a padding row. |
| `track_ids` | `(I,)` | The track id of each row. -1 without an `associate` node. |

The delivered value of `wholebody` and `holistic` (`CanonicalKeypoints`; [ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 15):

| Field | Shape | Description |
|-------|-------|-------------|
| `point_names` | `(C,)` | The canonical point names: the `point_names` of the output schema ([Behaviour](#behaviour) item 7). |
| `xy` | `(I, C, 2)` | x and y of each point, in source-image pixels. A missing point is NaN. |
| `z` | `(I, C)` | Only for a `3d` output, as `z` of a `keypoints` value. A `2d` output has no `z`. |
| `geometry` | none | `2d` or `3d`, as `geometry` of a `keypoints` value. |
| `score` | `(I, C)` | The score of each point. A missing point has 0. |
| `groups` | list | The groups that pass through, with `start` and `count` in the canonical columns: the `groups` of the output schema. |
| `present` | `(I,)` | The `present` of each row of the port value. |
| `instance_score` | `(I,)` | The `instance_score` of each row of the port value. |

The delivered keypoints have no `raw_score` and no `track_ids`. The ports and the taps keep `raw_score`.

The delivered value of `boxes` (`OutputBoxes`; [ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) items 16 and 17):

| Field | Shape | Description |
|-------|-------|-------------|
| `xyxy` | `(I, 4)` | The corners `(x1, y1, x2, y2)` of each box, in source-image pixels, float64 ([Behaviour](#behaviour) item 6). The pipeline does not clip a box. |
| `score` | `(I,)` | The `instance_score` of the row. |
| `class_index` | `(I,)` | The `class_index` of the row. |
| `present` | `(I,)` | The `present` of the row. |
| `detector_ran` | `(I,)` | True when the instance source node of the boxes ran for this camera on this frame ([Behaviour](#behaviour) item 10). Each row has the same value, also a padding row. |

`OutputBoxes` has no rotation and no `track_ids`.

The values of a padding row:

| Field | Padding value |
|-------|---------------|
| `xy`, `z` (only for a `3d` output), `boxes`, `xyxy` | NaN |
| `score`, `raw_score`, `instance_score` | 0 |
| `present` | false |
| `track_ids`, `class_index` | -1 |

The result of one camera for one call:

| Field | Description |
|-------|-------------|
| `wholebody`, `holistic`, `boxes` | The delivered value of each key of the `outputs` block. The result has only the keys of the block. |
| `frame_index` | The frame index of the call. |
| `image_width` | The width of the source image, in pixels. |
| `image_height` | The height of the source image, in pixels. |
| `timestamp_ms` | The timestamp of the frame, in milliseconds, as a float ([Running](running.md#behaviour)). |
| `node_ran` | A mapping of node id to a boolean, with one key for each inference node of the file ([README](README.md#terms)). The value is true when the node ran for this camera on this frame ([Behaviour](#behaviour) item 8). |

The output schema gives these fields for each key of the block. They describe the delivered value:

| Field | Description |
|-------|-------------|
| `port_type` | The port type of the port of the key: `keypoints` or `boxes`. |
| `point_names` | The canonical point names, `<group>/<point>` ([Behaviour](#behaviour) item 7). Only for `keypoints`. |
| `groups` | The groups that pass through the canonical form, in column order: a list of `{name, start, count, landmark_schema}`. Group `k` holds the canonical columns `start` to `start + count - 1`. `landmark_schema` is the name of a registered landmark schema, or null for a group of a `mediapipe_tasks` node and for an `assign_keypoints` slot or a `merge` part that adds such a group ([Graph](graph.md#behaviour) item 7; [ADR-4MP6](../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md)). A group that the canonical mapping maps is not in the list. Only for `keypoints`. |
| `geometry` | `2d` or `3d`, as the sidecar [`keypoint.geometry`](../model-sidecar/post/keypoint/schema.md#fields). Only for `keypoints`. |
| `depth_unit` | `m`, `mm` or `pixel`, as the sidecar [`keypoint.decode.depth_unit`](../model-sidecar/post/keypoint/schema.md#keypointdecode). Only for a `3d` output. |
| `class_names` | The class names of the model, in class index order: [`object.classes`](../model-sidecar/post/object/decode.md#objectclasses) of the sidecar of the object detector that made the boxes, or null ([Behaviour](#behaviour) item 5). A gap is null. Only for `boxes`. |
| `max_instances` | `I`. |
| `tracked` | True when the track ids come from an `associate` node. |
| `instance_source` | The node id of the instance source of the port ([Graph](graph.md#behaviour) item 8). For `boxes`, `detector_ran` is the `node_ran` of this node. |
| `edges` | The pairs of canonical point names to draw, `<group>/<point>` ([Behaviour](#behaviour) items 2 and 7). Only for `keypoints`. |

## Behaviour

1. The run gives the output schema before frame 0 ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).
2. The `edges` of a `keypoints` port come from the [overlay](../model-sidecar/post/keypoint/overlay.md#fields) of the sidecar of the node that makes the points: the skeleton that `keypoint.overlay.skeleton` names, else the first of `keypoint.skeletons`. For a `mediapipe_tasks` node, they come from the MediaPipe YAML files in `core/detectors/keypoint_detectors/mediapipe/` ([ADR-0XW9](../../decisions/entries/0XW9-entry-points-layout-guard-test-and-session-code.md) item 5). Each name of an edge gets the group of its point: `<group>/<point>`. An edge with a name of `keypoint.derived_points` is not in `edges`, because a derived point has no column ([ADR-4MP6](../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md)). An `assign_keypoints` node keeps the edges of `target` and adds the edges of each adding slot ([Node: assign keypoints](nodes/assign_keypoints.md#behaviour) item 8; [ADR-KW76](../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 3). A `merge` node keeps the edges of `body` and adds the edges of each part that adds a group ([Node: merge](nodes/merge.md#behaviour) item 8). The output schema gives these edges in canonical names (item 7).
3. Each output has the same shapes on each frame ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).
4. The cameras stay separate. No output joins the values of two cameras ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1). In `live`, a call can hold a subset of the cameras of the run. The run then gives a result only for each camera of the call ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 3).
5. An `onnx_model` node gives the `class_names` of its sidecar to its `boxes` output. `boxes_from_points` gives null. Each other node that passes a `boxes` value keeps the `class_names` of its input. `first_of` keeps those of its first input ([ADR-2RWC](../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md)).
6. **Delivered values.** The run converts the value of each key after each node ran ([ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) items 14 to 17):
   - `wholebody` and `holistic` give the canonical form of the `keypoints` value (item 7), with the `present` and the `instance_score` of each row. For `wholebody`, the load gives the warning `output_group_without_landmark_schema` for each group of the port with a null `landmark_schema` ([Running](running.md#behaviour) item 8). `holistic` gives no such warning.
   - `boxes` gives the corners `xyxy = (cx - w/2, cy - h/2, cx + w/2, cy + h/2)` of each row. The conversion changes nothing else: the load proved that the box has no rotation (`V-pipeline.outputs-5`). A padding row stays NaN. The pipeline does not clip a box ([ADR-RA0E](../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 6).
   - The block has no key for a `flag` port and no key for an image. A flag and an image are not outputs.
   - The conversion has no timing span. Its time is in the time of the call, not in a node span.
7. **Canonical form.** The canonical form maps the groups that one node or one `assign_keypoints` slot made together, with the canonical mapping of their schema ([Canonical mapping](../model-sidecar/post/keypoint/canonical-mapping.md#behaviour)). These are the groups with one `landmark_schema`. A schema with two or more groups comes from one node, because group names are unique in a file (`V-pipeline.graph-10`). A group of a schema with one group stands alone. For example, the region `body` of `COCO_WholeBody` reads the toes of the group `feet` of the same node. Each canonical region comes from at most one group: the group with its name. A group with a null `landmark_schema` passes through. The `point_names` of the output schema give the canonical names in the order of that section. The run gives them before frame 0. No param selects the canonical form ([ADR-4MP6](../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md) items 6 and 7). The canonical form has `xy`, and it has `z` only for a `3d` output. It has `score` and no `raw_score` (item 9) ([ADR-JHB3](../../decisions/entries/JHB3-keypoints-xy-and-z-and-image-width-and-height.md)). The `edges` of the output schema are the pairs of the `edges` of the port in canonical names, in the order of the `edges` of the port. Each point that the canonical form copies or renames has a canonical name. A point with two or more canonical names takes the first of them in the canonical names. A computed canonical point, for example a centre point, is in no edge. The `edges` leave out an edge with a point that has no canonical name, an edge whose two points get the same canonical name, and a pair that an earlier edge gave, also in the other direction ([ADR-QD6G](../../decisions/entries/QD6G-canonical-edges-in-the-output-schema.md)). The output schema has no `canonical_names` and no `canonical_edges`: `point_names` and `edges` give them ([ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 14).
8. **`node_ran`.** An inference node ran for a camera when it did an inference on the frame of that camera in this call. A node that got an empty required input, or a `run_if` input that is false, did not run ([Graph](graph.md#behaviour) item 6). A node that the run does not use, or whose outputs are all replayed, did not run ([Running](running.md#behaviour) item 9). A padded batch item is not a run ([Running](running.md#behaviour) item 4). A node that ran and found no instance has the value true, and its outputs are empty. A node that did not run has the value false. The run gives `node_ran` also when the timing is off ([ADR-Q5BN](../../decisions/entries/Q5BN-node-ran-in-the-camera-result.md)).
9. **`raw_score`.** Each node that copies, moves, holds or passes the score of a point does the same with its `raw_score`. Each node that sets the score of a point to 0 also sets its `raw_score` to 0. A missing point thus has the score 0 and the `raw_score` 0. A point of a model with a score map can have the score `0.0` and a `raw_score` greater than 0: the mapped score of a present point can round to `0.0` in float32 ([Keypoint score map](../model-sidecar/post/keypoint/score-map.md#behaviour)). Thus the canonical form takes a point as missing when its `raw_score` is 0 or less, not from its score. A mean or a weighted canonical point uses this rule for its sources, and its score is the minimum of the scores of its sources. The canonical form has no `raw_score`: a computed canonical point has no decode score, and the sidecar gives the score of a derived point only from the mapped scores ([Decoded keypoints](../model-sidecar/post/keypoint/schema.md#decoded-keypoints)) ([ADR-PX6Z](../../decisions/entries/PX6Z-keypoint-raw-score-in-the-pipeline-result.md)).
10. **`detector_ran`.** Each `boxes` port has an instance source: the inference node whose rows the boxes follow ([Graph](graph.md#behaviour) item 8). The output schema gives it as `instance_source`. For each row of the delivered `boxes`, `detector_ran` is the `node_ran` of that node for this camera on this frame (item 8). All rows of one value have one instance source, so all rows have the same `detector_ran`. Thus `detector_ran` is true on a frame on which the detector ran, also when it found no instance. It is false on a frame on which the box comes from another node, for example from the points of the previous frame, and in a replay of each output of the detector. An application reads `detector_ran` and needs no node id ([ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 16).
11. **Rotated box.** The load refuses a file whose `outputs.boxes` can hold a rotated box. The output never changes a box ([ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 17). The load finds it in this way:
    - Only [`boxes_from_points`](nodes/boxes_from_points.md#behaviour) with a `target_rotation_deg` gives a rotation that is not 0 (step 6). `target_rotation_deg: 0` also gives a rotation, from the two alignment points. An object detector gives the rotation 0 ([ADR-2RWC](../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md) item 2).
    - A node that passes a box keeps its rotation: `gate` (the input `value`), `first_of` (each item), `hold_boxes` (the inputs `previous` and `current`) and `smooth_boxes` (the input `boxes`).
    - The load starts at the port of `outputs.boxes`. It follows these inputs, also an `@prev` input, until it finds the node that makes the box. It refuses the file when it finds a `boxes_from_points` node with `target_rotation_deg`. The error names that node.
    - The load does not follow the `condition` of `gate`, the `previous_keypoints` of `hold_boxes`, or the inputs of `boxes_from_points` and of a model node. The rotation of the output of `boxes_from_points` comes only from its own params (steps 6 and 10 of the node).

## Validation rules

- [ ] `V-pipeline.outputs-1` The `outputs` block must have one key or more. Each key must be `wholebody`, `holistic` or `boxes`. Each port reference must name an existing node and an output port of the type of that node. It must not have `@prev`, and it must not be the frame port `frame.image` ([ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 14).
- [ ] `V-pipeline.outputs-2` Each point name of an output must be unique in that output. The host checks this rule at load, with the sidecars.
- [ ] `V-pipeline.outputs-3` Removed. The closed set of keys of `V-pipeline.outputs-1` covers it. Its ID is not used again ([ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 14).
- [ ] `V-pipeline.outputs-4` `wholebody` and `holistic` must name a `keypoints` port, and `boxes` must name a `boxes` port. The `wholebody` value must have a group `body`. The groups of the `holistic` value must be exactly `body`, `right_hand`, `left_hand` and `face`, in this order. The host checks the groups at load, with the sidecars ([ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 14).
- [ ] `V-pipeline.outputs-5` The port of `boxes` must not be able to hold a rotated box ([Behaviour](#behaviour) item 11; [ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 17).

## Implementer guidance

- The reference model checks `V-pipeline.outputs-1`, the port types of `V-pipeline.outputs-4` and `V-pipeline.outputs-5` in `check_structure`. It does not check `V-pipeline.outputs-2` and the groups of `V-pipeline.outputs-4`, because the point names and the groups come from the sidecars and the MediaPipe assets. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- The result has no adapter to the old `Observation` type ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).
- `to_canonical(value, groups)` stays a public function. It gives the canonical form of a `keypoints` value with the `groups` of its port, for example a value that a tap recorded. (skellytracker `skellytracker/core/pipelines/canonical.py`)

## Authoring guidance

- `I` can be more than 1, also for an output. Without an `associate` node, a row has no identity across frames: row `i` of two frames can be two persons ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).

- This version tracks one person ([ADR-TH8E](../../decisions/entries/TH8E-one-person-in-v2.md)). To read that person, read row 0. Check `present[0]` first, because a padding row has NaN in `xy` and in `xyxy` ([ADR-JHB3](../../decisions/entries/JHB3-keypoints-xy-and-z-and-image-width-and-height.md)):

  ```python
  body, boxes = result["wholebody"], result["boxes"]
  if body.present[0]:
      nose_x, nose_y = body.xy[0, body.point_names.index("body/nose")]
  if boxes.present[0]:
      x1, y1, x2, y2 = boxes.xyxy[0]
  detector_ran = bool(boxes.detector_ran[0])
  ```

- A consumer must take a point by its name. It must not use a fixed column index. The delivered `point_names` are canonical names: they do not depend on the model. The canonical form can have a different point count and order from the `point_names` of the port. For example, the port `wholebody.keypoints` of `yolox-rtmw-wholebody` has 133 point names in 5 groups, and the output `wholebody` has 137 canonical names:

  | `point_names` of the port | Group of the port | `point_names` of the output |
  |---------------------------|-------------------|-----------------------------|
  | `left_hand/left_thumb1` | `left_hand` | `left_hand/thumb_cmc` |
  | `left_hand/left_hand_root` | `left_hand` | `left_hand/wrist` |
  | `feet/left_big_toe` | `feet` | `body/left_big_toe` |
  | `face/face-0` | `face` | `face/face-0` |

  The canonical form has no group `feet`: the region `body` holds the toes and the heels. It adds four computed points, for example `body/neck_center`. Only the group `face` passes through, so the output schema gives only `face` in `groups`. (skellytracker `skellytracker/core/model_zoo/landmark_schemas/COCO_WholeBody.yaml`, `canonical_mapping`; `skellytracker/core/pipelines/canonical.py`, `to_canonical`)
- To keep the box of the detector, record a tap on its port, for example `person.boxes` ([Taps](taps.md)). The block gives at most one `boxes` output.

## Examples

```yaml
# The outputs of `yolox-rtmw-wholebody`. `boxes` is the smoothed crop box of each frame.
outputs:
  wholebody: wholebody.keypoints
  boxes: crop.boxes
```

```yaml
# The groups of the port `wholebody.keypoints` of `yolox-rtmw-wholebody` (the resolved facts of the port, not the output schema)
groups:
  - {name: body, start: 0, count: 17, landmark_schema: COCO_WholeBody}
  - {name: feet, start: 17, count: 6, landmark_schema: COCO_WholeBody}
  - {name: face, start: 23, count: 68, landmark_schema: COCO_WholeBody}
  - {name: left_hand, start: 91, count: 21, landmark_schema: COCO_WholeBody}
  - {name: right_hand, start: 112, count: 21, landmark_schema: COCO_WholeBody}
```

```yaml
# The groups of the output schema of `wholebody` (yolox-rtmw-wholebody): only `face` passes through
groups:
  - {name: face, start: 27, count: 68, landmark_schema: COCO_WholeBody}
```

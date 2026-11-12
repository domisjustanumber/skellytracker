---
id: pipeline.graph
title: Graph
kind: pipeline
vectors: null
status: {spec: draft}
---

# Graph

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The graph of a pipeline is a flat list of nodes. Each node has an id, a type and inputs. An input refers to an output port of another node, or to the camera frame. The suffix `@prev` refers to the value of the previous frame. This section gives the node fields, the port types, the ROI type, the empty values, the point names and the instance rows of a port ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) items 4, 6 and 8; [ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `nodes[].id` | name | yes | The node id. It is unique in the file. `pipeline` and `frame` are reserved. |
| `nodes[].type` | enum | yes | A node type of the [section map](README.md#section-map): `detector`, `mediapipe_tasks`, `roi_from_points`, `roi_tracking`, `gate`, `first_of`, `concat`, `merge`, `smooth_keypoints`, `smooth_roi` or `redetect`. |
| `nodes[].inputs` | mapping or list | see the node section | For most types, a mapping of input name to port reference. For `first_of` and `concat`, a list of port references. The node section gives the input names and the required inputs. |
| `nodes[].params` | mapping | see the node section | The params of the node type. The params table of the node section gives each param. A node type with a required param needs `params`. |

A **port reference** is a string `<node>.<port>`, with an optional suffix `@prev`. It matches `^[a-z][a-z0-9_-]*\.[a-z][a-z0-9_]*(@prev)?$`.

The **frame** is the reserved source of the graph. Its one port `frame.image` is the camera frame of the call. It has the type `image`.

The port types:

| Type | Value |
|------|-------|
| `image` | One image of one camera. |
| `roi` | `I` ROI rows ([Behaviour](#behaviour) item 3). |
| `keypoints` | `I` keypoint rows, each with `P` points ([Outputs](outputs.md#fields)). |
| `detections` | `I` box rows, each with one box and a score ([Outputs](outputs.md#fields)). |
| `tensor` | One array. |
| `any` | An input or an output of a `gate` or a `first_of` node. The type of an `any` output comes from the inputs ([Behaviour](#behaviour) item 4). |

The [README](README.md#terms) gives the letter key `I`, `P` and the other letters.

## Behaviour

1. **Order.** The nodes are in any order. A node runs after each node that it takes a same-frame input from.
2. **`@prev`.** An input with `@prev` gets the value of the port on the previous frame that the run processed for the same camera. The value is empty on the first frame. In the running mode `image`, each `@prev` value is empty ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 2). An `@prev` edge does not count for the cycle check. The frame has no `@prev` value.
3. **ROI.** An ROI is `(cx, cy, w, h, rotation)` in source-image pixels: the centre, the width, the height and the rotation. A box is an ROI with rotation 0 ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 8):
   - `rotation` is in radians, in `[-π, π)`. A positive rotation turns the ROI clockwise in the image, because the image y axis points down.
   - The ROI x axis is `(cos(rotation), sin(rotation))` and the ROI y axis is `(-sin(rotation), cos(rotation))`, in image pixels.
   - The positions of points, boxes and ROIs are those of the sidecar [unprojection](../model-sidecar/post/unprojection.md#behaviour). Their pixel centres follow the resize method of the model ([Pixel centres](../model-sidecar/pre/interpolation.md#pixel-centres)). A glue node adds no `0.5` offset and removes none.
   - Only the detector node cuts pixels, always from `frame.image` ([Node: detector](nodes/detector.md#behaviour) gives the crop order).
4. **The type of an `any` output.** The output `value` of a `gate` node has the type of its input `value`. The output `value` of a `first_of` node has the type of its inputs. The load uses this type for `V-pipeline.graph-3`. When an input is also `any`, the load follows it to its own inputs. An `@prev` loop gives no type.
5. **Empty values.** An `image` value is empty when it holds no image. A `roi`, `keypoints` or `detections` value is empty when it has no present row. A `tensor` value is empty when it holds no array.
6. **Empty inputs.** A node that gets an empty required input does not run. Each output of that node is then empty. An empty optional input does not stop a node ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6):
   - The optional inputs are `roi_tracking.previous_keypoints`, `redetect.previous_keypoints` and `redetect.previous_rois`.
   - The `rois` input of a top-down keypoint model is required ([`V-node.detector-2`](nodes/detector.md#validation-rules)).
   - The rule of a node type can also read an empty required input: `gate` reads an empty `condition`, `first_of` skips each empty input, `roi_tracking` reads an empty `previous`, `merge` reads an empty `source`, [`concat`](nodes/concat.md#behaviour) runs with an empty input and gives missing points in its columns, and `smooth_keypoints` counts an empty input as a miss after its first input. The node section gives each such input.
7. **Point names.** Each point name in the graph has a prefix: `<prefix>.<point>` ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6):
   - The prefix is the id of the node that makes the points, for example `left_hand.wrist` from the node `left_hand`.
   - A `mediapipe_tasks` node of the variant `holistic` gives the prefixes `body`, `right_hand`, `left_hand` and `face`, in this order ([Node: MediaPipe Tasks](nodes/mediapipe_tasks.md#behaviour)).
   - A `merge` node gives the prefix of each slot name to the columns of that slot ([Node: merge](nodes/merge.md#behaviour)).
   - The other glue nodes keep the names. An output adds no prefix.
   - Each point name in a param has its prefix, for example `body.left_wrist` (`V-pipeline.graph-8`). A derived point of `roi_from_points` is local to its node and has no prefix.
8. **Instance rows.** Each `roi`, `keypoints` and `detections` value has `I` rows ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1):
   - The **instance source** of a value is the node that makes its instance rows: an object detector, a one-stage model or a `mediapipe_tasks` node. `I` is the `max_instances` of the instance source. `I` is fixed for the run. Each frame has the same shapes. `I` can be more than 1.
   - The present rows come first, in descending order of the instance score: the `score` of the `detections` row of an object detector or a one-stage model. Each present row of a `mediapipe_tasks` node has the instance score 1.0, so its rows keep the order of MediaPipe. A tie goes to the lower row index, as in the sidecar [selection behaviour](../model-sidecar/post/object/decode.md#selection-behaviour). The padding rows come last. A padding row has `present` false.
   - A missing point has NaN coordinates and the score 0 ([Decoded keypoints](../model-sidecar/post/keypoint/schema.md#decoded-keypoints)).
   - No row and no point is dropped.
   - A node that takes ROIs runs once for each present row. Its output row `i` comes from the ROI row `i`. A padding row stays a padding row. The output has the instance source of the ROI input.
   - Each `roi` and `keypoints` row carries the `instance_score` of its instance source row. No other node changes it. The instance source sets it: an object detector or a one-stage model gives the detection score of the row, the `score` of its `detections` row after the sidecar [object decode](../model-sidecar/post/object/decode.md#selection-behaviour). A `mediapipe_tasks` node gives 1.0 for each present row, because the Tasks results have no instance score. The instance score is not a function of the point scores. Each other node copies the value of the row from its input: a top-down keypoint model from its `rois` row, `roi_from_points` from its keypoints row, `smooth_roi`, `smooth_keypoints`, `gate`, `first_of` and `concat` from their input row, and `merge` from its `target` row. A row that `roi_tracking` carries over from `@prev` keeps the instance score of the last frame on which the instance source ran. The value does not decay.
   - `concat` joins row `i` of each input to row `i` of the output. All inputs of `concat` have the same instance source. The inputs of `first_of` also have one instance source.
   - `merge` keeps the instance source and the `I` of its `target` input. Its `source` input can have any instance source and any `I`.
   - A fan-out child adds point columns to the row of its instance. It adds no row. For example, a hand model on the hand ROI of person `i` adds its points to row `i`.
   - Without an `associate` node, each `track_ids` value is -1, and a row has no identity across frames: row `i` of two frames can be two persons. This version has no `associate` node type.

## Validation rules

- [ ] `V-pipeline.graph-1` Each node id must be a name and must be unique in the file. The ids `pipeline` and `frame` are reserved and must not be node ids.
- [ ] `V-pipeline.graph-2` Each input must be a port reference. It must name an existing node and an output port of the type of that node, or the frame port `frame.image` with no `@prev`.
- [ ] `V-pipeline.graph-3` The type of each input must match the type of the port that it refers to, after the load gives each `any` output its type ([Behaviour](#behaviour) item 4). An `any` input matches each type.
- [ ] `V-pipeline.graph-4` The same-frame edges must make no cycle. An `@prev` input is not a same-frame edge.
- [ ] `V-pipeline.graph-5` Each input name must be an input port of the node type. The variadic types `first_of` and `concat` must have a list of port references. The other types must have a mapping.
- [ ] `V-pipeline.graph-6` Each node must have each required input of its type. The list of a `first_of` or `concat` node must have at least one item.
- [ ] `V-pipeline.graph-7` `type` must be a node type of the [section map](README.md#section-map). `params` must agree with the params table of that type: each param name is a param of the type, each value has the type and the range of the param, and each param with no default is present.
- [ ] `V-pipeline.graph-8` Each point name in a param must be `<prefix>.<point>`. The prefix must be a node id of the file, a prefix of a `holistic` node of the file, or a slot name of a `merge` node of the file. A derived point name of a `roi_from_points` node is the only exception. The host also checks at load that each name is a point of the input port.

## Implementer guidance

- `check_structure` in the reference model checks `V-pipeline.graph-1` to `V-pipeline.graph-6` and `V-pipeline.graph-8`. Each check raises a `ValueError` whose message starts with the rule ID. The discriminated union `NodeConfig` and the params models check `V-pipeline.graph-7`. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- The reference model gives each item of the list of a variadic type the input name `*` (`VARIADIC`). Its cycle check ignores each `@prev` edge and each edge from the frame. `_ref_type` gives an `any` output the type of its inputs. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- The host checks at load the rules that need the point names, the geometries and the instance sources of the ports: these come from the sidecars and the MediaPipe YAML files.

## Authoring guidance

- Use `@prev` only where a node needs the previous frame. An `@prev` input makes the pipeline stateful, and a stateful pipeline runs at batch = camera count in the running mode `video` ([Running](running.md#behaviour); [ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 5).

## Examples

A top-down keypoint model takes the image and the ROIs of a person detector:

```yaml
nodes:
  - id: person
    type: detector
    inputs: {image: frame.image}
    params: {key: yolox-person@openmmlab-exporter, size: m}
  - id: wholebody
    type: detector
    inputs: {image: frame.image, rois: person.rois}
    params: {key: rtmw-wholebody133@openmmlab-exporter, size: m}
```

An ROI from the keypoints of the previous frame:

```yaml
  - id: hand_roi
    type: roi_from_points
    inputs: {keypoints: body.keypoints@prev}
    params: {points: [body.left_wrist, body.left_elbow], square_long: true, expand_ratio: 2.0}
```

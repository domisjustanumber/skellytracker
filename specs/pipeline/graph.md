---
id: pipeline.graph
title: Graph
kind: pipeline
vectors: null
status: {spec: draft}
---

# Graph

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The graph of a pipeline is a flat list of nodes. Each node has an id, a type and inputs. An input refers to an output port of another node, or to the camera frame. The suffix `@prev` refers to the value of the previous frame. This section gives the node fields, the port types, the box type, the empty values, the point names and their groups, and the instance rows of a port ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) items 4, 6 and 8; [ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1; [ADR-4MP6](../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md)).

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `nodes[].id` | name | yes | The node id. It is unique in the file. `pipeline` and `frame` are reserved. |
| `nodes[].description` | string | no | Text for people about the node. It can have more than one line. Default: empty. The run does not read it ([ADR-2RWC](../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md)). |
| `nodes[].type` | enum | yes | A node type of the [section map](README.md#section-map): `onnx_model`, `mediapipe_tasks`, `boxes_from_points`, `hold_boxes`, `gate`, `first_of`, `assign_keypoints`, `merge`, `flag_when`, `smooth_keypoints`, `smooth_boxes` or `redetect_trigger`. |
| `nodes[].inputs` | mapping or list | see the node section | For most types, a mapping of input name to port reference. For `first_of`, a list of port references. The node section gives the input names and the required inputs. |
| `nodes[].params` | mapping | see the node section | The params of the node type. The params table of the node section gives each param. A node type with a required param needs `params`. |

A **port reference** is a string `<node>.<port>`, with an optional suffix `@prev`. It matches `^[a-z][a-z0-9_-]*\.[a-z][a-z0-9_]*(@prev)?$`.

The **frame** is the reserved source of the graph. Its one port `frame.image` is the camera frame of the call. When the caller gives a JPEG buffer, `frame.image` is the decoded and turned frame ([Running](running.md#behaviour) item 13; [ADR-P245](decisions/entries/P245-jpeg-frame-input.md)). It has the type `image`. It is the only image of the graph: no node type has an output of the type `image`, so each `image` input names `frame.image` ([ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 4).

The port types:

| Type | Value |
|------|-------|
| `image` | The camera frame of one camera: only the port `frame.image` ([Behaviour](#behaviour) item 9). |
| `boxes` | `I` box rows, each with one box, an instance score and a class index ([Behaviour](#behaviour) item 3; [Outputs](outputs.md#fields); [ADR-2RWC](../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md)). |
| `keypoints` | `I` keypoint rows, each with `P` points ([Outputs](outputs.md#fields)). |
| `flag` | One boolean for one camera on one frame: true or false. A flag has no instance rows and no empty state. Only `redetect_trigger` and `flag_when` give a flag. Each of them runs on each frame and always decides ([ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) items 1, 2 and 8). |

Each input of a node type lists the port types that it accepts: the column "Type" of the ports table of the node section. An input that accepts two or more types names them all. The output `value` of `gate` and of `first_of` can have two or more types. It gets its type from its inputs ([Behaviour](#behaviour) item 4; [ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 1).

The [README](README.md#terms) gives the letter key `I`, `P` and the other letters.

## Behaviour

1. **Order.** The nodes are in any order. A node runs after each node that it takes a same-frame input from.
2. **`@prev`.** An input with `@prev` gets the value of the port on the previous frame that the run processed for the same camera. The value is empty on the first frame. In the running mode `image`, each `@prev` value is empty ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 2). An `@prev` edge does not count for the cycle check. The frame has no `@prev` value. An `@prev` input names only a `boxes` port or a `keypoints` port (`V-pipeline.graph-12`; [ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 5).
3. **Box.** A box is `(cx, cy, w, h, rotation)` in source-image pixels: the centre, the width, the height and the rotation. An object detector gives each box with rotation 0. `boxes_from_points` can give a rotated box. One port type holds both ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 8; [ADR-2RWC](../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md)):
   - `rotation` is in radians, in `[-π, π)`. A positive rotation turns the box clockwise in the image, because the image y axis points down.
   - The box x axis is `(cos(rotation), sin(rotation))` and the box y axis is `(-sin(rotation), cos(rotation))`, in image pixels.
   - The positions of points and boxes are those of the sidecar [unprojection](../model-sidecar/post/unprojection.md#behaviour). Their pixel centres follow the resize method of the model ([Pixel centres](../model-sidecar/pre/interpolation.md#pixel-centres)). A glue node adds no `0.5` offset and removes none.
   - Only the `onnx_model` node cuts pixels, always from `frame.image` ([Node: ONNX model](nodes/onnx_model.md#behaviour) gives the crop order).
   - **Source-image pixels.** Each `boxes` output and each `keypoints` output of each node is in source-image pixels. No node gives a box or a point in the space of a crop or of a model input. The sidecar `crop_policy` makes the crop larger than the box right before the warp, and no port shows that larger area ([ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 3).
4. **The type of an output with two or more types.** The output `value` of a `gate` node has the type of its input `value`. The output `value` of a `first_of` node has the type of its inputs. The load uses this type for `V-pipeline.graph-3`. When an input is also such an output, the load follows it to its own inputs. Such an output gets its type only from the inputs that are not `@prev`: an `@prev` input gives no type. The load thus follows only same-frame edges, and the search always ends (`V-pipeline.graph-9`; [ADR-97X9](../../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) item 5; [ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 1).
5. **Empty values.** The frame image is never empty. A `boxes` or `keypoints` value is empty when it has no present row. A `flag` value is never empty: it is true or false.
6. **Empty inputs.** A node that gets an empty required input does not run. Each output of that node is then empty. An empty optional input does not stop a node ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6):
   - The optional inputs are `hold_boxes.previous_keypoints`, `redetect_trigger.previous_keypoints`, `redetect_trigger.previous_boxes`, `boxes_from_points.previous_boxes` and `boxes_from_points.reference_boxes` ([ADR-RA0E](../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 3). `redetect_trigger` has no required input, so it runs on each frame.
   - The `boxes` input of a top-down keypoint model is required ([`V-node.onnx_model-2`](nodes/onnx_model.md#validation-rules)).
   - The input `run_if` of `onnx_model` and `mediapipe_tasks` is optional. A flag is never empty. When `run_if` is false, the node does not run, and each output is empty, as for an empty required input ([ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 7).
   - The rule of a node type can also read an empty required input: `gate` reads an empty `condition`, `first_of` skips each empty input, `hold_boxes` reads an empty `previous`, `assign_keypoints` reads an empty `source`, `flag_when` reads an empty `value`, `smooth_keypoints` counts an empty input as a miss after its first input, and `smooth_boxes` with the filter `one_euro` clears its state on an empty input ([ADR-RA0E](../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 5). The node section gives each such input.
7. **Point names and groups.** A point name is `<group>/<point>`, for example `body/left_wrist`. `<point>` is a point name of the sidecar or of the MediaPipe assets. A port reference and a timing span keep the dot ([ADR-4MP6](../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md) item 1):
   - An `onnx_model` node with the role `keypoint_detector` makes the groups of the landmark schema of its sidecar, in the order of the schema ([Landmark schema](../model-sidecar/post/keypoint/landmark-schema.md#fields)). A schema with two or more groups gives each group its name in the schema, for example `body`, `feet`, `face`, `left_hand` and `right_hand` of `COCO_WholeBody`. A schema with one group gives that group the id of the node.
   - A `mediapipe_tasks` node makes the groups that [Node: MediaPipe Tasks](nodes/mediapipe_tasks.md#behaviour) gives. The variant `holistic` makes the groups `body`, `right_hand`, `left_hand` and `face`, in this order.
   - An `assign_keypoints` node gives the groups of `target`, then one group for each slot that adds a group. A slot that replaces a group of `target` keeps that group ([Node: assign keypoints](nodes/assign_keypoints.md#behaviour) item 7; [ADR-KW76](../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) items 2 and 3).
   - A `merge` node gives exactly the groups of the layout of its `format`, in that order. A part gives the group of its input name: `left_hand`, `right_hand` or `face` ([Node: merge](nodes/merge.md#behaviour); [ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 11). The group names that `merge` gives do not count for `V-pipeline.graph-10`: the node makes no new group.
   - A `first_of` node gives the groups of its inputs, which are the same (`V-node.first_of-2`). The other glue nodes keep the point names and the groups of their input. An output adds no group.
   - The group names that the nodes of a file make are unique (`V-pipeline.graph-10`).
   - The group name of a schema with one hand gives the side of its canonical points: a node, a slot or a `merge` part `left_hand` gives `left_hand/wrist` ([Canonical mapping](../model-sidecar/post/keypoint/canonical-mapping.md#behaviour) item 2).
   - Each point name in a param is `<group>/<point>` (`V-pipeline.graph-8`). A derived point of `boxes_from_points` is local to its node and has no group.
8. **Instance rows.** Each `boxes` and `keypoints` value has `I` rows ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1):
   - The **instance source** of a value is the node that makes its instance rows: an object detector, a one-stage model or a `mediapipe_tasks` node. `I` is the `max_instances` of the instance source. `I` is fixed for the run. Each frame has the same shapes. `I` can be more than 1.
   - The present rows come first, in descending order of the instance score: the detection score of the row of an object detector or a one-stage model. Each present row of a `mediapipe_tasks` node has the instance score 1.0, so its rows keep the order of MediaPipe. A tie goes to the lower row index, as in the sidecar [selection behaviour](../model-sidecar/post/object/decode.md#selection-behaviour). The padding rows come last. A padding row has `present` false.
   - A missing point has NaN coordinates and the score 0 ([Decoded keypoints](../model-sidecar/post/keypoint/schema.md#decoded-keypoints)).
   - No row and no point is dropped.
   - A node that takes boxes runs once for each present row. Its output row `i` comes from the box row `i`. A padding row stays a padding row. The output has the instance source of the box input.
   - Each `boxes` and `keypoints` row carries the `instance_score` of its instance source row. No other node changes it. The instance source sets it: an object detector or a one-stage model gives the detection score of the row after the sidecar [object decode](../model-sidecar/post/object/decode.md#selection-behaviour). A `mediapipe_tasks` node gives 1.0 for each present row, because the Tasks results have no instance score. The instance score is not a function of the point scores. Each other node copies the value of the row from its input: a top-down keypoint model from its `boxes` row, `boxes_from_points` from its keypoints row, `smooth_boxes`, `smooth_keypoints`, `gate` and `first_of` from their input row, `assign_keypoints` from its `target` row, and `merge` from its `body` row. A row that `hold_boxes` carries over from `@prev` keeps the instance score of the last frame on which the instance source ran. The value does not decay. A row that `smooth_keypoints` holds gets its value from [Node: smooth keypoints](nodes/smooth_keypoints.md#behaviour) step 10 ([ADR-97X9](../../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) items 1 and 2).
   - Each `boxes` row carries a `class_index`. An object detector or a one-stage model sets it: the class index that the sidecar decode keeps. `boxes_from_points` gives -1, because a keypoints row has no class. `hold_boxes`, `smooth_boxes`, `gate` and `first_of` copy it with the row, as they copy the `instance_score` ([ADR-2RWC](../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md)).
   - `merge` joins row `i` of each part to row `i` of `body`. All inputs of `merge` have the same instance source (`V-node.merge-7`). The inputs of `first_of` also have one instance source.
   - `assign_keypoints` keeps the instance source and the `I` of its `target` input. Its `source` input can have any instance source and any `I`.
   - `x@prev` has the instance source and the `I` of `x` ([ADR-97X9](../../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) item 6).
   - A fan-out child adds point columns to the row of its instance. It adds no row. For example, a hand model on the hand box of person `i` adds its points to row `i`.
   - Each `track_ids` value is -1. This version tracks one person. Each input of `smooth_boxes`, `smooth_keypoints` and `redetect_trigger`, and each `@prev` input, must have `I` = 1 (`V-pipeline.graph-11`). When the instance source sees two persons, row 0 can still change from one person to the other between frames. This version has no `associate` node type ([ADR-TH8E](../../decisions/entries/TH8E-one-person-in-v2.md)).
9. **Image.** The only image is the camera frame `frame.image`. No node gives an image, and `gate` and `first_of` do not take one. The run gives the frame to each node that takes it by reference: the plumbing of the run never copies the image. A node can convert the image for its model. Each `mediapipe_tasks` node makes one BGR to RGB copy for the landmarker ([Node: MediaPipe Tasks](nodes/mediapipe_tasks.md#implementer-guidance)). No `@prev` input, no tap and no output reads the image (`V-pipeline.graph-2`, `V-pipeline.graph-12`; [Taps](taps.md#validation-rules); [Outputs](outputs.md#validation-rules); [ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 4).

## Validation rules

- [ ] `V-pipeline.graph-1` Each node id must be a name and must be unique in the file. The ids `pipeline` and `frame` are reserved and must not be node ids.
- [ ] `V-pipeline.graph-2` Each input must be a port reference. It must name an existing node and an output port of the type of that node, or the frame port `frame.image` with no `@prev`.
- [ ] `V-pipeline.graph-3` The type of the port that an input refers to must be one of the port types that the input accepts, after the load gives each output with two or more types its type ([Behaviour](#behaviour) item 4).
- [ ] `V-pipeline.graph-4` The same-frame edges must make no cycle. An `@prev` input is not a same-frame edge.
- [ ] `V-pipeline.graph-5` Each input name must be an input port of the node type. The variadic type `first_of` must have a list of port references. The other types must have a mapping.
- [ ] `V-pipeline.graph-6` Each node must have each required input of its type. The list of a `first_of` node must have at least one item.
- [ ] `V-pipeline.graph-7` `type` must be a node type of the [section map](README.md#section-map). `params` must agree with the params table of that type: each param name is a param of the type, each value has the type and the range of the param, and each param with no default is present.
- [ ] `V-pipeline.graph-8` Each point name in a param must be `<group>/<point>`: `<group>` is a name, and `<point>` has no `/` and no whitespace. A derived point name of a `boxes_from_points` node is the only exception. The host also checks at load that each name is a point of the input port, and refuses a point name of a sidecar or of the MediaPipe assets with `/` or whitespace ([ADR-4MP6](../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md)).
- [ ] `V-pipeline.graph-9` Each output with two or more port types must get its port type from an input that is not `@prev` ([Behaviour](#behaviour) item 4; [ADR-97X9](../../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) item 5).
- [ ] `V-pipeline.graph-10` The groups that the nodes of a file make must have unique names: the groups of each inference node and the group of each adding slot of each `assign_keypoints` node ([Behaviour](#behaviour) item 7). A replacing slot of an `assign_keypoints` node makes no group: it has the name of a group of its `target` on purpose. A `merge` node makes no group ([ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 11). The host checks this rule at load ([ADR-4MP6](../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md); [ADR-KW76](../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 2).
- [ ] `V-pipeline.graph-11` Each input of `smooth_boxes`, `smooth_keypoints` and `redetect_trigger`, and each `@prev` input, must have `I` = 1 ([Behaviour](#behaviour) item 8). The host checks this rule at load ([ADR-TH8E](../../decisions/entries/TH8E-one-person-in-v2.md)).
- [ ] `V-pipeline.graph-12` An `@prev` input must name a port of the type `boxes` or `keypoints` ([Behaviour](#behaviour) item 2; [ADR-9HTX](../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 5).

## Implementer guidance

- `check_structure` in the reference model checks `V-pipeline.graph-1` to `V-pipeline.graph-6`, `V-pipeline.graph-8`, `V-pipeline.graph-9` and `V-pipeline.graph-12`. Each check raises a `ValueError` whose message starts with the rule ID. The discriminated union `NodeConfig` and the params models check `V-pipeline.graph-7`. `V-pipeline.graph-10` needs the sidecars and the registry, and `V-pipeline.graph-11` needs the `max_instances` of each instance source, so the host checks them at load. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- The reference model gives each item of the list of a variadic type the input name `*` (`VARIADIC`). `inputs` and `outputs` of a node class map each port name to a tuple of port types. Its cycle check ignores each `@prev` edge and each edge from the frame. `_ref_type` gives an output with two or more types the type of its `any_from` inputs that are not `@prev`, and `x@prev` the type of `x`. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- The host checks at load the rules that need the point names, the geometries and the instance sources of the ports: these come from the sidecars, the landmark schema registry and the MediaPipe YAML files.

## Authoring guidance

- Use `@prev` only where a node needs the previous frame. An `@prev` input makes the pipeline stateful, and a stateful pipeline runs at batch = camera count in the running mode `video` ([Running](running.md#behaviour); [ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 5).

## Examples

A top-down keypoint model takes the image and the boxes of a person detector:

```yaml
nodes:
  - id: person
    type: onnx_model
    inputs: {image: frame.image}
    params: {key: yolox-person@openmmlab-exporter, size: m}
  - id: wholebody
    type: onnx_model
    inputs: {image: frame.image, boxes: person.boxes}
    params: {key: rtmw-wholebody133@openmmlab-exporter, size: m}
```

A box from the keypoints of the previous frame:

```yaml
  - id: hand_box
    type: boxes_from_points
    inputs: {keypoints: body.keypoints@prev}
    params: {points: [body/left_wrist, body/left_elbow], square_long: true, expand_ratio: 2.0}
```

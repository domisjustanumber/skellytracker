---
id: pipeline.graph
title: Graph
kind: pipeline
vectors: null
status: {spec: draft}
---

# Graph

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The graph of a pipeline is a flat list of nodes. Each node has an id, a type and named inputs. An input refers to an output port of another node, or to the camera frame. The suffix `@prev` refers to the value of the previous frame. This section gives the node fields, the port types, the ROI type, the empty values and the instance rows of a port ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) items 4, 6 and 8; [ADR-99MH](../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `nodes[].id` | name | yes | The node id. It is unique in the file. `pipeline` and `frame` are reserved. |
| `nodes[].type` | enum | yes | A node type of the [section map](README.md#section-map): `detector`, `mediapipe_tasks`, `roi_from_points`, `roi_tracking`, `gate`, `first_of`, `concat`, `smooth_keypoints`, `smooth_roi` or `redetect`. |
| `nodes[].inputs` | mapping | see the node section | Input name to port reference. The node section gives the input names and the required inputs. |
| `nodes[].params` | mapping | see the node section | The params of the node type. The params table of the node section gives each param. A node type with a required param needs `params`. |

A **port reference** is a string `<node>.<port>`, with an optional suffix `@prev`. It matches `^[a-z][a-z0-9_-]*\.[a-z][a-z0-9_]*(@prev)?$`.

The **frame** is the reserved source of the graph. Its one port `frame.image` is the camera frame of the call. It has the type `image`.

The port types:

| Type | Value |
|------|-------|
| `image` | One image of one camera. |
| `roi` | ROI rows ([ROI](#behaviour)). |
| `keypoints` | Keypoint rows: `I` instances, each with `P` points ([Outputs](outputs.md#fields)). |
| `detections` | Box rows: `I` instances, each with one box and a score ([Outputs](outputs.md#fields)). |
| `tensor` | One array. |
| `any` | An input or output of a `gate` or a `first_of` node. An `any` port takes a value of each type. |

## Behaviour

1. **Order.** The nodes are in any order. A node runs after each node that it takes a same-frame input from.
2. **`@prev`.** An input with `@prev` gets the value of the port on the previous frame that the run processed for the same camera. The value is empty on the first frame. In the running mode `image`, each `@prev` value is empty ([ADR-99MH](../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 2). An `@prev` edge does not count for the cycle check. The frame has no `@prev` value.
3. **ROI.** An ROI is `(cx, cy, w, h, rotation)` in source-image pixels: the centre, the width, the height and the rotation. A box is an ROI with rotation 0 ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 8). This draft does not fix the unit and the sign of `rotation`.
4. **Empty values.** An `image` value is empty when it holds no image. A `roi`, `keypoints` or `detections` value is empty when it has no present row. A `tensor` value is empty when it holds no array.
5. **Empty inputs.** A node that gets an empty input does not run. Each output of that node is then empty ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6). The rule of a node type can read an empty input: `gate` reads an empty `condition`, `first_of` skips each empty input, `roi_tracking` reads an empty `previous`, `redetect` reads its empty previous-frame inputs, and `smooth_keypoints` counts an empty input as a miss after its first input. The node section gives each such input.
6. **Instance rows.** Each `roi`, `keypoints` and `detections` value has `I` rows ([ADR-99MH](../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1):
   - The **root** of a value is the node that makes its instance rows: an object detector, a one-stage model or a `mediapipe_tasks` node. `I` is the `max_instances` of the root. `I` is fixed for the run. Each frame has the same shapes.
   - Each point name has a prefix. The prefix is the id of the node that makes the points, for example `left_hand.wrist` from the node `left_hand`. A `mediapipe_tasks` node of the variant `holistic` gives the prefixes `body`, `left_hand`, `right_hand` and `face` ([Node: MediaPipe Tasks](nodes/mediapipe_tasks.md#behaviour)). `concat` and the other glue nodes keep the names. An output adds no prefix.
   - The present rows come first, in descending order of score. The padding rows come last. A padding row has `present` false.
   - A missing point has NaN coordinates and visibility 0.
   - No row and no point is dropped.
   - A node that takes ROIs runs once for each present row. Its output row `i` comes from the ROI row `i`. A padding row stays a padding row.
   - `concat` joins row `i` of each input to row `i` of the output. All inputs of `concat` have the same root.
   - A fan-out child adds point columns to the row of its instance. It adds no row. For example, a hand model on the hand ROI of person `i` adds its points to row `i`.
   - Without an `associate` node, each `track_ids` value is -1. This version has no `associate` node type.

## Validation rules

- [ ] `V-pipeline.graph-1` Each node id must be a name and must be unique in the file. The ids `pipeline` and `frame` are reserved and must not be node ids.
- [ ] `V-pipeline.graph-2` Each input must be a port reference. It must name an existing node and an output port of the type of that node, or the frame port `frame.image` with no `@prev`.
- [ ] `V-pipeline.graph-3` The type of each input must match the type of the port that it refers to. An `any` port, as the input or as the source, matches each type.
- [ ] `V-pipeline.graph-4` The same-frame edges must make no cycle. An `@prev` input is not a same-frame edge.
- [ ] `V-pipeline.graph-5` Each input name must be an input port of the node type. The variadic types `first_of` and `concat` take each input name.
- [ ] `V-pipeline.graph-6` Each node must have each required input of its type. A `first_of` or `concat` node must have at least one input.
- [ ] `V-pipeline.graph-7` `type` must be a node type of the [section map](README.md#section-map). `params` must agree with the params table of that type: each param name is a param of the type, each value has the type and the range of the param, and each param with no default is present.

## Implementer guidance

- `check_structure` in the reference model checks `V-pipeline.graph-1` to `V-pipeline.graph-6`. Each check raises a `ValueError` whose message starts with the rule ID. The discriminated union `NodeConfig` and the params models check `V-pipeline.graph-7`. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- The reference model stores the input of a variadic type under the input name `*` (`VARIADIC`). Its cycle check ignores each `@prev` edge and each edge from the frame. (skellytracker `specs/pipeline/reference/pipeline_config.py`)

## Authoring guidance

- Use `@prev` only where a node needs the previous frame. An `@prev` input makes the pipeline stateful, and a stateful pipeline runs at batch = camera count in the running mode `video` ([Running](running.md#behaviour); [ADR-99MH](../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 5).

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
    params: {points: [left_wrist, left_elbow], square_long: true, scale: 2.0}
```

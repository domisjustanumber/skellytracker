---
id: node.merge
title: Merge node
kind: node
vectors: vectors/node.merge.yaml
status: {spec: draft}
---

# Merge node

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A `merge` node joins the parts `left_hand`, `right_hand` and `face` to `body`, row for row, in one fixed layout of groups. All inputs describe the same instances: row `i` of each part joins row `i` of `body`. The node does no position matching: use [`assign_keypoints`](assign_keypoints.md) for a source of another instance source. A part replaces the group of its name in `body`, or adds it ([ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 11). It is a glue node.

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Set during run | Description | Source |
|---|---|---|---|---|---|---|
| `format` | `Literal['wholebody', 'holistic']` |  | required | no | The layout of groups of the output. `wholebody`: `body`, `feet`, `face`, `left_hand`, `right_hand`, as `COCO_WholeBody`. `holistic`: `body`, `right_hand`, `left_hand`, `face`, as MediaPipe Holistic. | ADR-9HTX item 11 |
| `map` | `dict[str, str]` |  | `{}` | no | Output point to part point `<part>/<point>`, for example `body/left_wrist: left_hand/root`. A present part point replaces the output point. | ADR-9HTX item 11 |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `body` | input | `keypoints` |
| `left_hand` | input | `keypoints` |
| `right_hand` | input | `keypoints` |
| `face` | input | `keypoints` |
| `keypoints` | output | `keypoints` |
<!-- /node-table:ports -->

- `body` is required. `left_hand`, `right_hand` and `face` are optional parts. Each input is a `keypoints` port.
- `format` gives the layout of groups of the output:

  | `format` | Groups, in column order | Points of a group with no source |
  |---|---|---|
  | `wholebody` | `body`, `feet`, `face`, `left_hand`, `right_hand` | The points of that group of the landmark schema `COCO_WholeBody`, with its `landmark_schema` |
  | `holistic` | `body`, `right_hand`, `left_hand`, `face` | The points of that group of the `mediapipe_tasks` variant `holistic`, with a null `landmark_schema` |

  The group `feet` has no part: it comes only from `body`.
- `map` maps an output point name to a part point `<part>/<point>`, where `<part>` is a connected part and `<point>` is a point of that part, for example `body/left_wrist: left_hand/root`. A present part point replaces the output point.

## Behaviour

1. **Rows.** All inputs describe the same instances, row for row (`V-node.merge-7`). The output has the rows, the `present` flags, the `instance_score`, the `track_ids`, the instance source, the `I` and the geometry of `body`. A `body` row that is not present stays a padding row.
2. **Groups.** For each group of the layout of `format`, in its order, the output takes:
   - the group of `body` with that name, with its points and its `landmark_schema`; else
   - the connected part with that name: the points of the part, with the group of the input name, for example `left_hand/root` for the point `hand/root`, and the `landmark_schema` of the part; else
   - the points of the layout ([Fields](#fields)), each missing on each frame.

   A group of `body` that the layout does not name is not in the output.
3. **Replace.** When `body` has the group of a connected part, the part replaces that group in each row in which the part row is present. Each point of the group gets the part point with the same canonical name, as step 5 of [`assign_keypoints`](assign_keypoints.md#behaviour) gives the canonical name. A missing part point gives a missing point. A point of the group with no part point of its canonical name is **unfilled**. An unfilled point is missing. The load gives the warning `merge_unfilled_points` when a replaced group has an unfilled point that no key of `map` names ([Running](../running.md#behaviour) item 8).
4. **Add.** When `body` has no group of the name of a connected part, the part adds the group. In each row in which the part row is present, the group gets the points of the part: x, y, score and `raw_score`, and z for a `3d` output.
5. **No part row.** A part with no present row `i` leaves row `i` of its group as step 2 gives it before steps 3 and 4: the points of `body` for a replaced group, and missing points for an added group. An empty part does not stop the node.
6. **Map.** For each entry `output point: part point` of `map`, in each row `i`: when the part row `i` and the part point are present, the output point gets its x, y, score and `raw_score`, and its z for a `3d` output. Else the output point keeps its value after steps 3 to 5.
7. **Missing point.** A missing point has x and y NaN, z NaN for a `3d` output, and the score and the `raw_score` 0 ([ADR-PX6Z](../../../decisions/entries/PX6Z-keypoint-raw-score-in-the-pipeline-result.md)).
8. **Edges.** The output keeps each edge of `body` whose two points are in the output. An added group adds the edges of its part, with the group of the input name. A replaced group and a group of the layout add no edge. The edges are only drawing data ([Outputs](../outputs.md#behaviour) item 2).
9. **Empty `body`.** An empty `body` stops the node ([Graph](../graph.md#behaviour) item 6). The output is then empty.
10. The timing span is `run`.

## Validation rules

- [ ] `V-node.merge-6` Each part must have exactly one group. The host checks this at load.
- [ ] `V-node.merge-7` All inputs must have one instance source and one `geometry`. The host checks this at load.
- [ ] `V-node.merge-8` The landmark schema of `left_hand` and `right_hand` must be a schema with one group `hand`, and the landmark schema of `face` a schema with one group `face`. A part with a null `landmark_schema` is not refused: the load gives the warning `merge_part_without_landmark_schema` ([Running](../running.md#behaviour) item 8). The host checks this at load.
- [ ] `V-node.merge-9` Each value of `map` must be a part point `<part>/<point>` of a connected part, and each key must be a point name of the output. The reference model checks that the group of each value is `left_hand`, `right_hand` or `face`. The host checks the other names at load.

The IDs `V-node.merge-1` to `V-node.merge-5` are the rules of [`assign_keypoints`](assign_keypoints.md#validation-rules) of the first form. They are not used again.

## Implementer guidance

- The vector file `specs/pipeline/vectors/node.merge.yaml` holds the cases of this node. `tools/make_vectors.py` runs the reference implementation `specs/pipeline/reference/node_merge.py` on them. A case gives the layout and the canonical names, which the host finds at load in the landmark schema registry and the MediaPipe assets.
- The host finds the canonical names of step 3 at load, as for [`assign_keypoints`](assign_keypoints.md#implementer-guidance). Until stage 2.2 of the implementation plan registers the other schemas, a part of another schema fills only the points that `map` names.
- The node gives no group to `V-pipeline.graph-10`: each group of its output comes from an input or from the layout.

## Authoring guidance

- To join the hands and the face of one person to its body, connect each part model, which runs on a box from the body points, to the input of its name.
- To join a hand detector that finds hands in the whole image, use [`assign_keypoints`](assign_keypoints.md). Its hands have another instance source.
- Use `format: holistic` for the four groups of MediaPipe Holistic. The output `holistic` needs exactly these groups ([Outputs](../outputs.md#fields)).

## Examples

A body model, two hand models and a face model on boxes from the body points, as in the example [`rtmpose-body-hands-face`](../examples/rtmpose-body-hands-face.pipeline.yaml). The body model has no hand group and no face group, so each part adds its group:

```yaml
  - id: joined
    type: merge
    inputs:
      body: body.keypoints
      right_hand: right_hand.keypoints
      left_hand: left_hand.keypoints
      face: face.keypoints
    params: {format: wholebody}
```

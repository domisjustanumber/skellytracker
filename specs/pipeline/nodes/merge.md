---
id: node.merge
title: Merge node
kind: node
vectors: vectors/node.merge.yaml
status: {spec: draft}
---

# Merge node

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A `merge` node joins the keypoints of a `source` to the keypoints of a `target` with another instance source. For example, a hand detector finds hands in the whole image, and a merge puts each hand row in the slot of a body wrist, with the smallest total distance. A slot adds a group to the target, or replaces a group of the target ([ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md)). The output keeps the instance rows of the target ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6). It is a glue node. Use [`concat`](concat.md) for keypoint sets of one instance source.

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Set during run | Description | Source |
|---|---|---|---|---|---|---|
| `slots` | `dict[str, str]` | length >= 1 | required | no | Slot name to the target point that anchors the slot, for example `left_hand: body/left_wrist`. A slot with the name of a group of `target` replaces that group. A slot with another name adds a group. | ADR-KW76 items 2 and 3 |
| `source_anchor` | `str` |  | required | no | The point of `source` that the node compares with the slot anchors, for example `hand/root`. | ADR-KW76 item 6 |
| `max_distance` | `float` | > 0.0 | required | yes | The largest anchor distance, as a part of the diagonal of the box around the present points of the target row. | ADR-KW76 item 6 |
| `map` | `dict[str, str]` |  | `{}` | no | Target point to slot point `<slot>/<point>`, where `<point>` is a point of `source`. A present slot point replaces the target point. | ADR-KW76 item 4 |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `target` | input | `keypoints` |
| `source` | input | `keypoints` |
| `keypoints` | output | `keypoints` |
<!-- /node-table:ports -->

- `target` and `source` are `keypoints` ports. `source` can have any instance source and any `I` ([Graph](../graph.md#behaviour) item 8). `source` has exactly one group (`V-node.merge-4`; [ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 1).
- `slots` maps each slot name to its anchor: a point name of `target`. A slot name is a name ([Graph](../graph.md#behaviour) item 7):
  - A slot with the name of a group of `target` **replaces** that group. The output keeps the name, the place and the `landmark_schema` of that group (Behaviour steps 5 and 7).
  - A slot with another name **adds** a group with the slot name. The group has the points and the `landmark_schema` of `source` ([ADR-4MP6](../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md) item 2; [ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 3).
- A **slot point** `<slot>/<point>` is the point `<point>` of `source` in the slot `<slot>`. Each slot has one slot point for each point name `<group>/<point>` of `source`, in its order. For example, the slot `left_hand` and the source point `hand/root` give the slot point `left_hand/root`. The slot points of an adding slot are its columns in the output. The slot points of a replacing slot are not columns of the output.
- `source_anchor` is a point name of `source`. The node compares its position with the slot anchors.
- `max_distance` is required. It is a part of the diagonal of the axis-aligned box around the present points of the target row. A run can change it ([ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 6).
- `map` maps a target point name to a slot point ([ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 4). A present slot point replaces the target point. A key can be a point of a replaced group.

## Behaviour

1. **Empty inputs.** If `target` is empty, the node does not run. The output is empty. An empty `source` does not stop the node. This is a rule of the node, as [Graph](../graph.md#behaviour) item 6 allows: each slot point is then missing.
2. **Present points.** A point is present when its x and its y are not NaN.
3. **Match.** A candidate pair is one present row `j` of `source` and one slot `k` of one present row `i` of `target`, when the `source_anchor` of row `j` and the anchor of slot `k` in row `i` are both present, and:

   ```text
   distance = sqrt((x_source - x_slot)² + (y_source - y_slot)²)
   distance <= max_distance · diagonal
   ```

   `diagonal` is the diagonal of the axis-aligned box around the present points of target row `i`. An assignment is a set of candidate pairs in which each source row has at most one pair and each slot of each target row has at most one pair. The node keeps the assignment with the most pairs. Of these assignments, it keeps the assignment with the smallest total distance ([ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 5). Two totals are equal when they differ by at most 1e-9 of the larger total. The slot order is the lower target row first, then the earlier slot of `slots`. The node gives the source rows their slots in turn, from the lowest row. Each row gets the first slot in the slot order that still allows an assignment with the most pairs and the smallest total, with the slots of the rows before it. When no slot allows this, the row has no pair.
4. **Slot points.** For a kept pair, the slot points of slot `k` in row `i` are the points of source row `j`: x, y, score and `raw_score`, and z for a `3d` output. A slot point with no kept pair is missing: x and y are NaN, z of a `3d` output is NaN, and the score and the `raw_score` are 0 ([ADR-PX6Z](../../../decisions/entries/PX6Z-keypoint-raw-score-in-the-pipeline-result.md); [ADR-JHB3](../../../decisions/entries/JHB3-keypoints-xy-and-z-and-image-width-and-height.md)).
5. **Replace.** For a replacing slot, each point of the replaced group in row `i` gets the slot point with the same canonical name. A missing slot point gives a missing point. A point of the group with no slot point of its canonical name is **unfilled**. An unfilled point is missing, also when `target` had a value for it. The canonical name of a point is the canonical point name of the first passthrough entry whose source is that point, in the region whose key is the group of that point in its schema file ([Canonical mapping](../../model-sidecar/post/keypoint/canonical-mapping.md#behaviour)). The group name in the pipeline can be different, for example the node id `hand` of a one-group schema. A mean entry, a weighted entry, a group with a null `landmark_schema` and a schema with no canonical mapping give no canonical name. For example, the `COCO_WholeBody` point `left_hand/left_hand_root` and a slot point `left_hand/root` of a hand schema that maps `wrist: root` both have the canonical name `wrist`. The load gives the warning `merge_unfilled_points` when a replacing slot has an unfilled point that no key of `map` names ([Running](../running.md#behaviour) item 8; [ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 2).
6. **Map.** For each entry `target point: slot point` of `map`, in each row `i`: when the slot point is present, the target point gets its x, y, score and `raw_score`, and its z for a `3d` output. Else the target point keeps its value after step 5. The anchors of step 3 are the target points before steps 5 and 6.
7. **Output.** The output has the columns of `target`, then the slot points of each adding slot, in the order of `slots`. Thus it has the groups of `target`, then one group for each adding slot. A replaced group keeps its name, its place and its `landmark_schema`. The group of an adding slot has the slot name and the `landmark_schema` of `source` ([ADR-4MP6](../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md) item 2). It has the rows, the `present` flags, the `instance_score`, the `track_ids`, the instance source, the `I` and the geometry of `target`. A target row that is not present stays a padding row.
8. **Edges.** The output keeps the edges of `target`. An adding slot adds the edges of `source`, with the slot name as the group of each name. It also adds one edge from the slot anchor to the slot point of `source_anchor`, for example `[body/left_wrist, left_hand/root]`. A replacing slot adds no edge. The edges are only drawing data ([Outputs](../outputs.md#behaviour) item 2; [ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 3).
9. The timing span is `run` ([ADR-Q59W](../../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 1; [ADR-9PDQ](../../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 3).

## Validation rules

- [ ] `V-node.merge-1` Each slot name must be a name. The reference model checks this rule ([ADR-4MP6](../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md); [ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 2).
- [ ] `V-node.merge-2` Each value of `slots` and each key of `map` must be a point name of `target`. `source_anchor` must be a point name of `source`. Each value of `map` must be a slot point of the node. The reference model checks that the group of each value of `map` is a slot name. The host checks the other names at load ([ADR-4MP6](../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md); [ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 4).
- [ ] `V-node.merge-3` `target` and `source` must have the same `geometry` ([Outputs](../outputs.md#fields)). The host checks this at load.
- [ ] `V-node.merge-4` `source` must have exactly one group. The host checks this at load ([ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 1).
- [ ] `V-node.merge-5` A slot `face` that replaces the group `face` of `target` must have one or more keys of `map` in the group `face`, because a face point has no canonical name. The host checks this at load ([ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 2; [ADR-23F5](../../../decisions/entries/23F5-landmark-schema-registry.md) item 4).

## Implementer guidance

- The vector file `specs/pipeline/vectors/node.merge.yaml` holds the cases of this node. `tools/make_vectors.py` runs the reference implementation `specs/pipeline/reference/node_merge.py` on them ([ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 7).
- The reference finds the assignment of step 3 with `scipy.optimize.linear_sum_assignment` (the Hungarian method). A pair that is not a candidate gets a cost larger than the total of each assignment of candidate pairs, so the solver gives the most pairs first. For the tie order, the reference then gives each source row, from the lowest, the first slot that keeps the most pairs and the smallest total. It sums the distances with `math.fsum`, and it compares each total with the first optimum, with the tolerance of step 3.
- The host finds the canonical names of step 5 at load, in the schema files of the registry ([Landmark schema](../../model-sidecar/post/keypoint/landmark-schema.md#fields)). Until stage 2.2 of the implementation plan registers the other schemas, only `COCO_WholeBody` has a canonical mapping, and the groups of a `mediapipe_tasks` node have a null `landmark_schema`. A replace from a source of another schema then fills only the points that `map` names, and the load gives `merge_unfilled_points`.

## Authoring guidance

- To add a face from a face detector, chain a second `merge` after the first one, with the first merge as `target`.
- Start `max_distance` near 0.15 for a hand to its wrist. This value is not measured.
- The assignment has the most pairs, so a source row far from each slot takes a free slot when `max_distance` lets it. A small `max_distance` drops the hand of another person.
- `map` with the root points replaces the body wrists with the hand roots. Leave out `map` to keep the body points.
- To replace the hands of a whole-body model with the hands of a hand model, give the slots the names `left_hand` and `right_hand` of the target groups. A replace of the group `face` needs `map` (`V-node.merge-5`).
- A replaced group is missing in a row with no matched source row. To keep the points of the target in these rows, use an adding slot, for example `left_hand_mp`. The output then has the two groups, and a later filter can use the two of them.

## Examples

A body model with one person, and a hand detector with two hands, as in the example [`rtmpose-hand-detector`](../examples/rtmpose-hand-detector.pipeline.yaml). The slots add the groups `right_hand` and `left_hand`. The first point of the hand model is `root`:

```yaml
  - id: body_hands
    type: merge
    inputs: {target: body.keypoints, source: hand.keypoints}
    params:
      slots: {right_hand: body/right_wrist, left_hand: body/left_wrist}
      source_anchor: hand/root
      max_distance: 0.15
      map: {body/right_wrist: right_hand/root, body/left_wrist: left_hand/root}
```

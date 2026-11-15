# KW76 — `merge`: one source group, slots that replace or add a group, the smallest total distance and a required `max_distance`

**Status:** accepted, 2026-11-15 (user, design review 2026-11-13).

## Decision

1. **One source group.** The `source` of a `merge` node has exactly one group (`V-node.merge-4`).
2. **Replace.** A slot with the name of a group of `target` replaces that group. Each point of the
   group gets the slot point with the same canonical name: the name of the passthrough entry of the
   canonical mapping of its schema ([ADR-23F5](23F5-landmark-schema-registry.md)). For example, a
   MediaPipe hand and a `COCO_WholeBody` hand have 21 one-to-one names. The output keeps the name,
   the place and the `landmark_schema` of the group. A point with no slot point of its canonical
   name is unfilled. It is missing, and the load gives the warning `merge_unfilled_points`. A row
   with no matched source row has each point of the group missing. A face point has no canonical
   name, so a replace of the group `face` needs `map` (`V-node.merge-5`). A replacing slot makes no
   group, so `V-pipeline.graph-10` does not count it.
3. **Add.** A slot with another name adds a group with the slot name, the points and the
   `landmark_schema` of `source`. Its edges are the edges of `source` with the slot name as their
   group, and one edge from the slot anchor to the slot point of `source_anchor`. The edges are only
   drawing data.
4. **`map`.** A key of `map` is a target point, also a point of a replaced group. A value is a slot
   point `<slot>/<point>`, with a point of `source`. A present slot point replaces the target point.
   There is no `region` field.
5. **Match.** The node keeps the assignment with the most pairs, and of these, the assignment with
   the smallest total distance (the Hungarian method; the reference uses
   `scipy.optimize.linear_sum_assignment`). The candidate pairs do not change. A tie goes to the
   lower source row, then to the lower target row, then to the earlier slot. Two totals are equal
   when they differ by at most 1e-9 of the larger total.
6. **`max_distance`.** The param is required. A run can change it. The authoring guidance is: start
   near 0.15 for a hand to its wrist; this value is not measured. The examples use
   `source_anchor: hand/root`, because the first point of hand21 is `root`.
7. **Vectors.** The cases of `merge` move to `specs/pipeline/vectors/node.merge.yaml`, and
   `tools/tests/test_pipeline_glue_nodes.py` goes.
8. **Open work.** The pipeline open work gets "use a source side label in `merge`": MediaPipe gives
   the handedness of the hands of the subject, and a mirrored input inverts it. It also gets the
   heading "Ideas", with no stage, with an adapter to the OpenPose `POSE_KEYPOINT` form for ComfyUI.

This changes the text "`merge` keeps its named tests until the change of `merge` lands" of
[ADR-Y753](Y753-pipeline-templates-glue-vectors-and-taps-flag.md) item 4: that change is this entry.
It changes items 2, 4 and 8 of [ADR-4MP6](4MP6-pipeline-point-groups-and-canonical-form.md). Item
2: a `merge` output has the groups of `target`, then one group for each adding slot. Item 4: a
replacing slot makes no group, so `V-pipeline.graph-10` does not count it. Item 8: only an adding
slot adds the columns `<slot>/<point>`, and the other rules of `merge` change here.

## Reason

- The user decided each item in the design review of 2026-11-13.
- A whole-body model and a hand model give two sets of hand points. A replace keeps one hand group
  with the schema of the target, so the canonical form and the group names stay simple.
- A greedy match can give a hand to the wrong wrist, or leave a hand with no slot, when a better
  assignment exists.
- With the most pairs first, a hand of another person takes a free slot when no limit stops it. A
  required limit makes the author select it.
- The first point of hand21 is `root` (`hand21_tracked_points.yaml`), so `hand/wrist` was not a
  point of the source.
- One source for each case ([ADR-8DSW](8DSW-vector-files-are-the-case-source.md)).

## Alternatives rejected

- **A `region` field on a slot.** The slot name already gives the group, as the node id does
  ([ADR-4MP6](4MP6-pipeline-point-groups-and-canonical-form.md) item 5).
- **Keep the target points of a replaced group in a row with no matched source row.** One column
  then holds the points of two models. A later filter cannot tell them apart, and each change of
  model is a step in position that is not motion. An adding slot keeps the two groups apart.
- **An error for a slot with the name of a target group.** The replace is the use of that name.
- **A greedy match.** It is not the smallest total.
- **No limit as the default of `max_distance`.** A far hand then takes a free slot.
- **The MediaPipe handedness label now.** A mirrored input inverts it. It waits in the open work.

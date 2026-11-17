# 4MP6 — Pipeline point names `<group>/<point>`, output groups and the canonical form

**Status:** absorbed into [`graph.md#behaviour`](../../specs/pipeline/graph.md#behaviour), [`graph.md#validation-rules`](../../specs/pipeline/graph.md#validation-rules), [`outputs.md#fields`](../../specs/pipeline/outputs.md#fields), [`outputs.md#behaviour`](../../specs/pipeline/outputs.md#behaviour), [`mediapipe_tasks.md#behaviour`](../../specs/pipeline/nodes/mediapipe_tasks.md#behaviour), [`merge.md#merge-node`](../../specs/pipeline/nodes/merge.md#merge-node), [`concat.md#behaviour`](../../specs/pipeline/nodes/concat.md#behaviour), [`first_of.md#validation-rules`](../../specs/pipeline/nodes/first_of.md#validation-rules), [`boxes_from_points.md#fields`](../../specs/pipeline/nodes/boxes_from_points.md#fields), [`boxes_from_points.md#validation-rules`](../../specs/pipeline/nodes/boxes_from_points.md#validation-rules), [`pipeline/README.md#terms`](../../specs/pipeline/README.md#terms), 2026-11-15 (user, design review 2026-11-13; PR: pending).

## Decision

1. **Point names.** A pipeline point name is `<group>/<point>`. `<point>` is the point name of the
   sidecar or of the MediaPipe assets. A port reference and a timing span keep the dot. This changes
   the point-name rule that [ADR-W5QD](W5QD-pipeline-entries-consolidation.md) items 1 and 2
   restate (from [ADR-7NY2](7NY2-pipeline-form-graph-and-nodes.md) item 6, "a point name has the id
   of its node as a prefix", and [ADR-ZYS9](ZYS9-pipeline-outputs-running-sharing-inside-one-run.md)
   item 1, the prefixed `point_names`).
2. **Groups.** An inference node makes the groups of its landmark schema
   ([ADR-23F5](23F5-landmark-schema-registry.md)). A schema with two or more groups gives the group
   names of the schema. A schema with one group gives the node id. The fixed four parts of
   `holistic` are its declared groups `body`, `right_hand`, `left_hand` and `face`. The groups of a
   `mediapipe_tasks` node have a null `landmark_schema` until stage 2.2 registers the MediaPipe
   schemas. A `merge` output has the groups of `target`, then one group for each slot, with the slot
   name and the schema of `source`. `concat` gives the groups of its inputs in list order. The
   `keypoints` inputs of `first_of` have the same groups. The other glue nodes keep the groups of
   their input.
3. **Output schema.** Each `keypoints` output has `groups`: a list of
   `{name, start, count, landmark_schema}` in column order, contiguous. The load derives it. The
   output schema also has `canonical_names`, known before frame 0. No param such as
   `form: canonical` selects the canonical form. An edge with a derived point of the sidecar is not
   in `edges`, because a derived point has no column.
4. **Unique groups.** The group names that the nodes of a file make are unique
   (`V-pipeline.graph-10`).
5. **Side of a hand.** A schema of one hand takes its side from a group with the name `left_hand` or
   `right_hand`: the node id or the slot name. There is no `group` or `region` param.
6. **Canonical form.** The canonical form maps the groups that one node or one slot made together,
   with the canonical mapping of their schema: the groups with one `landmark_schema`. A schema with
   two or more groups comes from one node (item 4). For example, the `body` region of
   `COCO_WholeBody` uses the toes of its `feet` group. Each region comes from at most one group: the
   group with its name.
7. **Package function.** Stage 1.10 adds `to_canonical(keypoints_value, output_schema)`. It gives
   the canonical names, `xyz`, `score` and the passthrough groups. The freemocap migration uses it in
   place of its own map of names.
8. **`merge` names.** `merge` takes `<group>/<point>` names, and a slot adds the columns
   `<slot>/<point>`. The other rules of `merge` do not change here.

## Reason

- The user decided each item in the design review of 2026-11-13.
- A group from the model, not from the node id, lets one node make the body, the feet, the face and
  both hands of RTMW. The `/` keeps a point name apart from a port reference `<node>.<port>`.
- The node id names the group of a one-group schema, so two nodes that run one hand model do not
  collide, and the id gives the side.
- `groups` and `canonical_names` are static, so a caller reads them once before frame 0.

## Alternatives rejected

- **A `group` or `region` param on the node.** The node id and the slot name already give the name.
- **A `form: canonical` param of the pipeline.** A caller converts a result when it needs to.

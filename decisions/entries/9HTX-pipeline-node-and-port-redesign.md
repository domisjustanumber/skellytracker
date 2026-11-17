# 9HTX — Redesign of the pipeline node and port types: internal and external types, an `output` node, a three-state `flag` and named inputs

**Status:** proposed, 2026-11-17 (user, rulings of 2026-11-17).

## Decision

The user gave these rulings on 2026-11-17. A text in quotation marks is the wording of the user.
The design that applies them is in the proposal
[`node-and-port-redesign.md`](../../specs/pipeline/proposals/node-and-port-redesign.md). That
design is not decided. Its section 11 holds the open questions.

1. **Two kinds of type.** "there are two concepts - internal pipeline data types, and external ones
   that must be delivered to core."
2. **Output node.** "The output node type converts output data to holistic, wholebody, boxes
   (whichever combination is appropriate)."
3. **Output boxes.** "Boxes are output with no rotation, as required by core." "a rotated box is
   not permitted as an output box."
4. **Internal boxes.** "Internally in the pipeline, boxes can have rotation, score, presence and
   must always be converted to source image scaling on output from a node."
5. **Images.** "Image datatypes remain. They must never copy images in memory as it is expensive."
6. **Named inputs.** "I would like to make node inputs more explicit and not implied or assumed."
   "Whatever is plugged into each input is then tested and validated to be of that type and flagged
   or blocked if it is not."
7. **`merge`.** "a merge node would have 4 inputs - body, left_hand, right_hand, face". `body` is
   required, and the other three are optional. "This merge will replace existing keypoints on the
   body."
8. **`flag`.** One new port type `flag` holds the control signals. It has three states: true, false
   and empty.
9. **Gate.** `gate` gets the new modes `is_set` and `is_not_set` for a flag. A gate on an image
   stays allowed. A new converter node makes a flag from boxes or keypoints.
10. **`run_if`.** `onnx_model` gets the input `run_if`. For `mediapipe_tasks`: "onnx-only for the
    holistic task. For individual hand/face/body tasks it is permitted."
11. **Least number of types.** "I would like to have a minimal number of different inputs and
    outputs on nodes."

The user gave no ruling on these points. The proposal gives options for each: the meaning of
`holistic` and `wholebody`; a refusal or a conversion of a rotated output box; what "replace" covers
in `merge`; if `concat` goes; if the position matching of today's `merge` stays; the rule of each
consumer for an empty flag; the name and the ports of the converter node; the hand box node; and
the stages that land before the 2.0.0 pre-release.

When the user accepts the design, the accepted entry changes these rules:

- [ADR-W5QD](W5QD-pipeline-entries-consolidation.md) items 1, 2 and 3: the rules that it restates
  from [ADR-7NY2](7NY2-pipeline-form-graph-and-nodes.md) item 6 and
  [ADR-ZYS9](ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) items 1 and 7.
- [ADR-4WR9](4WR9-params-schema-in-the-node-catalog.md) item 3.
- [ADR-2RWC](2RWC-one-boxes-port-type-and-node-descriptions.md) item 6.
- [ADR-97X9](97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) items 1 and 5.
- [ADR-4MP6](4MP6-pipeline-point-groups-and-canonical-form.md) items 2, 3, 5 and 7.
- [ADR-PX6Z](PX6Z-keypoint-raw-score-in-the-pipeline-result.md) item 2.
- [ADR-RA0E](RA0E-built-in-box-behaviour-of-sfn26.md) items 4 and 6.
- [ADR-KW76](KW76-merge-replace-add-and-hungarian-match.md): the node gets a new name.
- [ADR-Q5BN](Q5BN-node-ran-in-the-camera-result.md) item 5.
- [ADR-6DKT](../../specs/pipeline/decisions/entries/6DKT-instance-rows-carry-class-and-score.md)
  item 5.

[ADR-TH8E](TH8E-one-person-in-v2.md), [ADR-3SF2](3SF2-pipeline-spec-and-node-workflow.md) and
[ADR-271H](271H-pipeline-bundles.md) do not change. This entry changes no entry, no spec section
and no code.

## Reason

The user wants the least number of port types, inputs that the load validates, and one fixed form
for the result that freemocap Core reads. Today Core has the output names and one node id of each
built-in pipeline as literals, and an image port carries a control signal.

The entry is in the root log, because the design changes files in `specs/pipeline/`, in the package
code and in freemocap. It is not a `proposal` bundle, because it also changes the sections
`pipeline.graph` and `pipeline.outputs`, and a node proposal holds only `node.<type>` sections.

## Consequences

- The node count goes from 11 to 13 in the proposed design. The port type count goes from 5 to 4.
- A flag with three states needs a rule for the empty state in each consumer. A flag with two
  states needs none.
- The `pipeline_sha256` of each pipeline changes, and each recorded tap of `yolox-rtmw-wholebody`
  stops to replay.
- freemocap Core and the pipeline editor of freemocap must change with the result and the catalog.

## Alternatives rejected

- **No `image` type** (the first-principles review of 2026-11-17). The user ruled that the image
  types remain.
- **A flag with two states.** The user chose three.
- **A gate that refuses an image.** The user ruled that a gate on an image stays allowed.

# Proposal: redesign of the pipeline node types and port types

This file uses ASD-STE100 Simplified Technical English.

This file is an informative proposal. It is not spec text. It changes no code, no spec section, no
schema, no example and no built-in pipeline. The entry
[ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) records the rulings
of the user and has the status `proposed`.

**Home of this file.** [Change a node type](../contributions.md#change-a-node-type) gives
`specs/pipeline/proposals/<slug>/` as the record folder of a `proposal` bundle. That record is a byte
copy of a bundle, and it holds only `node.<type>` sections. This redesign is not a bundle, and it
also changes the sections `pipeline.graph` and `pipeline.outputs`. Thus this file is one file beside
the record folders. `tools/intake_bundle.py` reads only the folders of `proposals/`.

**Baseline.** Each code fact is from commit 3c83a5b0. A `path:line` with no repository name is a
path in skellytracker. "Core" is freemocap Core, on the branch `sidecar-implementation` of freemocap.
"The editor" is the pipeline editor of freemocap, on the branch `pipeline-gui`.

**Authority.** Only a sentence of the user in quotation marks is a ruling. Each other statement in
this file is a proposal. Each open point is a question in [Open questions](#11-open-questions).

## 1. The design in short

- Four internal port types: `image`, `boxes`, `keypoints` and the new type `flag`. The types
  `tensor` and `any` go.
- Three external deliverables for Core: `wholebody`, `holistic` and `boxes`. One new node type
  `output` makes them. It replaces the free `outputs` map.
- A `flag` has three states: true, false and empty. `redetect_trigger` gives a flag in place of an
  image. `onnx_model` and `mediapipe_tasks` get the optional input `run_if`. `gate` gets the modes
  `is_set` and `is_not_set`.
- `merge` gets four named inputs: `body` (required), `left_hand`, `right_hand` and `face`
  (optional). `concat` goes. The position matching of today's `merge` stays as the node
  `assign_keypoints`.
- One new converter node `flag_when` makes a flag from boxes or keypoints.
- An image value is always a reference to the frame of the host. The pipeline plumbing never copies
  it.
- The two built-in pipelines keep their behaviour. The result that Core reads changes its form.

**Cost, stated plainly.** The node count does not go down. Today the spec has 11 node types. This
design has 13 (`concat` goes; `output`, `flag_when` and `assign_keypoints` come). The port type
count goes from 5 to 4.

## 2. The rulings and their consequences

The user gave each ruling on 2026-11-17. The quotations keep the spelling of the user.

| # | Ruling | Design consequence |
|---|---|---|
| R1 | "I would like to have a minimal number of different inputs and outputs on nodes." | Four port types. No new option that no ruling asks for. |
| R2 | "there are two concepts - internal pipeline data types, and external ones that must be delivered to core." | [Section 3](#3-port-types) separates the internal values from the external values. A node port never carries an external value. |
| R3 | "The output node type converts output data to holistic, wholebody, boxes (whichever combination is appropriate)." | One node type `output` with the optional inputs `wholebody`, `holistic` and `boxes` ([section 6](#6-the-output-node)). |
| R4 | "Boxes are output with no rotation, as required by core." and "a rotated box is not permitted as an output box." | The external box has no rotation field. The two sentences fit a refusal and a conversion. Question Q3 gives both. |
| R5 | "Internally in the pipeline, boxes can have rotation, score, presence and must always be converted to source image scaling on output from a node." | `InstanceBoxes` stays as it is. The rule "each `boxes` output is in source-image pixels" becomes a stated rule with a test. It is true in the code today. |
| R6 | "Image datatypes remain. They must never copy images in memory as it is expensive." | The type `image` stays. [Section 8](#8-the-image-rule) gives the copies of today and the new rules. |
| R7 | "I would like to make node inputs more explicit and not implied or assumed." and "Whatever is plugged into each input is then tested and validated to be of that type and flagged or blocked if it is not." | Each input has a name and a list of the types that it accepts. The load refuses a wrong type. The type `any` goes. |
| R8 | "a merge node would have 4 inputs - body, left_hand, right_hand, face" and, to "`body` required, the other three optional": "4 - yes". | The new `merge` ([section 4.2](#42-new-and-changed-node-types)). |
| R9 | "This merge will replace existing keypoints on the body. Is it still a concat or a merge?" | It is a merge. `concat` never replaces a point (`V-node.concat-2`). What "replace" covers is open (question Q4). |
| R10 | "I am unclear on where concat would be used." | The new `merge` does the work of `concat` in each example. `concat` goes (question Q5). |
| R11 | To "add a flag type as well as keeping `image`": "2 - yes", with the task to describe the control signals "in a single new "flag" datatype". | The port type `flag` ([section 5](#5-the-flag-rules)). |
| R12 | To "two (set / not set), or three with an explicit false?": "1 - three". | A flag is true, false or empty. The rule of each consumer for the empty state is open (question Q7). |
| R13 | To "Gating an image: refuse it, or still allow it?": "2 - allow and create the new node". | `gate` still takes an image as `value`. The new node `flag_when` makes a flag from boxes or keypoints. |
| R14 | To "`run_if`: on `onnx_model` only, or also on `mediapipe_tasks`?": "3 - onnx-only for the holistic task. For individual hand/face/body tasks it is permitted." | `run_if` on `onnx_model`, and on `mediapipe_tasks` for the variants `body`, `hand` and `face`. The load refuses it for the variant `holistic`. This reading is not confirmed (question Q9). |
| R15 | To "reuse `is_present` / `is_empty`, or add `is_set` / `is_not_set`?": "4 - add new names". | `gate` gets the modes `is_set` and `is_not_set`. |
| R16 | The hand example: "The keypoints then go into a hand roi node that has 2 outputs: a left_hand and a right_hand box." | A node `hand_boxes` is possible. Two `boxes_from_points` nodes give the same boxes today (question Q11). |

Two rulings of message 1 changed in message 2, and the user did not say if the first form stays:

- "Merge and concat nodes then have an output format that is set on the node, and 2 input nodes.
  The node config determines how inputs are mapped to outputs and the user can specify the
  mapping." This proposal reads message 2 as the later ruling: the `output` node sets the form,
  and `merge` has four inputs. The param `map` keeps a mapping that the user can write (Q4).
- "outputs the keypoints in canonical skeleton form". Message 2 names `holistic` and `wholebody`.
  How the two names relate to the canonical form is open (question Q2).

Two standing constraints apply. v2.0.0 tracks one person
([ADR-TH8E](../../../decisions/entries/TH8E-one-person-in-v2.md)). The decomposed MediaPipe pipeline
is later work: the hand example of the user is only the design case here.

## 3. Port types

### 3.1 Internal types

| Type | Value in Python | Empty value | Change |
|---|---|---|---|
| `image` | The frame array of the host, `(H, W, 3)`, BGR, uint8. A reference, never a copy. | `None` | Stays. New rules in [section 8](#8-the-image-rule). |
| `boxes` | `InstanceBoxes` | No present row | No change. |
| `keypoints` | `InstanceKeypoints` | No present row | No change. |
| `flag` | `True` or `False` | `None` | New. |

`InstanceBoxes` keeps its fields (`skellytracker/core/pipelines/values.py:81-90`):

| Field | Shape | Meaning |
|---|---|---|
| `boxes` | `(I, 5)` | `(cx, cy, w, h, rotation)` in source-image pixels. `rotation` is in radians, clockwise, in `[-pi, pi)`. |
| `instance_score` | `(I,)` | The score of the row. |
| `class_index` | `(I,)` | The class index of a detector row, else -1. |
| `present` | `(I,)` | True for a present row. |
| `track_ids` | `(I,)` | -1 in this version. |

`InstanceKeypoints` keeps its fields (`values.py:26-45`): `point_names` `(P,)`, `xy` `(I, P, 2)`,
`score` `(I, P)`, `raw_score` `(I, P)`, `instance_score` `(I,)`, `present` `(I,)`, `track_ids`
`(I,)` and `z` `(I, P)` or `None`.

**Source-image scale (R5).** Each `boxes` and `keypoints` output of each node is in source-image
pixels. The docstring states it today (`values.py:79`: "in source-image pixels"). No node gives a
box in the space of a crop or of a model input. The spec gets this sentence as a rule, and a test
checks the box of each node type against a known frame. One fact stays as today: the sidecar
`crop_policy` makes the crop larger than the box right before the warp, and no port shows that
larger area.

**`tensor` goes.** No node type has a `tensor` port (`config.py:493-587`). The name is only in
`PORT_TYPES` (`config.py:34`) and in the spec tables.

**`any` goes.** Today `gate` and `first_of` have the type `any` (`config.py:531-532`,
`config.py:541-542`). An `any` input validates nothing, so it is against R7. After the change, each
input has a list of the types that it accepts, and the output `value` of `gate` and of `first_of`
has the type of its input. The load still follows only same-frame edges to find that type
(`V-pipeline.graph-9`). Question Q10 gives the option to keep `any`.

### 3.2 External types

Core gets these values in the result of a camera. No node takes them as an input.

`wholebody` and `holistic` are both the type `CanonicalKeypoints`
(`skellytracker/core/pipelines/canonical.py:26-39`), with two new fields:

| Field | Shape | Today | After |
|---|---|---|---|
| `point_names` | `(C,)` | yes | yes |
| `xy` | `(I, C, 2)` | yes | yes |
| `score` | `(I, C)` | yes | yes |
| `groups` | list | yes | yes |
| `z` | `(I, C)` or `None` | yes | yes |
| `present` | `(I,)` | no | new: the `present` of the input row |
| `instance_score` | `(I,)` | no | new: the `instance_score` of the input row |
| `raw_score` | | no | no (question Q12) |
| `track_ids` | | no | no: each value is -1 in this version |

`boxes` is a new small type, `OutputBoxes`:

| Field | Shape | Meaning |
|---|---|---|
| `xyxy` | `(I, 4)` | `(x1, y1, x2, y2)` in source-image pixels, float64, not clipped. A padding row is NaN. |
| `score` | `(I,)` | The `instance_score` of the row. |
| `class_index` | `(I,)` | Copied from the row. |
| `present` | `(I,)` | Copied from the row. |

`OutputBoxes` has no rotation field (R4). `xyxy` is `(cx - w/2, cy - h/2, cx + w/2, cy + h/2)`.
Core computes the same four numbers today, then it clips them
(freemocap `freemocap/core/tracking/pipeline_runs.py:165-168`). The pipeline still does not clip,
as [ADR-RA0E](../../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 6 decides.

## 4. Node types

### 4.1 Each node type of today

"Load" is a check before frame 0. "Run" is a rule on each frame. An input with "(R)" is required.

| Node type | Inputs today | Outputs today | Inputs after | Outputs after | Checked at load | Rule at run | Verdict |
|---|---|---|---|---|---|---|---|
| `onnx_model` | `image` (R) image; `boxes` boxes, required for a top-down model | `boxes`; `keypoints` (the role decides) | `image` (R) image; `boxes` boxes, required for a top-down model; `run_if` flag, optional | no change | Role against ports (`V-node.onnx_model-2`). New: `run_if` is a flag. | Does not run when `image` is empty, when the `boxes` of a top-down model is empty, or when `run_if` is connected and is not true. | Changes |
| `mediapipe_tasks` | `image` (R) image | `keypoints` | `image` (R) image; `run_if` flag, optional, not for the variant `holistic` | no change | New: no `run_if` with `variant: holistic`. | As `onnx_model`. | Changes |
| `boxes_from_points` | `keypoints` (R); `previous_boxes`; `reference_boxes` | `boxes` | no change | no change | No change (`V-node.boxes_from_points-1` to `-7`). | No change. | Stays |
| `hold_boxes` | `previous` (R) boxes; `current` (R) boxes; `previous_keypoints` keypoints | `boxes` | no change | no change | No change. | No change. | Stays |
| `gate` | `value` (R) any; `condition` (R) any | `value` any | `value` (R) image, boxes or keypoints; `condition` (R) boxes, keypoints or flag | `value`: the type of the input `value` | New: `is_set` and `is_not_set` need a `flag` condition. `score_above` needs boxes or keypoints (`V-node.gate-2`). An `image` condition is refused. | Reads an empty `condition`. New modes on a flag ([section 5](#5-the-flag-rules)). | Changes |
| `first_of` | list of any | `value` any | list of one type: image, boxes or keypoints | `value`: the type of the inputs | No change (`V-node.first_of-1`, `-2`). A `flag` item is refused. | No change. | Stays, with declared types |
| `concat` | list of keypoints | `keypoints` | | | | | Goes: the new `merge` does its work |
| `merge` | `target` (R) keypoints; `source` (R) keypoints | `keypoints` | no change | no change | No change (the five rules move with the node). | No change. | Renamed to `assign_keypoints` |
| `smooth_keypoints` | `keypoints` (R) | `keypoints` | no change | no change | No change. | No change. | Stays |
| `smooth_boxes` | `boxes` (R) | `boxes` | no change | no change | No change. | No change. | Stays |
| `redetect_trigger` | `image` (R) image; `previous_keypoints`; `previous_boxes` | `image` image | `previous_keypoints` keypoints, optional; `previous_boxes` boxes, optional | `redetect` flag | No change (`V-node.redetect_trigger-1`, `-2`). | Runs on each frame, because it has no required input. True when a detection is necessary, else false. In the running mode `image`: always true. | Changes |

Notes on this table:

- `first_of` keeps its list. The order of the list is the priority, so names add nothing. It is
  the only node type with unnamed inputs after `concat` goes.
- `gate.value` and `first_of` take no `flag`. No ruling asks for a flag through a gate. Thus this
  design has no AND and no OR of two flags. A pipeline with two conditions puts two `gate` nodes in
  a row on the data. The change to allow a flag there is additive.
- Today the catalog gives `onnx_model.boxes` as optional (`config.py:495`:
  `required_inputs = ("image",)`), and the executor makes it required from the role
  (`_runtime/executor.py:317`). The catalog must state "required for a top-down model", so that the
  editor can show it.
- No port gets a new name except `redetect_trigger.image`, which becomes `redetect`. The inputs
  `previous_*` and the outputs `value` keep their names.

### 4.2 New and changed node types

**`output`** (new). [Section 6](#6-the-output-node) gives it in full.

| Port | Direction | Accepts | Required |
|---|---|---|---|
| `wholebody` | input | keypoints | no |
| `holistic` | input | keypoints | no |
| `boxes` | input | boxes | no |

No params and no output port. A file has exactly one `output` node, with one input or more.

**`flag_when`** (new, the converter of R13). It makes a flag from a `boxes` or a `keypoints` value.

| Port | Direction | Accepts | Required |
|---|---|---|---|
| `value` | input | boxes, keypoints | yes; the node reads an empty value |
| `flag` | output | flag | |

| Param | Type | Default | Meaning |
|---|---|---|---|
| `mode` | `is_empty`, `is_present` or `score_above` | required | The test on `value`, as [`gate`](../nodes/gate.md#behaviour) step 2 gives it for a list of present rows. |
| `threshold` | float, `>= 0` | none | Only for `score_above`. A run can change it. |

The output is true when the test passes, else false. It is never empty, because the node reads an
empty input. The node does one test on each frame, on all present rows, as step 4 of `gate`. It
keeps no state. An `@prev` input makes the pipeline stateful, as each `@prev` input does. The
"detect when lost" case of [`gate`](../nodes/gate.md#authoring-guidance) then has two forms: the
gated image of today, and this one:

```yaml
  - id: lost
    type: flag_when
    inputs: {value: body.keypoints@prev}
    params: {mode: is_empty}
  - id: person
    type: onnx_model
    inputs: {image: frame.image, run_if: lost.flag}
    params: {key: yolox-person@openmmlab-exporter, size: m}
```

Cost: R13 keeps the gated image and adds the flag. A file can thus stop a detector in two ways.

**`merge`** (new meaning, R8 to R10).

| Port | Direction | Accepts | Required |
|---|---|---|---|
| `body` | input | keypoints | yes |
| `right_hand` | input | keypoints, one group | no |
| `left_hand` | input | keypoints, one group | no |
| `face` | input | keypoints, one group | no |
| `keypoints` | output | keypoints | |

| Param | Type | Default | Meaning |
|---|---|---|---|
| `map` | mapping of point name to point name | `{}` | A point of `body` to a point of a part, for example `body/left_wrist: left_hand/root`. A present part point replaces the body point. It is the `map` of today's `merge`. |

Behaviour, as proposed:

1. All inputs describe the same instances, row for row. Row `i` of each part joins row `i` of
   `body`. The node does no position matching.
2. The group of a part takes the name of its input: `right_hand`, `left_hand` or `face`. The node
   id of the model does not set the side of a hand any more. This is the "explicit, not implied"
   rule of R7 for the group name. A `body` input with one group gets the group name `body`. A
   `body` input with two or more groups keeps its group names.
3. When `body` has a group with the name of a part, the part **replaces** that group, point for
   point by canonical name, as step 5 of today's [`merge`](../nodes/merge.md#behaviour) does. Else
   the part **adds** a group, after the groups of `body`, in the order `right_hand`, `left_hand`,
   `face`. This is the order of `mediapipe_tasks` with the variant `holistic`.
4. A part that is not connected adds nothing. A connected part with an empty row gives missing
   points in its columns, as `concat` does today. For a replaced group, question Q17 gives the two
   options.
5. `body` is required: an empty `body` stops the node. The output has the rows, the `present`
   flags, the `instance_score` and the instance source of `body`.

Checked at load: each input is `keypoints`; each part has exactly one group; all inputs have one
instance source and one `geometry`; the landmark schema of a part has the region of its input
(a hand schema for `left_hand`). A part with a null `landmark_schema` cannot be checked. It gives
a load warning and is not refused: "flagged", in the word of R7. A wrong schema is "blocked".

**`assign_keypoints`** (today's `merge`, with a new name). Ports `target` and `source`, the params
`slots`, `source_anchor`, `max_distance` and `map`, and the rules `V-node.merge-1` to `-5` move
with the node and do not change
([ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md)). It is only
for a `source` of another instance source, for example a hand detector on the full frame. Question
Q6 gives the option to drop it.

**`hand_boxes`** (possible, R16; this proposal defers it).

| Port | Direction | Accepts | Required |
|---|---|---|---|
| `keypoints` | input | keypoints | yes |
| `left_hand` | output | boxes | |
| `right_hand` | output | boxes | |

Params: `left` and `right`, each with the box rule of `boxes_from_points`: `points`,
`derived_points`, `size_rule`, `alignment_start`, `alignment_end`, `target_rotation_deg`,
`square_long`, `expand_ratio` and `score_threshold`. The behaviour is that of two
`boxes_from_points` nodes. The node thus adds no new behaviour: it saves one node and one wire.
The alternative, `boxes_from_points` with a mapping of named box rules and one output for each
name, breaks a rule of the catalog: the ports of a node type are fixed (`config.py:480-481`).

## 5. The flag rules

A `flag` is one value for one camera on one frame. It has no instance rows.

| State | Python value | It means |
|---|---|---|
| true | `True` | The producer ran and decided yes. |
| false | `False` | The producer ran and decided no. |
| empty | `None` | No decision: the producer did not run, or the value is an `@prev` value on the first frame or in the running mode `image`. |

`is_empty` of `values.py:101-103` already gives true for `None` and false for `False`. `PortInfo.empty()`
already gives `None` for a type that is not `boxes` or `keypoints` (`values.py:136-142`).

**The rule of each consumer.** The column "empty" is the proposal of question Q7. It is strict: an
empty flag passes nothing and starts nothing.

| Consumer | true | false | empty |
|---|---|---|---|
| `gate`, mode `is_set` | passes `value` | output empty | output empty |
| `gate`, mode `is_not_set` | output empty | passes `value` | output empty |
| `gate`, mode `is_present` | passes `value` | passes `value` | output empty |
| `gate`, mode `is_empty` | output empty | output empty | passes `value` |
| `gate`, mode `score_above` | refused at load | | |
| `onnx_model.run_if`, `mediapipe_tasks.run_if` | the node runs | the node does not run; `node_ran` is false | the node does not run; `node_ran` is false |
| `output` | a flag is not an input of `output` | | |

- **`x@prev`.** A flag with `@prev` is empty on the first frame, as each `@prev` value is
  ([Graph](../graph.md#behaviour) item 2). In the running mode `image` it is always empty
  (`_runtime/executor.py:305-308`). With the strict rule, a node whose `run_if` is an `@prev` flag
  never runs in the running mode `image`, and does not run on the first frame.
- **Who can give an empty flag.** `redetect_trigger` and `flag_when` always decide. An empty flag
  thus comes only from `@prev`, or from a later node type.
- **Cost of three states.** With two states, "not set" is the empty value, and no consumer needs a
  new rule. With three states, each consumer needs the third column above, each vector file of a
  consumer needs the third case, and the editor must show three states. No pipeline file of today
  needs the third state.
- **Taps.** A tap on a `flag` port is refused, as a tap on an `image` port is today
  (`_runtime/taps.py:33`: `JSONL_TYPES = ("boxes", "keypoints")`). A replay of the node that made
  the flag is not possible. Question Q15 gives the option of a `flag.jsonl` form.
- **Timing.** A flag has no span and no event. The node that makes it has its span `run`. The
  timing header does not name flags.
- **`node_ran`.** A node that `run_if` stops has `node_ran` false, as a node with an empty required
  input has today ([ADR-Q5BN](../../../decisions/entries/Q5BN-node-ran-in-the-camera-result.md)
  item 3).
- **Stateful pipelines.** The stateful rule follows each input of an `onnx_model` node
  (`_runtime/resolve.py:146-152`), so a trigger on `run_if` still makes the pipeline stateful.

**The control signals of today.** The flag inventory found 19 signals. This table groups them. Only
one becomes a flag.

| Signal of today | Where | After |
|---|---|---|
| Redetect trigger: the image, or empty | `_runtime/node_redetect_trigger.py:122`: `return {"image": image if hit else None}, n if hit else last` | The flag `redetect`: true or false. |
| "An empty required input stops the node" | `_runtime/executor.py:313-319` | Stays. `run_if` adds: connected and not true stops the node. |
| Rules that read an empty input (`READS_EMPTY`) | one constant in each `_runtime/node_*.py` | Stay. `flag_when` reads its `value`. `output` reads each input. |
| `gate` modes `is_empty`, `is_present`, `score_above` | `_runtime/node_gate.py:55-61` | Stay. Two modes come for a flag condition. The row-by-row test stays for an instance condition. |
| `first_of`: the first input that is not empty | `_runtime/node_first_of.py:46` | Stays. Also the self-`@prev` latch `detected_box` of the built-in. |
| `present` row mask; point validity (NaN, `raw_score > 0`) | `values.py:33-40`, `values.py:87-88` | Stay. They are data for each row or each point. A flag is not for each row. |
| Interval and `last` of the trigger; the fitness checks | `_runtime/node_redetect_trigger.py`, params `config.py` | Stay inside the node. `last` is still the frame of the last request. |
| Internal rules of `hold_boxes`, `smooth_boxes`, `smooth_keypoints`, `assign_keypoints` | their node modules | Stay inside the nodes. |
| `node_ran` | `_runtime/executor.py:340`, `:370-372`, `:378` | Stays, in the result of the camera. It is not a port. |
| Running mode `image`; replay; the stateful classification | `_runtime/executor.py:305-308`, `_runtime/resolve.py:138-157` | Stay. They are facts of the run. |
| MediaPipe VIDEO tracking | inside the landmarker | Stays hidden. `run_if` can now skip frames of a `body`, `hand` or `face` landmarker ([section 9.6](#96-risks)). |

## 6. The output node

**What it takes.** The inputs `wholebody`, `holistic` and `boxes` of
[section 4.2](#42-new-and-changed-node-types). One input or more. No `@prev`, and not the frame.

**What it delivers.** The result of a camera has one key for each connected input, with the name of
the input, and the fixed fields of today (`config.py:50`: `frame_index`, `image_width`,
`image_height`, `timestamp_ms`, `node_ran`).

| Input | Delivered value | Conversion | Checked at load |
|---|---|---|---|
| `wholebody` | `CanonicalKeypoints` with the canonical names | `to_canonical` (`canonical.py:146`), as Core calls it today | The value has a group `body`. A group with a null `landmark_schema` passes through with its names and gives a load warning. |
| `holistic` | `CanonicalKeypoints` with the groups `body`, `right_hand`, `left_hand`, `face`, in this order | The same function. For a `mediapipe_tasks` node it changes no name today: its groups have a null `landmark_schema`. | The groups have exactly these names and this order. |
| `boxes` | `OutputBoxes` | `(cx, cy, w, h)` to `xyxy`. Rotation: question Q3. | Question Q3. |

The meaning of the two keypoint names is the proposal of question Q2. Measured on this commit with
`check_pipeline`: the output `wholebody` of `yolox-rtmw-wholebody` has 133 point names and 137
canonical names; the output `holistic` of `mediapipe-holistic-tasks` has 553 point names, and its
canonical names are equal to them.

**The free `outputs` map.** The key `outputs` of the file goes
(`config.py:709`: `outputs: dict[str, str]`). The `output` node is in `nodes`. A file can no longer
give an output a free name, and it can no longer give two `boxes` outputs. The output `detector_box`
of `yolox-rtmw-wholebody` goes. Core does not read it: `pipeline_runs.py` reads only
`result["wholebody"]`, `result["crop_box"]`, `result["holistic"]` and `result["node_ran"]`
(freemocap `pipeline_runs.py:159-172`). A `record` tap on `person.boxes` gives the same data.

**The output schema.** It has one item for each connected input. For `wholebody` and `holistic`,
`point_names`, `groups` and `edges` describe the delivered value. They are the `canonical_names`,
the passthrough groups and the `canonical_edges` of today. The two fields `canonical_names` and
`canonical_edges` go, because they would repeat `point_names` and `edges`. `geometry`,
`depth_unit`, `max_instances`, `tracked` and `instance_source` stay. For `boxes`, `class_names`
stays.

**`to_canonical` and `CanonicalKeypoints`.** `to_canonical` stays a public function. The `output`
node calls it. Core stops calling it. `CanonicalKeypoints` gets `present` and `instance_score`
([section 3.2](#32-external-types)). It still has no `raw_score`: `to_canonical` reads the
`raw_score` of its input for the missing rule (`canonical.py:172`: `present=keypoints_value.raw_score > 0`),
and gives none. Today the result of `mediapipe-holistic-tasks` is an `InstanceKeypoints` with
`raw_score`. After the change it has none. Core does not store it (freemocap `pipeline_runs.py:149`:
"Its `raw_score` is not stored"). The internal ports and the taps keep `raw_score`.

**Presence and score of the box.** `OutputBoxes.present` and `OutputBoxes.score` are the `present`
and the `instance_score` of the row. Core reads these two today (freemocap `pipeline_runs.py:164`,
`:169`).

**`node_ran` and `detector_ran`.** `node_ran` does not change
([ADR-Q5BN](../../../decisions/entries/Q5BN-node-ran-in-the-camera-result.md)). The `output` node
is not an inference node and gets no key. Today Core has the literal node id `person`
(freemocap `pipeline_runs.py:28`, `:170`). Core can read the id from the output schema:
`node_ran[output_schema["boxes"]["instance_source"]]`. Measured on this commit: the
`instance_source` of `crop.boxes` is `person`. The output node delivers no flag (question Q13).

**A rotated box.** Only `boxes_from_points` with a `target_rotation_deg` gives a rotation that is
not 0 ([`boxes_from_points`](../nodes/boxes_from_points.md#behaviour) step 6). The load can thus
know if a box can rotate: it does when such a node is upstream of the port, also through `@prev`.
The options:

- **A, refuse at load.** The load refuses a file whose `output.boxes` can hold a rotated box. No
  rotated box reaches the output node, and the node converts nothing.
- **B, convert at run.** The output node gives the axis-aligned box that encloses the rotated box.
  The `bbox` of a `boxes` tap line already has this formula (`_runtime/taps.py:96`).
- **C, refuse, with a param to convert.** As A, but a param `rotated: enclose` of the output node
  selects B. This adds a param that no ruling asks for.

Neither built-in sets `target_rotation_deg`, so A, B and C give the same result for them.

## 7. The pipelines in the new form

The YAML of this section is only in this file. Each `description`, each `sidecar_sha256` and each
param that does not change is left out, shown as `# ...`.

### 7.1 Built-in `yolox-rtmw-wholebody`

```yaml
nodes:
  - id: trigger
    type: redetect_trigger
    inputs:
      previous_keypoints: wholebody.keypoints@prev
      previous_boxes: crop.boxes@prev
    params: # ... no change
  - id: person
    type: onnx_model
    inputs: {image: frame.image, run_if: trigger.redetect}
    params: # ... no change
  - id: detected_box
    type: first_of
    inputs: [person.boxes, detected_box.value@prev]
  - id: points_box
    type: boxes_from_points
    inputs:
      keypoints: wholebody.keypoints@prev
      previous_boxes: crop.boxes@prev
      reference_boxes: detected_box.value
    params: # ... no change
  - id: carried_box
    type: gate
    inputs: {value: points_box.boxes, condition: trigger.redetect}
    params: {mode: is_not_set}
  - id: box
    type: first_of
    inputs: [person.boxes, carried_box.value]
  - id: crop
    type: smooth_boxes
    inputs: {boxes: box.value}
    params: # ... no change
  - id: wholebody
    type: onnx_model
    inputs: {image: frame.image, boxes: crop.boxes}
    params: # ... no change
  - id: output
    type: output
    inputs: {wholebody: wholebody.keypoints, boxes: crop.boxes}
```

Behaviour of the tracking: no change. The reasons, from the code:

- The trigger runs on each frame today, because `frame.image` is never empty. After the change it
  has no required input, so it runs on each frame. Its decision and its `last` do not change.
- `person` stops on the same frames: today on an empty `trigger.image`, after the change on a
  false `trigger.redetect`. `node_ran["person"]` is the same.
- `carried_box` passes on the same frames: today `is_empty` on the image, after the change
  `is_not_set` on the flag. The trigger never gives an empty flag, so question Q7 does not change
  this pipeline.
- The pipeline stays stateful.

This claim is reasoned from the code. The box parity test of
[ADR-7E4Z](../../../decisions/entries/7E4Z-box-parity-of-the-built-in-with-sfn26.md) must prove it
in the stage that makes the change.

What changes, and why:

- The result has `boxes` in place of `crop_box`, as `xyxy` with no rotation (R3, R4).
- The result has no `detector_box` (R3: three deliverables).
- `wholebody` is delivered in the canonical form, with 137 names. Today the result has 133 names,
  and Core converts it. The numbers that Core stores are the same.
- The graph has two image wires in place of three.
- `pipeline_sha256` and each `upstream_sha256` change.

### 7.2 Built-in `mediapipe-holistic-tasks`

```yaml
nodes:
  - id: holistic
    type: mediapipe_tasks
    inputs: {image: frame.image}
    params: {variant: holistic}
  - id: output
    type: output
    inputs: {holistic: holistic.keypoints}
```

Behaviour: no change of a point name, a position or a score. The delivered value has no
`raw_score` and no `track_ids` (question Q12).

### 7.3 Example `rtmpose-body-hands-face`

The nodes `person`, `body`, `right_hand_box`, `left_hand_box`, `face_box`, `right_hand`, `left_hand`
and `face` do not change. The last node and the outputs become:

```yaml
  - id: joined
    type: merge
    inputs:
      body: body.keypoints
      right_hand: right_hand.keypoints
      left_hand: left_hand.keypoints
      face: face.keypoints
  - id: output
    type: output
    inputs: {wholebody: joined.keypoints}
```

Behaviour: the same columns, in the same order, as the `concat` of today: `body`, `right_hand`,
`left_hand`, `face`. No part replaces a group, because the body model has no hand group and no face
group. The result is in the canonical form.

### 7.4 Example `rtmpose-hand-detector`

The four model nodes do not change. The `merge` node gets the type `assign_keypoints`, with the same
inputs and params. The output becomes:

```yaml
  - id: body_hands
    type: assign_keypoints
    inputs: {target: body.keypoints, source: hand.keypoints}
    params: # ... no change
  - id: output
    type: output
    inputs: {wholebody: body_hands.keypoints}
```

Behaviour: no change of the node. The output name `body_hands` becomes `wholebody`.

### 7.5 Example `mediapipe-holistic-decomposed`

```yaml
  - id: trigger
    type: redetect_trigger
    inputs: {previous_keypoints: body.keypoints@prev}
  - id: pose_detector
    type: onnx_model
    inputs: {image: frame.image, run_if: trigger.redetect}
    params: {key: mediapipe-pose-detector@mediapipe-exporter, size: full}
  # ... pose_box_prev to body_smooth: no change
  - id: joined
    type: merge
    inputs:
      body: body_smooth.keypoints
      right_hand: right_hand.keypoints
      left_hand: left_hand.keypoints
  - id: output
    type: output
    inputs: {wholebody: joined.keypoints}
```

Behaviour changes, and why. Today the file has three outputs: `body`, `right_hand` and `left_hand`.
The three deliverables of R3 hold one keypoint set of a kind, so a `merge` node joins them. This is
the merge of the hand example of the user. The two `gate` nodes of the file take a `boxes` value and
a `keypoints` condition, and they do not change. The hand boxes of this file are rotated, but they
are not an output, so option A of section 6 does not refuse the file.

## 8. The image rule

R6: "They must never copy images in memory as it is expensive."

**Where the runtime passes an image today, with no copy:**

- `_runtime/executor.py:337`: `values[camera_id] = {(FRAME, "image"): frame.image}`. A reference.
- `_runtime/executor.py:419`: `runner.run(index, [ready[camera_id]["image"] for camera_id in cameras], boxes, timer)`.
  A list of references.
- `_runtime/node_redetect_trigger.py:122`, `_runtime/node_gate.py:103` and
  `_runtime/node_first_of.py:46` give the input object back.

**Where the runtime copies a full frame today:**

| Place | Line | When |
|---|---|---|
| `_runtime/mediapipe_tasks.py:151` | `mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(image[:, :, ::-1]))` | On each frame, for each camera, in each `mediapipe_tasks` node with the variant `body`, `hand` or `face`. BGR to RGB. |
| `_runtime/mediapipe_tasks.py:143`, which calls `skellytracker/core/detectors/mediapipe_holistic.py:109` | `mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB))` | On each frame, for each camera, in the variant `holistic`. |

These two are the only full-frame copies that the search found in `_runtime/`. Two more places are
in the sidecar preprocessing, outside `_runtime/`:

- `skellytracker/core/detectors/processing/pre/resize_interpolation.py:45`:
  `return np.ascontiguousarray(image, dtype=COMPUTE_DTYPES[compute_dtype])`. No copy for a
  contiguous uint8 frame with `compute_dtype: uint8`. A full-frame float32 copy with
  `compute_dtype: float32`.
- `skellytracker/core/detectors/processing/pre/resize_affine_crop.py:154`:
  `np.ascontiguousarray(image)`. A copy only for a frame that is not contiguous.

**One place keeps an image with no copy.** `_runtime/executor.py:391` stores each `@prev` port:
`self.prev[camera_id].update({port: values[camera_id][port] for port in self.prev_ports})`. Today
`trigger.image@prev` or the `value@prev` of a gated image loads. The run then holds the frame
buffer of the host for one more frame. When the host uses the buffer again, the "previous image" is
silently the new image. Only `frame.image@prev` is refused today (`V-pipeline.graph-2`).

**What the rule "never copy" needs:**

1. A sentence in `pipeline.graph`: an `image` value is a reference to the frame of the host. A glue
   node passes the same object or gives the empty value. No node type makes a new image.
2. A new load rule: an `@prev` input must not name a port of the type `image`.
3. No tap and no output of the type `image` (as today).
4. A test that follows the frame object to each consumer with `is`.
5. A decision on the two MediaPipe conversions (question Q16). MediaPipe needs RGB, and the host
   gives BGR, so each landmarker call needs one conversion. The rule can cover only the pipeline
   plumbing, or one conversion can serve each `mediapipe_tasks` node of a camera on a frame.

## 9. Consequences

### 9.1 Decision entries

[ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) and
[ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) are
superseded by [ADR-W5QD](../../../decisions/entries/W5QD-pipeline-entries-consolidation.md), which
restates them. [ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) is
superseded and needs no change. The accepted entry of this redesign changes these rules:

| Entry | Item | Change |
|---|---|---|
| [ADR-W5QD](../../../decisions/entries/W5QD-pipeline-entries-consolidation.md) | Item 1, the rules of [ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6 | The closed set of glue nodes changes. The trigger is a flag, not an image. `concat` goes. |
| [ADR-W5QD](../../../decisions/entries/W5QD-pipeline-entries-consolidation.md) | Item 2, the rules of [ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) items 1 and 7 | "The `outputs:` block maps public names to ports" goes. The result holds the three deliverables. The port type list of the load checks changes. |
| [ADR-W5QD](../../../decisions/entries/W5QD-pipeline-entries-consolidation.md) | Item 3, text on the built-ins and the annotator | The annotator draws the external values. |
| [ADR-4WR9](../../../decisions/entries/4WR9-params-schema-in-the-node-catalog.md) | Item 3 | `any_from` names the inputs that give an output its type. The type `any` goes. The catalog gives the accepted types of each input. |
| [ADR-2RWC](../../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md) | Item 6 | The outputs `detector_box` and `crop_box` become the one deliverable `boxes`. Items 1 to 5 stay for the internal type. |
| [ADR-97X9](../../../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) | Items 1 and 5 | The row rule of `concat` moves to `merge`. The `any` rule becomes "the output has the type of an input that is not `@prev`". |
| [ADR-4MP6](../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md) | Items 2, 3, 5 and 7 | The groups of `merge` and `concat`. The output schema loses `canonical_names`. The side of a hand also comes from the input name of `merge`. Core does not call `to_canonical`. The sentence "No param such as `form: canonical` selects the canonical form" stays true: the input name of the `output` node selects it. |
| [ADR-PX6Z](../../../decisions/entries/PX6Z-keypoint-raw-score-in-the-pipeline-result.md) | Item 2 | The result of a camera has no `raw_score`. The ports and the taps keep it. Items 3 and 4 stay. |
| [ADR-RA0E](../../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) | Items 4 and 6 | The trigger gives a flag. The drawn box is the deliverable `boxes`. It stays not clipped. |
| [ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) | Each item | The node gets the name `assign_keypoints`. No rule changes. |
| [ADR-Q5BN](../../../decisions/entries/Q5BN-node-ran-in-the-camera-result.md) | Item 5 | The rule of the reserved output names goes with the free output names. Items 1 to 4 stay. |
| [ADR-6DKT](../decisions/entries/6DKT-instance-rows-carry-class-and-score.md) | Item 5 | The empty-input rule of `concat` moves to `merge`. |
| [ADR-TH8E](../../../decisions/entries/TH8E-one-person-in-v2.md) | none | No change. A flag has no rows. |
| [ADR-3SF2](../../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md), [ADR-271H](../../../decisions/entries/271H-pipeline-bundles.md) | none | No change. The landing is "another pipeline spec edit" of the skill `change-pipeline-spec`. |

Three more entries state rules that this redesign touches. Read them before the landing:
[ADR-QD6G](../../../decisions/entries/QD6G-canonical-edges-in-the-output-schema.md) (the field
`canonical_edges`), [ADR-JHB3](../../../decisions/entries/JHB3-keypoints-xy-and-z-and-image-width-and-height.md)
(the fields of a `keypoints` value) and
[ADR-Y753](../../../decisions/entries/Y753-pipeline-templates-glue-vectors-and-taps-flag.md) (the
vector file of `concat`).

### 9.2 Spec sections, rules, vectors and schema

| Place | Change |
|---|---|
| `graph.md` | The node type list; the port type table; Behaviour items 4, 5, 6 and 7; the "source-image pixels" rule; the image rule. |
| `outputs.md` | The `outputs` field goes. New: the external values, the result keys, the output schema of the `output` node. Behaviour items 6, 7 and 9. |
| `running.md` | Item 5 names no new temporal node. The text on `set_params` does not change. |
| `taps.md`, `timing.md`, `file.md` | The lines for `tensor` go. `pipeline_sha256` hashes `schema_version` and `nodes`. `V-pipeline.file-4` loses `outputs`. The node type `output` and `flag_when` get the span `run`. |
| `nodes/` | New: `output.md`, `flag_when.md`, `assign_keypoints.md` (from `merge.md`). Rewritten: `merge.md`. Deleted: `concat.md`. Changed: `onnx_model.md`, `mediapipe_tasks.md`, `gate.md`, `first_of.md`, `redetect_trigger.md`. |
| `README.md`, `changelog.md`, `inventory.yaml`, `templates/` | The section map, the terms "glue node" and "frame", the validation index, one changelog row, the two templates. |
| `reference/` | `pipeline_config.py`; `node_gate.py`, `node_redetect_trigger.py`; new `node_flag_when.py`, `node_assign_keypoints.py` (from `node_merge.py`), new `node_merge.py`; `node_concat.py` goes. |
| `vectors/` | `node.gate.yaml` (cases with an image condition, new flag cases), `node.redetect_trigger.yaml` (the output), `node.first_of.yaml`; new `node.flag_when.yaml`, `node.merge.yaml`; `node.merge.yaml` of today becomes `node.assign_keypoints.yaml`; `node.concat.yaml` goes. |
| `pipeline.schema.json` | Both copies, from `tools/make_pipeline_schema.py`. The two files are equal today. |
| The 5 examples and the 2 built-ins | The form of [section 7](#7-the-pipelines-in-the-new-form). |

Validation rules. A removed ID is not used again, as the spec does for `V-node.smooth_keypoints-2`.

| Rule | Change |
|---|---|
| `V-pipeline.graph-3` | New wording: the type of the connected output must be in the accepted types of the input. |
| `V-pipeline.graph-5`, `-6` | `first_of` is the only variadic type. |
| `V-pipeline.graph-9` | New wording, with no `any`. |
| New `V-pipeline.graph-12` | An `@prev` input must not name a port of the type `image`. |
| `V-pipeline.outputs-1`, `-3` | Removed. |
| New `V-pipeline.outputs-4` | A file has exactly one `output` node, with one input or more, with no `@prev` and not the frame. No input of another node names the `output` node. |
| New `V-pipeline.outputs-5` | The `holistic` input has the groups `body`, `right_hand`, `left_hand`, `face`. The `wholebody` input has a group `body`. |
| New `V-pipeline.outputs-6` | The rotation rule of question Q3. |
| New `V-node.onnx_model-6`, `V-node.mediapipe_tasks-3` | `run_if` is a `flag`. `mediapipe_tasks` with `variant: holistic` has no `run_if`. |
| `V-node.gate-2`; new `V-node.gate-4` | `is_set` and `is_not_set` need a `flag` condition. A condition is not an `image`. |
| `V-node.concat-1` to `-3` | Removed with the node. |
| `V-node.merge-1` to `-5` | Become `V-node.assign_keypoints-1` to `-5`. The new `merge` starts at `V-node.merge-6`, so that no ID gets a new meaning. |
| New `V-node.flag_when-1` | `score_above` needs `threshold`, and the other modes have none. |

### 9.3 Hashes and taps

- `pipeline_sha256` hashes `schema_version`, `nodes` and `outputs` today
  (`skellytracker/core/pipelines/timing.py:62`). The hash of each pipeline changes.
- `upstream_sha256` hashes the config of a node and of each node upstream of it
  (`timing.py:65-83`). It changes for `trigger`, for `person` and for each node downstream of them.
  A replay compares it (`_runtime/taps.py:32`), so each recorded tap of `yolox-rtmw-wholebody`
  stops to replay. Version 2.0.0 is not released, so no released tap breaks.
- A tap names an internal port. The external values have no tap. The COCO evaluation of skellybench
  reads the 133 native points from a tap, so it does not change.
- No hash holds the canonical mapping of the landmark schema registry. The delivered `wholebody`
  value depends on that mapping. This is true today for the `to_canonical` call of Core.

### 9.4 Package code and tests

`config.py` and its copy `specs/pipeline/reference/pipeline_config.py`; `values.py`; `canonical.py`;
`nodes.py` (the accepted types of a port); `annotate.py`; `cli.py`; in `_runtime/`: `executor.py`
(`_stops`, the result assembly at line 377, the output check at lines 109-114), `resolve.py`,
`taps.py`, `node_gate.py`, `node_redetect_trigger.py`, `node_merge.py`, `node_concat.py`,
`mediapipe_tasks.py`. Tests: each file of `skellytracker/tests/pipelines/`, and in `tools/tests/`:
`test_pipeline_schema.py`, `test_pipeline_node_catalog.py`, `test_pipeline_package_schema.py`,
`test_vectors.py`, `test_examples.py`.

### 9.5 freemocap

**Core.** The one boundary is `observations_from_results` in
`freemocap/core/tracking/pipeline_runs.py`. Its readers get the observation type of freemocap and
do not change.

| Line | Today | After |
|---|---|---|
| `:27`, `:30` | `RTMW_NODE = "wholebody"`, `HOLISTIC_NODE = "holistic"`, used as output names | The same strings are the keys of the result. No change. |
| `:28`, `:170` | `PERSON_NODE = "person"`; `result["node_ran"][PERSON_NODE]` | The node id from `output_schema["boxes"]["instance_source"]`. |
| `:29` | `CROP_BOX = "crop_box"` | `"boxes"`. |
| `:117`, `:130` | `canonical_names`, `canonical_edges` of the schema | `point_names`, `edges`. |
| `:153`, `:159-160` | `to_canonical(result[RTMW_NODE], output_schema[RTMW_NODE])` | The result value, with no call. `present` comes from the same value. |
| `:165-168` | `cx, cy, w, h, _ = crop.boxes[0]`, then clip and `int()` | `x1, y1, x2, y2 = boxes.xyxy[0]`, then the same clip and `int()`. |
| `:48` | The size of the node `wholebody` | No change. |

`freemocap/tests/test_pipeline_runs.py` builds `InstanceKeypoints` and `InstanceBoxes` values for
the result. It must build the external values.

**The pipeline metrics.** Core makes each stage name from the timing event:
`stage = f"{record['node_id']}.{record['span']}"`
(freemocap `freemocap/core/pipeline/pipeline_timing_events.py:60`). No Core code holds a node id of
the built-in. Only tests and fixtures hold `person.inference`, `wholebody.inference` and `crop.run`,
for example freemocap `freemocap-ui/src/components/pipeline-metrics/pipelineTaskTopology.test.ts:20-23`.
This redesign renames no node of a built-in and no span, so nothing breaks. One stage is new:
`output.run`. Core turns on each span of the catalog
(freemocap `pipeline_runs.py:72-73`), so the stage appears with no change in Core.

**The editor** (`freemocap-ui/src/pipeline-editor/`, read on the branch `pipeline-gui`):

- The three fixtures in `fixtures/` come again from the new catalog and the new examples.
- `flow-graph.ts:45` has a colour for `tensor` and none for `flag`.
- `flow-graph.ts:75-77` draws the card `outputs` from `config.outputs`, with the port `NEW_OUTPUT`.
  The `output` node is a node of the catalog, so the card and its special cases can go
  (`PipelineEditor.tsx:114`, `:124`; `Inspector.tsx:106`).
- `pipeline-model.ts:68-82` gives an `any` output its type from `any_from`. `pipeline-model.ts:168`
  and `PipelineEditor.tsx:118` compare one expected type. They must test the accepted types.
- `NodeCard.tsx:13` shows "optional" for an input. The named inputs of `merge` and `output` use it.

### 9.6 Risks

- `run_if` on a `mediapipe_tasks` node skips frames of a VIDEO-mode landmarker. The measurement of
  [ADR-6JWJ](../decisions/entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md) found that a
  landmarker finds a person again after a gap. It did not measure a landmarker that gets no frame
  for a time.
- The new `merge` has no measured pipeline. Its two examples are structure only.
- The `wholebody` deliverable is canonical only for a registered schema. Today the registry has one
  schema, `COCO_WholeBody`.

## 10. Build order

Each stage is one commit group that passes `tools/run_checks.py` on its own. The sizes are rough:
S is less than 150 changed lines, M is 150 to 500, L is more than 500. The lines of spec text,
vectors and tests count.

| Stage | Content | Size | Can wait until after the 2.0.0 pre-release |
|---|---|---|---|
| 1 | The type `flag`; `tensor` and `any` go; accepted types in the reference model, `config.py`, the catalog, the schema and `graph.md`. No file changes its behaviour. | M | No: it changes the catalog that the editor reads. |
| 2 | `redetect_trigger.redetect`; `run_if` on `onnx_model` and `mediapipe_tasks`; the `gate` modes `is_set` and `is_not_set`; the built-in and the two examples with a trigger; the vectors of `gate` and `redetect_trigger`. The box parity test must pass. | L | No: it changes the file of a built-in. |
| 3 | The image rule: the load rule for `@prev`, the test with `is`, the spec text. | S | No: it is small, and it closes a silent error. |
| 4 | The `output` node; the external values; the rotation rule; the output schema; the key `outputs` goes; each example, each built-in, the templates, `annotate.py` and `cli.py`. | L | No: it changes the result that Core reads. |
| 5 | freemocap Core: `pipeline_runs.py` and its tests. It lands with stage 4. | S to M | No. |
| 6 | `merge` with four inputs; `assign_keypoints`; `concat` goes; the two examples. | L | Yes: no built-in uses these nodes. A rename after a release costs more. |
| 7 | `flag_when`: the section, the reference module, the vectors, the runtime. | M | Yes: no file needs it. |
| 8 | The editor: the fixtures, the flag, the accepted types, the `output` node. | M | Yes: it follows the catalog. |
| 9 | `hand_boxes`; one RGB conversion for each frame; a `flag.jsonl` tap form. | M | Yes: with the decomposed MediaPipe work. |

Stages 1 to 5 are the least that gives Core the new result. Stages 2 and 4 can change places.

## 11. Open questions

Each question is one decision. The first option is the recommendation. "Blocks" means that the
design of a stage cannot start without the answer. "Default" means that the work can start with the
recommendation, and the answer can change it later at a small cost. The questions with the largest
effect come first.

**Q1 — Shall the output be a node type `output` in `nodes`, in place of the `outputs` block?**
(Blocks stage 4.)

**Yes:** the file has `- {id: output, type: output, inputs: {wholebody: wholebody.keypoints, boxes: crop.boxes}}`
and no key `outputs`. The catalog gives the editor its ports, as for each node.
- "`outputs` | mapping | yes | Public output name (a name) to port reference" becomes\
  -> removed

**No, keep the block:** the file keeps `outputs: {wholebody: wholebody.keypoints, boxes: crop.boxes}`.
Only the three names are legal. The file format, the schema and `pipeline_sha256` keep the key. The
editor keeps its special card. This is about half of the work of stage 4.

Changes: [ADR-W5QD](../../../decisions/entries/W5QD-pipeline-entries-consolidation.md) changed
(both); [ADR-Q5BN](../../../decisions/entries/Q5BN-node-ran-in-the-camera-result.md) changed (yes).

➡️ **Yes**, because your words are "The output node type", and one catalog then describes each
card of the editor.

**Q2 — Shall `wholebody` mean "the canonical skeleton names" and `holistic` mean "the four
MediaPipe Holistic groups"?** (Blocks stage 4.)

**Yes:** the input name of the `output` node selects the form. `wholebody` gives canonical names,
for example `left_hand/thumb_cmc` for the RTMW point `left_hand/left_thumb1`. `holistic` gives the
groups `body`, `right_hand`, `left_hand`, `face` with their MediaPipe names, 553 points.

**No, one form:** the result has one keypoint deliverable, `keypoints`, always canonical. The
built-in `mediapipe-holistic-tasks` then gives `keypoints` too, and Core selects its mapping from
the pipeline that it started, not from the name.

**No, the names are only labels:** `wholebody` and `holistic` take each keypoint set, with no check
of its groups.

Changes: [ADR-4MP6](../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md)
changed (each option).

➡️ **Yes**, because Core has these two paths today, and the names of the two results do not change.

**Q3 — Shall the load refuse a file whose output box can be rotated?** (Blocks stage 4.)

**Yes, refuse:** a file with `boxes_from_points` and `target_rotation_deg: 90` upstream of
`output.boxes` does not load. The error names the node. The output node never changes a box.

**No, convert:** the same file loads. The output node gives the axis-aligned box that encloses the
rotated box. The delivered box is then larger than the box that the model crops.

**Refuse, with a param to convert:** as "Yes", and `params: {rotated: enclose}` on the output node
selects the conversion.

Changes: [ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) (each
option).

➡️ **Yes**, because your answer to the question about the conversion was "a rotated box is not
permitted as an output box". A refusal can become a conversion later, and no file breaks.

**Q4 — Shall "replace" in `merge` mean: a part replaces the group of `body` with its name, and
`map` replaces single points?** (Blocks stage 6.)

**Yes:** with RTMW as `body`, `left_hand: hand.keypoints` replaces the 21 points of the group
`left_hand`. With a body model of 17 points, the same input adds the group `left_hand`. The body
wrist changes only with `map: {body/left_wrist: left_hand/root}`.

**No, also the same joint:** the hand wrist also replaces `body/left_wrist` with no `map`. The
landmark schema files must then say which body point is which hand point. They do not say it today.

**No, add only:** a part never replaces a point. The node is then the `concat` of today with names.

Changes: [ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) and
[ADR-4MP6](../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md) changed
(each option).

➡️ **Yes**, because it uses the replace rule and the `map` that the spec already has.

**Q5 — Shall `concat` go?** (Blocks stage 6.)

**Yes:** `rtmpose-body-hands-face` uses `merge` with `body`, `right_hand`, `left_hand` and `face`.
A file with `type: concat` does not load.

**No:** `concat` stays for a list of keypoint sets with other names than the four parts, for example
a body set and a feet set.

Changes: [ADR-W5QD](../../../decisions/entries/W5QD-pipeline-entries-consolidation.md),
[ADR-97X9](../../../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md)
and [ADR-6DKT](../decisions/entries/6DKT-instance-rows-carry-class-and-score.md) changed (yes).

➡️ **Yes**, because no built-in and no example needs a fifth part.

**Q6 — Shall the position matching of today's `merge` stay, as the node `assign_keypoints`?**
(Default.)

**Yes:** `rtmpose-hand-detector` keeps its node, with `type: assign_keypoints`. No rule changes.

**No, drop it:** the node, its vector file and the example `rtmpose-hand-detector` go. A hand
detector on the full frame is then not possible in 2.0.0.

Changes: [ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md)
changed (yes) or superseded (no).

➡️ **Yes**, because it is a rename of code that has vectors and tests, and the other option deletes
a capability.

**Q7 — Shall an empty flag pass no gate mode except `is_empty`, and start no node?** (Default.)

**Yes, strict:** `is_set` passes only on true. `is_not_set` passes only on false. `run_if` runs the
node only on true. For example, `run_if: lost.flag@prev` does not run the node on frame 0.

**No, empty counts as false:** `is_not_set` passes on false and on empty. `run_if` does not run on
empty. The third state then changes a result only with `is_empty` and `is_present`.

**No, an empty `run_if` runs the node:** "no decision" means "no limit". This is against the rule
of today that an empty input stops a node.

Changes: [ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) (each
option).

➡️ **Yes**, because it is the only option in which each of the three states has its own result at
a gate, and no model runs on a flag that nothing decided.

**Q8 — Shall the converter node be `flag_when`, with the input `value`, the output `flag` and the
three tests of `gate`?** (Default; blocks only stage 7.)

**Yes:** `{id: lost, type: flag_when, inputs: {value: body.keypoints@prev}, params: {mode: is_empty}}`
gives true when the person is lost.

**No, another name:** `to_flag`, with the same ports and params.

**No, one node for each test:** `flag_when_empty` and `flag_when_score_above`. Two node types, no
`mode` param.

Changes: [ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) (each
option).

➡️ **Yes**, because the node then uses the test code and the vector cases of `gate`.

**Q9 — Is this the meaning of your answer on `run_if`: `onnx_model` and the `mediapipe_tasks`
variants `body`, `hand` and `face` take it, and the variant `holistic` does not?** (Default.)

**Yes:** `{type: mediapipe_tasks, inputs: {image: frame.image, run_if: trigger.redetect}, params: {variant: holistic}}`
does not load.

**No, `onnx_model` only:** no `mediapipe_tasks` node takes `run_if`.

Changes: [ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) (both).

➡️ **Yes**, because it is the reading that uses each part of your sentence.

**Q10 — Shall the type `any` go, with a list of accepted types on each input?** (Default; blocks
only the wording of stage 1.)

**Yes:** `gate.condition` accepts `boxes`, `keypoints` and `flag`. `condition: frame.image` does
not load.

**No, keep `any`:** `gate` and `first_of` stay as they are. Only the modes `is_set` and `is_not_set`
get a load check. The catalog, the schema and the editor change less.

Changes: [ADR-4WR9](../../../decisions/entries/4WR9-params-schema-in-the-node-catalog.md) and
[ADR-97X9](../../../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md)
changed (yes).

➡️ **Yes**, because an `any` input validates nothing, and you asked for each input to be validated.

**Q11 — Shall the hand box node wait, with two `boxes_from_points` nodes for now?** (Default.)

**Yes:** the examples keep `right_hand_box` and `left_hand_box`. `hand_boxes` comes with the
decomposed MediaPipe work, when its box rules are measured.

**No, add `hand_boxes` now:** one node with the outputs `left_hand` and `right_hand` and the params
`left` and `right`. One new node type with a section, a reference module and vectors. The boxes are
the same.

Changes: [ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) (both).

➡️ **Yes**, because the node adds no behaviour, and the decomposed MediaPipe pipeline is later work.

**Q12 — Shall the delivered keypoints have `present` and `instance_score`, and no `raw_score` and
no `track_ids`?** (Default.)

**Yes:** `result["holistic"].raw_score` does not exist any more. A caller that needs it records a
tap on `holistic.keypoints`.

**No, keep `raw_score`:** `CanonicalKeypoints` gets `raw_score`. A computed canonical point, for
example `body/neck_center`, has no decode score, so the field needs a rule for it.

Changes: [ADR-PX6Z](../../../decisions/entries/PX6Z-keypoint-raw-score-in-the-pipeline-result.md)
changed (yes).

➡️ **Yes**, because Core does not store `raw_score`, and each `track_ids` value is -1.

**Q13 — Shall Core keep `detector_ran` from `node_ran`, with the node id from the output schema?**
(Default.)

**Yes:** Core reads `node_ran[output_schema["boxes"]["instance_source"]]`, which is `person` for the
built-in. The output node delivers no flag.

**No, a field of the result:** the result gets `detector_ran`, a boolean that the output node sets.
The output node then needs a rule for a pipeline with two detectors.

Changes: [ADR-Q5BN](../../../decisions/entries/Q5BN-node-ran-in-the-camera-result.md) not changed
(yes) or changed (no).

➡️ **Yes**, because the run already records which node ran, also for a pipeline with no trigger.

**Q14 — Shall the port type `tensor` go?** (Default.)

**Yes:** `PORT_TYPES` has `image`, `boxes`, `keypoints` and `flag`. The tap form `<image_id>.npy`
goes from the spec.

**No:** the name stays, with no node that uses it.

Changes: [ADR-W5QD](../../../decisions/entries/W5QD-pipeline-entries-consolidation.md) changed (yes).

➡️ **Yes**, because no node type has a `tensor` port.

**Q15 — Shall a tap on a `flag` port be refused?** (Default.)

**Yes:** `taps: [{name: t, port: trigger.redetect, action: record}]` does not load, as a tap on an
`image` port today.

**No, a `flag.jsonl` form:** one line for each frame and camera, with `flag: true`, `false` or
`null`. A replay of the trigger is then possible.

Changes: [ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) (both).

➡️ **Yes**, because no use needs the file now, and the form can come later.

**Q16 — Shall "never copy an image" cover the pipeline plumbing, and not the conversion that a
model needs?** (Default.)

**Yes:** the ports, `gate`, `first_of`, `@prev` and the taps never copy an image, and a test proves
it. Each `mediapipe_tasks` node still makes one RGB copy of the frame for its landmarker.

**No, one conversion for each frame:** the run makes the RGB frame one time for a camera and gives
it to each `mediapipe_tasks` node. Three Tasks nodes then cost one copy, not three.

**No, the host gives RGB:** a run parameter says that the frame is RGB. Core must then convert, or
the camera must give RGB.

Changes: [ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) (each
option).

➡️ **Yes**, because each built-in has at most one MediaPipe node, so the second option saves
nothing today.

**Q17 — When a part replaces a group of `body` and the part row is not present, shall the group
keep the points of `body`?** (Default; blocks only stage 6.)

**Yes, keep:** with RTMW as `body`, a frame with no left hand box keeps the RTMW points of
`left_hand`.

**No, missing:** the 21 points are NaN with the score 0 on that frame, as a replaced group of
today's `merge` with no matched row.

Changes: [ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md)
changed (yes).

➡️ **Yes**, because a hand model that does not run must not delete the hand of the body model.

**Q18 — Shall stages 1 to 5 land before the 2.0.0 pre-release?** (Blocks the plan, not the design.)

**Yes:** the pre-release has the new file form and the new result. Stages 6 to 9 come after it.

**No, all after:** the pre-release has the file form of today. Each pipeline file of an exporter
that the pre-release loads must then change later.

**No, all before:** also `merge`, `flag_when` and the editor. The pre-release waits for them.

Changes: none.

➡️ **Yes**, because a change of the file form after a release costs each user of the release.

**Q19 — Shall the editor draw the `output` node as one more node card?** (Default; ask it after Q1.)

**Yes:** the special card `outputs` and its port "new output" go. The card of the `output` node has
three inputs, each "optional".

**No:** the editor keeps a special sink card, and fills it from the `output` node.

Changes: none in skellytracker.

➡️ **Yes**, because it deletes code in the editor.

**Points with no question.** These follow from the answers above, and the user did not react to
them: no port gets a new name except `redetect`; `last` of the trigger stays the frame of the last
request, and `onnx_model` gets no `ran` output; `merge` has no output-format param, because the
`output` node sets the form; the MediaPipe landmark schemas stay open work of stage 2.2, so
`holistic` passes its names through until then.

## 12. Checked and not checked

**Checked.** Each `path:line` of this file was opened on commit 3c83a5b0 of skellytracker, on the
branch `sidecar-implementation` of freemocap or on the branch `pipeline-gui`, and the quoted line
was read there. Two facts were measured with `check_pipeline` of this commit: the counts 133, 137
and 553 of section 6, and the `instance_source` `person` of `crop.boxes`. The two schema copies were
compared with `diff`. The decision-log check and the document tests ran on the two new files.

**Not checked.**

- The behaviour claims of section 7 are reasoned from the code. No code was changed, so no test ran
  on the new form.
- The control signals of `hold_boxes`, `smooth_boxes`, `smooth_keypoints` and today's `merge` in
  the table of section 5 come from the flag inventory. Their node modules were not read in full.
- The vector files were not read. Section 9.2 names them from their file names and a word count.
- `annotate.py`, `cli.py`, `catalog.py`, `loading.py` and `run.py` were not read. Section 9.4 names
  them from their role.
- The entries [ADR-QD6G](../../../decisions/entries/QD6G-canonical-edges-in-the-output-schema.md),
  [ADR-JHB3](../../../decisions/entries/JHB3-keypoints-xy-and-z-and-image-width-and-height.md) and
  [ADR-Y753](../../../decisions/entries/Y753-pipeline-templates-glue-vectors-and-taps-flag.md) were
  not read in full.
- In the editor, only the lines that section 9.5 names were read. The fixtures were not read.
- In freemocap, the readers after `observations_from_results` were not read. The box-coordinate
  trace states that they use `x1, y1, x2, y2`.
- No measurement exists of a `mediapipe_tasks` landmarker that `run_if` stops for some frames.
- The sizes of section 10 are estimates.

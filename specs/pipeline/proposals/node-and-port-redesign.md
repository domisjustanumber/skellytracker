# Proposal: redesign of the pipeline node types and port types

This file uses ASD-STE100 Simplified Technical English.

This file is an informative proposal. It is not spec text. It changes no code, no spec section, no
schema, no example and no built-in pipeline. The entry
[ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) records the rulings
of the user and has the status `accepted`. The build stages of [section 10](#10-build-order) write
the design into the spec and the code.

**Home of this file.** [Change a node type](../contributions.md#change-a-node-type) gives
`specs/pipeline/proposals/<slug>/` as the record folder of a `proposal` bundle. That record is a byte
copy of a bundle, and it holds only `node.<type>` sections. This redesign is not a bundle, and it
also changes the sections `pipeline.graph`, `pipeline.outputs` and `pipeline.taps`. Thus this file is
one file beside the record folders. `tools/intake_bundle.py` reads only the folders of `proposals/`.

**Baseline.** Each code fact is from commit 3c83a5b0. A `path:line` with no repository name is a
path in skellytracker. "Core" is freemocap Core, on the branch `sidecar-implementation` of freemocap.
"The editor" is the pipeline editor of freemocap, on the branch `pipeline-gui`.

**Authority.** The user gave the rulings of [section 2](#2-the-rulings) on 2026-11-17. They are
decided. A sentence in quotation marks is the wording of the user. Each other statement is the
design that applies the rulings. [Section 11](#11-decided-and-still-open) gives the points that no
ruling settles, each with a default.

## 1. The design in short

- Four internal port types: `image`, `boxes`, `keypoints` and the new type `flag`. The types
  `tensor` and `any` go. Each input lists the types that it accepts.
- A `flag` is a boolean: true or false. It has no empty state.
- The only image is the camera frame, `frame.image`. No node gives an image. No node gates an
  image. No tap and no `@prev` reads an image.
- `redetect_trigger` gives the flag `redetect`. `run_if` on a model node is the only way to stop a
  detector.
- `gate` passes boxes or keypoints. Its condition is boxes, keypoints or a flag, with the new modes
  `is_true` and `is_false` for a flag. `first_of` selects between boxes or between keypoints.
- `flag_when` makes a flag from boxes or keypoints.
- `merge` gets four named inputs and a required `format`. `concat` goes. The position matching of
  today's `merge` stays as the node `assign_keypoints`.
- The output is the `outputs` block, not a node type. Each file must have it. Its only keys are
  `wholebody`, `holistic` and `boxes`. The conversion to the delivered forms happens at this block.
- Core reads only the outputs. The delivered `boxes` carry `detector_ran` for each row.
- The two built-in pipelines keep their tracking behaviour. The result that Core reads changes its
  form.

**Cost, stated plainly.** The node count does not go down. Today the spec has 11 node types. This
design has 12 (`concat` goes; `flag_when` and `assign_keypoints` come). The port type count goes
from 5 to 4.

## 2. The rulings

The user gave each ruling on 2026-11-17. Rulings with quotation marks keep the spelling of the user.
A ruling with no quotation is from the question-and-answer session of the user with the supervisor
session on that day. This file does not have the words of the user for it.

| # | Ruling | Words of the user | Reverses |
|---|---|---|---|
| 1 | Internal port types: `image`, `boxes`, `keypoints`, `flag`. `tensor` and `any` go. Each input lists the types that it accepts. | "I would like to have a minimal number of different inputs and outputs on nodes." "Whatever is plugged into each input is then tested and validated to be of that type and flagged or blocked if it is not." | |
| 2 | A `flag` is true or false. It has no third state. Each node that gives a flag always runs and always gives true or false, also when a previous-frame input is empty. No first-frame param. | | **Reverses** "1 - three" (three states). The user dropped the third state. |
| 3 | Internal boxes can have rotation, score and presence. They are in source-image pixels at each node output. | "Internally in the pipeline, boxes can have rotation, score, presence and must always be converted to source image scaling on output from a node." | |
| 4 | An image is only the camera frame. No node gives an image output. `gate` and `first_of` do not accept an image. The plumbing never copies an image, and a test proves it. The one BGR to RGB conversion of each `mediapipe_tasks` node is allowed. A tap on an image port is not allowed, and the array-file tap form leaves the spec. | "Image datatypes remain. They must never copy images in memory as it is expensive." "a detector must not have a gated image, the only thing that gates it is the flag" On image taps: "the caller already has it and it's expensive to tap" | **Reverses** "2 - allow and create the new node" for the part "allow". The new node stays (ruling 8). |
| 5 | `@prev` is allowed only on `boxes` and `keypoints` ports. It is refused on a `flag` port and on an image. | | |
| 6 | `redetect_trigger` reads the previous boxes and keypoints and gives the flag `redetect`. It loses its image input and its image output. It keeps `last`. No other port gets a new name. | | |
| 7 | `run_if` is a flag input that runs the node only on true. It is on each `onnx_model` of each role, and on the `mediapipe_tasks` variants `body`, `hand` and `face`. It is not on the variant `holistic`. `run_if` is the only way to stop a detector. `onnx_model` gets no "ran" output. | "3 - onnx-only for the holistic task. For individual hand/face/body tasks it is permitted." | |
| 8 | The converter node is `flag_when`: input `value` (boxes or keypoints), output `flag`, with the three tests of `gate` for data. | | |
| 9 | `gate`: `value` is boxes or keypoints. `condition` is boxes, keypoints or a flag. A flag condition has the modes `is_true` and `is_false`. `is_present` and `is_empty` are refused on a flag. `gate` never passes a flag. | The new names are "for clarity". | **Reverses** the names `is_set` and `is_not_set` of "4 - add new names". |
| 10 | `first_of` selects between boxes or between keypoints, all inputs of one type. It never selects between flags. | | |
| 11 | `merge`: inputs `body` (required), `left_hand`, `right_hand`, `face` (optional), the same instance, row for row. A part replaces the group of its name in `body`, or adds it. A part with no present row on a frame leaves the points of `body` for that group. A required param `format: wholebody` or `format: holistic`. An optional `map` for single points. Nothing else is configurable. | "a merge node would have 4 inputs - body, left_hand, right_hand, face" "This merge will replace existing keypoints on the body." "merge node keeps its output format param" | **Reverses** the point of the first form of this file that `merge` has no output-format param. |
| 12 | `concat` goes. The position matching of today's `merge` stays as the node `assign_keypoints`. | "I am unclear on where concat would be used." | |
| 13 | No hand box node. It is dropped, not deferred. | "the existing boxes_from_points node can do what I want" | **Reverses** the hand ROI node of the hand example of the user. |
| 14 | The output is not a node type. Each pipeline file must have the `outputs` block. Its only keys are `wholebody`, `holistic` and `boxes`, with one or more. The conversion happens at this block. A file with another output name does not load. | "a block. Every pipeline must have the output block" | **Reverses** "The output node type converts output data to holistic, wholebody, boxes (whichever combination is appropriate)." for the part "node type". The three deliverables stay. |
| 15 | The delivered keypoints carry `present` and `instance_score`, and no `raw_score` and no `track_ids`. | | |
| 16 | The delivered `boxes` carry, for each row, corners, score, class, presence and `detector_ran`. Core reads only the outputs. It reads no `node_ran`, and it has no literal node id. | | |
| 17 | A pipeline whose output box can be rotated is refused at load. The output never changes a box. | "a rotated box is not permitted as an output box." | |
| 18 | Later work, to record: look into one canonical output keypoint set that becomes the only output format of a pipeline. | | |
| 19 | Taps are on `boxes`, `keypoints` and `flag` ports. A flag tap is one line for each frame and camera, with `true` or `false`. | | |
| 20 | Before the 2.0.0 pre-release: the flag type and the accepted-type lists; the trigger flag and `run_if`; the image rule; the `outputs` block with the delivered forms; the reader of Core. After it: the new `merge`, `flag_when`, `assign_keypoints` and the editor. | | |
| 21 | Build order now: the first three parts are built in parallel with other work. The `outputs` change and the reader of Core wait until the pipeline-metrics stage of freemocap is in the hands of the user. | | |

Two standing constraints apply. v2.0.0 tracks one person
([ADR-TH8E](../../../decisions/entries/TH8E-one-person-in-v2.md)). The decomposed MediaPipe pipeline
is later work. The drawing of the outputs in the editor is not in the scope of this file: the user
handles the editor with another session.

## 3. Port types

### 3.1 Internal types

| Type | Value in Python | Empty value | Change |
|---|---|---|---|
| `image` | The frame array of the host, `(H, W, 3)`, BGR, uint8. A reference, never a copy. | None: the frame is never empty. | Only the port `frame.image` has this type ([section 8](#8-the-image-rule)). |
| `boxes` | `InstanceBoxes` | No present row | No change. |
| `keypoints` | `InstanceKeypoints` | No present row | No change. |
| `flag` | `True` or `False` | None: a flag is never empty. | New. |

`InstanceBoxes` keeps its fields (`skellytracker/core/pipelines/values.py:78`):

| Field | Shape | Meaning |
|---|---|---|
| `boxes` | `(I, 5)` | `(cx, cy, w, h, rotation)` in source-image pixels. `rotation` is in radians, clockwise, in `[-pi, pi)`. |
| `instance_score` | `(I,)` | The score of the row. |
| `class_index` | `(I,)` | The class index of a detector row, else -1. |
| `present` | `(I,)` | True for a present row. |
| `track_ids` | `(I,)` | -1 in this version. |

`InstanceKeypoints` keeps its fields (`values.py:23`): `point_names` `(P,)`, `xy` `(I, P, 2)`,
`score` `(I, P)`, `raw_score` `(I, P)`, `instance_score` `(I,)`, `present` `(I,)`, `track_ids`
`(I,)` and `z` `(I, P)` or `None`.

**Source-image scale (ruling 3).** Each `boxes` and `keypoints` output of each node is in
source-image pixels. The docstring states it today (`values.py:79`: "in source-image pixels"). No
node gives a box in the space of a crop or of a model input. The spec gets this sentence as a rule,
and a test checks the box of each node type against a known frame. One fact stays as today: the
sidecar `crop_policy` makes the crop larger than the box right before the warp, and no port shows
that larger area.

**`tensor` goes.** No node type has a `tensor` port. The name is only in `PORT_TYPES`
(`skellytracker/core/pipelines/config.py:34`) and in the spec tables.

**`any` goes.** Today `gate` and `first_of` have the type `any` (`config.py:531-532`,
`config.py:541-542`). An `any` input validates nothing. After the change, each input has a list of
the types that it accepts. The output `value` of `gate` has the type of its input `value`. The
output `value` of `first_of` has the type of its inputs. The load still follows only same-frame
edges to find that type (`V-pipeline.graph-9`).

**`@prev` (ruling 5).** An `@prev` input must name a `boxes` port or a `keypoints` port. The load
refuses `@prev` on a `flag` port. The frame port has no `@prev` today (`V-pipeline.graph-2`). No
built-in, no example and no test of today needs a flag or an image through `@prev`. The run stores
each `@prev` value for each camera as a reference (`_runtime/executor.py:153`, `:391`). The value is
empty on frame 0 and in the running mode `image` (`_runtime/executor.py:305-308`), and after a frame
on which the upstream node did not run.

### 3.2 Delivered types

Core gets these values in the result of a camera. No node takes them as an input. The `outputs`
block makes them ([section 6](#6-the-outputs-block)).

`wholebody` and `holistic` are both the type `CanonicalKeypoints`
(`skellytracker/core/pipelines/canonical.py:26`), with two new fields (ruling 15):

| Field | Shape | Today | After |
|---|---|---|---|
| `point_names` | `(C,)` | yes | yes |
| `xy` | `(I, C, 2)` | yes | yes |
| `score` | `(I, C)` | yes | yes |
| `groups` | list | yes | yes |
| `z` | `(I, C)` or `None` | yes | yes |
| `present` | `(I,)` | no | new: the `present` of the input row |
| `instance_score` | `(I,)` | no | new: the `instance_score` of the input row |
| `raw_score` | | no | no |
| `track_ids` | | no | no |

`boxes` is a new small type, `OutputBoxes` (ruling 16):

| Field | Shape | Meaning |
|---|---|---|
| `xyxy` | `(I, 4)` | The corners `(x1, y1, x2, y2)` in source-image pixels, float64, not clipped. A padding row is NaN. |
| `score` | `(I,)` | The `instance_score` of the row. |
| `class_index` | `(I,)` | Copied from the row. |
| `present` | `(I,)` | Copied from the row. |
| `detector_ran` | `(I,)` | Boolean. True when the detector node that the box comes from ran for this camera on this frame ([section 6](#6-the-outputs-block)). |

`OutputBoxes` has no rotation field. `xyxy` is `(cx - w/2, cy - h/2, cx + w/2, cy + h/2)`. The
block computes these four numbers and changes nothing else: the load already refused each file whose
output box can be rotated (ruling 17). Core computes the same four numbers today, then it clips them
(freemocap `freemocap/core/tracking/pipeline_runs.py:165-168`). The pipeline still does not clip,
as [ADR-RA0E](../../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 6 decides.

## 4. Node types

### 4.1 Each node type

"Load" is a check before frame 0. "Run" is a rule on each frame. An input with "(R)" is required.

| Node type | Inputs today | Outputs today | Inputs after | Outputs after | Checked at load | Rule at run | Verdict |
|---|---|---|---|---|---|---|---|
| `onnx_model` | `image` (R) image; `boxes` boxes, required for a top-down model | `boxes`; `keypoints` (the role decides) | `image` (R) image; `boxes` boxes, required for a top-down model; `run_if` flag, optional, for each role | no change. No "ran" output. | Role against ports (`V-node.onnx_model-2`). New: `run_if` is a flag. | Does not run when the `boxes` of a top-down model is empty, or when `run_if` is connected and is false. | Changes |
| `mediapipe_tasks` | `image` (R) image | `keypoints` | `image` (R) image; `run_if` flag, optional, only for the variants `body`, `hand` and `face` | no change | New: no `run_if` with `variant: holistic`. | Does not run when `run_if` is connected and is false. | Changes |
| `boxes_from_points` | `keypoints` (R); `previous_boxes`; `reference_boxes` | `boxes` | no change | no change | No change. | No change. | Stays |
| `hold_boxes` | `previous` (R) boxes; `current` (R) boxes; `previous_keypoints` keypoints | `boxes` | no change | no change | No change. | No change. | Stays |
| `gate` | `value` (R) any; `condition` (R) any | `value` any | `value` (R) boxes or keypoints; `condition` (R) boxes, keypoints or flag | `value`: the type of the input `value` | New: `is_true` and `is_false` need a `flag` condition. `is_present`, `is_empty` and `score_above` need a `boxes` or `keypoints` condition. | A flag condition is one test for the frame ([section 5](#5-the-flag-rules)). A boxes or keypoints condition: no change. | Changes |
| `first_of` | list of any | `value` any | list of one type: boxes or keypoints | `value`: the type of the inputs | The items have one type (`V-node.first_of-1`, `-2`). An `image` item and a `flag` item are refused. | No change. | Stays, with declared types |
| `concat` | list of keypoints | `keypoints` | | | | | Goes: the new `merge` does its work |
| `merge` | `target` (R) keypoints; `source` (R) keypoints | `keypoints` | no change | no change | No change (the five rules move with the node). | No change. | Renamed to `assign_keypoints` |
| `smooth_keypoints` | `keypoints` (R) | `keypoints` | no change | no change | No change. | No change. | Stays |
| `smooth_boxes` | `boxes` (R) | `boxes` | no change | no change | No change. | No change. | Stays |
| `redetect_trigger` | `image` (R) image; `previous_keypoints`; `previous_boxes` | `image` image | `previous_keypoints` keypoints, optional; `previous_boxes` boxes, optional | `redetect` flag | No change (`V-node.redetect_trigger-1`, `-2`). | Runs on each frame, because it has no required input. True when a detection is necessary, else false. In the running mode `image`: always true. | Changes |

Notes on this table:

- `first_of` keeps its list. The order of the list is the priority, so names add nothing. It is
  the only node type with unnamed inputs after `concat` goes.
- This design has no AND and no OR of two flags (rulings 9 and 10). A pipeline with two conditions
  puts two `gate` nodes in a row on the data.
- A detector has only the input `image`, and the frame is never empty. Thus only `run_if` stops a
  detector (ruling 7). A top-down model also stops by the empty-input rule when its `boxes` value
  is empty, as today (`_runtime/executor.py:317`).
- Today the catalog gives `onnx_model.boxes` as optional (`config.py:495`:
  `required_inputs = ("image",)`), and the executor makes it required from the role
  (`_runtime/executor.py:317`). The catalog must state "required for a top-down model", so that the
  editor can show it.
- No port gets a new name except `redetect_trigger.image`, which becomes `redetect` (ruling 6). The
  inputs `previous_*` and the outputs `value` keep their names.
- `redetect_trigger` keeps its state `last`: the frame of the last request. On frame 0 `last` is
  empty, so the node gives true (`_runtime/node_redetect_trigger.py:109`).

### 4.2 New and changed node types

**`flag_when`** (new, ruling 8). It makes a flag from a `boxes` or a `keypoints` value.

| Port | Direction | Accepts | Required |
|---|---|---|---|
| `value` | input | boxes, keypoints | yes; the node reads an empty value |
| `flag` | output | flag | |

| Param | Type | Default | Meaning |
|---|---|---|---|
| `mode` | `is_present`, `is_empty` or `score_above` | required | The test on `value`, as [`gate`](../nodes/gate.md#behaviour) step 2 gives it for a list of present rows. |
| `threshold` | float, `>= 0` | none | Only for `score_above`. A run can change it. |

The output is true when the test passes, else false. The node runs on each frame, because it reads
an empty input. It does one test on each frame, on all present rows, as step 4 of `gate`. It keeps
no state. An `@prev` input makes the pipeline stateful, as each `@prev` input does. The "detect when
lost" case of [`gate`](../nodes/gate.md#authoring-guidance) gets this form:

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

On frame 0 `body.keypoints@prev` is empty, so `lost.flag` is true and `person` runs (ruling 2).

**`merge`** (new meaning, rulings 11 and 12).

| Port | Direction | Accepts | Required |
|---|---|---|---|
| `body` | input | keypoints | yes |
| `left_hand` | input | keypoints, one group | no |
| `right_hand` | input | keypoints, one group | no |
| `face` | input | keypoints, one group | no |
| `keypoints` | output | keypoints | |

| Param | Type | Default | Meaning |
|---|---|---|---|
| `format` | `wholebody` or `holistic` | required | The layout of groups of the output. The node gives exactly this layout. |
| `map` | mapping of point name to point name | `{}` | A point of `body` to a point of a part, for example `map: {body/left_wrist: left_hand/root}`. A present part point replaces the body point. It is the `map` of today's `merge`. |

Behaviour:

1. All inputs describe the same instances, row for row. Row `i` of each part joins row `i` of
   `body`. The node does no position matching.
2. The group of a part takes the name of its input: `left_hand`, `right_hand` or `face`. The node
   id of the model does not set the side of a hand any more.
3. When `body` has a group with the name of a part, the part **replaces** that group, point for
   point by canonical name, as step 5 of today's [`merge`](../nodes/merge.md#behaviour) does. Else
   the part **adds** the group.
4. A connected part with no present row on a frame leaves the points of `body` for that group. When
   `body` has no such group, the points of the group are missing on that frame.
5. The output has exactly the layout of groups of `format`. A group of the layout with no source is
   missing. Point S1 of [section 11](#112-still-open) gives the exact layouts and the form of a
   missing group.
6. `map` replaces single points after step 3.
7. `body` is required: an empty `body` stops the node. The output has the rows, the `present`
   flags, the `instance_score` and the instance source of `body`.

Checked at load: each input is `keypoints`; each part has exactly one group; all inputs have one
instance source and one `geometry`; the landmark schema of a part has the region of its input
(a hand schema for `left_hand`). A part with a null `landmark_schema` cannot be checked. It gives
a load warning and is not refused: "flagged", in the word of the user. A wrong schema is "blocked".

**`assign_keypoints`** (today's `merge`, with a new name, ruling 12). Ports `target` and `source`,
the params `slots`, `source_anchor`, `max_distance` and `map`, and the rules `V-node.merge-1` to
`-5` move with the node and do not change
([ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md)). It is only
for a `source` of another instance source, for example a hand detector on the full frame.

**No hand box node** (ruling 13). Two `boxes_from_points` nodes give the two hand boxes, as the
example `mediapipe-holistic-decomposed` does today.

## 5. The flag rules

A `flag` is one boolean for one camera on one frame. It has no instance rows.

| State | Python value | It means |
|---|---|---|
| true | `True` | The producer decided yes. |
| false | `False` | The producer decided no. |

A flag is never empty, for three reasons:

- Only `redetect_trigger` and `flag_when` give a flag. Each of them runs on each frame and always
  decides, also when an `@prev` input is empty (ruling 2).
- `@prev` is refused on a flag port (ruling 5).
- `gate` and `first_of` do not pass a flag (rulings 9 and 10).

A later node type that gives a flag must keep the first rule.

**The rule of each consumer.**

| Consumer | true | false |
|---|---|---|
| `gate`, mode `is_true` | passes `value` | output empty |
| `gate`, mode `is_false` | output empty | passes `value` |
| `gate`, modes `is_present`, `is_empty`, `score_above` | refused at load on a flag condition | |
| `onnx_model.run_if`, `mediapipe_tasks.run_if` | the node runs, if no other rule stops it | the node does not run; `node_ran` is false; each output is empty |
| `outputs` block | a flag is not an output | |

- **Not connected.** A node with no `run_if` runs as today.
- **`node_ran`.** A node that `run_if` stops has `node_ran` false, as a node with an empty required
  input has today ([ADR-Q5BN](../../../decisions/entries/Q5BN-node-ran-in-the-camera-result.md)
  item 3).
- **Taps (ruling 19).** A tap on a `flag` port writes `flag.jsonl`: one line for each frame and
  camera, with `true` or `false`. A replay of the flag is then possible. Today the tap code has only
  `JSONL_TYPES = ("boxes", "keypoints")` (`_runtime/taps.py:33`).
- **Timing.** A flag has no span and no event. The node that makes it has its span `run`.
- **Stateful pipelines.** The stateful rule follows each input of an `onnx_model` node
  (`_runtime/resolve.py:146-152`), so a trigger on `run_if` still makes the pipeline stateful.
- **Running mode `image`.** Each `@prev` value is empty. `redetect_trigger` gives true. A
  `flag_when` node with `mode: is_empty` on an `@prev` value gives true. Each detector thus runs on
  each image.

**The control signals of today.** The flag inventory found 19 signals. This table groups them. Only
one becomes a flag.

| Signal of today | Where | After |
|---|---|---|
| Redetect trigger: the image, or empty | `_runtime/node_redetect_trigger.py:122`: `return {"image": image if hit else None}, n if hit else last` | The flag `redetect`: true or false. |
| "An empty required input stops the node" | `_runtime/executor.py:313-319` | Stays. `run_if` adds: connected and false stops the node. |
| Rules that read an empty input (`READS_EMPTY`) | one constant in each `_runtime/node_*.py` | Stay. `flag_when` reads its `value`. |
| `gate` modes `is_empty`, `is_present`, `score_above` | `_runtime/node_gate.py` | Stay for a boxes or keypoints condition. Two modes come for a flag condition. |
| `first_of`: the first input that is not empty | `_runtime/node_first_of.py` | Stays. Also the self-`@prev` latch `detected_box` of the built-in. |
| `present` row mask; point validity (NaN, `raw_score > 0`) | `values.py` | Stay. They are data for each row or each point. A flag is not for each row. |
| Interval and `last` of the trigger; the fitness checks | `_runtime/node_redetect_trigger.py` | Stay inside the node. |
| Internal rules of `hold_boxes`, `smooth_boxes`, `smooth_keypoints`, `assign_keypoints` | their node modules | Stay inside the nodes. |
| `node_ran` | `_runtime/executor.py:372` | Stays, in the result of the camera. It is not a port. Core does not read it. |
| Running mode `image`; replay; the stateful classification | `_runtime/executor.py:305-308`, `_runtime/resolve.py` | Stay. They are facts of the run. |
| MediaPipe VIDEO tracking | inside the landmarker | Stays hidden. `run_if` can now skip frames of a `body`, `hand` or `face` landmarker ([section 9.6](#96-risks)). |

## 6. The `outputs` block

The output is not a node type (ruling 14). Each pipeline file must have the block `outputs`. The
conversion to the delivered forms happens at this block.

```yaml
outputs:
  wholebody: wholebody.keypoints
  boxes: crop.boxes
```

**Keys.** The only keys are `wholebody`, `holistic` and `boxes`. The block must have one key or
more. Each value is a port reference `<node>.<port>`, with no `@prev`. A file with another key does
not load. A file can thus give at most one `boxes` output: the output `detector_box` of
`yolox-rtmw-wholebody` goes. Core does not read it. A `record` tap on `person.boxes` gives the same
data.

**What each key checks at load, and what it delivers.**

| Key | Checked at load | Delivered value | Conversion |
|---|---|---|---|
| `wholebody` | The port has the type `keypoints`. The value has a group `body`. | `CanonicalKeypoints` with the canonical names. | `to_canonical` (`canonical.py:146`), as Core calls it today. A group with a null `landmark_schema` passes through with its names and gives a load warning. |
| `holistic` | The port has the type `keypoints`. The groups are exactly `body`, `right_hand`, `left_hand`, `face`, in this order. | `CanonicalKeypoints` with the four MediaPipe Holistic groups and their names. | The same function. For a `mediapipe_tasks` node it changes no name today: its groups have a null `landmark_schema`. |
| `boxes` | The port has the type `boxes`. The box cannot be rotated. | `OutputBoxes` ([section 3.2](#32-delivered-types)). | `(cx, cy, w, h)` to `xyxy`, and `detector_ran`. |

Measured on commit 3c83a5b0 with `check_pipeline`, for the first form of this file: the output
`wholebody` of `yolox-rtmw-wholebody` has 133 point names and 137 canonical names; the output
`holistic` of `mediapipe-holistic-tasks` has 553 point names, and its canonical names are equal to
them.

**The result of a camera.** It has one key for each key of the block, and the fixed fields of today:
`frame_index`, `image_width`, `image_height`, `timestamp_ms` and `node_ran`. The result assembly is
at `_runtime/executor.py:377`.

**The delivered keypoints (ruling 15).** `CanonicalKeypoints` gets `present` and `instance_score`.
It has no `raw_score`: `to_canonical` reads the `raw_score` of its input for the missing rule
(`canonical.py:172`), and gives none. It has no `track_ids`: each value is -1 in this version.
Today the result of `mediapipe-holistic-tasks` is an `InstanceKeypoints` with `raw_score`. After the
change it has none. Core does not store it. The internal ports and the taps keep `raw_score`.
`to_canonical` stays a public function. The block calls it. Core stops calling it.

**A rotated box (ruling 17).** The load refuses a file whose `outputs.boxes` can hold a rotated
box. The output never changes a box. The load finds it in this way:

1. Only `boxes_from_points` with a `target_rotation_deg` that is not empty gives a rotation that is
   not 0 ([`boxes_from_points`](../nodes/boxes_from_points.md#behaviour) step 6). `target_rotation_deg: 0`
   also gives a rotation, from the two alignment points. An object detector gives the rotation 0
   ([ADR-2RWC](../../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md) item 2).
2. A node that passes a box keeps its rotation: `gate`, `first_of`, `hold_boxes` and `smooth_boxes`.
3. The load starts at the port of `outputs.boxes`. It follows each `boxes` input of each node that
   passes a box, also an `@prev` input, until it finds a detector or a `boxes_from_points` node. It
   refuses the file when it finds a `boxes_from_points` node with `target_rotation_deg`. The error
   names that node.
4. The load does not follow the `keypoints` input, the `previous_boxes` input or the
   `reference_boxes` input of a `boxes_from_points` node. The rotation of its output comes only from
   its own params (step 6 of the node; step 10 states that the floors do not use the rotation of
   these two inputs).

Neither built-in sets `target_rotation_deg`. The example `mediapipe-holistic-decomposed` has rotated
boxes, but they are not an output.

**`detector_ran` (ruling 16).** Each `boxes` port has an instance source: the inference node whose
rows the boxes follow ([Graph](../graph.md#behaviour) item 8). The output schema gives it at load.
For each row of the delivered `boxes`, `detector_ran` is the `node_ran` value of that node for this
camera on this frame. All rows of one value have one instance source, so all rows have the same
`detector_ran`, also a padding row. Measured for the first form of this file: the `instance_source`
of `crop.boxes` of the built-in is `person`. Thus:

- On a frame on which `person` ran, `detector_ran` is true, also when `person` found no person.
- On a frame on which the box comes from the points of the previous frame, `detector_ran` is false.
- A node whose outputs are all replayed did not run
  ([Outputs](../outputs.md#behaviour) item 8), so `detector_ran` is false in such a replay.

Core reads `result["boxes"].detector_ran[0]`. It reads no `node_ran` and has no literal node id.
`node_ran` stays in the result
([ADR-Q5BN](../../../decisions/entries/Q5BN-node-ran-in-the-camera-result.md)). Point S2 of
[section 11](#112-still-open) covers an instance source that is not a detector.

**The output schema.** It has one item for each key of the block. For `wholebody` and `holistic`,
`point_names`, `groups` and `edges` describe the delivered value. They are the `canonical_names`,
the passthrough groups and the `canonical_edges` of today. The two fields `canonical_names` and
`canonical_edges` go, because they would repeat `point_names` and `edges`. `geometry`, `depth_unit`,
`max_instances`, `tracked` and `instance_source` stay. For `boxes`, `class_names`, `max_instances`,
`tracked` and `instance_source` stay. The schema of `boxes` states that the value has `xyxy` and
`detector_ran`.

**No `image` output.** The block has no key for an image. The check at `_runtime/executor.py:110`
goes with the free names.

**Later work (ruling 18).** Look into one canonical output keypoint set that becomes the only output
format of a pipeline. The keys `wholebody` and `holistic` would then become one key.

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
    params: {mode: is_false}
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
outputs:
  wholebody: wholebody.keypoints
  boxes: crop.boxes
```

Three lines change in `nodes`: `trigger` loses `image: frame.image`; `person` gets
`image: frame.image` and `run_if: trigger.redetect` in place of `image: trigger.image`;
`carried_box` gets the condition `trigger.redetect` with `mode: is_false` in place of
`trigger.image` with `mode: is_empty`. No image is gated.

**Frame by frame.** "Today" is the file of commit 3c83a5b0.

| Frame | `trigger` | `person` | `carried_box` | `box` | Delivered `boxes.detector_ran` |
|---|---|---|---|---|---|
| Frame 0 | `last` is empty, so it asks for a detection. Today: it gives the image. After: true. | Runs. | `points_box` is empty, because `wholebody.keypoints@prev` is empty. The gate also does not pass. Empty. | `person.boxes` | true |
| A normal frame | No detection is necessary. Today: empty image. After: false. | Does not run. Today: its required `image` is empty. After: `run_if` is false. `person.boxes` is empty. | Passes `points_box.boxes`. Today: `is_empty` on the empty image. After: `is_false` on the false flag. | `carried_box.value` | false |
| A lost frame `L` | As a normal frame. | Does not run. | Passes the box from the points of frame `L - 1`. | `carried_box.value`. `wholebody` runs on it and gives no point with a score of 0.4 or more. | false |
| Frame `L + 1` | The check `bbox_area_collapse` fails on the keypoints of frame `L`. It asks for a detection, and `last` becomes `L + 1`. Today: the image. After: true. | Runs. | Does not pass. Empty. | `person.boxes`. When `person` finds no person, it is empty, `wholebody` does not run, and the trigger asks again on frame `L + 2` (`box_missing`). | true |

In each row, the decision of the trigger and its state `last` come from the same code and the same
inputs as today. `person` runs on the same frames. `carried_box` passes on the same frames. Thus
`box`, `crop` and `wholebody` get the same values, and `node_ran` is the same. The pipeline stays
stateful.

**The tracking behaviour is meant to be equal to today.** This claim rests on reasoning from the
code. No code was changed and no test ran on the new form. The box parity test of
[ADR-7E4Z](../../../decisions/entries/7E4Z-box-parity-of-the-built-in-with-sfn26.md) must prove it
in the stage that changes the built-in file.

What changes, and why:

- The result has `boxes` in place of `crop_box`, as `xyxy` with no rotation and with
  `detector_ran` (rulings 14, 16, 17).
- The result has no `detector_box` (ruling 14: three keys).
- `wholebody` is delivered in the canonical form, with 137 names. Today the result has 133 names,
  and Core converts it. The numbers that Core stores are the same.
- The graph has two image wires in place of three. Both start at `frame.image`.
- `pipeline_sha256` and each `upstream_sha256` change.

### 7.2 Built-in `mediapipe-holistic-tasks`

```yaml
nodes:
  - id: holistic
    type: mediapipe_tasks
    inputs: {image: frame.image}
    params: {variant: holistic}
outputs:
  holistic: holistic.keypoints
```

The file does not change. Behaviour: no change of a point name, a position or a score. The
delivered value is a `CanonicalKeypoints` with `present` and `instance_score`, and with no
`raw_score` and no `track_ids`.

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
    params: {format: wholebody}
outputs:
  wholebody: joined.keypoints
```

Behaviour: no part replaces a group, because the body model has no hand group and no face group.
Each part adds its group. The order of the groups is the order of `format: wholebody`, not the list
order of the `concat` of today. The result is in the canonical form.

### 7.4 Example `rtmpose-hand-detector`

The four model nodes do not change. The `merge` node gets the type `assign_keypoints`, with the same
inputs and params. The output becomes:

```yaml
  - id: body_hands
    type: assign_keypoints
    inputs: {target: body.keypoints, source: hand.keypoints}
    params: # ... no change
outputs:
  wholebody: body_hands.keypoints
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
    params: {format: wholebody}
outputs:
  wholebody: joined.keypoints
```

Behaviour changes, and why. Today the file has three outputs: `body`, `right_hand` and `left_hand`.
The block holds one keypoint set of a kind, so a `merge` node joins them. This is the merge of the
hand example of the user, who named its output "wholebody keypoints". The two `gate` nodes of the
file take a `boxes` value and a `keypoints` condition, and they do not change. The two hand boxes
come from two `boxes_from_points` nodes, as today (ruling 13). The hand boxes are rotated, but they
are not an output, so the load does not refuse the file. The file stays "structure only".

### 7.6 The examples between the stages

The `outputs` block lands before the new `merge` (ruling 20). Between these two stages, the three
examples have this form (point S3 of [section 11](#112-still-open)):

- `rtmpose-body-hands-face` keeps its `concat` node. Its keypoint output gets the key `wholebody`.
- `rtmpose-hand-detector` keeps the type `merge`. Its output gets the key `wholebody`.
- `mediapipe-holistic-decomposed` gets a `concat` node on `body_smooth.keypoints`,
  `right_hand.keypoints` and `left_hand.keypoints`, with the key `wholebody`.

## 8. The image rule

"They must never copy images in memory as it is expensive." "a detector must not have a gated
image, the only thing that gates it is the flag"

**The rule.** The only image is the camera frame. The only port of the type `image` is
`frame.image`.

**The load rules that give it:**

1. The catalog has no node type with an `image` output. `redetect_trigger` loses its output `image`
   (ruling 6). `gate` and `first_of` do not accept an image, so their output `value` is never an
   image (rulings 4, 9, 10). A test on the catalog proves that no output has the type `image`.
2. `V-pipeline.graph-3` with the accepted types: an `image` input accepts only an `image` port.
   With rule 1, an `image` input of a file can name only `frame.image`.
3. `V-pipeline.graph-2` refuses `frame.image@prev`, as today. The new rule `V-pipeline.graph-12`
   allows `@prev` only on `boxes` and `keypoints` ports.
4. `V-pipeline.taps-1` refuses a tap on `frame.image`, as today. No other image port exists, so no
   tap reads an image. The tap form `<image_id>.npy` leaves the spec.
5. The `outputs` block has no key for an image.

No new load rule for the image is necessary: rules 1 and 2 give it.

**What this closes.** Today `_runtime/executor.py:391` stores each `@prev` port by reference. A
file with `trigger.image@prev`, or with the `value@prev` of a gated image, loads today. The run then
holds the frame buffer of the host for one more frame. When the host uses the buffer again, the
"previous image" is silently the new image. After the change, no such file loads.

**Where an image is gated today, all to stop a model:** the nodes `person` and `carried_box` of the
built-in, the node `pose_detector` of the example `mediapipe-holistic-decomposed`, test fixtures,
the spec text of `gate` and `redetect_trigger`, and 8 of the 11 cases of `node.gate.yaml`. Each
moves to `run_if` or to a flag condition.

**Where the runtime passes the frame, with no copy:**

- `_runtime/executor.py:337`: `values[camera_id] = {(FRAME, "image"): frame.image}`. A reference.
- `_runtime/executor.py:419`: `runner.run(index, [ready[camera_id]["image"] for camera_id in cameras], boxes, timer)`.
  A list of references.

**The test.** A test follows the frame object to each consumer with `is`: each model node gets the
same object that the host gave.

**The conversions that stay.** "Never copy" covers the pipeline plumbing. It does not cover the
conversion that a model needs:

| Place | Line | When |
|---|---|---|
| `_runtime/mediapipe_tasks.py:151` | `mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(image[:, :, ::-1]))` | On each frame, for each camera, in each `mediapipe_tasks` node with the variant `body`, `hand` or `face`. BGR to RGB. |
| `skellytracker/core/detectors/mediapipe_holistic.py:109` | `mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB))` | On each frame, for each camera, in the variant `holistic`. |

The one BGR to RGB conversion of each `mediapipe_tasks` node is allowed (ruling 4). A shared
conversion, one for each camera and frame, is later work for the decomposed MediaPipe pipeline. The
sidecar preprocessing is outside the pipeline plumbing and does not change:
`skellytracker/core/detectors/processing/pre/resize_interpolation.py:45` makes a full-frame float32
copy only with `compute_dtype: float32`, and `resize_affine_crop.py:154` copies only a frame that is
not contiguous.

## 9. Consequences

### 9.1 Decision entries

[ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) and
[ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) are
superseded by [ADR-W5QD](../../../decisions/entries/W5QD-pipeline-entries-consolidation.md), which
restates them. [ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md)
amends these rules:

| Entry | Item | Change |
|---|---|---|
| [ADR-W5QD](../../../decisions/entries/W5QD-pipeline-entries-consolidation.md) | Item 1, the rules of [ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6 | The closed set of glue nodes changes. The trigger gives a flag, not an image. `concat` goes. `flag_when` and `assign_keypoints` come. |
| [ADR-W5QD](../../../decisions/entries/W5QD-pipeline-entries-consolidation.md) | Item 2, the rules of [ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) items 1 and 7 | The `outputs` block stays, with only the keys `wholebody`, `holistic` and `boxes`. The result holds the delivered forms, not port values. The port type list of the load checks changes. |
| [ADR-W5QD](../../../decisions/entries/W5QD-pipeline-entries-consolidation.md) | Item 3, text on the built-ins and the annotator | The annotator draws the delivered values. |
| [ADR-4WR9](../../../decisions/entries/4WR9-params-schema-in-the-node-catalog.md) | Item 3 | `any_from` names the inputs that give an output its type. The type `any` goes. The catalog gives the accepted types of each input. |
| [ADR-2RWC](../../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md) | Item 6 | The outputs `detector_box` and `crop_box` become the one deliverable `boxes`. Items 1 to 5 stay for the internal type. |
| [ADR-97X9](../../../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) | Items 1, 5 and 6 | The row rule of `concat` moves to `merge`. The `any` rule becomes "the output has the type of an input that is not `@prev`". `@prev` is only on `boxes` and `keypoints` ports. |
| [ADR-4MP6](../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md) | Items 2, 3, 5 and 7 | The groups of `merge` and `concat`. The output schema loses `canonical_names`. The side of a hand also comes from the input name of `merge`. Core does not call `to_canonical`. The key of the `outputs` block selects the delivered form, and `merge.format` selects the layout of groups. |
| [ADR-PX6Z](../../../decisions/entries/PX6Z-keypoint-raw-score-in-the-pipeline-result.md) | Item 2 | The result of a camera has no `raw_score`. The ports and the taps keep it. Items 3 and 4 stay. |
| [ADR-RA0E](../../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) | Items 4 and 6 | The trigger gives a flag. The drawn box is the deliverable `boxes`. It stays not clipped. |
| [ADR-KW76](../../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) | Each item | The node gets the name `assign_keypoints`. No rule changes. |
| [ADR-Q5BN](../../../decisions/entries/Q5BN-node-ran-in-the-camera-result.md) | Item 5 | The rule of the reserved output names goes: the block has a closed set of keys. Items 1 to 4 stay. Core reads `detector_ran`, not `node_ran`. |
| [ADR-Q59W](../../../decisions/entries/Q59W-pipeline-timing-and-taps.md) | The tap forms | The array-file form `<image_id>.npy` goes. The form `flag.jsonl` comes. |
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
| `graph.md` | The node type list; the port type table; Behaviour items 4, 5, 6 and 7; the "source-image pixels" rule; the image rule; the `@prev` rule. |
| `outputs.md` | The field `outputs` gets the three keys. New: the delivered values, the result keys, `detector_ran`, the rotation rule, the output schema. Behaviour items 6, 7 and 9. |
| `running.md` | Item 5 names no new temporal node. The text on `set_params` does not change. |
| `taps.md`, `timing.md`, `file.md` | The lines for `image` and `tensor` and the form `<image_id>.npy` go. The form `flag.jsonl` comes. `flag_when` gets the span `run`. `file.md` keeps the key `outputs`. |
| `nodes/` | New: `flag_when.md`, `assign_keypoints.md` (from `merge.md`). Rewritten: `merge.md`. Deleted: `concat.md`. Changed: `onnx_model.md`, `mediapipe_tasks.md`, `gate.md`, `first_of.md`, `redetect_trigger.md`. |
| `README.md`, `changelog.md`, `inventory.yaml`, `templates/` | The section map, the terms "glue node" and "frame", the validation index, one changelog row, the two templates. |
| `reference/` | `pipeline_config.py`; `node_gate.py`, `node_redetect_trigger.py`; new `node_flag_when.py`, `node_assign_keypoints.py` (from `node_merge.py`), new `node_merge.py`; `node_concat.py` goes. |
| `vectors/` | `node.gate.yaml` (the 8 cases with an image become cases with a flag condition or go), `node.redetect_trigger.yaml` (the output), `node.first_of.yaml`; new `node.flag_when.yaml`, `node.merge.yaml`; `node.merge.yaml` of today becomes `node.assign_keypoints.yaml`; `node.concat.yaml` goes. |
| `pipeline.schema.json` | Both copies, from `tools/make_pipeline_schema.py`. `outputs` gets the three property names, with `additionalProperties: false` and `minProperties: 1`. |
| The 5 examples and the 2 built-ins | The form of [section 7](#7-the-pipelines-in-the-new-form). |

Validation rules. A removed ID is not used again, as the spec does for `V-node.smooth_keypoints-2`.

| Rule | Change |
|---|---|
| `V-pipeline.graph-3` | New wording: the type of the connected output must be in the accepted types of the input. |
| `V-pipeline.graph-5`, `-6` | `first_of` is the only variadic type. |
| `V-pipeline.graph-9` | New wording, with no `any`. |
| New `V-pipeline.graph-12` | An `@prev` input must name a port of the type `boxes` or `keypoints`. |
| `V-pipeline.outputs-1` | New wording: the block must have one key or more. Each key must be `wholebody`, `holistic` or `boxes`. Each port reference must name an existing output port, with no `@prev`. |
| `V-pipeline.outputs-3` | Removed: the closed set of keys covers it. |
| New `V-pipeline.outputs-4` | `wholebody` and `holistic` must name a `keypoints` port, and `boxes` a `boxes` port. The `holistic` value must have the groups `body`, `right_hand`, `left_hand`, `face`. The `wholebody` value must have a group `body`. The host checks the groups at load. |
| New `V-pipeline.outputs-5` | The port of `boxes` must not be able to hold a rotated box ([section 6](#6-the-outputs-block)). |
| `V-pipeline.taps-1` and the tap forms | A tap port has the type `boxes`, `keypoints` or `flag`. |
| New `V-node.onnx_model-6`, `V-node.mediapipe_tasks-3` | `run_if` is a `flag`. `mediapipe_tasks` with `variant: holistic` has no `run_if`. |
| `V-node.gate-2`; new `V-node.gate-4` | `is_true` and `is_false` need a `flag` condition. `is_present`, `is_empty` and `score_above` need a `boxes` or `keypoints` condition. |
| `V-node.concat-1` to `-3` | Removed with the node. |
| `V-node.merge-1` to `-5` | Become `V-node.assign_keypoints-1` to `-5`. The new `merge` starts at `V-node.merge-6`, so that no ID gets a new meaning. |
| New `V-node.flag_when-1` | `score_above` needs `threshold`, and the other modes have none. |

The new rule numbers are the next free numbers as the first form of this file found them. The stage
that writes a rule must check its number.

### 9.3 Hashes and taps

- `pipeline_sha256` hashes `schema_version`, `nodes` and `outputs`
  (`skellytracker/core/pipelines/timing.py:62`). The key list does not change. The hash of
  `yolox-rtmw-wholebody` changes. The hash of `mediapipe-holistic-tasks` does not change, because
  its file does not change.
- `upstream_sha256` hashes the config of a node and of each node upstream of it. It changes for
  `trigger`, for `person` and for each node downstream of them. A replay compares it, so each
  recorded tap of `yolox-rtmw-wholebody` stops to replay. Version 2.0.0 is not released, so no
  released tap breaks.
- A tap names an internal port. The delivered values have no tap. The COCO evaluation of
  skellybench reads the 133 native points from a tap, so it does not change.
- A tap is on a `boxes`, `keypoints` or `flag` port (ruling 19). The file `flag.jsonl` has one line
  for each frame and camera. A replay of a `flag` port must cover each frame and each camera
  (`V-pipeline.taps-4`), so a replayed flag is also never empty.
- No hash holds the canonical mapping of the landmark schema registry. The delivered `wholebody`
  value depends on that mapping. This is true today for the `to_canonical` call of Core.

### 9.4 Package code and tests

`config.py` and its copy `specs/pipeline/reference/pipeline_config.py`; `values.py`; `canonical.py`;
`nodes.py` (the accepted types of a port); `annotate.py`; `cli.py`; in `_runtime/`: `executor.py`
(`_stops` with `run_if`, the result assembly at line 377 with the conversion and `detector_ran`,
the output check at lines 109-114), `resolve.py` (the rotation check, the group checks), `taps.py`
(the flag form), `node_gate.py`, `node_redetect_trigger.py`, `node_merge.py`, `node_concat.py`,
`mediapipe_tasks.py`. Tests: each file of `skellytracker/tests/pipelines/`, the box parity test,
and in `tools/tests/`: `test_pipeline_schema.py`, `test_pipeline_node_catalog.py`,
`test_pipeline_package_schema.py`, `test_vectors.py`, `test_examples.py`. New tests: no `image`
output in the catalog; the frame object reaches each model node with `is`; the box of each node
type is in source-image pixels.

### 9.5 freemocap

**Core.** The one boundary is `observations_from_results` in
`freemocap/core/tracking/pipeline_runs.py`. Its readers get the observation type of freemocap and
do not change. Core reads only the outputs (ruling 16).

| Line | Today | After |
|---|---|---|
| `:27`, `:30` | `RTMW_NODE = "wholebody"`, `HOLISTIC_NODE = "holistic"`, used as output names | The same strings are the keys of the result. No change. |
| `:28`, `:170` | `PERSON_NODE = "person"`; `result["node_ran"][PERSON_NODE]` | `result["boxes"].detector_ran[0]`. The constant `PERSON_NODE` goes. |
| `:29` | `CROP_BOX = "crop_box"` | `"boxes"`. |
| `:117`, `:130` | `canonical_names`, `canonical_edges` of the schema | `point_names`, `edges`. |
| `:153`, `:159-160` | `to_canonical(result[RTMW_NODE], output_schema[RTMW_NODE])` | The result value, with no call. `present` comes from the same value. |
| `:165-168` | `cx, cy, w, h, _ = crop.boxes[0]`, then clip and `int()` | `x1, y1, x2, y2 = boxes.xyxy[0]`, then the same clip and `int()`. |
| `:48` | The size of the node `wholebody` | No change. |

`freemocap/tests/test_pipeline_runs.py` builds `InstanceKeypoints` and `InstanceBoxes` values for
the result. It must build the delivered values.

**The pipeline metrics.** Core makes each stage name from the timing event:
`stage = f"{record['node_id']}.{record['span']}"`
(freemocap `freemocap/core/pipeline/pipeline_timing_events.py:60`). This redesign renames no node of
a built-in and no span, and it adds no node to a built-in. No stage name changes. The conversion of
the `outputs` block has no span (point S5 of [section 11](#112-still-open)). The `outputs` change
and the reader of Core wait until the pipeline-metrics stage is in the hands of the user
(ruling 21).

**The editor.** The user handles the editor with another session, after the 2.0.0 pre-release
(ruling 20). This file decides nothing for it. These facts of the catalog and the file change for
it: the type `flag` comes, and `tensor` and `any` go; each input has a list of accepted types;
`any_from` stays as "the inputs that give an output its type"; the `outputs` block stays a block,
with three fixed keys; `merge` gets named inputs; `concat` goes; `flag_when` and `assign_keypoints`
come; `onnx_model.boxes` is "required for a top-down model".

### 9.6 Risks

- `run_if` on a `mediapipe_tasks` node skips frames of a VIDEO-mode landmarker. The measurement of
  [ADR-6JWJ](../decisions/entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md) found that a
  landmarker finds a person again after a gap. It did not measure a landmarker that gets no frame
  for a time.
- The equal tracking behaviour of the built-in is not measured
  ([section 7.1](#71-built-in-yolox-rtmw-wholebody)).
- The new `merge` has no measured pipeline. Its two examples are structure only.
- The `wholebody` deliverable is canonical only for a registered schema. Today the registry has one
  schema, `COCO_WholeBody`. The MediaPipe landmark schemas stay open work, so `holistic` passes its
  names through until then.
- The rename of `merge` to `assign_keypoints` and the end of `concat` come after the pre-release
  (ruling 20). A file of the pre-release with `concat` or with today's `merge` must change then.

## 10. Build order

Each stage is one commit group that passes `tools/run_checks.py` on its own. The sizes are rough:
S is less than 150 changed lines, M is 150 to 500, L is more than 500. The lines of spec text,
vectors and tests count. "Now" is ruling 21: the stage is built in the worktree of this redesign, in
parallel with other work.

| Stage | Content | Size | When |
|---|---|---|---|
| 1 | The type `flag`; `tensor` and `any` go; the accepted types of each input in the reference model, `config.py`, the catalog, the schema and `graph.md`; the `@prev` rule `V-pipeline.graph-12`. `gate` and `first_of` still accept an image until stage 3. No file changes its behaviour. | M | Now. Before the pre-release. |
| 2 | `redetect_trigger.redetect`; `run_if` on `onnx_model` and `mediapipe_tasks`; the `gate` modes `is_true` and `is_false`; the built-in and the example with a trigger; the vectors of `gate` and `redetect_trigger`. The box parity test must pass. | L | Now. Before the pre-release. |
| 3 | The image rule: `gate` and `first_of` refuse an image; the catalog test for "no `image` output"; the test with `is`; the tap form `<image_id>.npy` goes; the spec text; the "source-image pixels" rule with its test. | M | Now. Before the pre-release. |
| 4 | The `outputs` block: the three keys; the delivered values; `detector_ran`; the rotation rule; the output schema; each example, each built-in, the templates, `annotate.py` and `cli.py`. | L | After the metrics stage. Before the pre-release. |
| 5 | freemocap Core: `pipeline_runs.py` and its tests. It lands with stage 4. | S to M | After the metrics stage. Before the pre-release. |
| 6 | `merge` with four inputs and `format`; `assign_keypoints`; `concat` goes; the three examples. | L | After the pre-release. |
| 7 | `flag_when`: the section, the reference module, the vectors, the runtime. The tap form `flag.jsonl` (point S4). | M | After the pre-release. |
| 8 | The editor. | M | After the pre-release. The user handles it with another session. |
| 9 | Later work: one RGB conversion for each camera and frame for the decomposed MediaPipe pipeline; the look into one canonical output keypoint set (ruling 18). | not sized | Later. |

Stages 1 to 3 need no change in freemocap: the result of a camera keeps its form until stage 4.
Stage 2 changes the file of a built-in, so `pipeline_sha256` of `yolox-rtmw-wholebody` changes
there.

## 11. Decided and still open

### 11.1 Decided

The first form of this file had 19 questions. Each has a ruling now.

| Former question | Ruling |
|---|---|
| Q1, output as a node type | No. The output is the `outputs` block, and each file must have it (ruling 14). |
| Q2, meaning of `wholebody` and `holistic` | `wholebody` delivers canonical names. `holistic` delivers the four MediaPipe Holistic groups with their names (ruling 14). |
| Q3, rotated output box | The load refuses the file. The output never changes a box (ruling 17). |
| Q4, "replace" in `merge` | A part replaces the group of its name in `body`, or adds it. `map` replaces single points (ruling 11). |
| Q5, `concat` | It goes (ruling 12). |
| Q6, position matching | It stays as the node `assign_keypoints` (ruling 12). |
| Q7, empty flag | No such state. A flag is true or false (ruling 2). |
| Q8, converter node | `flag_when`, with `value`, `flag` and the three tests of `gate` (ruling 8). |
| Q9, `run_if` | On each `onnx_model` of each role, and on the `mediapipe_tasks` variants `body`, `hand` and `face`. Not on `holistic` (ruling 7). |
| Q10, `any` | It goes. Each input lists its accepted types (ruling 1). |
| Q11, hand box node | No such node. It is dropped, not deferred (ruling 13). |
| Q12, fields of the delivered keypoints | `present` and `instance_score`. No `raw_score` and no `track_ids` (ruling 15). |
| Q13, `detector_ran` | The delivered `boxes` carry it for each row. Core reads no `node_ran` (ruling 16). |
| Q14, `tensor` | It goes (ruling 1). |
| Q15, flag taps | Allowed: one line for each frame and camera with `true` or `false` (ruling 19). |
| Q16, "never copy" | It covers the plumbing. One conversion for each `mediapipe_tasks` node is allowed. A shared conversion is later work (ruling 4). |
| Q17, a replaced group with no present part row | The group keeps the points of `body` (ruling 11). |
| Q18, stages before the pre-release | Stages 1 to 5 before, stages 6 to 8 after (ruling 20). Stages 1 to 3 now, stages 4 and 5 after the metrics stage (ruling 21). |
| Q19, the editor | Not in the scope of this file. The user handles the editor with another session. |

The "points with no question" of the first form: no port gets a new name except `redetect`
(ruling 6, confirmed); `last` stays and `onnx_model` gets no "ran" output (rulings 6 and 7,
confirmed); "`merge` has no output-format param" is reversed (ruling 11); an image through a `gate`
is reversed (ruling 4).

### 11.2 Still open

No two rulings conflict, as far as this file found. Each point here is a detail that no ruling
settles. Each has a default, and the build can start with it.

**S1 — The layouts of `merge.format`, and the form of a missing group.** Ruling 11: "the node gives
exactly that layout of groups, and a group with no source is missing."

- Default layouts: `holistic` is `body`, `right_hand`, `left_hand`, `face`, the order of
  `mediapipe_tasks` with the variant `holistic`. `wholebody` is `body`, `feet`, `face`, `left_hand`,
  `right_hand`, the order of `COCO_WholeBody`. `feet` has no input of its own: it comes only from
  `body`.
- Default for a missing group: the group has its columns, and each point is missing (NaN, score 0).
  The node then needs the point list of each group: from `COCO_WholeBody` for `wholebody`, and from
  the MediaPipe YAML files for `holistic`. The output has the same shape for each set of connected
  parts, and `outputs.holistic` accepts a `merge` with no `face` input.
- Other option: a missing group has no columns. The node needs no point list. `outputs.holistic`
  then refuses a `merge` with a part that is not connected.
- With the default, `outputs.wholebody` and `outputs.holistic` check only their own group rule. A
  `format` that does not agree with the key fails that rule, or passes it. No extra rule.
- Blocks: only stage 6, after the pre-release.

**S2 — `detector_ran` when the instance source of the output box is not a detector.** For example
boxes from `boxes_from_points` on the keypoints of a `mediapipe_tasks` node. Default: `detector_ran`
is the `node_ran` of the instance source node, for each node type. Each instance source is an
inference node, so the value always exists. Other option: the load refuses `outputs.boxes` when the
instance source is not an `onnx_model` detector. Blocks: nothing. For the built-in, the instance
source is the detector `person`.

**S3 — The examples between stage 4 and stage 6.** The block allows one keypoint set of a kind, and
the new `merge` lands later. Default: [section 7.6](#76-the-examples-between-the-stages): the
examples use `concat` and today's `merge` until stage 6. Other option: the example
`mediapipe-holistic-decomposed` delivers only its body until stage 6. Blocks: nothing.

**S4 — The stage of the flag tap.** Ruling 20 does not name the taps. Default: the form
`flag.jsonl` lands in stage 7, after the pre-release. Until then the load refuses a tap on a `flag`
port, as the code of today does for each type that is not `boxes` or `keypoints`. The later change
only allows more. Other option: stage 2, with the first flag port. Blocks: nothing.

**S5 — A timing span for the conversion of the `outputs` block.** Today Core calls `to_canonical`
outside the run, so no span has this time. After stage 4 the run does the conversion. Default: no
new span. The time is in the time of the call, and not in a node span. Other option: one span for
the block. Blocks: nothing in skellytracker. Decide it with stage 4, because that stage follows the
pipeline-metrics stage of freemocap.

## 12. Checked and not checked

**Checked for this form.** These lines were opened again in the worktree, whose package code is
equal to commit 3c83a5b0: each cited line of `_runtime/executor.py`,
`_runtime/node_redetect_trigger.py`, `_runtime/taps.py`, `_runtime/mediapipe_tasks.py`,
`mediapipe_holistic.py`, `config.py`, `values.py`, `canonical.py` and `timing.py`. The file of the
built-in `yolox-rtmw-wholebody` and the examples `mediapipe-holistic-decomposed` and
`rtmpose-hand-detector` were read. `outputs.md` was read in full. The rotation rule was read in
`boxes_from_points.md` (steps 6 and 10) and in
[ADR-2RWC](../../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md) item 2. The
decision-log check, the link check, the private-data check and the document tests ran on the changed
files.

**Carried over from the first form, not checked again.** Each line of freemocap and of the editor;
the counts 133, 137 and 553; the `instance_source` `person` of `crop.boxes`; the lines of
`resolve.py` and of the sidecar preprocessing; the next free rule numbers.

**Not checked.**

- The frame-by-frame table of section 7.1 is reasoned from the code. No code was changed, so no test
  ran on the new form. The box parity test must prove the equal behaviour.
- The count "8 of the 11 cases of `node.gate.yaml`" and the list of the places that gate an image
  come from a read-only investigation of the supervisor session. The vector files were not read.
- The rotation walk of section 6 rests on the spec text. The modules of `hold_boxes`,
  `smooth_boxes`, `gate` and `first_of` were not read to prove that no other node sets a rotation.
- That each instance source is an inference node (point S2) comes from a search for
  `instance_source` in the package, not from a proof.
- The control signals of `hold_boxes`, `smooth_boxes`, `smooth_keypoints` and today's `merge` in
  the table of section 5 come from the flag inventory. Their node modules were not read in full.
- `annotate.py`, `cli.py`, `catalog.py`, `loading.py` and `run.py` were not read. Section 9.4 names
  them from their role.
- The entries [ADR-QD6G](../../../decisions/entries/QD6G-canonical-edges-in-the-output-schema.md),
  [ADR-JHB3](../../../decisions/entries/JHB3-keypoints-xy-and-z-and-image-width-and-height.md),
  [ADR-Y753](../../../decisions/entries/Y753-pipeline-templates-glue-vectors-and-taps-flag.md) and
  [ADR-Q59W](../../../decisions/entries/Q59W-pipeline-timing-and-taps.md) were not read in full.
  For the other amended entries, only the first line of each item was read.
- The point lists of the MediaPipe YAML files and of `COCO_WholeBody` (point S1) were not read.
- No measurement exists of a `mediapipe_tasks` landmarker that `run_if` stops for some frames.
- The sizes of section 10 are estimates.

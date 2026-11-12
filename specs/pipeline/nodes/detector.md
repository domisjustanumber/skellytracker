---
id: node.detector
title: Detector node
kind: node
vectors: null
status: {spec: draft}
---

# Detector node

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A `detector` node runs one ONNX model. It does the preprocessing, the inference and the postprocessing that the sidecar of the model declares, for example the crop, the decode and NMS. A pipeline has no step nodes for these steps ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 5). The [sidecar spec](../../model-sidecar/README.md) defines all model processing. This section defines only how the node refers to a model and how the node connects to the graph.

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Live | Description | Source |
|---|---|---|---|---|---|---|
| `key` | `str` |  | required | no | The catalog key of the model, `<model_id>@<source.name>`, with an optional pin `==<version>`. | ADR-7NY2 item 10; ADR-88WQ item 7 |
| `sidecar_sha256` | `str \| None` |  | `null` | no | The SHA-256 of the sidecar file bytes. Required in a shipped or an exported file. | ADR-7NY2 item 10 |
| `size` | `str` |  | required | no | A size key of the `sizes` of the sidecar. | ADR-7NY2 item 10 |
| `precision` | `Optional[Literal['fp32', 'fp16']]` |  | `null` | no | The precision of the artifact. Empty: fp16 on a GPU EP and fp32 on CPU; fp32 when the size has no fp16 artifact. | ADR-7NY2 item 10 |
| `execution_provider` | `str \| None` |  | `null` | no | A key of the EP catalog for this node, for example `cuda`, `trt-rtx` or `cpu`. Empty: the EP of the run. | ADR-7NY2 item 12; ADR-9NW0 item 1 |
| `ep_options` | `dict[str, str]` |  | `{}` | no | EP options for this node: option names and values that the EP catalog allows for its EP. Empty: the EP options of the run when the node uses the EP of the run, else none. | ADR-9NW0 item 2 |
| `max_instances` | `int` | >= 1 | `1` | no | The number of instance rows `I` that this node makes (object detector or one-stage model). | ADR-ZYS9 item 1 |
| `object_decode` | `dict[str, Any]` |  | `{}` | no | Changes of the fields of the `object.decode` block of the sidecar. The load checks each name against the sidecar. | ADR-7NY2 item 11; ADR-88WQ item 7 |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `image` | input | `image` |
| `rois` | input | `roi` |
| `detections` | output | `detections` |
| `rois` | output | `roi` |
| `keypoints` | output | `keypoints` |
<!-- /node-table:ports -->

- `key`, `sidecar_sha256`, `size` and `precision` are the model reference. A config refers to a sidecar and does not copy its content ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) items 3 and 10).
- `key` is the catalog key `<model_id>@<source.name>` of the sidecar. It can pin a version: `<model_id>@<source.name>==<version>`. The catalog key rules of the sidecar spec apply: without a pin, the newest `source.version` wins, and `skellytracker` is reserved for the package root ([Identity](../../model-sidecar/common/identity.md#implementer-guidance); [ADR-88WQ](../../../decisions/entries/88WQ-sidecar-vocabulary.md) item 7).
- `size` is required in a pipeline file, also when the sidecar has one size. The first-size default of the sidecar is for the `detectors` API. A pipeline file names its size, so a run can be repeated.
- `precision` has no fixed default. When `precision` is empty, the node uses `fp16` on a GPU EP and `fp32` on the CPU EP. When the size has no `fp16` artifact, the node uses `fp32` ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 10).
- `execution_provider` is a key of the EP catalog, for example `cuda`, `trt-rtx` or `cpu`. When it is empty, the node uses the EP of the run. There is no EP policy ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 12; [ADR-9NW0](../../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 1).
- `ep_options` holds the EP options of the node. The EP catalog lists the allowed names and values of its EP. When it is empty and the node uses the EP of the run, the node uses the EP options of the run ([ADR-9NW0](../../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 2).
- `object_decode` holds only the fields of the sidecar block [`object.decode`](../../model-sidecar/post/object/decode.md#objectdecode) that the file changes. The mapping nests as the sidecar block nests, for example `object_decode: {nms: {post_nms_top_k: 1}}`. Each other field keeps the value of the sidecar. The defaults come from the sidecar, because a threshold is tuned to one model and one size ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 11). In v1, no value changes during a run (item 1). There is no param for the fields of `keypoint.decode` until a keypoint field can be tuned ([ADR-88WQ](../../../decisions/entries/88WQ-sidecar-vocabulary.md) item 7).
- `max_instances` is the row count `I` of the outputs of a node that makes instances: an object detector or a model with both roles. A top-down keypoint model takes its rows from its `rois` input ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).
- The limit of `max_instances` comes from the selection mode of the sidecar, after the changes of `object_decode` ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 7):
  - `selection: nms` with `nms.post_nms_top_k`: `post_nms_top_k`. A change of `post_nms_top_k` in `object_decode` sets the limit.
  - `selection: top_k`: `top_k`.
  - `selection: none`: `max_detections`, or the row count `Q` of the primary output when `max_detections` is absent.
  - `selection: nms` with no `post_nms_top_k`: the row count `Q` of the primary output.

## Behaviour

- The `role` of the sidecar decides the ports that the node uses ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 5; [ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1):

  | Model | `role` | Inputs | Outputs |
  |---|---|---|---|
  | Object detector | `[object_detector]` | `image` | `detections`, `rois` |
  | Top-down keypoint model | `[keypoint_detector]`, `keypoint.estimator_type` `top_down_single_person` or `top_down_multi_person` | `image`, `rois` | `keypoints` |
  | Bottom-up keypoint model | `[keypoint_detector]`, `keypoint.estimator_type: bottom_up` | `image` | `keypoints` |
  | One-stage model with both roles | `[object_detector, keypoint_detector]` | `image` | `detections`, `rois`, `keypoints` |

- An object detector or a one-stage model gives `max_instances` rows ([Graph](../graph.md#behaviour) item 8). The present rows come first, in descending score order. Padding rows come last. A missing point is NaN with the score 0 ([Decoded keypoints](../../model-sidecar/post/keypoint/schema.md#decoded-keypoints)).
- Each `detections` row has a `class_index`: the class index that the sidecar decode keeps ([Selection behaviour](../../model-sidecar/post/object/decode.md#selection-behaviour) shared step 1). The output schema gives the `class_names` from [`object.classes`](../../model-sidecar/post/object/decode.md#objectclasses) of the sidecar ([Outputs](../outputs.md#fields)).
- The `rois` output holds the box of each `detections` row as an ROI with rotation 0 ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 8).
- An object detector or a one-stage model sets the `instance_score` of each `rois` and `keypoints` row: the `score` of its `detections` row. A top-down keypoint model copies the `instance_score` of its `rois` row ([Graph](../graph.md#behaviour) item 8).
- A top-down keypoint model runs once for each present row of its `rois` input. Row `i` of `keypoints` belongs to row `i` of `rois`. A row that is not present gives a keypoint row that is not present ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).
- **Crop.** Only the detector node cuts pixels, always from `frame.image` ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 8). The steps are in this order:
  1. The glue nodes make the ROI. The ROI rules of `roi_from_points` apply the shift, then the square, then `expand_ratio` ([ROI from points](roi_from_points.md#behaviour) step 9).
  2. Right before the warp, the detector node applies the padding and the aspect fix of the crop of its sidecar ([Affine crop](../../model-sidecar/pre/resize-affine-crop.md#behaviour): `crop_policy.expand_ratio` and `crop_policy.maintain_aspect_ratio`).

  Two growth factors multiply. For example, an ROI with `expand_ratio: 1.2` and a sidecar `crop_policy.expand_ratio` of 1.25 give a crop 1.5 times the size of the points box.
- **Rotated ROI.** The sidecar crop takes the ROI with its rotation ([Affine crop](../../model-sidecar/pre/resize-affine-crop.md#behaviour)). A box is an ROI with rotation 0.
- **Batch.** A top-down keypoint model batches its crops: k × the camera count × the `I` of the instance source of its `rois` input ([Running](../running.md#behaviour) item 3).
- NMS is a part of the postprocessing of the model. The sidecar section [`post.object.selection.nms`](../../model-sidecar/post/object/selection-nms.md#behaviour) defines it ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 9).
- The timing points are `preprocess`, `inference` and `postprocess` ([ADR-Q59W](../../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 1).

## Validation rules

- [ ] `V-node.detector-1` When `sidecar_sha256` is present, it must equal the SHA-256 of the bytes of the sidecar file that `key` resolves. The error message of a mismatch must name both hashes.
- [ ] `V-node.detector-2` The `role` of the model must match its use. A node with a `rois` input must be a keypoint model with the [`keypoint.estimator_type`](../../model-sidecar/post/keypoint/schema.md#fields) `top_down_single_person` or `top_down_multi_person`. A top-down keypoint model must have a `rois` input. A `bottom_up` keypoint model and an object detector must not have a `rois` input. Each output port of the node that the graph uses must be an output of the role ([Behaviour](#behaviour)).
- [ ] `V-node.detector-3` Each name in `object_decode` must be a field that the sidecar spec allows in the `object.decode` block of that sidecar. Its value must have the type and the range of that field.
- [ ] `V-node.detector-4` `size` must be a size key of the `sizes` of the sidecar. When `precision` is present, `sizes.<size>.onnx.precision_artifacts` must have that precision.
- [ ] `V-node.detector-5` `max_instances` must not be more than the limit of the model ([Fields](#fields)).

## Implementer guidance

- The host runs one NMS implementation ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 9). The sidecar section [`post.object.selection.nms`](../../model-sidecar/post/object/selection-nms.md#behaviour) gives its steps.
- A shipped or an exported pipeline file must have `sidecar_sha256` ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 10). For a hand-written file with no `sidecar_sha256`, the loader logs the hash that it resolves.
- The host does the checks of this section at load, because they need the sidecar. The reference model does not do them (`specs/pipeline/reference/pipeline_config.py`).
- The runtime builds each ONNX session with `eps.build_session()` ([ADR-48PG](../../../decisions/entries/48PG-pipeline-api-ep-options-and-warnings.md) item 5). The session runs on the requested EP, or the start of the run fails before frame 0 ([ADR-9NW0](../../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 4). When a session has nodes on the CPU EP, the run gives the warning `ep_partial_placement` ([ADR-48PG](../../../decisions/entries/48PG-pipeline-api-ep-options-and-warnings.md) item 6; [ADR-9NW0](../../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 5).
- In one run, nodes with the same artifact `sha256`, batch, EP key, EP options and device share one inference session. No session is shared between runs. The file says nothing about it ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 6).
- The ONNX `NonMaxSuppression` session of the node requests `cpu` ([ADR-9NW0](../../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 7).

## Authoring guidance

- Write only the params that the file changes ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 11).
- To keep only the best detection of a single-person pipeline, set `object_decode.nms.post_nms_top_k` to 1. The built-in `yolox-rtmw-wholebody` does this ([ADR-48PG](../../../decisions/entries/48PG-pipeline-api-ep-options-and-warnings.md) item 3).

## Examples

A person detector and a top-down keypoint model, as in the built-in `yolox-rtmw-wholebody`. The models are the sidecar examples [`yolox-person.yaml`](../../model-sidecar/examples/detectors/object_detectors/yolox-person/yolox-person.yaml) and [`rtmw-wholebody133.yaml`](../../model-sidecar/examples/detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133.yaml).

```yaml
nodes:
  - id: person
    type: detector
    inputs: {image: frame.image}
    params:
      key: yolox-person@openmmlab-exporter
      size: t
      object_decode: {nms: {post_nms_top_k: 1}}
  - id: wholebody
    type: detector
    inputs: {image: frame.image, rois: person.rois}
    params:
      key: rtmw-wholebody133@openmmlab-exporter
      size: m
      precision: fp32
```

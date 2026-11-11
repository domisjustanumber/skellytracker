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
| `key` | `str` |  | required | no | The catalog key of the model, `<model_id>@<source>`. | ADR-7NY2 item 10 |
| `sidecar_sha256` | `str \| None` |  | `null` | no | The SHA-256 of the sidecar file bytes. Required in a shipped or an exported file. | ADR-7NY2 item 10 |
| `size` | `str` |  | required | no | A size name of the `sizes` of the sidecar. | ADR-7NY2 item 10 |
| `precision` | `Optional[Literal['fp32', 'fp16']]` |  | `null` | no | The precision of the artifact. Empty: fp16 on a GPU EP, fp32 on CPU. | ADR-7NY2 item 10 |
| `execution_provider` | `str \| None` |  | `null` | no | A concrete EP for this node. Empty: the EP of the run. | ADR-7NY2 item 12 |
| `max_instances` | `int` | >= 1 | `1` | no | The number of instance rows that this node makes (object detector or one-stage model). | ADR-99MH item 1 |
| `decode` | `dict[str, Any]` |  | `{}` | no | Changes of the `decode` fields of the sidecar. The load checks each name against the sidecar. | ADR-7NY2 item 11 |
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
- `precision` has no fixed default. When `precision` is empty, the node uses `fp16` on a GPU EP and `fp32` on the CPU EP ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 10).
- `execution_provider` is a concrete EP, for example `cuda`, `tensorrt` or `cpu`. When it is empty, the node uses the EP of the run. There is no EP policy ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 12).
- `decode` holds only the `decode` fields that the file changes. For a pose model, these are the fields of `pose.decode`. The mapping nests as the sidecar nests, for example `decode: {nms: {post_nms_top_k: 1}}`. Each other field keeps the value of the sidecar. The defaults come from the sidecar, because a threshold is tuned to one model and one size. The sidecar spec marks each `decode` field `live: yes` or `live: no` ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 11). In v1, no value changes during a run (item 1).
- `max_instances` is the row count `I` of the outputs of a node that makes instances: an object detector or a model with both roles. A top-down keypoint model takes its rows from its `rois` input ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).
- The limit of `max_instances` comes from the selection mode of the sidecar ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 7):
  - `selection: nms` with `nms.post_nms_top_k`: `post_nms_top_k`.
  - `selection: top_k`: `top_k`.
  - Other cases: the row count of the primary output of the graph.

## Behaviour

- The `role` of the sidecar decides the ports that the node uses ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 5; [ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1):

  | Model | `role` | Inputs | Outputs |
  |---|---|---|---|
  | Object detector | `[object_detector]` | `image` | `detections`, `rois` |
  | Top-down keypoint model | `[pose_estimator]`, `pose.requires_object_detector: true` | `image`, `rois` | `keypoints` |
  | One-stage model with both roles | `[object_detector, pose_estimator]` | `image` | `detections`, `rois`, `keypoints` |

- An object detector or a one-stage model gives `max_instances` rows. The present rows come first, in descending score order. Padding rows come last. A missing point is NaN with visibility 0 ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).
- The `rois` output holds the box of each `detections` row as an ROI with rotation 0 ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 8).
- A top-down keypoint model runs once for each present row of its `rois` input. Row `i` of `keypoints` belongs to row `i` of `rois`. A row that is not present gives a keypoint row that is not present ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).
- NMS is a part of the postprocessing of the model. The sidecar section [`post.det.selection.nms`](../../model-sidecar/post/object/selection-nms.md) defines it ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 9).
- The timing points are `preprocess`, `inference` and `postprocess` ([ADR-Q59W](../../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 1).

## Validation rules

- [ ] `V-node.detector-1` When `sidecar_sha256` is present, it must equal the SHA-256 of the bytes of the sidecar file that `key` resolves. The error message of a mismatch must name both hashes.
- [ ] `V-node.detector-2` The `role` of the model must match its use. A node with a `rois` input must be a top-down keypoint model (`pose.requires_object_detector: true`). A top-down keypoint model must have a `rois` input. An object detector must not have a `rois` input. Each output port of the node that the graph uses must be an output of the role ([Behaviour](#behaviour)).
- [ ] `V-node.detector-3` Each name in `decode` must be a `decode` field of the sidecar. Its value must have the type and the range of that field.
- [ ] `V-node.detector-4` `size` must be a size name of the `sizes` of the sidecar. When `precision` is present, `sizes.<size>.onnx.precision_artifacts` must have that precision.
- [ ] `V-node.detector-5` `max_instances` must not be more than the limit of the model ([Fields](#fields)).

## Implementer guidance

- The host runs one NMS implementation: an ONNX `NonMaxSuppression` graph on the CPU provider of ONNX Runtime. It is the same as the OpenMMLab-Exporter `NmsDecoder`, which the sidecar vectors verify against. It uses `max_output_boxes_per_class` `2**31-1` ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 9).
- A shipped or an exported pipeline file must have `sidecar_sha256` ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 10). For a hand-written file with no `sidecar_sha256`, the loader logs the hash that it resolves.
- The host does the checks of this section at load, because they need the sidecar. The reference model does not do them (`specs/pipeline/reference/pipeline_config.py`).
- The runtime builds each ONNX session with `eps.build_session()` ([ADR-8NVD](../../../decisions/entries/8NVD-pipeline-api-warnings-and-catalog.md) item 5). When the requested EP and the used EP differ, the run gives the warning `ep_fallback` (item 6).
- In one process, nodes with the same artifact `sha256`, batch and execution share one inference session. The file says nothing about it ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 6).

## Authoring guidance

- Write only the params that the file changes ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 11).
- To keep only the best detection of a single-person pipeline, set `decode.nms.post_nms_top_k` to 1. The built-in `yolox-rtmw-wholebody` does this ([ADR-8NVD](../../../decisions/entries/8NVD-pipeline-api-warnings-and-catalog.md) item 3).

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
      decode: {nms: {post_nms_top_k: 1}}
  - id: wholebody
    type: detector
    inputs: {image: frame.image, rois: person.rois}
    params:
      key: rtmw-wholebody133@openmmlab-exporter
      size: m
      precision: fp32
```

---
id: pipeline.taps
title: Taps
kind: pipeline
vectors: null
status: {spec: draft}
---

# Taps

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A tap writes the value of a port to files, or reads the value of a port from files. A `record` tap writes the value during the run. A `replay` tap reads the value, and the upstream nodes do not run. This section gives the tap fields, the tap folder, the file forms and the manifest `tap.json` ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 5).

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `instrumentation.taps` | array | no | The taps. Default: no tap. |
| `instrumentation.taps[].action` | enum | yes | `record` writes the port. `replay` reads the port from files. |
| `instrumentation.taps[].port` | string | yes | The port reference `<node>.<port>`, with no `@prev`. The frame port `frame.image` is not a tap port. |
| `instrumentation.taps[].name` | name | yes | The name of the tap and of its sub-folder. |

The layout of one tap:

```text
<tap folder>/<name>/
  tap.json                 # the manifest, written last
  <port_type>.jsonl        # detections, keypoints or roi: one line for each present row
  <image_id>.npy           # image or tensor: one file for each image
```

The file form of each port type:

| Port type | File form |
|-----------|-----------|
| `detections` | `detections.jsonl`: COCO result records, with `class` (the class name from the `class_names` of the output schema) in place of `category_id`. The consumer maps the name to the category id of its data set. A class index plus 1 is not a COCO category id ([Object decode](../model-sidecar/post/object/decode.md#authoring-guidance)). |
| `keypoints` | `keypoints.jsonl`: COCO keypoint records. `score` is the `instance_score` of the row. The tap applies no rescoring. A consumer applies its own rule, for example the `score_mode` of mmpose, from `instance_score` and the point scores. |
| `roi` | `roi.jsonl`: records with `roi: [cx, cy, w, h, rotation]` and `score`, the `instance_score` of the row. |
| `image` | One `<image_id>.npy` file for each image. |
| `tensor` | One `<image_id>.npy` file for each image. |

Each JSONL line is one present row. Each line has the keys `image_id`, `frame_index`, `camera_id` and `row`. `row` is the row index of the line, in `[0, I)`. The lines of one image are in ascending `row` order. The images are in the order of the image list. A padding row has no line.

The fields of `tap.json`:

| Field | Description |
|-------|-------------|
| `schema` | `skellytracker.tap/1`. |
| `skellytracker_version` | The version of skellytracker that wrote the tap. |
| `run_id` | The id of the run that wrote the tap. |
| `port` | The port reference of the tap. |
| `port_type` | The port type of the tap port. |
| `point_names` | The point names of a `keypoints` port, else null. |
| `class_names` | The class names of a `detections` port, as the output schema gives them, else null. |
| `geometry` | The geometry of a `keypoints` port, else null. |
| `upstream_sha256` | The SHA-256 of the canonical JSON ([Timing](timing.md#behaviour) item 5) of the list of the resolved configs of the tapped node and of each node upstream of it, also through `@prev` inputs, sorted by node id. A resolved config is the item of the node in `PipelineConfig.model_dump(mode="json")`. |
| `nodes` | The node items of the timing header ([Timing](timing.md#fields)) of the tapped node and its upstream nodes, each with `artifact_sha256`. |
| `image_list_sha256` | The hash of the image list ([Timing](timing.md#behaviour) item 6), or null. |
| `camera_ids` | The camera ids of the run. |
| `running_mode` | The running mode of the run. |
| `pipeline_sha256` | The `pipeline_sha256` of the run ([Timing](timing.md#behaviour) item 5). It is information only. |
| `record_count` | The number of JSONL lines, or the number of `.npy` files. |

## Behaviour

1. The run parameter tap folder gives the folder of the taps. Each tap has one sub-folder with its name. There is no default folder in the repository ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 5).
2. **Record.** A `record` tap refuses a sub-folder that exists and is not empty. It writes the value of its port on each frame. It writes `tap.json` last: to a temporary file, then a rename. A sub-folder with no `tap.json` holds a partial record.
3. **Replay.** A `replay` tap reads the value of its port from its files. Each line fills the row that its `row` gives. Each other row is a padding row. A `keypoints` or `roi` line gives the `instance_score` of its row from its `score`. A `detections` line gets its `class_index` from its `class` and the `class_names` of the output schema of the port (`V-pipeline.taps-7`). A port whose node is an instance source has its present rows first ([Graph](graph.md#behaviour) item 8), so its lines have the rows `0` to `n - 1`. A port of a fan-out child can have a padding row before a present row (`V-pipeline.taps-6`). The node of that port and its upstream nodes do not run when nothing else uses them ([Running](running.md#behaviour)).
4. **Match.** A replay compares `tap.json` with the run. These fields must agree: `schema`, `port`, `port_type`, `upstream_sha256`, `image_list_sha256`, `camera_ids`, `running_mode`, and the `sidecar_sha256`, the `artifact_sha256` and the `used_ep` of each node item (`V-pipeline.taps-3`). The device is information only. The pipeline file can differ, so `pipeline_sha256` is information only. The tap has no hash of its data files.
5. **No video replay yet.** A replay refuses a tap with `image_list_sha256: null`. Thus only a tap of the COCO input form can be replayed in this version.
6. In the COCO input form, `image_id` comes from the COCO file ([Timing](timing.md#behaviour) item 6). For video, `image_id` is `frame_index × n_cameras + camera_index`. `camera_index` is the position of the camera id in the camera ids of the run.
7. Crops and tensors of dataset images must not be committed to a repository ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 5).

## Validation rules

- [ ] `V-pipeline.taps-1` Each tap must name an existing node and an output port of the type of that node, with no `@prev`. The frame port `frame.image` must not be a tap port. Each tap name must be a name and must be unique in the file.
- [ ] `V-pipeline.taps-2` A run of a file with a tap must have a tap folder.
- [ ] `V-pipeline.taps-3` A replay must refuse a tap with no `tap.json`, a tap with `image_list_sha256: null`, and a tap whose `tap.json` does not agree with the run in a field of [Behaviour](#behaviour) item 4.
- [ ] `V-pipeline.taps-4` The files of a replay tap must cover each frame and each camera of the run.
- [ ] `V-pipeline.taps-5` A record tap must refuse a sub-folder that exists and is not empty.
- [ ] `V-pipeline.taps-6` A replay must refuse a line whose `row` is not an integer in `[0, I)`, and a `row` that occurs twice for one image. For a port whose node is an instance source, it must also refuse the lines of an image whose `row` values are not `0` to `n - 1`, with `n` the number of lines of that image.
- [ ] `V-pipeline.taps-7` A replay must refuse a `detections` line whose `class` is not a name of the `class_names` of the output schema of the port.

## Implementer guidance

- The reference model checks `V-pipeline.taps-1` in `check_structure`. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- A `replay` tap takes the place of the old `precomputed` detector ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 13).
- The first draft compared a hash of the whole pipeline file. A replay config always differs from its record config, because it has the `replay` tap. `upstream_sha256` holds only the nodes that make the tapped value.

## Authoring guidance

- To measure one detector node, replay its upstream outputs ([Timing](timing.md#authoring-guidance); [ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 4).

## Examples

```yaml
instrumentation:
  taps:
    - {action: replay, port: person.rois, name: person-rois}
    - {action: record, port: wholebody.keypoints, name: wholebody-keypoints}
```

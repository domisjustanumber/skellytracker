---
id: pipeline.taps
title: Taps
kind: pipeline
vectors: null
status: {spec: draft}
---

# Taps

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A tap writes the value of a port to files, or reads the value of a port from files. A `record` tap writes the value during the run. A `replay` tap reads the value, and the upstream nodes do not run. This section gives the tap fields, the tap folder, the file forms and the manifest ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 5).

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `instrumentation.taps` | array | no | The taps. Default: no tap. |
| `instrumentation.taps[].kind` | enum | yes | `record` writes the port. `replay` reads the port from files. |
| `instrumentation.taps[].port` | string | yes | The port reference `<node>.<port>`. |
| `instrumentation.taps[].name` | name | yes | The name of the tap and of its sub-folder. |

The file form of each port type:

| Port type | File form |
|-----------|-----------|
| `detections` | JSONL of COCO result records. |
| `keypoints` | JSONL of COCO keypoint records, one row for each input ROI. |
| `roi` | JSONL with `roi: [cx, cy, w, h, rotation]`. |
| `image` | One `.npy` file for each `image_id`. |
| `tensor` | One `.npy` file for each `image_id`. |

The keys of each row: `image_id`, `frame_index` and `camera_id`.

The sub-folder of each tap holds a `tap.json` manifest. The manifest holds:

- the SHA-256 of the artifact, of the sidecar, of the image list, of the node params and of the pipeline file;
- the EP and the device.

This draft does not fix the field names of the manifest and the names of the data files.

## Behaviour

1. The run parameter tap folder gives the folder of the taps. Each tap has one sub-folder with its name. There is no default folder in the repository ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 5).
2. A `record` tap writes the value of its port on each frame.
3. A `replay` tap reads the value of its port from its files. The node of that port and its upstream nodes do not run when nothing else uses them ([Running](running.md#behaviour)).
4. In the COCO input form, `image_id` comes from the COCO file ([Timing](timing.md#behaviour)). For video, `image_id` is `frame_index × n_cameras + camera_index`. `camera_index` is the position of the camera id in the camera ids of the run.
5. Crops and tensors of dataset images must not be committed to a repository ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 5).

## Validation rules

- [ ] `V-pipeline.taps-1` Each tap must name an existing node and an output port of the type of that node. Each tap name must be a name and must be unique in the file.
- [ ] `V-pipeline.taps-2` A run of a file with a tap must have a tap folder.
- [ ] `V-pipeline.taps-3` A replay must refuse a tap whose manifest does not agree with the run: the hashes of the artifact, the sidecar, the image list, the node params and the pipeline file, the EP and the device.
- [ ] `V-pipeline.taps-4` The files of a replay tap must hold a row for each frame and each camera of the run.

## Implementer guidance

- The reference model checks `V-pipeline.taps-1` in `check_structure`. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- A `replay` tap takes the place of the old `precomputed` detector ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 13).

## Authoring guidance

- To measure one detector node, replay its upstream outputs ([Timing](timing.md#authoring-guidance); [ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 4).

## Examples

```yaml
instrumentation:
  taps:
    - {kind: replay, port: person.rois, name: person-rois}
    - {kind: record, port: wholebody.keypoints, name: wholebody-keypoints}
```

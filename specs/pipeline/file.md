---
id: pipeline.file
title: Pipeline file
kind: pipeline
vectors: null
status: {spec: draft}
---

# Pipeline file

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A pipeline file is one YAML file that gives one pipeline config. It names the nodes of the graph, the public outputs and the instrumentation. It refers to sidecars and never copies them. This section gives the top-level keys, the input forms, the key of a pipeline and the discovery of pipeline files ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) items 1 to 3; [ADR-8NVD](../../decisions/entries/8NVD-pipeline-api-warnings-and-catalog.md) item 2).

## Fields

A **name** is a string that matches `^[a-z][a-z0-9_-]*$`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | The pipeline spec version, in SemVer, in quotes, for example `"2.0.0"`. The [changelog](changelog.md#revisions) gives the versions. |
| `pipeline_id` | name | yes | The id of the pipeline. The file name is `<pipeline_id>.pipeline.yaml`. |
| `source` | name | yes | Who made the file, for example `skellytracker`. The key of the pipeline is `<pipeline_id>@<source>`. |
| `description` | string | no | A short text for people. Default: empty. |
| `nodes` | array | yes | The nodes of the graph, in any order. [Graph](graph.md) gives the node fields. |
| `outputs` | mapping | yes | Public output name to port. [Outputs](outputs.md) gives the fields. |
| `instrumentation` | mapping | no | The keys `timing_points` ([Timing](timing.md)) and `taps` ([Taps](taps.md)). Default: no timing point and no tap. |

## Behaviour

1. **Fixed at start.** A pipeline is fixed when its run starts. A run takes no overrides of the config. To change a pipeline, load the config, change it and give the changed config to the run. Live changes of params wait for a later version ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 1).
2. **Input forms.** A host accepts a YAML file, a JSON file or a mapping that holds the same keys. A YAML loader must use a safe load (`yaml.safe_load` or an equivalent loader that makes only plain data). It must refuse a duplicate key ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 2).
3. **Strict.** An unknown key is an error at each level of the config, also in `params` ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) items 2 and 11).
4. **No code.** A pipeline file runs no user code. The node types are a closed set. A new node type is a spec change ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6; [ADR-AD33](../../decisions/entries/AD33-bundles-are-untrusted-input.md)).
5. **Sidecar references.** A detector node refers to its model by `key` and `sidecar_sha256`. A config never copies the content of a sidecar ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 3). The [detector node](nodes/detector.md) section gives these params.
6. **Key.** The key of a pipeline is `<pipeline_id>@<source>`. When the same key is in two roots, a list of the pipelines shows both files. A load by that key is then an error that names both paths. A load by path always works ([ADR-8NVD](../../decisions/entries/8NVD-pipeline-api-warnings-and-catalog.md) item 2).
7. **Discovery.** A host finds the pipeline files that match `*.pipeline.yaml` in two roots ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 2):
   - the package root `core/model_zoo/pipelines/`;
   - `<user root>/pipelines/`. The user root is the argument of the call, then the environment variable `SKELLYTRACKER_USER_ROOT`, then `platformdirs.user_data_dir("skellytracker", appauthor=False)` + `/models` ([ADR-AQR4](../../decisions/entries/AQR4-detectors-and-pipelines-entry-points.md) item 6).
8. **Export.** An export writes the config in one of two forms ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 3):
   - as written: only the keys and the params that the config gives;
   - resolved: each param of each node, with its default when the config does not give it.

## Validation rules

- [ ] `V-pipeline.file-1` `schema_version` must be a SemVer string. It must be a version heading of [`changelog.md`](changelog.md#revisions) or a pre-release that the changelog records. Until 2.0.0 is released, the only valid value is `"2.0.0"`.
- [ ] `V-pipeline.file-2` `pipeline_id` and `source` must be names. The name of a pipeline file must be `<pipeline_id>.pipeline.yaml`.
- [ ] `V-pipeline.file-3` The config must have no unknown key at any level.
- [ ] `V-pipeline.file-4` The config must have `schema_version`, `pipeline_id`, `source`, `nodes` with at least one node, and `outputs` with at least one entry.
- [ ] `V-pipeline.file-5` A YAML pipeline file must have no duplicate key in a mapping.

## Implementer guidance

- The reference model `PipelineConfig` in [`reference/pipeline_config.py`](reference/pipeline_config.py) checks the SemVer form of `V-pipeline.file-1`, the name pattern of `V-pipeline.file-2`, `V-pipeline.file-3` (`extra="forbid"`) and `V-pipeline.file-4`. It does not check the changelog versions, the file name or duplicate keys. The host does these checks at load. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- `tools/make_pipeline_schema.py` makes `pipeline.schema.json` from `PipelineConfig` ([ADR-3SF2](../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 3).

## Authoring guidance

- Write only the params that you change. The defaults of a detector node come from the `decode` fields of its sidecar. The node sections give the defaults of the other node types ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 11).
- A shipped or an exported file must give `sidecar_sha256` for each detector node ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 10). The hand-written [examples](examples/) do not give it.

## Examples

```yaml
schema_version: "2.0.0"
pipeline_id: mediapipe-holistic-tasks
source: skellytracker
description: MediaPipe Holistic, one Tasks landmarker on the full frame.
nodes:
  - id: holistic
    type: mediapipe_tasks
    inputs: {image: frame.image}
    params: {variant: holistic}
outputs:
  body: holistic.keypoints
```

The [examples](examples/) folder holds the full examples.

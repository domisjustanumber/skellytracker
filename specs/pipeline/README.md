# Pipeline Specification

## Overview

A **pipeline** is one YAML file that connects models and glue steps into a graph. Each node of the graph is one detector model, one MediaPipe Tasks landmarker or one glue node. The edges are the ports. The file names the public outputs, the timing points and the taps. A run takes the file and frames of one or more cameras, and gives the outputs of each camera. The pipeline spec never defines model processing. The preprocessing, the inference and the postprocessing of a model are in the [sidecar spec](../model-sidecar/README.md). A change of model processing is a sidecar proposal ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md); [ADR-3SF2](../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md)).

This document is the one entry point of the pipeline spec.

Also: [Changelog](changelog.md), [examples](examples/) and the [decision log](decisions/README.md) of this module.

## Status

The pipeline spec is a draft. Each section is `draft`. The `schema_version` of a pipeline file follows the skellytracker version. The open target is `2.0.0` ([Changelog](changelog.md#revisions)).

## Reading order

1. [Pipeline file](file.md): the top-level keys, the input forms, the key and the discovery.
2. [Graph](graph.md): the nodes, the ports, the ROI type, the empty values and the instance rows.
3. [Outputs](outputs.md): the public outputs, the result of each camera and the output schema.
4. The node sections in [`nodes/`](#section-map): the params and the ports of each node type.
5. [Running](running.md): the running modes, the batch, the warnings and the start checks.
6. [Timing](timing.md) and [Taps](taps.md): the instrumentation.
7. The [examples](examples/).

## Conventions

- "must" marks a requirement.
- "must not" marks a prohibition.
- "can" marks a permitted option.
- A rule ID `V-<section-id>-<n>` names one checklist rule. Each rule is in the section of the thing that it constrains ([ADR-3SF2](../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 2).
- The section ID is the `id` in the front matter of a section file.
- The headings Fields, Behaviour and Validation rules of a section are normative. The headings Implementer guidance, Authoring guidance and Examples are informative.
- The CLI and the Python API are not spec sections.

## Section status

The field `status.spec` in the front matter of a section file gives the status of the section: `stable` or `draft`. The front matter is the authority.

1. Each section starts as `draft`. A `draft` section is normative.
2. The first body line of a `draft` section, after its title, is the banner "This section is a draft. ...". A `stable` section has no banner.
3. A `draft` section becomes `stable` when all of these conditions are true:
   - An example uses the section.
   - Vectors or a named test cover each algorithm of the section ([ADR-3SF2](../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 4).
   - A decision entry exists for the section.
   - The user approves the change.
4. The change to `stable` is a content change. It changes `status.spec`, removes the banner and adds a row to the [summary of changes](changelog.md#summary-of-changes).

## Section map

### Pipeline

| Section ID | File | Kind |
|------------|------|------|
| `pipeline.file` | [file.md](file.md) | pipeline |
| `pipeline.graph` | [graph.md](graph.md) | pipeline |
| `pipeline.outputs` | [outputs.md](outputs.md) | pipeline |
| `pipeline.running` | [running.md](running.md) | pipeline |
| `pipeline.timing` | [timing.md](timing.md) | pipeline |
| `pipeline.taps` | [taps.md](taps.md) | pipeline |

### Nodes

The node types are a closed set. A new node type is a spec change ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6).

| Section ID | File | Kind |
|------------|------|------|
| `node.detector` | [nodes/detector.md](nodes/detector.md) | node |
| `node.mediapipe_tasks` | [nodes/mediapipe_tasks.md](nodes/mediapipe_tasks.md) | node |
| `node.roi_from_points` | [nodes/roi_from_points.md](nodes/roi_from_points.md) | node |
| `node.roi_tracking` | [nodes/roi_tracking.md](nodes/roi_tracking.md) | node |
| `node.gate` | [nodes/gate.md](nodes/gate.md) | node |
| `node.first_of` | [nodes/first_of.md](nodes/first_of.md) | node |
| `node.concat` | [nodes/concat.md](nodes/concat.md) | node |
| `node.smooth_keypoints` | [nodes/smooth_keypoints.md](nodes/smooth_keypoints.md) | node |
| `node.smooth_roi` | [nodes/smooth_roi.md](nodes/smooth_roi.md) | node |
| `node.redetect` | [nodes/redetect.md](nodes/redetect.md) | node |

## Generated files

Do not edit these files by hand. `tools/make_pipeline_schema.py` makes them from the reference model [`reference/pipeline_config.py`](reference/pipeline_config.py) ([ADR-3SF2](../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 3):

- `pipeline.schema.json`: the JSON Schema of a pipeline file. It is descriptive. The `V-` rules hold the checks that a schema cannot hold.
- The params table and the ports table of each node section, between the `node-table` markers.

## Terms

| Term | Meaning |
|------|---------|
| node | One step of the graph, with an `id`, a `type`, named `inputs` and `params`. |
| port | A named input or output of a node, with a port type. A reference to an output port is `<node>.<port>`. |
| glue node | A node of a type that the pipeline spec defines and that runs no model: `roi_from_points`, `roi_tracking`, `gate`, `first_of`, `concat`, `smooth_keypoints`, `smooth_roi` and `redetect`. |
| ROI | A region of the source image: `(cx, cy, w, h, rotation)` in source-image pixels. A box is an ROI with rotation 0. |
| instance row | One row of a `roi`, `keypoints` or `detections` value: one instance, present or padding ([Graph](graph.md#behaviour)). |
| frame | The reserved source of the graph. Its port `frame.image` is the camera frame of the call. |
| stateful pipeline | A pipeline with an `@prev` input, or with a stateful node upstream of a detector node ([Running](running.md#behaviour)). |

## Validation index

A pipeline file and its run are valid when all of the following rules hold.

- [Pipeline file](file.md#validation-rules): `V-pipeline.file-1`, `V-pipeline.file-2`, `V-pipeline.file-3`, `V-pipeline.file-4`, `V-pipeline.file-5`
- [Graph](graph.md#validation-rules): `V-pipeline.graph-1`, `V-pipeline.graph-2`, `V-pipeline.graph-3`, `V-pipeline.graph-4`, `V-pipeline.graph-5`, `V-pipeline.graph-6`, `V-pipeline.graph-7`
- [Outputs](outputs.md#validation-rules): `V-pipeline.outputs-1`, `V-pipeline.outputs-2`
- [Running](running.md#validation-rules): `V-pipeline.running-1`, `V-pipeline.running-2`, `V-pipeline.running-3`, `V-pipeline.running-4`, `V-pipeline.running-5`
- [Timing](timing.md#validation-rules): `V-pipeline.timing-1`
- [Taps](taps.md#validation-rules): `V-pipeline.taps-1`, `V-pipeline.taps-2`, `V-pipeline.taps-3`, `V-pipeline.taps-4`
- [Detector node](nodes/detector.md#validation-rules)
- [MediaPipe Tasks node](nodes/mediapipe_tasks.md#validation-rules): `V-node.mediapipe_tasks-1`, and the other rules of the section
- [ROI from points node](nodes/roi_from_points.md#validation-rules): `V-node.roi_from_points-1`, and the other rules of the section
- [ROI tracking node](nodes/roi_tracking.md#validation-rules)
- [Gate node](nodes/gate.md#validation-rules): `V-node.gate-1`, and the other rules of the section
- [First-of node](nodes/first_of.md#validation-rules)
- [Concat node](nodes/concat.md#validation-rules)
- [Smooth keypoints node](nodes/smooth_keypoints.md#validation-rules)
- [Smooth ROI node](nodes/smooth_roi.md#validation-rules)
- [Redetect node](nodes/redetect.md#validation-rules)

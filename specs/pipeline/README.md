# Pipeline Specification

## Overview

A **pipeline** is one YAML file that connects models and glue steps into a graph. Each node of the graph is one detector model, one MediaPipe Tasks landmarker or one glue node. The edges are the ports. The file names the public outputs, the timing points and the taps. A run takes the file and frames of one or more cameras, and gives the outputs of each camera. The pipeline spec never defines model processing. The preprocessing, the inference and the postprocessing of a model are in the [sidecar spec](../model-sidecar/README.md). A change of model processing is a sidecar proposal ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md); [ADR-3SF2](../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md)).

This document is the one entry point of the pipeline spec.

Also: [Changelog](changelog.md), [examples](examples/) and the [decision log](decisions/README.md) of this module.

## Status

The pipeline spec is a draft. Each section is `draft`. The `schema_version` of a pipeline file follows the skellytracker version. The open target is `2.0.0` ([Changelog](changelog.md#revisions)).

## Reading order

1. [Pipeline file](file.md): the top-level keys, the input forms, the key and the discovery.
2. [Graph](graph.md): the nodes, the ports, the ROI type, the empty values, the point names and the instance rows.
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
| `node.merge` | [nodes/merge.md](nodes/merge.md) | node |
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
| glue node | A node of a type that the pipeline spec defines and that runs no model: `roi_from_points`, `roi_tracking`, `gate`, `first_of`, `concat`, `merge`, `smooth_keypoints`, `smooth_roi` and `redetect`. |
| ROI | A region of the source image: `(cx, cy, w, h, rotation)` in source-image pixels, with `rotation` in radians, clockwise, in `[-π, π)`. A box is an ROI with rotation 0 ([Graph](graph.md#behaviour) item 3). |
| instance row | One row of a `roi`, `keypoints` or `detections` value: one instance, present or padding ([Graph](graph.md#behaviour) item 8). |
| instance source | The node that makes the instance rows of a value: an object detector, a one-stage model or a `mediapipe_tasks` node ([Graph](graph.md#behaviour) item 8). |
| point name | `<prefix>.<point>`, for example `body.left_wrist` ([Graph](graph.md#behaviour) item 7). |
| score | The confidence of a point or a box: the decoded score of the sidecar, or the landmark visibility of MediaPipe. A threshold on a score is `>= 0` and has no upper bound ([ADR-88WQ](../../decisions/entries/88WQ-sidecar-vocabulary.md) item 6). |
| frame | The reserved source of the graph. Its port `frame.image` is the camera frame of the call. |
| stateful pipeline | A pipeline with an `@prev` input, or with a temporal node upstream of a detector node ([Running](running.md#behaviour) item 5). |

The pipeline spec and the sidecar spec use one letter key ([ADR-88WQ](../../decisions/entries/88WQ-sidecar-vocabulary.md) item 5). The sidecar spec defines the letters: [Detection output semantics](../model-sidecar/post/object/outputs.md#detection-output-semantics) and the [shape key](../model-sidecar/post/keypoint/schema.md#shape-key) of the keypoint schema.

| Letter | Meaning |
|--------|---------|
| `B` | The batch. |
| `Q` | The rows of a model output tensor. |
| `I` | The instance rows of a port value. |
| `P` | The points of a keypoint set. |
| `C` | The classes. |

The words `cov` and `noise` name the Kalman covariance and the process noise of [Smooth keypoints](nodes/smooth_keypoints.md#behaviour), so they do not take a letter of the key.

## Validation index

A pipeline file and its run are valid when all of the following rules hold.

- [Pipeline file](file.md#validation-rules): `V-pipeline.file-1` to `V-pipeline.file-5`
- [Graph](graph.md#validation-rules): `V-pipeline.graph-1` to `V-pipeline.graph-8`
- [Outputs](outputs.md#validation-rules): `V-pipeline.outputs-1`, `V-pipeline.outputs-2`
- [Running](running.md#validation-rules): `V-pipeline.running-1` to `V-pipeline.running-6`
- [Timing](timing.md#validation-rules): `V-pipeline.timing-1`
- [Taps](taps.md#validation-rules): `V-pipeline.taps-1` to `V-pipeline.taps-7`
- [Detector node](nodes/detector.md#validation-rules): `V-node.detector-1` to `V-node.detector-5`
- [MediaPipe Tasks node](nodes/mediapipe_tasks.md#validation-rules): `V-node.mediapipe_tasks-1`
- [ROI from points node](nodes/roi_from_points.md#validation-rules): `V-node.roi_from_points-1` to `V-node.roi_from_points-5`
- [ROI tracking node](nodes/roi_tracking.md#validation-rules): `V-node.roi_tracking-1`, `V-node.roi_tracking-2`
- [Gate node](nodes/gate.md#validation-rules): `V-node.gate-1` to `V-node.gate-3`
- [First-of node](nodes/first_of.md#validation-rules): `V-node.first_of-1`, `V-node.first_of-2`
- [Concat node](nodes/concat.md#validation-rules): `V-node.concat-1` to `V-node.concat-3`
- [Merge node](nodes/merge.md#validation-rules): `V-node.merge-1` to `V-node.merge-3`
- [Smooth keypoints node](nodes/smooth_keypoints.md#validation-rules): `V-node.smooth_keypoints-1`, `V-node.smooth_keypoints-3`. The rule `V-node.smooth_keypoints-2` is removed, and its ID is not used again.
- [Smooth ROI node](nodes/smooth_roi.md#validation-rules): no rule yet
- [Redetect node](nodes/redetect.md#validation-rules): `V-node.redetect-1`

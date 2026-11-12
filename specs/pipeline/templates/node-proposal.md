# Node proposal template

This template uses ASD-STE100 Simplified Technical English.

Copy this file to `proposal.md` in the payload of a `proposal` bundle whose `sections` are only
`node.<type>` sections. Fill in each part. Delete these instructions. The workflow is
[Pipeline contributions](../contributions.md). The bundle rules are in the hand-over file of the
model addition workflow (skellytracker ADR-3SF2, item 7).

A node change never changes model processing. A change of preprocessing, inference or decode is a
sidecar proposal. A node change that needs a sidecar change is two proposals, linked with
`depends_on`.

## Header

| Field | Value |
|---|---|
| Title | One line |
| Slug | `<slug>` |
| Date | YYYY-MM-DD |
| Exporter repo | `<repo name>`, or `none` |
| Exporter commit | `<40 hex>`, or `none` |
| Sections | `node.<type>`, … |

## 1. Gap

The pipeline that needs the change, and why the current node types cannot express it. Give a
concrete pipeline file, or the part of one.

## 2. Spec change

### 2.1 Sections

Each changed or new section file in `specs/pipeline/nodes/`.

### 2.2 Params and ports

The params of the node type, with the type, the range, the default, the description and `live` of
each param. The input ports and the output ports, with their port types. skellytracker makes the
node table from the reference model ([Pipeline Spec Rules](../AGENTS.md)). Give the change of
`specs/pipeline/reference/pipeline_config.py` as text.

### 2.3 Behaviour

The new or changed items of the Behaviour heading, in the words of the section.

### 2.4 Validation rules

Each new or changed rule, with its rule ID `V-node.<type>-<n>`.

### 2.5 Changelog row

One row for the summary of changes of `specs/pipeline/changelog.md`.

## 3. Reference implementation

A glue node with an algorithm: `reference/node_<type>.py`. A node with no algorithm: write `none`.

## 4. Vectors

`vectors/node.<type>.yaml`, with the cases of the change. Run `fill` of `tools/make_vectors.py`
before `pack`. A node with no vectors: name the tests that skellytracker adds.

## 5. Evidence

The upstream behaviour that the node follows, for example a MediaPipe graph, with its source and its
version.

## 6. skellytracker implementation proposal

Where the node code goes in `core/pipelines/`, and the tests. From the 2.0.0 pre-release, give the
code as `skellytracker.patch`.

## 7. Pipeline impact

Each pipeline file in `specs/pipeline/examples/` and in `core/model_zoo/pipelines/` that the change
makes invalid, and the edit of each one.

## 8. Alternatives considered

Each other option, and why you did not use it.

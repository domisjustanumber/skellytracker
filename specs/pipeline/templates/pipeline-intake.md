# Pipeline intake template

This template uses ASD-STE100 Simplified Technical English.

Copy this file to `pipeline.md` in the payload of a `pipeline` bundle. Fill in each part. Delete
these instructions. The workflow is [Pipeline contributions](../contributions.md). The bundle rules
are in "Pipeline bundles" of the hand-over file of the model addition workflow (skellytracker
ADR-271H).

## Header

| Field | Value |
|---|---|
| Pipeline | `<pipeline_id>@<source.name>` |
| Exporter repo | `<repo name>` |
| Exporter commit | `<40 hex>` of the pipeline file |
| Spec version | the `schema_version` of the pipeline file |
| Date | YYYY-MM-DD |

## 1. Purpose

One or two sentences: what the pipeline finds, and for which use.

## 2. Models

One row for each `detector` node.

| Node `id` | `key` | `sidecar_sha256` | `size` | State of the sidecar |
|---|---|---|---|---|
| `<id>` | `<model_id>@<source.name>` | `<64 hex>` | `<size>` | landed, or the `model` bundle in `depends_on` |

## 3. Node types

List each node type that the pipeline uses. This is the manifest `sections`. Name each node proposal
that the pipeline needs, with its bundle ID. It is in `depends_on`.

## 4. Reference run

Optional. Give the input, the command and the files of `run/`. Write `none` when you give no
reference run. After stage 1.10 of the skellytracker implementation plan, a run gate compares the
skellytracker run with `run/`.

## 5. Notes and questions to the skellytracker session

Each question about a rule. Cite the rule by its heading and its file.

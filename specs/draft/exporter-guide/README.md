# Exporter guide (draft)

**Status: DRAFT. This guide is not complete.**

This guide will give everything that you need to build an exporter. An exporter is a repo that makes
ONNX files, validates their accuracy, measures their throughput, writes reports and writes their
sidecars. Today, the guide has only its sidecar part. The other parts, for example the architecture,
the phases and the shared code, are not written yet.

A local plan of the user, the exporter implementation plan, owns the creation of this guide. Git
does not track that plan. The plan is deleted at the end of its implementation work, when its
content is in this guide. When the guide is complete, or when an end-to-end test proves that its
first version works, the guide moves from `specs/draft/exporter-guide/` to `specs/exporter-guide/`.
That move needs a new decision entry. Decision
[x64y](../../../decisions/x64y-draft-exporter-guide-folder.md) records this folder, its owner
and its final location.

## What applies now

- The files of [`sidecars/`](sidecars/README.md) are complete, and they apply now.
  [`sidecars/README.md`](sidecars/README.md) gives what is normative.
- A part that is not in this guide has no rule here yet. Until that part moves here, the local plan
  that owns this guide is its source. Ask the user for that plan. Do not use a different draft as a
  rule.

## Add a model or request a spec change

To add a model, or to request a change to the sidecar spec, follow the
[model addition workflow](../../model-sidecar/model-addition-workflow/README.md). It is the same
process for an exporter agent, a human contributor and a skellytracker session. It also holds the
rules for the sidecar files, the validation and the publishing. This guide does not repeat it.

## Files

| File | Content |
|---|---|
| [`README.md`](README.md) | This file: the status, the owner, and the file list. |
| [`sidecars/README.md`](sidecars/README.md) | The entry point of the sidecar part: how to use it, the block for the exporter `AGENTS.md`, and the "Sidecars" section. |
| [`sidecars/where-to-read.md`](sidecars/where-to-read.md) | The steps that check the skellytracker checkout and its branch in an exporter repo. |
| [`sidecars/known-open-items.md`](sidecars/known-open-items.md) | The known open items for the exporter overhaul. They are not a part of the "Sidecars" section. |

## Paths

- In an exporter repo, read this guide in the skellytracker checkout:
  `../freemocap/skellytracker/specs/draft/exporter-guide/`.
- The folder `specs/exporter-guide/` does not exist now. No stub stays at the old paths. The rules
  that applied to each contributor moved to the
  [model addition workflow](../../model-sidecar/model-addition-workflow/README.md).

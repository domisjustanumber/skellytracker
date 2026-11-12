# 271H — Pipeline bundles: a `pipeline` bundle kind; a spec example before the pipeline API; the session updates pinned sidecar hashes

**Status:** absorbed into [`hand-over.md#layout`](../../specs/model-sidecar/model-addition-workflow/hand-over.md#layout), [`hand-over.md#pipeline-bundles`](../../specs/model-sidecar/model-addition-workflow/hand-over.md#pipeline-bundles), [`contributions.md#choose-the-path`](../../specs/pipeline/contributions.md#choose-the-path), [`contributions.md#add-a-pipeline`](../../specs/pipeline/contributions.md#add-a-pipeline), [`file.md#validation-rules`](../../specs/pipeline/file.md#validation-rules), [`pipeline/AGENTS.md#pipeline-spec-rules`](../../specs/pipeline/AGENTS.md#pipeline-spec-rules), [`change-pipeline-spec/SKILL.md#procedure-a-land-a-pipeline-bundle`](../../.claude/skills/change-pipeline-spec/SKILL.md#procedure-a-land-a-pipeline-bundle), [`change-pipeline-spec/SKILL.md#procedure-c-update-the-pinned-hashes-after-a-re-export`](../../.claude/skills/change-pipeline-spec/SKILL.md#procedure-c-update-the-pinned-hashes-after-a-re-export), [`inventory.yaml`](../../specs/pipeline/inventory.yaml), 2026-11-12 (absorb sweep, user; PR: pending).

## Decision

1. **Kind.** An exporter sends a pipeline file in its own bundle,
   `intakes/pipeline-<pipeline_id>@<contributor>/v<k>/`. The payload holds a short `pipeline.md`
   and the file `<pipeline_id>.pipeline.yaml`. A reference run output is optional.
   `tools/intake_bundle.py` gets the bundle kind `pipeline`.
2. **Order.** `depends_on` names each `model` bundle and each node proposal bundle that the pipeline
   needs. The bundle is `waiting` until they land. A pipeline can use the models of more than one
   exporter. It needs no consent step.
3. **Check.** A pipeline file runs no code
   ([File](../../specs/pipeline/file.md#behaviour) item 4). The session checks it only with the code
   of this repository: the reference model of the pipeline spec, the file name, `source.name` (the
   contributor, never `skellytracker`), the model keys (each one resolves to a landed sidecar or to
   a `depends_on` bundle) and each `sidecar_sha256` (it equals the bytes of the landed sidecar).
   After stage 1.10 of the implementation plan, the load checks
   ([ADR-99MH](99MH-pipeline-outputs-and-running.md) item 7) and a run gate also apply. Stage 1.10
   sets the run gate and its tolerance.
4. **Landing.** Before stage 1.10, an accepted pipeline lands in `specs/pipeline/examples/`. Stage
   1.10 copies the examples to `core/model_zoo/pipelines/`
   ([ADR-3SF2](3SF2-pipeline-spec-and-node-workflow.md)). After stage 1.10, an accepted pipeline
   lands in `core/model_zoo/pipelines/`, with a test that loads it by its key.
5. **Hash updates.** When a re-exported sidecar lands, the same commit group changes the
   `sidecar_sha256` of each landed pipeline that uses it. The session makes this edit. The
   contributor sends no new version.
6. **Homes.** `specs/pipeline/inventory.yaml` holds the provenance of each landed pipeline: its
   bundle ID and the exporter commit. `specs/pipeline/templates/` holds the pipeline intake template
   and the node proposal template.

## Reason

- The user selected a new bundle kind, a spec example before stage 1.10 and a hash update by the
  session.
- A pipeline often uses the models of more than one exporter, for example `yolox-rtmw-wholebody`.
  It changes on its own schedule. A `model` bundle cannot hold it.
- The kind reuses `depends_on`, the state `waiting` and the responses.
- A pipeline file is data. The check runs no bundle code, so the risk of
  [ADR-AD33](AD33-bundles-are-untrusted-input.md) stays low.
- `tools/tests/test_pipeline_schema.py` already validates each spec example against the reference
  model.
- A hash update by the session keeps each landed pipeline available after a re-export.

## Consequences

- `tools/intake_bundle.py`, `hand-over.md`, the templates and the skills change (stage 0.2 of the
  implementation plan).
- A later GitHub Issues channel carries a small data file for a pipeline.

## Alternatives rejected

- **The pipeline file in the `model` bundle.** A pipeline that uses the models of two exporters, or
  that comes later, has no home.
- **A note in the intake, and a maintainer writes the file.** No hash check and no provenance. It
  does not scale to all exporters.
- **Wait for stage 1.10.** No pipeline lands in phase 0 or early in phase 1.
- **The exporter sends a new version for a hash change.** The pipeline is unavailable until then.

## Open work

See [open-work.md](../open-work.md).

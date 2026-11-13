---
name: change-pipeline-spec
description: Use this skill in skellytracker when you land a pipeline bundle or an accepted node proposal of the pipeline spec. Use it also when a re-exported sidecar changes the sidecar_sha256 of a landed pipeline, and for any other edit to the pipeline spec.
---

# Change the pipeline spec

This skill uses ASD-STE100 Simplified Technical English.

This skill lands the contributions of [Pipeline contributions](../../../specs/pipeline/contributions.md).
It runs only in skellytracker. The user decides each acceptance. The bundle rules are in
[Hand-over bundles](../../../specs/model-sidecar/model-addition-workflow/hand-over.md)
([ADR-3SF2](../../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 7;
[ADR-271H](../../../decisions/entries/271H-pipeline-bundles.md)). The rules of
[`change-sidecar-spec`](../change-sidecar-spec/SKILL.md) apply where this skill links to them.

## Read first

1. Read [`specs/pipeline/AGENTS.md`](../../../specs/pipeline/AGENTS.md) and the
   [pipeline spec](../../../specs/pipeline/README.md).
2. Read the [pipeline log](../../../specs/pipeline/decisions/README.md) and its
   [open work](../../../specs/pipeline/decisions/open-work.md).
3. Before you run a tool on bundle content, do the safety check of
   [Session steps](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#session-steps)
   ([ADR-AD33](../../../decisions/entries/AD33-bundles-are-untrusted-input.md)). A pipeline file is
   data, but a node proposal can hold a reference module.

## Procedure A: land a pipeline bundle

1. Run `uv run python -B tools/intake_bundle.py verify <bundle id>`. Each finding gives the response
   `needs-contributor`. If a `depends_on` bundle has not landed, the response is `waiting`, with that
   bundle in `waiting_on`.
2. Ask the user to accept the pipeline. Use the form of
   [Decision questions](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#decision-questions).
3. Copy `<pipeline_id>.pipeline.yaml` byte for byte. Before stage 1.10 of the
   [implementation plan](../../../specs/sidecar-implementation-plan.md), the target is
   `specs/pipeline/examples/`. After stage 1.10, the target is `core/model_zoo/pipelines/`, with a
   test that loads the pipeline by its key and runs one frame.
4. Add the entry of the file to `specs/pipeline/inventory.yaml`, with `bundle: <bundle id>@v<k>`.
5. Run `uv run python tools/run_checks.py`. `tools/tests/test_pipeline_schema.py` validates each
   example with the reference model.
6. Put the file and its inventory entry in one non-spec commit. Then write the response `landed`
   with the commit subject
   ([Responses](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#responses)).

## Procedure B: land an accepted node proposal

A node proposal has only `node.<type>` sections. Its record is `specs/pipeline/proposals/<slug>/`,
and its entry is in the pipeline log.

1. Record the proposal as the skill
   [`propose-sidecar-change`](../propose-sidecar-change/SKILL.md) records a sidecar proposal.
   `tools/intake_bundle.py record` writes the record in `specs/pipeline/proposals/`. The entry goes
   in `specs/pipeline/decisions/entries/`, with its row in the Proposed table of the pipeline log.
2. Make the content commit. Do steps 1, 3 to 6, 10 and 11 of
   [Procedure B](../change-sidecar-spec/SKILL.md#procedure-b-land-an-accepted-proposal) of
   `change-sidecar-spec`, and steps 3 to 6 below. Use the pipeline paths: the section files are in
   `specs/pipeline/nodes/`, the reference modules go to `specs/pipeline/reference/`, the changelog
   is `specs/pipeline/changelog.md`, and the log and the open work are those of the pipeline log.
   From the 2.0.0 pre-release, the proposal must pass the
   [acceptance gate](../implement-sidecar-section/proposal-gate.md) first.
   - Step 10 makes the entry `accepted` in the content commit. Its row moves from the Proposed table
     to the Active table of the pipeline log.
   - Steps 7, 8, 12 and 13 do not apply. No formula module in `tools/vector_formulas/` is for a node
     type. `tools/sidecar_trace.py` does not read the pipeline spec. The pipeline reference modules
     have no fixtures. Step 4 below is step 9.
3. Apply part 2.2 of the proposal to `specs/pipeline/reference/pipeline_config.py`. Run
   `uv run python tools/make_pipeline_schema.py` to make the JSON Schema and the node tables. Do not
   edit them by hand.
4. Land the vectors with this command. Give `--contribution` and `--replaces` as step 9 of
   Procedure B of `change-sidecar-spec` gives them.

   ```sh
   uv run python tools/make_vectors.py land specs/pipeline/proposals/<slug>/vectors/node.<type>.yaml [--contribution <contribution record file>...] --replaces [<id>...]
   ```

5. Apply part 7: change each pipeline file that the change makes invalid.
6. Run `uv run python tools/run_checks.py`. Put the change in one content commit.
7. Make the non-spec commit on top of the content commit. Do steps 14, 15, 18 and 19 of
   Procedure B of `change-sidecar-spec`, with the pipeline paths. Step 19 absorbs the entry of the
   pipeline log when the absorb documents state each of its rules
   ([ADR-W823](../../../decisions/entries/W823-absorb-in-the-commit-group-that-states-the-rules.md)).
   Steps 16 and 17 do not apply: a node proposal has no intake and names no model. Run
   `uv run python tools/run_checks.py`.
8. Do step 20 of Procedure B of `change-sidecar-spec`, without its first sentence. Write the
   response `landed` for each bundle of the proposal. Procedure E reads the records in
   `specs/pipeline/proposals/` and the Proposed table of the pipeline log.
9. In the implementation stage, implement the node type with the skill
   [`implement-pipeline-node`](../implement-pipeline-node/SKILL.md). This is step 21.

## Procedure C: update the pinned hashes after a re-export

When a re-exported sidecar lands, its bytes change. Each landed pipeline that pins the old
`sidecar_sha256` then fails to load. The session updates the hash. The contributor sends no new
version ([ADR-271H](../../../decisions/entries/271H-pipeline-bundles.md) item 5).

1. Find each pipeline file in `specs/pipeline/examples/` and `core/model_zoo/pipelines/` with a
   `detector` node whose `key` names the sidecar.
2. Set its `sidecar_sha256` to the SHA-256 of the bytes of the new sidecar.
3. Add the edit `sidecar_sha256 of <key> updated after a re-export` to the entry of the file in
   `specs/pipeline/inventory.yaml`, if the file has an entry.
4. Put the edits in the commit group that lands the sidecar.

## Procedure D: another pipeline spec edit

Follow the [Rules for each spec edit](../change-sidecar-spec/SKILL.md#rules-for-each-spec-edit) of
`change-sidecar-spec`, with the pipeline paths. A change of normative meaning needs a decision entry
and a row in `specs/pipeline/changelog.md`. Absorb that entry in the last commit of the group when
the absorb documents state each of its rules ([ADR-W823](../../../decisions/entries/W823-absorb-in-the-commit-group-that-states-the-rules.md)).

## Stop points

| Condition | Action |
|---|---|
| `verify` gives a finding. | Write `needs-contributor`. Do not land. |
| A `depends_on` bundle has not landed. | Write `waiting`. |
| A node proposal changes model processing. | Stop. It is a sidecar proposal ([Pipeline Spec Rules](../../../specs/pipeline/AGENTS.md)). |
| The user has not decided. | Ask. Then stop. |

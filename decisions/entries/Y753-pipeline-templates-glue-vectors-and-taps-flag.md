# Y753 — Pipeline templates without links, vectors for `first_of` and `concat`, and the skellybench tap flag

**Status:** absorbed into [`AGENTS.md#5-decision-log`](../../AGENTS.md#5-decision-log), [`implement-pipeline-node/SKILL.md#stage`](../../.claude/skills/implement-pipeline-node/SKILL.md#stage), [`timing.md#implementer-guidance`](../../specs/pipeline/timing.md#implementer-guidance), [`first_of.md#implementer-guidance`](../../specs/pipeline/nodes/first_of.md#implementer-guidance), [`concat.md#implementer-guidance`](../../specs/pipeline/nodes/concat.md#implementer-guidance), [`README.md#section-status`](../../specs/pipeline/README.md#section-status), 2026-11-17 (absorb pass, user; PR: pending).

## Decision

1. **Templates.** The templates in `specs/pipeline/templates/` name a file by its path in a code
   span and a heading by its text. They have no relative link. They cite a skellytracker entry as
   `skellytracker ADR-<ID>`, as the templates in `specs/model-sidecar/templates/` do
   ([ADR-ESP4](ESP4-one-home-for-each-workflow-rule.md)). Section 5 of the root `AGENTS.md` names
   both folders.
2. **Node work.** Stage 1.10 of the
   [implementation plan](../../specs/sidecar-implementation-plan.md#110-the-pipeline-api-was-p)
   implements the node types. The skill `implement-pipeline-node` and stage 1.10 say this.
3. **Tap flag.** The skellybench command line has `--taps <dir>`. It gives the tap folder of the
   run. A run of a file with a tap needs it (`V-pipeline.taps-2`).
4. **Glue vectors.** `first_of` and `concat` get the vector files `specs/pipeline/vectors/node.first_of.yaml`
   and `specs/pipeline/vectors/node.concat.yaml`. Their named tests move into these files and go
   from `tools/tests/test_pipeline_glue_nodes.py`, so each case has one source
   ([ADR-8DSW](8DSW-vector-files-are-the-case-source.md)). The `concat` file has a case for item 1
   of [ADR-97X9](97X9-pipeline-instance-rows-prev-types-and-refused-calls.md). This changes the
   named-test rule of item 4 of [ADR-3SF2](3SF2-pipeline-spec-and-node-workflow.md). `merge` keeps
   its named tests until the change of `merge` lands.

## Reason

- Item 1: a copy of a template leaves this repository. `pack` refuses a link of a proposal that does
  not resolve from the record path ([ADR-730P](730P-anchor-check-of-bundle-links.md)). An unchanged
  copy of the node-proposal template had two such links. The pipeline templates already cited
  entries with no link.
- Item 3: the line in `specs/pipeline/timing.md` had `--coco` and `--images`, but no tap folder. A
  record tap or a replay tap is then not possible from skellybench.
- Item 4: a vector file is the one place that a host reads the cases of a section. The named tests
  were a second place for the same kind of case.

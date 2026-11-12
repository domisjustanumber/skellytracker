# 3SF2 — The pipeline spec in `specs/pipeline/`: a Pydantic reference model and its schema, glue vectors, a changelog, a module log, and a thin workflow for new node types

**Status:** absorbed into [`pipeline/README.md#overview`](../../specs/pipeline/README.md#overview), [`pipeline/README.md#status`](../../specs/pipeline/README.md#status), [`pipeline/README.md#conventions`](../../specs/pipeline/README.md#conventions), [`pipeline/README.md#section-map`](../../specs/pipeline/README.md#section-map), [`pipeline/README.md#section-status`](../../specs/pipeline/README.md#section-status), [`pipeline/README.md#generated-files`](../../specs/pipeline/README.md#generated-files), [`pipeline/AGENTS.md#pipeline-spec-rules`](../../specs/pipeline/AGENTS.md#pipeline-spec-rules), [`changelog.md#changelog`](../../specs/pipeline/changelog.md#changelog), [`changelog.md#revisions`](../../specs/pipeline/changelog.md#revisions), [`contributions.md#pipeline-contributions`](../../specs/pipeline/contributions.md#pipeline-contributions), [`contributions.md#change-a-node-type`](../../specs/pipeline/contributions.md#change-a-node-type), [`first_of.md#implementer-guidance`](../../specs/pipeline/nodes/first_of.md#implementer-guidance), [`concat.md#implementer-guidance`](../../specs/pipeline/nodes/concat.md#implementer-guidance), [`change-pipeline-spec/SKILL.md#procedure-d-another-pipeline-spec-edit`](../../.claude/skills/change-pipeline-spec/SKILL.md#procedure-d-another-pipeline-spec-edit), [`AGENTS.md#repository-instructions`](../../AGENTS.md#repository-instructions), [`make_vectors.py`](../../tools/make_vectors.py), [`intake_bundle.py`](../../tools/intake_bundle.py), [`check_decision_log.py`](../../tools/check_decision_log.py), 2026-11-12 (absorb sweep, user; PR: pending).

## Decision

1. **Where.** The pipeline spec is in `specs/pipeline/`, with `README.md` as its one entry point: a
   JSON Schema, `V-` rules, the examples of [ADR-8NVD](8NVD-pipeline-api-warnings-and-catalog.md),
   the node tables, and the reference implementations in `specs/pipeline/reference/`.
   `schema_version` uses SemVer and follows skellytracker
   ([ADR-6GE2](6GE2-spec-version-follows-skellytracker.md)).
2. **Sections.** The section IDs are `pipeline.<area>` (`pipeline.file`, `pipeline.graph`,
   `pipeline.outputs`, `pipeline.running`, `pipeline.timing`, `pipeline.taps`) and `node.<type>`,
   one section for each node type. Rule IDs are `V-<section-id>-<n>`. Each rule goes in the section
   of the thing that it constrains. Each section starts as `draft`. The CLI and the Python API are
   not spec sections. The built-in pipelines are examples in `specs/pipeline/examples/` until the
   implementation stage copies them to `core/model_zoo/pipelines/`.
3. **Schema source.** During the spec-build stage, the Pydantic reference model is in
   `specs/pipeline/reference/pipeline_config.py`. A tool in `tools/` makes the JSON Schema and the
   node tables from it, and the schema is committed in `specs/pipeline/` as the public, descriptive
   schema. In the implementation stage, the model moves into `core/pipelines/config.py`, and a doc
   test checks that the committed schema agrees.
4. **Glue vectors.** These glue nodes get vector files: `roi_from_points`, `roi_tracking`,
   `smooth_roi`, `smooth_keypoints`, `gate` and `redetect`. `first_of` and `concat` get named tests.
   `tools/make_vectors.py` routes each section ID that starts with `node.` to the `vectors/` and
   `reference/` folders of `specs/pipeline/`, with tests. Its generate and `--check` modes make and
   check these files. `fill` refuses a path in the checkout
   ([ADR-AD33](AD33-bundles-are-untrusted-input.md)), so it is only for an outside bundle. A case of
   `test_keypoint_bbox_detector.py` or `test_detection_stage_hierarchy.py` seeds a `roi_from_points`
   case only when its meaning is the same
   ([ADR-7NY2](7NY2-pipeline-form-graph-and-nodes.md) item 13).
5. **Changelog.** `specs/pipeline/changelog.md` starts with the first content commit. Each content
   change adds a summary row and a `Row` line with the normative fingerprint of the pipeline
   sections, which its own test checks.
6. **Module.** `specs/pipeline/` is a module. It has its own `AGENTS.md` and its own log
   `specs/pipeline/decisions/`, and the folder is in `LOG_DIRS` of `tools/check_decision_log.py`. The
   user approved the new module log. An entry whose files are all in `specs/pipeline/` goes in that
   log. An entry with files in another module goes in the root log.
7. **Node workflow.** New node types have their own thin workflow, not a kind of the model addition
   workflow. It is one workflow file and one node-proposal template in `specs/pipeline/`, which link
   to the headings of `hand-over.md`, and one landing skill `change-pipeline-spec`.
   `tools/intake_bundle.py` maps the prefix `node.` to `specs/pipeline/`. A node change that comes
   with a sidecar change is two linked proposals (`depends_on`). The workflow comes after the draft
   spec lands. Until then, a node request goes in the intake row "Notes and questions to the
   skellytracker session".

## Reason

- The spec-build stage does not change code under `skellytracker/`. A reference model in the spec
  folder is allowed, as `specs/model-sidecar/reference/` is. One model makes the schema, the node
  tables and the catalog, so they cannot drift.
- The tools find the spec folder from the prefix of a section ID. A `format.*` ID would point to the
  sidecar spec, and `V-format.graph-1` reads as a sidecar rule. The module name of a reference file
  comes from its stem, so a generic name such as `config` can collide.
- The glue nodes are pure functions, and a reference implementation with no vectors checks nothing.
- A changelog from the start keeps one record of each change, as the sidecar spec does.
- Most triggers for a new node are sidecar proposals, because the pipeline spec never defines model
  processing. A node has no ONNX, batch, size or exporter step, so most of the model addition
  workflow does not apply to it. The bundles, the safety check, the vectors, the records and the
  states carry over.

## Alternatives rejected

- **A hand-written JSON Schema as the source.** Two models to keep in step.
- **The `fill` flow for the in-repo vectors.** It refuses a path in the checkout, for safety.
- **A "node" kind in the model addition workflow.** It adds "skip this for a node" lines to about ten
  workflow files and two skills.
- **Maintainers only.** It throws away the vector flow for outside authors.
- **Entries of the pipeline spec in the root log only.** The changes of one spec are then mixed with
  all other entries.

## Open work

See [open-work.md](../open-work.md).

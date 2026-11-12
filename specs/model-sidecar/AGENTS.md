# Sidecar Rules

These rules apply to work in skellytracker on the sidecar spec, a sidecar or a reference example.
Exporter agents use the [exporter guide](../draft/exporter-guide/README.md) instead.
The root [`AGENTS.md`](../../AGENTS.md) also applies.
The decision log of the sidecar spec is in [`decisions/`](decisions/README.md). Read it with the
root log ([ADR-GN3D](../../decisions/entries/GN3D-module-decision-logs.md)).

- The section files under this folder are normative. Read the sections that apply before you change
  a sidecar, an example or the spec. The [section map](README.md#section-map) lists them.
- Link to the spec by its relative path. Do not link to a branch URL.
- Each spec change and each proposal targets [the open target](changelog.md#revisions)
  ([ADR-6GE2](../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- Publish a sidecar only when the publish ban allows it
  ([Publishing](model-addition-workflow/validation-and-publishing.md#publishing)).
- A spec change has no class. It applies to each sidecar from the commit that lands it
  ([ADR-C0YD](../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md) item 1). Each
  sidecar has one reading: the current spec text. The spec has no legacy reading
  ([ADR-0QKK](../../decisions/entries/0QKK-no-legacy-layer.md)). The old package sidecars stay
  outside the spec until they are deleted. They do not migrate: exporter models replace them
  ([ADR-AMJ8](../../decisions/entries/AMJ8-replace-package-onnx-detectors.md)).
- Make a spec change in the section file that owns the rule. The `id` in the front matter is the
  section ID. The rule IDs of the section are `V-<id>-<n>`. When you move or reword a section, keep
  its section ID and its rule IDs
  ([Rule IDs and section IDs](../../.claude/skills/change-sidecar-spec/spec-edit-rules.md#rule-ids-and-section-ids);
  [ADR-8DSW](../../decisions/entries/8DSW-vector-files-are-the-case-source.md)).
- The sidecar spec and the pipeline spec must use one name for each concept. Do not add an alias
  for an old name ([ADR-88WQ](../../decisions/entries/88WQ-sidecar-vocabulary.md)).
- A spec change needs a decision entry and a changelog row. Add a row to the
  [summary of changes](changelog.md#summary-of-changes). A content commit also appends one
  ``- Row N: `<fingerprint>`.`` line under the open target in [Revisions](changelog.md#revisions).
- Stop on a gap. If a model property does not map exactly to a spec section, do not approximate it.
  A near-miss is a gap. Then follow
  [`propose-sidecar-change`](../../.claude/skills/propose-sidecar-change/SKILL.md).
- Put one kind of change in each PR. In the spec-build stage, put one kind of change in each
  commit ([section 6](../../AGENTS.md#6-git-rules) of `AGENTS.md`).
  The kinds are: content (a change of normative meaning), move, rewording, and non-spec (decision
  log, agent files, tools, test vectors, guidance, CI, test fixes).
  - A non-spec PR can also add an example that changes no normative meaning, with its provenance
    record. It can also add an exporter's reference implementation of the current spec text.
  - A content PR also has the examples, vectors and reference implementations that define its new
    meaning.
  - Put new content in a new PR on top of the PR stack. Never put it in a move PR or a rewording PR.
  - A move PR can add labels: section IDs, rule IDs and the front matter fields `id`, `title` and
    `kind`.
- The [reference examples](examples/README.md) are part of the spec. To add or replace one, follow
  [Reference examples](model-addition-workflow/reference-examples.md).
- A sidecar goes in the path that the [storage layout](format/file-layout.md#storage-layout) gives.
- Do not change an exporter repository. You may read one.

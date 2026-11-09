# Sidecar Rules

These rules apply to work in skellytracker on the sidecar spec, a sidecar or a reference example.
Exporter agents use the [exporter guide](../draft/exporter-guide/README.md) instead.
The root [`AGENTS.md`](../../AGENTS.md) also applies.
The decision log of the sidecar spec is in [`decisions/`](decisions/README.md). Read it with the
root log ([ADR-GN3D](../../decisions/entries/GN3D-module-decision-logs.md)).

- The section files under this folder are normative. Read the sections that apply before you change
  a sidecar, an example or the spec. The [section map](README.md#section-map) lists them.
- Link to the spec by its relative path. Do not link to a branch URL.
- Each spec change and each proposal targets the open target: the next skellytracker release. Until
  the user bumps skellytracker, the open target is `2.0.0`
  ([Revisions](changelog.md#revisions); [ADR-6GE2](../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- Do not publish a sidecar to a shared or remote sidecar root until a final skellytracker release
  loads its `schema_version`. This ban applies to each target. A pre-release does not end it. The
  private test repo of the implementation stage is the one exception. Put a sidecar with a
  pre-release `schema_version` only in the private test repo. The exporter exports it again after
  the final release ([Authoring guidance](format/versioning.md#authoring-guidance);
  [Publishing](model-addition-workflow/validation-and-publishing.md#publishing)).
- A spec change has no class. It applies to each sidecar from the commit that lands it
  ([ADR-C0YD](../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md) item 1). Each
  sidecar has one reading: the current spec text. The spec has no legacy reading. The package
  sidecars stay outside the spec until they migrate
  ([ADR-0QKK](../../decisions/entries/0QKK-no-legacy-layer.md)).
- Make a spec change in the section file that owns the rule. The `id` in the front matter is the
  section ID. The rule IDs of the section are `V-<id>-<n>`. When you move or reword a section, keep
  its section ID and its rule IDs
  ([Rule IDs and section IDs](../../.claude/skills/change-sidecar-spec/SKILL.md#rule-ids-and-section-ids);
  [ADR-8DSW](../../decisions/entries/8DSW-vector-files-are-the-case-source.md)).
- A spec change needs a decision entry and a changelog row. Add a row to the
  [summary of changes](changelog.md#summary-of-changes). A content commit also appends one
  ``- Row N: `<fingerprint>`.`` line under the open target in [Revisions](changelog.md#revisions).
- Stop on a gap. If a model property does not map exactly to a spec section, do not approximate it.
  A near-miss is a gap. A gap that a skellytracker session finds goes on the
  [spec-defect list](decisions/open-work.md#spec-defects). Then stop. A contributor writes the
  change proposal with the parts of [`templates/change-proposal.md`](templates/change-proposal.md)
  and packs it as a `proposal` bundle ([Hand-over bundles](model-addition-workflow/hand-over.md);
  [ADR-ZXD7](../../decisions/entries/ZXD7-bundle-process.md)). A skellytracker session copies
  the bundle version to `proposals/<slug>/` and records it as a short decision entry with status
  `proposed`. Then stop. The user accepts or rejects the proposal.
- Put one kind of change in each PR
  (ADR-[0027](../../decisions/entries/0027-single-working-branch.md#one-kind-of-change-in-each-pr)).
  In the spec-build stage, the exception of
  [ADR-AB79](../../decisions/entries/AB79-one-pr-for-the-spec-build-work.md) applies: one PR, one kind of
  change in each commit. It ends when the user opens the one PR.
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

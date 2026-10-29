# Sidecar Rules

These rules apply to work in skellytracker on the sidecar spec, a sidecar or a reference example.
Exporter agents use the [exporter guide](../draft/exporter-guide/README.md) instead.
The root [`AGENTS.md`](../../AGENTS.md) also applies.
The decision log of the sidecar spec is in [`decisions/`](decisions/README.md). Read it with the
root log ([ADR-GN3D](../../decisions/entries/GN3D-module-decision-logs.md)).

- The section files under this folder are normative. Read the sections that apply before you change
  a sidecar, an example or the spec. The [section map](README.md#section-map) lists them.
- Link to the spec by its relative path. Do not link to a branch URL.
- Every spec change goes into the `vNEXT` revision until the first skellytracker release that ships
  the spec ([Publishing](model-addition-workflow/validation-and-publishing.md#publishing)).
- `load_sidecar` rejects `schema_version: "vNEXT"` (`SidecarModel._check_schema_version_pattern` in
  `skellytracker/core/sidecar/model.py`). Do not publish a `vNEXT` sidecar to a shared or remote
  folder.
- The meaning of an older `schema_version` never changes. A clarification is not a change of
  meaning. A change in [Every-version changes](format/versioning.md#every-version-changes) is the
  only exception. [Version-aware compatibility](format/versioning.md#version-aware-compatibility)
  defines a clarification. It indexes each "Legacy behaviour" heading that gives a legacy
  difference. The availability of a new feature is in the "Legacy behaviour" table of Schema
  versioning. Each change has a class
  ([Change classes](model-addition-workflow/hand-over.md#change-classes);
  [ADR-KDBD](../../decisions/entries/KDBD-change-classes-and-spec-forced-edits.md)).
- Make a spec change in the section file that owns the rule. The `id` in the front matter is the
  section ID. The rule IDs of the section are `V-<id>-<n>`. When you move or reword a section, keep
  its section ID and its rule IDs
  ([Rule IDs and section IDs](../../.claude/skills/change-sidecar-spec/SKILL.md#rule-ids-and-section-ids);
  [ADR-TA0G](../../decisions/entries/TA0G-vector-cases-and-reference-modules.md)).
- A spec change needs a decision entry and a changelog row. Add a row to the
  [summary of changes](changelog.md#summary-of-changes). Add the change to the `vNEXT` row of the
  [changelog](changelog.md#schema_version-history).
- Stop on a gap. If a model property does not map exactly to a spec section, do not approximate it.
  A near-miss is a gap. A gap that a skellytracker session finds goes on the
  [spec-defect list](decisions/open-work.md#spec-defects). Then stop. A contributor writes the
  change proposal with the parts of [`templates/change-proposal.md`](templates/change-proposal.md)
  and packs it as a `proposal` bundle ([Hand-over bundles](model-addition-workflow/hand-over.md);
  [ADR-FADS](../../decisions/entries/FADS-hand-over-bundles-in-intakes.md)). A skellytracker session copies
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

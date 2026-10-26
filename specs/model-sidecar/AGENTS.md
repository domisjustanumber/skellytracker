# Sidecar Rules

These rules apply to work in skellytracker on the sidecar spec, a sidecar or a reference example.
Exporter agents use the [exporter guide](../draft/exporter-guide/README.md) instead.
The root [`AGENTS.md`](../../AGENTS.md) also applies.

- The section files under this folder are normative. Read the sections that apply before you change
  a sidecar, an example or the spec. The [section map](README.md#section-map) lists them.
- Link to the spec by its relative path. Do not link to a branch URL.
- Every spec change goes into the `vNEXT` revision until the first skellytracker release that ships
  the spec (ADR-[0014](../../notes/decisions/0014-spec-lifecycle.md)).
- `load_sidecar` rejects `schema_version: "vNEXT"` (`SidecarModel._check_schema_version_pattern` in
  `skellytracker/core/sidecar/model.py`). Do not publish a `vNEXT` sidecar to a shared or remote
  folder.
- The meaning of an older `schema_version` never changes. Its legacy rules are in the "Legacy
  behaviour" heading of each section.
  [Version-aware compatibility](format/versioning.md#version-aware-compatibility) indexes these
  headings.
- Make a spec change in the section file that owns the rule. The `id` in the front matter is the
  section ID. The rule IDs of the section are `V-<id>-<n>`. When you move or reword a section, keep
  its section ID and its rule IDs
  (ADR-[0013](../../notes/decisions/0013-spec-structure.md#one-owner-for-each-rule)).
- A spec change needs a decision entry and a changelog row. Add a row to the
  [summary of changes](changelog.md#summary-of-changes). Add the change to the `vNEXT` row of the
  [changelog](changelog.md#schema_version-history).
- Stop on a gap. If a model property does not map exactly to a spec section, do not approximate it.
  A near-miss is a gap. Write a change proposal with the parts of
  [`templates/change-proposal.md`](templates/change-proposal.md). Copy it to
  `proposals/<slug>/proposal.md`. Record it as a short decision entry with status `proposed`
  (ADR-[faac](../../notes/decisions/faac-proposal-records.md)). Then stop. The user accepts or
  rejects the proposal.
- Put one kind of change in each PR
  (ADR-[0027](../../notes/decisions/0027-single-working-branch.md#one-kind-of-change-in-each-pr)).
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

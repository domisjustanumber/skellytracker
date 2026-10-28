# KDBD — Change classes and spec-forced example edits

**Status:** accepted, 2026-10-28 (user; PR: pending).

## Decision

This entry supersedes [0009](../specs/model-sidecar/decisions/0009-imagenet-bgr-meaning.md) in
full. Items 1 to 6 are new. Item 7 restates the kept rules of 0009 by links
([ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md)).

1. **Change classes.** Each spec change has one class. The manifest key `change_class` and part 2
   of the proposal name it. The decision entry repeats it.
   `vnext` (the default) applies only at `vNEXT`. `clarification` applies at every
   `schema_version` and meets the four conditions of
   [Clarifications](../specs/model-sidecar/format/versioning.md#clarifications). `breaking` applies
   at every `schema_version` and can make an older sidecar invalid.
2. **Clarification.** It has no **(vNEXT)** mark and no "Legacy behaviour" row. Its summary row
   says "(every `schema_version`)". Part 2.6 gives the result in exact math before and after the
   change, and names each host that stops conforming. Part 7 tells for each sidecar if it stays
   valid, with the commit that the contributor checked. In the spec-build stage, a package host
   that stops conforming is a recorded gap: the comment of its `implemented_by` line and
   "Implementer guidance". The rule has no time limit.
3. **Breaking.** It needs its own entry with the explicit acceptance of the user, an item in
   [Every-version changes](../specs/model-sidecar/format/versioning.md#every-version-changes), a
   summary row that says "(breaking, every `schema_version`)", and an audit of
   `skellytracker/core/detectors/**/*.yaml`. A change of a package sidecar waits for the
   implementation stage, unless the entry gives a waiver of the user. The removal of `int8`
   ([ADR-CNSN](CNSN-spec-build-actions-after-the-fact.md)) is the first item of the list. Its
   exception sentence and its changelog bullet move into the list.
4. **Legacy index.**
   [Version-aware compatibility](../specs/model-sidecar/format/versioning.md#version-aware-compatibility)
   indexes only a "Legacy behaviour" heading that gives a legacy difference. A new field, value or
   section that is not available before `vNEXT` goes in the availability row of Schema versioning.
   Thus `batching.batch_conversion` leaves the index, and it and `top_k` join that row.
5. **Spec-forced edits.** The reference examples obey the spec at each commit. A content change that
   makes an example invalid edits the example in the same content commit. This spec-forced edit is
   not a correction. The rule "Do not correct an example by hand" stays.
   - Allowed: remove a field or a value, rename, change `model_id` and the file names, move, and
     change a comment. After a fragment edit, write the `$ref` and `base` hashes again. Add no other
     value.
   - An edit that needs a value that only an export can give (`needs-export`) waits for the
     re-export bundle. The session adds a re-export request. An edit of a fragment that equals a
     package copy is also `needs-export`.
   - Keep the ONNX placeholder hash, `kind`, `exporter`, `exporter_path`, `tracked` and `commit`.
   - `edits` gets `"spec change <ID>: <edit>"`, with a bare ID. Older items stay.
   - A doc test of the old rule changes in the same commit.
   - The content commit holds all forced edits. Its message names each example and rule ID.
   - A re-copy replaces an example only when the copy obeys each rule.
6. **Affected examples.** Part 7 of each proposal has a table: the example, the rule ID, the impact
   (`forced-edit` or `needs-export`) and the edit text, or `none` with the reason. At landing, the
   session runs `tools/sidecar_trace.py impact`. An invalid example that part 7 does not list is a
   finding with the state `needs-contributor`.
7. **Where the rules are.** Items 1 to 3: the headings above, and "Change classes" in
   [`hand-over.md`](../specs/model-sidecar/model-addition-workflow/hand-over.md). Items 5 and 6:
   "When a spec change makes an example invalid" in
   [`reference-examples.md`](../specs/model-sidecar/model-addition-workflow/reference-examples.md),
   and part 7 of the [change proposal template](../specs/model-sidecar/templates/change-proposal.md).
   The 0009 rules that stay (the `imagenet_bgr` meaning at each version, `imagenet_rgb`, and the
   `custom` form of the legacy computation) are in
   [Normalization modes](../specs/model-sidecar/pre/normalization.md#behaviour) and
   [Legacy behaviour](../specs/model-sidecar/pre/normalization.md#legacy-behaviour). The 0009
   sentence "The spec never applies `vNEXT` requirements to a legacy sidecar" changes: a
   clarification and an every-version change apply to a legacy sidecar. The legacy `imagenet_bgr`
   tuple is a result in exact math, so no clarification can change it.

## Reason

- Proposals defined the arithmetic, the rounding or the tie order of an older text. Each asked the
  user "clarification or change?". The spec had no test that gave the answer.
- Two proposals added their own exception sentence after the `int8` sentence.
- The removal of `int8` made legacy sidecars invalid with no class and no entry.
- The skill said "list the invalid example in the PR body", but the examples belong to the spec.
- The legacy index held one availability-only link and left out others.

## Consequences

- A third-party host sees a stricter conformance in the "(every `schema_version`)" rows.

## Alternatives rejected

- **Keep the absolute rule.** A precision fix then needs a **(vNEXT)** mark and a second legacy
  text for one formula.
- **A "The same" legacy row and an equal legacy vector for each clarification.** The row is a second
  source. One generator writes both vectors, so the second vector proves nothing.
- **Known-invalid examples with a note.** The spec then contradicts its examples.
- **Remove an invalid example.** It breaks links and the traceability matrix.

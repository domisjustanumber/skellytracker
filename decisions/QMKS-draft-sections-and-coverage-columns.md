# QMKS — Draft sections and the coverage columns

**Status:** accepted, 2026-10-28 (user; PR: pending).

## Decision

1. **Draft status.** "Draft" is the value `draft` of the section field `status.spec`. It is not the
   folder `specs/draft/` and not the revision `vNEXT`. The [spec README](../specs/model-sidecar/README.md)
   states the section status rules:
   - A `draft` section is normative for `vNEXT`. Writers can write its fields.
   - Each content commit can change a `draft` section. Its change class is always `vnext`.
   - The first body line of a `draft` section is the banner "This section is a draft...".
   - A new section enters as `draft`. A changed `stable` section stays `stable`. The front matter is
     the authority.
   - The section becomes `stable` when an accepted entry exists for it, a `kind: export` example uses
     it (or the user records "no model" with a reason), its vector cases are verified (or a named test
     checks it when vectors cannot hold its input), and each `V-` rule has a case.
   - The graduation is a content commit. It changes `status.spec`, removes the banner and adds a
     changelog row.
   - The release step stops when a section is `draft`. The user graduates the section or removes its
     fields from the release.
2. **Commit kinds.** The README definition and each graduation are content commits. The tool, the
   tests and the skill table are non-spec.
3. **The batch-conversion stop.** The release step also stops when an example or a package sidecar
   has `batching.batch_conversion` and the `validate` or `load` status of `common.batch_conversion` is
   not `implemented`. This stop does not use the graduation gate. The `change-sidecar-spec` skill
   (Procedure D) gives both stops.
4. **Coverage columns.** `tools/sidecar_trace.py matrix` adds columns to the Implementation status
   table of [`TRACEABILITY.md`](../specs/model-sidecar/TRACEABILITY.md). It adds no second table.
   The Vectors cell counts the cases and the verified cases. New columns: examples by `kind`, `V-`
   rules with a case (n of m), the reference module, the "no model" reason and the gate. The Gate
   column is the coverage backlog. It shows the conditions of item 1 that the files show. The
   "Backlog" section stays the `implemented_by` backlog. Exporters read the Gate column. They do not
   claim items.
5. **"No model" reasons.** The user records a reason in `no_model` of
   [`inventory.yaml`](../specs/model-sidecar/inventory.yaml), keyed by section ID.
6. **Tests.** `tools/tests/test_traceability.py` checks that a section has the banner if and only if
   it is `draft`. No test fails a `draft` section for an open gate item. The release stop is the only
   place that acts on a `draft` section.
7. **Selector.** A `common` section that is one optional key has one key-presence selector, for
   example `batching.batch_conversion`. It applies only to a sidecar that has the key. A `format` or
   `common` section with `selectors: []` applies to every sidecar.
8. **Backfill.** skellytracker adds the numeric vectors from the text as `unverified`, and the
   validator cases of all `V-` rules, in non-spec commits. The exporters verify the vectors, give the
   reference modules and give the examples through bundles. The existing `stable` sections stay
   `stable`. Their open gate items are the coverage backlog.

## Reason

- One section used `spec: draft`, but no file defined it. No rule told how a section enters or
  leaves `draft`, and nothing linked it to the release.
- `TRACEABILITY.md` marked `common.batch_conversion` for every model, because the section had
  `selectors: []`. Its real example coverage is 0.
- No file showed which sections have verified vectors, validator cases or an export example.
- A `converts` family that publishes only batch 3 needs host conversion for batches 1 and 2. No host
  implements it, and the package rejects the key `batch_conversion`. A release must not ship such a
  sidecar as if a host can load it.

## Consequences

- A new section waits in `draft` until the exporters give an export example and verified vectors.
- The Gate column shows open items for most `stable` sections. It does not demote them.

## Evidence

- `tools/sidecar_trace.py matrix`, 2026-10-28: 29 sections, 9 vector files with 129 cases, 19
  verified cases, 0 of 83 `V-` rules with a case, no reference module, 3 `kind: export` examples.

## Alternatives rejected

- **Demote the `stable` sections with open gate items.** Their meaning is accepted. Coverage is a
  backlog, not a change of status.
- **A second coverage table or a second writer.** The Implementation status table already lists each
  section, and `matrix` already keeps it current.
- **A test that fails a `draft` section with gate `pass`.** At 0 of 83 rules it guards nothing.
- **A front-matter key for the "no model" reason.** It changes every section file for a value that
  few sections need.

# TA0G — Vector cases and reference modules

**Status:** accepted, 2026-10-28 (user; PR: pending).

## Decision

This entry supersedes [ADR-A33Q](a33q-vector-case-form.md) and [ADR-0013](0013-spec-structure.md) in
full. Items 1 to 6 are new or changed. Item 7 restates the rules that stay by links, as
[ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md) allows.

1. **Refused inputs.** A reference function refuses an input only with `ValueError`. The case
   writes `expect: {error: <value>}` and no other `expect` key. The value is the rule ID at the
   start of the message. It is `no-rule` when the input is not a sidecar value (a tensor, a caller
   argument or a second sidecar), or when a sidecar before `vNEXT` uses a feature that is "Not
   available.". The input must break exactly one rule. The note of a `no-rule` case tells why no
   rule applies. A sidecar value that no rule refuses is a spec gap: add a rule in part 2.4. Do not
   use `no-rule` for it.
2. **Validation results.** A validator that reports each failed rule returns
   `{failed: [<rule IDs>]}`: sorted, unique, `[]` for a valid sidecar, and no other `expect` key.
   A validator case can be data only, with no `function`. A run-time function never gets a sidecar
   value that a rule refuses: write a validator case for that rule. Each rule ID in `error` or
   `failed` must be in a section file at landing.
3. **The generator.** A builder calls a reference function through
   `make_vectors.outcome(function, *args, **kwargs)`. It changes a `ValueError` into the expect of
   item 1. Any other exception stops the generator. A host run of an exporter compares only the
   numeric cases.
4. **Size.** A vector file must be 256 KiB or smaller, with the cases of each proposal for its
   section. `intake_bundle.py verify` and a doc test also check the vector files of bundles and
   records.
5. **Landing check.** The new vector file holds the current cases, the cases of part 4 and the
   cases of each contribution. A part 4 case with the `id` of a current case replaces it. A
   contribution case must equal the case with its `id`. If not, the landing stops.
6. **Reference modules.** A module imports the module of another section by its name and calls
   through it. It does not copy it. With no such module, it holds a marked fixture, which a later
   landing replaces. A proposal that changes two sections gives one module for each. Case code
   stays outside `reference/`. `load_reference` puts the folder on `sys.path` while the module runs.
   The full-section rule applies only to a changed algorithm, value meaning or validation rule.
7. **Where the rules are.**
   - Items 1 to 3, and a33q items 2 to 4 and 6 to 8:
     [4. Vectors](../../specs/model-sidecar/templates/change-proposal.md#4-vectors) of the change
     proposal template and
     [Examples and vectors](../../.claude/skills/change-sidecar-spec/SKILL.md#examples-and-vectors).
   - Items 4 and 5, and a33q item 1: the same headings and step 9 of
     [Procedure B](../../.claude/skills/change-sidecar-spec/SKILL.md#procedure-b-land-an-accepted-proposal).
     Items 4 and 5 replace a33q items 10 and 11.
   - Item 6, and a33q item 9:
     [Reference implementations](../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#reference-implementations),
     with its headings from "Full section" to "Run a module that imports another module", and steps
     6 and 13 of Procedure B and steps 2 and 11 of
     [Procedure C](../../.claude/skills/change-sidecar-spec/SKILL.md#procedure-c-land-a-reference-implementation-of-an-exporter).
   - 0013, each rule:
     [Rules for each spec edit](../../.claude/skills/change-sidecar-spec/SKILL.md#rules-for-each-spec-edit).
     Item 6 changes its import rule. Items 1 to 5 change its vector rules.
   - Item 1 replaces a33q item 5 and adds the refusal to a33q item 3. A run-time check with no
     rule ID stays `no-rule` ([open work](../open-work.md#implementation-stage)).

## Reason

- A run-time function also refuses tensors and caller arguments. No validation rule can check them,
  so the a33q form had no value for these cases.
- A validator that reports each failure had no form. `make_vectors.py` had no way to record a
  refusal.
- One proposal gave a file of about 130 KiB. Two proposals for one section gave a file over
  64 KiB. The cases are small. The number of cases and a repeated value make the file large.
- A contribution and a follow-up add cases to a section. A file equal to part 4 then cannot hold the
  current cases.
- A copy of the algorithm of another section drifts. `load_reference` could not run a module that
  imports another module. Seven files restated the import rule.
- No reference module exists yet, so the full-section rule applied to each edit of a section.

## Consequences

- A recorded proposal in the old form must give a new bundle version in this form before
  acceptance.
- A builder defect that raises `ValueError` gives an `error` case. The hand-computed anchors of
  `test_vectors.py` still check the values.

## Evidence

- `tools/tests/test_vectors.py`: `check_case`, the `outcome` test, the import test and the renderer
  test.
- `tools/tests/test_proposal_records.py`: the size test of the record vector files.

## Alternatives rejected

- **A rule for each refusal.** A rule cannot check a tensor or a caller argument.
- **Expect the error message.** A message differs between implementations.
- **More than one vector file for each section.** It changes the tools in many places, and one
  function alone gives a large file.
- **Load another module by its path beside the file.** It fails in bundles and records.
- **No fixtures.** Partial owner modules must then land first, each with parity results.
- **New run-time check IDs now.** The open work holds them for the implementation stage.

_Edited 2026-10-29 (this PR): link repair._

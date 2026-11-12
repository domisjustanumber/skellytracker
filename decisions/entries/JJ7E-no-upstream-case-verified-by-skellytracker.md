# JJ7E — A vector case with no upstream output is verified when skellytracker agrees and its note names the spec rule

**Status:** absorbed into [`sidecar-files.md#independence`](../../specs/model-sidecar/model-addition-workflow/sidecar-files.md#independence), [`proposal-gate.md#steps`](../../.claude/skills/implement-sidecar-section/proposal-gate.md#steps), 2026-11-12 (absorb sweep, user; PR: pending).

## Decision

This entry adds a rule to item 5 of [ADR-6J8E](6J8E-exporters-run-released-skellytracker.md). It
does not change the other items of 6J8E.

1. **The cases.** A vector case with no upstream reference output: a refusal case, for example
   `expect: {error: no-rule}`, and a data-only validation case.
2. **Verified.** Such a case is verified when the skellytracker code agrees with it and the `note`
   of the case names the spec rule that it tests: a rule ID `V-<id>-<n>` or a Behaviour item of the
   section. The spec text is the source of the case.
3. **When.** Items 1 and 2 apply from the 2.0.0 pre-release, with items 1 to 6 of 6J8E. Until then,
   the current [Independence](../../specs/model-sidecar/model-addition-workflow/sidecar-files.md#independence)
   rules stay: a vector made only from a reading of the spec text is not verified.

## Reason

- The user selected "verified when skellytracker agrees" for a case with no upstream output.
- A refusal has no upstream behaviour to compare with. The spec text is its only authority.
- After the pre-release, the exporters retire their host code for the spec sections (6J8E item 1).
  A second implementation of a refusal case thus does not come, and the case would stay unverified
  for all time.

## Alternatives rejected

- **The case also needs an exporter.** The exporters must then keep validation host code, which
  6J8E item 1 retires.
- **The case stays unverified until a second implementation exists.** In practice it stays
  unverified for all time.

## Open work

See [open-work.md](../open-work.md).

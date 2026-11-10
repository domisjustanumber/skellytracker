# 6G6G — The CI read comes before the push

**Status:** absorbed into [`stack-commit/SKILL.md#spec-build-stage`](../../.claude/skills/stack-commit/SKILL.md#spec-build-stage), [`model-addition-workflow/hand-over.md#decision-questions`](../../specs/model-sidecar/model-addition-workflow/hand-over.md#decision-questions), 2026-11-10 (user; PR: pending).

## Decision

1. **Before each push.** The session reads the last fork CI runs of the working branch before each
   push, not before the push request. The user can approve the end-of-round push early, in the
   decision message of a proposal.
2. **A red or empty read stops the push.** A red run or an empty list stops the push, also after an
   early approval. The session reports it. After the fix, it asks for the push again.
3. **Changed rule.** Items 1 and 2 replace the first sentence of
   [ADR-R39S](R39S-test-fix-on-the-working-branch.md) item 9 ("Before a push request"). The rest of
   R39S stays, also the read of each push before the next push.

[Spec-build stage](../../.claude/skills/stack-commit/SKILL.md#spec-build-stage) states items 1 and
2 with the command.
[Decision questions](../../specs/model-sidecar/model-addition-workflow/hand-over.md#decision-questions)
links it.

## Reason

R39S item 9 put the read before the push request. [ADR-3HZ4](3HZ4-decision-questions-and-rule-defaults.md)
item 2 (now in [ADR-BQZ9](BQZ9-intake-process-consolidation.md)) lets the user approve the push in
the decision message, before the commits exist. A session that followed 3HZ4 broke R39S. A review
of the skills on 2026-11-10 found the conflict. On the same day, the user chose the timing of 3HZ4.

- The read shows the runs of the last push, not of the new commits. No push happens between the
  decision message and the push, so an earlier read gives the same result.
- A read before each decision message costs a call in each round, also when the user approves no
  push.

## Alternatives rejected

- **Keep R39S item 9.** The session then reads the CI before each decision message that asks for a
  push. The user sees the same red runs, but at a less useful moment.

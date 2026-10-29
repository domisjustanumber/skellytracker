# AB79 — One PR for the spec-build work

**Status:** accepted, 2026-10-28 (user; PR: pending).

## Decision

This entry is an exception to [ADR-0027](0027-single-working-branch.md) for the spec-build work. It
supersedes nothing. The rules of 0027 stay in [`AGENTS.md`](../../AGENTS.md#6-git-rules). They apply
again when this exception ends.

1. **One PR.** The spec-build work goes to `development` in one PR from
   `dom/sidecar-implementation`. The PR holds every commit on the branch. This includes the root
   files: `decisions/`, `tools/`, `.claude/skills/`, `AGENTS.md`, `.gitignore` and
   `.gitattributes`. The topic of the PR is the model sidecar. The user opens the PR and writes its
   body.
2. **No new branch.** The work uses no new `dom/NN-*` branch.
3. **One kind of change in each commit.** Each commit has one kind of change: content, move,
   rewording or non-spec. A commit group is a run of commits in a row on the working branch that do
   one task. The tree must be valid after the last commit of a group.
4. **The reading.** In the rules of the sidecar process, "the same PR" means the same commit group.
   A content, non-spec, move or rewording PR means a commit of that kind. This reading applies to
   the rules of 0027, [`specs/model-sidecar/AGENTS.md`](../../specs/model-sidecar/AGENTS.md) and the
   skills `change-sidecar-spec` and `stack-commit`.
5. **The test-fix rule does not change.** The rule of [ADR-0014](0014-spec-lifecycle.md) in
   [`AGENTS.md`](../../AGENTS.md#3-install-and-test) stays: a fix of one root cause of a test failure
   goes in its own PR against `development`, outside the spec-build PR.
6. **No rebase below the base.** New commits go only on top of the commit "Remove the precision
   int8 from the sidecar model" (PR: pending). No rebase starts below it. Thus #81 and the
   `dom/NN-*` branches stay valid and frozen, and the commit SHAs of #81 that
   `specs/sidecar-implementation-plan.md` cites stay valid.
7. **PR references.** "this PR" in an `_Edited_` line and "PR: pending" in a status line name the one
   PR. They stay as written after the PR opens.
8. **End.** This exception ends when the user opens the PR. Then this entry is `done`.

The [`stack-commit`](../../.claude/skills/stack-commit/SKILL.md#spec-build-stage) skill gives the
steps for this stage.

## Reason

- The user decided on 2026-10-28 to send the spec-build work as one PR.
- The stack has more than 50 branches. A rebase of a lower branch moves all of them, and a wrong SHA
  copies commits into the wrong PR. Commits on top of one base need no rebase.
- A commit of one kind keeps the review of each change simple, as a PR of one kind did.
- The test-fix rule keeps a fix of the package tests out of a large PR, so it can merge fast.

## Consequences

- Until #81 merges, the diff of the one PR also holds the commits and the package code of #81 and
  of the branches `dom/01-*` to `dom/51-*`, which have no PR. The user decides what happens to #81
  and to these branches.
- The "Add a commit" steps, the `dom/NN` push form and the PR steps of `stack-commit` do not apply
  until this exception ends.

## Alternatives rejected

- **A new `dom/NN-*` branch for each task.** Each task adds a PR to a long stack, and each change of
  a lower PR needs a rebase of all the branches above it.
- **Supersede 0027.** The exception is for one PR only. 0027 applies again after it.
- **Apply the one-PR reading to the test-fix rule.** A test fix then waits for the review of the
  full spec-build work.

## Not repeated

- Do not rebase below the base commit. The cited #81 SHAs and the `dom/NN-*` branches change.

_Edited 2026-10-29 (this PR): link repair._

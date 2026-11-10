# R39S — A test fix goes on the working branch in the spec-build stage

**Status:** absorbed into [`stack-commit/SKILL.md`](../../.claude/skills/stack-commit/SKILL.md), [`AGENTS.md`](../../AGENTS.md), 2026-11-10 (user; PR: pending).

## Decision

This entry supersedes [ADR-AB79](AB79-one-pr-for-the-spec-build-work.md) in full. It is an
exception to [ADR-0027](0027-single-working-branch.md) for the spec-build work. The rules of 0027
stay in [`AGENTS.md`](../../AGENTS.md#6-git-rules). They apply again when this exception ends.
Items 1 to 4 and 6 to 8 restate AB79 items 1 to 4 and 6 to 8. Item 5 replaces AB79 item 5. Item 9
is new.

1. **One PR.** The spec-build work goes to `development` in one PR from
   `dom/sidecar-implementation`. The user opens it and writes its body.
   [`AGENTS.md`](../../AGENTS.md#6-git-rules) and
   [Spec-build stage](../../.claude/skills/stack-commit/SKILL.md#spec-build-stage) state it, with the
   root files that the PR holds.
2. **No new branch.** [Spec-build stage](../../.claude/skills/stack-commit/SKILL.md#spec-build-stage)
   states it.
3. **One kind of change in each commit.**
   [Spec-build stage](../../.claude/skills/stack-commit/SKILL.md#spec-build-stage) and
   [Commit groups](../../.claude/skills/stack-commit/SKILL.md#commit-groups) state it, with the
   commit group and the valid tree after its last commit.
4. **The reading.** "The same PR" means the same commit group. A PR of one kind means a commit of
   that kind. [`AGENTS.md`](../../AGENTS.md#6-git-rules) states it.
5. **A test fix goes on the working branch.** In the spec-build stage, a fix of one root cause of a
   test or CI failure is its own commit on `dom/sidecar-implementation`, with no other change. The
   session reports it. It does not ask for the branch. This applies to a fix in
   `skellytracker/tests/`, in `tools/` and in CI. A fix that changes package code under
   `skellytracker/`, outside `skellytracker/tests/`, still stops for the user: the session reports
   the defect, and its fix waits for the implementation stage
   ([Phase 3](../../specs/model-sidecar/model-addition-workflow/phase-3-skellytracker.md) item 5).
6. **No rebase below the base.**
   [Spec-build stage](../../.claude/skills/stack-commit/SKILL.md#spec-build-stage) and
   [One worktree and frozen PRs](../../.claude/skills/stack-commit/SKILL.md#one-worktree-and-frozen-prs)
   state it. Thus #81 and the `dom/NN-*` branches stay valid and frozen.
7. **PR references.** [Spec-build stage](../../.claude/skills/stack-commit/SKILL.md#spec-build-stage)
   states it.
8. **End.** This exception ends when the user opens the PR. Then this entry is `done`. The steps of
   `.claude/skills/stack-commit/after-spec-build.md` then apply.
9. **Read the CI before a push.** Before a push request, the session reads the last fork CI runs of
   the working branch and reports a red run. An empty list is not a pass. After each push, it reads
   the CI result of that push before the next push.
   [Spec-build stage](../../.claude/skills/stack-commit/SKILL.md#spec-build-stage) gives the
   commands.

## Reason

- The user ruled two times that a test fix goes on the working branch: on 2026-11-07 (UTC) and on
  2026-11-09. Each time, the session stopped and asked, because AB79 item 5 and the skill told it to.
  Each question cost a user turn and a wait, and the answer was the same.
- The phase-3 rule for package code stays. A code defect is implementation work, and the package
  code does not change in this stage.
- The fork CI was red from 2026-11-04. About 20 commits were pushed on a red run before the user
  saw the failure. A read of `gh run list` before each push request finds a red run early.

## Consequences

- `stack-commit/SKILL.md` holds only the rules of the spec-build stage and the rules that apply in
  each stage. The post-stage steps are in `after-spec-build.md` next to it.
- A test fix lands in the one PR. It does not merge before the full spec-build work.

## Evidence

- 2026-11-07 (UTC): the session asked where the fix "Refuse an external-data location with a Windows
  drive on each OS" (a `tools/intake_bundle.py` fix) goes. The user answered "Working branch".
- 2026-11-09: the session asked again for a second test fix. The user answered
  "sidecar-implementation".
- The retrospective of the YOLOX and RTMW intake sessions (2026-11-06 to 2026-11-09) found both
  questions and the pushes on a red CI run.

## Alternatives rejected

- **Keep AB79 item 5.** Each test fix then stops the session for a question with a known answer.
- **Supersede 0027.** The exception is for one PR only. 0027 applies again after it.
- **Let a package-code fix go on the working branch.** The package code does not change in the
  spec-build stage ([Stages](../../specs/model-sidecar/model-addition-workflow/README.md#stages)).

## Not repeated

- Do not rebase below the base commit. The cited #81 SHAs and the `dom/NN-*` branches change.

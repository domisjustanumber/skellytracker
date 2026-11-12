---
name: stack-commit
description: Use this skill in skellytracker before you commit, rebase or push on the working branch, add a PR branch, change a lower PR, or write a PR body.
---

# Commit, rebase and push on the working branch

This skill uses ASD-STE100 Simplified Technical English.

The git rules of the root [`AGENTS.md`](../../../AGENTS.md#6-git-rules) also apply: no push and no
other outside action without the approval of the user, and no AI attribution.

Before you write a commit message or a PR body that names a decision entry, load
[`cite-entries`](../cite-entries/SKILL.md).

## Commit commands

- Run `git add <path>` for each file of the commit, also for a new file. `git commit -- <path>`
  refuses a file that git does not track yet.
- Then run `git commit -- <path>` with the same paths. The commit then holds only these files, also
  when the index holds staged files of other work.
- After each commit, run `git show --stat HEAD`. Make sure that it shows only the files of this
  commit.
- Run each `git commit` in its own tool call. Read its result before the next commit. A failed
  commit then stops the group
  ([ADR-9K2M](../../../decisions/entries/9K2M-agent-session-rules.md)).

## Spec-build stage

These rules apply until the rebuild at the gate of phase 0
([ADR-BH7C](../../../decisions/entries/BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md) item 3).

- The spec-build work goes to `development` in two PRs: `dom/52-process`, then `dom/53-spec`. Until
  the rebuild, all of it is on `dom/sidecar-implementation`
  ([ADR-BH7C](../../../decisions/entries/BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md) item 1).
  [Rebuild at the gate](after-spec-build.md#rebuild-at-the-gate) gives the steps.
- Commit only on `dom/sidecar-implementation`, on top of its current commits.
- Until the rebuild, do not add a `dom/NN-*` branch.
- Do not make a fixup commit for a lower PR. Do not run a rebase with `--update-refs`.
- Do not start a rebase below the commit "Remove the precision int8 from the sidecar model". Only
  the rebuild goes below it.
- Put one kind of change in each commit: content, move, rewording or non-spec.
- The tree must be valid after the last commit of each commit group.
- The parent of a range is the commit before the commit group (`git log` shows it). Give each report
  that a step puts in the PR body to the user in the session. Also write a summary of it in the
  message of the last commit of the group.
- [Section 3](../../../AGENTS.md#3-install-and-test) of `AGENTS.md` gives the commit of a test or
  CI fix.
- If the fix changes package code under `skellytracker/` outside `skellytracker/tests/`, stop.
  Report the defect to the user. Its fix waits for the implementation stage
  ([Phase 3](../../../specs/model-sidecar/model-addition-workflow/phase-3-skellytracker.md) item 5).
- Before each push, run
  `gh run list --repo "$(git remote get-url origin)" --branch dom/sidecar-implementation --limit 3`.
  The CI runs of a push are on the fork, not on the upstream repository. The list shows the runs of
  the last push. A red run or an empty list stops the push, also when the user approved the push
  earlier. Report it to the user. After the fix, ask for the push again
  ([ADR-6G6G](../../../decisions/entries/6G6G-ci-read-before-the-push.md)).
- Push only the working branch, after the approval of the user:
  `git push origin dom/sidecar-implementation`.
- After each push, run the same `gh run list` command when the runs of that push finish. Do this
  before the next push. Report a red result to the user
  ([ADR-R39S](../../../decisions/entries/R39S-test-fix-on-the-working-branch.md) item 9).
- "this PR" in an `_Edited_` line and "PR: pending" in a status line name the spec-build PR that
  holds the file. They stay as written after the PR opens
  ([ADR-R39S](../../../decisions/entries/R39S-test-fix-on-the-working-branch.md) item 7).
- The user opens each spec-build PR and writes its body.
- The steps of [`after-spec-build.md`](after-spec-build.md) apply after the rebuild.

## Commit groups

A commit group is a run of commits in a row on the working branch that do one task. Outside the
spec-build stage, the commits of one PR are its commit group.

## One worktree and frozen PRs

- Use one worktree only. Do not add a worktree. A rebase does not move a branch that a different
  worktree has checked out. The worktree of `hw-and-ep-work` stays until the stage "Merge
  `hw-and-ep-work`" copies its commits. Until then, each rebase waits
  ([ADR-BH7C](../../../decisions/entries/BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md) item 6).
- Do not change #81 (`dom/add-sidecar-spec`) or the old branches `dom/01-*` to `dom/51-*`. After the
  rebuild, the old branches are not in the stack
  ([ADR-BH7C](../../../decisions/entries/BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md) item 5).
- Do not change the commits of an open PR that other files cite. Do not add commits to it. Do not
  rebase it. #81 is such a PR: `specs/sidecar-implementation-plan.md` cites its commit SHAs.

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

The spec-build stage ended at the rebuild at the gate of phase 0
([ADR-V6G2](../../../decisions/entries/V6G2-implementation-stage.md)).
[`after-spec-build.md`](after-spec-build.md) gives the steps after the rebuild. Its rules that stay are
in [CI read](#ci-read) and [Old PR references](#old-pr-references).

## CI read

- Before each push, run
  `gh run list --repo "$(git remote get-url origin)" --branch dom/sidecar-implementation --limit 3`.
  The CI runs of a push are on the fork, not on the upstream repository. The list shows the runs of
  the last push. A red run or an empty list stops the push, also when the user approved the push
  earlier. Report it to the user. After the fix, ask for the push again
  ([ADR-6G6G](../../../decisions/entries/6G6G-ci-read-before-the-push.md)).
- After each push, run the same `gh run list` command when the runs of that push finish. Do this
  before the next push. Report a red result to the user
  ([ADR-R39S](../../../decisions/entries/R39S-test-fix-on-the-working-branch.md) item 9).

## Old PR references

- "this PR" in an `_Edited_` line and "PR: pending" in a status line of the spec-build stage name the
  spec-build PR that holds the file. They stay as written after the PR opens
  ([ADR-R39S](../../../decisions/entries/R39S-test-fix-on-the-working-branch.md) item 7).

## Commit groups

A commit group is a run of commits in a row on the working branch that do one task. The commits of
one PR are its commit group.

Before the last commit of a group, examine each decision entry that the group wrote or landed, and
each entry whose rules the group wrote into an absorb document. When the absorb documents state all
of the rules of the entry, absorb it in the last commit: set `absorbed into` with one link for each
heading, and move its row to `historical.md`. Do not ask the user. This applies also when you use
no other skill ([Rules](../../../decisions/README.md#rules); [ADR-W823](../../../decisions/entries/W823-absorb-in-the-commit-group-that-states-the-rules.md)).

## One worktree and frozen PRs

- Use one worktree only. Do not add a worktree. A rebase does not move a branch that a different
  worktree has checked out
  ([ADR-BH7C](../../../decisions/entries/BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md) item 6).
- Do not change #81 (`dom/add-sidecar-spec`) or the old branches `dom/01-*` to `dom/51-*`. After the
  rebuild, the old branches are not in the stack
  ([ADR-BH7C](../../../decisions/entries/BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md) item 5).
- Do not change the commits of an open PR that other files cite. Do not add commits to it. Do not
  rebase it. #81 is such a PR: `specs/sidecar-implementation-plan.md` cites its commit SHAs.

---
name: stack-commit
description: Use this skill in skellytracker before you commit, rebase or push on the PR stack, add a PR branch, change a lower PR, or write a PR body.
---

# Commit, rebase and push on the PR stack

This skill uses ASD-STE100 Simplified Technical English.

The git rules of the root [`AGENTS.md`](../../../AGENTS.md#6-git-rules) also apply: no push and no
other outside action without the approval of the user, and no AI attribution.
ADR-[0027](../../../decisions/0027-single-working-branch.md) gives the reasons for these steps.

## The working branch and the PR branches

- `dom/sidecar-implementation` is the working branch. It is the top of the PR stack. Commit only on
  this branch.
- Each PR has a branch `dom/NN-<topic>`. `NN` has two digits: the order in which the PRs are opened.
  The branch points to the last commit of its PR. Do not commit on a `dom/NN-*` branch. Do not check
  one out.
- Use one worktree only. Do not add a worktree. A rebase does not move a branch that a different
  worktree has checked out.
- Do not change #81 (`dom/add-sidecar-spec`), `dom/01-*` or `dom/02-*`. `dom/03-*` holds the merges
  of `dom/01-*` and `dom/02-*`.
- Do not change the commits of an open PR that other files cite. Do not add commits to it. Do not
  rebase it. #81 is such a PR: `specs/sidecar-implementation-plan.md` cites its commit SHAs.

## Add a commit

- **A new PR.** Commit on the working branch. When the PR is complete, add its branch at its last
  commit: `git branch dom/<NN>-<topic> <sha>`. `<NN>` is the next free number.
- **A change to a lower PR.** Make the commit on the working branch with
  `git commit --fixup=<sha>`. `<sha>` is a commit of that PR. Then run:

  ```sh
  git rebase -i --autosquash --update-refs dom/03-sidecar-spec-fixes
  ```

  Always write `--update-refs`, also when the config sets `rebase.updateRefs`. A different clone can
  have a different config. In the todo list, a line `update-ref refs/heads/dom/NN-<topic>` follows
  the last commit of each PR. To move a commit to a different PR, move its `pick` line to the other
  side of an `update-ref` line.
- **A change to `dom/03-*`.** Add `--rebase-merges`, and start the rebase at `dom/add-sidecar-spec`.
  Do not start a rebase below `dom/03-*` without `--rebase-merges`. A rebase without it removes the
  merges.
- **A decision entry.** Put a change of ID in the PR that adds the entry. Put each citation repair in
  the PR that adds the citation.
- Before a rebase, run `git worktree list`. If it shows more than one worktree, stop and ask the user.

## Check and push

- After a rebase, examine each changed PR:
  `git log --oneline <branch of the PR below>..<branch of the PR>`. Make sure that it shows only the
  commits of that PR. Then run `uv run pytest tools/tests`.
- Push the changed branches and the working branch in one command:

  ```sh
  git push --force-with-lease origin dom/<NN>-<topic> ... dom/sidecar-implementation
  ```

  A rebase changes commits, so this push is a force-push. It needs the approval of the user.
- A rebase changes the commit SHAs. Tell the user which PR bodies give an old SHA in "Review the
  commits after `<sha>`".
- **A squash merge upstream.** If a PR below is squashed, run `git fetch upstream`. Then run
  `git rebase --onto upstream/development <old branch of the squashed PR> dom/sidecar-implementation --update-refs`.
  Push the changed branches after the approval of the user.

## PRs

- Open each PR to `freemocap/skellytracker` against `development`. Keep each PR small.
- Start each PR body with: "Part NN/M of the sidecar spec series. Depends on #X. Until #X merges,
  this diff includes it. Review the commits after `<sha>`." `NN` is the order number of the PR. `M`
  is the number of PRs in the series.
- Link the passing CI run on the fork in each PR body.
- Merge a PR outside the stack, for example a CI fix, into the bottom branch of the stack.
- Make a draft ready only when each PR that it depends on has merged.
- A freemocap maintainer merges each PR and selects the merge method. When a PR body cites commit
  SHAs, it asks for a merge commit. If #81 is squashed, a follow-up PR replaces its cited SHAs.

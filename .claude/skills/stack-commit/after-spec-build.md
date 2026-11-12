# Commit, rebase and push after the spec-build stage

This file uses ASD-STE100 Simplified Technical English.

These steps of the [`stack-commit`](SKILL.md) skill apply after the rebuild at the gate of phase 0
([ADR-BH7C](../../../decisions/entries/BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md) item 3).
The rules of the skill also apply.

## Rebuild at the gate

Do these steps one time, at the gate of phase 0, after the exporter kit and the copy of
`hw-and-ep-work`
([ADR-BH7C](../../../decisions/entries/BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md) item 2;
[ADR-RH69](../../../decisions/entries/RH69-repository-infrastructure-first.md)).

1. Run `git worktree list`. It must show one worktree.
2. Keep the old history: `git branch dom/spec-build-history dom/sidecar-implementation`.
3. Make `dom/52-process` on the last commit of #81 with the repository infrastructure of the final
   files ([ADR-RH69](../../../decisions/entries/RH69-repository-infrastructure-first.md) item 1).
   Give `run_checks.py` and the lint workflow their own form with only the checks that the tree of
   `dom/52-process` can run.
4. Make `dom/53-spec` on `dom/52-process` with the rest (RH69 item 2). `git diff
   dom/spec-build-history dom/53-spec` must show no change.
5. Put each kind of change in its own commit. Run `uv run python tools/run_checks.py` on the last
   commit of each branch.
6. Move the working branch to `dom/53-spec`. Then push `dom/spec-build-history`, the two PR
   branches and the working branch, after the approval of the user. This push is a force-push.
7. The user opens the two PRs.

## The working branch and the PR branches

- `dom/sidecar-implementation` is the working branch. It is the top of the PR stack. Commit only on
  this branch.
- Each PR has a branch `dom/NN-<topic>`. `NN` has two digits: the order in which the PRs are opened.
  The branch points to the last commit of its PR. Do not commit on a `dom/NN-*` branch. Do not check
  one out.
- The stack starts with `dom/52-process` and `dom/53-spec`. Then each stage of phase 1 of the
  implementation plan is one PR, in the stage order: `dom/54-dependencies`, `dom/55-package-layout`
  and so on. The gate of the stage is the gate of its PR. A stage that can run in parallel also goes
  in this one stack
  ([ADR-BH7C](../../../decisions/entries/BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md) item 4).

## Add a commit

- **A new PR.** Commit on the working branch. When the PR is complete, add its branch at its last
  commit: `git branch dom/<NN>-<topic> <sha>`. `<NN>` is the next free number.
- **A change to a lower PR.** Make the commit on the working branch with
  `git commit --fixup=<sha>`. `<sha>` is a commit of that PR. Then run:

  ```sh
  git rebase -i --autosquash --update-refs origin/dom/add-sidecar-spec
  ```

  Always write `--update-refs`, also when the config sets `rebase.updateRefs`. A different clone can
  have a different config. In the todo list, a line `update-ref refs/heads/dom/NN-<topic>` follows
  the last commit of each PR. To move a commit to a different PR, move its `pick` line to the other
  side of an `update-ref` line. Do not start a rebase below the last commit of #81
  ([ADR-BH7C](../../../decisions/entries/BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md) item 5).
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

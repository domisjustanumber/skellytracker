# 0027 — One working branch for the PR stack

**Status:** absorbed into [`AGENTS.md#6-git-rules`](../../AGENTS.md#6-git-rules), 2026-10-25 (user; the absorption review).

## Decision

This entry supersedes [0015](0015-review-discipline.md). It keeps the rules of 0015, except the
rules for the branch `dom/sidecar-latest` and the worktree `skellytracker-latest`. 0015 keeps the
reasons and the evidence for the rules that stay. [`AGENTS.md`](../../AGENTS.md#6-git-rules) gives
the git commands.

### One kind of change in each PR

- Each PR has one kind of change: content, move, rewording or non-spec. The table in
  [0015](0015-review-discipline.md#one-kind-of-change-in-each-pr) defines each kind.
- A move PR can add labels: section IDs, rule IDs and the front matter fields `id`, `title` and
  `kind`.
- New content goes on top of the PR stack. It never goes in a move PR or a rewording PR.

### Stacked PRs

- Each PR to `freemocap/skellytracker` targets `development`, and it is small.
- Each PR has one branch on the fork, `dom/NN-<topic>`. `NN` has two digits. It is the order in which
  the PRs are opened. The branch points to the last commit of its PR. A new PR gets the next free
  number. #81 keeps its branch `dom/add-sidecar-spec`.
- Each PR body starts: "Part NN/M of the sidecar spec series. Depends on #X. Until #X merges, this
  diff includes it. Review the commits after `<sha>`." `NN` is the order number of the PR, and `M`
  is the number of PRs in the series. The body links the passing CI run on the fork.
- A PR outside the stack, for example a CI fix, is merged into the bottom branch of the stack.
- A draft is ready only when each PR that it depends on has merged.
- Do not change the commits of #81. Other files cite its commit SHAs.

### The working branch

- `dom/sidecar-implementation` is the working branch. It is the top of the stack. All commits for the
  stack go on it, and it is pushed to the fork.
- Do not commit on a `dom/NN-*` branch.
- To change a PR below the top, make a fixup commit on the working branch. Then run an interactive
  rebase with `--autosquash` and `--update-refs`. The rebase moves each `dom/NN-*` branch to its
  rewritten commit.
- A rebase starts at `dom/03-*` or higher. `dom/03-*` holds the merges of `dom/01-*` and `dom/02-*`.
  A rebase that crosses them needs `--rebase-merges`.
- The repo has one worktree, the checkout `skellytracker`. A rebase does not move a branch that a
  different worktree has checked out.

### Exporter agents

- Exporter agents read the spec, the skills and the templates in the checkout
  `../freemocap/skellytracker`. They read only. They do not edit files, commit or change the branch.
- The checkout must be on the working branch. If it is on a different branch, the exporter agent
  stops and asks the user.

### Merge method, citations and approvals

- A freemocap maintainer merges each PR and selects the merge method. Where commit SHAs are cited, the
  PR body asks for a merge commit. If #81 is squashed, a follow-up PR replaces its cited SHAs.
- If a PR below is squashed, rebase the working branch with `--onto upstream/development` and
  `--update-refs`. Then push the changed branches.
- Until a commit is on `development`, cite its PR number and the file path, not its SHA.
- One approval for each PR covers its push, its draft PR and its description. A force-push is a new
  push. It needs its own approval. Ask before any other action that is visible outside this machine.

## Reason

- The stack has 11 branches. A commit on a lower branch leaves the branches above it behind. Each of
  them then needs its own rebase, and a wrong SHA copies commits into the wrong PR. With one working
  branch and `--update-refs`, one rebase moves all the branches.
- `dom/sidecar-latest` was a copy of the top of the stack. It needed a move after each push. The
  working branch is the top of the stack, so exporter agents read it directly.
- The number prefix shows the order of the PRs in the branch list.
- The user decided on 2026-10-23 that the repo has one checkout, and that exporter agents read it.
  The checkout must then stay on the working branch.

## Alternatives rejected

- **Keep the read-only worktree `skellytracker-latest`.** It needs a move after each change. With
  one checkout, there is no copy to keep current.
- **One PR for the full stack.** No part of it can merge alone, and one change request stops all of it.
- **ghstack, spr or Graphite.** These tools push branches to the target repo. The fork account has
  `push: false` on `freemocap/skellytracker`.

## Not repeated

- Do not commit on a `dom/NN-*` branch. The branches above it do not move.
- Do not start a rebase below `dom/03-*` without `--rebase-merges`.
- Do not rename the head branch of an open PR. GitHub closes the PR.

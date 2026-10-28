# 0015 — Review discipline: one kind of change per PR, stacked drafts, merge method

**Status:** superseded by [0027](0027-single-working-branch.md), 2026-10-23 (user).

## Decision

### One kind of change in each PR

- Each PR has one kind of change:

  | Kind | What it changes |
  |------|-----------------|
  | content | The normative meaning of the spec. The examples, vectors and reference implementations that define that meaning go with it. |
  | move | The place of text, for example the split of the spec into section files. The words do not change. |
  | rewording | The words of the text. The meaning does not change. |
  | non-spec | The decision log, agent files, tools, vectors, guidance, CI and test fixes. Also an example that changes no normative meaning, with its provenance record, and an exporter's reference implementation of the current spec text. |

- A move PR can add labels to the text: section IDs, rule IDs and the front matter fields `id`,
  `title` and `kind`. Labels do not change the meaning.
- A move PR links the last single-file version of the spec by permalink. It includes the output of
  the verbatim check and a table from each old heading to its new file. A rewording PR includes the
  meaning-check tables of [0013](0013-spec-structure.md).
- New content goes on top of the PR stack. It never goes inside a move or rewording PR.

### Small PRs on stacked branches

- Each PR to `freemocap/skellytracker` targets `development`. Each PR is small and easy for a person
  to read.
- Each PR has one branch on the fork. Each branch is built on the branch of the PR below it
  (stacked). Work continues up the stack. It does not wait for a review.
- Each stacked branch gets a draft PR into `development` when it is pushed. The body says: "Stack
  N/M. Depends on #X. Until #X merges, this diff includes it. Review the commits after `<sha>`." The
  body also links the passing CI run on the fork.
- Claude also merges each PR outside the stack, for example a CI fix or a test fix, into the bottom
  branch of the stack. Then each stacked branch has passing CI. The bottom PR lists it as a
  dependency.
- A draft is marked ready only when each PR that it depends on has merged, not only the PR below it.
  When the PR below merges with a merge commit, the diff of the draft becomes its own commits without
  a rebase.
- The freemocap developers approve the PRs to follow the work. If a PR gets change requests, the
  branches above it are rebuilt on the changed branch.

### The local branch `dom/sidecar-latest` and the read-only worktree

- `dom/sidecar-latest` is a local branch. It is never pushed. It always points to the top of the
  stack.
- The worktree `skellytracker-latest`, next to the skellytracker repo, is detached at
  `dom/sidecar-latest`. It has no branch to commit to. A commit made there by mistake is on no
  branch, and the next move of the worktree leaves it behind.
- Exporter agents read the spec, the skills and the templates from this worktree, as
  `../freemocap/skellytracker-latest` from their own repo. They never edit files there. They never
  commit to skellytracker.
- Claude makes the branch and the worktree after the push of the stacked branch that adds the
  exporter guide. The branch starts at the tip of that stacked branch. Then Claude runs this command
  from the skellytracker repo:

  ```sh
  git worktree add --detach ../skellytracker-latest dom/sidecar-latest
  ```

- After each push of a stacked branch, Claude moves the branch and the worktree to the new top of the
  stack. The worktree shares the branches of the skellytracker repo, so no fetch is necessary. If an
  exporter agent thinks that the worktree is out of date, it runs this command from its own repo:

  ```sh
  git -C ../freemocap/skellytracker-latest checkout --detach dom/sidecar-latest
  ```

- When the full stack has merged, `dom/sidecar-latest` is equal to `upstream/development`.

### #81

- Do not change the commits of #81: no new commits and no rebase. Its commit SHAs are cited, and it
  has one kind of change. Its description can change, with the user's approval.

### Merge method

- A freemocap maintainer merges #81 and each later PR. The merge method is their choice. The workflow
  works with a merge commit and with a squash.
- Where commit SHAs are cited, the PR body asks for a merge commit. For #81, the note is: "Please
  merge with a merge commit if possible. `specs/sidecar-implementation-plan.md` cites commit SHAs of
  this PR, and a squash orphans them." Claude adds this note to the description of #81 after the
  user approves it. On 2026-10-22, the description of #81 does not have it.
- **Squash fallback.** If a PR below is squashed, Claude runs `git fetch upstream`. Then Claude
  rebases the child branch:

  ```sh
  git rebase --onto upstream/development <old parent tip> <child>
  ```

  After the user approves the push, Claude force-pushes the child branch. Claude does this before the
  draft is marked ready.

- If #81 is squashed, a small follow-up PR replaces its cited SHAs with `#81` and the SHA of the
  squash commit.

### Citations

- Until a commit is on `development`, decision entries and new documents cite the PR number and the
  file path (with the heading), not the commit SHA.
- After a merge, a citation can add the SHA that exists on `development`. With merge commits, the
  SHAs of merged PRs stay valid.

### Approvals

- One approval for each PR covers its push, its draft PR and its description.
- Do not push without approval. Ask before any other action that is visible outside this machine.
- Claude can move the local branch `dom/sidecar-latest` and the worktree without approval, because
  nothing leaves the machine.
- The force-push of the squash fallback is a new push. It needs its own approval.

## Reason

- **One kind of change is easy to review.** A move PR is checked with a script: the same lines before
  and after. A rewording PR is checked with the meaning check. Only a content PR needs a review of
  meaning. In a PR that mixes kinds, a change of meaning can hide among many moved lines.
- **Small PRs** are easy for a person to read.
- **Stacked drafts let work continue.** The fork account cannot push to `freemocap/skellytracker`, and
  a fork PR can only target a branch of that repo. Thus a PR cannot use the branch of the PR below as
  its base. A draft shows the work and its dependencies before its base merges.
- **A draft is ready only when all of its dependencies have merged.** Before that, its diff also
  shows the commits of the PRs below it.
- **Exporter agents need a stable place to read.** The skellytracker working tree is often on a
  feature branch. `development` is behind the stack, and it has no spec until #81 merges. A detached
  worktree at the top of the stack gives the current text and has no branch to commit to.
- **The branch stays local.** A pushed branch would need a force-push, a CI run and an approval on
  each move. This assumes that exporter agents run on the same machine.
- **#81 stays unchanged.** Other files cite its commit SHAs. New commits or a rebase would change
  the review and the SHAs.
- **A merge commit keeps the cited SHAs and the stack.** See the table in "Evidence".
- **A PR number and a file path survive a squash.** A branch SHA can become orphaned.
- **One approval for each PR** keeps each outward action approved, with fewer interruptions.

## Evidence

- **Merge methods.** The three GitHub merge methods, and their effect on this workflow:

  | | Merge commit | Squash | Rebase |
  |---|---|---|---|
  | Commits on `development` | All PR commits, and one merge commit | One new commit for each PR | All PR commits, with new SHAs |
  | PR commit SHAs | Kept | Lost: no branch keeps them after the PR branch is deleted | Lost |
  | History | Shows each step of the work | One line for each PR | Linear; shows each step |
  | Revert a full PR | `git revert -m 1 <merge>` | `git revert <commit>` | Revert each commit |
  | Bisect | Finds the exact commit | Finds the PR | Finds the exact commit |
  | Stacked branches after the PR below merges | Merge without problems | Need `git rebase --onto`; conflicts are likely | Need `git rebase --onto` |
  | Blame on the section files after the split | The move commit, then each rewording commit | One commit for each PR | The same as a merge commit |

- **#81** (checked 2026-10-22). It is open into `development` and has 13 commits. None of them is
  on `development`. `specs/sidecar-implementation-plan.md` cites six of these commits by SHA. A
  squash orphans all six citations.
- **Upstream uses both methods.** #75, #77, #78 and #86 were squashed: `2c2615c`, `6192542`,
  `7a8f80c` and `1458bb5` each have one parent. #27 was merged with the merge commit `48e366a`. Thus
  a request for a merge commit does not go against an existing rule.
- **Fork access.** The GitHub API gives the fork account `push: false` on `freemocap/skellytracker`.
- **Upstream CI.** On 2026-10-22, 98 of the last 100 Actions runs on `freemocap/skellytracker` ended
  in `startup_failure`. The other two were GitHub's own "Dependency Graph" runs. Thus each PR body
  links the CI run on the fork.

## Alternatives rejected

- **Squash for each PR.** It loses the cited SHAs, and each stacked branch then needs
  `git rebase --onto`.
- **Rebase merge.** It gives all commits new SHAs, so the cited SHAs are lost.
- **More commits on #81** for the content fixes. #81 is already large, and its SHAs are cited. The
  fixes go in a separate small PR.
- **Wait for each review before the next PR.** The reviews come later than the work. The stack lets
  the work continue.
- **Push `dom/sidecar-latest` to the fork.** Each move would need a force-push, a CI run and an
  approval.
- **Exporter agents read from the working tree or from `development`.** The working tree is often on
  a feature branch, and `development` is behind the stack.

## Not repeated

- Do not put new content in a move or rewording PR. Put it on top of the stack.
- Do not mark a draft ready while a PR that it depends on is open.
- Do not change the commits of #81.
- Do not cite the SHA of a commit that is not on `development`. Cite the PR number and the file
  path.
- Do not edit files in the `skellytracker-latest` worktree. Do not push `dom/sidecar-latest`.

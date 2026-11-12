# BH7C — Two spec-build PRs from a rebuild at the gate; one stacked PR for each implementation stage

**Status:** accepted, 2026-11-12 (user).

## Decision

This entry supersedes [ADR-R39S](R39S-test-fix-on-the-working-branch.md) and
[ADR-0027](0027-single-working-branch.md) in full. Items 2 to 5, 7 and 9 of R39S stay. Items 1 to 3
below replace R39S items 1, 6 and 8. The rules of 0027 stay, except its rebase start at `dom/03-*`.
Item 5 replaces it. These headings restate the rules that stay:
[Install and Test](../../AGENTS.md#3-install-and-test),
[Git Rules](../../AGENTS.md#6-git-rules),
[Spec-build stage](../../.claude/skills/stack-commit/SKILL.md#spec-build-stage),
[Commit groups](../../.claude/skills/stack-commit/SKILL.md#commit-groups),
[One worktree and frozen PRs](../../.claude/skills/stack-commit/SKILL.md#one-worktree-and-frozen-prs)
and [after-spec-build.md](../../.claude/skills/stack-commit/after-spec-build.md#commit-rebase-and-push-after-the-spec-build-stage).

1. **Two spec-build PRs.** The spec-build work goes to `development` in two PRs on top of #81:
   - `dom/52-process`: the agent instructions, the process skills, the decision log rules, the
     process entries, the checks in `tools/` and the repository configuration.
   - `dom/53-spec`: the model sidecar spec, the pipeline spec, their skills, tools and entries, and
     the implementation plan. It depends on `dom/52-process`. Its last tree is the tree of the
     working branch.

   The user opens each PR and writes its body.
2. **The rebuild at the gate.** At the gate of phase 0, after the exporter kit and the copy of
   item 6, the session makes the two PRs from the final files of the working branch. It does not
   split the old commits. Each new commit has one kind of change. The tree of `dom/52-process` must
   pass `tools/run_checks.py` alone. Thus a root entry that links a spec file goes in `dom/53-spec`.
   `dom/52-process` gets its own form of `AGENTS.md` and of the index files, and `dom/53-spec` adds
   the rest. This one rebuild goes below the commit "Remove the precision int8 from the sidecar
   model". The old history stays on the fork in the branch `dom/spec-build-history`, so the commit
   SHAs that tracked files cite stay valid.
3. **End of the exception.** The rules of the spec-build stage apply until the rebuild. Then the
   steps of `after-spec-build.md` apply.
4. **One stacked PR for each implementation stage.** Each stage of phase 1 of the implementation
   plan is one PR, in the stage order, with the next free number: `dom/54-dependencies`,
   `dom/55-package-layout` and so on. The gate of the stage is the gate of its PR. A stage that can
   run in parallel also goes in the one stack.
5. **The working branch and the rebase start.** `dom/sidecar-implementation` stays the working
   branch and the top of the stack. Exporter agents read it. A rebase starts at the last commit of
   #81 or higher. #81 and the old branches `dom/01-*` to `dom/51-*` do not change. After the
   rebuild, the old branches are not in the stack.
6. **The copy of `hw-and-ep-work`.** The stage "Merge `hw-and-ep-work`" copies the six commits of
   the EP device check suite with `git cherry-pick`. It does not copy the graphify commits or the
   merge commit. Then the branch and its worktree retire. Until then, the second worktree is
   permitted, and each rebase waits.

## Reason

- The user chose on 2026-11-12: two PRs, the process first; a rebuild from the final files; the
  rebuild at the gate; one PR for each stage; a branch for each PR; the cherry-pick.
- One PR would hold 452 commits and about 79,000 added lines. 0027 rejected one PR for the full
  stack: no part of it can merge alone.
- A split of the old commits is too costly: 167 commits change both kinds of file.
- The rebuild uses the final files. At the gate, it is done one time.
- A PR head that is also the working branch takes each later commit into that PR.
- The pre-release is published from a tag in `freemocap/skellytracker`, so the spec-build PRs must
  merge before the pre-release.
- The graphify commits of `hw-and-ep-work` are byte copies of files on the working branch.

## Evidence

On 2026-11-12, at the head of the working branch:

- `git diff-tree` of each of the 442 non-merge commits after #81, with this classification: spec =
  `specs/`, `notes/`, `rearchitecture-docs/`, the package code and tests, the spec tools and the spec
  skills; process = the rest. 56 commits change only process files, 219 only spec files, 167 both.
- A tree of #81 plus the process files of the head: `tools/check_links.py` gives 660 broken links.
  76 of the 125 root entries link a spec file.
- `git merge-tree` of the working branch and `hw-and-ep-work`: conflicts only in `AGENTS.md` and
  `decisions/README.md`.

## Alternatives rejected

- **One spec-build PR (R39S item 1).** It is too large to review.
- **A split of the old commits.** Each of 167 commits needs a split, and the tree of each commit
  group must pass the checks.
- **The rebuild now.** The later phase 0 work then needs a second rebuild.
- **Grouped stage PRs, or side branches for the parallel stages.** A group gives a large PR. A side
  branch needs its own rebase.
- **A new working branch for phase 1.** Exporter agents then change the branch.
- **A merge of `hw-and-ep-work`.** The PR shows the graphify change two times, and the merge commit
  mixes kinds of change.

## Not repeated

- Do not make the head of a PR the working branch.

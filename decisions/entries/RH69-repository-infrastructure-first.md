# RH69 — The rebuild puts the repository infrastructure in `dom/52-process`

**Status:** accepted, 2026-11-12 (user).

## Decision

This entry supersedes [ADR-BH7C](BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md) in full. It
changes item 1 of BH7C and the part of item 2 that names the content of `dom/52-process`. These
headings state the other rules of BH7C:
[Install and Test](../../AGENTS.md#3-install-and-test),
[Git Rules](../../AGENTS.md#6-git-rules),
[Commit groups](../../.claude/skills/stack-commit/SKILL.md#commit-groups),
[One worktree and frozen PRs](../../.claude/skills/stack-commit/SKILL.md#one-worktree-and-frozen-prs),
[Rebuild at the gate](../../.claude/skills/stack-commit/after-spec-build.md#rebuild-at-the-gate),
[The working branch and the PR branches](../../.claude/skills/stack-commit/after-spec-build.md#the-working-branch-and-the-pr-branches)
and [Add a commit](../../.claude/skills/stack-commit/after-spec-build.md#add-a-commit).

1. **`dom/52-process`** holds the repository infrastructure of the final files: the CI workflows,
   `.gitleaks.toml`, `.gitignore`, `.gitattributes`, and the checks that need no spec file and no
   decision log: `tools/check_private_data.py`, `tools/check_ai_attribution.py`,
   `tools/check_ste_tokens.py`, `tools/run_checks.py` and their tests. Two files have their own form
   there. `run_checks.py` runs ruff on `skellytracker/` and `tools/`, the doc tests and the package
   tests. The lint workflow runs ruff on the same folders.
2. **`dom/53-spec`** holds the rest: each `AGENTS.md` and `CLAUDE.md`, all skills, the whole
   decision log, `pyproject.toml`, `uv.lock`, the pre-commit configuration, the other tools in
   `tools/`, the specs, the package code and tests, `README.md` and the implementation plan. Its
   last tree is the tree of the working branch.

## Reason

- The user chose this split on 2026-11-12 (question Q24).
- 93 of the 142 root entries link a spec file. A decided entry does not change, so each entry that
  links one of them also goes to `dom/53-spec`. Only 3 entries stayed for `dom/52-process`, and it
  needed stripped forms of about 12 files with about 290 links.
- In a tree of #81 with the infrastructure: `tools/check_links.py` finds a broken link in the #81
  file `specs/sidecar-spec.md`; the test of `tools/check_decision_log.py` needs a real log; the
  test of `tools/graphify_hooks.py` reads `AGENTS.md`. Thus these tools go to `dom/53-spec`, with
  the pre-commit configuration that runs the decision log check.
- The golden fixtures of the package tests changed with the `onnxruntime` 1.31 floor of
  `pyproject.toml`. Thus `pyproject.toml` and `uv.lock` go with the package code.

## Alternatives rejected

- **BH7C as written.** Its process PR would be stripped forms that the spec PR puts back.
- **One PR.** It would hold about 79,000 added lines, and no part of it could merge alone.

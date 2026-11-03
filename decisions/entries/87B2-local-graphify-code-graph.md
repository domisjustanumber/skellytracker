# 87B2 — Optional local graphify code graph in an ignored `graphify-out/`; `uvx` pin; hooks from `tools/graphify_hooks.py`; opt-in for each checkout

**Status:** accepted, 2026-11-03 (user).

## Decision

1. **The tool.** graphify (PyPI `graphifyy`, version `0.9.100`) is an optional local tool. Run it
   with `uvx --from graphifyy==0.9.100 graphify`. It is not a project dependency.
2. **The graph.** Each checkout keeps its graph in `graphify-out/` in its root. Git ignores this
   folder. Do not commit a file from it.
3. **The hooks.** [`tools/graphify_hook.sh`](../../tools/graphify_hook.sh) is the hook.
   `uv run python tools/graphify_hooks.py install` copies it to `post-commit`, `post-checkout`,
   `post-merge` and `post-rewrite` in the common hooks folder, adds `graphify-out/` to
   `info/exclude` and builds the current checkout. The docstring of
   [`tools/graphify_hooks.py`](../../tools/graphify_hooks.py) states the install rules.
4. **Opt-in.** The hook updates only a checkout that has `graphify-out/`. The hook runs
   `graphify update . --force` in the background, with no LLM, one worker and a limit of 900 s
   (`timeout` or `gtimeout`; with neither, no limit). It always exits 0.
5. **Not managed elsewhere.** The pre-commit framework and `graphify hook install` do not manage
   these hooks.
6. **No writes to agent files.** Do not let graphify write to a `CLAUDE.md`, an `AGENTS.md`,
   `.claude/` or `.gitattributes`. [`AGENTS.md` section 3](../../AGENTS.md#3-install-and-test) lists
   the commands that agents must not run.
7. **No LLM pass.** Do not run `/graphify`, `graphify extract`, `graphify label` or `graphify add`
   without the approval of the user.

## Reason

- The common hooks folder and `info/exclude` apply to each worktree. One install covers each branch
  and each worktree.
- graphify rewrites the whole graph on each build. A tracked graph changes on each commit of each
  branch.
- `uvx` comes with uv, so a new machine needs no install step. A dev dependency adds about 30
  tree-sitter packages to `uv.lock` and to each CI install. A background `uv run` after a branch
  switch also syncs `.venv` to the lock of that branch.
- A build in a linked worktree holds its files. On Windows, `git worktree remove --force` then
  fails. The opt-in keeps temporary worktrees free of builds.

## Evidence

Measured on 2026-11-03 with graphifyy 0.9.100, uv 0.11.8 and Git for Windows 2.43.0, in a clone of
`hw-and-ep-work`, with [`scripts/graphify_build_timing.sh`](../scripts/graphify_build_timing.sh):

- A full build reads 418 files (202 `.py`, 155 `.md`, 42 `.yaml`) in 10 s and writes 21 MB. A build
  with no change takes 1 s. A cached `uvx` start takes 0.2 s.
- `tools/check_private_data.py` passes while `graphify-out/` exists.
- `timeout` stops the build (rc 124), and no graphify Python process stays. The next build is not
  blocked: it takes 8 s.

Code facts and checks by hand:

- `graphify/watch.py` `_rebuild_lock` locks `.rebuild.lock` with `msvcrt.locking` on Windows.
  Windows releases that lock when the process stops, so a leftover file does not block a build.
- `graphify query` finds Python symbols, Markdown headings and the matching resize code.
- `.graphify_build_state.json` holds the absolute path of the checkout. `graphify-out/` is ignored.

## Alternatives rejected

- **The pre-commit framework.** `development`, `main`, #79 and #81 have no
  `.pre-commit-config.yaml`. There, a `post-checkout` hook of pre-commit exits 1, and `git switch`
  returns that status.
- **`graphify hook install`.** At version 0.9.100, its hooks do nothing in a linked worktree. It
  also registers a merge driver in the git config and in the tracked `.gitattributes`
  (`graphify/hooks.py`, the worktree guard and the merge-driver functions).
- **A build in each worktree.** It blocks the removal of temporary worktrees on Windows.
- **A Claude Code hook or the graphify skill.** `CLAUDE.md` only imports `AGENTS.md`. A line in
  `AGENTS.md` reaches each agent.

## Not repeated

- `graphify update` without `--force` does not write a graph with fewer nodes. A switch to an older
  branch then leaves a stale graph.

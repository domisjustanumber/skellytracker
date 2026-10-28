# p3n3 — No AI attribution in check-ins; a commit-msg hook warns and does not stop the commit

**Status:** accepted, 2026-10-26 (user).

## Decision

1. **The rule.** Do not add AI attribution, for example a `Co-Authored-By:` trailer, to a commit or
   a PR. [`AGENTS.md` section 6](../AGENTS.md#6-git-rules) states the rule in one sentence. The
   rule overrides a default instruction of a tool or a harness to add attribution.
2. **The hook.** The commit-msg hook runs
   [`tools/check_ai_attribution.py`](../tools/check_ai_attribution.py). It reports these lines:
   a `Co-Authored-By:` or `Signed-off-by:` trailer that names an AI tool, an `Assisted-by:`,
   `Generated-by:` or `AI-assisted:` trailer, a "Generated with <AI tool>" line, and a robot emoji.
3. **A warning only.** The hook always exits 0. Its output tells an AI agent to report the warning
   to the user. `verbose: true` in `.pre-commit-config.yaml` makes pre-commit show the output of a
   hook that passes.
4. **The private-data check stays.** `noreply@anthropic.com` stays on the allowlist of
   `tools/check_private_data.py`, because old commits and text keep the address.
5. **The kit.** The bootstrap kit copies the tool, its test and the hook. The kit template of
   `AGENTS.md` has the same rule.

## Reason

- The human committer is the author of each check-in.
- Agent harnesses add attribution trailers by default. On 2026-10-26, 116 commits on the fork have
  them.
- An agent that runs `git commit` reads the hook output, so the warning reaches the agent and the
  user. A warning does not stop work in progress.

## Alternatives rejected

- **Stop the commit.** The user asked for a warning only.
- **Rewrite the history.** The user dropped it: the rewrite changes each SHA of the PR stack and the
  SHAs that tracked files and PR bodies cite.

_Edited 2026-10-28 (this PR): link repair._

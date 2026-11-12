# 9K2M — Agent session rules: one commit for each call, questions to the user, sub-agent briefs, spec changes that the user decides

**Status:** absorbed into [`stack-commit/SKILL.md#commit-commands`](../../.claude/skills/stack-commit/SKILL.md#commit-commands), [`ask-the-user/SKILL.md#steps`](../../.claude/skills/ask-the-user/SKILL.md#steps), [`ask-the-user/SKILL.md#check-before-you-send`](../../.claude/skills/ask-the-user/SKILL.md#check-before-you-send), [`brief-subagent/SKILL.md#the-brief`](../../.claude/skills/brief-subagent/SKILL.md#the-brief), [`brief-subagent/SKILL.md#the-result`](../../.claude/skills/brief-subagent/SKILL.md#the-result), [`change-sidecar-spec/SKILL.md#procedure-d-another-spec-edit`](../../.claude/skills/change-sidecar-spec/SKILL.md#procedure-d-another-spec-edit), 2026-11-12 (absorb sweep, user; PR: pending).

## Decision

1. **Commits.** Run each `git commit` in its own tool call. Run `git add <path>` for each file,
   then `git commit -- <path>` with the same paths, so that other staged work stays out of the
   commit. After the commit, check its files with `git show --stat HEAD`. The skill `stack-commit`
   states this rule.
2. **Questions to the user.** Each question names its subject in full, gives one concrete example
   for each option, cites the file and line of each fact that it starts from, and ends with a
   recommendation. The skill `ask-the-user` gives the steps.
3. **Sub-agent briefs.** A brief tells the agent to give each location as `path:line` from `grep -n`
   or Read output, with the quoted line. The main agent opens each cited line before it tells the
   user a claim or acts on it. The skill `brief-subagent` gives the steps.
4. **Spec changes that the user decides.** When the user decides a spec content change in a
   skellytracker session and no proposal bundle exists, the agent writes the decision entry with
   the status `accepted`. Procedure D of the skill `change-sidecar-spec` states this case.

## Reason

A retrospective of the pipeline-spec session of 2026-11-11 found these failures:

- Three commits ran in one tool call. The first commit failed: `git commit -- <path>` refuses a
  file that git does not track. The next two commits ran, took the wrong files, and needed a reset.
- In the retrospective session, the index held the staged renames of an unfinished landing. A
  `git commit` with no path would have put them in the wrong commit.
- The user asked for an explanation or an example about 20 times. The user also asked what a
  plan item number meant. One question started from a wrong fact that the draft spec corrects.
- A review sub-agent gave wrong line numbers. The main agent found them only because it checked
  each finding.
- Procedure D sent a spec change with no entry to `propose-sidecar-change`. In skellytracker, that
  skill only records a contributor bundle. The agent found no path for a change that the user
  decided in the session.

## Consequences

- `AGENTS.md` section 2 lists the two new skills. The bootstrap kit copy of section 2 does not
  hold the skill table, so the kit does not change.
- A `&&` chain is not a fix for item 1: the shells of the agents do not all read it the same way.

## Open work

[open-work.md](../open-work.md)

# VCQ7 — A skill for the citation of entries

**Status:** absorbed into [`cite-entries/SKILL.md#cite-decision-entries`](../../.claude/skills/cite-entries/SKILL.md#cite-decision-entries), [`AGENTS.md#2-skills`](../../AGENTS.md#2-skills), [`stack-commit/SKILL.md#commit-rebase-and-push-on-the-working-branch`](../../.claude/skills/stack-commit/SKILL.md#commit-rebase-and-push-on-the-working-branch), 2026-11-12 (absorb sweep, user; PR: pending).

## Decision

1. **The skill.** [`cite-entries`](../../.claude/skills/cite-entries/SKILL.md) gives the steps to
   apply the citation rule of [section 5](../../AGENTS.md#5-decision-log) of `AGENTS.md`. The rule
   stays in section 5. The skill holds the forms, the steps for lists, tables and paths, and a check
   before a reply is sent.
2. **Its triggers.** An agent loads it before it sends a reply, or writes a plan, a PR body or a
   commit message, that names an entry. The [section 2](../../AGENTS.md#2-skills) table lists it.
   [`stack-commit`](../../.claude/skills/stack-commit/SKILL.md) tells the agent to load it before a
   commit message or a PR body.
3. **No hook.** No hook or test checks the citations of replies or commit messages for now. The user
   decides on a hook when the skill is not enough.

## Reason

- The user, 2026-11-10, asked why a reply cited entries as bare IDs, then chose the skill and "no
  hooks for now, let's see if the skills file is enough first".
- A review of 2026-11-10 found that no skill restated or linked the rule, and that no check read
  replies or commit messages. A scan of the tracked Markdown found almost no bare IDs outside the
  logs. So the bare IDs came from replies and commit messages.
- The bare IDs were IDs used as names in lists, tables and option labels. A citation that supports
  one sentence had its link.

## Alternatives rejected

- **A Stop hook that scans each reply.** It is the only check of replies, but it lives in the
  untracked `.claude/settings.json` and needs a tool with a test. The user chose to try the skill
  first.
- **A commit-msg hook that warns about bare IDs.** Deferred with the Stop hook.
- **A test that scans the tracked Markdown.** The tracked files are almost clean, so it guards a
  place that does not leak.
- **Restate the rule in the skill.** The rule then has two homes. The skill links section 5.

# C3E5 — The skill `ask-the-user` is the one place for the form of a question; an entry that is not pushed can change

**Status:** absorbed into [`ask-the-user/SKILL.md#steps`](../../.claude/skills/ask-the-user/SKILL.md#steps), [`ask-the-user/SKILL.md#the-first-message`](../../.claude/skills/ask-the-user/SKILL.md#the-first-message), [`ask-the-user/SKILL.md#changes-to-rules`](../../.claude/skills/ask-the-user/SKILL.md#changes-to-rules), [`ask-the-user/SKILL.md#the-explanation`](../../.claude/skills/ask-the-user/SKILL.md#the-explanation), [`ask-the-user/SKILL.md#check-before-you-send`](../../.claude/skills/ask-the-user/SKILL.md#check-before-you-send), [`hand-over.md#decision-questions`](../../specs/model-sidecar/model-addition-workflow/hand-over.md#decision-questions), [`change-decision-log`: Rules](../../.claude/skills/change-decision-log/SKILL.md#rules), [`stack-commit/SKILL.md#commit-commands`](../../.claude/skills/stack-commit/SKILL.md#commit-commands), [`brief-subagent/SKILL.md#the-brief`](../../.claude/skills/brief-subagent/SKILL.md#the-brief), [`brief-subagent/SKILL.md#the-result`](../../.claude/skills/brief-subagent/SKILL.md#the-result), [`change-sidecar-spec/SKILL.md#procedure-d-another-spec-edit`](../../.claude/skills/change-sidecar-spec/SKILL.md#procedure-d-another-spec-edit), 2026-11-15 (user; PR: pending).

## Decision

This entry supersedes [ADR-9K2M](9K2M-agent-session-rules.md) in full. Items 1 to 4 replace 9K2M
item 2. Item 5 is new. Item 6 restates 9K2M items 1, 3 and 4 by links.

1. **One place.** The skill [`ask-the-user`](../../.claude/skills/ask-the-user/SKILL.md) is the
   only document that states how a session presents a question, its options or a report to the
   user. Each other document links the skill. It adds only the content that its own questions
   need. [Decision questions](../../specs/model-sidecar/model-addition-workflow/hand-over.md#decision-questions)
   keeps the rules of a proposal question and states no form. This changes item 1 of
   [ADR-3HZ4](3HZ4-decision-questions-and-rule-defaults.md), which made that heading the home of
   the form. [ADR-BQZ9](BQZ9-intake-process-consolidation.md) restates that item by a link.
2. **The first message.** The user must be able to decide from the first message, and "yes"
   accepts the recommendation.
   [The first message](../../.claude/skills/ask-the-user/SKILL.md#the-first-message) states its
   parts and their order: the question, the options, the line `Changes:` and the recommendation.
   The question and the options give the wording of a rule. An entry ID and an item number go only
   in the line `Changes:` and in
   [the explanation](../../.claude/skills/ask-the-user/SKILL.md#the-explanation). The session sends
   the explanation only on request. It holds the file and the line of each fact. 9K2M item 2 put
   them in the question.
3. **Changes to rules.** [Changes to rules](../../.claude/skills/ask-the-user/SKILL.md#changes-to-rules)
   states the form: the wording of today, the word `becomes`, and the new wording in quotation
   marks.
4. **Reports.** [Steps](../../.claude/skills/ask-the-user/SKILL.md#steps) states when a session
   reports and does not ask: the user already made the decision, or item 5 applies. A report starts
   with `FYI —`. A question that depends on an open question waits for the next message.
5. **An entry that is not pushed.** An entry in a commit that is not pushed to a remote can change
   in that commit, in each part. The session makes the correction and reports it. It writes no new
   entry and asks no question. The four edits of the [Rules](../README.md#rules) apply from the
   first push.
6. **Rules that stay.** [Commit commands](../../.claude/skills/stack-commit/SKILL.md#commit-commands),
   [The brief](../../.claude/skills/brief-subagent/SKILL.md#the-brief),
   [The result](../../.claude/skills/brief-subagent/SKILL.md#the-result) and
   [Procedure D](../../.claude/skills/change-sidecar-spec/SKILL.md#procedure-d-another-spec-edit)
   state 9K2M items 1, 3 and 4.

## Reason

A review of 33 questions that sessions asked from 2026-10-25 to 2026-11-12, about a decision that
changes an earlier decision, found these problems. The questions come from the session transcripts.

- The user answered 7 of them with a request for an explanation or with a question.
- Many questions named an entry only by its ID or its title, for example "supersedes ADR-FADS".
  The user reads the wording that changes. The IDs are for agents, so they go on one line.
- The conflict was often in the text of one option, or behind a plan label or a stage number.
- 5 questions asked for a decision that needed none. In 3, the user had already decided. In 2, the
  choice was between a correction of an entry that was not pushed and a new entry that supersedes
  it. The user chose the correction each time.
- 4 questions gave no recommendation.
- The skill and "Decision questions" each stated a form, and the two forms were different.

## Consequences

- A session must write the new wording of a rule before it asks.
- The first message is short. A session prepares the explanation before it asks, so that it is
  ready.
- The Rules get one bullet for item 5. The bootstrap kit takes it through the kit sync.

## Alternatives rejected

- A fixed block that lists the new entry and each earlier entry with a description of fewer than
  15 words. The user found it harder to read than the old questions.
- The context before the options. It makes the first message long, and the user can decide most
  questions from the options.
- A bullet for each option. It uses width and adds nothing to a bold label.

## Open work

[open-work.md](../open-work.md)

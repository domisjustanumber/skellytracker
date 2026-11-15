---
name: ask-the-user
description: Use this skill in skellytracker before you ask the user a question or give the user options to choose from. Use it also in a grilling session, a plan review, a stop point and a decision question, and before you report a rule change that needs no decision.
---

# Ask the user a question

This skill uses ASD-STE100 Simplified Technical English.

The user must be able to decide from the first message alone, and "yes" must be a full answer. Each
question that the user sends back for an explanation costs one more round
([ADR-9K2M](../../../decisions/entries/9K2M-agent-session-rules.md)).

## Steps

1. Find the facts first. Answer each question that the code, the spec or a decision entry answers.
   Open the file that states each fact, and keep its `path:line` for the explanation. Use a
   sub-agent for a fact that is not checked. If no file states a fact, it is your assumption.
2. Report when no decision is open: the user already made it, or the change corrects a rule that is
   committed and not pushed. Correct such a rule in place, with no new entry. A report starts with
   `FYI —` and shows each change in the form of [Changes to rules](#changes-to-rules).
3. Ask each question whose answer changes what you do next. Ask one decision in each question. A
   question that depends on an open question goes in the next message.

## The first message

```markdown
**Q5 — Shall the pipeline timing helper be the public module `core/pipelines/timing.py`?**

**Yes:** freemocap and a notebook can call it on a timing JSONL file.
- "A helper in `core/metrics/` aggregates the events" becomes\
  -> "A helper in `core/pipelines/timing.py` aggregates the events"

**No, skellybench aggregates:** skellytracker writes only the raw events.
- The same sentence\
  -> removed

Changes: [ADR-Q59W](decisions/entries/Q59W-pipeline-timing-and-taps.md) replaced (both).

➡️ **Yes**, because freemocap can then use the helper too.
```

- **Order.** The question, the options, the line `Changes:`, the recommendation. The context goes
  in [the explanation](#the-explanation).
- **Question.** It has a short label, for example `Q5`. Use the same label in each later message.
  Word it so that "yes" accepts your recommendation.
- **Options.** Each option is a paragraph that starts with its label in bold. It states its own
  consequences and one concrete example, with real field names, values and file paths.
- **Content.** In the question and the options, write the wording of a rule, the name of a step and
  the path of a file. An entry ID, an item number, a rule number, a plan label and a stage number go
  only in the line `Changes:` and in the explanation.
- **`Changes:`.** One line with the entries that are new, replaced or changed, as links, and the
  option of each. Load [`cite-entries`](../cite-entries/SKILL.md) for it.
- **Recommendation.** Each question has one. It is the last line: `➡️`, then your answer with its
  first word in bold and a capital letter, then the reason.
- **Lists.** Two or more facts of one kind are a list. Entries that do not change are one line of
  links.

## Changes to rules

- Each rule that changes is a bullet. It gives the wording of today in quotation marks, copied from
  the file, then the word `becomes` and a line break. The next line is `-> "<new wording>"`,
  exactly as you will write it.
- A rule that goes has no `becomes`. Its next line is `-> removed`.
- For an addition, the bullet ends with `adds`. Each added part is a quoted bullet below it that
  starts with `...`.
- A new rule is the rule itself, in quotation marks.
- An option that changes no rule says "No rule changes."

## The explanation

Send the explanation only when the user asks for it. It gives the sentence of each entry with its
item number and `path:line`, the rules that stay, one worked example, each size or count, and each
assumption.

## Check before you send

The user can answer "yes" from the first message. Each option is complete without the explanation.
Each new wording is in quotation marks. No entry ID is outside the line `Changes:`.

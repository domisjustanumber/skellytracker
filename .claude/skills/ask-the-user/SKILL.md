---
name: ask-the-user
description: Use this skill in skellytracker before you ask the user a question or give the user options to choose from. Use it also in a grilling session, a plan review, a stop point and a decision question.
---

# Ask the user a question

This skill uses ASD-STE100 Simplified Technical English.

The user must be able to decide from your message alone. Each question that the user sends back
for an explanation costs one more round
([ADR-9K2M](../../../decisions/entries/9K2M-agent-session-rules.md)).

## Steps

1. Answer each question that the code, the spec or a decision entry answers. Ask only the
   questions whose answer changes what you do next.
2. Check each fact that the question starts from. Open the file that states it. Write its
   `path:line`, for example `specs/pipeline/running.md:46`. If no file states the fact, write that
   it is your assumption.
3. Give each question a short label, for example `Q4` or `B12`. Use the same label in each later
   message.
4. Name the subject in full. Write what a plan step, an item number or a short name is in the same
   sentence, for example "step 5, the MediaPipe measurement entry".
5. Give one concrete example for each option. Use real field names, values and file paths of this
   repository. Show what changes for a user of the package or for a reader of the spec.
6. Give your recommendation and its reason as the last line of the question.
7. Load [`cite-entries`](../cite-entries/SKILL.md) when the question names a decision entry.

## Check before you send

Each question has a label, a subject in full, an example for each option, a `path:line` or the
word "assumption" for each fact, and a recommendation.

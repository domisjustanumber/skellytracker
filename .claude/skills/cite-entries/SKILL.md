---
name: cite-entries
description: Use this skill in skellytracker before you send a reply, or write a plan, a PR body or a commit message, that names a decision entry. Use it also for a list, a table, an option or a summary that names entry IDs.
---

# Cite decision entries

This skill uses ASD-STE100 Simplified Technical English.

[Section 5](../../../AGENTS.md#5-decision-log) of `AGENTS.md` holds the citation rule. The
[Rules](../../../decisions/README.md#rules) give the places that hold the bare ID: a file name, a
heading, an index row and a status line. This skill gives the steps to apply the rule when you write
([ADR-VCQ7](../../../decisions/entries/VCQ7-cite-entries-skill.md)).

No hook or test checks the citations of a reply or a commit message. The user decides on a hook
when this skill is not enough.

## Forms

| Where | Form |
|---|---|
| A reply, a plan, a PR body or a tracked file | `[ADR-5EVP](decisions/entries/5EVP-absorb-across-documents.md)` |
| A commit subject that adds or changes an entry | It ends with `(ADR-5EVP)`. |
| A commit body | `ADR-5EVP`, with no link |
| A file name or a path, also a proposed one | The bare ID, for example `decisions/evidence/5EVP-absorb-map.md` |
| An entry of another repository | The form of section 5 |

In a reply or a plan, the link path starts at the repository root. In a tracked file, it is relative
to that file.

## Steps

1. Treat each entry ID that you write as a citation. An ID that names an option, a verdict, a group,
   a commit or the subject of a sentence is also a citation.
2. In a list of IDs, make each ID a link. Write "Root log:
   `[ADR-R39S](decisions/entries/R39S-test-fix-on-the-working-branch.md)`, …". Do not write "Root
   log: R39S, 6G6G".
3. In a table, make each ID cell a link. Do not use a bare ID as a row label.
4. Find the file name with Glob before you write the link. Do not guess the slug. Root-log entries
   are in `decisions/entries/`. Spec-log entries are in `specs/model-sidecar/decisions/entries/`.
5. A path is not a citation. Keep the bare ID in a file name. When the same sentence names the
   entry, cite the entry with a link in that sentence.
6. In a commit message, write `ADR-<ID>` with no link. Do not write a bare ID.

## Check before you send

1. Find each token of four digits and letters in the draft.
2. For each token that is an entry ID, make sure that it is in a link, in a path or in the
   `ADR-<ID>` of a commit message.
3. Change each other token to a link.
4. Check the tables, the option lists and the last paragraph again. Bare IDs occur most in these
   places.

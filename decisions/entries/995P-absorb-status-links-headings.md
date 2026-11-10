# 995P — An absorbed status links the headings that state the rules

**Status:** absorbed into [`decisions/README.md#rules`](../README.md#rules), [`check_decision_log.py`](../../tools/check_decision_log.py), [`change-sidecar-spec/SKILL.md#procedure-b-land-an-accepted-proposal`](../../.claude/skills/change-sidecar-spec/SKILL.md#procedure-b-land-an-accepted-proposal), 2026-11-10 (user; PR: pending).

## Decision

This entry supersedes no entry. It makes item 2 of
[ADR-5EVP](5EVP-absorb-across-documents.md) more exact. The other items of 5EVP stay.

1. **One link for each heading.** The status `absorbed into` has one link for each heading that
   states a rule of the entry. A heading gets one link, also when it states two or more rules. A
   file gets a link with no anchor only when the rule is not under a heading, for example in a tool
   docstring or a YAML file.
2. **Too long.** When the status paragraph is longer than `STATUS_EXEMPTION_LIMIT`, the headings of
   one file become the title heading of that file, first for the file with the most links. If the
   paragraph is still too long, the files of one document become the title heading of its main
   file: the workflow `README.md`, the spec `README.md` or the `SKILL.md` of a skill. The entry
   stays absorbed.
3. **Repairs.** A commit that renames a heading repairs each status link to that heading. A change
   from a file link to heading links is a link repair.
4. **The check.** [`check_decision_log.py`](../../tools/check_decision_log.py) reports an
   `absorbed into` link or code span to a Markdown file with no `#anchor`. A title heading
   satisfies the check, so each status can pass.
5. **Step 19.** Step 19 of Procedure B of
   [`change-sidecar-spec`](../../.claude/skills/change-sidecar-spec/SKILL.md) links the Rules. It no
   longer says "use the heading that states the main rule".
6. **The statuses of 6927be5.** The 17 statuses of that commit that linked a Markdown file with no
   anchor now link the headings. They were written in this PR, so the change needs no `_Edited`
   line.

## Reason

- The user, 2026-11-10: per-heading statuses, and a skill wording review "to tighten this up and
  ensure it happens where possible".
- With item 2 of 5EVP, the status of [ADR-JAA4](JAA4-one-batch-field.md) linked only the spec
  `README.md`. Its `output_shapes` rule is under one heading of `common/sizes-and-artifacts.md`.
- Step 19 of `change-sidecar-spec` was a second home of the status form, and it disagreed with the
  Rules.
- The review proposed that an entry that does not fit stays `accepted`. That undoes an absorb for a
  long status only. The title-heading steps always fit: the longest status of the 17 has 1,803
  characters.

## Alternatives rejected

- **A link for each heading with no limit.** [ADR-0QKK](0QKK-no-legacy-layer.md) has about 25
  headings, and its status would pass `STATUS_EXEMPTION_LIMIT`.
- **Keep item 2 of 5EVP.** A status can then name only the documents, and a reader must search for
  the rule.
- **The entry stays `accepted` when its status is too long.** It keeps a stated entry on the read
  path.

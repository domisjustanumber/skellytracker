# JW9N — Restate a kept rule by a link

**Status:** accepted, 2026-10-28 (user; PR: pending).

## Decision

This entry supersedes [ADR-NGNB](ngnb-supersede-an-absorbed-entry.md) and
[ADR-HJNP](HJNP-upper-case-entry-ids.md) in full. Items 1 to 3 are new. Item 1 changes the
complete-restatement rule of ngnb item 2 and HJNP item 5. Item 4 restates the other rules of both
entries by a link, as item 1 allows. This entry applies to itself.

1. **Restatement by a link.** A new entry must restate each rule of the old entry that stays. A link
   can restate a rule. The link must go to a heading that states the rule. The heading must be in a
   document of the absorb rule of the [Rules](README.md#rules): the spec, the root or a nested
   `AGENTS.md`, the skills, the model addition workflow, the exporter guide, the templates of
   `specs/model-sidecar/templates/`, or the Rules with `template.md`. The commit group that adds the
   entry must make sure that the heading states the rule. If the heading does not state the rule,
   add the missing text under the heading first. Then that document is the only source of the rule.
   A restatement in full stays allowed.
2. **A later change of the document.** A later entry can change the text under a heading that an
   entry links. The commit that changes the text cites the later entry next to the changed rule, as
   `(ADR-<ID>)`. The later entry does not supersede the linking entry.
3. **The chain rule.** An entry can restate a rule by a link to a heading of a document of the absorb
   rule. A later entry can change the text under that heading. The later entry cites itself at the
   heading. It does not supersede the linking entry. A later entry that changes a rule that the
   linking entry states in its own text supersedes the linking entry in full.
4. **The rules that stay.** The [Rules](README.md#rules) state ngnb items 1 and 3 to 5, HJNP items 1
   to 4 and 6 to 9, and the parts of ngnb item 2 and HJNP item 5 that item 1 does not change. Both
   entries were absorbed into the Rules before this entry. This includes the full 40-character SHA,
   the move of the prefix and the record-again details of HJNP item 8.
5. **The kit.** The bootstrap kit takes items 1 to 3. Its decision-log Rules and its guide state
   them. A later change of these rules also changes the kit by hand, in the same commit group.

## Reason

- Under ngnb item 2, a change of one rule of an absorbed entry supersedes it in full, and the new
  entry restates each rule that stays. Some absorbed entries are much larger than the limit of 6,000
  characters for an entry. A full restatement of them cannot pass the doc tests.
- An absorbed entry already makes its document the source of its rules. A full copy of these rules
  in a new entry makes a second source.
- Without item 3, each later edit of a linked heading supersedes the linking entry. Then a chain of
  supersessions forms for rules that did not change.

## Consequences

- The text under a linked heading is normative. An edit of it must cite its entry.
- A reader of an entry follows the link to read the rule. The rule text is not in the entry.

## Alternatives rejected

- **A `supersedes-<id>.md` file in a proposal folder.** It copies the rules a second time.
- **A consolidation entry.** It has the same size problem.
- **Keep the old entries `absorbed`, with no supersession.** The old entry then points to a document
  that no longer states its rule. ngnb gives this reason.

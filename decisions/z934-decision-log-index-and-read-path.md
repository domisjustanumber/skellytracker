# z934 — Index and read path: a Proposed table, `historical.md`, `template.md` and `done`

**Status:** absorbed into [`decisions/README.md#rules`](README.md#rules), 2026-10-25 (user; the absorption review).

## Decision

This entry supersedes [0035](0035-decision-log-limits.md) in full. It restates the rules of 0035
that stay. 0035 and [0029](0029-decision-log-read-path.md) keep the reasons for those rules.

1. **Read path.** An agent reads [`README.md`](README.md) and [`open-work.md`](open-work.md). Then it
   reads the Active entries that apply to its task. It reads a Proposed entry only for spec work in
   the section of that entry, or when a skill tells it to. It reads an entry of
   [`historical.md`](historical.md) only to find the reason for a decision.
2. **Tables and status forms.** The Status cell has only one of these forms. Free text after a status
   is not allowed.

   | Table | File | Status forms |
   |---|---|---|
   | Active | `README.md` | `accepted`, `evidence` |
   | Proposed | `README.md` | `proposed` |
   | Historical | `historical.md` | `evidence; used by XXXX`, `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`, `done` |

   `XXXX` must be an entry that is not `proposed` or `rejected`. The Decision cell has 160 characters
   or fewer. The Deferred table and its 183-day rule go: off the read path, a Deferred table and the
   Proposed table differ only by age.
3. **Section cell.** A Proposed row has the cells `| # | Decision | Section | Status |`. Section is the
   section ID of the change in backticks, or `none`. A new section ID is allowed.
4. **Used evidence.** An `evidence` entry gets `evidence; used by XXXX` when an accepted entry cites
   it for its decision. Its row moves to Historical. Its Decision cell keeps the one-line result.
5. **Absorbed status.** An accepted entry is absorbed when one of these documents states all of its
   rules: the spec, `AGENTS.md`, the skills, the exporter guide, the templates of
   `specs/sidecar/templates/`, and the Rules of `README.md` with [`template.md`](template.md). Change
   the status line to `absorbed into <path>#<anchor>`, with the date and the PR. Do not change the
   body.
6. **Done status.** An accepted entry that records a one-off action, with no rule that stays, gets
   `done` when the action is complete. The status line gives the date and the PR.
7. **Consolidation entries.** A consolidation entry states the rules that stay from a group of
   entries. It supersedes each entry of the group, and it changes no decision. Write one at the end
   of the spec-build stage ([0014](0014-spec-lifecycle.md)), and when the read-path limit fails.
8. **Open work.** The open work and the spec defects are in `open-work.md`. Delete an item when its
   work is done, or when the content PR of a spec defect lands.
9. **Template.** The entry template and its notes are in `template.md`. It is not in the read path.
10. **Limits.** [`tools/check_decision_log.py`](../tools/check_decision_log.py) counts characters
    after it changes CRLF to LF.

    | Limit | Characters | Applies to |
    |---|---|---|
    | Index | 18,000 | `README.md` |
    | Open work | 20,000 | `open-work.md` |
    | Entry | 6,000 | each entry after 0025 |
    | Read path | 330,000 | `README.md`, `open-work.md` and the Active entries |

    Entries 0001 to 0025 keep their length. Put long evidence in a tracked file next to the entry,
    and link to it. A PR can lower a limit. A PR that raises a limit must add a decision entry. After
    the first consolidation, lower the read-path limit to 160,000 characters.
11. **Warnings.** The tool prints a warning when the index, the open work or the read path is at 80%
    of its limit or more. A warning does not fail the doc tests. An entry does not warn.
12. **Checks.** The tool checks the rows, the tables, the cells, the status forms, the `XXXX` of each
    status and the limits. The doc tests run it.
13. **Exporter guide.** The exporter guide is normative for the workflow. The sidecar spec is
    normative for the meaning of a sidecar. The guide does not change the meaning of the spec.
14. **Bootstrap kit.** The kit takes these rules. Its copy of the tool keeps the limits of 0029: 14,000
    for the index and 220,000 for the read path ([0031](0031-bootstrap-kit.md)).

## Reason

- On 2026-10-25, after the record of the exporter proposals, the read path was 290,476 of 330,000
  characters. The 21 `proposed` entries held 102,370 of them. One batch of proposals added about
  76,000. Each later batch adds the same.
- A `proposed` entry is not a rule yet. Until a content PR lands it, the spec text applies. An agent
  that does other work does not need it. `propose-sidecar-change` already tells an agent to read the
  `proposed` entries of its section.
- The gap records 0017, 0018, 0019 and 0023 have no proposal folder. The Section cell lets an agent
  find them by section.
- An agent does not need the Historical rows or the template for a task.
- 0035 named only the spec, `AGENTS.md` and the skills as normative. About 40 rules of 0013 and 0014
  are only in the exporter guide and the templates, and the log rules are in the README. So these
  entries could not be absorbed, and each rule was on the read path two or three times.
- A one-off action, for example the move of a folder, has no rule that stays. Without `done`, its
  entry stays Active.

## Consequences

- An agent that does not follow `propose-sidecar-change` can miss a pending proposal of its section.

## Alternatives rejected

- **A cap on the length of a `proposed` entry.** It makes each proposal smaller, but the total still
  grows with each batch.
- **Keep the Deferred table.** Off the read path, it adds a table, a rule and a check, and gives no
  benefit.
- **Higher limits again.** 0026, 0029 and 0035 changed the limits in three days. The cause was the
  content of the read path, not the limits.

_Edited 2026-10-28 (this PR): link repair._

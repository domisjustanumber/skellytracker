# 0029 — Read path, Deferred proposals, status forms and the open-work file

**Status:** accepted, 2026-10-24 (user).

## Decision

This entry supersedes [0026](0026-decision-log-size.md) in full
([0028](0028-entry-edits-and-citations.md)). It restates the rules of 0026 and adds new rules. 0026
keeps the reasons and the evidence for the rules that stay.

1. **Read path.** The index in [`README.md`](README.md) has three tables: Active, Deferred and
   Historical. An agent reads `README.md` and [`open-work.md`](open-work.md). Then it reads the
   Active entries that apply to its task. It reads a Deferred entry only for spec work in the area
   of that entry. It reads a Historical entry only to find the reason for a decision.
2. **Status forms.** The Status cell of an index row is one of these forms. Free text after a status
   is not allowed.

   | Table | Status forms |
   |---|---|
   | Active | `proposed`, `accepted`, `evidence` |
   | Deferred | `proposed` |
   | Historical | `evidence; used by NNNN`, `rejected`, `superseded by NNNN`, `absorbed into <path>#<anchor>` |

   `NNNN` must be an entry of the index that is not `proposed` or `rejected`. The Decision cell has
   160 characters or fewer.
3. **Deferred proposals.** A `proposed` row moves from Active to Deferred when the latest date in the
   status line of its entry is more than 183 days old. The status stays `proposed`. A row goes back
   to Active when the entry changes and its status line gets a new date.
4. **Used evidence.** An `evidence` entry gets the status `evidence; used by NNNN` when an accepted
   entry cites it for its decision. Its row moves to Historical. Its Decision cell keeps the
   one-line result.
5. **Absorbed status.** An accepted entry is absorbed when a normative document states all of its
   rules. The normative documents are the spec, `AGENTS.md` and the skills. Change the status line
   to `absorbed into <path>#<anchor>`, with the date and the PR. Do not change the body. The
   document is then the source of the rules. The entry is the record of the reasons.
6. **Consolidation entries.** A consolidation entry states the rules that stay from a group of
   entries. It supersedes each entry of the group, and it changes no decision. Write one at the end
   of the spec-build stage ([0014](0014-spec-lifecycle.md)), and when the read-path limit fails.
7. **Open work.** The open work, the repository state and the spec defects are in
   [`open-work.md`](open-work.md). Delete an item when its work is done, or when the content PR of a
   spec defect lands. The PR that closes an item records the result.
8. **Limits.** [`tools/check_decision_log.py`](../../tools/check_decision_log.py) counts characters
   after it changes CRLF to LF.

   | Limit | Characters | Applies to |
   |---|---|---|
   | Index | 14,000 | `README.md` |
   | Open work | 20,000 | `open-work.md` |
   | Entry | 6,000 | each entry after 0025 |
   | Read path | 220,000 | `README.md`, `open-work.md` and all Active entries |

   Entries 0001 to 0025 keep their length. Put long evidence in a tracked file next to the entry,
   and link to it. A PR can lower a limit. A PR that raises a limit must add a decision entry. After
   the first consolidation, lower the read-path limit to 160,000 characters.
9. **Warnings.** The tool prints a warning when the index, the open work or the read path is at 80%
   of its limit or more. A warning does not fail the doc tests. An entry does not warn, because its
   body does not change after the decision.
10. **Checks.** The tool checks that each entry file has one index row, that each row links to an
    entry file, and that each Status cell has a form of its table. It checks the `NNNN` of each
    status, the Decision cells, the Deferred rule and the limits.
    [`tools/tests/test_decision_log.py`](../../tools/tests/test_decision_log.py) runs the tool in
    the doc tests.
11. **First review.** Examine the accepted entries 0001 to 0016. Mark each entry that a normative
    document states in full as absorbed.

Mirror: OpenMMLab-Exporter 0040 (planned).

## Reason

- On 2026-10-24, the read path is 203,879 of 220,000 characters (93%). The 0026 check fails only at
  100%. A warning at 80% gives time for a review before a PR fails.
- The open-work list had 13,316 of the 23,461 characters of `README.md`. A task needs only some of its
  items. In its own file, it has its own limit, and the index stays small.
- Nine of the 25 Active entries (0017 to 0025) are proposals. A proposal that waits for a long time
  costs read-path characters in each session.
- An `evidence` entry records a measurement. When a decision uses the measurement, the decision
  gives the result that agents need.
- Free text in a Status cell grows. In OpenMMLab-Exporter, a status cell names up to four other
  entries. The status forms keep the cross-references in the entries.

## Consequences

- The index limit is 14,000, not 10,000: the index without the open work has about 10,100
  characters.
- The links of entries and of the spec to `README.md#open-work` resolve to a heading that points to
  `open-work.md`. Agents follow one more link.
- The Deferred check depends on the date of the test run. A proposal can fail a PR that does not
  touch it. The fix is one row move.

## Alternatives rejected

- **Open work as GitHub issues.** Agents can read a tracked file offline, and the link check covers
  it.
- **A warning for an old proposal, not a failure.** A warning that does not fail is easy to ignore.

# 0035 — Higher index and read-path limits for the decision log

**Status:** superseded by [z934](z934-decision-log-index-and-read-path.md), 2026-10-25 (user).

## Decision

This entry supersedes [0029](0029-decision-log-read-path.md) in full. It restates the rules of 0029
and changes two limits. 0029 keeps the reasons for the rules that stay.

1. **Read path.** The index in [`README.md`](../README.md) has three tables: Active, Deferred and
   Historical. An agent reads `README.md` and [`open-work.md`](../open-work.md). Then it reads the
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
   to `absorbed into <path>#<anchor>`, with the date and the PR. Do not change the body.
6. **Consolidation entries.** A consolidation entry states the rules that stay from a group of
   entries. It supersedes each entry of the group, and it changes no decision. Write one at the end
   of the spec-build stage ([0014](0014-spec-lifecycle.md)), and when the read-path limit fails.
7. **Open work.** The open work, the repository state and the spec defects are in
   [`open-work.md`](../open-work.md). Delete an item when its work is done, or when the content PR of a
   spec defect lands. The PR that closes an item records the result.
8. **Limits.** [`tools/check_decision_log.py`](../../tools/check_decision_log.py) counts characters
   after it changes CRLF to LF.

   | Limit | Characters | Applies to |
   |---|---|---|
   | Index | 18,000 | `README.md` |
   | Open work | 20,000 | `open-work.md` |
   | Entry | 6,000 | each entry after 0025 |
   | Read path | 330,000 | `README.md`, `open-work.md` and all Active entries |

   Entries 0001 to 0025 keep their length. Put long evidence in a tracked file next to the entry,
   and link to it. A PR can lower a limit. A PR that raises a limit must add a decision entry. After
   the first consolidation, lower the read-path limit to 160,000 characters.
9. **Warnings.** The tool prints a warning when the index, the open work or the read path is at 80%
   of its limit or more. A warning does not fail the doc tests. An entry does not warn.
10. **Checks.** The tool checks that each entry file has one index row, that each row links to an
    entry file, and that each Status cell has a form of its table. It checks the `NNNN` of each
    status, the Decision cells, the Deferred rule and the limits.
    [`tools/tests/test_decision_log.py`](../../tools/tests/test_decision_log.py) runs the tool in
    the doc tests.
11. **Bootstrap kit.** The kit copy of the tool
    (`specs/agents-and-adr-process/bootstrap/tools/check_decision_log.py`) keeps the limits of 0029:
    14,000 for the index and 220,000 for the read path. `tools/sync_bootstrap_kit.py` applies this
    edit ([0031](0031-bootstrap-kit.md)).

## Reason

- On 2026-10-25, the index is 13,712 of 14,000 characters (98%), and the read path is 209,186 of
  220,000 (95%).
- The OpenMMLab-Exporter and MediaPipe-Exporter proposals need one `proposed` entry for each spec
  change, five completed gap records (0020, 0021, 0022, 0024 and 0025) and the entries that the
  proposals supersede on acceptance. This adds about 2,000 characters to the index and about
  100,000 to the read path.
- A `proposed` entry does not supersede an entry until the user accepts it. So the recording frees
  no characters.
- Rotation cannot free the space. Each entry keeps its index row in `README.md`, also in Historical.
  0013, 0014 and 0016 hold about 71,000 read-path characters, and the first review of 0029 found
  rules that only these entries state. A consolidation entry after 0025 has the 6,000 limit, so it
  cannot restate them.
- A new repo starts with an empty log, so the kit keeps the lower limits.

## Consequences

- An agent reads more characters for each task until the proposals are decided.
- The consolidation at the end of the spec-build stage becomes more important.

## Alternatives rejected

- **A separate index for `proposed` entries, off the read path.** It changes the read path of every
  agent. The user chose higher limits.
- **An archive file for Historical rows.** It frees about 1,000 characters of the index and no
  read-path characters.
- **A consolidation entry first.** The 6,000 limit of a new entry cannot hold the rules of 0013,
  0014 and 0016.

_Edited 2026-10-28 (this PR): link repair._

_Edited 2026-10-29 (this PR): link repair._

# Z05A — Essential decision-log Rules

**Status:** accepted, 2026-10-29 (user; PR: pending).

## Decision

This entry supersedes [ADR-Z934](z934-decision-log-index-and-read-path.md),
[ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md),
[ADR-NSR2](NSR2-adr-citations-as-links-in-each-text.md) and [ADR-0031](0031-bootstrap-kit.md) in
full. Item 1 removes rules. Items 6 and 7 change rules. Items 2 to 5 restate the other rules of
these entries by links.

1. **Essential Rules.** The [Rules](../README.md#rules) of the index state only the rules that an agent
   needs and that no tool and no loaded document states. A rule that a tool checks with a clear
   message, a rule that `AGENTS.md` or a skill states, and a description leave the Rules. A rule
   that an agent follows with no sentence is removed: no document states it after this entry. The
   [cut list](../evidence/Z05A-rules-cut-list.md) gives each removed unit and its class.
2. **The sources of the rules that leave.**
   - The read path, the placement of an entry, one entry for each decision, the `--new` ID, the
     citation forms, the commit subject and `plans/`: the intro of the index,
     [`AGENTS.md#5-decision-log`](../../AGENTS.md#5-decision-log) and
     [`AGENTS.md#6-git-rules`](../../AGENTS.md#6-git-rules).
   - Proposals, gaps and a new version of a recorded proposal: the skill
     [`propose-sidecar-change`](../../.claude/skills/propose-sidecar-change/SKILL.md) and
     [`specs/model-sidecar/AGENTS.md`](../../specs/model-sidecar/AGENTS.md).
   - The tables, the status forms, the Decision and Section cells, the ID alphabet, the collision
     order and the size limits: [`tools/check_decision_log.py`](../../tools/check_decision_log.py). The
     full-SHA permalink: [`tools/check_links.py`](../../tools/check_links.py). A tool is the source of
     a rule that it checks. The Rules add the docstring of a tool to the absorb documents.
3. **Z934 and JW9N.** The intro of the index and
   [`AGENTS.md#5-decision-log`](../../AGENTS.md#5-decision-log) state the read path of Z934. The
   workflow README states that the workflow is normative. The kit tool states the kit limits. The
   [Rules](../README.md#rules) state the absorb documents, the restatement by a
   link, the citation of the changing entry and the status changes. The chain rule of JW9N item 3
   stays: a later entry that changes the text under a linked heading does not supersede the linking
   entry. JW9N item 4 restated rules of [ADR-NGNB](ngnb-supersede-an-absorbed-entry.md) and
   [ADR-HJNP](HJNP-upper-case-entry-ids.md). Item 2 above gives their sources now.
4. **NSR2.** [`AGENTS.md#5-decision-log`](../../AGENTS.md#5-decision-log) states NSR2 items 1 to 4.
   The Rules state the provisional-entry form of item 4 and the parts of item 5 that an agent needs.
   The relative-path form of item 2 is a removed default (cut unit R103). The older forms of item 5
   stay valid. A tool accepts them.
5. **0031.** [`AGENTS.md#5-decision-log`](../../AGENTS.md#5-decision-log) and
   [Keep the kit current](../../specs/agents-and-adr-process/README.md#keep-the-kit-current) state 0031
   items 1 to 5, with `--check`, the doc tests and kit entry 0001.
6. **The kit.** The kit templates take the same Rules, the same sections 5, 7 and 8 of `AGENTS.md`,
   and the shared rules of its other sections. A shared rule outside these sections is between the
   lines `<!-- kit:<name> -->` and `<!-- /kit -->` in the live file and in the template.
   [`tools/sync_bootstrap_kit.py`](../../tools/sync_bootstrap_kit.py) writes these blocks from the live
   files, with the text edits that it lists. It removes each citation of a single live entry.
   `--check` fails when a block differs. The decision-log `template.md` becomes a copy.
   [`AGENTS.md#5-decision-log`](../../AGENTS.md#5-decision-log) also states the module-log rules of
   [ADR-GN3D](GN3D-module-decision-logs.md) and the tool and script rules of
   [ADR-EY8R](EY8R-tools-and-scripts.md), so the kit gets them. The kit keeps no rule that
   skellytracker does not state. This replaces "by hand" in 0031 item 6, JW9N item 5 and NSR2 item
   7. Change the rest of a kit template by hand in the same commit group.
7. **Entry limit.** The size limit of an entry does not count its status paragraph: the lines from
   `**Status:**` to the next blank line or heading, up to 1,000 characters. A status change then
   never makes a full entry too long. The docstring of `tools/check_decision_log.py` states this.

## Reason

- The Rules had 11,740 of the 17,193 characters of the index. The index limit is 18,000.
- Most rules were also in `AGENTS.md`, in a skill or in a tool message. An agent read them twice.
  Two copies drift.
- A rewording that kept each rule saved only 605 characters.
- The kit templates drifted from the live Rules when they were changed by hand (NSR2).

## Consequences

- The Rules are about 3,700 characters. The index is about 9,200 characters.
- An agent learns a tool-checked rule from the tool message when it breaks the rule.
- A change of a tool check is a change of a rule. It needs an entry, as before for the limits.

## Evidence

- A ledger split the Rules at commit `2ff24e4` into 150 units. Four agents classified each unit.
  Four skeptics tried to put each cut back with a failure scenario. A fresh reviewer checked the
  result ([cut list](../evidence/Z05A-rules-cut-list.md)). Of the 150 units, 28 stay. 65 are in another loaded document, 25 have a tool check, 14
  change no behaviour and 18 are descriptions. The reviewer added back the date rule of a status
  change and the tool bullet.

## Alternatives rejected

- **Reword and keep each rule.** It saved 5%.
- **Move the Rules to their own file.** The user decided that the Rules stay in the index.
- **Raise the index limit.** The duplicates stay, and they drift.

_Edited 2026-10-29 (this PR): link repair._

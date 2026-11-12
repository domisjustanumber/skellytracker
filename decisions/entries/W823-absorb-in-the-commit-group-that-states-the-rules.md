# W823 — Absorb each entry in the commit group that states its rules; restate kept rules by link

**Status:** accepted, 2026-11-12 (user).

## Decision

1. **Absorb at landing, for each entry.** The commit group that writes or lands an entry, or that
   writes the rules of an entry into the absorb documents, absorbs the entry in its last commit when
   the absorb documents state all of its rules. This applies in each log, in each skill and in a
   session that uses no skill. If an absorb document does not state a rule, the entry stays
   `accepted`, and the session does not ask the user. This widens item 1 of
   [ADR-3AM0](3AM0-absorb-at-landing-and-landed-copies.md), which
   [ADR-BQZ9](BQZ9-intake-process-consolidation.md) restates. Step 19 of Procedure B of
   `change-sidecar-spec` stays as one case of this rule.
2. **The homes.** The [Rules](../README.md#rules) state item 1. These places apply it: "Commit
   groups" of the skill `stack-commit`, which each session loads before a commit; step 19 and the
   rows for a user decision and a workflow change of `change-sidecar-spec`; Procedures B and D of
   `change-pipeline-spec`; and [template.md](../template.md).
3. **Restate by link.** An entry that supersedes an old entry links the heading that states each
   kept rule. It writes text only for a changed rule and for a kept rule that no heading states.
4. **The spec in the absorb list** is the sidecar spec and the pipeline spec.
5. **Package docstrings.** From the implementation stage, the docstring of a public module of the
   package is an absorb document for the rules of the API of that module. Until then, the
   implementation-stage entries stay `accepted`. The consolidation entry at the end of the spec-build
   stage shortens them.

## Reason

- The read path grew from 50,977 characters on 2026-11-10 to 141,139 on 2026-11-12. The only
  absorb step covered the landing of a spec proposal. The entries of user decisions, workflow
  changes, pipeline landings and plan sessions stayed Active after their rules were in skills and
  workflow files. The only other trigger was the sweep at 90% of the limit, which comes late.
- The user, on 2026-11-12: improve the rule "so it doesn't get missed". Each session loads
  `stack-commit` before a commit, also a session that uses no other skill.
- Supersede chains restated whole entries in text. For example, ADR-ZYS9 changed one item and
  restated seven that `specs/pipeline/running.md` states.
- The user chose on 2026-11-12 to keep implementation-stage design in entries until the code exists,
  and then to absorb it into the package docstrings.

## Evidence

- `read_path_size` of `tools/check_decision_log.py` on trees made with `git archive` at the commits
  of 2026-11-10 (end of the absorb sweep), 2026-11-11 and 2026-11-12: 50,977, 101,395, 121,242 and
  141,139 characters.
- A read-only review of 2026-11-12 found 16 Active entries whose rules the absorb documents state,
  or state after a one-line edit: about 60,000 characters.

## Alternatives rejected

- **Keep the sweep at 90% as the only trigger.** It lets the read path grow by about 90,000
  characters in two days.
- **Make the implementation plan an absorb document.** [ADR-5EVP](5EVP-absorb-across-documents.md)
  item 3 rejects it. The plan mixes rules with dated status, and the user can delete it.
- **A package API document now.** It must stay in sync with code that does not exist yet.

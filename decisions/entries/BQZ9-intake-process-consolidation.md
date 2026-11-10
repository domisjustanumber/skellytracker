# BQZ9 — Consolidation of the intake-process entries

**Status:** absorbed into [`AGENTS.md#sidecar-rules`](../../specs/model-sidecar/AGENTS.md#sidecar-rules), [`change-sidecar-spec/SKILL.md`](../../.claude/skills/change-sidecar-spec/SKILL.md), [`templates/change-proposal.md#7-exporter-impact`](../../specs/model-sidecar/templates/change-proposal.md#7-exporter-impact), [`model-addition-workflow/README.md`](../../specs/model-sidecar/model-addition-workflow/README.md), [`README.md`](../../specs/model-sidecar/README.md), [`propose-sidecar-change/SKILL.md`](../../.claude/skills/propose-sidecar-change/SKILL.md), [`author-sidecar/SKILL.md`](../../.claude/skills/author-sidecar/SKILL.md), [`tools/intake_bundle.py`](../../tools/intake_bundle.py), [`decisions/README.md#rules`](../README.md#rules), 2026-11-10 (user; PR: pending).

## Decision

This entry supersedes [ADR-C0YD](C0YD-the-part-7-row-is-the-re-export-request.md),
[ADR-3HZ4](3HZ4-decision-questions-and-rule-defaults.md),
[ADR-FM0B](FM0B-one-response-for-each-commit-group.md),
[ADR-3AM0](3AM0-absorb-at-landing-and-landed-copies.md) and
[ADR-37CD](37CD-retro-follow-up-session-rules.md) in full. It changes no decision. "The workflow" is
the [model addition workflow](../../specs/model-sidecar/model-addition-workflow/README.md#model-addition-workflow).
"The skill" is [`change-sidecar-spec`](../../.claude/skills/change-sidecar-spec/SKILL.md).

1. **C0YD.** A spec change has no class. It applies to each sidecar from the commit that lands it.
   The package sidecars stay outside the spec until they migrate
   ([One reading](../../.claude/skills/change-sidecar-spec/spec-edit-rules.md#one-reading)). The
   part 7 `needs-export` row of an accepted proposal is the request for a new export. A user ruling
   can name an example with no rebuild: part 7 gives it `removed (user ruling)`, and each content
   commit that makes it invalid removes it. Its models stay in scope until an entry removes them.
   The spec-forced edits, the graph read and the impact run stay
   ([When a spec change makes an example invalid](../../specs/model-sidecar/model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid)
   steps 3, 4 and 12; [Re-export requests](../../specs/model-sidecar/model-addition-workflow/hand-over.md#re-export-requests);
   [7. Exporter impact](../../specs/model-sidecar/templates/change-proposal.md#7-exporter-impact)).
   The 0009 rules are in [Behaviour](../../specs/model-sidecar/pre/normalization.md#behaviour). On
   2026-11-09, the user ruled that `rtmdet-person`, `rtmo-body7`, `yolo26` and `yolo26-body` get no
   rebuild. Each example entry of `inventory.yaml` has `bundle` and `kind: export`, and
   `tools/intake_bundle.py` checks it.
   [ADR-VV8B](VV8B-fragments-have-an-inventory-entry.md) replaces the package-copy sentence of C0YD.
2. **3HZ4.** [Decision questions](../../specs/model-sidecar/model-addition-workflow/hand-over.md#decision-questions)
   states the form of a question, the approvals in the same message and "a rule decides first".
   [Independence](../../specs/model-sidecar/model-addition-workflow/sidecar-files.md#independence)
   states the independence rule. The defaults are in the skill: a landing with no text change is
   non-spec (Procedure B step 2); an `expect` change within `FILE_TOLERANCE` and the `compare`
   tolerance of a listed case is not a stop (steps 9 and 13). A bundle with no finding is recorded
   with no question ([Step 2](../../.claude/skills/propose-sidecar-change/SKILL.md#step-2-get-the-proposal)).
3. **FM0B.** [Session steps](../../specs/model-sidecar/model-addition-workflow/hand-over.md#session-steps)
   steps 2 and 6, [States](../../specs/model-sidecar/model-addition-workflow/hand-over.md#states),
   [Responses](../../specs/model-sidecar/model-addition-workflow/hand-over.md#responses) and
   [Deferral](../../specs/model-sidecar/model-addition-workflow/hand-over.md#deferral) state one
   response for each bundle and commit group, the append-only responses, the request forms, the
   order of a round, the named waits and the drift exceptions. The docstring of `list_lines` in
   `tools/intake_bundle.py` states the `waiting_on no longer open` mark. `verify` gives no
   `spec_commit` or version-heading finding for a finished bundle. This narrows
   [ADR-ZXD7](ZXD7-bundle-process.md) item 2.
4. **3AM0.** The skill states the absorb at landing (Procedure B step 19) and the copy search
   (step 18). Procedure B step 1, Procedure D, the stop points and rule 5 of
   [Section status](../../specs/model-sidecar/README.md#section-status) accept an entry that is
   `accepted` or `absorbed into`. The [Rules](../README.md#rules) state the absorb-first order at
   90% of the read path and the copy fix with no own entry.
5. **37CD.** The workflow states items 1 to 7: Decision questions, Session steps steps 4, 6 and 7,
   Deferral, [Full section](../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#full-section)
   and [Sources](../../specs/model-sidecar/model-addition-workflow/rules.md#sources).
   [Step 8](../../.claude/skills/author-sidecar/SKILL.md#step-8-write-the-final-verdict-and-stop)
   item 1 of `author-sidecar` states the one parity run.

## Reason

The read path was at 92% of its limit after the absorbs of 2026-11-10. The Rules ask for a
consolidation entry at 90% or more. The user asked for it on 2026-11-10. The five entries came
from the intake retro of 2026-11-09, and each rule is in an absorb document.

## Not repeated

The citations of the five entries in the workflow and the skills stay. Each one links an entry
whose status names this entry.

# 3AM0 — Absorb a landed entry in its landing group, and copy fixes with no own entry

**Status:** accepted, 2026-11-09 (user; PR: pending).

## Decision

1. **Absorb at landing.** Procedure B step 19 of
   [`change-sidecar-spec`](../../.claude/skills/change-sidecar-spec/SKILL.md#procedure-b-land-an-accepted-proposal)
   is the home. When the spec states each rule of the entry, the non-spec commit of the landing
   group sets `absorbed into <section file>#<anchor>`. The commit body names the other headings.
   The commit copies the open "Notes at acceptance" items to the open work of the spec log. If the
   spec does not state a rule, the entry stays `accepted`, and the session does not ask the user.
2. **Absorbed is landed.** Procedure B step 1, the graduation check of Procedure D and rule 5 of
   [Section status](../../specs/model-sidecar/README.md#section-status) accept an entry that is `accepted` or `absorbed into`. `tools/intake_bundle.py` already treats
   `absorbed into` as landed ([ADR-ZXD7](ZXD7-bundle-process.md) item 3).
3. **Order of actions.** At 90% of the read-path limit or more, first absorb. Then write a
   consolidation entry ([Rules](../README.md#rules)).
4. **Copies of a landed spec entry.** Procedure B step 18 is the home of the search: the skills, the
   model addition workflow, the templates, `tools/` and `tools/tests/`. The step updates each copy
   in the non-spec commit of the landing group, and reports each copy in `specs/draft/exporter-guide/`
   ([ADR-x64y](x64y-draft-exporter-guide-folder.md)). A workflow file or a skill links the home
   where it can ([ADR-ESP4](ESP4-one-home-for-each-workflow-rule.md) item 1). A new section or a new
   required key adds its rows to `templates/model-intake.md` and to the author-sidecar inputs in the
   same group.
5. **No own entry for a copy fix.** The [Rules](../README.md#rules) state it: a commit that only
   makes a workflow, skill, template or tool copy agree with a landed spec entry cites that entry. A
   new rule is not a copy. [Workflow changes](../../specs/model-sidecar/model-addition-workflow/hand-over.md#workflow-changes)
   links it.

## Reason

- The YOLOX and RTMW intake sessions of 2026-11-06 to 2026-11-09 had three absorb sweeps. The
  commit "Absorb ADR-1GG7 and ADR-730P into the hand-over text" came at a read path over the limit
  ([ADR-1GG7](1GG7-no-compiled-files-in-bundles.md); [ADR-730P](730P-anchor-check-of-bundle-links.md)).
  Each sweep cost a user question, a review workflow and a commit. The last sweep absorbed four
  landings of the same day, and it lost one note of
  [ADR-XH1J](../../specs/model-sidecar/decisions/entries/XH1J-normalize-input-dtype.md) from
  tracking. The read path was at 95% again on 2026-11-09.
- The copy fixes after [ADR-50BW](../../specs/model-sidecar/decisions/entries/50BW-verification-batches.md) (11 files) and after
  [ADR-52NQ](../../specs/model-sidecar/decisions/entries/52NQ-model-id-suffix.md) (9 files) each got a root entry,
  [ADR-JY47](JY47-verification-batch-6-in-the-workflow.md) and
  [ADR-1TR6](1TR6-workflow-copies-of-the-keypoint-detector-id.md). The two held about 4600 read-path characters. A spec
  entry cannot name a skill or a tool file, so only a Rules exception lets a copy fix cite it.
- The intake template had no License rows after
  [ADR-NBG2](../../specs/model-sidecar/decisions/entries/NBG2-license-and-training-data-without-the-deferred-examples.md) landed, until the user asked. A search for
  changed values cannot find a missing row, so item 4 adds the new-section check.

## Consequences

- This decision reverses the earlier user decision that gave the 52NQ copy fix its own entry. The
  user approved this change on 2026-11-09.
- The reviewer of the landing group checks that no rule and no open note is lost.
- Older entries still need an absorb sweep from time to time.

## Alternatives rejected

- **An entry that starts as `absorbed into`.** It changes the allowed status changes and
  `tools/check_decision_log.py`. It needs its own entry.
- **"The heading that states most of the rules".** A reader can take it as a partial absorb. One
  absorb document still states all of the rules.

## Open work

See [open-work.md](../open-work.md).

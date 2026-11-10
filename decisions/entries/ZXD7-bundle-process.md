# ZXD7 — Bundle process

**Status:** absorbed into [`model-addition-workflow/README.md`](../../specs/model-sidecar/model-addition-workflow/README.md), [`templates/model-intake.md#validation-checklist`](../../specs/model-sidecar/templates/model-intake.md#validation-checklist), [`change-sidecar-spec/SKILL.md`](../../.claude/skills/change-sidecar-spec/SKILL.md), 2026-11-10 (user; PR: pending).

## Decision

This entry supersedes [ADR-FADS](FADS-hand-over-bundles-in-intakes.md) in full. The workflow
commit of [ADR-0QKK](0QKK-no-legacy-layer.md) item 6 accepts it.

1. **Publishing.** The release step that replaces `vNEXT` goes.
   [ADR-6GE2](6GE2-spec-version-follows-skellytracker.md) gives the version rules and the publish
   ban. The stops of [ADR-QMKS](QMKS-draft-sections-and-coverage-columns.md) items 1 and 3 stay as
   stops of the `2.0.0` release. An intake gives `V-format.versioning-1` pass or fail, and `-2`
   "n/a until a final release loads the target".
2. **`spec_version`.** The manifest key `spec_version` is the target version that the contributor
   read. `pack` writes the newest version in the checkout `changelog.md`.
   `verify` gives a drift finding for each manifest `sections` entry that changed since `spec_commit`, and for a newer
   version in the checkout. `list` shows the key.
3. **Proposal state.** Each proposal record has one spec-log entry `<id>-<slug>.md`. Its status is
   the authority for the state. `accepted`, `absorbed into` and `superseded by` are landed.
   `proposed`, `accepted` and `absorbed into` own the sections. A bundle with no entry gets its state
   from the latest response. A response is a notice. A `proposed` entry allows the responses
   `recorded`, `accepted` and `needs-contributor`. A `rejected` entry allows `rejected` and
   `resolved-otherwise`. A landed entry allows `landed`. On another pair, the session writes a
   response that agrees with the entry. `proposals/README.md` loses its table. `intake_bundle.py`
   uses these states. `pack` also refuses a `proposal` bundle that has a response `accepted`.
   `(can delete)` also reads the latest response `goals`. When more than one proposal can own a
   section, the owner has the earlier manifest `created` (`pack` keeps the `created` of version 1),
   then the slug that sorts first. Procedure B lands a proposal only when each `base` and
   `depends_on` proposal is landed on the working branch, or lands in the same content commit.
   Procedure E finds the open proposals on the sections of a commit from the record manifest
   `sections` and the Proposed-table Section cell. It lists only `proposed` entries.
4. **Owner rule.** Only the owner writes parts 2, 3 and 6 of a new proposal. A follow-up (`base`)
   can change parts 2 and 3 of its base, and gives the reason in part 8.
5. **Sources.** `hand-over.md` is the source of the bundle rules. `tools/intake_bundle.py` is the
   source of the rules that it checks.
6. **Bundle provenance.** `example/provenance.yaml` has no `source`. The session takes `source`
   from the example sidecar. Each new example entry of `inventory.yaml` must have `bundle`.
7. **The rules that stay.**
   - FADS item 1: [Hand-over bundles](../../specs/model-sidecar/model-addition-workflow/hand-over.md)
     and its headings.
   - FADS item 2: [Hand-over](../../specs/model-sidecar/model-addition-workflow/README.md#hand-over)
     and [Repository instructions](../../AGENTS.md).
   - FADS item 3: [Tracked records](../../specs/model-sidecar/model-addition-workflow/hand-over.md#tracked-records)
     and [Record a new version](../../.claude/skills/propose-sidecar-change/SKILL.md#record-a-new-version).
   - FADS item 4: [Responses](../../specs/model-sidecar/model-addition-workflow/hand-over.md#responses).
   - FADS item 5: a gap is a `proposal` bundle or a spec-log defect, not a gap record. An empty part says `none` and the reason
     ([Step 3](../../.claude/skills/propose-sidecar-change/SKILL.md#step-3-write-each-proposal)).
   - FADS item 6: [Workflow changes](../../specs/model-sidecar/model-addition-workflow/hand-over.md#workflow-changes)
     and [Procedure D](../../.claude/skills/change-sidecar-spec/SKILL.md#procedure-d-another-spec-edit).
   - FADS item 7: [Step 3](../../.claude/skills/propose-sidecar-change/SKILL.md#step-3-copy-the-proposal-into-the-spec-folder)
     and [Step 4](../../.claude/skills/propose-sidecar-change/SKILL.md#step-4-write-the-decision-entry)
     of `propose-sidecar-change`; [Stages](../../specs/model-sidecar/model-addition-workflow/README.md#stages),
     [Phases](../../specs/model-sidecar/model-addition-workflow/README.md#phases) and the phase files,
     [Reference implementations](../../specs/model-sidecar/model-addition-workflow/reference-implementations.md),
     [Independence](../../specs/model-sidecar/model-addition-workflow/sidecar-files.md#independence)
     and [Stage](../../.claude/skills/change-sidecar-spec/spec-edit-rules.md#stage). Item 1 replaces the 0014
     version bullets. The 0014 pitfalls stay in the workflow and the skills.

## Reason

- A newer version shows a bundle of a released target. `spec_commit` shows the changed sections.
- Three stores held the proposal state, with no rule for which one wins.
- The user wants GitHub Issues as the only exporter channel. The bundle folder tests that
  process, so a response is a notice, as an issue comment will be.
- The owner rule forbade the follow-up form, which `intake_bundle.py` accepts.
- The tool checks rules that `hand-over.md` does not state.
- A copy of `source` can disagree with the example sidecar. Without `bundle`, an entry does not
  name its bundle version.

## Consequences

- The workflow commit changes each heading that states a rule of items 1 to 6. It removes each text
  that names the proposal index or the release step. The decided entries and the draft exporter
  guide keep their citations of FADS. Each other citation of FADS cites this entry.
- A bundle that has no `spec_version` needs a new version.

## Alternatives rejected

- **The proposal index or the responses as the authority.** The index copies the entry status. Git
  ignores the responses, and the user deletes them.
- **`spec_version` in place of `spec_commit`.** Only the commit names the exact text that the
  contributor read.

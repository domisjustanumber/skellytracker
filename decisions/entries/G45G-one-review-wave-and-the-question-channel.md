# G45G — One review wave, landing blockers at record time, and the question channel before a pack

**Status:** absorbed into [`model-addition-workflow/hand-over.md#responses`](../../specs/model-sidecar/model-addition-workflow/hand-over.md#responses), 2026-11-10 (user; PR: pending).

## Decision

1. **One review wave.** The session reviews the full version of a bundle before it writes the
   response. The response gives all the findings of that version. A response to version k+1 gives
   no new finding for a problem of version k.
2. **Landing blockers at record time.** Under "Before acceptance", the `proposed` entry lists each
   `needs-export` example of part 7 with no live owner, each `depends_on` bundle that has not
   landed, and each rule of the contributor that waits for the proposal while the proposal waits for
   that contributor. Such a rule is a deadlock. The session asks the user about it in the decision
   question of the record.
3. **The split test.** Two changes are two contract units when the user can accept one change
   without the other, also in one section. The entry lists each such change as its own item, and
   the user decides a split at the decision turn. A split gives a new bundle and a new entry for
   each unit.
4. **Questions before a pack.** A contributor can ask the skellytracker session about a rule before
   it packs. The channel is a direct message today and an issue comment later. The session answers
   with a reading: each condition of the cited rule as `pass` or `fail`, and the rule that decides.
   A changed reading names the condition that the session missed. When no rule decides, the session
   drafts the workflow edit and asks the user once.
5. **The scope of a ruling.** The session that hears a user ruling asks "general rule or this intake
   only?" in the same turn. It passes the answer on with the ruling. The session that gets the
   ruling from an agent lists it, with the answer, in its next decision message to the user.
6. **Workflow findings.** A contributor gives a workflow finding on the channel or in the intake row
   "Notes and questions to the skellytracker session". The session lists each finding, with a
   drafted edit, in its next decision message to the user. The session never accepts a finding by
   itself ([ADR-AD33](AD33-bundles-are-untrusted-input.md) item 6). The manifest gets no new key.
7. **Intake rows.** The Final verdict table of the model intake gets two rows: the findings of
   earlier responses with their answers, and the notes and questions to the session.
8. **Changed rule.** Item 6 changes the path of a workflow change of
   [ADR-ZXD7](ZXD7-bundle-process.md) (FADS item 6): the session gives the finding to the user, and
   the user decides. The rest of that rule stays.

[Responses](../../specs/model-sidecar/model-addition-workflow/hand-over.md#responses) states item 1.
[Tracked records](../../specs/model-sidecar/model-addition-workflow/hand-over.md#tracked-records)
states items 2 and 3.
[Proposal forms](../../specs/model-sidecar/model-addition-workflow/hand-over.md#proposal-forms) states
the split test. [Questions before a pack](../../specs/model-sidecar/model-addition-workflow/hand-over.md#questions-before-a-pack)
states items 4 and 5.
[Workflow changes](../../specs/model-sidecar/model-addition-workflow/hand-over.md#workflow-changes) and
[User decisions](../../specs/model-sidecar/model-addition-workflow/rules.md#user-decisions) state item
6. The template `specs/model-sidecar/templates/model-intake.md` holds item 7.

## Reason

The YOLOX and RTMW intake sessions of 2026-11-06 to 2026-11-09 show these costs:

- `proposal-model-id-suffix@openmmlab-exporter` r3 gave a must-fix finding on the partial
  `input.sidecar` cases at version 2. Version 1 already held those cases. That cost one exporter
  round trip.
- The landing blocker of [ADR-52NQ](../../specs/model-sidecar/decisions/entries/52NQ-model-id-suffix.md),
  the RTMO rebuild, came first in r5, at version 3. The version 2 record was silent about it. An
  OpenMMLab-Exporter rule waited for the proposal to land, while the proposal waited for the
  rebuild. The user saw the deadlock about 3 days later than possible.
- The split of `normalize-input-dtype` and `normalize-custom-defaults` came at the decision turn and
  took 4 exporter user turns. The split test had no home.
- On 2026-11-09 the two sessions talked directly by message. Questions before a pack avoided
  versions ("I want to avoid a v3", "so we avoid a v4"). A reading of intake row G7 changed after
  the user approved the pack, and it did not name the missed condition.
- The skellytracker session asked again "general rule or this intake only?" about a ruling that the
  user gave in the exporter session.
- An onnxruntime 1.27 fp16 note of the exporter was in an untracked plan and needed a relay of the
  user ([ADR-4KW6](4KW6-onnxruntime-1-31-for-the-cpu-check.md)). Three intakes added a notes row by
  hand.

## Consequences

- The record step takes longer, because the session reviews the full version first.
- A finding that only a later version shows, or a later user ruling, still gives a new finding.

## Alternatives rejected

- **`make_vectors.py land --check` at record time.** `land` runs the landed producer. For a
  proposal that changes a reference module, each changed case is a mismatch before the reviewed
  copy ([ADR-AD33](AD33-bundles-are-untrusted-input.md) item 3).
- **A scratch tree for `sidecar_trace.py impact`.** Bundles use the main checkout, not a worktree.
- **A `verify` check of the part 4 replaced-id list.** Part 4 gives the list as prose in a table
  row, sometimes for two sections. A parse of it is not a clear check.
- **A user ruling is general by default.** It can make an intake-only ruling a rule with no notice.
- **A `workflow_findings` manifest key.** The intake row and the channel carry the finding.
- **Land both halves of a split with no new bundle.** The user ruled that they are separate contract
  units.

## Open work

See [open-work.md](../open-work.md).

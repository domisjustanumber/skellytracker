# FADS — Hand-over bundles in `intakes/`

**Status:** accepted, 2026-10-28 (user; PR: pending).

## Decision

This entry supersedes [ADR-PYKX](pykx-submission-folders.md), [ADR-FAAC](faac-proposal-records.md)
and [ADR-0014](0014-spec-lifecycle.md) in full. Items 1 to 6 are new. Item 7 restates the rules that
stay by links, as [ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md) allows.

1. **Bundles.** A contributor gives its files to skellytracker in a bundle in `intakes/` at the root
   of the checkout. Git ignores the folder. A bundle has the kind `model` or `proposal`. A
   contribution (`contributes_to`) and a follow-up (`base`) are `proposal` bundles. A bundle version
   is append-only. Its `manifest.yaml` gives the hashes, the commits and the links between bundles.
   The tool `tools/intake_bundle.py` packs, lists and verifies bundles.
   [Hand-over bundles](../specs/model-sidecar/model-addition-workflow/hand-over.md) states the
   location, the layout, the payload, the manifest, the versions, the proposal forms, the section
   owner, the states, the responses, the deferral, the changes at acceptance, the re-export requests,
   the retention and the writers.
2. **No scan.** skellytracker does not scan or read the `plans/` folder of an exporter. An exporter
   writes no file in skellytracker except the new version folders of its own bundles
   ([`AGENTS.md`](../AGENTS.md#repository-instructions), [Git rules](../AGENTS.md#6-git-rules)).
3. **Byte-copy records.** A proposal record in `specs/model-sidecar/proposals/<slug>/` is a byte copy
   of one bundle version, with its manifest. The session changes no file of it, except
   `redactions.yaml`. A doc test checks the hashes and the vector file size (256 KiB). The facts of
   the session go under "Before acceptance" of the entry
   ([Tracked records](../specs/model-sidecar/model-addition-workflow/hand-over.md#tracked-records)).
   A new version of a recorded proposal replaces the record in full and keeps the entry
   ([Record a new version](../.claude/skills/propose-sidecar-change/SKILL.md#record-a-new-version)).
4. **`resolved-otherwise`.** When the user accepts the goal of a proposal but a different change
   lands, the response state is `resolved-otherwise` with a `goals` table. In the log, the entry is
   `rejected` with the reason "Resolved by ADR-<X>". The Rules do not change.
5. **No gap records.** A gap is a `proposal` bundle, or a spec defect in the spec log
   `open-work.md`. A part that a contributor cannot fill says `none` and the reason.
6. **Workflow changes.** A bundle never holds a workflow change. The user asks a session for it. It
   lands in one non-spec commit with an entry that is `accepted` in that commit. A change of the
   Rules also changes the kit in that commit (Procedure D of `change-sidecar-spec`).
7. **Rules that stay.**
   - pykx items 1 to 4 (with new paths in the bundle) and 7:
     [Payload](../specs/model-sidecar/model-addition-workflow/hand-over.md#payload). Items 5 and 6
     go: the states and [Retention](../specs/model-sidecar/model-addition-workflow/hand-over.md#retention)
     replace them.
   - faac items 1, 4, 6, 7, 9 to 11: [Step 3](../.claude/skills/propose-sidecar-change/SKILL.md#step-3-copy-the-proposal-into-the-spec-folder)
     and [Step 4](../.claude/skills/propose-sidecar-change/SKILL.md#step-4-write-the-decision-entry)
     of `propose-sidecar-change`. Items 2 to 5 and 8 go: the record is a byte copy with no front
     matter, no copy rules and no gap records, and item 3 moves "Before acceptance" to the entry.
   - 0014 "Stages" and "No implementation change":
     [Stages](../specs/model-sidecar/model-addition-workflow/README.md#stages) and
     [Phase 3](../specs/model-sidecar/model-addition-workflow/phase-3-skellytracker.md).
   - 0014 "Versions", "`vNEXT` is not a version" and "Release step":
     [Publishing](../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing).
   - 0014 "New-model workflow":
     [Phases](../specs/model-sidecar/model-addition-workflow/README.md#phases) and the phase files.
   - 0014 "Reference implementations from exporters":
     [Reference implementations](../specs/model-sidecar/model-addition-workflow/reference-implementations.md#reference-implementations).
   - 0014 "Independence":
     [Independence](../specs/model-sidecar/model-addition-workflow/sidecar-files.md#independence).
   - 0014 "Who writes what" goes: items 1 and 2 replace it. Its rule "do not change an exporter
     repo" is in [Stage](../.claude/skills/change-sidecar-spec/SKILL.md#stage).
   - 0014 "Not repeated" goes as a list. Its pitfalls stay as rules of the workflow and the skills.

## Reason

- The scan of `../../*-Exporter/plans/sidecar/` read untracked files that change with no version. A
  session could not tell which text it had recorded, and a changed file needed a manual record
  again.
- The copy rules changed the exporter text. Then the record was not the text of the exporter, and a
  hash could not prove the copy.
- A second exporter on one slug overwrote the first. Follow-ups and dependencies had no form, and
  "Needed by" needed an edit in another repo.
- A gap record needed its own status-line form and a second path to a proposal.
- An ignored folder in the checkout survives a branch switch and a rebase. An exporter cannot commit
  to it.

## Consequences

- An exporter agent writes in one place outside its repo: `intakes/` of the checkout.
- Each fix of a bundle goes back to the contributor as a new version. The session makes only
  editorial fixes at acceptance.
- `git clean -x` or a second worktree loses or hides the bundles. `AGENTS.md` forbids both.

## Alternatives rejected

- **Track `intakes/` in git.** One bad bundle would block each commit on the private-data and link
  checks, and exporters cannot commit here.
- **A notices file for re-export requests.** The spec `open-work.md` already holds the work lists.

_Edited 2026-10-29 (this PR): link repair._

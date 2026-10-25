---
name: propose-sidecar-change
description: Use this skill when the sidecar spec does not describe a model property exactly (a `near-miss` or a `gap`). Use it to write the eight-part spec change proposal. Use it also to record such a proposal in skellytracker as a `proposed` decision entry, and to record it again when the exporter changes it.
---

# Propose a sidecar spec change

This skill uses ASD-STE100 Simplified Technical English.

This skill is phase 2 of the new-model workflow. A proposal asks for one new or changed contract unit
of the spec (one section) and for its implementation.

This skill wraps "Phase 2" of the
[exporter guide](../../../specs/exporter-guide/sidecars/workflow/phase-2-proposal.md#phase-2-propose-a-spec-change-and-its-implementation)
and the [change proposal template](../../../specs/sidecar/templates/change-proposal.md). The guide and
the template give the rules and the details. This skill gives the order of the steps, the inputs, the
outputs and the stop points. If this skill and the guide do not agree, follow the guide. The spec is
normative.

## Where this skill runs

| Place | What you do | Where you stop |
|---|---|---|
| An exporter repo | Write the proposal files in the `plans/` folder of the exporter repo. | After the proposal files. You do not change skellytracker. |
| skellytracker | Copy a proposal to `specs/sidecar/proposals/<slug>/proposal.md`. Record it as a short decision entry with the status `proposed`. Record it again when the exporter changes it. | After the entry. The user accepts or rejects the proposal. |

**In an exporter repo:**

- This skill file is in the skellytracker repo. Read it, read-only, in the skellytracker checkout
  `../freemocap/skellytracker`. From the root of an exporter repo, the path of this file is
  `../freemocap/skellytracker/.claude/skills/propose-sidecar-change/SKILL.md`.
- Read the files of the checkout as normal files. Do not edit them. Do not commit to skellytracker.
  Do not change its branch.
- A relative link in this file starts at the folder of this file. In the checkout, the link
  `../../../specs/sidecar/templates/change-proposal.md` opens the file
  `../freemocap/skellytracker/specs/sidecar/templates/change-proposal.md`.
- If your agent does not support skills, read this file. Then do its steps in order.

## Files

| File | Link | Path from the root of an exporter repo |
|---|---|---|
| Exporter guide, "Phase 2" | [exporter-guide.md](../../../specs/exporter-guide/sidecars/workflow/phase-2-proposal.md#phase-2-propose-a-spec-change-and-its-implementation) | `../freemocap/skellytracker/specs/exporter-guide/sidecars/README.md` |
| Change proposal template | [change-proposal.md](../../../specs/sidecar/templates/change-proposal.md) | `../freemocap/skellytracker/specs/sidecar/templates/change-proposal.md` |
| Changelog, "Considered and deliberately not added" | [changelog.md](../../../specs/sidecar/changelog.md#considered-and-deliberately-not-added) | `../freemocap/skellytracker/specs/sidecar/changelog.md` |
| Section map and validation index | [README.md](../../../specs/sidecar/README.md#section-map) | `../freemocap/skellytracker/specs/sidecar/README.md` |
| skellytracker package code (for part 6) | [skellytracker/](../../../skellytracker/) | `../freemocap/skellytracker/skellytracker/` |
| Decision log (for a skellytracker session) | [README.md](../../../notes/decisions/README.md) | `../freemocap/skellytracker/notes/decisions/README.md` |

## Inputs

In an exporter repo:

- the intake `plans/sidecar-intake-<model>.md`, with its `near-miss` rows and `gap` rows (from the
  skill [`author-sidecar`](../author-sidecar/SKILL.md));
- the upstream evidence of each row;
- the committed host implementation of the exporter, if it exists;
- or a host implementation that does not agree with an existing reference implementation;
- the `proposed` entries of the skellytracker decision log that cover the same property, if they
  exist.

If the evidence of a row is only a secondary source, you can still write its proposal. Follow the
evidence rule in [Rules](../../../specs/exporter-guide/sidecars/rules.md#rules). Name the primary evidence
that is missing in part 1.

In skellytracker:

- the proposal files in the exporter repos. Find them with a scan of
  `../../*-Exporter/plans/sidecar-proposal-*` from the root of the skellytracker repo;
- or a gap that a skellytracker session finds, with no exporter proposal.

## Outputs

| Place | Output |
|---|---|
| An exporter repo | `plans/sidecar-proposal-<slug>.md`, one for each contract unit. |
| An exporter repo | `plans/sidecar-reference-<section_module>.py`, the reference implementation of part 3. It exists also when no host code exists yet. |
| An exporter repo | The parity script of part 5, committed in the exporter repo. |
| An exporter repo | A link to each proposal in the intake. |
| skellytracker | `specs/sidecar/proposals/<slug>/proposal.md`: the eight parts in full ([faac](../../../notes/decisions/faac-proposal-records.md)). |
| skellytracker | A row in the proposal index [`specs/sidecar/proposals/README.md`](../../../specs/sidecar/proposals/README.md). |
| skellytracker | `notes/decisions/<id>-<slug>.md`: a short decision entry "Spec change: <slug>", with the status `proposed`. |
| skellytracker | A row for the entry in the Proposed table of [`notes/decisions/README.md`](../../../notes/decisions/README.md). |

## Procedure in an exporter repo

### Step 1: Prepare

1. Do the steps of
   [Where to read the spec](../../../specs/exporter-guide/sidecars/where-to-read.md#where-to-read-the-spec). Get the
   commit of the checkout.
2. If the checkout does not exist, or it is not on the branch `dom/sidecar-implementation`, stop.
   Ask the user what to do.
3. Read the table
   [Considered and deliberately not added](../../../specs/sidecar/changelog.md#considered-and-deliberately-not-added).
   If your gap is in it, cite the row in part 1. Give the evidence that a model needs the feature now.
4. Find the `proposed` entries that cover your rows. Read the Proposed table of the
   [decision log](../../../notes/decisions/README.md#proposed). Read each entry whose Section cell
   is one of your sections or `none`. Also read each `proposed` entry that the "Authoring
   guidance" or the "Implementer guidance" of your sections cites.
5. If a `proposed` entry covers your rows, do not write a competing proposal. Do these steps:
   - Use the slug of the entry as the slug of your proposal.
   - Cite the entry in the header and in part 1.
   - Add your evidence, your vectors and your parity plan.
   - If your rows need a different change, say where your proposal differs. Give the reason in
     part 8.
   - If the entry is a gap record (its Decision section says so), give the parts that it does not
     have. A skellytracker session adds your proposal to the gap record.
6. If the exporter has no git repo, follow "An exporter with no git repo" in
   [New-model workflow](../../../specs/exporter-guide/sidecars/workflow/README.md#new-model-workflow).

### Step 2: Find the contract units

1. Group the `near-miss` rows and the `gap` rows of the intake by the section that they change.
2. Write one proposal for each group. Do not put two contract units in one proposal.
3. Put a new role with its enum edits and path edits in one proposal (part 2 of
   [Phase 2](../../../specs/exporter-guide/sidecars/workflow/phase-2-proposal.md#phase-2-propose-a-spec-change-and-its-implementation)).
4. If a proposal needs another proposal, write the dependency in the header of each proposal.

### Step 3: Write each proposal

1. Copy the change proposal template to `plans/sidecar-proposal-<slug>.md`. `<slug>` is a short
   lowercase name of the change, with hyphens. If the file exists, read it and update it in place.
   Do not overwrite a `plans/sidecar-*` file that you did not read. `plans/` is not in git, so you
   cannot undo an overwrite.
2. Follow [How to use this template](../../../specs/sidecar/templates/change-proposal.md#how-to-use-this-template).
3. Fill in the [Header](../../../specs/sidecar/templates/change-proposal.md#header).
4. Fill in the eight parts. Each part has its rules in the template and in the guide:

   | Part | Template heading | What to check |
   |---|---|---|
   | 1 | [1. Gap](../../../specs/sidecar/templates/change-proposal.md#1-gap) | Give a number where possible. |
   | 2 | [2. Spec change](../../../specs/sidecar/templates/change-proposal.md#2-spec-change) | Write the exact normative text in ASD-STE100. List each place that the change edits. |
   | 3 | [3. Reference implementation](../../../specs/sidecar/templates/change-proposal.md#3-reference-implementation) | Use only NumPy, OpenCV and the Python standard library. Write `plans/sidecar-reference-<section_module>.py`. If no host code exists yet, write the functions from the text of part 2, and write `source commit: none (no host code)` in the note at the top of the file. |
   | 4 | [4. Vectors](../../../specs/sidecar/templates/change-proposal.md#4-vectors) | Make the vectors with part 3. Verify them against the host implementation. If you cannot, write `unverified: <reason>`. Give each pixel case a tolerance in `compare`. |
   | 5 | [5. Parity evidence](../../../specs/sidecar/templates/change-proposal.md#5-parity-evidence) | Follow [Parity](../../../specs/exporter-guide/sidecars/workflow/parity.md#parity). Commit the script. If you cannot run the script or commit it, write `to run` and describe the script. If you do not know the path or the commit of the script, write `unknown (<reason>)`. |
   | 6 | [6. skellytracker implementation proposal](../../../specs/sidecar/templates/change-proposal.md#6-skellytracker-implementation-proposal) | Read the package code in the checkout. If a call site is not known, write `for the implementer`. |
   | 7 | [7. Exporter impact](../../../specs/sidecar/templates/change-proposal.md#7-exporter-impact) | Name each exporter that must write new fields or regenerate sidecars. |
   | 8 | [8. Alternatives considered](../../../specs/sidecar/templates/change-proposal.md#8-alternatives-considered) | Include the near-miss and the reason to reject it. |

5. If a part has no content, write `none` and the reason. Do not delete a part.
6. Do not write a sidecar file of the model with the proposed fields. Part 2 can have YAML excerpts.
7. If your host code does not agree with an existing reference implementation, write a proposal. Do
   not write a second reference implementation
   ([Reference implementations](../../../specs/exporter-guide/sidecars/reference-implementations.md#reference-implementations)).

### Step 4: Link and stop

1. Link each proposal from the intake, in
   [Proposals and reference files](../../../specs/sidecar/templates/model-intake.md#proposals-and-reference-files).
2. Do the checklist [Before you stop](../../../specs/sidecar/templates/change-proposal.md#before-you-stop).
3. Stop. Do not change a file in skellytracker.
4. Tell the user these items:
   - the proposal files and their reference files;
   - the dependencies between the proposals;
   - the `proposed` skellytracker entries that your proposals build on;
   - the primary evidence that each proposal still needs;
   - the spec defects that you found and did not propose;
   - each result that is `to run`;
   - each `plans/sidecar-*` file that no current intake or proposal owns.
5. A skellytracker session records each proposal (phase 3). The user accepts or rejects it.
6. If you changed a proposal that skellytracker already recorded (the folder
   `specs/sidecar/proposals/<slug>/` exists in the checkout), tell the user. A skellytracker session
   records it again ([Record a changed proposal](#record-a-changed-proposal)).

## Procedure in skellytracker

### Step 1: Prepare

1. Read [section 4](../../../AGENTS.md#4-sidecar-rules) and
   [section 5](../../../AGENTS.md#5-decision-log) of `AGENTS.md`.
2. Read the [Rules](../../../notes/decisions/README.md#rules) and the
   [entry template](../../../notes/decisions/template.md) of the decision log.
3. Read the index of the decision log. If an entry already records the proposal, do not add a second
   entry. If the exporter changed the proposal after the copy, do the steps of
   [Record a changed proposal](#record-a-changed-proposal).
4. If a `proposed` entry covers the same property as the exporter proposal, read the entry:
   - If it is a gap record (see [Rules](../../../notes/decisions/README.md#rules)) and the exporter
     proposal builds on it (the same slug, and the entry is cited in the header), add the proposal
     to the gap record (Step 4, item 9).
   - Otherwise, do not add a competing entry. Tell the user the two items. The user decides.

### Step 2: Get the proposal

1. Find the exporter proposals with a scan of `../../*-Exporter/plans/sidecar-proposal-*`.
2. Read the exporter repos. Do not change them.
3. Check each exporter proposal with
   [Before you stop](../../../specs/sidecar/templates/change-proposal.md#before-you-stop).
4. If a part is missing, tell the user. Do not write the missing part from your own reading of the
   spec.
5. For a gap that a skellytracker session finds, write the eight parts yourself with the template.
   If the evidence gives only the gap and the direction of a change (for example, no exporter has
   host code or a parity script yet), write a gap record instead
   ([Rules](../../../notes/decisions/README.md#rules)). Start its Decision section with
   "**Proposed, not decided.** This entry is a gap record". Say which work the full proposal must do.
6. Parts 3, 4 and 5 need an exporter implementation. If none exists, write `none` and the reason in
   part 3 and in part 5.
7. Do not write a reference implementation from your own reading of the spec.
8. In part 4, a vector that comes only from a reading of the text is `unverified`. Write
   `unverified: <reason>`.

### Step 3: Copy the proposal into the spec folder

Decision [faac](../../../notes/decisions/faac-proposal-records.md) gives the rules of this step.

1. Create `specs/sidecar/proposals/<slug>/proposal.md`. Use the slug of the proposal. The file is
   informative. It is not normative until a content PR lands its text in the section files.
2. Write the front matter: `slug`, `section` (the proposed section ID), `exporter`, `decision` (the
   entry ID of Step 4, in quotes) and `state: recorded`. `state` is `recorded`, `accepted`,
   `landed` or `rejected`.
3. Write the source note at the top of the file: the exporter repo, its commit and the date of the
   copy. For an exporter with no git repo, write `none (no git repo)` as the commit.
4. Copy the header and all eight parts in full. The code of part 3 is a `python` code block. The YAML
   of part 4 is a `yaml` code block.
5. Change only these items:
   - a `plans/` path becomes "the untracked <topic> plan of <repo> (plan facts)", with no path;
   - private data is redacted ([Private data](../../../AGENTS.md#8-private-data));
   - a skellytracker commit that is not on `development` becomes its PR or branch and the file path;
   - a path of an exporter with no git repo stays as it is. The source note says one time that the
     exporter has no git repo and that its paths are not pinned;
   - a relative link that does not resolve in skellytracker becomes a code span.
6. Do not write a missing part. Do not correct the text of a part.
7. Add the heading "Before acceptance" at the end. List each failed item of
   [Before you stop](../../../specs/sidecar/templates/change-proposal.md#before-you-stop), the
   missing primary evidence, each `to run` result and each open question.
8. Put other long text of the proposal in the same folder: the draft of an entry that the proposal
   supersedes (`supersedes-<id>.md`), and long evidence (`evidence.md`).
9. Add a row to the proposal index
   [`specs/sidecar/proposals/README.md`](../../../specs/sidecar/proposals/README.md). The row gives
   the proposal, the section, the exporter, the decision entry and the state. The proposal index is
   the list of the proposals. `open-work.md` has no line for each proposal.
10. On acceptance, the content PR takes the text, the code and the vectors from `proposal.md`. It
    sets the decision entry and `state` to `accepted`. The last PR of the proposal sets `state` to
    `landed`. When the content PR lands part 6, it adds an open-work item for the implementer
    guidance. A rejected proposal gets `state: rejected`. Its folder stays.

### Step 4: Write the decision entry

1. Run `git fetch --all` when you can. Then run `uv run python tools/check_decision_log.py --new`.
   Give the entry the ID of the `new:` line ([section 5](../../../AGENTS.md#5-decision-log) of
   `AGENTS.md`).
2. Name the file `notes/decisions/<id>-<slug>.md`. Use the slug of the proposal. The title is
   "<id> — Spec change: <slug>". In the front matter of `proposal.md`, write the ID in quotes, for
   example `decision: "gtwq"`.
3. Write the status line: `**Status:** proposed, <YYYY-MM-DD> (<source>).` The source names the
   proposing repo, for example "OpenMMLab-Exporter proposal".
4. Start the Decision section with "**Proposed, not decided.**" and a link to `proposal.md`. Then
   give these items in a list: the section, the change, the version, the models, the entries that the
   proposal supersedes on acceptance, and the related proposals.
5. In Reason, give the gap (part 1) in a few sentences. In Evidence, give the parity state (part 5).
   In Open work, write only the link to the open-work list.
6. Keep the entry inside the entry limit
   ([z934](../../../notes/decisions/z934-decision-log-index-and-read-path.md)). The details stay in
   `proposal.md`.
7. Write the repo name with the ID of an exporter decision, for example "OpenMMLab-Exporter
   0020". Write the entry in ASD-STE100.
8. Add the entry to the Proposed table of the decision log, with the status `proposed`. Its
   Section cell is the section ID of the proposal in backticks, or `none`. Do not add a line to
   `open-work.md`: the proposal index lists the proposals.
9. If the proposal completes a gap record, edit the gap record. Do not add a new entry. Items 1, 2
   and 8 do not apply. Write the Decision of item 4. Move the original
   text under Reason. Remove the sentence "This entry is a gap record". Keep the status `proposed`.
   Add `completed <YYYY-MM-DD> (<source>)` to its status line
   ([gtwq](../../../notes/decisions/gtwq-random-entry-ids.md)).
10. If the proposal supersedes an accepted entry on acceptance, write the superseding entry now, with
    the status `proposed`. When its restated rules do not fit the entry limit, link to
    `supersedes-<id>.md` in the proposal folder.

### Step 5: Check and stop

1. Do not change the spec text, the changelog, the vectors or the examples. They come after the user
   accepts the proposal.
2. Run `uv run pytest tools/tests -q`. All tests must pass.
3. The proposal file and the entry are a non-spec change. Put them in a non-spec PR
   ([0027](../../../notes/decisions/0027-single-working-branch.md#one-kind-of-change-in-each-pr)).
4. Stop. Tell the user the entry number and the decision to make.
5. The user accepts or rejects the proposal. After acceptance, use the skill
   [`change-sidecar-spec`](../change-sidecar-spec/SKILL.md).

### Record a changed proposal

Decision [vac0](../../../notes/decisions/vac0-record-a-changed-proposal.md) gives the rules of this
procedure. Do it when the exporter file of a proposal with `state: recorded` changed after the copy
that the source note of `proposal.md` gives. Procedure B step 4 of
[`change-sidecar-spec`](../change-sidecar-spec/SKILL.md) stops a landing until the new record exists.

1. Do Step 1 and Step 2. Read the new exporter file and its reference file in full.
2. If `state` is `accepted` or `landed`, stop. Do not change the copy. Tell the user: the exporter
   writes a new proposal for a new change.
3. Do not add a second entry. The entry ID, the slug, the file names and the status `proposed` stay.
4. Replace `proposal.md` in full with a copy of the new exporter file. Replace the other exporter
   files of the folder (for example `evidence.md`) in the same way. Apply only the copy rules of
   Step 3, items 3 to 6. Keep the front matter.
5. Write a new source note: the exporter repo, its commit, the date of the new copy and the date of
   the first copy.
6. Write the heading "Before acceptance" again from the old list:
   - Keep each item of the old list, in its order.
   - Tick each item that the new version closes. Give the reason after it.
   - Rewrite each item that the new version changes. Mark it `(changed <YYYY-MM-DD>)`.
   - Add each new item (Step 3, item 7) at the end of its group. Mark it `(new <YYYY-MM-DD>)`.
7. Change the Decision, the Reason and the Evidence of the entry only where the new version changes
   them. Keep the entry inside the entry limit.
8. Add `recorded again <YYYY-MM-DD> (<source>)` to the status line of the entry. The source names
   the exporter, for example "MediaPipe-Exporter proposal".
9. If the Decision cell or the Section cell of the index row changes, change the row in the same PR.
10. Do Step 5. Put the new record in a non-spec PR. End the commit subject with `(<id>)` of the
    entry.

## Stop points

| Condition | Action |
|---|---|
| The checkout does not exist, or it is not on the branch `dom/sidecar-implementation` (exporter repo). | Stop. Ask the user what to do. |
| You wrote the proposal files (exporter repo). | Stop. Report to the user. |
| An exporter proposal has a missing part (skellytracker). | Tell the user. Do not write the part yourself. |
| You wrote the `proposed` entry (skellytracker). | Stop. The user accepts or rejects the proposal. |
| The exporter changed a proposal with `state: accepted` or `landed` (skellytracker). | Stop. Do not change the copy. The exporter writes a new proposal. |

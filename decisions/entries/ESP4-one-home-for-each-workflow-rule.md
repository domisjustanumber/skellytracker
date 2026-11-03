# ESP4 — One home for each workflow rule; the templates are forms

**Status:** accepted, 2026-11-03 (user; PR: pending).

## Decision

This entry supersedes no entry. A file name with no folder is in
`specs/model-sidecar/model-addition-workflow/`.

1. **One home.** Each workflow rule has one home: a heading of a workflow file. Item 4 gives the
   only other homes. A skill or a workflow file links the home. A template names it by heading text
   and code-span path, with no relative link. A template cites a skellytracker entry as
   `skellytracker ADR-<ID>`, with no link. Section 5 of the root `AGENTS.md` gets this exception.
   An entry of another repo keeps the form of that section: `<Repo> ADR-<ID>`, with a full-SHA
   permalink when the entry is on its default branch. "Path bases" of `reading-the-spec.md` uses
   `<Repo> ADR-<ID>`.
2. **The homes.**
   - Batch-form policy: "Publishing" of `validation-and-publishing.md`. The field meanings stay in
     "Manifest" of `hand-over.md`. The outcomes stay in `batch-conversion-check.md`.
   - Host-run rule: template part 4, the complete copy (item 4), and "Payload" of `hand-over.md`
     for the bundle.
   - Skip rules of the reference-implementation step: "When to do the step" of
     `reference-implementations.md`.
   - Blocking row: "Blocking rows" of `phase-1-intake.md`.
   - Near-misses: "Near-misses seen so far" of `mapping-hints.md`. Item 1 gets the intake wording,
     with its compare step, and an
     [ADR-0012](../../specs/model-sidecar/decisions/entries/0012-fit-resize-for-rtmo.md) link. The
     ROI-refiner case stays a rule in `rules.md`. `mapping-hints.md` links it.
   - Independence: "Independence" of `sidecar-files.md`.
3. **New headings.** `phase-1-intake.md` gets "Verdicts", "Blocking rows" and "Final verdict" after
   the numbered list. The step numbers do not change. `phase-2-proposal.md` gets "Before you write a
   proposal". "When to do the step" replaces the bold "Rule." in `reference-implementations.md`.
4. **The templates are forms.** They keep their headings, anchors, tables, row lists and slot
   instructions. The intake uses the step numbers of phase 1. Its section column holds bare section
   IDs. The Verdicts examples that section files cite stay. Parts 4, 5 and 7 of the proposal
   template stay homes of the rules that [ADR-8DSW](8DSW-vector-files-are-the-case-source.md),
   [ADR-JAA4](JAA4-one-batch-field.md) and
   [ADR-NB5F](NB5F-no-change-classes-and-one-re-export-request.md) restate there.
5. **The code map.** Part 6 cites the Steps column of `specs/model-sidecar/TRACEABILITY.md`. A short
   table gives only dispatch, `DetectionStage`, `runtime.sidecar_model_spec` and the catalog.
6. **Rules that move.** These rules are only in the intake. They move to "Rules" of `rules.md`:
   - A different exporter value does not change the verdict `exact`.
   - A row of a value that the exporter chooses is a `gap` only when the spec has no rule for the
     role of the model.
   - The slot words `not read (<reason>)` and `not checked`.
7. **Step order.** The intake uses the order of the skill `author-sidecar`. The reference
   implementations come before the final verdict.
8. **Bundle rules.** The Batch-conversion check is now in its own file, `batch-conversion-check.md`.
   `hand-over.md` names that file as a part of the bundle rules, so
   [ADR-ZXD7](ZXD7-bundle-process.md) item 5 stays true. The same sentence says that the templates
   name `hand-over.md` and the skills link it.

## Reason

- A review found the batch-form policy in more than eight places: the skills, the workflow files
  and both templates. Some copies already disagree. For example, item 1 of the intake near-misses
  has a compare step, and the copy in `mapping-hints.md` does not. An edit of one copy leaves the
  other copies stale.
- A template goes into each bundle. A rule copy in a template goes stale in each bundle. A heading
  name stays correct when the text under the heading changes.
- `verify` of `tools/intake_bundle.py` resolves each relative link of a `proposal` bundle from the
  record folder `specs/model-sidecar/proposals/<name>/`. A template link does not resolve from
  there. No tool checks the links of an intake, but they also break in a bundle.
- Section files cite the Verdicts examples. Decided entries restate rules through parts 4, 5
  and 7.
- The intake put the reference files after the final verdict. The skill puts them before it.

## Consequences

- The commit cites this entry next to the changed text under each heading that a decided entry
  restates: "Inputs" and "Verdicts" of `batch-conversion-check.md`, `reference-implementations.md`,
  template part 4, "Rules for each spec edit" and "Examples and vectors" of `change-sidecar-spec`,
  "Step 3: Write each proposal" of `propose-sidecar-change`, the phase files (also step 1b of
  phase 1), `rules.md`, each changed heading of `hand-over.md`
  ([ADR-ZXD7](ZXD7-bundle-process.md) item 7), "Publishing" of
  `validation-and-publishing.md` ([ADR-JAA4](JAA4-one-batch-field.md)), "Independence" of `sidecar-files.md` if its text changes,
  and section 5 of `AGENTS.md`
  ([ADR-Z05A](Z05A-essential-decision-log-rules.md) item 4).
- Section 5 of `AGENTS.md` is a kit block. The commit runs `tools/sync_bootstrap_kit.py --write`.
- Of the homes that [ADR-8DSW](8DSW-vector-files-are-the-case-source.md) item 7 names, only part 4
  states the host-run rule now.
- No tool checks a reference by heading name. A rename of a home breaks such a reference with no
  finding.
- The draft exporter guide goes stale in some places. The user fixes it.

## Alternatives rejected

- **The intake as the home of the near-misses.** The templates must get shorter.
- **Links in the intake section column.** They do not resolve in a bundle.
- **Three commits.** Procedure D of `change-sidecar-spec` and "Workflow changes" of `hand-over.md`
  give one non-spec commit.

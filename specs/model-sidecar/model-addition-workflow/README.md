# Model addition workflow

Use this workflow for each new model. Use it also to request a change to the sidecar spec. This
workflow is also called the "new-model workflow".

The workflow is the same for each contributor: an exporter agent, a human contributor or a
skellytracker session. An exporter is a repo that makes ONNX files and writes their sidecars, for
example OpenMMLab-Exporter. You do not need an exporter repo to follow this workflow.

The [sidecar spec](../sidecar-spec.md) is normative for the meaning of a sidecar. This workflow is
normative for the process: it tells how to apply the spec to a new model, and how to request a spec
change. It does not change the meaning of the spec. If this workflow and the spec do not agree, the
spec is correct. This workflow is not a section of the spec. It has no section ID and no rule IDs.

## Files of the workflow

- [Read the spec](reading-the-spec.md): the files to read, the section IDs, the vectors and the links
  to the spec.
- [Rules](rules.md): the evidence rules and the stop rule.
- [Sidecar files](sidecar-files.md): Independence, Sidecar YAML, Path.
- [Validation and publishing](validation-and-publishing.md): Validation, Publishing, `source` and
  hashes.
- [Phase 1: can the current spec describe the model?](phase-1-intake.md)
- [Parity](parity.md)
- [Mapping hints for phase 1](mapping-hints.md)
- [Phase 2: propose a spec change and its implementation](phase-2-proposal.md)
- [Phase 3: what skellytracker does next](phase-3-skellytracker.md)
- [Reference implementations](reference-implementations.md)
- [Reference examples](reference-examples.md): the procedure that adds a spec example or replaces one

## Phases

Do phase 1 and phase 2. Then stop. A skellytracker session does phase 3. The user accepts or rejects
each proposal.

Two skills give the steps of phase 1 and phase 2. They use the rules of this workflow:

- `author-sidecar` (`../freemocap/skellytracker/.claude/skills/author-sidecar/SKILL.md`):
  phase 1 and the reference-implementation step.
- `propose-sidecar-change`
  (`../freemocap/skellytracker/.claude/skills/propose-sidecar-change/SKILL.md`): phase 2.

Read each skill file in the skellytracker checkout. Do its steps in order.

## Paths and words

- A path in a code span that starts with `../freemocap/skellytracker/` starts at the root of an
  exporter repo, for example `../freemocap/skellytracker/specs/model-sidecar/README.md`. The
  exporter repos and the `freemocap` folder are in the same parent folder.
  [Path bases](reading-the-spec.md#path-bases) gives the bases of the other paths.
- If your skellytracker checkout is in a different folder, replace the prefix
  `../freemocap/skellytracker/` with the path of your checkout. In the skellytracker repo, remove the
  prefix.
- "Your repo" is the git repo that holds your sidecar writer code, your host implementation and your
  parity scripts. In an exporter, it is the exporter repo.
- The templates and the skills say "the exporter" and "the exporter repo". If you are not an
  exporter, read "you" and "your repo".

## Stages

In the spec-build stage, the contributors add models, find gaps, propose spec changes and implement
each section on their host side. The skellytracker package code does not change. In the
implementation stage, skellytracker implements each section in the order that the models need it.
In the steady state, each spec change is specified and then implemented in skellytracker and in
the exporters in the same cycle.

## Files in `plans/`

Write the files of the submission in the folder `plans/sidecar/` of your repo. Each folder holds the
files of one model or of one proposal. It stays in your repo until skellytracker has landed its
files (ADR-[pykx](../../../notes/decisions/pykx-submission-folders.md)).

```text
plans/sidecar/
  models/<model_id>/
    intake.md                       # the filled model intake template (phase 1)
  proposals/<slug>/                 # one folder for each contract unit (phase 2)
    proposal.md                     # the filled change proposal template
    reference/<section_module>.py   # part 3: the reference implementation
    vectors/<section ID>.yaml       # part 4: the vectors
    evidence.md                     # optional: long parity tables and long evidence
    example/                        # optional: a candidate example (phase 2, part 7)
      detectors/...                 # the sidecar and its fragments, in the storage layout
      provenance.yaml               # its entries for inventory.yaml
  reference/<section_module>.py     # a reference implementation of the current spec text
```

- `<model_id>` is the `model_id` of the family. Write one intake for each family.
- `<slug>` is a short lowercase name of the proposed change, with hyphens, for example
  `letterbox-floor-rounding`.
- `<section_module>` names one section. "Reference implementations" gives the rule.
- Each file name in a proposal folder is the name of its target file in skellytracker. When
  skellytracker records the proposal, it copies the folder to `specs/model-sidecar/proposals/<slug>/`.
  When it lands the proposal, it copies `reference/<section_module>.py` to
  `specs/model-sidecar/reference/`, and the generator writes `vectors/<section ID>.yaml` to
  `specs/model-sidecar/vectors/`. The candidate example does not land. After acceptance, the
  procedure [Reference examples](reference-examples.md) copies your real export.
- A proposal folder serves each model that needs it. Do not copy it into a model folder. The intake
  links to each proposal folder.
- `plans/sidecar/reference/` holds only the reference implementations of the current spec text
  ("Reference implementations"). The reference implementation of a proposal is in its folder.
- Use these names exactly. A skellytracker session finds the files with a scan of `plans/sidecar/`
  in each exporter repo. If your repo is not an exporter repo, tell the user or the skellytracker
  maintainers the path of your `plans/` folder.
- `plans/` is a local folder. Do not commit the files of `plans/sidecar/`.
- Before you write a file of `plans/sidecar/`, look for it. If it exists, read it and update it in
  place. Do not overwrite a file that you did not read. Git does not track `plans/`, so you cannot
  undo an overwrite.
- If you find a file with an old name (`plans/sidecar-intake-<model>.md`,
  `plans/sidecar-proposal-<slug>.md` or `plans/sidecar-reference-<section_module>.py`), move it to its
  new path. Move it, do not copy it. Tell the user.
- When you stop, tell the user about each file of `plans/sidecar/` that no current intake or proposal
  owns. Do not delete it.

### When a folder is complete

skellytracker shows when it has landed each file. A folder is complete when each of these items is
true:

- A model folder: the example of the model is in `specs/model-sidecar/inventory.yaml`, and each
  proposal folder that its intake links to is complete.
- A proposal folder: the proposal has `state: landed` or `state: rejected` in
  `specs/model-sidecar/proposals/README.md`.
- A file in `plans/sidecar/reference/`: `specs/model-sidecar/reference/<section_module>.py` exists,
  and your function is in `external_impl` of the section.

When a folder is complete, tell the user. The user deletes the folder. Do not delete it yourself.

## Files that you commit

Commit these files in your repo: the sidecar writer code, the host implementation of each section,
and the parity scripts. The intake and the proposals cite their commits.

## Inputs

Get these inputs before you start:

- the ONNX files;
- the upstream inference config;
- the upstream preprocessing code and postprocessing code;
- one reference output of the upstream library on a known image.

If an input is missing, do not stop. Write `missing` for it in the intake. Use the best secondary
source for the rows that need the input, and give each of these rows the verdict `unverified`. A
`near-miss` row or a `gap` row can rest on a secondary source (see "Rules"). When you stop, tell the
user which inputs are missing.

## A contributor with no git repo

If your code has no git repo yet, no commit exists. This rule was "An exporter with no git repo":

- Write `none (no git repo)` in each commit cell.
- Write `to run` as each parity result. A script without a commit is not evidence.
- In a vector file, write `unverified: <reason>` in place of `verified_against`.
- The intake and the proposals are allowed, but they are not complete. Complete them when the
  repo exists and the commits exist.

## In an exporter repo

These rules apply only to an agent or a person in an exporter repo:

- Read the sidecar part of the draft exporter guide first. Its entry point is
  `../freemocap/skellytracker/specs/draft/exporter-guide/sidecars/README.md`. Follow its heading "How to
  use this guide".
- Before each sidecar task, do the checkout steps of the draft exporter guide:
  `../freemocap/skellytracker/specs/draft/exporter-guide/sidecars/where-to-read.md`. They check the
  skellytracker checkout and its branch.

## Decisions

The decisions behind this workflow are in the skellytracker decision log:
[0013](../../../notes/decisions/0013-spec-structure.md) (section IDs, rule IDs, reference
implementations and test vectors), [0014](../../../notes/decisions/0014-spec-lifecycle.md) (the spec
lifecycle, the `vNEXT` rule and the new-model workflow),
[faac](../../../notes/decisions/faac-proposal-records.md) (the proposal records),
[vac0](../../../notes/decisions/vac0-record-a-changed-proposal.md) (a changed proposal) and
[x64y](../../../notes/decisions/x64y-draft-exporter-guide-folder.md) (this folder and the draft
exporter guide) and [b9fm](../../../notes/decisions/b9fm-finished-sidecar-plans.md) (the reference
examples procedure).

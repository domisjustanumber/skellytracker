# Read the spec

Read the sidecar spec, the templates and the skills in a skellytracker checkout. Read them only. In
an exporter repo, first do the checkout steps of
`../freemocap/skellytracker/specs/draft/exporter-guide/sidecars/where-to-read.md`.

## The branch

Read the spec on the skellytracker branch `dom/sidecar-implementation`. That branch has the newest
spec work. Do not read the spec from the skellytracker `development` branch. It does not have the
newest spec work. In a local checkout, examine the branch with
`git -C <checkout> branch --show-current`. If it gives a different branch, do not use that text.
Tell the user or the skellytracker maintainers the name of the branch.

## Files

| File | Use |
|---|---|
| `../freemocap/skellytracker/specs/model-sidecar/sidecar-spec.md` | The entry point of the spec. It is the permanent index: it keeps each old heading as an anchor with a link to the section file that holds the text now. |
| `../freemocap/skellytracker/specs/model-sidecar/README.md` | The section map: each section ID and its file. It also has the validation index and the meaning of **(vNEXT)**. |
| `../freemocap/skellytracker/specs/model-sidecar/format/`, `common/`, `pre/`, `post/` | The section files. They are the normative text of the spec. |
| `../freemocap/skellytracker/specs/model-sidecar/changelog.md` | The `vNEXT` summary of changes, the table "Considered and deliberately not added" and the `schema_version` history. |
| `../freemocap/skellytracker/specs/model-sidecar/examples/README.md` | The reference examples. They are not upstream evidence. |
| `../freemocap/skellytracker/specs/model-sidecar/inventory.yaml` | The provenance of each reference example. |
| `../freemocap/skellytracker/specs/model-sidecar/templates/model-intake.md` | The template for phase 1. |
| `../freemocap/skellytracker/specs/model-sidecar/templates/change-proposal.md` | The template for phase 2. |
| `../freemocap/skellytracker/.claude/skills/author-sidecar/SKILL.md` | The skill `author-sidecar`: the steps of phase 1 and of the reference-implementation step. |
| `../freemocap/skellytracker/.claude/skills/propose-sidecar-change/SKILL.md` | The skill `propose-sidecar-change`: the steps of phase 2. |
| `../freemocap/skellytracker/specs/model-sidecar/model-addition-workflow/README.md` | The entry point of this workflow. |
| `../freemocap/skellytracker/specs/draft/exporter-guide/sidecars/README.md` | The sidecar part of the draft exporter guide: the rules that only an exporter needs, the block for the exporter `AGENTS.md` and the checkout steps. |
| `../freemocap/skellytracker/specs/sidecar-implementation-plan.md` | The procedure that turns an exporter sidecar into a spec example ("Reference examples"). |
| `../freemocap/skellytracker/notes/decisions/` | The skellytracker decision log. |
| `../freemocap/skellytracker/skellytracker/` | The skellytracker package code. Read it for part 6 of a proposal. Do not import it. |

## The commit of the spec text

Write the skellytracker commit of the spec text that you read in the header of the intake or the
proposal. Get it with `git -C <checkout> rev-parse HEAD`. `<checkout>` is the folder of your
skellytracker checkout, for example `../freemocap/skellytracker`. Then run
`git -C <checkout> status --porcelain`. If it lists a file that you read, write
`+ uncommitted changes` after the commit.

## Path bases

A path that starts with `skellytracker/` or `specs/` names a file in the skellytracker repo. Read it
in your skellytracker checkout, for example `../freemocap/skellytracker/`. A path that starts with
`plans/` names a file in your repo. Both an exporter repo and skellytracker have a
`notes/decisions/` folder. Thus always write the repo name with the number of a decision entry, for
example "skellytracker decision 0012" or "OpenMMLab-Exporter 0020". In a file of the exporter, a
number without a repo name is a decision of that exporter.

## Decision entries

The skellytracker decision entries are informative. They give the reasons and the evidence for the
rules. The spec is normative. Read the [Model addition workflow](README.md#model-addition-workflow)
before your first intake. When this workflow or a template cites another entry, read that entry if
its topic applies to your model.

## Section IDs

The spec is split into section files under `specs/model-sidecar/`. `specs/model-sidecar/sidecar-spec.md`
is the index. The section map `../freemocap/skellytracker/specs/model-sidecar/README.md` lists each
section ID and its file. The section ID is the `id` in the front matter of the section file, for
example `pre.resize.letterbox`. Each validation rule has a rule ID in the form `V-<section-id>-<n>`,
for example `V-pre.resize.letterbox-1`. When this workflow names a spec heading, it also names the
section ID or the file that holds the heading.

## Vectors

A test vector is a small worked case for the algorithm of one section. The vectors of a section are
in `../freemocap/skellytracker/specs/model-sidecar/vectors/<section ID>.yaml`. If that file does not
exist, the section has no vectors.

## Reference examples are not evidence

The reference examples of the spec
(`../freemocap/skellytracker/specs/model-sidecar/examples/README.md`) show complete sidecars.
`../freemocap/skellytracker/specs/model-sidecar/inventory.yaml` records the provenance of each
example. They are not upstream evidence. Do not copy a value from an example into the intake. After
you fill in every row, compare your values with the example of the same family, if one exists. Record
each difference in the intake.

## Links to the spec

In a tracked file outside skellytracker, for example in an exporter, name the spec as
`specs/model-sidecar/sidecar-spec.md` of the skellytracker repo. That file is the permanent entry
point. The section map is `specs/model-sidecar/README.md`. You can also name a section file under
`specs/model-sidecar/`, for example `specs/model-sidecar/pre/resize-letterbox.md`. Do not link to a
URL of a branch. A branch URL breaks when the branch moves or when someone deletes it. Do not link to
the spec with a relative path into a local skellytracker checkout. That path does not resolve on
GitHub or in a different folder layout. It also points into a working tree that is often on a
feature branch. Name the spec in a code span: `specs/model-sidecar/sidecar-spec.md` of the
skellytracker repo.

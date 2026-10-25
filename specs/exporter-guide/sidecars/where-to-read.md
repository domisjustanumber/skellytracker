# Where to read the spec

- Read the sidecar spec, the templates and the skills in the skellytracker checkout
  `../freemocap/skellytracker`. Read it only.
- That checkout must be on the branch `dom/sidecar-implementation`. That branch has the newest spec
  work. Examine the branch: `git -C ../freemocap/skellytracker branch --show-current`.
- If the command gives a different branch, stop. Do not change the branch. Tell the user the name of
  the branch, and ask what to do.
- Do not read the spec from the skellytracker `development` branch. It does not have the newest spec
  work.
- Read the files as normal files. Then the relative links in the spec and in the skills resolve.
- If the folder `../freemocap/skellytracker` does not exist, stop. Ask the user which skellytracker
  folder to read. Then read only that folder, and write its path in the header of the intake or the
  proposal.
- Get the commit of the spec text that you read:
  `git -C ../freemocap/skellytracker rev-parse HEAD`. If you read another folder, use that
  folder in the command. Then run `git -C <folder> status --porcelain`. If it lists a file that you
  read, write `+ uncommitted changes` after the commit.
- Never edit a file in skellytracker.
- Never commit to skellytracker. Never change its branch.

| File | Use |
|---|---|
| `../freemocap/skellytracker/specs/sidecar-spec.md` | The entry point of the spec. It is the permanent index: it keeps each old heading as an anchor with a link to the section file that holds the text now. |
| `../freemocap/skellytracker/specs/sidecar/README.md` | The section map: each section ID and its file. It also has the validation index and the meaning of **(vNEXT)**. |
| `../freemocap/skellytracker/specs/sidecar/format/`, `common/`, `pre/`, `post/` | The section files. They are the normative text of the spec. |
| `../freemocap/skellytracker/specs/sidecar/changelog.md` | The `vNEXT` summary of changes, the table "Considered and deliberately not added" and the `schema_version` history. |
| `../freemocap/skellytracker/specs/sidecar/examples/README.md` | The reference examples. They are not upstream evidence. |
| `../freemocap/skellytracker/specs/sidecar/inventory.yaml` | The provenance of each reference example. |
| `../freemocap/skellytracker/specs/sidecar/templates/model-intake.md` | The template for phase 1. |
| `../freemocap/skellytracker/specs/sidecar/templates/change-proposal.md` | The template for phase 2. |
| `../freemocap/skellytracker/.claude/skills/author-sidecar/SKILL.md` | The skill `author-sidecar`: the steps of phase 1 and of the reference-implementation step. |
| `../freemocap/skellytracker/.claude/skills/propose-sidecar-change/SKILL.md` | The skill `propose-sidecar-change`: the steps of phase 2. |
| `../freemocap/skellytracker/specs/exporter-guide/sidecars/README.md` | The source of this section. |
| `../freemocap/skellytracker/specs/sidecar-implementation-plan.md` | The procedure that turns an exporter sidecar into a spec example ("Reference examples"). |
| `../freemocap/skellytracker/notes/decisions/` | The skellytracker decision log. |
| `../freemocap/skellytracker/skellytracker/` | The skellytracker package code. Read it for part 6 of a proposal. Do not import it. |

**Path bases.** A path that starts with `skellytracker/` or `specs/` names a file in the skellytracker
repo. Read it in `../freemocap/skellytracker/`. A path that starts with `plans/` names a file
in the exporter repo. Both repos have a `notes/decisions/` folder. Thus always write the repo name with
the number of a decision entry, for example "skellytracker decision 0012" or "OpenMMLab-Exporter
0020". In a file of the exporter, a number without a repo name is a decision of that exporter.

**Decision entries.** The skellytracker decision entries are informative. They give the reasons and
the evidence for the rules. The spec is normative. Read the
[New-model workflow](workflow/README.md#new-model-workflow) before your first intake. When this section or a template cites another entry, read that entry if its
topic applies to your model.

**Section IDs.** The spec is split into section files under `specs/sidecar/`. `specs/sidecar-spec.md`
is the index. The section map `../freemocap/skellytracker/specs/sidecar/README.md` lists each
section ID and its file. The section ID is the `id` in the front matter of the section file, for
example `pre.resize.letterbox`. Each validation rule has a rule ID in the form `V-<section-id>-<n>`,
for example `V-pre.resize.letterbox-1`. When this section names a spec heading, it also names the
section ID or the file that holds the heading.

**Vectors.** A test vector is a small worked case for the algorithm of one section. The vectors of a
section are in `../freemocap/skellytracker/specs/sidecar/vectors/<section ID>.yaml`. If that
file does not exist, the section has no vectors.

**Reference examples are not evidence.** The reference examples of the spec
(`../freemocap/skellytracker/specs/sidecar/examples/README.md`) show complete sidecars.
`../freemocap/skellytracker/specs/sidecar/inventory.yaml` records the provenance of each
example. They are not upstream evidence. Do not copy a value from an example into the intake. After
you fill in every row, compare your values with the example of the same family, if one exists. Record
each difference in the intake.

**Links to the spec.** In a tracked file of the exporter, name the spec as `specs/sidecar-spec.md` of
the skellytracker repo. That file is the permanent entry point. The section map is
`specs/sidecar/README.md`. You can also name a section file under `specs/sidecar/`, for example
`specs/sidecar/pre/resize-letterbox.md`. Do not link to a URL of a branch. A branch URL breaks when
the branch moves or when someone deletes it. Do not link to the spec with a relative path into a
local skellytracker checkout. That path does not resolve on GitHub or in a different folder layout.
It also points into a working tree that is often on a feature branch. Name the spec in a code span:
`specs/sidecar-spec.md` of the skellytracker repo.

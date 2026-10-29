# x64y — The model addition workflow, and the draft exporter guide in `specs/draft/`

**Status:** accepted, 2026-10-26 (user).

## Decision

This entry supersedes [0034](0034-sidecar-guide-folder.md) in full
([ngnb](ngnb-supersede-an-absorbed-entry.md)). Items 3 and 6 restate the rules of 0034 that stay.
Items 1 and 4 replace its rule "all guidance for exporters is in one folder".

1. **The workflow.** The process that adds a model and that requests a spec change is in
   [`specs/model-sidecar/model-addition-workflow/`](../../specs/model-sidecar/model-addition-workflow/README.md),
   with the title "Model addition workflow" ("new-model workflow" is a second name). It is the same
   for an exporter agent, a human contributor and a skellytracker session. It also holds the rules
   that apply to each contributor that writes a sidecar: `sidecar-files.md` (Independence, Sidecar
   YAML, Path) and `validation-and-publishing.md` (Validation, Publishing, `source` and hashes).
   `reading-the-spec.md` gives the branch to read, the files to read, the commit of the spec text,
   the path bases and the links to the spec.
2. **Not a spec section.** The workflow is normative for the process and for these rules. The
   section files are normative for the meaning of a sidecar. The workflow files have no front
   matter, no section ID and no rule ID. The spec overview and the permanent index link to it.
3. **Words, paths and files.** The workflow says "you" and "your repo" where a rule applies to each
   contributor. Its heading "In an exporter repo" holds the rules for an exporter repo only. In the
   templates, "the exporter" means the contributor. Code-span paths start at the root of an exporter
   repo, for example `../freemocap/skellytracker/specs/model-sidecar/README.md`. A contributor in a
   different layout replaces the prefix `../freemocap/skellytracker/`. Links between the workflow
   files are relative. In the workflow and in the draft guide, each file starts with one `#` title,
   and a file stays small. A `README.md` lists the files of its folder.
4. **The draft guide.** The guide to build an exporter is in
   [`specs/draft/exporter-guide/`](../../specs/draft/exporter-guide/README.md). It is not complete.
   It holds only the guidance that exporters need. Its `README.md` gives the status, the owner and
   the file list, and links to the workflow. `sidecars/` holds `README.md` (how to use the guide, the
   block for the exporter `AGENTS.md` and the "Sidecars" section), `where-to-read.md` (the checkout
   steps) and `known-open-items.md`. The files of `sidecars/` are complete, and they apply now. The
   guide is normative for the rules that it adds for exporters: the block for the exporter
   `AGENTS.md` and the checkout steps. Other parts go in new folders beside `sidecars/`.
5. **The owner and the final location.** A local plan of the user, the exporter implementation
   plan, owns the creation of the guide. A tracked file calls it "a local plan" and does not link to
   it. The plan is deleted at the end of its implementation work, when its content is in the guide.
   When the guide is complete, or when an end-to-end test proves that its first version works, the
   guide moves to `specs/exporter-guide/`. That move needs a new entry.
6. **No stub.** No file stays under `specs/exporter-guide/` until that move. No stub stays at an
   older path of the guide, for example `specs/sidecar/exporter-guide.md`. A link to a moved file
   goes to its new path and anchor. A decided entry with such a link gets a link-repair `_Edited_`
   line. A plain-text mention of an old path in a decided entry stays, because it is history. A
   later rewording PR removes each exporter repository name that is only an example from the guide
   and from the model addition workflow. A citation of an exporter entry or commit as evidence
   stays. The PR also removes the open items that do not apply to a new exporter.
7. **The block.** The source line of the block for the exporter `AGENTS.md` names
   `specs/draft/exporter-guide/sidecars/README.md`. The block names the workflow too.

## Reason

- The workflow is not specific to an exporter. A human contributor follows the same phases, rules,
  evidence, parity and proposal parts. The spec, its templates and its proposals are in
  `specs/model-sidecar/`, so the process that changes the spec belongs beside them.
- The rules for the sidecar files, the validation and the publishing apply to each contributor that
  writes a sidecar. A normative process must not cite rules in a draft folder.
- The folder `specs/draft/` tells each reader that the guide is not complete. The planned guide has
  `sidecars/` beside its other parts, so the sidecar files do not move again.
- The user chose no stub (2026-10-26). One owner prevents two competing designs.

## Consequences

- An exporter agent reads two folders: the draft guide and the workflow. The block names both.
- The exporter copies of the old block name `specs/exporter-guide/sidecars/README.md`. That path does
  not exist now. Each exporter copies the block again.
- The exporter files and the recorded proposals cite old paths, some with line numbers at a pinned
  commit. Those citations stay correct at their commit.

## Alternatives rejected

- **Keep the guide in `specs/exporter-guide/`.** The path does not tell that the guide is not
  complete.
- **Make the workflow a spec section.** A section has a section ID, rule IDs and selectors. The
  workflow has no sidecar field.
- **Keep `sidecar-files.md` and `validation-and-publishing.md` in the draft guide.** Their rules apply
  to each contributor.
- **A stub at the old entry point.** It keeps a second place to read, and each search of a path
  gives more results.

_Edited 2026-10-28 (this PR): link repair._

_Edited 2026-10-29 (this PR): link repair._

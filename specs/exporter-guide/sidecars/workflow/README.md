# New-model workflow

Use this workflow for each new model. In an exporter repo, do phase 1 and phase 2. Then stop. A
skellytracker session does phase 3.

Two skills give the steps of phase 1 and phase 2. They use the rules of this section:

- `author-sidecar` (`../freemocap/skellytracker/.claude/skills/author-sidecar/SKILL.md`):
  phase 1 and the reference-implementation step.
- `propose-sidecar-change`
  (`../freemocap/skellytracker/.claude/skills/propose-sidecar-change/SKILL.md`): phase 2.

Read each skill file in the skellytracker checkout. Do its steps in order.

**Files in `plans/`.** Write these files in the `plans/` folder of the exporter repo:

| File | Content |
|---|---|
| `plans/sidecar-intake-<model>.md` | The filled model intake template (phase 1). One file for each family. |
| `plans/sidecar-proposal-<slug>.md` | One change proposal for each gap (phase 2). |
| `plans/sidecar-reference-<section_module>.py` | One reference implementation for each section that you implemented on the host side (see "Reference implementations"). |

- `<model>` is the `model_id` of the family.
- `<slug>` is a short lowercase name of the proposed change, with hyphens, for example
  `letterbox-floor-rounding`.
- `<section_module>` names one section. "Reference implementations" gives the rule.
- Use these file names exactly. A skellytracker session finds the files with a scan of
  `plans/sidecar-*` in each exporter repo.
- `plans/` is a local folder. Do not commit the `plans/sidecar-*` files.
- Before you write a `plans/sidecar-*` file, look for it. If it exists, read it and update it in
  place. Do not overwrite a file that you did not read. Git does not track `plans/`, so you cannot
  undo an overwrite.
- When you stop, tell the user about each `plans/sidecar-*` file that no current intake or proposal
  owns. Do not delete it.

**Files that you commit.** Commit these files in the exporter repo: the sidecar writer code, the host
implementation of each section, and the parity scripts. The intake and the proposals cite their
commits.

**Inputs.** Get these inputs before you start:

- the ONNX files;
- the upstream inference config;
- the upstream preprocessing code and postprocessing code;
- one reference output of the upstream library on a known image.

If an input is missing, do not stop. Write `missing` for it in the intake. Use the best secondary
source for the rows that need the input, and give each of these rows the verdict `unverified`. A
`near-miss` row or a `gap` row can rest on a secondary source (see "Rules"). When you stop, tell the
user which inputs are missing.

**An exporter with no git repo.** If the exporter has no git repo yet, no commit exists:

- Write `none (no git repo)` in each commit cell.
- Write `to run` as each parity result. A script without a commit is not evidence.
- In a vector file, write `unverified: <reason>` in place of `verified_against`.
- The intake and the proposals are allowed, but they are not complete. Complete them when the
  exporter has a git repo and the commits exist.

The workflow is split into these files:

- [Phase 1: can the current spec describe the model?](phase-1-intake.md)
- [Parity](parity.md)
- [Mapping hints for phase 1](mapping-hints.md)
- [Phase 2: propose a spec change and its implementation](phase-2-proposal.md)
- [Phase 3: what skellytracker does next](phase-3-skellytracker.md)

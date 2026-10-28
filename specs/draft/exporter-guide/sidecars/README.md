# Sidecar exporter guide

This guide gives the rules that exporters follow when they write sidecars. An exporter is a repo
that makes ONNX files and writes their sidecars: OpenMMLab-Exporter, Roboflow-Exporter,
Ultralytics-Exporter, Qualcomm-Exporter and MediaPipe-Exporter.

This folder is the sidecar part of the [draft exporter guide](../README.md). The draft guide is not
complete. The rules in this folder are complete, and they apply now.

The [sidecar spec](../../../model-sidecar/sidecar-spec.md) is normative for the meaning of a sidecar. The
[model addition workflow](../../../model-sidecar/model-addition-workflow/README.md) is normative for the
process: it tells how to apply the spec to a new model, and how to request a spec change. That
workflow is the same for each contributor. It also holds the rules for the sidecar files, the
validation and the publishing. This guide is normative for the rules that it adds for exporters: the
block for the exporter `AGENTS.md` and the checkout steps. It does not change the meaning of the
spec. If this guide and the spec do not agree, the spec is correct.

## How to use this guide

- skellytracker sessions do not change exporter repos. They can read them. The exporters will be
  overhauled soon, and each overhaul adopts this guide. (Decided by the user on 2026-10-22.)
- Only skellytracker sessions write the skellytracker repo. The only exception: an exporter agent
  writes the new version folders of its own bundles in `intakes/` of the checkout
  ([Hand-over bundles](../../../model-sidecar/model-addition-workflow/hand-over.md);
  [ADR-FADS](../../../../decisions/FADS-hand-over-bundles-in-intakes.md)). There is no spec freeze.
- An exporter overhaul copies the fenced block of
  [The block for the exporter `AGENTS.md`](#the-block-for-the-exporter-agentsmd) into the exporter's
  `AGENTS.md`. It copies the block without change, and fills in only the commit of the source line.
  Do not copy the [Sidecars](#sidecars) section. The block tells the agents of that exporter to read
  the Sidecars section here before each sidecar task, and to follow the model addition workflow.
- Before its overhaul, an exporter agent runs the workflow only when the user asks. Then it writes only
  the files of its bundles, unless the user permits more.
- The Sidecars section names each file by its path in the skellytracker checkout, in a code span. It has
  no relative Markdown links, because exporter agents open its paths from the root of the exporter
  repo. The block for the exporter `AGENTS.md` has no relative links, because relative links break
  when the block is copied to another repo. For the same reason, the change proposal template has no
  relative links to other files. The model
  intake template has them only in the section column of its property tables.
- The skellytracker paths in the Sidecars section start at the root of the exporter repo. The exporter repos
  and the `freemocap` folder must be in the same parent folder.
- When the block changes here, the exporters copy it again. A change of the Sidecars section needs no
  copy, because the agents read the section here.
- Two skills wrap the model addition workflow for exporter agents:
  [`author-sidecar`](../../../../.claude/skills/author-sidecar/SKILL.md) for phase 1 and the
  reference-implementation step, and
  [`propose-sidecar-change`](../../../../.claude/skills/propose-sidecar-change/SKILL.md) for phase 2. The
  skills give the steps, the inputs, the outputs and the stop points. They link to the workflow and
  to this guide for the rules. The model addition workflow stays the full workflow.

The decisions behind this guide:

- [0013](../../../../decisions/0013-spec-structure.md): section IDs, rule IDs, reference
  implementations and test vectors. [ADR-TA0G](../../../../decisions/TA0G-vector-cases-and-reference-modules.md) supersedes it. It gives
  the vector cases and the reference modules.
- [0014](../../../../decisions/0014-spec-lifecycle.md): the spec lifecycle, the `vNEXT` rule and the
  new-model workflow. The workflow headings
  [Stages](../../../model-sidecar/model-addition-workflow/README.md#stages) and
  [Publishing](../../../model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing)
  state its rules now. [ADR-FADS](../../../../decisions/FADS-hand-over-bundles-in-intakes.md) supersedes it.
- [0016](../../../../decisions/0016-sidecar-catalogs.md): sidecar catalogs: `source`, reference
  hashes, roots, discovery and the capability check. The spec text for exporters is in
  [`common.identity`](../../../model-sidecar/common/identity.md#fields) (`source`),
  [`format.composition`](../../../model-sidecar/format/composition.md#reference-hashes) (the reference hashes and the bytes
  of a file) and
  [`common.sizes_and_artifacts`](../../../model-sidecar/common/sizes-and-artifacts.md#sizessizeonnxbatch_artifacts) (the
  artifact hashes and the placeholder). The rule for each contributor is
  [`source` and hashes](../../../model-sidecar/model-addition-workflow/validation-and-publishing.md#source-and-hashes)
  in the model addition workflow.
- [x64y](../../../../decisions/x64y-draft-exporter-guide-folder.md): the model addition workflow
  is in `specs/model-sidecar/model-addition-workflow/`, with the rules for the sidecar files, the
  validation and the publishing. This guide is in the draft folder `specs/draft/exporter-guide/`.

The spec is split into section files under `specs/model-sidecar/`. The entry point is
[`specs/model-sidecar/sidecar-spec.md`](../../../model-sidecar/sidecar-spec.md): it is the permanent index, and it keeps each old
heading as an anchor with a link to the section file that holds the text now. The section map is
[`specs/model-sidecar/README.md`](../../../model-sidecar/README.md#section-map). It lists each section ID and its file. The
sections and headings that this guide uses most:
[`input.resize`](../../../model-sidecar/common/input.md#inputresize), [`sizes`](../../../model-sidecar/common/sizes-and-artifacts.md#sizes),
[Storage layout](../../../model-sidecar/format/file-layout.md#storage-layout),
[Schema versioning](../../../model-sidecar/format/versioning.md),
[Version-aware compatibility](../../../model-sidecar/format/versioning.md#version-aware-compatibility) (the index of the
"Legacy behaviour" heading of each section),
[Validation rules](../../../model-sidecar/README.md#validation-rules) (the validation index),
[Considered and deliberately not added](../../../model-sidecar/changelog.md#considered-and-deliberately-not-added) and
[Reference examples](../../../model-sidecar/examples/README.md), with the provenance of each example in
[`inventory.yaml`](../../../model-sidecar/inventory.yaml).
The templates are [model intake](../../../model-sidecar/templates/model-intake.md) and
[change proposal](../../../model-sidecar/templates/change-proposal.md).

## The block for the exporter `AGENTS.md`

Copy the text inside the fence into the exporter's `AGENTS.md`, after section 4. Replace `<commit>`
with the commit of the skellytracker checkout. Make no other change. The block must have fewer
than 2,000 characters.

```markdown
## Sidecars

Source: `../freemocap/skellytracker/specs/draft/exporter-guide/sidecars/README.md`, skellytracker commit `<commit>`.
Do not change this section here. Copy it again when the source changes.

- The sidecar spec is in the skellytracker checkout `../freemocap/skellytracker`. Read it there,
  read-only. Do not change a file in that checkout. The only exception: the new version folders of
  your own bundles in `intakes/`. Read
  `../freemocap/skellytracker/specs/model-sidecar/model-addition-workflow/hand-over.md`.
- Before each sidecar task, read the section "Sidecars" of
  `../freemocap/skellytracker/specs/draft/exporter-guide/sidecars/README.md`. Follow the workflow in
  `../freemocap/skellytracker/specs/model-sidecar/model-addition-workflow/README.md`.
- For workflow phase 1, use the skill
  `../freemocap/skellytracker/.claude/skills/author-sidecar/SKILL.md`. For workflow phase 2, use
  the skill `../freemocap/skellytracker/.claude/skills/propose-sidecar-change/SKILL.md`.
- The spec is normative. Do not change its meaning in docs or code.
- If a model property does not map exactly to the spec, do not use an approximate mapping. Write a
  change proposal and stop.
- Cite primary evidence: an upstream file and line, an upstream config key, or a read of the ONNX
  graph. Mark each secondary source `(secondary)`.
- Do not publish a `vNEXT` sidecar to a shared or remote folder. Publish a sidecar only after the
  release step ("Publishing" in
  `../freemocap/skellytracker/specs/model-sidecar/model-addition-workflow/validation-and-publishing.md`).
```

## Sidecars

The Sidecars section is split into these files:

- [Where to read the spec](where-to-read.md): the skellytracker checkout and its branch
- [Model addition workflow](../../../model-sidecar/model-addition-workflow/README.md): reading the spec,
  the rules, phases 1 to 3, parity, the mapping hints and the reference implementations. It is in
  `../freemocap/skellytracker/specs/model-sidecar/model-addition-workflow/`.
- [Sidecar files](../../../model-sidecar/model-addition-workflow/sidecar-files.md): Independence,
  Sidecar YAML, Path. It is in the model addition workflow.
- [Validation and publishing](../../../model-sidecar/model-addition-workflow/validation-and-publishing.md):
  Validation, Publishing, `source` and hashes. It is in the model addition workflow.

The [known open items for the exporter overhaul](known-open-items.md) are not a part of the Sidecars section.

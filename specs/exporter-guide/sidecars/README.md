# Sidecar exporter guide

This guide gives the rules that exporters follow when they write sidecars. An exporter is a repo
that makes ONNX files and writes their sidecars: OpenMMLab-Exporter, Roboflow-Exporter,
Ultralytics-Exporter, Qualcomm-Exporter and MediaPipe-Exporter.

The [sidecar spec](../../sidecar-spec.md) is normative for the meaning of a sidecar. This guide is
normative for the workflow: it tells how to apply the spec to a new model. It does not change the
meaning of the spec. If this guide and the spec do not agree, the spec is correct.

## How to use this guide

- skellytracker sessions do not change exporter repos. The exporters will be overhauled soon, and each
  overhaul adopts this guide. (Decided by the user on 2026-10-22.)
- An exporter overhaul copies the fenced block of
  [The block for the exporter `AGENTS.md`](#the-block-for-the-exporter-agentsmd) into the exporter's
  `AGENTS.md`. It copies the block without change, and fills in only the commit of the source line.
  Do not copy the [Sidecars](#sidecars) section. The block tells the agents of that exporter to read
  the Sidecars section here before each sidecar task, and to follow its workflow.
- Before its overhaul, an exporter agent runs the workflow only when the user asks. Then it writes only
  the `plans/sidecar-*` files, unless the user permits more.
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
- Two skills wrap the workflow of the Sidecars section for exporter agents:
  [`author-sidecar`](../../../.claude/skills/author-sidecar/SKILL.md) for phase 1 and the
  reference-implementation step, and
  [`propose-sidecar-change`](../../../.claude/skills/propose-sidecar-change/SKILL.md) for phase 2. The
  skills give the steps, the inputs, the outputs and the stop points. They link to this guide for the
  rules. The Sidecars section stays the full workflow.

The decisions behind this guide:

- [0013](../../../notes/decisions/0013-spec-structure.md): section IDs, rule IDs, reference
  implementations and test vectors.
- [0014](../../../notes/decisions/0014-spec-lifecycle.md): the spec lifecycle, the `vNEXT` rule and the
  new-model workflow.
- [0016](../../../notes/decisions/0016-sidecar-catalogs.md): sidecar catalogs: `source`, reference
  hashes, roots, discovery and the capability check. The spec text for exporters is in
  [`common.identity`](../../sidecar/common/identity.md#fields) (`source`),
  [`format.composition`](../../sidecar/format/composition.md#reference-hashes) (the reference hashes and the bytes
  of a file) and
  [`common.sizes_and_artifacts`](../../sidecar/common/sizes-and-artifacts.md#sizessizeonnxbatch_artifacts) (the
  artifact hashes and the placeholder). The rule for exporters is
  [`source` and hashes](validation-and-publishing.md#source-and-hashes).

The spec is split into section files under `specs/sidecar/`. The entry point is
[`specs/sidecar-spec.md`](../../sidecar-spec.md): it is the permanent index, and it keeps each old
heading as an anchor with a link to the section file that holds the text now. The section map is
[`specs/sidecar/README.md`](../../sidecar/README.md#section-map). It lists each section ID and its file. The
sections and headings that this guide uses most:
[`input.resize`](../../sidecar/common/input.md#inputresize), [`sizes`](../../sidecar/common/sizes-and-artifacts.md#sizes),
[Storage layout](../../sidecar/format/file-layout.md#storage-layout),
[Schema versioning](../../sidecar/format/versioning.md),
[Version-aware compatibility](../../sidecar/format/versioning.md#version-aware-compatibility) (the index of the
"Legacy behaviour" heading of each section),
[Validation rules](../../sidecar/README.md#validation-rules) (the validation index),
[Considered and deliberately not added](../../sidecar/changelog.md#considered-and-deliberately-not-added) and
[Reference examples](../../sidecar/examples/README.md), with the provenance of each example in
[`inventory.yaml`](../../sidecar/inventory.yaml).
The templates are [model intake](../../sidecar/templates/model-intake.md) and
[change proposal](../../sidecar/templates/change-proposal.md).

## The block for the exporter `AGENTS.md`

Copy the text inside the fence into the exporter's `AGENTS.md`, after section 4. Replace `<commit>`
with the commit of the skellytracker checkout. Make no other change.

```markdown
## Sidecars

Source: `../freemocap/skellytracker/specs/exporter-guide/sidecars/README.md`, skellytracker commit `<commit>`.
Do not change this section here. Copy it again when the source changes.

- The sidecar spec is in the skellytracker checkout `../freemocap/skellytracker`. Read it there,
  read-only. Do not change a file in that checkout.
- Before each sidecar task, read the section "Sidecars" of
  `../freemocap/skellytracker/specs/exporter-guide/sidecars/README.md`. Follow its new-model workflow.
- For workflow phase 1, use the skill
  `../freemocap/skellytracker/.claude/skills/author-sidecar/SKILL.md`. For workflow phase 2, use
  the skill `../freemocap/skellytracker/.claude/skills/propose-sidecar-change/SKILL.md`.
- The spec is normative. Do not change its meaning in docs or code.
- If a model property does not map exactly to the spec, do not use an approximate mapping. Write a
  change proposal and stop.
- Cite primary evidence: an upstream file and line, an upstream config key, or a read of the ONNX
  graph. Mark each secondary source `(secondary)`.
- Do not publish a `vNEXT` sidecar to a shared or remote folder. Publish a sidecar only after the
  release step of skellytracker decision 0014.
```

## Sidecars

The Sidecars section is split into these files:

- [Where to read the spec](where-to-read.md)
- [Rules](rules.md)
- [New-model workflow](workflow/README.md)
- [Reference implementations](reference-implementations.md)
- [Sidecar files](sidecar-files.md): Independence, Sidecar YAML, Path
- [Validation and publishing](validation-and-publishing.md): Validation, Publishing, `source` and hashes

The [known open items for the exporter overhaul](known-open-items.md) are not a part of the Sidecars section.

# 0033 — A short "Sidecars" block for the exporter `AGENTS.md`

**Status:** absorbed into [`exporter-guide/sidecars/README.md#the-block-for-the-exporter-agentsmd`](../../specs/exporter-guide/sidecars/README.md#the-block-for-the-exporter-agentsmd), 2026-10-25 (user; the absorption review).

## Decision

1. **The block.** The [exporter guide](../../specs/exporter-guide/sidecars/README.md#the-block-for-the-exporter-agentsmd)
   has a short block in a fenced code block. An exporter copies the text inside the fence into its
   `AGENTS.md`, after section 4. It fills in only the skellytracker commit of the source line.
2. **No copy of the Sidecars section.** The exporter does not copy the
   [Sidecars](../../specs/exporter-guide/sidecars/README.md#sidecars) section. The block tells the exporter
   agents to read that section in the skellytracker checkout before each sidecar task, and to follow
   its new-model workflow.
3. **The content of the block.** Where to read the spec, the two skills, and the sidecar rules that
   every session needs: the spec is normative, no approximate mapping, primary evidence, and no
   publication before the release step. The block has no relative Markdown links. It is shorter than
   2,000 characters.
4. **Copy again.** When the block changes, the exporters copy it again. A change of the Sidecars
   section needs no copy.

## Reason

- The Sidecars section is about 45,000 characters. A copy in each exporter `AGENTS.md` is read in each
  session, also when the session does no sidecar work.
- The exporter `AGENTS.md` must stay short. The user set the target: the filled file is shorter than
  10,000 characters.
- A copy goes out of date when the section changes. A read in place does not.
- The block is in a fenced code block, not under a second `## Sidecars` heading. A second heading
  would take the `#sidecars` anchor that the skills and the templates link to.

## Consequences

- The two HTML comments that marked the old copy unit are removed.
- An exporter agent needs the skellytracker checkout for each sidecar task. The guide already
  requires it.

## Alternatives rejected

- **Keep the full copy.** It makes the exporter `AGENTS.md` about 50,000 characters, and each change
  of the section needs a copy in each exporter.
- **Link only, with no rules in the block.** The four rules of the block apply in each session, also
  before the agent opens the guide.

_Edited 2026-10-24 (this PR): link repair._

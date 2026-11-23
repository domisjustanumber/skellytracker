# Decision log

This log records the technical decisions for skellytracker that affect more than one module, with
their reasons and evidence. The [spec log](../specs/model-sidecar/decisions/README.md) holds the
decisions of the sidecar spec only ([ADR-GN3D](entries/GN3D-module-decision-logs.md)). The
[pipeline spec log](../specs/pipeline/decisions/README.md) holds the decisions of the pipeline spec
only ([ADR-3SF2](entries/3SF2-pipeline-spec-and-node-workflow.md)). Read this file before you change the spec, a sidecar, the
sidecar code, the agent instructions or the PR workflow. Also read [open-work.md](open-work.md). The
[Rules](#rules) tell you which entries to read.

Each entry gives the decision, its reason, the evidence (when there is evidence), the alternatives
rejected and a "Not repeated" section for pitfalls already found. Entries 0002 to 0012, here and in
the spec log, are backfilled. They record decisions made before this log existed, and they cite the original sources.
When a decision changes, add a new entry that supersedes the old entry in full. The body of a
decided entry changes only by the edits that the skill
[`change-decision-log`](../.claude/skills/change-decision-log/SKILL.md) allows. To write an entry,
load that skill and use [template.md](template.md).

## Index

### Active

These entries are `accepted`.

| # | Decision | Status |
|---|----------|--------|
| [AMJ8](entries/AMJ8-replace-package-onnx-detectors.md) | Replace the package ONNX detectors with exporter models; no legacy layer; shipped sidecars in `core/model_zoo/`; RTMPose replacements block v2.0.0 | accepted |
| [0XW9](entries/0XW9-entry-points-layout-guard-test-and-session-code.md) | Entry points `detectors` and `pipelines`; `system/`, `metrics/`, `eps/` under an eager `core`; one `eps` guard test; new session code in `core/eps/` | accepted |
| [NHM3](entries/NHM3-phases-to-the-exporter-checkpoint.md) | Phase 0 and phase 1 to the exporter checkpoint; pre-release at the checkpoint; new code beside old; supersedes EM74 | accepted |
| [P1F3](entries/P1F3-hardware-probe-devices-and-multi-gpu.md) | Hardware probe fields; `free_vram`; `device_key`; default GPU by VRAM; a run splits its cameras across GPUs; no pre-Turing GPUs | accepted |
| [P0JZ](entries/P0JZ-certify-contract-in-each-package.md) | `certify(level)` in each package; reports to `skellycertify`; any recorded build is evidence; OS and EP layers | accepted |
| [21BK](entries/21BK-quick-check-local-pass-and-hand-in.md) | Quick check in a child process on the user's pipeline; local pass; hard failures; passive record; hand-in | accepted |
| [1N9Y](entries/1N9Y-ep-store-install-and-certification-consolidation.md) | Consolidation of MF2R: EP catalog, lock and store; download after the user accepts; the evidence file; the pass rule; links to the documents that state them | accepted |
| [0Q48](entries/0Q48-certify-suite-consolidation.md) | Consolidation of Y14H: the certify suite command, its sections in child processes, consent, privacy and the model files; the replaced items are listed | accepted |
| [6A1Y](entries/6A1Y-field-test-and-amd-eps-consolidation.md) | Consolidation of Z5X7 and XSE7: the field-test state and its opt-in, built-in `directml`, the `migraphx` ROCm packs and the Windows ML EPs | accepted |
| [4RWX](entries/4RWX-sessions-and-errors-consolidation.md) | Consolidation of D8DH: `core/errors.py`, the exit-code table, the ready rule, `build_session()` and no EP variables | accepted |
| [J4SH](entries/J4SH-pipeline-api-second-consolidation.md) | Second consolidation of the pipeline entries: links to the pipeline spec and the package docstrings, and the Python API text that they do not state | accepted |
| [4JAW](entries/4JAW-rulings-of-2026-11-23-on-sessions-the-certify-prompt-and-linux.md) | Thread counts and optimization level as session attributes; freemocap stores "do not ask again"; catalog sets `enable_cuda_graph`; Linux only through certify | accepted |

### Proposed

These entries wait for a decision of the user. Section is the spec section of the change, or `none`
when the change has no one section. The spec change proposals of the sidecar spec are in the
[spec log](../specs/model-sidecar/decisions/README.md#proposed).

| # | Decision | Section | Status |
|---|----------|---------|--------|

The entries that are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX`, `evidence; replaced by XXXX` or `done` are in [historical.md](historical.md).
The entries that are `evidence` are in [evidence.md](evidence.md).

## Open work

The open work and the repository state are in [open-work.md](open-work.md). The spec defects are
in the [open work of the spec log](../specs/model-sidecar/decisions/open-work.md). The
implementation-stage work is in the [implementation plan](../specs/sidecar-implementation-plan.md).

## Rules

- Read the Active entries that apply to your task. Then you do not repeat a settled question. Before
  you make a measurement, scan the rows of `evidence.md` of each log, and read the entries that
  apply. Then you do not repeat a completed measurement. `evidence.md` and its entries are not in
  the read path ([ADR-FJG4](entries/FJG4-evidence-file-and-the-skill-for-log-changes.md)). Read a Proposed entry only for spec work in its section, or when a skill
  tells you to. Read an entry of [historical.md](historical.md) only to find the reason for a
  decision ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).
- A decision that a document or code refers to must be in an entry. "This log" in an older entry or
  in the Rules means all logs ([ADR-2XW6](entries/2XW6-process-entries-consolidation.md)).
- Delete an open-work item when the work is done. Put a dated fact in `open-work.md` or in an
  entry, not in `AGENTS.md`.
- Before you add or change an entry, a status or a row of a table, load the skill
  [`change-decision-log`](../.claude/skills/change-decision-log/SKILL.md). It gives the rules for
  each change to a log ([ADR-FJG4](entries/FJG4-evidence-file-and-the-skill-for-log-changes.md)).

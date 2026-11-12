# Spec change proposals

This folder holds the spec change proposals that skellytracker has recorded. Each proposal has one
folder, `<slug>/`. The folder is a byte copy of one version of a `proposal` bundle, with its
`manifest.yaml`
([Tracked records](../model-addition-workflow/hand-over.md#tracked-records);
[ADR-ZXD7](../../../decisions/entries/ZXD7-bundle-process.md)).

The files are informative. A proposal is not normative until a content commit lands its text in the
section files. Each record has one decision entry `<id>-<slug>.md` in the
[spec log](../decisions/README.md). The status of that entry is the state of the proposal
([States](../model-addition-workflow/hand-over.md#states)). The skill
[`propose-sidecar-change`](../../../.claude/skills/propose-sidecar-change/SKILL.md) records a
proposal. The skill [`change-sidecar-spec`](../../../.claude/skills/change-sidecar-spec/SKILL.md)
lands it.

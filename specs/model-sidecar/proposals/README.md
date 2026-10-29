# Spec change proposals

This folder holds the spec change proposals that skellytracker has recorded. Each proposal has one
folder, `<slug>/`. The folder is a byte copy of one version of a `proposal` bundle, with its
`manifest.yaml`
([Tracked records](../model-addition-workflow/hand-over.md#tracked-records);
[ADR-FADS](../../../decisions/entries/FADS-hand-over-bundles-in-intakes.md)).

The files are informative. A proposal is not normative until a content commit lands its text in the
section files. The row of this index is the only place of the state of a proposal. The skill
[`propose-sidecar-change`](../../../.claude/skills/propose-sidecar-change/SKILL.md) records a
proposal. The skill [`change-sidecar-spec`](../../../.claude/skills/change-sidecar-spec/SKILL.md)
lands it.

`State` is `recorded`, `accepted`, `landed`, `rejected` or `resolved-otherwise`
([States](../model-addition-workflow/hand-over.md#states)). A `resolved-otherwise` row links the
entry of the change that landed. `Bundle version` is `<bundle id>@v<k>`: provenance text, not a
path.

| Proposal | Section | Contributor | Bundle version | Decision | State |
|---|---|---|---|---|---|

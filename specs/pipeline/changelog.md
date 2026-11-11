# Changelog

This file records each content change of the pipeline spec. It starts with the first content commit
([ADR-3SF2](../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 5). The form of
the lines is the form of the [sidecar changelog](../model-sidecar/changelog.md#revisions).

## Summary of changes

| # | Area | Change | Driven by | Section |
|---|------|--------|-----------|---------|
| 1 | Pipeline | Draft pipeline spec: the six pipeline sections and the ten node sections. | [ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md), [ADR-99MH](../../decisions/entries/99MH-pipeline-outputs-and-running.md), [ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md), [ADR-8NVD](../../decisions/entries/8NVD-pipeline-api-warnings-and-catalog.md), [ADR-3SF2](../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) | [Section map](README.md#section-map) |

## Revisions

A spec version is the skellytracker version, in SemVer, that first releases a spec change. Each
heading below is one spec version. The open target is the next skellytracker release that includes
a spec change ([ADR-6GE2](../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).

Each version heading has these lines:

- `- Released: no.` or `- Released: yes.`: the first line. The open target has `no`.
- ``- Row N: `<fingerprint>`.``: each content commit appends one such line under the open target,
  with no version bump. `N` is the highest row number of the
  [summary of changes](#summary-of-changes). The fingerprint is the SHA-256 of the headings and the
  `V-` rule lines of the section files of this spec. `tools/tests/test_pipeline_changelog.py`
  checks it. When the value is not current, that test fails and gives the new value.
- `- Pre-release X.Y.Z-<tag>: row N.`: the session of a skellytracker pre-release appends this
  line under its target. `N` is the last row that the pre-release holds.

### 2.0.0

- Released: no.
- Row 1: `c1c50d709ebb29d3fa6e100452a6635f0d9a41e4b181a79b9ef7600de471817f`.

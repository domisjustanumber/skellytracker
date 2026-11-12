# A2CW — A dataset owner page is enough evidence

**Status:** absorbed into [`model-addition-workflow/rules.md#rules`](../../specs/model-sidecar/model-addition-workflow/rules.md#rules), 2026-11-10 (user; PR: pending).

## Decision

For a `license` row of the model intake, a page or a README of the owner of a dataset is enough
evidence for the license and the contents of that dataset. An example is the list of datasets that a
combined annotation file holds. The row gives the URL, and the commit or the date of the read
([Rules](../../specs/model-sidecar/model-addition-workflow/rules.md#rules)). The model intake template
states the rule in the notes of its table "License". This entry adds to
[ADR-V8FK](V8FK-license-evidence-and-models-with-no-license.md) item 1. It does not change it.

## Reason

- The user ruled in the OpenMMLab-Exporter session, 2026-11-09, that the Human-Art README is good
  enough evidence that the YOLOX training file holds COCO 2017 and Human-Art. In this session the
  user asked for the ruling as a general rule ("yes").
- The rules name a README as a secondary source. Without this rule, a strict reading makes such a
  row `unverified`, also when the owner of the dataset is the only source and the file is not
  public.

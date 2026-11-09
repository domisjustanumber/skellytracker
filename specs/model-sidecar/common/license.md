---
id: common.license
title: License and training data
kind: common
selectors: []
implemented_by:
  validate: missing  # SidecarModel forbids the key license (skellytracker/core/sidecar/model.py::SidecarModel). No code checks V-common.license-1 to V-common.license-7.
  load: missing  # No code reads license.
external_impl: []
tests: []
vectors: vectors/common.license.yaml
status: {spec: draft, validate: missing, load: missing}
---

# License and training data

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The `license` block gives the license of the weights and the training data of the weights. A user must know if a model can go into a product. The terms of a dataset can restrict the use of the weights, so the model license alone does not answer this ([ADR-NBG2](../decisions/entries/NBG2-license-and-training-data-without-the-deferred-examples.md)). All sizes of a family share these fields. Sizes that differ in license or data are two families.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `license` | object | yes | The keys `model` and `training_data`, and `training_data_unknown_reason` only when `training_data` is `unknown`. |
| `license.model` | license object | yes | The license of the weights. |
| `license.training_data` | array or `unknown` | yes | One dataset entry for each dataset that made the weights. This includes each dataset of a checkpoint that the training started from, and each dataset of a distillation teacher ([ADR-1BS2](../decisions/entries/1BS2-distillation-teacher-is-a-start-checkpoint.md)). |
| `license.training_data_unknown_reason` | string | only with `training_data: unknown` | Why the datasets are not known ([Behaviour](#behaviour)). |
| `license.training_data[].name` | string | yes | The name of the dataset. |
| `license.training_data[].url` | string | no | A public page of the dataset. |
| `license.training_data[].use` | enum | yes | `pretraining` (the dataset made a checkpoint that the training started from, or a distillation teacher) or `training`. |
| `license.training_data[].license` | license object | yes | The license of the dataset. |
| license object `id` | string | yes | An SPDX license expression, or `unknown`. An expression can hold a `LicenseRef-<name>` id for a license that the SPDX License List does not list. |
| license object `url` | string | no | The license text. It is required for a `LicenseRef-` id (`V-common.license-3`). |
| license object `unknown_reason` | string | only with `id: unknown` | Why the license is not known ([Behaviour](#behaviour)). |

## Behaviour

- Write `unknown` only after research that finds no answer.
- Write `training_data: unknown` only when the datasets are not public and the publisher of the sidecar has no access to them.
- Each reason (`unknown_reason`, `training_data_unknown_reason`) names each source that the writer checked, and the date.
- A host does not change its inference for this block. It shows the block to a user, and it can compare the SPDX ids.

## Validation rules

- [ ] `V-common.license-1` The sidecar must have the `license` mapping with the keys `model` and `training_data`, and `training_data_unknown_reason` only when `training_data` is `unknown`. It must have no other key.
- [ ] `V-common.license-2` Each license object must have a non-empty string `id`, and only the keys `id`, `url` and `unknown_reason`.
- [ ] `V-common.license-3` `id` must be a valid SPDX license expression or `unknown`. If `id` holds a `LicenseRef-` id, `url` must be a non-empty string.
- [ ] `V-common.license-4` If `id` is `unknown`, `unknown_reason` must be a non-empty string. Else the key must be absent.
- [ ] `V-common.license-5` `license.model.id` must not be `unknown`.
- [ ] `V-common.license-6` `training_data` must be `unknown` or a non-empty array. If it is `unknown`, `training_data_unknown_reason` must be a non-empty string.
- [ ] `V-common.license-7` Each dataset entry must have a non-empty string `name`, `use` with the value `pretraining` or `training`, and `license`. Its only other key can be `url`.

## Implementer guidance

- A validator of `V-common.license-3` needs a copy of the SPDX License List. OpenMMLab-Exporter checks the ids against the SPDX License List 3.29.0 (release 2026-09-16). (OpenMMLab-Exporter [`pipeline/spdx/spdx-ids.json`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/pipeline/spdx/spdx-ids.json))
- The package `SidecarModel` forbids a key that it does not know. Thus the package rejects a sidecar with `license` until stage M8 of the [implementation plan](../../sidecar-implementation-plan.md). (skellytracker `skellytracker/core/sidecar/model.py` (`SidecarModel`)) (implementation stage)

## Authoring guidance

- The exporter knows the upstream checkpoint that it exports. Thus the exporter writes this block, not a skellytracker session ([ADR-NBG2](../decisions/entries/NBG2-license-and-training-data-without-the-deferred-examples.md)).
- List the datasets of each checkpoint in the start chain, not only the datasets of the last training ([Fields](#fields)).
  - OpenMMLab-Exporter follows two rulings of its user for a checkpoint chain. A distillation teacher counts as a start checkpoint. Where a checkpoint name and its config disagree on the datasets, the list holds the union of the two dataset sets. Neither ruling adds a dataset to the RTMW list. (OpenMMLab-Exporter ADR-EC75 [`decisions/entries/EC75-sidecar-license-block.md:16-17`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/decisions/entries/EC75-sidecar-license-block.md#L16-L17) (secondary))
- skellytracker has no list of `LicenseRef-` names. `V-common.license-3` only requires a `url` for a `LicenseRef-` id.
  - The seven `LicenseRef-` names of the RTMW example are proposals of OpenMMLab-Exporter. (OpenMMLab-Exporter [`rtmw/README.md:119-129`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmw/README.md#L119-L129) (secondary))
- A permissive model license does not clear a model for commercial use.
  - The RTMW weights are `Apache-2.0`. No RTMW training dataset is fully permissive. Each dataset is non-commercial, research only or `unknown`, or it holds such a part. Thus a user must check the dataset terms before a commercial use. ([`rtmw-wholebody133.yaml`](../examples/detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133.yaml) `license`; OpenMMLab-Exporter ADR-EC75 [`decisions/entries/EC75-sidecar-license-block.md:41-43`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/decisions/entries/EC75-sidecar-license-block.md#L41-L43); OpenMMLab-Exporter [`rtmw/README.md:130-131`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmw/README.md#L130-L131) (secondary))

## Examples

```yaml
license:
  model: {id: Apache-2.0, url: https://github.com/open-mmlab/mmpose/blob/v1.3.2/LICENSE}
  training_data:
    - name: COCO 2017 (train2017, person annotations)
      url: https://cocodataset.org/
      use: training
      license: {id: CC-BY-4.0 AND LicenseRef-COCO-Images, url: https://cocodataset.org/#termsofuse}
```

# SE3Y — License and training data

**Status:** superseded by [NBG2](NBG2-license-and-training-data-without-the-deferred-examples.md), 2026-11-09 (user; PR: pending).

## Decision

The user asked for a mandatory model license and mandatory training data: "which datasets were
used, with links if available, and what license each dataset carries". "unknown" is acceptable
"only after extensive research or an inability to identify the training datasets or their license
(i.e. they are proprietary/not publicly disclosed *and* the publisher of the model sidecar does not
have access to them)". The user chose a new section, SPDX ids with URLs, a `use` field, and values
from the exporters.

1. **Section.** New section `common.license` in `common/license.md`, with `selectors: []` and
   `status.spec: draft`. All sizes share its fields. Sizes that differ in license or data are two
   families.
2. **Fields.**
   - `license` (object, required): the keys `model` and `training_data`, and
     `training_data_unknown_reason` only when `training_data` is `unknown`.
   - `license.model` (license object, required): the license of the weights.
   - `license.training_data` (array or `unknown`, required): one entry for each dataset that made
     the weights. This includes each dataset of a checkpoint that the training started from.
   - A dataset entry: `name` (string, required), `url` (string, optional: a public page of the
     dataset), `use` (`pretraining` or `training`, required), `license` (license object, required).
   - A license object: `id` (string, required): an SPDX license expression or `unknown`. An
     expression can hold a `LicenseRef-<name>` id for a license that SPDX does not list. `url`
     (string): the license text. `unknown_reason` (string): only when `id` is `unknown`.
3. **Unknown.** Write `unknown` only after research that finds no answer. Write
   `training_data: unknown` only when the datasets are not public and the publisher of the sidecar
   has no access to them. Each reason names each source that the writer checked, and the date.
4. **Rules.**
   - `V-common.license-1`: the sidecar must have the `license` mapping with the keys of item 2 and
     no other key.
   - `V-common.license-2`: each license object must have a non-empty string `id`, and only the keys
     `id`, `url` and `unknown_reason`.
   - `V-common.license-3`: `id` must be a valid SPDX license expression or `unknown`. If `id` holds
     a `LicenseRef-` id, `url` must be a non-empty string.
   - `V-common.license-4`: if `id` is `unknown`, `unknown_reason` must be a non-empty string. Else
     the key must be absent.
   - `V-common.license-5`: `license.model.id` must not be `unknown`.
   - `V-common.license-6`: `training_data` must be `unknown` or a non-empty array. If it is
     `unknown`, `training_data_unknown_reason` must be a non-empty string.
   - `V-common.license-7`: each dataset entry must have a non-empty string `name`, `use` with the
     value `pretraining` or `training`, and `license`. Its only other key can be `url`.
5. **Vectors.** A data-only file `vectors/common.license.yaml` holds one validator case for each
   rule.
6. **Examples: `needs-export`.** The rules make each of the five examples invalid. The forced-edit
   rules allow no added value
   ([When a spec change makes an example invalid](../../model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid)),
   and the user chose the exporters as the source. Thus the content commit waits for the rebuild
   bundles of the [Re-export requests](../open-work.md#re-export-requests) item:
   Ultralytics-Exporter for `yolo26` and `yolo26-body`, OpenMMLab-Exporter for `rtmdet-person`,
   `rtmw-wholebody` and `rtmo-body7`. Each rebuild sidecar writes the `license` block of items 2
   and 3.
7. **Landing.** The content commit adds the section file, its rows in the section map and the
   validation index of the spec `README.md`, a changelog row, the vectors and the five rebuilt
   examples.

## Reason

- A user must know if a model can go into a product. The model license does not answer this
  alone. The terms of a dataset can restrict the use of the weights.
- An SPDX id is a standard, and a host can compare it. A `LicenseRef-` id covers a license that
  SPDX does not list, for example a license of one model publisher.
- The reason of an `unknown` records the research. Thus a reviewer can check the claim.
- `use: pretraining` keeps the data of a start checkpoint. Its terms can also apply to the weights.
- A new section keeps [Identity](../../common/identity.md) for the catalog key. The new rules and
  vectors have their own section.
- The exporter knows the upstream checkpoint that it exports (user).

## Consequences

- No exporter writes license data now. Each exporter must add the block to its sidecar writer.
- The package `SidecarModel` forbids a key that it does not know. Thus the package rejects a
  sidecar with `license` until stage M8 of the
  [implementation plan](../../../sidecar-implementation-plan.md). The content commit adds the M8
  item.
- The section is `draft`. The `2.0.0` release stops until it becomes `stable`
  ([Section status](../../README.md#section-status), rule 7).
- A validator of `V-common.license-3` needs a copy of the SPDX License List. The content commit
  gives its version in the Implementer guidance.

## Alternatives rejected

- **Fields in `common.identity`.** Identity is `stable` and holds the catalog key. The new rules
  are a separate topic.
- **Free-text strings.** A host cannot compare them, and nothing records the research.
- **Final training data only.** The data and the terms of a start checkpoint are then lost.
- **Values from a skellytracker session as forced edits.** The forced-edit rules allow no added
  value, and the user chose the exporters as the source.

## Open work

See [open-work.md](../open-work.md).

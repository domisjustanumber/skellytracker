# NBG2 — License and training data without the deferred examples

**Status:** absorbed into [`license.md#fields`](../../common/license.md#fields), [`license.md#behaviour`](../../common/license.md#behaviour), [`license.md#validation-rules`](../../common/license.md#validation-rules), [`license.md#implementer-guidance`](../../common/license.md#implementer-guidance), [`model-sidecar/README.md#section-status`](../../README.md#section-status), 2026-11-10 (user; PR: pending).

## Decision

This entry supersedes [ADR-SE3Y](SE3Y-license-and-training-data.md) in full. Items 1 to 5 restate
SE3Y items 1 to 5 with no change. Items 6 and 7 change.

1. **Section.** New section `common.license` in `common/license.md`, with `selectors: []` and
   `status.spec: draft`. All sizes share its fields. Sizes that differ in license or data are two
   families.
2. **Fields.**
   - `license` (object, required): the keys `model` and `training_data`, and
     `training_data_unknown_reason` only when `training_data` is `unknown`.
   - `license.model` (license object, required): the license of the weights.
   - `license.training_data` (array or `unknown`, required): one entry for each dataset that made
     the weights, also each dataset of a checkpoint that the training started from.
   - A dataset entry: `name` (string, required), `url` (string, optional: a public page of the
     dataset), `use` (`pretraining` or `training`, required), `license` (license object, required).
   - A license object: `id` (string, required): an SPDX license expression or `unknown`. An
     expression can hold a `LicenseRef-<name>` id. `url` (string): the license text.
     `unknown_reason` (string): only when `id` is `unknown`.
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
6. **Examples.** The rules make each current example invalid. Each one is `needs-export`.
   - `rtmw-wholebody` gets its rebuild: the content commit replaces it with the copy of
     `model-rtmw-wholebody133@openmmlab-exporter` in
     `detectors/keypoint_detectors/rtmw/wholebody133/`. The commit waits for that bundle.
   - `rtmdet-person`, `yolo26` and `yolo26-body` get no rebuild
     ([ADR-YS4C](../../../../decisions/entries/YS4C-example-removal-by-a-user-ruling.md) item 7).
     The content commit removes them with step 12 of
     [When a spec change makes an example invalid](../../model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid).
   - The content commit lands after the content commit of
     [ADR-52NQ](52NQ-model-id-suffix.md), so that the RTMW copy obeys the storage layout.
7. **Landing.** The content commit adds the section file, its rows in the section map and the
   validation index of the spec `README.md`, a changelog row, the vectors, the RTMW copy and the
   removals. It gives the version of the SPDX License List in the Implementer guidance. Then the Re-export item closes. The `yolox-person`
   example lands after it, in its own commit.

## Reason

- A user must know if a model can go into a product. The terms of a dataset can restrict the use of
  the weights, so the model license alone does not answer this.
- An SPDX id is a standard that a host can compare. The reason of an `unknown` records the research.
- The exporter knows the upstream checkpoint that it exports (user).
- SE3Y item 6 waited for five rebuilds. Four of them will not come
  ([ADR-YS4C](../../../../decisions/entries/YS4C-example-removal-by-a-user-ruling.md)).

## Consequences

- Each exporter must add the block to its sidecar writer.
- The package `SidecarModel` rejects a sidecar with `license` until stage M8 of the
  [implementation plan](../../../sidecar-implementation-plan.md). The content commit adds the M8
  item.
- The section is `draft`. The `2.0.0` release stops until it becomes `stable`
  ([Section status](../../README.md#section-status), rule 7).
- Both new examples have `batching.batch_conversion`. Thus the release also stops until
  `common.batch_conversion` is implemented.

## Alternatives rejected

- **Fields in `common.identity`.** Identity is `stable` and holds the catalog key.
- **Free-text strings.** A host cannot compare them, and nothing records the research.
- **Values from a skellytracker session.** The user chose the exporters as the source.
- **Wait for the rebuilds of the deferred examples.** They have no date.

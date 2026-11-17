# F067 — Spec change: simcc-score-map

**Status:** proposed, 2026-11-16 (OpenMMLab-Exporter proposal; user decisions of 2026-11-16).

## Decision

The record is [`proposal.md`](../../proposals/simcc-score-map/proposal.md)
(proposal-simcc-score-map@openmmlab-exporter@v1).

- Section: new section `post.keypoint.score_map`. The change also edits `common.sizes_and_artifacts`,
  `post.keypoint.decode.simcc` and `post.keypoint.schema`.
- Change: the keypoint score of a SimCC model is a normalised value in `[0, 1]`. The score is
  `1 / (1 + exp(-(a * raw + b)))`. `raw` is the score of `post.keypoint.decode.simcc`, with no
  change. The missing rule runs on `raw` before the map, and a missing keypoint has the score `0.0`
  exactly. A size of a `simcc` model has the required key `sizes.<size>.score_map` with `method`,
  `a` and `b`, an optional pair for each group of the landmark schema and an optional `fit`
  record. A reference module and 21 vector cases are new.
- Target spec version: `2.0.0`.
- Models: RTMW (OpenMMLab-Exporter `rtmw-wholebody133`).
- Supersedes: none.
- Related: `model-rtmw-wholebody133@openmmlab-exporter`;
  [ADR-03PH](03PH-simcc-score-rule.md) (the raw score);
  [ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md) (the size entry).
- The user decided these items on 2026-11-16:
  - The keypoint score of the skellytracker result is a normalised value in `[0, 1]`. The sidecar
    spec defines it, and skellytracker computes it.
  - The map is logistic in the raw score, with an optional pair for each keypoint group. The
    proposal keeps this map family. The map in `ln(raw)` is evidence only.
  - The pair is a new permitted key of each size, `sizes.<size>.score_map`. A key at the top level
    that is keyed by size name is rejected.
  - A threshold in a sidecar that reads a keypoint score reads the mapped score, for example
    `score_gate`. This is a recommendation. The user confirms it at the landing.
  - The `license` block does not change: the model is a re-export of an existing model.

This entry changes two rules of [ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md)
that the spec states under [`sizes`](../../common/sizes-and-artifacts.md#sizes): a size entry also
allows `score_map` (item 4), and `score_map` is not a size-level override (item 9, the family
invariant). This entry does not supersede ADR-90CE. The commit that changes the text under a linked
heading cites its own entry next to the changed rule
([Rules](../../../../decisions/README.md#rules)).

## Reason

The decode score has no fixed range, and its scale changes with the size of one family. The raw
score with a 50 % chance to be a correct point is 0.51 to 0.53 at 256x192, 2.85 at l-384 and 5.20
at x-384 (COCO-WholeBody v1.0 val). One threshold cannot serve all sizes. The user requires one
normalised score. The pair is a property of the weights of one size, so it is a per-size key, not a
contract item.

## Evidence

Part 5 of the record and its `evidence.md`: a fit on 6352 persons of COCO-WholeBody v1.0 val. The
check-split ECE with one pair for each size and the group rule is 0.0063 to 0.0230. One pair for all
sizes gives 0.126 to 0.184. Each size passes the fp16 check. The ONNX files are byte-identical to
bundle version 5 of `model-rtmw-wholebody133`, so no parity run is repeated.

## Before acceptance

- Known limit: at l-384, the logistic map in `raw` does not fit the group `body` well (check ECE
  0.048 with its own pair). The map in `ln(raw)` is better at 384x288 and worse at 256x192. The user
  keeps the logistic map in `raw`.
- The reference module reads only `numpy` and `math`. The safety review found no file, network,
  process, environment or dynamic-code access.
- Landing blocker: the part 7 row of `rtmw-wholebody133` has the impact `needs-export`. The
  exporter packs version 6 of its `model` bundle after this change lands. Until then, the example
  has no `score_map`.
- The pipeline result API (`score` is the mapped score, and a new `raw_score` field) is a follow-up
  of the pipeline spec.

## Open work

See [open-work.md](../open-work.md).

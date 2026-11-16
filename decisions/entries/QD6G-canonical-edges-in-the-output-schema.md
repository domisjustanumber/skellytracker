# QD6G — The output schema of a `keypoints` output has `canonical_edges`

**Status:** absorbed into [`outputs.md#fields`](../../specs/pipeline/outputs.md#fields), [`outputs.md#behaviour`](../../specs/pipeline/outputs.md#behaviour), 2026-11-16 (user, question R6 of 2026-11-16; PR: pending).

## Decision

1. The output schema of a `keypoints` output has the field `canonical_edges`, next to
   `canonical_names`: the pairs of `edges`, with each point name in its canonical form.
2. Each point that the canonical form copies or renames has a canonical name. A point with two or
   more canonical names takes the first of them in `canonical_names`.
3. An edge with a point that has no canonical name is left out.
4. A computed canonical point, for example a centre point, is in no edge.
5. The order of `canonical_edges` is the order of `edges`.
6. A pair that an earlier edge gave is left out, also in the other direction.
7. An edge whose two points get the same canonical name is left out.
8. The run gives `canonical_edges` before frame 0, with the output schema.

This entry adds one field to the output schema that
[ADR-4MP6](4MP6-pipeline-point-groups-and-canonical-form.md) defines. That entry does not change.

## Reason

- The spec tells a consumer to use the canonical form. No public value gave the edges in canonical
  names.
- freemocap built the link again with a probe through `to_canonical`.
- The code already has the plan of the mapping. The new field reuses it
  (`skellytracker/core/pipelines/canonical.py`, `_plan` and `canonical_edges`).

## Consequences

- The canonical form gives each copied point exactly one source. Thus two different points never
  get one canonical name, and a rename makes no new duplicate. Items 6 and 7 apply only to `edges`
  that hold an edge two times or an edge from a point to itself.
- No registered landmark schema copies one point to two canonical names. The first-name rule of
  item 2 applies to no built-in pipeline.

## Evidence

- `yolox-rtmw-wholebody@skellytracker`: 65 `edges` and 65 `canonical_edges`. Each point of an edge is
  in `canonical_names`. For example, `[body/left_ankle, feet/left_big_toe]` becomes
  `[body/left_ankle, body/left_big_toe]`.
- `mediapipe-holistic-tasks@skellytracker`: 213 `edges` and 213 `canonical_edges`. Each group passes
  through, so the two lists are equal.
- The tests are `skellytracker/tests/pipelines/test_canonical.py` and
  `skellytracker/tests/pipelines/test_resolve.py`.

## Alternatives rejected

- A consumer maps the edges itself. Each consumer then needs the private plan of the mapping, or a
  probe.
- Edges for the computed points. No text defines them.

# 9HBB — The SimCC decode is 2D only

**Status:** accepted, 2026-11-06 (user; PR: pending).

## Decision

1. **The user decision.** On 2026-11-06, the user chose to gate the 3D SimCC decode off: "the goal
   is for 2D models to comply now, and models that output 3D simcc data in the future to be able to
   comply too". The gate is `pose.geometry`.
2. **What goes.** The value `simcc_z` of `outputs[].semantic`, because only the 3D SimCC decode used
   it. The field `pose.decode.depth_range`. The rule `V-post.pose.decode.simcc-1`. Its number stays
   unused. The `Z_bins` item of the Shape key. The 3D sentences of the Behaviour of
   [`post.pose.decode.simcc`](../../specs/model-sidecar/post/pose-decode-simcc.md#behaviour), and its
   selector `outputs[].semantic=simcc_z`.
3. **What changes.** `V-post.pose.schema-7`: a `simcc` decoder must have `pose.geometry: 2d`. A 3D
   SimCC sidecar fails with this rule ID. `V-post.pose.schema-9` no longer names `depth_range`.
   [`common.outputs`](../../specs/model-sidecar/common/outputs.md) and the model intake template do
   not list `simcc_z`. The changelog lists the 3D SimCC decode under "Considered and deliberately not
   added".
4. **What stays.** `pose.geometry: 3d` and `pose.decode.depth_unit`, for the `coordinate` decode.
   The 2D SimCC decode. No example and no package sidecar has `simcc_z`, so no example changes.
5. **A future 3D SimCC model.** Its proposal adds a new section, selected by
   `outputs[].semantic=simcc_z`. It brings the upstream codec as evidence, the score rule for three
   peaks, the exact map from a depth bin to depth, vectors and a reference module. It removes the
   `pose.geometry: 2d` condition of `V-post.pose.schema-7`. A new section has no owner
   ([Section owner](../../specs/model-sidecar/model-addition-workflow/hand-over.md#section-owner)),
   so each contributor can write it.
6. **The frozen package.** `skellytracker/core/sidecar/model.py` still accepts `simcc_z` and
   `depth_range`. The `Literal` coverage test of `tools/tests/test_traceability.py` skips
   `simcc_z` (`REMOVED_VALUES`). The M8 item "3D SimCC decode removed" of the
   [implementation plan](../../specs/sidecar-implementation-plan.md) removes them from the package
   and removes the skip.

## Reason

- A host could not implement the 3D text. It gave no score rule for three peaks: "Its score is the
  max value". It said only that the z axis "maps `Z_bins` linearly onto `depth_range`". With
  `Z_bins: 64` over `[-1, 1]` m, a map of the bin edges gives -1.000 m for bin 0, and a map of the
  bin centres gives -0.984 m. Two hosts that obey the text then differ by about 1.6 cm.
- No model in scope has a `simcc_z` output. The spec adds only the features that a model in scope
  needs ([Scope of this revision](../../specs/model-sidecar/changelog.md#scope-of-this-revision)).
- The first reference module of the section must implement the full section
  ([Full section](../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#full-section)).
  The 2D proposal `proposal-simcc-score-rule@openmmlab-exporter` could not write the 3D path from
  this text. With the gate, a 2D module is the full section.
- After a proposal on `post.pose.decode.simcc` is accepted, its contributor owns that section. A 3D
  part in that section would make each other contributor of a 3D model go through that owner.

## Alternatives rejected

- **Allow a 2D-only reference as an exception.** A 3D SimCC sidecar then stays valid, but the
  reference and the skellytracker host refuse it or guess.
- **Move the 3D part to a draft section now.** Section status rule 7 stops the release while a
  section is `draft`, and no 3D implementation can make it `stable`. The text stays vague until the
  release removes it.

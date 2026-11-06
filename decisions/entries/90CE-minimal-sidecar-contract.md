# 90CE — Minimal sidecar contract

**Status:** absorbed into [`common/input.md#fields`](../../specs/model-sidecar/common/input.md#fields), 2026-11-06 (user; PR: pending).

## Decision

This entry supersedes
[ADR-0010](../../specs/model-sidecar/decisions/entries/0010-family-invariant.md) in full. Items 1 to
8 are new. Item 4 replaces the merge rule of ADR-0010. Item 9 restates the other rules by a link
([ADR-Z05A](Z05A-essential-decision-log-rules.md)). The content commit renumbers the rules that it
changes, as item 5 of [ADR-0QKK](0QKK-no-legacy-layer.md) says.

1. **Deleted fields.** `sizes.<size>.onnx.precision_artifacts.<precision>.input_dtype`,
   `outputs[].rank` and `input.resize.supports_dynamic_size` go. A resize method that needs
   `target_size` has it in each size.
2. **NCHW only.** `input.layout` and the NHWC form go. The model input is NCHW. Convert a TFLite or
   MediaPipe model with `tf2onnx --inputs-as-nchw`. The Authoring guidance of `common.input` says
   this.
3. **No `base`.** The `base` directive goes, in its string form and in its `{$ref, sha256}` form.
   `$ref` is the only directive that reuses a file. The two `base`-only rules of
   `format.composition` go. The rule on the hash of a directive and the rule on the root of its
   target keep only their `$ref` part.
4. **Sizes are plain fields.** A size entry holds `input.shape`, `input.resize.target_size` and
   `onnx`. Any other key in a size entry is invalid. The host does not merge a size entry over the
   top level. It reads the three fields of the size and the other fields from the top level.
5. **`pose.geometry`.** `pose.decode.is_3d` goes. The pose-level enum `pose.geometry` is required.
   Its values are `2d` and `3d`. Each rule that keys on `is_3d: true` keys on `pose.geometry: 3d`.
   Each rule that keys on its absence or on `false` keys on `2d`. Thus a `simcc` decoder has a
   `simcc_z` output if and only if the geometry is `3d`. The packed `components` contain `z` if and
   only if the geometry is `3d`. `3d` needs `pose.decode.depth_unit`. The heatmap decode is `2d`
   only. Each pose example gets `pose.geometry: 2d`, the value that the old `is_3d` default gives.
6. **Packed keypoints.** Packed keypoints use the `decode.box_scale` of the detection decode.
   `pose.decode.coordinate_scale` must not be present when `packed_keypoints` is present.
   `yolo26-body` loses its `coordinate_scale` (a spec-forced edit).
7. **One `imagenet` mode.** `imagenet_bgr` and `imagenet_rgb` go. The mode `imagenet` applies the
   ImageNet mean and standard deviation in the channel order of `input.color_format`.
   `input.color_format` is required for each normalization mode. `custom.color_format` goes: the
   mode `custom` uses `input.color_format`.
8. **Presence rules.** A rule that tells when a resize field is present goes from `common.input`
   to the `pre/` section of its method. `pad_value` stays defined once, in
   [`input.resize`](../../specs/model-sidecar/common/input.md#inputresize).
9. **The rules that stay.** The family invariant of ADR-0010, the list of keys that a size entry
   must not hold and its pitfall "do not add a size-level override":
   [`sizes`](../../specs/model-sidecar/common/sizes-and-artifacts.md#sizes). The deep merge of a
   size entry goes with item 4. The rule for a sidecar before `vNEXT` goes with ADR-0QKK item 1.
   The list of places that state the rule goes. The pitfall on the frozen package code goes: the
   package stays outside the spec until it migrates
   ([ADR-NB5F](NB5F-no-change-classes-and-one-re-export-request.md) item 1).

## Reason

- The user decided on 2026-11-02 that all contract simplifications land in the spec cleanup. The
  user named `pose.geometry`. Its purpose is that a catalog can filter models by output kind. The
  value `mesh` can join later.
- `input_dtype` had to agree with `input.dtype`, and `rank` had to equal `len(shape)`. Neither field
  gave information.
- A `git grep` of the four exporter repos on 2026-11-02 finds no `supports_dynamic_size`, no NHWC
  and no `base`. Only the frozen package RTMW mapping fragment uses `base`. The package migration
  must inline it.
- A field that comes back later with the default `NCHW` keeps each sidecar valid.
- With no deep merge, a size entry cannot change a top-level key. The family invariant then needs
  no merge rules.
- `is_3d` is a flag that the output semantics also imply. The geometry is a property of the
  family, not of the decode.
- `imagenet_bgr` and `imagenet_rgb` differ only in the channel order, and `input.color_format`
  already gives that order.
- The merged `imagenet` mode has no channel order of its own, so `input.color_format` must give it.
  A second `color_format` on `custom` can disagree with `input.color_format`, and a fallback to
  `rgb` hides a missing value.
- A presence rule in `common.input` is a second copy of the rule of a method.

## Consequences

- Each example and each exporter writes the new fields. The spec-owned version entry that follows
  adds this entry to the re-export request of
  [ADR-NB5F](NB5F-no-change-classes-and-one-re-export-request.md) item 2.
- The frozen package keeps the old normalization values. A doc test excludes `imagenet_bgr` and
  `imagenet_rgb` from the selector check until the package migrates.
- The package RTMPose and RTMW sidecars choose `custom` or the merged `imagenet` mode in the
  implementation stage. The implementation plan holds that choice.

## Alternatives rejected

- **Keep `is_3d` as an agreement check.** A catalog cannot filter on a decode flag, and the flag
  repeats the output semantics.
- **An optional `components` list for every keypoint output.** It adds a field where the geometry
  and the semantics already give the layout.
- **Keep `base` until the package migrates.** No exporter or example uses it. The package sidecars
  are outside the spec until they migrate.
- **Keep `imagenet_rgb` with an agreement rule.** Two values then state one fact.

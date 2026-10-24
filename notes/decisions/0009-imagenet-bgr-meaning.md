# 0009 — `imagenet_bgr` changes meaning at `vNEXT`; the legacy meaning stays

**Status:** absorbed into [`pre/normalization.md#legacy-behaviour`](../../specs/sidecar/pre/normalization.md#legacy-behaviour), 2026-10-24 (user; the first review of
[0029](0029-decision-log-read-path.md)). It was accepted on 2026-10-22 (backfilled from #81).

## Decision

The meaning of `input.normalization: imagenet_bgr` depends on the `schema_version` of the sidecar.

| `schema_version` | Meaning of `imagenet_bgr` |
|---|---|
| `>= vNEXT` | BGR-ordered statistics. The host computes `(pixel - mean) / std` on 0–255 pixels in BGR channel order. B uses mean `103.53` and std `57.375`. G uses `116.28` and `57.12`. R uses `123.675` and `58.395`. |
| `< vNEXT` (legacy) | The RGB-ordered tuple. Mean is `(123.675, 116.28, 103.53)`. Std is `(58.395, 57.12, 57.375)`. The host applies the tuple in order to the B, G and R channels of the BGR frame. B uses `123.675`. This is the rtmlib convention. |

- A legacy sidecar keeps the legacy meaning. The spec never applies `vNEXT` requirements to a legacy
  sidecar.
- `imagenet_rgb` does not change. The compatibility table has no row for it.
- At `vNEXT`, the two `imagenet_*` modes use the same per-colour ImageNet statistics. They differ only
  in the channel order of the tensor.
- A `vNEXT` sidecar that needs the legacy computation must declare it with
  `normalization: {mode: custom, color_format: bgr, mean: [123.675, 116.28, 103.53], std: [58.395, 57.12, 57.375]}`.

The spec states the rule in these places:

- change 6 of the [Summary of changes](../../specs/sidecar/changelog.md#summary-of-changes);
- the `imagenet_bgr` row of [Normalization modes](../../specs/sidecar/pre/normalization.md#behaviour);
- the `normalization: imagenet_bgr` row of
  [Version-aware compatibility](../../specs/sidecar/pre/normalization.md#legacy-behaviour).

## Reason

- The CSPNeXt sizes of RTMDet take BGR input with BGR-ordered statistics. The mmdet config sets
  `bgr_to_rgb=False` and mean `(103.53, 116.28, 123.675)` (OpenMMLab-Exporter 0004). The legacy meaning
  applies `123.675` to the B channel. A sidecar for RTMDet cannot use `imagenet_bgr` with the legacy
  meaning.
- At `vNEXT`, each colour gets its own ImageNet statistic in both `imagenet_*` modes
  ([Normalization modes](../../specs/sidecar/pre/normalization.md#behaviour)). The legacy `imagenet_bgr`
  gives the B channel the R statistic. Change 6 spells out the channel order of both modes.
- Legacy sidecars must keep their meaning. The spec never applies `vNEXT` requirements to a sidecar
  with `schema_version < vNEXT`
  ([Version-aware compatibility](../../specs/sidecar/format/versioning.md#version-aware-compatibility)). The in-repo
  RTMPose and RTMW sidecars declare `v2024.09.1019` and `imagenet_bgr`. Their numbers are the
  `_RTMPOSE_MEAN` and `_RTMPOSE_STD` constants that the detectors hard-coded before the migration. A
  change of meaning for these sidecars would change the model input.

## Evidence

Code, checked on 2026-10-22:

- `skellytracker/core/detectors/processing/image_preprocessing.py`, function `build_normalization_fn`:
  the `imagenet_bgr` branch and the `imagenet_rgb` branch use the same constants
  (`_IMAGENET_MEAN = (123.675, 116.28, 103.53)`, `_IMAGENET_STD = (58.395, 57.12, 57.375)`) and the
  same computation, `(img.astype(np.float32) - mean) / std`, in array channel order. For a BGR frame,
  the B channel gets `123.675`. **The code implements the legacy meaning.**
- `build_normalization_fn` does not read `schema_version`. `InputSpec`
  (`skellytracker/core/sidecar/model.py`) has no `schema_version` and no `color_format` field. The
  code does not implement the `vNEXT` meaning yet.
- `CustomNormalization` (`skellytracker/core/sidecar/model.py`) has a `color_format` field with
  default `rgb`. The `custom` branch of `build_normalization_fn` does not read it. It computes
  `(img * scale - mean) / std` with `mean` and `std` in array channel order.
- The test `TestNormalizationDispatch::test_imagenet_bgr_mode_matches_known_constants` in
  `skellytracker/tests/test_image_preprocessing.py` pins the legacy numbers for `imagenet_bgr`.
- `rtmpose-body.yaml`, `rtmpose-hand.yaml`, `rtmpose-face.yaml` and `rtmw-wholebody.yaml` (under
  `skellytracker/core/detectors/keypoint_detectors/`) declare `schema_version: "v2024.09.1019"` and
  `normalization: imagenet_bgr`. They are legacy sidecars. `yolox.yaml` declares `normalization: none`.
- The RTMPose migration (section "M4b" of `specs/sidecar-implementation-plan.md`) verified that
  `imagenet_bgr` gives the same numbers as the constants that it replaced.

## Alternatives rejected

- Change the meaning of `imagenet_bgr` for legacy sidecars as well. The spec does not allow this:
  `vNEXT` requirements never apply retroactively
  ([Version-aware compatibility](../../specs/sidecar/format/versioning.md#version-aware-compatibility)). The change
  would also alter the input of the in-repo RTMPose and RTMW models.

## Not repeated

- Do not assume that `imagenet_bgr` means BGR-ordered statistics in a sidecar older than `vNEXT`.
- Do not rely on the default `normalization` of a detector. The default is `imagenet_bgr`. The spec
  warns that detector models must declare their normalization.
- Do not change the `imagenet_bgr` branch of `build_normalization_fn` without a `schema_version`
  branch. The in-repo legacy sidecars would get a different input.

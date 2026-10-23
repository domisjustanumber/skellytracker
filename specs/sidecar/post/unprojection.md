---
id: post.unprojection
title: Unprojection
kind: postprocessor
---

# Unprojection

## Behaviour

Decoded box and keypoint coordinates are always in a **top-left origin** — `x` grows right, `y` grows down — in the model's input image; the host unprojects them to the source image (see [Unprojection](unprojection.md)). There is no per-sidecar origin override.

Decoded coordinates are first converted to **model-input pixels** — `box_scale` / `coordinate_scale` `normalized_01` multiplies `x` by the model input width and `y` by its height; `normalized_11` maps `[-1, 1]` to `[0, width]` / `[0, height]` — and then mapped back to the source image:

- `letterbox`: [Letterbox resize](../pre/resize-letterbox.md#inverse)
- `stretch`: [Stretch resize](../pre/resize-stretch.md#inverse)
- `fit`: [Fit resize](../pre/resize-fit.md#inverse)
- `none`: [No resize](../pre/resize-none.md#inverse)
- `affine_person_crop`: [Affine person crop](../pre/resize-affine-person-crop.md#inverse)

## Implementer guidance

## Authoring guidance

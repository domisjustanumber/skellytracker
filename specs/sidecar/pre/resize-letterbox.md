---
id: pre.resize.letterbox
title: Letterbox resize
kind: preprocessor
---

# Letterbox resize

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pad_position` | enum | `letterbox`: yes | `top_left` or `center` — where the resized image sits on the padded canvas. `letterbox` only. |
| `rounding` | enum | `letterbox`: yes | How the resized width/height are rounded: `half_even` (Python `round`) or `half_up` (`floor(x + 0.5)`). `letterbox` only. |
| `preserve_aspect_ratio` | bool | no | Letterbox only; when present must be `true`. (`false` is a legacy alias for `stretch`; see [Version-aware compatibility](#legacy-behaviour).) |

`target_size`, `pad_value` and `interpolation` are defined in [`input.resize`](../common/input.md#inputresize) and [Interpolation](interpolation.md).

## Behaviour

The whole source image is resized with a single scale factor and padded to `target_size` `[T_h, T_w]`:

```text
s    = min(T_w / src_w, T_h / src_h)
n_w  = max(1, R(src_w * s))         # R = resize.rounding
n_h  = max(1, R(src_h * s))
dst  = full((T_h, T_w, 3), pad_value)
left, top = (0, 0)                                          # pad_position: top_left
left, top = (floor((T_w - n_w) / 2), floor((T_h - n_h) / 2))  # pad_position: center
dst[top:top+n_h, left:left+n_w] = resize(src, (n_w, n_h), <interpolation>)
```

With `center`, any odd remainder goes to the right/bottom. `half_even` with `center` matches Ultralytics `LetterBox`; `half_up` with `top_left` matches mmdet `Resize(keep_ratio=True)` + `Pad(size=…)`.

### Inverse

Applied as part of [Unprojection](../post/unprojection.md).

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `letterbox` | `x_src = (x - left) * src_w / n_w`, `y_src = (y - top) * src_h / n_h` — the exact inverse of the resize, using the rounded `n_w`/`n_h` and the pad offsets from the letterbox algorithm. |

## Validation rules

Rules marked **(vNEXT)**: see [Validation rules](../README.md#validation-rules).

- [ ] `V-pre.resize.letterbox-1` **(vNEXT)** A `letterbox` resize declares `pad_position` (`top_left` | `center`) and `rounding` (`half_even` | `half_up`); `preserve_aspect_ratio`, when present, is `true`.

See also [Input](../common/input.md#validation-rules) and [Sizes and artifacts](../common/sizes-and-artifacts.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `letterbox` + `preserve_aspect_ratio: false` | Alias for `method: stretch`. | Invalid; use `stretch`. |
| Letterbox `pad_position` / `rounding` absent | Existing host behaviour (implementation-defined). | Required. |

## Implementer guidance

## Authoring guidance

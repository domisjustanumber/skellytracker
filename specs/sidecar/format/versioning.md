---
id: format.versioning
title: Schema versioning
kind: format
---

# Schema versioning

## Behaviour

`schema_version` is a **string** matching the skellytracker release version that introduced or last required a change to the sidecar contract.

| Aspect | Rule |
|--------|------|
| Field | `schema_version` |
| Type | string |
| Value | Exact skellytracker release version (e.g. `"v2024.09.1019"`) |
| Pattern | `vYYYY.0M.BUILD[-TAG]` |

See also [`schema_version` history](../changelog.md#schema_version-history).

### Semantics

- **`schema_version` on a sidecar** = the skellytracker version that defined the contract the sidecar was authored against.
- **Minimum consumer** — skellytracker release `S` loads a sidecar with `schema_version` `V` when `S >= V`. Older sidecars (lower `schema_version`) remain supported by newer skellytracker releases unless a release note says otherwise; newer sidecars (higher `schema_version`) are rejected by older skellytracker releases.
- **Too-new sidecar** — if `sidecar.schema_version > installed_skellytracker_version`, reject with a recoverable error naming both versions and an upgrade hint.
- **Exporter obligation** — set `schema_version` to the skellytracker version documented as current at export time.
- **Stable versions only** — sidecars must not use pre-release tags (`-TAG` suffix).

### Version comparison

`parse_skellytracker_version(version) -> (year, month, build, tag)`:

1. Strip an optional leading `v`.
2. Split on `-` into `core` and optional `tag`.
3. Parse `core` as `YYYY.MM.BUILD` (three dot-separated integers).
4. Compare `(year, month, build, tag)` lexicographically; `tag=None` sorts **after** a tagged pre-release of the same core (stable > pre-release).

### Version-aware compatibility

Validation and decode branch on the sidecar's `schema_version`. `vNEXT` requirements are never applied retroactively; a sidecar with `schema_version < vNEXT` is validated and decoded with the legacy meaning below.

- [Schema versioning](versioning.md#legacy-behaviour)
- [Sizes and artifacts](../common/sizes-and-artifacts.md#legacy-behaviour)
- [Input](../common/input.md#legacy-behaviour)
- [Letterbox resize](../pre/resize-letterbox.md#legacy-behaviour)
- [Normalization](../pre/normalization.md#legacy-behaviour)
- [Detection decode](../post/detection-decode.md#legacy-behaviour)
- [Selection: none](../post/selection-none.md#legacy-behaviour)
- [Selection: NMS](../post/selection-nms.md#legacy-behaviour)
- [Bottom-up pose](../post/pose-bottom-up.md#legacy-behaviour)

## Validation rules

- [ ] `V-format.versioning-1` `schema_version` is a string matching the skellytracker version pattern (no pre-release tag).
- [ ] `V-format.versioning-2` `schema_version` is supported by the installed skellytracker release (`installed >= schema_version`).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `boxes`/`scores`/`class_logits` semantics, `packed_keypoints`, `stretch`, `fit`, `class_id_map` | Not available. | Available. |

## Implementer guidance

## Authoring guidance

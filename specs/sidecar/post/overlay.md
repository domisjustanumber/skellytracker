---
id: post.overlay
title: Overlay
kind: schema
---

# Overlay

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `overlay.skeleton` | string or array[[name, name]] | no | Skeleton to draw: a `pose.connections[].name`, or an inline edge list. Defaults to the first named skeleton. |
| `overlay.groups` | object | no | Map of group name → group schema (below). Each group selects a subset of the skeleton's edges and colors them. |
| `overlay.keypoint_color` | array[3] | no | Default keypoint color `[r, g, b]`. |

**Group schema** (`overlay.groups.<name>`) — mirrors the RTMPose annotator's `ConnectionGroupSchema`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connections` | array[[name, name]] | no | Explicit edge subset of the skeleton (alternative to `prefix`). |
| `prefix` | string | no | Select skeleton edges where **either** endpoint starts with this prefix (e.g. `right_hand_`). |
| `connection_color` | array[3] | yes | RGB color for this group's edges. |
| `connection_thickness` | int | no | Default `2`. |
| `keypoint_color` | array[3] | no | RGB color for this group's keypoints; omit to use `overlay.keypoint_color`. |

Each group selects its edges via `connections` or `prefix` (not both). A `prefix` group matches every skeleton edge where **either** endpoint starts with the prefix; prefixed groups are evaluated in **declaration order**, and the first match wins. A group with neither `connections` nor `prefix` is the **default** group — it receives every skeleton edge not selected by another group (the RTMPose `body` group); at most one default group is allowed. Group names are free-form; the RTMPose convention is `body`, `right_hand`, `left_hand`, `face`.

## Validation rules

- [ ] `V-post.overlay-1` `overlay.skeleton` (when a string) names an entry in `pose.connections`; when an inline edge list, every endpoint appears in `pose.tracked_points` or `pose.derived_points`.
- [ ] `V-post.overlay-2` Each `overlay.groups.<name>` declares `connection_color` and uses `connections` or `prefix` (not both); at most one group has neither (the default group).
- [ ] `V-post.overlay-3` `overlay.groups.<name>.connection_thickness` (when present) is a positive integer.
- [ ] `V-post.overlay-4` Every edge in a group's `connections` is a member of the selected skeleton's edge set (the named `pose.connections[]` entry, or the inline `overlay.skeleton` edge list).
- [ ] `V-post.overlay-5` `overlay.keypoint_color`, `overlay.groups.<name>.connection_color`, and `overlay.groups.<name>.keypoint_color` (when present) are length-3 arrays.

## Implementer guidance

## Authoring guidance

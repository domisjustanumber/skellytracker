---
id: post.overlay
title: Overlay
kind: schema
since: v2024.09.1019
changed_in: []
selectors:
  - overlay
implemented_by:
  validate: skellytracker/core/sidecar/model.py::SidecarModel._check_overlay  # with OverlaySpec and OverlayGroupSpec
  load: skellytracker/core/detectors/overlay_groups.py::resolve_overlay_groups  # partial: it groups the edges only; colours, thickness, keypoint_color and overlay.skeleton are not read
external_impl: []
tests:
  - skellytracker/tests/test_overlay_groups.py
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/sidecar/test_rtmw_sidecar.py
vectors: null
status: {spec: stable, validate: implemented, load: partial}
---

# Overlay

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `overlay.skeleton` | string or array[[name, name]] | no | The skeleton to draw: a `pose.connections[].name`, or an inline edge list. The default is the first named skeleton. |
| `overlay.groups` | object | no | A map of group name → group schema (below). Each group selects a subset of the edges of the skeleton and colors them. |
| `overlay.keypoint_color` | array[3] | no | The default keypoint color `[r, g, b]`. |

**Group schema** (`overlay.groups.<name>`) — this schema mirrors `ConnectionGroupSchema` of the RTMPose annotator:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connections` | array[[name, name]] | no | An explicit subset of the edges of the skeleton. It is an alternative to `prefix`. |
| `prefix` | string | no | Select the skeleton edges where **either** endpoint starts with this prefix (for example `right_hand_`). |
| `connection_color` | array[3] | yes | The RGB color of the edges of this group. |
| `connection_thickness` | int | no | The default is `2`. |
| `keypoint_color` | array[3] | no | The RGB color of the keypoints of this group. To use `overlay.keypoint_color`, omit this field. |

Each group selects its edges with `connections` or `prefix` (not both). A `prefix` group matches every skeleton edge where **either** endpoint starts with the prefix. The host evaluates the prefixed groups in **declaration order**. An edge belongs to the first prefixed group that matches it. A group with neither `connections` nor `prefix` is the **default** group. It receives every skeleton edge that no other group selects (the RTMPose `body` group). The overlay must have at most one default group. A group name can be any name. The RTMPose convention is `body`, `right_hand`, `left_hand` and `face`.

## Validation rules

- [ ] `V-post.overlay-1` If `overlay.skeleton` is a string, it must name an entry in `pose.connections`. If it is an inline edge list, every endpoint must appear in `pose.tracked_points` or `pose.derived_points`.
- [ ] `V-post.overlay-2` Each `overlay.groups.<name>` must declare `connection_color`. It must use `connections` or `prefix`, but not both. At most one group can have neither (the default group).
- [ ] `V-post.overlay-3` If `overlay.groups.<name>.connection_thickness` is present, it must be a positive integer.
- [ ] `V-post.overlay-4` Every edge in the `connections` of a group must be a member of the edge set of the selected skeleton. The selected skeleton is the named `pose.connections[]` entry, or the inline `overlay.skeleton` edge list.
- [ ] `V-post.overlay-5` If `overlay.keypoint_color`, `overlay.groups.<name>.connection_color` or `overlay.groups.<name>.keypoint_color` is present, it must be a length-3 array.

## Implementer guidance

No exporter evidence yet.

## Authoring guidance

- RTMW: `skeleton` is `wholebody`. The block has a top-level `keypoint_color` and three groups (`body`, `left_hand` and `right_hand`). Each group has an explicit `connections` list, split by the edge indexes: body up to index 22, left hand 91-111, right hand from 112. The groups have 25, 20 and 20 edges, which cover all 65 edges. There is no `prefix` group, no default group and no face group, because the skeleton has no face edges. (OpenMMLab-Exporter [`rtmw/keypoints.py:148-238`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/keypoints.py#L148-L238); [`rtmw/sidecar.py:166-175`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/sidecar.py#L166-L175))
- RTMO: `skeleton` is `coco`, with one `body` group that has only `connection_color` `[0, 200, 83]`. That group has neither `connections` nor `prefix`, so it is the default group. (OpenMMLab-Exporter [`rtmo/sidecar.py:166-167`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/sidecar.py#L166-L167))
- YOLO26-pose: `overlay.skeleton` is the name of `connections[0]` (`coco_17`). The colours come from the earlier hex palette of the exporter, converted to RGB (body `#00B7EB` to `[0, 183, 235]`, left `#00C853` to `[0, 200, 83]`, right `#FF5252` to `[255, 82, 82]`). They are not an Ultralytics palette. (Ultralytics-Exporter [`yolo_sidecar.py:109-112`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L109-L112), [`yolo_sidecar.py:531-546`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L531-L546))
- Check the edge count of each group. YOLO26-pose has the groups `left` (prefix `left_`), `right` (prefix `right_`) and a default `body` group. Every one of its 16 edges has an endpoint that starts with `left_` or `right_`, so the `body` group gets no edges. The cross-side edges `left_shoulder`-`right_shoulder` and `left_hip`-`right_hip` fall in the `left` group, because it comes first and the first match wins. RTMW avoids this with explicit `connections` lists. (Ultralytics-Exporter [`yolo_sidecar.py:58-76`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L58-L76), [`yolo_sidecar.py:531-546`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L531-L546); OpenMMLab-Exporter [`rtmw/keypoints.py:219-238`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/keypoints.py#L219-L238))

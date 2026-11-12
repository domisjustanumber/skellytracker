---
id: post.keypoint.overlay
title: Overlay
kind: schema
selectors:
  - keypoint.overlay
implemented_by:
  validate: skellytracker/core/sidecar/model.py::SidecarModel._check_overlay  # with OverlaySpec and OverlayGroupSpec
  load: skellytracker/core/detectors/overlay_groups.py::resolve_overlay_groups  # partial: it groups the edges only; colours, thickness, keypoint_color and keypoint.overlay.skeleton are not read
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
| `keypoint.overlay.skeleton` | string or array[[name, name]] | no | The skeleton to draw: a `keypoint.skeletons[].name`, or an inline edge list. The default is the first named skeleton. |
| `keypoint.overlay.parts` | object | no | A map of part name → part schema (below). Each part selects a subset of the edges of the skeleton and colors them. |
| `keypoint.overlay.keypoint_color` | array[3] | no | The default keypoint color `[r, g, b]`. |

**Part schema** (`keypoint.overlay.parts.<name>`) — this schema mirrors `ConnectionGroupSchema` of the RTMPose annotator:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `edges` | array[[name, name]] | no | An explicit subset of the edges of the skeleton. It is an alternative to `prefix`. |
| `prefix` | string | no | Select the skeleton edges where **either** endpoint starts with this prefix (for example `right_hand_`). |
| `edge_color` | array[3] | yes | The RGB color of the edges of this part. |
| `edge_thickness` | int | no | The default is `2`. |
| `keypoint_color` | array[3] | no | The RGB color of the keypoints of this part. To use `keypoint.overlay.keypoint_color`, omit this field. |

Each part selects its edges with `edges` or `prefix` (not both). A `prefix` part matches every skeleton edge where **either** endpoint starts with the prefix. The host evaluates the prefixed parts in **declaration order**. An edge belongs to the first prefixed part that matches it. A part with neither `edges` nor `prefix` is the **default** part. It receives every skeleton edge that no other part selects (the RTMPose `body` group). The overlay must have at most one default part. A part name can be any name. The RTMPose convention is `body`, `right_hand`, `left_hand` and `face`.

## Validation rules

- [ ] `V-post.keypoint.overlay-1` If `keypoint.overlay.skeleton` is a string, it must name an entry in `keypoint.skeletons`. If it is an inline edge list, every endpoint must appear in `keypoint.point_names` or `keypoint.derived_points`.
- [ ] `V-post.keypoint.overlay-2` Each `keypoint.overlay.parts.<name>` must declare `edge_color`. It must use `edges` or `prefix`, but not both. At most one part can have neither (the default part).
- [ ] `V-post.keypoint.overlay-3` If `keypoint.overlay.parts.<name>.edge_thickness` is present, it must be a positive integer.
- [ ] `V-post.keypoint.overlay-4` Every edge in the `edges` of a part must be a member of the edge set of the selected skeleton. The selected skeleton is the named `keypoint.skeletons[]` entry, or the inline `keypoint.overlay.skeleton` edge list.
- [ ] `V-post.keypoint.overlay-5` If `keypoint.overlay.keypoint_color`, `keypoint.overlay.parts.<name>.edge_color` or `keypoint.overlay.parts.<name>.keypoint_color` is present, it must be a length-3 array.

## Implementer guidance

No exporter evidence yet.

## Authoring guidance

- RTMW: `skeleton` is `wholebody`. The block has a top-level `keypoint_color` and three parts (`body`, `left_hand` and `right_hand`). Each part has an explicit `edges` list, split by the edge indexes: body up to index 22, left hand 91-111, right hand from 112. The parts have 25, 20 and 20 edges, which cover all 65 edges. There is no `prefix` part, no default part and no face part, because the skeleton has no face edges. (OpenMMLab-Exporter [`rtmw/keypoints.py:148-238`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/keypoints.py#L148-L238); [`rtmw/sidecar.py:166-175`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/sidecar.py#L166-L175))
- RTMO: `skeleton` is `coco`, with one `body` part that has only `edge_color` `[0, 200, 83]`. That part has neither `edges` nor `prefix`, so it is the default part. (OpenMMLab-Exporter [`rtmo/sidecar.py:166-167`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/sidecar.py#L166-L167))
- YOLO26-pose: `keypoint.overlay.skeleton` is the name of `skeletons[0]` (`coco_17`). The colours come from the earlier hex palette of the exporter, converted to RGB (body `#00B7EB` to `[0, 183, 235]`, left `#00C853` to `[0, 200, 83]`, right `#FF5252` to `[255, 82, 82]`). They are not an Ultralytics palette. (Ultralytics-Exporter [`yolo_sidecar.py:109-112`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L109-L112), [`yolo_sidecar.py:531-546`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L531-L546))
- Check the edge count of each part. YOLO26-pose has the parts `left` (prefix `left_`), `right` (prefix `right_`) and a default `body` part. Every one of its 16 edges has an endpoint that starts with `left_` or `right_`, so the `body` part gets no edges. The cross-side edges `left_shoulder`-`right_shoulder` and `left_hip`-`right_hip` fall in the `left` part, because it comes first and the first match wins. RTMW avoids this with explicit `edges` lists. (Ultralytics-Exporter [`yolo_sidecar.py:58-76`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L58-L76), [`yolo_sidecar.py:531-546`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L531-L546); OpenMMLab-Exporter [`rtmw/keypoints.py:219-238`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/keypoints.py#L219-L238))

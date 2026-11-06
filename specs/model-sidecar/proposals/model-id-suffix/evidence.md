# Evidence: model-id-suffix

This file uses ASD-STE100 Simplified Technical English.

## Exporter values

A `model_id` and a folder are values that the exporter chooses. They have no upstream evidence.

- OpenMMLab-Exporter [`rtmw/identity.py:33-36`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d9704753a22792c32a1d3018a0c9e9ea2d279d71/rtmw/identity.py#L33-L36):
  `FAMILY = "rtmw-wholebody133"`, `FAMILY_BRANCH = Path("detectors/keypoint_detectors/rtmw/wholebody133")`.
- OpenMMLab-Exporter [`rtmo/identity.py:39-42`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d9704753a22792c32a1d3018a0c9e9ea2d279d71/rtmo/identity.py#L39-L42):
  `FAMILY = "rtmo-coco17-body7"`, `FAMILY_BRANCH = Path("detectors/keypoint_detectors/rtmo/coco17")`.
- The exporter decision that sets the grammar:
  [OpenMMLab-Exporter ADR-0039](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d9704753a22792c32a1d3018a0c9e9ea2d279d71/decisions/entries/0039-keypoint-model-id-format.md).

## Upstream facts that a part token cannot express

mmpose `5408bc76f5b848cf925a0d1857899011d8c5b497` (tag `v1.3.2`), read in
the published exporter image with the tag `df-dcab32049439` ([OpenMMLab-Exporter ADR-F5VE](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d9704753a22792c32a1d3018a0c9e9ea2d279d71/decisions/entries/F5VE-docker-image.md)):

- One family, one region, two keypoint outputs: RTMPose body with 17 points
  ([`configs/body_2d_keypoint/rtmpose/body8/rtmpose-m_8xb256-420e_body8-256x192.py:77`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/configs/body_2d_keypoint/rtmpose/body8/rtmpose-m_8xb256-420e_body8-256x192.py#L77),
  `out_channels=17`) and with 26 points
  ([`configs/body_2d_keypoint/rtmpose/body8/rtmpose-m_8xb512-700e_body8-halpe26-256x192.py:4`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/configs/body_2d_keypoint/rtmpose/body8/rtmpose-m_8xb512-700e_body8-halpe26-256x192.py#L4),
  `num_keypoints = 26`).
- One family, one keypoint output, two training sets: RTMO COCO
  ([`configs/body_2d_keypoint/rtmo/coco/rtmo-m_16xb16-600e_coco-640x640.py:255`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/configs/body_2d_keypoint/rtmo/coco/rtmo-m_16xb16-600e_coco-640x640.py#L255))
  and RTMO body7
  ([`configs/body_2d_keypoint/rtmo/body7/rtmo-m_16xb16-600e_body7-640x640.py:467`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/configs/body_2d_keypoint/rtmo/body7/rtmo-m_16xb16-600e_body7-640x640.py#L467)),
  both with `RTMOHead(num_keypoints=17)`.

## Spec text

- `specs/model-sidecar/decisions/open-work.md`, heading "Spec defects", item 1 (the `{family}-{part}`
  item), at skellytracker `8351b7f8c20c8db74eb3e547478970e4dceb0308`.
- The reference examples: `rtmo-body7` in `rtmo/body/` is the one example that the current text
  cannot express.

## Parity

none. A name changes no tensor and no decoded output.

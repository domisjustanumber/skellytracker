# G79P — Pixel centres follow the OpenCV call of each resize method

**Status:** absorbed into [`pre/interpolation.md#pixel-centres`](../../pre/interpolation.md#pixel-centres), 2026-11-06 (user; PR: pending).

## Decision

The user chose the option "Per method, as OpenCV": "letterbox/stretch: half-pixel centres
(cv2.resize). fit/affine_person_crop: the warpAffine convention (src = M^-1 * dst, no 0.5 offset),
in the forward warp and in the inverse."

1. **Two conventions.** A new heading
   [Pixel centres](../../pre/interpolation.md#pixel-centres) of `pre.resize.interpolation` gives
   the convention of each method:
   - `letterbox` and `stretch` resize with `cv2.resize`. A coordinate is a position on the image
     plane. Pixel `i` covers `[i, i + 1)`, and its centre is at `i + 0.5`. `cv2.resize` samples at
     half-pixel centres for `linear`, `cubic` and `area`. `nearest` (`cv2.INTER_NEAREST`) takes the
     source pixel `floor(x * src_n / dst_n)`, so the quote is not true for `nearest`.
   - `fit` and `affine_person_crop` warp with `cv2.warpAffine`. A coordinate is a pixel index. The
     centre of pixel `i` is at `i`. The destination pixel `(x, y)` samples the source at
     `M^-1 · (x, y, 1)`.
2. **The inverse.** Each Inverse and [Unprojection](../../post/unprojection.md#behaviour) use the
   convention of the method. No step adds or removes a `0.5` offset. The source coordinates keep
   the convention of the method. The host does not convert a box between the two conventions. No
   formula changes.
3. **The text that goes.** The phrase "`cv2.resize` / `cv2.warpAffine`, half-pixel centres" of
   [Interpolation](../../pre/interpolation.md#behaviour) goes. Each text that calls the pixel
   centres a spec defect goes or links to the new heading: the Implementer guidance of
   `pre.resize.interpolation` and `pre.resize.fit`,
   [mapping-hints.md](../../model-addition-workflow/mapping-hints.md) and
   [model-intake.md](../../templates/model-intake.md). Two items of the
   [spec defects](../open-work.md#spec-defects) go: the item on the `input.resize` text and the
   sub-item "the pixel-centre convention of the unprojection".
4. **The vectors.** No `expect` changes. The inverse cases already use no `0.5` offset. The
   sampled source position of a pixel is pixel-level output, which the vectors do not cover.

## Reason

- Each method has one upstream call. The convention of that call gives upstream parity with no new
  field. mmpose v1.3.2 `TopdownAffine` and `BottomupResize` call `cv2.warpAffine`, and the pose
  estimators map the keypoints back with `M^-1`. The RTMPose face6 and hand5 configs use
  `TopdownAffine` with no `use_udp`. Thus RTMO body7, RTMW wholebody and the RTMPose body, face and
  hand sidecars keep parity.
- Ultralytics `LetterBox` resizes with `cv2.resize`. Its inverse `(x - pad) / gain` has no `0.5`
  offset. That is the letterbox inverse of the spec.
- The old text named one convention for two calls that differ.

## Consequences

- The MediaPipe face and hand sidecars of Qualcomm-Exporter get the call of their upstream, but no
  parity. `qai_hub_models` 0.64.0 maps the ROI corners to the pixel centres `0` and `W - 1`, not to
  `0` and `W`, and the ROI is rotated. The spec defect on the rotated ROI covers both.
- A box of a `letterbox` detector (RTMDet) goes unchanged into an `affine_person_crop` model
  (RTMW). The clamp bounds `[0, W]` of
  [ADR-17KN](../../../../decisions/entries/17KN-one-selection-pipeline.md) are image-plane bounds. A
  host must not add a `0.5` conversion between them. The
  [spec defect](../open-work.md#spec-defects) on the box format of `affine_person_crop` stays open.
- `cv2.warpAffine` runs `cv2.INTER_AREA` as `cv2.INTER_LINEAR`. A new spec defect records this.
- The package code already follows the decision. The implementation plan gets no item.

## Evidence

- OpenCV 4.13.0, [`scripts/G79P_pixel_centres.py`](../scripts/G79P_pixel_centres.py): a 2x upscale
  of `[0, 10, 20, 30]` gives `2.5` with `cv2.resize` and `5.0` with `cv2.warpAffine` at `x = 1`.
  For a scale `s`, the source positions of one destination pixel differ by `0.5 * (1 / s - 1)`
  source pixels (checked at `s` = 2, 0.5, 1/3, 0.512 and 6.4). The mmpose inverse equals `M^-1`
  (difference 0.0 on the vector case `tall-box-grows-width`). A 10 to 4 `INTER_NEAREST` resize of
  an index ramp gives `[0, 2, 5, 7]`. `cv2.warpAffine` gives equal arrays with `INTER_AREA` and
  `INTER_LINEAR`.
- mmpose v1.3.2, read at the tag commit 5408bc76f5b848cf925a0d1857899011d8c5b497:
  `mmpose/datasets/transforms/topdown_transforms.py:104-118` and
  `mmpose/datasets/transforms/bottomup_transforms.py:575-592` call `cv2.warpAffine`. `use_udp` is
  `False` by default (`topdown_transforms.py:46`, `bottomup_transforms.py:472`). The inverse is
  `mmpose/models/pose_estimators/topdown.py:154-156` and `bottomup.py:172-174`.
  `configs/face_2d_keypoint/rtmpose/face6/rtmpose-m_8xb256-120e_face6-256x256.py:116,142,156` and
  `configs/hand_2d_keypoint/rtmpose/hand5/rtmpose-m_8xb256-210e_hand5-256x256.py:116,139,153` use
  `TopdownAffine` with no `use_udp`.
- ultralytics 8.4.184, installed in the Ultralytics-Exporter `.venv`: `data/augment.py:1839-1840`
  and `utils/ops.py:151-170`.
- `qai_hub_models` 0.64.0, installed in the Qualcomm-Exporter `.venv`:
  `utils/bounding_box_processing.py:209-211`, `utils/image_processing.py:569`,
  `models/templates/mediapipe/app.py:571-586`.

## Alternatives rejected

- **Half-pixel centres for each method.** RTMO, RTMW and RTMPose lose parity. The 16 inverse cases
  of `fit` and `affine_person_crop` change, for example by 0.48 px at `s = 0.512`.
- **The `cv2.warpAffine` convention for each method.** The letterbox and stretch models lose
  parity with Ultralytics. 27 inverse cases change.
- **A sidecar field for the convention.** No model needs a second value for its method.

## Not repeated

- torchvision `antialias=False` reproduces `cv2.resize`, not `cv2.warpAffine`.

## Open work

See [open-work.md](../open-work.md).

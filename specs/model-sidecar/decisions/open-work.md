# Open work

This file holds the open work of the [decision log](README.md) of the sidecar spec: the repository
state of the spec and the spec defects. Read the items that apply to your task. The other
repository state is in the root [open-work.md](../../../decisions/open-work.md).

## Repository state

- `specs/model-sidecar/post/canonical-mapping.md` links to the VRM specification by the branch `master`. A
  rewording PR must pin the two links to a commit.

## Re-export requests

This heading holds one item
([Re-export requests](../model-addition-workflow/hand-over.md#re-export-requests);
[ADR-YS4C](../../../decisions/entries/YS4C-example-removal-by-a-user-ruling.md)).

- **Rebuild of each example.** Each exporter rebuilds each of its examples on the spec version
  `2.0.0`. It answers with a new version of the `model` bundle of each example. OpenMMLab-Exporter:
  `rtmw-wholebody`, as `rtmw-wholebody133`. A user ruling gives no rebuild to `rtmdet-person`,
  `yolo26` and `yolo26-body`. The content commit of NBG2 removes them ([ADR-YS4C](../../../decisions/entries/YS4C-example-removal-by-a-user-ruling.md)).
  The prerequisite changes: the removal of the legacy layer
  ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)), the one batch field with
  `output_shapes` in each size ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)), the
  minimal contract ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)), the
  one-statement fix of the selection pipeline
  ([ADR-17KN](../../../decisions/entries/17KN-one-selection-pipeline.md)), the spec version that
  follows the skellytracker version
  ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)), and the
  `license` block with the model license and the training data
  ([ADR-NBG2](entries/NBG2-license-and-training-data-without-the-deferred-examples.md)). The item
  names its target, and each of these changes is accepted. Thus the item is open
  ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md) item 5). It
  closes when each example that stays is an export copy at `2.0.0`.

## Spec defects

Spec defects found during the spec-build stage. Each one needs a content change to the spec:

- `cv2.warpAffine` runs `cv2.INTER_AREA` as `cv2.INTER_LINEAR` (OpenCV 4.13.0). `area` with `fit`
  or `affine_person_crop` thus gives the pixels of `linear`. The
  [interpolation](../pre/interpolation.md#behaviour) table names `cv2.INTER_AREA` for `area`. No
  current model uses this pair ([ADR-G79P](entries/G79P-pixel-centres-per-resize-method.md)).
- The spec has no description of a one-class detector of an object that is not a person. A sidecar
  with no class source must set `decode.is_person_only: true`, so each detection gets the class
  `person_class_id` ([`V-post.det.decode-9`](../post/detection-decode.md#validation-rules);
  [ADR-17KN](../../../decisions/entries/17KN-one-selection-pipeline.md)).
- The spec does not state these facts, but a host needs them:
  - the keypoint scores in a `poses` tensor are already activated (the spec states this only for
    `packed_keypoints`). No exporter checks this channel: the RTMO probe of OpenMMLab-Exporter
    compares only `x` and `y` ([`notes/decisions/scripts/rtmo_sidecar_probe.py:97-102`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/scripts/rtmo_sidecar_probe.py#L97-L102));
  - the host frame is BGR, and the host converts it to `input.color_format`;
  - the arithmetic precision of the geometry (except the warp matrix `M` of `affine_person_crop`)
    and of the pixel math. One case of [ADR-PHJ3](entries/PHJ3-resize-compute-dtype.md) is open: a
    fractional `pad_value` with `compute_dtype: uint8`. The `pre.normalize` reference computes in
    float64 and then casts to `float16`, but a host can compute in float32. Near a `float16`
    rounding midpoint, the two results differ by one `float16` step. This is more than the
    tolerance 1e-5 ([ADR-XH1J](entries/XH1J-normalize-input-dtype.md));
  - the dtype of a score comparison. A float64 score `0.7` passes `>` against a float32 threshold
    `0.7`, because the float32 value is `0.699999988` (numpy 2.4.6).
- The [Storage layout](../format/file-layout.md#storage-layout) gives no folder to a sidecar whose
  `role` has both `object_detector` and `pose_estimator`. Both one-stage pose exporters write such a
  sidecar under `detectors/keypoint_detectors/`. Ultralytics-Exporter uses `yolo26/body/`
  ([`yolo_sidecar.py:104-107`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L104-L107)). OpenMMLab-Exporter uses
  `rtmo/coco17/` ([`rtmo/identity.py:42`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d9704753a22792c32a1d3018a0c9e9ea2d279d71/rtmo/identity.py#L42)).
  The reference example with both roles (YOLO26 pose) uses
  `detectors/keypoint_detectors/{family}/body/`.
- [`letterbox`](../pre/resize-letterbox.md#fields) has no `rounding` value for `floor`, and its
  [inverse](../pre/resize-letterbox.md#inverse) uses the rounded size. The `resize_pad` function of
  `qai_hub_models` 0.64.0 (the MediaPipe person detector) cuts the scaled size with `math.floor`, and
  its inverse divides by the unrounded scale. At the content right edge of a 427x640 source in a
  128x128 canvas, that inverse gives 425 and the spec inverse gives 427. (`qai_hub_models==0.64.0`,
  `qai_hub_models-0.64.0-py3-none-any.whl`, `qai_hub_models/utils/image_processing.py:327-328,
  499-538`; hand calculation)
- The test vectors found these points that the spec does not define. Each vector file avoids them:
  - the box format and the coordinate space of the person box that `affine_person_crop` warps;
  - the order of the final rows for `selection: none`. The YOLO26 graph gives its rows in descending
    score order, and ultralytics 8.4.184 keeps that order with no sort (`utils/nms.py:74-77`).
- No resize method crops a rotated ROI (centre, size and rotation) that the host gives with no
  detector box. `V-post.pose.schema-2` and `V-pre.resize.affine_person_crop-2` tie a top-down model
  to `requires_object_detector: true` and to `affine_person_crop`. The `crop_policy` of that method
  has only `expand_ratio` and `maintain_aspect_ratio`. The MediaPipe Holistic hand chain makes its
  ROI from the wrist, pinky and index keypoints of a body pose. It moves the ROI along its own axis
  (`shift_y` -0.1), makes it square (`square_long`), scales it (2.7, 1.0 or 2.0) and fills the
  border with the edge pixels (MediaPipe-Exporter [`docs/mediapipe-whole-body.md:79-88`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L79-L88), [`docs/mediapipe-whole-body.md:381-399`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L381-L399)).
  Qualcomm-Exporter writes `affine_person_crop` with `expand_ratio: 1.0` as an approximation
  ([`qai_sidecar.py:270-276`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_sidecar.py#L270-L276), [`README.md:129-133`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/README.md#L129-L133)).
  ([Pose schema](../post/pose-schema.md#validation-rules),
  [`affine_person_crop`](../pre/resize-affine-person-crop.md#validation-rules))
- The MediaPipe hand landmark model has four outputs: 21 landmarks, a hand flag, a handedness score
  and 21 world landmarks in metres (MediaPipe-Exporter [`docs/mediapipe-whole-body.md:199`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L199), [`docs/mediapipe-whole-body.md:147-151`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L147-L151)). The closed
  `semantic` set of [Outputs](../common/outputs.md#fields) and `V-post.pose.schema-7` (one
  `keypoints` output for a `coordinate` decoder) let a sidecar declare only the landmarks. MediaPipe
  keeps a hand only when the flag is `> 0.5`. The handedness is the probability of `Right` (label
  item 0) ([`docs/mediapipe-whole-body.md:362-363`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L362-L363), [`docs/mediapipe-whole-body.md:404-408`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L404-L408)). Without the flag, a host gives
  landmarks for a crop with no hand. The landmark wrapper of Qualcomm-Exporter keeps only the
  landmarks ([`qai_catalog.py:358-360`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_catalog.py#L358-L360)).
- [`pose.decode`](../post/pose-schema.md#posedecode) has no field for a divisor of the raw depth. The
  spec has no rule that maps a `pixel` depth to the source image
  ([Unprojection](../post/unprojection.md#behaviour)). MediaPipe computes the depth as
  `z / input_width / normalize_z`. `normalize_z` is 0.4 for the hand graph and 1.0 for the pose and
  face graphs. The projection then multiplies `z` by the ROI width (MediaPipe-Exporter
  [`docs/mediapipe-whole-body.md:141-143`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L141-L143), [`docs/mediapipe-whole-body.md:147-149`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L147-L149)). Qualcomm-Exporter multiplies `z` by the
  input width and writes `depth_unit: pixel` ([`qai_catalog.py:346`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_catalog.py#L346),
  [`qai_sidecar.py:255`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_sidecar.py#L255)). Thus two hosts can give depths that differ by a factor of 2.5.
- The spec has no role for an ROI refiner model. `V-common.identity-2` allows only `object_detector`
  and `pose_estimator` ([Identity](../common/identity.md#validation-rules)). The closed `semantic` set
  has no value for ROI points ([Outputs](../common/outputs.md#fields)). The
  [Storage layout](../format/file-layout.md#storage-layout) has no folder for such a model. The
  MediaPipe Holistic hand ROI refinement model gives two points in crop pixels. The host maps them to
  the image and makes a rotated ROI from them: centre `p0`, size `2 * |p1 - p0|`, rotation target
  -90 degrees, then `shift_y` -0.1, `square_long` and scale 1.0. The input ROI of the model comes from
  keypoints of the parent pose model (MediaPipe-Exporter [`docs/mediapipe-whole-body.md:200`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L200), [`docs/mediapipe-whole-body.md:381-394`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L381-L394)).
  A pose estimator with two points describes the tensor, but then a host reads the points as
  keypoints. This gap depends on the rotated ROI gap above.

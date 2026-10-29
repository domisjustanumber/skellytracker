# Open work

This file holds the open work of the [decision log](README.md) of the sidecar spec: the repository
state of the spec and the spec defects. Read the items that apply to your task. The
implementation-stage items and the other repository state are in the root
[open-work.md](../../../decisions/open-work.md).

## Repository state

- `specs/model-sidecar/post/canonical-mapping.md` links to the VRM specification by the branch `master`. A
  rewording PR must pin the two links to a commit.
- **Absorption gap.** The reviews of 2026-10-24 and 2026-10-25 absorbed every accepted entry except
  [ADR-0011](0011-rtmdet-host-nms.md). [ADR-YNX0](YNX0-vnext-scope-list.md) supersedes 0008. The
  user chose on 2026-10-26 to keep 0011 Active until the proposal 0041 was decided.
  [ADR-SR1E](../../../decisions/SR1E-reset-of-the-spec-build-proposals.md) deleted 0041. Absorb 0011
  into `specs/model-sidecar/post/selection-nms.md#authoring-guidance` when the user agrees. Close its
  gap first: the `-1` row axis of the RTMDet `boxes` and `scores` shapes takes its value from
  `output_shapes`.

## Re-export requests

Each item asks an exporter to regenerate a sidecar or to export it again. It names the exporter
repo, the example or the model, and the reason. The exporter answers with a new version of its
`model` bundle
([Re-export requests](../model-addition-workflow/hand-over.md#re-export-requests)). The session
deletes the item when it lands that bundle.

- [ADR-CNSN](../../../decisions/CNSN-spec-build-actions-after-the-fact.md), owner
  Ultralytics-Exporter, action `regenerate`: `detectors/object_detectors/yolo26/yolo26.yaml`
  (`model_id` `yolo26`) and `detectors/keypoint_detectors/yolo26/body/yolo26-body.yaml` (`model_id`
  `yolo26-body`). Remove the precision key `int8`
  ([Every-version changes](../format/versioning.md#every-version-changes),
  [V-common.sizes_and_artifacts-6](../common/sizes-and-artifacts.md#validation-rules)).
- [ADR-JB5J](../../../decisions/JB5J-one-batch-form-for-each-sidecar.md), owner
  Ultralytics-Exporter, action `export again`: `detectors/object_detectors/yolo26/yolo26.yaml`
  (`model_id` `yolo26`) and `detectors/keypoint_detectors/yolo26/body/yolo26-body.yaml` (`model_id`
  `yolo26-body`). The spec-forced edit of JB5J kept only the batch 1 groups. Run the
  [batch-conversion check](../model-addition-workflow/hand-over.md#batch-conversion-check). With
  the verdict `converts`, the example uses the goal form: only the key `"3"`, with
  `batching.batch_conversion` ([Batch forms](../common/sizes-and-artifacts.md#batch-forms)). With
  another verdict, follow [Publishing](../model-addition-workflow/validation-and-publishing.md#publishing).
- [ADR-JB5J](../../../decisions/JB5J-one-batch-form-for-each-sidecar.md), owner
  OpenMMLab-Exporter, action `export again`:
  `detectors/object_detectors/rtmdet-person/rtmdet-person.yaml` (`model_id` `rtmdet-person`). The
  spec-forced edit of JB5J kept only the batch 1 groups. No measurement of `static-batch-v1` exists
  for this family. Run the
  [batch-conversion check](../model-addition-workflow/hand-over.md#batch-conversion-check). With
  the verdict `converts`, the example uses the goal form: only the key `"3"`, with
  `batching.batch_conversion` ([Batch forms](../common/sizes-and-artifacts.md#batch-forms)). With
  another verdict, follow [Publishing](../model-addition-workflow/validation-and-publishing.md#publishing).

## Spec defects

Spec defects found during the spec-build stage. Each one needs a content change to the spec:

- The note "The `imagenet_bgr` default is the RTMPose convention" in the spec's normalization modes is
  ambiguous at `vNEXT`. At `vNEXT`, `imagenet_bgr` means BGR-ordered statistics, but RTMPose uses the
  legacy meaning ([0009](0009-imagenet-bgr-meaning.md)).
- The reviewer note of the `vNEXT` change summary says to replace `vNEXT` "before merging". The
  workflow section [Publishing](../model-addition-workflow/validation-and-publishing.md#publishing) moves that step to
  the first release that ships the spec.
- The [Identity](../common/identity.md) fields say that a keypoint detector's
  `model_id` is `{family}-{part}`. This rule cannot express a variant suffix or a stage suffix. The
  RTMO body7 reference example, copied from OpenMMLab-Exporter, has `model_id: rtmo-body7` in the
  `body` part folder. A hand landmark model and a hand re-crop model of one family would both get
  `{family}-hand`. The spec must allow a suffix after the part, or the exporters must rename these
  models. OpenMMLab-Exporter sets `FAMILY = "rtmo-body7"` ([`rtmo/identity.py:24`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/identity.py#L24)).
- The [`input.resize`](../pre/interpolation.md#behaviour) text says that every interpolation
  uses "`cv2.resize` / `cv2.warpAffine`, half-pixel centres". `cv2.warpAffine` maps the pixel centres
  in a different way. A 2x upscale of the ramp `[0, 10, 20, 30]` gives `2.5` with `cv2.resize` and
  `5.0` with `cv2.warpAffine` at destination `x = 1` (OpenCV 4.13.0).
- The `pad_value` row of [`input.resize`](../common/input.md#inputresize) and the
  `crop_policy.pad_value` row say only that an array is per channel. They do not say what a scalar
  fills. The `fit` and `affine_person_crop` pseudocode passes `pad_value` unchanged to
  `cv2.warpAffine`. With a scalar, `cv2.warpAffine` fills only channel 0: a scalar `114` gives the
  border `[114, 0, 0]` (OpenCV 4.13.0). The `letterbox` pseudocode fills every channel
  (`full((T_h, T_w, 3), pad_value)`). The spec must state that a scalar fills every channel
  ([0012](0012-fit-resize-for-rtmo.md)).
- `clamp_boxes` in [`decode` (detection)](../post/detection-decode.md#decode-detection) clamps the
  boxes to the source-image bounds. The spec does not define the bounds (`[0, W]` or `[0, W-1]`). It
  does not define the result for a box with zero area after the clamp. OpenMMLab-Exporter
  ([`onnx_runtime/decode_nms.py:170-171`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d2e68d27d2da0a4f22ddd19449df5601dcac87cc/onnx_runtime/decode_nms.py#L170-L171)), Roboflow-Exporter
  ([`rf_detr/coco_format.py:133`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/16852ca3f7e63e61fda1086ecf07491dc788581a/rf_detr/coco_format.py#L133)) and ultralytics 8.4.184 (`utils/ops.py`,
  `clip_boxes`) clamp to `[0, W]` and `[0, H]`.
- `schema_version` is quoted (`"vNEXT"`) in some
  [reference examples](../examples/README.md) and not quoted in the RTMO
  body7 example. YAML reads both forms as the same string, but the examples do not agree.
- Two identity rules of [Validation rules](../format/versioning.md#validation-rules) cannot pass
  at `vNEXT`: the version pattern, and the support by the installed release. Also, the sentence "Rules
  marked **(vNEXT)** apply only when `schema_version >= vNEXT`" is circular for `vNEXT`. `vNEXT` does
  not match the version pattern, so the comparison has no defined result for a `vNEXT` sidecar.
- The spec does not state these facts, but a host needs them:
  - the resizes run on the source dtype (for example `uint8`, before the cast). Roboflow-Exporter
    divides by 255 and then resizes the float image ([`onnx_runtime/preprocess.py:75-78`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/onnx_runtime/preprocess.py#L75-L78));
  - the keypoint scores in a `poses` tensor are already activated (the spec states this only for
    `packed_keypoints`). No exporter checks this channel: the RTMO probe of OpenMMLab-Exporter
    compares only `x` and `y` ([`notes/decisions/scripts/rtmo_sidecar_probe.py:97-102`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/scripts/rtmo_sidecar_probe.py#L97-L102));
  - the host frame is BGR, and the host converts it to `input.color_format`;
  - the arithmetic precision of the geometry and of the pixel math.
- The [Storage layout](../format/file-layout.md#storage-layout) gives no folder to a sidecar whose
  `role` has both `object_detector` and `pose_estimator`. Both one-stage pose exporters write such a
  sidecar under `detectors/keypoint_detectors/`. Ultralytics-Exporter uses `yolo26/body/`
  ([`yolo_sidecar.py:104-107`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L104-L107)). OpenMMLab-Exporter uses
  `rtmo/body7/` ([`rtmo/identity.py:27`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/identity.py#L27)).
  `body7` is not a part folder ([Authoring guidance](../format/file-layout.md#authoring-guidance)).
  The two reference examples with both roles (RTMO body7 and YOLO26 pose) use
  `detectors/keypoint_detectors/{family}/body/`.
- `V-common.outputs-1` (unique `outputs[].name`) has no **(vNEXT)** mark, so the text applies it to a
  legacy sidecar too. The validator of the legacy release does not check it. The legacy YOLO26 pose
  file of Ultralytics-Exporter declares the one tensor `output0` as `detections` and again as
  `poses`. The spec must say which reading is correct. (Ultralytics-Exporter
  [`yolo_sidecar.py:574-582`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L574-L582),
  [`yolo_sidecar.py:596`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L596))
- The spec requires `-1` as the batch axis of `input.shape` (`V-common.sizes_and_artifacts-2`). It
  gives no batch rule for `outputs[].shape`. Ultralytics-Exporter and Qualcomm-Exporter write the
  smallest native batch (`1`) there, and their sizes list the batches 1, 2 and 3. Thus the sentence
  of [`batch_artifacts`](../common/sizes-and-artifacts.md#sizessizeonnxbatch_artifacts) that lets the
  top-level `outputs[].shape` replace the `output_shapes` of a size with one batch key is ambiguous.
  (Ultralytics-Exporter [`yolo_sidecar.py:342-349`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L342-L349),
  [`yolo_sidecar.py:436-455`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L436-L455); Qualcomm-Exporter
  [`qai_sidecar.py:79-95`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L79-L95),
  [`qai_sidecar.py:111-118`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L111-L118))
- [`letterbox`](../pre/resize-letterbox.md#fields) has no `rounding` value for `floor`, and its
  [inverse](../pre/resize-letterbox.md#inverse) uses the rounded size. The `resize_pad` function of
  `qai_hub_models` 0.64.0 (the MediaPipe person detector) cuts the scaled size with `math.floor`, and
  its inverse divides by the unrounded scale. At the content right edge of a 427x640 source in a
  128x128 canvas, that inverse gives 425 and the spec inverse gives 427. (`qai_hub_models==0.64.0`,
  `qai_hub_models-0.64.0-py3-none-any.whl`, `qai_hub_models/utils/image_processing.py:327-328,
  499-538`; hand calculation)
- A code docstring under `skellytracker/` cites the spec heading "Sizes", but the heading is `sizes`.
- The test vectors found these points that the spec does not define. Each vector file avoids them:
  - the box format and the coordinate space of the person box that `affine_person_crop` warps;
  - the order of the final rows for `selection: none`. The YOLO26 graph gives its rows in descending
    score order, and ultralytics 8.4.184 keeps that order with no sort (`utils/nms.py:74-77`);
  - the class of a candidate that has no class source when `is_person_only` is `false` (for
    `selection: none` and `top_k`);
  - the pixel-centre convention of the unprojection (see the `cv2.warpAffine` item above).
- The default `confidence_threshold_default` is `0.7` with a strict `>`, so a score of exactly `0.7`
  is dropped. The spec does not say that this is intended. The upstream of Qualcomm-Exporter,
  `qai_hub_models` 0.64.0, keeps a score equal to the threshold in `batched_nms` (`>=`,
  `utils/bounding_box_processing.py:86`).
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
- [SimCC decode](../post/pose-decode-simcc.md#behaviour) says "Its score is the max value". SimCC has
  two peaks for each keypoint. The text does not say how the two peaks combine, if a softmax comes
  first, which bin a tie selects, or what a score `<= 0` gives. mmpose v1.3.2 applies no softmax
  by default (`apply_softmax=False`,
  [`mmpose/codecs/utils/post_processing.py:41-44`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/codecs/utils/post_processing.py#L41-L44)).
  It takes the smaller of the two raw peaks, and sets the location to `-1` for a score `<= 0`
  ([`mmpose/codecs/utils/post_processing.py:93-99`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/codecs/utils/post_processing.py#L93-L99)). The skellytracker host takes the mean of
  the two softmax peaks
  ([`simcc_decode.py`](../../../skellytracker/core/detectors/processing/simcc_decode.py), lines
  53-63). Thus a keypoint threshold does not transfer from one host to the other.
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

# Reference examples

Revision: [Changes in this revision](../changelog.md#changes-in-this-revision-vnext).

Each example is a sidecar for this revision from the named exporter. The OpenMMLab-Exporter examples (RTMDet person, RTMW, RTMO body7) come from its real `vNEXT` exports. The Ultralytics-Exporter examples (YOLO26 detection and pose) are written from that exporter's code and published artifacts: tensor names, shapes, dtypes, sizes, batches, precisions and filenames. They will be replaced when it emits `vNEXT`. There is no RF-DETR example until Roboflow-Exporter is overhauled; the `stretch`, `top_k` and `class_logits` rules have no example until then. Where a family has more sizes than shown, the omitted sizes differ only in `input.shape`, `target_size` and filenames.

## YOLO26 detector (Ultralytics-Exporter; NMS-free, graph-final rows)

Centre letterbox with half-even rounding, RGB `unit_float` input, and one packed `[B, 300, 6]` tensor of final detections (`nms=False`, `max_det=300` at export). Every precision, including int8, keeps float32 I/O.

```yaml
---
schema_version: "vNEXT"
model_id: yolo26
display_name: YOLO26
role: [object_detector]

input:
  name: images
  dtype: {fp32: float32, fp16: float32, int8: float32}
  layout: NCHW
  color_format: rgb
  normalization: unit_float
  resize: {method: letterbox, pad_position: center, rounding: half_even, pad_value: 114, interpolation: linear}

batching: {batch_axis: 0}

outputs:
  - name: output0
    dtype: {fp32: float32, fp16: float32, int8: float32}
    shape: [-1, 300, 6]
    rank: 3
    semantic: detections
    fields: [x1, y1, x2, y2, score, class_id]

decode:
  selection: none
  max_detections: 300
  box_format: xyxy
  box_scale: pixel
  score_field: score
  class_field: class_id
  class_id_base: 0
  person_class_id: 0
  is_person_only: false
  confidence_threshold_default: 0.7

sizes:
  nano:
    input:
      shape: [-1, 3, 640, 640]
      resize:
        target_size: [640, 640]
    onnx:
      batch_artifacts:
        "1":
          precision_artifacts:
            fp32: {filename: yolo26-nano_b1_fp32.onnx}
            fp16: {filename: yolo26-nano_b1_fp16.onnx}
            int8: {filename: yolo26-nano_b1_int8.onnx}
          output_shapes:
            - [1, 300, 6]
        "2":
          precision_artifacts:
            fp32: {filename: yolo26-nano_b2_fp32.onnx}
            fp16: {filename: yolo26-nano_b2_fp16.onnx}
            int8: {filename: yolo26-nano_b2_int8.onnx}
          output_shapes:
            - [2, 300, 6]
        "3":
          precision_artifacts:
            fp32: {filename: yolo26-nano_b3_fp32.onnx}
            fp16: {filename: yolo26-nano_b3_fp16.onnx}
            int8: {filename: yolo26-nano_b3_int8.onnx}
          output_shapes:
            - [3, 300, 6]
  # small, medium, large, xlarge: identical to nano (640x640, batches 1-3) except filenames.
```

## YOLO26 pose (Ultralytics-Exporter; bottom-up, packed keypoints)

The pose export emits one `[B, 300, 57]` tensor: 6 detection columns followed by 17 × `(x, y, score)`, with keypoints in model-input pixels and keypoint scores already sigmoid-activated. It is declared once, with `packed_keypoints`.

```yaml
---
schema_version: "vNEXT"
model_id: yolo26-body
display_name: YOLO26 Pose
role: [object_detector, pose_estimator]

input:
  name: images
  dtype: {fp32: float32, fp16: float32, int8: float32}
  layout: NCHW
  color_format: rgb
  normalization: unit_float
  resize: {method: letterbox, pad_position: center, rounding: half_even, pad_value: 114, interpolation: linear}

batching: {batch_axis: 0}

outputs:
  - name: output0
    dtype: {fp32: float32, fp16: float32, int8: float32}
    shape: [-1, 300, 57]
    rank: 3
    semantic: detections
    fields: [x1, y1, x2, y2, score, class_id]
    packed_keypoints:
      offset: 6
      components: [x, y, score]

decode:
  selection: none
  max_detections: 300
  box_format: xyxy
  box_scale: pixel
  score_field: score
  class_field: class_id
  class_id_base: 0
  person_class_id: 0
  is_person_only: true
  confidence_threshold_default: 0.3

pose:
  estimator_type: bottom_up
  requires_object_detector: false
  landmark_schema: COCO17
  tracked_points: [nose, left_eye, right_eye, left_ear, right_ear, left_shoulder, right_shoulder, left_elbow, right_elbow,
    left_wrist, right_wrist, left_hip, right_hip, left_knee, right_knee, left_ankle, right_ankle]
  connections:
    - name: coco_17
      edges:
        - [nose, left_eye]
        - [nose, right_eye]
        - [left_eye, left_ear]
        - [right_eye, right_ear]
        - [left_shoulder, right_shoulder]
        - [left_shoulder, left_elbow]
        - [left_elbow, left_wrist]
        - [right_shoulder, right_elbow]
        - [right_elbow, right_wrist]
        - [left_shoulder, left_hip]
        - [right_shoulder, right_hip]
        - [left_hip, right_hip]
        - [left_hip, left_knee]
        - [left_knee, left_ankle]
        - [right_hip, right_knee]
        - [right_knee, right_ankle]
  decode:
    method: coordinate
    coordinate_scale: pixel

overlay:
  skeleton: coco_17
  keypoint_color: [0, 183, 235]
  groups:
    left:
      prefix: left_
      connection_color: [0, 200, 83]
    right:
      prefix: right_
      connection_color: [255, 82, 82]
    body:
      connection_color: [0, 183, 235]

sizes:
  nano:
    input:
      shape: [-1, 3, 640, 640]
      resize:
        target_size: [640, 640]
    onnx:
      batch_artifacts:
        "1":
          precision_artifacts:
            fp32: {filename: yolo26-body-nano_b1_fp32.onnx}
            fp16: {filename: yolo26-body-nano_b1_fp16.onnx}
            int8: {filename: yolo26-body-nano_b1_int8.onnx}
          output_shapes:
            - [1, 300, 57]
        "2":
          precision_artifacts:
            fp32: {filename: yolo26-body-nano_b2_fp32.onnx}
            fp16: {filename: yolo26-body-nano_b2_fp16.onnx}
            int8: {filename: yolo26-body-nano_b2_int8.onnx}
          output_shapes:
            - [2, 300, 57]
        "3":
          precision_artifacts:
            fp32: {filename: yolo26-body-nano_b3_fp32.onnx}
            fp16: {filename: yolo26-body-nano_b3_fp16.onnx}
            int8: {filename: yolo26-body-nano_b3_int8.onnx}
          output_shapes:
            - [3, 300, 57]
  # small, medium, large, xlarge: identical to nano except filenames.
```

## RTMDet person (OpenMMLab-Exporter; NMS-free outputs, host NMS)

The mmdet test pipeline letterboxes into the top-left corner with half-up rounding and pad 114, normalizing BGR pixels. The graph emits every anchor point's decoded box and sigmoid person score; the host runs the family's baseline NMS (`score_thr` 0.05, IoU 0.6, `max_per_img` 100). The row count depends on input size: 2100 at 320 and 8400 at 640.

```yaml
---
schema_version: "vNEXT"
model_id: rtmdet-person
display_name: RTMDet Person
role: [object_detector]

input:
  name: input
  dtype: {fp32: float32, fp16: float32}
  layout: NCHW
  color_format: bgr
  normalization: imagenet_bgr
  resize: {method: letterbox, pad_position: top_left, rounding: half_up, pad_value: 114, interpolation: linear}

batching: {batch_axis: 0}

outputs:
  - name: boxes
    dtype: {fp32: float32, fp16: float32}
    shape: [-1, -1, 4]
    rank: 3
    semantic: boxes
  - name: scores
    dtype: {fp32: float32, fp16: float32}
    shape: [-1, -1]
    rank: 2
    semantic: scores

decode:
  selection: nms
  boxes_output: boxes
  scores_output: scores
  box_format: xyxy
  box_scale: pixel
  class_id_base: 0
  person_class_id: 0
  is_person_only: true
  confidence_threshold_default: 0.7
  clamp_boxes: true
  nms:
    iou_threshold: 0.6
    score_threshold: 0.05
    class_agnostic: false
    post_nms_top_k: 100

sizes:
  nano:
    input:
      shape: [-1, 3, 320, 320]
      resize:
        target_size: [320, 320]
    onnx:
      batch_artifacts:
        "1":
          precision_artifacts:
            fp32: {filename: rtmdet-person-nano_b1_fp32.onnx}
            fp16: {filename: rtmdet-person-nano_b1_fp16.onnx}
          output_shapes:
            - [1, 2100, 4]
            - [1, 2100]
        "2":
          precision_artifacts:
            fp32: {filename: rtmdet-person-nano_b2_fp32.onnx}
            fp16: {filename: rtmdet-person-nano_b2_fp16.onnx}
          output_shapes:
            - [2, 2100, 4]
            - [2, 2100]
  medium:
    input:
      shape: [-1, 3, 640, 640]
      resize:
        target_size: [640, 640]
    onnx:
      batch_artifacts:
        "1":
          precision_artifacts:
            fp32: {filename: rtmdet-person-medium_b1_fp32.onnx}
            fp16: {filename: rtmdet-person-medium_b1_fp16.onnx}
          output_shapes:
            - [1, 8400, 4]
            - [1, 8400]
        # "2": same pattern, with row count 8400.
```

The graph ends before NMS. It emits every anchor point's decoded box and sigmoid person score, so the host applies the family's baseline NMS (mmpose `test_cfg`: score > 0.05, IoU 0.6, top 100). The row count is the anchor-point count for the input size (2100 at 320, 8400 at 640), so the family-level shape leaves it as `-1`. mmdet's per-level `nms_pre` cap (1000) is deliberately not expressed; dropping it has no measurable effect on AP.

## RTMW WholeBody (OpenMMLab-Exporter; top-down pose)

mmpose `input_size` is `(width, height)`: the `256x192` models take `[N, 3, 256, 192]` input and the `384x288` models `[N, 3, 384, 288]`. The model consumes RGB (`bgr_to_rgb=True`) normalized with ImageNet statistics. SIMCC bin counts are twice the input width/height (`simcc_split_ratio=2.0`) and are read from the output tensors, so `shape` is omitted.

```yaml
---
schema_version: "vNEXT"
model_id: rtmw-wholebody
display_name: RTMW WholeBody
role: [pose_estimator]

input:
  name: input
  dtype: {fp32: float32, fp16: float32}
  layout: NCHW
  color_format: rgb
  normalization: imagenet_rgb
  resize:
    method: affine_person_crop
    interpolation: linear
    crop_policy:
      expand_ratio: 1.25
      maintain_aspect_ratio: true
      pad_value: 0

batching: {batch_axis: 0}

outputs:
  - name: simcc_x
    dtype: {fp32: float32, fp16: float32}
    semantic: simcc_x
    keypoint_axis: 1
    keypoint_count: 133
  - name: simcc_y
    dtype: {fp32: float32, fp16: float32}
    semantic: simcc_y
    keypoint_axis: 1
    keypoint_count: 133

pose:
  estimator_type: top_down_single_person
  requires_object_detector: true
  landmark_schema: COCO_WholeBody
  # The exporter currently inlines these 133 names and edges; the shared fragments are equivalent.
  tracked_points: {$ref: ../../../shared/skeletons/coco133_tracked_points.yaml}
  connections: {$ref: ../../../shared/skeletons/coco133_skeletons.yaml}
  decode:
    method: simcc

overlay:
  skeleton: rtmpose_skeleton
  groups:
    right_hand:
      prefix: right_hand_
      connection_color: [0, 100, 255]
    left_hand:
      prefix: left_hand_
      connection_color: [255, 100, 0]
    face:
      prefix: face_
      connection_color: [200, 0, 200]
    body:
      connection_color: [0, 200, 100]

sizes:
  m:
    input:
      shape: [-1, 3, 256, 192]
      resize:
        target_size: [256, 192]
    onnx:
      batch_artifacts:
        "1":
          precision_artifacts:
            fp32: {filename: rtmw-wholebody-m_b1_fp32.onnx}
            fp16: {filename: rtmw-wholebody-m_b1_fp16.onnx}
  l-384:
    input:
      shape: [-1, 3, 384, 288]
      resize:
        target_size: [384, 288]
    onnx:
      batch_artifacts:
        "1":
          precision_artifacts:
            fp32: {filename: rtmw-wholebody-l-384_b1_fp32.onnx}
            fp16: {filename: rtmw-wholebody-l-384_b1_fp16.onnx}
  # l-256, x-256 (256x192) and x-384 (384x288): same pattern.
```

For comparison, skellytracker's in-repo `rtmw/wholebody/rtmw-wholebody.yaml` describes the rtmlib `onnx_sdk` downloads (with `url`/`url_sha256`) at `schema_version: v2024.09.1019`. It uses the legacy `imagenet_bgr` meaning (see [Version-aware compatibility](../pre/normalization.md#legacy-behaviour)).

## RTMO body7 (OpenMMLab-Exporter; bottom-up pose, NMS in the graph)

Source: OpenMMLab-Exporter `notes/decisions/rtmo-body7.yaml` at commit `38ed76f` (the tracked copy of the sidecar its `rtmo-body7` family writes; header comment removed). Spec path: `detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml`. The exporter writes it to `rtmo/body7/`, which is not one of the spec's part folders.

mmpose `BottomupResize` warps the whole frame with `cv2.warpAffine` to a fractional fit size, centred, with pad 114: that is `fit`, not `letterbox`. RTMO normalizes with mean 0 and std 1 and keeps BGR (`bgr_to_rgb: false`), so the input is `normalization: none` with `color_format: bgr`. The deployed graph keeps NMS, so the `dets` and `keypoints` row count is dynamic and the host uses `selection: none` with no `max_detections`. `confidence_threshold_default` is the upstream `score_thr` (0.1); it drops the near-zero row that the graph can emit on an image with no person.

```yaml
---
schema_version: vNEXT
model_id: rtmo-body7
display_name: RTMO Body7
role: [object_detector, pose_estimator]

input:
  name: input
  dtype: {fp32: float32}
  layout: NCHW
  color_format: bgr
  normalization: none
  resize:
    method: fit
    pad_value: 114
    interpolation: linear

batching: {batch_axis: 0}

outputs:
  - name: dets
    dtype: {fp32: float32}
    shape: [-1, -1, 5]
    rank: 3
    semantic: detections
    fields: [x1, y1, x2, y2, score]
  - name: keypoints
    dtype: {fp32: float32}
    shape: [-1, -1, 17, 3]
    rank: 4
    semantic: poses
    keypoint_axis: 2
    keypoint_count: 17

decode:
  selection: none
  box_format: xyxy
  box_scale: pixel
  score_field: score
  is_person_only: true
  confidence_threshold_default: 0.1
  clamp_boxes: true

pose:
  estimator_type: bottom_up
  requires_object_detector: false
  landmark_schema: COCO17
  tracked_points:
    - nose
    - left_eye
    - right_eye
    - left_ear
    - right_ear
    - left_shoulder
    - right_shoulder
    - left_elbow
    - right_elbow
    - left_wrist
    - right_wrist
    - left_hip
    - right_hip
    - left_knee
    - right_knee
    - left_ankle
    - right_ankle
  connections:
    - name: coco
      edges:
        - [left_ankle, left_knee]
        - [left_knee, left_hip]
        - [right_ankle, right_knee]
        - [right_knee, right_hip]
        - [left_hip, right_hip]
        - [left_shoulder, left_hip]
        - [right_shoulder, right_hip]
        - [left_shoulder, right_shoulder]
        - [left_shoulder, left_elbow]
        - [right_shoulder, right_elbow]
        - [left_elbow, left_wrist]
        - [right_elbow, right_wrist]
        - [left_eye, right_eye]
        - [nose, left_eye]
        - [nose, right_eye]
        - [left_eye, left_ear]
        - [right_eye, right_ear]
        - [left_ear, left_shoulder]
        - [right_ear, right_shoulder]
  decode:
    method: coordinate
    coordinate_scale: pixel

overlay:
  skeleton: coco
  groups:
    body:
      connection_color: [0, 200, 83]

sizes:
  m:
    input:
      shape: [-1, 3, 640, 640]
      resize:
        target_size: [640, 640]
    onnx:
      batch_artifacts:
        "1":
          precision_artifacts:
            fp32: {filename: rtmo-body7-m_b1_fp32.onnx}
```

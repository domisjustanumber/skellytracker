# Open work

This file holds the open work of the [decision log](README.md) of the sidecar spec: the repository
state of the spec and the spec defects. Read the items that apply to your task. The
implementation-stage items and the other repository state are in the root
[open-work.md](../../../decisions/open-work.md).

## Repository state

- `specs/model-sidecar/post/canonical-mapping.md` links to the VRM specification by the branch `master`. A
  rewording PR must pin the two links to a commit.
- **Absorption gaps.** The reviews of 2026-10-24 and 2026-10-25 absorbed every accepted entry except
  [0008](0008-vnext-scope.md) and [0011](0011-rtmdet-host-nms.md). The proposals 0042 and 0048
  supersede 0008, and 0041 supersedes 0011, on acceptance. An absorbed entry can be superseded
  ([ngnb](../../../decisions/ngnb-supersede-an-absorbed-entry.md)), but the user chose on 2026-10-26 to keep 0008 and
  0011 Active until the proposals are decided. Then absorb each entry that no accepted proposal
  supersedes: absorb 0008 into
  `specs/model-sidecar/changelog.md#considered-and-deliberately-not-added` and 0011 into
  `specs/model-sidecar/post/selection-nms.md#authoring-guidance`. Close their gaps first: Qualcomm-Exporter
  is out of the `vNEXT` scope until its library is complete (0008), and the `-1` row axis of the RTMDet
  `boxes` and `scores` shapes takes its value from `output_shapes` (0011).

## Spec defects

Spec defects found during the spec-build stage. Each one needs a content change to the spec:

- The note "The `imagenet_bgr` default is the RTMPose convention" in the spec's normalization modes is
  ambiguous at `vNEXT`. At `vNEXT`, `imagenet_bgr` means BGR-ordered statistics, but RTMPose uses the
  legacy meaning ([0009](0009-imagenet-bgr-meaning.md)).
- The reviewer note of the `vNEXT` change summary says to replace `vNEXT` "before merging". Decision
  [0014](../../../decisions/0014-spec-lifecycle.md) moves that step to the first release that ships the spec.
- The [Identity](../common/identity.md) fields say that a keypoint detector's
  `model_id` is `{family}-{part}`. This rule cannot express a variant suffix or a stage suffix. The
  RTMO body7 reference example, copied from OpenMMLab-Exporter, has `model_id: rtmo-body7` in the
  `body` part folder. A hand landmark model and a hand re-crop model of one family would both get
  `{family}-hand`. The spec must allow a suffix after the part, or the exporters must rename these
  models. OpenMMLab-Exporter sets `FAMILY = "rtmo-body7"` ([`rtmo/identity.py:24`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/identity.py#L24)).
  The gap record [0025](0025-model-id-suffix.md) (proposed) records this question.
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

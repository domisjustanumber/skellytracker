# 0007 — Generic pre- and post-processing live in `core/detectors/processing/`

**Status:** absorbed into [`AGENTS.md#1-purpose`](../AGENTS.md#1-purpose), 2026-10-25 (user; the absorption review).
cleanup in [M3](../specs/sidecar-implementation-plan.md#m3--yolox-migration), then
[M4c](../specs/sidecar-implementation-plan.md#m4c--consolidate-generic-preprocessingdecode-helpers) and
[M4d](../specs/sidecar-implementation-plan.md#m4d--group-generic-prepost-processing-under-coredetectorsprocessing)).
The user asked for the move to `processing/` (M4d).

## Decision

- Generic processing code lives in `skellytracker/core/detectors/processing/`. Generic code prepares an
  image for a model or decodes a model output. It does not belong to one model family.
- A caller imports the specific module. The file `processing/__init__.py` is empty and re-exports
  nothing.
- Code that belongs to one family stays with that family. The YOLOX anchor-grid decode and the
  `yolox_detection_decode` dispatcher stay in
  `core/detectors/object_detectors/yolox/yolox_decode.py`.
- `core/detectors/overlay_groups.py` stays next to `processing/`. It groups skeleton connections for
  annotation. It does not process model tensors.
- `core/sidecar/` keeps only the code that parses and resolves sidecars. `core/sidecar/runtime.py`
  holds only `sidecar_model_spec`.

The package holds these modules:

| Module | Contents |
|---|---|
| `image_preprocessing.py` | `resolve_normalization_mode`, `build_normalization_fn`, `letterbox_preprocess`, `fit_preprocess`, `preprocess_image` |
| `object_detection_decode.py` | `nms`, `multiclass_nms`, `boxes_to_xyxy`, `decode_prenms`, `decode_nms_baked_in` |
| `affine_crop.py` | `get_warp_matrix`, `bbox_xyxy2cs`, `top_down_affine` (and two private helpers) |
| `simcc_decode.py` | `get_simcc_maximum`, `decode_simcc`, `simcc_pose_decode` (and one private helper) |

## Reason

- The code is generic. Some of it sat in a family folder because of the place where it was first
  vendored.
  - The affine-crop math is the usual top-down transform from a box to a crop. Many pose models use it.
    It is not RTMPose code.
  - SIMCC is a decode head. Several model families share it. It is not RTMPose code.
  - The NMS and box-format functions make no assumption about a model family.
- The code reads specs that a sidecar describes (`InputSpec`, `DetectionDecodeSpec`, `PoseDecodeSpec`).
  The sidecar only supplies the configuration values. The code processes images and tensors. It does
  not parse sidecars. This is why it is not in `core/sidecar/`.
- A location inside `keypoint_detectors/rtmpose/` forced deferred imports. Any import from that package
  runs `rtmpose/__init__.py`, which imports the detectors. A module-level import of the helpers from
  `image_preprocessing.py` or from the RTMW detector made an import cycle. After the move, these
  imports are normal module-level imports.
- Four generic modules stood loose in `core/detectors/` next to other detector modules
  (`detection_context.py`, `detector_base_classes.py`, `metadata.py`, `overlay_groups.py`). One package
  separates the processing code from them.
- A new model family can reuse the modules. It does not need its own copy.

## Evidence

Checked in the code on 2026-10-22.

- The files in `core/detectors/processing/` are `__init__.py` (0 bytes), `affine_crop.py`,
  `image_preprocessing.py`, `object_detection_decode.py` and `simcc_decode.py`. The function list in the
  table comes from these files. `fit_preprocess` came after the move, with the `fit` resize method.
- Apart from the standard library, the modules import only `numpy`, `cv2`, `beartype` and the spec
  types in `skellytracker/core/sidecar/model.py`. `image_preprocessing.py` also imports
  `affine_crop.py`. `skellytracker/core/sidecar/` does not import from `core/detectors/`.
- These files import from `processing/`:
  - `preprocess_image`: `yolox_person_detector.py`, `rtmw_wholebody_detector.py`,
    `rtmpose_body_detector.py`, `rtmpose_hand_detector.py` and `rtmpose_face_detector.py`.
  - `simcc_pose_decode`: the four RTMW and RTMPose detectors.
  - `decode_nms_baked_in`, `decode_prenms` and `multiclass_nms`: `yolox_decode.py`.
  - The tests `skellytracker/tests/test_image_preprocessing.py` and
    `skellytracker/tests/test_object_detection_decode.py`.
- `rtmpose_simcc_decode.py` does not exist. The file
  `keypoint_detectors/rtmpose/rtmpose_preprocessing.py` still exists. No Python file imports it. It
  holds identical copies of `get_simcc_maximum`, `get_warp_matrix`, `bbox_xyxy2cs` and
  `top_down_affine`. It also holds `rtmpose_letterbox_preprocess` and `rtmpose_letterbox_postprocess`.
  The section M4c of `specs/sidecar-implementation-plan.md` says that the move deleted this file.
  The code does not agree.

## Not repeated

- Do not recreate a SIMCC decode module for one family. `simcc_decode.py` serves the RTMW whole-body
  detector and the RTMPose body, hand and face detectors.
- Do not move family-specific code into `processing/`. The YOLOX raw anchor-grid decode depends on the
  YOLOX head, so it stays in `yolox_decode.py`.
- Do not put generic processing code back inside a family package. The `rtmpose` package imports its
  detectors in `__init__.py`. An import from it brings back the import cycle that
  [0005](0005-rtmw-moved-to-rtmw-family.md) describes.
- Do not write migration history in the docstrings of the detectors. The user decided this when the code
  moved to `processing/`. Write the history in a decision entry or in a commit message.

_Edited 2026-10-28 (this PR): link repair._

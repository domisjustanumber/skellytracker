# 0004 — Detectors migrated to sidecars in place; registry keys unchanged

**Status:** accepted, 2026-10-22 (backfilled from #81).

## Decision

- The existing detector classes changed in place. Each class replaced its hard-coded constants (model
  URLs, mean and standard deviation, input sizes, output order) with lookups in its sidecar. The
  migration added no new detector class.
- Each detector keeps its `detector_type` string. This string is the key of the detector in
  `OBJECT_DETECTOR_REGISTRY` or `KEYPOINT_DETECTOR_REGISTRY`
  (`skellytracker/core/detectors/detector_base_classes.py`):

  | `detector_type` | Registry | Class | Sidecar |
  |---|---|---|---|
  | `yolox_person` | object detector | `YoloxPersonDetector` | `yolox.yaml` |
  | `rtmpose` | keypoint detector | `RTMWWholebodyDetector` | `rtmw-wholebody.yaml` |
  | `rtmpose_body` | keypoint detector | `RTMPoseBodyDetector` | `rtmpose-body.yaml` |
  | `rtmpose_hand` | keypoint detector | `RTMPoseHandDetector` | `rtmpose-hand.yaml` |
  | `rtmpose_face` | keypoint detector | `RTMPoseFaceDetector` | `rtmpose-face.yaml` |

- Each detector keeps the fields of its config class and the signatures of `preprocess`, `postprocess`,
  `detect` and `connections`. `build_object_detector`, `build_keypoint_detector`, `TrackerConfig` and the
  other call sites need no change.
- The migration changed no behavior. The models and the math stayed the same. The output stayed the same
  for each point name. The RTMW whole-body array order changed (see
  [0003](0003-tracked-points-native-order.md)).
- The decode and affine-crop math is the code that existed before. The YOLOX decode functions
  (`_postprocess_prenms`, `_postprocess_yolox`) came from `yolox_person_detector.py`. The YOLOX letterbox
  and NMS functions came from `yolox_preprocessing.py`. The affine-crop and SIMCC decode functions came
  from `rtmpose_preprocessing.py`. The code did not change when it moved. Those functions have since moved
  again. See [0007](0007-generic-processing-package.md).
- The RTMW whole-body class and its config got new names (`RTMWWholebodyDetector`,
  `RTMWWholebodyDetectorConfig`). The key `rtmpose` did not change. Decision
  [0005](0005-rtmw-moved-to-rtmw-family.md) describes the move and the shims for the old names.

## Reason

- Callers choose a detector by its `detector_type` string. A new key would break each config and each call
  site that uses the old one. With the same key, config and signatures, these callers keep working.
- The migration had to change no behavior. The goal was the same models and the same math, loaded from
  sidecar YAML in place of Python constants (see "Context" in
  [`specs/sidecar-implementation-plan.md`](../../specs/sidecar-implementation-plan.md#context)).
- Reuse of the same decode math keeps the outputs equal. The parity tests check this.

## Evidence

- The registrations are in these files:
  - `skellytracker/core/detectors/object_detectors/yolox/yolox_person_detector.py`:
    `OBJECT_DETECTOR_REGISTRY["yolox_person"]`
  - `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py`:
    `KEYPOINT_DETECTOR_REGISTRY["rtmpose"]`
  - `skellytracker/core/detectors/keypoint_detectors/rtmpose/body/rtmpose_body_detector.py`,
    `.../hand/rtmpose_hand_detector.py` and `.../face/rtmpose_face_detector.py`:
    `"rtmpose_body"`, `"rtmpose_hand"` and `"rtmpose_face"`
- Each of these five modules loads its sidecar once, when Python imports the module
  (`_SIDECAR = load_sidecar(...)`).
- `YoloxPersonDetectorConfig` has the same fields before and after the migration: `detector_type`,
  `session_backend`, `model_name`, `score_threshold`, `nms_threshold`, `max_detections`. The RTMW
  whole-body config has the same fields before and after the migration: `detector_type`,
  `session_backend`, `model_name`, `confidence_threshold`.
- The signatures of `preprocess`, `postprocess`, `detect`, `connections`, `create` and `model_spec` are the
  same before and after the migration, in all five detector classes. There are two differences. #86 later
  added the argument `parent_keypoints` to `YoloxPersonDetector.detect()`. The migration renamed the RTMW
  class, so the return type of its `create()` is now `RTMWWholebodyDetector`.
- `build_object_detector()` and `build_keypoint_detector()` look up `config.detector_type` in the
  registries. `DetectionStage` in `skellytracker/core/tracker/detection_stage.py` calls them.
- `skellytracker/tests/test_rtmpose_detectors.py` asserts the two original keys in `TestRegistry`.
  `skellytracker/tests/test_run_batched.py` imports from the old module path of the RTMW detector. The
  implementation plan records that these tests pass without change. See section "M4 — RTMW migration" of
  [`specs/sidecar-implementation-plan.md`](../../specs/sidecar-implementation-plan.md#m4--rtmw-migration).
- Parity tests compare the migrated detectors with output captured before the migration. The golden
  fixtures are in `skellytracker/tests/sidecar/fixtures/golden/`: `yolox_*_detect.json` (2 sizes),
  `rtmw_wholebody_*_detect.json` (3 sizes) and `rtmpose_{body,hand,face}_*_detect.json`.
- The results differ across machines and execution providers. Thus the parity tests run on the CPU
  provider and compare at the precision of the model itself
  (`skellytracker/tests/sidecar/golden_parity.py`). A YOLOX box passes when its IoU with the fixture
  box is at least 0.99 and its confidence is within 0.01. A SimCC keypoint passes as given in
  [0003](0003-tracked-points-native-order.md). The RTMPose face fixture and the two YOLOX fixtures
  were made again on the CPU provider from the code before the migration. Each fixture records its
  source in `skellytracker/tests/sidecar/fixtures/golden/environments.json`.

## Not repeated

- Do not change a `detector_type` string. Callers select detectors with it.
- The key `rtmpose` names the RTMW whole-body detector. It does not name the whole RTMPose family. The
  body, hand and face detectors use `rtmpose_body`, `rtmpose_hand` and `rtmpose_face`.
- A registry key is not a catalog key. Decision [0016](0016-sidecar-catalogs.md) keeps these
  `detector_type` strings as aliases of `<model_id>@skellytracker`.

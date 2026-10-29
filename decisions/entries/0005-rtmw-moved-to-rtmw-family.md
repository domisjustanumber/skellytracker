# 0005 — RTMW moved to `keypoint_detectors/rtmw/` with import shims

**Status:** absorbed into [`AGENTS.md#1-purpose`](../../AGENTS.md#1-purpose), 2026-10-25 (user; the absorption review).
[specs/sidecar-implementation-plan.md](../../specs/sidecar-implementation-plan.md#key-decisions), "Key decisions" item 4).

## Decision

- The RTMW whole-body detector lives in `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/`.
  It moved from `keypoint_detectors/rtmpose/wholebody/`.
- The folder holds `rtmw_wholebody_detector.py`, `rtmw-wholebody.yaml` and
  `rtmw_wholebody_to_canonical_mapping.yaml`.
- The classes are `RTMWWholebodyDetector` and `RTMWWholebodyDetectorConfig`. The size table is
  `RTMW_WHOLEBODY_MODEL_SPECS`.
- The old import paths must keep working. A shim is a module that only re-exports names. These shims
  re-export the old names `RTMPoseDetectorConfig`, `RTMPoseKeypointDetector` and `RTMPOSE_MODEL_SPECS`:
  - `keypoint_detectors/rtmpose/wholebody/rtmpose_wholebody_detector.py` imports the three RTMW names
    and gives them the old names.
  - `keypoint_detectors/rtmpose/rtmpose_keypoint_detector.py` re-exports the same three names from the
    first shim. This shim existed before the move. The move did not change it.
  - `keypoint_detectors/rtmpose/__init__.py` imports the first shim. The import registers the detector.
    It re-exports the old names and the names of the body, hand and face detectors. The move did not
    change this file.
- The registry key stays `"rtmpose"`. See [0004](0004-detectors-migrated-in-place.md).

## Reason

- The spec names this family `rtmw`. The `model_id` is `rtmw-wholebody`. The
  [storage layout](../../specs/model-sidecar/format/file-layout.md#storage-layout) puts a keypoint sidecar at
  `detectors/keypoint_detectors/{family}/{part}/`. The folder `rtmpose/wholebody/` did not match the
  family name.
- Other code imports the old paths. A search of the importers found the files in the Evidence section.
  The shims keep them working without an edit.
- The registry key and the config field `detector_type` are part of the config surface. A rename
  would break the existing call sites. See [0004](0004-detectors-migrated-in-place.md).

## Evidence

Checked in the code on 2026-10-22.

- These files import from the old paths. The shims serve them:
  - `skellytracker/examples/run_rtmpose_on_folder.py` and
    `skellytracker/examples/run_multiperson_on_video.py` import from `keypoint_detectors.rtmpose`.
  - `skellytracker/tests/test_rtmpose_detectors.py`, `skellytracker/tests/test_rtmpose_video.py` and
    `skellytracker/tests/test_yolox_detector.py` import from `keypoint_detectors.rtmpose`. The import in
    `test_yolox_detector.py` is inside a test function.
  - `skellytracker/tests/test_run_batched.py` imports from
    `keypoint_detectors.rtmpose.wholebody.rtmpose_wholebody_detector`.
  - `skellytracker/core/detectors/keypoint_detectors/rtmpose/run_demo.py` and
    `skellytracker/examples/demo_bbox_policy.py` import from
    `keypoint_detectors.rtmpose.rtmpose_keypoint_detector`. These are the importers of the second shim.
  - `skellytracker/__main__.py` and `rtmpose/wholebody/run_demo.py` import `build_rtmpose_demo` from
    `rtmpose/run_demo.py`. They reach the second shim through that file. The usage lines of
    `rtmpose/wholebody/run_demo.py` name the module path `keypoint_detectors.rtmpose.wholebody.run_demo`.
- `rtmw_wholebody_detector.py` sets `KEYPOINT_DETECTOR_REGISTRY["rtmpose"] = RTMWWholebodyDetector`.
  `RTMWWholebodyDetectorConfig.detector_type` defaults to `"rtmpose"`. The body, hand and face
  detectors use the keys `rtmpose_body`, `rtmpose_hand` and `rtmpose_face`.
- `skellytracker/tests/sidecar/test_rtmw_sidecar.py` imports from the new path.

## Not repeated

- The key `"rtmpose"` names the RTMW whole-body detector. It does not name the RTMPose body, hand or
  face detectors. Do not rename it.
- Do not remove a shim while a file still imports its path.
- Do not import from the `keypoint_detectors.rtmpose` package at module level in
  `rtmw_wholebody_detector.py`. `rtmpose/__init__.py` imports the first shim, and the shim imports
  the RTMW module. A module-level import in the other direction makes an import cycle. The generic
  code that the detector needs lives in `core/detectors/processing/`, outside that package. See
  [0007](0007-generic-processing-package.md).

_Edited 2026-10-26 (this PR): link repair._

_Edited 2026-10-28 (this PR): link repair._

_Edited 2026-10-29 (this PR): link repair._

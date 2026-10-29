# 0003 — `tracked_points` are in native model output order

**Status:** absorbed into [`post/pose-schema.md#posetracked_points`](../../specs/model-sidecar/post/pose-schema.md#posetracked_points), 2026-10-25 (user; the absorption review).

## Decision

- A sidecar lists `pose.tracked_points` in the order of the model output. The i-th name is the i-th output
  index. This is the rule in [`pose.tracked_points`](../../specs/model-sidecar/post/pose-schema.md#posetracked_points) in the
  spec.
- The RTMW whole-body sidecar follows the rule. Its list is
  `skellytracker/core/detectors/shared/skeletons/coco133_tracked_points.yaml`. The order is:

  | Group | Indices |
  |---|---|
  | body | 0 to 22 |
  | face | 23 to 90 |
  | left hand | 91 to 111 |
  | right hand | 112 to 132 |

- The detector does not reorder the model output. The permutation array `_MODEL_TO_SCHEMA_PERM` is
  removed.
- The `connections` were ported without change. They use names, so the order of the list does not affect
  them.
- For RTMW whole-body, the array order of `Keypoints` changed. The mapping from name to value did not
  change. A parity test must compare by name. It must not compare by array position.

## Reason

- Before this change, the list of point names (`rtmpose_wholebody.yaml`) used the order body, right hand,
  left hand, face. The model outputs body, face, left hand, right hand. The detector closed the gap with
  `_MODEL_TO_SCHEMA_PERM`, a permutation that was hard-coded in Python.
- The spec requires the i-th name to be the i-th model output. The old list broke this rule. The sidecar
  must describe the model, not a re-ordered copy of it.
- `Keypoints` carries the names with the points. Consumers in the package look points up by name. A new
  order does not change what a reader finds under a name.
- With the native order, the permutation has no job. The decode step returns arrays in `tracked_points`
  order, and the detector uses them as they are.

## Evidence

- The old list had this header in `rtmpose_wholebody.yaml`: "Point order: body(0-22) + right_hand(23-43) +
  left_hand(44-64) + face(65-132)". The old detector indexed the decoded arrays with
  `_MODEL_TO_SCHEMA_PERM`, which concatenated `arange(0, 23)`, `arange(112, 133)`, `arange(91, 112)` and
  `arange(23, 91)`. #81 removed the YAML file and the permutation.
- Checked on 2026-10-22: no `.py` file in the repository contains `_MODEL_TO_SCHEMA_PERM`.
- `simcc_pose_decode()` in `skellytracker/core/detectors/processing/simcc_decode.py` returns `(K, 2)` and
  `(K,)` arrays in `pose.tracked_points` order. Its docstring says that the caller uses them against
  `tracked_points` with no permutation. `RTMWWholebodyDetector.postprocess()` in
  `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py` builds
  `Keypoints` from these arrays and the sidecar names.
- Consumers look points up by name with `Keypoints.index_of()`. Examples are
  `skellytracker/core/annotation/keypoint_annotator.py` and
  `skellytracker/core/detectors/object_detectors/keypoint_bbox/keypoint_bbox_detector.py`. No code under
  `skellytracker/` calls the positional `Keypoints.slice()`, except the tests.
- `skellytracker/tests/sidecar/test_rtmw_sidecar.py` checks the order in `test_tracked_points_native_model_order`
  (`nose` at 0, `right_heel` at 22, `face_0000` at 23, `face_0067` at 90, `left_hand_root` at 91,
  `left_hand_pinky_finger4` at 111, `right_hand_root` at 112, `right_hand_pinky_finger4` at 132).
- Golden fixtures came from the detector before the migration. They are the files
  `skellytracker/tests/sidecar/fixtures/golden/rtmw_wholebody_*_detect.json`, one for each of the three
  model sizes. The test compared by name with `np.allclose(atol=1e-3)`. The recorded result is an exact
  match with zero numeric difference for all three sizes. The result is in
  section "M4 — RTMW migration" of
  [`specs/sidecar-implementation-plan.md`](../../specs/sidecar-implementation-plan.md#m4--rtmw-migration).
- The implementation plan records that result. It does not record the machine or the execution
  provider. The results differ across machines and execution providers. Thus the parity tests now run on the CPU provider
  and compare at the precision of the model itself
  (`skellytracker/tests/sidecar/golden_parity.py`). A SimCC keypoint passes on each axis when it is
  within one SimCC bin of the fixture, or when the fixture bin has at least half the peak
  probability. The comparison is still by name.
- The RTMPose body, hand and face detectors had no permutation. Their point lists were ported without
  change. This entry changes nothing for them.

## Alternatives rejected

- Keep the schema order and the permutation in the detector. The spec rule forbids it, and the permutation
  is a hidden fact that no sidecar field describes.

## Not repeated

- Do not compare RTMW whole-body results by array position across this change. The positions changed. Use
  the names.
- Do not re-order `tracked_points` to group them by side or by use. The list must match the model output.
- Do not add a permutation to a detector. The sidecar must describe the model output as it is.

_Edited 2026-10-26 (this PR): link repair._

_Edited 2026-10-28 (this PR): link repair._

_Edited 2026-10-29 (this PR): link repair._

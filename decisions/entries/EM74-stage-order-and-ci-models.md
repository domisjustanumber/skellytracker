# EM74 — New code beside old code; the order N5, pre-release, P, Da, N6, Db, Dc; generated ONNX models in CI

**Status:** accepted, 2026-11-11 (user).

## Decision

1. **Beside, then delete.** The new code is built beside the old code. The old ONNX detectors, the
   old loader `core/sidecar/`, the old processing modules, `core/tracker/` and the old detector
   contract do not change until their replacements pass the gate. Then a deletion stage removes
   them. No new code imports them. No shared function gets a legacy switch
   ([ADR-AMJ8](AMJ8-replace-package-onnx-detectors.md)).
2. **Order.**
   1. L: layout, with the platform changes of [ADR-MSH0](MSH0-supported-platforms-v2.md).
   2. N1: the spec loader. N2: the spec processing. N3: the catalog and `detectors`.
   3. N4: standalone generic detectors.
   4. N5: `yolox-person` and `rtmw-wholebody133`, with the model gate at the detector level.
   5. The 2.0.0 pre-release, with the old and the new detectors side by side.
   6. P: the pipeline API.
   7. Da: delete the old YOLOX and RTMW.
   8. N6: the RTMPose replacements, with their pipeline.
   9. Db: delete the old RTMPose, the old loader and the old processing.
   10. Dc: delete the old run code (`core/tracker/`, the old configs and contract, `keypoint_bbox`,
       `precomputed`, the old MediaPipe classes, the old annotators and the demo builders).
   11. The 2.0.0 release. It ships with the old detectors and the old run code deleted, so
       freemocap moves one time (user, 2026-11-12).
3. **Standalone generic detectors.** The generic detectors of N4 have no old registry key, no
   `detector_type`, no old config base and no link to `DetectionStageConfig`. The batch path (batch
   at start, conversion, padding) is in the pipeline runtime of P. N4 and N5 write no Python
   pipeline builders. N4 does not change `core/tracker/`.
4. **Pre-release.** It comes after N5 and before any deletion. Its release note says that the old
   ONNX detectors, their keys and their `model_name` values go in a later release, and that freemocap
   must not move to 2.0.0 before it migrates.
5. **CI.** CI tests the ONNX path with tiny fixed-batch models that `onnx.helper` makes at run time,
   with a sidecar in a temporary root. CI runs no real model. Parity against the upstream reference
   output is a local gate (M10).
6. **MediaPipe at each stage.** MediaPipe works after each stage. Its tests keep their expected
   values, except in the one commit of the MediaPipe change and in Dc. Do not change the MediaPipe
   tests to close their detectors or to add teardown. On Windows with Python 3.11 or 3.12, two frames
   can get the same timestamp, and the tests can hang
   ([ADR-MSH0](MSH0-supported-platforms-v2.md)). Fix the timestamp fallback of the detectors, and
   make them close their landmarkers safely, also when the garbage collector frees them.
7. **Gates.** Dc checks that each built-in pipeline runs as a config. The MediaPipe built-in has no
   keypoint parity with the old builders ([ADR-8NVD](8NVD-pipeline-api-warnings-and-catalog.md)).

## Reason

- The old detectors call `load_sidecar` at import. A change of `core/sidecar/` or `processing/` in
  place breaks them or changes their output.
- Deletion has no deadline. The exporters need the new loader and the generic detectors to build the
  RTMPose replacements on a release
  ([ADR-6J8E](6J8E-exporters-run-released-skellytracker.md)), not the pipeline API. A pre-release
  after N5 unblocks them first.
- Da after P keeps a working YOLOX and YOLOX+RTMW pipeline at each step.
- Python builders on the old `Tracker` would need a config union that does not exist, and P would
  delete them.
- The new ONNX files are untracked, so CI cannot run them. Generated models check the plumbing on
  three operating systems with no binary file in git.
- The MediaPipe tests show the timestamp defect when it comes back.

## Alternatives rejected

- **Change the old code in place.** It breaks the old detectors before their replacements exist.
- **Python builders as a bridge before P.** Throw-away work on the old run code.
- **Da before P, and the pre-release after Da.** No YOLOX pipeline between Da and P, and the
  exporters wait longer.
- **Real tiny models in CI now.** They need the Hugging Face repo and a trimmed upstream reference.
  This is later work.

## Open work

See [open-work.md](../open-work.md).

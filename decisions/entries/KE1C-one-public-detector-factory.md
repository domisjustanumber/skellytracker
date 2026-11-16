# KE1C — One public detector factory that also makes charuco and aruco; a public calibration module

**Status:** absorbed into [`factory.py`](../../skellytracker/core/detectors/factory.py), [`calibration.py`](../../skellytracker/core/detectors/calibration.py), [`skellytracker/AGENTS.md#layout`](../../skellytracker/AGENTS.md#layout), 2026-11-16 (user, questions M1, F6 and B1 of 2026-11-16; PR: pending).

## Decision

1. **One factory.** `skellytracker.core.detectors.create_detector(key, **options)` is the one public
   factory of the `detectors` entry point. It uses the `category` of the catalog entry. For an
   `onnx` key it calls `create_detector` of `core/detectors/generic/` with the same arguments, and
   it returns the same generic detector. For `charuco@skellytracker` and `aruco@skellytracker` it
   makes the calibration class, with its CPU session.
2. **Options.** The option of charuco is `board`: a `CharucoBoardDefinition` or a mapping of its
   fields. The options of aruco are `aruco_ids` and `aruco_dictionary_enum`. The factory checks
   them with the config of the class, so a wrong value gives the Pydantic error with the field
   name. An other option name raises `TypeError`.
3. **Result.** The result of a calibration key has `detect(image)` and `close()`. The charuco
   result has `board`, the `CharucoBoardDefinition` of the detector. `detect` returns the
   `Keypoints` of today (`names`, `xyz`, `visibility`), until stage 2.4 of the implementation
   plan defines the result of the plain classes. The charuco names are the corner names of the
   board, in order, then the marker corner names. A point that is not found is NaN with the
   visibility 0. The factory keeps its signature and its options at stage 2.4.
4. **MediaPipe.** A `mediapipe` key raises `DetectorUnavailableError`. The message names the
   pipeline node `mediapipe_tasks`. No text gives a standalone MediaPipe detector of the
   `detectors` entry point.
5. **Errors.** An unknown key raises `DetectorNotFoundError`. An entry that is not available
   raises `DetectorUnavailableError` with the reason.
6. **Lazy imports.** The factory imports each detector module in its function body. A plain
   `import skellytracker.core.detectors` loads no generic detector, no calibration detector, no
   ONNX Runtime and no MediaPipe. A test in a subprocess checks it.
7. **The public surface.** A caller imports from the public surface only:
   `skellytracker.core.detectors` and `skellytracker.core.detectors.calibration`. It imports no
   detector class, no config class of a detector, no session and no module of
   `calibration_detectors`. The calibration module is one public module with plain re-exports of
   the calibration names that are not detectors: `CharucoBoardDefinition`, the board selector,
   `compute_board_pose`, `transform_to_camera_coordinates`, `to_anipose_camera_row`, the charuco
   annotator, the board tags and `CHARUCO_BOARD_MAPPING`. The entry point does not import this
   module.
8. **The board model is public data.** `CharucoBoardDefinition` is a part of the public surface. It
   stays a Pydantic model that is not frozen, with `extra="forbid"`. freemocap uses it as a field
   type, changes its fields, and copies, compares and pickles it. The rule of the user is about
   the detector classes and the internal package path, not about the board model.
9. **The port.** The board selector, the board tags, the point names, the positions and the
   connections of the board model, and `CHARUCO_BOARD_MAPPING` with its YAML file come from the
   ref `sfn26` of freemocap/skellytracker, commit `2d356a6c41f831484251677050fafb2576193060`, to
   `calibration_detectors/charuco/`. Only these parts come. There is no merge of that branch and
   no shim at an old path.

This adds to [ADR-0XW9](0XW9-entry-points-layout-guard-test-and-session-code.md) item 4. The text
"`detectors` lists them" becomes "`detectors` lists them, and its factory `create_detector` makes
them". The other text of that item stays.

## Reason

- The user decided on 2026-11-16: "freemocap must use the new API surface and must not call any
  calibration class directly" (question M1), the scope of the port (question F6) and its source
  (question B1).
- freemocap at its ref `sfn26` uses the board model as data in its configs and its files. A second
  board type for the caller would give two types for one thing.
- The implementation plan says that charuco runs through `detectors`. Before this entry,
  `detectors` listed charuco and aruco, but a caller made them from the class, a config and an old
  session.
- One factory keeps the caller unchanged when stage 2.4 changes the calibration classes to plain
  classes and deletes the old session code.
- A module with plain re-exports obeys the freeze rules with no special code. A type checker and
  PyInstaller read its names. The entry point stays lazy, because it does not import the module.

## Consequences

- The factory uses the old `CpuSession` and the old detector contract until stage 2.4.
- `create_detector` takes `**options`, so its signature does not name the arguments of the generic
  factory. The module docstring gives the options of each calibration key.

## Alternatives rejected

- **The caller imports the calibration class.** Then freemocap changes again at stage 2.4, and it
  imports the old session code.
- **A separate calibration factory.** The caller then needs the category of a key before it can
  make a detector. The catalog already holds the category.
- **Wait for stage 2.4.** freemocap then migrates to the old classes first, or it waits for the
  deletion stage.
- **Helper names on `skellytracker.core.detectors` through a module `__getattr__`.** It needs
  special code to stay lazy, and a type checker does not read the names.

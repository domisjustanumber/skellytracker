# 0XW9 — Entry points and layout; the eps guard test and the home of new session code

**Status:** accepted, 2026-11-12 (user).

## Decision

This entry supersedes [ADR-AQR4](AQR4-detectors-and-pipelines-entry-points.md) in full. It keeps
the item numbers of AQR4. Items 1 and 3 change: item 1 gives the home of new session code, and item 3
keeps one guard test. The other items restate AQR4.

1. **Entry points.** The public API has two entry points. `skellytracker.core.detectors` lists the
   models. `skellytracker.core.pipelines` lists, loads, exports, validates and starts pipelines
   ([ADR-V7GZ](V7GZ-pipeline-api-device-and-vram-reserve.md)). There is no `trackers` entry point.
   New session code is in `core/eps/`, with `eps.build_session()`. The old `core/sessions/` code does
   not change until stage 2.4 (Delete the old run code), which deletes it with `core/tracker/`
   ([ADR-D8DH](D8DH-sessions-errors-and-the-ready-rule.md) item 13).
2. **Categories.** Each `detectors` entry has the category `onnx`, `mediapipe` or `calibration`.
   `keypoint_bbox` and `precomputed` are not models
   ([ADR-7NY2](7NY2-pipeline-form-graph-and-nodes.md)).
3. **One `core` package.** The modules of the hardware and EP track (`system/`, `metrics/` and
   `eps/`) go under `core/`. `core/__init__.py` stays eager. The import isolation rules of that track
   are withdrawn, with one exception: a guard test checks that `import skellytracker.core.eps` loads
   no `onnxruntime`. It tests the lazy import only ([ADR-D8DH](D8DH-sessions-errors-and-the-ready-rule.md)
   item 14). `system` and `metrics` can load `core` code, and `core` and `eps` can have an edge. The
   new pipeline runtime calls `eps.build_session()` directly. The freeze rule stays: no import by a
   computed name, and a lazy import is a plain statement in a function body.
4. **Calibration.** charuco and aruco move to `core/detectors/calibration_detectors/`. They stay
   outside pipelines. When the old run code is deleted, they become plain classes with their own
   frozen config dataclass and `detect(image)`, and they subclass no base. `detectors` lists them.
5. **MediaPipe assets.** `mediapipe_model_manager.py`, the point-name YAML files, the connections and
   the canonical mappings stay at `core/detectors/keypoint_detectors/mediapipe/`. The old MediaPipe
   detector classes are deleted with the old run code.
6. **User models folder.** The user root is `platformdirs.user_data_dir("skellytracker",
   appauthor=False)` + `/models`, with the layout of `core/model_zoo/`. `platformdirs` becomes a
   direct dependency. skellytracker keeps no settings file. `list_detectors`, `list_pipelines`,
   `load_pipeline` and `start_pipeline` take `user_root`. The order is the argument, then
   `SKELLYTRACKER_USER_ROOT`, then the default. An application, for example freemocap, keeps the
   choice of its UI and passes it.
7. **Old import paths.** No shims. Each move updates the README, the examples, the demos and the
   tests.

## Reason

- The user decided both changes on 2026-11-12, with AQR4 items 1 and 3 quoted in the questions, and
  agreed with the recommendations: keep the guard test as a test of the lazy import, and put new
  session code in `core/eps/` with the deletion of `core/sessions/` in stage 2.4.
- No stage deleted `core/sessions/` before. It would stay as dead code after the old detectors go.
- The lazy import of `onnxruntime` keeps `import skellytracker.core` fast. A test keeps it lazy.
- AQR4 keeps the reasons of items 2 and 4 to 7.

## Alternatives rejected

- **Drop the guard test with the other isolation rules.** A later eager import of `onnxruntime`
  then slows each import of `core`, and no test finds it.
- **Keep `core/sessions/` for the new code.** It holds the old detector contract that the deletion
  stages remove.

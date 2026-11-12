# AQR4 — Two entry points `detectors` and `pipelines`; the hw-and-ep modules go under an eager `core`; calibration stays outside pipelines

**Status:** superseded by [0XW9](0XW9-entry-points-layout-guard-test-and-session-code.md), 2026-11-12 (user; PR: pending).

## Decision

1. **Entry points.** The public API has two entry points. `skellytracker.core.detectors` lists the
   models. `skellytracker.core.pipelines` lists, loads, exports, validates and starts pipelines
   ([ADR-8NVD](8NVD-pipeline-api-warnings-and-catalog.md)). There is no `trackers` entry point.
   `sessions` keeps its meaning: the inference sessions of `core/sessions/`.
2. **Categories.** Each `detectors` entry has the category `onnx`, `mediapipe` or `calibration`.
   `keypoint_bbox` and `precomputed` are not models
   ([ADR-7NY2](7NY2-pipeline-form-graph-and-nodes.md)).
3. **One `core` package.** The modules of the hardware and EP track (`system/`, `metrics/` and
   `eps/`) go under `core/`. `core/__init__.py` stays eager. The import isolation rules of that track
   are withdrawn: `system` and `metrics` load no `core` code, `eps` loads no `onnxruntime`, cv2,
   `core` or `metrics`, and `core` and `eps` have no edge. The new pipeline runtime calls
   `eps.build_session()` directly. The freeze rule stays: no import by a computed name, and a lazy
   import is a plain statement in a function body.
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

- The user wants one package tree: "Adding new modules to core is fine, things do not need to be
  separate, as this is already going to be a big overhaul."
- `import skellytracker.core` loads cv2, but no optional extra (Evidence). So an eager `core` does
  not load ONNX Runtime before the EP setup of `eps`. The availability checks of
  [ADR-8NVD](8NVD-pipeline-api-warnings-and-catalog.md) report a missing extra at startup and at
  load. An eager import cannot do that, because it does not import the extras.
- The runtime must build the session for a given EP. A session factory that each caller passes in
  pushes the EP work to each caller.
- Calibration has no crops, no previous-frame input and no batch. A pipeline adds nothing to it.
- A cache folder can be deleted, and user models cannot be downloaded again. `AppData\Local` does
  not sync to OneDrive. One owner of settings is enough, and tests and frozen apps need no file.

## Evidence

Measured on 2026-11-11 in the project environment (Python 3.12.13, MediaPipe 0.10.33): `import
skellytracker.core` takes about 0.55 s and loads cv2, but not `mediapipe`, `onnxruntime` or `onnx`.
Code facts (graphify 0.9.100): only the three MediaPipe detector modules import `mediapipe`; only
`core/sessions/onnx_session.py` and `core/sessions/ort_session_utils.py` import `onnxruntime`.

## Alternatives rejected

- **A lazy `core/__init__.py` with a module `__getattr__`.** It keeps the isolation rules, but the
  user prefers one package tree, and it does not report a missing extra either.
- **Top-level `system/` and `metrics/` packages.** Withdrawn by the user for one `core` tree.
- **A calibration node type.** Calibration needs nothing that a pipeline gives.
- **A fixed `~/.skellytracker/models`.** It is a hidden folder on Linux and macOS and is not the OS
  convention.
- **A settings file with `set_user_root()`.** Two owners of one setting.

## Open work

See [open-work.md](../open-work.md).

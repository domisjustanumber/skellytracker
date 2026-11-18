# skellytracker

The tracking backend for freemocap. Collects different pose estimation tools behind a consistent API built around a **Tracker → Session → Detector** pipeline. Supports inference on images, webcams, and videos.

## Installation

skellytracker needs Python 3.13.18. It supports Windows on x86_64, Linux on x86_64 and macOS on
Apple Silicon (arm64). macOS on Intel (x86_64) is not supported.

The base package includes ONNX Runtime 1.30 for the CPU and the OpenCV trackers (ArUco, ChArUco):

```bash
pip install skellytracker

# Or with uv
uv add skellytracker
```

Add an extra to enable more trackers:

| Extra | What it adds |
|---|---|
| `mediapipe` | The MediaPipe trackers (pose, hands, face) |

```bash
pip install "skellytracker[mediapipe]"
uv add "skellytracker[mediapipe]"
```

The ONNX trackers run on the CPU. On macOS, they can also run on CoreML. A plain install gives the
CPU core of ONNX Runtime. A GPU EP for an NVIDIA GPU is a plugin EP pack:
`skellytracker-eps install` puts it in the EP store of the user. On Windows, the DirectML EP is a
part of ONNX Runtime. It is in a field test and needs an opt-in. The AMD GPU EPs (`migraphx` and
`amdgpu`) are in a field test too. The [GPU setup guide](GPU_SETUP_GUIDE.md) gives the procedure.

## Quick start

### MediaPipe (pose, hands, face)

```python
import cv2
from skellytracker.core import Tracker, TrackerConfig, DetectionStageConfig, TrackerState
from skellytracker.core.detectors.keypoint_detectors.mediapipe import (
    MediaPipeSession, MediaPipeSessionConfig,
    MediapipePoseDetectorConfig,
    MediapipeHandDetectorConfig,
    MediapipeFaceDetectorConfig,
)

session = MediaPipeSession.create(MediaPipeSessionConfig())
config = TrackerConfig(stages=[
    DetectionStageConfig(name="body",  keypoint_detectors=[MediapipePoseDetectorConfig()]),
    DetectionStageConfig(name="hands", keypoint_detectors=[MediapipeHandDetectorConfig()]),
    DetectionStageConfig(name="face",  keypoint_detectors=[MediapipeFaceDetectorConfig()]),
])
tracker = Tracker.create(config, sessions={"mediapipe": session})
state = TrackerState()

image = cv2.imread("image.jpg")
observation, state = tracker.process_image(image, frame_number=0, state=state)

body_keypoints = observation.stages["body"].keypoints   # Keypoints with .xyz (N,3), .names, .visibility
tracker.close()
```

### RTMPose + YOLOX (ONNX-based)

```python
import cv2
from skellytracker.core import Tracker, TrackerConfig, DetectionStageConfig, TrackerState
from skellytracker.core.detectors.object_detectors.yolox import YoloxPersonDetectorConfig
from skellytracker.core.detectors.keypoint_detectors.rtmpose import RTMPoseDetectorConfig
from skellytracker.core.sessions.onnx_session import OnnxSession, OnnxSessionConfig
from skellytracker.core.detectors.object_detectors.yolox import YoloxPersonDetector
from skellytracker.core.detectors.keypoint_detectors.rtmpose import RTMPoseKeypointDetector

session = OnnxSession.create(OnnxSessionConfig(
    batch_size=1,
    models=[
        YoloxPersonDetector.model_spec("yolox-m"),
        RTMPoseKeypointDetector.model_spec("rtmw-x-l_256x192"),
    ],
))
config = TrackerConfig(stages=[
    DetectionStageConfig(
        name="body",
        object_detector=YoloxPersonDetectorConfig(),
        keypoint_detectors=[RTMPoseDetectorConfig()],
    )
])
tracker = Tracker.create(config, sessions={"onnx": session})
state = TrackerState()

image = cv2.imread("image.jpg")
observation, state = tracker.process_image(image, frame_number=0, state=state)

keypoints = observation.stages["body"].keypoints  # 133 whole-body keypoints
tracker.close()
```

### Webcam demo

`skellytracker` installs a console script, so once it's on your environment you can run demos with `uv run skellytracker` (or plain `skellytracker` / `python -m skellytracker` if you've activated the venv yourself).

```bash
# Default demo (MediaPipe holistic: pose + hands + face)
uv run skellytracker

# Pick a different tracker
uv run skellytracker --tracker rtmpose
uv run skellytracker --tracker aruco
uv run skellytracker --tracker charuco

# Use a non-default camera
uv run skellytracker --tracker mediapipe --camera 1

# List available trackers
uv run skellytracker --list
```

`--tracker` chooses among `mediapipe`, `rtmpose`, `aruco`, and `charuco`. Each demo opens a live OpenCV window; press `q` (or close the window) to quit.

The option `--pipeline` runs a pipeline of the pipeline API on the camera, in place of `--tracker`. Its value is a key of the pipeline catalog or a pipeline file. Press `q` or `Esc` to stop. The options `--ep <key>`, `--ep-option <name>=<value>` and `--device <key>` select the execution provider. With no `--ep`, the demo uses the recommended execution provider and prints it.

```bash
# Run a built-in pipeline on the camera
uv run skellytracker --pipeline mediapipe-holistic-tasks@skellytracker
uv run skellytracker --pipeline yolox-rtmw-wholebody@skellytracker --ep cpu

# List the node types of a pipeline file
uv run skellytracker nodes
uv run skellytracker nodes --json

# Run the load checks of a pipeline file or a pipeline key, and print the warnings
uv run skellytracker validate my.pipeline.yaml

# Run a pipeline on the images of a COCO file, and write the timing file and the tap files
uv run skellytracker run --pipeline yolox-rtmw-wholebody@skellytracker --coco annotations.json --images images/ --out out/ --ep cpu
```

`run` writes `timing.jsonl` in the `--out` folder. The option `--taps <dir>` gives the tap folder. The exit code is 0 for a good run, 2 for a usage error or a pipeline that is not valid, 3 when the execution provider is not available, 4 when a session was not created and 5 when the GPU memory is exhausted.

For tracker-specific options beyond `--camera` (model choice, execution provider, which body parts to detect, board geometry, etc.), run that tracker's `run_demo` module directly with `--help`:

```bash
# MediaPipe: toggle pose/hands/face
uv run python -m skellytracker.core.detectors.keypoint_detectors.mediapipe.run_demo --no-hands --no-face

# RTMPose: choose model/provider, or skip the YOLOX person detector
uv run python -m skellytracker.core.detectors.keypoint_detectors.rtmpose.run_demo --model rtmw-x-l_384x288 --provider cpu
uv run python -m skellytracker.core.detectors.keypoint_detectors.rtmpose.run_demo --no-detector

# Aruco: choose which marker IDs to look for
uv run python -m skellytracker.core.detectors.calibration_detectors.aruco.run_demo --ids 0 1 2 3

# Charuco: set board geometry
uv run python -m skellytracker.core.detectors.calibration_detectors.charuco.run_demo --squares-x 7 --squares-y 5 --square-mm 58
```

## API overview

- **`Tracker`** — top-level orchestrator. Built from a `TrackerConfig` and a `sessions` dict via `Tracker.create()`. Call `process_image(image, frame_number, state)` per frame; it returns `(Observation, TrackerState)`. Call `close()` when done.
- **`Session`** — manages computational resources (model weights, device context) shared across detectors. One session per backend (e.g. one `MediaPipeSession`, one `OnnxSession`).
- **`DetectionStage`** — one stage in the pipeline, configured via `DetectionStageConfig`. Each stage has an optional object detector (to crop person bounding boxes) and one or more keypoint detectors.
- **`Observation`** — per-frame result. `observation.stages["name"].keypoints` returns a `Keypoints` object with `.xyz` `(N, 3)`, `.names`, and `.visibility` arrays.
- **`TrackerState`** — temporal state (bounding box history, smoothing buffers) passed into and returned from each `process_image` call.

### Hardware and EP API

These modules are for the new code. The trackers above do not use them.

- **`skellytracker.core.system`** gives facts that do not change while the application runs:
  `probe_host()` (OS, CPU, memory, GPUs), `probe_runtime()`, `probe_environment()` and
  `probe_loaded_libraries()`. The probes do not raise for missing hardware.
- **`skellytracker.core.metrics`** gives live system values: `LiveSampler.sample(pids)` (CPU, memory,
  processes, GPUs) and `free_vram(device)`.
- **`skellytracker.core.eps`** gives the execution providers: `recommend(form)`, `status()`,
  `install()`, `verify()`, `run_devices()` and `build_session()`. `build_session()` returns the
  session and a `SessionReport`. It never runs a session on an other EP than the requested EP.
- **`skellytracker.core.errors`** has `EpRequestError`, `EpUnavailableError`, `SessionCreationError`
  and `VRAMExhaustionError`.

To freeze an application with PyInstaller, you need no hook of your own: the package has a
PyInstaller hook that collects its YAML files.

## Extending the API

Implement a new keypoint detector by subclassing `KeypointDetector` and registering it:

```python
from skellytracker.core.detectors import KeypointDetector, KEYPOINT_DETECTOR_REGISTRY

class MyDetector(KeypointDetector):
    ...

KEYPOINT_DETECTOR_REGISTRY["my_detector"] = MyDetector
```

## Contributing

Pull requests are welcome. [`AGENTS.md`](AGENTS.md) gives the full rules for human and AI contributors.
The [sidecar spec](specs/model-sidecar/README.md) gives the contract of the YAML sidecar that an ONNX detector reads.

1. Fork the repo. Create your branch from `development`.
2. Install the dev tools: `uv sync --all-extras`. Then run `uv run pre-commit install` once.
3. If you add a tracker, add tests under `skellytracker/tests/`.
4. Run the fast tests: `uv run pytest -m "not video"`. To include the slow video tests, run `uv run pytest`.
5. Lint: `uv run ruff check skellytracker/ tools/`
6. Open a pull request against `development`.

CI runs the lint and the fast tests on each push, and on each PR into `main` or `development`. It runs all tests on each PR into `main`.

---

# GPU setup

The [GPU setup guide](GPU_SETUP_GUIDE.md) gives the EP packs for an NVIDIA GPU and the command `skellytracker-eps`.

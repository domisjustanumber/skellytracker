# skellytracker

The tracking backend for freemocap. Collects different pose estimation tools behind a consistent API built around a **Tracker → Session → Detector** pipeline. Supports inference on images, webcams, and videos.

## Installation

The base package includes ONNX Runtime 1.31 for the CPU and the OpenCV trackers (ArUco, ChArUco):

```bash
pip install skellytracker

# Or with uv
uv add skellytracker
```

Add an extra to enable more trackers:

| Extra | What it adds |
|---|---|
| `mediapipe` | The MediaPipe trackers (pose, hands, face) |
| `onnx` | The `onnx` package. The RTMPose and YOLOX trackers need it to change the ONNX graph. |

```bash
pip install "skellytracker[mediapipe,onnx]"
uv add "skellytracker[mediapipe,onnx]"
```

The ONNX trackers run on the CPU. On macOS, they can also run on CoreML. This version has no GPU
support. The [GPU setup guide](GPU_SETUP_GUIDE.md) gives the status.

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

For tracker-specific options beyond `--camera` (model choice, execution provider, which body parts to detect, board geometry, etc.), run that tracker's `run_demo` module directly with `--help`:

```bash
# MediaPipe: toggle pose/hands/face
uv run python -m skellytracker.core.detectors.keypoint_detectors.mediapipe.run_demo --no-hands --no-face

# RTMPose: choose model/provider, or skip the YOLOX person detector
uv run python -m skellytracker.core.detectors.keypoint_detectors.rtmpose.run_demo --model rtmw-x-l_384x288 --provider cpu
uv run python -m skellytracker.core.detectors.keypoint_detectors.rtmpose.run_demo --no-detector

# Aruco: choose which marker IDs to look for
uv run python -m skellytracker.core.detectors.keypoint_detectors.aruco.run_demo --ids 0 1 2 3

# Charuco: set board geometry
uv run python -m skellytracker.core.detectors.keypoint_detectors.charuco.run_demo --squares-x 7 --squares-y 5 --square-mm 58
```

## API overview

- **`Tracker`** — top-level orchestrator. Built from a `TrackerConfig` and a `sessions` dict via `Tracker.create()`. Call `process_image(image, frame_number, state)` per frame; it returns `(Observation, TrackerState)`. Call `close()` when done.
- **`Session`** — manages computational resources (model weights, device context) shared across detectors. One session per backend (e.g. one `MediaPipeSession`, one `OnnxSession`).
- **`DetectionStage`** — one stage in the pipeline, configured via `DetectionStageConfig`. Each stage has an optional object detector (to crop person bounding boxes) and one or more keypoint detectors.
- **`Observation`** — per-frame result. `observation.stages["name"].keypoints` returns a `Keypoints` object with `.xyz` `(N, 3)`, `.names`, and `.visibility` arrays.
- **`TrackerState`** — temporal state (bounding box history, smoothing buffers) passed into and returned from each `process_image` call.

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

For help configuring your GPU for ONNX-based trackers (RTMPose, YOLOX), see the [GPU_SETUP_GUIDE](GPU_SETUP_GUIDE.md).

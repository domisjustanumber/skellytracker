# skellytracker

The tracking backend for freemocap. Collects different pose estimation tools and aggregates them using a consistent API. Can run pose estimation on images, webcams, and videos.

## Run skelly_tracker

Installation: `pip install skellytracker`
Then it can be run with `skellytracker`.

Running the basic `skellytracker` will open the first webcam port on your computer and run pose estimaiton in realtime with mediapipe holistic as a tracker. You can specify the tracker with `skellytracker TRACKER_NAME`, where `TRACKER_NAME` is the name of an available tracker. To view the names of all available trackers, see `RUN_ME.py`.

It will take some time to initialize the tracker the first time you run it, as it will likely need to download the model.

## Using skellytracker in your project

To use skellytracker in your project, import a tracker like `from skellytracker import YOLOPoseTracker`, then instantiate it with your desired parameters like `tracker = YOLOPoseTracker(model_size="medium")`, and then use `tracker.process_image(frame)` or `tracker.process_video(video_filepath)`. Processing image by image will let you access each individual annotated frame with `tracker.annotated_image`, and you can optionally record the data with `tracker.recorder.record()`. Access recorded data with `tracker.recorder.process_tracked_objects()`. The running, recording, and processing are done separately to give control over the amount of processing done at each step in the pipeline. Processing an entire video allows you to save the annotated frames as a video, and optionally saves and returns the data as a numpy array. Each tracker has an associated `ModelInfo` class to access model attributes.

Skellytracker is still under development, so version updates may make breaking changes to the API. Please report any issues and pull requests to the [skellytracker repo](https://github.com/freemocap/skellytracker).

### Extending the API
To extend the API, import the `BaseTracker` and `BaseRecorder` abstract base classes from skellytracker. Then create a new tracker and recorder inheriting from the base classes and implement all of the abstract methods.

## Contributing

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

Pull requests are the best way to propose changes to the codebase (we
use [Github Flow](https://docs.github.com/en/get-started/quickstart/github-flow)). We actively welcome your pull
requests:

1. Fork the repo and create your branch from `main`.
2. Download the development dependencies with `pip install -e '.[dev]'`.
2. If you've added code that should be tested (including any tracker), add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes by running `pytest skellytracker/tests`.
5. Make sure your code lints.
6. Make that pull request!

---

# GPU setup

For GPU-accelerated RTMPose, see the [GPU_SETUP_GUIDE](GPU_SETUP_GUIDE.md). In a dev checkout, run `skellytracker-gpus` to list detected GPUs, compare optimal vs installed execution providers, and install the matching extra with `--install`.

## Hardware Precision Compatibility

Use this table when matching model artifact precision to execution provider and hardware. Model sidecars may list any available precision artifacts, but a session should only start when the selected model precision is compatible with the requested EP and detected hardware.

| Vendor | Hardware Generation | Best Optimised Format | Formats NOT Supported |
| ------ | ------------------- | --------------------- | --------------------- |
| NVIDIA | GeForce RTX 20-Series (Turing) | FP16, INT8 | FP8, FP4 (fails/no hardware instructions) |
| NVIDIA | GeForce RTX 30-Series (Ampere) | FP16, INT8 (supports 2:4 sparsity) | FP8, FP4 (fails/no hardware instructions) |
| NVIDIA | GeForce RTX 40-Series (Ada Lovelace) | FP8 (E4M3/E5M2), FP16, INT8 | FP4 (fails/no hardware instructions) |
| NVIDIA | GeForce RTX 50-Series (Blackwell) | FP4 (NVFP4/MXFP4), FP8, FP16 | None (fully downward compatible) |
| NVIDIA | Jetson Orin Series | INT8, FP16 | FP8, FP4 |
| Intel | Core CPUs (Gen 6 to 11) | FP32, INT8 (via AVX-512 VNNI) | FP16 (software emulation penalty), FP8, FP4 |
| Intel | Core CPUs (Gen 12+ / Alder, Raptor, Arrow Lake) | INT8 (via AVX-VNNI), FP32 | FP8, FP4 |
| Intel | Iris Xe & Arc GPUs (Alchemist / Battlemage) | FP16, INT8 (via XMX) | FP4, FP8 |
| Intel | Core Ultra NPUs (Meteor Lake / Lunar Lake) | INT8, FP16 | FP32 (NPU bypasses; forces high latency CPU fallback), FP4 |
| AMD | Ryzen CPUs (Non-AI) | FP32, INT8 (via AVX-512) | FP16 (heavy execution penalty on older Zen), FP4 |
| AMD | Ryzen AI NPUs (XDNA 1 / XDNA 2) | INT8, Block-FP16 (BFloat16 variant) | FP32 (unsupported natively on the NPU block), FP4 |
| AMD | Radeon RX GPUs (RDNA 2 / RDNA 3 / RDNA 3.5) | FP16, INT8 (WMMA) | FP8 (no native hardware processing), FP4 |
| AMD | Radeon RX GPUs (RDNA 4) | FP8, FP16, INT8 | FP4 |
| Apple | Apple Silicon (M1 / M2 / M3 / M4) | FP16 (ANE native), INT8 | FP8, FP4 (Neural Engine pipeline fails/rejects graph) |
| Qualcomm | Snapdragon (8 Gen Series, Snapdragon X) | INT8 (Hexagon native), FP16 | FP32 (forces QNN to bypass NPU to slow CPU runtime), FP4 |

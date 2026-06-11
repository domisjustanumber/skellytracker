# SkellyTracker GPU Setup Guide (RTMPose)

This guide covers GPU-accelerated RTMPose inference in skellytracker. RTMPose uses **ONNX Runtime execution providers** (CUDA, TensorRT, DirectML, CoreML, CPU) — not rtmlib device strings.

## Quick start: `skellytracker-gpus`

After installing skellytracker in a clone of this repo (or any checkout with `pyproject.toml` at the project root), run:

```bash
uv sync --extra rtmpose-nvidia   # or your chosen extra — see below
skellytracker-gpus
```

The CLI always prints:

1. Detected physical GPUs (OS-native enumeration — no CUDA required)
2. **Optimal EP** — best execution provider for your hardware (may not be installed yet)
3. **Installed best EP** — best provider available in your current ONNX Runtime install

When optimal and installed best differ, it also prints an install hint. To install the pyproject extra for your GPU:

```bash
skellytracker-gpus --install
```

`--install` runs `uv sync --extra <name>` in the project root. Use `--dry-run` to print the command without executing it, or `--extra rtmpose-nvidia` to override auto-detection.

**Requirements:** `uv` on `PATH` for `--install`. The CLI does not add new Python dependencies.

---

## Which extra should I install?

| Your hardware | OS | Recommended extra | Execution provider (when wired) |
|---------------|-----|-------------------|--------------------------------|
| NVIDIA (GTX, Quadro, etc.) | Windows / Linux | `rtmpose-nvidia` | `cuda` |
| NVIDIA RTX 30 / 40 / 50 | Windows / Linux | `rtmpose-trt-rtx` | `trt-trx` (fastest; first run compiles engines) |
| AMD or Intel GPU | Windows | `rtmpose-directml` | `directml` |
| Apple Silicon | macOS | `rtmpose` | `coreml` (runtime wiring landing in a follow-up release) |
| No GPU / fallback | Any | `rtmpose` | `cpu` |

Classic TensorRT (`rtmpose-trt`) is available but **never auto-selected** — long compile times on older GPUs. Install manually only if you need it:

```bash
uv sync --extra rtmpose-trt
```

### Install commands

```bash
# NVIDIA CUDA (bundled CUDA/cuDNN pip packages — no system CUDA Toolkit required on most setups)
pip install "skellytracker[rtmpose-nvidia]"
# or: uv sync --extra rtmpose-nvidia

# NVIDIA RTX with TensorRT RTX EP (recommended on RTX 30+)
pip install "skellytracker[rtmpose-trt-rtx]"

# Windows AMD / Intel / any DirectX 12 GPU
pip install "skellytracker[rtmpose-directml]"

# macOS / CPU fallback
pip install "skellytracker[rtmpose]"

# Mediapipe + NVIDIA
pip install "skellytracker[mediapipe,rtmpose-nvidia]"
```

Only **one** RTMPose ONNX Runtime wheel can be installed at a time (`onnxruntime`, `onnxruntime-gpu`, `onnxruntime-directml` conflict). Use `uv sync --extra <target>` to switch — it prunes the previous extra automatically.

---

## Python introspection API

For Freemocap or other callers, use `skellytracker.utilities.gpu_utils`:

```python
import skellytracker.utilities.gpu_utils as gpu

# Hardware (no ORT import)
gpus = gpu.list_installed_gpus()
for g in gpus:
    print(g.id, g.name, g.vendor, g.vram_bytes)

# Best EP for this hardware (may not be installed)
optimal = gpu.recommend_optimal_execution_provider(gpus)

# Installed ORT packages + dual recommendation flags
info = gpu.list_execution_providers()
print(info.optimal_provider_id)              # hardware-optimal
print(info.recommended_provider_id)          # installed-best (auto chain)
print(info.install_recommended_provider_id)  # extra install hint, or None

# pyproject extra for --install
extra = gpu.recommend_rtmpose_extra(gpus)    # e.g. "rtmpose-trt-rtx"

# Model catalog (for settings UI)
detectors = gpu.list_detection_models()
poses = gpu.list_pose_models()               # broad list — filter rtmw-* for RTMPose
```

`list_execution_providers()` may load CUDA DLLs when a CUDA-family EP is installed — cache results at app startup, don't call every UI frame.

**Two EP signals (important):**

| Signal | Meaning |
|--------|---------|
| `recommended` / `recommended_provider_id` | Best EP **currently installed** — used for session auto mode |
| `optimal` / `optimal_provider_id` | Best EP for your **GPU hardware** — used for install guidance |

They can differ (e.g. GTX 1080 + classic TensorRT installed → recommended `trt`, optimal `cuda`).

---

## RTMPose configuration

`RTMPoseDetectorConfig` defaults to **auto** execution provider selection:

```python
from skellytracker.trackers.rtmpose_tracker.rtmpose_detector import (
    RTMPoseDetectorConfig,
    RTMPoseDetector,
)

# Auto: picks installed-best EP at session create
detector = RTMPoseDetector.create(RTMPoseDetectorConfig())

# Legacy explicit device alias still works
detector = RTMPoseDetector.create(RTMPoseDetectorConfig(device="cuda"))

# Force a specific EP
detector = RTMPoseDetector.create(
    RTMPoseDetectorConfig(execution_provider="trt-trx")
)

# Optional wholebody model overrides (validated against model catalog)
detector = RTMPoseDetector.create(
    RTMPoseDetectorConfig(
        mode="performance",
        detector_model="yolox-tiny",
        pose_model="rtmw-x-l_256x192",
    )
)
```

`pose_model` accepts **`rtmw-*` ids only** for RTMPose wholebody. Filter `list_pose_models()` client-side:

```python
rtmw_choices = [m for m in gpu.list_pose_models() if m.id.startswith("rtmw-")]
```

Direct `RTMPoseSession.create()` without config also uses auto EP (`execution_provider=None`) — no longer forces TensorRT by default.

---

## Option 1: NVIDIA GPU (CUDA / TensorRT)

### Recommended path (pip-bundled CUDA)

The `rtmpose-nvidia` extra installs `onnxruntime-gpu` plus `nvidia-*` pip packages (CUDA 12 + cuDNN 9). Skellytracker calls `onnxruntime.preload_dlls()` and loads NVIDIA DLLs from those packages — **you usually do not need a separate CUDA Toolkit or cuDNN install**.

```bash
uv sync --extra rtmpose-nvidia
skellytracker-gpus
```

### RTX 30 / 40 / 50: TensorRT RTX (fastest)

```bash
uv sync --extra rtmpose-trt-rtx
```

First run compiles TRT engines (10–20 seconds); cached under `~/.cache/skellytracker/trt_engines/rtx/`. The CLI recommends this extra when it detects an RTX GPU.

### Manual CUDA Toolkit path (optional)

If you prefer system CUDA or hit DLL errors, install:

1. **NVIDIA Driver** (CUDA 12.x capable — check with `nvidia-smi`)
2. **CUDA Toolkit 12.x** (optional if using pip-bundled libs)
3. **cuDNN 9.x** (optional if using pip-bundled libs)

#### Windows manual install

1. [CUDA Toolkit 12.x](https://developer.nvidia.com/cuda-downloads)
2. [cuDNN 9.x](https://developer.nvidia.com/cudnn-downloads)
3. [Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist) (x64)
4. Restart

#### Linux manual install

```bash
sudo apt update
sudo apt install nvidia-cuda-toolkit
# cuDNN: see NVIDIA's cuDNN .deb instructions
```

### Verify

```python
import onnxruntime as ort
print(ort.get_available_providers())
assert "CUDAExecutionProvider" in ort.get_available_providers()
```

Or:

```bash
skellytracker-gpus
```

---

## Option 2: AMD / Intel GPU on Windows (DirectML)

DirectML works with any DirectX 12 GPU. No CUDA toolkit, no cuDNN, no driver installs beyond Windows defaults.

```bash
pip install "skellytracker[rtmpose-directml]"
skellytracker-gpus --install   # when developing in this repo
```

### Verify

```python
import onnxruntime as ort
assert "DmlExecutionProvider" in ort.get_available_providers()
```

### Limitations

- **Windows only**
- Slightly slower than CUDA on NVIDIA hardware (use `rtmpose-nvidia` on NVIDIA instead)
- CoreML/DirectML runtime auto-selection completes in a follow-up release; until then, introspection may show `directml` as optimal while the session auto chain uses the best **currently wired** EP

---

## Option 3: Apple Silicon (macOS)

```bash
pip install "skellytracker[rtmpose]"
```

The base `onnxruntime` wheel on macOS includes CoreML. Hardware introspection recommends `coreml` on darwin; full CoreML auto-selection in the session chain is landing in a follow-up release. Until then, auto mode falls back to CPU if CoreML is not yet wired in the runtime.

```python
detector = RTMPoseDetector.create()  # device="auto" by default
```

---

## Option 4: AMD GPU on Linux (ROCm)

ROCm / `ROCMExecutionProvider` is not a supported skellytracker RTMPose path today. Use CPU:

```bash
pip install "skellytracker[rtmpose]"
```

RTMPose models are lightweight enough for usable CPU inference on many machines.

---

## Troubleshooting

### Start with the CLI

```bash
skellytracker-gpus
```

Compare **Optimal EP** vs **Installed best EP**. If they differ, run `skellytracker-gpus --install` (from a repo checkout with `pyproject.toml`).

### `nvidia-smi` not found

Install NVIDIA drivers from [nvidia.com/drivers](https://www.nvidia.com/download/index.aspx) (Windows) or your distro's `nvidia-driver` package (Linux).

### `CUDAExecutionProvider` missing

1. Confirm the right extra: `skellytracker-gpus` or `pip show onnxruntime-gpu`
2. On Windows with `rtmpose-nvidia`, ensure `nvidia-cudnn-cu12` installed (`pip show nvidia-cudnn-cu12`)
3. Try `pip install --force-reinstall "skellytracker[rtmpose-nvidia]"`

### `LoadLibrary failed with error 126` (Windows)

Usually a missing cuDNN/CUDA DLL. With `rtmpose-nvidia`, reinstall the extra. With manual CUDA, add CUDA and cuDNN `bin` directories to `PATH`.

### ONNX Runtime packages conflict

Only one of `onnxruntime`, `onnxruntime-gpu`, `onnxruntime-directml` can be installed. Switch with:

```bash
uv sync --extra rtmpose-nvidia   # or rtmpose-directml, rtmpose, etc.
```

### Inference uses CPU unexpectedly

Check installed EP:

```python
from skellytracker.utilities.gpu_utils import list_execution_providers
print(list_execution_providers().recommended_provider_id)
```

Ensure you did not force `execution_provider="cpu"` or `device="cpu"` in config. Auto mode (`device="auto"`, `execution_provider=None`) picks installed-best.

### CUDA out of memory

Close other GPU apps, reduce batch size / resolution, or use CPU extra.

### `uv: command not found` (for `--install`)

Install [uv](https://docs.astral.sh/uv/) or install manually:

```bash
pip install "skellytracker[rtmpose-nvidia]"
```

---

## Quick reference

| Goal | Install | CLI check |
|------|---------|-----------|
| NVIDIA CUDA | `pip install "skellytracker[rtmpose-nvidia]"` | `skellytracker-gpus` |
| NVIDIA RTX (TRT-RTX) | `pip install "skellytracker[rtmpose-trt-rtx]"` | `skellytracker-gpus` |
| Windows AMD/Intel | `pip install "skellytracker[rtmpose-directml]"` | `skellytracker-gpus` |
| macOS / CPU | `pip install "skellytracker[rtmpose]"` | `skellytracker-gpus` |
| Classic TensorRT (manual) | `pip install "skellytracker[rtmpose-trt]"` | — |
| Dev repo sync | `uv sync --extra rtmpose-nvidia` | `skellytracker-gpus --install` |

| Python API | Purpose |
|------------|---------|
| `list_installed_gpus()` | OS-native GPU inventory |
| `list_execution_providers()` | Installed EPs + optimal vs recommended flags |
| `recommend_rtmpose_extra(gpus)` | pyproject extra for `uv sync --extra` |
| `list_detection_models()` / `list_pose_models()` | Model picker data |

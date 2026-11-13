# GPU setup

This version of skellytracker has no GPU support. The ONNX trackers (RTMPose, YOLOX) run on the CPU.
On macOS, they can also run on CoreML.

The base dependency `onnxruntime` gives the CPU EP and the CoreML EP. The GPU extras
(`all-cuda`, `all-trt`, `all-directml` and the `onnx-*` extras) are removed.

GPU support comes back as plugin EP packs. The command `skellytracker-eps install` installs a pack.
The packs are `cuda` and `trt-rtx`. They need CUDA 13 and an NVIDIA GPU of the Turing generation or
newer. Classic TensorRT and DirectML are not supported
([ADR-M2C6](decisions/entries/M2C6-exact-pins-and-one-python-patch-release.md) items 2 and 3).

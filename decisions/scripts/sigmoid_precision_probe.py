"""Compare float32 sigmoid implementations near score thresholds (evidence of ADR-XXZ8).

The reference value of each logit is `1 / (1 + exp(-x))` computed in float64 and rounded once to
float32. The script compares torch CPU, torch CUDA (when available), a NumPy float32 formula (the
form of the Roboflow-Exporter decoder) and the ONNX Runtime CPU `Sigmoid` operator with it:

1. one logit, 0.8472979, against the threshold 0.7;
2. the largest difference in float32 steps (ulps) over 2,000,001 logits in [-20, 20];
3. the keep or drop results (`score > threshold`, both float32) of the 10,001 float32 logits
   around the logit of each of 8 thresholds.

It needs torch, NumPy, onnx and onnxruntime. It reads no file and writes no file. Run it with the
Python of an environment that has torch, for example the `.venv` of Roboflow-Exporter or
Ultralytics-Exporter: `<venv python> -I decisions/scripts/sigmoid_precision_probe.py`.

Result of 2026-11-16 (Python 3.14.2, torch 2.14.1+cu130 with CUDA, NumPy 2.5.4, ONNX Runtime
1.31.0, in the Roboflow-Exporter `.venv`): logit 0.8472979 gives 0.7 (dropped) for the reference,
torch CPU, torch CUDA and ONNX Runtime CPU, and 0.70000005 (kept) for NumPy float32. The largest
difference is 2 ulps on torch CPU, 3 on torch CUDA and 3 on NumPy float32. The ONNX Runtime CPU
`Sigmoid` is an approximation, and it returns 0 below about -15, so its largest difference in
ulps is not a useful number. The flips against the reference are 2 (torch CPU), 3 (torch CUDA),
3 (NumPy float32) and 13 (ONNX Runtime CPU) of 80,008 logits.
"""

from __future__ import annotations

import math
import sys

import numpy as np
import onnx
import onnxruntime as ort
import torch
from onnx import TensorProto, helper

THRESHOLDS = (0.01, 0.05, 0.1, 0.3, 0.5, 0.7, 0.75, 0.9)
SWEEP_ULPS = 5000


def reference(x: np.ndarray) -> np.ndarray:
    """Return the float64 sigmoid of float32 logits, rounded once to float32."""
    return (1.0 / (1.0 + np.exp(-x.astype(np.float64)))).astype(np.float32)


def numpy_float32(x: np.ndarray) -> np.ndarray:
    """Return the NumPy float32 sigmoid of the Roboflow-Exporter decoder form."""
    one = np.asarray(1, dtype=x.dtype)
    return one / (one + np.exp(-x.clip(-88, 88)))


def torch_cpu(x: np.ndarray) -> np.ndarray:
    """Return the torch float32 sigmoid on the CPU."""
    return torch.from_numpy(x).sigmoid().numpy()


def torch_cuda(x: np.ndarray) -> np.ndarray:
    """Return the torch float32 sigmoid on the first CUDA device."""
    return torch.from_numpy(x).cuda().sigmoid().cpu().numpy()


def ort_cpu_session() -> ort.InferenceSession:
    """Return an ONNX Runtime CPU session of a graph with one `Sigmoid` node."""
    graph = helper.make_graph(
        [helper.make_node("Sigmoid", ["x"], ["y"])],
        "sigmoid",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [None])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [None])],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 8
    onnx.checker.check_model(model)
    return ort.InferenceSession(model.SerializeToString(), providers=["CPUExecutionProvider"])


def ulps(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Return the distance in float32 steps of two float32 arrays of the same sign."""
    return np.abs(a.view(np.int32).astype(np.int64) - b.view(np.int32).astype(np.int64))


def main() -> None:
    session = ort_cpu_session()
    methods = {"torch_cpu": torch_cpu, "numpy_float32": numpy_float32}
    if torch.cuda.is_available():
        methods["torch_cuda"] = torch_cuda
    methods["ort_cpu"] = lambda x: session.run(None, {"x": x})[0]
    print("python", sys.version.split()[0], "numpy", np.__version__, "torch", torch.__version__,
          "onnxruntime", ort.__version__, "cuda", torch.cuda.is_available())

    one = np.array([0.8472979], np.float32)
    print("logit 0.8472979 reference", reference(one)[0], "kept at 0.7:", bool(reference(one)[0] > np.float32(0.7)))
    for name, method in methods.items():
        value = method(one)[0]
        print(f"logit 0.8472979 {name}", value, "kept at 0.7:", bool(value > np.float32(0.7)))

    grid = np.linspace(-20, 20, 2_000_001).astype(np.float32)
    expected = reference(grid)
    for name, method in methods.items():
        print(f"largest ulps in [-20, 20] {name}:", int(ulps(method(grid), expected).max()))

    flips = dict.fromkeys(methods, 0)
    for threshold in THRESHOLDS:
        centre = np.array([math.log(threshold / (1 - threshold))], np.float32).view(np.int32)[0]
        logits = np.arange(centre - SWEEP_ULPS, centre + SWEEP_ULPS + 1, dtype=np.int32).view(np.float32)
        limit = np.float32(threshold)
        kept = reference(logits) > limit
        for name, method in methods.items():
            flips[name] += int(((method(logits) > limit) != kept).sum())
    total = len(THRESHOLDS) * (2 * SWEEP_ULPS + 1)
    for name, count in flips.items():
        print(f"flips against the reference {name}: {count} of {total}")


if __name__ == "__main__":
    main()

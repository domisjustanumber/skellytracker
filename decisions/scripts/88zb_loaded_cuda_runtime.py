"""Evidence of ADR-88ZB: the CUDA runtime that a session on one EP loads, and the CUDA runtime of nvImageCodec.

Run one EP for each process, with an installed pack and an importable ``nvidia.nvimgcodec``::

    uv run python decisions/scripts/88zb_loaded_cuda_runtime.py cuda
    uv run python decisions/scripts/88zb_loaded_cuda_runtime.py trt-rtx

It builds one session on the probe model, then creates one ``nvimgcodec.Decoder()``. After each step it
prints the loaded CUDA runtime, nvJPEG, nvImageCodec, cuBLAS and cuDNN libraries. Then it tells if
``cudart64_13.dll`` loads by name and if ``nvcudart_hybrid64.dll`` exports ``cudaStreamSynchronize``.
It writes no file.
"""

import ctypes
import os
import sys

from skellytracker.core._hardware.libraries import loaded_module_paths
from skellytracker.core.eps import build_session
from skellytracker.core.eps._probe_model import model_bytes

MARKS = ("cudart", "nvjpeg", "nvimgcodec", "nvcuda", "cublas", "cudnn")


def show(stage):
    print(f"-- {stage}")
    for path in sorted(set(loaded_module_paths())):
        if any(mark in os.path.basename(path).lower() for mark in MARKS):
            print("  ", path)


ep = sys.argv[1]
show("before session")
session, report = build_session(model_bytes(), execution_provider=ep)
print("session", report.used_ep, report.pack_id, report.pack_version, dict(report.nodes_by_ep))
show("after session")
import nvidia.nvimgcodec as nvimgcodec  # noqa: E402

print("nvimgcodec", nvimgcodec.__version__, "cuda", nvimgcodec.__cuda_version__)
decoder = nvimgcodec.Decoder()
show("after nvimgcodec.Decoder()")
for name in ("cudart64_13.dll", "nvcudart_hybrid64.dll"):
    try:
        lib = ctypes.CDLL(name)
        print(name, "loads by name; cudaStreamSynchronize:", hasattr(lib, "cudaStreamSynchronize"))
    except OSError as error:
        print(name, "does not load by name:", error)

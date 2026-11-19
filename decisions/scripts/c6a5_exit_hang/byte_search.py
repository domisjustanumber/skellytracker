"""Evidence of ADR-C6A5: search DLL files for three markers of the 1DS telemetry client of ONNX Runtime.

Usage::

    uv run --no-sync python -B decisions/scripts/c6a5_exit_hang/byte_search.py <dll> [<dll> ...]

For each file it prints the size and, for each marker, whether the bytes are in the file. The search
ignores the case. It reads the files only. It writes no file. It ran on 2026-11-19 on the
`onnxruntime_providers_cuda.dll` of `cuda-cu13` 0.3.0 and 0.2.0 in the EP store and on the
`onnxruntime.dll` of `onnxruntime-windowsml` 1.30.0.
"""

import sys
from pathlib import Path

MARKERS = (b"WINHTTP.dll", b"OneCollector", b"ORT_DISABLE_TELEMETRY")

for name in sys.argv[1:]:
    data = Path(name).read_bytes().lower()
    found = {m.decode(): m.lower() in data for m in MARKERS}
    print(Path(name).name, len(data), found)

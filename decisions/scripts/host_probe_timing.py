#!/usr/bin/env python3
"""Time the first call of the host readers of ``skellytracker.core.system``.

Usage::

    uv run python decisions/scripts/host_probe_timing.py [REPEATS]

The script starts REPEATS new processes (default 9). Each process times the first call of each
reader and of ``probe_host()``, and the second call of ``probe_host()``. The script prints the
median of each time in milliseconds, and the count of the GPUs and of the ``probe_errors`` lines.
It prints no name, no path and no id of the host.
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys

CHILD = r"""
import json, sys, time
t0 = time.perf_counter_ns()
import skellytracker.core.system.host as host
from skellytracker.core._hardware import nvml
times = {"import": time.perf_counter_ns() - t0}
def timed(name, call):
    start = time.perf_counter_ns()
    try:
        call()
    except Exception:
        name += " (failed)"
    times[name] = time.perf_counter_ns() - start
timed("nvml init and read", nvml.read_gpus)
if sys.platform == "win32":
    from skellytracker.core._hardware import windows
    timed("dxgi and d3dkmt", windows.gpus)
    timed("psutil cores and memory", windows.cores_and_memory)
    timed("registry cpu name", windows.cpu_name)
start = time.perf_counter_ns()
info = host.probe_host()
times["probe_host, NVML started"] = time.perf_counter_ns() - start
start = time.perf_counter_ns()
host.probe_host()
times["probe_host, second call"] = time.perf_counter_ns() - start
print(json.dumps({"times": times, "gpus": len(info.gpus), "errors": len(info.probe_errors),
                  "onnxruntime": "onnxruntime" in sys.modules}))
"""


def main() -> int:
    repeats = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    runs = [json.loads(subprocess.run([sys.executable, "-c", CHILD], capture_output=True, text=True, check=True)  # noqa: S603
                       .stdout.splitlines()[-1]) for _ in range(repeats)]
    print(f"{repeats} new processes; median of each first call, in ms")
    for name in runs[0]["times"]:
        print(f"  {name}: {statistics.median(run['times'][name] for run in runs) / 1e6:.3f}")
    print(f"GPUs: {runs[0]['gpus']}; probe_errors lines: {runs[0]['errors']}; onnxruntime loaded: {runs[0]['onnxruntime']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

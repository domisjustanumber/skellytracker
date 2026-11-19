# Evidence of ADR-975Z. This scratch script ran on 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Run repro.py in a clean child process of a given interpreter, 3 times per mode, with a hard timeout. usage: runrepro.py <python> [timeout]"""
import os
import subprocess
import sys
import time
from pathlib import Path

python, timeout = sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 20
env = {k: v for k, v in os.environ.items() if not k.startswith(("NVIMGCODEC", "PYNVIMGCODEC", "PYTHON", "VIRTUAL_ENV"))}
for mode in ("single", "batch"):
    for i in range(3):
        t = time.perf_counter()
        child = subprocess.Popen([python, "-I", str(Path(__file__).parent / "repro.py"), mode], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,  # noqa: S603
                                 env=env, cwd=Path(__file__).parent)
        try:
            out, _ = child.communicate(timeout=timeout)
            code = child.returncode
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(child.pid)], capture_output=True)  # noqa: S603, S607
            out, _ = child.communicate()
            code = "killed"
        lines = [line for line in out.decode(errors="replace").splitlines() if line.startswith(("decoding", "returned", "Traceback", "  File")) or "Error" in line]
        result = "returned" if any(line.startswith("returned") for line in lines) else ("HANG" if code == "killed" else "ERR")
        print(f"{mode} run {i + 1}: {result} exit={code} {time.perf_counter() - t:.1f}s :: {' | '.join(lines)[-400:]}", flush=True)

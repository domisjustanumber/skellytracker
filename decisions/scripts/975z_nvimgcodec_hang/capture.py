# Evidence of ADR-975Z. This scratch script ran on 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Start one hanging probe child (T=4, S=1, n=1), capture its native stacks and CPU time, then end it."""
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).parent
STACKS = HERE.parent / "exit_hang" / "native_stacks.py"
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
env.pop("NVIMGCODEC_DEFAULT_NUM_CUDA_STREAMS", None)
child = subprocess.Popen([sys.executable, "-B", str(HERE / "probe.py"), "4", "1", "1"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)  # noqa: S603
try:
    time.sleep(8)
    launcher = psutil.Process(child.pid)
    kids = [p for p in launcher.children() if p.name().lower() == "python.exe"]
    target = kids[0] if kids else launcher
    t1 = target.cpu_times()
    time.sleep(3)
    t2 = target.cpu_times()
    print(f"interpreter pid {target.pid} threads {target.num_threads()} cpu user {t2.user:.2f}s system {t2.system:.2f}s; "
          f"cpu in the last 3 s: {t2.user + t2.system - t1.user - t1.system:.3f}s", flush=True)
    print(subprocess.run([sys.executable, "-B", str(STACKS), str(target.pid)], capture_output=True, text=True, timeout=60).stdout, flush=True)  # noqa: S603
finally:
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(child.pid)], capture_output=True)  # noqa: S603, S607
    out, _ = child.communicate()
    print("--- child output\n" + out.decode(errors="replace")[-1500:])

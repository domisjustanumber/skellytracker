# Evidence of ADR-C6A5. This scratch script ran on 2026-11-17. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Run gpu_preprocess_race.py unchanged, with exit markers.

Env: PAD_KB (extra stdout/stderr bytes, in KiB, to fill a pipe), TEARDOWN (an order name, see teardown in
race_teardown.py; not used here).
"""
import atexit
import os
from pathlib import Path
import runpy
import sys
import time

SCRIPTS = str(Path(__file__).resolve().parents[4] / "specs" / "model-sidecar" / "decisions" / "scripts")
T0 = time.perf_counter()


def _marker():
    print(f"MARK atexit ran t={time.perf_counter() - T0:.1f}s cpu={time.process_time():.1f}s", flush=True)
    sys.stderr.write("MARK atexit ran (stderr)\n")
    sys.stderr.flush()


atexit.register(_marker)  # registered first, so it runs last of the atexit handlers
sys.path.insert(0, SCRIPTS)
pad = int(os.environ.get("PAD_KB", "0"))
if pad:
    line = "p" * 1023 + "\n"
    for _ in range(pad):
        sys.stdout.write(line)
        sys.stderr.write(line)
    sys.stdout.flush()
    sys.stderr.flush()
    print("MARK pad written", flush=True)
sys.argv = [os.path.join(SCRIPTS, "gpu_preprocess_race.py"), *sys.argv[1:]]
runpy.run_path(sys.argv[0], run_name="__main__")
print(f"MARK runpy returned t={time.perf_counter() - T0:.1f}s", flush=True)

# Evidence of ADR-1SZ9. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Run measure.py configurations one after another. Before each: wait (max 20 min) until no other python process is on the GPU."""
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = os.environ["SKELLYTRACKER_CHECKOUT"]
LOG = HERE / "logs"
LOG.mkdir(exist_ok=True)


def gpu_state():
    apps = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"], capture_output=True, text=True, timeout=60).stdout  # noqa: S607
    util = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=60).stdout.strip()  # noqa: S607
    pythons = [line for line in apps.splitlines() if "python" in line.lower()]
    return pythons, util


def wait_quiet(log):
    deadline = time.time() + 1200
    while True:
        pythons, util = gpu_state()
        busy = int(util.split(",")[0])
        if not pythons and busy < 30:
            log.write(f"gpu quiet: util,mem={util}\n")
            return util
        log.write(f"gpu busy: pythons={pythons} util,mem={util}\n")
        log.flush()
        if time.time() > deadline:
            raise SystemExit(f"GPU not quiet after 20 minutes: {pythons} {util}")
        time.sleep(20)


def main():
    plan = [line.split() for line in Path(sys.argv[1]).read_text().splitlines() if line.strip() and not line.startswith("#")]
    with open(LOG / f"driver_{Path(sys.argv[1]).stem}.log", "a") as log:
        for args in plan:
            tag = args[args.index("--tag") + 1]
            if (HERE / "runs" / f"{tag}.json").exists():
                continue
            util = wait_quiet(log)
            cmd = ["uv", "run", "--no-sync", "python", str(HERE / "measure.py"), *args]
            t = time.time()
            with open(LOG / f"{tag}.log", "w") as out:
                out.write(f"gpu before: {util}\n")
                out.flush()
                try:
                    code = subprocess.run(cmd, cwd=WORKTREE, stdout=out, stderr=subprocess.STDOUT, timeout=1200).returncode  # noqa: S603
                except subprocess.TimeoutExpired:
                    code = "timeout"
            log.write(f"{tag}: exit {code} in {time.time() - t:.0f}s\n")
            log.flush()
            print(tag, code, f"{time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()

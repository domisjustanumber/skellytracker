# Evidence of ADR-BP5Y. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Run the plan one job at a time (pipeline measure.py or decoder_alone.py) with the exported tree first on PYTHONPATH.

Before each job: wait (poll 30 s, max 20 min) until no other python process is on the GPU and the GPU is under 30 %;
after 20 min the job runs anyway and the log says so. Each child has a 300 s timeout; on timeout only the child's own
process tree is killed (taskkill /T on the child pid), and the log says whether the job had already written its result.
Usage: uv run --project <worktree> --no-sync python -B driver.py plan.txt
"""
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = os.environ["SKELLYTRACKER_CHECKOUT"]
LOG = HERE / "logs"
LOG.mkdir(exist_ok=True)
ENV = os.environ | {"PYTHONPATH": str(HERE / "src")}


def gpu_state():
    apps = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"], capture_output=True, text=True, timeout=60).stdout  # noqa: S607
    util = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=60).stdout.strip()  # noqa: S607
    return [line for line in apps.splitlines() if "python" in line.lower()], util


def wait_quiet(log):
    deadline = time.time() + 1200
    while True:
        pythons, util = gpu_state()
        if not pythons and int(util.split(",")[0]) < 30:
            return f"quiet util,mem={util}"
        log.write(f"gpu busy: pythons={pythons} util,mem={util}\n")
        log.flush()
        if time.time() > deadline:
            return f"RAN WITH GPU BUSY after 20 min: pythons={pythons} util,mem={util}"
        time.sleep(30)


def main():
    plan = [line.split() for line in Path(sys.argv[1]).read_text().splitlines() if line.strip() and not line.startswith("#")]
    with open(LOG / f"driver_{Path(sys.argv[1]).stem}.log", "a") as log:
        for script, *args in plan:
            tag = args[args.index("--tag") + 1]
            result = HERE / "runs" / f"{tag}.json"
            if result.exists():
                continue
            gpu = wait_quiet(log)
            cmd = ["uv", "run", "--project", WORKTREE, "--no-sync", "python", "-B", str(HERE / script), *args]
            t = time.time()
            with open(LOG / f"{tag}.log", "w") as out:
                out.write(f"gpu before: {gpu}\n")
                out.flush()
                child = subprocess.Popen(cmd, cwd=HERE, env=ENV, stdout=out, stderr=subprocess.STDOUT)  # noqa: S603
                try:
                    code = child.wait(timeout=300)
                except subprocess.TimeoutExpired:
                    subprocess.run(["taskkill", "/T", "/F", "/PID", str(child.pid)], capture_output=True)  # noqa: S603, S607
                    child.wait()
                    code = f"timeout (result written: {result.exists()})"
            line = f"{tag}: exit {code} in {time.time() - t:.0f}s; gpu before: {gpu}"
            log.write(line + "\n")
            log.flush()
            print(line, flush=True)


if __name__ == "__main__":
    main()

# Evidence of ADR-FBV5. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Run measure.py lines of a plan file one after another (one GPU process at a time).

Before each: wait (max 20 min) until no other python process is on the GPU. A run that passes its timeout is NOT killed:
the driver records its process facts to logs/hang_<tag>.txt and stops the plan.
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
TIMEOUT = 1500


def gpu_state():
    apps = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"], capture_output=True, text=True, timeout=60).stdout  # noqa: S607
    util = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=60).stdout.strip()  # noqa: S607
    return [line for line in apps.splitlines() if "python" in line.lower()], util


def wait_quiet(log):
    deadline = time.time() + 1200
    while True:
        pythons, util = gpu_state()
        if not pythons:
            log.write(f"gpu quiet: util,mem={util}\n")
            return util
        log.write(f"gpu busy: pythons={pythons} util,mem={util}\n")
        log.flush()
        if time.time() > deadline:
            raise SystemExit(f"GPU not quiet after 20 minutes: {pythons} {util}")
        time.sleep(20)


def facts(tag, root_pid):
    ps = ("$all = Get-CimInstance Win32_Process; $kids = @(" + str(root_pid) + "); "
          "for ($i=0; $i -lt 4; $i++) { $kids += ($all | Where-Object { $kids -contains $_.ParentProcessId }).ProcessId; $kids = $kids | Select-Object -Unique }; "
          "foreach ($p in $kids) { $c = $all | Where-Object ProcessId -eq $p; if ($c) { \"PID $p PARENT $($c.ParentProcessId) THREADS $($c.ThreadCount) CMD $($c.CommandLine)\"; "
          "try { (Get-Process -Id $p).Modules | ForEach-Object ModuleName | Sort-Object | Out-String -Width 400 } catch { \"modules: $_\" } } }")
    out = subprocess.run(["pwsh", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=120)  # noqa: S603, S607
    (LOG / f"hang_{tag}.txt").write_text(out.stdout + out.stderr)


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
                proc = subprocess.Popen(cmd, cwd=WORKTREE, stdout=out, stderr=subprocess.STDOUT)  # noqa: S603
                try:
                    code = proc.wait(timeout=TIMEOUT)
                except subprocess.TimeoutExpired:
                    facts(tag, proc.pid)
                    log.write(f"{tag}: TIMEOUT after {TIMEOUT}s, pid {proc.pid} left running, facts in hang_{tag}.txt\n")
                    print(tag, "TIMEOUT", proc.pid, flush=True)
                    raise SystemExit(2)  # noqa: B904
            log.write(f"{tag}: exit {code} in {time.time() - t:.0f}s\n")
            log.flush()
            print(tag, code, f"{time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()

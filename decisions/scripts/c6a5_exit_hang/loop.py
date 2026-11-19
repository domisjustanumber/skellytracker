# Evidence of ADR-C6A5. This scratch script ran on 2026-11-18 and 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Bounded child-run loop for the exit-hang study (stdlib only).

Each child runs as the S8 driver ran it: Popen(cmd, cwd=WORKTREE, stdout=<file>, stderr=STDOUT).
A child that is not done after --timeout s is a HANG: the loop first captures each descendant
python.exe (threads with state and wait reason, modules, py-spy native+Python stacks, nvidia-smi),
then ends the tree.

usage: loop.py --runs N --timeout S --label L [--gpu-wait] [--stdout file|pipe] [--env K=V ...] -- cmd...
Row (rows.txt): label idx result exit total_s exit_latency_s gpu_mem_before marks
exit_latency_s = process end - last write to the log (the result line or the last marker).
"""
import argparse
import json
import os
import pathlib
import subprocess
import time

HERE = pathlib.Path(__file__).resolve().parent
WORKTREE = os.environ["LOOP_CWD"]  # the child cwd: uv picks this project
PS = ["powershell", "-NoProfile", "-Command"]
GPU_BUDGET_S = 120 * 60
_gpu_waited = [0.0]


def processes() -> list[dict]:
    q = "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name | ConvertTo-Json -Compress"
    out = subprocess.run(PS + [q], capture_output=True, text=True, timeout=120).stdout  # noqa: S603
    return json.loads(out or "[]")


def descendants(root: int) -> list[dict]:
    procs = processes()
    found, seen, frontier = [], {root}, {root}
    while frontier:
        kids = [p for p in procs if p["ParentProcessId"] in frontier and p["ProcessId"] not in seen]
        found += kids
        frontier = {p["ProcessId"] for p in kids}
        seen |= frontier
    return found


def gpu_pythons() -> list[str]:
    out = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],  # noqa: S607
                         capture_output=True, text=True, timeout=60).stdout
    return [line for line in out.splitlines() if "python" in line.lower()]


def gpu_mem() -> str:
    return subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],  # noqa: S607
                          capture_output=True, text=True, timeout=60).stdout.strip().replace(" ", "")


def foreign_driver() -> bool:
    """Another agent's plan driver (driver.py) is alive: it polls for a quiet GPU every 20 s, so leave it a gap."""
    q = "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*driver.py*' }).Count"
    out = subprocess.run(PS + [q], capture_output=True, text=True, timeout=120).stdout.strip()  # noqa: S603
    return out.isdigit() and int(out) > 0


def wait_gpu(log) -> bool:
    if foreign_driver():
        log.write(f"{time.strftime('%H:%M:%S')} foreign driver alive: 30 s gap\n")
        log.flush()
        time.sleep(30)
    while True:
        busy = gpu_pythons()
        if not busy:
            return True
        if _gpu_waited[0] >= GPU_BUDGET_S:
            return False
        log.write(f"{time.strftime('%H:%M:%S')} gpu busy: {busy}\n")
        log.flush()
        time.sleep(60)
        _gpu_waited[0] += 60


def capture(root: int, path: pathlib.Path) -> None:
    with open(path, "a", encoding="utf-8", errors="replace") as f:
        tree = descendants(root)
        f.write(f"tree of {root}: {tree}\n")
        f.write(f"gpu: {gpu_mem()}\nnvidia-smi python apps: {gpu_pythons()}\n")
        for p in tree:
            if p["Name"].lower() != "python.exe":
                continue
            pid = p["ProcessId"]
            ps = (f"$g=Get-Process -Id {pid}; 'pid {pid} cpu '+$g.TotalProcessorTime+' threads '+$g.Threads.Count+' handles '+$g.HandleCount+' ws '+$g.WorkingSet64; "
                  f"$g.Threads | Select Id,ThreadState,WaitReason,TotalProcessorTime,StartAddress | Format-Table -AutoSize | Out-String -Width 250; "
                  f"$g.Modules | Select ModuleName,FileName | Format-Table -AutoSize | Out-String -Width 300")
            for cmd in (PS + [ps], ["uv", "run", "--no-sync", "--project", WORKTREE, "python", "-I", str(HERE / "native_stacks.py"), str(pid)], ["uvx", "--offline", "py-spy", "dump", "--native", "--pid", str(pid)],
                        ["uvx", "--offline", "py-spy", "dump", "--pid", str(pid)]):
                f.write(f"--- {' '.join(cmd)[:120]}\n")
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180, errors="replace")  # noqa: S603
                    f.write(r.stdout + r.stderr + "\n")
                except subprocess.TimeoutExpired:
                    f.write("(capture command timed out)\n")


def end_tree(proc: subprocess.Popen) -> None:
    rest = descendants(proc.pid)
    subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, timeout=60)  # noqa: S603, S607
    for p in rest:  # a launcher whose parent died is no longer in the tree of proc
        subprocess.run(["taskkill", "/F", "/PID", str(p["ProcessId"])], capture_output=True, timeout=60)  # noqa: S603, S607
    proc.wait(timeout=60)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, required=True)
    ap.add_argument("--timeout", type=float, required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--gpu-wait", action="store_true")
    ap.add_argument("--stdout", default="file", choices=["file", "pipe"])
    ap.add_argument("--env", nargs="*", default=[])
    ap.add_argument("--stop-on-hang", action="store_true")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    logdir = HERE / "logs" / a.label
    logdir.mkdir(parents=True, exist_ok=True)
    rows = open(HERE / "rows.txt", "a")
    loop_log = open(logdir / "loop.log", "a")
    for i in range(a.runs):
        if a.gpu_wait and not wait_gpu(loop_log):
            rows.write(f"{a.label} {i} NOGPU\n")
            rows.flush()
            break
        if (HERE / "STOP").exists():
            break
        env = dict(os.environ, **dict(kv.split("=", 1) for kv in a.env))
        env["EXIT_FH"] = str(logdir / f"run{i:03d}.faulthandler.txt")
        log = logdir / f"run{i:03d}.log"
        mem = gpu_mem()
        fh = open(log, "wb")
        kw = {"stdout": fh, "stderr": subprocess.STDOUT} if a.stdout == "file" else {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
        t0 = time.time()
        proc = subprocess.Popen(cmd, cwd=WORKTREE, env=env, **kw)  # noqa: S603
        try:
            code = proc.wait(timeout=a.timeout)
            result = "ok" if code == 0 else "fail"
        except subprocess.TimeoutExpired:
            result = "HANG"
            capture(proc.pid, logdir / f"run{i:03d}.capture.txt")
            end_tree(proc)
            code = proc.returncode
        t_end = time.time()
        fh.close()
        if a.stdout == "pipe":
            log.write_bytes(proc.stdout.read() + proc.stderr.read())
            last_write = t_end
        else:
            last_write = log.stat().st_mtime
        text = log.read_bytes().decode("utf-8", "replace")
        marks = "".join(m[0] for m in ("main-returned", "gc-done", "unreg-done", "terminate-now", "atexit-last", "builtins-teardown") if f"MARK {m}" in text) or "-"
        row = f"{a.label} {i} {result} exit={code} total_s={t_end - t0:.1f} exit_latency_s={t_end - last_write:.2f} gpu={mem} marks={marks}"
        rows.write(row + "\n")
        rows.flush()
        print(row, flush=True)
        if result == "HANG" and a.stop_on_hang:
            break


if __name__ == "__main__":
    main()

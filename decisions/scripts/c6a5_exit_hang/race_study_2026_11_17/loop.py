# Evidence of ADR-C6A5. This scratch script ran on 2026-11-17. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Bounded run loop (stdlib only). Each run gets a deadline; a stuck run is captured, then killed.

usage: loop.py --runs N --timeout S --label L --out rows.txt [--stdout file|pipe|devnull] [--env K=V ...] -- cmd...
Row: label idx result exit ms marks ctxrel
"""
import argparse
import os
import pathlib
import subprocess
import sys  # noqa: F401
import time

HERE = pathlib.Path(__file__).parent
PS = "powershell -NoProfile -Command "


def interpreter_pid(launcher: int) -> int:
    q = f"(Get-CimInstance Win32_Process -Filter 'ParentProcessId={launcher}' | Where-Object Name -eq 'python.exe' | Select-Object -First 1).ProcessId"
    out = subprocess.run(PS + f'"{q}"', capture_output=True, text=True, timeout=60).stdout.strip()  # noqa: S603
    return int(out) if out.isdigit() else launcher


def capture(pid: int, path: pathlib.Path) -> None:
    cmds = [
        PS + f'"$g=Get-Process -Id {pid}; \'cpu \'+$g.TotalProcessorTime+\' threads \'+$g.Threads.Count; '
        f'$g.Threads | Group-Object ThreadState,WaitReason | Select Count,Name | Format-Table -AutoSize | Out-String -Width 200; '
        f'$g.Threads | Select Id,ThreadState,WaitReason,TotalProcessorTime | Format-Table -AutoSize | Out-String -Width 200"',
        "nvidia-smi --query-compute-apps=pid,process_name --format=csv",
        f"uvx py-spy dump --native --pid {pid}",
        f"uvx py-spy dump --pid {pid}",
    ]
    with open(path, "a", encoding="utf-8", errors="replace") as f:
        for c in cmds:
            f.write(f"--- {c}\n")
            try:
                r = subprocess.run(c, capture_output=True, text=True, timeout=120, errors="replace")  # noqa: S603
                f.write(r.stdout + r.stderr + "\n")
            except subprocess.TimeoutExpired:
                f.write("(capture command timed out)\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--runs", type=int, required=True)
    p.add_argument("--timeout", type=float, required=True)
    p.add_argument("--label", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--stdout", default="file", choices=["file", "pipe", "devnull"])
    p.add_argument("--env", nargs="*", default=[])
    p.add_argument("--keep-logs", action="store_true")
    p.add_argument("--stop-file", help="stop before the next run when this file exists")
    p.add_argument("cmd", nargs=argparse.REMAINDER)
    a = p.parse_args()
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    env = dict(os.environ, **dict(kv.split("=", 1) for kv in a.env))
    logdir = HERE / "logs" / a.label
    logdir.mkdir(parents=True, exist_ok=True)
    for i in range(a.runs):
        if a.stop_file and os.path.exists(a.stop_file):
            break
        log = logdir / f"run{i:03d}.log"
        if a.stdout == "file":
            fh = open(log, "wb")
            kw = {"stdout": fh, "stderr": subprocess.STDOUT}
        elif a.stdout == "pipe":  # a pipe that nobody reads
            kw = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
        else:
            kw = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        t0 = time.perf_counter()
        proc = subprocess.Popen(cmd, env=env, cwd=os.environ["SKELLYTRACKER_CHECKOUT"], **kw)  # noqa: S603
        try:
            code = proc.wait(timeout=a.timeout)
            result = "ok" if code == 0 else "fail"
        except subprocess.TimeoutExpired:
            result = "STUCK"
            capture(interpreter_pid(proc.pid), logdir / f"run{i:03d}.capture.txt")
            subprocess.run(f"taskkill /T /F /PID {proc.pid}", capture_output=True, timeout=60)  # noqa: S603
            code = proc.wait(timeout=60)
        ms = int((time.perf_counter() - t0) * 1000)
        if a.stdout == "file":
            fh.close()
            text = log.read_bytes().decode("utf-8", "replace")
        else:
            text = ""
            if a.stdout == "pipe":
                text = (proc.stdout.read() + proc.stderr.read()).decode("utf-8", "replace")
                log.write_text(text, encoding="utf-8")
        marks = "".join(k for k, s in (("M", "main returned"), ("A", "MARK atexit ran"), ("D", "MARK done"), ("T", "Timeout (")) if s in text)
        ctx = text.count("cuDevicePrimaryCtxRelease failed")
        row = f"{a.label} {i} {result} exit={code} ms={ms} marks={marks or '-'} ctxrel={ctx}"
        print(row, flush=True)
        with open(a.out, "a", encoding="utf-8") as f:
            f.write(row + "\n")
        if result == "ok" and not a.keep_logs:
            log.unlink(missing_ok=True)


if __name__ == "__main__":
    main()

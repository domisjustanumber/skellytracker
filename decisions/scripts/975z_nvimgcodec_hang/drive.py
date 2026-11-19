# Evidence of ADR-975Z. This scratch script ran on 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Run probe.py children with a hard timeout; print one row per run. Kills only its own child tree.

usage: drive.py <rows file> <spec>...   spec = "ENV=VAL;...|probe args"  (ENV part may be empty)
"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
TIMEOUT = float(os.environ.get("PROBE_TIMEOUT", "15"))
LOG = re.compile(r"selected num_threads|CUDA streams|num_cuda_streams", re.I)


def run(env_part: str, args: list[str]) -> str:
    env = dict(os.environ, PYNVIMGCODEC_VERBOSITY="3", PYTHONDONTWRITEBYTECODE="1")
    env.pop("NVIMGCODEC_DEFAULT_NUM_CUDA_STREAMS", None)
    for item in filter(None, env_part.split(";")):
        key, value = item.split("=", 1)
        env[key] = value
    t = time.perf_counter()
    child = subprocess.Popen([sys.executable, "-B", str(HERE / os.environ.get("PROBE_SCRIPT", "probe.py")), *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)  # noqa: S603
    try:
        out, _ = child.communicate(timeout=TIMEOUT)
        code = child.returncode
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(child.pid)], capture_output=True)  # noqa: S603, S607
        out, _ = child.communicate()
        code = "killed"
    text = out.decode(errors="replace")
    result = "ok" if "main done" in text else ("HANG" if code == "killed" else "ERR")
    logs = sorted({re.sub(r"\x1b\[[0-9;]*m", "", line).strip()[-110:] for line in text.splitlines() if LOG.search(line)})
    tail = "" if result != "ERR" else " || " + text.strip().splitlines()[-1][-200:]
    done = [line for line in text.splitlines() if line.startswith(("decode", "pre ", "affinity", "open", "exit", "LOG"))]
    done = done if os.environ.get("PROBE_SCRIPT") else done[-1:]
    return f"{result:4} exit={code} {time.perf_counter() - t:5.1f}s env=[{env_part}] args={' '.join(args)} :: {' | '.join(logs)} :: {' '.join(done)}{tail}"


rows = Path(sys.argv[1])
for spec in sys.argv[2:]:
    env_part, _, arg_part = spec.partition("|")
    row = run(env_part, arg_part.split())
    print(row, flush=True)
    with rows.open("a", encoding="utf-8") as f:
        f.write(row + "\n")

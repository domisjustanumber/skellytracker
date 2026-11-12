"""Run the gemm/deterministic matrix, one fresh child process per job, one at a time.

Usage: python -I -B run.py GROUP [GROUP ...] [--force]
Groups: probe, base, gemm, det, base2, detrep, gemmcfg, gemmenv.
Appends one JSON line per job to results/results.jsonl. Peak VRAM: NVML device-wide, sampled each 20 ms.
"""
import ctypes
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS, RESULTS, INPUTS = ROOT / "scripts", ROOT / "results", ROOT / "inputs"
JOBS, LOGS, REFS, DETREP = RESULTS / "jobs", RESULTS / "logs", RESULTS / "refs", RESULTS / "detrep"
JSONL = RESULTS / "results.jsonl"
PY = ROOT / "env" / ".venv" / "Scripts" / "python.exe"
EXP = Path(os.environ["GEMM_EXPORTS"])  # the exporter model folder (read only)
SIZES, BATCHES, PRECS = ("m", "x-384"), (1, 3), ("fp32", "fp16")
TIMEOUT = 600
GREP = ["gemm", "auto_tune", "autotune", "autotuned", "tune", "determinis", "invalid value", "tinygemm",
        "small_n", "candidate"]


def model(size, b, p):
    return str(EXP / f"rtmw-wholebody133-{size}_b{b}_{p}.onnx")


def tag(size, b, p):
    return f"{size}_b{b}_{p}"


def job(group, size, b, p, suffix="", po=None, cfg=None, env=None, det=False, **kw):
    jid = f"{group}|{tag(size, b, p)}" + (f"|{suffix}" if suffix else "")
    j = {"id": jid, "group": group, "size": size, "batch": b, "precision": p, "model": model(size, b, p),
         "input": str(INPUTS / f"{size}_b{b}.npy"), "ref": str(REFS / f"{tag(size, b, p)}.npz"),
         "provider_options": po or {}, "session_config": cfg or {}, "env_vars": env or {},
         "deterministic": det, "warmup": 5, "runs": 30, "log_severity": 2}
    j.update(kw)
    return j


def grid(group, **kw):
    return [job(group, s, b, p, **kw) for s in SIZES for b in BATCHES for p in PRECS]


def matrix():
    J = {}
    v = {"log_severity": 0, "runs": 3, "warmup": 1}
    J["probe"] = [
        job("probe", "x-384", 1, "fp16", "verbose-baseline", **v),
        job("probe", "x-384", 1, "fp16", "po-1-verbose", po={"enable_gemm_auto_tune": "1"}, **v),
        job("probe", "x-384", 1, "fp32", "po-1-verbose", po={"enable_gemm_auto_tune": "1"}, **v),
        job("probe", "x-384", 1, "fp16", "po-banana", po={"enable_gemm_auto_tune": "banana"}, **v),
        job("probe", "x-384", 1, "fp16", "po-epcuda-banana", po={"ep.cuda.enable_gemm_auto_tune": "banana"}, **v),
        job("probe", "x-384", 1, "fp16", "cfg-epcuda-banana", cfg={"ep.cuda.enable_gemm_auto_tune": "banana"}, **v),
        job("probe", "x-384", 1, "fp16", "cfg-epcuda-1-verbose", cfg={"ep.cuda.enable_gemm_auto_tune": "1"}, **v),
        job("probe", "x-384", 1, "fp16", "env-banana", env={"ORT_CUDA_GEMM_AUTO_TUNE": "banana"}, **v),
        job("probe", "x-384", 1, "fp16", "env-1-verbose", env={"ORT_CUDA_GEMM_AUTO_TUNE": "1"}, **v),
        job("probe", "x-384", 1, "fp32", "det-verbose", det=True, **v),
    ]
    J["base"] = [dict(j, ref=None, save_out=j["ref"]) for j in grid("base")]
    J["gemm"] = grid("gemm", po={"enable_gemm_auto_tune": "1"})
    J["gemmcfg"] = grid("gemmcfg", cfg={"ep.cuda.enable_gemm_auto_tune": "1"})
    J["gemmenv"] = grid("gemmenv", env={"ORT_CUDA_GEMM_AUTO_TUNE": "1"})
    J["det"] = grid("det", det=True)
    J["base2"] = grid("base2")
    # interleaved timing: base, gemm, det in rotated order, three rounds per configuration
    J["inter"] = []
    arms = [("base", {}, False), ("gemm", {"enable_gemm_auto_tune": "1"}, False), ("det", {}, True)]
    for s in SIZES:
        for b in BATCHES:
            for p in PRECS:
                for r in range(3):
                    for k in range(3):
                        name, po, det = arms[(k + r) % 3]
                        J["inter"].append(job("inter", s, b, p, f"{name}-r{r}", po=po, det=det))
    J["inter2"] = []  # five more rotated rounds for the noisy m fp16 configurations
    for b in BATCHES:
        for r in range(3, 8):
            for k in range(3):
                name, po, det = arms[(k + r) % 3]
                J["inter2"].append(job("inter2", "m", b, "fp16", f"{name}-r{r}", po=po, det=det))
    # where is the option parsed? tiny models with and without a MatMul
    tiny = ROOT / "tiny"
    J["tiny"] = []
    for mname in ("relu", "matmul32", "matmul16"):
        for t, po in (("off", {}), ("banana", {"enable_gemm_auto_tune": "banana"}), ("on", {"enable_gemm_auto_tune": "1"})):
            J["tiny"].append(job("tiny", "tiny", 1, mname, t, po=po, model=str(tiny / f"{mname}.onnx"),
                                 input=str(tiny / "tiny_in.npy"), ref=None, runs=50, warmup=10,
                                 save_out=str(tiny / f"{mname}_{t}.npz")))
    J["detrep"] = []
    for size in SIZES:
        for mode in ("nodet", "det"):
            for i in range(10):
                out = str(DETREP / f"{size}_b3_fp32_{mode}_{i}.npz")
                J["detrep"].append(job("detrep", size, 3, "fp32", f"{mode}-s{i}", det=(mode == "det"),
                                       runs=0, warmup=0, save_out=out))
    return J


class Nvml:
    def __init__(self):
        self.lib = None
        for name in ("nvml.dll", r"C:\Program Files\NVIDIA Corporation\NVSMI\nvml.dll"):
            try:
                self.lib = ctypes.CDLL(name)
                break
            except OSError:
                continue
        if self.lib is None or self.lib.nvmlInit_v2() != 0:
            raise OSError("NVML is not available")
        self.handle = ctypes.c_void_p()
        if self.lib.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(self.handle)) != 0:
            raise OSError("NVML lists no GPU")

    def used_mb(self):
        class Memory(ctypes.Structure):
            _fields_ = [("total", ctypes.c_ulonglong), ("free", ctypes.c_ulonglong), ("used", ctypes.c_ulonglong)]
        mem = Memory()
        self.lib.nvmlDeviceGetMemoryInfo(self.handle, ctypes.byref(mem))
        return mem.used / 2**20


class Sampler:
    def __init__(self, nvml):
        self.nvml, self.stop = nvml, threading.Event()
        self.base = self.peak = nvml.used_mb() if nvml else 0.0

    def __enter__(self):
        if self.nvml:
            self.t = threading.Thread(target=self.loop, daemon=True)
            self.t.start()
        return self

    def loop(self):
        while not self.stop.wait(0.02):
            self.peak = max(self.peak, self.nvml.used_mb())

    def __exit__(self, *a):
        self.stop.set()
        if self.nvml:
            self.t.join()


def done_ids():
    if not JSONL.exists():
        return set()
    return {json.loads(line)["id"] for line in JSONL.read_text(encoding="utf-8").splitlines() if line.strip()}


def read_log(path):
    """ORT on Windows writes its log lines to stderr as UTF-16-LE; Python prints UTF-8. Decode both."""
    raw = Path(path).read_bytes()
    if raw.count(b"\x00") > len(raw) // 4:
        return raw.replace(b"\x00", b"").decode("utf-8", errors="replace")
    return raw.decode("utf-8", errors="replace")


def run_one(j, nvml):
    safe = j["id"].replace("|", "__")
    j["result"] = str(JOBS / f"{safe}.result.json")
    jf = JOBS / f"{safe}.json"
    jf.write_text(json.dumps(j, indent=1), encoding="utf-8")
    Path(j["result"]).unlink(missing_ok=True)
    log = LOGS / f"{safe}.log"
    env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME")}
    env.update(j.get("env_vars", {}))
    rec = {}
    t0 = time.perf_counter()
    with Sampler(nvml) as s, open(log, "w", encoding="utf-8", errors="replace") as lf:
        try:
            proc = subprocess.run([str(PY), "-I", "-B", str(SCRIPTS / "child.py"), str(jf)], stdout=lf,  # noqa: S603
                                  stderr=subprocess.STDOUT, env=env, timeout=TIMEOUT, cwd=str(ROOT))
            rec["exit_code"] = proc.returncode
        except subprocess.TimeoutExpired:
            rec["exit_code"], rec["timeout"] = None, True
    rec["wall_s"] = round(time.perf_counter() - t0, 2)
    rec["vram_base_mb"] = round(s.base) if nvml else None
    rec["vram_peak_delta_mb"] = round(s.peak - s.base) if nvml else None
    try:
        rec.update(json.loads(Path(j["result"]).read_text(encoding="utf-8")))
    except Exception as exc:  # noqa: BLE001
        rec["ok"] = False
        rec["error"] = f"no result file ({type(exc).__name__}); exit {rec.get('exit_code')}"
    text = read_log(log)
    rec["log_bytes"] = len(text)
    rec["log_hits"] = [ln[:400] for ln in text.splitlines() if any(k in ln.lower() for k in GREP)][:60]
    rec["log_tail"] = text[-800:]
    return rec


def main():
    groups = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    J = matrix()
    for d in (JOBS, LOGS, REFS, DETREP):
        d.mkdir(parents=True, exist_ok=True)
    try:
        nvml = Nvml()
    except OSError:
        nvml = None
    done = set() if force else done_ids()
    for g in groups:
        for j in J[g]:
            if j["id"] in done:
                continue
            jj = dict(j)
            rec = run_one(jj, nvml)
            line = {"id": j["id"], "job": jj, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), **rec}
            with open(JSONL, "a", encoding="utf-8") as f:
                f.write(json.dumps(line, default=str) + "\n")
            t = rec.get("timing") or {}
            dec = rec.get("decoded_vs_baseline") or {}
            mx = max((v["max_abs"] for v in (rec.get("vs_baseline") or {}).values()), default=None)
            print(f"{j['id']:<44} ok={rec.get('ok')} cpu={rec.get('cpu_nodes')} build={rec.get('build_ms')} "
                  f"med={t.get('median_ms')} p95={t.get('p95_ms')} maxabs={mx} flips={dec.get('argmax_flips')} "
                  f"vram={rec.get('vram_peak_delta_mb')} hits={len(rec.get('log_hits', []))} "
                  f"{(rec.get('error') or '')[:200]}", flush=True)


if __name__ == "__main__":
    main()

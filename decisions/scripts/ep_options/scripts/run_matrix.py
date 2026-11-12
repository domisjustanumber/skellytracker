"""Run the EP option matrix: one fresh child process per configuration, one at a time.

Usage: python -I -B run_matrix.py ROW [ROW ...] [--force] [--dry]
ROW is a row name (C1, T2, O5, P3, M, REF ...) or a prefix group (C, T, O, P).
Appends one JSON line per configuration to results/results.jsonl. Skips ids already there unless --force.
Stdlib only. Peak VRAM: NVML (ctypes), device wide, sampled each 20 ms while the child runs.
"""
import ctypes
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS, RESULTS, CACHE = ROOT / "scripts", ROOT / "results", ROOT / "cache"
JOBS, LOGS = RESULTS / "jobs", RESULTS / "logs"
JSONL = RESULTS / "results.jsonl"
EPDC = Path(r"<epdc>\envs")
PY = {
    "cpu": EPDC / "cpu" / ".venv" / "Scripts" / "python.exe",
    "cuda": EPDC / "cuda-cu13" / ".venv" / "Scripts" / "python.exe",
    "trt": EPDC / "trt-rtx-cu13" / ".venv" / "Scripts" / "python.exe",
    "ov": ROOT / "envs" / "openvino" / ".venv" / "Scripts" / "python.exe",
}
EP = {
    "cpu": {"module": None, "select": {"type": "CPU"}},
    "cuda": {"module": "onnxruntime_ep_cuda", "select": {"vendor_id": 0x10DE}},
    "trt": {"module": "onnxruntime_ep_nv_tensorrt_rtx", "select": {"vendor_id": 0x10DE}},
    "ov": {"module": "onnxruntime_ep_openvino", "select": {"vendor_id": 0x8086, "type": "GPU"}},
}
EXP = Path(r"<repos>\OpenMMLab-Exporter\exports\detectors")
MODEL_FILE = {
    "yolox": str(EXP / "object_detectors" / "yolox-person" / "yolox-person-m_b{b}_{p}.onnx"),
    "rtmw": str(EXP / "keypoint_detectors" / "rtmw" / "wholebody133" / "rtmw-wholebody133-x-384_b{b}_{p}.onnx"),
}
MODELS, BATCHES, PRECS = ("yolox", "rtmw"), (1, 3), ("fp32", "fp16")
TIMEOUT = 300


def ref_path(m, b):
    return str(CACHE / "refs" / f"{m}_b{b}.npz")


def job(row, env, m, b, p, po=None, cfg=None, attrs=None, envvars=None, suffix="", **kw):
    jid = f"{row}|{m}|b{b}|{p}" + (f"|{suffix}" if suffix else "")
    j = {"id": jid, "row": row, "env": env, **EP[env], "model_key": m, "batch": b, "precision": p,
         "model": MODEL_FILE[m].format(b=b, p=p), "input": str(CACHE / "inputs" / f"{m}_b{b}.npy"),
         "ref": ref_path(m, b), "provider_options": po or {}, "session_config": cfg or {},
         "session_attrs": attrs or {}, "env_vars": envvars or {}, "warmup": 5, "runs": 30}
    j.update(kw)
    return j


def grid(row, env, po=None, models=MODELS, batches=BATCHES, precs=PRECS, **kw):
    return [job(row, env, m, b, p, po, **kw) for m in models for b in batches for p in precs]


def matrix():
    J = {}
    # reference = P1 ORT_ENABLE_ALL on the CPU EP, fp32, default threads
    J["REF"] = [job("REF", "cpu", m, b, "fp32", attrs={"graph_optimization_level": "ORT_ENABLE_ALL"},
                    save_ref=ref_path(m, b), ref=None) for m in MODELS for b in BATCHES]
    # ---- CUDA
    J["C1"] = grid("C1", "cuda", {})
    J["C2"] = grid("C2", "cuda", {"use_tf32": "0"})
    J["C3"] = grid("C3", "cuda", {"use_tf32": "0", "cudnn_conv_algo_search": "HEURISTIC"})
    J["C3x"] = grid("C3x", "cuda", {"use_tf32": "0", "cudnn_conv_algo_search": "EXHAUSTIVE"}, precs=("fp32",))
    J["C3x1"] = grid("C3x1", "cuda", {"cudnn_conv_algo_search": "EXHAUSTIVE"}, precs=("fp32",))
    J["C4"] = grid("C4", "cuda", {"use_tf32": "0", "cudnn_conv_algo_search": "DEFAULT"})
    J["C5"] = grid("C5", "cuda", {"prefer_nhwc": "1"})
    J["C5b"] = grid("C5b", "cuda", {"prefer_nhwc": "1", "use_tf32": "0"})
    J["C6"] = grid("C6", "cuda", {"fuse_conv_bias": "1"})
    J["C6b"] = grid("C6b", "cuda", {"fuse_conv_bias": "1", "use_tf32": "0"})
    J["C7"] = grid("C7", "cuda", {"arena.extend_strategy": "1"})
    J["C8"] = grid("C8", "cuda", {"arena.max_mem": "1073741824"}, batches=(3,), precs=("fp32",))
    J["C8b"] = grid("C8b", "cuda", {"arena.max_mem": "1073741824", "use_tf32": "0"}, models=("yolox",), batches=(3,), precs=("fp32",))
    J["C9"] = grid("C9", "cuda", {"enable_cuda_graph": "1"}, mode="iobind")
    for j in J["C9"]:
        j["cpu_model"] = MODEL_FILE[j["model_key"]].format(b=j["batch"], p="fp32")
    J["C9n"] = grid("C9n", "cuda", {}, precs=("fp32",), mode="iobind")  # I/O binding without graph
    J["C10"] = [job("C10", "cuda", "rtmw", 3, "fp32", {"use_tf32": "0"}, cfg=cfg, suffix=f"{tag}-r{i}",
                    warmup=0, runs=0)
                for tag, cfg in (("nodet", {}), ("det", {"session.use_deterministic_compute": "1"}))
                for i in range(5)]
    J["C11"] = [job("C11", "cuda", m, 1, "fp32", po, suffix=tag, log_severity=0, runs=5,
                    log_grep=["bogus", "gpu_mem_limit", "unknown", "invalid", "not recognized", "unsupported"])
                for m in MODELS for tag, po in (("bogus", {"bogus_key": "1"}), ("memlimit1", {"gpu_mem_limit": "1"}))]
    # ---- follow-up: cudnn_conv_use_max_workspace=0 with use_tf32=0
    J["REF6"] = [job("REF6", "cpu", "yolox", 6, "fp32", attrs={"graph_optimization_level": "ORT_ENABLE_ALL"},
                     save_ref=ref_path("yolox", 6), ref=None)]
    nows = {"cudnn_conv_use_max_workspace": "0"}
    J["W1"] = [job("W1", "cuda", "yolox", 3, "fp32", {"use_tf32": "0", **nows})]
    J["W2"] = [job("W2", "cuda", "yolox", 3, "fp32", {"use_tf32": "0", **nows, "arena.max_mem": "1073741824"})]
    J["W3"] = [job("W3", "cuda", "yolox", 1, "fp32", {"use_tf32": "0", **nows})]
    J["W4"] = [job("W4", "cuda", "yolox", 6, "fp32", {"use_tf32": "0"})]
    J["W4b"] = [job("W4b", "cuda", "yolox", 6, "fp32", {"use_tf32": "0", **nows})]
    J["W5"] = [job("W5", "cuda", "rtmw", 3, "fp32", {"use_tf32": "0", **nows})]
    J["W6"] = [job("W6", "cuda", "yolox", 3, "fp32", {"use_tf32": "1", **nows})]
    J["W6b"] = [job("W6b", "cuda", "yolox", 3, "fp16", dict(nows))]
    J["W7"] = [job("W7", "cuda", "yolox", 3, "fp32", {"use_tf32": "0", "cudnn_conv_algo_search": "HEURISTIC", **nows})]
    J["W8"] = [job("W8", "cuda", "yolox", 3, "fp32", {"use_tf32": "0", "prefer_nhwc": "1", **nows})]
    J["W4c"] = [job("W4c", "cuda", "yolox", 6, "fp32", {})]
    J["Wk"] = [job("Wk", "cuda", "yolox", 1, "fp32", po, suffix=tag, runs=3, log_severity=0,
                   log_grep=["workspace", "tf32", "invalid", "banana"])
               for tag, po in (("ws-banana", {"cudnn_conv_use_max_workspace": "banana"}),
                               ("tf32-banana", {"use_tf32": "banana"}),
                               ("algo-banana", {"cudnn_conv_algo_search": "banana"}))]
    J["Wv"] = [job("Wv", "cuda", "yolox", 3, "fp32", po, suffix=tag, log_severity=0, warmup=0, runs=1)
               for tag, po in (("C2", {"use_tf32": "0"}), ("W1", {"use_tf32": "0", **nows}))]
    # ---- TensorRT RTX
    J["T1"] = grid("T1", "trt", {})
    J["T2"] = []
    for m in MODELS:
        for b in BATCHES:
            for p in PRECS:
                d = str(CACHE / "trtrtx-rc" / f"{m}_b{b}_{p}")
                for phase in ("cold", "warm"):
                    J["T2"].append(job("T2", "trt", m, b, p, {"nv_runtime_cache_path": d}, suffix=phase,
                                       clear_dirs=[d] if phase == "cold" else [], check_dir=d))
    J["T3"] = []
    for m in MODELS:
        for p in PRECS:
            for form in ("cfg", "po"):
                for embed in ("0", "1"):
                    ctx = str(CACHE / "ctx" / f"{m}_b3_{p}_{form}_e{embed}_ctx.onnx")
                    keys = {"ep.context_enable": "1", "ep.context_file_path": ctx, "ep.context_embed_mode": embed}
                    tag = f"{form}-e{embed}"
                    J["T3"].append(job("T3w", "trt", m, 3, p, keys if form == "po" else {},
                                       cfg=keys if form == "cfg" else {}, suffix=tag, runs=5,
                                       clear_prefix=[Path(ctx).stem.replace("_ctx", "")], check_dir=str(CACHE / "ctx"),
                                       check_files=[ctx]))
                    J["T3"].append(job("T3l", "trt", m, 3, p, {}, suffix=tag, model_override=ctx,
                                       requires_file=ctx))
                    J["T3"].append(job("T3s", "trt", m, 3, p, {}, suffix=tag, model_override=ctx,
                                       requires_file=ctx, cfg={"session.fail_on_suboptimal_compiled_model": "1"},
                                       runs=5))
    J["T3c"] = []  # EPContext (embed 1) load plus a runtime cache: cold then warm
    for m in MODELS:
        for p in PRECS:
            ctx = str(CACHE / "ctx" / f"{m}_b3_{p}_cfg_e1_ctx.onnx")
            d = str(CACHE / "trtrtx-rc-ctx" / f"{m}_b3_{p}")
            for phase in ("cold", "warm"):
                J["T3c"].append(job("T3c", "trt", m, 3, p, {"nv_runtime_cache_path": d}, suffix=phase,
                                    model_override=ctx, requires_file=ctx, runs=10,
                                    clear_dirs=[d] if phase == "cold" else [], check_dir=d))
    J["T4"] = grid("T4", "trt", {"nv_persistent_context_memory": "1"})
    J["T5"] = grid("T5", "trt", {"enable_cuda_graph": "0"})
    J["T6"] = grid("T6", "trt", {}, envvars={"NVIDIA_TF32_OVERRIDE": "0"})
    J["T7"] = [job("T7", "trt", "yolox", 1, "fp32", po, suffix=tag, log_severity=0, runs=5,
                   log_grep=["bogus", "device_id", "unknown", "invalid", "not recognized", "unsupported"])
               for tag, po in (("bogus", {"bogus_key": "1"}), ("device_id", {"device_id": "0"}))]
    # ---- OpenVINO on the Intel iGPU
    def lc(d):
        return {"load_config": json.dumps({"GPU": d})}
    J["O1"] = grid("O1", "ov", {})
    J["O2"] = grid("O2", "ov", lc({"INFERENCE_PRECISION_HINT": "f32"}))
    J["O3"] = grid("O3", "ov", lc({"EXECUTION_MODE_HINT": "ACCURACY"}))
    J["O4"] = []
    for tag, d in (("LATENCY", {"PERFORMANCE_HINT": "LATENCY"}), ("THROUGHPUT", {"PERFORMANCE_HINT": "THROUGHPUT"}),
                   ("NS1", {"NUM_STREAMS": "1"}), ("NS2", {"NUM_STREAMS": "2"})):
        J["O4"] += [dict(j, id=j["id"] + "|" + tag) for j in grid("O4", "ov", lc(d), batches=(3,), precs=("fp32",))]
    J["O5"] = []
    for m in MODELS:
        for b in BATCHES:
            for p in PRECS:
                d = str(CACHE / "ovcache" / f"{m}_b{b}_{p}")
                for phase in ("cold", "warm"):
                    J["O5"].append(job("O5", "ov", m, b, p, lc({"CACHE_DIR": d}), suffix=phase, runs=5,
                                       clear_dirs=[d] if phase == "cold" else [], check_dir=d))
    J["O6"] = []
    for tag, d in (("prioHIGH", {"MODEL_PRIORITY": "HIGH"}), ("throttleLOW", {"GPU_QUEUE_THROTTLE": "LOW"}),
                   ("throttleHIGH", {"GPU_QUEUE_THROTTLE": "HIGH"})):
        J["O6"] += [dict(j, id=j["id"] + "|" + tag) for j in grid("O6", "ov", lc(d), precs=("fp32",))]
    J["O7"] = [job("O7", "ov", "yolox", 1, "fp32", po, suffix=tag, log_severity=0, runs=5,
                   log_grep=["precision", "cache_dir", "unknown", "invalid", "not recognized", "unsupported"])
               for tag, po in (("precision", {"precision": "FP32"}),
                               ("cache_dir", {"cache_dir": str(CACHE / "ov-o7")}))]
    def lc0(dev, d):
        return {"load_config": json.dumps({dev: d})}
    J["O9"] = []  # load_config keyed by the resolved device name GPU.0, verbose log
    for dev in ("GPU", "GPU.0"):
        for tag, d in (("f32", {"INFERENCE_PRECISION_HINT": "f32"}), ("ACC", {"EXECUTION_MODE_HINT": "ACCURACY"})):
            J["O9"].append(job("O9", "ov", "rtmw", 1, "fp32", lc0(dev, d), suffix=f"{dev}-{tag}", log_severity=1,
                               runs=10))
    for phase in ("cold", "warm"):
        d = str(CACHE / "ovcache0" / "rtmw_b1_fp32")
        J["O9"].append(job("O9", "ov", "rtmw", 1, "fp32", lc0("GPU.0", {"CACHE_DIR": d}), suffix=f"GPU.0-cache-{phase}",
                           runs=5, log_severity=1, clear_dirs=[d] if phase == "cold" else [], check_dir=d))
    for r in ("O2", "O3", "O4", "O5", "O6"):  # same rows, load_config keyed by "GPU.0"
        rg = r + "g"
        J[rg] = []
        for j in J[r]:
            k = json.loads(j["provider_options"]["load_config"])
            g = json.loads(json.dumps(k["GPU"]).replace("ovcache", "ovcacheg"))
            jj = json.loads(json.dumps(j))
            jj["provider_options"] = {"load_config": json.dumps({"GPU.0": g})}
            jj["row"], jj["id"] = rg, rg + jj["id"][len(r):]
            jj["clear_dirs"] = [x.replace("ovcache", "ovcacheg") for x in jj.get("clear_dirs", [])]
            if jj.get("check_dir"):
                jj["check_dir"] = jj["check_dir"].replace("ovcache", "ovcacheg")
            J[rg].append(jj)
    J["O8"] = grid("O8", "ov", {}, batches=(1,), cfg={"session.disable_cpu_ep_fallback": "1"}, runs=5)
    # ---- CPU
    fp32 = {"precs": ("fp32",)}
    J["P1"] = (grid("P1", "cpu", None, attrs={"graph_optimization_level": "ORT_ENABLE_EXTENDED"}, suffix="EXTENDED", **fp32)
               + grid("P1", "cpu", None, attrs={"graph_optimization_level": "ORT_ENABLE_BASIC"}, suffix="BASIC", **fp32))
    J["P2"] = grid("P2", "cpu", None, cfg={"session.dynamic_block_base": "4"}, **fp32)
    J["P3"] = []
    for t in ("1", "8", "20"):
        J["P3"] += grid("P3", "cpu", None, attrs={"intra_op_num_threads": t}, suffix=f"t{t}", **fp32)
    J["P3"] += grid("P3", "cpu", None, cfg={"session.intra_op.allow_spinning": "0"}, suffix="spin0", **fp32)
    # ---- multi-camera simulation
    J["M"] = []
    for tname, attrs in (("tdef", {}), ("t1", {"intra_op_num_threads": "1"})):
        for spin in ("1", "0"):
            J["M"].append(job("M", "cuda", "rtmw", 1, "fp32", {"use_tf32": "0"}, attrs=attrs,
                              cfg={"session.intra_op.allow_spinning": spin}, suffix=f"{tname}-spin{spin}",
                              mode="multicam", threads=3, frames=100))
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


def child_env(extra):
    env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME")}
    env.update(extra)
    return env


def run_one(j, nvml):
    safe = j["id"].replace("|", "__")
    if j.get("requires_file") and not Path(j["requires_file"]).exists():
        return {"ok": False, "skipped": f"missing {Path(j['requires_file']).name} (write step made no file)"}
    if j.get("model_override"):
        j["model"] = j["model_override"]
    for d in j.get("clear_dirs", []):
        shutil.rmtree(d, ignore_errors=True)
        Path(d).mkdir(parents=True, exist_ok=True)
    for f in j.get("clear_files", []):
        p = Path(f)
        if p.is_file():
            p.unlink()
    for stem in j.get("clear_prefix", []):
        for p in Path(CACHE / "ctx").glob(stem + "*"):
            p.unlink()
    j["result"] = str(JOBS / f"{safe}.result.json")
    jf = JOBS / f"{safe}.json"
    jf.write_text(json.dumps(j, indent=1), encoding="utf-8")
    Path(j["result"]).unlink(missing_ok=True)
    log = LOGS / f"{safe}.log"
    before = {p.name for p in Path(j["check_dir"]).glob("*")} if j.get("check_dir") and Path(j["check_dir"]).exists() else set()
    gpu = j["env"] in ("cuda", "trt")
    t0 = time.perf_counter()
    rec = {}
    with Sampler(nvml if gpu else None) as s, open(log, "w", encoding="utf-8", errors="replace") as lf:
        try:
            proc = subprocess.run([str(PY[j["env"]]), "-I", "-B", str(SCRIPTS / "child.py"), str(jf)],  # noqa: S603
                                  stdout=lf, stderr=subprocess.STDOUT, env=child_env(j.get("env_vars", {})),
                                  timeout=TIMEOUT, cwd=str(ROOT))
            rec["exit_code"] = proc.returncode
        except subprocess.TimeoutExpired:
            rec["exit_code"] = None
            rec["timeout"] = True
    rec["wall_s"] = round(time.perf_counter() - t0, 2)
    rec["vram_peak_mb"] = round(s.peak - s.base) if gpu and nvml else None
    rec["vram_base_mb"] = round(s.base) if gpu and nvml else None
    try:
        rec.update(json.loads(Path(j["result"]).read_text(encoding="utf-8")))
    except Exception as exc:  # noqa: BLE001
        rec["ok"] = False
        rec["error"] = rec.get("error") or f"no result file ({type(exc).__name__}); exit {rec.get('exit_code')}"
    text = log.read_text(encoding="utf-8", errors="replace")
    rec["log_tail"] = text[-1500:]
    rec["log_bytes"] = len(text)
    if j.get("log_grep"):
        keys = [k.lower() for k in j["log_grep"]]
        rec["log_hits"] = [ln[:400] for ln in text.splitlines() if any(k in ln.lower() for k in keys)][:25]
    if j.get("check_dir"):
        d = Path(j["check_dir"])
        after = {p.name: p.stat().st_size for p in d.glob("*")} if d.exists() else {}
        rec["dir_after"] = {"files": len(after), "bytes": sum(after.values()),
                            "new": sorted(set(after) - before)[:10]}
    return rec


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force, dry = "--force" in sys.argv, "--dry" in sys.argv
    J = matrix()
    rows = []
    for a in args:
        rows += [r for r in J if r == a] or [r for r in J if r.startswith(a) and r != "REF"]
    for d in (JOBS, LOGS, CACHE / "refs", CACHE / "ctx"):
        d.mkdir(parents=True, exist_ok=True)
    try:
        nvml = Nvml()
    except OSError:
        nvml = None
    done = set() if force else done_ids()
    for r in rows:
        for j in J[r]:
            if j["id"] in done:
                continue
            if dry:
                print(j["id"], j["provider_options"], j["session_config"], j["session_attrs"])
                continue
            jj = dict(j)
            rec = run_one(jj, nvml)
            line = {"id": j["id"], "job": jj, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), **rec}
            with open(JSONL, "a", encoding="utf-8") as f:
                f.write(json.dumps(line, default=str) + "\n")
            t = rec.get("timing") or {}
            c = rec.get("compare") or {}
            print(f"{j['id']:<44} ok={rec.get('ok')} build={rec.get('build_ms')} med={t.get('median_ms')} "
                  f"rel={c.get('max_rel')} vram={rec.get('vram_peak_mb')} wall={rec.get('wall_s')} "
                  f"{(rec.get('error') or rec.get('skipped') or '')[:160]}", flush=True)


if __name__ == "__main__":
    main()

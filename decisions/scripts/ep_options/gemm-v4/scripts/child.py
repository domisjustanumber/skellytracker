"""Run one CUDA plugin configuration in a fresh process. Usage: python -I -B child.py JOB.json

Adapted from the ep-options-evidence child: PATH prepend of the NVIDIA wheel DLL folders,
register_execution_provider_library, device pick by EP name and NVIDIA vendor id,
add_provider_for_devices, session.record_ep_graph_assignment_info node assignment, timing.
"""
import hashlib
import importlib
import json
import os
import statistics
import sys
import sysconfig
import time
import traceback
from pathlib import Path

JOB = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
OUT = Path(JOB["result"])
R: dict = {"steps": []}
PURELIB = Path(sysconfig.get_paths()["purelib"])
PROBE_KEYS = ["enable_gemm_auto_tune", "ep.cuda.enable_gemm_auto_tune",
              "ep.cudaexecutionprovider.enable_gemm_auto_tune", "ep.CUDAExecutionProvider.enable_gemm_auto_tune",
              "session.use_deterministic_compute"]


def save():
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(R, indent=1, default=str), encoding="utf-8")
    tmp.replace(OUT)


def ms(t0):
    return round(1000 * (time.perf_counter() - t0), 2)


def err(exc):
    return f"{type(exc).__name__}: {str(exc)[:2500]}"


def prepare_libraries():
    root = PURELIB / "nvidia"
    if root.is_dir():
        dirs = sorted({str(p.parent) for p in root.rglob("*.dll")})
        os.environ["PATH"] = os.pathsep.join([*dirs, os.environ.get("PATH", "")])


def register(ort):
    mod = importlib.import_module("onnxruntime_ep_cuda")
    name, lib = mod.get_ep_name(), str(Path(mod.get_library_path()).resolve())
    ort.register_execution_provider_library(name, lib)
    R["ep_name"] = name
    return name


def select_device(ort, ep_name):
    for dev in ort.get_ep_devices():
        if dev.ep_name == ep_name and dev.device.vendor_id == 0x10DE:
            R["device"] = {"desc": dict(dev.device.metadata).get("Description", ""),
                           "ep_metadata": dict(dev.ep_metadata), "ep_options": dict(dev.ep_options)}
            return dev
    raise RuntimeError(f"no {ep_name} NVIDIA device")


def session_options(ort, dev):
    so = ort.SessionOptions()
    so.log_severity_level = JOB.get("log_severity", 2)
    so.log_verbosity_level = 0
    if JOB.get("deterministic"):
        so.use_deterministic_compute = True  # the attribute, not a config entry
    R["use_deterministic_compute_attr"] = so.use_deterministic_compute
    so.add_session_config_entry("session.record_ep_graph_assignment_info", "1")
    for k, v in JOB.get("session_config", {}).items():
        so.add_session_config_entry(k, str(v))
    so.add_provider_for_devices([dev], {k: str(v) for k, v in JOB.get("provider_options", {}).items()})
    seen = {}
    for k in PROBE_KEYS:
        try:
            v = so.get_session_config_entry(k)
            if v != "":
                seen[k] = v
        except Exception as exc:  # noqa: BLE001
            seen[k] = "ERR " + err(exc)[:80]
    R["config_entries_after_add"] = seen
    return so


def assignment(session):
    per_ep = {}
    for item in session.get_provider_graph_assignment_info():
        rec = per_ep.setdefault(item.ep_name, {"nodes": 0, "op_types": set()})
        for node in item.get_nodes():
            rec["nodes"] += 1
            rec["op_types"].add(node.op_type)
    return {ep: {"nodes": r["nodes"], "op_types": sorted(r["op_types"])} for ep, r in per_ep.items()}


def sha(np, outs):
    h = hashlib.sha256()
    for x in outs:
        h.update(np.ascontiguousarray(np.asarray(x)).tobytes())
    return h.hexdigest()


def compare(np, names, outs, refs):
    per = {}
    for name, out in zip(names, outs, strict=False):
        ref = refs[name].astype(np.float64)
        o = np.asarray(out).astype(np.float64)
        d = np.abs(o - ref)
        scale = float(np.abs(ref).max())
        per[name] = {"max_abs": float(d.max()), "ref_max_abs": scale,
                     "max_rel_to_range": float(d.max() / scale) if scale else None,
                     "max_rel_elementwise": float((d / np.maximum(np.abs(ref), 1e-6)).max()),
                     "bit_identical": bool(np.array_equal(np.asarray(out), refs[name]))}
    rx, ry = refs["simcc_x"], refs["simcc_y"]
    o = dict(zip(names, outs, strict=False))
    cx, cy = np.asarray(o["simcc_x"]), np.asarray(o["simcc_y"])
    dx = np.abs(rx.argmax(-1) - cx.argmax(-1))
    dy = np.abs(ry.argmax(-1) - cy.argmax(-1))
    flip = (dx > 0) | (dy > 0)
    conf = np.minimum(rx.max(-1), ry.max(-1))
    top = conf >= np.median(conf)
    split = JOB.get("simcc_split", 2.0)
    dec = {"kpts": int(flip.size), "argmax_flips": int(flip.sum()),
           "max_px_shift": float(max(dx.max(), dy.max()) / split),
           "argmax_flips_tophalf_conf": int((flip & top).sum()),
           "max_px_shift_tophalf_conf": float(max(dx[top].max(initial=0), dy[top].max(initial=0)) / split)}
    return per, dec


def timed_runs(fn, warmup, runs):
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        times.append(1000 * (time.perf_counter() - t0))
    times.sort()
    return {"warmup": warmup, "runs": runs, "median_ms": round(statistics.median(times), 3),
            "p95_ms": round(times[min(len(times) - 1, int(round(0.95 * (len(times) - 1))))], 3),
            "min_ms": round(times[0], 3), "max_ms": round(times[-1], 3)}


def main():
    R["job_id"] = JOB["id"]
    try:
        prepare_libraries()
        import numpy as np
        import onnxruntime as ort
        ort.set_default_logger_severity(JOB.get("log_severity", 2))
        R["ort_version"] = ort.__version__
        dev = select_device(ort, register(ort))
        R["steps"].append("device")
        so = session_options(ort, dev)
        t0 = time.perf_counter()
        session = ort.InferenceSession(JOB["model"], sess_options=so)
        R["build_ms"] = ms(t0)
        R["steps"].append("build")
        R["providers"] = session.get_providers()
        R["assignment"] = assignment(session)
        R["cpu_nodes"] = R["assignment"].get("CPUExecutionProvider", {}).get("nodes", 0)
        save()
        x = np.load(JOB["input"])
        feed = {session.get_inputs()[0].name: x}
        names = [o.name for o in session.get_outputs()]
        t0 = time.perf_counter()
        outs = session.run(None, feed)
        R["first_run_ms"] = ms(t0)
        R["out_sha256"] = sha(np, outs)
        R["nan"] = int(sum(np.isnan(o).sum() for o in outs))
        if JOB.get("save_out"):
            np.savez(JOB["save_out"], **dict(zip(names, outs, strict=False)))
        if JOB.get("ref") and Path(JOB["ref"]).exists():
            refs = dict(np.load(JOB["ref"]))
            R["vs_baseline"], R["decoded_vs_baseline"] = compare(np, names, outs, refs)
        R["steps"].append("first_run")
        save()
        if JOB.get("runs", 30):
            R["timing"] = timed_runs(lambda: session.run(None, feed), JOB.get("warmup", 5), JOB.get("runs", 30))
            R["steps"].append("timed")
            outs2 = session.run(None, feed)
            R["repeat_identical_after_timed"] = sha(np, outs2) == R["out_sha256"]
        R["ok"] = True
    except Exception as exc:  # noqa: BLE001
        R["ok"] = False
        R["error"] = err(exc)
        R["traceback"] = traceback.format_exc()[-2000:]
    save()
    return 0


if __name__ == "__main__":
    sys.exit(main())

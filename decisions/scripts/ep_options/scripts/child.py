"""Run one EP option configuration in a fresh process. Usage: python -I -B child.py JOB.json

Logic copied (not imported) from the device-check suite route_check.py: PATH prepend of the NVIDIA
wheel library folders, register_execution_provider_library, device pick by EP name and vendor,
add_provider_for_devices, and node assignment via session.record_ep_graph_assignment_info.
The result JSON is written after each step, so a crash keeps the steps before it.
"""
import hashlib
import importlib
import json
import os
import statistics
import sys
import sysconfig
import threading
import time
import traceback
from pathlib import Path

JOB = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
OUT = Path(JOB["result"])
R: dict = {"steps": []}
PURELIB = Path(sysconfig.get_paths()["purelib"])


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
    plugin = JOB.get("module")
    if not plugin:
        return "CPUExecutionProvider"
    mod = importlib.import_module(plugin)
    name, lib = mod.get_ep_name(), str(Path(mod.get_library_path()).resolve())
    t0 = time.perf_counter()
    ort.register_execution_provider_library(name, lib)
    R["register_ms"] = ms(t0)
    R["ep_library"] = Path(lib).name
    return name


def select_device(ort, ep_name):
    want = JOB["select"]
    found = []
    for dev in ort.get_ep_devices():
        if dev.ep_name != ep_name:
            continue
        hw = dev.device
        found.append({"type": str(hw.type).rsplit(".", 1)[-1], "vendor_id": hex(hw.vendor_id),
                      "desc": dict(hw.metadata).get("Description", ""),
                      "ep_options": dict(dev.ep_options)})
        ok = True
        if "vendor_id" in want and hw.vendor_id != want["vendor_id"]:
            ok = False
        if "type" in want and not str(hw.type).endswith(want["type"]):
            ok = False
        if ok:
            R["devices_seen"] = found
            R["device"] = found[-1]
            return dev
    R["devices_seen"] = found
    raise RuntimeError(f"no {ep_name} device matches {want}")


def session_options(ort, dev):
    so = ort.SessionOptions()
    so.log_severity_level = JOB.get("log_severity", 2)
    so.log_verbosity_level = 0
    attrs = JOB.get("session_attrs", {})
    if "graph_optimization_level" in attrs:
        so.graph_optimization_level = getattr(ort.GraphOptimizationLevel, attrs["graph_optimization_level"])
    for key in ("intra_op_num_threads", "inter_op_num_threads"):
        if key in attrs:
            setattr(so, key, int(attrs[key]))
    so.add_session_config_entry("session.record_ep_graph_assignment_info", "1")
    for k, v in JOB.get("session_config", {}).items():
        so.add_session_config_entry(k, str(v))
    if dev is not None:
        so.add_provider_for_devices([dev], {k: str(v) for k, v in JOB.get("provider_options", {}).items()})
    return so


def build(ort, dev, model):
    so = session_options(ort, dev)
    t0 = time.perf_counter()
    if dev is None:
        s = ort.InferenceSession(model, sess_options=so, providers=["CPUExecutionProvider"])
    else:
        s = ort.InferenceSession(model, sess_options=so)
    return s, ms(t0)


def assignment(session):
    per_ep = {}
    for item in session.get_provider_graph_assignment_info():
        rec = per_ep.setdefault(item.ep_name, {"nodes": 0, "op_types": set()})
        for node in item.get_nodes():
            rec["nodes"] += 1
            rec["op_types"].add(node.op_type)
    return {ep: {"nodes": r["nodes"], "op_types": sorted(r["op_types"])} for ep, r in per_ep.items()}


def compare(np, names, outs, refs):
    rec = {"nan": 0, "inf": 0, "per_output": {}}
    for name, out in zip(names, outs, strict=False):
        out = np.asarray(out)
        rec["nan"] += int(np.isnan(out).sum())
        rec["inf"] += int(np.isinf(out).sum())
        if refs is None or name not in refs:
            continue
        ref = refs[name]
        if out.shape != ref.shape:
            rec["per_output"][name] = {"shape": list(out.shape), "ref_shape": list(ref.shape)}
            continue
        d = float(np.nanmax(np.abs(out.astype(np.float64) - ref.astype(np.float64))))
        scale = float(np.max(np.abs(ref.astype(np.float64))))
        rec["per_output"][name] = {"max_abs": d, "ref_max_abs": scale, "rel": d / scale if scale else None}
    if rec["per_output"]:
        vals = [v for v in rec["per_output"].values() if "max_abs" in v]
        if vals:
            rec["max_abs"] = max(v["max_abs"] for v in vals)
            rec["max_rel"] = max(v["rel"] or 0 for v in vals)
    return rec


def decode(np, key, names, outs, refs):
    if refs is None:
        return {}
    o = dict(zip(names, [np.asarray(x) for x in outs], strict=False))
    if key == "rtmw":
        rx, ry, cx, cy = refs["simcc_x"], refs["simcc_y"], o["simcc_x"], o["simcc_y"]
        ax_r, ay_r, ax_c, ay_c = rx.argmax(-1), ry.argmax(-1), cx.argmax(-1), cy.argmax(-1)
        conf = np.minimum(rx.max(-1), ry.max(-1))
        top = conf >= np.median(conf)
        dx, dy = np.abs(ax_r - ax_c), np.abs(ay_r - ay_c)
        flip = (dx > 0) | (dy > 0)
        return {"kpts": int(flip.size), "flips_x": int((dx > 0).sum()), "flips_y": int((dy > 0).sum()),
                "flips_any": int(flip.sum()), "flips_any_tophalf": int((flip & top).sum()),
                "max_px_err": float(max(dx.max(), dy.max()) / 2.0),
                "max_px_err_tophalf": float(max(dx[top].max(initial=0), dy[top].max(initial=0)) / 2.0)}
    if key == "yolox":
        rs, cs, rb, cb = refs["scores"], o["scores"], refs["boxes"], o["boxes"]
        mask = rs > 0.3
        box = float(np.abs(rb[mask].astype(np.float64) - cb[mask]).max()) if mask.any() else None
        return {"det_ref": int(mask.sum()), "det_cfg": int((cs > 0.3).sum()),
                "det_both": int((mask & (cs > 0.3)).sum()), "max_box_px": box,
                "max_score_diff_on_det": float(np.abs(rs[mask] - cs[mask]).max()) if mask.any() else None}
    return {}


def timed_runs(fn, warmup, runs):
    for _ in range(warmup):
        fn()
    times = []
    c0 = time.process_time()
    w0 = time.perf_counter()
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        times.append(1000 * (time.perf_counter() - t0))
    wall = time.perf_counter() - w0
    cpu = time.process_time() - c0
    times.sort()
    return {"runs": runs, "median_ms": round(statistics.median(times), 3),
            "p95_ms": round(times[min(len(times) - 1, int(round(0.95 * (len(times) - 1))))], 3),
            "min_ms": round(times[0], 3), "cpu_ms_per_run": round(1000 * cpu / runs, 3),
            "cpu_util": round(cpu / wall, 3) if wall else None}


def sha(np, outs):
    h = hashlib.sha256()
    for x in outs:
        h.update(np.ascontiguousarray(np.asarray(x)).tobytes())
    return h.hexdigest()


def finish_outputs(np, ort, session, outs):
    names = [o.name for o in session.get_outputs()]
    refs = None
    if JOB.get("ref") and Path(JOB["ref"]).exists():
        refs = dict(np.load(JOB["ref"]))
    if JOB.get("save_ref"):
        np.savez(JOB["save_ref"], **{n: np.asarray(o) for n, o in zip(names, outs, strict=False)})
    R["compare"] = compare(np, names, outs, refs)
    R["decoded"] = decode(np, JOB["model_key"], names, outs, refs)
    R["out_sha256"] = sha(np, outs)


def mode_standard(np, ort, dev):
    session, R["build_ms"] = build(ort, dev, JOB["model"])
    R["steps"].append("build")
    R["providers"] = session.get_providers()
    try:
        R["assignment"] = assignment(session)
    except Exception as exc:  # noqa: BLE001
        R["assignment_error"] = err(exc)
    save()
    x = np.load(JOB["input"])
    feed = {session.get_inputs()[0].name: x}
    t0 = time.perf_counter()
    outs = session.run(None, feed)
    R["first_run_ms"] = ms(t0)
    R["steps"].append("first_run")
    finish_outputs(np, ort, session, outs)
    save()
    if JOB.get("runs", 30):
        R["timing"] = timed_runs(lambda: session.run(None, feed), JOB.get("warmup", 5), JOB.get("runs", 30))
        R["steps"].append("timed")
        save()
        # a second output check after the timed runs (catches drift, e.g. cuda graph replay issues)
        outs2 = session.run(None, feed)
        R["repeat_identical"] = sha(np, outs2) == R["out_sha256"]


def device_value(np, ort, dev, shape, attempts):
    """Allocate a float32 OrtValue on the EP device. Try several API forms; record each error."""
    forms = [
        ("memory_info_default", lambda: ort.OrtValue.ortvalue_from_shape_and_type(
            shape, np.float32, memory_info=dev.memory_info(ort.OrtDeviceMemoryType.DEFAULT))),
        ("gpu_vendor", lambda: ort.OrtValue.ortvalue_from_shape_and_type(
            shape, np.float32, "gpu", 0, dev.device.vendor_id)),
        ("cuda_name", lambda: ort.OrtValue.ortvalue_from_shape_and_type(shape, np.float32, "cuda", 0)),
    ]
    for name, fn in forms:
        try:
            v = fn()
            attempts.append({"form": name, "ok": True, "device": v.device_name()})
            return v
        except Exception as exc:  # noqa: BLE001
            attempts.append({"form": name, "ok": False, "error": err(exc)})
    raise RuntimeError("no form could allocate device memory: " + json.dumps(attempts)[:2000])


def mode_iobind(np, ort, dev):
    session, R["build_ms"] = build(ort, dev, JOB["model"])
    R["steps"].append("build")
    R["providers"] = session.get_providers()
    R["assignment"] = assignment(session)
    save()
    x = np.load(JOB["input"])
    attempts = R.setdefault("alloc_attempts", [])
    x_dev = device_value(np, ort, dev, list(x.shape), attempts)
    x_cpu = ort.OrtValue.ortvalue_from_numpy(x)
    ort.copy_tensors([x_cpu], [x_dev])
    R["steps"].append("input_on_device")
    outs_meta = session.get_outputs()
    o_dev = [device_value(np, ort, dev, list(o.shape), attempts) for o in outs_meta]
    o_cpu = [ort.OrtValue.ortvalue_from_shape_and_type(list(o.shape), np.float32) for o in outs_meta]
    io = session.io_binding()
    io.bind_ortvalue_input(session.get_inputs()[0].name, x_dev)
    for meta, v in zip(outs_meta, o_dev, strict=False):
        io.bind_ortvalue_output(meta.name, v)
    R["steps"].append("bound")
    save()

    def run_only():
        session.run_with_iobinding(io)
        io.synchronize_outputs()

    def run_e2e():
        ort.copy_tensors([x_cpu], [x_dev])
        session.run_with_iobinding(io)
        io.synchronize_outputs()
        ort.copy_tensors(o_dev, o_cpu)

    t0 = time.perf_counter()
    run_e2e()
    R["first_run_ms"] = ms(t0)
    R["steps"].append("first_run")
    t0 = time.perf_counter()
    run_e2e()
    R["second_run_ms"] = ms(t0)  # cuda graph capture is often on the 2nd run
    outs = [v.numpy().copy() for v in o_cpu]
    finish_outputs(np, ort, session, outs)
    save()
    R["timing"] = timed_runs(run_e2e, JOB.get("warmup", 5), JOB.get("runs", 30))
    R["timing_run_only"] = timed_runs(run_only, 2, JOB.get("runs", 30))
    R["steps"].append("timed")
    run_e2e()
    outs2 = [v.numpy().copy() for v in o_cpu]
    R["repeat_identical"] = sha(np, outs2) == R["out_sha256"]
    # change the input in place: does the graph replay see the new data?
    x2 = np.ascontiguousarray(x[::-1].copy()) if x.shape[0] > 1 else np.ascontiguousarray(x[..., ::-1])
    x_cpu = ort.OrtValue.ortvalue_from_numpy(x2)
    run_e2e()
    outs3 = [v.numpy().copy() for v in o_cpu]
    R["new_input_changed_output"] = bool(max(np.abs(a - b).max() for a, b in zip(outs3, outs, strict=False)) > 0)
    try:  # CPU EP outputs for the changed input (fp32 model of the same batch when the job names one)
        cpu_s = ort.InferenceSession(JOB.get("cpu_model", JOB["model"]), providers=["CPUExecutionProvider"])
        refn = cpu_s.run(None, {cpu_s.get_inputs()[0].name: x2})
        R["new_input_max_abs_vs_cpu"] = float(max(np.abs(a - b).max() for a, b in zip(outs3, refn, strict=False)))
        R["new_input_rel_vs_cpu"] = float(max(np.abs(a - b).max() / np.abs(b).max() for a, b in zip(outs3, refn, strict=False)))
    except Exception as exc:  # noqa: BLE001
        R["cpu_check_error"] = err(exc)
    try:
        ref_new = session.run(None, {session.get_inputs()[0].name: x2})
        R["plain_run_outputs"] = len(ref_new)
        R["new_input_max_abs_vs_plain_run"] = float(max(np.abs(a - b).max() for a, b in zip(outs3, ref_new, strict=False)))
    except Exception as exc:  # noqa: BLE001
        R["plain_run_after_graph_error"] = err(exc)
    save()


def mode_multicam(np, ort, dev):
    n, frames = JOB.get("threads", 3), JOB.get("frames", 100)
    sessions = []
    builds = []
    for _ in range(n):
        s, b = build(ort, dev, JOB["model"])
        sessions.append(s)
        builds.append(b)
    R["build_ms_each"] = builds
    R["assignment"] = assignment(sessions[0])
    x = np.load(JOB["input"])
    name = sessions[0].get_inputs()[0].name
    for s in sessions:  # warm each
        for _ in range(5):
            s.run(None, {name: x})
    outs = sessions[0].run(None, {name: x})
    finish_outputs(np, ort, sessions[0], outs)
    save()
    barrier = threading.Barrier(n + 1)
    lat = [[] for _ in range(n)]
    errors = []

    def worker(i):
        try:
            barrier.wait()
            for _ in range(frames):
                t0 = time.perf_counter()
                sessions[i].run(None, {name: x})
                lat[i].append(1000 * (time.perf_counter() - t0))
        except Exception as exc:  # noqa: BLE001
            errors.append(err(exc))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    c0 = time.process_time()
    barrier.wait()
    w0 = time.perf_counter()
    for t in threads:
        t.join()
    wall = time.perf_counter() - w0
    cpu = time.process_time() - c0
    allv = sorted(v for lst in lat for v in lst)
    R["multicam"] = {"threads": n, "frames_each": frames, "wall_s": round(wall, 3),
                     "total_fps": round(n * frames / wall, 2), "cpu_s": round(cpu, 3),
                     "cpu_ms_per_frame": round(1000 * cpu / (n * frames), 3),
                     "cpu_util": round(cpu / wall, 3),
                     "median_ms": round(statistics.median(allv), 3) if allv else None,
                     "p95_ms": round(allv[int(0.95 * (len(allv) - 1))], 3) if allv else None,
                     "errors": errors}
    save()


def main():
    R["job_id"] = JOB["id"]
    try:
        prepare_libraries()
        import numpy as np
        import onnxruntime as ort
        ort.set_default_logger_severity(JOB.get("log_severity", 2))
        R["ort_version"] = ort.__version__
        ep = register(ort)
        dev = None if ep == "CPUExecutionProvider" else select_device(ort, ep)
        R["steps"].append("device")
        save()
        mode = JOB.get("mode", "standard")
        {"standard": mode_standard, "iobind": mode_iobind, "multicam": mode_multicam}[mode](np, ort, dev)
        for f in JOB.get("check_files", []):
            p = Path(f)
            R.setdefault("files", {})[p.name] = p.stat().st_size if p.exists() else None
        R["ok"] = True
    except Exception as exc:  # noqa: BLE001
        R["ok"] = False
        R["error"] = err(exc)
        R["traceback"] = traceback.format_exc()[-2000:]
        for f in JOB.get("check_files", []):
            p = Path(f)
            R.setdefault("files", {})[p.name] = p.stat().st_size if p.exists() else None
    save()
    return 0


if __name__ == "__main__":
    sys.exit(main())

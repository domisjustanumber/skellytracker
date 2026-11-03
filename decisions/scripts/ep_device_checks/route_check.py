"""Run one check of one EP route. It runs in the environment of that route, in its own process.

Usage: ``python -I -B route_check.py JOB.json``. ``run_checks.py`` writes the job and runs this file.

Stage ``l2l3``: register the plugin by its absolute library path, find the target device in
``get_ep_devices()`` (L2), then run the probe model and compare it with the CPU EP (L3).
Stage ``l4``: register, then build one real model on the device, run it and compare it with the
reference outputs of ``prep_assets.py``.

The child writes its result JSON after each step, so a crash keeps the steps before it.
Each session uses ``add_provider_for_devices``, ``session.record_ep_graph_assignment_info=1`` and,
unless the job allows the fallback, ``session.disable_cpu_ep_fallback=1``.
"""

from __future__ import annotations

import importlib
import json
import os
import re
import statistics
import sys
import sysconfig
import time
from pathlib import Path

JOB = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
RESULT: dict = {"stage": JOB["stage"], "allow_fallback": JOB["allow_fallback"]}
OUT = Path(JOB["result"])
PURELIB = Path(sysconfig.get_paths()["purelib"])
NOT_IDS = ("luid", "uuid", "serial", "bus", "pci")  # metadata keys that the report must not hold


def save() -> None:
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(RESULT, indent=1, default=str), encoding="utf-8")
    tmp.replace(OUT)


def ms_since(start: float) -> float:
    return round(1000 * (time.perf_counter() - start), 1)


def error_text(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {str(exc)[:1500]}"


def nvidia_lib_dirs() -> list[Path]:
    """Each folder under site-packages/nvidia that holds a shared library of the NVIDIA wheels."""
    root = PURELIB / "nvidia"
    pattern = "*.dll" if os.name == "nt" else "*.so*"
    return sorted({p.parent for p in root.rglob(pattern)}) if root.is_dir() else []


def prepare_libraries() -> None:
    """Windows: prepend the folders to PATH (os.add_dll_directory does not work for these packs).

    Linux: start this process again with LD_LIBRARY_PATH, because the loader reads it only at the
    start of a process. UNVERIFIED on Linux.
    """
    dirs = [str(d) for d in nvidia_lib_dirs()]
    RESULT["library_dirs"] = [Path(d).relative_to(PURELIB).as_posix() for d in dirs]
    if not dirs:
        return
    if os.name == "nt":
        os.environ["PATH"] = os.pathsep.join([*dirs, os.environ.get("PATH", "")])
    elif os.environ.get("EPDC_LD_SET") != "1":
        env = dict(os.environ, EPDC_LD_SET="1")
        env["LD_LIBRARY_PATH"] = os.pathsep.join([*dirs, env.get("LD_LIBRARY_PATH", "")])
        os.execve(sys.executable, [sys.executable, "-I", "-B", *sys.argv], env)  # noqa: S606


def longest_path(module_dir: Path) -> int:
    paths = [module_dir, PURELIB / "nvidia"]
    return max((len(str(p)) for d in paths if d.is_dir() for p in d.rglob("*")), default=0)


def register(ort) -> tuple[str, str | None]:
    """Register the plugin. Return the EP name and the library path (None for the built-in CPU EP)."""
    plugin = JOB.get("module")
    if not plugin:
        return "CPUExecutionProvider", None
    module = importlib.import_module(plugin)
    name, lib = module.get_ep_name(), str(Path(module.get_library_path()).resolve())
    RESULT["l2"]["library"] = Path(lib).name
    if os.name == "nt":
        length = longest_path(Path(module.__file__).parent)
        RESULT["l2"]["longest_path_chars"] = length
        if length >= JOB["path_limit"]:
            raise RuntimeError(f"path guard: a pack file path has {length} characters (limit "
                               f"{JOB['path_limit']}); use a shorter --work folder")
    start = time.perf_counter()
    ort.register_execution_provider_library(name, lib)
    RESULT["l2"]["register_ms"] = ms_since(start)
    return name, lib


def device_record(dev) -> dict:
    hw = dev.device
    meta = {k: v for k, v in dict(dev.ep_metadata).items() if not any(t in k.lower() for t in NOT_IDS)}
    return {"ep_name": dev.ep_name, "type": str(hw.type).rsplit(".", 1)[-1],
            "vendor_id": f"{hw.vendor_id:#06x}", "device_id": f"{hw.device_id:#06x}",
            "description": dict(hw.metadata).get("Description", ""), "ep_metadata": meta}


def select_device(ort, ep_name: str):
    devices = list(ort.get_ep_devices())
    RESULT["l2"]["devices"] = [device_record(d) for d in devices if d.ep_name == ep_name]
    want = JOB["select"]
    for dev in devices:
        if dev.ep_name != ep_name:
            continue
        if "vendor_id" in want and dev.device.vendor_id == want["vendor_id"]:
            return dev
        if "type" in want and str(dev.device.type).endswith(want["type"]):
            return dev
    raise RuntimeError(f"no device: get_ep_devices() lists no {ep_name} device that matches {want}")


def make_session(ort, dev, model: str):
    opts = ort.SessionOptions()
    opts.log_severity_level = 3
    opts.add_provider_for_devices([dev], {})
    if dev.ep_name != "CPUExecutionProvider":  # ORT refuses this entry when the CPU EP is the target
        opts.add_session_config_entry("session.disable_cpu_ep_fallback", "0" if JOB["allow_fallback"] else "1")
    opts.add_session_config_entry("session.record_ep_graph_assignment_info", "1")
    start = time.perf_counter()
    session = ort.InferenceSession(model, sess_options=opts)
    return session, ms_since(start)


def assignment(session) -> dict:
    """Node counts per EP and the op types of each EP."""
    per_ep: dict = {}
    for item in session.get_provider_graph_assignment_info():
        rec = per_ep.setdefault(item.ep_name, {"nodes": 0, "op_types": set()})
        for node in item.get_nodes():
            rec["nodes"] += 1
            rec["op_types"].add(node.op_type)
    return {ep: {"nodes": r["nodes"], "op_types": sorted(r["op_types"])} for ep, r in per_ep.items()}


def failed_op(text: str) -> str | None:
    match = re.search(r"running (\w+) node", text) or re.search(r"for (\w+)\(\d+\) node", text)
    return match.group(1) if match else None


def compare(np, outputs: list, refs: list) -> dict:
    rec = {"nan": 0, "inf": 0, "max_abs_diff": None, "max_abs_ref": None, "shapes_match": True}
    diffs, scale = [], 0.0
    for out, ref in zip(outputs, refs, strict=True):
        out = np.asarray(out)
        if out.dtype.kind == "f":
            rec["nan"] += int(np.isnan(out).sum())
            rec["inf"] += int(np.isinf(out).sum())
        if out.shape != ref.shape:
            rec["shapes_match"] = False
            continue
        if out.size:
            diffs.append(float(np.max(np.abs(out.astype(np.float64) - ref.astype(np.float64)))))
            scale = max(scale, float(np.max(np.abs(ref.astype(np.float64)))))
    if diffs:
        rec["max_abs_diff"], rec["max_abs_ref"] = max(diffs), scale
    rec["out_shapes"] = [list(np.asarray(o).shape) for o in outputs]
    return rec


def run_l3(ort, np, dev) -> None:
    probe = JOB["probe"]
    x = np.load(probe["input"])
    ref = ort.InferenceSession(probe["model"], providers=["CPUExecutionProvider"]).run(None, {"x": x})
    l3 = RESULT["l3"] = {"atol": JOB["atol"]}
    save()
    session, l3["session_ms"] = make_session(ort, dev, probe["model"])
    l3["assignment"] = assignment(session)
    save()
    start = time.perf_counter()
    out = session.run(None, {"x": x})
    l3["first_run_ms"] = ms_since(start)
    l3.update(compare(np, out, ref))
    target = l3["assignment"].get(dev.ep_name, {}).get("op_types", [])
    others = [ep for ep in l3["assignment"] if ep != dev.ep_name]
    problems = []
    if not {"Conv", "Relu"} <= set(target):
        problems.append(f"Conv and Relu are not both on {dev.ep_name} (on it: {target})")
    if others:
        problems.append(f"nodes on other EPs: {others}")
    if l3["max_abs_diff"] is None or l3["max_abs_diff"] > JOB["atol"] or l3["nan"] or l3["inf"]:
        problems.append(f"output differs from CPU: max_abs_diff {l3['max_abs_diff']} > atol {JOB['atol']}")
    l3["ok"] = not problems
    if problems:
        l3["reason"] = "; ".join(problems)


def run_l4(ort, np, dev) -> None:
    spec = JOB["model"]
    l4 = RESULT["l4"] = {"model": spec["key"], "precision": spec["precision"]}
    x = np.load(spec["input"])
    refs = list(np.load(spec["ref"]).values())
    save()
    session, l4["session_ms"] = make_session(ort, dev, spec["onnx"])
    l4["assignment"] = assignment(session)
    save()
    feed = {session.get_inputs()[0].name: x}
    start = time.perf_counter()
    out = session.run(None, feed)
    l4["first_run_ms"] = ms_since(start)
    save()
    times = []
    for _ in range(JOB["runs"]):
        start = time.perf_counter()
        session.run(None, feed)
        times.append(1000 * (time.perf_counter() - start))
    l4["runs"] = len(times)
    l4["median_ms"] = round(statistics.median(times), 2) if times else None
    l4.update(compare(np, out, refs))
    cpu = l4["assignment"].get("CPUExecutionProvider", {})
    l4["cpu_nodes"], l4["cpu_op_types"] = cpu.get("nodes", 0), cpu.get("op_types", [])
    l4["ok"] = not (l4["nan"] or l4["inf"])
    if not l4["ok"]:
        l4["reason"] = f"output has {l4['nan']} NaN and {l4['inf']} Inf values"


def main() -> int:
    stage = JOB["stage"]
    RESULT["l2"] = {"ok": False}
    try:
        prepare_libraries()
        import numpy as np
        import onnxruntime as ort

        RESULT["ort_version"] = ort.__version__
        ep_name, _ = register(ort)
        RESULT["l2"]["ep_name"] = ep_name
        dev = select_device(ort, ep_name)
        RESULT["l2"]["selected"] = device_record(dev)
        RESULT["l2"]["ok"] = True
        save()
    except Exception as exc:  # noqa: BLE001 - each failure is a recorded result
        RESULT["l2"]["reason"] = error_text(exc)
        save()
        return 0
    level = "l3" if stage == "l2l3" else "l4"
    try:
        run_l3(ort, np, dev) if stage == "l2l3" else run_l4(ort, np, dev)
    except Exception as exc:  # noqa: BLE001
        rec = RESULT.setdefault(level, {})
        rec["ok"], rec["reason"] = False, error_text(exc)
        rec["failed_op_type"] = failed_op(str(exc))
    save()
    return 0


if __name__ == "__main__":
    sys.exit(main())

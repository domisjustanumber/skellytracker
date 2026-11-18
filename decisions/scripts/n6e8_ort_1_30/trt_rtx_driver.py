"""Run each project model on the TRT-RTX wheel plugin with Windows ML ORT and with plain ORT, and compare. Usage: trt_rtx_driver.py ROOT REPO

ROOT holds `envs/winml` (`windowsml[with-ort]==2.6.74rc0`) and `envs/plain` (`onnxruntime==1.30.0`), each with
`onnxruntime-ep-nv-tensorrt-rtx-cu13==0.5.0` and numpy, and `scripts/trt_rtx_child.py`.

Each GPU job waits until no other python process is on the GPU. A CPU run of each model is the reference.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT, REPO = Path(sys.argv[1]), Path(sys.argv[2])
RES = ROOT / "results"
JOBS_DIR, OUTS, CACHE = RES / "jobs", RES / "outs", RES / "cache"
for folder in (JOBS_DIR, OUTS, CACHE):
    folder.mkdir(parents=True, exist_ok=True)
ZOO = REPO / "skellytracker" / "core" / "model_zoo" / "detectors"
RTMW, YOLOX = ZOO / "keypoint_detectors/rtmw/wholebody133", ZOO / "object_detectors/yolox-person"
ARMS = ["winml", "plain"]
JOBS = [("rtmw-m-fp32", RTMW / "rtmw-wholebody133-m_b3_fp32.onnx"), ("rtmw-m-fp16", RTMW / "rtmw-wholebody133-m_b3_fp16.onnx"),
        ("rtmw-x384-fp16", RTMW / "rtmw-wholebody133-x-384_b3_fp16.onnx"), ("yolox-m-fp32", YOLOX / "yolox-person-m_b3_fp32.onnx"),
        ("yolox-m-fp16", YOLOX / "yolox-person-m_b3_fp16.onnx")]
ATOL = 1.5e-2  # `l3_atol` of the EP catalog


def log(text):
    line = f"{time.strftime('%H:%M:%S')} {text}"
    print(line, flush=True)
    with (RES / "driver.log").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def wait_quiet(seconds, limit):
    start = quiet_since = time.time()
    while time.time() - quiet_since < seconds:
        text = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],  # noqa: S603, S607 - a fixed command
                              capture_output=True, text=True, check=True).stdout
        if any("python" in line.lower() for line in text.splitlines()):
            quiet_since = time.time()
        if time.time() - start > limit:
            return False
        time.sleep(5)
    return True


def run(arm, name, model, device):
    stem = f"{arm}__{name}__{device}"
    job, result = JOBS_DIR / f"{stem}.json", JOBS_DIR / f"{stem}.result.json"
    cache = CACHE / arm / name
    cache.mkdir(parents=True, exist_ok=True)
    job.write_text(json.dumps({"job": name, "arm": arm, "device": device, "model": str(model), "cache": str(cache),
                               "out": str(OUTS / f"{stem}.npz"), "result": str(result)}), encoding="utf-8")
    system = os.environ["SystemRoot"]
    env = {k: os.environ[k] for k in ("SystemRoot", "SystemDrive", "TEMP", "TMP", "USERPROFILE", "ProgramData", "ProgramFiles",
                                      "LOCALAPPDATA", "APPDATA", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE") if k in os.environ}
    env["PATH"] = os.pathsep.join([str(Path(system) / "System32"), system])
    try:
        done = subprocess.run([str(ROOT / "envs" / arm / "Scripts" / "python.exe"), "-I", "-B", str(ROOT / "scripts" / "trt_rtx_child.py"), str(job)],  # noqa: S603 - the paths of this run
                              cwd=RES, env=env, capture_output=True, text=True, errors="replace", timeout=1500)
        code, err = done.returncode, done.stderr
    except subprocess.TimeoutExpired as exc:
        code, err = "timeout", str(exc.stderr)
    row = json.loads(result.read_text(encoding="utf-8")) if result.exists() else {"job": name, "arm": arm, "device": device, "ok": False, "error": "no result file"}
    row.update(returncode=code, stderr_tail=err[-2000:])
    result.write_text(json.dumps(row, indent=1), encoding="utf-8")
    log(f"{arm:6} {name:16} {device:8} ok={row.get('ok')} rc={code} build={row.get('build_ms')} median={row.get('median_ms')} {row.get('error', '')[:200]}")
    return row


def max_abs(a, b):
    with np.load(a) as x, np.load(b) as y:
        return max(float(np.abs(x[k] - y[k]).max()) for k in x.files)


def main():
    if not wait_quiet(60, 3600):
        log("STOPPED: the GPU did not become quiet, so no GPU job ran")
        return 3
    summary = []
    for name, model in JOBS:
        cpu = run("winml", name, model, "cpu")
        rows = {}
        for arm in ARMS:
            wait_quiet(15, 1800)
            rows[arm] = run(arm, name, model, "trt-rtx")
            wait_quiet(5, 600)
            rows[arm + "-warm"] = run(arm, name, model, "trt-rtx")  # the second run reads the engine cache
        def out(arm, device="trt-rtx", name=name):
            return OUTS / f"{arm}__{name}__{device}.npz"

        both = all(rows[a].get("ok") for a in ARMS)
        w = rows["winml"]
        summary.append({
            "job": name, "cpu_ok": cpu.get("ok"), **{f"{a}_ok": rows[a].get("ok") for a in rows},
            **{f"{a}_error": rows[a].get("error", "")[:400] for a in rows if not rows[a].get("ok")},
            "winml_nodes": w.get("nodes"), "winml_devices_before": w.get("devices_before"), "winml_devices_after": w.get("devices_after"),
            "winml_ep_device_count": w.get("ep_device_count"), "winml_available_providers": w.get("available_providers"),
            "winml_modules_after_run": w.get("after_run"),
            "catalog_library_loaded": any(m.startswith("WindowsApps:") for m in w.get("after_run", [])),
            "winml_vs_cpu_max_abs": max_abs(out("winml"), out("winml", "cpu")) if w.get("ok") and cpu.get("ok") else None,
            "winml_vs_plain_max_abs": max_abs(out("winml"), out("plain")) if both else None,
            "bit_identical_winml_plain": w.get("sha256") == rows["plain"].get("sha256") if both else None,
            "atol": ATOL, "build_ms": {a: rows[a].get("build_ms") for a in rows}, "median_ms": {a: rows[a].get("median_ms") for a in rows}})
    (RES / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    log("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

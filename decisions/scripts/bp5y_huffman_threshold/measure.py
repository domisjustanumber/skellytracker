# Evidence of ADR-BP5Y. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Copy of s8_measure/measure.py for the hybrid_huffman_threshold=0 test: CPU blocks of 25 calls, peak VRAM, versions.

S8: one configuration of the built-in pipeline yolox-rtmw-wholebody, measured in one process.

Modes switch only by the input form and two module constants (no repo change):
  M0 array, CPU preprocess (GRAPH_EPS empty)      M1 array, GPU preprocess
  M2 JPEG, CPU decode (JPEG_DECODER_EPS empty)    M3 JPEG, GPU decode, GPU preprocess
  M2b JPEG, CPU decode, CPU preprocess (both empty)
Camera frames are read in place and never written. Output: one JSON summary and one .npz of results.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import statistics
import sys  # noqa: F401
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRAMES = Path(os.environ["JPEG_FRAMES_DIR"])
MAIN_ZOO = Path(os.environ["MAIN_MODEL_ZOO"])
ISO = HERE / "iso"
RES = {"720": "1280x720", "1080": "1920x1080"}
HOLD = 10  # calls that each camera keeps one still frame before the next frame of its cycle
HUFF_OPTION = " nvjpeg_cuda_decoder:hybrid_huffman_threshold=0"


def isolate(cache_dir: Path) -> None:
    """Hash cache, download folder, user root and EP cache in the scratchpad; model files read from the main checkout."""
    from skellytracker.core.detectors import catalog
    from skellytracker.core.eps import store
    from skellytracker.core.model_spec import artifacts
    from skellytracker.core.model_spec.landmark_schemas import PACKAGE_SIDECAR_ROOT

    (ISO / "user").mkdir(parents=True, exist_ok=True)
    os.environ[catalog.USER_ROOT_VARIABLE] = str(ISO / "user")
    artifacts.default_hash_cache_path = lambda: ISO / "hash-cache.json"
    artifacts.download_root = lambda: ISO / "downloads"
    store.cache_root = lambda: cache_dir
    real_write = store.write_json
    # registration writes a `last_used` time to the user's EP store at each process: drop that write
    store.write_json = lambda path, value, *args, **kw: None if Path(path).name == "verdicts.json" else real_write(path, value, *args, **kw)
    package_zoo = Path(PACKAGE_SIDECAR_ROOT)
    real = catalog._artifacts

    def artifacts_from_main(found, cache):
        try:
            rel = found.path.relative_to(package_zoo)
        except ValueError:
            return real(found, cache)
        alt = MAIN_ZOO / rel
        return real(dataclasses.replace(found, path=alt, root=MAIN_ZOO), cache) if alt.parent.is_dir() else real(found, cache)

    catalog._artifacts = artifacts_from_main


def strip_dht(data: bytes) -> bytes:
    out, i = bytearray(data[:2]), 2
    while data[i + 1] != 0xDA:
        end = i + 2 + int.from_bytes(data[i + 2:i + 4], "big")
        if data[i + 1] != 0xC4:
            out += data[i:end]
        i = end
    return bytes(out + data[i:])


def pct(values, q):
    values = sorted(values)
    if not values:
        return None
    k = (len(values) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (k - lo)


def stats(values):
    if not values:
        return None
    return {"n": len(values), "median": statistics.median(values), "p95": pct(values, 0.95), "min": min(values), "max": max(values),
            "mean": statistics.fmean(values)}


def vram(sampler, pid):
    s = sampler.sample([pid])
    proc = s.processes[0].vram_used_bytes if s.processes else None
    gpu = s.gpus[0] if s.gpus else None
    return {"process_vram_bytes": proc, "gpu_used_bytes": getattr(gpu, "vram_used_bytes", None), "gpu_free_bytes": getattr(gpu, "vram_free_bytes", None),
            "gpu_util": getattr(gpu, "utilization", None), "errors": list(s.sample_errors)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", required=True)
    ap.add_argument("--mode", required=True, choices=["M0", "M1", "M2", "M3", "M2b"])
    ap.add_argument("--res", required=True, choices=list(RES))
    ap.add_argument("--cams", type=int, required=True)
    ap.add_argument("--calls", type=int, default=300)
    ap.add_argument("--warmup", type=int, default=30)
    ap.add_argument("--rot", type=int, default=0)
    ap.add_argument("--huff", action="store_true")
    ap.add_argument("--refuse", action="store_true", help="the last camera sends JPEGs with no DHT segment")
    ap.add_argument("--cache", default=str(ISO / "ep-cache"))
    ap.add_argument("--tag", required=True)
    ap.add_argument("--variant", default="P1", choices=["P0", "P1"])
    ap.add_argument("--interval", type=int, default=None)
    ap.add_argument("--nms-floor", type=float, default=0.001)
    a = ap.parse_args()

    isolate(Path(a.cache))
    import numpy as np

    from skellytracker.core.decode import cpu as cpu_decode
    from skellytracker.core.metrics.live import LiveSampler
    from skellytracker.core.pipelines import Frame, get_pipeline, load_pipeline, start_pipeline
    from skellytracker.core.pipelines._runtime import executor, onnx_model

    jpeg_input = a.mode in ("M2", "M3", "M2b")
    if a.mode in ("M0", "M2b"):
        onnx_model.GRAPH_EPS = frozenset()
    if a.mode in ("M2", "M2b"):
        executor.JPEG_DECODER_EPS = frozenset()
    huff_calls = []
    if a.huff:
        from skellytracker.core.eps import registration

        module, _ = registration.prepare_jpeg_decoder(a.ep)
        real_decoder = module.Decoder

        def decoder(*args, **kwargs):
            kwargs["options"] = kwargs.get("options", "") + HUFF_OPTION
            huff_calls.append(kwargs["options"])
            return real_decoder(*args, **kwargs)

        module.Decoder = decoder

    files = sorted(FRAMES.glob(f"*_{RES[a.res]}_*.jpg"))
    buffers = [f.read_bytes() for f in files]
    arrays = [cpu_decode.decode_jpeg(b, 0) for b in buffers]  # the package CPU decode: M0/M1 get the same pixels as the CPU JPEG path
    refused = [strip_dht(b) for b in buffers] if a.refuse else None
    cams = [f"cam{c}" for c in range(a.cams)]

    def frame_of(cam_index: int, call: int) -> int:
        return (cam_index * 3 + call // HOLD) % len(files)

    entry = get_pipeline("yolox-rtmw-wholebody@skellytracker")
    config = load_pipeline(entry.path)
    data = config.model_dump(mode="json", exclude_unset=True)
    node_ids = [n["id"] for n in data["nodes"]]
    spans = ["pipeline.run", "frame.decode", "frame.upload"]
    for n in data["nodes"]:
        spans += [f"{n['id']}.{s}" for s in (("preprocess", "inference", "postprocess") if n["type"] == "onnx_model" else ("run",))]
    data["instrumentation"] = {"timing_spans": spans}
    nodes = {n["id"]: n for n in data["nodes"]}
    if a.variant == "P1":
        # The frames hold no person: the detector keeps its best box of any score, and only `box_missing` asks for a
        # detection, so the built-in cadence (detector 1 in `interval`, keypoints on each call) runs on them.
        nodes["person"]["params"]["object_decode"] = {"min_score": 0.0, "nms": {"post_nms_top_k": 1, "score_threshold": a.nms_floor}}
        nodes["trigger"]["params"]["fitness_checks"] = [{"check": "box_missing"}]
        nodes["points_box"]["params"]["score_threshold"] = 0.0
    if a.interval is not None:
        nodes["trigger"]["params"]["redetect_interval"] = a.interval
    pipeline = load_pipeline(data)

    sampler = LiveSampler()
    pid = os.getpid()
    mem = {"before_start": vram(sampler, pid)}
    lines: list[dict] = []
    warns: list = []
    t0 = time.perf_counter()
    run = start_pipeline(pipeline, camera_ids=cams, running_mode="live", execution_provider=a.ep, timing_sink=lines.append, on_warning=warns.append)
    start_s = time.perf_counter() - t0
    mem["after_start"] = vram(sampler, pid)
    header = lines[0]
    total = a.warmup + a.calls
    walls, cpu_blocks = [], []
    rec_xy = np.full((total, a.cams, 137, 2), np.nan)
    rec_score = np.zeros((total, a.cams, 137))
    rec_kp_present = np.zeros((total, a.cams), bool)
    rec_box = np.full((total, a.cams, 4), np.nan)
    rec_box_score = np.full((total, a.cams), np.nan)
    rec_box_present = np.zeros((total, a.cams), bool)
    rec_det = np.zeros((total, a.cams), bool)
    block = 25
    cpu_mark = None
    try:
        for i in range(total):
            if i == a.warmup:
                mem["start_measured"] = vram(sampler, pid)
                cpu_mark, cpu_count = time.process_time(), 0
            frames = {}
            for c, cam in enumerate(cams):
                k = frame_of(c, i)
                if jpeg_input:
                    image = refused[k] if (a.refuse and c == a.cams - 1) else buffers[k]
                else:
                    image = arrays[k]
                frames[cam] = Frame(image, i, i * 1000.0 / 30.0, rotation_deg=a.rot)
            t = time.perf_counter_ns()
            result = run.process_batch(frames)
            walls.append((time.perf_counter_ns() - t) / 1e6)
            if cpu_mark is not None:
                cpu_count += 1
                if cpu_count == block:
                    now = time.process_time()
                    cpu_blocks.append((now - cpu_mark) * 1000 / block)
                    cpu_mark, cpu_count = now, 0
            for c, cam in enumerate(cams):
                r = result[cam]
                kp, bx = r["wholebody"], r["boxes"]
                if kp.present.size and kp.present[0]:
                    rec_xy[i, c] = kp.xy[0]
                    rec_score[i, c] = kp.score[0]
                    rec_kp_present[i, c] = True
                if bx.present.size and bx.present[0]:
                    rec_box[i, c] = bx.xyxy[0]
                    rec_box_score[i, c] = bx.score[0]
                    rec_box_present[i, c] = True
                rec_det[i, c] = bool(r["node_ran"]["person"])
        mem["end_measured"] = vram(sampler, pid)
        executor_obj = run._executor
        preprocess_sessions = len(executor_obj.sessions.preprocess)
    finally:
        run.close()
    mem["after_close"] = vram(sampler, pid)

    # The events of each call, by frame_index (each camera of a call has the same frame_index).
    per_call: list[dict[str, float]] = [dict() for _ in range(total)]  # noqa: C408
    for ev in lines[1:]:
        if "span" not in ev:
            continue
        idx = ev["images"][0]["frame_index"]
        key = f"{ev['node_id']}.{ev['span']}"
        per_call[idx][key] = per_call[idx].get(key, 0.0) + (ev["end_ns"] - ev["start_ns"]) / 1e6
    glue = [n for n in node_ids if n not in ("person", "wholebody")]
    for d in per_call:
        d["glue.run"] = sum(d.get(f"{n}.run", 0.0) for n in glue)
    measured = range(a.warmup, total)
    det_calls = [i for i in measured if rec_det[i].any()]
    kp_calls = [i for i in measured if not rec_det[i].any()]
    span_keys = ["frame.decode", "frame.upload", "person.preprocess", "person.inference", "person.postprocess",
                 "wholebody.preprocess", "wholebody.inference", "wholebody.postprocess", "glue.run", "pipeline.run"]

    def span_table(calls):
        return {k: stats([per_call[i].get(k, 0.0) for i in calls]) for k in span_keys} | {"wall": stats([walls[i] for i in calls])}

    cpu_total = statistics.fmean(cpu_blocks) if cpu_blocks else None
    w = [walls[i] for i in measured]
    summary = {
        "tag": a.tag, "ep": a.ep, "mode": a.mode, "res": RES[a.res], "cams": a.cams, "rot": a.rot, "huff": a.huff, "refuse": a.refuse,
        "variant": a.variant, "interval": a.interval, "nms_floor": a.nms_floor,
        "box_present_fraction": float(rec_box_present[a.warmup:].mean()), "huff_options_seen": huff_calls, "calls": a.calls, "warmup": a.warmup, "hold": HOLD,
        "start_s": start_s, "first_call_ms": walls[0], "first_calls_ms": walls[:5], "first_call_spans": per_call[0],
        "wall": stats(w), "calls_per_s": 1000.0 / statistics.fmean(w), "cpu_ms_per_call_blocks": stats(cpu_blocks), "cpu_ms_per_call": cpu_total,
        "spans_all": span_table(list(measured)), "spans_detector": span_table(det_calls), "spans_keypoint_only": span_table(kp_calls),
        "detector_calls": len(det_calls), "detector_call_indices": det_calls[:40],
        "keypoint_present_fraction": float(rec_kp_present[a.warmup:].mean()),
        "memory": mem, "preprocess_sessions": preprocess_sessions,
        "vram_peak_bytes": max((m["process_vram_bytes"] or 0) for m in mem.values()),
        "skellytracker_file": __import__("skellytracker").__file__,
        "versions": {p: __import__("importlib.metadata").metadata.version(p) for p in ("onnxruntime", "opencv-contrib-python", "numpy")}
        | {"nvimgcodec": getattr(__import__("skellytracker.core.eps.registration", fromlist=["x"]).prepare_jpeg_decoder(a.ep)[0], "__version__", None)},
        "warnings": [{"code": x.code, "message": x.message, "details": dict(x.details)} for x in warns],
        "stage_providers": {n["id"]: n.get("stage_providers") for n in header.get("nodes", [])},
        "execution": {n["id"]: n.get("execution") for n in header.get("nodes", []) if n.get("execution")},
        "batching": {n["id"]: n.get("batching") for n in header.get("nodes", [])},
        "files": [f.name for f in files], "frame_cycle": {cam: [files[frame_of(c, i)].name for i in range(0, 80, HOLD)] for c, cam in enumerate(cams)},
    }
    out = HERE / "runs"
    out.mkdir(exist_ok=True)
    (out / f"{a.tag}.json").write_text(json.dumps(summary, indent=1, default=str))
    np.savez_compressed(out / f"{a.tag}.npz", xy=rec_xy, score=rec_score, kp_present=rec_kp_present, box=rec_box, box_score=rec_box_score,
                        box_present=rec_box_present, det=rec_det, walls=np.array(walls))
    s = summary
    print(f"{a.tag}: start {start_s:.1f}s first {walls[0]:.1f}ms wall med {s['wall']['median']:.2f} p95 {s['wall']['p95']:.2f} max {s['wall']['max']:.2f} "
          f"cps {s['calls_per_s']:.1f} cpu {cpu_total} det_calls {len(det_calls)} kp_frac {s['keypoint_present_fraction']:.2f} warns {[x['code'] for x in s['warnings']]} "
          f"decode med {s['spans_all']['frame.decode']['median']:.2f} vram_peak {s['vram_peak_bytes'] / 2**20:.0f}MiB huff {sorted(set(huff_calls))}", flush=True)


if __name__ == "__main__":
    main()

# Evidence of ADR-FBV5. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Accuracy runs of the built-in pipeline yolox-rtmw-wholebody on the freemocap sample data (JPEG re-encodes), one mode per process.

Modes (no repo change; switch by input form and the two module constants, as in s8_measure/measure.py):
  R   array from the package CPU decode (cv2.imdecode) of the same JPEG bytes, CPU preprocess (GRAPH_EPS empty)
  A1  the same array, GPU preprocess
  J2  JPEG bytes, CPU decode in the run (JPEG_DECODER_EPS empty), GPU preprocess
  J3  JPEG bytes, GPU decode, GPU preprocess
  DEC decode only: nvJPEG (package NvJpegDecoder) vs cv2 on the first --frames frames, no pipeline
Running mode `video`, all cameras in one call per frame index, fps 30 (no timestamp given).
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import pickle
import statistics
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN_ZOO = Path(os.environ["MAIN_MODEL_ZOO"])
ISO = HERE / "iso"


def isolate(cache_dir: Path) -> None:
    """Copied from s8_measure/measure.py: hash cache, downloads, user root, EP cache in the scratchpad; model files read in place from the main checkout."""
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


def decode_only(a, frames, cams) -> None:
    import numpy as np

    from skellytracker.core.decode import cpu as cpu_decode
    from skellytracker.core.decode.nvidia import NvJpegDecoder

    from skellytracker.core.eps import registration

    registration.ensure_registered(a.ep)  # OrtValue.numpy() of a CUDA tensor needs the EP's data transfer
    dec = NvJpegDecoder.open(a.ep)
    assert dec is not None, "no GPU JPEG decoder for this EP"  # noqa: S101
    maxd, sums, npx, ndiff, hist = 0, 0, 0, 0, np.zeros(256, np.int64)
    per = []
    try:
        for row in frames[:a.frames]:
            gpu = dec.decode(row, [0] * len(row))
            for buf, g in zip(row, gpu, strict=True):
                assert g is not None, "nvJPEG refused a buffer"  # noqa: S101
                d = np.abs(g.host.astype(np.int16) - cpu_decode.decode_jpeg(buf, 0).astype(np.int16))
                maxd = max(maxd, int(d.max()))
                sums += int(d.sum())
                npx += d.size
                ndiff += int((d > 0).sum())
                hist += np.bincount(d.ravel(), minlength=256)[:256]
                per.append(float(d.mean()))
            del gpu
    finally:
        dec.close()
    out = {"tag": a.tag, "ep": a.ep, "quality": a.quality, "frames": a.frames, "cams": cams, "channel_values": npx, "max_abs": maxd,
           "mean_abs": sums / npx, "pct_values_differ": 100.0 * ndiff / npx, "hist_abs": {int(k): int(v) for k, v in enumerate(hist) if v},
           "per_image_mean_abs_max": max(per)}
    (HERE / "runs").mkdir(exist_ok=True)
    (HERE / "runs" / f"{a.tag}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", required=True)
    ap.add_argument("--mode", required=True, choices=["R", "A1", "J2", "J3", "DEC"])
    ap.add_argument("--quality", type=int, default=90)
    ap.add_argument("--frames", type=int, default=1108)
    ap.add_argument("--interval", type=int, default=None, help="variant: redetect_interval of the trigger node")
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()

    isolate(ISO / "ep-cache")
    import numpy as np

    data = pickle.loads((HERE / "data" / f"jpeg_q{a.quality}.pkl").read_bytes())  # noqa: S301
    cams, frames = data["cams"], data["frames"][:a.frames]
    if a.mode == "DEC":
        return decode_only(a, frames, cams)

    from skellytracker.core.decode import cpu as cpu_decode
    from skellytracker.core.pipelines import Frame, get_pipeline, load_pipeline, start_pipeline
    from skellytracker.core.pipelines._runtime import executor, onnx_model

    jpeg_input = a.mode in ("J2", "J3")
    if a.mode == "R":
        onnx_model.GRAPH_EPS = frozenset()
    if a.mode == "J2":
        executor.JPEG_DECODER_EPS = frozenset()

    entry = get_pipeline("yolox-rtmw-wholebody@skellytracker")
    cfg = load_pipeline(entry.path).model_dump(mode="json", exclude_unset=True)
    if a.interval is not None:
        next(n for n in cfg["nodes"] if n["id"] == "trigger")["params"]["redetect_interval"] = a.interval
    pipeline = load_pipeline(cfg)

    T, C = len(frames), len(cams)
    K = 137  # output_schema.json: the 133 model points plus 4 derived centers (indices 23..26)
    rec = {"xy": np.full((T, C, K, 2), np.nan), "score": np.full((T, C, K), np.nan), "kp_present": np.zeros((T, C), bool),
           "box": np.full((T, C, 4), np.nan), "box_score": np.full((T, C), np.nan), "box_present": np.zeros((T, C), bool),
           "det": np.zeros((T, C), bool), "n_kp_inst": np.zeros((T, C), np.int8), "n_box_inst": np.zeros((T, C), np.int8)}
    walls, warns = [], []
    t0 = time.perf_counter()
    run = start_pipeline(pipeline, camera_ids=cams, running_mode="video", execution_provider=a.ep, fps=30.0, on_warning=warns.append)
    start_s = time.perf_counter() - t0
    try:
        for i, row in enumerate(frames):
            batch = {cam: Frame(row[c] if jpeg_input else cpu_decode.decode_jpeg(row[c], 0), i) for c, cam in enumerate(cams)}
            t = time.perf_counter_ns()
            result = run.process_batch(batch)
            walls.append((time.perf_counter_ns() - t) / 1e6)
            for c, cam in enumerate(cams):
                r = result[cam]
                kp, bx = r["wholebody"], r["boxes"]
                rec["n_kp_inst"][i, c] = int(kp.present.sum()) if kp.present.size else 0
                rec["n_box_inst"][i, c] = int(bx.present.sum()) if bx.present.size else 0
                if kp.present.size and kp.present[0]:
                    rec["xy"][i, c], rec["score"][i, c], rec["kp_present"][i, c] = kp.xy[0], kp.score[0], True
                if bx.present.size and bx.present[0]:
                    rec["box"][i, c], rec["box_score"][i, c], rec["box_present"][i, c] = bx.xyxy[0], bx.score[0], True
                rec["det"][i, c] = bool(r["node_ran"]["person"])
        models = run.models
        all_warns = run.warnings
    finally:
        run.close()
    summary = {"tag": a.tag, "ep": a.ep, "mode": a.mode, "quality": a.quality, "frames": T, "cams": cams, "interval": a.interval, "start_s": start_s,
               "wall_median_ms": statistics.median(walls[5:]), "wall_mean_ms": statistics.fmean(walls[5:]), "models": models,
               "detector_calls": int(rec["det"].any(axis=1).sum()), "kp_present_fraction": float(rec["kp_present"].mean()),
               "warnings": [{"code": w.code, "message": w.message} for w in all_warns]}
    out = HERE / "runs"
    out.mkdir(exist_ok=True)
    (out / f"{a.tag}.json").write_text(json.dumps(summary, indent=1, default=str))
    np.savez_compressed(out / f"{a.tag}.npz", walls=np.array(walls), **rec)
    print(json.dumps({k: summary[k] for k in ("tag", "start_s", "wall_median_ms", "detector_calls", "kp_present_fraction")}),
          [w["code"] for w in summary["warnings"]], flush=True)


if __name__ == "__main__":
    main()

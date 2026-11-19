# Evidence of ADR-BP5Y. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""NvJpegDecoder alone (the exported package code), hybrid_huffman_threshold default vs 0, in one process.

Small JPEGs are made in memory from the camera frames (resize INTER_AREA, cv2.imencode quality 90, 4:2:2 like the
cameras); nothing is written to disk. Pixel check: each size, plus one grayscale and one progressive JPEG.
Timing: per round, one block of --iters batches per (size, N, decoder), order rotated per round; round 0 is a warm-up.
Wall per batch: perf_counter around decode() (includes the stream sync). CPU per batch: process_time of the block / iters.
"""
import os
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from skellytracker.core.decode.nvidia import NvJpegDecoder
from skellytracker.core.eps import registration

HERE = Path(__file__).resolve().parent
FRAMES = Path(os.environ["JPEG_FRAMES_DIR"])
CAMS = ("C922", "C930e", "KiyoPro", "generic")
HUFF_OPTION = " nvjpeg_cuda_decoder:hybrid_huffman_threshold=0"

ap = argparse.ArgumentParser()
ap.add_argument("--ep", default="cuda")
ap.add_argument("--iters", type=int, default=200)
ap.add_argument("--rounds", type=int, default=5)
ap.add_argument("--tag", required=True)
args = ap.parse_args()

print("skellytracker from", sys.modules["skellytracker.core.decode.nvidia"].__file__, flush=True)
src720 = [(FRAMES / f"{c}_1280x720_{k}.jpg").read_bytes() for c in CAMS for k in ("median", "max")]
src1080 = [(FRAMES / f"{c}_1920x1080_{k}.jpg").read_bytes() for c in CAMS for k in ("median", "max")]
ENC = [cv2.IMWRITE_JPEG_QUALITY, 90, cv2.IMWRITE_JPEG_SAMPLING_FACTOR, cv2.IMWRITE_JPEG_SAMPLING_FACTOR_422]


def small(w, h):
    out = []
    for b in src720:
        img = cv2.resize(cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR), (w, h), interpolation=cv2.INTER_AREA)
        out.append(cv2.imencode(".jpg", img, ENC)[1].tobytes())
    return out


SETS = {"320x240": small(320, 240), "640x480": small(640, 480), "1280x720": src720, "1920x1080": src1080}
for name, s in SETS.items():
    print(f"{name}: mean {statistics.mean(map(len, s)) / 1024:.1f} KiB", flush=True)

module, _ = registration.prepare_jpeg_decoder(args.ep)
real = module.Decoder
seen = []


def patched(*a, **kw):
    kw["options"] = kw.get("options", "") + HUFF_OPTION
    seen.append(kw["options"])
    return real(*a, **kw)


print("open OFF", flush=True)
off = NvJpegDecoder.open(args.ep)
module.Decoder = patched
print("open ON", flush=True)
on = NvJpegDecoder.open(args.ep)
module.Decoder = real
print("options of ON:", seen, flush=True)
DEC = {"off": off, "on": on}
off.decode([src720[0]], [90])  # builds a turn session: ORT then has the EP device copy that OrtValue.numpy() needs


def host(dec, bufs):
    return [None if f is None else f.device.numpy() for f in dec.decode(bufs, [0] * len(bufs))]


# pixels
pixels = {}
g = cv2.imdecode(np.frombuffer(src720[0], np.uint8), cv2.IMREAD_COLOR)
extra = {
    "gray_1280x720": cv2.imencode(".jpg", cv2.cvtColor(g, cv2.COLOR_BGR2GRAY), [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes(),
    "gray_640x480": cv2.imencode(".jpg", cv2.cvtColor(cv2.resize(g, (640, 480), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY), [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes(),
    "progressive_1280x720": cv2.imencode(".jpg", g, ENC + [cv2.IMWRITE_JPEG_PROGRESSIVE, 1])[1].tobytes(),
    "progressive_640x480": cv2.imencode(".jpg", cv2.resize(g, (640, 480), interpolation=cv2.INTER_AREA), ENC + [cv2.IMWRITE_JPEG_PROGRESSIVE, 1])[1].tobytes(),
}
for name, bufs in list(SETS.items()) + [(k, [v]) for k, v in extra.items()]:
    print(f"pixels {name} first decode OFF", flush=True)
    a = host(off, bufs)
    print(f"pixels {name} first decode ON", flush=True)
    b = host(on, bufs)
    diffs, nones = [], []
    for x, y in zip(a, b):  # noqa: B905
        nones.append((x is None, y is None))
        if x is not None and y is not None:
            diffs.append(int(np.abs(x.astype(np.int16) - y).max()) if x.shape == y.shape else f"shape {x.shape} vs {y.shape}")
    # agreement with the CPU (cv2) decode, to show the frames are real images
    cv = [cv2.imdecode(np.frombuffer(buf, np.uint8), cv2.IMREAD_COLOR) for buf in bufs]
    vs_cv = [round(float(np.abs(x.astype(np.int16) - c).mean()), 3) for x, c in zip(a, cv) if x is not None and x.shape == c.shape]  # noqa: B905
    pixels[name] = {"n": len(bufs), "max_abs_diff_off_vs_on": diffs, "none_off_on": nones, "off_vs_cv2_mean_abs": vs_cv,
                    "shapes": [None if x is None else list(x.shape) for x in a]}
    print(f"PIXELS {name}: {pixels[name]}", flush=True)


def block(dec, bufs, n, start):
    walls = []
    c0 = time.process_time()
    for i in range(args.iters):
        sel = [bufs[(start + i + k) % len(bufs)] for k in range(n)]
        t0 = time.perf_counter_ns()
        keep = dec.decode(sel, [0] * n)  # noqa: F841
        walls.append((time.perf_counter_ns() - t0) / 1e6)
    return walls, (time.process_time() - c0) * 1e3 / args.iters


def pct(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, int(q * len(v)))]


configs = [(size, n, d) for size in ("320x240", "640x480", "1280x720") for n in (3, 6) for d in ("off", "on")]
wall, cpu = {}, {}
for rnd in range(args.rounds + 1):
    order = configs[rnd % len(configs):] + configs[:rnd % len(configs)]
    if rnd % 2:
        order = order[::-1]
    for size, n, d in order:
        w, c = block(DEC[d], SETS[size], n, rnd)
        if rnd:
            wall.setdefault((size, n, d), []).extend(w)
            cpu.setdefault((size, n, d), []).append(c)
rows = []
for key in configs:
    w, c = wall[key], cpu[key]
    row = {"size": key[0], "n": key[1], "huff": key[2], "batches": len(w), "wall_median": statistics.median(w), "wall_p95": pct(w, 0.95),
           "wall_max": max(w), "cpu_median": statistics.median(c), "cpu_p95": pct(c, 0.95), "cpu_max": max(c)}
    rows.append(row)
    print("ROW " + " ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}" for k, v in row.items()), flush=True)
off.close()
on.close()
(HERE / "runs").mkdir(exist_ok=True)
(HERE / "runs" / f"{args.tag}.json").write_text(json.dumps({"rows": rows, "pixels": pixels, "options_on": seen, "iters": args.iters,
                                                            "rounds": args.rounds}, indent=1))
print("DONE", flush=True)

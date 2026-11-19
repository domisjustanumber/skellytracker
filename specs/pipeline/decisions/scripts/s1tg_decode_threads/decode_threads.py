# Evidence of ADR-S1TG. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""CPU threaded cv2.imdecode vs nvJPEG batch decode: N JPEG buffers in host memory -> N BGR frames in GPU memory.

Usage (from the skellytracker-native-jpeg worktree): uv run --no-sync python decode_threads.py --res 720|1080 [--spin]
Each round runs every path as a block of --iters batches (order rotated per round); round 0 is a warm-up.
Wall time per batch: perf_counter. CPU time per batch: process_time delta of the block / iters (GetProcessTimes ticks
are too coarse for one batch).
"""
import argparse
import concurrent.futures as cf
import ctypes
import os
import pathlib
import statistics
import sys
import threading
import time

import cv2
import numpy as np
from nvidia import nvimgcodec

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[5] / "specs" / "model-sidecar" / "decisions" / "scripts"))
from gpu_preprocess_graphs import load_cudart, versions  # noqa: E402

FRAMES = pathlib.Path(os.environ["JPEG_FRAMES_DIR"])
CAMS = ("C922", "C930e", "KiyoPro", "generic")

ap = argparse.ArgumentParser()
ap.add_argument("--res", type=int, default=720)
ap.add_argument("--iters", type=int, default=40)
ap.add_argument("--rounds", type=int, default=5)
ap.add_argument("--spin", action="store_true", help="only the busy-interpreter config (N=3)")
args = ap.parse_args()
W, H = (1280, 720) if args.res == 720 else (1920, 1080)
FB = W * H * 3


def check(rc, what):
    assert rc == 0, f"{what} returned {rc}"  # noqa: S101


names = [f"{c}_{W}x{H}_{k}.jpg" for c in CAMS for k in ("median", "max")]
jpegs = [(FRAMES / n).read_bytes() for n in names]  # read in place, never written anywhere
bufs = [np.frombuffer(j, np.uint8) for j in jpegs]
NF = len(jpegs)

CUDART = load_cudart(None)
stream = ctypes.c_void_p()
check(CUDART.cudaStreamCreateWithFlags(ctypes.byref(stream), 1), "cudaStreamCreateWithFlags")  # non-blocking
dev = ctypes.c_void_p()
check(CUDART.cudaMalloc(ctypes.byref(dev), ctypes.c_size_t(6 * FB)), "cudaMalloc")
params = nvimgcodec.DecodeParams(apply_exif_orientation=False, sample_format=nvimgcodec.I_BGR)
dec = nvimgcodec.Decoder()
dec_gh = nvimgcodec.Decoder(options="nvjpeg_cuda_decoder:hybrid_huffman_threshold=0")
ONLY = {d: nvimgcodec.Decoder(decoder_ids=[d]) for d in ("nvjpeg_cuda_decoder", "libjpeg_turbo_decoder")}


def imdecode(b):
    return cv2.imdecode(b, cv2.IMREAD_COLOR)


def upload(frames):
    # the pageable cudaMemcpy upload of sync_xfer.py, one sync at the end (staged copies can still be in flight)
    for k, f in enumerate(frames):
        check(CUDART.cudaMemcpy(ctypes.c_void_p(dev.value + k * FB), ctypes.c_void_p(f.ctypes.data),
                                ctypes.c_size_t(FB), 1), "cudaMemcpy")
    check(CUDART.cudaStreamSynchronize(None), "cudaStreamSynchronize(0)")


def nv(decoder, sel):
    images = decoder.decode([jpegs[i] for i in sel], params=params, cuda_stream=stream.value)
    check(CUDART.cudaStreamSynchronize(stream), "cudaStreamSynchronize")
    return images


def make_paths(n, pool):
    p = {
        "P1 serial decode": lambda sel: [imdecode(bufs[i]) for i in sel],
        "P1 serial +upload": lambda sel: upload([imdecode(bufs[i]) for i in sel]),
        "P2 pool decode": lambda sel: list(pool.map(imdecode, [bufs[i] for i in sel])),
        "P2 pool +upload": lambda sel: upload(list(pool.map(imdecode, [bufs[i] for i in sel]))),
        "P3 nvjpeg": lambda sel: nv(dec, sel),
    }
    if W * H < 1000 * 1000:  # the default hybrid_huffman_threshold; above it the GPU Huffman path is already used
        p["P4 nvjpeg gpuhuff"] = lambda sel: nv(dec_gh, sel)
    return p


def correctness(n, pool):
    sel = list(range(n))
    ref = [imdecode(bufs[i]) for i in sel]
    pooled = list(pool.map(imdecode, [bufs[i] for i in sel]))
    assert all(np.array_equal(a, b) for a, b in zip(ref, pooled)), "pool decode differs"  # noqa: B905, S101
    upload(ref)
    back = np.empty((n, H, W, 3), np.uint8)
    check(CUDART.cudaMemcpy(ctypes.c_void_p(back.ctypes.data), dev, ctypes.c_size_t(n * FB), 2), "cudaMemcpy D2H")
    assert all(np.array_equal(back[k], ref[k]) for k in range(n)), "upload differs"  # noqa: S101
    out = []
    for tag, d in (("P3", dec), ("P4", dec_gh)):
        imgs = nv(d, sel)
        host = [np.asarray(im.cpu()) for im in imgs]
        assert all(h.shape == (H, W, 3) for h in host), [h.shape for h in host]  # noqa: S101
        diffs = [float(np.abs(h.astype(np.int16) - r).mean()) for h, r in zip(host, ref)]  # noqa: B905
        assert max(diffs) < 3, f"{tag} vs cv2 mean abs diff {diffs}"  # noqa: S101
        out.append(f"{tag} vs cv2 BGR mean|diff| max {max(diffs):.2f}")
        # which decoder ran: compare with single-decoder allow-lists (bit-exact match identifies it)
        for did in ("nvjpeg_cuda_decoder", "libjpeg_turbo_decoder"):
            only = ONLY[did]
            o = [np.asarray(im.cpu()) for im in nv(only, sel)]
            out.append(f"{tag}=={did}: {all(np.array_equal(a, b) for a, b in zip(host, o))}")  # noqa: B905
    return "; ".join(out)


def run_block(fn, n, start):
    walls = []
    c0 = time.process_time()
    for i in range(args.iters):
        sel = [(start + i + k) % NF for k in range(n)]  # distinct frames in a batch
        t0 = time.perf_counter_ns()
        keep = fn(sel)  # noqa: F841  (results stay alive until the next batch, as downstream use would hold them)
        walls.append((time.perf_counter_ns() - t0) / 1e6)
    return walls, (time.process_time() - c0) * 1e3 / args.iters


def stats(v):
    return statistics.median(v), min(v), max(v)


def spinner(stop):
    x = 0
    while not stop.is_set():
        for _ in range(20000):  # pure Python: holds the GIL until the 5 ms switch interval forces a release
            x += 1


def measure(configs, label):
    """configs: list of (name, fn, n, cv_threads, spin)."""
    wall, cpu = {}, {}
    for rnd in range(args.rounds + 1):
        order = configs[rnd % len(configs):] + configs[:rnd % len(configs)]
        for name, fn, n, cvt, spin in order:
            cv2.setNumThreads(cvt)
            stop = threading.Event()
            th = threading.Thread(target=spinner, args=(stop,), daemon=True) if spin else None
            if th:
                th.start()
                time.sleep(0.05)
            w, c = run_block(fn, n, rnd)
            if th:
                stop.set()
                th.join()
            if rnd:
                wall.setdefault(name, []).extend(w)
                cpu.setdefault(name, []).append(c)
    cv2.setNumThreads(DEFAULT_CV_THREADS)
    for name, *_ in configs:
        wm, wn, wx = stats(wall[name])
        cm, cn, cx = stats(cpu[name])
        p95 = sorted(wall[name])[int(0.95 * len(wall[name]))]
        print(f"ROW {label:12s} {name:34s} wall median {wm:7.3f} min {wn:7.3f} p95 {p95:7.3f} max {wx:7.3f} ms | "
              f"cpu/batch median {cm:7.3f} min {cn:7.3f} max {cx:7.3f} ms", flush=True)


DEFAULT_CV_THREADS = cv2.getNumThreads()
print(f"{W}x{H} frames: " + ", ".join(f"{n} {len(j) / 1024:.0f}KiB" for n, j in zip(names, jpegs)))  # noqa: B905
print(f"mean size {statistics.mean(len(j) for j in jpegs) / 1024:.0f} KiB; logical cores {os.cpu_count()}; "
      f"cv2 {cv2.__version__} default threads {DEFAULT_CV_THREADS}; python {sys.version.split()[0]}; "
      f"switchinterval {sys.getswitchinterval()}")
print(versions())
print(f"nvimgcodec decoder ids: {nvimgcodec.get_decoder_ids()}")
print(f"iters/round {args.iters}, rounds {args.rounds} (+1 warm-up)", flush=True)

for n in ((3,) if args.spin else (1, 3, 6)):
    with cf.ThreadPoolExecutor(max_workers=n) as pool:
        print(f"N={n} correctness: {correctness(n, pool)}", flush=True)
        paths = make_paths(n, pool)
        if args.spin:
            configs = []
            for spin in (False, True):
                for name in ("P1 serial decode", "P2 pool decode", "P2 pool +upload", "P3 nvjpeg"):
                    configs.append((f"{name}{' SPIN' if spin else ''}", paths[name], n, DEFAULT_CV_THREADS, spin))  # noqa: PERF401
        else:
            configs = [(f"{k} cvT={t}", fn, n, t, False) for k, fn in paths.items() if k.startswith(("P1", "P2"))
                       for t in (DEFAULT_CV_THREADS, 1)]
            configs += [(k, fn, n, DEFAULT_CV_THREADS, False) for k, fn in paths.items() if not k.startswith(("P1", "P2"))]
        measure(configs, f"{W}x{H} N={n}")
check(CUDART.cudaFree(dev), "cudaFree")
print("DONE")

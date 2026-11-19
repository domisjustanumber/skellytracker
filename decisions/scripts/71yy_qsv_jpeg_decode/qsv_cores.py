"""Throwaway measurement: CPU imdecode pool vs mjpeg_qsv (one context per thread) under a CPU affinity limit.

Usage: python qsv_cores.py <2|4|all> [timed_batches]
"""
import ctypes
import ctypes.wintypes as wt
import json
import sys

k32 = ctypes.WinDLL("kernel32", use_last_error=True)


def topology():
    """[(efficiency_class, [logical cpu ids])] per physical core, group 0 only."""
    n = wt.DWORD(0)
    k32.GetLogicalProcessorInformationEx(0, None, ctypes.byref(n))
    buf = ctypes.create_string_buffer(n.value)
    assert k32.GetLogicalProcessorInformationEx(0, buf, ctypes.byref(n)), ctypes.get_last_error()  # noqa: S101
    raw, off, cores = buf.raw, 0, []
    while off < n.value:
        size = int.from_bytes(raw[off + 4:off + 8], "little")
        eff = raw[off + 9]
        mask = int.from_bytes(raw[off + 32:off + 40], "little")  # first GROUP_AFFINITY.Mask
        cores.append((eff, [i for i in range(64) if mask >> i & 1]))
        off += size
    return cores


CORES = topology()
LIMIT = sys.argv[1]
TIMED = int(sys.argv[2]) if len(sys.argv) > 2 else 200
if LIMIT == "all":
    CPUS = sorted(c for _, ids in CORES for c in ids)
else:
    pmax = max(e for e, _ in CORES)
    pcores = [ids for e, ids in CORES if e == pmax]
    # skip the first P-core (logical CPU 0 takes most interrupts); one SMT thread per physical P-core
    CPUS = [ids[0] for ids in pcores[1:1 + int(LIMIT)]]
    assert len(CPUS) == int(LIMIT)  # noqa: S101
k32.GetCurrentProcess.restype = wt.HANDLE
k32.SetProcessAffinityMask.argtypes = [wt.HANDLE, ctypes.c_size_t]
assert k32.SetProcessAffinityMask(k32.GetCurrentProcess(), ctypes.c_size_t(sum(1 << c for c in CPUS)))  # noqa: S101
NCPU = len(CPUS)

import concurrent.futures  # noqa: E402
import time  # noqa: E402

import av  # noqa: E402
import cv2  # noqa: E402
import numpy as np  # noqa: E402

if len(sys.argv) > 3:  # optional: OpenCV internal thread count (variant run)
    cv2.setNumThreads(int(sys.argv[3]))
WARM = 10
SAMP = {"422": cv2.IMWRITE_JPEG_SAMPLING_FACTOR_422, "420": cv2.IMWRITE_JPEG_SAMPLING_FACTOR_420}
TARGET_KIB = {720: 175, 1080: 275}


def synth(w, h, sigma, seed):
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 255, w, dtype=np.float32)[None, :, None]
    y = np.linspace(0, 255, h, dtype=np.float32)[:, None, None]
    img = np.concatenate([np.broadcast_to(x, (h, w, 1)), np.broadcast_to(y, (h, w, 1)), np.broadcast_to((x + y) / 2, (h, w, 1))], 2)
    img = img + rng.normal(0, sigma, (h, w, 3))
    cx = w // 3 + 37 * seed % (w // 4)  # move shapes per seed so frames differ
    cv2.circle(img, (cx, h // 2), h // 4, (0, 0, 255), -1)
    cv2.rectangle(img, (w // 2, h // 4), (w // 2 + h // 3, h // 4 + h // 3), (40, 220, 40), -1)
    cv2.ellipse(img, (w * 3 // 4, h * 3 // 4), (h // 6, h // 10), 30, 0, 360, (220, 120, 30), -1)
    return np.clip(img, 0, 255).astype(np.uint8)


def encode(img, chroma):
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90, cv2.IMWRITE_JPEG_SAMPLING_FACTOR, SAMP[chroma]])
    assert ok  # noqa: S101
    return buf.tobytes()


def tuned_sigma(w, h, chroma):
    """Bisect the noise sigma so the JPEG lands near the target size (deterministic)."""
    lo, hi, target = 0.5, 40.0, TARGET_KIB[h] * 1024
    for _ in range(12):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if len(encode(synth(w, h, mid, 0), chroma)) < target else (lo, mid)
    return (lo + hi) / 2


def qsv_open():
    c = av.CodecContext.create("mjpeg_qsv", "r")
    c.options = {"async_depth": "1"}
    c.open()
    return c


def qsv_decode(ctx, data):
    frames = ctx.decode(av.Packet(data))
    if not frames:  # drain fallback, as in qsv_probe.py
        frames = ctx.decode(None)
        ctx.flush_buffers()
    return frames[0]


def frame_planes(f):
    """Host-memory planes: (format, ndarray)."""
    return f.format.name, f.to_ndarray()


def to_bgr(fmt, nd, w, h):
    """NV12 (or YUYV) -> BGR, BT.601 full range, linear chroma upsample, like libjpeg's output."""
    if fmt == "nv12":
        y = nd[:h]
        uv = cv2.resize(nd[h:].reshape(h // 2, w // 2, 2), (w, h), interpolation=cv2.INTER_LINEAR)
    elif fmt == "yuyv422":
        y = np.ascontiguousarray(nd[..., 0])
        uv = cv2.resize(nd[..., 1].reshape(h, w // 2, 2), (w, h), interpolation=cv2.INTER_LINEAR)
    else:
        raise RuntimeError(f"unexpected QSV output format {fmt}")
    return cv2.cvtColor(cv2.merge([y, uv[..., 1], uv[..., 0]]), cv2.COLOR_YCrCb2BGR)


def imdecode(d):
    return cv2.imdecode(np.frombuffer(d, np.uint8), cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION)


def timeit(fn):
    for _ in range(WARM):
        fn()
    ts = []
    c0 = time.process_time()
    for _ in range(TIMED):
        t0 = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t0)
    cpu = (time.process_time() - c0) / TIMED
    ts = np.array(ts) * 1e3
    return {"med": float(np.median(ts)), "p95": float(np.percentile(ts, 95)), "max": float(ts.max()), "cpu": cpu * 1e3}


out = {"limit": LIMIT, "cpus": CPUS, "topology": CORES, "versions": {
    "pyav": av.__version__, "libavcodec": av.library_versions["libavcodec"], "opencv": cv2.__version__, "numpy": np.__version__}, "cells": [], "pixdiff": {}}

for (w, h, n) in [(1280, 720, 3), (1920, 1080, 6)]:
    for chroma in ["422", "420"]:
        sigma = tuned_sigma(w, h, chroma)
        datas = [encode(synth(w, h, sigma, s), chroma) for s in range(n)]
        cell = {"w": w, "h": h, "n": n, "chroma": chroma, "sigma": round(sigma, 2), "kib": [round(len(d) / 1024, 1) for d in datas]}

        cpu_pool = concurrent.futures.ThreadPoolExecutor(min(n, NCPU))
        cell["A"] = timeit(lambda: list(cpu_pool.map(imdecode, datas)))  # noqa: B023
        cpu_pool.shutdown()

        opens, firsts, ctxs = [], [], []
        for d in datas:  # one-time context creation + first decode, not timed below
            t0 = time.perf_counter()
            c = qsv_open()
            t1 = time.perf_counter()
            f = qsv_decode(c, d)
            frame_planes(f)
            firsts.append((time.perf_counter() - t1) * 1e3)
            opens.append((t1 - t0) * 1e3)
            ctxs.append(c)
        cell["qsv_open_ms"] = [round(x, 1) for x in opens]
        cell["qsv_first_decode_ms"] = [round(x, 1) for x in firsts]
        cell["qsv_format"] = f.format.name
        pool = concurrent.futures.ThreadPoolExecutor(n)
        pairs = list(zip(ctxs, datas))  # noqa: B905
        dec = lambda cd: frame_planes(qsv_decode(*cd))  # noqa: E731
        e2e = lambda cd: to_bgr(*frame_planes(qsv_decode(*cd)), w, h)  # noqa: B023, E731
        cell["B_dec"] = timeit(lambda: list(pool.map(dec, pairs)))  # noqa: B023, F821
        cell["B"] = timeit(lambda: list(pool.map(e2e, pairs)))  # noqa: B023, F821
        if w == 1280:
            a, b = imdecode(datas[0]), e2e(pairs[0])
            assert a.shape == b.shape and b.dtype == np.uint8  # noqa: S101
            diff = np.abs(a.astype(np.int16) - b.astype(np.int16))
            out["pixdiff"][chroma] = {"max": int(diff.max()), "mean": float(diff.mean()), "share_gt3": float((diff > 3).mean())}
        pool.shutdown()
        del ctxs, pairs
        out["cells"].append(cell)
        print(json.dumps(cell), file=sys.stderr, flush=True)

print(json.dumps(out))

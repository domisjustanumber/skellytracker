# Evidence of ADR-975Z. This scratch script ran on 2026-11-17. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Hang 2 probe: one decode call per variant, with a faulthandler watchdog.

usage: hang2.py --opts ":num_cuda_streams=1" --stream none|private --n 1 [--threads 0] [--session cuda] [--repeat 3] [--warm]
"""
import argparse
import ctypes
import faulthandler
import glob
import os
import pathlib
import sys
import time

import cv2
import numpy as np

p = argparse.ArgumentParser()
p.add_argument("--opts", default="")
p.add_argument("--stream", default="none", choices=["none", "private", "legacy0"])
p.add_argument("--n", type=int, default=1)
p.add_argument("--threads", type=int, default=0)
p.add_argument("--session", default="")
p.add_argument("--repeat", type=int, default=1)
p.add_argument("--warm", action="store_true", help="first decode with a default decoder (as sync_pixels.py)")
p.add_argument("--watchdog", type=float, default=30)
a = p.parse_args()
faulthandler.dump_traceback_later(a.watchdog, exit=True)

from nvidia import nvimgcodec  # noqa: E402

print(f"cpu_count {os.cpu_count()} args {vars(a)}", flush=True)
path = sorted(glob.glob(str(pathlib.Path.home() / ".cache/skellytracker/test_images/*.jpg")))[0]
img = cv2.resize(cv2.imread(path), (1280, 720), interpolation=cv2.INTER_AREA)
jpeg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90, cv2.IMWRITE_JPEG_SAMPLING_FACTOR, cv2.IMWRITE_JPEG_SAMPLING_FACTOR_422])[1].tobytes()

sess = None
if a.session:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "specs" / "model-sidecar" / "decisions" / "scripts"))
    from gpu_preprocess_graphs import session as mk_session, model_file, YOLOX  # noqa: E402
    from skellytracker.core.detectors.catalog import load_detector_sidecar  # noqa: E402
    sc = load_detector_sidecar(YOLOX, None)
    sess, _ = mk_session(model_file(sc, pathlib.Path(os.environ["MAIN_MODEL_ZOO"]) / "detectors"), a.session, "yolox")

stream = None
if a.stream == "private":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "specs" / "model-sidecar" / "decisions" / "scripts"))
    from gpu_preprocess_graphs import load_cudart  # noqa: E402
    cudart = load_cudart(None)
    h = ctypes.c_void_p()
    assert cudart.cudaStreamCreateWithFlags(ctypes.byref(h), 1) == 0  # noqa: S101
    stream = h.value
elif a.stream == "legacy0":
    stream = 0

if a.warm:
    np.asarray(nvimgcodec.Decoder().decode(jpeg).cpu())
    print("warm decode done", flush=True)

kw = {"options": a.opts} if a.opts else {}
dec = nvimgcodec.Decoder(max_num_cpu_threads=a.threads, **kw)
src = jpeg if a.n == 0 else [jpeg] * a.n  # n=0: bare bytes (decode(src)), else a list
for r in range(a.repeat):
    t = time.perf_counter()
    print(f"decode {r} start", flush=True)
    out = dec.decode(src, cuda_stream=stream) if stream is not None else dec.decode(src)
    first = out if a.n == 0 else out[0]
    host = np.asarray(first.cpu())
    print(f"decode {r} done {time.perf_counter() - t:.3f}s shape {host.shape} mean {host.mean():.2f}", flush=True)
print("main done", flush=True)
faulthandler.cancel_dump_traceback_later()

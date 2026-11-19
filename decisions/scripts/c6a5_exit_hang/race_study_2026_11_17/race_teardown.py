# Evidence of ADR-C6A5. This scratch script ran on 2026-11-17. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Decode -> preprocess graph -> model, as the race script (with the wait), then one explicit close order.

usage: race_teardown.py --order interp|fwd|rev|osexit [--gc] [--ep cuda] [--iters 50] --photo P
interp: keep every object as a module global and let interpreter shutdown free it.
fwd:    bindings + OrtValues, sessions, decoded images, decoder, private stream.
rev:    private stream, decoder, decoded images, sessions, bindings + OrtValues.
osexit: os._exit(0) after the work, with every object alive.
"""
import argparse
import atexit
import ctypes  # noqa: F401
import faulthandler
import gc
import os
from pathlib import Path
import sys
import time

SCRIPTS = str(Path(__file__).resolve().parents[4] / "specs" / "model-sidecar" / "decisions" / "scripts")
ZOO = os.path.join(os.environ["MAIN_MODEL_ZOO"], "detectors")
sys.path.insert(0, SCRIPTS)
T0 = time.perf_counter()
atexit.register(lambda: print(f"MARK atexit ran t={time.perf_counter() - T0:.1f}s", flush=True))

import cv2  # noqa: E402
from gpu_preprocess_graphs import YOLOX, DeviceDecoder, frame_inputs, load_cudart, model_file, preprocess_graph, session  # noqa: E402

from skellytracker.core.detectors.catalog import load_detector_sidecar  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--order", required=True, choices=["interp", "fwd", "rev", "osexit"])
p.add_argument("--gc", action="store_true")
p.add_argument("--ep", default="cuda")
p.add_argument("--iters", type=int, default=50)
p.add_argument("--photo", required=True)
p.add_argument("--watchdog", type=float, default=100)
a = p.parse_args()
faulthandler.dump_traceback_later(a.watchdog, exit=True)

photo = cv2.imread(a.photo)
h, w = photo.shape[:2]
flags = [cv2.IMWRITE_JPEG_QUALITY, 90, cv2.IMWRITE_JPEG_SAMPLING_FACTOR, cv2.IMWRITE_JPEG_SAMPLING_FACTOR_422]
jpegs = [cv2.imencode(".jpg", im, flags)[1].tobytes() for im in (photo, cv2.flip(photo, 0))]
cudart = load_cudart(None)
decoder = DeviceDecoder(cudart)
sidecar = load_detector_sidecar(YOLOX, None)
model, _ = session(model_file(sidecar, __import__("pathlib").Path(ZOO)), a.ep, "yolox")
pre, _ = session(preprocess_graph(sidecar, w, h), a.ep, "letterbox graph")
m_in = model.get_inputs()[0].name
for i in range(a.iters):
    images = decoder.decode([jpegs[(i + k) % 2] for k in range(3)], wait=True)
    inputs = frame_inputs(images)
    b_pre = pre.io_binding()
    for name, value in inputs.items():
        b_pre.bind_ortvalue_input(name, value)
    for o in pre.get_outputs():
        b_pre.bind_output(o.name, "cuda", 0)
    pre.run_with_iobinding(b_pre)
    b_pre.synchronize_outputs()
    tensor = b_pre.get_outputs()[0]
    b_model = model.io_binding()
    b_model.bind_ortvalue_input(m_in, tensor)
    for o in model.get_outputs():
        b_model.bind_output(o.name, "cuda", 0)
    model.run_with_iobinding(b_model)
    b_model.synchronize_outputs()
    outputs = b_model.get_outputs()
print(f"MARK work done iters={a.iters} out={outputs[0].shape()}", flush=True)


def close_ort():
    global b_pre, b_model, inputs, tensor, outputs
    del b_pre, b_model, inputs, tensor, outputs


def close_sessions():
    global model, pre
    del model, pre


def close_images():
    global images
    del images


def close_decoder():
    del decoder.decoder


def close_stream():
    print(f"  cudaStreamDestroy -> {cudart.cudaStreamDestroy(decoder.stream)}", flush=True)


steps = {"fwd": [close_ort, close_sessions, close_images, close_decoder, close_stream],
         "rev": [close_stream, close_decoder, close_images, close_sessions, close_ort]}.get(a.order, [])
for step in steps:
    step()
    print(f"  closed {step.__name__}", flush=True)
if a.gc:
    print(f"  gc.collect -> {gc.collect()}", flush=True)
if a.order == "osexit":
    print("MARK done (os._exit)", flush=True)
    sys.stderr.flush()
    os._exit(0)
faulthandler.cancel_dump_traceback_later()
print("main returned; MARK done", flush=True)

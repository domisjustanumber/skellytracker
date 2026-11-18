"""Evidence of ADR-88ZB: the GPU JPEG decoder of the EP store component decodes on each EP.

Run one EP for each process, after `skellytracker-eps install <key>` installed the pack and the
component `gpu-jpeg-cu13`::

    uv run python decisions/scripts/88zb_store_decoder_check.py cuda
    uv run python decisions/scripts/88zb_store_decoder_check.py trt-rtx

It builds one session on the probe model, then calls `registration.prepare_jpeg_decoder()`. It
decodes one synthetic 640x480 JPEG (quality 90) on a private non-blocking CUDA stream, waits with
`cudaStreamSynchronize` of the CUDA runtime of the component, and compares the pixels with
`cv2.imdecode`: at most 3 `uint8` steps. It keeps the default thread and stream counts and turns off
the EXIF orientation. It prints the loaded decoder libraries. It writes no file.
"""
import ctypes
import os
import sys

import cv2
import numpy as np

from skellytracker.core._hardware.libraries import loaded_module_paths
from skellytracker.core.eps import build_session, registration
from skellytracker.core.eps._probe_model import model_bytes


def check(ok, what: str) -> None:
    if not ok:
        raise SystemExit(f"FAIL: {what}")


ep = sys.argv[1]
session, report = build_session(model_bytes(), execution_provider=ep)
print("session", report.used_ep, report.pack_id, report.pack_version)
nvimgcodec, cudart_path = registration.prepare_jpeg_decoder(ep)
print("nvimgcodec", nvimgcodec.__version__, "from store:", "gpu-jpeg-cu13" in nvimgcodec.__file__, "| cudart:", cudart_path.name)
cudart = ctypes.CDLL(str(cudart_path))
stream = ctypes.c_void_p()
check(cudart.cudaStreamCreateWithFlags(ctypes.byref(stream), 1) == 0, "cudaStreamCreateWithFlags")  # 1: cudaStreamNonBlocking
y, x = np.mgrid[0:480, 0:640]
picture = np.dstack([(x * 255 // 639), (y * 255 // 479), ((x + y) % 256)]).astype(np.uint8)
picture = cv2.GaussianBlur(picture + np.random.default_rng(0).integers(0, 30, picture.shape, dtype=np.uint8), (5, 5), 0)
ok, jpeg = cv2.imencode(".jpg", picture, [cv2.IMWRITE_JPEG_QUALITY, 90])
check(ok, "cv2.imencode")
# GPU_ONLY alone gives ARCH_MISMATCH (status 7): the nvJPEG CUDA decoder is a hybrid backend. No CPU-only decoder.
decoder = nvimgcodec.Decoder(backends=[nvimgcodec.Backend(nvimgcodec.BackendKind.GPU_ONLY),
                                       nvimgcodec.Backend(nvimgcodec.BackendKind.HYBRID_CPU_GPU)])
images = decoder.decode([jpeg.tobytes()], params=nvimgcodec.DecodeParams(apply_exif_orientation=False), cuda_stream=stream.value)
check(cudart.cudaStreamSynchronize(stream) == 0, "cudaStreamSynchronize")
print("buffer kind", images[0].buffer_kind)
bgr = np.ascontiguousarray(np.asarray(images[0].cpu())[..., ::-1])
reference = cv2.imdecode(jpeg, cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION)
diff = np.abs(bgr.astype(np.int16) - reference.astype(np.int16))
print("shape", bgr.shape, "max diff", int(diff.max()), "mean", round(float(diff.mean()), 4))
for path in sorted(set(loaded_module_paths())):
    if any(mark in os.path.basename(path).lower() for mark in ("cudart", "nvjpeg", "nvimgcodec")):
        print("  loaded", path.split("eps\\")[-1].split("site-packages\\")[-1])
del images, decoder
check(cudart.cudaStreamDestroy(stream) == 0, "cudaStreamDestroy")
check(diff.max() <= 3, "at most 3 uint8 steps")
print("PASS", ep)

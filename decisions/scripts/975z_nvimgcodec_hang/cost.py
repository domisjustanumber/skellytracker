# Evidence of ADR-975Z. This scratch script ran on 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""The time of NvJpegDecoder.open() with and without the self-test, and of the first decodes. usage: cost.py with|without"""
import sys
import time

import cv2
import numpy as np

from skellytracker.core.decode.nvidia import NvJpegDecoder
from skellytracker.core.eps import registration

if sys.argv[1] == "without":
    NvJpegDecoder._self_test = lambda self: None  # the open of HEAD 326359bf, with no test decode
registration.prepare_jpeg_decoder("cuda")  # the import, outside the measured open
import onnxruntime  # noqa: E402,F401  the decode imports it: keep it outside the measured decode

y, x = np.mgrid[0:720, 0:1280]
jpeg = cv2.imencode(".jpg", np.dstack([x % 256, y % 256, (x + y) % 256]).astype(np.uint8))[1].tobytes()
t = time.perf_counter()
decoder = NvJpegDecoder.open("cuda")
opened = time.perf_counter() - t
times = []
for _ in range(3):
    t = time.perf_counter()
    (frame,) = decoder.decode([jpeg], [0])
    times.append(time.perf_counter() - t)
    del frame
decoder.close()
print(f"exit-check {sys.argv[1]}: open {opened * 1000:.1f} ms, decodes of one 1280x720 frame {' '.join(f'{v * 1000:.1f}' for v in times)} ms", flush=True)
print("main done", flush=True)

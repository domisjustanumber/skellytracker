# Evidence of ADR-975Z. This scratch script ran on 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""The package decoder in a process limited to K cores. usage: core.py K"""
import sys

import psutil

psutil.Process().cpu_affinity(list(range(int(sys.argv[1]))))  # before any other import

import os  # noqa: E402

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from skellytracker.core.decode import nvidia  # noqa: E402
from skellytracker.core.decode.nvidia import NvJpegDecoder  # noqa: E402

print(f"affinity {psutil.Process().cpu_affinity()} process_cpu_count {os.process_cpu_count()} cpu_count {os.cpu_count()} "
      f"cuda_threads {nvidia.cuda_threads()}", flush=True)
decoder = NvJpegDecoder.open("cuda")
print("open", decoder is not None, flush=True)
jpeg = cv2.imencode(".jpg", np.full((48, 64, 3), 100, np.uint8))[1].tobytes()
for i in range(3):
    (frame,) = decoder.decode([jpeg], [0])
    print(f"decode {i} done {frame.width}x{frame.height}", flush=True)
    del frame
decoder.close()
print("main done", flush=True)

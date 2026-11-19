# Evidence of ADR-975Z. This scratch script ran on 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""NvJpegDecoder.open() with the library Decoder forced to T threads and S streams (test-only wrap, no package change).

usage: forced.py T S [--env-at-create]
--env-at-create: set NVIMGCODEC_DEFAULT_NUM_CUDA_STREAMS=1 again just before the library Decoder is made (undoes the removal).
"""
import logging
import os
import sys
import time

import cv2
import numpy as np

from skellytracker.core.decode.nvidia import NvJpegDecoder
from skellytracker.core.eps import registration

logging.basicConfig(level=logging.WARNING, format="LOG %(levelname)s %(message)s")
T, S = int(sys.argv[1]), int(sys.argv[2])
nv, _ = registration.prepare_jpeg_decoder("cuda")
library_decoder = nv.Decoder


def forced(**kwargs):
    if "--env-at-create" in sys.argv:
        os.environ["NVIMGCODEC_DEFAULT_NUM_CUDA_STREAMS"] = "1"
    print(f"env at create: {os.environ.get('NVIMGCODEC_DEFAULT_NUM_CUDA_STREAMS')}", flush=True)
    options = kwargs["options"].replace(kwargs["options"].split(" ")[0], f":num_cuda_streams={S}")
    return library_decoder(**{**kwargs, "max_num_cpu_threads": T, "options": options})


nv.Decoder = forced
if "--session" in sys.argv:  # a model session on the cuda EP first, as in a pipeline run
    from skellytracker.core.eps import build_session
    from skellytracker.core.eps._probe_model import model_bytes

    session, _ = build_session(model_bytes(), execution_provider="cuda")
    print("exit-check: session built", flush=True)
t = time.perf_counter()
decoder = NvJpegDecoder.open("cuda")
print(f"open {decoder is not None} {time.perf_counter() - t:.2f}s", flush=True)
if decoder is not None:
    (frame,) = decoder.decode([cv2.imencode(".jpg", np.full((48, 64, 3), 100, np.uint8))[1].tobytes()], [0])
    print(f"decode done {frame.width}x{frame.height}", flush=True)
    del frame
    decoder.close()
print("main done", flush=True)

# Evidence of ADR-975Z. This scratch script ran on 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
# nvImageCodec 0.10: Decoder.decode() of ONE image never returns when num_cuda_streams < max_num_cpu_threads.
# pip install nvidia-nvimgcodec-cu13 nvidia-nvjpeg nvidia-cuda-runtime numpy
# python repro.py single  -> prints "decoding single" and then waits forever (0 % CPU)
# python repro.py batch   -> decodes [jpeg, jpeg] and prints "returned 2"
import sys

import numpy as np
from nvidia import nvimgcodec

pixels = np.tile((np.arange(64, dtype=np.uint8) * 4)[:, None, None], (1, 64, 3))  # 64x64 RGB gradient
jpeg = nvimgcodec.Encoder().encode(pixels, "jpeg")  # JPEG bytes from the library's own encoder
decoder = nvimgcodec.Decoder(max_num_cpu_threads=2, options=":num_cuda_streams=1")
mode = sys.argv[1] if len(sys.argv) > 1 else "single"
print("decoding", mode, flush=True)
result = decoder.decode(jpeg) if mode == "single" else decoder.decode([jpeg, jpeg])
print("returned", 1 if mode == "single" else len(result), flush=True)

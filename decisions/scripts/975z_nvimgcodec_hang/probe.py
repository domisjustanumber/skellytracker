# Evidence of ADR-975Z. This scratch script ran on 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""One nvImageCodec decoder, decodes as asked, prints 'main done' at the end.

usage: probe.py T S|none N [--pre K] [--bad]
T = max_num_cpu_threads, S = :num_cuda_streams option (none: no option), N = images in the last decode.
--pre K: K decodes of 2 images first. --bad: the images have no DHT segments.
The backends and the Huffman option are those of skellytracker/core/decode/nvidia.py.
"""
import ctypes
import sys
import time

import cv2
import numpy as np

from skellytracker.core.eps import registration

T, S, N = int(sys.argv[1]), sys.argv[2], int(sys.argv[3])
pre = int(sys.argv[sys.argv.index("--pre") + 1]) if "--pre" in sys.argv else 0
bad = "--bad" in sys.argv

y, x = np.mgrid[0:240, 0:320]
image = np.dstack([x * 255 // 319, y * 255 // 239, (x + 3 * y) % 256]).astype(np.uint8)
good = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes()


def strip_dht(data: bytes) -> bytes:
    out, i = bytearray(data[:2]), 2
    while i < len(data):
        marker, length = data[i + 1], int.from_bytes(data[i + 2:i + 4], "big")
        if marker == 0xDA:  # start of scan: keep the rest
            out += data[i:]
            break
        if marker != 0xC4:
            out += data[i:i + 2 + length]
        i += 2 + length
    return bytes(out)


jpeg = strip_dht(good) if bad else good
nvimgcodec, cudart_path = registration.prepare_jpeg_decoder("cuda")
cudart = ctypes.CDLL(str(cudart_path))
stream = ctypes.c_void_p()
assert cudart.cudaStreamCreateWithFlags(ctypes.byref(stream), 1) == 0  # noqa: S101
options = (f":num_cuda_streams={S} " if S != "none" else "") + "nvjpeg_cuda_decoder:hybrid_huffman_threshold=500000"
decoder = nvimgcodec.Decoder(device_id=0, max_num_cpu_threads=T, options=options,
                             backends=[nvimgcodec.Backend(nvimgcodec.BackendKind.GPU_ONLY), nvimgcodec.Backend(nvimgcodec.BackendKind.HYBRID_CPU_GPU)])
params = nvimgcodec.DecodeParams(apply_exif_orientation=False, sample_format=nvimgcodec.I_BGR)
for k in range(pre):
    out = decoder.decode([good, good], params=params, cuda_stream=stream.value)
    cudart.cudaStreamSynchronize(stream)
    print(f"pre {k} done {[o is not None for o in out]}", flush=True)
t = time.perf_counter()
print(f"decode n={N} start", flush=True)
out = decoder.decode([jpeg] * N, params=params, cuda_stream=stream.value)
cudart.cudaStreamSynchronize(stream)
print(f"decode n={N} done {time.perf_counter() - t:.3f}s results {[o is not None for o in out]}", flush=True)
print("main done", flush=True)

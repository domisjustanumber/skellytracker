# Evidence of ADR-BP5Y. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Package decoder (threshold 500000 in the code), 3 x 1280x720 camera JPEGs read in place, 50 batches, then exit."""
import os
import sys
from pathlib import Path

from skellytracker.core.decode import nvidia
from skellytracker.core.decode.nvidia import NvJpegDecoder

FRAMES = Path(os.environ["JPEG_FRAMES_DIR"])
bufs = [(FRAMES / f"{c}_1280x720_median.jpg").read_bytes() for c in ("C922", "C930e", "KiyoPro")]
if len(sys.argv) > 2:  # control: the library default threshold
    nvidia.HUFFMAN_GPU_THRESHOLD = "nvjpeg_cuda_decoder:hybrid_huffman_threshold=1000000"
print("module", nvidia.__file__, "option", nvidia.HUFFMAN_GPU_THRESHOLD, flush=True)
dec = NvJpegDecoder.open(sys.argv[1])
print("options", dec._decoder is not None, flush=True)
for _ in range(50):
    frames = dec.decode(bufs, [0, 0, 0])
print("decoded", [None if f is None else "ok" for f in frames], flush=True)
del frames
dec.close()
print("END", flush=True)

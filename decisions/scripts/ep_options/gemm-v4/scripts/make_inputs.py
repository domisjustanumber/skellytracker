"""Fixed random inputs, one per (size, batch). Usage: python -I -B make_inputs.py OUT_DIR"""
import sys
from pathlib import Path

import numpy as np

SHAPES = {"m": (3, 256, 192), "x-384": (3, 384, 288)}
SEEDS = {("m", 1): 1001, ("m", 3): 1003, ("x-384", 1): 2001, ("x-384", 3): 2003}
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
for (size, b), seed in SEEDS.items():
    x = np.random.default_rng(seed).standard_normal((b, *SHAPES[size])).astype(np.float32)
    np.save(out / f"{size}_b{b}.npy", x)
    print(size, b, x.shape, seed, float(x.mean()), float(x.std()))

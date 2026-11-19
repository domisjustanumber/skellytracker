# Evidence of ADR-C6A5. This scratch script ran on 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Read-only: string and import references of each function in RVA ranges of a PE (no disassembler).

usage: pe_region.py <dll> <lo-hi> [<lo-hi> ...]   (hex RVAs)
Also prints the raw bytes before given return RVAs with --ret <rva,...>.
"""
import sys

import pe_probe_lib as L

dll, *args = sys.argv[1:]
rets = []
if "--ret" in args:
    i = args.index("--ret")
    rets = [int(x, 16) for x in args[i + 1].split(",")]
    args = args[:i] + args[i + 2:]
pe, img, funcs, iat = L.load(dll)
for r in rets:
    print(f"bytes before ret {r:#x}:", img[r - 16:r].hex(" "))
for rng in args:
    lo, hi = (int(x, 16) for x in rng.split("-"))
    for f0, f1 in funcs:
        if f1 <= lo or f0 >= hi:
            continue
        refs = [(k, w) for k, _, w in L.scan(img, funcs, iat, f0, f1) if k in ("str", "icall", "lea-iat")]
        if refs:
            print(f"{f0:#x}-{f1:#x}: " + " | ".join(f"{k}:{w}" for k, w in dict.fromkeys(refs)))

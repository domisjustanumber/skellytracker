# Evidence of ADR-C6A5. This scratch script ran on 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Read-only: functions that reference a string (lea rip-relative), with their callers and string refs.

usage: pe_xref.py <dll> <string> [caller depth, default 2]
"""
import struct
import sys

import pe_probe_lib as L

dll, needle = sys.argv[1], sys.argv[2].encode()
depth = int(sys.argv[3]) if len(sys.argv) > 3 else 2
pe, img, funcs, iat = L.load(dll)
text = next(s for s in pe.sections if s.Name.startswith(b".text"))
lo, hi = text.VirtualAddress, text.VirtualAddress + text.Misc_VirtualSize
targets = set()
i = img.find(needle + b"\0")
while i >= 0:
    targets.add(i)
    i = img.find(needle + b"\0", i + 1)
print("string RVAs", [hex(t) for t in targets])
b = img[lo:hi]
starts = [f[0] for f in funcs]
import bisect  # noqa: E402


def func_of(rva):
    k = bisect.bisect_right(starts, rva) - 1
    while k >= 0 and not (funcs[k][0] <= rva < funcs[k][1]):
        k -= 1
    return funcs[k] if k >= 0 else None


def refs_to(pred):
    hits = set()
    for j in range(len(b) - 7):
        if b[j] in (0x48, 0x4C) and b[j + 1] == 0x8D and (b[j + 2] & 0xC7) == 0x05:
            t = lo + j + 7 + struct.unpack_from("<i", b, j + 3)[0]
            if pred(t):
                hits.add(lo + j)
    return hits


def callers(f0):
    hits = set()
    for j in range(len(b) - 5):
        if b[j] == 0xE8 and lo + j + 5 + struct.unpack_from("<i", b, j + 1)[0] == f0:
            f = func_of(lo + j)
            if f:
                hits.add(f)
    return hits


def show(f, indent):
    refs = [(k, w) for k, _, w in L.scan(img, funcs, iat, f[0], f[1]) if k in ("str", "icall")]
    print(" " * indent + f"{f[0]:#x}-{f[1]:#x}: " + " | ".join(f"{k}:{w}" for k, w in dict.fromkeys(refs))[:1500])


level = {func_of(h) for h in refs_to(lambda t: t in targets)} - {None}
for d in range(depth + 1):
    print(f"-- level {d} ({len(level)} functions)")
    for f in sorted(level):
        show(f, 2 * d)
    if d < depth:
        nxt = set()
        for f in level:
            nxt |= callers(f[0])
        level = nxt

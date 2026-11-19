# Evidence of ADR-C6A5. This scratch script ran on 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Read-only PE probe of the CUDA plugin EP DLL: headers, debug dir, imports, and the functions of the hang frames.

usage: pe_probe.py <dll> [frame offsets relative to ReleaseEpFactory, hex ...]
No disassembler: it scans each function body for call rel32, call [rip+x] (IAT) and lea r,[rip+x] (strings).
"""
import bisect
import struct
import sys

import pefile

path = sys.argv[1]
offs = [int(x, 16) for x in sys.argv[2:]]
pe = pefile.PE(path, fast_load=False)
base = pe.OPTIONAL_HEADER.ImageBase
print("file", path)
print("TimeDateStamp", hex(pe.FILE_HEADER.TimeDateStamp), "SizeOfImage", hex(pe.OPTIONAL_HEADER.SizeOfImage),
      "Linker", pe.OPTIONAL_HEADER.MajorLinkerVersion, pe.OPTIONAL_HEADER.MinorLinkerVersion)
for s in pe.sections:
    print(" section", s.Name.rstrip(b"\0").decode(), hex(s.VirtualAddress), hex(s.Misc_VirtualSize))
for d in getattr(pe, "DIRECTORY_ENTRY_DEBUG", []):
    e = d.entry
    if e is not None and hasattr(e, "PdbFileName"):
        g = e
        guid = f"{g.Signature_Data1:08X}{g.Signature_Data2:04X}{g.Signature_Data3:04X}{bytes(g.Signature_Data4).hex().upper()}"
        print(" debug CodeView", e.PdbFileName.rstrip(b"\0").decode(errors="replace"), "guid+age", guid + format(e.Age, "X"))
    else:
        print(" debug type", d.struct.Type)
rich = pe.parse_rich_header()
if rich:
    vals = rich["values"]
    ids = sorted({(vals[i] >> 16, vals[i] & 0xFFFF) for i in range(0, len(vals), 2)}, key=lambda t: -t[1])
    print(" rich (prodid, build) top:", ids[:8])
exports = sorted((e.address, (e.name or b"?").decode()) for e in pe.DIRECTORY_ENTRY_EXPORT.symbols)
print(" exports", exports)
rel = dict((n, a) for a, n in exports)["ReleaseEpFactory"]  # noqa: C402
iat = {}
crt = []
for imp in pe.DIRECTORY_ENTRY_IMPORT:
    dll = imp.dll.decode()
    for f in imp.imports:
        name = (f.name or b"#%d" % f.ordinal).decode()
        iat[f.address - base] = f"{dll}!{name}"
        if dll.lower().startswith(("msvcp140", "vcruntime")) and any(k in name for k in ("Cnd", "Thrd", "Mtx", "thread", "Thread", "cond", "condition", "atexit", "_Init_thread")):
            crt.append(f"{dll}!{name}")
print(" imported DLLs", [i.dll.decode() for i in pe.DIRECTORY_ENTRY_IMPORT])
print(" thread/cv imports", sorted(crt))
# .pdata: function ranges
pdata = next(s for s in pe.sections if s.Name.startswith(b".pdata"))
raw = pdata.get_data()
funcs = sorted(struct.unpack_from("<III", raw, i)[:2] for i in range(0, pdata.Misc_VirtualSize - 11, 12))
starts = [f[0] for f in funcs]
img = pe.get_memory_mapped_image()


def func_of(rva):
    i = bisect.bisect_right(starts, rva) - 1
    while i >= 0 and not (funcs[i][0] <= rva < funcs[i][1]):
        i -= 1
    return funcs[i] if i >= 0 else None


def cstr(rva):
    if not (0 <= rva < len(img)):
        return None
    end = img.find(b"\0", rva, rva + 200)
    s = img[rva:end] if end > 0 else b""
    if len(s) >= 4 and all(32 <= c < 127 for c in s):
        return s.decode()
    w = img[rva:rva + 160]
    try:
        t = w.decode("utf-16-le").split("\0")[0]
        if len(t) >= 4 and t.isprintable():
            return "L" + t
    except UnicodeDecodeError:
        pass
    return None


def scan(lo, hi):
    out = []
    b = img[lo:hi]
    for i in range(len(b) - 6):
        if b[i] == 0xE8:  # call rel32
            t = lo + i + 5 + struct.unpack_from("<i", b, i + 1)[0]
            f = func_of(t)
            if f and f[0] == t:
                out.append(("call", i, hex(t)))
        if b[i] == 0xFF and b[i + 1] == 0x15:  # call [rip+disp32]
            t = lo + i + 6 + struct.unpack_from("<i", b, i + 2)[0]
            if t in iat:
                out.append(("icall", i, iat[t]))
        if b[i] in (0x48, 0x4C) and b[i + 1] == 0x8D and (b[i + 2] & 0xC7) == 0x05:  # lea r64,[rip+disp32]
            t = lo + i + 7 + struct.unpack_from("<i", b, i + 3)[0]
            s = cstr(t)
            if s:
                out.append(("str", i, s[:120]))
            elif t in iat:
                out.append(("lea-iat", i, iat[t]))
    return out


for off in offs:
    ret = rel + off
    f = func_of(ret - 1)
    print(f"\n== frame ReleaseEpFactory+{off:#x}: return RVA {ret:#x}", end=" ")
    if not f:
        print("(no pdata function)")
        continue
    print(f"in function {f[0]:#x}-{f[1]:#x} (size {f[1]-f[0]}), ret at +{ret-f[0]:#x}")
    seen = set()
    for kind, i, what in scan(f[0], f[1]):
        key = (kind, what)
        if kind == "call" and key in seen:
            continue
        seen.add(key)
        mark = " <== return here" if f[0] + i < ret <= f[0] + i + 7 and kind in ("call", "icall") else ""
        print(f"   +{i:#06x} {kind:6} {what}{mark}")

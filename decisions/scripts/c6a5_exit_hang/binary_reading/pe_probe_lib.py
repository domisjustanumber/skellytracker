# Evidence of ADR-C6A5. This scratch script ran on 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Shared helpers of pe_region.py (read-only PE scanning, no disassembler)."""
import bisect  # noqa: F401
import struct

import pefile


def load(path):
    pe = pefile.PE(path, fast_load=False)
    base = pe.OPTIONAL_HEADER.ImageBase
    iat = {}
    for imp in pe.DIRECTORY_ENTRY_IMPORT:
        for f in imp.imports:
            iat[f.address - base] = f"{imp.dll.decode()}!{(f.name or b'#%d' % f.ordinal).decode()}"
    pdata = next(s for s in pe.sections if s.Name.startswith(b".pdata"))
    raw = pdata.get_data()
    funcs = sorted(struct.unpack_from("<II", raw, i) for i in range(0, pdata.Misc_VirtualSize - 11, 12))
    funcs = [f for f in funcs if f[0]]
    return pe, pe.get_memory_mapped_image(), funcs, iat


def cstr(img, rva):
    if not (0 <= rva < len(img)):
        return None
    end = img.find(b"\0", rva, rva + 200)
    s = img[rva:end] if end > 0 else b""
    if len(s) >= 4 and all(32 <= c < 127 for c in s):
        return s.decode()
    try:
        t = img[rva:rva + 160].decode("utf-16-le").split("\0")[0]
        if len(t) >= 4 and t.isprintable() and t.isascii():
            return "L" + t
    except UnicodeDecodeError:
        pass
    return None


def scan(img, funcs, iat, lo, hi):
    starts = {f[0] for f in funcs}
    out = []
    b = img[lo:hi]
    for i in range(len(b) - 6):
        if b[i] == 0xE8:
            t = lo + i + 5 + struct.unpack_from("<i", b, i + 1)[0]
            if t in starts:
                out.append(("call", i, hex(t)))
        if b[i] == 0xFF and b[i + 1] == 0x15:
            t = lo + i + 6 + struct.unpack_from("<i", b, i + 2)[0]
            if t in iat:
                out.append(("icall", i, iat[t]))
        if b[i] in (0x48, 0x4C) and b[i + 1] == 0x8D and (b[i + 2] & 0xC7) == 0x05:
            t = lo + i + 7 + struct.unpack_from("<i", b, i + 3)[0]
            s = cstr(img, t)
            if s:
                out.append(("str", i, s[:100]))
            elif t in iat:
                out.append(("lea-iat", i, iat[t]))
    return out

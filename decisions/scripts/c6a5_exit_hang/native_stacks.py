# Evidence of ADR-C6A5. This scratch script ran on 2026-11-18 and 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Native stacks of each thread of a process, with the Windows dbghelp.dll only (no debugger, no PDBs).

usage: native_stacks.py <pid>
Symbols are the nearest export of each module (as py-spy shows them); a frame of a module with no
exports shows module+offset. It suspends each thread for the walk and resumes it after.
"""
import ctypes
import sys
from ctypes import wintypes as w

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
dbg = ctypes.WinDLL("dbghelp", use_last_error=True)
PROCESS_ALL_ACCESS, THREAD_ALL_ACCESS = 0x1F0FFF, 0x1F03FF
TH32CS_SNAPTHREAD, CONTEXT_FULL = 0x4, 0x10000B


class THREADENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("th32ThreadID", w.DWORD), ("th32OwnerProcessID", w.DWORD),
                ("tpBasePri", w.LONG), ("tpDeltaPri", w.LONG), ("dwFlags", w.DWORD)]


class ADDRESS64(ctypes.Structure):
    _fields_ = [("Offset", ctypes.c_uint64), ("Segment", w.WORD), ("Mode", ctypes.c_int)]


class STACKFRAME64(ctypes.Structure):
    _fields_ = [("AddrPC", ADDRESS64), ("AddrReturn", ADDRESS64), ("AddrFrame", ADDRESS64), ("AddrStack", ADDRESS64),
                ("AddrBStore", ADDRESS64), ("FuncTableEntry", ctypes.c_void_p), ("Params", ctypes.c_uint64 * 4),
                ("Far", w.BOOL), ("Virtual", w.BOOL), ("Reserved", ctypes.c_uint64 * 3),
                ("KdHelp", ctypes.c_byte * 512)]  # KDHELP64 is smaller; the slack is safe


dbg.StackWalk64.argtypes = [w.DWORD, w.HANDLE, w.HANDLE, ctypes.POINTER(STACKFRAME64), ctypes.c_void_p,
                            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
dbg.SymFunctionTableAccess64.restype = ctypes.c_void_p
dbg.SymFunctionTableAccess64.argtypes = [w.HANDLE, ctypes.c_uint64]
dbg.SymGetModuleBase64.restype = ctypes.c_uint64
dbg.SymGetModuleBase64.argtypes = [w.HANDLE, ctypes.c_uint64]
dbg.SymFromAddrW.argtypes = [w.HANDLE, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_void_p]
dbg.SymInitializeW.argtypes = [w.HANDLE, w.LPCWSTR, w.BOOL]
k32.OpenProcess.restype = k32.OpenThread.restype = k32.CreateToolhelp32Snapshot.restype = w.HANDLE
k32.K32GetModuleBaseNameW.argtypes = [w.HANDLE, ctypes.c_void_p, w.LPWSTR, w.DWORD]
k32.GetThreadContext.argtypes = [w.HANDLE, ctypes.c_void_p]
FTA = ctypes.cast(dbg.SymFunctionTableAccess64, ctypes.c_void_p)
GMB = ctypes.cast(dbg.SymGetModuleBase64, ctypes.c_void_p)


def threads(pid):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    entry = THREADENTRY32(dwSize=ctypes.sizeof(THREADENTRY32))
    ok = k32.Thread32First(snap, ctypes.byref(entry))
    found = []
    while ok:
        if entry.th32OwnerProcessID == pid:
            found.append(entry.th32ThreadID)
        ok = k32.Thread32Next(snap, ctypes.byref(entry))
    k32.CloseHandle(snap)
    return found


def name_of(proc, pc):
    base = dbg.SymGetModuleBase64(proc, pc)
    module = ctypes.create_unicode_buffer(260)
    k32.K32GetModuleBaseNameW(proc, ctypes.c_void_p(base), module, 260) if base else None
    buf = ctypes.create_string_buffer(88 + 2 * 512)
    ctypes.memmove(buf, ctypes.byref(ctypes.c_ulong(88)), 4)  # SizeOfStruct
    ctypes.memmove(ctypes.addressof(buf) + 80, ctypes.byref(ctypes.c_ulong(512)), 4)  # MaxNameLen
    disp = ctypes.c_uint64()
    if dbg.SymFromAddrW(proc, pc, ctypes.byref(disp), buf):
        name = ctypes.wstring_at(ctypes.addressof(buf) + 84)
        return f"{module.value}!{name}+{disp.value:#x}"
    return f"{module.value or '?'}+{pc - base:#x}" if base else f"{pc:#x}"


def main(pid):
    proc = k32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not proc:
        sys.exit(f"OpenProcess failed: {ctypes.get_last_error()}")
    dbg.SymSetOptions(0x2 | 0x4)  # SYMOPT_UNDNAME | SYMOPT_DEFERRED_LOADS
    dbg.SymInitializeW(proc, None, True)
    for tid in threads(pid):
        th = k32.OpenThread(THREAD_ALL_ACCESS, False, tid)
        k32.SuspendThread(th)
        try:
            raw = ctypes.create_string_buffer(1232 + 16)
            ctx = (ctypes.addressof(raw) + 15) & ~15  # CONTEXT is 16-byte aligned
            ctypes.memmove(ctx + 0x30, ctypes.byref(ctypes.c_ulong(CONTEXT_FULL)), 4)
            if not k32.GetThreadContext(th, ctypes.c_void_p(ctx)):
                print(f"Thread {tid}: GetThreadContext failed {ctypes.get_last_error()}")
                continue
            rd = lambda off: ctypes.c_uint64.from_address(ctx + off).value  # noqa: B023, E731
            frame = STACKFRAME64()
            frame.AddrPC = ADDRESS64(rd(0xF8), 0, 3)
            frame.AddrFrame = ADDRESS64(rd(0xA0), 0, 3)
            frame.AddrStack = ADDRESS64(rd(0x98), 0, 3)
            print(f"Thread {tid}:")
            for _ in range(64):
                if not dbg.StackWalk64(0x8664, proc, th, ctypes.byref(frame), ctypes.c_void_p(ctx), None,
                                       FTA, GMB, None) or not frame.AddrPC.Offset:
                    break
                print(f"    {name_of(proc, frame.AddrPC.Offset)}")
        finally:
            k32.ResumeThread(th)
            k32.CloseHandle(th)
    dbg.SymCleanup(proc)


if __name__ == "__main__":
    main(int(sys.argv[1]))

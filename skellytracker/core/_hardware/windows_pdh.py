"""Windows PDH: the dedicated VRAM of each process, summed over all GPUs of each vendor.

The counter is `\\GPU Process Memory(*)\\Dedicated Usage`. Its instance names have the form
`pid_<pid>_luid_0x<hi>_0x<lo>_phys_<n>`. Windows 10 1709 or later. Import this module only on Windows.
"""

import ctypes
import re
import threading
import weakref
from ctypes import wintypes

COUNTER = r"\GPU Process Memory(*)\Dedicated Usage"
PDH_MORE_DATA = 0x800007D2
PDH_CSTATUS_NO_OBJECT = 0xC0000BB8
PDH_FMT_LARGE = 0x400
_PID = re.compile(r"^pid_(\d+)_", re.IGNORECASE)


class _Item(ctypes.Structure):
    _fields_ = [("name", wintypes.LPWSTR), ("status", wintypes.DWORD), ("value", ctypes.c_longlong)]


def sum_by_pid(items) -> dict[int, int]:
    """The sum of the values of each pid. `items` gives `(instance name, status, value)`; a bad status is skipped."""
    totals: dict[int, int] = {}
    for name, status, value in items:
        match = _PID.match(name or "")
        if match and status in (0, 1):  # PDH_CSTATUS_VALID_DATA, PDH_CSTATUS_NEW_DATA
            totals[int(match.group(1))] = totals.get(int(match.group(1)), 0) + int(value)
    return totals


class GpuProcessMemory:
    """One PDH query. `read()` gives the dedicated VRAM bytes of each pid that has an instance."""

    def __init__(self, pdh=None) -> None:
        self._pdh = pdh or ctypes.WinDLL("pdh")
        self._lock = threading.Lock()
        self._query = self._counter = None
        self.unavailable: str | None = None  # the cached reason when the counter does not exist

    def _open(self) -> None:
        query, counter = wintypes.HANDLE(), wintypes.HANDLE()
        status = self._pdh.PdhOpenQueryW(None, 0, ctypes.byref(query)) & 0xFFFFFFFF
        if status == 0:
            status = self._pdh.PdhAddEnglishCounterW(query, COUNTER, 0, ctypes.byref(counter)) & 0xFFFFFFFF
        if status != 0:
            self.unavailable = f"PDH status {status:#010x}" + (" (no GPU counters)" if status == PDH_CSTATUS_NO_OBJECT else "")
            return
        self._query, self._counter = query, counter
        weakref.finalize(self, _close, self._pdh, query, self._lock)

    def read(self) -> dict[int, int]:
        """The dedicated VRAM bytes of each pid. It raises `OSError` when the counter does not exist or a read fails."""
        with self._lock:
            if self._query is None and self.unavailable is None:
                self._open()
            if self.unavailable is not None:
                raise OSError(self.unavailable)
            self._pdh.PdhCollectQueryData(self._query)
            size, count = wintypes.DWORD(0), wintypes.DWORD(0)
            status = self._pdh.PdhGetFormattedCounterArrayW(self._counter, PDH_FMT_LARGE, ctypes.byref(size), ctypes.byref(count), None) & 0xFFFFFFFF
            if status != PDH_MORE_DATA:  # the unsigned compare; no instance gives a different status
                return {}
            buffer = ctypes.create_string_buffer(size.value)
            status = self._pdh.PdhGetFormattedCounterArrayW(self._counter, PDH_FMT_LARGE, ctypes.byref(size), ctypes.byref(count), buffer) & 0xFFFFFFFF
            if status != 0:
                raise OSError(f"PDH status {status:#010x}")
            items = ctypes.cast(buffer, ctypes.POINTER(_Item))
            return sum_by_pid((items[i].name, items[i].status, items[i].value) for i in range(count.value))


def _close(pdh, query, lock) -> None:
    with lock:
        pdh.PdhCloseQuery(query)

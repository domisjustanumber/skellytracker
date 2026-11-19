"""`LiveSampler` and `free_vram(device)`.

The sampler makes no CUDA call and loads no EP library. It does not raise for a missing GPU or a
process that ended: the value is `None` or the pid is in `missing_pids`, with one line in
`sample_errors`. Each `sample()` call is thread-safe. Two owners with two cadences make two samplers.
"""

import os
import sys
import threading
import time
from collections.abc import Iterable

from skellytracker.core._hardware import nvml
from skellytracker.core._hardware.sanitize import error_line
from skellytracker.core.metrics.records import GpuProcessSample, GpuSample, LiveSample, ProcessSample
from skellytracker.core.system.host import gpu_device_keys


def free_vram(device: str) -> int | None:
    """The free VRAM bytes of the GPU with the device key `device`: one NVML read, with no state.

    The value is `None` for an unknown device key and for a GPU with no NVML value. It is the free
    memory of the whole GPU, and it can change before the next call.
    """
    bus = next((gpu.pci_bus_id for key, gpu in gpu_device_keys() if key == device), None)
    return None if bus is None else nvml.free_bytes(bus)


def _reader():
    if sys.platform == "win32":
        from skellytracker.core._hardware import windows as reader
    elif sys.platform == "darwin":
        from skellytracker.core._hardware import darwin as reader
    else:
        from skellytracker.core._hardware import linux as reader
    return reader


def _load_average_1m() -> float | None:
    try:
        return os.getloadavg()[0]
    except (AttributeError, OSError):  # Windows has no `os.getloadavg`
        return None


def _ratio(part: float, whole: float) -> float | None:
    return None if whole <= 0 else min(1.0, max(0.0, part / whole))


class LiveSampler:
    """Samples the CPU, the memory, the asked processes and each NVML GPU."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cpus = os.cpu_count() or 1
        self._reader = _reader()
        self._previous: tuple[int, float, float] | None = None  # perf_counter_ns, busy, total
        self._processes: dict[int, tuple[float, float]] = {}  # pid: (identity, CPU seconds)
        self._pdh = None

    def _process_vram(self, errors: list[str]) -> dict[int, int] | None:
        """The PDH dedicated VRAM of each pid on Windows. `None` off Windows and after a failed read."""
        if sys.platform != "win32":
            return None
        try:
            if self._pdh is None:
                from skellytracker.core._hardware.windows_pdh import GpuProcessMemory

                self._pdh = GpuProcessMemory()
            return self._pdh.read()
        except OSError as error:
            errors.append(error_line("pdh", error))
            return None

    def sample(self, pids: Iterable[object] = ()) -> LiveSample:
        """One sample. A pid that is a `bool`, not an `int` or below 1 raises `ValueError`."""
        asked: list[int] = []
        for pid in pids:
            if isinstance(pid, bool) or not isinstance(pid, int) or pid < 1:
                raise ValueError(f"a pid must be an int of 1 or more, not {pid!r}")
            if pid not in asked:
                asked.append(pid)
        with self._lock:
            now = time.perf_counter_ns()
            errors: list[str] = []
            total, available = self._reader.memory()
            busy, all_time = self._reader.cpu_times()
            window = None if self._previous is None else now - self._previous[0]
            cpu = None if self._previous is None else _ratio(busy - self._previous[1], all_time - self._previous[2])
            self._previous = (now, busy, all_time)
            vram = self._process_vram(errors) if asked else None
            processes, missing, seen = [], [], {}
            for pid in asked:
                try:
                    identity, seconds, rss = self._reader.process(pid)
                except ProcessLookupError:
                    missing.append(pid)
                    continue
                except PermissionError as error:
                    errors.append(error_line(f"process {pid}", error))
                    processes.append(ProcessSample(pid))
                    continue
                before = self._processes.get(pid)
                if before is not None and before[0] != identity:  # the pid has a new process
                    missing.append(pid)
                    continue
                seen[pid] = (identity, seconds)
                share = None if before is None or not window else _ratio(seconds - before[1], window / 1e9 * self._cpus)
                processes.append(ProcessSample(pid, share, rss, None if vram is None else vram.get(pid, 0)))
            self._processes = seen
            gpus = []
            try:
                for bus, utilization, used, free, running in nvml.sample(frozenset(asked)):
                    rows = None if running is None else tuple(GpuProcessSample(pid, bytes_) for pid, bytes_ in running)
                    gpus.append(GpuSample(bus or "nvml", utilization, used, free, rows))
            except nvml.NvmlUnavailableError as error:
                errors.append(error_line("nvml", str(error)))
            return LiveSample(
                perf_counter_ns=now, memory_used_bytes=total - available, memory_available_bytes=available,
                cpu_utilization=cpu, cpu_window_ns=window, processes=tuple(processes), missing_pids=tuple(missing),
                gpus=tuple(sorted(gpus, key=lambda gpu: gpu.key)), sample_errors=tuple(errors),
                load_average_1m=_load_average_1m(),
            )

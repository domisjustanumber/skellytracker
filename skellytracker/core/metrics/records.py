"""The records of `core.metrics`: system-level live values only.

Memory is `int` bytes. Time is `int` ns. A field whose name ends in `utilization` is a `float`
ratio from 0 to 1. A CPU utilization is a share of all logical CPUs.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessSample:
    pid: int
    cpu_utilization: float | None = None
    rss_bytes: int | None = None
    vram_used_bytes: int | None = None  # Windows PDH, summed over all GPUs; None off Windows


@dataclass(frozen=True)
class GpuProcessSample:
    pid: int
    vram_used_bytes: int | None = None  # None under Windows WDDM


@dataclass(frozen=True)
class GpuSample:
    """One NVML GPU. `key` is equal to `GpuInfo.key` of `core.system`."""

    key: str
    utilization: float | None = None
    vram_used_bytes: int | None = None
    vram_free_bytes: int | None = None
    processes: tuple[GpuProcessSample, ...] | None = None


@dataclass(frozen=True)
class LiveSample:
    """The result of `LiveSampler.sample()`. The CPU values are `None` on the first call."""

    perf_counter_ns: int
    memory_used_bytes: int
    memory_available_bytes: int
    cpu_utilization: float | None = None
    cpu_window_ns: int | None = None
    processes: tuple[ProcessSample, ...] = ()
    missing_pids: tuple[int, ...] = ()
    gpus: tuple[GpuSample, ...] = ()
    sample_errors: tuple[str, ...] = ()
    load_average_1m: float | None = None  # `os.getloadavg()[0]`; `None` on Windows or on `OSError`

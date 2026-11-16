"""`LiveSampler`, the PDH reader and `free_vram(device)`."""

import os
import subprocess
import sys

import pytest

from skellytracker.core import metrics
from skellytracker.core._hardware import windows_pdh
from skellytracker.tests.hw_fakes import GIB, FakeNvml, install_nvml, nvml_gpu


class FakeReader:
    """An OS reader with values that a test sets. `processes` maps a pid to its values or to an error."""

    def __init__(self):
        self.busy, self.total, self.processes = 0.0, 0.0, {}

    def memory(self):
        return 16 * GIB, 6 * GIB

    def cpu_times(self):
        return self.busy, self.total

    def process(self, pid):
        value = self.processes.get(pid, ProcessLookupError(pid))
        if isinstance(value, Exception):
            raise value
        return value


@pytest.fixture
def sampler(monkeypatch):
    install_nvml(monkeypatch, FakeNvml([nvml_gpu(processes=((7, 512), (8, None)))]))
    sampler = metrics.LiveSampler()
    sampler._reader, sampler._cpus = FakeReader(), 4
    monkeypatch.setattr(sampler, "_process_vram", lambda errors: {7: 3 * GIB})
    return sampler


def test_first_call_has_no_cpu_values_then_deltas_and_clamps(sampler, monkeypatch):
    clock = iter([1_000_000_000, 2_000_000_000, 3_000_000_000])
    monkeypatch.setattr(metrics.live.time, "perf_counter_ns", lambda: next(clock))
    reader = sampler._reader
    reader.processes = {7: (1.0, 10.0, 100)}
    first = sampler.sample([7])
    assert (first.cpu_utilization, first.cpu_window_ns, first.processes[0].cpu_utilization) == (None, None, None)
    assert (first.memory_used_bytes, first.memory_available_bytes) == (10 * GIB, 6 * GIB)
    reader.busy, reader.total, reader.processes = 2.0, 4.0, {7: (1.0, 12.0, 200)}
    second = sampler.sample([7])
    assert (second.cpu_utilization, second.cpu_window_ns) == (0.5, 1_000_000_000)
    assert second.processes[0] == metrics.ProcessSample(7, 0.5, 200, 3 * GIB)  # 2 s of CPU in 1 s on 4 CPUs
    reader.busy, reader.total, reader.processes = 9.0, 5.0, {7: (1.0, 99.0, 200)}
    third = sampler.sample([7])
    assert third.cpu_utilization == 1.0 and third.processes[0].cpu_utilization == 1.0


def test_dead_reused_and_denied_pids(sampler):
    reader = sampler._reader
    reader.processes = {7: (1.0, 1.0, 100), 9: PermissionError(9)}
    sample = sampler.sample(pid for pid in (7, 8, 9, 7))  # a generator, with a duplicate
    assert [row.pid for row in sample.processes] == [7, 9] and sample.missing_pids == (8,)
    assert sample.processes[1] == metrics.ProcessSample(9) and any("process 9" in line for line in sample.sample_errors)
    reader.processes[7] = (2.0, 0.0, 100)  # the same pid, a new process
    assert sampler.sample([7]).missing_pids == (7,)
    assert sampler.sample([7]).processes[0].cpu_utilization is None  # a new baseline


@pytest.mark.parametrize("pids", [[1, None], [True], [0], [-3], ["4"], [1.0]])
def test_bad_pids_raise_value_error(sampler, pids):
    for _ in range(200):  # each call, not one call in two
        with pytest.raises(ValueError, match="pid"):
            sampler.sample(pids)


def test_gpu_values(sampler):
    (gpu,) = sampler.sample([7, 8]).gpus
    assert (gpu.key, gpu.utilization, gpu.vram_used_bytes, gpu.vram_free_bytes) == ("0000:01:00.0", 0.25, 2 * GIB, 6 * GIB)
    assert gpu.processes == (metrics.GpuProcessSample(7, 512), metrics.GpuProcessSample(8, None))
    assert sampler.sample().gpus[0].processes == ()


def test_gpu_values_that_nvml_does_not_support_are_none(monkeypatch):
    install_nvml(monkeypatch, FakeNvml([nvml_gpu(util=None, free=None)]))
    (gpu,) = metrics.LiveSampler().sample().gpus
    assert (gpu.utilization, gpu.vram_used_bytes, gpu.vram_free_bytes) == (None, None, None)


def test_no_nvml_gives_no_gpus_and_the_cached_line(monkeypatch):
    fake = install_nvml(monkeypatch, FakeNvml(fail="no driver"))
    sampler = metrics.LiveSampler()
    for _ in range(2):
        sample = sampler.sample()
        assert sample.gpus == () and sample.sample_errors == ("nvml: RuntimeError: no driver",)
    assert fake.init_calls == 1


def test_real_sampler_reads_this_process_and_a_dead_process():
    child = subprocess.Popen([sys.executable, "-c", "pass"])  # noqa: S603
    child.wait()
    sampler = metrics.LiveSampler()
    sampler.sample([os.getpid()])
    sum(range(200_000))
    sample = sampler.sample([os.getpid(), child.pid])
    (row,) = sample.processes
    assert row.pid == os.getpid() and row.rss_bytes > 0 and 0.0 <= row.cpu_utilization <= 1.0
    assert sample.missing_pids == (child.pid,) and 0.0 <= sample.cpu_utilization <= 1.0
    assert sample.memory_available_bytes > 0 and sample.cpu_window_ns > 0
    assert (row.vram_used_bytes is None) == (sys.platform != "win32" or any("pdh" in e for e in sample.sample_errors))


def test_free_vram(monkeypatch):
    install_nvml(monkeypatch, FakeNvml([nvml_gpu(), nvml_gpu(bus="00000000:02:00.0", uuid="GPU-b", free=None)]))
    assert metrics.free_vram("gpu:10de:2484:0") == 6 * GIB
    assert metrics.free_vram("gpu:10de:2484:1") is None  # no NVML value
    assert metrics.free_vram("gpu:10de:ffff:0") is None  # no such GPU
    install_nvml(monkeypatch, FakeNvml(fail="no driver"))
    assert metrics.free_vram("gpu:10de:2484:0") is None


def test_pdh_sum_by_pid():
    items = [("pid_100_luid_0x00000000_0x0001ABCD_phys_0", 0, 5), ("PID_100_LUID_0X00000000_0X0001F00D_PHYS_0", 1, 7),
             ("pid_200_luid_0x00000000_0x0001abcd_phys_0", 0xC0000BBA, 9), ("_Total", 0, 99), (None, 0, 1)]
    assert windows_pdh.sum_by_pid(items) == {100: 12}


def test_pdh_missing_counter_is_cached():
    class FakePdh:
        opens = 0

        def PdhOpenQueryW(self, *_):
            self.opens += 1
            return 0

        def PdhAddEnglishCounterW(self, *_):
            return -1073738824  # 0xC0000BB8 as a signed value: the compare must be unsigned

    reader = windows_pdh.GpuProcessMemory(pdh=FakePdh())
    for _ in range(2):
        with pytest.raises(OSError, match="no GPU counters"):
            reader.read()
    assert reader._pdh.opens == 1

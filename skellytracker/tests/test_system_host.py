"""The host readers on fakes, and `probe_host()`."""

import dataclasses
import os
import platform
import sys
import threading

import pytest

from skellytracker.core._hardware import darwin, linux, nvml, pci
from skellytracker.core.system import host as host_module
from skellytracker.core.system.records import GpuInfo
from skellytracker.tests.hw_fakes import FakeNvml, install_nvml, nvml_gpu
from skellytracker.tests.hw_fakes import host as fake_host


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("00000000:01:00.0", "0000:01:00.0"),
        ("0000:01:00.0", "0000:01:00.0"),
        ("@System32\\drivers\\pci.sys,#65536;PCI bus %1, device %2, function %3;(1,0,0)", "0000:01:00.0"),
        ("PCI bus 1, device 0, function 0", "0000:01:00.0"),
        ("00010000:00:00.0", "10000:00:00.0"),
        ("../../devices/pci0000:00/0000:00:02.0", "0000:00:02.0"),
        ("slot 4", None),
    ],
)
def test_normalize_bus_id(text, expected):
    assert pci.normalize_bus_id(text) == expected


def adapter(bus, vendor_id=0x10DE, device_id=0x2484, software=False, luid=1, name="NVIDIA GeForce RTX 3070"):
    return GpuInfo(key=bus or f"luid:{luid:#x}", vendor=pci.vendor_of(vendor_id), name=name, pci_bus_id=bus,
                   pci_vendor_id=vendor_id, pci_device_id=device_id, pci_subsys_id=7, is_software=software, luid=luid,
                   driver_version="32.0.16.1088")


def test_second_adapter_and_software_adapter_are_dropped():
    adapters = [adapter("0000:01:00.0", luid=1), adapter("0000:00:02.0", 0x8086, 0xA780, luid=2, name="UHD 770"),
                adapter(None, luid=3), adapter(None, 0x1414, 0x8C, software=True, luid=4, name="Basic Render")]
    assert [a.luid for a in pci.drop_second_adapters(adapters)] == [1, 2]


def test_merge_keeps_the_os_facts_and_other_vendors(monkeypatch):
    install_nvml(monkeypatch, FakeNvml([nvml_gpu()]))
    amd = adapter("0000:03:00.0", 0x1002, 0x73BF, luid=9, name="Radeon RX 6800")
    merged = host_module.merge_gpus(nvml.read_gpus(), [adapter("0000:01:00.0", luid=5), amd])
    assert [g.key for g in merged] == ["0000:01:00.0", "0000:03:00.0"]
    nvidia, other = merged
    assert nvidia.luid == 5 and nvidia.driver_version == "610.88" and nvidia.vram_total_bytes == 8 * 2**30
    assert nvidia.nvidia.compute_capability == "8.6" and nvidia.nvidia.brand == "geforce"
    assert nvidia.pci_vendor_id == 0x10DE and nvidia.pci_device_id == 0x2484
    assert other.vendor == "amd" and other.driver_version == "32.0.16.1088" and other.nvidia is None


def test_two_identical_gpus_get_two_device_keys(monkeypatch):
    fake = FakeNvml([nvml_gpu(bus="00000000:02:00.0", uuid="GPU-b"), nvml_gpu(bus="00000000:01:00.0", uuid="GPU-a")])
    install_nvml(monkeypatch, fake)
    gpus = host_module.merge_gpus(nvml.read_gpus(), [])
    host = dataclasses.replace(host_module.probe_host(), gpus=gpus)
    keys = host_module.gpu_device_keys(host)
    assert [(key, gpu.pci_bus_id) for key, gpu in keys] == [("gpu:10de:2484:0", "0000:01:00.0"), ("gpu:10de:2484:1", "0000:02:00.0")]


def test_nvml_failure_is_cached_for_the_process_id(monkeypatch):
    fake = install_nvml(monkeypatch, FakeNvml(fail="NVML Shared Library Not Found"))
    for _ in range(2):
        with pytest.raises(nvml.NvmlUnavailableError, match="Not Found"):
            nvml.read_gpus()
    assert fake.init_calls == 1
    assert nvml.free_bytes("0000:01:00.0") is None
    monkeypatch.setattr(os, "getpid", lambda: -5)
    fake.fail = None
    assert nvml.read_gpus() == [] and fake.init_calls == 2


def test_probe_host_does_not_raise_with_no_nvml(monkeypatch):
    install_nvml(monkeypatch, FakeNvml(fail="no driver"))
    info = host_module.probe_host()
    assert any(line.startswith("nvml: ") for line in info.probe_errors)
    assert all(gpu.nvidia is None for gpu in info.gpus)
    assert host_module.probe_host() is info  # cached for the process


def test_probe_host_has_no_hostname(monkeypatch):
    install_nvml(monkeypatch, FakeNvml([nvml_gpu()]))
    info = host_module.probe_host()
    node = platform.node().lower()
    assert info.memory_total_bytes > 0 and info.cpu_logical_cores
    assert info.cpu_max_frequency_hz is None or 2e8 < info.cpu_max_frequency_hz < 1e10
    assert node and node not in repr(dataclasses.asdict(info)).lower()
    assert [g for g in info.gpus if g.nvidia][0].nvidia.uuid.startswith("GPU-")


@pytest.mark.skipif(not hasattr(os, "fork"), reason="fork is POSIX only")
def test_nvml_read_works_in_a_fork_child_while_a_thread_holds_the_locks(monkeypatch):
    fake = install_nvml(monkeypatch, FakeNvml([nvml_gpu()]))
    held, release = threading.Event(), threading.Event()

    def hold():
        with nvml.lock(), fake.libLoadLock:
            held.set()
            release.wait(20)

    thread = threading.Thread(target=hold)
    thread.start()
    held.wait(5)
    pid = os.fork()
    if pid == 0:  # the child: a read must not wait for a lock that the parent thread holds
        ok = len(nvml.read_gpus()) == 1 and fake.shutdown_calls == 0 and not fake.libLoadLock.locked()
        os._exit(0 if ok else 1)
    release.set()
    thread.join()
    assert os.waitpid(pid, 0)[1] == 0


def linux_root(tmp_path):
    for path, text in {
        "proc/cpuinfo": "processor\t: 0\nmodel name\t: AMD Ryzen 7 5800X\nphysical id\t: 0\ncore id\t: 0\n"
                        "flags\t\t: fpu hypervisor\n\nprocessor\t: 1\nmodel name\t: AMD Ryzen 7 5800X\n"
                        "physical id\t: 0\ncore id\t: 1\nflags\t\t: fpu hypervisor\n",
        "proc/meminfo": "MemTotal:       32768000 kB\nMemFree:  100 kB\n",
        "proc/sys/kernel/osrelease": "6.8.0-generic\n",
        "proc/1/cgroup": "0::/docker/abc\n",
        "sys/class/drm/card0/device/uevent": "DRIVER=amdgpu\nPCI_SLOT_NAME=0000:03:00.0\n",
        "sys/class/drm/card0/device/vendor": "0x1002\n",
        "sys/class/drm/card0/device/device": "0x73bf\n",
        "sys/class/drm/card0/device/subsystem_device": "0x0e3a\n",
        "sys/class/drm/card0/device/boot_vga": "1\n",
        "sys/class/drm/card0/device/mem_info_vram_total": "17163091968\n",
        "sys/class/drm/card0-HDMI-A-1/status": "connected\n",
        "sys/module/amdgpu/version": "6.8.5\n",
        "sys/fs/cgroup/cpu.max": "150000 100000\n",
        "sys/fs/cgroup/memory.max": "max\n",
        "etc/os-release": 'NAME="Ubuntu"\nPRETTY_NAME="Ubuntu 24.04 LTS"\n',
    }.items():
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text(text, encoding="utf-8")
    return tmp_path


def test_linux_readers_on_fake_files(tmp_path):
    root = linux_root(tmp_path)
    assert linux.cpu_name(root) == "AMD Ryzen 7 5800X" and linux.cpu_max_frequency_hz(root) is None
    (root / "sys/devices/system/cpu/cpu0/cpufreq").mkdir(parents=True)
    (root / "sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq").write_text("4850195\n", encoding="utf-8")
    assert linux.cpu_max_frequency_hz(root) == 4_850_195_000
    physical, _, memory = linux.cores_and_memory(root)
    assert (physical, memory) == (2, 32768000 * 1024)
    (gpu,) = linux.gpus(root)
    assert (gpu.key, gpu.vendor, gpu.pci_device_id, gpu.driver_version) == ("0000:03:00.0", "amd", 0x73BF, "6.8.5")
    assert gpu.vram_total_bytes == 17163091968 and gpu.is_integrated is True
    virtualization = linux.virtualization(root, detect_virt=False)
    assert (virtualization.is_wsl, virtualization.is_vm, virtualization.hypervisor) == (False, True, "unknown")
    container = linux.container(root, environ={"NVIDIA_VISIBLE_DEVICES": "all", "CUDA_VERSION": "13.0"})
    assert (container.runtime, container.cpu_quota_cores, container.memory_limit_bytes) == ("docker", 1.5, None)
    assert container.base_os == "Ubuntu 24.04 LTS" and container.nvidia.visible_devices == "all"


def test_linux_wsl_and_no_container(tmp_path):
    (tmp_path / "proc/sys/kernel").mkdir(parents=True)
    (tmp_path / "proc/sys/kernel/osrelease").write_text("5.15.167.4-microsoft-standard-WSL2\n", encoding="utf-8")
    assert linux.virtualization(tmp_path, detect_virt=False).is_wsl is True
    assert linux.container(tmp_path, environ={}) is None and linux.gpus(tmp_path) == []


PCI_IDS = ("# a comment line\n"
           "1002  Advanced Micro Devices, Inc. [AMD/ATI]\n"
           "\t73bf  Navi 21 [Radeon RX 6800/6800 XT / 6900 XT]\n"
           "\t\t1002 0e3a  Radeon RX 6900 XT\n"
           "8086  Intel Corporation\n"
           "\t4680  AlderLake-S GT1\n"
           "\t\t8086 73bf  A subsystem line\n"
           "C 03  Display controller\n"
           "\t00  VGA compatible controller\n"
           "8086  A line after the start of the class section\n"
           "\t9999  Not a device\n")


def test_pci_ids_device_name():
    assert pci.device_name(PCI_IDS, 0x8086, 0x4680) == "AlderLake-S GT1"
    assert pci.device_name(PCI_IDS, 0x1002, 0x73BF) == "Navi 21 [Radeon RX 6800/6800 XT / 6900 XT]"
    assert pci.device_name(PCI_IDS, 0x8086, 0x73BF) is None  # a device of an other vendor, and a subsystem line
    assert pci.device_name(PCI_IDS, 0x1002, 0x0E3A) is None  # a subsystem id is not a device id
    assert pci.device_name(PCI_IDS, 0x8086, 0x9999) is None  # after the start of the class section
    assert pci.device_name(PCI_IDS, 0x10DE, 0x2484) is None and pci.device_name("", 0x8086, 0x4680) is None


def test_linux_gpu_name_from_pci_ids(tmp_path):
    root = linux_root(tmp_path)
    assert linux.gpus(root)[0].name is None  # no `pci.ids` file
    for path, text in {"usr/share/misc/pci.ids": PCI_IDS, "sys/class/drm/card1/device/vendor": "0x8086\n",
                       "sys/class/drm/card1/device/device": "0x4680\n",
                       "sys/class/drm/card1/device/uevent": "DRIVER=i915\nPCI_SLOT_NAME=0000:00:02.0\n"}.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text, encoding="utf-8")
    assert {gpu.key: gpu.name for gpu in linux.gpus(root)} == {
        "0000:00:02.0": "AlderLake-S GT1", "0000:03:00.0": "Navi 21 [Radeon RX 6800/6800 XT / 6900 XT]"}
    (root / "usr/share/hwdata").mkdir(parents=True)
    (root / "usr/share/hwdata/pci.ids").write_text("8086  Intel Corporation\n\t4680  The hwdata name\n", encoding="utf-8")
    (root / "sys/class/drm/card0/device/product_name").write_text("AMD Radeon RX 6900 XT\n", encoding="utf-8")
    assert {gpu.key: gpu.name for gpu in linux.gpus(root)} == {  # `hwdata` first; `product_name` before `pci.ids`
        "0000:00:02.0": "The hwdata name", "0000:03:00.0": "AMD Radeon RX 6900 XT"}


def test_darwin_gpus_from_registry_entries():
    # The keys are the IORegistry key names. `ioreg -l -w0 -r -c IOAccelerator` and `-c IOPCIDevice` show them.
    (gpu,) = darwin.gpus_from_registry([{"model": "Apple M2", "vendor-id": bytes.fromhex("6b100000")}])  # Apple Silicon
    assert (gpu.key, gpu.vendor, gpu.name, gpu.pci_bus_id) == ("apple:0:Apple M2", "apple", "Apple M2", None)
    assert gpu.vram_total_bytes is None  # unified memory: no VRAM property
    assert darwin.gpus_from_registry([{"model": "Apple M1 Pro"}])[0].vendor == "apple"
    integrated, discrete = darwin.gpus_from_registry([  # an Intel Mac with a discrete GPU
        {"model": b"Intel UHD Graphics 630\x00", "vendor-id": bytes.fromhex("86800000"), "VRAM,totalMB": bytes.fromhex("00060000")},
        {"model": b"AMD Radeon Pro 5500M\x00", "vendor-id": bytes.fromhex("02100000"), "VRAM,totalMB": 8192},
    ])
    assert (integrated.vendor, integrated.name, integrated.vram_total_bytes) == ("intel", "Intel UHD Graphics 630", 1536 * 2**20)
    assert (discrete.key, discrete.vendor, discrete.vram_total_bytes) == ("apple:1:AMD Radeon Pro 5500M", "amd", 8 * 2**30)
    (unknown,) = darwin.gpus_from_registry([{"model": None, "vendor-id": "wrong type", "VRAM,totalMB": None}])
    assert (unknown.vendor, unknown.name, unknown.vram_total_bytes) == ("other", None, None)


def test_darwin_cpu_max_frequency():
    assert darwin.cpu_max_frequency_hz({"hw.cpufrequency_max": 2_600_000_000, "hw.cpufrequency": 2_400_000_000}.get) == 2_600_000_000
    assert darwin.cpu_max_frequency_hz({"hw.cpufrequency": 2_400_000_000}.get) == 2_400_000_000
    assert darwin.cpu_max_frequency_hz({}.get) is None  # Apple Silicon


@pytest.mark.skipif(sys.platform == "darwin", reason="a host with no IOKit")
def test_darwin_registry_reader_gives_no_entry_with_no_iokit():
    assert darwin.gpu_registry_entries() == [] and darwin.gpus() == []


@pytest.mark.skipif(sys.platform != "win32", reason="the Windows readers")
def test_windows_registry_readers_on_a_fake_registry():
    from skellytracker.core._hardware import windows

    class FakeRegistry:
        HKEY_LOCAL_MACHINE = 0
        values = {("HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0", "ProcessorNameString"): "Intel(R) Core(TM) i7 ",
                  ("HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0", "~MHz"): 3408,
                  ("HARDWARE\\DESCRIPTION\\System\\BIOS", "SystemManufacturer"): "VMware, Inc.",
                  ("HARDWARE\\DESCRIPTION\\System\\BIOS", "SystemProductName"): "VMware Virtual Platform"}

        class OpenKey:
            def __init__(self, _root, key):
                self.key = key

            def __enter__(self):
                return self.key

            def __exit__(self, *_):
                return False

        @classmethod
        def QueryValueEx(cls, key, name):
            if (key, name) not in cls.values:
                raise FileNotFoundError(name)
            return cls.values[(key, name)], 1

    assert windows.cpu_name(FakeRegistry) == "Intel(R) Core(TM) i7"
    assert windows.cpu_max_frequency_hz(FakeRegistry) == 3_408_000_000
    assert windows.cpu_max_frequency_hz(type("NoValue", (FakeRegistry,), {"values": {}})) is None
    assert windows.virtualization(FakeRegistry).hypervisor == "vmware"
    assert windows.container(FakeRegistry) is None


def test_physical_cores_reads_no_gpu_and_gives_the_value_of_a_probed_host(monkeypatch):
    monkeypatch.setattr(host_module, "_cached", None)
    monkeypatch.setattr(nvml, "read_gpus", lambda: pytest.fail("physical_cores() must make no NVML call"))
    found = host_module.physical_cores()
    assert found is None or found >= 1
    monkeypatch.setattr(host_module, "_cached", dataclasses.replace(fake_host(), cpu_physical_cores=8))
    assert host_module.physical_cores() == 8

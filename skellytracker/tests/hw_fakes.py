"""Fakes for the hardware and EP tests: a fake `pynvml` module and fake `HostInfo` records."""

import sys
import threading
import types

from skellytracker.core._hardware import nvml
from skellytracker.core.system import host as host_module
from skellytracker.core.system.records import GpuInfo, HostInfo, NvidiaGpuInfo

GIB = 2**30


class NvmlNotSupportedError(Exception):
    pass


def nvml_gpu(bus="00000000:01:00.0", device_id=0x2484, name="NVIDIA GeForce RTX 3070", total=8 * GIB, free=6 * GIB,
             cc=(8, 6), uuid="GPU-00000000-0000-0000-0000-000000000001", util=25, processes=()) -> dict:
    return {"bus": bus, "device_id": device_id, "name": name, "total": total, "free": free, "cc": cc, "uuid": uuid,
            "util": util, "processes": processes}


class FakeNvml(types.ModuleType):
    """The part of `pynvml` that the readers call. `fail` makes `nvmlInit` raise."""

    def __init__(self, gpus=(), driver="610.88", fail: str | None = None):
        super().__init__("pynvml")
        self.gpus, self.driver, self.fail = list(gpus), driver, fail
        self.init_calls = self.shutdown_calls = 0
        self.libLoadLock = threading.Lock()
        self.NVML_BRAND_GEFORCE = 5  # `dir()` of a module lists only its instance attributes

    def nvmlInit(self):
        self.init_calls += 1
        if self.fail:
            raise RuntimeError(self.fail)

    def nvmlShutdown(self):
        self.shutdown_calls += 1

    def nvmlDeviceGetCount(self):
        return len(self.gpus)

    def nvmlDeviceGetHandleByIndex(self, index):
        return index

    def nvmlDeviceGetPciInfo(self, handle):
        gpu = self.gpus[handle]
        return types.SimpleNamespace(busId=gpu["bus"].encode(), pciDeviceId=gpu["device_id"] << 16 | 0x10DE,
                                     pciSubSystemId=0x37551462)

    def nvmlDeviceGetUUID(self, handle):
        return self.gpus[handle]["uuid"]

    def nvmlDeviceGetName(self, handle):
        return self.gpus[handle]["name"].encode()

    def nvmlSystemGetDriverVersion(self):
        return self.driver

    def nvmlSystemGetCudaDriverVersion(self):
        return 13030

    def nvmlDeviceGetMemoryInfo(self, handle):
        gpu = self.gpus[handle]
        if gpu["free"] is None:
            raise NvmlNotSupportedError
        return types.SimpleNamespace(total=gpu["total"], free=gpu["free"], used=gpu["total"] - gpu["free"])

    def nvmlDeviceGetCudaComputeCapability(self, handle):
        return self.gpus[handle]["cc"]

    def nvmlDeviceGetBrand(self, handle):
        return 5

    def nvmlDeviceGetUtilizationRates(self, handle):
        if self.gpus[handle]["util"] is None:
            raise NvmlNotSupportedError
        return types.SimpleNamespace(gpu=self.gpus[handle]["util"], memory=0)

    def nvmlDeviceGetComputeRunningProcesses(self, handle):
        return [types.SimpleNamespace(pid=pid, usedGpuMemory=used) for pid, used in self.gpus[handle]["processes"]]


def install_nvml(monkeypatch, fake: FakeNvml) -> FakeNvml:
    """Make `fake` the `pynvml` of this test and drop the cached NVML init and the cached host."""
    monkeypatch.setitem(sys.modules, "pynvml", fake)
    monkeypatch.setattr(nvml, "_state", None)
    monkeypatch.setattr(host_module, "_cached", None)
    return fake


def gpu(vendor="nvidia", cc: str | None = "8.6", driver="610.88", vram=8 * GIB, bus="0000:01:00.0", device_id=0x2484,
        name="NVIDIA GeForce RTX 3070", brand="geforce") -> GpuInfo:
    vendor_id = {"nvidia": 0x10DE, "intel": 0x8086, "amd": 0x1002}.get(vendor)
    section = NvidiaGpuInfo(uuid=f"GPU-{bus}", compute_capability=cc, brand=brand) if vendor == "nvidia" else None
    return GpuInfo(key=bus, vendor=vendor, name=name, pci_bus_id=bus, pci_vendor_id=vendor_id, pci_device_id=device_id,
                   driver_version=driver, vram_total_bytes=vram, nvidia=section)


def host(*gpus: GpuInfo, os_name="Windows", arch="AMD64", native_arch=None) -> HostInfo:
    return HostInfo(os_name=os_name, os_release="11", os_version="10.0.26300", arch=arch, memory_total_bytes=64 * GIB,
                    native_arch=native_arch or arch, gpus=tuple(sorted(gpus, key=lambda g: g.key)))


def reviewed_rows_for_each_gpu(monkeypatch) -> None:
    """Make each EP certified on each GPU, so the check rule of `gate.py` lets a test of an other subject run its fake GPUs."""
    from skellytracker.core.eps import evidence

    monkeypatch.setattr(evidence, "certified", lambda key, gpu, os_name: True)


def fake_pack(key: str, files=()) -> None:
    """Write the manifest of the pack of an EP key in the store of this test, with no library."""
    from skellytracker.core.eps import catalog, store

    pack = catalog.load_catalog().pack(key)
    folder = store.pack_dir(pack["id"], pack["version"])
    store.write_json(folder / "pack.json", {"format": 1, "pack_id": pack["id"], "version": pack["version"], "ep_key": key,
                                            "ep_name": pack["ep_name"], "library": "plugin.dll", "files": list(files)})

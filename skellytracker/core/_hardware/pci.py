"""PCI bus ids and PCI vendor ids."""

import re

_HEX = re.compile(r"^([0-9a-fA-F]{4,8}):([0-9a-fA-F]{2}):([0-9a-fA-F]{2})\.([0-7])$")
_WINDOWS = re.compile(r"(?:;\(|PCI bus )(\d+),\s*(?:device )?(\d+),\s*(?:function )?(\d+)\)?$")
_VENDORS = {0x10DE: "nvidia", 0x8086: "intel", 0x1002: "amd", 0x1022: "amd", 0x106B: "apple"}


def bus_id(domain: int, bus: int, device: int, function: int) -> str:
    return f"{domain:04x}:{bus:02x}:{device:02x}.{function:x}"


def normalize_bus_id(text: str) -> str | None:
    """`0000:01:00.0` from an NVML, CUDA, sysfs or Windows `LocationInformation` form; `None` for an unknown form."""
    text = text.strip()
    match = _HEX.match(text.rsplit("/", 1)[-1])
    if match:
        return bus_id(*(int(part, 16) for part in match.groups()))
    match = _WINDOWS.search(text)
    if match:  # the Windows form gives no PCI domain: domain 0 is assumed
        return bus_id(0, *(int(part) for part in match.groups()))
    return None


def vendor_of(pci_vendor_id: int | None) -> str:
    return _VENDORS.get(pci_vendor_id, "other")


def device_name(pci_ids: str, vendor_id: int, device_id: int) -> str | None:
    """The name of a device in the text of a `pci.ids` file; `None` when the file does not hold the ids.

    A vendor line starts with 4 hex digits. A device line starts with one tab and 4 hex digits. A
    subsystem line starts with two tabs. A `#` line is a comment. The class section starts at the
    first `C ` line and ends the read.
    """
    vendor, device, in_vendor = f"{vendor_id:04x}", f"{device_id:04x}", False
    for line in pci_ids.splitlines():
        if line.startswith("C "):
            break
        if not line.strip() or line.startswith(("#", "\t\t")):
            continue
        if not line.startswith("\t"):
            if in_vendor:
                break  # the next vendor: the device is not in the file
            in_vendor = line[:4].lower() == vendor
        elif in_vendor and line[1:5].lower() == device:
            return line[5:].strip() or None
    return None


def drop_second_adapters(adapters: list) -> list:
    """`adapters` (`GpuInfo` records) without each software adapter and without a second adapter of one device.

    An adapter with no bus id is a second adapter when an adapter with a bus id has the same PCI ids.
    """
    adapters = [a for a in adapters if not a.is_software]
    on_bus = {a.pci_bus_id: a for a in adapters if a.pci_bus_id is not None}
    ids = {(a.pci_vendor_id, a.pci_device_id, a.pci_subsys_id) for a in on_bus.values()}
    off_bus = {a.key: a for a in adapters
               if a.pci_bus_id is None and (a.pci_vendor_id, a.pci_device_id, a.pci_subsys_id) not in ids}
    return [*on_bus.values(), *off_bus.values()]

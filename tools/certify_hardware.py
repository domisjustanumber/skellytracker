"""Section 2 of the certify suite (``tools/certify_platform.py``): the hardware probe.

The section records the values of skellytracker (``probe_host()``, ``probe_environment()``,
``eps.status()`` and ``eps.recommend()``, which load no EP library) and the values of each OS tool of
the platform side by side. It flags each difference and does not fail on one: the result is
``record-only``. It is ``fail`` only when ``probe_host()`` raises.

Each OS method is optional. An absent tool or file is ``not-run`` with ``tool-missing``. Each
method has its own time limit. A parser takes only the fields of its allowlist from the tool
output: a model name, a PCI vendor id and device id, a driver version, a memory size, an OS label
and build. It never keeps raw output, a serial number, a UUID or a bus address.

The comparison: the GPU count, each GPU (vendor id, device id, name, driver version, VRAM in MiB),
the CPU name and cores, the memory in MiB, and the OS label, version and build. A GPU matches by its
PCI ids, else by its name. A value that only one side has is recorded, not flagged. A method with
``scope_vendor_id`` (``nvidia-smi``) sees only the GPUs of that vendor. The NVIDIA driver version of
Windows (``32.0.16.1088``) equals the NVML form (``610.88``). Windows ``AdapterRAM`` is a 32-bit
value: from 4 GiB it is capped and not compared. The OS label compares without a first word
``Microsoft`` and with a prefix match, because ``probe_host()`` adds the release (``26H2``).
"""

from __future__ import annotations

import dataclasses
import glob
import json
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MIB = 2**20
METHOD_TIMEOUT = 30
SCALAR_FIELDS = ("os_label", "os_version", "os_build", "cpu_name", "cpu_physical_cores", "cpu_logical_cores", "memory_mib")
GPU_FIELDS = ("name", "driver_version", "vram_mib")


def hex4(value) -> str | None:
    return None if value is None else f"{int(value):04x}"


# --------------------------------------------------------------------------------------------
# Parsers: each takes the text of one tool and returns its allowlisted facts
# --------------------------------------------------------------------------------------------


def _items(text: str) -> list[dict]:
    data = json.loads(text)
    return data if isinstance(data, list) else [data]


def parse_cim_video(text: str) -> dict:
    gpus, other = [], []
    for item in _items(text):
        ids = re.search(r"VEN_([0-9A-F]{4})&DEV_([0-9A-F]{4})", item.get("PNPDeviceID") or "", re.IGNORECASE)
        if ids is None:
            other.append(item.get("Name"))
            continue
        ram = item.get("AdapterRAM")
        capped = isinstance(ram, int) and ram >= 0xFFF00000  # a uint32: a larger VRAM shows as about 4 GiB
        gpus.append({"vendor_id": ids[1].lower(), "device_id": ids[2].lower(), "name": item.get("Name"),
                     "driver_version": item.get("DriverVersion"),
                     "vram_mib": ram // MIB if isinstance(ram, int) and not capped else None,
                     **({"vram_note": "adapter-ram-capped"} if capped else {})})
    return {"gpus": gpus, "non_pci_adapters": other}


def parse_cim_processor(text: str) -> dict:
    items = _items(text)
    return {"cpu_name": " ".join((items[0].get("Name") or "").split()) or None,
            "cpu_physical_cores": sum(item.get("NumberOfCores") or 0 for item in items) or None,
            "cpu_logical_cores": sum(item.get("NumberOfLogicalProcessors") or 0 for item in items) or None,
            "max_clock_mhz": items[0].get("MaxClockSpeed")}


def parse_cim_os(text: str) -> dict:
    item = _items(text)[0]
    memory = item.get("TotalVisibleMemorySize")
    return {"os_label": item.get("Caption"), "os_version": item.get("Version"), "os_build": item.get("BuildNumber"),
            "memory_mib": memory // 1024 if isinstance(memory, int) else None, "os_architecture": item.get("OSArchitecture")}


def parse_nvidia_smi(text: str) -> dict:
    """`--query-gpu=name,driver_version,memory.total,pci.device_id --format=csv,noheader`."""
    gpus = []
    for line in filter(str.strip, text.splitlines()):
        name, driver, memory, ids = (part.strip() for part in line.rsplit(",", 3))
        number = int(ids, 16)  # 0xDDDDVVVV: the device id, then the vendor id
        size = re.match(r"\d+", memory)
        gpus.append({"vendor_id": hex4(number & 0xFFFF), "device_id": hex4(number >> 16), "name": name,
                     "driver_version": driver, "vram_mib": int(size[0]) if size else None})
    return {"scope_vendor_id": "10de", "gpus": gpus}


def parse_os_release(text: str) -> dict:
    values = dict(re.findall(r'^([A-Z_]+)="?([^"\n]*)"?$', text, re.MULTILINE))
    return {"os_label": values.get("PRETTY_NAME"), "os_id": values.get("ID"), "os_version_id": values.get("VERSION_ID")}


def parse_uname(text: str) -> dict:
    return {"os_build": text.strip() or None}


def parse_lspci(text: str) -> dict:
    """`lspci -nn -k`: the VGA, 3D and display controllers (classes 0300, 0302, 0380), without the bus address."""
    gpus, current = [], None
    for line in text.splitlines():
        if not line[:1].isspace():  # a device line; the indented lines below it belong to it
            device = re.match(r"^\S+ .*\[03(?:00|02|80)\]: (.*) \[([0-9a-f]{4}):([0-9a-f]{4})\]", line)
            current = {"vendor_id": device[2], "device_id": device[3], "pci_name": device[1], "kernel_driver": None} if device else None
            gpus += [current] if current else []
        elif current and (driver := re.match(r"^\s+Kernel driver in use: (\S+)", line)):
            current["kernel_driver"] = driver[1]
    return {"gpus": gpus}


def read_drm() -> str | None:
    """`vendor device` of each `/sys/class/drm/card<N>/device`, one line each; None when no card has them."""
    lines = []
    for card in sorted(glob.glob("/sys/class/drm/card*")):
        if re.search(r"card\d+$", card):
            try:
                lines.append(" ".join(Path(card, "device", name).read_text().strip() for name in ("vendor", "device")))
            except OSError:
                continue
    return "\n".join(lines) or None


def parse_drm(text: str) -> dict:
    return {"gpus": [{"vendor_id": hex4(int(vendor, 16)), "device_id": hex4(int(device, 16))}
                     for vendor, device in (line.split() for line in text.splitlines() if line.strip())]}


def parse_cpuinfo(text: str) -> dict:
    names = re.findall(r"^model name\s*:\s*(.+)$", text, re.MULTILINE)
    cores = set(re.findall(r"^physical id\s*:\s*(\d+)$.*?^core id\s*:\s*(\d+)$", text, re.MULTILINE | re.DOTALL))
    return {"cpu_name": " ".join(names[0].split()) if names else None,
            "cpu_logical_cores": len(re.findall(r"^processor\s*:", text, re.MULTILINE)) or None,
            "cpu_physical_cores": len(cores) or None}


def parse_meminfo(text: str) -> dict:
    total = re.search(r"^MemTotal:\s*(\d+) kB", text, re.MULTILINE)
    return {"memory_mib": int(total[1]) // 1024 if total else None}


def parse_glxinfo(text: str) -> dict:
    """`glxinfo -B`: the renderer of the current GL context only, so it is recorded and not compared."""
    def value(pattern):
        found = re.search(pattern, text, re.MULTILINE)
        return found[1].strip() if found else None
    return {"gl_renderer": value(r"^OpenGL renderer string:(.*)$"), "gl_version": value(r"^OpenGL version string:(.*)$"),
            "gl_vendor_id": value(r"^\s*Vendor:.*\(0x([0-9a-f]+)\)$"), "gl_device_id": value(r"^\s*Device:.*\(0x([0-9a-f]+)\)$"),
            "gl_vram_mib": int(v) if (v := value(r"^\s*Video memory:\s*(\d+)MB$")) else None}


def parse_rocminfo(text: str) -> dict:
    gpus = []
    for block in re.split(r"^\*+\s*$", text, flags=re.MULTILINE):
        if re.search(r"^\s*Device Type:\s*GPU\s*$", block, re.MULTILINE):
            name = re.search(r"^\s*Marketing Name:\s*(.+)$", block, re.MULTILINE)
            target = re.search(r"^\s*Name:\s*(gfx\w+)\s*$", block, re.MULTILINE)
            gpus.append({"marketing_name": name[1].strip() if name else None, "gfx_target": target[1] if target else None})
    return {"rocm_gpus": gpus}


def parse_rocm_version(text: str) -> dict:
    return {"rocm_version": text.strip() or None}


def parse_vulkaninfo(text: str) -> dict:
    """`vulkaninfo --summary`: each GPU block, without the CPU (software) devices."""
    gpus = []
    for block in re.split(r"^GPU\d+:\s*$", text, flags=re.MULTILINE)[1:]:
        values = dict(re.findall(r"^\s*(\w+)\s*=\s*(.+?)\s*$", block, re.MULTILINE))
        if values.get("deviceType", "").endswith("_CPU") or "vendorID" not in values:
            continue
        gpus.append({"vendor_id": hex4(int(values["vendorID"], 16)), "device_id": hex4(int(values.get("deviceID", "0"), 16)),
                     "name": values.get("deviceName"), "vulkan_driver_info": values.get("driverInfo")})
    return {"gpus": gpus}


def parse_sw_vers(text: str) -> dict:
    values = dict(re.findall(r"^(\w+):\s*(.+?)\s*$", text, re.MULTILINE))
    name, version = values.get("ProductName"), values.get("ProductVersion")
    return {"os_label": f"{name} {version}" if name and version else None, "os_build": version, "os_build_id": values.get("BuildVersion")}


def parse_sysctl(text: str) -> dict:
    """`sysctl -n machdep.cpu.brand_string hw.memsize hw.ncpu`: three lines in this order."""
    brand, memory, cpus = (text.splitlines() + ["", "", ""])[:3]
    return {"cpu_name": brand.strip() or None, "memory_mib": int(memory) // MIB if memory.strip().isdigit() else None,
            "cpu_logical_cores": int(cpus) if cpus.strip().isdigit() else None}


def parse_system_profiler(text: str) -> dict:
    """`system_profiler SPDisplaysDataType -json`: only the GPU model, its PCI ids, its VRAM and its core count."""
    gpus = []
    for item in json.loads(text).get("SPDisplaysDataType", []):
        vram = re.match(r"(\d+)\s*(MB|GB)", item.get("spdisplays_vram") or item.get("spdisplays_vram_shared") or "")
        ids = {key: hex4(int(item[field], 16)) if re.fullmatch(r"0x[0-9a-fA-F]+", item.get(field) or "") else None
               for key, field in (("vendor_id", "spdisplays_vendor-id"), ("device_id", "spdisplays_device-id"))}
        gpus.append({**ids, "name": item.get("sppci_model"), "gpu_cores": item.get("sppci_cores"),
                     "vram_mib": int(vram[1]) * (1024 if vram[2] == "GB" else 1) if vram else None})
    return {"gpus": gpus}


def parse_ioreg(text: str) -> dict:
    """`ioreg -r -c IOAccelerator`: the `model`, `vendor-id` and `device-id` of each object that has a `model`."""
    def le32(data):  # ioreg data <de100000>: little-endian bytes
        return hex4(int.from_bytes(bytes.fromhex(data[:8]).ljust(4, b"\0"), "little") & 0xFFFF)

    gpus = []
    for block in text.split("+-o ")[1:]:
        model = re.search(r'"model" = <?"([^"]+)"', block)
        if model:
            vendor, device = (re.search(rf'"{key}" = <([0-9a-f]+)>', block) for key in ("vendor-id", "device-id"))
            gpus.append({"name": model[1], "vendor_id": le32(vendor[1]) if vendor else None,
                         "device_id": le32(device[1]) if device else None})
    return {"gpus": gpus}


def powershell(cim_class: str, fields: str) -> list[str]:
    return ["powershell", "-NoProfile", "-NonInteractive", "-Command",
            f"Get-CimInstance {cim_class} | Select-Object {fields} | ConvertTo-Json -Compress"]


NVIDIA_SMI = ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,pci.device_id", "--format=csv,noheader"]
# (method, source, parser): the source is a command, a file path or a callable that returns the text
METHODS = {
    "win32": [
        ("cim-video-controller", powershell("Win32_VideoController", "Name,PNPDeviceID,DriverVersion,AdapterRAM"), parse_cim_video),
        ("cim-processor", powershell("Win32_Processor", "Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed"),
         parse_cim_processor),
        ("cim-operating-system", powershell("Win32_OperatingSystem", "Caption,Version,BuildNumber,TotalVisibleMemorySize,OSArchitecture"),
         parse_cim_os),
        ("nvidia-smi", NVIDIA_SMI, parse_nvidia_smi),
    ],
    "linux": [
        ("os-release", "/etc/os-release", parse_os_release),
        ("uname", ["uname", "-r"], parse_uname),
        ("lspci", ["lspci", "-nn", "-k"], parse_lspci),
        ("drm-sysfs", read_drm, parse_drm),
        ("cpuinfo", "/proc/cpuinfo", parse_cpuinfo),
        ("meminfo", "/proc/meminfo", parse_meminfo),
        ("nvidia-smi", NVIDIA_SMI, parse_nvidia_smi),
        ("glxinfo", ["glxinfo", "-B"], parse_glxinfo),
        ("rocminfo", ["rocminfo"], parse_rocminfo),
        ("rocm-version", "/opt/rocm/.info/version", parse_rocm_version),
        ("vulkaninfo", ["vulkaninfo", "--summary"], parse_vulkaninfo),
    ],
    "darwin": [
        ("sw_vers", ["sw_vers"], parse_sw_vers),
        ("sysctl", ["sysctl", "-n", "machdep.cpu.brand_string", "hw.memsize", "hw.ncpu"], parse_sysctl),
        ("system_profiler", ["system_profiler", "SPDisplaysDataType", "-json"], parse_system_profiler),
        ("ioreg", ["ioreg", "-r", "-c", "IOAccelerator"], parse_ioreg),
    ],
}


def run_method(name: str, source, parser: Callable[[str], dict], timeout: float = METHOD_TIMEOUT) -> dict:
    """Run one OS method. Its result is `record-only` with the facts, or `not-run` with a reason code."""
    started, found = time.monotonic(), {"method": name, "result": "not-run", "reason_code": None, "seconds": None, "facts": {}}
    try:
        if isinstance(source, list):
            if shutil.which(source[0]) is None:
                return {**found, "reason_code": "tool-missing"}
            done = subprocess.run(source, capture_output=True, text=True, encoding="utf-8", errors="replace",  # noqa: S603
                                  timeout=timeout, check=False, stdin=subprocess.DEVNULL)
            if done.returncode:
                return {**found, "reason_code": "tool-failed", "exit_code": done.returncode}
            text = done.stdout
        elif callable(source):
            text = source()
        else:
            text = Path(source).read_text(encoding="utf-8", errors="replace") if Path(source).is_file() else None
    except subprocess.TimeoutExpired:
        return {**found, "reason_code": "timed-out", "seconds": timeout}
    if text is None:
        return {**found, "reason_code": "tool-missing"}
    try:
        facts = parser(text)
    except Exception:  # noqa: BLE001 - an output in an unknown form is a finding
        return {**found, "reason_code": "parse-failed"}
    return {**found, "result": "record-only", "seconds": round(time.monotonic() - started, 2), "facts": facts}


# --------------------------------------------------------------------------------------------
# The comparison
# --------------------------------------------------------------------------------------------


def nvidia_driver(version: str) -> str:
    """The NVIDIA form of a Windows driver version: `32.0.16.1088` -> `610.88`. Other texts do not change."""
    match = re.fullmatch(r"\d+\.\d+\.(\d{2})\.(\d{4})", version)  # an Intel or AMD version has other part lengths
    if match is None:
        return version
    digits = (match[1] + match[2])[-5:]
    return f"{digits[:3]}.{digits[3:]}"


def same(field: str, ours, theirs) -> bool:
    a, b = (" ".join(str(value).split()).casefold() for value in (ours, theirs))
    if field == "os_label":
        a, b = a.removeprefix("microsoft "), b.removeprefix("microsoft ")
        return a.startswith(b) or b.startswith(a)
    if field == "driver_version":
        return nvidia_driver(a) == nvidia_driver(b)
    return a == b


def compare(ours: dict, method: str, theirs: dict) -> list[dict]:
    """One row for each value of the method: `same`, `differs` (flagged), `only-os` or `only-skellytracker` (recorded)."""
    rows = []

    def row(field, gpu, a, b):
        status = "only-os" if a is None else "only-skellytracker" if b is None else "same" if same(field, a, b) else "differs"
        rows.append({"method": method, "field": field, "gpu": gpu, "skellytracker": a, "os": b, "status": status})

    for field in SCALAR_FIELDS:
        if theirs.get(field) is not None:
            row(field, None, ours.get(field), theirs[field])
    if "gpus" not in theirs:
        return rows
    scope = theirs.get("scope_vendor_id")
    pool = [gpu for gpu in ours["gpus"] if scope in (None, gpu["vendor_id"])]
    with_ids = [gpu for gpu in theirs["gpus"] if gpu.get("vendor_id") and gpu.get("device_id")]
    if with_ids or not theirs["gpus"]:
        row("gpu_count", None, sum(gpu["vendor_id"] is not None for gpu in pool), len(with_ids))
    for gpu in theirs["gpus"]:
        ids = (gpu.get("vendor_id"), gpu.get("device_id"))
        match = next((g for g in pool if (g["vendor_id"], g["device_id"]) == ids), None) if all(ids) else \
            next((g for g in pool if gpu.get("name") and same("name", g["name"], gpu["name"])), None)
        label = gpu.get("name") or gpu.get("pci_name") or ":".join(filter(None, ids))
        if match is None:
            row("gpu", label, None, label)
            continue
        pool.remove(match)
        for field in GPU_FIELDS:
            if gpu.get(field) is not None:
                row(field, match["name"], match[field], gpu[field])
    for gpu in pool:
        row("gpu", gpu["name"], gpu["name"], None)
    return rows


# --------------------------------------------------------------------------------------------
# The skellytracker side and the section
# --------------------------------------------------------------------------------------------


def host_facts(host) -> dict:
    """The values of `probe_host()` in the form of the parsers."""
    return {"os_label": host.os_label, "os_version": host.os_version, "os_build": None if host.os_build is None else str(host.os_build),
            "cpu_name": host.cpu_name, "cpu_physical_cores": host.cpu_physical_cores, "cpu_logical_cores": host.cpu_logical_cores,
            "memory_mib": host.memory_total_bytes // MIB if host.memory_total_bytes else None,
            "gpus": [{"vendor_id": hex4(gpu.pci_vendor_id), "device_id": hex4(gpu.pci_device_id), "name": gpu.name,
                      "driver_version": gpu.driver_version,
                      "vram_mib": None if gpu.vram_total_bytes is None else gpu.vram_total_bytes // MIB} for gpu in host.gpus]}


def error_sources(lines) -> list[str]:
    """The source tag of each `probe_errors` line (`<source>: <message>`): a report holds no error text."""
    return [line.split(":", 1)[0] for line in lines]


def host_record(host) -> dict:
    """The `probe_host()` record without the bus address, the LUID, the GPU UUID, the container ids and the error texts."""
    record = dataclasses.asdict(host)
    record["probe_errors"] = error_sources(host.probe_errors)
    for gpu in record["gpus"]:
        for field in ("key", "pci_bus_id", "luid"):
            gpu.pop(field)
        if gpu["nvidia"]:
            gpu["nvidia"].pop("uuid")
    if host.container is not None:
        record["container"] = {"runtime": host.container.runtime, "base_os": host.container.base_os}
    return record


def eps_record(host) -> dict:
    """What `eps.status()` and `eps.recommend()` give, for each EP and each GPU. Neither loads an EP library."""
    from skellytracker.core import eps
    from skellytracker.core.system.host import gpu_device_keys

    status = eps.status()
    rows = [{"key": row.key, "state": row.state, "reason_code": row.reason_code, "usable": row.usable, "uses_gpu": row.uses_gpu,
             "certified": row.certified, "pack_version": row.pack_version, "catalog_status": row.catalog_status,
             "devices": [device.device_key for device in row.devices]} for row in status.eps]
    performance = status.performance
    gpus = [{"device_key": key, "name": gpu.name, "usable_eps": [row["key"] for row in rows if key in row["devices"]],
             "recommended": performance.chosen.ep_key if performance.chosen.device_key == key else None}
            for key, gpu in gpu_device_keys(host)]
    return {"eps": rows, "gpus": gpus,
            "performance": {"ep": performance.chosen.ep_key, "device_key": performance.chosen.device_key,
                            "state": performance.chosen.status, "precision": performance.precision,
                            "hardware_class": performance.hardware_class,
                            "skipped": [{"ep": c.ep_key, "state": c.status} for c in performance.skipped],
                            "offers": [offer.kind for offer in performance.offers]},
            "accuracy": {"ep": status.accuracy.chosen.ep_key, "precision": status.accuracy.precision},
            "certify_offers": [offer.ep_key for offer in status.certify_offers], "warning_count": len(status.warnings),
            "core_matches_pin": status.core_matches_pin}


def section_hardware(work: Path) -> dict:
    sys.path.insert(0, str(REPO_ROOT))
    from skellytracker.core.system import probe_environment, probe_host

    checks, details, ours = [], {}, None
    try:
        host = probe_host()
        ours = host_facts(host)
        details["skellytracker"] = {"host": host_record(host)}
        checks.append({"name": "probe-host", "result": "pass", "reason_code": None, "probe_errors": len(host.probe_errors)})
    except Exception as error:  # noqa: BLE001 - the one failure of this section
        checks.append({"name": "probe-host", "result": "fail", "reason_code": type(error).__name__})
    if ours is not None:
        environment = probe_environment()
        details["skellytracker"]["environment"] = {"python": dataclasses.asdict(environment.python), "frozen": environment.frozen,
                                                   "package_count": len(environment.packages),
                                                   "probe_errors": error_sources(environment.probe_errors)}
        try:
            details["skellytracker"]["eps"] = eps_record(host)
            checks.append({"name": "eps-state", "result": "pass", "reason_code": None})
        except Exception as error:  # noqa: BLE001
            checks.append({"name": "eps-state", "result": "not-run", "reason_code": type(error).__name__})
    methods = [run_method(*method) for method in METHODS.get(sys.platform, METHODS["linux"])]
    checks += [{"name": m["method"], "result": m["result"], "reason_code": m["reason_code"]} for m in methods]
    details["os_methods"] = methods
    rows = [row for m in methods if m["result"] == "record-only" and ours is not None for row in compare(ours, m["method"], m["facts"])]
    flagged = [row for row in rows if row["status"] == "differs"]
    details["comparison"] = rows
    details["flagged"] = flagged
    if ours is None:
        return {"result": "fail", "reason_code": checks[0]["reason_code"], "summary": "probe_host() raised", "checks": checks,
                "details": details}
    ran = sum(m["result"] == "record-only" for m in methods)
    return {"result": "record-only", "reason_code": "differences-flagged" if flagged else None,
            "summary": f"{len(ours['gpus'])} GPU(s); {ran} of {len(methods)} OS methods ran; "
                       f"{len(flagged)} difference(s) flagged in {len(rows)} comparisons",
            "checks": checks, "details": details}

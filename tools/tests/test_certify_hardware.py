"""Tests of section 2 of the certify suite (`tools/certify_hardware.py`): the parsers on short made-up texts, and the comparison.

The samples hold no real hostname, serial number, UUID or bus address. A parser must drop the ones that a tool prints.
"""

import json
import sys

import certify_hardware as ch

CIM_VIDEO = json.dumps([
    {"Name": "Virtual Display", "PNPDeviceID": "ROOT\\DISPLAY\\0000", "DriverVersion": "1.0", "AdapterRAM": None},
    {"Name": "Intel(R) UHD Graphics 770", "PNPDeviceID": "PCI\\VEN_8086&DEV_A780&SUBSYS_00000000&REV_04\\3&FAKE&0&10",
     "DriverVersion": "32.0.101.7088", "AdapterRAM": 2147479552},
    {"Name": "NVIDIA GeForce RTX 3070", "PNPDeviceID": "PCI\\VEN_10DE&DEV_2484&SUBSYS_00000000&REV_A1\\4&FAKE&0&8",
     "DriverVersion": "32.0.16.1088", "AdapterRAM": 4293918720}])


def test_cim_video_keeps_the_ids_and_drops_the_instance_path():
    facts = ch.parse_cim_video(CIM_VIDEO)
    assert facts["non_pci_adapters"] == ["Virtual Display"]
    assert facts["gpus"][0] == {"vendor_id": "8086", "device_id": "a780", "name": "Intel(R) UHD Graphics 770",
                                "driver_version": "32.0.101.7088", "vram_mib": 2047}
    assert facts["gpus"][1]["vram_mib"] is None and facts["gpus"][1]["vram_note"] == "adapter-ram-capped"
    assert "FAKE" not in json.dumps(facts)


def test_cim_processor_and_os():
    cpu = ch.parse_cim_processor('{"Name":"Intel(R) Core(TM)  i7-14700K ","NumberOfCores":20,"NumberOfLogicalProcessors":28,"MaxClockSpeed":3400}')
    assert cpu == {"cpu_name": "Intel(R) Core(TM) i7-14700K", "cpu_physical_cores": 20, "cpu_logical_cores": 28, "max_clock_mhz": 3400}
    os_facts = ch.parse_cim_os('{"Caption":"Microsoft Windows 11 Home","Version":"10.0.26300","BuildNumber":"26300",'
                               '"TotalVisibleMemorySize":66785160,"OSArchitecture":"64-bit"}')
    assert os_facts["memory_mib"] == 65219 and os_facts["os_build"] == "26300"


def test_nvidia_smi():
    facts = ch.parse_nvidia_smi("NVIDIA GeForce RTX 3070, 610.88, 8192 MiB, 0x248410DE\n")
    assert facts == {"scope_vendor_id": "10de", "gpus": [{"vendor_id": "10de", "device_id": "2484", "name": "NVIDIA GeForce RTX 3070",
                                                          "driver_version": "610.88", "vram_mib": 8192}]}


def test_linux_parsers():
    assert ch.parse_os_release('NAME="Ubuntu"\nPRETTY_NAME="Ubuntu 24.04.1 LTS"\nID=ubuntu\nVERSION_ID="24.04"\n') == {
        "os_label": "Ubuntu 24.04.1 LTS", "os_id": "ubuntu", "os_version_id": "24.04"}
    lspci = ("00:02.0 VGA compatible controller [0300]: Intel Corporation Device [8086:a780] (rev 04)\n"
             "\tSubsystem: Fake Vendor Device [1234:5678]\n"
             "01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GA104 [GeForce RTX 3070] [10de:2484] (rev a1)\n"
             "\tKernel driver in use: nvidia\n"
             "01:00.1 Audio device [0403]: NVIDIA Corporation GA104 audio [10de:228b] (rev a1)\n"
             "\tKernel driver in use: snd_hda_intel\n")
    assert ch.parse_lspci(lspci)["gpus"] == [
        {"vendor_id": "8086", "device_id": "a780", "pci_name": "Intel Corporation Device", "kernel_driver": None},
        {"vendor_id": "10de", "device_id": "2484", "pci_name": "NVIDIA Corporation GA104 [GeForce RTX 3070]", "kernel_driver": "nvidia"}]
    assert ch.parse_drm("0x10de 0x2484\n0x8086 0xa780\n")["gpus"][0] == {"vendor_id": "10de", "device_id": "2484"}
    cpuinfo = "".join(f"processor\t: {n}\nmodel name\t: Fake CPU 9000\nphysical id\t: 0\ncore id\t\t: {n // 2}\n\n" for n in range(4))
    assert ch.parse_cpuinfo(cpuinfo) == {"cpu_name": "Fake CPU 9000", "cpu_logical_cores": 4, "cpu_physical_cores": 2}
    assert ch.parse_meminfo("MemTotal:       65536000 kB\nMemFree: 1 kB\n") == {"memory_mib": 64000}
    assert ch.parse_uname("6.8.0-48-generic\n") == {"os_build": "6.8.0-48-generic"}


def test_linux_gpu_tool_parsers():
    glx = ("OpenGL vendor string: NVIDIA Corporation\n    Vendor: NVIDIA Corporation (0x10de)\n"
           "    Device: NVIDIA GeForce RTX 3070/PCIe/SSE2 (0x2484)\n    Video memory: 8192MB\n"
           "OpenGL renderer string: NVIDIA GeForce RTX 3070/PCIe/SSE2\nOpenGL version string: 4.6.0 NVIDIA 590.48.01\n")
    assert ch.parse_glxinfo(glx) == {"gl_renderer": "NVIDIA GeForce RTX 3070/PCIe/SSE2", "gl_version": "4.6.0 NVIDIA 590.48.01",
                                     "gl_vendor_id": "10de", "gl_device_id": "2484", "gl_vram_mib": 8192}
    rocm = ("*******\nAgent 1\n*******\n  Name:                    Fake CPU\n  Marketing Name:          Fake CPU\n"
            "  Device Type:             CPU\n*******\nAgent 2\n*******\n  Name:                    gfx1100\n"
            "  Uuid:                    GPU-0000000000000000\n  Marketing Name:          AMD Radeon RX 7900 XTX\n"
            "  Device Type:             GPU\n")
    assert ch.parse_rocminfo(rocm) == {"rocm_gpus": [{"marketing_name": "AMD Radeon RX 7900 XTX", "gfx_target": "gfx1100"}]}
    assert ch.parse_rocm_version("6.2.4-120\n") == {"rocm_version": "6.2.4-120"}
    vulkan = ("Devices:\n========\nGPU0:\n\tvendorID           = 0x1002\n\tdeviceID           = 0x744c\n"
              "\tdeviceType         = PHYSICAL_DEVICE_TYPE_DISCRETE_GPU\n\tdeviceName         = AMD Radeon RX 7900 XTX (RADV NAVI31)\n"
              "\tdeviceUUID         = 00000000-0000-0000-0000-000000000000\n\tdriverInfo         = Mesa 24.0.9\n"
              "GPU1:\n\tvendorID           = 0x10005\n\tdeviceID           = 0x0000\n\tdeviceType         = PHYSICAL_DEVICE_TYPE_CPU\n"
              "\tdeviceName         = llvmpipe\n")
    assert ch.parse_vulkaninfo(vulkan) == {"gpus": [{"vendor_id": "1002", "device_id": "744c", "name": "AMD Radeon RX 7900 XTX (RADV NAVI31)",
                                                     "vulkan_driver_info": "Mesa 24.0.9"}]}


def test_macos_parsers():
    assert ch.parse_sw_vers("ProductName:\t\tmacOS\nProductVersion:\t\t15.1\nBuildVersion:\t\t24B83\n") == {
        "os_label": "macOS 15.1", "os_build": "15.1", "os_build_id": "24B83"}
    assert ch.parse_sysctl("Apple M2\n17179869184\n8\n") == {"cpu_name": "Apple M2", "memory_mib": 16384, "cpu_logical_cores": 8}
    profiler = json.dumps({"SPDisplaysDataType": [{"sppci_model": "Apple M2", "sppci_cores": "10", "spdisplays_vendor": "sppci_vendor_Apple",
                                                   "spdisplays_ndrvs": [{"_name": "Display", "_spdisplays_display-serial-number": "FAKE1"}]},
                                                  {"sppci_model": "AMD Radeon Pro 5500M", "spdisplays_vram": "8 GB",
                                                   "spdisplays_vendor-id": "0x1002", "spdisplays_device-id": "0x7340"}]})
    facts = ch.parse_system_profiler(profiler)
    assert facts["gpus"] == [{"vendor_id": None, "device_id": None, "name": "Apple M2", "gpu_cores": "10", "vram_mib": None},
                             {"vendor_id": "1002", "device_id": "7340", "name": "AMD Radeon Pro 5500M", "gpu_cores": None, "vram_mib": 8192}]
    assert "FAKE1" not in json.dumps(facts)
    ioreg = ('+-o AGXAcceleratorG14G  <class AGXAcceleratorG14G, id 0x1, registered>\n  {\n    "model" = "Apple M2"\n'
             '    "IORegistryEntryID" = 1\n  }\n+-o AMDRadeonX6000  <class AMDRadeonX6000>\n  {\n    "model" = <"AMD Radeon Pro 5500M">\n'
             '    "vendor-id" = <02100000>\n    "device-id" = <40730000>\n  }\n')
    assert ch.parse_ioreg(ioreg)["gpus"] == [{"name": "Apple M2", "vendor_id": None, "device_id": None},
                                             {"name": "AMD Radeon Pro 5500M", "vendor_id": "1002", "device_id": "7340"}]


def test_a_missing_tool_and_a_failing_parser_are_not_run():
    assert ch.run_method("x", ["no-such-tool-for-the-certify-test"], ch.parse_uname)["reason_code"] == "tool-missing"
    assert ch.run_method("x", "/no/such/file/for/the/certify/test", ch.parse_uname)["reason_code"] == "tool-missing"
    assert ch.run_method("x", lambda: None, ch.parse_uname)["reason_code"] == "tool-missing"
    assert ch.run_method("x", lambda: "not json", ch.parse_cim_os)["reason_code"] == "parse-failed"
    failed = ch.run_method("x", [sys.executable, "-c", "raise SystemExit(4)"], ch.parse_uname)
    assert (failed["reason_code"], failed["exit_code"]) == ("tool-failed", 4)
    slow = ch.run_method("x", [sys.executable, "-c", "import time; time.sleep(30)"], ch.parse_uname, timeout=0.5)
    assert slow["reason_code"] == "timed-out"
    assert ch.run_method("x", lambda: "6.8.0\n", ch.parse_uname) | {"seconds": 0} == {
        "method": "x", "result": "record-only", "reason_code": None, "seconds": 0, "facts": {"os_build": "6.8.0"}}


def test_the_nvidia_driver_form_of_windows():
    assert ch.nvidia_driver("32.0.16.1088") == "610.88" and ch.nvidia_driver("31.0.15.5222") == "552.22"
    assert ch.nvidia_driver("32.0.101.7088") == "32.0.101.7088"


OURS = {"os_label": "Windows 11 Home 26H2", "os_version": "10.0.26300", "os_build": "26300", "cpu_name": "Fake CPU",
        "cpu_physical_cores": 8, "cpu_logical_cores": 16, "memory_mib": 65219,
        "gpus": [{"vendor_id": "8086", "device_id": "a780", "name": "Intel(R) UHD Graphics 770", "driver_version": "32.0.101.7088",
                  "vram_mib": 128},
                 {"vendor_id": "10de", "device_id": "2484", "name": "NVIDIA GeForce RTX 3070", "driver_version": "610.88", "vram_mib": 8192}]}


def statuses(rows):
    return {(row["field"], row["gpu"]): row["status"] for row in rows}


def test_the_comparison_flags_differences_and_records_one_sided_values():
    rows = ch.compare(OURS, "cim", {**ch.parse_cim_video(CIM_VIDEO), **ch.parse_cim_os(
        '{"Caption":"Microsoft Windows 11 Home","Version":"10.0.26300","BuildNumber":"26300","TotalVisibleMemorySize":66785160}')})
    found = statuses(rows)
    assert found[("gpu_count", None)] == "same" and found[("os_label", None)] == "same" and found[("memory_mib", None)] == "same"
    assert found[("driver_version", "NVIDIA GeForce RTX 3070")] == "same"
    assert found[("vram_mib", "Intel(R) UHD Graphics 770")] == "differs"
    assert ("vram_mib", "NVIDIA GeForce RTX 3070") not in found  # the capped AdapterRAM is not compared


def test_the_comparison_matches_by_ids_then_by_name_and_respects_a_vendor_scope():
    smi = ch.compare(OURS, "nvidia-smi", ch.parse_nvidia_smi("NVIDIA GeForce RTX 3070, 600.00, 8192 MiB, 0x248410DE\n"))
    assert statuses(smi) == {("gpu_count", None): "same", ("name", "NVIDIA GeForce RTX 3070"): "same",
                             ("driver_version", "NVIDIA GeForce RTX 3070"): "differs", ("vram_mib", "NVIDIA GeForce RTX 3070"): "same"}
    extra = ch.compare(OURS, "drm", {"gpus": [{"vendor_id": "8086", "device_id": "a780"}, {"vendor_id": "1002", "device_id": "744c"}]})
    found = statuses(extra)
    assert found[("gpu", "1002:744c")] == "only-os" and found[("gpu", "NVIDIA GeForce RTX 3070")] == "only-skellytracker"
    assert found[("gpu_count", None)] == "same"  # two and two: the count does not see which GPUs
    by_name = ch.compare(OURS, "ioreg", {"gpus": [{"name": "NVIDIA GeForce RTX 3070", "vendor_id": None, "device_id": None}]})
    assert statuses(by_name)[("name", "NVIDIA GeForce RTX 3070")] == "same" and ("gpu_count", None) not in statuses(by_name)

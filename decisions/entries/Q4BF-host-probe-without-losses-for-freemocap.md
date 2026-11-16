# Q4BF — The host probe runs no macOS command and gives the macOS VRAM, the Linux GPU name and the CPU frequency

**Status:** absorbed into [`records.py`](../../skellytracker/core/system/records.py), [`host.py`](../../skellytracker/core/system/host.py), 2026-11-16 (user, question H1 and the instruction on the losses of the freemocap host probe, 2026-11-16; PR: pending).

## Decision

1. **No external command on macOS.** The package runs no external hardware command on macOS. The
   macOS reader gets the GPUs from the IORegistry, with IOKit and CoreFoundation through `ctypes`.
   It does not run `system_profiler`. It adds no dependency.
2. **macOS VRAM.** On macOS, `GpuInfo.vram_total_bytes` is the IORegistry value `VRAM,totalMB`,
   when the GPU has it. An Apple Silicon GPU has unified memory and no such value: the field is
   `None`.
3. **Linux GPU name.** On Linux, `GpuInfo.name` of a GPU with no NVML name and no `product_name`
   file is the device name of the `pci.ids` database: `/usr/share/hwdata/pci.ids`, else
   `/usr/share/misc/pci.ids`. The reader reads the file one time for each probe. When no file
   exists, or the file does not hold the ids, `name` is `None`.
4. **CPU frequency.** `HostInfo` has the new field `cpu_max_frequency_hz`: the nominal maximum
   frequency of the CPU in Hz, or `None`. The sources are the registry value `~MHz` on Windows,
   `/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq` on Linux, and `hw.cpufrequency_max`,
   else `hw.cpufrequency`, of `sysctlbyname` on macOS.

The readers stay in `core/_hardware/`, and the Windows GPU reader and NVML do not change
([ADR-P1F3](P1F3-hardware-probe-devices-and-multi-gpu.md) items 1 and 2).

## Reason

- The application freemocap drops its own hardware commands (`nvidia-smi`, WMIC, `lspci` and
  `system_profiler`) and reads `probe_host()`. A review found three values that freemocap then
  loses: the macOS VRAM, the Linux name of a GPU that is not an NVIDIA GPU, and the CPU frequency.
  The user wants no loss.
- The user decided that skellytracker stops the `system_profiler` call.
- `lspci` reads the same `pci.ids` file, so the device name is the name that `lspci` gives.

## Consequences

- No test ran the macOS reader on a Mac. It was written from the IOKit documentation. A person with
  a Mac must compare the keys `model`, `vendor-id` and `VRAM,totalMB` with the output of
  `ioreg -l -w0 -r -c IOAccelerator` and `ioreg -l -w0 -r -c IOPCIDevice`. On a failure, the reader
  gives no GPU and does not raise.
- No test ran the Linux readers of items 3 and 4 on Linux. The tests use fake files.
- `systemd-detect-virt` is still an external command on Linux. It is out of the scope of this entry.
- A `pci.ids` name is the device name only, for example a chip family name. It has no vendor name.
- On Windows, `~MHz` is the base frequency of the CPU. It does not include a turbo frequency.
- An Apple Silicon Mac gives no CPU frequency and no VRAM.
- The `skellytracker-eps status` output does not change: it has no CPU value.

## Evidence

- `gpu_registry_entries`, `gpus_from_registry` and `cpu_max_frequency_hz` of
  `skellytracker/core/_hardware/darwin.py`; `device_name` of `skellytracker/core/_hardware/pci.py`;
  `gpus` and `cpu_max_frequency_hz` of `skellytracker/core/_hardware/linux.py`;
  `cpu_max_frequency_hz` of `skellytracker/core/_hardware/windows.py`.
- The tests are in `skellytracker/tests/test_system_host.py`.
- On the Windows test host of [ADR-0YYY](0YYY-host-reader-costs.md), the first `probe_host()` call
  of a process takes 96 ms before the change and 97 ms after it: the median of 5 new
  processes, CPython 3.13.18.

## Alternatives rejected

- **Keep `system_profiler`.** The user decided against it.
- **The `pyobjc` package for IOKit.** It is a new dependency. `ctypes` is sufficient.
- **A copy of `pci.ids` in the package.** It is large, and it gets old. The host file is the file
  that `lspci` reads.

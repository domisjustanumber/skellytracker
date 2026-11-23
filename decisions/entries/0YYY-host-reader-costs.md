# 0YYY — Host reader costs and the Windows adapter facts of `probe_host()`

**Status:** evidence; used by [Q4BF](Q4BF-host-probe-without-losses-for-freemocap.md), 2026-11-23 (PR: pending). It was `evidence` from 2026-11-16 (measurement of stage 1.3 of the implementation plan).

## Decision

1. **Cost.** On the Windows test host, the first `probe_host()` call of a process takes about 76 ms:
   25.1 ms for the NVML start and its read, and 51.0 ms for the other readers. A later call takes
   0.002 ms, because the result is cached. The parts: DXGI with the D3DKMT query 9.8 ms, the first
   psutil call 11.6 ms, the registry read of the CPU name 0.03 ms. The import of
   `skellytracker.core.system` takes 586 ms, because `core/__init__.py` is eager
   ([ADR-0XW9](0XW9-entry-points-layout-guard-test-and-session-code.md) item 3).
2. **No ONNX Runtime.** After the import and `probe_host()`, `onnxruntime` is not in `sys.modules`.
3. **Second adapter.** DXGI lists the NVIDIA GPU two times, with two LUIDs. The D3DKMT
   adapter-address query gives bus 1, device 0, function 0 for the first adapter and the bus number
   `0xFFFFFFFF` for the second adapter. Thus the reader gives no bus id for a bus number above 255,
   and it drops an adapter with no bus id when an adapter with a bus id has the same PCI ids.
4. **Software adapter.** The Microsoft Basic Render Driver has the DXGI flag `0x2`. The reader drops
   it.
5. **Bus id join.** The bus id of the D3DKMT query (`0000:01:00.0`) is equal to the normalised NVML
   bus id. The join of an NVML GPU to its LUID needs no registry read.
6. **VRAM.** For the same GPU, DXGI gives 8,407,482,368 dedicated bytes and NVML gives
   8,589,934,592 total bytes. `GpuInfo.vram_total_bytes` of an NVIDIA GPU is the NVML value.
7. **Driver version.** For the NVIDIA GPU, DXGI `CheckInterfaceSupport` gives `32.0.16.1088` and
   NVML gives `610.88`. `GpuInfo.driver_version` of an NVIDIA GPU is the NVML value, because the
   driver branch rule reads it ([ADR-D8DH](D8DH-sessions-errors-and-the-ready-rule.md) item 7).

## Reason

- Step 4 of stage 1.3 needs an evidence entry for the costs of the host readers.
- [ADR-P1F3](P1F3-hardware-probe-devices-and-multi-gpu.md) item 2 keeps one D3DKMT query for the
  join of a LUID to a PCI bus id. Items 3 and 5 show that this query is sufficient on the test host.

## Evidence

- Host: one NVIDIA RTX 3070 (CC 8.6, driver 610.88) and one Intel UHD 770, Windows 11 build 26300,
  CPython 3.13.18, `nvidia-ml-py` 13.615.71, `psutil` 7.2.2.
- Method: 9 new processes. Each value is the median of the first call in each process.
- Script: [`host_probe_timing.py`](../scripts/host_probe_timing.py).
- Not measured: Linux, macOS, a host with two GPUs of one model, and a frozen application.

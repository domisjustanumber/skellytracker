# P1F3 — The hardware probe, the default device and the multi-GPU camera split

**Status:** accepted, 2026-11-12 (user).

## Decision

1. **Readers.** The private hardware readers are in `core/_hardware/`: NVML, the readers of each
   OS, the PCI bus-id normaliser, the path sanitizer, Windows PDH and DXGI. `core.system` gives the
   public facts ([ADR-0XW9](0XW9-entry-points-layout-guard-test-and-session-code.md) item 3).
2. **`probe_host()` fields.** v2 has these groups: NVML, PCI ids, the Windows LUID map, the OS build,
   the native architecture, CPU and memory, and virtualization and container. There is no DXCore
   reader and no NPU reader. One D3DKMT adapter-address query stays. It is used only to join a LUID
   to a PCI bus id, so that two identical GPUs get two bus ids.
3. **Free VRAM.** `core.metrics.free_vram(device)` is a one-shot NVML read of the free bytes of one
   GPU. It keeps no state. A GPU with no NVML value gives `None`, and batch k stays 1
   ([ADR-ZYS9](ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 4). The batch choice
   must leave VRAM for skellycam and the player (item 9).
4. **Old GPUs.** An NVIDIA GPU older than Turing (CC below 7.5) is unsupported and runs on the CPU
   only. It gets no driver offer. The `update-driver` offer is only for Turing and later, below R580.
5. **Device key.** A GPU is named by `device_key` = `<kind>:<pci_vendor>:<pci_device>:<n>`, for
   example `gpu:10de:2484:0`. `n` is the rank by PCI bus id among the devices with the same kind,
   vendor and device id.
6. **Default device.** `build_session()` with no `device_key` uses the GPU with the most VRAM among
   the GPUs that the EP lists. On a tie, it uses the lowest PCI bus id.
   `recommend("performance")` returns that device too.
7. **Camera split.** A run splits its cameras across GPUs. Each GPU runs the whole pipeline for its
   cameras. A node is never split across GPUs. Session sharing inside one run is for each GPU: the
   sharing key of ZYS9 item 6 holds the device. On each GPU, the batch of ZYS9 item 4 is k × the
   cameras of that GPU.
8. **GPU set.** A run uses one EP, on each GPU that the EP lists and that passes its floors. The GPU
   set of the split is the GPUs that each GPU EP of the nodes of the run lists. A node EP override
   and the `cpu` NMS session stay.
9. **Restriction and reserve.** [ADR-V7GZ](V7GZ-pipeline-api-device-and-vram-reserve.md) gives the
   API of `device` and `vram_reserve_bytes`. With `device`, the run uses exactly those GPUs. A key
   that is not a qualifying GPU raises `EpUnavailableError` with the reason. Without `device`, the
   run uses each qualifying GPU. For now, the reserve applies on each GPU of the run. Stage 1.10
   sizes k for each GPU from `free_vram(device) - vram_reserve_bytes`.
10. **Weights.** The split weights the cameras by the warm-up speed of each GPU. It is fixed at start.
    There is no rebalancing.
11. **Scope and gate.** The camera split ships in v2. Stage 1.3 (Hardware and EP API) gives the
    device map. Stage 1.10 (Pipeline API) gives the runtime. The gate is a simulated split on one
    GPU. Real two-GPU testing is not verified. Stage 1.10 defines how the timing reports a node that
    has a session on each of two or more GPUs.
12. **GTX 16xx.** fp16 stays the default on GTX 16xx
    ([ADR-7NY2](7NY2-pipeline-form-graph-and-nodes.md) item 10). The full GTX 1650 run gives data.
    It is not a gate.
13. **Names.** `run_devices()` and `RunDevice` are proposed names. The author of stage 1.3 can change
    them.

## Reason

- The user decided these items on 2026-11-12, in a grilling session of the hardware and EP track.
- The user, on devices: "the session setup picks which GPU to use, and uses multiple GPUs if they're
  available. Specifying a GPU restricts to only that GPU; else skellytracker uses whatever it wants."
- No v2 code reads an NPU fact or a fact that only DXCore gives. `is_integrated` is `None` on
  Windows.
- DXGI gives a LUID and PCI ids, but no bus id. Without the D3DKMT query, two GPUs with the same PCI
  ids cannot be told apart.
- CUDA 13 has no kernels for a GPU older than Turing, so a newer driver does not help it.
- A split of cameras keeps each frame of one camera on one GPU. A split of nodes copies tensors
  between GPUs.
- A fixed split keeps the batch shapes fixed for the run.
- The user first chose the reserve on the display GPU only. The user then chose each GPU, for now,
  because the display GPU needs its own detection.
- Item 13: no code exists yet to fix the names.

## Evidence

[ADR-V9NK](V9NK-ep-device-checks-evidence.md): on the GTX 1650 (CC 7.5), the `cuda` pack below R580
registers and lists no device, with no crash and no CPU fallback. It passes on R580 and later. Both
`trt-rtx` packs register and list no device on CC 7.5.

## Alternatives rejected

- **The first device of the EP as the default.** It can be the GPU with less VRAM.
- **A split of nodes across GPUs.** It copies data between GPUs on each frame.
- **Rebalancing during a run.** It changes the batch shapes.
- **The reserve on the display GPU only.** Later work. It needs the NVML display flag or the DXGI
  adapter outputs, and a caller override.
- **DXCore and NPU readers.** No consumer in v2.
- **No D3DKMT query.** Two identical GPUs would share one bus id.
- **An fp32-first rule for GTX 16xx.** The user keeps one precision rule for each EP.
- **A driver offer for pre-Turing GPUs.** No driver gives them CUDA 13 kernels.

## Open work

See [open-work.md](../open-work.md).

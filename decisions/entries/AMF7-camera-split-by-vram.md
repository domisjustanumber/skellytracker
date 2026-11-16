# AMF7 — A run splits its cameras over its GPUs by the VRAM that it can use on each GPU

**Status:** absorbed into [`running.md#behaviour`](../../specs/pipeline/running.md#behaviour), 2026-11-16 (user, answer to row 2 of the review of the unclear places, 2026-11-16; PR: pending).

## Decision

1. **The counts.** A run with two or more GPUs gives each GPU a count of cameras. With `n` cameras
   and the weights `w_i`, the quota of GPU `i` is `w_i × n / Σw`. Each GPU gets the integer part of
   its quota. The cameras that remain go one each to the GPUs with the largest fractional parts.
   On a tie, the earlier GPU gets the camera. The quotas use exact arithmetic. The GPUs are in the
   order of the GPUs of the run: the most VRAM first, then the lowest PCI bus id
   ([ADR-P1F3](P1F3-hardware-probe-devices-and-multi-gpu.md) item 6).
2. **The weight.** The weight of a GPU is the VRAM that the run can use on it: the free VRAM at
   start minus the VRAM reserve, with a floor of 0. When the host cannot read the free VRAM of each
   GPU of the run, the weight is the total VRAM minus the reserve, with a floor of 0. When the host
   cannot read the total VRAM of each GPU, or each weight is 0, all weights are equal. Thus GPUs
   with equal VRAM get equal counts, and a GPU with more VRAM gets more cameras.
3. **One camera or more.** Each GPU that the run uses gets one camera or more. Each GPU with the
   count 0, in GPU order, takes one camera from the GPU with the largest count. On a tie, it takes
   the camera from the earlier GPU.
4. **Fewer cameras than GPUs.** The run uses only the first GPUs, with one camera each.
5. **Blocks.** The run gives the cameras to the GPUs in the order of the camera ids: the first
   cameras to the first GPU, the next cameras to the second GPU, and so on.
6. **Fixed at start.** The split is fixed at start. There is no rebalancing.

This entry replaces item 10 of [ADR-P1F3](P1F3-hardware-probe-devices-and-multi-gpu.md): "The split
weights the cameras by the warm-up speed of each GPU." Item 6 keeps the other two sentences of that
item. The other items of ADR-P1F3 do not change.

## Reason

- No text gave a formula for the warm-up speed, and no host with two GPUs exists to measure it.
- The host knows the VRAM of each GPU at start: NVML gives the free VRAM
  (`free_vram` of `skellytracker/core/metrics/live.py`), and the probe gives the total VRAM
  (`vram_total_bytes` of `RunDevice` in `skellytracker/core/eps/records.py`).
- The user asked for the cases of two GPUs with different VRAM and with the same VRAM.
- The free VRAM shows the VRAM that other applications already use, for example skellycam. The
  reserve is the VRAM that the run must leave free
  ([ADR-V7GZ](V7GZ-pipeline-api-device-and-vram-reserve.md) item 1).
- The largest-remainder method gives the counts that are nearest to the quotas, and its tie rule
  makes the split the same in each implementation.
- Blocks keep the cameras of one batch together. A modulo split mixes the cameras of the GPUs.

## Consequences

- A faster GPU with less VRAM gets fewer cameras.
- The quotas of 24 GB and 8 GB with 6 cameras are 4.5 and 1.5. The tie gives 5 and 1, not 4 and 2.
- A GPU with less free VRAM than the reserve has the weight 0. It still gets one camera (item 3).
- The free VRAM can change between the read and the build of the sessions.
- No run on a host with two GPUs verified the split. The tests use fake GPUs
  (`skellytracker/tests/pipelines/test_sessions.py`).

## Evidence

- `split_cameras` and `gpu_weights` of `skellytracker/core/pipelines/_runtime/sessions.py`, and the
  executor (`skellytracker/core/pipelines/_runtime/executor.py`), implement the items.

## Alternatives rejected

- **An equal split always.** It wastes the larger GPU, and the smaller GPU can run out of memory.
- **The warm-up speed.** It needs a measurement at each start and a formula. No text gives one.
- **A modulo split.** It mixes the cameras of the GPUs, and it gives no form for unequal counts.

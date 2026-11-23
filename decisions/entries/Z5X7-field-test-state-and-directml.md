# Z5X7 — The field-test state of the EP catalog, and DirectML on Windows

**Status:** superseded by [6A1Y](6A1Y-field-test-and-amd-eps-consolidation.md), 2026-11-23 (consolidation; PR: pending). It was `accepted` from 2026-11-18 (user).

## Decision

This entry builds item 11 of [ADR-Y14H](Y14H-certify-suite.md) for DirectML. It changes item 3 of
[ADR-N6E8](N6E8-onnxruntime-1-30-on-each-os.md): `directml` is no longer a reserved key. Classic
TensorRT stays reserved. [ADR-XSE7](XSE7-amd-eps-in-the-field-test.md) makes `migraphx` a field-test EP.

1. **Catalog status.** A pack row or a built-in EP row can have `status: field-test`.
   `tools/ep_catalog.py --check` accepts only `ready`, `test` and `field-test`.
2. **Opt-in.** The EP store keeps the opt-in to a field-test EP key in `field-test.json`. Only
   `skellytracker-eps install KEY --field-test` and the certify suite write it. The suite writes it
   in its own store, and the frame deletes that store at the end.
3. **Refusal.** With no opt-in, the state of the EP is `field_test`, with the reason code
   `field-test`. `check_start()`, `build_session()`, `verify()` and `plan_install()` raise
   `EpUnavailableError` with the command of the opt-in. No other EP runs in its place. A field-test
   pack does not download before the opt-in, and `all-compatible` holds no field-test EP.
4. **No offer.** `recommend()` never gives a field-test EP as a candidate, a skipped candidate or an
   offer, also after the opt-in. `status()` shows it with its state and `catalog_status`, and
   `install_hint` is None. `suggest_execution_provider("directml")` stays None.
5. **DirectML.** `directml` is a built-in EP for `win_amd64` with `selects_gpu: true`, the precision
   order fp16 then fp32, `l3_atol` 1.5e-2, no allowed option, and `status: field-test`. It can use
   each GPU of the host. The hardware class `amd-windows` (an AMD GPU on Windows) lists `directml`
   before `cpu`. Linux and macOS do not change. XSE7 adds the AMD EPs to `amd-windows` and an
   `amd-linux` class.
6. **Device.** A session on a GPU takes the ONNX Runtime EP device of the GPU (the PCI ids, then the
   LUID on Windows) through `add_provider_for_devices`, never `device_id`.
7. **Certify suite.** Section 3 opts in, then runs `verify()` at L3 on each GPU as the check
   `directml@<device_key>`. Section 4 runs the pipeline on each GPU whose probe passed. A result
   counts only on a GPU whose hardware class lists the EP (an AMD GPU). On each other GPU it is
   `record-only`. XSE7 adds the AMD EPs.
8. **Certified.** For a field-test EP, certified means that sections 3 and 4 pass on the host. A
   person moves an EP to `ready` in a later commit, with a reviewed report as evidence. No code
   does it.

## Reason

- The user decisions of 2026-11-18: the field-test rules of Y14H item 11, and DirectML offered for
  AMD GPUs on Windows only.
- On a host with two GPUs, the DirectML `device_id` is the DXGI adapter index. It can name a
  different GPU than the device key.
- Packs come next, for example MIGraphX: the state is not only for a built-in EP.

## Consequences

- The order of `status().eps` on Windows is `trt-rtx`, `cuda`, `directml`, `cpu`.
- A catalog change gives a new catalog revision. Each stored L3 verdict then has an other key, and a
  `ready` pack is `installed_unverified` until its next trial session.
- A session on `directml` uses one intra-op thread, as a GPU pack does.
- There is no command to remove an opt-in. Delete `field-test.json` of the store.
- The note of `amd-windows` must change when DirectML leaves the field test.

## Evidence

Host: Windows 11, one RTX 3070 (NVIDIA driver 610.88) and one Intel UHD Graphics 770, 2026-11-18,
`onnxruntime-windowsml` 1.30.0.202609102321. ONNX Runtime lists three DirectML devices: the RTX 3070
under two LUIDs (DXGI adapters 0 and 2) and the UHD 770 (adapter 1).

- **Device.** A scratch run (not in git) read the PDH counters `GPU Process Memory` of its process
  for each LUID. On the RTX 3070 key: `ep_device_id` 0, 279 MiB dedicated on the LUID of adapter 0,
  nothing on the UHD 770. On the UHD 770 key: `ep_device_id` 1, 347 MiB shared on its LUID, 0 on
  the RTX 3070.
- **Probe.** `verify()` at L3 passes on each GPU, with a largest difference of 9.5e-7.
- **Pipeline.** Each model runs fp16 on each GPU, with each node on DirectML (395 and 401 nodes, 0
  on the CPU EP) and no warning. Against the CPU EP: box IoU 0.988 and 0.989, keypoint fraction
  max 0.0071 and 0.0057, median 0.0015 and 0.0015, p99 0.0048 and 0.0042 (RTX 3070, then UHD 770).
- **Suite.** `tools/certify_platform.py --wheel-dir`: sections 3 and 4 pass, and the four DirectML
  checks are `record-only`. Median ms of a call for 1, 3 and 6 cameras: DirectML 5.3, 7.9 and 15.3
  on the RTX 3070, and 35.8, 91.8 and 173.4 on the UHD 770; `trt-rtx` 6.1, 7.0 and 15.4; the CPU EP
  20.5 for 1 camera. The peak VRAM of the UHD 770 does not grow: the sampler reads dedicated memory
  only. The run changed no file in the user data and cache folders of skellytracker.
- **Refusal.** With no opt-in, `check_start()` and `start_pipeline()` raise `EpUnavailableError`.
  `recommend()` on this host gives `trt-rtx` in `nvidia-cc80-r580`, as before.

## Alternatives rejected

- **The option `device_id`.** It is the DXGI adapter index, not the GPU of the device key.
- **The opt-in in a setting of the app.** The suite needs its own opt-in, which its store deletes.
- **A recommendation of DirectML after the opt-in.** The user decided that the app never offers a
  field-test EP.

## Open work

See [open-work.md](../open-work.md).

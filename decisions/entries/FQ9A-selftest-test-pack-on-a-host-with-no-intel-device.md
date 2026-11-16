# FQ9A — The test pack step of `selftest()` on a host with no Intel device

**Status:** absorbed into [`self_test.py`](../../skellytracker/core/eps/self_test.py), 2026-11-16 (user; absorbed at landing; PR: pending).

## Decision

1. The test pack step of `selftest()` passes on a host with no Intel device when the test pack
   downloads, unpacks and registers. Its detail then says that the device list is not checked.
2. On a host with an Intel device, the step still needs that the EP lists a device.
3. A pack that does not register fails the step on each host.
4. A host has an Intel device when one or more of the hardware devices that ONNX Runtime lists has
   the PCI vendor id `8086`. This is the data that the EP reads for its device list. The child
   process of the step reads the list. When the list cannot be read, the step keeps the strict rule:
   it fails when the EP lists no device, and its detail says that the list could not be read.
5. Only `selftest()` changes. `ensure_registered()`, `verify()` and `build_session()` still raise
   `EpUnavailableError` when an EP lists no device.
6. The `ep_pack` test asserts the case of the host that runs it.

## Reason

- The user decided this rule on 2026-11-16: "The test pack step of `selftest()` passes on a host
  with no Intel device when the pack registers, and says so in its detail."
- The step proves the download and the install path. The test pack is an OpenVINO pack
  ([ADR-246B](246B-ep-catalog-store-and-install.md) item 4). A user with an AMD CPU must get a correct
  self test.
- The `ep_pack` CI job failed on each runner with an AMD CPU. The result depended on the CPU of the
  runner.

## Evidence

- ONNX Runtime `v1.31.0`, `onnxruntime/core/providers/openvino/ov_factory.cc` L92-L95: the device
  list of the OpenVINO EP skips each hardware device whose vendor id is not `vendor_id_`, with the
  comment "Not an Intel Device". `ov_factory.h` L105: `vendor_id_{0x8086}`, "Intel's PCI vendor ID".
- Run 43908364709 of `ep-pack.yml`: the Windows job failed with "registers, but the EP
  'OpenVINOExecutionProvider' lists no device on this host". The Linux job passed.
- Run 43910358178, with the device list in the error text: the Windows job failed with
  `CPUExecutionProvider on cpu 1022:0000`, and the Linux job failed with
  `CPUExecutionProvider on cpu 1022:0007`. `1022` is the PCI vendor id of AMD.
- On the Windows test host with an Intel CPU and an Intel GPU, the step passes with a device. There,
  `onnxruntime.capi._pybind_state.get_hardware_devices()` of `onnxruntime` 1.31.1 lists the CPU and
  the Intel GPU with the vendor id `8086`, and the NVIDIA GPU with `10de`.
- The source facts are of the EP code in the ONNX Runtime repository. The pack
  `onnxruntime-ep-openvino` 1.8.1 has no public source tag that this entry read.

## Alternatives rejected

- **The CPU name of `probe_host()`.** A CPU name is free text, and it is not the data that the EP
  reads. A name that cannot be read would hide a failure on an Intel host.

- **`selftest()` stays strict, and only the CI test skips.** An AMD user then gets a failed self test.
- **A different test pack.** Each other pack needs an NVIDIA GPU or macOS.

# 8N03 — The certify report obeys format 1.10.0: fewer rows, error numbers, the check list and the end of each record-only check

**Status:** accepted, 2026-11-23 (user).

## Decision

1. **Format.** `certify()` writes `skellycertify.report/1.10.0`. The report obeys section 5.8 of
   the format, "What a check writes".
2. **Rows.** A label has only the JPEG checks that its EP can have (`certify_names()` of
   `skellytracker/core/decode/certification.py`). A check of the CPU paths only runs one time,
   under the label `cpu`. `certify_plan()` counts in `total` each row that the run writes at its
   start. The top-level `seconds` is the length of the run.
3. **Values.** A value that is the same in each row is in `details` one time. A float has 4
   significant digits. A flag is a boolean, and "no value" is null.
4. **Errors.** A caught exception gives the class name in `error`, as written, and its number in
   `hresult`, `errno` or `code` (`error_numbers()` of `skellytracker/core/errors.py`). A report
   holds no message text. A failure on one frame writes `failed_frame` and the numbers of that
   frame.
5. **Versions.** `details.versions` holds Python, and MediaPipe when its check ran. The level
   `full` adds NumPy and OpenCV.
6. **Check list.** `skellytracker/core/eps/certify_checks.yaml` is the list of the check names of
   section 5.7 of the format. A person writes it. A new check goes into the list in the commit
   that adds it. Each `record-only` check has a `question` and an `end`.
7. **GPU frame path on an EP that is not an NVIDIA EP.** The checks `preprocess_graph_amd_ep.*`
   and `pipeline_amd_ep.*` ask if the EP keeps a decoded or preprocessed frame on the GPU, with no
   copy between the CPU and the GPU. The two checks of `DEDICATED_ONLY` run only on a dedicated
   GPU: on `directml`, a GPU with `GpuInfo.is_integrated` true has no row of them. On Windows the
   value is the DXCore property `IsIntegrated`. With null (not known), the checks run. On Linux
   the value is a fact of the kernel driver: for `amdgpu`, the file `board_info` or the flag
   `AMDGPU_IDS_FLAGS_FUSION`; for `i915` and `xe`, the memory query of the driver. Each other
   driver gives null. The reader makes no guess. The filter stays on `directml` until a Linux
   system with an AMD GPU has run the reader.
8. **Judged by GPU model.** A check of item 7 becomes a judged check on a system only with a
   reviewed pass row of `ep_evidence.yaml` for the EP, the OS and the GPU model. The EP joins the
   default EPs of the GPU preprocess only on such a GPU model. The code does not do this yet:
   today `directml` is judged on each GPU.
9. **Ends of the other record-only checks.** A timing has no end: it has no pass rule. A cut-JPEG
   check ends when the pipeline spec states what a run must do with a cut JPEG. A node placement
   check ends when a reviewed report for the EP shows 0 CPU nodes: it then passes only with 0. The
   check `<check>:exit` ends when the exit hang of the CUDA EP plugin
   ([ADR-C6A5](C6A5-exit-hang-of-the-cuda-ep-plugin.md)) has a fix or a workaround.

## Reason

- A review of a full report of one system found 368 rows. 126 were `not-run` rows that the EP can
  never have, and the CPU-only JPEG checks ran again under each GPU label.
- A reason code with no number did not let a developer find the cause.
- On Linux, `is_integrated` was a guess from the boot GPU. It is false for a system with one
  dedicated GPU. No Linux hardware has run the new reader. Thus the filter of item 7 applies only
  on `directml`.
- The run on an NVIDIA GPU with `directml` gave an unequal uploaded frame in 25 of 50 repeats. A
  pass on one GPU model thus says nothing about an other model.

## Evidence

- A projection of the old full report with the new rules: 154 rows in place of 368, and 32,791
  bytes in compact form in place of 65,656. No real run made these numbers.
- The constants of the DXCore reader are from `dxcore_interface.h` and `dxcore.h` of the Windows
  SDK 10.0.22621.0: `IsIntegrated = 12` and the IIDs of `IDXCoreAdapterFactory` and
  `IDXCoreAdapter`.
- The constants of the Linux reader are from the uapi headers `amdgpu_drm.h`, `i915_drm.h`,
  `xe_drm.h` and `drm.h` of the Linux kernel at the tag v6.12. The kernel sets the flag and hides
  the file from one driver flag, `AMD_IS_APU` (`amdgpu_kms.c`, `amdgpu_device.c`).
- On the development system, the DXCore reader gives false for the NVIDIA GeForce RTX 3070 and true for
  the Intel UHD Graphics 770.

## Open work

[open-work.md](../open-work.md)

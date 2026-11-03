# EP device checks

This folder holds a hardware test suite for the execution providers (EPs) of ONNX Runtime 1.31.0 on
an NVIDIA GPU. It makes the evidence for the GTX 1650 (Turing) and Pascal device checks, the driver
update checks and the missing sm_61 kernels of the CUDA 12 pack. An evidence decision entry will
name it ([ADR-EY8R](../../entries/EY8R-tools-and-scripts.md)). The suite does not use the
skellytracker package code.

## What the suite tests

The suite tests five routes. Each route has its own uv environment and runs in its own processes.
Two packs with the same EP name never share a process.

| Route | Packs (exact pins) | Index |
|---|---|---|
| `cpu` | `onnxruntime==1.31.0` | PyPI |
| `cuda-cu13` | `onnxruntime-ep-cuda13==0.3.0`, `nvidia-cublas` 13.8.0.4 (Windows) or 13.8.2.12 (Linux), `nvidia-cudnn-cu13==9.27.0.42` | Azure `onnxruntime-cuda-13` for the plugin |
| `cuda-cu12` | `onnxruntime-ep-cuda12==0.3.0`, `nvidia-cublas-cu12==12.9.2.10`, `nvidia-cuda-runtime-cu12==12.9.79`, `nvidia-cudnn-cu12==9.27.0.42` | Azure `onnxruntime-cuda-12` for the plugin |
| `trt-rtx-cu13` | `onnxruntime-ep-nv-tensorrt-rtx-cu13==0.5.0` | PyPI |
| `trt-rtx-cu12` | `onnxruntime-ep-nv-tensorrt-rtx-cu12==0.5.0` | PyPI |

Each route also has `onnxruntime==1.31.0` and `numpy==2.5.4`.

For each route, the suite does these steps:

1. **L1 prediction.** The suite reads the GPU facts (NVML, else `nvidia-smi`): the name, the compute
   capability (CC), the driver version, the highest CUDA version of the driver
   (`cuDriverGetVersion`), the VRAM and the PCI ids. It predicts a verdict from the table `RULES` in
   `run_checks.py`: `ok`, `experimental`, `update-driver` (with the target branch), `unsupported` or
   `no-nvidia-gpu`.
2. **L2 registration.** The child process registers the plugin with
   `register_execution_provider_library` and the absolute library path. It then finds the device in
   `get_ep_devices()` by the EP name and the NVIDIA vendor id. On Windows, the child first adds the
   NVIDIA library folders of the environment to the front of `PATH`. It also refuses a pack file path
   of 240 characters or more.
3. **L3 probe.** The child runs a small Conv and Relu model (1x3x64x64, opset 17) with
   `add_provider_for_devices`, `session.disable_cpu_ep_fallback=1` and
   `session.record_ep_graph_assignment_info=1`. L3 passes when Conv and Relu are on the target EP, no
   node is on a different EP, and the output agrees with the CPU EP.
4. **L4 real models.** The child runs RTMPose-m 256x192, RTMO-s 640x640, YOLOX-m 640x640 and
   RTMW-x 384x288 at batch 1. Each model runs in a new process, one at a time. The largest model runs
   last. The suite records the session build time, the first run time, the median of N runs, the
   NaN and Inf counts, the largest absolute difference from the CPU fp32 output, the node counts for
   each EP, the op types on the CPU, and the peak VRAM (NVML, for the full device). When a model
   fails with the CPU fallback turned off, the suite runs it again with the fallback turned on. It
   then records the op types that moved to the CPU, and the error text and op type of the failure.
   The column `Strict` of the report shows if the session built with the fallback turned off.
   For the CUDA EP, `Strict` is usually `False`: ORT puts some shape nodes (for example Slice,
   Concat, Gather) on the CPU EP. L4 fails only when the run with the fallback turned on also fails.

The input of the real models is one fixed test image. The preprocessing is simple. This is not an
accuracy test. It compares each EP with the CPU EP.

The fp16 models are copies that `onnxconverter-common` 1.16.0 makes with `keep_io_types=True`.
The suite compares them with the CPU fp32 output.

A child crash, an exit code (for example 127 or `0xC0000005`) or a timeout is a recorded reason. It
does not stop the suite.

### Driver scenarios

The report names the scenario from the installed driver branch:

| Scenario | Driver branch | Prediction on a GTX 1650 (CC 7.5) | Prediction on a GTX 10xx (CC 6.1) |
|---|---|---|---|
| A | below R525 | `cuda-cu12`: `update-driver` to R525; `cuda-cu13`: `update-driver` to R580; the TensorRT-RTX routes: `unsupported` | `cuda-cu12`: `update-driver` to R525; the other GPU routes: `unsupported` |
| B | R525 to R579 | `cuda-cu12`: `ok`; `cuda-cu13`: `update-driver` to R580; the TensorRT-RTX routes: `unsupported` | `cuda-cu12`: `ok`; the other GPU routes: `unsupported` |
| C | R580 or newer (Pascal: R580, the last branch) | `cuda-cu13`, `cuda-cu12`: `ok`; the TensorRT-RTX routes: `unsupported` | `cuda-cu12`: `ok`; the other GPU routes: `unsupported` |

- A driver branch is the major version rounded down to a multiple of 5. For example, 582.78 is R580
  and 576.88 is R575.
- The `cuda-cu12` floor is R525: CUDA 12.x minor version compatibility needs a driver of 525 or
  later (<https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html>).
  The pack has native code (SASS) for each CC in its list, so it needs no PTX compilation on the
  driver.
- TensorRT-RTX supports RTX GPUs of the Ampere generation (CC 8.0) and later
  (<https://github.com/NVIDIA/TensorRT-RTX-EP-ABI>).
- In scenario A and B, the suite runs all routes, also the routes that it predicts to fail. The
  failure mode is the evidence.
- In scenario C, use `--include-unexpected` to also run the routes that it predicts to fail.
- On Pascal, `update-driver` never gives a target above R580. A Pascal card with a driver above R580
  is an anomaly in the report.
- A mismatch between the prediction and the observed result is a finding in the report.

Each route record holds a verdict key: the driver version, the PCI `vendor:device:subsystem`, the OS
build, and the ORT and pack versions. When the key changes, the product must verify the route again.

## Prerequisites

- **uv** 0.11 or later. The suite was tested with uv 0.11.8. uv downloads CPython 3.12 if necessary.
- **git**, to clone the repository.
- **An NVIDIA driver**. The minimum branches:

  | Route | Lowest driver branch | GPU |
  |---|---|---|
  | `cuda-cu13` | R580 | CC 7.5 or higher |
  | `cuda-cu12` | R525 | CC in the build list. Windows: 6.1, 7.5, 8.6, 8.9, 12.0. Linux: 6.0, 7.0, 7.5, 8.0, 8.6, 8.9, 9.0, 12.0 |
  | `trt-rtx-cu13` | R580 | CC 8.0 or higher (Ampere and later) |
  | `trt-rtx-cu12` | R570 | CC 8.0 or higher |

- **Network access** to PyPI, the Azure feeds `aiinfra.pkgs.visualstudio.com`,
  `download.openmmlab.com` and `github.com`.
- **Disk space.** See [Sizes and times](#sizes-and-times).

## Commands

### Get the suite

The folder is on the branch `hw-and-ep-work`. Clone the repository that has this branch. Replace
`<repository URL>` with its URL.

```sh
git clone <repository URL> skellytracker
cd skellytracker
git checkout hw-and-ep-work
```

Run all commands of this README in the root folder of the clone. The suite does not need the
environment of the repository. Do not run `uv sync` for it.

### Full run

```sh
uv run --no-project --python 3.12 python -B decisions/scripts/ep_device_checks/run_checks.py --include-unexpected --redact-check
```

### Quick run (L2 and L3 only)

```sh
uv run --no-project --python 3.12 python -B decisions/scripts/ep_device_checks/run_checks.py --quick --include-unexpected --redact-check
```

### Options

| Option | Use |
|---|---|
| `--routes cpu,cuda-cu12` | Run only these routes |
| `--include-unexpected` | Also run the routes that the suite predicts to fail |
| `--quick` | Run only L2 and L3 |
| `--models rtmpose-m,yolox-m` | Run only these models |
| `--precision fp32,fp16` | The precisions. The default is `fp32,fp16`. Below CC 7.0 the default is `fp32` |
| `--runs N` | The number of timed runs for the median. The default is 20 |
| `--timeout S` | The time limit in seconds for each L4 child. The default is 900 |
| `--out DIR` | The report folder. The default is a new folder in the system temp folder |
| `--work DIR` | The folder for the environments, the models and the uv cache |
| `--redact-check` | Scan the report for the user name, the host name and user paths |
| `--plan-only` | Print the GPU facts and the plan, then stop |

The default work folder is `%LOCALAPPDATA%\epdc` on Windows and `~/.cache/epdc` on Linux. The suite
keeps it after each run, so the packs and the models download only once. Delete it after the last
run. Keep the work folder path short: a pack file path of 240 characters or more fails L2.

The suite prints the report folder at the end. It holds `report.json` and `report.md`.

### Driver links

Each run prints the driver download links for the GPU and the OS, at the start and at the end. The
list marks the installed scenario and gives the next step of the
[driver procedure](#driver-procedure-gtx-1650-turing-cc-75). The end of the run also gives the
`compare` command with the path of the new report. To print only the links, run this command. It
downloads nothing and runs no test:

```sh
uv run --no-project --python 3.12 python -B decisions/scripts/ep_device_checks/run_checks.py drivers
```

The links come from the table `DRIVERS` in `run_checks.py`. That table holds the same rows as the
tables of this README. If you change a row, change it in both places.

## Sizes and times

Measured on Windows 11 with an empty uv cache (`win_amd64` wheels, from the `uv.lock` of each
environment):

| Item | Download |
|---|---|
| `prep` environment (ORT, onnx, onnxconverter-common, numpy, pillow) | 42 MB |
| `cpu` | 27 MB |
| `cuda-cu13` | 1037 MB |
| `cuda-cu12` | 1569 MB |
| `trt-rtx-cu13` | 133 MB |
| `trt-rtx-cu12` | 136 MB |
| The four model archives and the test image | 395 MB |

- The total download is about 3.3 GB. A quick run does not download the models.
- The work folder needs about 5.2 GB of disk: the uv cache holds about 4.5 GB, and the models and the
  fp16 copies hold about 0.65 GB. uv hardlinks the environments to the cache on the same disk, so
  they add almost no space. Make sure that 6 GB is free.
- uv also downloads CPython 3.12 (about 30 MB) if it is not on the computer.
- Each report holds the measured sizes of that machine (`install.download_mb`, `disk_mb`).

Measured times on an RTX 3070 (CC 8.6, Windows 11, driver 610.88):

| Run | Time |
|---|---|
| Quick run, all five routes, empty uv cache (includes the 2.9 GB pack download) | 100 s |
| Full run, all five routes, packs and models already downloaded | 120 s |

- The GTX 1650 and a Pascal card are slower. The TensorRT-RTX build time is longer on CC 7.5. These
  times were not measured. Allow 10 to 20 minutes for a full run, plus the download time.
- Each L4 child has a time limit of 900 s (`--timeout`).

### Known results on the RTX 3070

- TensorRT-RTX 0.5.0 (cu13 and cu12) cannot build YOLOX-m or RTMO-s. The TensorRT log gives
  "ITopKLayer ... K exceeds the maximum value allowed (3840)". These two models have a TopK in their
  NMS part with a larger K. The other two models pass.
- `onnxconverter-common` makes an RTMO-s fp16 copy that fails the strict type check. The suite skips
  RTMO-s fp16 with that reason.

### Known results on the GTX 1650

Quick runs (L2 and L3) on a GTX 1650 (CC 7.5, 4 GB), Windows 11, drivers 566.36, 572.16, 576.88,
580.88 and 621.01 (2026-11-03). The reports are in [reports/gtx-1650/](reports/gtx-1650/).

- `cuda-cu12` passes L2 and L3 on each driver, also on 566.36 (R565). This result set the floor to
  R525.
- `cuda-cu13` lists no device below R580 ("no device" at L2: no crash and no silent CPU fallback).
  It passes L2 and L3 on 580.88 and 621.01.
- `trt-rtx-cu13` registers, but lists no device on 580.88 and 621.01. This result set the floor to
  CC 8.0.
- After each driver change, the verdict key of each route changed (field `driver_version`).
- The runs were quick runs, so they hold no L4 (real model) results and no timings.

## What to send back

Send `report.json` and `report.md` of each run.

- Before you send a report, make sure that the run printed "Redact check: no user name, host name or
  user path in the report."
- If the redact check fails, do not send the report. Tell us which item it found.
- The report holds the GPU name, the CC, the driver version, the VRAM, the PCI ids, the OS name and
  build, and the Python, ORT and pack versions. It does not hold a host name, a user name, a user
  path, a GPU UUID or a serial number.

## Driver procedure: GTX 1650 (Turing, CC 7.5)

Use this procedure to test the `update-driver` logic. You run the suite with an old driver, then
with the current driver, and then compare the two reports.

### Driver versions

The versions below list the GTX 1650 on the NVIDIA driver pages (checked on 2026-11-03). The CUDA
column is the highest CUDA version of that driver, from the NVIDIA CUDA Toolkit release notes
(<https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html>, "CUDA Toolkit and
Corresponding Driver Versions").

| Scenario | OS | Version | Date | Highest CUDA | Source |
|---|---|---|---|---|---|
| A | Windows, Linux | older than R525 | – | 11.x | <https://www.nvidia.com/en-us/drivers/> |
| B | Windows | 566.36 | 2024-12-05 | 12.6 Update 3 | <https://www.nvidia.com/Download/driverResults.aspx/237719/en-us> |
| B | Linux | 565.77 | 2024-12-05 | 12.6 Update 3 | <https://www.nvidia.com/Download/driverResults.aspx/237587/en-us> |
| B | Windows | 572.16 | 2025-01-30 | 12.8 | <https://www.nvidia.com/Download/driverResults.aspx/240547/en-us> |
| B | Windows | 576.88 | 2025-07-01 | 12.9 Update 1 | <https://www.nvidia.com/en-us/drivers/details/248978/> |
| B | Linux | 575.64.05 | 2025-07-22 | 12.9 Update 1 | <https://www.nvidia.com/en-us/drivers/details/250991/> |
| C | Windows | 580.88 | 2025-07-31 | 13.0 | <https://www.nvidia.com/en-us/drivers/details/251255/> |
| C | Windows | 621.01 (newest) | 2026-10-21 | 13.4 or higher | <https://www.nvidia.com/en-us/drivers/details/282412/> |
| C | Linux | 580.196.07 | 2026-10-21 | 13.0 | <https://www.nvidia.com/en-us/drivers/details/281487/> |
| C | Linux | 615.78.08 | 2026-10-07 | 13.4 | <https://www.nvidia.com/en-us/drivers/details/280299/> |

The CUDA release notes give these minimum drivers: CUDA 12.8 needs 570.26 (Linux) or 570.65
(Windows). CUDA 12.9 needs 575.51.03 (Linux) or 576.02 (Windows). CUDA 13.0 needs 580.65.06 (Linux).
The 13.0 notes give no Windows value. The newer notes give only the branch: R580 for CUDA 13.0.

### Windows

1. Pause Windows Update: open Settings > Windows Update > Pause updates. Windows Update can replace
   the GPU driver during the test. A stronger method is the group policy "Do not include drivers with
   Windows Updates" (<https://learn.microsoft.com/windows/client-management/mdm/policy-csp-update>).
2. Download the old driver of scenario A or B from the table. The suite also prints these links
   ([Driver links](#driver-links)).
3. Install it with a clean installation. In the NVIDIA installer, select "Custom (Advanced)" and then
   "Perform a clean installation". For a downgrade, you can also first remove the current driver with
   Display Driver Uninstaller (DDU) in Safe Mode.
4. Restart the computer.
5. Run `nvidia-smi` and make sure that it shows the old driver version.
6. Do the full run. Use `--out` to put the report in a folder for the GPU and the driver version:
   `--out decisions/scripts/ep_device_checks/reports/<gpu>/<driver version>`. For example:
   `--out decisions/scripts/ep_device_checks/reports/gtx-1650/566.36`. The suite runs all routes in
   scenario A and B.
7. Install the current driver (scenario C) with a clean installation, as in step 3.
8. Restart the computer, and make sure that `nvidia-smi` shows the new version.
9. Do the full run again with a different `--out` folder, for example
   `--out decisions/scripts/ep_device_checks/reports/gtx-1650/621.01`.
10. Compare the two reports:

    ```sh
    uv run --no-project --python 3.12 python -B decisions/scripts/ep_device_checks/run_checks.py compare decisions/scripts/ep_device_checks/reports/gtx-1650/566.36/report.json decisions/scripts/ep_device_checks/reports/gtx-1650/621.01/report.json --out decisions/scripts/ep_device_checks/reports/gtx-1650/compare
    ```

11. Resume Windows Update.

You can also do the procedure with three drivers: A, then B, then C. Give all three reports to
`compare`. It compares each report with the next one.

The `compare` output shows, for each route, the prediction and the result before and after, and
whether the change agrees with the prediction. It also shows that the verdict key changed, so the
product would verify the route again. It writes `compare.json` and `compare.md`.

### Linux (UNVERIFIED)

The suite was not run on Linux. The steps are the same, with these changes:

1. Stop automatic driver updates. For example, hold the driver packages of your package manager.
2. Install the old driver. Use the packages of your distribution, or the NVIDIA `.run` file of the
   table. Remove the current driver before a downgrade.
3. Restart the computer, and make sure that `nvidia-smi` shows the old version.
4. Do the full run, then install the current driver, restart, run again and compare, as on Windows.

On Linux the child process starts again with `LD_LIBRARY_PATH` set to the NVIDIA library folders of
the environment. This method is UNVERIFIED.

## Pascal: GTX 10xx (CC 6.1)

The suite uses the same code and the same rules table for a Pascal card.

### Recommended card

- Use one CC 6.1 card with 6 GB or more, for example a GTX 1060 6 GB, a GTX 1070 or a GTX 1080. All
  consumer Pascal cards are CC 6.1, so one card gives the result for all of them.
- A GTX 1050 Ti 4 GB is an optional low-VRAM check.
- A 2 GB card is not useful: the suite skips YOLOX-m and RTMW-x on it ("skipped: VRAM").

### What the suite expects on Pascal

- Only `cuda-cu12` is expected to work. Its build has SASS for sm_61 on Windows and Linux. It needs
  the R525 branch or newer.
- `cuda-cu13`, `trt-rtx-cu13` and `trt-rtx-cu12` are `unsupported` for an architecture reason.
  CUDA 13 has no build below CC 7.5. TensorRT-RTX supports CC 8.0 and later only. A driver update
  does not fix them.
- The `cuda-cu12` build has 42 kernels with no sm_61 version. With the CPU fallback turned
  off, a missing kernel makes the session build or the first run fail. The report then holds the
  error text and the op type. The suite runs the model again with the fallback turned on, and records
  the op types that moved to the CPU. This is the main evidence for the missing sm_61 kernels.
- fp32 is the target. The suite runs fp16 only when you give `--precision fp32,fp16`. An fp16 result
  on Pascal is informational, because consumer Pascal fp16 throughput is very low.
- On a card with less VRAM than a model needs, the suite skips the model with the reason
  "skipped: VRAM".

### Pascal driver versions

R580 is the last branch for Pascal. No R590 or newer driver lists the GTX 1060 or the GTX 1050 Ti
(checked on 2026-11-03). On Windows, R580 now gets only security update drivers (582.xx). The last
R580 Game Ready driver is 581.80 (2025-11-04, <https://www.nvidia.com/en-us/drivers/details/257496/>).

| Scenario | OS | Version | Date | Highest CUDA | Source |
|---|---|---|---|---|---|
| A | Windows, Linux | older than R525 | – | 11.x | <https://www.nvidia.com/en-us/drivers/> |
| B | Windows | 566.36 | 2024-12-05 | 12.6 Update 3 | <https://www.nvidia.com/Download/driverResults.aspx/237719/en-us> |
| B | Linux | 565.77 | 2024-12-05 | 12.6 Update 3 | <https://www.nvidia.com/Download/driverResults.aspx/237587/en-us> |
| B | Windows | 576.88 | 2025-07-01 | 12.9 Update 1 | <https://www.nvidia.com/en-us/drivers/details/248978/> |
| B | Linux | 575.64.05 | 2025-07-22 | 12.9 Update 1 | <https://www.nvidia.com/en-us/drivers/details/250991/> |
| C | Windows | 582.78 (security update, R580) | 2026-09-30 | 13.0 | <https://www.nvidia.com/en-us/drivers/details/280034/> |
| C | Linux | 580.196.07 | 2026-10-21 | 13.0 | <https://www.nvidia.com/en-us/drivers/details/281487/> |

These drivers list both the GTX 1060 and the GTX 1050 Ti. A CUDA 13 driver does not make CUDA 13 work
on Pascal: CUDA 13 removed Maxwell, Pascal and Volta.

### Procedure

1. Do the driver procedure of the GTX 1650 section, with the Pascal driver versions.
2. Do each full run with `--include-unexpected`, so that the suite also records how the three
   unsupported routes fail.
3. For scenario C, install R580, not a newer branch. A newer branch does not support Pascal.
4. Send back the reports of each run and the `compare` output.

## Files

| File | Runs in | Use |
|---|---|---|
| `run_checks.py` | any Python 3.12 (standard library only) | GPU facts, rules table, plan, environments, downloads, children, report, `compare` |
| `route_check.py` | the environment of one route | L2, L3 or L4 for one job |
| `prep_assets.py` | the `prep` environment | probe model, model inputs, CPU references, fp16 copies |
| `../tests/test_ep_device_checks.py` | the repository tests | the rules table with fake GPU facts, `compare` |

The suite checks the sha256 of each download: the model archives, the models in them and the test
image. The models come from the OpenMMLab download server. The test image comes from the freemocap
`skellysamples` releases.

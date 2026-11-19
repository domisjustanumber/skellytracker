# GPU setup

The base dependency `onnxruntime` gives the CPU EP, the CoreML EP on macOS and the DirectML EP on
Windows. The DirectML EP is in a field test (see [Field test](#field-test)). A GPU EP for an
NVIDIA GPU comes as a plugin EP pack. The command `skellytracker-eps install` puts a pack in the EP
store of the user. A pack is not a dependency of the package
([ADR-N6E8](decisions/entries/N6E8-onnxruntime-1-30-on-each-os.md) items 2 and 3). The AMD GPU EPs
are in a field test too: a pack on Linux, and a package of the Windows ML catalog on Windows
([ADR-XSE7](decisions/entries/XSE7-amd-eps-in-the-field-test.md)).

The ONNX trackers of this version (RTMPose, YOLOX) run on the CPU. On macOS, they can also run on
CoreML. They do not use the EP packs. The new code calls `skellytracker.core.eps.build_session()`.
The pipelines of a later version use it.

## EP keys

| Key | EP | Needs |
|---|---|---|
| `trt-rtx` | NVIDIA TensorRT for RTX, pack `onnxruntime-ep-nv-tensorrt-rtx-cu13` | An NVIDIA GPU with compute capability 8.0 or higher, and a driver of R580 or later on Windows, or R590 or later on Linux |
| `cuda` | NVIDIA CUDA, pack `onnxruntime-ep-cuda13` with cuBLAS and cuDNN | An NVIDIA GPU of the Turing generation or newer (compute capability 7.5), and a driver of R580 or later |
| `coreml` | Apple Core ML, a part of ONNX Runtime | macOS on Apple Silicon |
| `amdgpu` | AMD GPU EP of the Windows ML catalog | Windows, an AMD GPU, an AMD driver 24.12.1 or later, and the field-test opt-in |
| `migraphx` | AMD MIGraphX. Linux: pack `onnxruntime-ep-migraphx` for the ROCm release of the host, with `migraphx-libs`. Windows: the EP of the Windows ML catalog | An AMD GPU and the field-test opt-in. Linux: ROCm 10.0, 10.1 or 10.2 is installed. Windows: an RDNA 3 GPU or newer |
| `directml` | Microsoft DirectML, a part of the Windows ML build of ONNX Runtime | Windows and a DirectX 12 GPU, and the field-test opt-in |
| `cpu` | The CPU EP, a part of ONNX Runtime | – |

- The packs use CUDA 13. R580 is the first driver branch with CUDA 13.
- An NVIDIA GPU older than Turing runs on the CPU only. No driver gives it CUDA 13.
- Classic TensorRT (`trt`), OpenVINO, QNN and Vitis AI are reserved keys. A request for one fails
  with the reason.
- The `migraphx` pack installs no ROCm. Without ROCm, the state is `unsupported` with the reason
  code `rocm-missing`. AMD tested the packs with ONNX Runtime 1.29 only, so their state is
  `untested-ort`.
- You do not need a CUDA toolkit. The packs hold their libraries.

## Install a pack

```sh
uv run skellytracker-eps status              # the EP state of this host; no network
uv run skellytracker-eps install --dry-run   # the plan and its size
uv run skellytracker-eps install             # each pack that a GPU of this host can run
uv run skellytracker-eps install cuda        # one pack
uv run poe setup-eps --recommended           # the same command as a poe task
```

- A download starts only after this command. skellytracker never downloads a pack in the background.
- `install` shows the download size and a licence link for each pack. Then it asks one question.
  `--yes` answers it. With no terminal and no `--yes`, the command stops with exit code 2.
- The `trt-rtx` pack is about 106 MB. The `cuda` pack is about 966 MB.
- After the install, a child process registers the pack and runs a trial session on a small model.
- A plain `uv sync` gives the CPU core. It does not change the EP store.

## Field test

An EP in a field test has no reviewed certification report for the OS yet. Today these are
`directml` on Windows ([ADR-Z5X7](decisions/entries/Z5X7-field-test-state-and-directml.md)),
`amdgpu` on Windows and `migraphx` on Windows and Linux ([ADR-XSE7](decisions/entries/XSE7-amd-eps-in-the-field-test.md)).

```sh
uv run skellytracker-eps install directml --field-test   # the opt-in; DirectML needs no download
uv run skellytracker-eps install migraphx --field-test   # Linux: the pack; Windows: the Windows ML package
```

- The EP store keeps the opt-in. Without it, a request for the EP fails with exit code 3 and the
  state `field_test`. No other EP runs in its place.
- `status()` shows the EP with the state `field_test` and the `catalog_status` `field-test`.
  `recommend()` never gives the EP, also after the opt-in.
- The app offers DirectML for AMD GPUs only. You can opt in on each GPU, for example to test it.
- For `amdgpu`, and for `migraphx` on Windows, `install` asks one question. Then Windows downloads
  and installs the package of the Windows ML catalog. No command of skellytracker removes it.
  PowerShell removes it for your user with `Remove-AppxPackage <full name>`.
- The certify suite (`tools/certify_platform.py`) opts in to each field-test EP in its own store, and
  tests DirectML on each GPU of the host. On an AMD GPU it also tests the AMD EPs. On Windows, it
  installs the Windows ML package of each AMD EP that the catalog offers, and removes each package
  that it installed at the end. It never removes a package that was on the PC before.

## The EP store

The store is the folder `eps` in the user data folder of skellytracker, for example
`%LOCALAPPDATA%\skellytracker\eps` on Windows and `~/.local/share/skellytracker/eps` on Linux.
`SKELLYTRACKER_EP_STORE` sets a different folder for the whole process. Each checkout and each
application of the user share one store.

- On Windows, a file path of a pack must have fewer than 240 characters. If `install` refuses the
  store path, set `SKELLYTRACKER_EP_STORE` to a shorter folder.
- `skellytracker-eps gc` deletes the packs that no environment needs.
- `skellytracker-eps remove <pack_id>` deletes one pack.

## Install with no network

```sh
uv run skellytracker-eps download cuda --platform win_amd64 --dest wheels   # on a host with a network
uv run skellytracker-eps install cuda --from-dir wheels                     # on the target host
```

Use this procedure when a proxy or a firewall blocks the download. The platform tags are
`win_amd64` and `manylinux_x86_64`. The sha256 of each wheel must agree with the EP catalog.

The download uses the system proxy setting and the system trust store. A PAC file is not supported.
`SSL_CERT_FILE` or `SSL_CERT_DIR` sets a different trust store. `skellytracker-eps doctor` shows the
proxy, the trust store and if each index is reachable.

## Select an EP

No environment variable selects the EP or the device. The caller passes a concrete key.

```python
from skellytracker.core import eps

choice = eps.recommend("performance")        # or "accuracy", which is `cpu` with fp32
session, report = eps.build_session(
    "model.onnx",
    execution_provider=choice.chosen.ep_key,
    ep_options=dict(choice.options),
)
print(report.used_ep, report.cpu_nodes, report.cpu_op_types)
```

- `recommend()` reads a table of hardware classes. It runs no benchmark. `choice.skipped` names each
  faster EP that is not ready, with the reason.
- `build_session()` never runs a session on an other EP than the requested EP. It raises
  `EpUnavailableError` with the install command when the pack is not ready.
- A node of a model can run on the CPU EP. `report.cpu_nodes` and `report.cpu_op_types` report it.
- With no `device_key`, a session uses the GPU with the most VRAM. `eps.run_devices("cuda")` lists
  the GPUs with their device keys. `directml` can use each GPU of the host.
- The session takes the ONNX Runtime device of the GPU of `device_key`: the PCI ids, then the LUID
  on Windows. For DirectML, the ONNX Runtime option `device_id` is the DXGI adapter index. On a host
  with two GPUs, that index can name the other GPU.

## EP options

`ep_options` maps option names to string values. Each other option is refused.

| EP | Allowed options |
|---|---|
| `cuda` | `prefer_nhwc` (`0`, `1`), `use_tf32` (`0`, `1`), `arena.max_mem` (positive bytes) |
| `trt-rtx` | `enable_cuda_graph` (`0`, `1`) |
| `coreml` | `MLComputeUnits` (`ALL`, `CPUAndGPU`, `CPUAndNeuralEngine`, `CPUOnly`) |
| `directml` | none |
| `cpu` | none |

`device_id` is refused for each EP. Use `device_key`.

## Exit codes of `skellytracker-eps`

| Code | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| Meaning | ok | failure | usage, refused key or option | EP not available | session not created | GPU memory exhausted | cancelled |

## Frozen applications

skellytracker has a PyInstaller hook. PyInstaller finds it through the entry point group
`pyinstaller40`. The hook collects the YAML files of the package. An application does not put an EP
pack in its bundle: the pack stays in the EP store. A frozen application that calls
`skellytracker-eps install` or `eps.verify()` must call `multiprocessing.freeze_support()` at its
start.

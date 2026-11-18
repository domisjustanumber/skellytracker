# 88ZB — The GPU JPEG decoder is a component of the EP catalog that the packs share

**Status:** accepted, 2026-11-18 (user, decisions on the step S4 of the native JPEG input; PR: pending).

## Decision

This entry extends [ADR-246B](246B-ep-catalog-store-and-install.md) items 1 and 6.

1. **Component.** `ep_catalog.yaml` has a section `components`. A component is a set of wheels that
   packs share. A pack row names its component in `component`. The store folder
   `<id>/<version>/` of a component does not change after its install, as a pack folder. The lock
   has a row for each component, with the fields of a pack row. `tools/ep_catalog.py` gives the
   checks.
2. **Decoder.** The component `gpu-jpeg-cu13` holds `nvidia-nvimgcodec-cu13` 0.10.0.9,
   `nvidia-nvjpeg` 13.3.2.43 and `nvidia-cuda-runtime` 13.4.92. The packs of `cuda` and `trt-rtx`
   name it. It is not a base dependency and not an extra of `pyproject.toml`.
3. **Install.** Each install of `cuda` or `trt-rtx` installs the component. There is no opt-out. A
   plan holds the component one time. `install <key>` on a store of an older catalog installs only
   the component: the pack folder does not change. A failure of the component goes to
   `InstallResult.warnings`, not to `failed`, and the exit code stays 0. `download()` includes its
   wheels. `gc()` keeps each component of the catalog.
4. **State.** `store.component_state()` gives `installed`, `missing` or `other_version`, with no
   library load. `PackStatus.jpeg_decoder` gives it, and `PackStatus.jpeg_decoder_hint` gives the
   install command. `PackState` does not change. No component state blocks the EP: the run decodes
   on the CPU ([ADR-P245](../../specs/pipeline/decisions/entries/P245-jpeg-frame-input.md) item 8).
   `PackStatus.download_bytes` includes the component when it is not installed.
5. **Load.** `registration.prepare_jpeg_decoder()` makes the component importable and imports
   `nvidia.nvimgcodec` at its first call. The component folder is first on `sys.path` and in
   `nvidia.__path__`. It returns the module and the path of the CUDA runtime of the component. The
   wait for the decode (`cudaStreamSynchronize`) uses that CUDA runtime on each EP. It returns None
   and logs the reason when the import fails or an other copy of the module is imported. A plain
   `import skellytracker` loads no `nvidia` module.

## Reason

- A pack folder does not change after its install. Thus wheels that a pack gets at the same
  version never reach a store that holds the pack. A new pack version makes the pack `stale`,
  `stale` blocks the EP ([ADR-D8DH](D8DH-sessions-errors-and-the-ready-rule.md) item 3), and the
  user downloads the full pack again: 966 MB for `cuda` on Windows.
- A missing decoder must not block the EP. A new `PackState` changes the ready rule of ADR-D8DH
  item 3. A field does not.
- No EP pack loads a CUDA runtime that exports `cudaStreamSynchronize` (Evidence). One CUDA runtime
  in the component serves both EPs and both platforms, for 2.7 MB.

## Consequences

- An install of `cuda` or `trt-rtx` downloads 18.3 MB more on Windows (38.9 MB on disk) and 32.5 MB
  more on Linux (87.4 MB on disk), in MB of 1024 x 1024 bytes.
- `store.verdict_key()` holds the catalog revision, so each catalog change drops the saved
  verifications. `cuda` goes from `ready` to `installed_unverified` until `install cuda` or `verify`
  runs. `trt-rtx` stays `untested-ort`.
- `nvimgcodec.Decoder()` prints errors for nvJPEG2000 and nvTIFF to stderr: the component has no
  such wheels. The decoder step must keep them out of the output of a run.
- PyInstaller can put a copy of nvImageCodec of the build environment in a frozen application. A
  frozen import comes before `sys.path`. The build environment must not hold nvImageCodec.
- The Linux preload list and `libcudart.so.13` come from the wheel listings. No Linux host loaded
  them.

## Evidence

- Code facts: `installer._install_pack()` returns when `pack.json` exists. `store.pack_state()`
  gives `stale` for an other version of a pack. `records.USABLE_STATES` has no `stale`.
- On 2026-11-18, Windows 11, RTX 3070, driver 610.88, ONNX Runtime 1.31.1, `cuda-cu13` 0.3.0,
  `trt-rtx-cu13` 0.5.0, nvImageCodec 0.10.0
  ([`88zb_loaded_cuda_runtime.py`](../scripts/88zb_loaded_cuda_runtime.py)): after a session on
  `cuda` or `trt-rtx`, the process holds the `nvcudart_hybrid64.dll` of the driver and no
  `cudart64_13.dll`. The `trt-rtx` pack holds a `cudart64_13.dll`, but the EP does not load it.
  `nvcudart_hybrid64.dll` does not export `cudaStreamSynchronize`. nvImageCodec also uses
  `nvcudart_hybrid64.dll`.
- Same host, after the install of the component into the store
  ([`88zb_store_decoder_check.py`](../scripts/88zb_store_decoder_check.py)): on `cuda` and on
  `trt-rtx`, a 640x480 JPEG at quality 90 decodes into GPU memory on a private non-blocking
  stream. The wait uses `cudaStreamSynchronize` of the CUDA runtime of the component. The pixels
  differ from `cv2.imdecode` by at most 3 `uint8` steps, mean 0.034. nvImageCodec, nvJPEG and the
  CUDA runtime load from the component folder.

## Alternatives rejected

- The wheels in `dependency_wheels` of each pack at the same version: a store with the pack never
  gets them.
- The same with a new pack version: the pack goes `stale`, the EP is blocked, and the full pack
  downloads again.
- `stale` or a new `PackState` for a missing decoder: see Reason.
- The CUDA runtime of the `trt-rtx` pack: the `cuda` pack has none.
- `cuStreamSynchronize` of the driver library: no download, but it needs context code, and it is
  not tested.
- An extra of `pyproject.toml`: a GPU package goes in the EP store, not in `pyproject.toml`.

## Not repeated

- A `Decoder` with the backend `GPU_ONLY` alone fails with status 7 (`ARCH_MISMATCH`). The nvJPEG
  CUDA decoder is a hybrid backend. Allow `GPU_ONLY` and `HYBRID_CPU_GPU`.

## Open work

See [open-work.md](../open-work.md).

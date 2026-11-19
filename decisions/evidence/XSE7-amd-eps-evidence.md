# Evidence for XSE7: the AMD indexes and wheels, and the Windows ML catalog route

This file is the evidence of
[ADR-XSE7](../entries/XSE7-amd-eps-in-the-field-test.md). The script paths are relative to
`decisions/`.

2026-11-18. Each item except the rehearsal is read as data, with nothing run:

- **AMD indexes.** `whl-next/onnxruntime-ep-migraphx` lists cp311 to cp314 for each ROCm release.
  `rocm/migraphx/whl-next/migraphx-libs` lists the three library wheels (83 to 89 MB). No page gives
  a sha256. Two separate downloads gave the sha256 values of `ep_lock.yaml`.
- **Metadata.** Each EP wheel: `Requires-Dist: onnxruntime~=1.29.0`. 10.1 and 10.2:
  `migraphx-libs==2.18.0+rocm10.1.0` and `==2.19.0+rocm10.2.0`. 10.0 declares none.
  `onnxruntime_ep_migraphx/__init__.py` returns the library `libmigraphx-ep.so` and the EP name
  `MIGraphXExecutionProvider`. It changes nothing on Linux.
- **Link tables** (`scripts/n6e8_ort_1_30/sonames.py`, pyelftools 0.32). 10.1 and 10.2: NEEDED
  `libamdhip64.so.7`, `libmigraphx_c.so.3`; RUNPATH `$ORIGIN/../migraphx_libs`, `/opt/rocm/lib`.
  10.0: NEEDED also `libonnxruntime.so.1`; RUNPATH only AMD build paths and `/opt/rocm/lib`.
  `migraphx_libs` libraries: RUNPATH `$ORIGIN`, `/opt/rocm/lib`. `onnxruntime` 1.30.0: the pybind
  module needs no `libonnxruntime.so.1`; `capi/libonnxruntime.so.1.30.0` has that SONAME.
- **PyPI.** `onnxruntime` 1.29.0 is the only 1.29 release with a cp313 manylinux wheel (23 136 817
  bytes).
- **Windows ML.** On this PC (no AMD GPU), `EpCatalog().find_all_providers()` gave OpenVINO
  (NotPresent), TRT-RTX (NotReady) and WebGPU (NotPresent): no AMD EP. The docs of Microsoft give
  the ready states, the register call and `AMDGPUExecutionProvider` (Windows ML 2.5.96 or later,
  AMD driver 24.12.1 or later), and no removal API.
- **Catalog route rehearsal** (`scripts/xse7_windows_ml_rehearsal.py`, 2026-11-18, Windows 11, one
  RTX 3070, `onnxruntime-windowsml` 1.30.0.202609102321). The test hook gives the EP row `amdgpu`
  the EP name `NvTensorRTRTXExecutionProvider` in the process of the script. Each step ran in its
  own process with an isolated EP store. The package is
  `Microsoft.WinML.NVIDIA.TRT-RTX.EP.Framework.2` 2.30.51.0, a framework package that no other
  package of the user needs. No other `Microsoft.WinML.*` package was on the PC.
  - Before `ensure_ready()`, the catalog gives an empty version and an empty package family, also
    for the installed package (NotReady). After it, the same provider object still gives empty
    values, and a new enumeration gives both.
  - Package on the PC: `ensure_ready()` needs 0.01 s and downloads nothing. `install()` needs
    1.1 s with the two package lists. `was_present: true`, `packages_installed: []`. The
    registration and the EP device of the RTX 3070 (`0x10de:0x2484`) need 0.6 s. The L3 probe of
    `_verify_child.run()` passes, largest difference 0.0053. `remove_windows_packages()` of the
    frame removes nothing, and the package stays.
  - `remove_package()` removes the package with `Remove-AppxPackage`, with no administrator rights,
    in 2.9 s.
  - Package not on the PC (NotPresent): `install()` needs 7.0 s and 6.3 s (two runs). The installed
    folder holds 286 153 881 bytes. The run does not show whether Windows downloaded the files or
    used a local copy. `was_present: false`, `packages_installed` is the one full name. The
    registration, the device and the L3 probe pass as above. `remove_windows_packages()` gives one
    `pass` row, and the package is gone.
  - At the end, `install()` put the package back: the same full name, 2.30.51.0, NotReady.
- **Set hash.** Unchanged by the AMD packs: `4abfaa76…` of the two Windows rows.

# XSE7 — The AMD EPs in the field test: MIGraphX packs on Linux, the Windows ML catalog on Windows

**Status:** superseded by [6A1Y](6A1Y-field-test-and-amd-eps-consolidation.md), 2026-11-23 (consolidation; PR: pending). It was `accepted` from 2026-11-18 (user).

## Decision

This entry builds item 11 of [ADR-Y14H](Y14H-certify-suite.md) with the field-test state of
[ADR-Z5X7](Z5X7-field-test-state-and-directml.md). `migraphx` is no longer a reserved key.

1. **Keys.** `migraphx` and `amdgpu` are `field-test` EP keys. On Linux, `migraphx` is a pack. On
   Windows, `migraphx` and `amdgpu` come from the Windows ML catalog: the EP row names the platform
   in `windows_ml`, with `ep_name` and the floor `requires: {vendor: amd}`.
2. **Linux packs.** One pack for each ROCm release: `onnxruntime-ep-migraphx` `1.0.0+rocm10.0.0`,
   `+rocm10.1.0` and `+rocm10.2.0` (cp313) with `migraphx-libs` 2.17.0, 2.18.0 and 2.19.0, from the
   two AMD indexes. `pack()` takes the pack whose `requires.rocm` is the release of
   `/opt/rocm/.info/version`. No ROCm is `unsupported` with `rocm-missing`, an other release
   `rocm-version`. The packs install no ROCm. 10.1 and 10.2 preload nothing
   (`preload_dependencies: []`). 10.0 preloads `libmigraphx_c.so.3` and, with
   `preload_ort_core: true`, the core library of the installed `onnxruntime`.
3. **ORT claim.** `vendor_tested: ["1.29", "1.29"]`. On 1.30.0 an opted-in pack is `untested-ort`:
   usable, with a warning.
4. **Windows ML route** (`core/eps/windows_ml.py`). `install(key)` lists the packages of the
   current user (`Get-AppxPackage`), writes a `pending` record with that list (`packages_before`),
   calls `ensure_ready()`, and enumerates again for the version and the family. The record in
   `windows-ml.json` of the EP store holds `was_present` (from the catalog, or a package of the
   family in the list) and `packages_installed`: each package of the family that the call added,
   none with `was_present`. `register(key)` registers `library_path` under `ep_name`, and refuses a
   package that is not on the PC. With no record or a `pending` record, the state is
   `not_installed`. `skellytracker-eps install KEY --field-test` asks one question, then installs.
   No command removes the package.
5. **Removal.** `remove_installed(record)` removes each package of `packages_installed` with
   `Remove-AppxPackage <PackageFullName>` for the current user, with no administrator rights, in one
   try. It refuses a full name that is not of the family that the catalog gives now, else of the
   record. `was_present` removes nothing and gives no row. An `ep_name` that is not a Windows ML EP
   of the catalog gives `record-refused`. A `pending` record removes each package of the family of a
   new enumeration that is not in `packages_before`. No family, or no list, gives `package-unknown`.
   A failure gives `package-not-removed`.
6. **Set hash.** Only `ready` packs are in the set hash. A `field-test` pack enters it at the move to
   `ready`, and the set then needs new evidence. A pack `component` is not in it:
   section 5 of the suite is its evidence.
7. **Hardware classes.** `amd-windows`: `amdgpu`, `migraphx`, `directml`, `cpu`. `amd-linux`:
   `migraphx`, `cpu`. `recommend()` gives `cpu`.
8. **Suite, Windows.** Section 3 installs the package of each AMD EP that the catalog offers, and
   tests the EP on each AMD GPU. The frame calls `remove_installed()` for each record of its EP
   store before it deletes the work folder, also after a crash, a timeout or Ctrl+C. Each removal
   is a check `remove-<package>` of section 3. A failure fails section 3. The consent text names
   the EP, because the catalog gives the package name only after the install.
9. **Suite, Linux, second environment.** When `migraphx` fails on 1.30.0 for a reason other than
   `probe-l3-failed` or its download, the suite builds `.certify-work/ort-1.29.0` with hash checks:
   `uv export --frozen`, the pin `onnxruntime==1.29.0` with the `sha256` of
   `certification.ort_fallback`, and an editable install of the checkout with the hash of
   `build_backend`. The child runs with `SKELLYTRACKER_EP_ORT_FALLBACK=1.29.0`, and only
   then the EP store accepts that version. Sections 3 and 4 record it as `migraphx@ort-1.29.0` with
   `certifies_version_set: false`. Each result records its `ort_version`.

## Reason

- The user decisions of 2026-11-18 for the AMD EPs (Y14H item 11), and the user decision of the
  same day for the removal: remove the package that the suite installed, and never a package that
  was on the PC before.
- `windowsml` has no removal API. The catalog gives no package family before `ensure_ready()`.
- A field-test pack has no maintainer evidence, so it must not make the evidence of the `ready`
  packs stale.

## Consequences

- No result on AMD hardware exists. Tests with fakes prove each AMD code path.
- A deployment that Windows ends after the cleanup stays on the PC.
- The ORT 1.29 core and the second core of the 10.0 pack in one process are not tested.
- `PackStatus.source` has the values `amd` and `windows-ml`.

## Evidence

2026-11-18. [XSE7-amd-eps-evidence.md](../evidence/XSE7-amd-eps-evidence.md) gives each item.

- **AMD packs**, read as data: the AMD index pages, the wheel metadata and the link tables of the
  three ROCm packs, and the `onnxruntime` 1.29 cp313 Linux wheel (its sha256 checked).
- **Windows ML catalog route**, run with the TensorRT RTX package of the catalog on a PC with no
  AMD GPU (`scripts/xse7_windows_ml_rehearsal.py`). A package on the PC stays. A package that the
  install added goes, with no administrator rights.
- **Set hash.** Unchanged by the AMD packs: `4abfaa76…` of the two Windows rows.

## Alternatives rejected

- **A removal by the package family or by a name pattern.** It can remove a package that was on
  the PC before, or a package of an other EP.
- **A test only of a package that Windows already has.** The user decided the install and the
  removal.
- **One key for each delivery route.** The catalog states the route for each platform.

## Open work

See [open-work.md](../open-work.md).

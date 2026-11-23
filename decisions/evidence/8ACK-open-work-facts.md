# Dated facts that open-work.md held before ADR-8ACK

This file holds dated facts that [open-work.md](../open-work.md) held until
[ADR-8ACK](../entries/8ACK-hardware-runs-checklist.md). No entry holds them. Each fact is done. The
open part of its item stays in [open-work.md](../open-work.md) or in
[hardware-runs.md](../hardware-runs.md).

- **Model list of the certify suite** (2026-11-18). `fetch_models` of section 4 of the certify suite
  downloaded the four files of the list `models` into an empty folder: 4 files, sizes and sha256
  right.
- **Section `hardware` of the certify suite** (item 2 of the
  [certification build list](../open-work.md#certification-build-list)). On one Windows system, the
  section `hardware` gave one difference in 17 comparisons: `vram_mib` of the UHD 770 is 128 in
  skellytracker and 2047 in `Win32_VideoController`. The two tools read two fields: skellytracker
  reads the dedicated memory of DXGI, and `AdapterRAM` of this GPU holds 2147479552 bytes. It is not
  a defect of the probe.
- **The build info in the wheel** (item 2 of the certification build list). `flit build` puts
  `skellytracker/_build_info.py` in the wheel and in the sdist, also when git ignores it (one trial
  on Windows, 2026-11-20).
- **Install from the Windows ML catalog** (item 4 of the certification build list). On one Windows
  system, only the async call on a package that was on the system ran: it ended in 0.01 s with no
  progress value. On 2026-11-20 the same system ran `_ensure_ready()` on the OpenVINO EP package of
  the catalog, which was not on the system (the catalog offers no AMD EP there): a cancel after 2 s
  ended in 2.6 s and left no package; the install ended in 10.3 s with the progress values 0, 90 and
  100, so the package now divides the value by 100; `remove_package()` gave `package-not-removed` in
  the process that installed, and the removal passed from a new process
  ([ADR-P47E](../entries/P47E-report-format-1-6-0-and-a-windows-ml-package-in-use.md) item 6).
- **Exporter dependencies** (2026-10-28). Two exporters required Python 3.14 or later, and uv could
  not resolve skellytracker in three of the four exporters.

# BZ7X — ONNX Runtime telemetry: the package sets `ORT_DISABLE_TELEMETRY=1`, and the ONNX stack tool scans for the client

**Status:** absorbed into [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime), 2026-11-19 (user; PR: pending).

## Decision

1. **Switch.** `skellytracker/__init__.py` runs `os.environ.setdefault("ORT_DISABLE_TELEMETRY", "1")`
   first. Each import of a package module runs it before each `import onnxruntime` of the package.
   A value that the host process set stays.
2. **Runtime record.** `RuntimeInfo.ort_disable_telemetry` holds the value or `None`. Section 1 of
   the certify suite records it in `onnx_stack`, with the check `telemetry-switch`: `pass` for `1`
   or `true` (trimmed, any case), else `record-only` with `telemetry-on`.
3. **Folder record.** The certify suite records whether the telemetry folder of ONNX Runtime exists
   before and after the run, as two booleans (`telemetry_database`), with no path. Windows:
   `Microsoft\DeveloperTools\.onnxruntime` under the local app data folder. Linux and macOS:
   `Microsoft/DeveloperTools/.onnxruntime` under `XDG_CACHE_HOME`, else `~/.cache`. The suite
   deletes nothing there.
4. **Static scan.** `tools/onnx_stack.py` scans each native library of a wheel for the client
   (`OneCollector` or `mobile.events.data.microsoft.com`) and the kill-switch string
   (`ORT_DISABLE_TELEMETRY`), as ASCII and UTF-16LE, in any case. An HTTP import is a hint only.
   `scan` and `check --wheel-dir` use it. A wheel that is not in a folder is `not-scanned`.
5. **Reviewed record.** The `telemetry` list of `ep_evidence.yaml` holds one row for each package,
   version and OS, with `client` and `switch_verified` (an evidence reference, or `false` with a
   `reason`). `check` fails for a scanned client with no row and for a row that the scan
   contradicts, and warns for a client with `switch_verified: false`. `solve` and `apply` refuse a
   new package version with no row or with a client and `switch_verified: false`.
6. **Pinned set.** The rows of ONNX Runtime 1.30.0 and `onnxruntime-ep-cuda13` 0.2.0 on Linux have
   the client and `switch_verified: false`. The set stays, and `check` warns.
7. **JPEG decode.** User ruling, 2026-11-19: GPU JPEG decode is for NVIDIA only (`cuda`,
   `trt-rtx`). Each other EP gets frames that the CPU decoded.

## Reason

- User decisions, 2026-11-19: stay on ONNX Runtime 1.30.0; skellytracker must set
  `ORT_DISABLE_TELEMETRY=1`; keep a value that the user set; the ONNX stack tool must know the
  finding and test for it at each bump.
- The client can send data from the host of a user, and an exit hang comes from it.
- The record is in `ep_evidence.yaml`: a change of `ep_catalog.yaml` needs
  `tools/ep_catalog.py --refresh`, and that needs the network.

## Consequences

- A host that imports `onnxruntime` before skellytracker is not covered. It must set the variable.
  `tools/intake_bundle.py` sets the variable before each of its three `import onnxruntime` lines. The
  scripts in `decisions/scripts/` that import `onnxruntime` alone do not set it, and they are frozen.
- Each new package version of the stack needs a reviewed row before a bump.

## Evidence

- **This session**, `tools/onnx_stack.py check --wheel-dir` on the locked wheels (sha256 checked):
  Linux `onnxruntime` 1.30.0 has the client and the string in `libonnxruntime.so.1.30.0` and in the
  pybind module; the Linux `onnxruntime-ep-cuda13` 0.2.0 library has both. No client: TRT-RTX 0.5.0
  (both OS), `onnxruntime-ep-cuda13` 0.2.0 on Windows, and the NVIDIA dependency wheels.
- **Supervisor byte search:** the Windows ML `onnxruntime.dll` 1.30.0.202609102321 has no marker
  and no `WINHTTP.dll` import.
- **A scan of a sub-agent** (scratch, not in git): Windows `onnxruntime-ep-cuda13` 0.3.0 and 0.4.0
  have the client, a `WINHTTP.dll` import and the string. No client in nvImageCodec 0.10.0.9, the
  three MIGraphX packs and the Windows ML TRT-RTX package.
- **Measured by another session** on one Windows host, 2 runs for each cell, state read after a
  10 s sleep, `onnxruntime-ep-cuda13` 0.3.0: with no variable, `webio.dll` loaded, one TCP
  connection to port 443, and the database, the registry key and its `deviceid` appeared. With the
  variable in the child environment, or set in the process before `import onnxruntime`, or after it
  but before the pack registers: none of them. Not tested: set after the registration. The ORT
  1.31.1 Windows core has no client. Exit hang: 9 in 192 runs on ORT 1.31.1 with that pack. Not
  measured: the exit hang with the variable.
- **Not verified:** the switch on Linux (the 1.29.0 release notes, read through a mirror, say it
  works when set before initialization); the Linux folder (strings `XDG_CACHE_HOME` and `/.cache/`
  near the telemetry strings); the macOS wheel (not scanned).

## Alternatives rejected

- **Set the variable in each function that imports `onnxruntime`.** One early place covers each.
- **Overwrite a value that the host set.** The user decided to keep it.
- **A row in `ep_catalog.yaml`.** It changes `catalog_revision`, and the lock refresh needs the network.
- **A failure of `check` for the pinned set.** The user stays on 1.30.0, and the Ubuntu run measures it.
- **A scan in `solve`.** The solve reads only the snapshot and has no wheel files.

## Open work

See [open-work.md](../open-work.md).

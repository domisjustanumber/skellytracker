# P47E — Report format 1.6.0, and the reason code of a Windows ML package in use

**Status:** absorbed into [`certification.py`](../../skellytracker/certification.py), [`REASON_CODES.md`](../../skellytracker/REASON_CODES.md#codes-of-this-package), [`windows_ml.py`](../../skellytracker/core/eps/windows_ml.py), 2026-11-21 (absorb at landing; PR: pending).

## Decision

1. **The format.** `certify()` and the certify suite write reports in the format
   `skellycertify.report/1.6.0`. A report of an older 1.x version stays in the hand-in list.
2. **The media record.** A module report has the top-level list `test_media`. One item gives the
   `name`, the `sha256`, the `bytes` and the `source` of the frames file: `shared` for the test
   media folder, `bundled` for the file of the package. The item is there only when a check that
   reads the frames ended with `pass`, `fail` or `record-only`. This builds item 4 of
   [ADR-Q9R6](Q9R6-certify-rulings-of-2026-11-21.md) with the field names of the format.
3. **The fallback.** A test media folder that does not hold the frames file gives the file of the
   package. A file in the folder with a wrong sha256 is never used, and the run does not fall back:
   the checks get `test-media-missing`.
4. **The shared memory of a GPU.** `GpuInfo.shared_memory_bytes` holds the shared system memory that
   the GPU can use, from DXGI on Windows. It is `None` on Linux and macOS. Each item of `host.gpus`
   of a report gives it. `vram_bytes` stays the dedicated memory.
5. **MediaPipe that is not installed.** The check `mediapipe:smoke` stays `not-run` with
   `models-missing`. The `component` summary item `MediaPipe` then has the result `skipped` with the
   reason `not-installed`.
6. **A Windows ML package in use.** When Windows refuses a removal with HRESULT 0x80073D02, the row
   of the package gets the reason code `package-in-use`. The record stays. The call tries one time.
   The CLI tells the person to close the application and to run the removal again.

## Reason

- The owner of the format released 1.6.0 with the fields of items 2, 4 and 5 (skellycertify
  ADR-9FHP).
- Item 4: an integrated GPU has little dedicated memory. On one Windows 11 system, an Intel UHD 770
  gave `vram_bytes` of 134217728. The shared memory is the larger part of what it can use.
- Item 6, measured on the same system on 2026-11-21 with the OpenVINO EP package of the Windows ML
  catalog, version 2.1080.97.0, in seven trials:
  - A removal failed with 0x80073D02 in each process that called `ensure_ready` on the package: the
    process of the install, the same process after it closed the catalog, and a process that only
    registered the package and ran sessions.
  - A removal passed from each process that did not call `ensure_ready`, also after an enumeration
    of the catalog.
  - No library of the package was loaded in the process of the install.
- The user agreed to item 6 in this session.

## Consequences

- `tools/certify_platform.py` needs no change for item 6: it installs in a child process and
  removes after that process ends.
- An application that calls `eps.install` and then `eps.remove` in one process gets
  `package-in-use`. It must show its own text for that code.

## Open work

- A `pending` record of an install that did not end gives `package-unknown` in a new process: the
  catalog gives no package family before `ensure_ready`. The package then stays on the system. The
  fix is not built. Evidence gives the family of two packages only, and neither is an EP of the EP
  catalog ([open work](../open-work.md#certification-build-list)).
- The read of the shared memory from DXGI ran in no test on real hardware.

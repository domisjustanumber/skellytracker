# Evidence for ZGF5: the certify measurements of 2026-11-18 and 2026-11-19

This file is the evidence of
[ADR-ZGF5](../entries/ZGF5-certify-measurements-of-2026-11-18.md). The paths are relative to
`decisions/`.

## Files

| File | What it is |
|---|---|
| [`evidence/ZGF5/recheck-trt-rtx.json`](ZGF5/recheck-trt-rtx.json), [`evidence/ZGF5/recheck-cuda.json`](ZGF5/recheck-cuda.json) | The two reports of `skellytracker-eps certify KEY --wide` (2026-11-18T21:34Z) behind the two rows of `skellytracker/core/eps/ep_evidence.yaml`. Copies with LF line ends. |
| [`evidence/ZGF5/fail-2px-trt-rtx.json`](ZGF5/fail-2px-trt-rtx.json), [`evidence/ZGF5/fail-2px-cuda.json`](ZGF5/fail-2px-cuda.json) | The two reports (2026-11-18T19:58Z) in which `trt-rtx` and `cuda` failed with `keypoints-differ` against the old limit `keypoint_px_max: 2.0`. Copies with LF line ends, from the `reports` folder of the EP store. |
| [`evidence/ZGF5/rehearsal-certify-report.md`](ZGF5/rehearsal-certify-report.md) | One suite report of a clean clone. It is a **rehearsal** record, not evidence for a platform. See below. |
| `scripts/zgf5_session_measurements/dml_measure.py` | The DirectML device-memory measurement of [ADR-Z5X7](../entries/Z5X7-field-test-state-and-directml.md) ("A scratch run (not in git)"). |
| `scripts/zgf5_session_measurements/snap.py` | The listing of the user data and cache folders of skellytracker (name, size, integer mtime) before and after a suite run: the leak check of ADR-Z5X7. |
| [`evidence/ZGF5/rehearsal-2026-11-19/`](ZGF5/rehearsal-2026-11-19/) | The JSON outputs of the Windows ML rehearsal on 2026-11-19 (item 5 of the entry). Folder `A`: package on the PC before. Folder `B`: package removed first. Files `state`, `run`, `remove` and `cleanup`. The `cleanup.json` files hold the `record-refused` rows. |
| `scripts/zgf5_session_measurements/hooked_cleanup.py` | A wrapper that calls `hook()` of the rehearsal script, then its `cleanup()`. |

The committed `dml_measure.py` has one lint edit: a `# noqa: B023` comment on the line of the
`lambda`. Its docstring still says "Not in git". It is otherwise the copy that ran. `snap.py` has no
edit.

## The rehearsal report

The tag `certify-v1` existed only in a throw-away clone, at commit 2f5efac2. No certification tag
exists in this repository or on a remote. Thus the line "Valid as evidence" of the report is not
true for a platform. The report records that the suite ran from a clean clone with the expected
versions. It is not evidence for an EP, a GPU or an OS. The first lines of the committed file are a
note that says this. The rest of the file is the report. The sha256 of the report as written is
`fe84570940aa09a2f7853b87334dde863b86b6bad9242d6a36dd67da2158e805`.

The clean clone ran the suite two times: 2 min 40 s and 2 min 17 s. Sections 1, 3 and 4 passed,
section 2 was `record-only`, and sections 5 to 7 were `not-run`. The listing of the shared EP store
(555 files, with names, sizes and last-write times) was the same before, after run 1 and after
run 2.

## Ranges over all saved suite reports

10 suite reports of `tools/certify_platform.py` (suite version 1) were saved, from 2026-11-18T22:07Z
to 2026-11-19T13:24Z. All are from one Windows host: Windows 11 build 26300, one RTX 3070 (driver
610.88) and one Intel UHD 770, `onnxruntime-windowsml` 1.30.0.202609102321, `trt-rtx-cu13` 0.5.0,
`cuda-cu13` 0.2.0. 7 reports hold section 4. 5 of them also hold DirectML. Each value is from the
JSON block of the report. Section 4 makes 10 warm-up calls and 100 timed calls for each camera count.

| EP | Box IoU (min) | Keypoint box fraction, max | Keypoint box fraction, median | Keypoint px, max |
|---|---|---|---|---|
| `trt-rtx` (7) | 0.9985 to 0.9990 | 0.0041 to 0.0047 | 0.00029 to 0.00037 | 4.49 to 5.17 |
| `cuda` (7) | 0.9890 in each | 0.0056 in each | 0.0015 in each | 6.14 in each |
| `directml`, RTX 3070 (5) | 0.9882 to 0.9885 | 0.0056 to 0.0071 | 0.0015 to 0.0015 | 6.10 to 7.72 |
| `directml`, UHD 770 (5) | 0.9887 in each | 0.0057 in each | 0.0015 in each | 6.18 in each |

| EP | Median, 1 camera (ms) | Median, 3 cameras (ms) | Median, 6 cameras (ms) |
|---|---|---|---|
| CPU EP (7) | 18.0 to 45.9 | not run | not run |
| `trt-rtx` (7) | 3.57 to 6.72 | 6.91 to 13.67 | 12.47 to 15.37 |
| `cuda` (7) | 6.95 to 8.78 | 10.45 to 11.68 | 18.22 to 23.00 |
| `directml`, RTX 3070 (5) | 4.02 to 5.43 | 7.45 to 8.50 | 15.05 to 16.22 |
| `directml`, UHD 770 (5) | 35.7 to 87.8 | 89.8 to 91.9 | 173.4 to 179.6 |

In some runs, another session used the same GPU. The timings are thus not a benchmark. They show
the spread on one host.

## The network install

The one run of section 3 with a download from PyPI installed 110,875,664 + 1,009,139,129 =
1,120,014,793 bytes (1.12 GB, 1.04 GiB) in 40.2 s.

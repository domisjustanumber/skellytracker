# ZGF5 — The certify measurements of 2026-11-18 and 2026-11-19: reports, spread and corrections

**Status:** evidence, 2026-11-19 (record of the measurements of the session of 2026-11-18 and
2026-11-19; the user approved the record).

## Decision

This entry records measurements. The entries
[ADR-MF2R](MF2R-ep-store-install-and-certification.md),
[ADR-Z5X7](Z5X7-field-test-state-and-directml.md),
[ADR-XSE7](XSE7-amd-eps-in-the-field-test.md) and [ADR-Y14H](Y14H-certify-suite.md) are pushed.
Thus this entry gives the facts that they do not give, and the corrections. The evidence file
[ZGF5-session-measurements.md](../evidence/ZGF5-session-measurements.md) gives each file and the
full tables.

1. **Source reports.** The two rows of `skellytracker/core/eps/ep_evidence.yaml` come from the two
   reports in `evidence/ZGF5/recheck-*.json`.
2. **The 2 px limit failed.** With the fixed limit `keypoint_px_max: 2.0`, both known-good NVIDIA
   EPs failed with `keypoints-differ` on one RTX 3070: `trt-rtx` 5.17 px, `cuda` 6.14 px, on a box
   of 519 x 958 px (`evidence/ZGF5/fail-2px-*.json`). This is the reason for the limit
   `keypoint_box_fraction_max: 0.01`, a part of the diagonal of the person box: the two EPs gave
   0.0047 and 0.0056.
3. **Spread over all saved suite reports.** 10 reports, 7 with section 4, 5 with DirectML. All are
   from one Windows host with one RTX 3070 and one Intel UHD 770. The ranges:
   - box IoU: `trt-rtx` 0.9985 to 0.9990; `cuda` 0.9890; DirectML RTX 3070 0.9882 to 0.9885; DirectML
     UHD 770 0.9887;
   - keypoint box fraction, max: `trt-rtx` 0.0041 to 0.0047; `cuda` 0.0056; DirectML RTX 3070 0.0056
     to 0.0071; DirectML UHD 770 0.0057;
   - keypoint box fraction, median: `trt-rtx` 0.00029 to 0.00037; each other EP 0.0015;
   - median time for 1, 3 and 6 cameras (ms): `trt-rtx` 3.57-6.72, 6.91-13.67, 12.47-15.37; `cuda`
     6.95-8.78, 10.45-11.68, 18.22-23.00; DirectML RTX 3070 4.02-5.43, 7.45-8.50, 15.05-16.22;
     DirectML UHD 770 35.7-87.8, 89.8-91.9, 173.4-179.6; CPU EP, 1 camera, 18.0-45.9.

   A value with one number was the same in each report. In some runs, another session used the same
   GPU. The timings are thus not a benchmark. The values of ADR-MF2R and ADR-Z5X7 are one run each in
   these ranges.
4. **Clean-clone run.** `evidence/ZGF5/rehearsal-certify-report.md` is a **rehearsal** record. The
   tag `certify-v1` existed only in a throw-away clone at commit 2f5efac2. No certification tag
   exists. The report is not evidence for a platform.
5. **Windows ML rehearsal of ADR-XSE7.** The first run was on the code of commit f8df11df. Commit
   1bd2417f then rewrote the removal: `remove_installed()` of `core/eps/windows_ml.py`. A second run
   on 2026-11-19 used the code of commit 3798bcbc: one Windows 11 host, one RTX 3070, the TensorRT
   RTX package of the catalog (version 2.30.51.0) and isolated scratch stores.
   - Package on the PC before: `install()` recorded `was_present: true` and no installed package
     (0.83 s). The cleanup gave no row. The package stayed.
   - Package removed first: `was_present: false`, the package in `packages_installed`. The install
     took 6.1 s (8.9 s in an earlier run of the same day), the registration about 0.5 s. The EP
     device of the RTX 3070 was found. The L3 probe was ok (max abs diff 0.00525). The cleanup
     (`remove_windows_packages` of `tools/certify_platform.py`, then `remove_installed()`) gave one
     `pass` row, and the package was gone. A later `install()` put it back.
   - Finding: the `cleanup` step of the script gives `fail` with `record-refused` in both cases.
     `remove_installed()` refuses a record whose `ep_name` is not a Windows ML EP of the EP catalog,
     and the script applies its in-memory catalog hook in the `run` step only. The refusal is the
     designed behaviour. To run the cleanup now, use
     `scripts/zgf5_session_measurements/hooked_cleanup.py`. It takes the path of the rehearsal
     script as its argument and calls the hook before the `cleanup` step. The `pass` rows come from
     that wrapper. The terminal output of the hooked cleanup is not saved. The saved files are the
     state, run, remove and cleanup outputs (`evidence/ZGF5/rehearsal-2026-11-19/`).
   - Not shown: an AMD package, a crash during the install, and whether Windows downloads the
     package again after a removal (6 to 9 s can be a download or a local copy).
6. **Download size.** The network install of section 3 was 1,120,014,793 bytes (1.12 GB) in 40.2 s.
   The comment of section 3 in `SECTIONS` of `tools/certify_platform.py` said 1.07 GB. This commit
   corrects that comment.

## Reason

- An audit of the session found that the source reports, the 2 px failure, the spread between runs
  and the clean-clone run were only in scratch files or in chat, and that the rehearsal of
  ADR-XSE7 is stale against the code.
- The Rules do not allow a new fact in the body of a pushed entry.

## Evidence

- Suite: `tools/certify_platform.py`, suite version 1, commits 1c5e0559 to 2f5efac2 as section 1 of
  each report records them. `skellytracker-eps certify KEY --wide` for the four EP reports.
- Host: Windows 11 build 26300, RTX 3070 (driver 610.88), Intel UHD 770, `onnxruntime-windowsml`
  1.30.0.202609102321, `windowsml` 2.6.74rc0, `trt-rtx-cu13` 0.5.0, `cuda-cu13` 0.2.0.
- The ranges came from the JSON block of each report, with a throw-away script that is not in git.
- Scripts: `scripts/zgf5_session_measurements/dml_measure.py` (the DirectML memory of ADR-Z5X7;
  the committed copy has one lint edit) and `scripts/zgf5_session_measurements/snap.py` (the leak
  check of ADR-Z5X7), and `scripts/zgf5_session_measurements/hooked_cleanup.py` (the cleanup of the
  rehearsal with the catalog hook; item 5).

## Open work

See [open-work.md](../open-work.md).

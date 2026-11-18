# MF2R — The EP catalog data, the EP store, the pack install and the EP certification

**Status:** accepted, 2026-11-18 (user).

## Decision

This entry supersedes [ADR-246B](246B-ep-catalog-store-and-install.md) in full. It keeps the item
numbers of 246B. Item 9 replaces 246B item 9. Items 12 to 18 are new. 246B keeps the reasons for
the items that stay.

1. **Catalog files.** `core/eps/ep_catalog.yaml` and `ep_lock.yaml` are package data, as 246B item 1
   states. The runtime never downloads a catalog.
2. **Allow-lists.** The EP options of 246B item 2 stay. Each other name is refused.
3. **Performance defaults.** The defaults of 246B item 3 stay.
4. **OpenVINO test pack.** It is for CI only. It is never offered to a user.
5. **Untested ORT.** A pack outside its ORT range is `untested-ort`. It stays usable, with one
   warning line for each process.
6. **Store.** The store of 246B item 6 stays. It records no EP choice. `certify.json` holds only the answers and results of item 14.
7. **Download.** The engine of 246B item 7 stays: `urllib`, `https` only, the sha256 of the lock as the gate, and `install --from-dir`.
8. **No mirror.** The Azure feed is the only source of the `cuda` wheel.
9. **User acceptance.** A download starts only after the user accepts it: a CLI `install`, the EP
   page of the freemocap installer or update installer, an action in the app settings, or a yes to a
   prompt of the app. The app can prompt to download an EP pack or a model, and to certify an EP. After the user accepts, the download can run in the background and must
   not block the UI.
10. **Installer flows.** The flows of 246B item 10 stay.
11. **Smart App Control.** Before stage 1.11, verify the install and a session once with Smart App Control on.
12. **Evidence file.** `core/eps/ep_evidence.yaml` is package data. A person writes a row after a review. A row gives `ep`, `os`, `gpu` (the PCI vendor id and
    device id), `set` (the set hash), `source` (`maintainer` or `field`), `result`, and
    `catalog_package` for an EP of the Windows ML catalog. A row can also hold the versions `pack`,
    `ort`, `windowsml`, `driver`, `os_build` and `os_label` as a record only. The key of a row stays
    `ep`, `os`, `gpu` and `set`.
13. **Certified state.** `PackStatus.certified` is true when a row records a pass of the EP on this
    GPU model on this OS. `EpStatus.certify_offers` has one `CertifyOffer` for each usable plugin EP
    that is not certified.
14. **Prompt.** The app prompts at its start, one time for each pair of EP pack version and GPU
    model. The answers are: certify now; later (ask again at the next start); do not ask again (the
    offer stays). No prompt appears in a non-interactive run. skellytracker stores the answer and owns the logic: `certify()` and
    `dismiss_certification()`. freemocap shows the dialog.
15. **`certify(key)`.** It always runs the probe: `verify()` at level L3. A probe pass makes the EP
    usable on that host before a review. When the user agrees, it also runs the pipeline `yolox-rtmw-wholebody` on one public test image, on the EP
    and on the CPU EP of the same host. The image is in a release of `freemocap/skellysamples`. The result is `pass`, `fail` or `not-run`. A setup problem, for example an
    absent pack or model file, is `not-run`, and the prompt stays.
16. **Pass rule.** The wider run passes when the two results have the same count of persons, each
    box IoU is 0.9 or more, and each keypoint with a score of 0.4 or more in the two results is
    within 1 % of the diagonal of the person box. A value that is not finite,
    a point that only the CPU EP finds and a node on the CPU EP also fail it. The run tests the
    precision that the pipeline selects on the EP. One RTX 3070 gave 0.47 % and 0.56 %.
17. **Report.** The report is a JSON file in the folder `reports` of the EP store. `certify` shows
    the whole report and, for a person, opens the folder. A failure is a fixed reason code, never an error text. The report takes its
    versions and OS facts from `probe_runtime()` and `probe_host()` of `core/system`. It holds the
    versions, the set hash, the OS name, release, version, build and label, the GPU
    model with its PCI ids and driver version, and the results. It holds no hostname, no path, no serial number, no bus address
    and no user id. Nothing leaves the host.
18. **Evidence for a version bump** (`tools/onnx_stack.py check`). A user pack for an NVIDIA GPU
    needs a `maintainer` row with a pass for the current set hash on Windows and on Linux. Evidence
    for an AMD GPU comes from reviewed reports of users: one passing report on an OS is
    enough. The version of `catalog_package` is not in the set hash. A vendor range that excludes
    the ONNX Runtime version blocks a bump. An `exception` with an `entry` lifts the block only for
    the ONNX Runtime version that it names. A newer pack version is a candidate only when the pack
    row has a claim for that exact version in `newer_versions`. The solve takes the newest ONNX
    Runtime release first, then the newest version of each pack. `apply` moves the chosen claim into
    the pack row and deletes the claims that it passed.

## Reason

- The maintainer has no AMD hardware. Users must test an EP on their GPU: "The app must prompt."
- A report with no private data can go to a public issue later.

## Evidence

Code facts: `core/eps/certification.py`; `core/eps/evidence.py`; the `certification` block of
`ep_catalog.yaml`; `certify_prompt()` in `core/eps/cli.py`; `tools/onnx_stack.py`.

## Alternatives rejected

- **skellypings**, the usage ping of freemocap. Nobody can review its data.
- **A GitHub issue with a login.** The user wants no login.
- **Test images in this repository.** [ADR-9VN4](9VN4-no-camera-recordings-or-frames-in-git.md)
  refuses camera frames.
- **Expected values in the repository.** The CPU EP of the same host is the reference.

## Open work

See [open-work.md](../open-work.md).

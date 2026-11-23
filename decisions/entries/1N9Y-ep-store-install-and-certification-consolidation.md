# 1N9Y — Consolidation of the EP catalog, store, install and certification entry

**Status:** accepted, 2026-11-23 (consolidation; PR: pending).

## Decision

This entry supersedes [ADR-MF2R](MF2R-ep-store-install-and-certification.md) in full. It changes
no decision, and keeps the item numbers of MF2R. Each item links the documents that state its kept
rules. Its text gives each kept rule that no document states, also the rules of
[ADR-246B](246B-ep-catalog-store-and-install.md) that MF2R kept by reference.

1. **Catalog files.** [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime),
   [`catalog.py`](../../skellytracker/core/eps/catalog.py) and
   [`ep_catalog.py`](../../tools/ep_catalog.py). Text: the runtime never downloads a catalog.
2. **Allow-lists.** [`session.py`](../../skellytracker/core/eps/session.py) and
   [`ep_catalog.py`](../../tools/ep_catalog.py). Text: `cuda` allows `prefer_nhwc` (`0`|`1`),
   `use_tf32` (`0`|`1`) and `arena.max_mem` (positive integer bytes). `trt-rtx` allows
   `enable_cuda_graph` (`0`|`1`; default `1`). `coreml` allows `MLComputeUnits` (`ALL`|`CPUAndGPU`|
   `CPUAndNeuralEngine`|`CPUOnly`). `cpu` allows no option. Each other name is refused, also
   `device_id` and each `session.*` setter key.
3. **Performance defaults.** Text: `recommend("performance")` gives the EP defaults, plus
   `prefer_nhwc=1` for `cuda` with an fp16 artifact only, and the `nv_runtime_cache_path` of the
   catalog for `trt-rtx`. A default set holds no EPContext entry and no `enable_gemm_auto_tune`.
4. **OpenVINO test pack.** [`ep_catalog.py`](../../tools/ep_catalog.py). Text: the `openvino`
   pack is for CI only. It is never offered, selected or installed for a user. The key stays
   reserved.
5. **Untested ORT.** Text: a pack outside its ORT range is `untested-ort`. It stays usable, with
   one warning line for each process.
6. **Store.** [`store.py`](../../skellytracker/core/eps/store.py). Text: the store does not follow
   a per-call `user_root`. The store records no EP choice. There is no `decisions.json`.
7. **Download.** [`cli.py`](../../skellytracker/core/eps/cli.py). Text: the engine uses `urllib`,
   over `https` only. The sha256 of the lock is the gate: a mismatch
   deletes the file. A download resumes with byte ranges. If the server does not resume, it starts
   again from byte 0. TLS uses `SSL_CERT_FILE` or `SSL_CERT_DIR`, else the system trust store, with
   no `certifi`. The proxy is the system proxy setting of `urllib`, with no PAC file.
   `install --from-dir` installs from local wheels with no network.
8. **No mirror.** Text: the Azure feed is the only source of the `cuda` wheel.
9. **User acceptance.** [`installer.py`](../../skellytracker/core/eps/installer.py). Text: the
   user accepts a download in a CLI `install`, on the EP page of the freemocap installer or update
   installer, with an action in the app settings, or with a yes to a prompt of the app. The app can
   prompt for the download of an EP pack or a model, and for a certify run. An accepted download can run in
   the background, and must not block the UI.
10. **Installer flows.** [`installer.py`](../../skellytracker/core/eps/installer.py)
    and [`cli.py`](../../skellytracker/core/eps/cli.py). Text: the Windows installer is per user,
    with no elevation. Its EP page offers Recommended, Advanced (with "Install from folder") and
    CPU only, and downloads the chosen packs during the installation. A cancel or a failure gives a
    CPU-only installation. The update installer shows the same page and downloads the changed pack
    versions. macOS installs no pack. Linux uses the app action or the CLI.
11. **Smart App Control.** Text: before stage 1.11, verify the install and a session once with
    Smart App Control on.
12. **Evidence file.** [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime) and
    [`onnx_stack.py`](../../tools/onnx_stack.py). Text: a row can also hold `pack`, `ort`,
    `windowsml`, `driver`, `os_build` and `os_label` as a record only. The key of a row is `ep`,
    `os`, `gpu` and `set`.
13. **Certified state.** [`core/eps/__init__.py`](../../skellytracker/core/eps/__init__.py).
14. **Prompt.** Text: the EP prompt has three answers: certify now, later, and do not ask again.
    freemocap shows the dialog and stores the answer ([ADR-4JAW](4JAW-rulings-of-2026-11-23-on-sessions-the-certify-prompt-and-linux.md) item 2). No prompt appears in a
    non-interactive run.
16. **Pass rule.** [Codes of this package](../../skellytracker/REASON_CODES.md#codes-of-this-package).
    Text: the thresholds are `box_iou_min` 0.9, `keypoint_box_fraction_max` 0.01 of the diagonal of
    the person box, and `score_min` 0.4. The run tests the precision that the pipeline selects on
    the EP.
17. **Report.** [ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime) and
    [Layout](../../skellytracker/AGENTS.md#layout). Text: the report takes its versions and OS facts
    from `probe_runtime()` and `probe_host()` of `core/system`.
18. **Evidence for a version bump.** [`onnx_stack.py`](../../tools/onnx_stack.py). Text: evidence
    for an AMD GPU comes from reviewed reports of users. One passing report on an OS is enough. The
    version of `catalog_package` is not in the set hash.

### Rules that do not stay

- [ADR-X7WD](X7WD-certify-levels-rulings-of-2026-11-20.md) item 9: `certify.json` (item 6),
  `certify_offers` (item 13), and `certify()` with `dismiss_certification()` (item 14).
- Item 14, the time: [ADR-P0JZ](P0JZ-certify-contract-in-each-package.md) item 5. "Later":
  [ADR-21BK](21BK-quick-check-local-pass-and-hand-in.md) item 2.
- Item 15: ADR-21BK items 1 and 2,
  [ADR-R0EB](R0EB-quick-check-runs-a-video-and-a-live-session.md) and ADR-X7WD items 6, 7 and 9.
- Item 16, the later frames: ADR-R0EB item 3.
- Item 17, the JSON form, the open folder and "Nothing leaves the host": ADR-X7WD items 9 and 12,
  ADR-21BK item 5.

## Reason

- Later entries replaced parts of MF2R.

## Open work

See [open-work.md](../open-work.md).

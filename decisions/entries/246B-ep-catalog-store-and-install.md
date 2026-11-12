# 246B — The EP catalog data, the EP store and the pack install

**Status:** accepted, 2026-11-12 (user).

## Decision

1. **Catalog files.** `core/eps/ep_catalog.yaml` (written by hand) and `core/eps/ep_lock.yaml`
   (written only by `tools/ep_catalog.py --refresh`) are package data. The lock holds the URL, the
   sha256 and the sizes of each wheel of each pack. The runtime never downloads a catalog.
   `ort_core.version` must equal the `onnxruntime` pin
   ([ADR-M2C6](M2C6-exact-pins-and-one-python-patch-release.md) item 2). `tools/ep_catalog.py --check`
   fails on drift.
2. **Allow-lists** (the check of [ADR-9NW0](9NW0-ep-keys-options-and-failures.md) item 2):
   - `cuda`: `prefer_nhwc` (`0`|`1`), `use_tf32` (`0`|`1`), `arena.max_mem` (positive integer bytes).
   - `trt-rtx`: `enable_cuda_graph` (`0`|`1`; default `1`).
   - `coreml`: `MLComputeUnits` (`ALL`|`CPUAndGPU`|`CPUAndNeuralEngine`|`CPUOnly`).
   - `cpu`: none.
   - Each other name is refused, also `device_id` and each `session.*` setter key. The device comes
     from the device map ([ADR-P1F3](P1F3-hardware-probe-devices-and-multi-gpu.md)).
3. **Performance defaults.** `recommend("performance")` gives: `cuda` the EP defaults plus
   `prefer_nhwc=1` for an fp16 artifact only; `trt-rtx` the EP defaults plus an
   `nv_runtime_cache_path` that the catalog sets; `coreml` the EP defaults. The default sets hold no
   EPContext entry and no `enable_gemm_auto_tune`.
4. **OpenVINO test pack.** The catalog keeps one `openvino` pack row as a CI-only test vehicle. It is
   never offered, selected or installed for a user. The key stays reserved (ADR-9NW0 item 1).
5. **Untested ORT.** A pack whose ORT range does not hold the core is `untested-ort`. It stays usable,
   with one warning line for each process. `trt-rtx` 0.5.0 on ORT 1.31 is accepted this way. Move to
   a tested pack when NVIDIA ships one.
6. **Store.** The default store is `platformdirs.user_data_dir("skellytracker", appauthor=False)` +
   `/eps`, beside `/models` ([ADR-0XW9](0XW9-entry-points-layout-guard-test-and-session-code.md) item 6).
   `SKELLYTRACKER_EP_STORE` overrides it for the whole process. The store does not follow a per-call
   `user_root`. Checkouts and freemocap share one store. A pack folder
   `<pack_id>/<pack_ver>/` is immutable. One ref file for each consumer (`refs/<consumer_id>.json`)
   is the input of `gc`. There is no `decisions.json` and no recorded EP decision.
7. **Download.** The engine uses `urllib` of the standard library, over `https` only.
   - The sha256 of the lock is the gate. A mismatch deletes the file.
   - Resume with byte ranges. If the server does not resume, restart from byte 0.
   - TLS uses `SSL_CERT_FILE` or `SSL_CERT_DIR`, else the system trust store. No `certifi`.
   - The proxy is the system proxy setting that `urllib` reads. No PAC file.
   - `install --from-dir` ("Install from folder") installs from local wheels with no network. It is
     the fallback for a blocked proxy or feed.
8. **No mirror.** The Azure feed is the only source of the `cuda` plugin wheel.
9. **User action.** A download starts only after an explicit user action: a CLI `install`, the EP
   page of the freemocap installer or update installer, or the "GPU acceleration" action that the
   user starts in the app settings. No background download. The app never prompts.
10. **Installer flows** (freemocap work; skellytracker gives the CLI, `status --format ini` and
    `install --progress jsonl --cancel-file`):
    - The Windows installer is per user and needs no elevation.
    - Its EP page offers Recommended, Advanced and CPU only. It downloads the chosen packs during
      the installation, not at first run.
    - A cancel or a failure finishes the installation CPU only.
    - Advanced has "Install from folder".
    - The update installer shows the same page and downloads the changed pack versions.
    - macOS installs no pack. Linux uses the app action or the CLI.
    - A pack shows a plain licence link. There is no accept step.
11. **Smart App Control.** No design change. Before stage 1.11 (Pre-release), verify the install and
    a session once on a Windows host with Smart App Control on.

## Reason

- The user decided these items on 2026-11-12, in a grilling session of the hardware and EP track.
- A catalog in the package with sha256 values gives one chain of trust: signed installer or locked
  wheel, then catalog, then pack.
- The plugins do not check their options (ADR-9NW0, Reason). Each refused name gives wrong
  outputs, a cost or no effect, or needs I/O binding, which the v2 runtime does not have
  ([ADR-NZK1](NZK1-ep-options-evidence.md)).
- Registration is per process, so a per-call store root cannot work.
- A frozen app bundles its own OpenSSL, whose default CA paths often do not exist.
- The user, on the feed: no mirror, "risk accepted".
- The app never prompts, so it has no earlier answer to record. The ref files stay for `gc`.

## Evidence

[ADR-NZK1](NZK1-ep-options-evidence.md): the option checks of each plugin, the `prefer_nhwc` gain on
fp16 only, the cache build times, `enable_cuda_graph` off 4% to 21% slower, and
`enable_gemm_auto_tune` with no gain.

## Alternatives rejected

- **A mirror of the `cuda` wheel.** The user accepted the risk of a feed outage. "Install from
  folder" covers an outage.
- **`certifi`.** It does not hold the roots of the system store.
- **PAC support.** It needs a script engine.
- **A download at first run, or a prompt in the app.** The user wants the choice in the installer.
- **`decisions.json`.** Nothing reads it when the app never prompts.
- **OpenVINO as a user EP.** Deferred (ADR-9NW0 item 1).
- **A bundled uv for the download.** uv stops with "No interpreter found" when it finds no Python.

## Open work

See [open-work.md](../open-work.md).

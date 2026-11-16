# J0D2 — Downloaded `url` artifacts go to the platform cache folder

**Status:** absorbed into [`sizes-and-artifacts.md#implementer-guidance`](../../specs/model-sidecar/common/sizes-and-artifacts.md#implementer-guidance), [`artifacts.py`](../../skellytracker/core/model_spec/artifacts.py), 2026-11-16 (user, question D1 of 2026-11-16; PR: pending).

## Decision

1. **The folder.** The host downloads the ONNX file of a `url` artifact to the download folder:
   `platformdirs.user_cache_dir("skellytracker", appauthor=False)` + `/models`.
2. **The file.** The file of one artifact is `<key>/<version>/<filename>` in the download folder
   (`download_path` of `skellytracker/core/model_spec/artifacts.py`).
3. **Not a root.** The download folder is not a sidecar root. The catalog does not scan it for
   sidecars.

This entry replaces one rule of the "Roots" heading of [ADR-0016](0016-sidecar-catalogs.md): "The
ONNX download cache for `url` artifacts stays at `~/.cache/skellytracker/models`". Item 3 keeps the
second sentence of that rule. The other rules of ADR-0016 do not change.

## Reason

- Stage 1.7 of the
  [implementation plan](../../specs/sidecar-implementation-plan.md#17-standalone-generic-detectors-was-n4)
  built the download with the platform cache folder. Only the plan stated the folder. The user
  confirmed it on 2026-11-16 (question D1).
- `~/.cache` is the cache folder of Linux only. On Windows and macOS, a cache in the home folder is
  not in the place that the system cleans and that a user expects.
- The EP pack cache and the hash cache of the package are in the same platform cache folder
  (`skellytracker/core/eps/store.py`, `default_hash_cache_path`). One folder holds each cache of
  skellytracker.
- The path has the key and the version. Two models with the same file name do not collide.

## Consequences

- A file that an old release downloaded to `~/.cache/skellytracker/models` is not found on Windows
  and macOS. The host downloads it again. On Linux, the folder is the same, but the path below it
  now has the key and the version.
- The old session code in `skellytracker/core/sessions/model_registry.py` still uses
  `~/.cache/skellytracker/models` until phase 2 deletes it.

## Alternatives rejected

- Keep `~/.cache/skellytracker/models` on each platform. It needs code that goes around
  `platformdirs`, and it puts a cache in the home folder of a Windows user.

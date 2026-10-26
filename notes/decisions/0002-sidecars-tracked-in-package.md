# 0002 — Sidecars are tracked in the package tree; ONNX files are not

**Status:** absorbed into [`common/sizes-and-artifacts.md#implementer-guidance`](../../specs/model-sidecar/common/sizes-and-artifacts.md#implementer-guidance), 2026-10-25 (user; the absorption review).

## Decision

- Git tracks each sidecar YAML file inside the package tree. The paths follow
  [Storage layout](../../specs/model-sidecar/format/file-layout.md#storage-layout) in the spec:
  - `skellytracker/core/detectors/object_detectors/{family}/{model_id}.yaml`
  - `skellytracker/core/detectors/keypoint_detectors/{family}/{part}/{model_id}.yaml`
- Git does not track ONNX files. `OnnxSession.create()` fetches each ONNX file at run time. It calls
  `resolve_model_path()` in `skellytracker/core/sessions/model_registry.py` with the `ModelSource` of the
  model spec. Sidecars do not get a new downloader. The existing download and zip-extraction code is
  reused.
- `resolve_model_path()` takes two optional arguments. Both default to `None`, so existing callers do not
  change:
  - `expected_filename`: the cache file gets the `filename` of the sidecar artifact. The tail of the URL
    does not set the name.
  - `expected_sha256`: the function checks the downloaded bytes against `url_sha256`. On a mismatch, it
    deletes the temporary file, writes nothing to the cache and raises `ModelIntegrityError`.
- A downloaded ONNX file stays in the flat cache `~/.cache/skellytracker/models` (`DEFAULT_CACHE_DIR`).
  The first design saved the file in the directory of its sidecar, in place of the flat cache. That part
  was **not built**. This entry records what was built.
- Decision [0016](0016-sidecar-catalogs.md) keeps this cache location for artifacts that have a `url`.

## Reason

- The tracked sidecar paths follow the storage layout of the spec.
- Each detector module loads its sidecar when Python imports the module (`_SIDECAR = load_sidecar(...)`).
  The sidecar must ship with the package.
- Each artifact in a tracked sidecar has a `url` and a `url_sha256`. The hash proves that a downloaded file
  is the file that the sidecar declares. Git does not need to hold the file.
- `model_registry.py` already downloads files, caches them and extracts zip archives. Two optional
  arguments are enough. A second download path is not needed.
- The sidecar `filename` sets the cache file name. It replaces the name that came from the URL tail. The
  user decided this during the YOLOX migration (see
  [M3 — YOLOX migration](../../specs/sidecar-implementation-plan.md#m3--yolox-migration)).
- No reason was recorded for leaving out the cache in the sidecar directory.

## Evidence

Checked in the repository on 2026-10-22.

- Tracked sidecars:
  - `object_detectors/yolox/yolox.yaml`
  - `keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml`
  - `keypoint_detectors/rtmpose/body/rtmpose-body.yaml`
  - `keypoint_detectors/rtmpose/hand/rtmpose-hand.yaml`
  - `keypoint_detectors/rtmpose/face/rtmpose-face.yaml`

  All five are under `skellytracker/core/detectors/`.
- `git ls-files` lists no `.onnx` file. `.gitignore` has no rule for `*.onnx`.
- `OnnxSession.create()` in `skellytracker/core/sessions/onnx_session.py` calls
  `resolve_model_path(spec.source, expected_filename=..., expected_sha256=...)`. It passes no `cache_dir`,
  so the default cache applies.
- `sidecar_model_spec()` in `skellytracker/core/sidecar/runtime.py` sets `expected_filename` from
  `artifact.filename` and `expected_sha256` from `artifact.url_sha256`. It does no I/O.
- The spec puts an ONNX file next to its sidecar. The code reads an ONNX file from the sidecar directory
  only for an artifact without `url`: `sidecar_model_spec()` then builds a `local_path` source from
  `sidecar_dir / artifact.filename`. No tracked sidecar has such an artifact. `resolve_model_path()`
  ignores `expected_filename` and `expected_sha256` for a `local_path` source.
- `skellytracker/tests/sidecar/test_model_registry_sidecar_support.py` tests the filename override, the
  zip extraction, a matching hash, a mismatched hash and the `local_path` case. The tests mock
  `requests.get`.

## Not repeated

- Do not treat the ONNX download cache (`~/.cache/skellytracker/models`) as the sidecar tree. The spec
  calls the sidecar tree `{cache_dir}`. Its default is `skellytracker/core`. The code does not save ONNX
  files there.
- `url_sha256` is the hash of the downloaded bytes. When the URL points to a zip archive, it is the hash of
  the archive. It is not the hash of the extracted `.onnx` file.
- `resolve_model_path()` returns an existing cache file without a hash check. The check runs only on a
  fresh download.

_Edited 2026-10-26 (this PR): link repair._

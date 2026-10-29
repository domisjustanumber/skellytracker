# Implement the Model Sidecar Spec + Dogfood YOLOX/RTMW

> **Decisions.** The decisions behind this plan are recorded in the decision log, [`decisions/`](../decisions/README.md). Entries 0002 to 0007 record its key decisions and milestones, and entry 0016 replaces the key, discovery and root rules of M6 Part A. This plan stays until the user decides to delete it ([ADR-5WKW](../decisions/entries/5WKW-implementation-work-in-the-plan.md)). Record a new decision as a decision entry, not in this plan.

> Status: **M1 to M5 are done. M6 to M12 have not started.** M6 changes package code, so it waits for the implementation stage (decision 0014). [M8](#m8--validation-preprocessing-and-decode-gaps) lists the known package gaps. The "Status" line of each milestone below gives its state.

## Context

`specs/model-sidecar/sidecar-spec.md` defines a YAML "sidecar" format that describes the runtime I/O contract for ONNX detector/pose models: input tensor shape, normalization, resize, batching, output semantics, and decode logic. Two commits (`ec12b32`, `837bd09`) landed the spec document itself; this plan implements it in code.

The goal is to "eat our own dog food": implement the sidecar system, then migrate the two existing hand-written ONNX detectors — YOLOX (person object detector) and RTMW/RTMPose wholebody (133-keypoint pose estimator) — to be driven by sidecar YAML instead of hardcoded Python constants (model URLs, mean/std, input sizes, output permutations). This must be a **no-functional-change** migration: same models, same math, same detection/keypoint output — just loaded declaratively.

Explicitly out of scope for this repo/plan: the skellycam API surface that exposes available models to FMC, and the FMC pipeline-builder UI. Those live in other repos.

Note: `CLAUDE.md` at the repo root is stale — it describes a pre-rewrite architecture (`trackers/`, `TrackedObjectDefinition`, `composite_gpu_tracker`) that no longer exists after commit `2c2615c` ("Structural rewrite (#75)"). This plan targets the **current** `skellytracker/core/` package. `CLAUDE.md` now only imports `AGENTS.md`, which describes the current layout (decision 0001).

## Key decisions

1. **Storage layout.** Sidecar YAML files are git-tracked inside the package tree at `skellytracker/core/detectors/object_detectors/{family}/{model_id}.yaml` and `skellytracker/core/detectors/keypoint_detectors/{family}/{part}/{model_id}.yaml`, matching the spec's layout exactly. ONNX binaries are **not** git-tracked — they still download through the existing `ModelSource`/`resolve_model_path()` (`skellytracker/core/sessions/model_registry.py`), extended to (a) save under the sidecar's own directory instead of the flat `~/.cache/skellytracker/models/`, (b) honor the sidecar's `filename` field instead of deriving it from the URL, and (c) verify `url_sha256`. This reuses the existing download/zip-extraction machinery rather than building a new one. **(a) was not implemented:** downloaded ONNX files still cache flat in `~/.cache/skellytracker/models/` under the sidecar's `filename` (see M2); decision 0016 (sidecar catalogs) keeps that location. (b) and (c) are done.

2. **`tracked_points` ordering for RTMW.** The existing `rtmpose_wholebody.yaml` point list is in a *re-ordered* "schema order" (body, right_hand, left_hand, face), requiring the hardcoded `_MODEL_TO_SCHEMA_PERM` permutation array to fix up the model's true native output order (body, face, left_hand, right_hand). The spec requires `tracked_points[i]` to equal the model's i-th native output index, so the new sidecar's `tracked_points` will be authored in **true native model order**, eliminating the permutation entirely. This changes the *array order* of the returned `Keypoints`, but not the name→value mapping (`Keypoints` is name-indexed; nothing in the codebase relies on positional order — confirmed via grep). Parity tests must therefore compare by name, not raw array equality.

3. **Detector replacement strategy.** Modify `YoloxPersonDetector` and `RTMPoseKeypointDetector`/`RTMWWholebodyDetector` *in place* — same registered `detector_type` string (`"yolox_person"`, `"rtmpose"`), same config field surface, same `detect`/`preprocess`/`postprocess`/`connections` signatures — so `build_object_detector`/`build_keypoint_detector`, `TrackerConfig`, and all existing call sites keep working unmodified. Internals swap hardcoded constants for sidecar-driven lookups, but decode math is reused verbatim from the existing pure functions in `yolox_preprocessing.py` / `rtmpose_preprocessing.py`.

4. **RTMW file relocation.** Move the wholebody detector from `keypoint_detectors/rtmpose/wholebody/` to a new `keypoint_detectors/rtmw/wholebody/` directory, matching the spec's own family naming (`model_id: rtmw-wholebody`). A grep of all importers found the following that must keep working: `skellytracker/core/detectors/keypoint_detectors/rtmpose/__init__.py`, `.../rtmpose/rtmpose_keypoint_detector.py` (already a re-export shim), `.../rtmpose/wholebody/run_demo.py`, plus test/example files importing `from skellytracker.core.detectors.keypoint_detectors.rtmpose import RTMPoseKeypointDetector` or directly from `rtmpose.wholebody.rtmpose_wholebody_detector`. Keep `rtmpose/__init__.py` and a `rtmpose/wholebody/rtmpose_wholebody_detector.py` re-export shim pointing at the new `rtmw/wholebody/rtmw_wholebody_detector.py` module so none of these break. `KEYPOINT_DETECTOR_REGISTRY["rtmpose"]` key is unchanged.

5. **YOLOX output-contract representation.** YOLOX's post-graph-surgery ONNX actually emits two tensors (pre-NMS boxes + scores), which doesn't fit the spec's single-tensor `detections`+`fields` model cleanly. Resolve by having the sidecar describe the **native, un-stripped checkpoint contract** (one `detections` output, `fields: [x1,y1,x2,y2,score]`, `requires_nms: false`) — the upstream OpenMMLab export's actual shape. The `prepare_yolox_onnx` graph-surgery step (dynamic batch + NMS-stripping optimization) stays exactly as-is, as an internal implementation detail not modeled in YAML, exactly as it isn't described by anything declarative today.

## Implementation

### M1 — Sidecar resolution engine + Pydantic model (no detector changes)

**Status: DONE (commit `dd10819`).**

New package `skellytracker/core/sidecar/`:

- `errors.py` — `SidecarError` base, plus `SidecarParseError`, `SidecarRefError` (missing file / cycle / sibling-key / escapes-cache_dir), `SidecarBaseError`, `SidecarSchemaVersionError`, `SidecarValidationError` (wraps Pydantic `ValidationError` with file path attached). Each error carries `.file_path` and names the offending directive, matching the spec's "recoverable catalog errors."
- `resolution.py` — pure YAML-merge logic, no Pydantic dependency:
  - `parse_sidecar_file(path) -> dict`
  - `resolve_sidecar_composition(path, cache_dir) -> dict` — resolves `$ref` for a file relative to *that file's own directory* before merging it into a `base` chain (order matters: ref-resolve top-down per file, then deep-merge bottom-up), enforcing "never escape above `cache_dir`" via `Path.resolve()` + `is_relative_to()`.
  - `_deep_merge(base, override)` — JSON Merge Patch semantics: mapping+mapping recurses key-by-key with `None`-value delete; sequence/scalar replaces wholesale. Used for both `base` inheritance and per-size `sizes.<name>` merging.
  - `_resolve_refs(node, current_file, cache_dir, stack)` — recursive `$ref` walker with cycle detection (`stack`) and strict-form enforcement (`{$ref: x, other: y}` errors).
- `model.py` — the `SidecarModel` Pydantic hierarchy (`extra="forbid"`), submodels: `InputSpec`, `CustomNormalization`, `ResizeSpec`, `CropPolicySpec`, `BatchingSpec`, `OutputSpec`, `DetectionDecodeSpec`, `PoseSpec`, `SkeletonSpec`, `PoseDecodeSpec`, `OverlaySpec`, `OverlayGroupSpec`, `SizeSpec`/`OnnxSpec`/`BatchArtifactGroup`/`PrecisionArtifact`. `SidecarModel` validates everything genuinely shared at the top level, but keeps `sizes: dict[str, dict[str, Any]]` as raw (unvalidated) dicts — `SidecarModel.resolved_size(name)` deep-merges `sizes[name]` over the top level (same `_deep_merge` as `base`) and validates the result as a `SizeSpec` where `input.shape`/`resize.target_size` become required.
  - `canonical_mapping`/`derived_points` `prefixes` + `[prefix]X: "Y"` expansion implemented as a shared, dependency-free helper (`core/io/canonical_mapping_expansion.py`), invoked as a `model_validator(mode="before")` on `PoseSpec`.
  - The spec's validation-rule checklist is mapped to field/model validators — single-field checks as `field_validator`s, single-submodel invariants as `model_validator`s on that submodel, and genuinely cross-cutting checks (role↔semantic↔decode consistency, `fields` must appear in `outputs`, overlay-vs-skeleton-vs-tracked_points) as `model_validator(mode="after")` on `SidecarModel` itself.
- `versioning.py` — `parse_skellytracker_version(v) -> (year, month, build, tag)`, `is_schema_version_supported(sidecar_version, installed_version) -> bool`, `require_stable_version(v)`, called from the loader.
- `loader.py` — `load_sidecar(path, cache_dir=None) -> SidecarModel`: `parse_sidecar_file` → `resolve_sidecar_composition` → `SidecarModel.model_validate()`, plus the `model_id == basename` check and `schema_version` support check.

Also done as part of M1: `skellytracker/core/io/canonical_mapping_expansion.py` (new, shared `prefixes`/`[prefix]` expansion helper) and `TrackerMapping.from_yaml` extended to use it.

Tests: `skellytracker/tests/sidecar/test_resolution.py` (18 tests, `tmp_path`-based fixtures covering `$ref` chains, cycles, `base`+null-delete, sibling-key errors, escape-cache_dir rejection) and `test_model_validation.py` (54 tests covering the validation-rule checklist, grouped by spec section). All passing; `ruff` clean.

### M2 — Storage/artifact plumbing

**Status: DONE (commit `dd10819`).**

- Extended `resolve_model_path()` in `skellytracker/core/sessions/model_registry.py` with optional `expected_filename` (save/lookup as `cache_dir / expected_filename` instead of deriving from the URL tail) and `expected_sha256` (verify downloaded bytes before caching, raise new `ModelIntegrityError` on mismatch — the corrupt temp file is deleted, nothing is written to the cache path). Additive/backward-compatible — existing callers unaffected (both default `None`).
- `skellytracker/core/sidecar/runtime.py`: `sidecar_model_spec(sidecar, size, batch_key, precision, name, sidecar_dir, prepare=None, coreml_options=None) -> OnnxModelSpec` (builds a lazy, pure `OnnxModelSpec` from the chosen artifact — `name` is caller-supplied, no I/O happens here; see the M3 follow-up note below for why this superseded an earlier eager version), `build_normalization_fn(input_spec, precision) -> Callable[[NDArray], NDArray]` (resolves `normalization_by_precision[precision] → normalization → "imagenet_bgr"` and returns the numpy transform for `none`/`unit_float`/`imagenet_bgr`/`imagenet_rgb`/`custom`), `resolve_normalization_mode(...)` helper.

Tests: `test_model_registry_sidecar_support.py` (sha256 verification and filename-override with mocked `requests.get`) and `test_runtime.py` (normalization dispatch, `OnnxModelSpec` construction from a local artifact) — no real downloads needed. All passing.

**Not yet built in M2** (deferred to M3/M4 since they're detector-specific): `sidecar_letterbox_preprocess`/`sidecar_detection_decode`/`sidecar_affine_crop_preprocess`/`sidecar_simcc_decode` dispatch functions in `runtime.py` — these wrap the existing preprocessing/decode functions and are added alongside each detector's migration.

### M3 — YOLOX migration

**Status: DONE, including a post-migration cleanup pass (commits `45533bd`, `8848781`, `4a22905`).** The bullets below narrate how it evolved; see "Current file layout" at the end for where things actually live now — several of the paths/names named in the earlier bullets (`yolox_preprocessing.py`, `sidecar_letterbox_preprocess`, `sidecar_detection_decode`) were later moved/renamed and no longer exist.

- New `skellytracker/core/detectors/object_detectors/yolox/yolox.yaml`: `role: [object_detector]`, `input.normalization: none` (ONNX graph normalizes internally, matching current behavior), `input.resize: {method: letterbox, preserve_aspect_ratio: true, pad_value: 114}`, `outputs` = single `detections` entry with `fields: [x1,y1,x2,y2,score]` (native contract, see decision 5), `decode: {box_format: xyxy, requires_nms: false, ...}` matching today's defaults. `sizes` keys kept identical to today's `model_name` strings (`yolox-tiny`, `yolox-m`). Real `url_sha256` computed for both checkpoint zips (downloaded once and hashed).
- Added `sidecar_letterbox_preprocess`/`sidecar_detection_decode` dispatch functions to `yolox_preprocessing.py` (**not** `runtime.py` as originally sketched — see below) — thin wrappers around the *existing* `yolox_letterbox_preprocess`, `_postprocess_prenms`, `_postprocess_yolox`, `multiclass_nms`, unchanged.
- **Deviation from the original sketch:** the plan's sketch had `runtime.py` importing from `yolox_person_detector.py`'s decode helpers while `yolox_person_detector.py` imports from `runtime.py` — a real circular import (confirmed by triggering it both ways depending on which module a test imports first). Fixed by (a) moving `_postprocess_prenms`/`_postprocess_yolox` into `yolox_preprocessing.py` (code unchanged), and (b) putting the two new `sidecar_*` dispatch wrappers in `yolox_preprocessing.py` too, which imports `build_normalization_fn` from `sidecar/runtime.py` — a one-directional dependency (`runtime.py` has zero knowledge of YOLOX). `yolox_person_detector.py` imports from both, no cycle.
- Captured a golden-output fixture from the **pre-migration** `YoloxPersonDetector` against the repo's existing test image, before touching the file: `skellytracker/tests/sidecar/fixtures/golden/yolox_m_detect.json` and `yolox_tiny_detect.json`.
- Rewrote `yolox_person_detector.py` internals: `_YOLOX_MODEL_URLS`/`_YOLOX_INPUT_SIZES` replaced by a module-level `_SIDECAR = load_sidecar(...)`; `preprocess`/`postprocess`/`detect` delegate to the sidecar + dispatch functions. `model_spec()` builds `OnnxModelSpec` directly from sidecar data rather than via `runtime.sidecar_model_spec()` — that helper eagerly downloads/verifies and renames the spec (`f"{model_id}-{size}"`), which would (a) trigger a network download merely by importing the module (`YOLOX_MODEL_SPECS` is built eagerly at import time) and (b) break the `spec.name == model_name` contract asserted by `TestYoloxPersonDetectorModelSpec`. Kept `OBJECT_DETECTOR_REGISTRY["yolox_person"]` and the config's public fields unchanged.
- **Follow-up (same working tree): `url_sha256` is now actually verified**, not just declared. `OnnxModelSpec` (`skellytracker/core/sessions/onnx_session.py`) gained two purely-additive optional fields, `expected_filename`/`expected_sha256`; `OnnxSession.create()`'s per-model loop threads `spec.expected_filename`/`spec.expected_sha256` into its (already-lazy, already-per-`create()`-call) `resolve_model_path(spec.source, ...)` call. Per user decision, the sidecar's declared filename (e.g. `yolox-m_b1_fp32.onnx`) is pinned as the cache filename instead of the old URL-tail-derived name.
- **Second follow-up (same working tree): `sidecar_model_spec()` redesigned to be the single, pure, generic builder** — the earlier YOLOX-specific hand-rolled `model_spec()` body (duplicating what `sidecar_model_spec()` does) was deleted; `YoloxPersonDetector.model_spec()` is now a direct call into `runtime.sidecar_model_spec(...)`. This was possible because the *original* reason the two diverged — `sidecar_model_spec()` eagerly downloading/verifying and renaming to `f"{model_id}-{size}"` — was itself a design flaw, not a fixed requirement: it conflated "build a declarative spec" with "resolve/cache/verify a model," work that already has a single home (`OnnxSession.create()`). Fixed by making `sidecar_model_spec()` pure (no I/O at all — not even checking a local artifact exists) and taking `name` as a required caller-supplied parameter instead of deriving it, since a fixed naming convention could collide across sidecars sharing one `OnnxSession`. `OnnxSession.create()` remains the only place resolution/verification happens for every sidecar-driven detector, present and future (e.g. M4's RTMW). No other detector calls `sidecar_model_spec()` yet, so this is a clean break with no other call sites to update.
- **Post-migration cleanup (commit `8848781`):** `detect()` had grown a second, duplicate code path (`_detect_yolox()`) that reimplemented preprocess→run→decode instead of calling `self.preprocess()`/`self.postprocess()`; folded into one path. Added guards so a sidecar declaring resize/decode options the code doesn't implement (`affine_person_crop`, non-`xyxy` box formats, etc.) fails loudly (`NotImplementedError`) instead of silently mis-processing.
- **Post-migration generalization (commit `4a22905`):** on review, decided the pre/postprocessing functions should become genuinely generic (branch on the full sidecar spec, not just guard against deviation) so future model families (RTMW in M4, and beyond) can reuse them instead of reimplementing. This moved code out of the YOLOX-specific file and out of `core/sidecar/` entirely, since preprocessing/decode aren't sidecar-*parsing* concerns even though they're configured by sidecar-described specs:
  - `core/detectors/image_preprocessing.py` (new) — `letterbox_preprocess`, `preprocess_image` (generic resize dispatch on `input.resize.method`), plus `build_normalization_fn`/`resolve_normalization_mode` (moved here from `sidecar/runtime.py`).
  - `core/detectors/object_detection_decode.py` (new) — `nms`, `multiclass_nms`, `boxes_to_xyxy`, `decode_prenms`, `decode_nms_baked_in` (moved from a short-lived `sidecar/detection_decode.py`).
  - `core/detectors/object_detectors/yolox/yolox_decode.py` (renamed from `yolox_preprocessing.py`) — now holds only what's genuinely YOLOX-specific: `_decode_yolox_raw_anchor_grid` (stride-grid reconstruction unique to YOLOX's head) and `yolox_detection_decode` (renamed from `sidecar_detection_decode` — the top-level dispatcher that picks between the generic decode strategies and the YOLOX-specific one based on what a given export emits).
  - `core/sidecar/runtime.py` trimmed to just `sidecar_model_spec` — the one genuinely sidecar-parsing concern (resolving artifact URLs/paths) left in that package.
  - Removed two dead `YoloxMetadata` fields (`original_size`, `is_prenms`) discovered during this pass — neither was read anywhere.

**Current file layout** (post-cleanup):
- `core/detectors/image_preprocessing.py` — generic resize+normalize, usable by any sidecar-driven detector.
- `core/detectors/object_detection_decode.py` — generic NMS/box-format/decode-strategy utilities, usable by any object detector.
- `core/detectors/object_detectors/yolox/yolox_decode.py` — YOLOX-specific raw-anchor-grid decode + the per-family dispatcher (`yolox_detection_decode`).
- `core/detectors/object_detectors/yolox/yolox_person_detector.py` — `preprocess()`/`postprocess()`/`detect()` call straight into the above; no YOLOX-specific preprocessing code of its own.
- `core/sidecar/runtime.py` — only `sidecar_model_spec` now.

**Known gap, not yet addressed:** `DetectionDecodeSpec` fields `requires_nms`, `max_detections`, `confidence_threshold_default`, `may_include_non_person_classes`, `class_field` are validated in `yolox.yaml` but nothing in the decode code reads them — actual thresholds/limits come from `YoloxPersonDetectorConfig`'s own Python defaults instead, which currently just happen to agree. Worth resolving (source config defaults from the sidecar, or drop the unused fields) before or during M4.

Tests: `skellytracker/tests/sidecar/test_yolox_sidecar.py` (loads/validates the real file; parity tests comparing post-migration `detect()` output against the golden fixture via `np.allclose`, run for both `yolox-m` and `yolox-tiny` — both passed, exact match within tolerance, still passing against real onnxruntime inference after the cleanup pass). `test_yolox_detector.py`/`test_image_preprocessing.py`/`test_object_detection_decode.py` cover the current module split. Full suite: `pytest skellytracker/tests` — 377 passed. `ruff`/`black`/`isort` clean on all touched files.

### M4 — RTMW migration

**Status: DONE.**

- `skellytracker/core/detectors/shared/skeletons/coco133_tracked_points.yaml` and `coco133_skeletons.yaml` — ported from the old `rtmpose_wholebody.yaml`, `tracked_points` reordered to native model order (body, face, left_hand, right_hand) per decision 2; `connections` ported unchanged (name-based, order-independent).
- `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml` — `role: [pose_estimator]`, `input.resize: {method: affine_person_crop, crop_policy: {expand_ratio: 1.25, maintain_aspect_ratio: true}}`, `input.normalization: imagenet_bgr`, `pose.tracked_points`/`connections` via `$ref` to the shared fragments, `pose.canonical_mapping` via `$ref` to a new composed mapping file, `pose.decode: {method: simcc}`, `overlay.groups` ported from `connection_groups()`'s prefix logic. `sizes` keys match the old `model_name` strings; real `url_sha256` computed from the three downloaded checkpoint zips.
- `rtmw_wholebody_to_canonical_mapping.yaml` (net-new — no wholebody canonical mapping existed before) — composes the existing body mapping via `base:` plus a hand-authored `prefixes: [right_hand_, left_hand_]` + `[prefix]X: "Y"` block (quoted — an unquoted leading `[` is a YAML flow-sequence opener, a parse error in a block-mapping key; the spec's own worked example omits the required quoting).
- **Deviation from the sketch:** `sidecar_affine_crop_preprocess`/`sidecar_simcc_decode` were not added to `runtime.py`. Following M3's established split (parsing stays in `core/sidecar/`, processing lives in `core/detectors/`), `affine_person_crop` was instead implemented as a new branch directly in the existing generic `core/detectors/image_preprocessing.py:preprocess_image()` (reusing `bbox_xyxy2cs`/`top_down_affine` from `rtmpose_preprocessing.py`), and SIMCC decode became `core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_decode.py` (family-specific, same tier as `yolox_decode.py`), reusing `rtmpose_letterbox_postprocess` unchanged. `preprocess_image()`'s return type widened to `float | tuple[NDArray, NDArray]` (letterbox's scalar `ratio` vs. affine crop's `(center, scale)`) — not a new pattern, since `YoloxMetadata.ratio` vs. `RTMPoseMetadata.center/scale` were already distinct per-family dataclasses one call-frame up.
- **New generic module** `core/detectors/overlay_groups.py` (`resolve_overlay_groups`) — generalizes the old hardcoded 4-branch prefix-matching `if/elif` in `connection_groups()` into a spec-driven version (explicit `connections` groups checked first, then `prefix` groups in declared order, remaining edges to the one default group), reusable by any future sidecar-driven pose detector.
- **Circular-import gotcha:** `rtmpose_preprocessing.py` lives under `keypoint_detectors.rtmpose`, whose `__init__.py` eagerly imports the wholebody shim (for registry side effects) — a module-load-time import of `rtmpose_preprocessing` from either `image_preprocessing.py` or the (then-named) `rtmw_decode.py` creates a real cycle back through the shim into the still-initializing `rtmw_wholebody_detector` module. Fixed by deferring both imports to inside the function body (they only run at call time, by which point everything is loaded) — see the comments at both import sites. (The same gotcha resurfaced in M4b when the decode module was promoted into the `rtmpose` package itself — see that section.)
- Moved to `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py`; deleted `_MODEL_TO_SCHEMA_PERM`. Per user decision, renamed the class/config to `RTMWWholebodyDetector`/`RTMWWholebodyDetectorConfig` (`detector_type`/registry key stay `"rtmpose"`, unchanged). Old `rtmpose/wholebody/rtmpose_wholebody_detector.py` is now a re-export shim (`as`-aliasing back to the old `RTMPoseDetectorConfig`/`RTMPoseKeypointDetector`/`RTMPOSE_MODEL_SPECS` names) — confirmed needed by `test_run_batched.py`'s direct import; `rtmpose/__init__.py` and the pre-existing `rtmpose_keypoint_detector.py` shim needed no changes. `connection_groups()` is a thin wrapper over `resolve_overlay_groups(_SIDECAR.overlay, _CONNECTIONS)`.
- Golden fixture captured from the pre-migration detector (by-name, all 3 model sizes) before touching the file: `skellytracker/tests/sidecar/fixtures/golden/rtmw_wholebody_{model_name}_detect.json`.
- Deleted the now-redundant `rtmpose_wholebody.yaml` schema file after the sidecar was validated and confirmed unreferenced (grep-checked).

Tests: `tests/sidecar/test_rtmw_sidecar.py` (loads/validates the real file; 133 tracked points in native order; `canonical_mapping` prefix-expansion produces `right_hand_wrist`/`left_hand_wrist`; `overlay.groups` has 4 entries; parity test against the golden fixture by name, `np.allclose(atol=1e-3)` — actual result: **exact match, zero numeric diff**, for all three model sizes; `model_spec()` no-network-I/O + sha256 verify/reject tests). New `tests/test_image_preprocessing.py::TestPreprocessImageAffinePersonCrop` and `tests/test_overlay_groups.py`. `test_run_batched.py`/`test_rtmpose_detectors.py`/`test_rtmpose_video.py` pass unmodified (48 tests) against the shim. Full suite: `pytest skellytracker/tests` — 400 passed. `ruff` clean; `black`/`isort` clean modulo a pre-existing repo-wide isort/black formatting disagreement on wrapped multi-name imports (already present on `main`/other M3 files before this change — left in black's formatting, matching existing convention). Manually smoke-tested the full YOLOX+RTMW+annotator demo pipeline (`build_rtmpose_demo` → `Tracker.process_image` → `KeypointAnnotator.annotate`) against the test image — skeleton and per-region overlay colors (body/right_hand/left_hand/face) render correctly.

**Superseded by M4b:** the decode helper originally landed here as `keypoint_detectors/rtmw/wholebody/rtmw_decode.py` (`rtmw_pose_decode`) was promoted to a shared, family-generic module during M4b — it turned out to have nothing RTMW-specific in it. It now lives at `keypoint_detectors/rtmpose/rtmpose_simcc_decode.py` as `simcc_pose_decode`; `rtmw_decode.py` was deleted.

### M4b — RTMPose body/hand/face migration

**Status: DONE.** Scoping correction: M4 should have migrated *all* RTM-based keypoint detectors, not just wholebody. This milestone finishes the job for `RTMPoseBodyDetector`, `RTMPoseHandDetector`, and `RTMPoseFaceDetector` (registry keys `rtmpose_body`/`rtmpose_hand`/`rtmpose_face`, unchanged), following the exact pattern M4 established, with no functional change (same models, same math; parity verified by-name against golden fixtures captured pre-migration).

- Unlike RTMW, **no directory relocation** — body/hand/face are genuine `rtmpose`-family models already living at `keypoint_detectors/rtmpose/{body,hand,face}/`, so files were edited in place with no shim needed.
- New shared skeleton fragments under `core/detectors/shared/skeletons/`: `coco17_tracked_points.yaml`/`coco17_skeletons.yaml` (body, 17 pts), `hand21_tracked_points.yaml`/`hand21_skeletons.yaml` (hand, 21 pts), `face106_tracked_points.yaml`/`face106_skeletons.yaml` (face, 106 pts, LaPa) — ported verbatim from each detector's old point/connections YAML.
- New sidecar YAMLs: `rtmpose/body/rtmpose-body.yaml`, `rtmpose/hand/rtmpose-hand.yaml`, `rtmpose/face/rtmpose-face.yaml` — same shape as `rtmw-wholebody.yaml` (`role: [pose_estimator]`, `input.normalization: imagenet_bgr` — verified identical to the pre-migration hardcoded `_RTMPOSE_MEAN`/`_STD`, `input.resize: {method: affine_person_crop, crop_policy: {expand_ratio: 1.25, maintain_aspect_ratio: true}}`, `pose.decode: {method: simcc}`). `sizes` keyed by the pre-migration `model_name` strings, with real `url_sha256` computed by downloading each checkpoint zip once. Old schema-only YAMLs (`rtmpose_body.yaml`, `rtmpose_hand.yaml`, `rtmpose_face.yaml`) deleted after porting (grep-confirmed unreferenced; `_schema_loader.py` itself is still used by the unrelated mediapipe detectors, so it was kept).
- **Canonical-mapping gap discovered by the sidecar's stricter validation:** `rtmpose_body_to_canonical_mapping.yaml` (used as the `base:` for RTMW's wholebody mapping) is authored for a 23-point body (COCO + 6 foot points) — the standalone body detector's own `tracked_points` is only 17 (no feet), so referencing that file directly fails `PoseSpec`'s "canonical_mapping sources must exist in tracked_points" validator. Pre-migration this was silently tolerated (missing keys are silently skipped per that file's own docstring); the sidecar's stricter validation doesn't allow it. Resolved by adding a new, correctly-scoped `rtmpose/body/rtmpose_body17_to_canonical_mapping.yaml` (17 direct mappings + the 4 already-foot-independent computed points) referenced from `rtmpose-body.yaml`; the original 23-point file is untouched and still serves RTMW's composition. Confirmed `canonical_mapping_path()` (the old classmethod pattern) has zero callers anywhere in the codebase — same as RTMW, which never defined it post-migration — so it was dropped for body/hand too rather than kept as dead API surface.
- **Pre-existing gap, left as-is:** face has no canonical-mapping YAML today and never defined `canonical_mapping_path()`. `pose.canonical_mapping` is optional in `SidecarModel`, so `rtmpose-face.yaml` simply omits it — same behavior as before migration.
- Golden fixtures captured from the pre-migration detectors (by-name, all model variants) before touching any detector file: `skellytracker/tests/sidecar/fixtures/golden/rtmpose_{body,hand,face}_{model_name}_detect.json`. (The hand fixture has 0 points — the test image isn't a hand crop, so every point falls below `confidence_threshold`; this is itself a valid parity case, since post-migration output must also be all-NaN.)
- Detector rewrites (`rtmpose_body_detector.py`/`rtmpose_hand_detector.py`/`rtmpose_face_detector.py`) follow RTMW's pattern exactly: hardcoded mean/std/URLs/input-sizes replaced by `_SIDECAR = load_sidecar(...)`; `preprocess()`/`postprocess()` call the shared `preprocess_image()`/`simcc_pose_decode()` instead of calling `rtmpose_letterbox_preprocess`/`rtmpose_letterbox_postprocess` inline; `model_spec()` becomes a thin `sidecar_model_spec(...)` call; the duplicate inline pre/postprocess logic each detector's `detect()` used to reimplement a second time (same duplication M3 cleaned up for YOLOX) was folded into one path. Registry keys, class names, and config field surfaces are unchanged.
- Body/hand/face detector modules import `rtmpose_simcc_decode` at plain module-load time (safe — they're already inside the `rtmpose` package's own import chain by the time `rtmpose/__init__.py` reaches them). `rtmw_wholebody_detector.py`, which lives *outside* the `rtmpose` package, hit the same circular-import gotcha M4 documented for `rtmpose_preprocessing` when its import of `rtmpose_simcc_decode` was tried at module level — fixed the same way, by deferring that one import to inside the function body.

Tests: `tests/sidecar/test_rtmpose_{body,hand,face}_sidecar.py` — sidecar loads/validates, tracked-point count/order, canonical-mapping spot checks, `model_spec()` no-network-I/O + sha256 verify/reject, and parity against the golden fixtures by name (`np.allclose(atol=1e-3)`) — all passing, including the hand detector's all-NaN case. Full suite: `pytest skellytracker/tests` — 431 passed. `ruff` clean; `black`/`isort` clean on all new/rewritten files (matching M4's convention: black-formatted, with the same pre-existing repo-wide isort/wrapped-import disagreement left alone).

### M4c — Consolidate generic preprocessing/decode helpers

**Status: DONE.** Follow-up prompted by reviewing M4b: `rtmpose_preprocessing.py` and `rtmpose_simcc_decode.py` (both under `keypoint_detectors/rtmpose/`) were named/located as if RTMPose-specific, but most of their contents weren't — the affine-crop math (`bbox_xyxy2cs`, `top_down_affine`, `get_warp_matrix`, ...) is the standard top-down bbox-crop transform used across pose architectures generally, and SIMCC decode (`get_simcc_maximum`, the sidecar-dispatching `simcc_pose_decode`) is specific to the SIMCC decode head, not to RTMPose as a family. Their location under `keypoint_detectors.rtmpose` was purely a packaging artifact of where the code was first vendored, and it's what forced the deferred-import workarounds in `image_preprocessing.py` and `rtmw_wholebody_detector.py` (importing anything from inside that package triggers `rtmpose/__init__.py`'s eager detector imports).

- Moved the two generic pieces to `core/detectors/`, alongside `image_preprocessing.py` and `object_detection_decode.py` (the existing precedent for "family-agnostic detector processing lives here"):
  - `core/detectors/affine_crop.py` — `bbox_xyxy2cs`, `top_down_affine`, `get_warp_matrix`, `_rotate_point`, `_get_3rd_point`, moved verbatim.
  - `core/detectors/simcc_decode.py` — `get_simcc_maximum`, `_stable_softmax`, `decode_simcc` (renamed from `rtmpose_letterbox_postprocess` — same math, moved verbatim), and `simcc_pose_decode` (the sidecar-dispatching entry point, merged in from the deleted `rtmpose_simcc_decode.py`).
- Deleted `rtmpose_preprocessing.py` and `rtmpose_simcc_decode.py` entirely. `rtmpose_letterbox_preprocess` (the other half of the old `rtmpose_preprocessing.py` pairing) was dead code by this point — nothing called it after M4b's detector rewrites switched body/hand/face to the generic `preprocess_image()` — so it was deleted rather than moved.
- **The circular-import workaround is gone**, not just relocated: since `core/detectors/affine_crop.py` and `core/detectors/simcc_decode.py` sit outside the `keypoint_detectors.rtmpose` package, importing them no longer triggers `rtmpose/__init__.py`'s eager detector imports. `image_preprocessing.py`'s deferred `bbox_xyxy2cs`/`top_down_affine` import and `rtmw_wholebody_detector.py`'s deferred `simcc_pose_decode` import both became plain top-level imports.
- All import sites updated: `image_preprocessing.py`, `rtmw_wholebody_detector.py`, and the three body/hand/face detectors now import from `core.detectors.affine_crop`/`core.detectors.simcc_decode`; `tests/test_image_preprocessing.py` likewise.

Tests: full suite unmodified and still green (`pytest skellytracker/tests` — 431 passed); `ruff`/`black` clean on all touched files.

**Superseded immediately by M4d:** `core/detectors/affine_crop.py`/`simcc_decode.py`/`image_preprocessing.py`/`object_detection_decode.py` were all moved one more time, into a new `core/detectors/processing/` subpackage — see below.

### M4d — Group generic pre/post-processing under `core/detectors/processing/`

**Status: DONE.** Follow-up on M4c, per user request: once the four generic modules (`image_preprocessing.py`, `object_detection_decode.py`, `affine_crop.py`, `simcc_decode.py`) all lived flat under `core/detectors/`, mixed in with family-specific code (`detection_context.py`, `detector_base_classes.py`, `metadata.py`, `overlay_groups.py`), it made sense to group them under one dedicated subpackage rather than leave them loose.

- New package `core/detectors/processing/` (with `__init__.py`, no re-exports — callers import the specific module) holding all four files, moved verbatim (`git mv` for the two tracked from M3/M4; plain `mv` for the two untracked from M4c).
- Every import site updated to the `core.detectors.processing.*` path: `image_preprocessing.py` (self-import of `affine_crop`), `yolox_person_detector.py`, `yolox_decode.py`, the three RTMPose body/hand/face detectors, `rtmw_wholebody_detector.py`, `sidecar/runtime.py`'s docstring, and the corresponding tests (`test_image_preprocessing.py`, `test_object_detection_decode.py`, `sidecar/test_runtime.py`).
- `overlay_groups.py` was deliberately **not** moved here — it's about grouping connections for annotation/visualization, not pre/post-processing a model's tensors, so it stays a sibling of `processing/` under `core/detectors/`.
- **Docstrings trimmed by user decision:** the "Sidecar-driven (...) — see specs/sidecar-implementation-plan.md M4b/M4..." migration-history paragraphs were removed from the four detector docstrings (body/hand/face/`rtmw_wholebody_detector.py`) — that history belongs in this plan doc and commit messages, not in code comments future readers have to wade through. Don't re-add migration narrative to these docstrings; this doc is the durable record of *why*.

Tests: full suite unmodified and still green (`pytest skellytracker/tests` — 431 passed); `ruff`/`black` clean on all touched files.

### M5 — Cleanup

**Status: DONE.** The package source has none of the dead constants below. `uv run pytest -m "not video"` passes (413 tests, 2026-10-26). A `CLAUDE.md` refresh is not necessary: `CLAUDE.md` only imports `AGENTS.md`, and `AGENTS.md` describes `core/sidecar/` (decision 0001).

- Delete dead hardcoded constants once confirmed unused (`_YOLOX_MODEL_URLS`, `_INPUT_SIZES`, `_RTMPOSE_MEAN`/`_STD`, etc. — the RTMPose body/hand/face equivalents were removed as part of M4b, mirroring RTMW in M4).
- Run the full test suite (`pytest skellytracker/tests`) to catch anything transitively exercising YOLOX/RTMPose through `Tracker`/`process_video`/`process_batch`.
- Flag (don't execute) a `CLAUDE.md` refresh describing the new `core/sidecar/` package as a follow-up.

### M6 — Generic sidecar-driven detector (drop in a YAML + ONNX, no new Python)

**Status: NOT STARTED.** M6 changes package code, so it waits for the implementation stage (decision 0014).

**Goal:** today, migrating a model family to the sidecar system still means hand-writing a `@dataclass` detector (`preprocess`/`postprocess`/`detect`/`model_spec`) per family and manually registering it — see `YoloxPersonDetector`, `RTMWWholebodyDetector`, `RTMPoseBodyDetector`/`RTMPoseHandDetector`/`RTMPoseFaceDetector`. The bodies of these are now thin wrappers around the generic `core/detectors/processing/*` functions, but they're still bespoke code per model. M6's goal is to close that last mile: **finding an ONNX file for an object or keypoint detector, writing a conforming sidecar YAML for it, and running it from skellytracker with zero new Python**, for the decode/preprocess combinations the spec already describes.

This milestone has two independent parts — a generic detector class/factory, and filling in the decode coverage gaps the current generic modules leave unimplemented. Either can land first; the factory is more valuable once decode coverage is broad enough that most new sidecars won't immediately hit a `NotImplementedError`.

**Two known gaps motivate this milestone, and neither is closed by anything already done through M4d:**

1. **The Python config/registration infrastructure is behind the sidecar infrastructure.** The sidecar YAML contract (`core/sidecar/`) and the generic processing math (`core/detectors/processing/`) are already fully generic — they don't know or care which family a model belongs to. But there is no generic Python *config* or *registration* path that lets a caller actually use a bare sidecar+ONNX pair: every detector still needs a hand-written `@dataclass` class, a hand-written `*Config` subclass with a fixed `Literal[...]` `detector_type`, and a hand-added `REGISTRY["..."] = SomeClass` line, before `TrackerConfig`/`Tracker` can run it at all. The sidecar side of the system outran the Python plumbing needed to drive it generically — Part A below is what closes that gap.
2. **YOLOX has decode math that is inherently family-specific and cannot become generic**, independent of how much Part B below gets built out. `_decode_yolox_raw_anchor_grid` (`yolox_decode.py`) reconstructs boxes from YOLOX's stride-based anchor-free grid (strides `[8,16,32]`, per-cell offset + `exp(wh)` decode) — that's specific to YOLOX's detection-head architecture, not a decode *strategy* the sidecar spec's declarative `decode` fields (`box_format`, `score_field`, `requires_nms`, ...) are designed to express. `yolox_detection_decode`'s dispatch also branches on the *loaded* ONNX graph's actual output tensor count/shape (2 outputs = pre-NMS; 1 output shape[-1]==5 = NMS baked in; shape[-1]==4 = raw grid) rather than purely on declared sidecar fields, and loading the checkpoint at all requires `prepare_yolox_onnx`'s ONNX graph surgery (`_yolox_dynamic_batch.py` — patching a static `batch=1` graph to a symbolic batch dim and extracting pre-NMS outputs, because the checkpoint's baked-in NMS/Squeeze subgraph breaks for `batch>1`) — a Python callable (`sidecar_model_spec(..., prepare=prepare_yolox_onnx)`), not a declarative sidecar field. None of this is a coverage gap Part B can fill; it's a permanent property of this model export. **YOLOX keeps its own hand-written detector/decode module, coexisting with the generic detector for other families, until it is re-exported** to a contract the spec describes (dynamic batch, no NMS in the graph, host `selection: nms`) — open work under decision 0016, which would retire the graph surgery and the exception.

**Part A — Generic detector class + auto-registration:**

> **Read decision 0016 (sidecar catalogs, in `decisions/`) before starting Part A. It replaces several rules below.** Catalog keys are `<model_id>@<source.name>` (from a new `source` field in each sidecar), not `sidecar:{model_id}`. Sidecars are discovered in every configured root — the package, local folders a user adds, and pinned Hugging Face repos — not only the package's `detectors/` folders; a YAML file is a sidecar when its top level has `schema_version` and a `model_id` equal to its basename. Detector code is chosen from the sidecar's role and sections, and a capability check marks sidecars that use unimplemented sections as unavailable. The existing `detector_type` keys stay as aliases. A hand-written detector may claim a catalog key, and the generic path never handles a claimed key: YOLOX claims `yolox@skellytracker` (gap 2 above), which answers the coexistence bullet below.

- Add `GenericObjectDetector` and `GenericKeypointDetector` — generic `ObjectDetector`/`KeypointDetector` implementations, parameterized entirely by a loaded `SidecarModel` (plus a resolved size/precision), whose `preprocess`/`postprocess`/`detect`/`model_spec` bodies are exactly what the current per-family classes already delegate to (`preprocess_image`, `yolox_detection_decode`-style generic decode dispatch, `simcc_pose_decode`, `sidecar_model_spec`). No family-specific subclassing should be required for models whose sidecar only uses implemented decode/resize options (see Part B).
- *(Replaced by 0016: the key is `<model_id>@<source.name>`, and the existing `detector_type` strings stay as aliases. The config/`TrackerConfig` work below still applies.)* Decide and implement a `detector_type` convention for generic sidecars — e.g. derive it from `model_id` (`sidecar:{model_id}` or similar) — since today's registries key off a fixed `Literal[...]` string per hand-written config class (`YoloxPersonDetectorConfig.detector_type`, etc.). A generic config (`GenericObjectDetectorConfig`/`GenericKeypointDetectorConfig`) needs a `model_id`/sidecar-path field instead of a fixed literal, and `TrackerConfig`'s discriminated-union validation needs to accept it. This is the concrete fix for gap 1 above — today nothing in `skellytracker/core/config/` or `TrackerConfig` can express "run this arbitrary sidecar" without a matching hand-written config class already existing.
- *(Replaced by 0016: discovery scans every configured root — package, user folders, pinned HF repos — with the discovery rule above, not only these two package folders.)* Add auto-discovery/registration: scan `detectors/object_detectors/*/` and `detectors/keypoint_detectors/*/*/` for sidecar YAMLs at import/startup time and populate `OBJECT_DETECTOR_REGISTRY`/`KEYPOINT_DETECTOR_REGISTRY` with generic detector entries, instead of requiring a hand-edited `REGISTRY["..."] = SomeClass` line per model (today's convention — see every `*_detector.py`'s bottom-of-file registration).
- *(Decided by 0016: a hand-written detector claims its catalog key, and the generic path never handles a claimed key.)* Decide how a hand-written family-specific detector (kept for families needing custom decode logic — YOLOX per gap 2 above being the clearest permanent example, via its raw-anchor-grid decode in `yolox_decode.py`) coexists with/overrides the generic auto-registered one for the same `model_id`, so a family that can never be purely generic doesn't collide with auto-discovery.
- Existing hand-written detectors (YOLOX, RTMW wholebody, RTMPose body/hand/face) are **not required to be replaced** by the generic class in this milestone — RTMW/RTMPose could plausibly move to the generic class once Part A lands, since their preprocess/decode (`affine_person_crop`/`simcc`) are already fully generic; YOLOX cannot, per gap 2. The bar for M6 is that a *new* model needs no new Python, not that old ones are rewritten.

**Part B — Fill decode/preprocess coverage gaps:**

Stage [M8](#m8--validation-preprocessing-and-decode-gaps) of this plan lists the known package gaps ([ADR-5WKW](../decisions/entries/5WKW-implementation-work-in-the-plan.md)). The spec also shows the gaps in these places:

- the `validate:` and `load:` notes in the front matter of each section file, and [`TRACEABILITY.md`](model-sidecar/TRACEABILITY.md);
- the skill [`implement-sidecar-section`](../.claude/skills/implement-sidecar-section/SKILL.md), which gives the steps and the order of the work.

Two rules of this part stay:

- The sidecar `decode` fields must control the decode. Today the thresholds and limits come from the Python defaults of each detector config (the known gap under M3).
- Test each new decode path with a real export: a sidecar, its ONNX file and an upstream reference output from the exporter. A spec reference example is never a test input, because it has no ONNX file. New decode math has no earlier output to compare with, so compare it with the output of the upstream library.

### M7 — Sidecar catalog, dispatch and trace tools

**Status: NOT STARTED.** It changes package code, so it waits for the implementation stage
([Stages](model-sidecar/model-addition-workflow/README.md#stages)). The generic detector of M6 needs these parts. Do them in this order: trace-tool functions, the catalog and its roots, then the capability check. The V- rule checks of the examples need a development build that loads `vNEXT` sidecars, so they come last.

- **Trace-tool functions.** Move `tools/sidecar_normalize.py` (the normalization table and the
  selector matching that the sidecar trace tool uses) into `skellytracker/core/sidecar/` without
  changes. The trace tool then imports them from the package. The capability check of [ADR-0016](../decisions/entries/0016-sidecar-catalogs.md) uses the
  same functions ([ADR-0013](../decisions/entries/0013-spec-structure.md);
  [`format.versioning`](model-sidecar/format/versioning.md#implementer-guidance)).
- **Sidecar catalog and roots.** Build the catalog of [ADR-0016](../decisions/entries/0016-sidecar-catalogs.md): the catalog key
  `<model_id>@<source.name>`, the version order and the version pins, the reserved name
  `skellytracker`, the root log and the run metadata
  ([`common.identity`](model-sidecar/common/identity.md#implementer-guidance)). Build the roots:
  the package root, local folders, Hugging Face repo snapshots (pin, refresh, cache paths without
  symlink resolution), development builds, user models and discovery in each root. Rename
  `cache_dir` to the sidecar root in the code
  ([`format.file_layout`](model-sidecar/format/file-layout.md#implementer-guidance)). See
  [ADR-0016](../decisions/entries/0016-sidecar-catalogs.md#decision).
- **Capability check and dispatch.** Build the capability check of [ADR-0016](../decisions/entries/0016-sidecar-catalogs.md). Map a catalog entry to
  detector code by its role and its spec sections. Keep the `detector_type` keys as aliases of
  `<model_id>@skellytracker`. Let a hand-written detector claim a catalog key. Make an unknown size
  an error, not a silent fallback
  ([`format.versioning`](model-sidecar/format/versioning.md#implementer-guidance); see
  [ADR-0016](../decisions/entries/0016-sidecar-catalogs.md#capability-check)).
- **V- rule checks of the examples.** The doc tests only parse and resolve each reference example,
  and check its provenance (`tools/tests/test_examples.py`).
  They do not run the `V-` rules on it, because `load_sidecar` rejects `vNEXT` and the package code
  does not change in the spec-build stage. Thus no test checks that a spec-forced edit keeps an
  example valid ([ADR-KDBD](../decisions/entries/KDBD-change-classes-and-spec-forced-edits.md), item 5). When a
  development build loads `vNEXT` sidecars (see the item Sidecar catalog and roots), validate each
  example with `SidecarModel` in `tools/tests/test_examples.py`. Until then, part 7 of the proposal
  and `uv run python tools/sidecar_trace.py impact <range>` at landing are the check.

### M8 — Validation, preprocessing and decode gaps

**Status: NOT STARTED.** It changes package code, so it waits for the implementation stage
([Stages](model-sidecar/model-addition-workflow/README.md#stages)). The package code does not yet do what the `vNEXT` spec requires for these sections. Do NMS box area and Batch forms before M10.

- **`fit` `pad_value`.** At `vNEXT`, the spec requires `pad_value` on a `fit` resize
  ([Validation rules](model-sidecar/pre/resize-fit.md#validation-rules)). The code does not require it.
  `ResizeSpec._check_method_specific_fields` in `skellytracker/core/sidecar/model.py` accepts a `fit`
  resize without `pad_value`. Then `preprocess_image` in
  `skellytracker/core/detectors/processing/image_preprocessing.py` uses `0`, and `fit_preprocess` has
  the default `pad_value=0`. Add the missing validator rule, so that no valid `vNEXT` sidecar uses the
  default. Add a test of the rejection to `skellytracker/tests/sidecar/test_model_validation.py`.
  `test_fit_method_is_valid` already sets `pad_value: 114` ([ADR-0012](model-sidecar/decisions/entries/0012-fit-resize-for-rtmo.md)).
- **`fit` scalar pad.** `fit_preprocess` in
  `skellytracker/core/detectors/processing/image_preprocessing.py` passes a scalar `pad_value` to
  `cv2.warpAffine` as `float(pad_value)`. OpenCV then fills only channel 0 of a 3-channel image: a
  scalar `114` gives the border `[114, 0, 0]`. A scalar must fill every channel, because
  `letterbox_preprocess` in the same file already does this (`np.full`). The spec does not state this
  rule. The spec must state it (see the [spec defects](model-sidecar/decisions/open-work.md#spec-defects), and
  [ADR-0012](model-sidecar/decisions/entries/0012-fit-resize-for-rtmo.md)).
- **Letterbox rounding.** `letterbox_preprocess` in
  `skellytracker/core/detectors/processing/image_preprocessing.py` cuts the resized size with `int()`.
  The `vNEXT` spec rounds with `half_even` or `half_up`, places the image at `top_left` or `center`,
  and keeps each side at least 1 pixel. The function has no `center` position and fails on a source
  that is 1 pixel wide. It reproduces 8 of the 12 `top_left` cases in
  [`pre.resize.letterbox`](model-sidecar/vectors/pre.resize.letterbox.yaml). The cut size is
  correct only for legacy sidecars.
- **Stretch unprojection.** The `stretch` branch of `preprocess_image` returns `resize_meta = 1.0`. The
  host then has no scale factors to unproject with `x * src_w / T_w`.
- **NMS box area.** The spec's `selection: nms` uses the box-area convention of the ONNX
  `NonMaxSuppression` operator, which does not add `1` to pixel widths or heights. The generic `nms()`
  in `skellytracker/core/detectors/processing/object_detection_decode.py` adds `1`. Today only the
  legacy YOLOX path uses it. It also breaks a tie between equal scores toward the higher row index,
  but the spec breaks it toward the lower row index. The vectors in
  [`post.det.selection.nms`](model-sidecar/vectors/post.det.selection.nms.yaml) show both
  differences.
- **Batch forms.** At `vNEXT`, a sidecar uses one batch form: only `"3"` with
  `batching.batch_conversion`, only `"1"`, or only `dynamic`
  ([Batch forms](model-sidecar/common/sizes-and-artifacts.md#batch-forms);
  [ADR-JB5J](../decisions/entries/JB5J-one-batch-form-for-each-sidecar.md)). `OnnxSpec._check_batch_keys` in
  `skellytracker/core/sidecar/model.py` accepts any set of integer keys, and `BatchingSpec` forbids
  the key `batch_conversion`. Add `V-common.sizes_and_artifacts-13` and `V-common.batch_conversion-1`
  to `V-common.batch_conversion-4` for `vNEXT`. The detectors ask for the batch key `"1"`, for
  example `rtmw_wholebody_detector.py` and `yolox_person_detector.py`. A b3 sidecar has no key
  `"1"`. To run it at batch 1 or 2, the host must make the artifact with `model_batch_convert`
  (Behaviour 3 of [`common.batch_conversion`](model-sidecar/common/batch-conversion.md#behaviour)).

### M9 — Source and hash checks

**Status: NOT STARTED.** It changes package code, so it waits for the implementation stage
([Stages](model-sidecar/model-addition-workflow/README.md#stages)). These checks have no order link to M7 and M8. The last sentence of Reference hash checks in the resolver waits for M12.

- **Reference hash checks in the resolver.** Add the checks of the `$ref` and `base` hashes, and of
  the bytes of each file, to `skellytracker/core/sidecar/resolution.py`. Then delete the temporary
  function `resolve` of `tools/sidecar_refs.py`. Move the `--write` and `--check` commands of that
  tool into the package as a command, and keep a thin wrapper in `tools/`. When the package sidecars
  move to a release `schema_version`, give them `source` and the hashes
  ([`format.composition`](model-sidecar/format/composition.md#implementer-guidance); see
  [ADR-0016](../decisions/entries/0016-sidecar-catalogs.md#tools-and-line-endings)).
- **Artifact hash checks.** Verify the file that `filename` names against `sha256` when the file is
  present and after a download. Today `skellytracker/core/sessions/model_registry.py` checks only
  `url_sha256`, and only during a download
  ([`common.sizes_and_artifacts`](model-sidecar/common/sizes-and-artifacts.md#implementer-guidance);
  see [ADR-0016](../decisions/entries/0016-sidecar-catalogs.md#artifact-hashes)).

### M10 — YOLOX re-export

**Status: NOT STARTED.** It changes package code, so it waits for the implementation stage
([Stages](model-sidecar/model-addition-workflow/README.md#stages)). This stage needs M6, the catalog-key claim of M7, and the NMS box area and the batch forms of M8.

- **YOLOX.** Re-export YOLOX to a contract that the spec describes: dynamic batch
  (`common.batching`), no NMS in the graph, and host `selection: nms` (`post.det.selection.nms`). Run
  a parity check on the new export. Then remove the claim of
  the hand-written YOLOX detector on the catalog key `yolox@skellytracker`
  ([`format.versioning`](model-sidecar/format/versioning.md#implementer-guidance);
  [ADR-0016](../decisions/entries/0016-sidecar-catalogs.md#detector-dispatch); see also
  [ADR-0006](../decisions/entries/0006-yolox-native-contract.md)).

### M11 — Repository fixes

**Status: NOT STARTED.** It changes package code, so it waits for the implementation stage
([Stages](model-sidecar/model-addition-workflow/README.md#stages)). Each fix has its own root cause. Fix each one in its own PR. Run-time check IDs is a decision of the user, not a fix.

- **Unused module.** `skellytracker/core/detectors/keypoint_detectors/rtmpose/rtmpose_preprocessing.py`
  is tracked, but no module imports it ([ADR-0007](../decisions/entries/0007-generic-processing-package.md)). Remove it.
- **MediaPipe timestamps on Windows.** In video mode, the MediaPipe detectors under
  `skellytracker/core/detectors/keypoint_detectors/mediapipe/` use `int(time.monotonic() * 1000)` as
  the timestamp when the caller gives no `timestamp_ms`. On Windows, with Python 3.12,
  `time.monotonic()` uses `GetTickCount64()`, which has a resolution of 15.6 ms. Two frames in one
  tick get the same timestamp, and MediaPipe raises "Input timestamp must be monotonically
  increasing". The fallback timestamp must increase on each call.
- **MediaPipe landmarkers on Windows.** On Windows, the fast suite (`uv run pytest -m "not video"`)
  can also hang. A MediaPipe `PoseLandmarker` that an earlier test left open is garbage-collected
  during the teardown of the `onnx_session` fixture in `skellytracker/tests/test_rtmpose_detectors.py`.
  Then `PoseLandmarker.__del__` calls `close()`, and `close()` deadlocks in the MediaPipe dispatcher.
  This occurred on 2026-10-23, two times in sequence. The file alone passes, and Linux CI passes. This
  is a code defect: the tests or the detectors must close their landmarkers. For example, the tests in
  `skellytracker/tests/test_mediapipe_detectors.py` create MediaPipe detectors and do not call
  `close()`. The fix waits for the implementation stage.
- **Run-time check IDs.** A vector case for a refused tensor or caller argument writes
  `{error: no-rule}`, because no validation rule can check that input
  ([ADR-TA0G](../decisions/entries/TA0G-vector-cases-and-reference-modules.md)). The implementation stage can give these
  run-time checks their own IDs, for example `C-<section-id>-<n>`. A sidecar before `vNEXT` that uses
  a feature that is "Not available." also gives `no-rule`. A rule `V-format.versioning-<n>` can
  replace that use. The user decides both.

### M12 — `vNEXT` release

**Status: NOT STARTED.** It waits for the first skellytracker release that ships the spec. It changes the spec, the examples and the vectors, not the package code. This is the last stage.

- **`vNEXT` release step.** At the first skellytracker release that ships the spec, one content PR
  replaces `vNEXT` with that release version everywhere. Then the exporters regenerate their sidecars
  ([Publishing](model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing)). OpenMMLab-Exporter ([`rtmdet_person/sidecar.py:30`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmdet_person/sidecar.py#L30)) and Roboflow-Exporter ([`rf_detr/sidecar.py:32`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L32)) write `vNEXT` today.

## Reference examples

Moved to [Reference examples](model-sidecar/model-addition-workflow/reference-examples.md) in the model addition workflow (decision [b9fm](../decisions/entries/b9fm-finished-sidecar-plans.md)). That file gives what the examples are and how to provide or replace an example.

## Verification

- `pytest skellytracker/tests` — full suite green, including the new `skellytracker/tests/sidecar/` directory and the existing YOLOX/RTMPose/run_batched tests unmodified.
- `uv run ruff check skellytracker/ tools/` passes. Do not run `black` or `isort` on the package (`AGENTS.md`, section 1).
- Manually run `uv run python -m skellytracker.core.detectors.keypoint_detectors.rtmpose.wholebody.run_demo` and the YOLOX demo path against a webcam or test video to visually confirm detections/keypoints look correct post-migration — this is the actual "no functional change" smoke test beyond numeric parity.
- Parity assertions (golden fixture vs. sidecar-driven output, `np.allclose` within tolerance) are the primary automated gate for "no functional change."

## Resuming this plan in a fresh session

M1 to M5 are done. Each milestone above gives its file layout. The four generic processing modules are in `core/detectors/processing/` (decision 0007). Do not create the deleted modules `yolox_preprocessing.py`, `rtmpose_preprocessing.py` and `rtmpose_simcc_decode.py` again. The next work is M6. It starts in the implementation stage (decision 0014). Use the skill `implement-sidecar-section`. Before Part A, read decision 0016. No `GenericObjectDetector` or `GenericKeypointDetector` class exists yet.

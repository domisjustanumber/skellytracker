# Phase 0 — Inventory Upstream core/ Package ✅ COMPLETED

**Depends on:** — (first phase)  
**Can run parallel with:** — (blocks Phase 1)  
**Estimated scope:** Read-only investigation, ~30 min

## Phase 0 Findings (2026-07-28)

The investigation confirmed the upstream `core/` structure largely matches expectations, with these key differences:

| Finding | Impact on Plans |
|---------|----------------|
| `batch_size` already in `OnnxSessionConfig` | Phase 3 config rename is a **no-op** for session config |
| `require_provider()` already strict, raises `SessionCreationError` | Phase 2 needs less work — only fix `build_tuned_ort_session` fallback |
| `build_tuned_ort_session` still has fallback chaining (TRT→CUDA→CPU, etc.) | Phase 2 IS needed for the session builder |
| `max_batch_size` still in ORT utility layer | Phase 3 rename needed in `ort_session_utils.py` |
| TRT profiles: min=1, opt=N, max=N | Phase 3 needs to pin min=N |
| No `BatchSizeMismatchError` | Phase 3 needs to create it |
| `scipy` removed from dependencies | Phase 1: don't add scipy; Kalman uses pure numpy |
| Upstream has 20+ test files | Phase 1: bring them in alongside core/ |
| `OnnxSessionConfig.batch_size` required, no default | Phase 3: add default=1 |
| Upstream branch is `main` (not `development`) | All references corrected |

## Goal

Clone or fetch the upstream `freemocap/skellytracker` main branch and inventory the actual `core/` package structure, API surface, and dependencies. Use this to validate and update the assumptions in Phases 1-3 before any code is copied or modified.

## Why This Matters

Phases 2 and 3 were written based on GitHub text searches, not by reading the actual upstream code. The upstream may differ from expectations in critical ways:

- ORT session construction may already be strict (Phase 2 becomes no-op)
- `batch_size` may already be renamed (Phase 3 becomes no-op)
- Session architecture may be completely different (Phases 2/3 need total rewrite)
- New dependencies may conflict with existing `pyproject.toml` constraints
- The `core/` tree may have extra files or missing files relative to the expected structure

A 30-minute inventory avoids hours of wasted implementation.

## Steps

### 0.1: Fetch Upstream

```powershell
# Add upstream remote if not already present
git remote add upstream https://github.com/freemocap/skellytracker.git

# Fetch main branch
git fetch upstream main

# Show what files exist in upstream core/
git ls-tree -r --name-only upstream/main -- skellytracker/core/
```

### 0.2: Inventory Files

Compare the actual file listing against the expected structure from Phase 1. Note:

- Files that exist but weren't expected
- Files that are missing from expectations
- Any `examples/` or `data/` directories that ship alongside `core/`

### 0.3: Inventory API Surface

Read key files to verify the API matches assumptions:

| File to Check | What to Verify |
|---------------|---------------|
| `core/__init__.py` | Public exports match the 34 symbols we expect |
| `core/tracker/tracker.py` | `Tracker` class has `create()`, `process_image()`, `process_batch()` |
| `core/config/tracker_config.py` | `TrackerConfig` has `stages: list[DetectionStageConfig]` |
| `core/config/detector_configs.py` | `KeypointDetectorConfig`, `ObjectDetectorConfig` exist |
| `core/detectors/detector_base_classes.py` | Registry pattern: `KEYPOINT_DETECTOR_REGISTRY`, `OBJECT_DETECTOR_REGISTRY`, `build_keypoint_detector()`, `build_object_detector()` |
| `core/sessions/onnx_session.py` | ORT session creation — look for fallback providers, `max_batch_size` vs `batch_size` |
| `core/sessions/ort_session_utils.py` | If separate: `build_tuned_ort_session` signature, provider list construction |
| `core/sessions/session_errors.py` | Existing error types — does `OnnxExecutionProviderStartupError` or `BatchSizeMismatchError` already exist? |
| `core/sessions/session.py` | Base `Session` ABC |
| `core/data_primitives/keypoints.py` | `Keypoints` dataclass — `names`, `xyz`, `visibility` fields |

### 0.4: Check ORT Session Construction

This is the most critical investigation for Phase 2. Find the function that builds ORT provider lists and answer:

1. Does it append fallback providers (CUDA behind TRT, CPU behind CUDA)?
2. Is there an `allow_provider_fallback` or `on_provider_missing` parameter?
3. Is there post-create provider verification?
4. What is the function signature — does it match our expected `build_tuned_ort_session(model_path, provider, device_id, ...)`?

### 0.5: Check Batch Size Semantics

Critical for Phase 3. In session configs and ORT session code:

1. Is the field called `max_batch_size` or `batch_size`?
2. What is the default value?
3. Are TRT profiles min-opt-max or exact-match?
4. Is there existing `BatchSizeMismatchError`?
5. Is there a `predict_batch()` method with size validation?

### 0.6: Inventory Dependencies

Read all `import` statements in `core/` and cross-reference against `pyproject.toml`. Identify:

- New packages not in `pyproject.toml`
- Version constraints that might conflict
- Optional imports (try/except) that indicate soft dependencies

### 0.7: Check for Upstream Tests

```powershell
git ls-tree -r --name-only upstream/main -- skellytracker/tests/
```

If upstream ships tests for `core/`, read them to understand:
- What test patterns they use
- What fixtures they expect
- What coverage exists

### 0.8: Update Phases 2 and 3

Based on findings, update `phase_2_strict_ort.md` and `phase_3_batch_size.md`:

- If upstream already has the behavior: mark phase as "no-op / verify only"
- If upstream is structurally different: rewrite the phase with correct file paths and API references
- If upstream removed relevant code: mark phase as "not applicable"

## Deliverables

- [ ] Upstream cloned/fetched
- [ ] Actual `core/` file listing compared to expected structure
- [ ] Key API surface verified (Tracker, DetectionStage, Session, Keypoints)
- [ ] ORT session construction analyzed (fallback behavior, provider list)
- [ ] Batch size semantics analyzed (field name, default, TRT profiles)
- [ ] Dependencies audited against `pyproject.toml`
- [ ] Upstream tests inventoried (if any)
- [ ] Phase 2 plan updated if needed
- [ ] Phase 3 plan updated if needed

## Verification

```powershell
# Confirm upstream remote and branch exist
git remote -v
git branch -r | Select-String "upstream/main"

# Confirm file listing captured
git ls-tree -r --name-only upstream/main -- skellytracker/core/ | Measure-Object

# Key question answered: does upstream have fallback providers?
Select-String -Path "skellytracker/core/sessions/*.py" -Pattern "CPUExecutionProvider" -Recurse
# If grep finds CPUExecutionProvider in onnx_session.py (not cpu_session.py), Phase 2 IS needed
```

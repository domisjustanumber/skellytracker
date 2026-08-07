# Phase 5 — Port Existing Tests

**Depends on:** Phases 1-4  
**Can run parallel with:** — (blocks Phase 6)  
**Estimated scope:** ~5-10 test files modified, ~3-5 new test files

## Goal

After removing old trackers and bringing in the new `core/` architecture, ensure the test suite passes. Migrate remaining architecture-agnostic tests to work with `core/`, and add tests for new paths that lack coverage.

## Context

**Phase 0 findings:** The upstream ships 20+ test files for the `core/` architecture. These should be brought in alongside `core/` during Phase 1, not written from scratch.

Upstream test files:

```
skellytracker/tests/
    README.md
    conftest.py
    test_aruco_detector.py
    test_aruco_video.py
    test_charuco_detector.py
    test_charuco_video.py
    test_data_store.py
    test_keypoints.py
    test_mediapipe_detectors.py
    test_mediapipe_video.py
    test_multi_person_tracker.py
    test_precomputed_object_detector.py
    test_process_batch.py
    test_process_video.py
    test_rtmpose_detectors.py
    test_rtmpose_video.py
    test_run_batched.py
    test_temporal_processing.py
    test_track_association.py
    test_yolox_detector.py
    test_yolox_video.py
```

After Phase 4, the remaining old test files are:

| Test File | Status | Action |
|-----------|--------|--------|
| `conftest.py` | Modified in Phase 4 | Verify fixtures work with core/ |
| `test_execution_provider_catalog.py` | Kept | May need import path updates |
| `test_gpu_enumeration.py` | Kept | May need import path updates |
| `test_gpu_extra_resolver.py` | Kept | May need import path updates |
| `test_gpus_cli.py` | Kept | May need import path updates |
| `test_pyproject_cuda_requirements.py` | Kept | Probably fine |
| `test_trt_trx_provider.py` | Kept | May need import path updates |
| `test_docs_extra_names.py` | Kept | Probably fine |
| `test_extra_install.py` | Kept | Probably fine |
| `test_model_catalog.py` | Kept | May need import path updates |
| `test_tracker_task_events.py` | Kept | May need migration to core/ |
| `test_yolox_provider_matrix.py` | Kept | May need import path updates |

## Steps

### 5.0: Bring in Upstream Tests (Additive — Do NOT Replace)

The upstream tests must be added **without overwriting** the locally-modified `conftest.py` or the kept architecture-agnostic tests from Phase 4.

```powershell
# Fetch upstream test files into a temp location, then copy selectively
git show upstream/main:skellytracker/tests/conftest.py > skellytracker/tests/conftest_upstream.py.bak
# DO NOT overwrite conftest.py — it was modified in Phase 4

# Bring in upstream test files one by one (these don't conflict with local files)
$upstreamTests = @(
    "test_aruco_detector.py", "test_aruco_video.py",
    "test_charuco_detector.py", "test_charuco_video.py",
    "test_data_store.py", "test_keypoints.py",
    "test_mediapipe_detectors.py", "test_mediapipe_video.py",
    "test_multi_person_tracker.py", "test_precomputed_object_detector.py",
    "test_process_batch.py", "test_process_video.py",
    "test_rtmpose_detectors.py", "test_rtmpose_video.py",
    "test_run_batched.py", "test_temporal_processing.py",
    "test_track_association.py", "test_yolox_detector.py",
    "test_yolox_video.py"
)
foreach ($f in $upstreamTests) {
    git show "upstream/main:skellytracker/tests/$f" > "skellytracker/tests/$f"
    Write-Host "  + $f"
}

# Bring in upstream conftest fixtures selectively — read it, extract needed
# fixtures, and add them to the local conftest.py (don't replace wholesale)
```

Then review `conftest_upstream.py.bak` for any fixtures the upstream tests need that aren't in the local `conftest.py`, and add them. Remove the `.bak` file after.

These tests already target the `core/` architecture and should pass with minimal adjustments once `conftest.py` has the right fixtures.

### 5.1: Run Full Test Suite

```powershell
pytest skellytracker/tests/ -v --tb=short 2>&1 | Tee-Object -FilePath test_results.txt
```

Categorize failures into:
- **Import errors**: old `trackers.` imports that need updating to `core.`
- **Deleted tests**: tests that were supposed to be deleted but were missed
- **Architecture changes**: tests that need refactoring for new API shapes
- **Missing deps**: tests requiring optional dependencies not installed

### 5.2: Fix Import Paths

For each test with import errors, update imports:

| Old Import | New Import |
|-----------|-----------|
| `from skellytracker.trackers.base_tracker...` | `from skellytracker.core...` |
| `from skellytracker.utilities.gpu_utils.ort_session_utils import ...` | Check if moved to `core/sessions/ort_session_utils.py` |
| `from skellytracker.trackers.rtmpose_tracker...` | `from skellytracker.core.detectors.keypoint_detectors.rtmpose...` or `from skellytracker.core.sessions...` |

### 5.3: Fix conftest.py Fixtures

Ensure `conftest.py` fixtures provide the right data for `core/` architecture:

- Test image fixtures: should still work (they provide numpy arrays)
- Config fixtures: may need to create `TrackerConfig` / `DetectionStageConfig` instead of old config types
- Session fixtures: may need `OnnxSession` or `CpuSession` instead of old `RTMPoseSession`

### 5.4: Migrate Architecture-Agnostic Tests

These tests test concepts that still exist but with different APIs:

- **`test_tracker_task_events.py`**: Task events for pipeline timing. Check if upstream has equivalent in `core/`. If not, the task event system may need to be ported to `core/` or the test removed.
- **`test_execution_provider_catalog.py`**: EP catalog. Update imports to `core/sessions/execution_provider_name.py`.
- **`test_trt_trx_provider.py`**: TRT provider tests. Update to test new session architecture.
- **`test_yolox_provider_matrix.py`**: YOLOX provider matrix. Update imports.

### 5.5: Add New Core Architecture Tests

Identify gaps in test coverage for the new `core/` architecture. The upstream tests brought in during step 5.0 already cover many of these areas — run them first, then check for remaining gaps.

Key areas to verify coverage:
- `Tracker.create()` with config
- `DetectionStage.create()` with detectors
- `Tracker.process_image()` basic flow
- `Keypoints` data primitive (from names + coordinates, name lookup, visibility)
- `Observation` / `StageObservation` construction
- `DataStore` recording and serialization
- Session creation (OnnxSession, CpuSession)
- Registry: `build_keypoint_detector()`, `build_object_detector()`

### 5.6: Handle Skipped Tests

For tests that can't immediately pass (e.g., require GPU, require specific models), use `pytest.mark.skip` with a clear reason:

```python
@pytest.mark.skip(reason="Requires NVIDIA GPU with CUDA")
def test_cuda_session():
    ...
```

## Deliverables

- [ ] `pytest skellytracker/tests/ -v` passes with no unexpected failures
- [ ] All import paths updated from `trackers.` to `core.`
- [ ] `conftest.py` fixtures compatible with core/ architecture
- [ ] Architecture-agnostic tests migrated
- [ ] New tests cover core/ paths that lack coverage
- [ ] Skipped tests have clear skip reasons

## Verification

```powershell
# Full test run
pytest skellytracker/tests/ -v

# Check for any remaining old import paths
$refs = Select-String -Path "skellytracker\tests\*.py" -Pattern "skellytracker\.trackers"
if ($refs) { Write-Error "Old references remain: $refs" } else { Write-Host "OK: no old references" }

# Test coverage summary (if pytest-cov installed)
pytest skellytracker/tests/ --cov=skellytracker/core --cov-report=term-missing

# Run with expected skips only
pytest skellytracker/tests/ -v 2>&1 | Select-String -Pattern "PASSED|FAILED|SKIPPED|ERROR"
# FAILED and ERROR should be empty; SKIPPED only for hardware-dependent tests
```

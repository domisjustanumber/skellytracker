# Phase 4 — Remove Old trackers/ Structure and Migrate io/utilities/scripts

**Depends on:** Phase 1  
**Can run parallel with:** Phase 2, Phase 3  
**Estimated scope:** ~15 files deleted, ~10 files modified

## Goal

Delete the entire old `skellytracker/trackers/` directory and migrate ALL references to it across the codebase. This includes the `io/`, `utilities/`, and `scripts/` directories that have live imports from `trackers`. This is alpha code — no deprecation period, no backwards compatibility shims.

## Files with Live Tracker Imports (Found by Audit)

Before starting, a grep audit found these files with NON-commented imports from `skellytracker.trackers`:

| # | File | Risk | Action |
|---|------|------|--------|
| 1 | `skellytracker/process_folder_of_videos.py` | HIGH | **DELETE** — 10 live imports, all references to deleted trackers |
| 2 | `skellytracker/io/process_videos/process_single_video.py` | HIGH | **DELETE** — 5 live imports, directly constructs `MediapipeTracker` |
| 3 | `skellytracker/io/demo_viewers/webcam_demo_viewer.py` | HIGH | **DELETE** — 4 live imports (`BaseTracker`, `BrightestPointTracker`, `CharucoTracker`, `MediapipeTracker`) |
| 4 | `skellytracker/io/demo_viewers/image_demo_viewer.py` | MEDIUM | **DELETE** — `BaseTracker` type annotation |
| 5 | `skellytracker/scripts/blendshapes_to_csv.py` | MEDIUM | **DELETE** — `MediapipeBlendshapeTracker` from `v1/` |
| 6 | `skellytracker/utilities/gpu_utils/ort_session_utils.py` | MEDIUM | **MIGRATE** — imports `_make_nvidia_pip_dlls_discoverable_on_windows` from old `rtmpose_detector`. If `core/sessions/ort_session_utils.py` supersedes it, delete; otherwise move the DLL helper to a shared location |

## Steps

### 4.1: Delete trackers/ Directory

```powershell
Remove-Item -Recurse -Force skellytracker/trackers/
```

This removes all subpackages: `base_tracker/`, `brightest_point_tracker/`, `charuco_tracker/`, `composite_gpu_tracker/`, `legacy_mediapipe_tracker/`, `mediapipe_tracker/`, `rtmpose_tracker/`, `vitpose_tracker/`, `v1/`.

### 4.2: Delete Old io/ Files

The old `skellytracker/io/` directory (demo viewers, single-video processor) is superseded by `core/io/` (DemoManager, process_video). Delete the old files:

```powershell
Remove-Item -Force skellytracker/io/demo_viewers/image_demo_viewer.py -ErrorAction SilentlyContinue
Remove-Item -Force skellytracker/io/demo_viewers/webcam_demo_viewer.py -ErrorAction SilentlyContinue
Remove-Item -Force skellytracker/io/process_videos/process_single_video.py -ErrorAction SilentlyContinue
Remove-Item -Force skellytracker/io/process_videos/video_handler.py -ErrorAction SilentlyContinue
```

If `skellytracker/io/` is now empty (only `__init__.py` and `__pycache__/` remain), delete it:

```powershell
if ((Get-ChildItem skellytracker/io/ -Recurse -File | Measure-Object).Count -eq 0) {
    Remove-Item -Recurse -Force skellytracker/io/
}
```

### 4.3: Delete process_folder_of_videos.py

```powershell
Remove-Item -Force skellytracker/process_folder_of_videos.py
```

Superseded by `core/io/process_video.py` (which includes `process_folder`).

### 4.4: Delete scripts/blendshapes_to_csv.py

```powershell
Remove-Item -Force skellytracker/scripts/blendshapes_to_csv.py
```

Blendshape tracking from `v1/` has no equivalent in the new architecture. If blendshape support is needed later, it should be built against `core/` mediapipe face detector.

### 4.5: Handle utilities/gpu_utils/ort_session_utils.py

**Phase 0 confirmed:** `core/sessions/ort_session_utils.py` exists upstream with the same `build_tuned_ort_session`. The upstream `OnnxSession.create()` in `core/sessions/onnx_session.py` already handles NVIDIA DLL loading on Windows (`_load_nvidia_dlls_on_windows`). Therefore the old `utilities/gpu_utils/ort_session_utils.py` is **fully superseded** — delete it.

```powershell
# Delete old ORT session utilities
Remove-Item -Force skellytracker/utilities/gpu_utils/ort_session_utils.py
```

Check if `utilities/gpu_utils/` has any remaining files that aren't superseded by `core/sessions/`:

```powershell
Get-ChildItem skellytracker/utilities/gpu_utils/ -File | Select-Object Name
```

If the directory is empty or only contains files that are superseded (model_registry → core/sessions/model_registry.py, etc.), delete the entire directory:

```powershell
Remove-Item -Recurse -Force skellytracker/utilities/gpu_utils/
```

If any utilities remain that have no `core/` equivalent, keep them but update their imports to not reference deleted `trackers/` modules.

### 4.6: Update skellytracker/__init__.py

Remove all old tracker imports. The file currently has:

```python
__version__ = "v2024.09.1019"
from beartype.claw import beartype_this_package
beartype_this_package()

# Commented-out lazy imports for MediapipeHolisticTracker, YOLOPoseTracker, YOLOMediapipeComboTracker
# ... logging configuration ...
```

**Changes:**
- Keep `__version__` and `beartype_this_package()`
- Remove all commented-out lazy tracker imports
- Add imports from `core/` to re-export at the top level:
  ```python
  from skellytracker.core import (
      Tracker, TrackerConfig, TrackerState,
      Observation, Keypoints, KeypointDetector, ObjectDetector,
      Session, SessionConfig, process_video, process_folder,
  )
  ```

### 4.7: Delete Old Test Files

```powershell
Remove-Item -Force skellytracker/tests/test_brightest_point_tracker.py
Remove-Item -Force skellytracker/tests/test_charuco_tracker.py
Remove-Item -Force skellytracker/tests/test_composite_gpu_tracker.py
Remove-Item -Force skellytracker/tests/test_mediapipe_holistic_tracker.py
Remove-Item -Force skellytracker/tests/test_rtmpose_batch_size.py
Remove-Item -Force skellytracker/tests/test_rtmpose_config_backward_compat.py
Remove-Item -Force skellytracker/tests/test_rtmpose_model_override.py
Remove-Item -Force skellytracker/tests/test_rtmpose_session_create.py
Remove-Item -Force skellytracker/tests/test_rtmpose_session_predict_batch_timing.py
Remove-Item -Force skellytracker/tests/test_yolo_mediapipe_combo_tracker.py
Remove-Item -Force skellytracker/tests/test_yolo_object_tracker.py
Remove-Item -Force skellytracker/tests/test_yolo_pose_tracker.py
```

Keep tests that are architecture-agnostic:
- `test_execution_provider_catalog.py`
- `test_gpu_enumeration.py`
- `test_gpu_extra_resolver.py`
- `test_gpus_cli.py`
- `test_pyproject_cuda_requirements.py`
- `test_trt_trx_provider.py`
- `test_docs_extra_names.py`
- `test_extra_install.py`
- `test_model_catalog.py`
- `test_tracker_task_events.py` (may need migration in Phase 5)
- `test_yolox_provider_matrix.py`

### 4.8: Update conftest.py

`skellytracker/tests/conftest.py` downloads test images from Figshare and provides them as fixtures. Review and remove:

- Fixtures specific to deleted trackers (e.g., `charuco_test_image`, any tracker-specific config fixtures)
- Any imports from `skellytracker.trackers`
- Keep generic fixtures that can serve the new `core/` architecture

### 4.9: Update __main__.py

Rewire to use `core/` imports. The exact code depends on the `DemoManager` API discovered in Phase 0, but the pattern is:

```python
from skellytracker.core import Tracker, TrackerConfig
from skellytracker.core.io import DemoManager
# ... wire up webcam demo ...
```

### 4.10: Update pyproject.toml

- Remove any `console_scripts` or entry points referencing old trackers
- Verify `[project.scripts]` section only references `core/` paths

### 4.11: Scan for Lingering References

```powershell
# Find any remaining references to old trackers
Select-String -Path "skellytracker\*\*.py" -Pattern "skellytracker\.trackers" | Select-String -NotMatch "__pycache__"
Select-String -Path "skellytracker\*\*.py" -Pattern "from.*trackers import"
Select-String -Path "skellytracker\*\*.py" -Pattern "import.*trackers"
```

Fix or remove any remaining references.

## Relevant Files

| File | Action |
|------|--------|
| `skellytracker/trackers/` | **DELETE** entire directory |
| `skellytracker/io/demo_viewers/*.py` | **DELETE** (superseded by `core/io/demo_manager.py`) |
| `skellytracker/io/process_videos/process_single_video.py` | **DELETE** (superseded by `core/io/process_video.py`) |
| `skellytracker/process_folder_of_videos.py` | **DELETE** (superseded by `core/io/process_video.py`) |
| `skellytracker/scripts/blendshapes_to_csv.py` | **DELETE** (no equivalent in new architecture) |
| `skellytracker/utilities/gpu_utils/ort_session_utils.py` | **DELETE or MIGRATE** (see Phase 0 findings) |
| `skellytracker/__init__.py` | Remove old imports, add core re-exports |
| `skellytracker/__main__.py` | Rewrite to use core/ |
| `skellytracker/tests/conftest.py` | Remove old tracker fixtures |
| `skellytracker/tests/test_*_tracker.py` | **DELETE** old tracker tests |
| `skellytracker/tests/test_rtmpose_*.py` | **DELETE** old RTMPose tests |
| `skellytracker/tests/test_yolo_*.py` | **DELETE** old YOLO tests |
| `pyproject.toml` | Remove old entry points |

## Deliverables

- [ ] `skellytracker/trackers/` directory does not exist
- [ ] Old `io/` demo files deleted
- [ ] `process_folder_of_videos.py` deleted
- [ ] `scripts/blendshapes_to_csv.py` deleted
- [ ] `utilities/gpu_utils/ort_session_utils.py` resolved (deleted or migrated)
- [ ] No imports from `skellytracker.trackers` anywhere in codebase
- [ ] Old tracker-specific tests deleted
- [ ] `__init__.py` updated with core/ exports
- [ ] `__main__.py` rewritten for core/
- [ ] `pyproject.toml` entry points updated

## Verification

```powershell
# Confirm trackers/ is gone
if (Test-Path skellytracker/trackers/) { Write-Error "trackers/ still exists" } else { Write-Host "OK: trackers/ removed" }

# Confirm no lingering references
$results = Select-String -Path "skellytracker\*\*.py" -Pattern "skellytracker\.trackers" | Where-Object { $_ -notmatch "__pycache__" }
if ($results) { Write-Error "Lingering references found: $results" } else { Write-Host "OK: no tracker references" }

# Confirm core imports work
python -c "from skellytracker import __version__; print(__version__)"
python -c "from skellytracker.core import Tracker; print('OK')"
```

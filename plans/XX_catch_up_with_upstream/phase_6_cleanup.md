# Phase 6 — Clean Up and Document

**Depends on:** Phase 5  
**Can run parallel with:** — (final phase)  
**Estimated scope:** ~3-5 files

## Goal

Final polish: update documentation, fix demo entry points, run lint/format, and verify the package installs and runs correctly end-to-end.

## Steps

### 6.1: Update CLAUDE.md

Rewrite `CLAUDE.md` to reflect the new `core/` architecture. Key sections to update:

- **Commands section**: Update demo commands to use new entry points
- **Architecture section**: Replace old Tracker→Detector/Annotator/Recorder pattern with new Tracker→DetectionStage→ObjectDetector+KeypointDetector pattern
- **Canonical data types**: Replace `PointCloud` with `Keypoints`, `BaseObservation` with `Observation`/`StageObservation`
- **YAML-driven tracker schema**: Update to reference new `_schema_loader.py` path
- **Tracker implementations table**: Replace with new detector registry table
- **GPU/ONNX Runtime section**: Update session paths to `core/sessions/`

### 6.2: Fix __main__.py and Demo Entry Points

`skellytracker/__main__.py` was flagged as broken even before this restructure. Rewrite it to work with the new architecture:

- Import `Tracker`, `TrackerConfig`, `DemoManager` from `core/`
- Support CLI argument to select tracker type (or use default)
- Wire up webcam demo via `DemoManager`

Also check for any other entry points:
- `skellytracker/scripts/gpus_cli.py` — verify still works with core/ paths
- Any `run_demo.py` scripts in `core/detectors/` — these are upstream demos, ensure they don't import old trackers

### 6.3: Update pyproject.toml

- Verify `[project.scripts]` section has correct entry points
- Ensure `[tool.uv].conflicts` and `exclude-dependencies` are still correct
- Check that extras still resolve: `rtmpose-nvidia`, `rtmpose-trt`, `rtmpose-trt-rtx`, `rtmpose-directml`, `recommended`

### 6.4: Run Lint and Format

```powershell
# Lint
ruff check skellytracker/

# Format
black skellytracker/
isort skellytracker/

# Type check (if mypy is configured)
mypy skellytracker/
```

Fix any issues:
- Unused imports (likely from deleted trackers)
- Import ordering (isort)
- Line length and style (black)
- Lint violations (ruff)

### 6.5: Verify Package Installation

```powershell
# Clean install
uv sync --extra recommended

# Verify import
python -c "from skellytracker import __version__; print(f'Version: {__version__}')"

# Verify core imports
python -c @"
from skellytracker.core import (
    Tracker, TrackerConfig, TrackerState,
    DetectionStage, DetectionStageConfig,
    Observation, StageObservation, Keypoints,
    Session, SessionConfig,
    process_video
)
print('All core imports OK')
"@
```

### 6.6: End-to-End Smoke Test

If a camera is available:

```powershell
# Webcam demo (quick smoke test — Ctrl+C after a few seconds)
python -m skellytracker
```

If no camera, test with an image file:

```powershell
python -c @"
from skellytracker.core import Tracker, TrackerConfig, DetectionStageConfig
# Create a minimal tracker and run on a test image
# ... (exact code depends on new API)
"@
```

### 6.7: Update Plans Directory

Add a note to `plans/00_plan_summary.md` documenting that this restructuring plan has been completed, and that plans 40-70 should now target the `core/` architecture.

## Relevant Files

| File | Action |
|------|--------|
| `CLAUDE.md` | Rewrite architecture docs |
| `skellytracker/__main__.py` | Rewrite demo entry point |
| `skellytracker/scripts/gpus_cli.py` | Verify still works |
| `pyproject.toml` | Verify scripts and extras |
| `plans/00_plan_summary.md` | Add completion note |

## Deliverables

- [ ] `CLAUDE.md` updated with new architecture docs
- [ ] `__main__.py` functional with core/ imports
- [ ] All demo/CLI entry points working
- [ ] Lint + format pass clean
- [ ] `uv sync --extra recommended` succeeds
- [ ] Package imports correctly
- [ ] End-to-end smoke test passes

## Verification

```powershell
# Lint and format
ruff check skellytracker/
black --check skellytracker/
isort --check skellytracker/

# Install and import
uv sync --extra recommended
python -c "from skellytracker.core import Tracker, TrackerConfig; print('OK')"

# Run full test suite
pytest skellytracker/tests/ -v

# Final scan for any old references
$refs = Select-String -Path "skellytracker\*\*.py" -Pattern "skellytracker\.trackers" | Where-Object { $_ -notmatch "__pycache__" }
if ($refs) { Write-Error "Old references remain: $refs" } else { Write-Host "OK: no old references" }

# Check for TODO/FIXME comments related to migration
Select-String -Path "skellytracker\core\*\*.py" -Pattern "TODO|FIXME|HACK|XXX" | Select-String -Pattern "migration|port|tracker" -SimpleMatch
# Address any remaining migration TODOs
```

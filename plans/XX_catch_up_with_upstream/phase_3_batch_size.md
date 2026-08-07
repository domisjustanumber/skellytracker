# Phase 3 — Port Plan 30 Invariants (batch_size Semantics)

**Depends on:** Phase 1 (Phase 0 confirmed: `OnnxSessionConfig.batch_size` already exists, `build_tuned_ort_session` still uses `max_batch_size`, TRT profiles still range 1..N, no `BatchSizeMismatchError`)  
**Can run parallel with:** Phase 2, Phase 4  
**Estimated scope:** 2 files modified in `core/sessions/`

## Goal

Finish the batch_size migration that upstream partially completed. `OnnxSessionConfig` already uses `batch_size` but `build_tuned_ort_session` still has `max_batch_size` parameter and range-based TRT profiles (min=1, opt=N, max=N). Add exact-batch validation and `BatchSizeMismatchError`.

## Context — Phase 0 Findings

| What | Upstream Status | Plan 30 Target |
|------|----------------|----------------|
| Config field name | `batch_size` ✅ | `batch_size` ✅ (already done) |
| Default value | Required (no default) | `1` (different — add default) |
| ORT utility param | `max_batch_size` ❌ | `batch_size` (rename needed) |
| TRT profiles | min=1, opt=N, max=N ❌ | min=N, opt=N, max=N (pin needed) |
| Warmup | Single at `batch_size` ✅ | Single at `batch_size` ✅ (already done) |
| `batch_size` property | On `OnnxSession` ✅ | On session ✅ (already done) |
| Exact-batch validation | None ❌ | `BatchSizeMismatchError` (add) |
| `BatchSizeMismatchError` | Doesn't exist ❌ | Create |

## Steps

### 3.1: Add Default to OnnxSessionConfig.batch_size

Currently `batch_size: int` (required, no default). Add:

```python
batch_size: int = Field(default=1, ge=1)
```

The existing `_batch_size_positive` validator can be **removed** — `Field(ge=1)` handles the same constraint natively via Pydantic.

### 3.2: Rename max_batch_size in build_tuned_ort_session

In `core/sessions/ort_session_utils.py`:

- Rename parameter `max_batch_size` → `batch_size` in `build_tuned_ort_session()` signature
- Update the call site in `OnnxSession.create()` (already passes `max_batch_size=config.batch_size`)

### 3.3: Rename in _trt_dynamic_batch_profile

- Rename parameter `max_batch_size` → `batch_size` in `_trt_dynamic_batch_profile()`
- Pin profiles: change `min=1` to `min=batch_size`

```python
# Before
min_str = f"{name}:1x{fixed_str}"

# After
min_str = f"{name}:{batch_size}x{fixed_str}"
```

### 3.4: Add BatchSizeMismatchError

In `core/sessions/session_errors.py`:

```python
class BatchSizeMismatchError(ValueError):
    """Raised when input batch size doesn't match session batch_size."""
```

Add to `core/__init__.py` exports.

### 3.5: Add Exact-Batch Validation (if predict_batch exists)

If the upstream `OnnxSession` or detectors have a `predict_batch` or `run_batched` method, add validation:

```python
if len(inputs) != self.batch_size:
    raise BatchSizeMismatchError(
        f"Expected {self.batch_size} inputs, got {len(inputs)}"
    )
```

If no batched inference method exists yet (Phase 0 confirmed none found), skip this step — it will be added when the realtime pipeline integrates multi-camera batching.

### 3.6: Add/Update Tests

- `batch_size` default is `1`
- `max_batch_size` no longer appears in `build_tuned_ort_session` signature
- TRT profiles have min=opt=max
- `BatchSizeMismatchError` importable

## Relevant Files

| File | Action |
|------|--------|
| `skellytracker/core/config/session_config.py` | Add `Field(default=1, ge=1)` to `batch_size` (if OnnxSessionConfig is here — check; may be in `onnx_session.py`) |
| `skellytracker/core/sessions/onnx_session.py` | Update `batch_size` default if defined here; update `build_tuned_ort_session` call |
| `skellytracker/core/sessions/ort_session_utils.py` | Rename `max_batch_size` → `batch_size`; pin TRT min profile |
| `skellytracker/core/sessions/session_errors.py` | Add `BatchSizeMismatchError` |
| `skellytracker/core/__init__.py` | Export `BatchSizeMismatchError` |

## Deliverables

- [ ] `batch_size` has default `1` on `OnnxSessionConfig`
- [ ] `max_batch_size` parameter removed from `build_tuned_ort_session` and `_trt_dynamic_batch_profile`
- [ ] TRT profiles: min=opt=max=batch_size
- [ ] `BatchSizeMismatchError` defined and exported

## Verification

```powershell
# Verify max_batch_size removed from ORT utility
Select-String -Path "skellytracker\core\sessions\ort_session_utils.py" -Pattern "max_batch_size"
# Should return nothing

# Verify batch_size default
python -c "from skellytracker.core.sessions.onnx_session import OnnxSessionConfig; c = OnnxSessionConfig(models=[]); print(c.batch_size)"
# Should print 1

# Verify BatchSizeMismatchError
python -c "from skellytracker.core import BatchSizeMismatchError; print('OK')"
```

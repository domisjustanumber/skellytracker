# Phase 2 — Port Plan 10 Invariants (Strict ORT Sessions)

**Depends on:** Phase 1 (Phase 0 confirmed: `require_provider()` already strict, but `build_tuned_ort_session()` still has fallback chaining)  
**Can run parallel with:** Phase 3, Phase 4  
**Estimated scope:** 2-3 files modified in `core/sessions/`

## Goal

Remove the fallback provider chaining from `build_tuned_ort_session()` in `core/sessions/ort_session_utils.py`. The upstream already has `require_provider()` (raises `SessionCreationError` with no fallback) and `auto_detect_provider()`, but the session builder still appends CPU fallback behind every GPU provider. Add `OnnxExecutionProviderStartupError` as a subclass of `SessionCreationError` with structured fields.

## Context — Phase 0 Findings

The upstream `ort_session_utils.py` has this split:

| Function | Behavior | Status |
|----------|----------|--------|
| `require_provider(requested)` | Raises `SessionCreationError` if EP unavailable — no fallback | ✅ Already strict |
| `auto_detect_provider()` | Probes TRT → CUDA → CoreML → CPU | ✅ Legitimate auto-detect |
| `resolve_provider()` | Deprecated shim with fallback | ⚠️ Deprecated, can ignore |
| `build_tuned_ort_session()` | Appends CPU behind TRT/CUDA/CoreML/DirectML | ❌ **Needs fix** |

The `SessionCreationError` already has this docstring: *"There is no fallback — FMC should surface this to the user so they can pick a different EP."* So the philosophy matches Plan 10 — only the implementation in `build_tuned_ort_session` lags behind.

## Steps

### 2.1: Add OnnxExecutionProviderStartupError

In `core/sessions/session_errors.py`, add as a subclass of `SessionCreationError`:

```python
class OnnxExecutionProviderStartupError(SessionCreationError):
    """Session creation failed because the requested EP could not be activated.

    Differs from the base SessionCreationError by carrying structured fields
    so FMC can show targeted UI messages (e.g., "CUDA not available — install
    onnxruntime-gpu or switch to CPU").
    """
    def __init__(
        self,
        *args,
        model_label: str,
        requested_provider: str,
        expected_ort_provider: str,
        active_ort_providers: list[str] | None = None,
        device_id: int | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.model_label = model_label
        self.requested_provider = requested_provider
        self.expected_ort_provider = expected_ort_provider
        self.active_ort_providers = active_ort_providers or []
        self.device_id = device_id
```

Export from `core/sessions/session_errors.py` (already exported via `core/__init__.py`).

### 2.2: Remove Fallback from build_tuned_ort_session

In `core/sessions/ort_session_utils.py`, modify provider list construction:

| Provider | Before (fallback) | After (strict) |
|----------|------------------|----------------|
| `trt` | TRT → CUDA → CPU | TRT only |
| `cuda` | CUDA → CPU | CUDA only |
| `coreml` | CoreML → CPU | CoreML only |
| `directml` | DirectML → CPU | DirectML only |
| `cpu` | CPU | CPU (unchanged) |

After `InferenceSession` construction, verify the active provider matches the requested EP. If not, raise `OnnxExecutionProviderStartupError`.

```python
actual = session.get_providers()
expected = _PROVIDER_EP_NAME[provider]
if expected not in actual:
    raise OnnxExecutionProviderStartupError(
        f"Requested {provider!r} but ORT activated {actual}",
        model_label=log_label,
        requested_provider=provider,
        expected_ort_provider=expected,
        active_ort_providers=list(actual),
        device_id=device_id,
    )
```

This replaces the current log-only verification that reports the active provider but doesn't fail on mismatch.

### 2.3: Update OnnxSession.create()

`OnnxSession.create()` already calls `require_provider()` for explicit EPs. It passes `active_provider` to `build_tuned_ort_session()`. Wrap the session creation in a try/except that catches ORT errors and re-raises as `OnnxExecutionProviderStartupError` with structured fields.

### 2.4: Handle YOLOX Detector Special Case

If the YOLOX object detector intentionally maps TRT → CUDA (model constraint, not fallback), preserve this in the detector's own session construction, but ensure the resulting CUDA session has no CPU fallback from `build_tuned_ort_session`.

### 2.5: Add/Update Tests

- `build_tuned_ort_session(provider="cuda")` → single `CUDAExecutionProvider` entry
- `build_tuned_ort_session(provider="trt")` → single `TensorrtExecutionProvider` entry
- Post-create provider mismatch raises `OnnxExecutionProviderStartupError`
- `require_provider("nonexistent")` raises `SessionCreationError` (already exists, verify)

## Relevant Files

| File | Action |
|------|--------|
| `skellytracker/core/sessions/ort_session_utils.py` | Remove fallback appending in `build_tuned_ort_session` |
| `skellytracker/core/sessions/session_errors.py` | Add `OnnxExecutionProviderStartupError` subclass |
| `skellytracker/core/sessions/onnx_session.py` | Wrap ORT errors in structured exception |
| `skellytracker/core/__init__.py` | Export `OnnxExecutionProviderStartupError` (add to the existing `from skellytracker.core.sessions.session_errors import ...` line) |

## Deliverables

- [ ] `build_tuned_ort_session` produces single-provider lists
- [ ] `OnnxExecutionProviderStartupError` defined as subclass of `SessionCreationError`
- [ ] `OnnxExecutionProviderStartupError` exported from `core/__init__.py`
- [ ] Post-create provider verification active
- [ ] No fallback config parameters exist

## Verification

```powershell
# Verify OnnxExecutionProviderStartupError is importable
python -c "from skellytracker.core.sessions.session_errors import OnnxExecutionProviderStartupError; print('OK')"

# Verify no fallback CPU in CUDA/TRT paths
Select-String -Path "skellytracker\core\sessions\ort_session_utils.py" -Pattern "CPUExecutionProvider"
# Should only appear in the `else: providers.append("CPUExecutionProvider")` cpu-only branch
```

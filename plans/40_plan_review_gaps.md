---
name: Plan 40 Review — Issues and Gaps
overview: Findings from a thorough review of the updated plan 40 (Pydantic-based Model Sidecar Spec) against consistency, completeness, and correctness.
isProject: false
---

# Plan 40 Review: Issues & Gaps

## Summary

**Severity legend:** 🔴 Must fix (blocker) | 🟡 Should fix (quality/consistency) | 🟢 Nice-to-have

---

## 🔴 1. Dead code: `SidecarIdentity` class

The Pydantic hierarchy defines `SidecarIdentity(BaseModel)` with `schema_version`, `model_id`, `display_name`, `family`, `role` — but `SidecarModel` duplicates all these fields directly. `SidecarIdentity` is never used.

**Fix:** Either remove `SidecarIdentity` or have `SidecarModel` compose it. Composing is cleaner:
```python
class SidecarModel(BaseModel):
    identity: SidecarIdentity
    onnx: OnnxConfig | None = None
    ...
```
But this changes the YAML structure (adds an `identity:` nesting). Simpler fix: delete `SidecarIdentity`.

---

## 🔴 2. Implementation plan steps still reference old API

Steps 1, 2, 3, and 3b all describe the old `SCHEMA_REQUIREMENTS` / `validate_*()` approach, contradicting the Pydantic redesign:

| Step | Current (wrong) | Should be |
|------|-----------------|-----------|
| **1** | "Add `parse_skellytracker_version`, `sidecar_schema_supported`, and `SCHEMA_REQUIREMENTS`" | "Add `parse_skellytracker_version` (free function); version gating via `@model_validator` on `SidecarModel`" |
| **2** | "Add `validate_batch_artifacts()` and `_require_batch_artifacts_when_onnx_present` to `SCHEMA_REQUIREMENTS`" | "`OnnxConfig` Pydantic model covers structural validation; `multi_batch_requires_shapes` validator covers per-group shapes" |
| **3** | "Add `_require_interpolation_when_resize_present` to `SCHEMA_REQUIREMENTS`" | "`ResizeConfig.interpolation` is non-optional; no separate validator needed" |
| **3b** | "Add `validate_normalization()` and `_require_normalization_when_input_present` to `SCHEMA_REQUIREMENTS`" | "`InputConfig.normalization` is non-optional (`Normalization` union); Pydantic catches missing/invalid" |

---

## 🔴 3. `validation-tests` todo still references old function names

The todo item says:
> "Unit-test ... `validate_sidecar_metadata`, `validate_batch_artifacts`"

These functions no longer exist in the Pydantic design. Should say:
> "Unit-test `SidecarModel.model_validate()`, `OnnxConfig` validation, `multi_batch_requires_shapes` validator"

---

## 🔴 4. Runtime batch selection still references old API

Line 226:
> "Add `sidecar_supports_runtime_batch(sidecar: dict, batch_size: int) -> bool` (or equivalent)"

The Pydantic model has `sidecar.supports_runtime_batch(n)` as a method. The description should be updated to reference the model method.

---

## 🔴 5. Validation plan for plan 50/60 references old functions

- **Plan 50** (line ~1100): "Unit-test `SidecarModelRegistry` scans `*.yaml` and calls `validate_sidecar_metadata`" → should say "calls `SidecarModel.model_validate()`" or "calls `load_sidecar()`"
- **Plan 60** (line ~1095): "Unit-test `validate_batch_conversion_profile()`" → should reference Pydantic `BatchingConversionConfig` model validation

---

## 🔴 6. Change sets intro references `SCHEMA_REQUIREMENTS`

Line 829:
> "add a `SCHEMA_REQUIREMENTS` entry, and bump example sidecars"

Should say:
> "add a `@model_validator` method or Pydantic field to `SidecarModel`, and bump example sidecars"

---

## 🔴 7. Main risks references `SCHEMA_REQUIREMENTS`

Line ~1115:
> "every spec edit must bump `schema_version`, add a `SCHEMA_REQUIREMENTS` entry, update the changelog table"

Should say:
> "every spec edit must bump `schema_version`, add a `@model_validator` method or Pydantic field, update the changelog table"

---

## 🔴 8. Version-gated validator example has broken version comparison

The Pydantic code shows:
```python
_PLAN_40_SCHEMA_VERSION = "vYYYY.MM.BBBB"

@model_validator(mode="after")
def _require_interpolation_when_resize_present(self):
    if self.schema_version < _PLAN_40_SCHEMA_VERSION:  # ❌ string compare!
        return self
```

Calendar version strings like `"v2024.09.1019"` cannot be reliably compared with `<`. Must use `parse_skellytracker_version()`:
```python
@model_validator(mode="after")
def _require_interpolation_when_resize_present(self):
    sidecar_ver = parse_skellytracker_version(self.schema_version)
    required_ver = parse_skellytracker_version(_PLAN_40_SCHEMA_VERSION)
    if sidecar_ver < required_ver:
        return self  # older sidecar — skip this requirement
    ...
```

---

## 🔴 9. `version_not_newer_than_installed` uses undefined `_get_installed_skellytracker_version()`

The validator calls a helper that is never defined or documented in the plan. Must document that this reads from `skellytracker.__version__`:
```python
def _get_installed_skellytracker_version() -> str:
    from skellytracker import __version__
    return __version__
```

---

## 🟡 10. `PostprocessingConfig` missing `nms_thr` and `score_thr`

The YAML example doesn't need them (YOLO26 has `requires_nms: false`), but RTMO (plan 70) needs `nms_thr` and `score_thr`. The Pydantic model should include optional fields:
```python
class PostprocessingConfig(BaseModel):
    requires_nms: bool = False
    nms_thr: float | None = None        # required when requires_nms=true
    score_thr: float | None = None       # required when requires_nms=true
    ...
```

---

## 🟡 11. `OutputTensor` missing `score_field` and `class_field`

The YAML example has `score_field: score` and `class_field: class_id` but the Pydantic model only has `fields: list[str] | None`. These individual field names are metadata for consumers that unpack packed detections — they should be on the model:
```python
class OutputTensor(BaseModel):
    fields: list[str] | None = None
    score_field: str | None = None     # field name containing confidence
    class_field: str | None = None     # field name containing class ID
```

---

## 🟡 12. `SidecarModel` defines `schema_version` pattern in two places

`SidecarIdentity` has `schema_version: str = Field(pattern=r"^v?\d{4}\.\d{2}\.\d{4}$")` and `SidecarModel` also has the same field with the same pattern. If `SidecarIdentity` is removed (issue #1), this resolves itself.

---

## 🟡 13. `on_` → `onnx` inconsistency in the YAML cross-reference

The boundary table references are fine, but in the Plans table, plan 70 references use markdown anchor links like `#pose-sidecar-referencing-names_and_connections`. No `on_` typos noted.

---

## 🟡 14. `Normalization` discriminated union — needs `Annotated` for proper Pydantic v2 discrimination

The current `Normalization = NamedNormalizationMode | CustomNormalization` works in simple cases but may produce confusing error messages when validation fails. For best results in Pydantic v2:
```python
from typing import Annotated
from pydantic import Field, TypeAdapter

Normalization = Annotated[
    NamedNormalizationMode | CustomNormalization,
    Field(discriminator="mode"),
]
```
However, Pydantic only auto-discriminates on `Union[BaseModel, BaseModel]`, not `Union[str, BaseModel]`. The string union case works because Pydantic tries the string first — if it matches a `Literal`, it wins. If it doesn't, it tries the model. This is fine in practice for this use case.

---

## 🟢 15. Validation checklist section still references `SCHEMA_REQUIREMENTS`

Line ~500: "human-readable mirror of `SCHEMA_REQUIREMENTS`" → should say "human-readable mirror of Pydantic validators"

---

## 🟢 16. `__init__.py` export hasn't been updated

The plan doesn't explicitly document what `skellytracker/utilities/gpu_utils/__init__.py` should export from `sidecar_validation.py`. Plan 50 mentions exporting for `SidecarModelRegistry` but plan 40 should specify at least: `SidecarModel`, `load_sidecar`, `parse_sidecar_file`.

---

## 🟢 17. No `resolve_precision()` helper

The plan has `resolve_resize_interpolation()` and `resolve_normalization_mode()` but no helper for selecting which precision artifact to use from `onnx.batch_artifacts[N].precision_artifacts`. The `native_batch_sizes` property and `supports_runtime_batch()` exist, but precision selection is implicit. This is likely plan 50's job, but worth flagging.

---

## 🟢 18. `BatchingConfig` has no `batch_conversion` field yet

This is intentional (plan 60), but the model should have a placeholder or comment noting where plan 60 adds it:
```python
class BatchingConfig(BaseModel):
    batch_axis: int = 0
    supports_dynamic_batch: bool = False
    # batch_conversion: BatchingConversionConfig | None = None  # plan 60
```

---

## 🟢 19. No error message format guidance

When `SidecarModel.model_validate()` fails, `pydantic.ValidationError` provides field paths and error messages. The plan doesn't specify how plan 50's `SidecarModelRegistry` should format these for user-facing error messages (e.g., include `model_id` and file path). This is a plan 50 concern but should be noted.

---

## 🟢 20. `parse_sidecar_file()` return type unchanged

It still returns `dict` — but consumers should call `load_sidecar()` which returns `SidecarModel`. The raw `parse_sidecar_file()` is only for scenarios where partial parsing is needed. The plan makes this clear in the Pydantic model section but the old description still says "returns dict".

---

## Action Items Summary

| # | Severity | Issue | Section |
|---|----------|-------|---------|
| 1 | 🔴 | Remove dead `SidecarIdentity` class | Pydantic model hierarchy |
| 2 | 🔴 | Update Implementation steps 1, 2, 3, 3b | Implementation plan |
| 3 | 🔴 | Update `validation-tests` todo | Frontmatter todos |
| 4 | 🔴 | Update runtime batch selection description | Runtime batch selection |
| 5 | 🔴 | Update Validation plan Plan 50/60 entries | Validation plan |
| 6 | 🔴 | Update Change sets intro | Change sets |
| 7 | 🔴 | Update Main risks | Main risks |
| 8 | 🔴 | Fix version comparison in Pydantic example | Version-gated requirements |
| 9 | 🔴 | Document `_get_installed_skellytracker_version()` | Pydantic model hierarchy |
| 10 | 🟡 | Add `nms_thr`/`score_thr` to `PostprocessingConfig` | Pydantic model hierarchy |
| 11 | 🟡 | Add `score_field`/`class_field` to `OutputTensor` | Pydantic model hierarchy |
| 15 | 🟢 | Update validation checklist description | Spec document updates |

# 8Z5Q — `onnx` is a base dependency

**Status:** absorbed into [`pyproject.toml`](../../pyproject.toml), [`test_dependency_pins.py`](../../tools/tests/test_dependency_pins.py), 2026-11-18 (user; PR: pending).

## Decision

1. `onnx` is a base dependency of skellytracker in `dependencies` of `pyproject.toml`, with the
   exact pin `onnx==1.22.0`. The exact-pin rule of
   [ADR-M2C6](M2C6-exact-pins-and-one-python-patch-release.md) item 1 applies.
2. The extra `onnx` is removed. No extra is `onnx`.
3. `tools/tests/test_dependency_pins.py` checks items 1 and 2.

## Reason

The package builds the preprocess graph at run time: the resize step and the normalization of one
sidecar as ONNX nodes (`core/detectors/processing/pre/graph.py`). It makes the graph with
`onnx.helper`. Thus a host with only the base dependencies must have `onnx`
([Interpolation](../../specs/model-sidecar/pre/interpolation.md#implementer-guidance)).
The batch conversion `model_batch_convert` also needs `onnx`. With a base dependency, each host can
convert a b3 artifact.

## Consequences

- The pin stays at 1.22: onnx 1.23 writes IR version 14, and onnxruntime 1.30 reads IR version 13
  or lower.
- `pip install skellytracker[onnx]` gives a warning, because the extra is gone.

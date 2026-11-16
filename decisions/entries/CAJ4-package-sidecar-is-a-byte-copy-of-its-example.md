# CAJ4 — A package sidecar is a byte copy of its reference example

**Status:** absorbed into [`sidecar_trace.py`](../../tools/sidecar_trace.py), [`skellytracker/AGENTS.md#layout`](../../skellytracker/AGENTS.md#layout), 2026-11-16 (stage 1.9 of the implementation plan; PR: pending).

## Decision

1. **Byte copy.** A package sidecar in `skellytracker/core/model_zoo/detectors/` that has the key of
   a reference example must have the bytes of that example. The example is the source. To change
   the package sidecar, change the example with the procedure of the spec, then copy the file.
2. **One model.** `tools/sidecar_trace.py` reads the two files as one model with the root
   `example, package`. The file of that model is the example.
3. **The check.** Different bytes are an error of `tools/sidecar_trace.py` that names the two files.
4. **No example.** A package sidecar with no example has the root `package`. It must hold
   `source.name`.

This entry adds no rule to [ADR-AMJ8](AMJ8-replace-package-onnx-detectors.md). Its item 5 gives the
folder of the package sidecars. It does not give their relation to the examples.

## Reason

- Stage 1.9 of the
  [implementation plan](../../specs/sidecar-implementation-plan.md#19-the-first-new-models-was-n5)
  put `yolox-person` and `rtmw-wholebody133` in the package as byte copies. The rule was only in the
  plan and in the tool docstring. A decision that code refers to must be in an entry
  ([Rules](../README.md#rules)).
- The exporter writes each example, and its provenance is in `inventory.yaml`. A package sidecar
  with other bytes is a second sidecar of the same key with no provenance.
- A byte check needs no parser and no list of the keys that can differ.

## Consequences

- A change of an example must copy the file to the package in the same commit, or the trace tool
  fails.
- `.gitattributes` must not change the line ends of one of the two files only.

## Evidence

- `tools/sidecar_trace.py`, function `_same_model`: it compares `read_bytes()` of the two files and
  raises `TraceError`.

## Alternatives rejected

- One file, with the package reading the example folder. The wheel does not hold `specs/`.
- A comparison of the parsed YAML. It lets a comment or a key order differ, and the `sha256` of a
  sidecar that a pipeline pins is a hash of the bytes.

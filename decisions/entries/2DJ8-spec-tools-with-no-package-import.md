# 2DJ8 — The spec tools import no package code, and the specs move to the repository `skellyspecs`

**Status:** accepted, 2026-11-23 (user).

## Decision

1. **The move.** The sidecar spec (`specs/model-sidecar/`), the pipeline spec (`specs/pipeline/`)
   and the exporter guide move to the repository `skellyspecs`, in the folders `model-sidecars`,
   `tracker-pipelines` and `exporter-guide`. The tools that check the specs move with them.
   skellytracker reads the specs from a sibling checkout `../skellyspecs` at a commit that a
   tracked file pins. A spec change lands in `skellyspecs` first. Then the pin moves here. The spec
   version stays the skellytracker version. `intakes/` stays in skellytracker. This entry prepares
   the move. It moves no spec file.
2. **The bundle tool has two parts.** `tools/intake_bundle.py` holds `pack`, `list`, the format
   checks of `verify` and `record`. It moves. `tools/intake_gate.py` holds `batch` and the load
   findings. It stays. `verify` of the gate tool is `verify` of the bundle tool plus the load
   findings. The gate tool gives the package sidecar root to `verify` (`package_sidecars`). The
   bundle tool names no path of the package.
3. **A moving tool imports no package code.** The whole import chain of each moving tool imports no
   `skellytracker`, no `onnx` and no `onnxruntime`, also in a function body.
   `tools/tests/test_intake_gate.py` checks it, and it holds the reviewed list of the dynamic
   imports of the moving tools.
4. **`verified_against`.** The vector tool checks an entry of the form
   `skellytracker/<path>.py::<function>` for its form only. A skellytracker test,
   `tools/tests/test_package_verified_against.py`, checks that each such entry of each vector file
   names a function of the package.
5. **The trace tool.** `tools/sidecar_trace.py` takes the sidecar resolver and the package root as
   parameters. `tools/sidecar_trace_package.py` stays in skellytracker and gives them. Each command
   of the trace tool runs through it here. The selector code has its lead copy in the spec,
   `specs/model-sidecar/reference/sidecar_normalize.py`. The package keeps its copy
   `skellytracker/core/model_spec/sidecar_normalize.py`. A skellytracker test,
   `tools/tests/test_sidecar_normalize.py`, fails when the code of the two copies differs. It
   ignores the module docstring.
6. **Reference files.** skellytracker tracks the byte copy of the `parity/` files of a `model`
   bundle in `skellytracker/tests/sidecar/fixtures/parity/<model_id>/`. This replaces the path
   `specs/model-sidecar/parity/<model_id>/` of
   [ADR-T41E](T41E-reference-files-of-a-model-bundle.md) item 1. The format and the gate of the
   reference files move with the spec. `skellyspecs` gets one made-up sample of the format.
7. **`--root`.** In `skellyspecs`, the bundle tool requires `--root`. It has no default path into
   another repository.

## Reason

- A tool in `skellyspecs` runs where the package is not installed.
- Only skellytracker can know that a function of its package exists.
- The package cannot import a file of a sibling checkout at run time. Thus the selector code has
  two copies. The copy of the spec leads, because a spec change lands there first.
- The reference files follow one exported ONNX file and the package code. They do not follow the
  spec text.

## Consequences

- `verify` and `land` of the vector tool no longer report an entry that names no function. The
  skellytracker test reports it.
- `tools/sidecar_trace.py matrix` stops with status 2 when no resolver is given. The command here
  is `tools/sidecar_trace_package.py matrix`.
- These decided texts name a command or a function at its old place. They stay as written:
  [ADR-AD33](AD33-bundles-are-untrusted-input.md) (`make_vectors.package_function`),
  [ADR-0013](0013-spec-structure.md), [ADR-0016](0016-sidecar-catalogs.md),
  [ADR-37CD](37CD-retro-follow-up-session-rules.md),
  [ADR-G45G](G45G-one-review-wave-and-the-question-channel.md),
  [ADR-KDBD](KDBD-change-classes-and-spec-forced-edits.md) and
  [ADR-QMKS](QMKS-draft-sections-and-coverage-columns.md) (commands of `sidecar_trace.py`),
  [ADR-4KW6](4KW6-onnxruntime-1-31-for-the-cpu-check.md), [ADR-BZ7X](BZ7X-onnx-runtime-telemetry-switch-and-scan.md),
  [ADR-JC4T](JC4T-parity-gates-and-batch-conversion-check.md) and [ADR-JY47](JY47-verification-batch-6-in-the-workflow.md)
  (`intake_bundle.py batch`).

## Evidence

- The copy check of the three pipeline reference modules that name package code as their source
  (`node_redetect_trigger.py`, `node_smooth_boxes.py`, `node_smooth_keypoints.py`), with each
  identifier replaced by one placeholder: 0, 3 and 1 statements also occur in the named package
  files, of 55, 62 and 114. Each match is a generic Python form.
- Today the vector files hold 297 entries of the package form, 27 different ones.

## Open work

[open-work.md](../open-work.md)

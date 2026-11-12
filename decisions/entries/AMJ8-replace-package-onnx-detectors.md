# AMJ8 — Replace the package ONNX detectors with exporter models; no legacy layer; `core/model_zoo/` holds the shipped sidecars

**Status:** accepted, 2026-11-11 (user).

## Decision

1. **Replace, do not migrate.** skellytracker re-implements each ONNX detector of the package on a
   fixed-batch, spec-compliant model from the exporters. The first models are `yolox-person` and
   `rtmw-wholebody133`. The old dynamic-batch detectors, their sidecars and their golden fixtures
   are deleted. Their sidecars are not migrated to the spec. This closes item 1 of
   [ADR-0QKK](0QKK-no-legacy-layer.md) for the package. The spec rule "no legacy reading" does not
   change.
2. **No legacy layer.** There is no `legacy/` folder, no frozen copy, no legacy reader and no legacy
   parameter of a shared function. The old `detector_type` keys (`yolox_person`, `rtmpose`,
   `rtmpose_body` and the others) go with their detectors, with no alias.
3. **MediaPipe.** The spec is ONNX only. MediaPipe is outside the spec. It must keep working.
4. **Processing.** `processing/` and the skeleton fragments move to the current spec, with no legacy
   behaviour. The new spec modules go in `processing/pre/` and `processing/post/`, one module for
   each spec section.
5. **Package sidecar root.** The shipped sidecars are in `skellytracker/core/model_zoo/`, with the
   spec layout. The folder holds data only. For now, the ONNX files of these sidecars are on disk
   beside them, but git does not track them, and no wheel or sdist holds them. Their move to a
   Hugging Face repo is later work.
6. **Keys.** An exporter model has the key `<model_id>@<source.name>`, for example
   `yolox-person@openmmlab-exporter`. A model of skellytracker has the key
   `<detector_type>@skellytracker`.
7. **RTMPose.** The replacements of RTMPose body, hand and face come from OpenMMLab-Exporter
   (`rtmpose-body17`, `rtmpose-hand21`, `rtmpose-face106`; the exporter applies the `model_id`
   rules). They block v2.0.0. Until they pass the acceptance gate, the old RTMPose detectors stay,
   with no change.
8. **Loader name.** The new spec loader is built as `core/model_spec/`, beside the old
   `core/sidecar/`. After the old loader is deleted, one `git mv` moves it to `core/sidecar/`. The
   `implemented_by` front matter, `TRACEABILITY.md` and the trace tools name `core/sidecar/`.

[ADR-AQR4](AQR4-detectors-and-pipelines-entry-points.md) gives the layout and the entry points.
[ADR-EM74](EM74-stage-order-and-ci-models.md) gives the order of the work.

## Reason

- A host must reject a `schema_version` that it does not implement, and the spec has no legacy
  reading ([ADR-0QKK](0QKK-no-legacy-layer.md);
  [versioning](../../specs/model-sidecar/format/versioning.md#behaviour)). So the spec loader cannot
  load an old package sidecar.
- The exporters already make fixed-batch models with spec sidecars. A re-export with the same
  upstream checkpoints costs less than a migration of the old sidecars and their code.
- A `$ref` target stays inside the root of the file that refers to it (`V-format.composition-4`).
  A root with no Python modules keeps discovery simple, and folder names with a hyphen do not sit
  among Python packages. A user can copy a model folder from the zoo to the user root, because both
  have the same layout.
- The spec resolves `filename` relative to the folder of the sidecar
  ([sizes and artifacts](../../specs/model-sidecar/common/sizes-and-artifacts.md)). So a sidecar with
  no `url` needs its ONNX file in its own folder.
- The old detectors call `load_sidecar` at import (for example `rtmpose_body_detector.py`). A change
  of `core/sidecar/` in place makes them fail at import. So the new loader has a temporary name.

## Consequences

- An installed package lists the shipped sidecars with each artifact unavailable until the Hugging
  Face repo exists. Only a git checkout has the ONNX files.
- freemocap uses the old detectors and their keys. It must not move to 2.0.0 before it migrates.
  freemocap is outside this work.
- Each release is built from a clean checkout. A check fails the build when a wheel or sdist holds
  an `.onnx` file.

## Alternatives rejected

- **Freeze the old detectors as legacy, or keep a `legacy/` folder.** It keeps two loaders and two
  processing paths, against [ADR-0QKK](0QKK-no-legacy-layer.md).
- **Bring the old sidecars and code up to the spec.** It costs more than a re-export, and the
  exporters own the model contract.
- **Aliases for the old keys.** No YAML or JSON config in this repository holds an old key, so an
  alias helps no user here.
- **The name `core/sidecars/` for the zoo.** It is too close to `core/sidecar/`.

## Open work

See [open-work.md](../open-work.md).

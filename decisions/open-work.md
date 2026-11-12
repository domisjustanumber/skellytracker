# Open work

This file holds the open work of the [decision log](README.md): the repository state. The
implementation-stage work is in the
[implementation plan](../specs/sidecar-implementation-plan.md). The spec defects are in the open work of the
[spec log](../specs/model-sidecar/decisions/open-work.md#spec-defects). Read the items that apply to
your task.

## Implementation stage

The implementation-stage work is in the stages of phase 1 and phase 2 of the
[implementation plan](../specs/sidecar-implementation-plan.md) ([ADR-5WKW](entries/5WKW-implementation-work-in-the-plan.md);
[ADR-NHM3](entries/NHM3-phases-to-the-exporter-checkpoint.md)).

## Repository state

- **Dependency pins for the exporters.** The target rule is that each exporter takes skellytracker
  as a dependency from a uv path source to the local checkout
  ([ADR-JAA4](entries/JAA4-one-batch-field.md), item 4). The pins of
  `pyproject.toml` stop it now: `requires-python = ">=3.11,<3.13"`, `numpy==2.4.6`,
  `opencv-contrib-python`, and onnx 1.22.0 and onnxruntime 1.31.1 in `uv.lock`
  ([ADR-4KW6](entries/4KW6-onnxruntime-1-31-for-the-cpu-check.md)). The exporters have
  (read 2026-10-28 from the `pyproject.toml` and the lock of each exporter):
  OpenMMLab-Exporter Python `>=3.14`, `numpy>=2.5.4`, `opencv-python-headless`, onnx 1.23.2,
  `onnxruntime-gpu` 1.31.0; Roboflow-Exporter Python `>=3.14`, `numpy==2.5.4`, onnx 1.23.2,
  onnxruntime 1.31.0; Ultralytics-Exporter Python `>=3.13`, `numpy==2.5.3`, onnx 1.22.0,
  onnxruntime 1.30.0; Qualcomm-Exporter Python `>=3.12,<3.14`, `numpy>=2.0`, `opencv-python` in its
  lock. uv cannot resolve the dependency in three of the four. In Qualcomm-Exporter,
  `opencv-contrib-python` next to `opencv-python` puts two `cv2` builds in one folder. A consumer
  does not get the `exclude-dependencies` of this repository.
  [ADR-B4QR](entries/B4QR-exact-pins-and-cuda-13.md) decides exact pins, ONNX Runtime 1.31 with
  CUDA 13 and `requires-python = ">=3.11,<3.14"`. The exporters that agents build again use those
  pins. The OpenCV package (`opencv-contrib-python` or a headless package) is not decided. The
  dependency stage of the implementation plan writes the pins. Until then, an exporter runs the batch
  tool in the checkout environment.
- **Exporter guide rewording.** A rewording PR removes each exporter repository name that is only an
  example from `specs/draft/exporter-guide/` and from all files of
  `specs/model-sidecar/model-addition-workflow/`. A citation of an exporter entry or commit as
  evidence stays. It also removes the open items that do not apply to a new exporter
  ([x64y](entries/x64y-draft-exporter-guide-folder.md), item 6).
- The exporters are re-implemented against the current exporter guide. This file does not track the
  old exporter copies or paths.
- **Draft exporter guide.** `specs/draft/exporter-guide/` is not complete. A local plan of the user
  owns its creation. When the guide is complete, or when an end-to-end test proves that its first
  version works, a new entry moves it to `specs/exporter-guide/`
  ([x64y](entries/x64y-draft-exporter-guide-folder.md)).
- **Exporter coverage note.** Retire `notes/sidecar-exporter-coverage.md` at the end of the
  spec-build stage. First, copy its unique measurements to an evidence entry
  ([ADR-5WKW](entries/5WKW-implementation-work-in-the-plan.md)).
- **Drift and vector-hash noise.** Two tool changes of `tools/intake_bundle.py` are later work
  ([ADR-FM0B](entries/FM0B-one-response-for-each-commit-group.md)). A section fingerprint for the
  drift finding: the section body without its front matter and without the text under
  "Implementer guidance" and "Authoring guidance". Do not reuse the changelog fingerprint: it does
  not hash the Behaviour text. A `vectors_sha256` of the parsed cases without `verified_against` and
  `unverified`, which `fill` prints and writes
  ([ADR-8DSW](entries/8DSW-vector-files-are-the-case-source.md)). An excused drift finding still
  blocks the session run of `batch` ([ADR-AD33](entries/AD33-bundles-are-untrusted-input.md)
  item 4). The user decides if a new entry changes that gate.
- **Kit PR in freemocap/project.** The kit is on the branch `dom/agents-and-adr-kit` of
  freemocap/project, in a PR for its owner
  ([ADR-P3NK](entries/P3NK-bootstrap-kit-in-freemocap-project.md)). The link repairs in 0031, NB91,
  QPS7 and Z05A pin the commit `0d88941` of that branch. When the PR merges with a different SHA,
  pin the merged commit.

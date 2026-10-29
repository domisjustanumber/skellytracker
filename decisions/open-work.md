# Open work

This file holds the open work of the [decision log](README.md): the repository state. The
implementation-stage work is in the
[implementation plan](../specs/sidecar-implementation-plan.md). The spec defects are in the open work of the
[spec log](../specs/model-sidecar/decisions/open-work.md#spec-defects). Read the items that apply to
your task.

## Implementation stage

The implementation-stage work is in the stages M7 to M12 of the
[implementation plan](../specs/sidecar-implementation-plan.md) ([ADR-5WKW](entries/5WKW-implementation-work-in-the-plan.md)).

## Repository state

- **Dependency pins for the exporters.** The target rule is that each exporter takes skellytracker
  as a dependency from a uv path source to the local checkout
  ([ADR-JB5J](entries/JB5J-one-batch-form-for-each-sidecar.md), item 5). The pins of
  `pyproject.toml` stop it now: `requires-python = ">=3.11,<3.13"`, `numpy==2.4.6`,
  `opencv-contrib-python`, and onnx 1.22.0 and onnxruntime 1.27.0 in `uv.lock`. The exporters have
  (read 2026-10-28 from the `pyproject.toml` and the lock of each exporter):
  OpenMMLab-Exporter Python `>=3.14`, `numpy>=2.5.4`, `opencv-python-headless`, onnx 1.23.2,
  `onnxruntime-gpu` 1.31.0; Roboflow-Exporter Python `>=3.14`, `numpy==2.5.4`, onnx 1.23.2,
  onnxruntime 1.31.0; Ultralytics-Exporter Python `>=3.13`, `numpy==2.5.3`, onnx 1.22.0,
  onnxruntime 1.30.0; Qualcomm-Exporter Python `>=3.12,<3.14`, `numpy>=2.0`, `opencv-python` in its
  lock. uv cannot resolve the dependency in three of the four. In Qualcomm-Exporter,
  `opencv-contrib-python` next to `opencv-python` puts two `cv2` builds in one folder. A consumer
  does not get the `exclude-dependencies` of this repository. The user decides the change. The
  options: a wider `requires-python`, a NumPy range, the headless OpenCV package, a lock refresh to
  onnx 1.23.2 or later and onnxruntime 1.31.0 or later (keep the `onnxruntime-gpu<1.27` cap in
  mind), and a split non-video test run on Python 3.12, 3.13 and 3.14. Until then, an exporter runs
  the batch tool in the checkout environment.
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

Repository state, not code work ([gtwq](entries/gtwq-random-entry-ids.md)):

- On 2026-10-22, the workflow runs on `freemocap/skellytracker` end in `startup_failure`.
- **Old mirror numbers.** [0028](entries/0028-entry-edits-and-citations.md) and
  [0029](entries/0029-decision-log-read-path.md) name "OpenMMLab-Exporter 0040 (planned)".
  [0030](entries/0030-no-private-data.md) names "OpenMMLab-Exporter 0041 (planned)". On 2026-10-24, these
  numbers belong to other entries in OpenMMLab-Exporter, and [0032](entries/0032-entry-numbers-and-edits.md)
  retires the mirror rule. The bodies do not change. These lines name no current entry.

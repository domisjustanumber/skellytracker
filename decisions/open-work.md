# Open work

This file holds the open work of the [decision log](README.md): the implementation-stage items and
the repository state. The spec defects are in the open work of the
[spec log](../specs/model-sidecar/decisions/open-work.md#spec-defects). Read the items that apply to
your task.

## Implementation stage

These items are for the implementation stage
([Stages](../specs/model-sidecar/model-addition-workflow/README.md#stages)). During the spec-build
stage, no file under `skellytracker/` changes, except test fixes.

- **`fit` `pad_value`.** At `vNEXT`, the spec requires `pad_value` on a `fit` resize
  ([Validation rules](../specs/model-sidecar/pre/resize-fit.md#validation-rules)). The code does not require it.
  `ResizeSpec._check_method_specific_fields` in `skellytracker/core/sidecar/model.py` accepts a `fit`
  resize without `pad_value`. Then `preprocess_image` in
  `skellytracker/core/detectors/processing/image_preprocessing.py` uses `0`, and `fit_preprocess` has
  the default `pad_value=0`. Add the missing validator rule, so that no valid `vNEXT` sidecar uses the
  default. Add a test of the rejection to `skellytracker/tests/sidecar/test_model_validation.py`.
  `test_fit_method_is_valid` already sets `pad_value: 114` ([0012](../specs/model-sidecar/decisions/0012-fit-resize-for-rtmo.md)).
- **`fit` scalar pad.** `fit_preprocess` in
  `skellytracker/core/detectors/processing/image_preprocessing.py` passes a scalar `pad_value` to
  `cv2.warpAffine` as `float(pad_value)`. OpenCV then fills only channel 0 of a 3-channel image: a
  scalar `114` gives the border `[114, 0, 0]`. A scalar must fill every channel, because
  `letterbox_preprocess` in the same file already does this (`np.full`). The spec does not state this
  rule. The spec must state it (see the [spec defects](../specs/model-sidecar/decisions/open-work.md#spec-defects), and
  [0012](../specs/model-sidecar/decisions/0012-fit-resize-for-rtmo.md)).
- **MediaPipe timestamps on Windows.** In video mode, the MediaPipe detectors under
  `skellytracker/core/detectors/keypoint_detectors/mediapipe/` use `int(time.monotonic() * 1000)` as
  the timestamp when the caller gives no `timestamp_ms`. On Windows, with Python 3.12,
  `time.monotonic()` uses `GetTickCount64()`, which has a resolution of 15.6 ms. Two frames in one
  tick get the same timestamp, and MediaPipe raises "Input timestamp must be monotonically
  increasing". The fallback timestamp must increase on each call.
- **MediaPipe landmarkers on Windows.** On Windows, the fast suite (`uv run pytest -m "not video"`)
  can also hang. A MediaPipe `PoseLandmarker` that an earlier test left open is garbage-collected
  during the teardown of the `onnx_session` fixture in `skellytracker/tests/test_rtmpose_detectors.py`.
  Then `PoseLandmarker.__del__` calls `close()`, and `close()` deadlocks in the MediaPipe dispatcher.
  This occurred on 2026-10-23, two times in sequence. The file alone passes, and Linux CI passes. This
  is a code defect: the tests or the detectors must close their landmarkers. For example, the tests in
  `skellytracker/tests/test_mediapipe_detectors.py` create MediaPipe detectors and do not call
  `close()`. The fix waits for the implementation stage.
- **Trace-tool functions.** Move `tools/sidecar_normalize.py` (the normalization table and the
  selector matching that the sidecar trace tool uses) into `skellytracker/core/sidecar/` without
  changes. The trace tool then imports them from the package. The capability check of 0016 uses the
  same functions ([0013](0013-spec-structure.md);
  [`format.versioning`](../specs/model-sidecar/format/versioning.md#implementer-guidance)).
- **Sidecar catalog and roots.** Build the catalog of 0016: the catalog key
  `<model_id>@<source.name>`, the version order and the version pins, the reserved name
  `skellytracker`, the root log and the run metadata
  ([`common.identity`](../specs/model-sidecar/common/identity.md#implementer-guidance)). Build the roots:
  the package root, local folders, Hugging Face repo snapshots (pin, refresh, cache paths without
  symlink resolution), development builds, user models and discovery in each root. Rename
  `cache_dir` to the sidecar root in the code
  ([`format.file_layout`](../specs/model-sidecar/format/file-layout.md#implementer-guidance)). See
  [0016](0016-sidecar-catalogs.md#decision).
- **Reference hash checks in the resolver.** Add the checks of the `$ref` and `base` hashes, and of
  the bytes of each file, to `skellytracker/core/sidecar/resolution.py`. Then delete the temporary
  function `resolve` of `tools/sidecar_refs.py`. Move the `--write` and `--check` commands of that
  tool into the package as a command, and keep a thin wrapper in `tools/`. When the package sidecars
  move to a release `schema_version`, give them `source` and the hashes
  ([`format.composition`](../specs/model-sidecar/format/composition.md#implementer-guidance); see
  [0016](0016-sidecar-catalogs.md#tools-and-line-endings)).
- **Artifact hash checks.** Verify the file that `filename` names against `sha256` when the file is
  present and after a download. Today `skellytracker/core/sessions/model_registry.py` checks only
  `url_sha256`, and only during a download
  ([`common.sizes_and_artifacts`](../specs/model-sidecar/common/sizes-and-artifacts.md#implementer-guidance);
  see [0016](0016-sidecar-catalogs.md#artifact-hashes)).
- **Capability check and dispatch.** Build the capability check of 0016. Map a catalog entry to
  detector code by its role and its spec sections. Keep the `detector_type` keys as aliases of
  `<model_id>@skellytracker`. Let a hand-written detector claim a catalog key. Make an unknown size
  an error, not a silent fallback
  ([`format.versioning`](../specs/model-sidecar/format/versioning.md#implementer-guidance); see
  [0016](0016-sidecar-catalogs.md#capability-check)).
- **YOLOX.** Re-export YOLOX to a contract that the spec describes: dynamic batch
  (`common.batching`), no NMS in the graph, and host `selection: nms` (`post.det.selection.nms`). Run
  a parity check on the new export. Then remove the claim of
  the hand-written YOLOX detector on the catalog key `yolox@skellytracker`
  ([`format.versioning`](../specs/model-sidecar/format/versioning.md#implementer-guidance);
  [0016](0016-sidecar-catalogs.md#detector-dispatch); see also
  [0006](0006-yolox-native-contract.md)).
- **`vNEXT` release step.** At the first skellytracker release that ships the spec, one content PR
  replaces `vNEXT` with that release version everywhere. Then the exporters regenerate their sidecars
  ([Publishing](../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing)). OpenMMLab-Exporter ([`rtmdet_person/sidecar.py:30`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmdet_person/sidecar.py#L30)) and Roboflow-Exporter ([`rf_detr/sidecar.py:32`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L32)) write `vNEXT` today.
- **NMS box area.** The spec's `selection: nms` uses the box-area convention of the ONNX
  `NonMaxSuppression` operator, which does not add `1` to pixel widths or heights. The generic `nms()`
  in `skellytracker/core/detectors/processing/object_detection_decode.py` adds `1`. Today only the
  legacy YOLOX path uses it. It also breaks a tie between equal scores toward the higher row index,
  but the spec breaks it toward the lower row index. The vectors in
  [`post.det.selection.nms`](../specs/model-sidecar/vectors/post.det.selection.nms.yaml) show both
  differences.
- **Letterbox rounding.** `letterbox_preprocess` in
  `skellytracker/core/detectors/processing/image_preprocessing.py` cuts the resized size with `int()`.
  The `vNEXT` spec rounds with `half_even` or `half_up`, places the image at `top_left` or `center`,
  and keeps each side at least 1 pixel. The function has no `center` position and fails on a source
  that is 1 pixel wide. It reproduces 8 of the 12 `top_left` cases in
  [`pre.resize.letterbox`](../specs/model-sidecar/vectors/pre.resize.letterbox.yaml). The cut size is
  correct only for legacy sidecars.
- **Stretch unprojection.** The `stretch` branch of `preprocess_image` returns `resize_meta = 1.0`. The
  host then has no scale factors to unproject with `x * src_w / T_w`.
- **Unused module.** `skellytracker/core/detectors/keypoint_detectors/rtmpose/rtmpose_preprocessing.py`
  is tracked, but no module imports it ([0007](0007-generic-processing-package.md)). Remove it.
- **Run-time check IDs.** A vector case for a refused tensor or caller argument writes
  `{error: no-rule}`, because no validation rule can check that input
  ([ADR-TA0G](TA0G-vector-cases-and-reference-modules.md)). The implementation stage can give these
  run-time checks their own IDs, for example `C-<section-id>-<n>`. A sidecar before `vNEXT` that uses
  a feature that is "Not available." also gives `no-rule`. A rule `V-format.versioning-<n>` can
  replace that use. The user decides both.

## Repository state

- **Dependency pins for the exporters.** The target rule is that each exporter takes skellytracker
  as a dependency from a uv path source to the local checkout
  ([ADR-JC4T](JC4T-parity-gates-and-batch-conversion-check.md), item 6). The pins of
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
  ([x64y](x64y-draft-exporter-guide-folder.md), item 6).
- **Exporter block copy.** The block for the exporter `AGENTS.md` names the model addition workflow,
  and its source line names `specs/draft/exporter-guide/sidecars/README.md`. Each exporter copies the
  block again in its own PR. Until then, an old copy names a path that does not exist, for example
  MediaPipe-Exporter `AGENTS.md` line 29 at commit `8f708a1ddecd8e035de15a5a9a7b652af035a58a` names
  `specs/exporter-guide/sidecars/README.md`
  ([x64y](x64y-draft-exporter-guide-folder.md)).
- **Old exporter guide paths.** The exporter repos and the recorded proposals cite old paths under
  `specs/exporter-guide/sidecars/`. No stub stays there. A session that lands a proposal edits the
  file at its new path. `README.md`, `known-open-items.md` and the checkout steps of
  `where-to-read.md` are under `specs/draft/exporter-guide/sidecars/`. The other parts of
  `where-to-read.md` are in `specs/model-sidecar/model-addition-workflow/reading-the-spec.md`. The
  files of `workflow/` (`workflow/README.md` is now `README.md`), `rules.md`,
  `reference-implementations.md`, `sidecar-files.md` and `validation-and-publishing.md` are under
  `specs/model-sidecar/model-addition-workflow/` ([x64y](x64y-draft-exporter-guide-folder.md)).
- **Draft exporter guide.** `specs/draft/exporter-guide/` is not complete. A local plan of the user
  owns its creation. When the guide is complete, or when an end-to-end test proves that its first
  version works, a new entry moves it to `specs/exporter-guide/`
  ([x64y](x64y-draft-exporter-guide-folder.md)).
- **Exporter paths to the spec folder.** The exporter repos cite the old spec folder
  `specs/sidecar/` and the old entry point `specs/sidecar-spec.md` in their agent files and notes.
  Each exporter changes these paths to `specs/model-sidecar/` in its own PR
  ([k6dz](k6dz-model-sidecar-folder.md)).
- **Moved reference-examples procedure.** The proposals `model-id-suffix`,
  `heatmap-decode-refinement` and `simcc-score-rule` cite `specs/sidecar-implementation-plan.md` by
  line number. A session that lands one of them edits the procedure in
  `specs/model-sidecar/model-addition-workflow/reference-examples.md`, and the package gaps in the
  front matter of the section ([b9fm](b9fm-finished-sidecar-plans.md)).
- **Exporter coverage note.** Retire `notes/sidecar-exporter-coverage.md` at the end of the
  spec-build stage, after the user decides [0041](../specs/model-sidecar/decisions/0041-rtmdet-host-nms-filters.md) and
  [0042](../specs/model-sidecar/decisions/0042-vnext-scope-nms-filters.md). First, copy its unique measurements to an evidence entry
  ([b9fm](b9fm-finished-sidecar-plans.md)).

Repository state, not code work ([gtwq](gtwq-random-entry-ids.md)):

- On 2026-10-22, MediaPipe-Exporter has no exporter code.
- On 2026-10-22, the workflow runs on `freemocap/skellytracker` end in `startup_failure`.
- **Old mirror numbers.** [0028](0028-entry-edits-and-citations.md) and
  [0029](0029-decision-log-read-path.md) name "OpenMMLab-Exporter 0040 (planned)".
  [0030](0030-no-private-data.md) names "OpenMMLab-Exporter 0041 (planned)". On 2026-10-24, these
  numbers belong to other entries in OpenMMLab-Exporter, and [0032](0032-entry-numbers-and-edits.md)
  retires the mirror rule. The bodies do not change. These lines name no current entry.

# Open work

This file holds the open work of the [decision log](README.md): the implementation-stage items,
the repository state and the spec defects. Read the items that apply to your task.

## Implementation stage

These items are for the implementation stage ([0014](0014-spec-lifecycle.md)). During the spec-build
stage, no file under `skellytracker/` changes, except test fixes.

- **`fit` `pad_value`.** At `vNEXT`, the spec requires `pad_value` on a `fit` resize
  ([Validation rules](../../specs/model-sidecar/pre/resize-fit.md#validation-rules)). The code does not require it.
  `ResizeSpec._check_method_specific_fields` in `skellytracker/core/sidecar/model.py` accepts a `fit`
  resize without `pad_value`. Then `preprocess_image` in
  `skellytracker/core/detectors/processing/image_preprocessing.py` uses `0`, and `fit_preprocess` has
  the default `pad_value=0`. Add the missing validator rule, so that no valid `vNEXT` sidecar uses the
  default. Add a test of the rejection to `skellytracker/tests/sidecar/test_model_validation.py`.
  `test_fit_method_is_valid` already sets `pad_value: 114` ([0012](0012-fit-resize-for-rtmo.md)).
- **`fit` scalar pad.** `fit_preprocess` in
  `skellytracker/core/detectors/processing/image_preprocessing.py` passes a scalar `pad_value` to
  `cv2.warpAffine` as `float(pad_value)`. OpenCV then fills only channel 0 of a 3-channel image: a
  scalar `114` gives the border `[114, 0, 0]`. A scalar must fill every channel, because
  `letterbox_preprocess` in the same file already does this (`np.full`). The spec does not state this
  rule. The spec must state it (see the spec defects below, and [0012](0012-fit-resize-for-rtmo.md)).
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
  [`format.versioning`](../../specs/model-sidecar/format/versioning.md#implementer-guidance)).
- **Sidecar catalog and roots.** Build the catalog of 0016: the catalog key
  `<model_id>@<source.name>`, the version order and the version pins, the reserved name
  `skellytracker`, the root log and the run metadata
  ([`common.identity`](../../specs/model-sidecar/common/identity.md#implementer-guidance)). Build the roots:
  the package root, local folders, Hugging Face repo snapshots (pin, refresh, cache paths without
  symlink resolution), development builds, user models and discovery in each root. Rename
  `cache_dir` to the sidecar root in the code
  ([`format.file_layout`](../../specs/model-sidecar/format/file-layout.md#implementer-guidance)). See
  [0016](0016-sidecar-catalogs.md#decision).
- **Reference hash checks in the resolver.** Add the checks of the `$ref` and `base` hashes, and of
  the bytes of each file, to `skellytracker/core/sidecar/resolution.py`. Then delete the temporary
  function `resolve` of `tools/sidecar_refs.py`. Move the `--write` and `--check` commands of that
  tool into the package as a command, and keep a thin wrapper in `tools/`. When the package sidecars
  move to a release `schema_version`, give them `source` and the hashes
  ([`format.composition`](../../specs/model-sidecar/format/composition.md#implementer-guidance); see
  [0016](0016-sidecar-catalogs.md#tools-and-line-endings)).
- **Artifact hash checks.** Verify the file that `filename` names against `sha256` when the file is
  present and after a download. Today `skellytracker/core/sessions/model_registry.py` checks only
  `url_sha256`, and only during a download
  ([`common.sizes_and_artifacts`](../../specs/model-sidecar/common/sizes-and-artifacts.md#implementer-guidance);
  see [0016](0016-sidecar-catalogs.md#artifact-hashes)).
- **Capability check and dispatch.** Build the capability check of 0016. Map a catalog entry to
  detector code by its role and its spec sections. Keep the `detector_type` keys as aliases of
  `<model_id>@skellytracker`. Let a hand-written detector claim a catalog key. Make an unknown size
  an error, not a silent fallback
  ([`format.versioning`](../../specs/model-sidecar/format/versioning.md#implementer-guidance); see
  [0016](0016-sidecar-catalogs.md#capability-check)).
- **YOLOX.** Re-export YOLOX to a contract that the spec describes: dynamic batch
  (`common.batching`), no NMS in the graph, and host `selection: nms` (`post.det.selection.nms`). Run
  a parity check on the new export. Then remove the claim of
  the hand-written YOLOX detector on the catalog key `yolox@skellytracker`
  ([`format.versioning`](../../specs/model-sidecar/format/versioning.md#implementer-guidance);
  [0016](0016-sidecar-catalogs.md#detector-dispatch); see also
  [0006](0006-yolox-native-contract.md)).
- **`vNEXT` release step.** At the first skellytracker release that ships the spec, one content PR
  replaces `vNEXT` with that release version everywhere. Then the exporters regenerate their sidecars
  ([0014](0014-spec-lifecycle.md)). OpenMMLab-Exporter ([`rtmdet_person/sidecar.py:30`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmdet_person/sidecar.py#L30)) and Roboflow-Exporter ([`rf_detr/sidecar.py:32`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L32)) write `vNEXT` today.
- **NMS box area.** The spec's `selection: nms` uses the box-area convention of the ONNX
  `NonMaxSuppression` operator, which does not add `1` to pixel widths or heights. The generic `nms()`
  in `skellytracker/core/detectors/processing/object_detection_decode.py` adds `1`. Today only the
  legacy YOLOX path uses it. It also breaks a tie between equal scores toward the higher row index,
  but the spec breaks it toward the lower row index. The vectors in
  [`post.det.selection.nms`](../../specs/model-sidecar/vectors/post.det.selection.nms.yaml) show both
  differences.
- **Letterbox rounding.** `letterbox_preprocess` in
  `skellytracker/core/detectors/processing/image_preprocessing.py` cuts the resized size with `int()`.
  The `vNEXT` spec rounds with `half_even` or `half_up`, places the image at `top_left` or `center`,
  and keeps each side at least 1 pixel. The function has no `center` position and fails on a source
  that is 1 pixel wide. It reproduces 8 of the 12 `top_left` cases in
  [`pre.resize.letterbox`](../../specs/model-sidecar/vectors/pre.resize.letterbox.yaml). The cut size is
  correct only for legacy sidecars.
- **Stretch unprojection.** The `stretch` branch of `preprocess_image` returns `resize_meta = 1.0`. The
  host then has no scale factors to unproject with `x * src_w / T_w`.
- **Unused module.** `skellytracker/core/detectors/keypoint_detectors/rtmpose/rtmpose_preprocessing.py`
  is tracked, but no module imports it ([0007](0007-generic-processing-package.md)). Remove it.

## Repository state

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

Repository state, not code work ([gtwq](gtwq-random-entry-ids.md)):

- On 2026-10-22, MediaPipe-Exporter has no exporter code.
- On 2026-10-22, the workflow runs on `freemocap/skellytracker` end in `startup_failure`.
- `specs/model-sidecar/post/canonical-mapping.md` links to the VRM specification by the branch `master`. A
  rewording PR must pin the two links to a commit.
- **Absorption gaps.** The reviews of 2026-10-24 and 2026-10-25 absorbed every accepted entry except
  [0008](0008-vnext-scope.md) and [0011](0011-rtmdet-host-nms.md). The proposals 0042 and 0048
  supersede 0008, and 0041 supersedes 0011, on acceptance. An absorbed entry can be superseded
  ([ngnb](ngnb-supersede-an-absorbed-entry.md)), but the user chose on 2026-10-26 to keep 0008 and
  0011 Active until the proposals are decided. Then absorb each entry that no accepted proposal
  supersedes: absorb 0008 into
  `specs/model-sidecar/changelog.md#considered-and-deliberately-not-added` and 0011 into
  `specs/model-sidecar/post/selection-nms.md#authoring-guidance`. Close their gaps first: Qualcomm-Exporter
  is out of the `vNEXT` scope until its library is complete (0008), and the `-1` row axis of the RTMDet
  `boxes` and `scores` shapes takes its value from `output_shapes` (0011).
- **Old mirror numbers.** [0028](0028-entry-edits-and-citations.md) and
  [0029](0029-decision-log-read-path.md) name "OpenMMLab-Exporter 0040 (planned)".
  [0030](0030-no-private-data.md) names "OpenMMLab-Exporter 0041 (planned)". On 2026-10-24, these
  numbers belong to other entries in OpenMMLab-Exporter, and [0032](0032-entry-numbers-and-edits.md)
  retires the mirror rule. The bodies do not change. These lines name no current entry.

## Spec defects

Spec defects found during the spec-build stage. Each one needs a content change to the spec:

- The note "The `imagenet_bgr` default is the RTMPose convention" in the spec's normalization modes is
  ambiguous at `vNEXT`. At `vNEXT`, `imagenet_bgr` means BGR-ordered statistics, but RTMPose uses the
  legacy meaning ([0009](0009-imagenet-bgr-meaning.md)).
- The reviewer note of the `vNEXT` change summary says to replace `vNEXT` "before merging". Decision
  [0014](0014-spec-lifecycle.md) moves that step to the first release that ships the spec.
- The [Identity](../../specs/model-sidecar/common/identity.md) fields say that a keypoint detector's
  `model_id` is `{family}-{part}`. This rule cannot express a variant suffix or a stage suffix. The
  RTMO body7 reference example, copied from OpenMMLab-Exporter, has `model_id: rtmo-body7` in the
  `body` part folder. A hand landmark model and a hand re-crop model of one family would both get
  `{family}-hand`. The spec must allow a suffix after the part, or the exporters must rename these
  models. OpenMMLab-Exporter sets `FAMILY = "rtmo-body7"` ([`rtmo/identity.py:24`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/identity.py#L24)).
  The gap record [0025](0025-model-id-suffix.md) (proposed) records this question.
- The [`input.resize`](../../specs/model-sidecar/pre/interpolation.md#behaviour) text says that every interpolation
  uses "`cv2.resize` / `cv2.warpAffine`, half-pixel centres". `cv2.warpAffine` maps the pixel centres
  in a different way. A 2x upscale of the ramp `[0, 10, 20, 30]` gives `2.5` with `cv2.resize` and
  `5.0` with `cv2.warpAffine` at destination `x = 1` (OpenCV 4.13.0).
- The `pad_value` row of [`input.resize`](../../specs/model-sidecar/common/input.md#inputresize) and the
  `crop_policy.pad_value` row say only that an array is per channel. They do not say what a scalar
  fills. The `fit` and `affine_person_crop` pseudocode passes `pad_value` unchanged to
  `cv2.warpAffine`. With a scalar, `cv2.warpAffine` fills only channel 0: a scalar `114` gives the
  border `[114, 0, 0]` (OpenCV 4.13.0). The `letterbox` pseudocode fills every channel
  (`full((T_h, T_w, 3), pad_value)`). The spec must state that a scalar fills every channel
  ([0012](0012-fit-resize-for-rtmo.md)).
- `clamp_boxes` in [`decode` (detection)](../../specs/model-sidecar/post/detection-decode.md#decode-detection) clamps the
  boxes to the source-image bounds. The spec does not define the bounds (`[0, W]` or `[0, W-1]`). It
  does not define the result for a box with zero area after the clamp. OpenMMLab-Exporter
  ([`onnx_runtime/decode_nms.py:170-171`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d2e68d27d2da0a4f22ddd19449df5601dcac87cc/onnx_runtime/decode_nms.py#L170-L171)), Roboflow-Exporter
  ([`rf_detr/coco_format.py:133`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/16852ca3f7e63e61fda1086ecf07491dc788581a/rf_detr/coco_format.py#L133)) and ultralytics 8.4.184 (`utils/ops.py`,
  `clip_boxes`) clamp to `[0, W]` and `[0, H]`.
- `schema_version` is quoted (`"vNEXT"`) in some
  [reference examples](../../specs/model-sidecar/examples/README.md) and not quoted in the RTMO
  body7 example. YAML reads both forms as the same string, but the examples do not agree.
- Two identity rules of [Validation rules](../../specs/model-sidecar/format/versioning.md#validation-rules) cannot pass
  at `vNEXT`: the version pattern, and the support by the installed release. Also, the sentence "Rules
  marked **(vNEXT)** apply only when `schema_version >= vNEXT`" is circular for `vNEXT`. `vNEXT` does
  not match the version pattern, so the comparison has no defined result for a `vNEXT` sidecar.
- The spec does not state these facts, but a host needs them:
  - the resizes run on the source dtype (for example `uint8`, before the cast). Roboflow-Exporter
    divides by 255 and then resizes the float image ([`onnx_runtime/preprocess.py:75-78`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/onnx_runtime/preprocess.py#L75-L78));
  - the keypoint scores in a `poses` tensor are already activated (the spec states this only for
    `packed_keypoints`). No exporter checks this channel: the RTMO probe of OpenMMLab-Exporter
    compares only `x` and `y` ([`notes/decisions/scripts/rtmo_sidecar_probe.py:97-102`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/scripts/rtmo_sidecar_probe.py#L97-L102));
  - the host frame is BGR, and the host converts it to `input.color_format`;
  - the arithmetic precision of the geometry and of the pixel math.
- A code docstring under `skellytracker/` cites the spec heading "Sizes", but the heading is `sizes`.
- The test vectors found these points that the spec does not define. Each vector file avoids them:
  - the box format and the coordinate space of the person box that `affine_person_crop` warps;
  - the order of the final rows for `selection: none`. The YOLO26 graph gives its rows in descending
    score order, and ultralytics 8.4.184 keeps that order with no sort (`utils/nms.py:74-77`);
  - the class of a candidate that has no class source when `is_person_only` is `false` (for
    `selection: none` and `top_k`);
  - the pixel-centre convention of the unprojection (see the `cv2.warpAffine` item above).
- The default `confidence_threshold_default` is `0.7` with a strict `>`, so a score of exactly `0.7`
  is dropped. The spec does not say that this is intended. The upstream of Qualcomm-Exporter,
  `qai_hub_models` 0.64.0, keeps a score equal to the threshold in `batched_nms` (`>=`,
  `utils/bounding_box_processing.py:86`).

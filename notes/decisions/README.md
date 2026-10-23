# Decision log

This log records technical decisions for skellytracker, with their reasons and evidence. Most entries
are about the model sidecar spec ([`specs/sidecar-spec.md`](../../specs/sidecar-spec.md)), the sidecar
code and the workflow that changes them. Read the entries that apply before you change the spec, a
sidecar, the sidecar code, the agent instructions or the PR workflow. Then you do not repeat a settled
question or a completed measurement.

Each entry gives the decision, its reason, the evidence (when there is evidence), the alternatives
rejected and a "Not repeated" section for pitfalls already found. Entries 0002 to 0012 are
backfilled. They record decisions made before this log existed, and they cite the original sources.
When a decision changes, add a new entry and mark the old entry superseded. Do not rewrite the old
entry.

| # | Decision | Status |
|---|----------|--------|
| [0001](0001-decision-log-and-agents-md.md) | Decision log; `AGENTS.md` is the single instructions file; `plans/` is local and ignored | accepted |
| [0002](0002-sidecars-tracked-in-package.md) | Sidecars are tracked in the package tree; ONNX files are not | accepted |
| [0003](0003-tracked-points-native-order.md) | `tracked_points` are in native model output order | accepted |
| [0004](0004-detectors-migrated-in-place.md) | Detectors migrated to sidecars in place; registry keys unchanged | accepted |
| [0005](0005-rtmw-moved-to-rtmw-family.md) | RTMW moved to `keypoint_detectors/rtmw/` with import shims | accepted |
| [0006](0006-yolox-native-contract.md) | The YOLOX sidecar describes the native ONNX contract | accepted |
| [0007](0007-generic-processing-package.md) | Generic pre- and post-processing live in `core/detectors/processing/` | accepted |
| [0008](0008-vnext-scope.md) | `vNEXT` scope, and the features considered and not added | accepted |
| [0009](0009-imagenet-bgr-meaning.md) | `imagenet_bgr` changes meaning at `vNEXT`; the legacy meaning stays | accepted |
| [0010](0010-family-invariant.md) | Family invariant: a size sets only its shape, target size and artifacts | accepted |
| [0011](0011-rtmdet-host-nms.md) | RTMDet: NMS-free graph with host `selection: nms`; no `pre_nms_top_k` | accepted |
| [0012](0012-fit-resize-for-rtmo.md) | `fit` resize for RTMO; `pad_value` is required | accepted |
| [0013](0013-spec-structure.md) | Spec structure: section files, rule owners, examples, reference implementations, traceability, STE | accepted |
| [0014](0014-spec-lifecycle.md) | Spec lifecycle, the `vNEXT` rule and the new-model workflow | accepted |
| [0015](0015-review-discipline.md) | Review discipline: one kind of change per PR, stacked drafts, merge method | accepted |
| [0016](0016-sidecar-catalogs.md) | Sidecar catalogs: source, reference hashes, roots, discovery and the capability check | accepted |

## Open work

These items are for the implementation stage ([0014](0014-spec-lifecycle.md)). During the spec-build
stage, no file under `skellytracker/` changes, except test fixes.

- **`fit` `pad_value`.** At `vNEXT`, the spec requires `pad_value` on a `fit` resize
  ([Validation rules](../../specs/sidecar/pre/resize-fit.md#validation-rules)). The code does not require it.
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
- **Trace-tool functions.** Move the normalization table and the selector matching of the sidecar
  trace tool into `skellytracker/core/sidecar/` without changes. The trace tool then imports them from
  the package. The capability check of 0016 uses the same functions ([0013](0013-spec-structure.md)).
- **Sidecar catalog.** Build the catalog of 0016: the catalog key `<model_id>@<source.name>`, the
  local and Hugging Face roots, discovery in each root, and the capability check
  ([0016](0016-sidecar-catalogs.md)).
- **YOLOX.** Re-export YOLOX to a contract that the spec describes: dynamic batch, no NMS in the
  graph, and host `selection: nms`. Run a parity check on the new export. Then remove the claim of
  the hand-written YOLOX detector on the catalog key `yolox@skellytracker`
  ([0016](0016-sidecar-catalogs.md); see also [0006](0006-yolox-native-contract.md)).
- **`vNEXT` release step.** At the first skellytracker release that ships the spec, one content PR
  replaces `vNEXT` with that release version everywhere. Then the exporters regenerate their sidecars
  ([0014](0014-spec-lifecycle.md)).
- **NMS box area.** The spec's `selection: nms` uses the box-area convention of the ONNX
  `NonMaxSuppression` operator, which does not add `1` to pixel widths or heights. The generic `nms()`
  in `skellytracker/core/detectors/processing/object_detection_decode.py` adds `1`. Today only the
  legacy YOLOX path uses it. It also breaks a tie between equal scores toward the higher row index,
  but the spec breaks it toward the lower row index. The vectors in
  [`post.det.selection.nms`](../../specs/sidecar/vectors/post.det.selection.nms.yaml) show both
  differences.
- **Letterbox rounding.** `letterbox_preprocess` in
  `skellytracker/core/detectors/processing/image_preprocessing.py` cuts the resized size with `int()`.
  The `vNEXT` spec rounds with `half_even` or `half_up`, places the image at `top_left` or `center`,
  and keeps each side at least 1 pixel. The function has no `center` position and fails on a source
  that is 1 pixel wide. It reproduces 8 of the 12 `top_left` cases in
  [`pre.resize.letterbox`](../../specs/sidecar/vectors/pre.resize.letterbox.yaml). The cut size is
  correct only for legacy sidecars.
- **Stretch unprojection.** The `stretch` branch of `preprocess_image` returns `resize_meta = 1.0`. The
  host then has no scale factors to unproject with `x * src_w / T_w`.
- **Unused module.** `skellytracker/core/detectors/keypoint_detectors/rtmpose/rtmpose_preprocessing.py`
  is tracked, but no module imports it ([0007](0007-generic-processing-package.md)). Remove it.

Spec defects found during the spec-build stage. Each one needs a content change to the spec:

- The note "The `imagenet_bgr` default is the RTMPose convention" in the spec's normalization modes is
  ambiguous at `vNEXT`. At `vNEXT`, `imagenet_bgr` means BGR-ordered statistics, but RTMPose uses the
  legacy meaning ([0009](0009-imagenet-bgr-meaning.md)).
- The reviewer note of the `vNEXT` change summary says to replace `vNEXT` "before merging". Decision
  [0014](0014-spec-lifecycle.md) moves that step to the first release that ships the spec.
- The [Identity](../../specs/sidecar/common/identity.md) fields say that a keypoint detector's
  `model_id` is `{family}-{part}`. This rule cannot express a variant suffix or a stage suffix. The
  RTMO body7 reference example, copied from OpenMMLab-Exporter, has `model_id: rtmo-body7` in the
  `body` part folder. A hand landmark model and a hand re-crop model of one family would both get
  `{family}-hand`. The spec must allow a suffix after the part, or the exporters must rename these
  models.
- The [`input.resize`](../../specs/sidecar/pre/interpolation.md#behaviour) text says that every interpolation
  uses "`cv2.resize` / `cv2.warpAffine`, half-pixel centres". `cv2.warpAffine` maps the pixel centres
  in a different way. A 2x upscale of the ramp `[0, 10, 20, 30]` gives `2.5` with `cv2.resize` and
  `5.0` with `cv2.warpAffine` at destination `x = 1` (OpenCV 4.13.0).
- The `pad_value` row of [`input.resize`](../../specs/sidecar/common/input.md#inputresize) and the
  `crop_policy.pad_value` row say only that an array is per channel. They do not say what a scalar
  fills. The `fit` and `affine_person_crop` pseudocode passes `pad_value` unchanged to
  `cv2.warpAffine`. With a scalar, `cv2.warpAffine` fills only channel 0: a scalar `114` gives the
  border `[114, 0, 0]` (OpenCV 4.13.0). The `letterbox` pseudocode fills every channel
  (`full((T_h, T_w, 3), pad_value)`). The spec must state that a scalar fills every channel
  ([0012](0012-fit-resize-for-rtmo.md)).
- `clamp_boxes` in [`decode` (detection)](../../specs/sidecar/post/detection-decode.md#decode-detection) clamps the
  boxes to the source-image bounds. The spec does not define the bounds (`[0, W]` or `[0, W-1]`). It
  does not define the result for a box with zero area after the clamp.
- `schema_version` is quoted (`"vNEXT"`) in some
  [reference examples](../../specs/sidecar/examples/README.md) and not quoted in the RTMO
  body7 example. YAML reads both forms as the same string, but the examples do not agree.
- Two identity rules of [Validation rules](../../specs/sidecar/format/versioning.md#validation-rules) cannot pass
  at `vNEXT`: the version pattern, and the support by the installed release. Also, the sentence "Rules
  marked **(vNEXT)** apply only when `schema_version >= vNEXT`" is circular for `vNEXT`. `vNEXT` does
  not match the version pattern, so the comparison has no defined result for a `vNEXT` sidecar.
- The spec does not state these facts, but a host needs them:
  - the resizes run on the source dtype (for example `uint8`, before the cast);
  - the keypoint scores in a `poses` tensor are already activated (the spec states this only for
    `packed_keypoints`);
  - the host frame is BGR, and the host converts it to `input.color_format`;
  - the arithmetic precision of the geometry and of the pixel math.
- A code docstring under `skellytracker/` cites the spec heading "Sizes", but the heading is `sizes`.
- The test vectors found these points that the spec does not define. Each vector file avoids them:
  - the box format and the coordinate space of the person box that `affine_person_crop` warps;
  - the order of the final rows for `selection: none`;
  - the class of a candidate that has no class source when `is_person_only` is `false` (for
    `selection: none` and `top_k`);
  - the pixel-centre convention of the unprojection (see the `cv2.warpAffine` item above).
- The default `confidence_threshold_default` is `0.7` with a strict `>`, so a score of exactly `0.7`
  is dropped. The spec does not say that this is intended.

## Rules

- Write one entry for each decision or measurement.
- Do not rewrite the body of an entry. To change a decision, add a new entry that supersedes it.
- The status line of an entry can change. These changes are allowed: `proposed` to `accepted` or
  `rejected`, and `accepted` to `superseded by NNNN`. Each change adds its date and the PR that made
  it.
- A decision can be accepted before its spec text lands. Its spec text then comes in a later content
  PR.
- Give a new entry the number after the highest number in the index. Add the entry to the index in
  the same PR.
- Cite commits that are on `development`, or tracked files. Do not cite or link `plans/`. Git does not
  track it ([0001](0001-decision-log-and-agents-md.md)).
- Until a commit is on `development`, cite its PR number and the file path, not its SHA
  ([0015](0015-review-discipline.md)).
- Write the number of another repo's entry with the repo name, for example "OpenMMLab-Exporter 0020".
  A bare number, for example 0016, is always an entry of this log.
- A spec change proposal is an entry with the status `proposed`. The new-model workflow in
  [0014](0014-spec-lifecycle.md) gives its parts.
- Write entries in ASD-STE100 Simplified Technical English. Use short sentences, the active voice and
  one instruction in each sentence. "must" is the requirement word. Technical names, field names, enum
  values, formulas, code and YAML stay unchanged.

## Entry template

The file name is `NNNN-<short-slug>.md`.

```markdown
# NNNN — <title>

**Status:** <proposed | accepted | evidence>, <YYYY-MM-DD> (<source>).

## Decision

## Reason

## Evidence

## Alternatives rejected

## Not repeated

## Open work
```

- **Status.** `accepted` is a decision. `evidence` is a measurement. `proposed` is a spec change
  proposal that waits for a decision. A later status change sets `rejected` or
  `superseded by NNNN` (see "Rules"). The source says who decided or where the entry comes from, for
  example "user" or "backfilled from #81".
- **Decision.** What is decided, written so that a reader can apply it.
- **Reason.** Why. Each entry gives its own reasons.
- **Evidence.** Write this section only when there is evidence: measurements, or code facts with
  their file and function.
- **Alternatives rejected.** The options that were examined and not used, with the reason for each.
  Omit the section when there are none.
- **Not repeated.** Pitfalls already found. Omit the section when there are none.
- **Open work.** Optional. Write only a link to the [Open work](#open-work) list of this README. Put
  the open-work items in that list, not in the entry.

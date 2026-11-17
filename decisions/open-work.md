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

- **Dependency pins for the exporters.** [ADR-M2C6](entries/M2C6-exact-pins-and-one-python-patch-release.md)
  decides exact pins, `onnxruntime` 1.31 as a base dependency with GPU EPs as CUDA 13 plugin packs,
  and `requires-python = "==3.13.18"`. The exporters that agents build again pin the 2.0.0
  pre-release (the draft exporter guide). On 2026-10-28, two exporters required Python 3.14 or later,
  and uv could not resolve skellytracker in three of the four exporters. The dependency stage of the
  implementation plan wrote the pins on 2026-11-12. Until the 2.0.0 pre-release, an exporter runs
  the batch tool in the checkout environment.
- **Exporter open items.** At the 2.0.0 pre-release, remove the rows of
  `specs/draft/exporter-guide/sidecars/known-open-items.md` that name a reference implementation.
  They do not apply to a new exporter, and the skill `implement-sidecar-section` uses them until
  then ([x64y](entries/x64y-draft-exporter-guide-folder.md), item 6;
  [ADR-6J8E](entries/6J8E-exporters-run-released-skellytracker.md) item 1).
- The exporters are re-implemented against the current exporter guide. This file does not track the
  old exporter copies or paths.
- **Draft exporter guide.** `specs/draft/exporter-guide/` is not complete. A local plan of the user
  owns its creation. When the guide is complete, or when an end-to-end test proves that its first
  version works, a new entry moves it to `specs/exporter-guide/`
  ([x64y](entries/x64y-draft-exporter-guide-folder.md)). Each new part of the guide goes in a new
  folder beside `sidecars/`.
- **Drift and vector-hash noise.** Two tool changes of `tools/intake_bundle.py` are later work
  ([ADR-FM0B](entries/FM0B-one-response-for-each-commit-group.md)). A section fingerprint for the
  drift finding: the section body without its front matter and without the text under
  "Implementer guidance" and "Authoring guidance". Do not reuse the changelog fingerprint: it does
  not hash the Behaviour text. A `vectors_sha256` of the parsed cases without `verified_against` and
  `unverified`, which `fill` prints and writes
  ([ADR-8DSW](entries/8DSW-vector-files-are-the-case-source.md)). An excused drift finding still
  blocks the session run of `batch` ([ADR-AD33](entries/AD33-bundles-are-untrusted-input.md)
  item 4).
- **Vector runs of a bundle that follows a proposal.** A `model` bundle that follows an accepted
  proposal cannot record a vector run on the vectors of that proposal. `verify` accepts only a
  vector file that is landed (`_payload_problems` in `tools/intake_bundle.py`). Thus the bundle
  records the run as `no vectors`. An example is version 6 of `model-rtmw-wholebody133` for
  `post.keypoint.score_map`
  ([ADR-F067](../specs/model-sidecar/decisions/entries/F067-simcc-score-map.md)).
- **Pipeline redesign.** The build stages of the redesign of the node and port types, and its
  points that are still open, are in
  [`node-and-port-redesign.md`](../specs/pipeline/proposals/node-and-port-redesign.md), sections 10
  and 11 ([ADR-9HTX](entries/9HTX-pipeline-node-and-port-redesign.md)). Stages 1 to 7 are built in
  skellytracker. Stage 8, the pipeline editor, is freemocap work that the user does in another
  session. [ADR-8TQT](entries/8TQT-redesign-stages-6-and-7-before-the-pre-release.md) records the
  new timing of stages 6 to 8. ADR-9HTX stays `accepted`: no absorb document states its item 13
  (no hand box node; two `boxes_from_points` nodes give the hand boxes), and the user ruled on
  2026-11-17 that the edges of a `merge` output must link the body and each part, which is not
  built yet. Two items are later work.
  Look into one canonical output keypoint set that becomes the only output format of a pipeline.
  Make one BGR to RGB conversion for each camera and frame for the decomposed MediaPipe pipeline.
- **Cost of the detector preprocess.** Measured on 2026-11-17 with `time.perf_counter_ns` on one
  desktop CPU, with OpenCV 5.0.0.93 and no other load. `preprocess_image` of
  `core/detectors/processing/pre/preprocess.py` needs about 5.2 ms for one 1280x720 frame with the
  `yolox-person` sidecar at size `m` (640x640). The time is almost the same for a 1920x1080 and a
  3840x2160 frame. It needs about 1.2 ms with the `rtmw-wholebody133` sidecar at size `m`
  (256x192). Three causes are known:
  - The `letterbox` function of `pre/resize_letterbox.py` needs about 1.8 ms, and its `cv2.resize`
    call needs 0.2 to 0.4 ms. The canvas fill from a `float64` array uses most of the difference.
  - The `normalize` function of `pre/normalize.py` makes a cast and two or three float passes
    over each pixel of the model input.
  - A detector prepares the images of one frame one after the other, in one `preprocess` span. The
    span thus grows with the number of cameras. freemocap showed more than 22 ms for the span
    `person.preprocess` with four cameras at 1280x720.

  In the built-in pipeline, the detector runs one time in 150 frames. The mean cost is small, but
  the frame with a detection has a delay of this size. No fix is decided. A change of this code
  must keep each output tensor equal.
- **Kit PR in freemocap/project.** The kit is on the branch `dom/agents-and-adr-kit` of
  freemocap/project, in a PR for its owner
  ([ADR-P3NK](entries/P3NK-bootstrap-kit-in-freemocap-project.md)). The link repairs in 0031, NB91,
  QPS7 and Z05A pin the commit `0d88941` of that branch. When the PR merges with a different SHA,
  pin the merged commit.

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

- **Linux gate of ONNX Runtime 1.30.0.** [ADR-N6E8](entries/N6E8-onnxruntime-1-30-on-each-os.md) item 9: run
  the certify suite `tools/certify_platform.py` on bare-metal Ubuntu 24.04 with an NVIDIA driver of
  590.48.01 or later. It replaces `decisions/scripts/n6e8_ort_1_30/linux_ep_gate.sh`
  ([ADR-Y14H](entries/Y14H-certify-suite.md) item 16). The change of the items 2 and 3 of N6E8 lands
  only after this run passes. Then write the result in the Evidence section of N6E8.
- **Certify suite.** [ADR-Y14H](entries/Y14H-certify-suite.md): the frame and sections 1 to 4 are
  built. Sections 3 and 4 are in `tools/certify_eps.py`. These items stay open:
  - Sections 5 to 7. Each is a placeholder with `not-run` and `not-built` in `SECTIONS` of
    `tools/certify_platform.py`.
  - Sections 3 and 4 ran on one Windows host with an NVIDIA GPU and an Intel iGPU only. No run on
    Linux, on macOS (`coreml`), on a host with an AMD GPU or on a laptop with two GPUs.
  - The AMD EPs (item 11): the Windows AMD EP package and its removal, the MIGraphX builds for ROCm
    10.0, 10.1 and 10.2, and the second environment on ONNX Runtime 1.29. Until then, section 3
    records the check `amd-eps` as `not-run` with `not-built`. The field-test state and DirectML are
    built ([ADR-Z5X7](entries/Z5X7-field-test-state-and-directml.md)). DirectML has no result on an
    AMD GPU yet. A reviewed passing report on Windows moves it to `ready`, and changes the note of
    the hardware class `amd-windows`.
  - Section 4 does not measure the VRAM of an integrated GPU: the PDH counter of `LiveSampler` reads
    dedicated memory only.
  - The public Hugging Face model repository of the freemocap organisation (not created yet), and
    the model list `models` (path, URL, sha256, bytes) in the `certification` block of
    `ep_catalog.yaml` (item 12). Section 4 reads the list, and is `not-run` with `models-missing`
    when a model file is absent.
  - A leak that the suite cannot stop: the cache of `uv`. It belongs to the tool of the volunteer.
  - The instructions page `CERTIFY.md`, the issue template and the contact email (item 14).
  - The entry points that the JPEG branch owes for sections 5 and 7, and that skellycam owes for
    section 6: a pinned public commit and its runner (item 10).
  - The name pattern of a certification tag. Section 1 now accepts each tag at HEAD.
- **EP certification.** Five items of [ADR-MF2R](entries/MF2R-ep-store-install-and-certification.md)
  stay open:
  - Check the `thresholds` of the `certification` block of `ep_catalog.yaml` on more hosts and images.
    One RTX 3070 with `cuda` and `trt-rtx` on one image gave the values of 2026-11-18 (item 16).
  - Write the `maintainer` rows of `ep_evidence.yaml` for the current set hash on Windows and on
    Linux. Until then, `tools/onnx_stack.py check` fails for each NVIDIA pack (item 18).
  - Later stage: send a report. The user decided a relay that opens an issue in a public intake
    repository of the freemocap organisation, with no login. Until then, nothing leaves the host.
  - Before a field-test EP ([ADR-Z5X7](entries/Z5X7-field-test-state-and-directml.md)) moves to
    `ready`, move the wider run of `certify()` to a child process: an EP that ends the process
    writes no report (`_wide_run` in `core/eps/certification.py`).
- **Field-test opt-in.** [ADR-Z5X7](entries/Z5X7-field-test-state-and-directml.md): there is no
  command that removes an opt-in. A user deletes `field-test.json` of the EP store.
  - freemocap work: the dialog of the prompt (item 14) and of the download prompt (item 9).
- **Dependency pins for the exporters.** [ADR-N6E8](entries/N6E8-onnxruntime-1-30-on-each-os.md)
  decides exact pins, ONNX Runtime 1.30.0 as a base dependency with GPU EPs as CUDA 13 plugin packs,
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
- **Pipeline redesign.** Stages 1 to 7 of the redesign of the node and port types are built in
  skellytracker, and the absorb documents state the rules of
  [ADR-9HTX](entries/9HTX-pipeline-node-and-port-redesign.md).
  [ADR-8TQT](entries/8TQT-redesign-stages-6-and-7-before-the-pre-release.md) records the new timing
  of stages 6 to 8. Three items stay open:
  - Stage 8, the pipeline editor, is freemocap work that the user does in another session.
  - Later work: look into one canonical output keypoint set that becomes the only output format of
    a pipeline.
  - Later work: make one BGR to RGB conversion for each camera and frame for the decomposed
    MediaPipe pipeline.
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

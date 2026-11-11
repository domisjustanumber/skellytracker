# 7NY2 — Pipeline config: one Pydantic model from a YAML file; a flat node graph with `@prev`; detector, `mediapipe_tasks` and a closed set of glue nodes

**Status:** accepted, 2026-11-10 (user).

## Decision

1. **Fixed at start.** A pipeline is fixed when its run starts. There are no overrides at start: load
   the config, change it, and pass it in. Live changes of params wait for a later version.
2. **Form.** One Pydantic model `PipelineConfig`. A YAML file `<pipeline_id>.pipeline.yaml`, a JSON
   file or a dict gives it. The loader uses `yaml.safe_load`, a duplicate-key check and strict
   validation. Discovery reads `*.pipeline.yaml` in `core/model_zoo/pipelines/` and in
   `<user root>/pipelines/` ([ADR-AQR4](AQR4-detectors-and-pipelines-entry-points.md)).
3. **Built-ins are files.** No Python builder remains. `export_pipeline(config, resolved=False)`
   writes the config as written; `resolved=True` writes each param. A config refers to a sidecar and
   never copies its content.
4. **Graph.** A flat list of nodes. Each node has an `id`, a `type` and named `inputs`
   (`<node>.<port>`). The suffix `@prev` names the value of the previous frame. The graph is acyclic
   except through `@prev`. Each `@prev` value is empty on the first frame.
5. **Detector node.** One ONNX model with its sidecar preprocessing and postprocessing (crop,
   decode, NMS). There are no step nodes for pre, infer, decode or NMS.
6. **Glue nodes.** A closed set that the pipeline spec defines. A pipeline file runs no user code
   ([ADR-AD33](AD33-bundles-are-untrusted-input.md)). A new node type is a spec change. A node that
   gets an empty required input does not run and gives an empty output. An empty optional input
   does not stop a node. In the whole graph, a point name has the id of its node as a prefix. v1:
   - `roi_from_points`: keypoints → ROIs. Point names with aliases, the sidecar derived points,
     size rule `alignment` or `bounds`, target rotation or `none`, a score gate, and
     `transform {shift_x, shift_y, square_long, expand_ratio}`.
   - `roi_tracking`: ROIs@prev and new ROIs → ROIs, with rotation, shift and size limits.
   - `gate` (`is_empty` or `score > t`), `first_of` (a list; the first input that is not empty),
     `concat` (a list of keypoint sets of one instance source; it never replaces a point).
   - `merge`: target keypoints and source keypoints of any instance source → the target plus one
     column set for each slot. A source row goes to the slot with the nearest anchor. A map
     replaces target points with present source points.
   - `smooth_keypoints` (`one_euro` or `kalman` in time units, `max_gap_ms`, `reset_after_ms`),
     `smooth_roi` (EMA `previous_weight`), `redetect` (keypoints@prev → trigger, with
     `redetect_interval` in frames and `fitness_checks`).
7. **MediaPipe.** A `mediapipe_tasks` node wraps one Tasks landmarker, with no reset and the shared
   param names (`min_*_score`, `size`). The decomposed form uses detector and glue nodes with ONNX
   models. It waits for sidecar proposals (a crop that takes a rotated ROI, weighted NMS, detection
   keypoints, the `roi_refiner` role). The pipeline spec never defines model processing.
8. **ROI.** One type `(cx, cy, w, h, rotation)` in source-image pixels. A box is an ROI with rotation
   0. `rotation` is in radians, clockwise in the image, in [−π, π). Only the detector node cuts
   pixels, from the camera frame: the ROI rules first, then the sidecar padding.
9. **NMS.** NMS stays in the postprocess of the detector node. One implementation: an ONNX
   `NonMaxSuppression` graph on the CPU provider, as the OpenMMLab-Exporter `NmsDecoder` that the
   spec verifies against, with `max_output_boxes_per_class` `2**31-1`. `post_nms_top_k` applies to
   the final rows. The gate is `vectors/post.det.selection.nms.yaml`.
10. **Model reference.** A detector node gives `key`, `sidecar_sha256`, `size` and `precision`.
    `sidecar_sha256` is required in shipped and exported files. A mismatch is an error that names
    both hashes. `size` is required. `key` can pin `<key>==<version>`. `precision` defaults to fp16
    on a GPU EP and fp32 on CPU, and to fp32 when the size has no fp16 artifact.
11. **Params.** The defaults of a detector node (`object_decode`) come from its sidecar. The
    spec gives the defaults of the glue nodes. A file writes only the params that it changes. An
    unknown param is an error. The spec marks each param `live: yes` or `live: no`.
12. **EP.** The execution provider is a concrete argument of the run (`cuda`, `tensorrt`, `cpu`, …).
    A node can override it. There is no EP policy such as `recommended:latency`.
13. **Not models.** `keypoint_bbox` and `precomputed` leave the `detectors` list and are deleted
    with the old run code. `roi_from_points` takes the place of `keypoint_bbox` in a pipeline, but it
    does not reproduce it: `keypoint_bbox` takes the mean of its centre points, the largest distance
    of several point pairs times a scale, a square box and a minimum size in pixels.
    `roi_from_points` keeps the MediaPipe-style params of item 6. `precomputed` becomes a `replay`
    tap ([ADR-Q59W](Q59W-pipeline-timing-and-taps.md)).

## Reason

- A stage tree cannot show fan-in or loops from the previous frame. MediaPipe Holistic has both.
- A config that holds step nodes could break the sidecar contract.
- One NMS implementation agrees with the reference that the spec verifies against.
- A threshold is tuned to one model and size, so the sidecar gives the defaults.
- A pipeline file is input from outside. It must not run code.

## Alternatives rejected

- A stage tree with special cases; step nodes; Python builders for the built-ins.
- An NMS glue node, an `nms_impl` switch, `cv2.dnn.NMSBoxes` and torchvision.
- Glue node types that users add in Python.
- Live param changes in v1; overrides at start; an EP policy.

## Open work

See [open-work.md](../open-work.md).

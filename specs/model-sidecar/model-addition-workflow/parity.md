# Parity

Parity compares the sidecar path with the upstream library on real images. Phase 1 (step 5) and
phase 2 (part 5) use these rules.

The sidecar path is your host implementation of each section (in an exporter, the host
implementation of the exporter). It does the
preprocessing and the decode exactly as the sidecar declares. Write it from the spec text. In phase 2,
the reference implementation of the proposal replaces the missing spec feature.

- If a section has test vectors, your host implementation must first pass each numeric case of each
  mode that the model uses. [Payload](hand-over.md#payload) gives the `not used` cases.
- If a reference implementation of the section exists, use it or match it.
- If no reference implementation of the section exists, your plan must include the
  reference-implementation step (see
  [Reference implementations](reference-implementations.md#reference-implementations)).

Do these steps:

1. Set the gate of each compared quantity before the run. Record each gate and its source
   ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)).
   - Use your own gate or a numeric floor of the upstream. Your own gate is an accuracy gate, for
     example AP, OKS, or a count of outliers above a fraction of the ROI size. A numeric floor is,
     for example, the float32 noise of the upstream computation. Another example is the change that
     the export error of step 3 causes in the quantity.
   - You can also set a gate from a measurement of the sidecar path before the run. This is a
     measured gate. Record the values of the measurement and the factor. Commit the script of the
     measurement, as step 6 says.
   - A measured gate is a pass gate only when both of these are true:
     - you cannot calculate a floor for the quantity, for example because the upstream gives only
       the output of the full chain. Write the reason;
     - a negative control in the same run fails the gate. A negative control is the run with a wrong
       value of the changed quantity, for example the old value of a changed field.
   - Otherwise a measured gate is a control. A control does not prove parity.
   - Each quantity that the intake or the proposal changes must have a pass gate. If you cannot set
     a pass gate yet, write `to run` for that gate. Give the reason.
   - If you replace a gate after a measurement, record the old gate, the measurement and the reason.
   - A gate that you set after the run is not a gate of that run.
   - If the scope changes after the run, the result of that run stays. A new result needs a new run.
     Set its gates before that run.
2. Choose the test images. Each branch of each section that the sidecar uses must run on at least
   one image. Calculate the branches from the formulas of the spec before you choose. For a resize,
   use source sizes where the scaled size has a fractional part below 0.5, above 0.5 and equal to
   0.5, a size with an odd pad gap, a portrait image, a landscape image, a downscale and an upscale.
   For a detector, use an image with no detection and an image with several detections. One image is
   not enough. Record the reason for each image.
   A branch that no real image can reach, for example a score `<= 0`, a tie or a NaN of a decode,
   needs no image. Name the branch and its coverage: the vector cases of the section that your host
   passes, or a committed check that runs crafted inputs through the upstream code and compares your
   host bit for bit
   ([ADR-R6J9](../decisions/entries/R6J9-test-time-steps-and-unreachable-branches.md)).
3. Measure the export error. Give the tensor of the upstream preprocessing to the ONNX file. Compare
   its outputs with the outputs of the upstream model on the same tensor.
4. Compare the preprocessed input. Compare the tensor of the sidecar path with the tensor of the
   upstream preprocessing. Give the maximum absolute difference for each image. Expect 0. If it is
   not 0, find the cause and write it. If the cause is a property of the model or of the upstream
   code, the row of that property is not `exact`. If the cause is outside both (for example two
   different OpenCV versions), remove it, or give its maximum and its cause.
5. Compare each final output of each role of the sidecar. The section of the role defines its final
   outputs ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)).
   - the row count of each image;
   - for the `object_detector` role: the boxes, the scores and the classes, with box AP or per-row
     box differences;
   - for the `keypoint_detector` role: the keypoints and the keypoint scores, with OKS or per-point
     differences;
   - for another role: each final output that the section of the role defines.

   Compare an output with coordinates in source-image coordinates, after the unprojection. Compare
   an output without coordinates as the model gives it, for example the score and the label of each
   class. The upstream can give no value for a final output, for example the ROI of a `roi_refiner`.
   Then compare the first later output that the upstream gives. Write which output you compared.

   A model with both roles needs both comparisons. A keypoint metric does not check the boxes.
   Compare each result with the change that the export error of step 3 causes in the same
   quantity. Use the unit of that quantity, for example pixels for a keypoint. The error above that
   change comes from the sidecar path.
6. Commit the parity script in your repo, so that a commit can be cited. A script that is
   only in the local `plans/` folder or only in a bundle is not evidence. A tracked copy of a bundle
   file is evidence ([Tracked records](hand-over.md#tracked-records)), but the script must still
   have a commit in your repo. Use the folder of your repo for evidence
   scripts.
7. If you cannot run the check, or if you cannot commit the script, write `to run` as the result.
   Give the reason. Describe the script and its gates. You can write the numbers of a run without a
   commit, but they are not evidence.
8. Unless the fields give `batch_forced` or `no_static_reason`, the
   [batch-conversion check](batch-conversion-check.md#batch-conversion-check) of phase 1 (step 1b) is the
   parity check of the generated batch artifacts
   ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). Its tolerance is in the authoring guidance of
   [`common.batch_conversion`](../common/batch-conversion.md#authoring-guidance). Do not make the
   tolerance larger.

If the upstream has no Python API (for example, it runs only in C++), take the reference output from
the upstream runtime itself, for example from a build of the upstream that writes its tensors. Do not
use your own copy of the upstream algorithm as the reference. If you cannot run the upstream, the
result is `to run`.

## Reference files

A `model` bundle can hold the folder `parity/`: the output of the parity run, as data. The model
gate of skellytracker compares the package with these files
([ADR-T41E](../../../decisions/entries/T41E-reference-files-of-a-model-bundle.md)).

- `parity/parity.yaml` is the manifest.
- `parity/<size>.<precision>.npz` is the array file of one published size and precision, for
  example `m.fp32.npz`. Write it with `numpy.savez_compressed`. It must be 256 KiB or smaller. It
  holds only numeric arrays. A reader loads it with `allow_pickle=False`.
- The folder holds no other file. Do not put an image or an ONNX file in it.
- `verify` of `tools/intake_bundle.py` checks the manifest keys and each array file.
- Use the images of your parity run. Do not make a second image list.

### Manifest

```yaml
parity_format: 1
exporter: <exporter repo>
commit: <40 hex>                  # the commit of the script
script: <path of the parity script in the exporter repo>
upstream: {library: <name>, version: <version>}
onnx_runtime: <version>           # the ONNX Runtime of the raw values
seed: <integer>
images:
  - key: <image key>              # a dataset image
    source: coco-val2017
    id: <image ID in the dataset>
    sha256: <64 hex>              # of the bytes of the image file
    stop_gap: true
  - key: <image key>              # a made image
    made: {op: <operation>, from: [<image key or dataset image ID>, ...], <numbers of the operation>}
    pixels_sha256: <64 hex>       # of the bytes of the decoded image: uint8, BGR, (H, W, 3), C order
    stop_gap: true
files:
  - path: <size>.<precision>.npz
    sha256: <64 hex>
    raw_limit: {<output name>: <number>}
    final_limit: {box: <number>, score: <number>}    # `object_detector`
    inputs: {<item key>: <64 hex>}
```

- No image goes into a bundle or into git. The manifest names each image. The session gets a
  dataset image from its local copy of the dataset, and it makes a made image.
- `stop_gap: true` marks an image that is not a frame of a freemocap recording. The images of
  COCO val2017 are a stop-gap. A recording that freemocap makes replaces them. Then a new bundle
  version gives the new list. The format does not change.
- A made image has one of these operations. Each resize is `cv2.resize` with `INTER_AREA`.
  - `flat`, with `size: [w, h]` and `value`: each value of the image is `value`.
  - `crop`, with `box: [x1, y1, x2, y2]`: the rows `y1` to `y2 - 1` and the columns `x1` to
    `x2 - 1` of the one image of `from`.
  - `resize`, with `size: [w, h]`: the one image of `from`, resized to `size`.
  - `hconcat`, with `height`: each image of `from`, resized to the height `height` and the width
    `round(w * height / h)`, side by side in the order of `from`.
  - `vconcat`, with `width`: each image of `from`, resized to the width `width` and the height
    `round(h * width / w)`, one below the other in the order of `from`.
- An item is one image of an `object_detector` model, or one person of a top-down
  `keypoint_detector` model. The key of a person is `<image key>_<name>`. `inputs` lists the
  items in the order of the run. Each value is the SHA-256 of the bytes of the input tensor of the
  item: the tensor of your host preprocessing, in the `input.dtype` of the precision, with no batch
  axis, in C order.
- `raw_limit` gives, for each output, the largest permitted difference of a raw value. Use 0.05
  for a box output in pixels and 0.0001 for a score output with fp32. Use 1.0 and 0.002 with fp16.
  Use 0.01 for a SimCC output. Write a different value only with a measurement, and give the
  measurement in the intake.
- `final_limit` of an `object_detector` gives the export error of step 3 for this size and
  precision: `box` in model-input pixels and `score`. `final_limit` of a `keypoint_detector` is
  `{bins: 1, outlier_fraction: 0.15}`, unless your parity run set a different measured gate with
  its negative controls.

### Array files

The raw values come from the ONNX file of the size and the precision, on the CPU EP of ONNX
Runtime, with the input tensor of `inputs`. The final values come from the upstream library on the
same image. `<output name>` is a name of `outputs[].name` of the sidecar. The values of `seed` come
from `numpy.random.default_rng(seed)`.

For each image of an `object_detector` model:

| Array | Content |
|---|---|
| `<image key>__raw_rows` | int32. The 100 rows with the highest score, then 200 other rows chosen with `seed`. With 300 rows or fewer, each row. |
| `<image key>__raw_<output name>` | The values of the output at these rows. |
| `<image key>__final_boxes` | float32, (K, 4). The boxes of the upstream library, `xyxy`, in source pixels, with the `min_score` of the sidecar. |
| `<image key>__final_scores`, `<image key>__final_classes` | float32 and int32, (K). |

For each person of a top-down `keypoint_detector` model with SimCC outputs:

| Array | Content |
|---|---|
| `<person key>__box` | float32, (4). The input box, `xyxy`, in source pixels. |
| `<person key>__peak_bin_<output name>` | int32, (K). The first bin with the largest value, for each keypoint. |
| `<person key>__peak_value_<output name>` | float32, (K). The value at that bin. |
| `<person key>__final_keypoints`, `<person key>__final_scores` | float32, (K, 2) in source pixels and (K). The output of the upstream library. |

And one time for each SimCC output of the file:

| Array | Content |
|---|---|
| `sample_index_<output name>` | int64. Indices chosen with `seed` into the output of all persons, stacked in the order of `inputs` and flattened in C order. The outputs share 4096 indices equally. |
| `sample_value_<output name>` | float32. The values at these indices. |

A model of another role or with another output form needs a proposal for its arrays.

### The gate on the reference files

The skellytracker session does these steps for each array file. The package runs on the CPU EP.

1. Get each image. A dataset image must have the `sha256` of the manifest. A made image must have
   the `pixels_sha256` of the manifest. Another OpenCV build can give other pixels for a resize.
   The session reports such an image as "image not reproduced" and does not use it. The gate fails
   when the session can use fewer than half of the images.
2. For each item, compare the SHA-256 of the input tensor of the package with `inputs`.
   - Equal: each raw value of the package must be within `raw_limit` of the stored value. For a
     peak, the value of the package at the stored bin must be within `raw_limit` of the stored
     value.
   - Not equal: the session reports "raw check not run: input differs" for the item. This is not
     a failure. A crop of two OpenCV builds can differ.
3. Compare the final output of the package with the final values, for each item.
   - `object_detector`: pair each stored row with the package row of the same class that has the
     largest IoU. Each box coordinate must be within `box` times the resize scale of the image,
     and each score within `score`. A row that only one side keeps passes in two cases: its score
     is within `score` of `min_score` or of `nms.score_threshold`; or its IoU with a kept box can
     be on the other side of `nms.iou_threshold` when each coordinate of the two boxes moves by at
     most `box`. There is no other margin.
   - `keypoint_detector`: a keypoint is an outlier when it is more than `bins` bins of the SimCC
     output away on an axis, in the model-input space of the person, or when only one side gives
     it. The median over the persons of the fraction of outliers must be `outlier_fraction` or
     smaller. There is no rule for the largest distance: one changed bin inside the export error
     can move a keypoint far.
4. The reference files do not check a GPU EP. `certify` compares each GPU EP with the CPU run of
   the package, with the thresholds of the EP catalog.

At landing, the session copies `parity/` byte for byte to
`specs/model-sidecar/parity/<model_id>/` ([Tracked records](hand-over.md#tracked-records)).

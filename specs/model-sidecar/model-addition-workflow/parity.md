# Parity

Parity compares the sidecar path with the upstream library on real images. Phase 1 (step 5) and
phase 2 (part 5) use these rules.

The sidecar path is your host implementation of each section (in an exporter, the host
implementation of the exporter). It does the
preprocessing and the decode exactly as the sidecar declares. Write it from the spec text. In phase 2,
the reference implementation of the proposal replaces the missing spec feature.

- If a section has test vectors, your host implementation must pass them first.
- If a reference implementation of the section exists, use it or match it.
- If no reference implementation of the section exists, your plan must include the
  reference-implementation step (see
  [Reference implementations](reference-implementations.md#reference-implementations)).

Do these steps:

1. Set the gate of each compared quantity before the run. Record each gate and its source
   ([ADR-JC4T](../../../decisions/JC4T-parity-gates-and-batch-conversion-check.md)).
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
3. Measure the export error. Give the tensor of the upstream preprocessing to the ONNX file. Compare
   its outputs with the outputs of the upstream model on the same tensor.
4. Compare the preprocessed input. Compare the tensor of the sidecar path with the tensor of the
   upstream preprocessing. Give the maximum absolute difference for each image. Expect 0. If it is
   not 0, find the cause and write it. If the cause is a property of the model or of the upstream
   code, the row of that property is not `exact`. If the cause is outside both (for example two
   different OpenCV versions), remove it, or give its maximum and its cause.
5. Compare each final output of each role of the sidecar. The section of the role defines its final
   outputs ([ADR-JC4T](../../../decisions/JC4T-parity-gates-and-batch-conversion-check.md)).
   - the row count of each image;
   - for the `object_detector` role: the boxes, the scores and the classes, with box AP or per-row
     box differences;
   - for the `pose_estimator` role: the keypoints and the keypoint scores, with OKS or per-point
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
   scripts. If your repo has no such folder, use `notes/decisions/scripts/` (OpenMMLab-Exporter
   uses it).
7. If you cannot run the check, or if you cannot commit the script, write `to run` as the result.
   Give the reason. Describe the script and its gates. You can write the numbers of a run without a
   commit, but they are not evidence.
8. Unless the fields give `batch_forced`, the
   [batch-conversion check](hand-over.md#batch-conversion-check) of phase 1 (step 1b) is the
   parity check of the generated batch artifacts
   ([ADR-JB5J](../../../decisions/JB5J-one-batch-form-for-each-sidecar.md)). Its tolerance is in the authoring guidance of
   [`common.batch_conversion`](../common/batch-conversion.md#authoring-guidance). Do not make the
   tolerance larger.

If the upstream has no Python API (for example, it runs only in C++), take the reference output from
the upstream runtime itself, for example from a build of the upstream that writes its tensors. Do not
use your own copy of the upstream algorithm as the reference. If you cannot run the upstream, the
result is `to run`.

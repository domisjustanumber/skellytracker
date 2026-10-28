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

1. Set the gate of each compared quantity before the run. Use your own gate (AP or OKS),
   or the numeric floor of the upstream, for example the float32 noise of the upstream computation.
   Record each gate and its source.
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
5. Compare the final outputs in source-image coordinates (after the unprojection):
   - the row count of each image;
   - for the `object_detector` role: the boxes, the scores and the classes, with box AP or per-row
     box differences;
   - for the `pose_estimator` role: the keypoints and the keypoint scores, with OKS or per-point
     differences.

   A model with both roles needs both comparisons. A keypoint metric does not check the boxes.
   Compare the result with the export error of step 3. The error above the export error comes from
   the sidecar path.
6. Commit the parity script in your repo, so that a commit can be cited. A script that is
   only in the local `plans/` folder or only in a bundle is not evidence. A tracked copy of a bundle
   file is evidence ([Tracked records](hand-over.md#tracked-records)), but the script must still
   have a commit in your repo. Use the folder of your repo for evidence
   scripts. If your repo has no such folder, use `notes/decisions/scripts/` (OpenMMLab-Exporter
   uses it).
7. If you cannot run the check, or if you cannot commit the script, write `to run` as the result.
   Give the reason. Describe the script and its gates. You can write the numbers of a run without a
   commit, but they are not evidence.

If the upstream has no Python API (for example, it runs only in C++), take the reference output from
the upstream runtime itself, for example from a build of the upstream that writes its tensors. Do not
use your own copy of the upstream algorithm as the reference. If you cannot run the upstream, the
result is `to run`.

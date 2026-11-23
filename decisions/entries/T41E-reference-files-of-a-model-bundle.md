# T41E — Reference files of a `model` bundle: `parity/parity.yaml` and one array file for each size and precision

**Status:** absorbed into [Reference files](../../specs/model-sidecar/model-addition-workflow/parity.md#reference-files), [Manifest](../../specs/model-sidecar/model-addition-workflow/parity.md#manifest), [Array files](../../specs/model-sidecar/model-addition-workflow/parity.md#array-files), [The gate on the reference files](../../specs/model-sidecar/model-addition-workflow/parity.md#the-gate-on-the-reference-files), [Payload](../../specs/model-sidecar/model-addition-workflow/hand-over.md#payload), [Tracked records](../../specs/model-sidecar/model-addition-workflow/hand-over.md#tracked-records), [Acceptance gate: Steps](../../.claude/skills/implement-sidecar-section/proposal-gate.md#steps), [`intake_bundle.py`](../../tools/intake_bundle.py), 2026-11-23 (user; PR: pending). It was `accepted` on 2026-11-23.

## Decision

The user decided each item on 2026-11-23.

1. **Content.** The reference of the model gate is the final result of the upstream library, plus
   a sample of raw values: the highest rows or the peaks, and values chosen with a seed.
2. **Files.** A `model` bundle holds them in `parity/`: one manifest `parity.yaml` and one array
   file `<size>.<precision>.npz` for each published size and precision. Each array file is 256 KiB
   or smaller. skellytracker tracks a byte copy in `specs/model-sidecar/parity/<model_id>/`.
3. **Images.** No image goes into a bundle or into git. The manifest names a dataset image by its
   ID and the SHA-256 of its file, and a made image by its recipe and the SHA-256 of its pixels.
   The session reports and skips a made image that it cannot reproduce. A run with fewer than half
   of its images fails.
4. **Stop-gap.** The image list is the list of the existing parity runs of the exporter, from COCO
   val2017. It stays only until freemocap makes its own recording. The manifest marks each such
   image with `stop_gap: true`.
5. **Sources.** The raw sample comes from the exported ONNX file on the CPU EP. The final result
   comes from the upstream library.
6. **Raw check.** The manifest stores the SHA-256 of each input tensor. The raw check of an item
   runs, with a strict limit, only when the package reproduces that tensor. If not, the session
   reports the item and the item does not fail.
7. **Final check, no extra margin.** For an object detector: each box within the stored export
   error, scaled to source pixels, and each score within the stored score error. A box that only
   one side keeps passes when its score is within the score error of a threshold, or when its
   overlap with a kept box is within the box error of the NMS limit. For a keypoint detector: the
   median over the persons of the fraction of keypoints that are more than one bin away is at most
   0.15. There is no rule for the largest distance.
8. **Sample size.** For an object detector, for each image: the 100 rows with the highest score
   and 200 rows chosen with the seed. For a keypoint detector: the peak bin and its value for each
   keypoint and output, and 4096 values chosen with the seed for each array file.
9. **Chain.** The reference files check the CPU run of the package. `certify` checks each GPU EP
   against that CPU run, with the thresholds of the EP catalog.

## Reason

- The acceptance gate needs the `parity/` output of a bundle, and no bundle had one
  ([ADR-GPW6](GPW6-model-gate-of-the-first-models.md)).
- A vector file cannot hold the output of a real model on an image.
- The freemocap sample data has one person. The target is 1 person now and about 5 people later.
- The photos of the existing image lists have these licences in the COCO annotation file: 9 of 21
  are Attribution, 1 is Attribution-ShareAlike, 6 are NonCommercial and 5 are
  NonCommercial-NoDerivs. A changed copy of such a photo cannot go into a public repository.

## Evidence

Measured on 2026-11-23 on one Windows system, on the CPU EP: ONNX Runtime 1.30.0, NumPy 2.5.5 and OpenCV 5.1.0,
with the worker files of the parity runs of OpenMMLab-Exporter (18 images of `yolox-person`, 49
persons of `rtmw-wholebody133`, each size, fp32 and fp16). The script
[`t41e_raw_limit.py`](../scripts/t41e_raw_limit.py) gave the session, input and raw values. The
crop comparison and the file sizes came from short checks that are not tracked.

- **Session.** The session of the package and a default ONNX Runtime session give equal raw values
  for equal input tensors, bit for bit, for each file.
- **`yolox-person` input.** The tensor of the package equals the upstream tensor for each image.
- **`rtmw-wholebody133` input.** 12.7% of the tensor values of the package differ from the upstream
  tensor. `cv2.warpAffine` of OpenCV 5.1.0 with the upstream matrix gives a crop that differs from
  the crop of OpenCV 4.5.4 by at most 4 grey levels. The raw values then differ by at most 0.16
  (`m`), 0.22 (`l-256`), 0.85 (`l-384`) and 1.64 (`x-384`). The export error of `x-384` is 0.28 to
  0.45. This is the reason for item 6.
- **A session with no graph optimization and one thread**, as a stand-in for another CPU. Against
  the default session: `yolox-person` boxes 0.005 px and scores 0.00001 (fp32), boxes 0.63 px and
  scores 0.0002 (fp16); `rtmw-wholebody133` raw values 0.0011 (fp32) and 0.0013 (fp16). The
  starting values of `raw_limit` are about 10 times these values.
- **File size.** An array file with the sample of item 8 and the upstream arrays is 145 KB to
  151 KB for `yolox-person` and 139 KB to 146 KB for `rtmw-wholebody133`, with one precision.
- Not measured: another CPU, Linux, a made image on a second OpenCV build, and the count of the
  rows that only one side keeps.

## Alternatives rejected

- **Images in the bundle.** The licences of 11 of the 21 photos do not permit it, and a camera
  frame does not go into git.
- **One array file for each size, with both precisions.** About 93% of the limit for
  `yolox-person`, by an estimate. It leaves no space for more images.
- **One loose limit for the raw check.** It needs a limit near 2 for `x-384`, so it finds only a
  gross error.
- **A margin on the final check, for example 2 times.** An error of the size of the export error
  then passes.
- **Each box needs a partner.** The gate run of [ADR-GPW6](GPW6-model-gate-of-the-first-models.md)
  found rows that only one side keeps, each with a cause in the export error.

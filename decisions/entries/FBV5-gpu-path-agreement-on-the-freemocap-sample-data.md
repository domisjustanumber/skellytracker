# FBV5 — Agreement of the GPU decode and the GPU preprocess with the CPU path on the freemocap sample data

**Status:** evidence, 2026-11-19 (measurement of 2026-11-18; PR: pending).

## Decision

"CPU path" is the CPU decode and the CPU preprocess. "GPU path" is JPEG input with the GPU decode and
the GPU preprocess. The numbers are the difference of one keypoint in source pixels, median / p99,
over the points with a score above 0.4 in both runs.

1. Two runs of one path on one EP are equal bit for bit (`cuda` and `trt-rtx`).
2. GPU path against CPU path: 1.18 / 7.55 on `cuda`, and 1.33 / 7.92 on `trt-rtx`.
3. The yardstick, the CPU path on two EPs: 1.26 / 7.87 for `cuda` against `cpu`, and 1.29 / 7.78 for
   `cuda` against `trt-rtx`. The GPU path thus differs from the CPU path as much as one EP differs
   from another EP.
4. The GPU decode adds no difference that the measurement can show. With the GPU preprocess, array
   input and JPEG input with the CPU decode are equal bit for bit. JPEG input with the GPU decode
   gives 1.18 / 7.55 against 1.14 / 7.47 (`cuda`). On 150 frames of this data, the GPU decode
   differs from `cv2.imdecode` by at most 3 `uint8` steps, mean 0.018, and 1.6 % of the values
   differ.
5. The difference does not grow with time. With a detector call at each frame, the median is 0.11
   (`cuda`, GPU path against CPU path) and 0.18 (`cuda` against `cpu`). The feedback from the
   keypoints to the crop box raises it to about 1.2. The median of each block of 100 frames stays
   between 0.55 and 1.64 with no trend.
6. 0.25 to 0.28 % of the points cross the score 0.4 in each pair, also in the yardstick.
7. The maximum is 320 to 326 px in each pair, and 281 to 323 px in the yardstick. It comes from a
   few frames in which the model moves a whole hand. The same frames are the worst frames of the
   yardstick.
8. On `cuda`, the GPU path ran the detector 45 times and the CPU path 47 times, and 2 camera frames
   have a different person count. `cuda` against `cpu` has 1 such frame.
9. JPEG quality 75, first 300 frames, `cuda`: GPU path against CPU path 1.23 / 10.87, with 0.60 % of
   the points across the score 0.4. Quality 90 on the same frames gives 1.30 / 9.13 and 0.57 %.

## Evidence

- Data: the freemocap sample data, a public sample recording of the freemocap project. 3 cameras
  at 720x1280, 1108 frames, one person. The script read the zip file locally. The repository does
  not hold the recording, its frames or the JPEG files, and the run deleted its extracted files.
  `cv2.imencode` encoded each video frame again as JPEG at quality 90 (mean 145 kB) and 75 (mean
  87 kB).
- The built-in pipeline `yolox-rtmw-wholebody` with no config change, running mode `video`, all
  cameras in one call. 133 model points, about 424 000 points with a score above 0.4 in each pair.
- Hardware and versions as in
  [ADR-1SZ9](1SZ9-gpu-preprocess-and-gpu-jpeg-decode-in-the-pipeline-run.md): one RTX 3070, ONNX
  Runtime 1.31.1, `cuda-cu13` 0.3.0, `trt-rtx-cu13` 0.5.0, nvImageCodec 0.10.0.9. These numbers
  come from 1.31.1 and 0.3.0, before the move to 1.30.0 and 0.2.0. A repeat on the pinned versions
  is open work. One run for each mode.
- Limits: one recording, JPEG made from decoded video and not from a camera, rotation 0 only, no
  ground truth. These are agreement numbers, not accuracy numbers.
- The scripts are in [`fbv5_sample_data_agreement/`](../scripts/fbv5_sample_data_agreement/):
  `prepare.py` (the extraction and the JPEG encode), `measure.py` (one mode: `R` CPU path, `A1`
  array input with the GPU preprocess, `J2` JPEG input with the CPU decode and the GPU preprocess,
  `J3` GPU path, `DEC` decode only), `driver.py`, `analyze.py`, `report_tables.py`,
  `schema_probe.py`, the plans and `data_probe.json`. `tables.txt` holds the output of
  `report_tables.py` and the decode check. Not kept: the JSON and `.npz` output of each run
  (keypoint arrays), and `analysis.json` (200 kB; `tables.txt` gives its numbers).

## Open work

See [open-work.md](../open-work.md).

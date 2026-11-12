# Evidence: verification-batches

This file gives the measurements of part 5 of `proposal.md`.

## Method

The script is `decisions/scripts/batch_conversion_n_variant.py` of OpenMMLab-Exporter (commit
9810e483c69efddea7a8b93e671d6250eb47c5f0). It has two modes. Both run from the exporter repo root.

1. `inputs` (OpenMMLab-Exporter environment). It writes input B with 6 items for each size. It uses
   the functions of the hand-over tool of the exporter: `select_images` with `count=6` and
   `write_input_b` of `pipeline/handover.py`. The images are the 6 COCO val2017 images with the
   lowest ids that have a non-crowd person box: 139, 785, 872, 885, 1000 and 1268. Items 1 to 4 are
   byte-equal (`np.array_equal`, same dtype) to the 4 items of the hand-over input B of each size of
   both families (11 of 11 sizes).
2. `check` (skellytracker environment: Python 3.12.13, NumPy 2.4.6, onnx 1.22.0, onnxruntime 1.27.0,
   CPU). It loads `tools/intake_bundle.py` of the checkout at `8351b7f8c20c8db74eb3e547478970e4dceb0308`
   and uses its `_Runner` (input A, input B, the run and the V5 comparison), `TOLERANCE`,
   `SOURCE_BATCH` (3), `PROFILE` and `onnx_problems`. V3 is `model_batch_convert` of the checkout,
   with the same profile dict as `batch_check`. V5 runs the converted file and the native bN file on
   input A (seed 42, uniform in [0, 1)) and on the first N items of input B. The tolerance is
   `rtol=atol=1e-3` (fp16) and `1e-5` (fp32). The control compares each tuple of N = 1, 2 and 4
   with the tuple of the hand-over `payload/batch/report.json` of `tools/intake_bundle.py batch`
   (same skellytracker environment, spec commit `b0dfe0bd2730fc36896c948ddd017f2ce5067ecb`): the
   source and native SHA-256, the V3 and V5 results and the `max_abs` of each output.

The ONNX files are the exports of OpenMMLab-Exporter of 2026-11-04 in
`exports/detectors/object_detectors/yolox-person/` (6 sizes) and
`exports/detectors/keypoint_detectors/rtmw/wholebody133/` (5 sizes), fp32 and fp16, at the batches
1, 2, 3, 4 and 6. The manifest `external` lists each file with its SHA-256.

## Results

| Run | Tuples | V3 pass | V5 pass | Largest max abs diff | Equal to the hand-over report |
|---|---|---|---|---|---|
| N = 1, 2 and 6 | 66 | 66 | 66 | 0.0 | 44 of 44 (N = 1 and 2) |
| N = 1, 2 and 4 | 66 | 66 | 65 | 0.75 | 65 of 66 |

The one failed tuple is `yolox-person` `l` fp16 at N = 4: input A, output `boxes`, max abs diff
0.75 (`scores` 3.3e-07). Input B of the same run gives 0.0. The hand-over report of the same two
files gives 0.0 on input A and on input B. The section "Run-to-run noise" gives the cause.

Each tuple:

| Model | Size | Precision | N | V3 | V5 | max abs A | max abs B | Equal to hand-over report |
|---|---|---|---|---|---|---|---|---|
| `yolox-person` | `n` | fp32 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `n` | fp32 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `n` | fp32 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `n` | fp32 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `yolox-person` | `n` | fp16 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `n` | fp16 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `n` | fp16 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `n` | fp16 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `yolox-person` | `t` | fp32 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `t` | fp32 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `t` | fp32 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `t` | fp32 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `yolox-person` | `t` | fp16 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `t` | fp16 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `t` | fp16 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `t` | fp16 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `yolox-person` | `s` | fp32 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `s` | fp32 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `s` | fp32 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `s` | fp32 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `yolox-person` | `s` | fp16 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `s` | fp16 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `s` | fp16 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `s` | fp16 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `yolox-person` | `m` | fp32 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `m` | fp32 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `m` | fp32 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `m` | fp32 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `yolox-person` | `m` | fp16 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `m` | fp16 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `m` | fp16 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `m` | fp16 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `yolox-person` | `l` | fp32 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `l` | fp32 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `l` | fp32 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `l` | fp32 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `yolox-person` | `l` | fp16 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `l` | fp16 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `l` | fp16 | 4 | pass | fail | 0.75 | 0.0 | NO |
| `yolox-person` | `l` | fp16 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `yolox-person` | `x` | fp32 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `x` | fp32 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `x` | fp32 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `x` | fp32 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `yolox-person` | `x` | fp16 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `x` | fp16 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `x` | fp16 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `yolox-person` | `x` | fp16 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `rtmw-wholebody133` | `m` | fp32 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `m` | fp32 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `m` | fp32 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `m` | fp32 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `rtmw-wholebody133` | `m` | fp16 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `m` | fp16 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `m` | fp16 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `m` | fp16 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `rtmw-wholebody133` | `l-256` | fp32 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `l-256` | fp32 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `l-256` | fp32 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `l-256` | fp32 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `rtmw-wholebody133` | `l-256` | fp16 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `l-256` | fp16 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `l-256` | fp16 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `l-256` | fp16 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `rtmw-wholebody133` | `x-256` | fp32 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `x-256` | fp32 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `x-256` | fp32 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `x-256` | fp32 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `rtmw-wholebody133` | `x-256` | fp16 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `x-256` | fp16 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `x-256` | fp16 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `x-256` | fp16 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `rtmw-wholebody133` | `l-384` | fp32 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `l-384` | fp32 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `l-384` | fp32 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `l-384` | fp32 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `rtmw-wholebody133` | `l-384` | fp16 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `l-384` | fp16 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `l-384` | fp16 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `l-384` | fp16 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `rtmw-wholebody133` | `x-384` | fp32 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `x-384` | fp32 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `x-384` | fp32 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `x-384` | fp32 | 6 | pass | pass | 0.0 | 0.0 | n/a |
| `rtmw-wholebody133` | `x-384` | fp16 | 1 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `x-384` | fp16 | 2 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `x-384` | fp16 | 4 | pass | pass | 0.0 | 0.0 | yes |
| `rtmw-wholebody133` | `x-384` | fp16 | 6 | pass | pass | 0.0 | 0.0 | n/a |

In this table, the rows of N = 1 and 2 come from the run of N = 1, 2 and 6. The run of N = 1, 2 and 4
gives the same V3 and V5 results and 0.0 for these rows. "n/a" means that the hand-over report has no
tuple of that N.

## Run-to-run noise

The failed tuple (`yolox-person` `l` fp16, N = 4) uses the same two files (same SHA-256), the same
input A, the same converter and the same environment as the hand-over report, which gives 0.0. Thus
the difference comes from the run, not from the conversion. A max abs diff of 0.75 on `boxes` is 1
to 3 fp16 steps for a value between 256 and 1024 (one step is 0.25 or 0.5). The fp16 tolerance
`rtol=atol=1e-3` allows about 0.5 for a value of 500.

The repeat run (`--repeats 20`) runs V5 of a tuple 20 times. Each repeat after the first makes new
onnxruntime sessions, compares the converted file with a new native run, and compares the new native
run with the first native run (`native_self`, the noise floor of the runtime):

| Tuple | Repeats (input A and input B each) | Converted fails | `native_self` fails | Largest max abs diff |
|---|---|---|---|---|
| `yolox-person` `l` fp16, N = 4 | 20 | 0 | 0 | 0.0 |
| `yolox-person` `l` fp16, N = 6 | 20 | 0 | 0 | 0.0 |
| `yolox-person` `x` fp16, N = 4 | 20 | 0 | 0 | 0.0 |
| `yolox-person` `x` fp16, N = 6 | 20 | 0 | 0 | 0.0 |

The failure did not come back in these 160 runs. It is rare. Its cause is not known. A possible cause
is the thread scheduling of onnxruntime CPU (default thread count, 28 logical processors), with other
work on the same computer during the first run. This noise can also fail a tuple of N = 6. It does
not depend on the choice of the verification batches, so it does not change this proposal. It can
give a false `does not convert` verdict for an fp16 family in any run of `batch`. The session can
decide if `batch` needs a fixed thread count or a repeat of a failed fp16 tuple. This proposal does
not propose it.

## Commands

From the exporter repo root:

```sh
uv run python decisions/scripts/batch_conversion_n_variant.py inputs --out <evidence>/inputs --items 6 --handover <hand-over root>
uv run --project ../freemocap/skellytracker --no-sync python -B decisions/scripts/batch_conversion_n_variant.py check --inputs <evidence>/inputs --targets 1,2,6 --out <evidence>/check-1-2-6.json --handover <hand-over root>
uv run --project ../freemocap/skellytracker --no-sync python -B decisions/scripts/batch_conversion_n_variant.py check --inputs <evidence>/inputs --targets 1,2,4 --out <evidence>/check-1-2-4.json --handover <hand-over root>
uv run --project ../freemocap/skellytracker --no-sync python -B decisions/scripts/batch_conversion_n_variant.py check --inputs <evidence>/inputs --models yolox-person --only yolox-person:l:fp16,yolox-person:x:fp16 --targets 4,6 --repeats 20 --out <evidence>/repeats-yolox-l-x-fp16-4-6.json --handover <hand-over root>
```

`<hand-over root>` is the local hand-over folder of the exporter, written by
`export_all.py --handover`. It holds the hand-over input B and `payload/batch/report.json` of each
family. The JSON reports of the runs are not in the bundle. The exporter keeps them.

## Follow-up: the fp16 noise and the onnxruntime version

A repeat test of the noisy pair (yolox-person `l` fp16, converted b4 against native b4), 100 fresh CPU
sessions each, on input A and input B: onnxruntime 1.27.0 gives 3 of 100 runs that differ on input B
(max 0.5); onnxruntime 1.31.0 and 1.31.1 give 0 of 100 on both inputs (max 0.0). The noise is a
property of onnxruntime 1.27.0 CPU on fp16. An environment with onnxruntime 1.31 or later removes it.

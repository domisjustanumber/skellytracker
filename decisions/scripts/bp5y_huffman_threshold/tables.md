## Pipeline yolox-rtmw-wholebody, M3 (JPEG, GPU decode, GPU preprocess), P1 cadence, 30 warm-up + 300 measured calls
Values: median / p95 / max (ms). CPU: process_time per call, one value per block of 25 calls (12 blocks); mean in brackets.
VRAM: process VRAM from LiveSampler (NVML), max of the samples before start, after start, at the first measured call, at the end.

| config | run | frame.decode | wall per call | CPU per call | VRAM peak MiB | det calls | warnings | option seen |
|---|---|---|---|---|---|---|---|---|
| trt-rtx_720x3 | off r1 | 2.36 / 2.75 / 3.18 | 6.61 / 7.58 / 17.56 | 10.00 / 11.81 / 12.50 (9.64) | 427 | 12 | none | False |
| trt-rtx_720x3 | on r1 | 1.38 / 1.75 / 3.25 | 5.47 / 6.72 / 15.84 | 7.81 / 11.81 / 12.50 (8.18) | 427 | 12 | none | True |
| trt-rtx_720x3 | off r2 | 2.40 / 2.79 / 3.46 | 6.94 / 8.10 / 17.46 | 9.06 / 13.84 / 16.25 (10.00) | 427 | 12 | none | False |
| trt-rtx_720x3 | on r2 | 1.41 / 1.78 / 2.54 | 5.69 / 6.78 / 15.88 | 8.44 / 10.62 / 10.62 (8.54) | 427 | 12 | none | True |
| trt-rtx_720x6 | off r1 | 2.73 / 3.26 / 6.00 | 10.78 / 27.45 / 30.15 | 19.38 / 29.62 / 33.75 (19.95) | 555 | 33 | none | False |
| trt-rtx_720x6 | on r1 | 2.50 / 3.01 / 4.63 | 10.24 / 27.37 / 29.25 | 14.38 / 22.62 / 28.12 (15.10) | 555 | 33 | none | True |
| trt-rtx_720x6 | off r2 | 2.63 / 3.04 / 3.57 | 10.29 / 27.06 / 28.82 | 16.56 / 23.50 / 26.25 (16.20) | 555 | 33 | none | False |
| trt-rtx_720x6 | on r2 | 2.34 / 2.91 / 3.58 | 9.88 / 26.22 / 28.89 | 15.94 / 23.56 / 25.62 (16.72) | 555 | 33 | none | True |
| cuda_720x3 | off r1 | 2.46 / 2.97 / 3.64 | 12.75 / 17.65 / 36.51 | 16.88 / 20.28 / 20.62 (16.30) | 1037 | 12 | none | False |
| cuda_720x3 | on r1 | 1.54 / 2.07 / 2.54 | 11.84 / 18.21 / 34.42 | 13.12 / 20.56 / 21.25 (14.01) | 1035 | 12 | none | True |
| cuda_720x3 | off r2 | 3.02 / 5.02 / 32.07 | 13.55 / 44.77 / 96.39 | 15.94 / 21.69 / 23.75 (16.56) | 1037 | 12 | none | False |
| cuda_720x3 | on r2 | 1.43 / 1.78 / 2.00 | 10.83 / 15.47 / 32.89 | 12.81 / 16.97 / 19.38 (13.33) | 1035 | 12 | none | True |
| cuda_720x6 | off r1 | 3.17 / 3.53 / 19.45 | 19.60 / 82.77 / 184.01 | 31.25 / 41.75 / 43.12 (31.20) | 1677 | 33 | none | False |
| cuda_720x6 | on r1 | 2.09 / 2.48 / 2.98 | 16.63 / 52.42 / 56.98 | 21.56 / 39.12 / 41.88 (24.43) | 1675 | 33 | none | True |
| cuda_720x6 | off r2 | 2.50 / 2.89 / 3.26 | 16.92 / 52.60 / 55.76 | 25.00 / 41.84 / 52.50 (27.19) | 1683 | 33 | none | False |
| cuda_720x6 | on r2 | 2.02 / 2.39 / 3.01 | 16.66 / 52.95 / 57.02 | 21.56 / 41.72 / 46.88 (25.16) | 1677 | 33 | none | True |
| trt-rtx_1080x3 | off r1 | 1.97 / 2.36 / 4.90 | 6.20 / 7.25 / 19.59 | 8.75 / 11.41 / 13.12 (8.96) | 587 | 2 | none | False |
| trt-rtx_1080x3 | on r1 | 1.91 / 2.27 / 2.71 | 6.10 / 6.74 / 19.10 | 8.12 / 9.66 / 10.00 (8.12) | 587 | 2 | none | True |
| trt-rtx_1080x3 | off r2 | 1.80 / 2.13 / 2.56 | 5.73 / 6.39 / 18.41 | 8.12 / 11.19 / 11.88 (8.59) | 587 | 2 | none | False |
| trt-rtx_1080x3 | on r2 | 1.83 / 2.11 / 2.59 | 5.77 / 6.31 / 18.38 | 7.50 / 9.03 / 9.38 (7.50) | 587 | 2 | none | True |
| cuda_1080x3 | off r1 | 2.28 / 2.65 / 3.16 | 13.83 / 17.78 / 37.45 | 15.31 / 17.72 / 18.75 (15.52) | 1521 | 2 | none | False |
| cuda_1080x3 | on r1 | 2.29 / 2.60 / 3.72 | 13.61 / 16.04 / 37.50 | 15.31 / 19.66 / 20.00 (15.73) | 1519 | 2 | none | True |
| cuda_1080x3 | off r2 | 2.39 / 2.86 / 3.76 | 14.04 / 17.47 / 39.13 | 15.00 / 18.34 / 19.38 (15.36) | 1525 | 2 | none | False |
| cuda_1080x3 | on r2 | 2.24 / 2.57 / 4.77 | 13.43 / 14.74 / 38.79 | 15.00 / 18.69 / 19.38 (15.68) | 1521 | 2 | none | True |

## Mean of the 2 repeats (medians), on minus off

| config | decode off | decode on | delta | wall off | wall on | delta | CPU mean off | CPU mean on | delta | VRAM off | VRAM on |
|---|---|---|---|---|---|---|---|---|---|---|---|
| trt-rtx_720x3 | 2.38 | 1.39 | -0.98 | 6.77 | 5.58 | -1.19 | 9.82 | 8.36 | -1.46 | 427 | 427 |
| trt-rtx_720x6 | 2.68 | 2.42 | -0.26 | 10.53 | 10.06 | -0.47 | 18.07 | 15.91 | -2.16 | 555 | 555 |
| cuda_720x3 | 2.74 | 1.48 | -1.26 | 13.15 | 11.34 | -1.81 | 16.43 | 13.67 | -2.76 | 1037 | 1035 |
| cuda_720x6 | 2.84 | 2.06 | -0.78 | 18.26 | 16.64 | -1.61 | 29.19 | 24.79 | -4.40 | 1680 | 1676 |
| trt-rtx_1080x3 | 1.88 | 1.87 | -0.01 | 5.96 | 5.93 | -0.03 | 8.78 | 7.81 | -0.96 | 587 | 587 |
| cuda_1080x3 | 2.33 | 2.26 | -0.07 | 13.93 | 13.52 | -0.41 | 15.44 | 15.70 | +0.26 | 1523 | 1520 |

## Pipeline outputs, on vs off (same repeat, same frame sequence)

| config | run | keypoint xy max abs diff | score max abs diff | box max abs diff | present differs | detector-ran differs |
|---|---|---|---|---|---|---|
| trt-rtx_720x3 | r1 | 0.0000 | 0.00000 | 0.0000 | 0 | 0 |
| trt-rtx_720x3 | r2 | 0.0000 | 0.00000 | 0.0000 | 0 | 0 |
| trt-rtx_720x6 | r1 | 0.0000 | 0.00000 | 0.0000 | 0 | 0 |
| trt-rtx_720x6 | r2 | 0.0000 | 0.00000 | 0.0000 | 0 | 0 |
| cuda_720x3 | r1 | 0.0000 | 0.00000 | 0.0000 | 0 | 0 |
| cuda_720x3 | r2 | 0.0000 | 0.00000 | 0.0000 | 0 | 0 |
| cuda_720x6 | r1 | 0.0000 | 0.00000 | 0.0000 | 0 | 0 |
| cuda_720x6 | r2 | 0.0000 | 0.00000 | 0.0000 | 0 | 0 |
| trt-rtx_1080x3 | r1 | 0.0000 | 0.00000 | 0.0000 | 0 | 0 |
| trt-rtx_1080x3 | r2 | 0.0000 | 0.00000 | 0.0000 | 0 | 0 |
| cuda_1080x3 | r1 | 0.0000 | 0.00000 | 0.0000 | 0 | 0 |
| cuda_1080x3 | r2 | 0.0000 | 0.00000 | 0.0000 | 0 | 0 |

## NvJpegDecoder alone (cuda EP device, 200 batches per block, 5 measured rounds + 1 warm-up, order rotated)

Wall per batch median / p95 / max (ms); CPU per batch = process_time of a block / 200, median / p95 / max over the 5 blocks.

| run | size | N | huff | wall | CPU |
|---|---|---|---|---|---|
| dec_1 | 320x240 | 3 | off | 0.477 / 0.569 / 1.501 | 1.172 / 1.172 / 1.172 |
| dec_1 | 320x240 | 3 | on | 0.653 / 0.886 / 2.100 | 1.328 / 1.484 / 1.484 |
| dec_1 | 320x240 | 6 | off | 0.580 / 0.705 / 1.607 | 2.109 / 2.500 / 2.500 |
| dec_1 | 320x240 | 6 | on | 1.216 / 1.524 / 3.079 | 3.438 / 4.297 / 4.297 |
| dec_1 | 640x480 | 3 | off | 1.020 / 1.289 / 2.144 | 2.344 / 2.812 / 2.812 |
| dec_1 | 640x480 | 3 | on | 0.850 / 1.122 / 1.950 | 1.953 / 2.188 / 2.188 |
| dec_1 | 640x480 | 6 | off | 1.183 / 1.493 / 4.248 | 4.766 / 6.094 / 6.094 |
| dec_1 | 640x480 | 6 | on | 1.495 / 1.892 / 3.311 | 3.984 / 4.453 / 4.453 |
| dec_1 | 1280x720 | 3 | off | 2.331 / 2.851 / 3.700 | 4.453 / 5.312 / 5.312 |
| dec_1 | 1280x720 | 3 | on | 1.298 / 1.671 / 2.153 | 2.578 / 3.125 / 3.125 |
| dec_1 | 1280x720 | 6 | off | 2.711 / 3.107 / 3.844 | 9.375 / 11.484 / 11.484 |
| dec_1 | 1280x720 | 6 | on | 1.818 / 2.200 / 3.475 | 6.875 / 7.734 / 7.734 |
| dec_2 | 320x240 | 3 | off | 0.456 / 0.611 / 1.495 | 1.094 / 1.641 / 1.641 |
| dec_2 | 320x240 | 3 | on | 0.619 / 0.848 / 1.954 | 1.250 / 1.797 / 1.797 |
| dec_2 | 320x240 | 6 | off | 0.527 / 0.679 / 1.642 | 1.875 / 2.734 / 2.734 |
| dec_2 | 320x240 | 6 | on | 1.114 / 1.346 / 2.453 | 2.891 / 3.828 / 3.828 |
| dec_2 | 640x480 | 3 | off | 0.961 / 1.171 / 1.742 | 1.875 / 2.266 / 2.266 |
| dec_2 | 640x480 | 3 | on | 0.856 / 1.062 / 2.225 | 1.484 / 2.578 / 2.578 |
| dec_2 | 640x480 | 6 | off | 1.136 / 1.418 / 2.138 | 4.453 / 5.312 / 5.312 |
| dec_2 | 640x480 | 6 | on | 1.429 / 2.087 / 2.703 | 4.062 / 5.859 / 5.859 |
| dec_2 | 1280x720 | 3 | off | 2.270 / 2.560 / 3.384 | 4.844 / 5.234 / 5.234 |
| dec_2 | 1280x720 | 3 | on | 1.336 / 1.660 / 2.253 | 2.578 / 3.281 / 3.281 |
| dec_2 | 1280x720 | 6 | off | 2.507 / 3.275 / 3.749 | 9.375 / 10.547 / 10.547 |
| dec_2 | 1280x720 | 6 | on | 1.802 / 2.251 / 3.208 | 5.625 / 7.578 / 7.578 |

## Pixels, option on vs off (decoder alone)

- dec_1 320x240: n 8, max abs diff [0, 0, 0, 0, 0, 0, 0, 0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.036
- dec_1 640x480: n 8, max abs diff [0, 0, 0, 0, 0, 0, 0, 0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.034
- dec_1 1280x720: n 8, max abs diff [0, 0, 0, 0, 0, 0, 0, 0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.034
- dec_1 1920x1080: n 8, max abs diff [0, 0, 0, 0, 0, 0, 0, 0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.029
- dec_1 gray_1280x720: n 1, max abs diff [0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.012
- dec_1 gray_640x480: n 1, max abs diff [0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.014
- dec_1 progressive_1280x720: n 1, max abs diff [0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.021
- dec_1 progressive_640x480: n 1, max abs diff [0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.027
- dec_2 320x240: n 8, max abs diff [0, 0, 0, 0, 0, 0, 0, 0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.036
- dec_2 640x480: n 8, max abs diff [0, 0, 0, 0, 0, 0, 0, 0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.034
- dec_2 1280x720: n 8, max abs diff [0, 0, 0, 0, 0, 0, 0, 0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.034
- dec_2 1920x1080: n 8, max abs diff [0, 0, 0, 0, 0, 0, 0, 0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.029
- dec_2 gray_1280x720: n 1, max abs diff [0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.012
- dec_2 gray_640x480: n 1, max abs diff [0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.014
- dec_2 progressive_1280x720: n 1, max abs diff [0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.021
- dec_2 progressive_640x480: n 1, max abs diff [0], None (off,on) {(False, False)}, off vs cv2 mean abs max 0.027

## Log lines only with the option on (pipeline runs; digits normalised)

- (30x) cuDevicePrimaryCtxRelease failed: #

## Log lines only with the option off

- none

## Log lines in both (count off / on)

- (12 / 12) Failed to load nvjpeg#k library! Please install nvJPEG# (see https://docs.nvidia.com/cuda/nvjpeg#/userguide.html#installing-nvjpeg#).
- (12 / 12) Note: If using nvImageCodec's Python distribution, it is enough to install the nvJPEG# wheel: e.g. `python# -m pip install nvidia-nvjpeg#k-cu#`
- (12 / 12) [#;#m[ERROR] [#m[nvjpeg#k_ext] Failed to load nvJPEG# library or retrieve version. Decoders and encoders will not be registered.
- (12 / 12) Failed to load nvtiff library! Please install nvTIFF (see https://docs.nvidia.com/cuda/nvtiff/userguide.html#installing-nvtiff).
- (12 / 12) Note: If using nvImageCodec's Python distribution, it is enough to install the nvTIFF wheel: e.g. `python# -m pip install nvidia-nvtiff-cu#`
- (12 / 12) [#;#m[ERROR] [#m[nvtiff_ext] Failed to load nvTIFF library or retrieve version. Decoders and encoders will not be registered.
- (8 / 8) Corrupt JPEG data: # extraneous bytes before marker #xd#
- (6 / 6) The EP 'cuda' is in the state installed_unverified: no trial session ran yet.
- (6 / 6) The EP 'trt-rtx' is in the state untested-ort: the pack trt-rtx-cu# #.# is not tested with ONNX Runtime #.#.

## Driver log

```
dec_1: exit 0 in 21s; gpu before: quiet util,mem=14, 2364
gpu busy: pythons=[] util,mem=36, 2341
trt-rtx_720x3_off_r1: exit 0 in 7s; gpu before: quiet util,mem=7, 2338
trt-rtx_720x3_on_r1: exit 0 in 7s; gpu before: quiet util,mem=18, 2362
cuda_720x3_off_r1: exit 0 in 9s; gpu before: quiet util,mem=1, 2351
cuda_720x3_on_r1: exit 0 in 8s; gpu before: quiet util,mem=1, 2372
gpu busy: pythons=[] util,mem=72, 2342
trt-rtx_720x6_off_r1: exit 0 in 10s; gpu before: quiet util,mem=11, 2343
trt-rtx_720x6_on_r1: exit 0 in 9s; gpu before: quiet util,mem=1, 2343
cuda_720x6_off_r1: exit 0 in 16s; gpu before: quiet util,mem=2, 2347
cuda_720x6_on_r1: exit 0 in 12s; gpu before: quiet util,mem=2, 2348
trt-rtx_1080x3_off_r1: exit 0 in 7s; gpu before: quiet util,mem=1, 2342
trt-rtx_1080x3_on_r1: exit 0 in 7s; gpu before: quiet util,mem=1, 2347
cuda_1080x3_off_r1: exit 0 in 9s; gpu before: quiet util,mem=19, 2342
cuda_1080x3_on_r1: exit 0 in 9s; gpu before: quiet util,mem=2, 2346
gpu busy: pythons=[] util,mem=69, 2346
trt-rtx_720x3_on_r2: exit 0 in 7s; gpu before: quiet util,mem=7, 2345
trt-rtx_720x3_off_r2: exit 0 in 7s; gpu before: quiet util,mem=17, 2345
cuda_720x3_on_r2: exit 0 in 8s; gpu before: quiet util,mem=1, 2345
cuda_720x3_off_r2: exit 0 in 12s; gpu before: quiet util,mem=1, 2355
trt-rtx_720x6_on_r2: exit 0 in 10s; gpu before: quiet util,mem=2, 2344
trt-rtx_720x6_off_r2: exit 0 in 9s; gpu before: quiet util,mem=1, 2344
gpu busy: pythons=[] util,mem=58, 2370
cuda_720x6_on_r2: exit 0 in 12s; gpu before: quiet util,mem=7, 2347
cuda_720x6_off_r2: exit 0 in 12s; gpu before: quiet util,mem=2, 2376
trt-rtx_1080x3_on_r2: exit 0 in 7s; gpu before: quiet util,mem=1, 2365
gpu busy: pythons=[] util,mem=49, 2355
trt-rtx_1080x3_off_r2: exit 0 in 7s; gpu before: quiet util,mem=7, 2343
gpu busy: pythons=[] util,mem=46, 2354
cuda_1080x3_on_r2: exit 0 in 9s; gpu before: quiet util,mem=19, 2360
cuda_1080x3_off_r2: exit 0 in 9s; gpu before: quiet util,mem=2, 2366
gpu busy: pythons=[] util,mem=41, 2381
dec_2: exit 0 in 20s; gpu before: quiet util,mem=20, 2346

```
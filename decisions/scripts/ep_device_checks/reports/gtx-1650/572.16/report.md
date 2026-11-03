# EP device checks

- GPU: NVIDIA GeForce GTX 1650, CC 7.5, 4096 MB, PCI 10de:1f91:08ea1028
- Driver: 572.16 (max CUDA 12.8); scenario B: R570 to R579
- OS: Windows 11 build 10.0.26300; Python 3.12.13
- Mode: quick (L2, L3); precisions fp32,fp16; runs 20; duration 31 s

| Route | Predicted (L1) | Observed | Match | Stage / mode | L2 register ms | L3 session ms | L3 max diff | Install s | Download MB |
|---|---|---|---|---|---|---|---|---|---|
| cpu | ok | pass | yes | - | - | 1.2 | 0 | 0.3 | 26.8 |
| cuda-cu13 | update-driver | fail | yes | L2 no-device | 4427 | - | - | 0.6 | 1037 |
| cuda-cu12 | ok | pass | yes | - | 3343 | 1287 | 2.86e-06 | 0.3 | 1569 |
| trt-rtx-cu13 | update-driver | fail | yes | L2 no-device | 2300 | - | - | 0.2 | 132 |
| trt-rtx-cu12 | unsupported | fail | yes | L2 no-device | 2293 | - | - | 0.2 | 136 |

## Findings

- none

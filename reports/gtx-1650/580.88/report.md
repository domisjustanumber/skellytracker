# EP device checks

- GPU: NVIDIA GeForce GTX 1650, CC 7.5, 4096 MB, PCI 10de:1f91:08ea1028
- Driver: 580.88 (max CUDA 13.0); scenario C: R580 or newer
- OS: Windows 11 build 10.0.26300; Python 3.12.13
- Mode: quick (L2, L3); precisions fp32,fp16; runs 20; duration 26 s

| Route | Predicted (L1) | Observed | Match | Stage / mode | L2 register ms | L3 session ms | L3 max diff | Install s | Download MB |
|---|---|---|---|---|---|---|---|---|---|
| cpu | ok | pass | yes | - | - | 1.2 | 0 | 0.1 | 26.8 |
| cuda-cu13 | ok | pass | yes | - | 2630 | 1213 | 2.86e-06 | 0.2 | 1037 |
| cuda-cu12 | ok | pass | yes | - | 2310 | 324 | 2.86e-06 | 0.2 | 1569 |
| trt-rtx-cu13 | experimental | fail | informational | L2 no-device | 1384 | - | - | 0.1 | 132 |
| trt-rtx-cu12 | unsupported | fail | yes | L2 no-device | 1346 | - | - | 0.1 | 136 |

## Findings

- none

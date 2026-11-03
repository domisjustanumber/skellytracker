# EP device checks

- GPU: NVIDIA GeForce GTX 1650, CC 7.5, 4096 MB, PCI 10de:1f91:08ea1028
- Driver: 621.01 (max CUDA 13.5); scenario C: R580 or newer
- OS: Windows 11 build 10.0.26300; Python 3.12.13
- Mode: quick (L2, L3); precisions fp32,fp16; runs 20; duration 26 s

| Route | Predicted (L1) | Observed | Match | Stage / mode | L2 register ms | L3 session ms | L3 max diff | Install s | Download MB |
|---|---|---|---|---|---|---|---|---|---|
| cpu | ok | pass | yes | - | - | 1.3 | 0 | 0.1 | 26.8 |
| cuda-cu13 | ok | pass | yes | - | 1937 | 312 | 2.86e-06 | 0.1 | 1037 |
| cuda-cu12 | ok | pass | yes | - | 1953 | 323 | 2.86e-06 | 0.1 | 1569 |
| trt-rtx-cu13 | experimental | fail | informational | L2 no-device | 1400 | - | - | 0.1 | 132 |
| trt-rtx-cu12 | unsupported | fail | yes | L2 no-device | 1632 | - | - | 1.4 | 136 |

## Findings

- none

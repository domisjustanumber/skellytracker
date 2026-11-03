# EP device checks

- GPU: NVIDIA GeForce GTX 1650, CC 7.5, 4096 MB, PCI 10de:1f91:08ea1028
- Driver: 566.36 (max CUDA 12.7); scenario A: below R570
- OS: Windows 11 build 10.0.26300; Python 3.12.13
- Mode: quick (L2, L3); precisions fp32,fp16; runs 20; duration 97 s

| Route | Predicted (L1) | Observed | Match | Stage / mode | L2 register ms | L3 session ms | L3 max diff | Install s | Download MB |
|---|---|---|---|---|---|---|---|---|---|
| cpu | ok | pass | yes | - | - | 1 | 0 | 0.8 | 26.8 |
| cuda-cu13 | update-driver | fail | yes | L2 no-device | 554 | - | - | 19.5 | 1037 |
| cuda-cu12 | update-driver | pass | NO | - | 329 | 434 | 2.86e-06 | 34.9 | 1569 |
| trt-rtx-cu13 | update-driver | fail | yes | L2 no-device | 1322 | - | - | 5.9 | 132 |
| trt-rtx-cu12 | unsupported | fail | yes | L2 no-device | 1483 | - | - | 4.6 | 136 |

## Findings

- cuda-cu12: predicted update-driver (driver R565 is below R570; update to R570 or newer), observed pass ()

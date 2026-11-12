| row | options | model b/prec | build ms | median ms (p95) | max abs / rel | flips all/top or det ref->cfg | px err or box px | CPU nodes | VRAM MB | note |
|---|---|---|---|---|---|---|---|---|---|---|
| REF  | [so]graph_optimization_level=ORT_ENABLE_ALL | yolox b1/fp32 | 195 | 61.49 (75.69) | - | - | all | - | cpu 1244.8 ms/run |
| REF  | [so]graph_optimization_level=ORT_ENABLE_ALL | yolox b3/fp32 | 190 | 199.69 (206.38) | - | - | all | - | cpu 3930.2 ms/run |
| REF  | [so]graph_optimization_level=ORT_ENABLE_ALL | rtmw b1/fp32 | 513 | 51.39 (52.72) | - | - | all | - | cpu 1026.0 ms/run |
| REF  | [so]graph_optimization_level=ORT_ENABLE_ALL | rtmw b3/fp32 | 508 | 153.87 (160.85) | - | - | all | - | cpu 2996.9 ms/run |
| C1  | {} | yolox b1/fp32 | 227 | 10.75 (11.27) | 0.741 / 8.7e-04 | 9->9 | 0.02 | 0 | 409 | cpu 10.4 ms/run |
| C1  | {} | yolox b1/fp16 | 185 | 7.37 (8.22) | 1.810 / 2.1e-03 | 9->9 | 0.25 | 0 | 283 | cpu 7.3 ms/run |
| C1  | {} | yolox b3/fp32 | 212 | 29.48 (30.50) | 0.666 / 7.7e-04 | 27->27 | 0.04 | 0 | 661 | cpu 29.7 ms/run |
| C1  | {} | yolox b3/fp16 | 202 | 18.44 (19.19) | 1.699 / 2.0e-03 | 27->27 | 0.27 | 0 | 422 | cpu 18.2 ms/run |
| C1  | {} | rtmw b1/fp32 | 352 | 14.22 (14.62) | 0.112 / 0.0107 | 4/3 | 0.5 | 0 | 661 | cpu 13.5 ms/run |
| C1  | {} | rtmw b1/fp16 | 285 | 10.26 (11.43) | 0.036 / 3.6e-03 | 8/3 | 0.5 | 3 (Clip) | 411 | cpu 9.9 ms/run |
| C1  | {} | rtmw b3/fp32 | 373 | 28.76 (29.48) | 0.114 / 0.0107 | 12/5 | 0.5 | 0 | 665 | cpu 28.1 ms/run |
| C1  | {} | rtmw b3/fp16 | 262 | 17.17 (18.45) | 0.047 / 4.7e-03 | 26/9 | 0.5 | 3 (Clip) | 411 | cpu 16.7 ms/run |
| C2  | use_tf32=0 | yolox b1/fp32 | 223 | 12.37 (13.26) | 8.7e-04 / 1.9e-06 | 9->9 | 6.1e-05 | 0 | 413 | cpu 12.0 ms/run |
| C2  | use_tf32=0 | yolox b1/fp16 | 175 | 7.47 (8.05) | 1.810 / 2.6e-03 | 9->9 | 0.25 | 0 | 282 | cpu 7.8 ms/run |
| C2  | use_tf32=0 | yolox b3/fp32 | 198 | 183.97 (186.03) | 1.0e-03 / 1.7e-06 | 27->27 | 6.1e-05 | 0 | 5073 | cpu 183.3 ms/run |
| C2  | use_tf32=0 | yolox b3/fp16 | 165 | 26.62 (27.31) | 2.253 / 2.6e-03 | 27->27 | 0.27 | 0 | 669 | cpu 26.6 ms/run |
| C2  | use_tf32=0 | rtmw b1/fp32 | 365 | 20.19 (20.87) | 4.6e-05 / 4.7e-06 | 0/0 | 0.0 | 0 | 675 | cpu 20.3 ms/run |
| C2  | use_tf32=0 | rtmw b1/fp16 | 268 | 13.04 (13.59) | 0.040 / 3.8e-03 | 6/1 | 0.5 | 3 (Clip) | 923 | cpu 13.0 ms/run |
| C2  | use_tf32=0 | rtmw b3/fp32 | 383 | 35.50 (36.16) | 6.4e-05 / 6.0e-06 | 0/0 | 0.0 | 0 | 661 | cpu 35.9 ms/run |
| C2  | use_tf32=0 | rtmw b3/fp16 | 264 | 20.21 (21.85) | 0.046 / 4.6e-03 | 21/7 | 0.5 | 3 (Clip) | 923 | cpu 20.8 ms/run |
| C3  | use_tf32=0; cudnn_conv_algo_search=HEURISTIC | yolox b1/fp32 | 218 | 11.97 (12.26) | 8.7e-04 / 1.9e-06 | 9->9 | 6.1e-05 | 0 | 403 | cpu 12.0 ms/run |
| C3  | use_tf32=0; cudnn_conv_algo_search=HEURISTIC | yolox b1/fp16 | 177 | 7.59 (8.12) | 1.810 / 2.6e-03 | 9->9 | 0.25 | 0 | 285 | cpu 7.8 ms/run |
| C3  | use_tf32=0; cudnn_conv_algo_search=HEURISTIC | yolox b3/fp32 | 197 | 184.11 (186.01) | 1.0e-03 / 1.7e-06 | 27->27 | 6.1e-05 | 0 | 5498 | cpu 182.8 ms/run |
| C3  | use_tf32=0; cudnn_conv_algo_search=HEURISTIC | yolox b3/fp16 | 172 | 26.57 (28.43) | 2.253 / 2.6e-03 | 27->27 | 0.27 | 0 | 669 | cpu 26.6 ms/run |
| C3  | use_tf32=0; cudnn_conv_algo_search=HEURISTIC | rtmw b1/fp32 | 361 | 20.19 (21.06) | 4.6e-05 / 4.7e-06 | 0/0 | 0.0 | 0 | 675 | cpu 19.8 ms/run |
| C3  | use_tf32=0; cudnn_conv_algo_search=HEURISTIC | rtmw b1/fp16 | 261 | 13.20 (13.68) | 0.040 / 3.8e-03 | 6/1 | 0.5 | 3 (Clip) | 927 | cpu 13.0 ms/run |
| C3  | use_tf32=0; cudnn_conv_algo_search=HEURISTIC | rtmw b3/fp32 | 356 | 35.45 (36.11) | 6.4e-05 / 6.0e-06 | 0/0 | 0.0 | 0 | 661 | cpu 35.9 ms/run |
| C3  | use_tf32=0; cudnn_conv_algo_search=HEURISTIC | rtmw b3/fp16 | 277 | 20.12 (21.46) | 0.046 / 4.6e-03 | 21/7 | 0.5 | 3 (Clip) | 925 | cpu 20.3 ms/run |
| C4  | use_tf32=0; cudnn_conv_algo_search=DEFAULT | yolox b1/fp32 | 216 | 22.66 (23.30) | 1.1e-03 / 1.9e-06 | 9->9 | 1.1e-04 | 0 | 408 | cpu 22.9 ms/run |
| C4  | use_tf32=0; cudnn_conv_algo_search=DEFAULT | yolox b1/fp16 | 170 | 22.40 (23.36) | 1.310 / 1.5e-03 | 9->9 | 0.36 | 0 | 277 | cpu 22.9 ms/run |
| C4  | use_tf32=0; cudnn_conv_algo_search=DEFAULT | yolox b3/fp32 | 200 | 46.55 (47.10) | 1.1e-03 / 1.9e-06 | 27->27 | 1.1e-04 | 0 | 659 | cpu 43.2 ms/run |
| C4  | use_tf32=0; cudnn_conv_algo_search=DEFAULT | yolox b3/fp16 | 179 | 43.64 (44.25) | 1.753 / 2.0e-03 | 27->27 | 0.36 | 0 | 403 | cpu 42.2 ms/run |
| C4  | use_tf32=0; cudnn_conv_algo_search=DEFAULT | rtmw b1/fp32 | 356 | 346.42 (401.67) | 4.6e-05 / 4.7e-06 | 0/0 | 0.0 | 0 | 659 | cpu 339.1 ms/run |
| C4  | use_tf32=0; cudnn_conv_algo_search=DEFAULT | rtmw b1/fp16 | 298 | 350.56 (373.38) | 0.036 / 3.6e-03 | 11/3 | 0.5 | 3 (Clip) | 411 | cpu 349.5 ms/run |
| C4  | use_tf32=0; cudnn_conv_algo_search=DEFAULT | rtmw b3/fp32 | 359 | 369.24 (419.38) | 6.8e-05 / 6.4e-06 | 0/0 | 0.0 | 0 | 661 | cpu 371.4 ms/run |
| C4  | use_tf32=0; cudnn_conv_algo_search=DEFAULT | rtmw b3/fp16 | 279 | 373.84 (439.46) | 0.055 / 5.5e-03 | 24/7 | 0.5 | 3 (Clip) | 411 | cpu 369.8 ms/run |
| C5  | prefer_nhwc=1 | yolox b1/fp32 | 239 | 10.21 (10.30) | 0.719 / 8.4e-04 | 9->9 | 0.03 | 0 | 417 | cpu 9.9 ms/run |
| C5  | prefer_nhwc=1 | yolox b1/fp16 | 286 | 7.35 (24.60) | 1.810 / 2.1e-03 | 9->9 | 0.27 | 0 | 293 | cpu 5.2 ms/run |
| C5  | prefer_nhwc=1 | yolox b3/fp32 | 458 | 28.32 (74.66) | 0.966 / 1.1e-03 | 27->27 | 0.03 | 0 | 669 | cpu 24.0 ms/run |
| C5  | prefer_nhwc=1 | yolox b3/fp16 | 184 | 14.93 (15.03) | 1.699 / 2.0e-03 | 27->27 | 0.28 | 0 | 421 | cpu 15.1 ms/run |
| C5  | prefer_nhwc=1 | rtmw b1/fp32 | 394 | 11.38 (11.48) | 0.111 / 0.0106 | 4/3 | 0.5 | 0 | 1185 | cpu 11.5 ms/run |
| C5  | prefer_nhwc=1 | rtmw b1/fp16 | 287 | 7.05 (7.11) | 0.043 / 4.4e-03 | 8/4 | 0.5 | 3 (Clip) | 419 | cpu 7.3 ms/run |
| C5  | prefer_nhwc=1 | rtmw b3/fp32 | 375 | 24.95 (25.63) | 0.106 / 0.0100 | 12/5 | 0.5 | 0 | 1187 | cpu 25.0 ms/run |
| C5  | prefer_nhwc=1 | rtmw b3/fp16 | 291 | 13.60 (14.32) | 0.043 / 4.3e-03 | 20/5 | 0.5 | 3 (Clip) | 677 | cpu 13.5 ms/run |
| C5b  | prefer_nhwc=1; use_tf32=0 | yolox b1/fp32 | 216 | 15.39 (16.05) | 1.6e-03 / 1.8e-06 | 9->9 | 1.1e-04 | 0 | 411 | cpu 15.6 ms/run |
| C5b  | prefer_nhwc=1; use_tf32=0 | yolox b1/fp16 | 196 | 6.25 (6.34) | 1.810 / 2.1e-03 | 9->9 | 0.36 | 0 | 291 | cpu 6.2 ms/run |
| C5b  | prefer_nhwc=1; use_tf32=0 | yolox b3/fp32 | 235 | 190.46 (197.35) | 1.7e-03 / 2.0e-06 | 27->27 | 6.1e-05 | 0 | 5661 | cpu 191.1 ms/run |
| C5b  | prefer_nhwc=1; use_tf32=0 | yolox b3/fp16 | 190 | 15.30 (15.99) | 1.699 / 2.0e-03 | 27->27 | 0.28 | 0 | 419 | cpu 15.1 ms/run |
| C5b  | prefer_nhwc=1; use_tf32=0 | rtmw b1/fp32 | 392 | 22.91 (24.68) | 5.4e-05 / 5.4e-06 | 0/0 | 0.0 | 0 | 1187 | cpu 22.9 ms/run |
| C5b  | prefer_nhwc=1; use_tf32=0 | rtmw b1/fp16 | 289 | 6.52 (6.65) | 0.042 / 4.2e-03 | 6/2 | 0.5 | 3 (Clip) | 425 | cpu 6.8 ms/run |
| C5b  | prefer_nhwc=1; use_tf32=0 | rtmw b3/fp32 | 381 | 50.24 (53.28) | 5.5e-05 / 5.2e-06 | 0/0 | 0.0 | 0 | 1185 | cpu 45.8 ms/run |
| C5b  | prefer_nhwc=1; use_tf32=0 | rtmw b3/fp16 | 316 | 14.39 (15.34) | 0.049 / 4.9e-03 | 22/7 | 0.5 | 3 (Clip) | 679 | cpu 14.6 ms/run |
| C6  | fuse_conv_bias=1 | yolox b1/fp32 | 208 | 13.36 (13.64) | 0.271 / 3.2e-04 | 9->9 | 0.02 | 0 | 403 | cpu 13.5 ms/run; repeat differs |
| C6  | fuse_conv_bias=1 | yolox b1/fp16 | 175 | 64.23 (68.26) | 0.891 / 1.2e-03 | 9->9 | 0.25 | 0 | 275 | cpu 1274.0 ms/run |
| C6  | fuse_conv_bias=1 | yolox b3/fp32 | 213 | 31.10 (33.55) | 0.442 / 5.1e-04 | 27->27 | 0.05 | 0 | 664 | cpu 31.2 ms/run; repeat differs |
| C6  | fuse_conv_bias=1 | yolox b3/fp16 | 187 | 207.08 (213.85) | 0.932 / 1.2e-03 | 27->27 | 0.25 | 0 | 277 | cpu 4089.6 ms/run |
| C6  | fuse_conv_bias=1 | rtmw b1/fp32 | 375 | 17.31 (17.79) | 0.099 / 9.4e-03 | 4/3 | 0.5 | 0 | 661 | cpu 16.7 ms/run; repeat differs |
| C6  | fuse_conv_bias=1 | rtmw b1/fp16 | 268 | 62.01 (910.55) | 0.049 / 4.7e-03 | 3/2 | 0.5 | 3 (Clip) | 403 | cpu 3445.8 ms/run |
| C6  | fuse_conv_bias=1 | rtmw b3/fp32 | 385 | 30.28 (31.36) | 0.091 / 8.6e-03 | 10/5 | 0.5 | 0 | 659 | cpu 30.2 ms/run; repeat differs |
| C6  | fuse_conv_bias=1 | rtmw b3/fp16 | 291 | 152.15 (155.53) | 0.049 / 4.6e-03 | 5/3 | 0.5 | 3 (Clip) | 403 | cpu 3015.6 ms/run |
| C6b  | fuse_conv_bias=1; use_tf32=0 | yolox b1/fp32 | 217 | 11.57 (12.27) | 8.7e-04 / 1.9e-06 | 9->9 | 6.1e-05 | 0 | 405 | cpu 11.5 ms/run; repeat differs |
| C6b  | fuse_conv_bias=1; use_tf32=0 | yolox b1/fp16 | 178 | 63.34 (69.38) | 0.891 / 1.2e-03 | 9->9 | 0.25 | 0 | 275 | cpu 1277.1 ms/run |
| C6b  | fuse_conv_bias=1; use_tf32=0 | yolox b3/fp32 | 217 | 178.59 (182.34) | 283.706 / 0.9931 | 27->27 | 58.39 | 0 | 5715 | cpu 178.1 ms/run; repeat differs |
| C6b  | fuse_conv_bias=1; use_tf32=0 | yolox b3/fp16 | 173 | 204.71 (210.90) | 0.932 / 1.2e-03 | 27->27 | 0.25 | 0 | 275 | cpu 4039.6 ms/run |
| C6b  | fuse_conv_bias=1; use_tf32=0 | rtmw b1/fp32 | 371 | 18.75 (19.88) | 0.289 / 0.0277 | 12/6 | 0.5 | 0 | 671 | cpu 17.2 ms/run; repeat differs |
| C6b  | fuse_conv_bias=1; use_tf32=0 | rtmw b1/fp16 | 253 | 51.05 (55.66) | 0.049 / 4.7e-03 | 3/2 | 0.5 | 3 (Clip) | 403 | cpu 1027.6 ms/run |
| C6b  | fuse_conv_bias=1; use_tf32=0 | rtmw b3/fp32 | 383 | 41.54 (42.13) | 3.478 / 0.3508 | 221/80 | 3.5 | 0 | 667 | cpu 38.5 ms/run; repeat differs |
| C6b  | fuse_conv_bias=1; use_tf32=0 | rtmw b3/fp16 | 263 | 154.85 (161.33) | 0.049 / 4.6e-03 | 5/3 | 0.5 | 3 (Clip) | 413 | cpu 3055.2 ms/run |
| C7  | arena.extend_strategy=1 | yolox b1/fp32 | 221 | 10.49 (10.93) | 0.741 / 8.7e-04 | 9->9 | 0.02 | 0 | 367 | cpu 8.9 ms/run |
| C7  | arena.extend_strategy=1 | yolox b1/fp16 | 187 | 7.06 (7.93) | 1.810 / 2.1e-03 | 9->9 | 0.25 | 0 | 291 | cpu 6.8 ms/run |
| C7  | arena.extend_strategy=1 | yolox b3/fp32 | 212 | 28.51 (30.39) | 0.666 / 7.7e-04 | 27->27 | 0.04 | 0 | 563 | cpu 27.1 ms/run |
| C7  | arena.extend_strategy=1 | yolox b3/fp16 | 188 | 17.90 (18.76) | 1.699 / 2.0e-03 | 27->27 | 0.27 | 0 | 419 | cpu 18.2 ms/run |
| C7  | arena.extend_strategy=1 | rtmw b1/fp32 | 390 | 13.68 (13.80) | 0.112 / 0.0107 | 4/3 | 0.5 | 0 | 655 | cpu 13.5 ms/run |
| C7  | arena.extend_strategy=1 | rtmw b1/fp16 | 287 | 10.13 (11.13) | 0.036 / 3.6e-03 | 8/3 | 0.5 | 3 (Clip) | 414 | cpu 10.4 ms/run |
| C7  | arena.extend_strategy=1 | rtmw b3/fp32 | 378 | 28.34 (29.44) | 0.114 / 0.0107 | 12/5 | 0.5 | 0 | 755 | cpu 27.1 ms/run |
| C7  | arena.extend_strategy=1 | rtmw b3/fp16 | 273 | 16.49 (17.76) | 0.047 / 4.7e-03 | 26/9 | 0.5 | 3 (Clip) | 453 | cpu 16.7 ms/run |
| C8  | arena.max_mem=1073741824 | yolox b3/fp32 | 255 | 28.43 (29.42) | 0.666 / 7.7e-04 | 27->27 | 0.04 | 0 | 673 | cpu 28.1 ms/run |
| C8  | arena.max_mem=1073741824 | rtmw b3/fp32 | 381 | 27.75 (28.82) | 0.114 / 0.0107 | 12/5 | 0.5 | 0 | 659 | cpu 28.1 ms/run |
| C9  | enable_cuda_graph=1 | yolox b1/fp32 | 246 | 9.90 (10.20) | 0.741 / 8.7e-04 | 9->9 | 0.02 | 0 | 428 | cpu 9.9 ms/run; run-only 8.78 ms; 2nd run 11.1 ms; new input changes out: True, rel vs CPU 5.7e-04, plain-run outs 0; plain run err: ValueError: max() iterable argument is empty; alloc forms ok: ['memory_info_default'] |
| C9  | enable_cuda_graph=1 | yolox b1/fp16 | 185 | 6.09 (6.17) | 1.810 / 2.1e-03 | 9->9 | 0.25 | 0 | 303 | cpu 5.7 ms/run; run-only 5.74 ms; 2nd run 6.2 ms; new input changes out: True, rel vs CPU 1.8e-03, plain-run outs 0; plain run err: ValueError: max() iterable argument is empty; alloc forms ok: ['memory_info_default'] |
| C9  | enable_cuda_graph=1 | yolox b3/fp32 | 224 | 27.43 (29.23) | 0.666 / 7.7e-04 | 27->27 | 0.04 | 0 | 695 | cpu 27.6 ms/run; run-only 26.21 ms; 2nd run 27.5 ms; new input changes out: True, rel vs CPU 7.7e-04, plain-run outs 0; plain run err: ValueError: max() iterable argument is empty; alloc forms ok: ['memory_info_default'] |
| C9  | enable_cuda_graph=1 | yolox b3/fp16 | 246 | 16.95 (18.15) | 1.699 / 2.0e-03 | 27->27 | 0.27 | 0 | 449 | cpu 17.2 ms/run; run-only 15.66 ms; 2nd run 18.1 ms; new input changes out: True, rel vs CPU 2.0e-03, plain-run outs 0; plain run err: ValueError: max() iterable argument is empty; alloc forms ok: ['memory_info_default'] |
| C9  | enable_cuda_graph=1 | rtmw b1/fp32 | 377 | 12.78 (13.27) | 0.112 / 0.0107 | 4/3 | 0.5 | 0 | 703 | cpu 12.5 ms/run; run-only 12.17 ms; 2nd run 13.2 ms; new input changes out: True, rel vs CPU 5.6e-03, plain-run outs 0; plain run err: ValueError: max() iterable argument is empty; alloc forms ok: ['memory_info_default'] |
| C9  | enable_cuda_graph=1 | rtmw b1/fp16 | - | - | - | - | 0 | 0 | FAIL: Fail: [ONNXRuntimeError] : 1 : FAIL : This session cannot use the graph capture feature as requested by the user  as all compute graph nodes have not been partitioned to the CUDAExecutionProvider |
| C9  | enable_cuda_graph=1 | rtmw b3/fp32 | 501 | 26.71 (37.21) | 0.114 / 0.0107 | 12/5 | 0.5 | 0 | 706 | cpu 23.4 ms/run; run-only 25.99 ms; 2nd run 28.6 ms; new input changes out: True, rel vs CPU 0.0107, plain-run outs 0; plain run err: ValueError: max() iterable argument is empty; alloc forms ok: ['memory_info_default'] |
| C9  | enable_cuda_graph=1 | rtmw b3/fp16 | - | - | - | - | 0 | 0 | FAIL: Fail: [ONNXRuntimeError] : 1 : FAIL : This session cannot use the graph capture feature as requested by the user  as all compute graph nodes have not been partitioned to the CUDAExecutionProvider |
| C9n  | {} | yolox b1/fp32 | 226 | 10.84 (11.59) | 0.741 / 8.7e-04 | 9->9 | 0.02 | 0 | 425 | cpu 10.9 ms/run; run-only 9.56 ms; 2nd run 10.8 ms; new input changes out: True, rel vs CPU -, plain-run outs None; alloc forms ok: ['memory_info_default'] |
| C9n  | {} | yolox b3/fp32 | 197 | 28.24 (29.17) | 0.666 / 7.7e-04 | 27->27 | 0.04 | 0 | 693 | cpu 28.6 ms/run; run-only 27.14 ms; 2nd run 28.4 ms; new input changes out: True, rel vs CPU -, plain-run outs None; alloc forms ok: ['memory_info_default'] |
| C9n  | {} | rtmw b1/fp32 | 364 | 13.58 (13.71) | 0.112 / 0.0107 | 4/3 | 0.5 | 0 | 667 | cpu 13.5 ms/run; run-only 13.36 ms; 2nd run 13.8 ms; new input changes out: True, rel vs CPU -, plain-run outs None; alloc forms ok: ['memory_info_default'] |
| C9n  | {} | rtmw b3/fp32 | 375 | 27.55 (28.21) | 0.114 / 0.0107 | 12/5 | 0.5 | 0 | 685 | cpu 27.6 ms/run; run-only 27.01 ms; 2nd run 27.8 ms; new input changes out: True, rel vs CPU -, plain-run outs None; alloc forms ok: ['memory_info_default'] |
| C10 nodet-r0 | use_tf32=0 | rtmw b3/fp32 | 371 | - | 6.4e-05 / 6.0e-06 | 0/0 | 0.0 | 0 | 671 |  |
| C10 nodet-r1 | use_tf32=0 | rtmw b3/fp32 | 372 | - | 6.4e-05 / 6.0e-06 | 0/0 | 0.0 | 0 | 671 |  |
| C10 nodet-r2 | use_tf32=0 | rtmw b3/fp32 | 370 | - | 6.4e-05 / 6.0e-06 | 0/0 | 0.0 | 0 | 665 |  |
| C10 nodet-r3 | use_tf32=0 | rtmw b3/fp32 | 364 | - | 6.4e-05 / 6.0e-06 | 0/0 | 0.0 | 0 | 665 |  |
| C10 nodet-r4 | use_tf32=0 | rtmw b3/fp32 | 379 | - | 6.4e-05 / 6.0e-06 | 0/0 | 0.0 | 0 | 661 |  |
| C10 det-r0 | use_tf32=0; [cfg]use_deterministic_compute=1 | rtmw b3/fp32 | 372 | - | 6.4e-05 / 6.0e-06 | 0/0 | 0.0 | 0 | 661 |  |
| C10 det-r1 | use_tf32=0; [cfg]use_deterministic_compute=1 | rtmw b3/fp32 | 368 | - | 6.4e-05 / 6.0e-06 | 0/0 | 0.0 | 0 | 665 |  |
| C10 det-r2 | use_tf32=0; [cfg]use_deterministic_compute=1 | rtmw b3/fp32 | 375 | - | 6.4e-05 / 6.0e-06 | 0/0 | 0.0 | 0 | 661 |  |
| C10 det-r3 | use_tf32=0; [cfg]use_deterministic_compute=1 | rtmw b3/fp32 | 384 | - | 6.4e-05 / 6.0e-06 | 0/0 | 0.0 | 0 | 667 |  |
| C10 det-r4 | use_tf32=0; [cfg]use_deterministic_compute=1 | rtmw b3/fp32 | 389 | - | 6.4e-05 / 6.0e-06 | 0/0 | 0.0 | 0 | 665 |  |
| C11 bogus | bogus_key=1 | yolox b1/fp32 | 359 | 10.82 (10.85) | 0.741 / 8.7e-04 | 9->9 | 0.02 | 0 | 410 | cpu 12.5 ms/run |
| C11 memlimit1 | gpu_mem_limit=1 | yolox b1/fp32 | 334 | 10.88 (11.02) | 0.741 / 8.7e-04 | 9->9 | 0.02 | 0 | 407 | cpu 9.4 ms/run |
| C11 bogus | bogus_key=1 | rtmw b1/fp32 | 468 | 14.32 (15.07) | 0.112 / 0.0107 | 4/3 | 0.5 | 0 | 663 | cpu 9.4 ms/run |
| C11 memlimit1 | gpu_mem_limit=1 | rtmw b1/fp32 | 477 | 13.72 (13.79) | 0.112 / 0.0107 | 4/3 | 0.5 | 0 | 664 | cpu 12.5 ms/run |
| M tdef-spin1 | use_tf32=0; [cfg]intra_op.allow_spinning=1 | rtmw b1/fp32 | - | - | 4.6e-05 / 4.7e-06 | 0/0 | 0.0 | 0 | 1731 | fps 82.47 cpu 16.615 ms/frame util 1.37 med 36.071 p95 38.19 |
| M tdef-spin0 | use_tf32=0; [cfg]intra_op.allow_spinning=0 | rtmw b1/fp32 | - | - | 4.6e-05 / 4.7e-06 | 0/0 | 0.0 | 0 | 1857 | fps 79.92 cpu 18.073 ms/frame util 1.444 med 37.499 p95 39.449 |
| M t1-spin1 | use_tf32=0; [cfg]intra_op.allow_spinning=1; [so]intra_op_num_threads=1 | rtmw b1/fp32 | - | - | 4.6e-05 / 4.7e-06 | 0/0 | 0.0 | 0 | 1859 | fps 78.56 cpu 17.292 ms/frame util 1.358 med 38.083 p95 39.516 |
| M t1-spin0 | use_tf32=0; [cfg]intra_op.allow_spinning=0; [so]intra_op_num_threads=1 | rtmw b1/fp32 | - | - | 4.6e-05 / 4.7e-06 | 0/0 | 0.0 | 0 | 1753 | fps 78.33 cpu 16.979 ms/frame util 1.33 med 38.093 p95 40.186 |
| C3x  | use_tf32=0; cudnn_conv_algo_search=EXHAUSTIVE | yolox b1/fp32 | 226 | 12.15 (12.74) | 8.7e-04 / 1.9e-06 | 9->9 | 6.1e-05 | 0 | 405 | cpu 12.0 ms/run |
| C3x  | use_tf32=0; cudnn_conv_algo_search=EXHAUSTIVE | yolox b3/fp32 | 211 | 186.16 (192.59) | 1.0e-03 / 1.7e-06 | 27->27 | 6.1e-05 | 0 | 5689 | cpu 184.9 ms/run |
| C3x  | use_tf32=0; cudnn_conv_algo_search=EXHAUSTIVE | rtmw b1/fp32 | 378 | 20.79 (22.64) | 4.6e-05 / 4.7e-06 | 0/0 | 0.0 | 0 | 659 | cpu 19.3 ms/run |
| C3x  | use_tf32=0; cudnn_conv_algo_search=EXHAUSTIVE | rtmw b3/fp32 | 379 | 35.91 (36.95) | 6.4e-05 / 6.0e-06 | 0/0 | 0.0 | 0 | 667 | cpu 35.4 ms/run |
| C3x1  | cudnn_conv_algo_search=EXHAUSTIVE | yolox b1/fp32 | 212 | 10.61 (11.32) | 0.741 / 8.7e-04 | 9->9 | 0.02 | 0 | 409 | cpu 9.9 ms/run |
| C3x1  | cudnn_conv_algo_search=EXHAUSTIVE | yolox b3/fp32 | 199 | 29.81 (30.62) | 0.666 / 7.7e-04 | 27->27 | 0.04 | 0 | 661 | cpu 28.1 ms/run |
| C3x1  | cudnn_conv_algo_search=EXHAUSTIVE | rtmw b1/fp32 | 370 | 14.52 (15.06) | 0.112 / 0.0107 | 4/3 | 0.5 | 0 | 670 | cpu 14.1 ms/run |
| C3x1  | cudnn_conv_algo_search=EXHAUSTIVE | rtmw b3/fp32 | 371 | 29.48 (30.91) | 0.114 / 0.0107 | 12/5 | 0.5 | 0 | 738 | cpu 26.6 ms/run |
| T1  | {} | yolox b1/fp32 | 4898 | 7.16 (7.96) | 0.619 / 7.3e-04 | 9->9 | 0.06 | 0 | 369 | cpu 7.8 ms/run |
| T1  | {} | yolox b1/fp16 | 3070 | 3.33 (3.41) | 2.688 / 3.1e-03 | 9->9 | 0.30 | 0 | 249 | cpu 3.1 ms/run |
| T1  | {} | yolox b3/fp32 | 2329 | 19.95 (21.09) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 436 | cpu 19.3 ms/run |
| T1  | {} | yolox b3/fp16 | 2910 | 9.24 (10.21) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 305 | cpu 9.4 ms/run |
| T1  | {} | rtmw b1/fp32 | 4217 | 8.32 (9.67) | 0.094 / 9.0e-03 | 4/3 | 0.5 | 0 | 536 | cpu 8.9 ms/run |
| T1  | {} | rtmw b1/fp16 | 4952 | 3.65 (4.32) | 0.147 / 0.0140 | 28/9 | 0.5 | 0 | 361 | cpu 3.1 ms/run |
| T1  | {} | rtmw b3/fp32 | 4577 | 20.06 (20.83) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 575 | cpu 19.8 ms/run |
| T1  | {} | rtmw b3/fp16 | 5403 | 8.73 (9.45) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 377 | cpu 8.9 ms/run |
| T7 bogus | bogus_key=1 | yolox b1/fp32 | 510 | 60.40 (63.08) | 0.000 / 0 | 9->9 | 0.00 | 388 (Add,ArgMax,Concat,Conv,Div,Equal,Exp,Gather,MaxPool,Mul,Reshape,Resize,Sigmoid,Slice,Sub,Transpose,Unsqueeze,Where) | 0 | cpu 1181.2 ms/run; log: runtime::PluginExecutionProviderFactory::CreateProvider Error creating execution provider: [ONNXRuntimeError] : 1 : FAIL : Unknown provider option: "bogus_key". |
| T7 device_id | device_id=0 | yolox b1/fp32 | 474 | 60.00 (61.44) | 0.000 / 0 | 9->9 | 0.00 | 388 (Add,ArgMax,Concat,Conv,Div,Equal,Exp,Gather,MaxPool,Mul,Reshape,Resize,Sigmoid,Slice,Sub,Transpose,Unsqueeze,Where) | 0 | cpu 1181.2 ms/run; log: runtime::PluginExecutionProviderFactory::CreateProvider Error creating execution provider: [ONNXRuntimeError] : 1 : FAIL : Unknown provider option: "device_id". |
| T2 cold | {} | yolox b1/fp32 | 4154 | 7.91 (8.63) | 0.619 / 7.3e-04 | 9->9 | 0.06 | 0 | 354 | cpu 8.3 ms/run; dir 1 files 4327 KB |
| T2 warm | {} | yolox b1/fp32 | 1102 | 7.53 (8.35) | 0.619 / 7.3e-04 | 9->9 | 0.06 | 0 | 342 | cpu 7.8 ms/run; dir 1 files 4327 KB |
| T2 cold | {} | yolox b1/fp16 | 2764 | 3.25 (3.95) | 2.688 / 3.1e-03 | 9->9 | 0.30 | 0 | 266 | cpu 3.1 ms/run; dir 1 files 3427 KB |
| T2 warm | {} | yolox b1/fp16 | 991 | 3.23 (3.95) | 2.688 / 3.1e-03 | 9->9 | 0.30 | 0 | 248 | cpu 3.1 ms/run; dir 1 files 3427 KB |
| T2 cold | {} | yolox b3/fp32 | 2591 | 27.71 (35.91) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 433 | cpu 17.2 ms/run; dir 1 files 3583 KB |
| T2 warm | {} | yolox b3/fp32 | 2231 | 27.67 (48.75) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 438 | cpu 18.2 ms/run; dir 1 files 3583 KB |
| T2 cold | {} | yolox b3/fp16 | 2923 | 9.45 (9.96) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 301 | cpu 9.9 ms/run; dir 1 files 3671 KB |
| T2 warm | {} | yolox b3/fp16 | 971 | 9.71 (10.08) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 302 | cpu 9.9 ms/run; dir 1 files 3671 KB |
| T2 cold | {} | rtmw b1/fp32 | 3935 | 8.71 (9.85) | 0.094 / 9.0e-03 | 4/3 | 0.5 | 0 | 522 | cpu 8.9 ms/run; dir 1 files 3862 KB |
| T2 warm | {} | rtmw b1/fp32 | 1891 | 8.75 (9.77) | 0.094 / 9.0e-03 | 4/3 | 0.5 | 0 | 517 | cpu 8.9 ms/run; dir 1 files 3862 KB |
| T2 cold | {} | rtmw b1/fp16 | 4840 | 3.64 (4.26) | 0.147 / 0.0140 | 28/9 | 0.5 | 0 | 377 | cpu 3.6 ms/run; dir 1 files 3780 KB |
| T2 warm | {} | rtmw b1/fp16 | 1625 | 3.69 (4.32) | 0.147 / 0.0140 | 28/9 | 0.5 | 0 | 369 | cpu 3.6 ms/run; dir 1 files 3780 KB |
| T2 cold | {} | rtmw b3/fp32 | 4105 | 19.96 (22.23) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 570 | cpu 20.3 ms/run; dir 1 files 4169 KB |
| T2 warm | {} | rtmw b3/fp32 | 1849 | 20.39 (22.31) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 567 | cpu 20.3 ms/run; dir 1 files 4169 KB |
| T2 cold | {} | rtmw b3/fp16 | 4818 | 8.77 (9.29) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 381 | cpu 8.9 ms/run; dir 1 files 4045 KB |
| T2 warm | {} | rtmw b3/fp16 | 1566 | 8.38 (10.07) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 373 | cpu 8.9 ms/run; dir 1 files 4045 KB |
| T3w cfg-e0 | [cfg]ep.context_enable=1; [cfg]ep.context_embed_mode=0 | yolox b3/fp32 | 2319 | 21.35 (21.92) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 446 | cpu 21.9 ms/run; dir 2 files 100995 KB; files yolox_b3_fp32_cfg_e0_ctx.onnx=1219 |
| T3l cfg-e0 | {} | yolox b3/fp32 | 1628 | 20.66 (21.66) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 444 | cpu 20.8 ms/run |
| T3s cfg-e0 | [cfg]fail_on_suboptimal_compiled_model=1 | yolox b3/fp32 | 1617 | 21.47 (22.08) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 445 | cpu 18.8 ms/run |
| T3w cfg-e1 | [cfg]ep.context_enable=1; [cfg]ep.context_embed_mode=1 | yolox b3/fp32 | 2531 | 20.03 (21.60) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 420 | cpu 18.8 ms/run; dir 3 files 201990 KB; files yolox_b3_fp32_cfg_e1_ctx.onnx=103419212 |
| T3l cfg-e1 | {} | yolox b3/fp32 | 1753 | 20.42 (21.44) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 443 | cpu 20.3 ms/run |
| T3s cfg-e1 | [cfg]fail_on_suboptimal_compiled_model=1 | yolox b3/fp32 | 1758 | 21.12 (21.97) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 421 | cpu 21.9 ms/run |
| T3w po-e0 | ep.context_enable=1; ep.context_file_path=<work>\epopt\cache\ctx\yolox_b3_fp32_po_e0_ctx.onnx; ep.context_embed_mode=0 | yolox b3/fp32 | 2393 | 20.95 (22.58) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 427 | cpu 21.9 ms/run; dir 3 files 201990 KB; files yolox_b3_fp32_po_e0_ctx.onnx=None |
| T3l po-e0 | {} | yolox b3/fp32 | - | - | - | - | 0 | - | FAIL: missing yolox_b3_fp32_po_e0_ctx.onnx (write step made no file) |
| T3s po-e0 | [cfg]fail_on_suboptimal_compiled_model=1 | yolox b3/fp32 | - | - | - | - | 0 | - | FAIL: missing yolox_b3_fp32_po_e0_ctx.onnx (write step made no file) |
| T3w po-e1 | ep.context_enable=1; ep.context_file_path=<work>\epopt\cache\ctx\yolox_b3_fp32_po_e1_ctx.onnx; ep.context_embed_mode=1 | yolox b3/fp32 | 2415 | 22.29 (23.15) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 423 | cpu 21.9 ms/run; dir 3 files 201990 KB; files yolox_b3_fp32_po_e1_ctx.onnx=None |
| T3l po-e1 | {} | yolox b3/fp32 | - | - | - | - | 0 | - | FAIL: missing yolox_b3_fp32_po_e1_ctx.onnx (write step made no file) |
| T3s po-e1 | [cfg]fail_on_suboptimal_compiled_model=1 | yolox b3/fp32 | - | - | - | - | 0 | - | FAIL: missing yolox_b3_fp32_po_e1_ctx.onnx (write step made no file) |
| T3w cfg-e0 | [cfg]ep.context_enable=1; [cfg]ep.context_embed_mode=0 | yolox b3/fp16 | 2735 | 10.14 (10.57) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 301 | cpu 9.4 ms/run; dir 5 files 254545 KB; files yolox_b3_fp16_cfg_e0_ctx.onnx=1265 |
| T3l cfg-e0 | {} | yolox b3/fp16 | 2096 | 9.81 (10.47) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 314 | cpu 9.9 ms/run |
| T3s cfg-e0 | [cfg]fail_on_suboptimal_compiled_model=1 | yolox b3/fp16 | 2149 | 10.00 (10.29) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 296 | cpu 9.4 ms/run |
| T3w cfg-e1 | [cfg]ep.context_enable=1; [cfg]ep.context_embed_mode=1 | yolox b3/fp16 | 2857 | 9.80 (10.54) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 305 | cpu 12.5 ms/run; dir 6 files 307099 KB; files yolox_b3_fp16_cfg_e1_ctx.onnx=53815579 |
| T3l cfg-e1 | {} | yolox b3/fp16 | 2223 | 9.70 (10.35) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 305 | cpu 9.9 ms/run |
| T3s cfg-e1 | [cfg]fail_on_suboptimal_compiled_model=1 | yolox b3/fp16 | 2148 | 9.98 (10.29) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 314 | cpu 9.4 ms/run |
| T3w po-e0 | ep.context_enable=1; ep.context_file_path=<work>\epopt\cache\ctx\yolox_b3_fp16_po_e0_ctx.onnx; ep.context_embed_mode=0 | yolox b3/fp16 | 2782 | 10.32 (10.80) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 305 | cpu 9.4 ms/run; dir 6 files 307099 KB; files yolox_b3_fp16_po_e0_ctx.onnx=None |
| T3l po-e0 | {} | yolox b3/fp16 | - | - | - | - | 0 | - | FAIL: missing yolox_b3_fp16_po_e0_ctx.onnx (write step made no file) |
| T3s po-e0 | [cfg]fail_on_suboptimal_compiled_model=1 | yolox b3/fp16 | - | - | - | - | 0 | - | FAIL: missing yolox_b3_fp16_po_e0_ctx.onnx (write step made no file) |
| T3w po-e1 | ep.context_enable=1; ep.context_file_path=<work>\epopt\cache\ctx\yolox_b3_fp16_po_e1_ctx.onnx; ep.context_embed_mode=1 | yolox b3/fp16 | 2707 | 11.00 (11.18) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 298 | cpu 9.4 ms/run; dir 6 files 307099 KB; files yolox_b3_fp16_po_e1_ctx.onnx=None |
| T3l po-e1 | {} | yolox b3/fp16 | - | - | - | - | 0 | - | FAIL: missing yolox_b3_fp16_po_e1_ctx.onnx (write step made no file) |
| T3s po-e1 | [cfg]fail_on_suboptimal_compiled_model=1 | yolox b3/fp16 | - | - | - | - | 0 | - | FAIL: missing yolox_b3_fp16_po_e1_ctx.onnx (write step made no file) |
| T3w cfg-e0 | [cfg]ep.context_enable=1; [cfg]ep.context_embed_mode=0 | rtmw b3/fp32 | 4213 | 20.67 (21.05) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 564 | cpu 18.8 ms/run; dir 8 files 671627 KB; files rtmw_b3_fp32_cfg_e0_ctx.onnx=1223 |
| T3l cfg-e0 | {} | rtmw b3/fp32 | 2870 | 20.78 (22.33) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 571 | cpu 16.1 ms/run |
| T3s cfg-e0 | [cfg]fail_on_suboptimal_compiled_model=1 | rtmw b3/fp32 | 2778 | 20.91 (21.63) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 571 | cpu 21.9 ms/run |
| T3w cfg-e1 | [cfg]ep.context_enable=1; [cfg]ep.context_embed_mode=1 | rtmw b3/fp32 | 5158 | 22.34 (23.29) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 569 | cpu 21.9 ms/run; dir 9 files 1036154 KB; files rtmw_b3_fp32_cfg_e1_ctx.onnx=373276284 |
| T3l cfg-e1 | {} | rtmw b3/fp32 | 3112 | 20.75 (21.82) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 572 | cpu 20.8 ms/run |
| T3s cfg-e1 | [cfg]fail_on_suboptimal_compiled_model=1 | rtmw b3/fp32 | 3102 | 22.70 (22.89) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 569 | cpu 21.9 ms/run |
| T3w po-e0 | ep.context_enable=1; ep.context_file_path=<work>\epopt\cache\ctx\rtmw_b3_fp32_po_e0_ctx.onnx; ep.context_embed_mode=0 | rtmw b3/fp32 | 3955 | 22.28 (22.51) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 565 | cpu 21.9 ms/run; dir 9 files 1036154 KB; files rtmw_b3_fp32_po_e0_ctx.onnx=None |
| T3l po-e0 | {} | rtmw b3/fp32 | - | - | - | - | 0 | - | FAIL: missing rtmw_b3_fp32_po_e0_ctx.onnx (write step made no file) |
| T3s po-e0 | [cfg]fail_on_suboptimal_compiled_model=1 | rtmw b3/fp32 | - | - | - | - | 0 | - | FAIL: missing rtmw_b3_fp32_po_e0_ctx.onnx (write step made no file) |
| T3w po-e1 | ep.context_enable=1; ep.context_file_path=<work>\epopt\cache\ctx\rtmw_b3_fp32_po_e1_ctx.onnx; ep.context_embed_mode=1 | rtmw b3/fp32 | 4716 | 20.43 (22.08) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 575 | cpu 21.9 ms/run; dir 9 files 1036154 KB; files rtmw_b3_fp32_po_e1_ctx.onnx=None |
| T3l po-e1 | {} | rtmw b3/fp32 | - | - | - | - | 0 | - | FAIL: missing rtmw_b3_fp32_po_e1_ctx.onnx (write step made no file) |
| T3s po-e1 | [cfg]fail_on_suboptimal_compiled_model=1 | rtmw b3/fp32 | - | - | - | - | 0 | - | FAIL: missing rtmw_b3_fp32_po_e1_ctx.onnx (write step made no file) |
| T3w cfg-e0 | [cfg]ep.context_enable=1; [cfg]ep.context_embed_mode=0 | rtmw b3/fp16 | 4974 | 9.64 (9.76) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 373 | cpu 9.4 ms/run; dir 11 files 1224231 KB; files rtmw_b3_fp16_cfg_e0_ctx.onnx=1272 |
| T3l cfg-e0 | {} | rtmw b3/fp16 | 3842 | 9.33 (9.91) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 379 | cpu 9.4 ms/run |
| T3s cfg-e0 | [cfg]fail_on_suboptimal_compiled_model=1 | rtmw b3/fp16 | 3902 | 9.62 (9.82) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 374 | cpu 9.4 ms/run |
| T3w cfg-e1 | [cfg]ep.context_enable=1; [cfg]ep.context_embed_mode=1 | rtmw b3/fp16 | 5387 | 9.54 (9.76) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 377 | cpu 9.4 ms/run; dir 12 files 1412308 KB; files rtmw_b3_fp16_cfg_e1_ctx.onnx=192590745 |
| T3l cfg-e1 | {} | rtmw b3/fp16 | 4036 | 8.88 (9.71) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 371 | cpu 8.9 ms/run |
| T3s cfg-e1 | [cfg]fail_on_suboptimal_compiled_model=1 | rtmw b3/fp16 | 4073 | 9.51 (9.82) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 377 | cpu 9.4 ms/run |
| T3w po-e0 | ep.context_enable=1; ep.context_file_path=<work>\epopt\cache\ctx\rtmw_b3_fp16_po_e0_ctx.onnx; ep.context_embed_mode=0 | rtmw b3/fp16 | 4929 | 9.53 (9.97) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 377 | cpu 9.4 ms/run; dir 12 files 1412308 KB; files rtmw_b3_fp16_po_e0_ctx.onnx=None |
| T3l po-e0 | {} | rtmw b3/fp16 | - | - | - | - | 0 | - | FAIL: missing rtmw_b3_fp16_po_e0_ctx.onnx (write step made no file) |
| T3s po-e0 | [cfg]fail_on_suboptimal_compiled_model=1 | rtmw b3/fp16 | - | - | - | - | 0 | - | FAIL: missing rtmw_b3_fp16_po_e0_ctx.onnx (write step made no file) |
| T3w po-e1 | ep.context_enable=1; ep.context_file_path=<work>\epopt\cache\ctx\rtmw_b3_fp16_po_e1_ctx.onnx; ep.context_embed_mode=1 | rtmw b3/fp16 | 5008 | 10.21 (10.36) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 390 | cpu 9.4 ms/run; dir 12 files 1412308 KB; files rtmw_b3_fp16_po_e1_ctx.onnx=None |
| T3l po-e1 | {} | rtmw b3/fp16 | - | - | - | - | 0 | - | FAIL: missing rtmw_b3_fp16_po_e1_ctx.onnx (write step made no file) |
| T3s po-e1 | [cfg]fail_on_suboptimal_compiled_model=1 | rtmw b3/fp16 | - | - | - | - | 0 | - | FAIL: missing rtmw_b3_fp16_po_e1_ctx.onnx (write step made no file) |
| T4  | nv_persistent_context_memory=1 | yolox b1/fp32 | 4092 | 8.39 (9.15) | 0.619 / 7.3e-04 | 9->9 | 0.06 | 0 | 354 | cpu 8.3 ms/run |
| T4  | nv_persistent_context_memory=1 | yolox b1/fp16 | 2802 | 3.26 (4.36) | 2.688 / 3.1e-03 | 9->9 | 0.30 | 0 | 226 | cpu 3.1 ms/run |
| T4  | nv_persistent_context_memory=1 | yolox b3/fp32 | 2387 | 21.27 (23.58) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 437 | cpu 21.9 ms/run |
| T4  | nv_persistent_context_memory=1 | yolox b3/fp16 | 2832 | 9.61 (10.44) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 310 | cpu 9.9 ms/run |
| T4  | nv_persistent_context_memory=1 | rtmw b1/fp32 | 4076 | 9.02 (10.18) | 0.094 / 9.0e-03 | 4/3 | 0.5 | 0 | 526 | cpu 8.3 ms/run |
| T4  | nv_persistent_context_memory=1 | rtmw b1/fp16 | 4947 | 3.68 (4.85) | 0.147 / 0.0140 | 28/9 | 0.5 | 0 | 372 | cpu 3.6 ms/run |
| T4  | nv_persistent_context_memory=1 | rtmw b3/fp32 | 4013 | 20.90 (23.25) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 574 | cpu 20.8 ms/run |
| T4  | nv_persistent_context_memory=1 | rtmw b3/fp16 | 4974 | 9.08 (10.10) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 382 | cpu 9.4 ms/run |
| T5  | enable_cuda_graph=0 | yolox b1/fp32 | 4337 | 8.69 (9.55) | 0.619 / 7.3e-04 | 9->9 | 0.06 | 0 | 357 | cpu 7.3 ms/run |
| T5  | enable_cuda_graph=0 | yolox b1/fp16 | 2844 | 3.64 (4.77) | 2.688 / 3.1e-03 | 9->9 | 0.30 | 0 | 252 | cpu 4.2 ms/run |
| T5  | enable_cuda_graph=0 | yolox b3/fp32 | 2452 | 23.16 (26.17) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 469 | cpu 21.9 ms/run |
| T5  | enable_cuda_graph=0 | yolox b3/fp16 | 2794 | 10.73 (11.72) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 294 | cpu 10.4 ms/run |
| T5  | enable_cuda_graph=0 | rtmw b1/fp32 | 4129 | 9.71 (10.65) | 0.094 / 9.0e-03 | 4/3 | 0.5 | 0 | 536 | cpu 8.9 ms/run |
| T5  | enable_cuda_graph=0 | rtmw b1/fp16 | 5004 | 4.09 (4.71) | 0.147 / 0.0140 | 28/9 | 0.5 | 0 | 407 | cpu 4.2 ms/run |
| T5  | enable_cuda_graph=0 | rtmw b3/fp32 | 4336 | 20.77 (23.00) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 579 | cpu 20.8 ms/run |
| T5  | enable_cuda_graph=0 | rtmw b3/fp16 | 5026 | 9.46 (10.11) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 367 | cpu 9.4 ms/run |
| T6  | [env]NVIDIA_TF32_OVERRIDE=0 | yolox b1/fp32 | 2989 | 16.52 (17.91) | 0.082 / 1.5e-04 | 9->9 | 1.4e-03 | 0 | 351 | cpu 16.7 ms/run |
| T6  | [env]NVIDIA_TF32_OVERRIDE=0 | yolox b1/fp16 | 2716 | 3.27 (3.99) | 2.688 / 3.1e-03 | 9->9 | 0.30 | 0 | 253 | cpu 3.1 ms/run |
| T6  | [env]NVIDIA_TF32_OVERRIDE=0 | yolox b3/fp32 | 2389 | 45.13 (46.27) | 0.086 / 1.5e-04 | 27->27 | 1.4e-03 | 0 | 440 | cpu 43.8 ms/run |
| T6  | [env]NVIDIA_TF32_OVERRIDE=0 | yolox b3/fp16 | 2872 | 10.01 (11.00) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 372 | cpu 9.4 ms/run |
| T6  | [env]NVIDIA_TF32_OVERRIDE=0 | rtmw b1/fp32 | 4490 | 17.77 (19.86) | 2.7e-03 / 2.6e-04 | 0/0 | 0.0 | 0 | 533 | cpu 18.2 ms/run |
| T6  | [env]NVIDIA_TF32_OVERRIDE=0 | rtmw b1/fp16 | 4865 | 3.68 (4.67) | 0.147 / 0.0140 | 28/9 | 0.5 | 0 | 348 | cpu 3.6 ms/run |
| T6  | [env]NVIDIA_TF32_OVERRIDE=0 | rtmw b3/fp32 | 4753 | 47.78 (48.76) | 2.7e-03 / 2.7e-04 | 0/0 | 0.0 | 0 | 545 | cpu 47.9 ms/run |
| T6  | [env]NVIDIA_TF32_OVERRIDE=0 | rtmw b3/fp16 | 4989 | 9.64 (10.76) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 374 | cpu 9.4 ms/run |
| T3c cold | {} | yolox b3/fp32 | 1970 | 21.52 (23.03) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 435 | cpu 21.9 ms/run; dir 1 files 3583 KB |
| T3c warm | {} | yolox b3/fp32 | 494 | 21.33 (22.02) | 0.787 / 9.1e-04 | 27->27 | 0.05 | 0 | 418 | cpu 21.9 ms/run; dir 1 files 3583 KB |
| T3c cold | {} | yolox b3/fp16 | 2300 | 10.49 (11.04) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 317 | cpu 10.9 ms/run; dir 1 files 3671 KB |
| T3c warm | {} | yolox b3/fp16 | 353 | 9.69 (10.61) | 3.139 / 3.6e-03 | 27->27 | 0.39 | 0 | 297 | cpu 9.4 ms/run; dir 1 files 3671 KB |
| T3c cold | {} | rtmw b3/fp32 | 3336 | 21.07 (22.92) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 576 | cpu 21.9 ms/run; dir 1 files 4169 KB |
| T3c warm | {} | rtmw b3/fp32 | 1051 | 21.81 (23.35) | 0.088 / 8.3e-03 | 13/5 | 0.5 | 0 | 588 | cpu 21.9 ms/run; dir 1 files 4169 KB |
| T3c cold | {} | rtmw b3/fp16 | 4219 | 9.36 (10.56) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 456 | cpu 9.4 ms/run; dir 1 files 4045 KB |
| T3c warm | {} | rtmw b3/fp16 | 664 | 8.86 (10.10) | 0.183 / 0.0172 | 50/18 | 0.5 | 0 | 353 | cpu 7.8 ms/run; dir 1 files 4045 KB |
| O1  | {} | yolox b1/fp32 | 6458 | 115.84 (116.60) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 114.1 ms/run |
| O1  | {} | yolox b1/fp16 | 1047 | 115.93 (116.08) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 115.6 ms/run |
| O1  | {} | yolox b3/fp32 | 7539 | 315.80 (316.25) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 315.6 ms/run |
| O1  | {} | yolox b3/fp16 | 1128 | 315.93 (317.09) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 314.1 ms/run |
| O1  | {} | rtmw b1/fp32 | 7022 | 75.73 (76.34) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 76.0 ms/run |
| O1  | {} | rtmw b1/fp16 | 4339 | 75.68 (75.88) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.5 ms/run |
| O1  | {} | rtmw b3/fp32 | 8579 | 218.03 (218.86) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 215.6 ms/run |
| O1  | {} | rtmw b3/fp16 | 3999 | 215.52 (216.25) | 0.518 / 0.0523 | 83/32 | 1.0 | 0 | - | cpu 213.5 ms/run |
| O2  | load_config={"GPU": {"INFERENCE_PRECISION_HINT": "f32"}} | yolox b1/fp32 | 845 | 115.89 (117.87) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 111.5 ms/run |
| O2  | load_config={"GPU": {"INFERENCE_PRECISION_HINT": "f32"}} | yolox b1/fp16 | 1018 | 115.98 (117.25) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 113.5 ms/run |
| O2  | load_config={"GPU": {"INFERENCE_PRECISION_HINT": "f32"}} | yolox b3/fp32 | 1137 | 316.00 (317.48) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 306.8 ms/run |
| O2  | load_config={"GPU": {"INFERENCE_PRECISION_HINT": "f32"}} | yolox b3/fp16 | 1127 | 316.65 (317.62) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 308.3 ms/run |
| O2  | load_config={"GPU": {"INFERENCE_PRECISION_HINT": "f32"}} | rtmw b1/fp32 | 1448 | 75.81 (76.05) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 74.0 ms/run |
| O2  | load_config={"GPU": {"INFERENCE_PRECISION_HINT": "f32"}} | rtmw b1/fp16 | 1353 | 75.85 (76.10) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 74.5 ms/run |
| O2  | load_config={"GPU": {"INFERENCE_PRECISION_HINT": "f32"}} | rtmw b3/fp32 | 1442 | 215.41 (215.95) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 213.5 ms/run |
| O2  | load_config={"GPU": {"INFERENCE_PRECISION_HINT": "f32"}} | rtmw b3/fp16 | 1476 | 215.50 (216.25) | 0.518 / 0.0523 | 83/32 | 1.0 | 0 | - | cpu 210.9 ms/run |
| O3  | load_config={"GPU": {"EXECUTION_MODE_HINT": "ACCURACY"}} | yolox b1/fp32 | 1070 | 115.74 (115.97) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 114.1 ms/run |
| O3  | load_config={"GPU": {"EXECUTION_MODE_HINT": "ACCURACY"}} | yolox b1/fp16 | 1050 | 115.70 (115.98) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 115.1 ms/run |
| O3  | load_config={"GPU": {"EXECUTION_MODE_HINT": "ACCURACY"}} | yolox b3/fp32 | 1096 | 315.81 (316.14) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 314.6 ms/run |
| O3  | load_config={"GPU": {"EXECUTION_MODE_HINT": "ACCURACY"}} | yolox b3/fp16 | 1099 | 316.27 (316.88) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 316.1 ms/run |
| O3  | load_config={"GPU": {"EXECUTION_MODE_HINT": "ACCURACY"}} | rtmw b1/fp32 | 1439 | 75.77 (75.87) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 72.4 ms/run |
| O3  | load_config={"GPU": {"EXECUTION_MODE_HINT": "ACCURACY"}} | rtmw b1/fp16 | 956 | 75.75 (75.94) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 70.3 ms/run |
| O3  | load_config={"GPU": {"EXECUTION_MODE_HINT": "ACCURACY"}} | rtmw b3/fp32 | 1482 | 215.33 (215.58) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 213.5 ms/run |
| O3  | load_config={"GPU": {"EXECUTION_MODE_HINT": "ACCURACY"}} | rtmw b3/fp16 | 975 | 215.29 (215.72) | 0.518 / 0.0523 | 83/32 | 1.0 | 0 | - | cpu 211.5 ms/run |
| O4 LATENCY | load_config={"GPU": {"PERFORMANCE_HINT": "LATENCY"}} | yolox b3/fp32 | 1130 | 315.85 (316.56) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 311.5 ms/run |
| O4 LATENCY | load_config={"GPU": {"PERFORMANCE_HINT": "LATENCY"}} | rtmw b3/fp32 | 1482 | 215.34 (216.13) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 213.0 ms/run |
| O4 THROUGHPUT | load_config={"GPU": {"PERFORMANCE_HINT": "THROUGHPUT"}} | yolox b3/fp32 | 1105 | 315.83 (316.19) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 314.6 ms/run |
| O4 THROUGHPUT | load_config={"GPU": {"PERFORMANCE_HINT": "THROUGHPUT"}} | rtmw b3/fp32 | 1468 | 215.89 (216.49) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 215.1 ms/run |
| O4 NS1 | load_config={"GPU": {"NUM_STREAMS": "1"}} | yolox b3/fp32 | 1107 | 316.12 (317.38) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 315.6 ms/run |
| O4 NS1 | load_config={"GPU": {"NUM_STREAMS": "1"}} | rtmw b3/fp32 | 1467 | 215.52 (216.03) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 213.0 ms/run |
| O4 NS2 | load_config={"GPU": {"NUM_STREAMS": "2"}} | yolox b3/fp32 | 1079 | 315.78 (316.19) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 313.0 ms/run |
| O4 NS2 | load_config={"GPU": {"NUM_STREAMS": "2"}} | rtmw b3/fp32 | 1463 | 215.67 (216.84) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 212.5 ms/run |
| O5 cold | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\yolox_b1_fp32"}} | yolox b1/fp32 | 1139 | 115.78 (115.90) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 112.5 ms/run; dir 0 files 0 KB |
| O5 warm | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\yolox_b1_fp32"}} | yolox b1/fp32 | 1092 | 116.27 (117.42) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 112.5 ms/run; dir 0 files 0 KB |
| O5 cold | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\yolox_b1_fp16"}} | yolox b1/fp16 | 1053 | 116.08 (116.31) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 112.5 ms/run; dir 0 files 0 KB |
| O5 warm | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\yolox_b1_fp16"}} | yolox b1/fp16 | 1109 | 115.83 (116.10) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 115.6 ms/run; dir 0 files 0 KB |
| O5 cold | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\yolox_b3_fp32"}} | yolox b3/fp32 | 1113 | 316.31 (316.44) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 312.5 ms/run; dir 0 files 0 KB |
| O5 warm | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\yolox_b3_fp32"}} | yolox b3/fp32 | 1112 | 316.43 (316.53) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 315.6 ms/run; dir 0 files 0 KB |
| O5 cold | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\yolox_b3_fp16"}} | yolox b3/fp16 | 1118 | 316.35 (316.57) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 315.6 ms/run; dir 0 files 0 KB |
| O5 warm | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\yolox_b3_fp16"}} | yolox b3/fp16 | 1108 | 316.46 (316.55) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 315.6 ms/run; dir 0 files 0 KB |
| O5 cold | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\rtmw_b1_fp32"}} | rtmw b1/fp32 | 1453 | 75.69 (75.79) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.0 ms/run; dir 0 files 0 KB |
| O5 warm | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\rtmw_b1_fp32"}} | rtmw b1/fp32 | 1377 | 75.68 (75.79) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.0 ms/run; dir 0 files 0 KB |
| O5 cold | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\rtmw_b1_fp16"}} | rtmw b1/fp16 | 970 | 75.77 (76.03) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 78.1 ms/run; dir 0 files 0 KB |
| O5 warm | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\rtmw_b1_fp16"}} | rtmw b1/fp16 | 1416 | 75.68 (75.74) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.0 ms/run; dir 0 files 0 KB |
| O5 cold | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\rtmw_b3_fp32"}} | rtmw b3/fp32 | 1510 | 215.49 (215.82) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 212.5 ms/run; dir 0 files 0 KB |
| O5 warm | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\rtmw_b3_fp32"}} | rtmw b3/fp32 | 1467 | 215.40 (215.62) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 215.6 ms/run; dir 0 files 0 KB |
| O5 cold | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\rtmw_b3_fp16"}} | rtmw b3/fp16 | 1477 | 215.23 (215.41) | 0.518 / 0.0523 | 83/32 | 1.0 | 0 | - | cpu 203.1 ms/run; dir 0 files 0 KB |
| O5 warm | load_config={"GPU": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache\\rtmw_b3_fp16"}} | rtmw b3/fp16 | 1522 | 215.53 (215.59) | 0.518 / 0.0523 | 83/32 | 1.0 | 0 | - | cpu 215.6 ms/run; dir 0 files 0 KB |
| O6 prioHIGH | load_config={"GPU": {"MODEL_PRIORITY": "HIGH"}} | yolox b1/fp32 | 1101 | 115.76 (115.98) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 115.6 ms/run |
| O6 prioHIGH | load_config={"GPU": {"MODEL_PRIORITY": "HIGH"}} | yolox b3/fp32 | 1104 | 316.38 (316.79) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 313.0 ms/run |
| O6 prioHIGH | load_config={"GPU": {"MODEL_PRIORITY": "HIGH"}} | rtmw b1/fp32 | 1441 | 75.72 (75.93) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.0 ms/run |
| O6 prioHIGH | load_config={"GPU": {"MODEL_PRIORITY": "HIGH"}} | rtmw b3/fp32 | 1490 | 215.32 (215.93) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 213.5 ms/run |
| O6 throttleLOW | load_config={"GPU": {"GPU_QUEUE_THROTTLE": "LOW"}} | yolox b1/fp32 | 1062 | 115.65 (115.94) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 114.1 ms/run |
| O6 throttleLOW | load_config={"GPU": {"GPU_QUEUE_THROTTLE": "LOW"}} | yolox b3/fp32 | 1130 | 315.77 (316.15) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 312.5 ms/run |
| O6 throttleLOW | load_config={"GPU": {"GPU_QUEUE_THROTTLE": "LOW"}} | rtmw b1/fp32 | 1416 | 75.68 (75.81) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.0 ms/run |
| O6 throttleLOW | load_config={"GPU": {"GPU_QUEUE_THROTTLE": "LOW"}} | rtmw b3/fp32 | 1493 | 215.36 (215.72) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 210.4 ms/run |
| O6 throttleHIGH | load_config={"GPU": {"GPU_QUEUE_THROTTLE": "HIGH"}} | yolox b1/fp32 | 1088 | 115.71 (115.94) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 113.0 ms/run |
| O6 throttleHIGH | load_config={"GPU": {"GPU_QUEUE_THROTTLE": "HIGH"}} | yolox b3/fp32 | 1113 | 316.38 (317.36) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 312.5 ms/run |
| O6 throttleHIGH | load_config={"GPU": {"GPU_QUEUE_THROTTLE": "HIGH"}} | rtmw b1/fp32 | 1437 | 75.72 (76.11) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 72.9 ms/run |
| O6 throttleHIGH | load_config={"GPU": {"GPU_QUEUE_THROTTLE": "HIGH"}} | rtmw b3/fp32 | 1488 | 215.32 (216.04) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 208.9 ms/run |
| O7 precision | precision=FP32 | yolox b1/fp32 | 1144 | 120.32 (120.67) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 112.5 ms/run |
| O7 cache_dir | cache_dir=<work>\epopt\cache\ov-o7 | yolox b1/fp32 | 1152 | 120.17 (120.50) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 118.8 ms/run |
| O8  | [cfg]disable_cpu_ep_fallback=1 | yolox b1/fp32 | 1078 | 116.05 (116.30) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 109.4 ms/run |
| O8  | [cfg]disable_cpu_ep_fallback=1 | yolox b1/fp16 | 1083 | 115.73 (116.15) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 118.8 ms/run |
| O8  | [cfg]disable_cpu_ep_fallback=1 | rtmw b1/fp32 | 1425 | 75.82 (75.86) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 78.1 ms/run |
| O8  | [cfg]disable_cpu_ep_fallback=1 | rtmw b1/fp16 | 1413 | 75.89 (75.97) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 71.9 ms/run |
| O9 GPU-f32 | load_config={"GPU": {"INFERENCE_PRECISION_HINT": "f32"}} | rtmw b1/fp32 | 1520 | 75.77 (76.11) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.0 ms/run |
| O9 GPU-ACC | load_config={"GPU": {"EXECUTION_MODE_HINT": "ACCURACY"}} | rtmw b1/fp32 | 1461 | 75.73 (75.94) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.0 ms/run |
| O9 GPU.0-f32 | load_config={"GPU.0": {"INFERENCE_PRECISION_HINT": "f32"}} | rtmw b1/fp32 | 7248 | 137.00 (137.29) | 4.4e-05 / 4.4e-06 | 0/0 | 0.0 | 0 | - | cpu 132.8 ms/run |
| O9 GPU.0-ACC | load_config={"GPU.0": {"EXECUTION_MODE_HINT": "ACCURACY"}} | rtmw b1/fp32 | 1564 | 137.07 (137.35) | 4.4e-05 / 4.4e-06 | 0/0 | 0.0 | 0 | - | cpu 134.4 ms/run |
| O9 GPU.0-cache-cold | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache0\\rtmw_b1_fp32"}} | rtmw b1/fp32 | 1642 | 75.63 (75.79) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.0 ms/run; dir 1 files 188809 KB |
| O9 GPU.0-cache-warm | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcache0\\rtmw_b1_fp32"}} | rtmw b1/fp32 | 969 | 76.24 (76.74) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.0 ms/run; dir 1 files 188809 KB |
| O2g  | load_config={"GPU.0": {"INFERENCE_PRECISION_HINT": "f32"}} | yolox b1/fp32 | 5340 | 184.38 (184.64) | 1.0e-03 / 2.1e-06 | 9->9 | 1.4e-04 | 0 | - | cpu 182.3 ms/run |
| O2g  | load_config={"GPU.0": {"INFERENCE_PRECISION_HINT": "f32"}} | yolox b1/fp16 | 1056 | 184.50 (185.04) | 0.709 / 1.1e-03 | 9->9 | 0.04 | 0 | - | cpu 182.8 ms/run |
| O2g  | load_config={"GPU.0": {"INFERENCE_PRECISION_HINT": "f32"}} | yolox b3/fp32 | 4916 | 533.42 (535.72) | 1.2e-03 / 2.1e-06 | 27->27 | 1.4e-04 | 0 | - | cpu 528.6 ms/run |
| O2g  | load_config={"GPU.0": {"INFERENCE_PRECISION_HINT": "f32"}} | yolox b3/fp16 | 1056 | 533.77 (535.13) | 0.803 / 1.0e-03 | 27->27 | 0.04 | 0 | - | cpu 528.1 ms/run |
| O2g  | load_config={"GPU.0": {"INFERENCE_PRECISION_HINT": "f32"}} | rtmw b1/fp32 | 1542 | 136.96 (137.39) | 4.4e-05 / 4.4e-06 | 0/0 | 0.0 | 0 | - | cpu 134.4 ms/run |
| O2g  | load_config={"GPU.0": {"INFERENCE_PRECISION_HINT": "f32"}} | rtmw b1/fp16 | 6650 | 136.97 (137.26) | 0.050 / 4.8e-03 | 3/2 | 0.5 | 0 | - | cpu 136.5 ms/run |
| O2g  | load_config={"GPU.0": {"INFERENCE_PRECISION_HINT": "f32"}} | rtmw b3/fp32 | 5703 | 393.37 (394.05) | 5.4e-05 / 5.5e-06 | 0/0 | 0.0 | 0 | - | cpu 390.1 ms/run |
| O2g  | load_config={"GPU.0": {"INFERENCE_PRECISION_HINT": "f32"}} | rtmw b3/fp16 | 4925 | 393.33 (394.47) | 0.050 / 4.7e-03 | 5/2 | 0.5 | 0 | - | cpu 389.6 ms/run |
| O3g  | load_config={"GPU.0": {"EXECUTION_MODE_HINT": "ACCURACY"}} | yolox b1/fp32 | 1066 | 184.40 (184.93) | 1.0e-03 / 2.1e-06 | 9->9 | 1.4e-04 | 0 | - | cpu 182.3 ms/run |
| O3g  | load_config={"GPU.0": {"EXECUTION_MODE_HINT": "ACCURACY"}} | yolox b1/fp16 | 6223 | 117.52 (119.35) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 116.7 ms/run |
| O3g  | load_config={"GPU.0": {"EXECUTION_MODE_HINT": "ACCURACY"}} | yolox b3/fp32 | 1122 | 533.72 (536.70) | 1.2e-03 / 2.1e-06 | 27->27 | 1.4e-04 | 0 | - | cpu 529.2 ms/run |
| O3g  | load_config={"GPU.0": {"EXECUTION_MODE_HINT": "ACCURACY"}} | yolox b3/fp16 | 6499 | 319.68 (320.12) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 313.0 ms/run |
| O3g  | load_config={"GPU.0": {"EXECUTION_MODE_HINT": "ACCURACY"}} | rtmw b1/fp32 | 1473 | 137.01 (137.70) | 4.4e-05 / 4.4e-06 | 0/0 | 0.0 | 0 | - | cpu 130.2 ms/run |
| O3g  | load_config={"GPU.0": {"EXECUTION_MODE_HINT": "ACCURACY"}} | rtmw b1/fp16 | 6444 | 76.47 (76.71) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.5 ms/run |
| O3g  | load_config={"GPU.0": {"EXECUTION_MODE_HINT": "ACCURACY"}} | rtmw b3/fp32 | 1511 | 393.30 (394.18) | 5.4e-05 / 5.5e-06 | 0/0 | 0.0 | 0 | - | cpu 388.5 ms/run |
| O3g  | load_config={"GPU.0": {"EXECUTION_MODE_HINT": "ACCURACY"}} | rtmw b3/fp16 | 7952 | 219.31 (221.35) | 0.518 / 0.0523 | 83/32 | 1.0 | 0 | - | cpu 217.7 ms/run |
| O4g LATENCY | load_config={"GPU.0": {"PERFORMANCE_HINT": "LATENCY"}} | yolox b3/fp32 | 1089 | 316.51 (316.87) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 315.1 ms/run |
| O4g LATENCY | load_config={"GPU.0": {"PERFORMANCE_HINT": "LATENCY"}} | rtmw b3/fp32 | 1490 | 215.53 (215.91) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 213.0 ms/run |
| O4g THROUGHPUT | load_config={"GPU.0": {"PERFORMANCE_HINT": "THROUGHPUT"}} | yolox b3/fp32 | 1156 | 315.94 (316.99) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 314.1 ms/run |
| O4g THROUGHPUT | load_config={"GPU.0": {"PERFORMANCE_HINT": "THROUGHPUT"}} | rtmw b3/fp32 | 1553 | 215.63 (218.40) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 212.5 ms/run |
| O4g NS1 | load_config={"GPU.0": {"NUM_STREAMS": "1"}} | yolox b3/fp32 | 1053 | 315.81 (316.28) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 313.5 ms/run |
| O4g NS1 | load_config={"GPU.0": {"NUM_STREAMS": "1"}} | rtmw b3/fp32 | 1486 | 215.77 (217.74) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 215.1 ms/run |
| O4g NS2 | load_config={"GPU.0": {"NUM_STREAMS": "2"}} | yolox b3/fp32 | 1146 | 316.44 (318.24) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 310.4 ms/run |
| O4g NS2 | load_config={"GPU.0": {"NUM_STREAMS": "2"}} | rtmw b3/fp32 | 1514 | 215.46 (216.46) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 212.5 ms/run |
| O5g cold | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\yolox_b1_fp32"}} | yolox b1/fp32 | 1102 | 115.75 (115.95) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 115.6 ms/run; dir 1 files 55731 KB |
| O5g warm | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\yolox_b1_fp32"}} | yolox b1/fp32 | 819 | 115.69 (115.92) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 112.5 ms/run; dir 1 files 55731 KB |
| O5g cold | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\yolox_b1_fp16"}} | yolox b1/fp16 | 1121 | 115.78 (115.93) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 115.6 ms/run; dir 1 files 55731 KB |
| O5g warm | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\yolox_b1_fp16"}} | yolox b1/fp16 | 356 | 115.69 (115.83) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 109.4 ms/run; dir 1 files 55731 KB |
| O5g cold | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\yolox_b3_fp32"}} | yolox b3/fp32 | 1156 | 316.71 (316.79) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 306.2 ms/run; dir 1 files 56175 KB |
| O5g warm | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\yolox_b3_fp32"}} | yolox b3/fp32 | 884 | 315.96 (316.09) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 312.5 ms/run; dir 1 files 56175 KB |
| O5g cold | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\yolox_b3_fp16"}} | yolox b3/fp16 | 1141 | 316.50 (317.21) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 318.8 ms/run; dir 1 files 56176 KB |
| O5g warm | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\yolox_b3_fp16"}} | yolox b3/fp16 | 875 | 317.15 (317.48) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 315.6 ms/run; dir 1 files 56176 KB |
| O5g cold | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\rtmw_b1_fp32"}} | rtmw b1/fp32 | 1527 | 75.79 (76.30) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.0 ms/run; dir 1 files 188809 KB |
| O5g warm | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\rtmw_b1_fp32"}} | rtmw b1/fp32 | 924 | 75.90 (75.93) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.0 ms/run; dir 1 files 188809 KB |
| O5g cold | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\rtmw_b1_fp16"}} | rtmw b1/fp16 | 1568 | 75.84 (75.90) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.0 ms/run; dir 1 files 188809 KB |
| O5g warm | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\rtmw_b1_fp16"}} | rtmw b1/fp16 | 881 | 75.80 (75.98) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 78.1 ms/run; dir 1 files 188809 KB |
| O5g cold | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\rtmw_b3_fp32"}} | rtmw b3/fp32 | 1671 | 215.71 (216.03) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 215.6 ms/run; dir 1 files 193420 KB |
| O5g warm | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\rtmw_b3_fp32"}} | rtmw b3/fp32 | 960 | 215.71 (217.60) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 215.6 ms/run; dir 1 files 193420 KB |
| O5g cold | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\rtmw_b3_fp16"}} | rtmw b3/fp16 | 1629 | 215.65 (216.35) | 0.518 / 0.0523 | 83/32 | 1.0 | 0 | - | cpu 215.6 ms/run; dir 1 files 193420 KB |
| O5g warm | load_config={"GPU.0": {"CACHE_DIR": "<work>\\epopt\\cache\\ovcacheg\\rtmw_b3_fp16"}} | rtmw b3/fp16 | 921 | 215.39 (215.55) | 0.518 / 0.0523 | 83/32 | 1.0 | 0 | - | cpu 215.6 ms/run; dir 1 files 193420 KB |
| O6g prioHIGH | load_config={"GPU.0": {"MODEL_PRIORITY": "HIGH"}} | yolox b1/fp32 | 1081 | 115.91 (116.11) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 115.6 ms/run |
| O6g prioHIGH | load_config={"GPU.0": {"MODEL_PRIORITY": "HIGH"}} | yolox b3/fp32 | 1100 | 315.93 (316.35) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 315.1 ms/run |
| O6g prioHIGH | load_config={"GPU.0": {"MODEL_PRIORITY": "HIGH"}} | rtmw b1/fp32 | 1400 | 75.78 (76.09) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.0 ms/run |
| O6g prioHIGH | load_config={"GPU.0": {"MODEL_PRIORITY": "HIGH"}} | rtmw b3/fp32 | 1483 | 215.77 (218.04) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 215.1 ms/run |
| O6g throttleLOW | load_config={"GPU.0": {"GPU_QUEUE_THROTTLE": "LOW"}} | yolox b1/fp32 | 1070 | 116.14 (117.69) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 1.0 ms/run |
| O6g throttleLOW | load_config={"GPU.0": {"GPU_QUEUE_THROTTLE": "LOW"}} | yolox b3/fp32 | 1115 | 317.13 (318.91) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 4.2 ms/run |
| O6g throttleLOW | load_config={"GPU.0": {"GPU_QUEUE_THROTTLE": "LOW"}} | rtmw b1/fp32 | 1453 | 76.92 (79.59) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 1.6 ms/run |
| O6g throttleLOW | load_config={"GPU.0": {"GPU_QUEUE_THROTTLE": "LOW"}} | rtmw b3/fp32 | 1478 | 216.31 (218.64) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 1.6 ms/run |
| O6g throttleHIGH | load_config={"GPU.0": {"GPU_QUEUE_THROTTLE": "HIGH"}} | yolox b1/fp32 | 1080 | 115.86 (116.19) | 5.842 / 6.8e-03 | 9->9 | 0.46 | 0 | - | cpu 116.1 ms/run |
| O6g throttleHIGH | load_config={"GPU.0": {"GPU_QUEUE_THROTTLE": "HIGH"}} | yolox b3/fp32 | 1111 | 316.07 (317.49) | 9.440 / 0.0110 | 27->27 | 0.44 | 0 | - | cpu 312.0 ms/run |
| O6g throttleHIGH | load_config={"GPU.0": {"GPU_QUEUE_THROTTLE": "HIGH"}} | rtmw b1/fp32 | 1452 | 75.82 (76.22) | 0.416 / 0.0420 | 35/16 | 0.5 | 0 | - | cpu 75.5 ms/run |
| O6g throttleHIGH | load_config={"GPU.0": {"GPU_QUEUE_THROTTLE": "HIGH"}} | rtmw b3/fp32 | 1483 | 215.42 (216.39) | 0.538 / 0.0543 | 84/30 | 0.5 | 0 | - | cpu 212.5 ms/run |
| P1 EXTENDED | [so]graph_optimization_level=ORT_ENABLE_EXTENDED | yolox b1/fp32 | 104 | 112.94 (117.32) | 7.3e-04 / 8.6e-07 | 9->9 | 6.1e-05 | all | - | cpu 2249.0 ms/run |
| P1 EXTENDED | [so]graph_optimization_level=ORT_ENABLE_EXTENDED | yolox b3/fp32 | 96 | 1077.86 (1212.10) | 8.1e-04 / 9.4e-07 | 27->27 | 6.1e-05 | all | - | cpu 21379.2 ms/run |
| P1 EXTENDED | [so]graph_optimization_level=ORT_ENABLE_EXTENDED | rtmw b1/fp32 | 224 | 104.95 (111.23) | 1.4e-05 / 1.4e-06 | 0/0 | 0.0 | all | - | cpu 2090.6 ms/run |
| P1 EXTENDED | [so]graph_optimization_level=ORT_ENABLE_EXTENDED | rtmw b3/fp32 | 224 | 801.99 (899.41) | 1.2e-05 / 1.2e-06 | 0/0 | 0.0 | all | - | cpu 15685.4 ms/run |
| P1 BASIC | [so]graph_optimization_level=ORT_ENABLE_BASIC | yolox b1/fp32 | 92 | 119.44 (124.28) | 7.3e-04 / 8.6e-07 | 9->9 | 6.1e-05 | all | - | cpu 2376.6 ms/run |
| P1 BASIC | [so]graph_optimization_level=ORT_ENABLE_BASIC | yolox b3/fp32 | 88 | 1120.45 (1235.32) | 8.1e-04 / 9.4e-07 | 27->27 | 6.1e-05 | all | - | cpu 22072.4 ms/run |
| P1 BASIC | [so]graph_optimization_level=ORT_ENABLE_BASIC | rtmw b1/fp32 | 224 | 107.97 (128.55) | 1.5e-05 / 1.4e-06 | 0/0 | 0.0 | all | - | cpu 2177.1 ms/run |
| P1 BASIC | [so]graph_optimization_level=ORT_ENABLE_BASIC | rtmw b3/fp32 | 217 | 588.11 (937.16) | 1.2e-05 / 1.2e-06 | 0/0 | 0.0 | all | - | cpu 12250.0 ms/run |
| P2  | [cfg]dynamic_block_base=4 | yolox b1/fp32 | 201 | 65.76 (68.23) | 0.000 / 0 | 9->9 | 0.00 | all | - | cpu 1308.3 ms/run |
| P2  | [cfg]dynamic_block_base=4 | yolox b3/fp32 | 198 | 193.66 (202.18) | 0.000 / 0 | 27->27 | 0.00 | all | - | cpu 3855.7 ms/run |
| P2  | [cfg]dynamic_block_base=4 | rtmw b1/fp32 | 627 | 55.91 (59.57) | 0.000 / 0 | 0/0 | 0.0 | all | - | cpu 1121.4 ms/run |
| P2  | [cfg]dynamic_block_base=4 | rtmw b3/fp32 | 596 | 152.38 (167.51) | 0.000 / 0 | 0/0 | 0.0 | all | - | cpu 3046.9 ms/run |
| P3 t1 | [so]intra_op_num_threads=1 | yolox b1/fp32 | 172 | 482.60 (495.37) | 0.000 / 0 | 9->9 | 0.00 | all | - | cpu 478.6 ms/run |
| P3 t1 | [so]intra_op_num_threads=1 | yolox b3/fp32 | 167 | 1444.51 (1484.53) | 0.000 / 0 | 27->27 | 0.00 | all | - | cpu 1433.3 ms/run |
| P3 t1 | [so]intra_op_num_threads=1 | rtmw b1/fp32 | 484 | 390.95 (399.15) | 3.8e-06 / 3.6e-07 | 0/0 | 0.0 | all | - | cpu 390.6 ms/run |
| P3 t1 | [so]intra_op_num_threads=1 | rtmw b3/fp32 | 492 | 1186.79 (1221.59) | 4.8e-06 / 4.5e-07 | 0/0 | 0.0 | all | - | cpu 1182.8 ms/run |
| P3 t8 | [so]intra_op_num_threads=8 | yolox b1/fp32 | 174 | 80.64 (91.06) | 0.000 / 0 | 9->9 | 0.00 | all | - | cpu 648.4 ms/run |
| P3 t8 | [so]intra_op_num_threads=8 | yolox b3/fp32 | 168 | 267.03 (352.41) | 0.000 / 0 | 27->27 | 0.00 | all | - | cpu 2158.3 ms/run |
| P3 t8 | [so]intra_op_num_threads=8 | rtmw b1/fp32 | 530 | 67.85 (75.54) | 0.000 / 0 | 0/0 | 0.0 | all | - | cpu 541.7 ms/run |
| P3 t8 | [so]intra_op_num_threads=8 | rtmw b3/fp32 | 581 | 214.91 (221.21) | 0.000 / 0 | 0/0 | 0.0 | all | - | cpu 1686.5 ms/run |
| P3 t20 | [so]intra_op_num_threads=20 | yolox b1/fp32 | 186 | 62.76 (65.09) | 0.000 / 0 | 9->9 | 0.00 | all | - | cpu 1243.2 ms/run |
| P3 t20 | [so]intra_op_num_threads=20 | yolox b3/fp32 | 192 | 190.39 (198.75) | 0.000 / 0 | 27->27 | 0.00 | all | - | cpu 3789.6 ms/run |
| P3 t20 | [so]intra_op_num_threads=20 | rtmw b1/fp32 | 577 | 52.23 (57.56) | 0.000 / 0 | 0/0 | 0.0 | all | - | cpu 1057.8 ms/run |
| P3 t20 | [so]intra_op_num_threads=20 | rtmw b3/fp32 | 629 | 150.61 (170.99) | 0.000 / 0 | 0/0 | 0.0 | all | - | cpu 3021.4 ms/run |
| P3 spin0 | [cfg]intra_op.allow_spinning=0 | yolox b1/fp32 | 172 | 67.33 (68.41) | 0.000 / 0 | 9->9 | 0.00 | all | - | cpu 1048.4 ms/run |
| P3 spin0 | [cfg]intra_op.allow_spinning=0 | yolox b3/fp32 | 169 | 188.46 (194.14) | 0.000 / 0 | 27->27 | 0.00 | all | - | cpu 3124.5 ms/run |
| P3 spin0 | [cfg]intra_op.allow_spinning=0 | rtmw b1/fp32 | 488 | 57.85 (60.82) | 0.000 / 0 | 0/0 | 0.0 | all | - | cpu 904.2 ms/run |
| P3 spin0 | [cfg]intra_op.allow_spinning=0 | rtmw b3/fp32 | 482 | 144.33 (149.23) | 0.000 / 0 | 0/0 | 0.0 | all | - | cpu 2321.4 ms/run |
| C8b  | arena.max_mem=1073741824; use_tf32=0 | yolox b3/fp32 | 258 | - | - | - | 0 | 403 | FAIL: RuntimeException: [ONNXRuntimeError] : 6 : RUNTIME_EXCEPTION : Non-zero status code returned while running Conv node. Name:'/bbox_head/multi_level_cls_convs.0/multi_level_cls_convs.0.0/conv/Conv' Status Message: N:\_work |
| REF6  | [so]graph_optimization_level=ORT_ENABLE_ALL | yolox b6/fp32 | 374 | 452.09 (2281.44) | - | - | all | - | cpu 13818.8 ms/run |
| W1  | use_tf32=0; cudnn_conv_use_max_workspace=0 | yolox b3/fp32 | 385 | 184.36 (189.80) | 1.0e-03 / 1.7e-06 | 27->27 | 6.1e-05 | 0 | 5718 | cpu 179.2 ms/run |
| W2  | use_tf32=0; cudnn_conv_use_max_workspace=0; arena.max_mem=1073741824 | yolox b3/fp32 | 248 | - | - | - | 0 | 418 | FAIL: RuntimeException: [ONNXRuntimeError] : 6 : RUNTIME_EXCEPTION : Non-zero status code returned while running Conv node. Name:'/bbox_head/multi_level_cls_convs.0/multi_level_cls_convs.0.0/conv/Conv' Status Message: N:\_work |
| W3  | use_tf32=0; cudnn_conv_use_max_workspace=0 | yolox b1/fp32 | 219 | 12.54 (36.27) | 8.7e-04 / 1.9e-06 | 9->9 | 6.1e-05 | 0 | 402 | cpu 11.5 ms/run |
| W4  | use_tf32=0 | yolox b6/fp32 | 621 | 2638.32 (2811.31) | 1.1e-03 / 2.1e-06 | 54->54 | 2.7e-04 | 0 | 5988 | cpu 2540.6 ms/run |
| W4b  | use_tf32=0; cudnn_conv_use_max_workspace=0 | yolox b6/fp32 | 222 | 2572.76 (2691.65) | 1.1e-03 / 2.1e-06 | 54->54 | 2.7e-04 | 0 | 5830 | cpu 2536.5 ms/run |
| W5  | use_tf32=0; cudnn_conv_use_max_workspace=0 | rtmw b3/fp32 | 385 | 35.05 (36.63) | 6.4e-05 / 6.0e-06 | 0/0 | 0.0 | 0 | 678 | cpu 35.4 ms/run |
| W6  | use_tf32=1; cudnn_conv_use_max_workspace=0 | yolox b3/fp32 | 202 | 29.91 (30.40) | 0.666 / 7.7e-04 | 27->27 | 0.04 | 0 | 662 | cpu 28.1 ms/run |
| W6b  | cudnn_conv_use_max_workspace=0 | yolox b3/fp16 | 176 | 18.62 (19.31) | 1.699 / 2.0e-03 | 27->27 | 0.27 | 0 | 415 | cpu 18.8 ms/run |
| W7  | use_tf32=0; cudnn_conv_algo_search=HEURISTIC; cudnn_conv_use_max_workspace=0 | yolox b3/fp32 | 203 | 182.07 (187.02) | 1.0e-03 / 1.7e-06 | 27->27 | 6.1e-05 | 0 | 5845 | cpu 181.8 ms/run |
| W8  | use_tf32=0; prefer_nhwc=1; cudnn_conv_use_max_workspace=0 | yolox b3/fp32 | 230 | 197.19 (202.26) | 1.7e-03 / 2.0e-06 | 27->27 | 6.1e-05 | 0 | 5854 | cpu 190.1 ms/run |
| Wv C2 | use_tf32=0 | yolox b3/fp32 | 324 | 181.39 (181.39) | 1.0e-03 / 1.7e-06 | 27->27 | 6.1e-05 | 0 | 5845 | cpu 187.5 ms/run |
| Wv W1 | use_tf32=0; cudnn_conv_use_max_workspace=0 | yolox b3/fp32 | 343 | 186.13 (186.13) | 1.0e-03 / 1.7e-06 | 27->27 | 6.1e-05 | 0 | 5852 | cpu 187.5 ms/run |
| W4c  | {} | yolox b6/fp32 | 232 | 58.02 (59.28) | 1.109 / 1.3e-03 | 54->54 | 0.24 | 0 | 659 | cpu 58.9 ms/run |
| Wk ws-banana | cudnn_conv_use_max_workspace=banana | yolox b1/fp32 | 352 | 10.60 (10.62) | 0.741 / 8.7e-04 | 9->9 | 0.02 | 0 | 399 | cpu 5.2 ms/run |
| Wk tf32-banana | use_tf32=banana | yolox b1/fp32 | 338 | 11.33 (11.55) | 0.741 / 8.7e-04 | 9->9 | 0.02 | 0 | 405 | cpu 5.2 ms/run |
| Wk algo-banana | cudnn_conv_algo_search=banana | yolox b1/fp32 | 885 | 11.70 (11.81) | 0.741 / 8.7e-04 | 9->9 | 0.02 | 0 | 411 | cpu 10.4 ms/run |

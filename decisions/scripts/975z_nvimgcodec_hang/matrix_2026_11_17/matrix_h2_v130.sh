#!/usr/bin/env bash
# Evidence of ADR-975Z. This scratch script ran on 2026-11-17. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
R=$SCRATCH/hang_study/run_h2.sh
export WD=25
V130=1 bash $R --opts ":num_cuda_streams=1" --n 1 --session cuda
V130=1 bash $R --opts ":num_cuda_streams=1" --n 1 --session trt-rtx
V130=1 bash $R --opts ":num_cuda_streams=1" --n 1
V130=1 bash $R --opts ":num_cuda_streams=1" --n 2 --session cuda
V130=1 bash $R --n 1 --session trt-rtx
bash $R --opts ":num_cuda_streams=1" --n 1 --session trt-rtx
bash $R --n 1 --session trt-rtx
bash $R --n 1
bash $R --n 1 --stream private

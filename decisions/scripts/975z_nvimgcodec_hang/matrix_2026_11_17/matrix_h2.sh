#!/usr/bin/env bash
# Evidence of ADR-975Z. This scratch script ran on 2026-11-17. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
R=$SCRATCH/hang_study/run_h2.sh
bash $R --opts ":num_cuda_streams=1" --n 1 --stream private
bash $R --opts ":num_cuda_streams=1" --n 1 --stream legacy0
bash $R --opts ":num_cuda_streams=1" --n 0
bash $R --opts ":num_cuda_streams=1" --n 2
bash $R --opts ":num_cuda_streams=1" --n 3 --stream private
bash $R --opts ":num_cuda_streams=1" --n 1 --threads 1
bash $R --opts ":num_cuda_streams=2" --n 1 --threads 2
bash $R --opts ":num_cuda_streams=1" --n 1 --threads 2
bash $R --opts ":num_cuda_streams=14" --n 1
bash $R --opts ":num_cuda_streams=27" --n 1
bash $R --opts ":num_cuda_streams=26" --n 1
bash $R --opts ":num_cuda_streams=1" --n 1 --warm
bash $R --opts ":num_cuda_streams=1" --n 2 --repeat 3
bash $R --opts "nvjpeg_cuda_decoder:hybrid_huffman_threshold=0" --n 1
bash $R --n 1 --threads 4 --stream private --repeat 3
NVIMGCODEC_DEFAULT_NUM_CUDA_STREAMS=1 bash $R --n 1
bash $R --opts ":num_cuda_streams=1" --n 1 --session cuda

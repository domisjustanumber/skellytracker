#!/usr/bin/env bash
# Evidence of ADR-C6A5. This scratch script ran on 2026-11-18 and 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
# Stage 2: one factor at a time, short runs (20 measured calls) for more exits per minute. Usage: stage2.sh [steps...]
cd "$SCRATCH/exit_hang" || exit 2
LOOP=(uv run --no-sync --project "$LOOP_CWD" python -I "$SCRATCH_W\exit_hang\loop.py")
WRAP=(uv run --no-sync python "$SCRATCH_W\exit_hang\wrap.py")
MINI=(uv run --no-sync python "$SCRATCH_W\exit_hang\mini.py")
SHORT=(--calls 20 --warmup 2)
: "${LOOP_CWD:?set LOOP_CWD to the project folder of the children}"
for s in ${*:-a b c d e}; do
  case $s in
  a) "${LOOP[@]}" --runs 100 --timeout 120 --gpu-wait --label S2a_wrap_normal_cuda_M1_1080x6_short --env EXIT_MODE=normal EXIT_DUMP_S=60 -- "${WRAP[@]}" --ep cuda --mode M1 --res 1080 --cams 6 "${SHORT[@]}" --tag EH_s2 ;;
  b) "${LOOP[@]}" --runs 50 --timeout 120 --gpu-wait --label S2b_wrap_leak_cuda_M1_1080x6_short --env EXIT_MODE=leak EXIT_DUMP_S=60 -- "${WRAP[@]}" --ep cuda --mode M1 --res 1080 --cams 6 "${SHORT[@]}" --tag EH_s2 ;;
  c) "${LOOP[@]}" --runs 30 --timeout 120 --gpu-wait --label S2c_wrap_normal_trt-rtx_M1_1080x6_short --env EXIT_MODE=normal EXIT_DUMP_S=60 -- "${WRAP[@]}" --ep trt-rtx --mode M1 --res 1080 --cams 6 "${SHORT[@]}" --tag EH_s2 ;;
  d) "${LOOP[@]}" --runs 50 --timeout 120 --gpu-wait --label S2d_mini_normal_cuda_6x1080 -- "${MINI[@]}" --ep cuda --cams 6 --res 1080 --iters 30 --exit normal ;;
  e) "${LOOP[@]}" --runs 50 --timeout 120 --gpu-wait --label S2e_mini_leak_cuda_6x1080 -- "${MINI[@]}" --ep cuda --cams 6 --res 1080 --iters 30 --exit leak ;;
  f) "${LOOP[@]}" --runs 60 --timeout 120 --gpu-wait --label S2f_wrap_unreg_cuda_M1_1080x6_short --env EXIT_MODE=unreg EXIT_DUMP_S=60 -- "${WRAP[@]}" --ep cuda --mode M1 --res 1080 --cams 6 "${SHORT[@]}" --tag EH_s2 ;;
  g) "${LOOP[@]}" --runs 40 --timeout 180 --gpu-wait --label S1b_exact_cuda_M1_1080x6 -- uv run --no-sync python "$(cygpath -w "$PWD")\measure.py" --ep cuda --mode M1 --res 1080 --cams 6 --tag EH_exact ;;
  h) "${LOOP[@]}" --runs 1 --timeout 180 --gpu-wait --label S2h_alive_check_cuda -- uv run --no-sync python "$(cygpath -w "$PWD")\alive_check.py" --ep cuda --mode M1 --res 1080 --cams 6 --calls 20 --warmup 2 --tag EH_alive ;;
  t) "${LOOP[@]}" --runs 60 --timeout 120 --gpu-wait --label S2t_wrap_terminate_cuda_M1_1080x6_short --env EXIT_MODE=terminate EXIT_DUMP_S=60 -- "${WRAP[@]}" --ep cuda --mode M1 --res 1080 --cams 6 "${SHORT[@]}" --tag EH_s2 ;;
  esac
done
echo stage2 done
